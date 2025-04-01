from typing import List, Callable

BIT_MODE = 32

MIN_UNSIGNED = 0
MAX_UNSIGNED = 2 ** BIT_MODE - 1

MIN_SIGNED = -2 ** (BIT_MODE - 1)
MAX_SIGNED = 2 ** (BIT_MODE - 1) - 1


def is_different_cells(cells: List[int]) -> bool:
    return len(set(cells)) == len(cells)


class BFAssembler:
    def __init__(self, temp_cell_pool_size: int = 20):
        self.generated_code = []
        self.symbol_table = {}
        self.current_pointer_pos = 0
        # Reserve, cells for temps initially
        # Temp cell usage must be finished before function returns
        self.temp_cell_pool = range(temp_cell_pool_size)
        self.next_available_cell = len(self.temp_cell_pool)  # Start allocating variables from here

    def plus(self, count=1) -> List[str]:
        return ["+"] * count

    def minus(self, count=1) -> List[str]:
        return ["-"] * count

    def move_right(self, count=1) -> List[str]:
        if count > 0:
            self.current_pointer_pos += count
            return [">"] * count
        else:
            raise ValueError("move_right called with non-positive count")

    def move_left(self, count=1) -> List[str]:
        if count > 0:
            self.current_pointer_pos -= count
            return ["<"] * count
        else:
            raise ValueError("move_left called with non-positive count")

    def open_brace(self) -> List[str]:
        return ["["]

    def close_brace(self) -> List[str]:
        return ["]"]

    def output(self) -> List[str]:
        return ["."]

    def input(self) -> List[str]:
        return [","]

    # --- Pointer Management ---
    def move_to_cell(self, target_cell_index: int) -> List[str]:
        delta = target_cell_index - self.current_pointer_pos
        if delta > 0:
            return self.move_right(delta)
        elif delta < 0:
            return self.move_left(-delta)
        else:
            # If delta is 0, do nothing
            return []

    # --- Basic Cell Operations ---
    def clear_cell(self, cell_index: int) -> List[str]:
        code = []
        code += self.move_to_cell(cell_index)
        code += self.open_brace()
        code += self.minus()
        code += self.close_brace()  # Result: "[-]". Pointer ends at cell_index.
        return code

    def set_cell_value(self, cell_index: int, value: int) -> List[str]:
        if value < 0:
            raise ValueError("set_cell_value called with negative value")

        code = []
        # Assumes 32-bit cells handle large values directly
        code += self.clear_cell(cell_index)
        code += self.move_to_cell(cell_index)  # Already there from clear_cell
        if value > 0:
            code += self.plus(value)
        # Handle negative values if your BF variant supports them,
        # otherwise only non-negative literals are easy.
        return code

    # --- More Complex Helpers ---

    # --- Variable Management ---
    def move_cell(self, src_index: int, dest_index: int) -> List[str]:
        if src_index == dest_index:
            return []

        # Destroys original value at src_index, leaves copy in dest_index
        code = []

        # Clear destination
        code += self.clear_cell(dest_index)

        # Move src -> dest
        code += self.move_to_cell(src_index)  # Go to source
        code += self.open_brace()  # [
        code += self.minus()  # - decrement src
        code += self.move_to_cell(dest_index)
        code += self.plus()  # + increment dest
        code += self.move_to_cell(src_index)  # < move back to src
        code += self.close_brace()  # ]
        return code

    def copy_cell_preserve_source(self, src_index: int, dest_index: int, temp_index: int = 0) -> List[str]:
        # Check if src_index, dest_index, and temp_index are all different
        if not is_different_cells([src_index, dest_index, temp_index]):
            raise ValueError("copy_cell_preserve_source called with non-distinct cell indices")

        # Copies src to dest, leaves src intact
        code = []

        # Clear destination and temp
        code += self.clear_cell(dest_index)
        code += self.clear_cell(temp_index)

        # Move src -> dest & temp
        code += self.move_to_cell(src_index)  # Go to source
        code += self.open_brace()  # [
        code += self.minus()  # - decrement src
        code += self.move_to_cell(dest_index)
        code += self.plus()  # + increment dest
        code += self.move_to_cell(temp_index)
        code += self.plus()  # + increment temp
        code += self.move_to_cell(src_index)  # < move back to src
        code += self.close_brace()  # ]

        # Move temp -> src
        code += self.move_to_cell(temp_index)
        code += self.open_brace()  # [
        code += self.minus()  # - decrement temp
        code += self.move_to_cell(src_index)
        code += self.plus()  # + increment src
        code += self.move_to_cell(temp_index)
        code += self.close_brace()  # ]
        return code

    # --- Loop Operations ---
    def loop_managed(self, condition_cell: int, loop_func: Callable[[], List[str]]) -> List[str]:
        code = []
        code += self.move_to_cell(condition_cell)
        code += self.open_brace()
        code += loop_func()
        code += self.move_to_cell(condition_cell)
        code += self.close_brace()
        return code

    def loop_managed_func(self, condition_func: Callable[[int], List[str]], loop_func: Callable[[], List[str]], temp_index_1: int = 0) -> List[str]:
        code = []
        code += condition_func(temp_index_1)
        code += self.move_to_cell(temp_index_1)
        code += self.open_brace()
        code += loop_func()
        code += condition_func(temp_index_1)
        code += self.move_to_cell(temp_index_1)
        code += self.close_brace()
        return code

    # --- Branching Operations ---
    def if_else(self, condition_cell: int, if_func: Callable[[], List[str]], else_code: Callable[[], List[str]] = None,
                temp_index_1: int = 0, temp_index_2: int = 1) -> List[str]:
        if not is_different_cells([condition_cell, temp_index_1, temp_index_2]):
            raise ValueError("if_else called with non-distinct cell indices")

        code = []

        # Copy condition to temp2
        code += self.copy_cell_preserve_source(condition_cell, temp_index_2, temp_index_1)

        if else_code:
            # Assume condition is false
            code += self.set_cell_value(temp_index_1, 1)

        # Check if condition is true
        def loop_func_wrapper(do_func: Callable[[], List[str]]) -> Callable[[], List[str]]:
            def loop_func() -> List[str]:
                loop_code = []
                loop_code += do_func()
                loop_code += self.clear_cell(temp_index_1)
                loop_code += self.clear_cell(temp_index_2)
                return loop_code

            return loop_func

        code += self.loop_managed(temp_index_2, loop_func_wrapper(if_func))

        if else_code:
            # Check if condition is false
            code += self.loop_managed(temp_index_1, loop_func_wrapper(else_code))

        return code

    # --- Arithmetic Operations ---
    def add_cells_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                           temp_index_2: int = 1) -> List[str]:
        if not is_different_cells([src1_index, src2_index, dest_index, temp_index_1, temp_index_2]):
            raise ValueError("add_cells called with non-distinct cell indices")

        # Adds src1 and src2, stores result in dest
        code = []

        # Clear destination
        code += self.clear_cell(dest_index)

        # Copy src1 -> dest
        code += self.copy_cell_preserve_source(src1_index, dest_index, temp_index_1)

        # Copy src2 -> temp
        code += self.copy_cell_preserve_source(src2_index, temp_index_2, temp_index_1)

        # Add temp -> dest
        code += self.move_to_cell(temp_index_2)
        code += self.open_brace()
        code += self.move_to_cell(dest_index)
        code += self.plus()
        code += self.move_to_cell(temp_index_2)
        code += self.minus()
        code += self.close_brace()
        return code

    def subtract_cells_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                                temp_index_2: int = 1) -> List[str]:
        if not is_different_cells([src1_index, src2_index, dest_index, temp_index_1, temp_index_2]):
            raise ValueError("subtract_cells called with non-distinct cell indices")

        # Subtracts src2 from src1, stores result in dest
        code = []

        # Clear destination
        code += self.clear_cell(dest_index)

        # Copy src1 -> dest
        code += self.copy_cell_preserve_source(src1_index, dest_index, temp_index_1)

        # Copy src2 -> temp
        code += self.copy_cell_preserve_source(src2_index, temp_index_2, temp_index_1)

        # Subtract temp -> dest
        code += self.move_to_cell(temp_index_2)
        code += self.open_brace()
        code += self.move_to_cell(dest_index)
        code += self.minus()
        code += self.move_to_cell(temp_index_2)
        code += self.minus()
        code += self.close_brace()
        return code

    # --- Comparison Operations ---

    def equals_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0, temp_index_2: int = 1) -> \
            List[str]:
        if not is_different_cells([src1_index, src2_index, dest_index, temp_index_1, temp_index_2]):
            raise ValueError("equals called with non-distinct cell indices")

        # Compares src1 and src2, stores 1 in dest if equal, 0 otherwise
        code = []

        # Subtract src2 from src1 and store in temp
        code += self.subtract_cells_unsigned(src1_index, src2_index, temp_index_1, dest_index, temp_index_2)

        # Assume src1 equals src2
        code += self.set_cell_value(dest_index, 1)

        # Start loop to check if temp is zero (if loop is entered, src1 != src2)
        def loop_check_equals() -> List[str]:
            loop_code = []
            loop_code += self.clear_cell(temp_index_1)
            loop_code += self.clear_cell(dest_index)
            return loop_code

        code += self.loop_managed(temp_index_1, loop_check_equals)
        return code

    def not_equals_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                            temp_index_2: int = 2) -> List[str]:
        if not is_different_cells([src1_index, src2_index, dest_index, temp_index_1, temp_index_2]):
            raise ValueError("not_equals called with non-distinct cell indices")

        # Compares src1 and src2, stores 1 in dest if not equal, 0 otherwise
        code = []

        # Subtract src2 from src1 and store in temp
        code += self.subtract_cells_unsigned(src1_index, src2_index, temp_index_1, dest_index, temp_index_2)

        # Assume src1 equals src2
        code += self.clear_cell(dest_index)

        # Start loop to check if temp is zero (if loop is entered, src1 != src2)
        def loop_check_equals() -> List[str]:
            loop_code = []
            loop_code += self.clear_cell(temp_index_1)
            loop_code += self.set_cell_value(dest_index, 1)
            return loop_code

        code += self.loop_managed(temp_index_1, loop_check_equals)
        return code

    def greater_than_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                              temp_index_2: int = 1, temp_index_3: int = 2, temp_index_4: int = 3) -> List[str]:
        if not is_different_cells(
                [src1_index, src2_index, dest_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4]):
            raise ValueError("greater_than called with non-distinct cell indices")

        # Compares src1 and src2, stores 1 in dest if src1 > src2, 0 otherwise
        code = []

        # Set dest to 0 to compare (this also means src1 !> src2, which is the default assumption)
        code += self.clear_cell(dest_index)

        # Subtract 1 from src1 and from src2 until one of them is zero
        code += self.copy_cell_preserve_source(src1_index, temp_index_1, temp_index_3)
        code += self.copy_cell_preserve_source(src2_index, temp_index_2, temp_index_3)

        # Loop to subtract 1 from src1 and src2 until one of them is zero
        def loop_func() -> List[str]:
            loop_code = []

            # Check if src2 is zero. If it is, src1 > src2
            def src2_is_zero_func() -> List[str]:
                src2_is_zero = []
                src2_is_zero += self.clear_cell(temp_index_1)
                src2_is_zero += self.set_cell_value(dest_index, 1)
                return src2_is_zero

            loop_code += self.if_else(temp_index_2, lambda: [], src2_is_zero_func, temp_index_3, temp_index_4)

            # Subtract 1 from src1 and src2 if src1 is not zero
            def subtract_func() -> List[str]:
                subtract_code = []
                subtract_code += self.move_to_cell(temp_index_1)
                subtract_code += self.minus()
                subtract_code += self.move_to_cell(temp_index_2)
                subtract_code += self.minus()
                return subtract_code

            loop_code += self.if_else(temp_index_1, subtract_func, lambda: [], temp_index_3, temp_index_4)

            return loop_code

        # Start loop 1
        code += self.loop_managed(temp_index_1, loop_func)

        return code

    def less_than_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0, temp_index_2: int = 1,
                           temp_index_3: int = 2, temp_index_4: int = 3) -> List[str]:
        if not is_different_cells([src1_index, src2_index, dest_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4]):
            raise ValueError("less_than called with non-distinct cell indices")

        # Compares src1 and src2, stores 1 in dest if src1 < src2, 0 otherwise
        # This uses the greater_than function since src1 < src2 is equivalent to src2 > src1
        return self.greater_than_unsigned(src2_index, src1_index, dest_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4)

    def logical_not(self, src_index: int, dest_index: int, temp_index_1: int = 0, temp_index_2: int = 1) -> List[str]:
        if not is_different_cells([src_index, dest_index, temp_index_1, temp_index_2]):
            raise ValueError("logical_not called with non-distinct cell indices")

        # Stores 1 in dest if src is 0, 0 otherwise
        code = []

        # Copy src -> temp1
        code += self.copy_cell_preserve_source(src_index, temp_index_1, temp_index_2)

        # Assume src is 0
        code += self.set_cell_value(dest_index, 1)

        # Start loop to check if src is zero (if loop is entered, src is not zero)
        def loop_check_zero() -> List[str]:
            loop_code = []
            loop_code += self.clear_cell(temp_index_1)
            loop_code += self.clear_cell(dest_index)
            return loop_code

        code += self.loop_managed(temp_index_1, loop_check_zero)

        return code

    def less_than_or_equal_to_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                                       temp_index_2: int = 1, temp_index_3: int = 2, temp_index_4: int = 3) -> List[str]:
        if not is_different_cells(
                [src1_index, src2_index, dest_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4]):
            raise ValueError("less_than_or_equal_to called with non-distinct cell indices")

        # Stores 1 in dest if src1 <= src2, 0 otherwise
        code = []

        # src1 <= src2 is equivalent to !(src1 > src2)
        code += self.greater_than_unsigned(src1_index, src2_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4,
                                           dest_index)
        code += self.logical_not(temp_index_1, dest_index, temp_index_2, temp_index_3)
        return code

    def greater_than_or_equal_to_unsigned(self, src1_index: int, src2_index: int, dest_index: int, temp_index_1: int = 0,
                                          temp_index_2: int = 1, temp_index_3: int = 2, temp_index_4: int = 3) -> List[str]:
        if not is_different_cells(
                [src1_index, src2_index, dest_index, temp_index_1, temp_index_2, temp_index_3, temp_index_4]):
            raise ValueError("greater_than_or_equal_to called with non-distinct cell indices")

        # Stores 1 in dest if src1 >= src2, 0 otherwise
        code = []

        # src1 >= src2 is equivalent to src2 <= src1
        code += self.less_than_or_equal_to_unsigned(src2_index, src1_index, dest_index, temp_index_1, temp_index_2, temp_index_3,
                                                    temp_index_4)
        return code
