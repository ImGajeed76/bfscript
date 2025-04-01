from lark import Lark, LarkError
import json # For pretty printing the IR

from lib.compiler.assembler import BFAssembler
from lib.compiler.memory_manager import MemoryManager
from lib.compiler.preprocessing import handle_includes, get_defines
from lib.compiler.scope_manager import Scope
from lib.compiler.transformer import BrainfuckScriptTransformer


class BrainfuckScriptCompiler:
    def __init__(self, grammar_file="grammar.lark"):
        with open(grammar_file, 'r', encoding='utf-8') as f:
            self.grammar = f.read()
        self.parser = Lark(self.grammar, start='start', parser='lalr') # Or 'earley'

        self.brainfuck_assembler = BFAssembler()

        # Configure memory layout
        # Cells 0-6 are reserved for temporary calculations
        self.temp_cell_pool_indices = self.brainfuck_assembler.temp_cell_pool
        self.memory_manager = MemoryManager(self.temp_cell_pool_indices)
        self.transformer = BrainfuckScriptTransformer(self.memory_manager, self.brainfuck_assembler)

    def compile(self, input_filepath):
        print(f"--- Starting Compilation: {input_filepath} ---")

        # 1. Handle Includes
        print("--- Pass 1: Handling Includes ---")
        try:
            full_code = handle_includes(input_filepath)
        except (FileNotFoundError, ValueError, RecursionError) as e:
            print(f"Error during include processing: {e}")
            return None

        # 1.2. Handle Defines
        print("--- Pass 1.2: Handling Defines ---")
        try:
            defines = get_defines(full_code)
            print("--- Defined Constants ---")
            print(json.dumps(defines, indent=2))
            print("-------------------------")
        except ValueError as e:
            print(f"Error during define processing: {e}")
            return None

        # 2. Parse the combined code
        print("--- Pass 2: Parsing ---")
        try:
            tree = self.parser.parse(full_code)
            # print("--- Abstract Syntax Tree (AST) ---")
            # print(tree.pretty())
            # print("---------------------------------")
        except LarkError as e:
            print(f"Error during parsing: {e}")
            return None

        # 3. Transform the AST into Intermediate Representation (IR)
        print("--- Pass 3: Transforming AST to IR (with Scope Mgmt, Defines, Folding) ---")
        try:
            self.transformer.defines = defines
            intermediate_representation = self.transformer.transform(tree)
            print("--- Intermediate Representation (IR) ---")
            # Pretty print the resulting IR dictionary
            print(json.dumps(intermediate_representation, indent=2, default=lambda o: repr(o))) # Use repr for non-serializable objects like Symbol
            print("---------------------------------------")
            print(f"Max Temp used: {self.memory_manager.max_temp}")
            print("---------------------------------------")
            print(intermediate_representation["code"])
            print(f"--- Compilation Finished ---")
            return intermediate_representation
        except (NameError, TypeError, ValueError, MemoryError, ZeroDivisionError, RuntimeError) as e:
            print(f"Error during transformation: {e}")
            # Potentially print stack trace here for debugging
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"An unexpected error occurred during transformation: {e}")
            import traceback
            traceback.print_exc()
            return None


# --- Beispiel-Ausführung ---
if __name__ == "__main__":
    # 1. Erstelle eine Beispiel-Grammatikdatei `grammar.lark` (wie in deiner Frage)
    # 2. Erstelle eine Beispiel-BrainfuckScript-Datei, z.B. `test.bfs`
    bfs_code = """
#define MODULO 50
#define REPEAT 5
    
size_t a = 5 * REPEAT + 2 - 1 + 30;
"""
    with open("test.bfs", "w", encoding="utf-8") as f:
        f.write(bfs_code)

    # Optional: Create an included file `math.bfs` if you want to test includes
    # with open("math.bfs", "w", encoding="utf-8") as f:
    #     f.write("size_t helper_var = 1;\n")

    # 3. Führe den Compiler aus
    compiler = BrainfuckScriptCompiler(grammar_file="grammar.lark")
    ir = compiler.compile("test.bfs")

    if ir:
        print("\nCompilation successful. IR generated.")
        # Hier würdest du den nächsten Schritt starten:
        # brainfuck_code = generate_brainfuck(ir, compiler.memory_manager)
        # print("\n--- Generated Brainfuck (Conceptual) ---")
        # print(brainfuck_code)
    else:
        print("\nCompilation failed.")

