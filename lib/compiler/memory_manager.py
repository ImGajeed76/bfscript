from typing import List, Union


class MemoryManager:
    """Manages the allocation of memory cells on the tape."""

    def __init__(self, temp_cell_pool_indices: List[int]):
        # Indices reserved for temporary calculations
        self.temp_cell_indices = list(temp_cell_pool_indices)
        self.temp_cell_pool = list(temp_cell_pool_indices)
        self.allocated_cells = set(temp_cell_pool_indices)
        self.max_temp = 0

    def _get_free_range(self, size: int = 1) -> int:
        """Finds the first free-range of the given size. Returns the start index."""
        range_start = 0
        found = False

        while not found:
            found = True

            for range_index in range(size):
                range_cell = range_start + range_index
                if range_cell in self.allocated_cells:
                    found = False
                    range_start = range_cell + range_index + 1
                    break

        return range_start

    def allocate(self, size=1) -> int:
        """Allocate a contiguous block of 'size' cells."""
        if size <= 0:
            raise ValueError("Allocation size must be positive.")

        start_cell = self._get_free_range(size)
        self.allocated_cells.update(range(start_cell, start_cell + size))
        return start_cell

    def release(self, cells: Union[int, List[int]]):
        """Mark cells as potentially reusable (basic implementation)."""
        if isinstance(cells, int):
            cells = [cells]
        self.allocated_cells.difference_update(cells)

    def get_temp_cell(self) -> int:
        """Get an available temporary cell."""
        if not self.temp_cell_pool:
            # This indicates a potential problem - complex expressions might
            # require more temp cells than allocated.
            raise MemoryError("Out of temporary cells!")
        cell = self.temp_cell_pool.pop(0)  # Get the first available
        if cell+1 > self.max_temp:
            self.max_temp = cell+1 # Use +1 because cell is 0-based
        print(f"MemoryManager: Temp cell {cell} allocated.")
        return cell

    def release_temp_cell(self, cell_index: int):
        """Return a temporary cell to the pool."""
        if cell_index not in self.temp_cell_pool:  # Avoid duplicates
            # Check that the cell is actually a temporary cell
            if cell_index not in self.temp_cell_indices:
                raise ValueError("Cannot release non-temporary cell.")

            # Add it back to the start for potential reuse (LIFO-like)
            self.temp_cell_pool.insert(0, cell_index)
            print(f"MemoryManager: Temp cell {cell_index} released.")
        else:
            raise ValueError("Cell already in the pool.")
