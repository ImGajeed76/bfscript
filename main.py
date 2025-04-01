from typing import List

from lib.compiler.assembler import BFAssembler
from lib.interpreter import BFInterpreter

if __name__ == "__main__":
    bfc = BFAssembler()
    code_fragments = [] # Use a list to gather code parts

    # Copy Cat Example
    keep_running_cell = 5
    input_cell = 6
    temp_cell = 7
    dot_cell = 8

    code_fragments += bfc.set_cell_value(keep_running_cell, 1)
    code_fragments += bfc.set_cell_value(dot_cell, ord("."))

    def copy_cat() -> List[str]:
        copy_code = []

        copy_code += bfc.move_to_cell(input_cell)
        copy_code += bfc.input()

        def if_dot() -> List[str]:
            return bfc.set_cell_value(keep_running_cell, 0)

        def if_not_dot() -> List[str]:
            print_code = []
            print_code += bfc.move_to_cell(input_cell)
            print_code += bfc.output()
            return print_code

        copy_code += bfc.equals_unsigned(input_cell, dot_cell, temp_cell)
        copy_code += bfc.if_else(temp_cell, if_dot, if_not_dot)

        return copy_code

    code_fragments += bfc.loop_managed(keep_running_cell, copy_cat)

    print("".join(code_fragments))

    bfi = BFInterpreter("".join(code_fragments), initial_input="Hello World!.")
    bfi.run()

    print(bfi.get_output())
