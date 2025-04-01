from typing import Optional, Self, Dict, List

from lib.compiler.memory_manager import MemoryManager

SYMBOL_TYPES = ['size_t', 'stack', 'func']

class Symbol:
    """Represents a symbol in the scope (variable, stack, function)."""

    def __init__(self, name, symbol_type: str, size=None, is_initialized=False):
        if symbol_type not in SYMBOL_TYPES:
            raise ValueError(f"Invalid symbol type: {symbol_type}")

        self.name = name
        # symbol_type: 'size_t', 'stack', 'func'
        self.symbol_type = symbol_type
        # location: Memory cell index (for size_t/stack pointer), will be defined later
        self.location = None
        # size: Number of cells for stack data
        self.size = size
        # is_initialized: Flag for variables
        self.is_initialized = is_initialized

    def __repr__(self):
        return (
            f"Symbol(name={self.name}, type={self.symbol_type}, "
            f"loc={self.location}, size={self.size}, "
            f"init={self.is_initialized})"
        )


class Scope:
    """Manages symbols within a specific scope."""

    def __init__(self, memory_manager: MemoryManager, parent: Optional[Self] = None):
        self.parent = parent
        self.memory_manager = memory_manager
        # name -> Symbol object
        self.symbols: Dict[str, Symbol] = {}
        # Keep track of memory allocated specifically in this scope
        self.allocated_cells: List[int] = []

    def define(self, symbol: Symbol):
        """Define a new symbol in the current scope."""
        if symbol.name in self.symbols:
            # Handle redefinition error appropriately
            raise NameError(f"Symbol '{symbol.name}' already defined in this scope.")
        self.symbols[symbol.name] = symbol

        if symbol.symbol_type == 'size_t':
            symbol.location = self.allocate_memory()
        elif symbol.symbol_type == 'stack':
            if symbol.size is None:
                raise ValueError("Stack symbol must have a defined size.")
            symbol.location = self.allocate_memory(symbol.size)

        print(f"Scope: Defined {symbol}")

    def lookup(self, name: str):
        """Look up a symbol by name, checking current and parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def is_defined_locally(self, name):
        """Check if a symbol is defined only in the current scope."""
        return name in self.symbols

    def allocate_memory(self, size=1):
        """Request memory allocation from the global manager."""
        if not self.memory_manager:
            raise RuntimeError("Memory manager not available in this scope.")
        location = self.memory_manager.allocate(size)
        self.allocated_cells.extend(range(location, location + size))
        print(f"Scope: Allocated {size} cells starting at {location}")
        return location

    def release_memory(self):
        """Release memory allocated by this scope."""
        if not self.memory_manager:
            return  # Nothing to release if no manager
        print(f"Scope: Releasing cells {self.allocated_cells}")
        self.memory_manager.release(self.allocated_cells)
        self.allocated_cells = []

    def __enter__(self):
        # Optional: For use with 'with' statement if needed later
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Automatically release memory when scope exits
        self.release_memory()
