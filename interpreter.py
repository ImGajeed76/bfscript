"""
Interpreter script for Brainfuck code.

Takes a Brainfuck (.bf) file as input, optionally accepts initial
input as a string, and runs the code using the BFInterpreter.
Allows configuration of memory size, cell bits, and max execution time.
"""

import argparse
import sys
import time
from pathlib import Path
from lib.interpreter import BFInterpreter


def main():
    """Parses arguments and runs the interpreter."""
    parser = argparse.ArgumentParser(
        description="Interpret Brainfuck (.bf) code."
    )
    parser.add_argument(
        "brainfuck_file",
        type=Path,
        help="Path to the Brainfuck file (.bf) to execute.",
    )
    parser.add_argument(
        "initial_input",
        nargs="?",  # Makes this argument optional
        default="",  # Default value if not provided
        type=str,
        help="Optional initial input string for the Brainfuck program.",
    )
    parser.add_argument(
        "-m",
        "--memory-size",
        type=int,
        default=30000,
        help="Size of the Brainfuck memory tape (number of cells). Default: 30000",
    )
    parser.add_argument(
        "-b",
        "--cell-bits",
        type=int,
        default=32,
        choices=[8, 16, 32, 64],  # Example choices, adjust if needed
        help="Bit size of each memory cell (8, 16, 32, 64). Default: 32",
    )
    parser.add_argument(
        "-t",
        "--max-time",
        type=float,
        default=5.0,
        help="Maximum execution time in seconds (0 for unlimited). Default: 5.0",
    )

    args = parser.parse_args()

    bf_file_path: Path = args.brainfuck_file
    initial_input: str = args.initial_input
    memory_size: int = args.memory_size
    cell_bits: int = args.cell_bits
    max_time: float = args.max_time if args.max_time > 0 else float('inf')

    if not bf_file_path.is_file():
        print(
            f"Error: Brainfuck file not found: {bf_file_path}", file=sys.stderr
        )
        sys.exit(1)

    try:
        print(f"Reading Brainfuck code from: {bf_file_path}")
        bf_code = bf_file_path.read_text(encoding="utf-8")

        print("Initializing Interpreter...")
        print(f"  Memory Size: {memory_size}")
        print(f"  Cell Bits:   {cell_bits}")
        print(f"  Max Time:    {'Unlimited' if max_time == float('inf') else max_time}")
        print(f"  Input:       '{initial_input}'")
        print("-" * 20)
        print("Running Code:")
        print("-" * 20)

        start_time = time.monotonic()

        bfi = BFInterpreter(
            code=bf_code,
            memory_size=memory_size,
            cell_bits=cell_bits,
            initial_input=initial_input,
            max_execution_time=max_time,
        )
        bfi.run()

        end_time = time.monotonic()

        print(bfi.get_output())
        print("-" * 20)
        print(f"Execution finished in {end_time - start_time:.4f} seconds.")

    except FileNotFoundError:
        # Should be caught by the initial check, but good practice
        print(
            f"Error: Brainfuck file not found: {bf_file_path}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"\nInterpreter Error:", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
