import unittest

from interpreter import BFInterpreter


class TestBrainfuckInterpreter(unittest.TestCase):

    def test_hello_world(self):
        """Tests the classic 'Hello World!' program."""
        code = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."
        interpreter = BFInterpreter(code)
        interpreter.run()
        self.assertEqual(interpreter.get_output(), "Hello World!\n")
        self.assertTrue(interpreter.finished)

    def test_increment_decrement_wrap(self):
        """Tests basic increment, decrement, and wrapping (8-bit)."""
        code = "+>++>+++>++++>+++++>++++++"  # Cells 0-5 get values 1-6
        code += ">" + ("+" * 255)  # Cell 6 gets 255
        code += ">+"  # Cell 7 gets 1
        interpreter = BFInterpreter(code, cell_bits=8)
        interpreter.run()
        # Check initial values
        self.assertEqual(interpreter.memory[0], 1)
        self.assertEqual(interpreter.memory[5], 6)
        self.assertEqual(interpreter.memory[6], 255)
        self.assertEqual(interpreter.memory[7], 1)

        # Test wrapping
        code2 = ">>>>>>+>-"  # Increment cell 6 (255->0), decrement cell 7 (1->0)
        interpreter2 = BFInterpreter(code2, cell_bits=8)
        # Manually set initial memory state for this part
        interpreter2.memory[6] = 255
        interpreter2.memory[7] = 1
        interpreter2.run()
        self.assertEqual(interpreter2.memory[6], 0)  # Wrap up
        self.assertEqual(interpreter2.memory[7], 0)  # Simple decrement

        # Test wrapping down
        code3 = "-"  # Decrement cell 0 (initially 0)
        interpreter3 = BFInterpreter(code3, cell_bits=8)
        interpreter3.run()
        self.assertEqual(interpreter3.memory[0], 255)  # Wrap down

    def test_pointer_movement(self):
        """Tests moving the data pointer."""
        code = "++>+++>-"  # Set cell 0=2, cell 1=3, cell 2=-1 (255 if 8bit)
        interpreter = BFInterpreter(code)
        interpreter.run()
        self.assertEqual(interpreter.data_ptr, 2)
        self.assertEqual(interpreter.memory[0], 2)
        self.assertEqual(interpreter.memory[1], 3)
        self.assertEqual(interpreter.memory[2], interpreter.cell_mask)  # Wrapped

        code2 = ">>>><<"  # Move right 4, then left 2
        interpreter2 = BFInterpreter(code2)
        interpreter2.run()
        self.assertEqual(interpreter2.data_ptr, 2)

    def test_simple_loop(self):
        """Tests a basic loop that executes."""
        # Set cell 0 to 3, then loop 3 times decrementing cell 0 and incrementing cell 1
        code = "+++[->+<]"
        interpreter = BFInterpreter(code)
        interpreter.run()
        self.assertEqual(interpreter.memory[0], 0)
        self.assertEqual(interpreter.memory[1], 3)
        self.assertEqual(interpreter.data_ptr, 0)  # Pointer ends back at cell 0

    def test_skipped_loop(self):
        """Tests a loop that is skipped because the cell is zero."""
        code = ">+++<[->+<]"  # Cell 1 = 3, loop should be skipped as cell 0 is 0
        interpreter = BFInterpreter(code)
        interpreter.run()
        self.assertEqual(interpreter.memory[0], 0)
        self.assertEqual(interpreter.memory[1], 3)
        self.assertEqual(interpreter.data_ptr, 0)  # Pointer ends at cell 1

    def test_input(self):
        """Tests the input command ','."""
        code = ",>,<."  # Read char into cell 0, move, read into cell 1, move back, print cell 0
        initial_input = "AB"
        interpreter = BFInterpreter(code, initial_input=initial_input)
        interpreter.run()
        self.assertEqual(interpreter.memory[0], ord('A'))
        self.assertEqual(interpreter.memory[1], ord('B'))
        self.assertEqual(interpreter.get_output(), "A")

    def test_input_eof(self):
        """Tests input EOF behavior (should store 0)."""
        code = ",."  # Read one char (EOF), print it
        interpreter = BFInterpreter(code, initial_input="")  # No input
        interpreter.run()
        self.assertEqual(interpreter.memory[0], 0)
        self.assertEqual(interpreter.get_output(), chr(0))  # Prints null byte

    def test_rle_effectiveness(self):
        """Tests if RLE handles consecutive commands correctly."""
        code_rle = "+++++>>---."
        code_no_rle = "+ + + + + > > - - - ."  # Spaces ignored
        interpreter_rle = BFInterpreter(code_rle)
        interpreter_no_rle = BFInterpreter(code_no_rle)

        interpreter_rle.run()
        interpreter_no_rle.run()

        self.assertEqual(interpreter_rle.get_output(), interpreter_no_rle.get_output())
        self.assertEqual(interpreter_rle.memory[0], 5)
        self.assertEqual(interpreter_rle.memory[1], 0)
        self.assertEqual(interpreter_rle.memory[2], (0 - 3) & interpreter_rle.cell_mask)
        self.assertEqual(interpreter_rle.data_ptr, 2)
        # Compare final memory state (simple check)
        self.assertListEqual(list(interpreter_rle.memory[:5]), list(interpreter_no_rle.memory[:5]))

    def test_fixed_memory_boundary_error(self):
        """Tests error when exceeding fixed memory."""
        code = ">>>"  # Default memory is 30000
        interpreter = BFInterpreter(code, memory_size=2)
        with self.assertRaises(IndexError):
            interpreter.run()

    def test_infinite_memory_expansion(self):
        """Tests if infinite memory expands as needed."""
        code = ""
        # Move pointer far right - adjust count based on default initial size
        initial_size = BFInterpreter._DEFAULT_INITIAL_MEM_SIZE
        code = ">" * (initial_size + 5) + "+"  # Move beyond initial size and increment
        interpreter = BFInterpreter(code, memory_size=None)  # Infinite memory
        try:
            interpreter.run()
            # Check if memory expanded and value was set
            self.assertGreater(interpreter.memory_size, initial_size)
            self.assertEqual(interpreter.data_ptr, initial_size + 5)
            self.assertEqual(interpreter.memory[interpreter.data_ptr], 1)
        except IndexError:
            self.fail("IndexError raised unexpectedly with infinite memory")

    def test_pointer_below_zero_error(self):
        """Tests error when data pointer goes below zero."""
        code = "<"
        interpreter = BFInterpreter(code)
        with self.assertRaises(IndexError):
            interpreter.run()

    def test_timeout_error(self):
        """Tests if execution times out correctly."""
        code = "+[]"  # Infinite loop
        interpreter = BFInterpreter(code, max_execution_time=0.01)
        with self.assertRaises(TimeoutError):
            interpreter.run()
        self.assertTrue(interpreter.finished)  # Should be marked finished due to timeout

    def test_bracket_mismatch_error_open(self):
        """Tests error on unmatched '['."""
        code = "++["
        with self.assertRaises(ValueError):
            BFInterpreter(code)

    def test_bracket_mismatch_error_close(self):
        """Tests error on unmatched ']'."""
        code = "++]"
        with self.assertRaises(ValueError):
            BFInterpreter(code)

    def test_invalid_cell_bits(self):
        """Tests error on unsupported cell_bits."""
        with self.assertRaises(ValueError):
            BFInterpreter("", cell_bits=12)

    def test_invalid_memory_size(self):
        """Tests error on invalid fixed memory size."""
        with self.assertRaises(ValueError):
            BFInterpreter("", memory_size=0)
        with self.assertRaises(ValueError):
            BFInterpreter("", memory_size=-100)

    def test_reset(self):
        """Tests the reset() method."""
        code = "++>+."
        interpreter = BFInterpreter(code)
        interpreter.run()

        # Check state after first run
        self.assertEqual(interpreter.get_output(), chr(1))
        self.assertEqual(interpreter.memory[0], 2)
        self.assertEqual(interpreter.memory[1], 1)
        self.assertEqual(interpreter.data_ptr, 1)
        self.assertTrue(interpreter.finished)

        interpreter.reset()

        # Check state after reset
        self.assertEqual(interpreter.get_output(), "")
        self.assertEqual(interpreter.memory[0], 0)
        self.assertEqual(interpreter.memory[1], 0)
        self.assertEqual(interpreter.data_ptr, 0)
        self.assertEqual(interpreter.code_ptr, 0)
        self.assertFalse(interpreter.finished)
        self.assertEqual(interpreter.execution_time, 0.0)

        # Run again after reset
        interpreter.run()
        self.assertEqual(interpreter.get_output(), chr(1))
        self.assertEqual(interpreter.memory[1], 1)
        self.assertTrue(interpreter.finished)

    def test_get_memory_view(self):
        """Tests the get_memory_view method."""
        code = "++>+++>++++"
        interpreter = BFInterpreter(code, cell_bits=8)
        interpreter.run()
        # Default view (around final pointer)
        view_dec = interpreter.get_memory_view(format='dec')
        self.assertIn("[0]: 2", view_dec)
        self.assertIn("[1]: 3", view_dec)
        self.assertIn("[2]: 4", view_dec)
        self.assertIn("(final ptr)", view_dec)  # Pointer should be at index 2

        # Hex view
        view_hex = interpreter.get_memory_view(start=0, end=3, format='hex')
        self.assertIn("[0]: 0x02", view_hex)
        self.assertIn("[1]: 0x03", view_hex)
        self.assertIn("[2]: 0x04", view_hex)

        # Char view
        code_ascii = "++++++[>++++++++++<-]>."  # Put 60 ('<') in cell 1
        interpreter_ascii = BFInterpreter(code_ascii, cell_bits=8)
        interpreter_ascii.run()
        view_char = interpreter_ascii.get_memory_view(start=0, end=2, format='char')
        self.assertIn("[0]: . (0)", view_char)  # Cell 0 is 0
        self.assertIn("[1]: '<' (60)", view_char)  # Cell 1 is 60

    def test_get_final_state(self):
        """Tests the get_final_state method."""
        code = "+>++."
        interpreter = BFInterpreter(code, initial_input="X", memory_size=50, cell_bits=16)
        interpreter.run()
        state = interpreter.get_final_state()

        self.assertTrue(state["finished"])
        self.assertEqual(state["final_data_ptr"], 1)
        self.assertEqual(state["final_cell_value"], 2)
        self.assertEqual(state["memory_size"], 50)
        self.assertEqual(state["configured_memory"], 50)
        self.assertEqual(state["cell_bits"], 16)
        self.assertEqual(state["total_output"], chr(2))
        self.assertGreater(state["execution_time_sec"], 0)
        self.assertEqual(state["input_consumed_count"], 0)  # No ',' used


if __name__ == '__main__':
    unittest.main()
