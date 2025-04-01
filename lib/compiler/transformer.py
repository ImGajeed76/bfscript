from typing import List, Union, Dict

from lark import Transformer, v_args

from lib.compiler.assembler import BFAssembler
from lib.compiler.memory_manager import MemoryManager
from lib.compiler.scope_manager import Scope, Symbol


# Placeholder for Intermediate Representation (IR)
# In a real compiler, this would be more structured.
# We use dictionaries for demonstration.
# Example: {'op': 'assign', 'target_loc': 5, 'value_ir': {'op': 'const', 'value': 10}}
# Example: {'op': 'add', 'left_ir': {...}, 'right_ir': {...}, 'result_temp_loc': 0}

class BrainfuckScriptTransformer(Transformer):
    def __init__(self, memory_manager: MemoryManager, brainfuck_assembler: BFAssembler, defines=None):
        super().__init__()
        self.memory_manager = memory_manager
        self.brainfuck_assembler = brainfuck_assembler
        self.global_scope = Scope(self.memory_manager)
        self.current_scope = self.global_scope
        self.defines = defines if defines else {}
        self.functions = {}  # Store function definitions (name -> {'params': [...], 'body_ir': [...]})
        # Track variable initialization status within scopes
        # This might be better integrated directly into the Symbol class
        self.init_status = {}  # (scope, var_name) -> bool

    def _enter_scope(self):
        """Creates a new child scope and sets it as current."""
        new_scope = Scope(self.memory_manager, parent=self.current_scope)
        self.current_scope = new_scope
        print(f"Transformer: Entered new scope (parent: {self.current_scope.parent is not None})")
        return new_scope  # Return the new scope in case it's needed immediately

    def _exit_scope(self):
        """Exits the current scope and returns to the parent."""
        if self.current_scope.parent is None:
            raise RuntimeError("Cannot exit global scope.")
        # Clean up memory allocated ONLY in this scope
        self.current_scope.release_memory()
        # Clean up initialization status for variables defined in this scope
        vars_in_scope = list(self.current_scope.symbols.keys())
        for var_name in vars_in_scope:
            key = (self.current_scope, var_name)
            if key in self.init_status:
                del self.init_status[key]

        print(f"Transformer: Exiting scope. Returning to parent.")
        self.current_scope = self.current_scope.parent

    # --- Preprocessor ---
    def define_directive(self, items):
        # This is handled directly in the preprocessor
        name = str(items[0])
        return {'op': 'nop', 'comment': f'define {name}'}  # No direct code gen

    # --- Top Level ---
    def _process_block(self, items) -> (List, List[str]):
        code = []
        processed_items = []

        def process_folded_array(arr: Union[List, Dict], fc: List[str], pi: List[Dict]):
            if isinstance(arr, list):
                return [process_folded_array(item, fc, pi) for item in arr]
            elif isinstance(arr, dict):
                if arr and arr.get('op') != 'nop':  # Skip nops like defines
                    fc += arr['code_func']()
                    pi.append(arr)

        process_folded_array(items, code, processed_items)
        return processed_items, code

    def start(self, items):
        # Process all top-level items (globals, functions)
        # Function definitions are processed first to allow forward calls
        function_defs = [item for item in items if isinstance(item, dict) and item.get('op') == 'func_def_stored']
        other_items = [item for item in items if not (isinstance(item, dict) and item.get('op') == 'func_def_stored')]

        processed_items, final_code = self._process_block(other_items)

        # Combine IRs - simple list for now
        # A real compiler might structure this into data/code sections
        return {'op': 'program', 'globals_ir': processed_items, 'functions': self.functions, 'code': "".join(final_code)}

    def global_declaration(self, items):
        # Processed by variable_declaration or stack_declaration
        return items[0]

    # --- Functions ---
    @v_args(inline=True)
    def function_definition(self, type_spec, name_token, params, block):
        raise NotImplementedError("Function definitions are not yet supported.")

    def parameter_list(self, items):
        raise NotImplementedError("Function parameters are not yet supported.")

    @v_args(inline=True)
    def parameter(self, type_spec, name_token):
        raise NotImplementedError("Function parameters are not yet supported.")

    # --- Blocks and Statements ---
    def block(self, items):
        self._enter_scope()

        processed_statements = []
        for stmt in items:
            if stmt:  # Might get None from empty statements or comments
                processed_statements.append(stmt)

        def code_func(_statements=processed_statements) -> List[str]:
            c = []
            for stmt in _statements:
                c += stmt['code_func']()
            return c

        self._exit_scope()

        return {'op': 'block', 'statements': processed_statements, 'code_func': code_func}

    def statement(self, items):
        return items[0]

    # --- Declarations ---
    @v_args(inline=True)
    def variable_declaration(self, name_ir, initial_value_ir=None):
        name = name_ir['name']
        if self.current_scope.is_defined_locally(name):
            raise NameError(f"Variable '{name}' already defined in this scope.")

        symbol = Symbol(name, 'size_t', is_initialized=True)
        self.current_scope.define(symbol)

        if initial_value_ir:
            if initial_value_ir['code_func'] is None:
                raise ValueError("Variable declaration requires an code_func for initialization.")

            # Generate IR to assign initial value

            def code_func() -> List[str]:
                return initial_value_ir['code_func'](symbol.location)

            return {'op': 'var_decl', 'symbol': symbol, 'code_func': code_func}
        else:
            def code_func() -> List[str]:
                return self.brainfuck_assembler.set_cell_value(symbol.location, 0)

            return {'op': 'var_decl', 'symbol': symbol, 'code_func': code_func}

    @v_args(inline=True)
    def stack_declaration(self, type_spec, name_token, size_expr):
        raise NotImplementedError("Stack declarations are not yet supported.")

    # --- Statements ---
    @v_args(inline=True)
    def assignment(self, lvalue, expression):
        symbol = lvalue['symbol']
        var_name = symbol.name

        if not symbol:
            raise NameError(f"Variable '{var_name}' not defined.")
        if symbol.symbol_type != 'size_t':
            raise TypeError(f"Cannot assign to non-variable '{var_name}' (type: {symbol.symbol_type}).")

        if expression['code_func'] is None:
            raise ValueError("Assignment requires an code_func for the expression.")

        def code_func() -> List[str]:
            c = []
            c += expression['code_func'](symbol.location)
            return c

        return {'op': 'assign', 'symbol': symbol, 'code_func': code_func}

    @v_args(inline=True)
    def expression(self, expr_ir):
        return {'op': 'expr_stmt', 'expr_ir': expr_ir}

    def push_statement(self, items):
        raise NotImplementedError("Stack push statements are not yet supported.")

    def stack_pop(self, items):
        raise NotImplementedError("Stack pop statements are not yet supported.")

    # --- Control Flow (Placeholders) ---
    @v_args(inline=True)
    def if_statement(self, expression, then_block, else_block=None):

        def code_func() -> List[str]:
            c = []
            result_cell = self.memory_manager.get_temp_cell()
            temp_1 = self.memory_manager.get_temp_cell()
            temp_2 = self.memory_manager.get_temp_cell()
            c += expression['code_func'](result_cell)
            c += self.brainfuck_assembler.if_else(result_cell, then_block['code_func'], else_block['code_func'], temp_1,
                                                  temp_2)
            self.memory_manager.release_temp_cell(temp_2)
            self.memory_manager.release_temp_cell(temp_1)
            self.memory_manager.release_temp_cell(result_cell)
            return c

        return {'op': 'if', 'code_func': code_func}

    @v_args(inline=True)
    def while_statement(self, expression, then):

        def code_func() -> List[str]:
            c = []
            result_cell = self.memory_manager.get_temp_cell()
            c += self.brainfuck_assembler.loop_managed_func(expression['code_func'], then['code_func'], result_cell)
            self.memory_manager.release_temp_cell(result_cell)
            return c

        return {'op': 'while', 'code_func': code_func}

    def return_statement(self, items):
        raise NotImplementedError("Return statements are not yet supported.")

    # --- Expressions ---
    # Helper for mapping and executing binary operations
    def _bin_op_func(self, op, left_r: int, right_r: int, result_r: int) -> List[str]:
        code = []

        temp1 = self.memory_manager.get_temp_cell()
        temp2 = self.memory_manager.get_temp_cell()

        if op == '+':
            code += self.brainfuck_assembler.add_cells_unsigned(left_r, right_r, result_r, temp1, temp2)
            return code
        elif op == '-':
            code += self.brainfuck_assembler.subtract_cells_unsigned(left_r, right_r, result_r, temp1, temp2)
        elif op == '*':
            # TODO: Implement multiplication
            raise NotImplementedError("Multiplication not yet implemented.")
        elif op == '/':
            # TODO: Implement division
            raise NotImplementedError("Division not yet implemented.")
        elif op == '==':
            code += self.brainfuck_assembler.equals_unsigned(left_r, right_r, result_r, temp1, temp2)
        elif op == '!=':
            code += self.brainfuck_assembler.not_equals_unsigned(left_r, right_r, result_r, temp1, temp2)
        elif op == '>=':
            temp3 = self.memory_manager.get_temp_cell()
            temp4 = self.memory_manager.get_temp_cell()
            code += self.brainfuck_assembler.greater_than_or_equal_to_unsigned(left_r, right_r, result_r, temp1, temp2, temp3, temp4)
            self.memory_manager.release_temp_cell(temp4)
            self.memory_manager.release_temp_cell(temp3)
        elif op == '<=':
            temp3 = self.memory_manager.get_temp_cell()
            temp4 = self.memory_manager.get_temp_cell()
            code += self.brainfuck_assembler.less_than_or_equal_to_unsigned(left_r, right_r, result_r, temp1, temp2, temp3, temp4)
            self.memory_manager.release_temp_cell(temp4)
            self.memory_manager.release_temp_cell(temp3)
        elif op == '>':
            temp3 = self.memory_manager.get_temp_cell()
            temp4 = self.memory_manager.get_temp_cell()
            code += self.brainfuck_assembler.greater_than_unsigned(left_r, right_r, result_r, temp1, temp2, temp3, temp4)
            self.memory_manager.release_temp_cell(temp4)
            self.memory_manager.release_temp_cell(temp3)
        elif op == '<':
            temp3 = self.memory_manager.get_temp_cell()
            code += self.brainfuck_assembler.less_than_unsigned(left_r, right_r, result_r, temp1, temp2, temp3)
            self.memory_manager.release_temp_cell(temp3)
        else:
            self.memory_manager.release_temp_cell(temp2)
            self.memory_manager.release_temp_cell(temp1)
            raise ValueError(f"Unknown binary operation: {op}")

        self.memory_manager.release_temp_cell(temp2)
        self.memory_manager.release_temp_cell(temp1)
        return code

    # Helper for binary operations
    def _bin_op(self, items, op_map):
        left_ir = items[0]
        for i in range(1, len(items), 2):
            op = str(items[i])
            right_ir = items[i+1]

            # Fold if both sides are constants
            if left_ir['op'] == 'const' and right_ir['op'] == 'const':
                left_val = left_ir['value']
                right_val = right_ir['value']
                if op == '+':
                    result = left_val + right_val
                elif op == '-':
                    result = left_val - right_val
                elif op == '*':
                    result = left_val * right_val
                elif op == '/':
                    if right_val == 0: raise ZeroDivisionError("Division by constant zero.")
                    result = int(left_val / right_val)  # Integer division
                elif op == '==':
                    result = 1 if left_val == right_val else 0
                elif op == '!=':
                    result = 1 if left_val != right_val else 0
                elif op == '>=':
                    result = 1 if left_val >= right_val else 0
                elif op == '<=':
                    result = 1 if left_val <= right_val else 0
                elif op == '>':
                    result = 1 if left_val > right_val else 0
                elif op == '<':
                    result = 1 if left_val < right_val else 0
                else:
                    raise ValueError(f"Unknown binary operation: {op}")
                print(f"Transformer: Folded constant expression: {left_val} {op} {right_val} -> {result}")

                def code_func(result_cell) -> List[str]:
                    return self.brainfuck_assembler.set_cell_value(result_cell, result)

                left_ir = {'op': 'const', 'value': result, 'code_func': code_func}
                continue

            # Check that both sides have a code_func
            if left_ir['code_func'] is None or right_ir['code_func'] is None:
                raise ValueError("Binary operation requires code_func for both sides.")

            # Capture the *current* function references and the operator value
            current_left_func = left_ir['code_func']
            current_right_func = right_ir['code_func']
            current_op = op  # Capture the operator string

            # Define the code_func using default arguments to capture current values
            def code_func(result_cell,
                          _left=current_left_func,
                          _right=current_right_func,
                          _op_val=current_op) -> List[str]:
                c = []
                r1 = self.memory_manager.get_temp_cell()
                r2 = self.memory_manager.get_temp_cell()
                # Use the captured functions/values
                c += _left(r1)
                c += _right(r2)
                c += self._bin_op_func(_op_val, r1, r2, result_cell)
                self.memory_manager.release_temp_cell(r2)
                self.memory_manager.release_temp_cell(r1)
                return c

            left_ir = {
                'op': op_map.get(op, f'unknown_op_{op}'),
                'left_ir': left_ir,
                'right_ir': right_ir,
                'code_func': code_func
            }
        return left_ir

    def comparison(self, items):
        op_map = {
            "==": "cmp_eq", "!=": "cmp_ne", ">=": "cmp_ge",
            "<=": "cmp_le", ">": "cmp_gt", "<": "cmp_lt"
        }
        return self._bin_op(items, op_map)

    def arithmetic(self, items):
        op_map = {"+": "add", "-": "sub"}
        # Constant Folding Example
        if len(items) == 3 and items[0]['op'] == 'const' and items[2]['op'] == 'const':
            left_val = items[0]['value']
            right_val = items[2]['value']
            op = str(items[1])
            if op == '+':
                result = left_val + right_val
            elif op == '-':
                result = left_val - right_val
            else:
                return self._bin_op(items, op_map)  # Fallback if op unknown
            print(f"Transformer: Folded constant expression: {left_val} {op} {right_val} -> {result}")

            def code_func(result_cell) -> List[str]:
                return self.brainfuck_assembler.set_cell_value(result_cell, result)

            return {'op': 'const', 'value': result, 'code_func': code_func}

        return self._bin_op(items, op_map)

    def term(self, items):
        op_map = {"*": "mul", "/": "div"}
        # Constant Folding Example
        if len(items) == 3 and items[0]['op'] == 'const' and items[2]['op'] == 'const':
            left_val = items[0]['value']
            right_val = items[2]['value']
            op = str(items[1])
            if op == '*':
                result = left_val * right_val
            elif op == '/':
                if right_val == 0: raise ZeroDivisionError("Division by constant zero.")
                result = int(left_val / right_val)  # Integer division
            else:
                return self._bin_op(items, op_map)  # Fallback if op unknown
            print(f"Transformer: Folded constant expression: {left_val} {op} {right_val} -> {result}")

            def code_func(result_cell) -> List[str]:
                return self.brainfuck_assembler.set_cell_value(result_cell, result)

            return {'op': 'const', 'value': result, 'code_func': code_func}
        return self._bin_op(items, op_map)

    def factor(self, items):
        if len(items) == 2:  # Unary +/-
            op = str(items[0])
            operand_ir = items[1]
            # Constant Folding for Unary
            if operand_ir['op'] == 'const':
                value = operand_ir['value']
                result = -value if op == '-' else value
                print(f"Transformer: Folded unary expression: {op}{value} -> {result}")

                def code_func(result_cell) -> List[str]:
                    return self.brainfuck_assembler.set_cell_value(result_cell, result)

                return {'op': 'const', 'value': result, 'code_func': code_func}

            return {'op': 'unary_' + op, 'operand_ir': operand_ir}

        # Make sure Atom has a code_func
        if items[0]['code_func'] is None and items[0]['op'] == 'const':
            def code_func(result_cell) -> List[str]:
                return self.brainfuck_assembler.set_cell_value(result_cell, items[0]['value'])

            items[0]['code_func'] = code_func

        return items[0]  # atom

    def atom(self, items):
        # This directly returns the result of NUMBER, NAME, function_call, etc.
        return items[0]  # Already transformed by specific rules below

    # --- Specific Expression Components ---
    def NUMBER(self, token):
        def code_func(result_cell) -> List[str]:
            return self.brainfuck_assembler.set_cell_value(result_cell, int(token))

        return {'op': 'const', 'value': int(token), 'code_func': code_func}

    def CHARACTER(self, token):
        # token is 'c', we need ASCII value
        token_value = str(token)
        if len(token_value) == 3:
            token_value = token_value[1]  # Extract the character
        if len(token_value) != 1:
            raise ValueError(f"Invalid character literal: '{token_value}'")

        value = ord(token_value)

        def code_func(result_cell) -> List[str]:
            return self.brainfuck_assembler.set_cell_value(result_cell, value)

        return {'op': 'const', 'value': value, 'code_func': code_func}

    def NEW_NAME(self, token):
        return {'op': 'new_name', 'name': str(token)}

    def DECLARED_NAME(self, token):
        name = str(token)
        # Check defines first
        if name in self.defines:
            print(f"Transformer: Substituted define '{name}' with value {self.defines[name]}")

            define_value = None
            if self.defines[name].isdigit():
                define_value = int(self.defines[name])
            elif self.defines[name].startswith("'") and self.defines[name].endswith("'"):
                define_value = ord(self.defines[name][1])
            else:
                raise ValueError(f"Invalid define value: '{self.defines[name]}'")

            def code_func(result_cell) -> List[str]:
                return self.brainfuck_assembler.set_cell_value(result_cell, define_value)

            return {'op': 'const', 'value': define_value, 'code_func': code_func}

        # Look up variable/stack/function
        symbol = self.current_scope.lookup(name)
        if not symbol:
            raise NameError(f"Name '{name}' is not defined.")

        if symbol.symbol_type == 'size_t':

            def code_func(result_cell) -> List[str]:
                c = []
                temp = self.memory_manager.get_temp_cell()
                c += self.brainfuck_assembler.copy_cell_preserve_source(symbol.location, result_cell, temp)
                self.memory_manager.release_temp_cell(temp)
                return c

            return {'op': 'load_var', 'symbol': symbol, 'code_func': code_func}
        elif symbol.symbol_type == 'stack':
            # TODO: Implement stack access
            raise NotImplementedError("Stack access not yet implemented.")
        elif symbol.symbol_type == 'func':
            # TODO: Implement function call
            raise NotImplementedError("Function calls not yet implemented.")
        else:
            raise TypeError(f"Unhandled symbol type for '{name}': {symbol.symbol_type}")

    def function_call(self, items):
        # TODO: Implement function calls
        raise NotImplementedError("Function calls not yet implemented.")

    def argument_list(self, items):
        raise NotImplementedError("Function arguments are not yet supported.")

    def stack_peek(self, items):
        raise NotImplementedError("Stack peek expressions are not yet supported.")

    def stack_pop(self, items):
        raise NotImplementedError("Stack pop expressions are not yet supported.")

    # --- Terminals that need specific handling ---
    def STRING(self, s):
        # Used in #include, handled before transformation usually
        # If encountered elsewhere, treat as error or handle if needed
        raise TypeError("Strings are only supported in #include directives.")

    # Default fallback for rules not explicitly handled (if any)
    def __default__(self, data, children, meta):
        print(f"Warning: No specific transformer method for rule '{data}'. Defaulting.")
        # Potentially return children or raise error depending on strictness
        return children
