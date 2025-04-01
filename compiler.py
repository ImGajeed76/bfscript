"""
Compiler script for BrainfuckScript.

Takes a BrainfuckScript (.bfs) file as input and outputs
compiled Brainfuck (.bf) code to a specified file.
"""

import argparse
import sys
from pathlib import Path
from lib.compiler.compiler import compile_bfscript


def main():
    """Parses arguments and runs the compiler."""
    parser = argparse.ArgumentParser(
        description="Compile BrainfuckScript (.bfs) to Brainfuck (.bf)."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input BrainfuckScript file (.bfs).",
    )
    parser.add_argument(
        "output_file",
        type=Path,
        help="Path to the output Brainfuck file (.bf).",
    )

    args = parser.parse_args()

    input_path: Path = args.input_file
    output_path: Path = args.output_file

    if not input_path.is_file():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Compiling {input_path}...")

    try:
        bf_code = compile_bfscript(str(input_path))

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bf_code)

        print(f"Successfully compiled to {output_path}")

    except FileNotFoundError:
        # This might be redundant if compile_bfscript handles it,
        # but good for robustness if it expects a path.
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nCompilation Error:", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
