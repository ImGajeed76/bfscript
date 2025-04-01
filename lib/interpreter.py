import array
import io
import time


class BFInterpreter:
    """
    A simplified, optimized Brainfuck interpreter.

    Features:
    - Fast execution via Run-Length Encoding (RLE) and pre-calculated jumps.
    - Input via a pre-supplied string.
    - Full output retrieval after execution.
    - Memory view retrieval after execution.
    - Configurable memory size, including an 'infinite' (auto-expanding) option.
    - Configurable cell size (8, 16, 32, 64 bits unsigned).
    - Maximum execution time limit.
    """

    # Default initial size if memory_size=None (infinite mode)
    _DEFAULT_INITIAL_MEM_SIZE = 1024

    def __init__(
            self,
            code,
            memory_size=30000,  # Set to None for 'infinite' memory
            cell_bits=8,
            initial_input="",
            max_execution_time=5.0,  # Seconds
    ):
        """
        Initializes the Brainfuck interpreter.

        Args:
            code (str): The Brainfuck code to interpret.
            memory_size (int | None): Number of cells in the memory tape.
                                      If None, memory starts small and expands
                                      automatically as needed.
            cell_bits (int): Size of each memory cell in bits (8, 16, 32, 64).
            initial_input (str): The string to use as input for ','.
            max_execution_time (float): Maximum allowed execution time in seconds.

        Raises:
            ValueError: If cell_bits is not supported or brackets mismatch.
            TimeoutError: If execution exceeds max_execution_time.
            IndexError: If data pointer goes below zero.
            MemoryError: If memory cannot be allocated/expanded.
        """
        self.original_code = code
        self.cell_bits = cell_bits
        self._input_buffer = initial_input
        self.max_execution_time = max_execution_time

        # --- Memory Configuration ---
        self._infinite_memory = memory_size is None
        self._initial_memory_size = (
            self._DEFAULT_INITIAL_MEM_SIZE if self._infinite_memory else memory_size
        )
        if self._initial_memory_size <= 0 and not self._infinite_memory:
            raise ValueError("memory_size must be positive or None")

        if cell_bits == 8:
            self._array_type = 'B'
            self.cell_mask = 0xFF
        elif cell_bits == 16:
            self._array_type = 'H'
            self.cell_mask = 0xFFFF
        elif cell_bits == 32:
            self._array_type = 'I'
            self.cell_mask = 0xFFFFFFFF
        elif cell_bits == 64:
            # Prefer 'Q' (unsigned long long) if available
            try:
                array.array('Q', [0])
                self._array_type = 'Q'
                self.cell_mask = 0xFFFFFFFFFFFFFFFF
            except ValueError:
                # Fallback to 'L' (unsigned long) if 'Q' not supported
                try:
                    array.array('L', [0])
                    self._array_type = 'L'
                    import struct
                    if struct.calcsize('L') == 8:
                        self.cell_mask = 0xFFFFFFFFFFFFFFFF
                    elif struct.calcsize('L') == 4:
                        self.cell_mask = 0xFFFFFFFF
                        if cell_bits == 64:
                            raise ValueError(
                                "64-bit cells ('Q') not supported, and 'L' is only 32-bit on this platform.")
                    else:
                        raise ValueError("Unsupported size for 'L' array type.")
                except ValueError:
                    raise ValueError("Neither 'Q' nor 'L' array type supported for 64-bit cells.")
        else:
            raise ValueError("Unsupported cell_bits. Use 8, 16, 32, or 64.")

        # --- Code Processing (RLE and Jumps) ---
        self._rle_code = []  # Stores tuples: (command, value/count, original_index)
        self._build_rle_and_jump_map()  # Populates _rle_code
        self.code_len = len(self._rle_code)

        # --- State Initialization ---
        self.memory = None
        self.memory_size = 0  # Actual current size
        self.data_ptr = 0
        self.code_ptr = 0
        self._input_ptr = 0
        self.full_output_buffer = io.StringIO()
        self.execution_time = 0.0
        self.finished = False

        self.reset()  # Initialize memory and pointers

    def _build_rle_and_jump_map(self):
        """
        Filters code, performs Run-Length Encoding (RLE), and builds
        jump map integrated into the RLE code list.
        Populates self._rle_code.
        """
        self._rle_code = []
        jump_stack = []
        last_cmd = None
        count = 0
        original_idx_start = 0  # Track start index of current RLE group

        for char_idx, char in enumerate(self.original_code):
            if char not in '.,+-<>[]':  # Ignore non-command characters (and '#')
                continue

            # If the command changes or is one that cannot be grouped
            if char != last_cmd or char in '.,[]':
                if last_cmd and count > 0:
                    # Store (command, count, start_original_index)
                    self._rle_code.append((last_cmd, count, original_idx_start))
                # Reset for the new command
                last_cmd = char
                count = 0
                original_idx_start = char_idx  # Store start index

            # Handle the current command
            if char in '+-><':
                count += 1
            elif char == '[':
                jump_stack.append(len(self._rle_code))
                # Store (command, placeholder, original_index)
                self._rle_code.append(('[', 0, original_idx_start))
                last_cmd = None  # Reset last_cmd
            elif char == ']':
                if not jump_stack:
                    raise ValueError(f"Mismatched ']' at code position ~{char_idx}")
                start_rle_index = jump_stack.pop()
                # Store (command, jump_target_index, original_index)
                self._rle_code.append((']', start_rle_index, original_idx_start))
                # Update the matching '[' command's placeholder value
                start_cmd, _, start_orig_idx = self._rle_code[start_rle_index]
                self._rle_code[start_rle_index] = (start_cmd, len(self._rle_code) - 1, start_orig_idx)
                last_cmd = None  # Reset last_cmd
            elif char in '.,':
                # Store (command, 1, original_index) - count is always 1
                self._rle_code.append((char, 1, original_idx_start))
                last_cmd = None  # Reset last_cmd

        # Add the last command group if any
        if last_cmd and count > 0:
            self._rle_code.append((last_cmd, count, original_idx_start))

        if jump_stack:
            unmatched_rle_index = jump_stack.pop()
            _, _, unmatched_original_idx = self._rle_code[unmatched_rle_index]
            raise ValueError(f"Mismatched '[' at code position ~{unmatched_original_idx}")

    def reset(self):
        """Resets the interpreter state (memory, pointers, output, input)."""
        self.memory = array.array(self._array_type, (0,) * self._initial_memory_size)
        self.memory_size = self._initial_memory_size
        self.data_ptr = 0
        self.code_ptr = 0
        self._input_ptr = 0
        self.full_output_buffer = io.StringIO()
        self.execution_time = 0.0
        self.finished = False

    def _ensure_memory_bounds(self):
        """Expands memory if data_ptr goes out of bounds (if infinite)."""
        if self.data_ptr < 0:
            raise IndexError("Data pointer went below zero")

        if self.data_ptr >= self.memory_size:
            if not self._infinite_memory:
                raise IndexError(f"Data pointer ({self.data_ptr}) out of fixed memory bounds ({self.memory_size})")
            else:
                # Expand memory (e.g., double it or increase by fixed chunk)
                new_size = max(self.data_ptr + 1, self.memory_size * 2)
                # Add a buffer beyond the immediate need
                new_size = max(new_size, self.data_ptr + 1024)
                try:
                    # Create new larger array and copy data efficiently
                    new_mem = array.array(self._array_type, (0,) * new_size)
                    # Use memoryview for potentially faster slicing/copying
                    new_mem[:self.memory_size] = self.memory
                    self.memory = new_mem
                    self.memory_size = new_size
                except MemoryError:
                    raise MemoryError(f"Cannot expand memory to size {new_size}")
                except OverflowError:
                    raise MemoryError(f"Cannot expand memory further (requested size {new_size})")

    def run(self):
        """Executes the code until completion, error, or timeout."""
        if self.finished:
            # print("Execution already completed.", file=sys.stderr)
            return  # Avoid re-running

        start_time = time.perf_counter()
        self.finished = False

        while self.code_ptr < self.code_len:
            # --- Time Limit Check ---
            current_time = time.perf_counter()
            if current_time - start_time > self.max_execution_time:
                self.execution_time = current_time - start_time
                self.finished = True  # Mark as finished (due to timeout)
                raise TimeoutError(f"Execution exceeded maximum time of {self.max_execution_time} seconds.")

            # --- Execute RLE Command ---
            command, value, _ = self._rle_code[self.code_ptr]  # value is count or jump target

            if command == '>':
                self.data_ptr += value
                self._ensure_memory_bounds()
            elif command == '<':
                self.data_ptr -= value
                self._ensure_memory_bounds()  # Checks < 0
            elif command == '+':
                current_val = self.memory[self.data_ptr]
                self.memory[self.data_ptr] = (current_val + value) & self.cell_mask
            elif command == '-':
                current_val = self.memory[self.data_ptr]
                self.memory[self.data_ptr] = (current_val - value) & self.cell_mask
            elif command == '.':
                char_val = self.memory[self.data_ptr]
                output_char = chr(char_val & 0xFF)  # Output lowest byte
                self.full_output_buffer.write(output_char * value)
            elif command == ',':
                for _ in range(value):
                    input_val = 0  # Default for EOF
                    if self._input_ptr < len(self._input_buffer):
                        input_char = self._input_buffer[self._input_ptr]
                        input_val = ord(input_char)
                        self._input_ptr += 1
                    self.memory[self.data_ptr] = input_val & self.cell_mask
            elif command == '[':
                if self.memory[self.data_ptr] == 0:
                    self.code_ptr = value  # Jump to matching ']' RLE index
            elif command == ']':
                if self.memory[self.data_ptr] != 0:
                    self.code_ptr = value  # Jump back to matching '[' RLE index

            self.code_ptr += 1
            # End of while loop

        # --- Execution Finished ---
        end_time = time.perf_counter()
        self.execution_time = end_time - start_time
        self.finished = True

    # --- Output and State Retrieval ---

    def get_output(self):
        """Returns the entire output generated during execution."""
        return self.full_output_buffer.getvalue()

    def get_memory_view(self, start=0, end=None, format='dec'):
        """
        Returns a string representation of a portion of the final memory state.

        Args:
            start (int): Starting memory index (inclusive).
            end (int): Ending memory index (exclusive). Defaults to start + 10
                       or end of memory, whichever is smaller.
            format (str): 'dec' (decimal), 'hex' (hexadecimal), 'char' (ASCII char).

        Returns:
            str: A string showing memory indices and values.
        """
        if self.memory is None:
            return "Memory not initialized."

        effective_end = self.memory_size
        if end is None:
            end = min(start + 10, effective_end)
        else:
            end = min(end, effective_end)
        start = max(0, start)

        if start >= end:
            return "Invalid memory range."

        output = []
        hex_width = (self.cell_bits + 3) // 4  # Calculate needed hex digits

        for i in range(start, end):
            # Check bounds against the *actual* allocated memory length
            if i >= len(self.memory):
                output.append(f"[{i}]: <beyond allocated>")
                continue

            val = self.memory[i]
            is_final_ptr = "(final ptr)" if i == self.data_ptr else ""

            if format == 'hex':
                val_str = f"0x{val:0{hex_width}X}"
            elif format == 'char':
                char_val = val & 0xFF
                val_str = f"'{chr(char_val)}' ({val})" if 32 <= char_val <= 126 else f". ({val})"
            else:  # 'dec'
                val_str = str(val)
            output.append(f"[{i}]: {val_str:<15} {is_final_ptr}")
        return "\n".join(output)

    def get_final_state(self):
        """
        Returns a dictionary containing the final interpreter state after running.
        """
        return {
            "final_code_ptr": self.code_ptr,
            "final_data_ptr": self.data_ptr,
            "final_cell_value": self.memory[
                self.data_ptr] if self.memory and 0 <= self.data_ptr < self.memory_size else None,
            "memory_size": self.memory_size,  # Current actual size
            "configured_memory": "infinite" if self._infinite_memory else self._initial_memory_size,
            "cell_bits": self.cell_bits,
            "finished": self.finished,
            "total_output": self.get_output(),
            "execution_time_sec": self.execution_time,
            "input_consumed_count": self._input_ptr
        }

    def __str__(self):
        """Provides a summary string of the final state."""
        state = self.get_final_state()
        mem_view = self.get_memory_view(max(0, state['final_data_ptr'] - 4), state['final_data_ptr'] + 6)
        status = "Finished" if state['finished'] else "Not Run/Incomplete"
        if not state['finished'] and self.execution_time > 0:
            status = "Timed Out"  # Or potentially errored before finishing

        return (
            f"--- Brainfuck Interpreter Final State ---\n"
            f" Status       : {status}\n"
            f" Code Ptr     : {state['final_code_ptr']} / {self.code_len}\n"
            f" Data Ptr     : {state['final_data_ptr']}\n"
            f" Final Cell   : {state['final_cell_value']}\n"
            f" Memory Size  : {state['memory_size']} (Configured: {state['configured_memory']})\n"
            f" Cell Bits    : {state['cell_bits']}\n"
            f" Input Read   : {state['input_consumed_count']} chars\n"
            f" Exec Time    : {state['execution_time_sec']:.6f} s\n"
            f" Total Output : '{state['total_output']}'\n"
            f"--- Final Memory View (around ptr) ---\n"
            f"{mem_view}\n"
            f"---------------------------------------"
        )

    def evaluate_number(self, number: int) -> int:
        """
        Converts the provided number to a valid cell value.

        For example in 8-Bit it would convert -1 to 255, and 256 to 0.

        Args:
            number (int): The number to evaluate.

        Returns:
            int: The valid cell value.
        """

        while number < 0:
            number += self.cell_mask + 1

        return number % (self.cell_mask + 1)
