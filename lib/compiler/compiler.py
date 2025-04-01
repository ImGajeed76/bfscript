import os

from lark import Lark, LarkError
import json  # For pretty printing the IR

from lib.compiler.assembler import BFAssembler
from lib.compiler.memory_manager import MemoryManager
from lib.compiler.preprocessing import handle_includes, get_defines
from lib.compiler.scope_manager import Scope
from lib.compiler.transformer import BrainfuckScriptTransformer


class BrainfuckScriptCompiler:
    def __init__(self, grammar_file=None, temp_cell_pool_size=20):
        if grammar_file is None:
            grammar_file = os.path.join(os.path.dirname(__file__), 'brainfuckscript.lark')

        with open(grammar_file, 'r', encoding='utf-8') as f:
            self.grammar = f.read()
        self.parser = Lark(self.grammar, start='start', parser='lalr')  # Or 'earley'

        self.brainfuck_assembler = BFAssembler(temp_cell_pool_size)

        self.temp_cell_pool_indices = self.brainfuck_assembler.temp_cell_pool
        self.memory_manager = MemoryManager(self.temp_cell_pool_indices)
        self.transformer = BrainfuckScriptTransformer(self.memory_manager, self.brainfuck_assembler)

    def compile(self, input_filepath) -> str:
        print(f"--- Starting Compilation: {input_filepath} ---")

        try:
            full_code = handle_includes(input_filepath)
        except (FileNotFoundError, ValueError, RecursionError) as e:
            print(f"Error during include processing: {e}")
            return None

        try:
            defines = get_defines(full_code)
        except ValueError as e:
            print(f"Error during define processing: {e}")
            return None

        try:
            tree = self.parser.parse(full_code)
            # print("--- Abstract Syntax Tree (AST) ---")
            # print(tree.pretty())
            # print("---------------------------------")
        except LarkError as e:
            print(f"Error during parsing: {e}")
            return None

        try:
            self.transformer.defines = defines
            intermediate_representation = self.transformer.transform(tree)
            print(f"Max Temp used: {self.memory_manager.max_temp}")
            return intermediate_representation["code"]
        except (NameError, TypeError, ValueError, MemoryError, ZeroDivisionError, RuntimeError) as e:
            print(f"Error during transformation: {e}")
            # Potentially print stack trace here for debugging
            import traceback
            traceback.print_exc()
            return ""
        except Exception as e:
            print(f"An unexpected error occurred during transformation: {e}")
            import traceback
            traceback.print_exc()
            return ""


# Convenience function to generate BrainfuckScript to Brainfuck code
def compile_bfscript(input_filepath: str):
    compiler = BrainfuckScriptCompiler()
    bf_code = compiler.compile(input_filepath)

    if compiler.memory_manager.max_temp < len(compiler.temp_cell_pool_indices):
        print(
            f"Only {compiler.memory_manager.max_temp} temporary cells used out of {len(compiler.temp_cell_pool_indices)} available.")
        if input("Would you like to optimize the temporary cell pool? (y/n): ").lower() == 'y':
            op_compiler = BrainfuckScriptCompiler(temp_cell_pool_size=compiler.memory_manager.max_temp)
            bf_code = op_compiler.compile(input_filepath)

    if bf_code:
        print("\nCompilation successful. Brainfuck code generated.")
        print("\n--- Generated Brainfuck ---")
        print(bf_code)
    else:
        print("\nCompilation failed.")

    return bf_code
