#!/usr/bin/env python3
"""
Python to Sui (粋) Transpiler (for humans)
Convert Python code to Sui
"""

import ast
import sys
from typing import Optional

def get_version() -> str:
    """Get package version"""
    try:
        from importlib.metadata import version
        return version("sui-lang")
    except Exception:
        return "0.4.1"


class Py2SuiTranspiler(ast.NodeVisitor):
    """Python to Sui transpiler"""

    def __init__(self):
        self.output: list[str] = []
        self.var_counter = 0
        self.label_counter = 0
        self.func_counter = 0
        self.var_map: dict[str, str] = {}  # Python var name -> Sui var
        self.func_map: dict[str, int] = {}  # Python func name -> Sui func id
        self.is_global = True
        self.func_args: list[str] = []  # Current function argument names

    def emit(self, line: str):
        """Emit a line of code"""
        self.output.append(line)

    def new_var(self) -> str:
        """Create a new local variable"""
        var = f"v{self.var_counter}"
        self.var_counter += 1
        return var

    def new_label(self) -> int:
        """Create a new label"""
        label = self.label_counter
        self.label_counter += 1
        return label

    def get_var(self, name: str) -> str:
        """Resolve a variable name"""
        # Function argument
        if name in self.func_args:
            return f"a{self.func_args.index(name)}"
        # Existing variable
        if name in self.var_map:
            return self.var_map[name]
        # New variable
        if self.is_global:
            var = f"g{len([v for v in self.var_map.values() if v.startswith('g')])}"
        else:
            var = self.new_var()
        self.var_map[name] = var
        return var

    def visit_expr(self, node: ast.expr) -> str:
        """Evaluate expression and return result variable"""
        if isinstance(node, ast.Constant):
            # Literal
            var = self.new_var()
            if isinstance(node.value, str):
                self.emit(f'= {var} "{node.value}"')
            else:
                self.emit(f"= {var} {node.value}")
            return var

        elif isinstance(node, ast.Name):
            return self.get_var(node.id)

        elif isinstance(node, ast.BinOp):
            left = self.visit_expr(node.left)
            right = self.visit_expr(node.right)
            result = self.new_var()

            op_map = {
                ast.Add: '+',
                ast.Sub: '-',
                ast.Mult: '*',
                ast.Div: '/',
                ast.FloorDiv: '/',
                ast.Mod: '%',
            }
            op = op_map.get(type(node.op), '+')
            self.emit(f"{op} {result} {left} {right}")
            return result

        elif isinstance(node, ast.Compare):
            left = self.visit_expr(node.left)
            result = self.new_var()

            for op, comparator in zip(node.ops, node.comparators):
                right = self.visit_expr(comparator)

                if isinstance(op, ast.Lt):
                    self.emit(f"< {result} {left} {right}")
                elif isinstance(op, ast.LtE):
                    # <= is < or ==
                    tmp1 = self.new_var()
                    tmp2 = self.new_var()
                    self.emit(f"< {tmp1} {left} {right}")
                    self.emit(f"~ {tmp2} {left} {right}")
                    self.emit(f"| {result} {tmp1} {tmp2}")
                elif isinstance(op, ast.Gt):
                    self.emit(f"> {result} {left} {right}")
                elif isinstance(op, ast.GtE):
                    tmp1 = self.new_var()
                    tmp2 = self.new_var()
                    self.emit(f"> {tmp1} {left} {right}")
                    self.emit(f"~ {tmp2} {left} {right}")
                    self.emit(f"| {result} {tmp1} {tmp2}")
                elif isinstance(op, ast.Eq):
                    self.emit(f"~ {result} {left} {right}")
                elif isinstance(op, ast.NotEq):
                    tmp = self.new_var()
                    self.emit(f"~ {tmp} {left} {right}")
                    self.emit(f"! {result} {tmp}")

                left = result

            return result

        elif isinstance(node, ast.UnaryOp):
            operand = self.visit_expr(node.operand)
            result = self.new_var()

            if isinstance(node.op, ast.Not):
                self.emit(f"! {result} {operand}")
            elif isinstance(node.op, ast.USub):
                self.emit(f"- {result} 0 {operand}")

            return result

        elif isinstance(node, ast.JoinedStr):
            # f-string: not supported
            print(f"⚠ Warning: f-strings are not supported. Use regular strings.", file=sys.stderr)
            result = self.new_var()
            self.emit(f"; Unsupported: f-string")
            self.emit(f"= {result} 0")
            return result

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id

                # print
                if func_name == 'print':
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):
                            # f-string warning
                            print(f"⚠ Warning: f-strings in print are not supported.", file=sys.stderr)
                            self.emit(f"; Unsupported: f-string in print")
                        else:
                            arg_var = self.visit_expr(arg)
                            self.emit(f". {arg_var}")
                    return self.new_var()

                # input
                if func_name == 'input':
                    result = self.new_var()
                    self.emit(f", {result}")
                    return result

                # len
                if func_name == 'len':
                    # Simplified implementation
                    result = self.new_var()
                    self.emit(f"= {result} 0")
                    return result

                # User-defined function
                if func_name in self.func_map:
                    func_id = self.func_map[func_name]
                    args = [self.visit_expr(arg) for arg in node.args]
                    result = self.new_var()
                    args_str = " ".join(args)
                    self.emit(f"$ {result} {func_id} {args_str}")
                    return result

            # Unknown function
            result = self.new_var()
            self.emit(f"= {result} 0")
            return result

        elif isinstance(node, ast.Subscript):
            arr = self.visit_expr(node.value)
            idx = self.visit_expr(node.slice)
            result = self.new_var()
            self.emit(f"] {result} {arr} {idx}")
            return result

        elif isinstance(node, ast.List):
            # List literal
            size = len(node.elts)
            result = self.new_var()
            self.emit(f"[ {result} {size}")
            for i, elt in enumerate(node.elts):
                val = self.visit_expr(elt)
                self.emit(f"{{ {result} {i} {val}")
            return result

        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = self.visit_expr(node.values[0])
                for val in node.values[1:]:
                    right = self.visit_expr(val)
                    new_result = self.new_var()
                    self.emit(f"& {new_result} {result} {right}")
                    result = new_result
                return result
            elif isinstance(node.op, ast.Or):
                result = self.visit_expr(node.values[0])
                for val in node.values[1:]:
                    right = self.visit_expr(val)
                    new_result = self.new_var()
                    self.emit(f"| {new_result} {result} {right}")
                    result = new_result
                return result

        # Default
        result = self.new_var()
        self.emit(f"= {result} 0")
        return result

    def visit_Assign(self, node: ast.Assign):
        """Assignment statement"""
        value = self.visit_expr(node.value)

        for target in node.targets:
            if isinstance(target, ast.Name):
                var = self.get_var(target.id)
                self.emit(f"= {var} {value}")
            elif isinstance(target, ast.Subscript):
                arr = self.visit_expr(target.value)
                idx = self.visit_expr(target.slice)
                self.emit(f"{{ {arr} {idx} {value}")

    def visit_AugAssign(self, node: ast.AugAssign):
        """Augmented assignment (+=, -= etc.)"""
        target = self.get_var(node.target.id)
        value = self.visit_expr(node.value)

        op_map = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
        }
        op = op_map.get(type(node.op), '+')
        self.emit(f"{op} {target} {target} {value}")

    def visit_If(self, node: ast.If):
        """If statement"""
        cond = self.visit_expr(node.test)

        if node.orelse:
            # if-else
            else_label = self.new_label()
            end_label = self.new_label()

            not_cond = self.new_var()
            self.emit(f"! {not_cond} {cond}")
            self.emit(f"? {not_cond} {else_label}")

            for stmt in node.body:
                self.visit(stmt)
            self.emit(f"@ {end_label}")

            self.emit(f": {else_label}")
            for stmt in node.orelse:
                self.visit(stmt)

            self.emit(f": {end_label}")
        else:
            # if only
            end_label = self.new_label()

            not_cond = self.new_var()
            self.emit(f"! {not_cond} {cond}")
            self.emit(f"? {not_cond} {end_label}")

            for stmt in node.body:
                self.visit(stmt)

            self.emit(f": {end_label}")

    def visit_While(self, node: ast.While):
        """While statement"""
        start_label = self.new_label()
        end_label = self.new_label()

        self.emit(f": {start_label}")
        cond = self.visit_expr(node.test)
        not_cond = self.new_var()
        self.emit(f"! {not_cond} {cond}")
        self.emit(f"? {not_cond} {end_label}")

        for stmt in node.body:
            self.visit(stmt)

        self.emit(f"@ {start_label}")
        self.emit(f": {end_label}")

    def visit_For(self, node: ast.For):
        """For statement (only range supported)"""
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == 'range':
                args = node.iter.args

                if len(args) == 1:
                    start, end = 0, args[0]
                elif len(args) == 2:
                    start, end = args[0], args[1]
                else:
                    start, end = args[0], args[1]

                # Loop variable
                loop_var = self.get_var(node.target.id)

                # Initialize
                if isinstance(start, int):
                    self.emit(f"= {loop_var} {start}")
                else:
                    start_val = self.visit_expr(start)
                    self.emit(f"= {loop_var} {start_val}")

                # End value
                end_val = self.visit_expr(end)

                start_label = self.new_label()
                end_label = self.new_label()

                self.emit(f": {start_label}")

                # Condition check
                cond = self.new_var()
                self.emit(f"< {cond} {loop_var} {end_val}")
                not_cond = self.new_var()
                self.emit(f"! {not_cond} {cond}")
                self.emit(f"? {not_cond} {end_label}")

                # Body
                for stmt in node.body:
                    self.visit(stmt)

                # Increment
                self.emit(f"+ {loop_var} {loop_var} 1")
                self.emit(f"@ {start_label}")
                self.emit(f": {end_label}")
                return

        raise NotImplementedError("Only range-based for loops are supported")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Function definition"""
        func_id = self.func_counter
        self.func_counter += 1
        self.func_map[node.name] = func_id

        argc = len(node.args.args)

        # Save context
        old_global = self.is_global
        old_var_counter = self.var_counter
        old_func_args = self.func_args
        old_var_map = self.var_map.copy()

        self.is_global = False
        self.var_counter = 0
        self.func_args = [arg.arg for arg in node.args.args]

        self.emit(f"# {func_id} {argc} {{")

        for stmt in node.body:
            self.visit(stmt)

        self.emit("}")

        # Restore context
        self.is_global = old_global
        self.var_counter = old_var_counter
        self.func_args = old_func_args
        self.var_map = old_var_map

    def visit_Return(self, node: ast.Return):
        """Return statement"""
        if node.value:
            value = self.visit_expr(node.value)
            self.emit(f"^ {value}")
        else:
            self.emit("^ 0")

    def visit_Expr(self, node: ast.Expr):
        """Expression statement"""
        self.visit_expr(node.value)

    def visit_Pass(self, node: ast.Pass):
        """Pass statement"""
        pass

    def visit_Module(self, node: ast.Module):
        """Module"""
        # Process function definitions first
        func_defs = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        other = [n for n in node.body if not isinstance(n, ast.FunctionDef)]

        for func in func_defs:
            self.visit(func)

        for stmt in other:
            self.visit(stmt)

    def transpile(self, code: str) -> str:
        """Transpile Python code to Sui"""
        tree = ast.parse(code)
        self.visit(tree)
        return '\n'.join(self.output)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ('--version', '-V'):
        print(f"sui-lang {get_version()}")
        return
    
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Python to Sui (粋) Transpiler (for humans)")
        print("=" * 50)
        print("")
        print("Usage:")
        print("  py2sui <file.py>            # Show converted code")
        print("  py2sui <file.py> -o out.sui # Output to file")
        print("  py2sui --version            # Show version")
        print("")
        print("Sample:")
        print("-" * 50)

        sample = '''
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = fibonacci(10)
print(result)
'''
        print("Python:")
        print(sample.strip())
        print("")
        print("Sui:")
        transpiler = Py2SuiTranspiler()
        result = transpiler.transpile(sample)
        print(result)
        print("")
        print("-" * 50)

        sample2 = '''
x = 0
while x < 10:
    print(x)
    x = x + 1
'''
        print("Python:")
        print(sample2.strip())
        print("")
        print("Sui:")
        transpiler = Py2SuiTranspiler()
        result = transpiler.transpile(sample2)
        print(result)
        return

    filename = sys.argv[1]

    with open(filename, 'r') as f:
        code = f.read()

    transpiler = Py2SuiTranspiler()
    sui_code = transpiler.transpile(code)

    if '-o' in sys.argv:
        out_idx = sys.argv.index('-o')
        out_file = sys.argv[out_idx + 1]
        with open(out_file, 'w') as f:
            f.write(sui_code)
        print(f"✓ Output saved to {out_file}")
    else:
        print(sui_code)


if __name__ == '__main__':
    main()
