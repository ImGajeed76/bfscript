import unittest

from lib.compiler.assembler import BFAssembler
from lib.interpreter import BFInterpreter


class TestBrainfuckAssembler(unittest.TestCase):

    def test_plus(self):
        bfc = BFAssembler()
        code = []
        code += bfc.plus(8)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[0], bfi.evaluate_number(8))

    def test_minus(self):
        bfc = BFAssembler()
        code = []
        code += bfc.minus(8)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[0], bfi.evaluate_number(-8))

    def test_move_right(self):
        bfc = BFAssembler()
        code = []
        code += bfc.plus(8)
        code += bfc.move_right(1)
        code += bfc.plus(4)
        code += bfc.move_right(3)
        code += bfc.plus(2)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[0], bfi.evaluate_number(8))
        self.assertEqual(bfi.memory[1], bfi.evaluate_number(4))
        self.assertEqual(bfi.memory[4], bfi.evaluate_number(2))

    def test_move_left(self):
        bfc = BFAssembler()
        code = []
        code += bfc.plus(8)
        code += bfc.move_right(1)
        code += bfc.plus(4)
        code += bfc.move_right(8)
        code += bfc.plus(2)
        code += bfc.move_left(4)
        code += bfc.plus(3)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[0], bfi.evaluate_number(8))
        self.assertEqual(bfi.memory[1], bfi.evaluate_number(4))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(2))
        self.assertEqual(bfi.memory[5], bfi.evaluate_number(3))

    def test_set_cell_value(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)
        code += bfc.move_right(1)
        code += bfc.plus(5)
        code += bfc.set_cell_value(2, 10)
        code += bfc.set_cell_value(0, 3)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(48))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[2], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[0], bfi.evaluate_number(3))

    def test_clear_cell(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)
        code += bfc.set_cell_value(5, 10)
        code += bfc.clear_cell(8)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(0))
        self.assertEqual(bfi.memory[5], bfi.evaluate_number(10))

    def test_move_cell(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)
        code += bfc.move_cell(8, 5)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(0))
        self.assertEqual(bfi.memory[5], bfi.evaluate_number(48))

    def test_copy_cell(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)
        code += bfc.copy_cell_preserve_source(8, 5)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(48))
        self.assertEqual(bfi.memory[5], bfi.evaluate_number(48))

    def test_output(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)
        code += bfc.output()

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.get_output(), "0")

    def test_input(self):
        bfc = BFAssembler()
        code = []
        code += bfc.input()

        bfi = BFInterpreter("".join(code), initial_input="5")
        bfi.run()

        self.assertEqual(bfi.memory[0], bfi.evaluate_number(48 + 5))

    def test_loop_managed(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 48)

        def loop_func():
            loop_code = []
            loop_code += bfc.move_to_cell(9)
            loop_code += bfc.plus()
            loop_code += bfc.move_to_cell(8)
            loop_code += bfc.minus()
            return loop_code

        code += bfc.loop_managed(8, loop_func)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(0))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(48))

    def test_if_else_if(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)

        def if_func():
            return bfc.set_cell_value(9, 10)

        def else_func():
            return bfc.set_cell_value(9, 20)

        code += bfc.if_else(8, if_func, else_func)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))

    def test_if_else_else(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 0)

        def if_func():
            return bfc.set_cell_value(9, 10)

        def else_func():
            return bfc.set_cell_value(9, 20)

        code += bfc.if_else(8, if_func, else_func)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[9], bfi.evaluate_number(20))

    def test_add_cells(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.add_cells_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(15))

    def test_subtract_cells(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.subtract_cells_unsigned(9, 8, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(5))

    def test_equals_true(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 5)
        code += bfc.equals_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_equals_false(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.equals_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_not_equals_true(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.not_equals_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_not_equals_false(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 5)
        code += bfc.not_equals_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_greater_than_true(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 10)
        code += bfc.set_cell_value(9, 5)
        code += bfc.greater_than_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_greater_than_false(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.greater_than_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_less_than_true(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.less_than_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_less_than_false(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 10)
        code += bfc.set_cell_value(9, 5)
        code += bfc.less_than_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_logical_not_true(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 0)
        code += bfc.logical_not(8, 9)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(0))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(1))

    def test_logical_not_false(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 1)
        code += bfc.logical_not(8, 9)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(1))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(0))

    def test_greater_than_or_equals_less(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 10)
        code += bfc.set_cell_value(9, 5)
        code += bfc.greater_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_greater_than_or_equals_equal(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 5)
        code += bfc.greater_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_greater_than_or_equals_greater(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.greater_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_less_than_or_equals_less(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 10)
        code += bfc.less_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_less_than_or_equals_equal(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 5)
        code += bfc.set_cell_value(9, 5)
        code += bfc.less_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(1))

    def test_less_than_or_equals_greater(self):
        bfc = BFAssembler()
        code = []
        code += bfc.set_cell_value(8, 10)
        code += bfc.set_cell_value(9, 5)
        code += bfc.less_than_or_equal_to_unsigned(8, 9, 10)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[8], bfi.evaluate_number(10))
        self.assertEqual(bfi.memory[9], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[10], bfi.evaluate_number(0))

    def test_loop_managed_func(self):
        bfc = BFAssembler()

        a_index = 7
        b_index = 8

        code = []

        def condition_func(result_cell: int):
            return bfc.not_equals_unsigned(a_index, b_index, result_cell, 5, 6)

        def loop_func():
            loop_code = []
            loop_code += bfc.move_to_cell(a_index)
            loop_code += bfc.plus()
            return loop_code

        code += bfc.set_cell_value(a_index, 0)
        code += bfc.set_cell_value(b_index, 5)
        code += bfc.loop_managed_func(condition_func, loop_func, 4)

        bfi = BFInterpreter("".join(code))
        bfi.run()

        self.assertEqual(bfi.memory[a_index], bfi.evaluate_number(5))
        self.assertEqual(bfi.memory[b_index], bfi.evaluate_number(5))


if __name__ == '__main__':
    unittest.main()