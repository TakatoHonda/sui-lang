#!/usr/bin/env python3
"""
Sui (粋) to Python Transpiler
Convert Sui code to Python code
"""

import sys
from typing import Union

def get_version() -> str:
    """Get package version"""
    try:
        from importlib.metadata import version
        return version("sui-lang")
    except Exception:
        return "0.4.1"


class Sui2PyTranspiler:
    """Sui to Python transpiler"""

    def __init__(self):
        self.indent = 0
        self.output: list[str] = []
        self.functions: dict[int, dict] = {}

    def emit(self, line: str):
        """Emit a line of code with proper indentation"""
        self.output.append("    " * self.indent + line)

    def parse_line(self, line: str) -> list[str] | None:
        """Parse a single line"""
        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]
        line = line.strip()
        if not line:
            return None
        return line.split()

    def resolve_value(self, val: str) -> str:
        """Convert a value to Python expression"""
        if val.startswith('v') or val.startswith('g') or val.startswith('a') or val.startswith('c'):
            return val
        elif val.startswith('"'):
            return val
        else:
            return val

    def transpile_block(self, lines: list[list[str]], is_function: bool = False):
        """
        Transpile a block of instructions
        Uses state machine pattern for labels/jumps
        """
        # Collect labels
        labels = set()
        for tokens in lines:
            if tokens and tokens[0] == ':':
                labels.add(int(tokens[1]))

        # Use state machine pattern if labels exist
        if labels:
            self.emit("_state = -1")
            self.emit("while True:")
            self.indent += 1
            self.emit("_state += 1")

            # Map labels to state numbers
            state_map = {-1: 0}
            state_num = 1

            for label in sorted(labels):
                state_map[label] = state_num
                state_num += 1

            # Group instructions by state
            states: dict[int, list] = {0: []}
            current = 0

            for tokens in lines:
                if tokens[0] == ':':
                    label_id = int(tokens[1])
                    current = state_map[label_id]
                    if current not in states:
                        states[current] = []
                elif tokens[0] == '}':
                    continue
                else:
                    if current not in states:
                        states[current] = []
                    states[current].append(tokens)

            # Generate code for each state
            for state_id in sorted(states.keys()):
                self.emit(f"if _state == {state_id}:")
                self.indent += 1

                state_lines = states[state_id]
                if not state_lines:
                    self.emit("pass")
                else:
                    for tokens in state_lines:
                        self.transpile_instruction(tokens, state_map, is_function)

                # State transition
                if state_lines and state_lines[-1][0] not in ['?', '@', '^']:
                    next_state = state_id + 1
                    if next_state in states:
                        self.emit(f"_state = {next_state} - 1")
                        self.emit("continue")
                    else:
                        self.emit("break")
                elif not state_lines:
                    self.emit("break")

                self.indent -= 1

            self.emit("break")
            self.indent -= 1
        else:
            # Simple case: no labels
            for tokens in lines:
                if tokens[0] != '}':
                    self.transpile_instruction(tokens, {}, is_function)

    def transpile_instruction(self, tokens: list[str], state_map: dict, is_function: bool = False):
        """Transpile a single instruction"""
        if not tokens:
            return

        op = tokens[0]

        if op == '=':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])}")

        elif op == '+':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])} + {self.resolve_value(tokens[3])}")

        elif op == '-':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])} - {self.resolve_value(tokens[3])}")

        elif op == '*':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])} * {self.resolve_value(tokens[3])}")

        elif op == '/':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])} / {self.resolve_value(tokens[3])}")

        elif op == '%':
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])} % {self.resolve_value(tokens[3])}")

        elif op == '<':
            self.emit(f"{tokens[1]} = 1 if {self.resolve_value(tokens[2])} < {self.resolve_value(tokens[3])} else 0")

        elif op == '>':
            self.emit(f"{tokens[1]} = 1 if {self.resolve_value(tokens[2])} > {self.resolve_value(tokens[3])} else 0")

        elif op == '~':
            self.emit(f"{tokens[1]} = 1 if {self.resolve_value(tokens[2])} == {self.resolve_value(tokens[3])} else 0")

        elif op == '!':
            self.emit(f"{tokens[1]} = 0 if {self.resolve_value(tokens[2])} else 1")

        elif op == '&':
            self.emit(f"{tokens[1]} = 1 if ({self.resolve_value(tokens[2])} and {self.resolve_value(tokens[3])}) else 0")

        elif op == '|':
            self.emit(f"{tokens[1]} = 1 if ({self.resolve_value(tokens[2])} or {self.resolve_value(tokens[3])}) else 0")

        elif op == '?':
            # Conditional jump
            cond = self.resolve_value(tokens[1])
            label = int(tokens[2])
            if label in state_map:
                self.emit(f"if {cond}:")
                self.indent += 1
                self.emit(f"_state = {state_map[label]} - 1")
                self.emit("continue")
                self.indent -= 1

        elif op == '@':
            # Unconditional jump
            label = int(tokens[1])
            if label in state_map:
                self.emit(f"_state = {state_map[label]} - 1")
                self.emit("continue")

        elif op == ':':
            # Label (handled by state machine)
            pass

        elif op == '$':
            # Function call
            result = tokens[1]
            func_id = tokens[2]
            args = ", ".join(self.resolve_value(a) for a in tokens[3:])
            self.emit(f"{result} = f{func_id}({args})")

        elif op == '^':
            # Return
            self.emit(f"return {self.resolve_value(tokens[1])}")

        elif op == '[':
            # Array create
            self.emit(f"{tokens[1]} = [0] * {self.resolve_value(tokens[2])}")

        elif op == ']':
            # Array read
            self.emit(f"{tokens[1]} = {self.resolve_value(tokens[2])}[int({self.resolve_value(tokens[3])})]")

        elif op == '{':
            # Array write
            if len(tokens) >= 4:
                self.emit(f"{self.resolve_value(tokens[1])}[int({self.resolve_value(tokens[2])})] = {self.resolve_value(tokens[3])}")

        elif op == '.':
            # Output
            self.emit(f"print({self.resolve_value(tokens[1])})")

        elif op == ',':
            # Input
            self.emit(f"_input = input()")
            self.emit(f"try:")
            self.indent += 1
            self.emit(f"{tokens[1]} = int(_input)")
            self.indent -= 1
            self.emit(f"except ValueError:")
            self.indent += 1
            self.emit(f"{tokens[1]} = _input")
            self.indent -= 1

        elif op == '#':
            # Function definition (handled separately)
            pass

        elif op == '}':
            # Block end
            pass

    def transpile(self, code: str, args: list[str] = None) -> str:
        """Transpile Sui code to Python"""
        self.output = []
        lines_raw = code.strip().split('\n')
        lines = []

        for line in lines_raw:
            parsed = self.parse_line(line)
            if parsed:
                lines.append(parsed)

        # Collect function definitions
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                func_id = int(lines[i][1])
                argc = int(lines[i][2])

                # Collect function body
                body = []
                i += 1
                depth = 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    body.append(lines[i])
                    i += 1

                self.functions[func_id] = {'argc': argc, 'body': body}
            i += 1

        # Output header
        self.emit("#!/usr/bin/env python3")
        self.emit("# Auto-generated from Sui")
        self.emit("")

        # Initialize command-line arguments (c0 = argc, c1+ = argv)
        self.emit("# Command-line arguments (read-only)")
        self.emit("import sys")
        self.emit("c0 = len(sys.argv) - 1")
        self.emit("for _i, _arg in enumerate(sys.argv[1:]):")
        self.indent += 1
        self.emit("try:")
        self.indent += 1
        self.emit("globals()[f'c{1 + _i}'] = int(_arg)")
        self.indent -= 1
        self.emit("except ValueError:")
        self.indent += 1
        self.emit("globals()[f'c{1 + _i}'] = _arg")
        self.indent -= 1
        self.indent -= 1
        self.emit("")

        # Output function definitions
        for func_id, func_info in sorted(self.functions.items()):
            argc = func_info['argc']
            body = func_info['body']

            args_str = ", ".join(f"a{i}" for i in range(argc))
            self.emit(f"def f{func_id}({args_str}):")
            self.indent += 1

            if body:
                self.transpile_block(body, is_function=True)
            else:
                self.emit("pass")

            self.indent -= 1
            self.emit("")

        # Output main code
        self.emit("# Main")
        main_lines = []
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                # Skip function definition
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                    i += 1
            else:
                main_lines.append(lines[i])
                i += 1

        if main_lines:
            self.transpile_block(main_lines)
        else:
            self.emit("pass")

        return '\n'.join(self.output)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ('--version', '-V'):
        print(f"sui-lang {get_version()}")
        return
    
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Sui (粋) to Python Transpiler")
        print("=" * 50)
        print("")
        print("Usage:")
        print("  sui2py <file.sui>           # Show converted code")
        print("  sui2py <file.sui> -o out.py # Output to file")
        print("  sui2py <file.sui> --run     # Convert and execute")
        print("  sui2py --version            # Show version")
        print("")
        print("Sample:")
        print("-" * 50)

        sample = """
= v0 10
+ v1 v0 5
. v1
"""
        print("Sui:")
        print(sample.strip())
        print("")
        print("Python:")
        transpiler = Sui2PyTranspiler()
        result = transpiler.transpile(sample)
        print(result)
        return

    filename = sys.argv[1]

    with open(filename, 'r') as f:
        code = f.read()

    transpiler = Sui2PyTranspiler()
    python_code = transpiler.transpile(code)

    if '-o' in sys.argv:
        # Output to file
        out_idx = sys.argv.index('-o')
        out_file = sys.argv[out_idx + 1]
        with open(out_file, 'w') as f:
            f.write(python_code)
        print(f"✓ Output saved to {out_file}")

    elif '--run' in sys.argv:
        # Convert and execute
        run_idx = sys.argv.index('--run')
        run_args = sys.argv[run_idx + 1:]

        import sys as sys_module
        old_argv = sys_module.argv
        sys_module.argv = [filename] + run_args

        exec(python_code, {'__name__': '__main__'})

        sys_module.argv = old_argv

    else:
        # Output to stdout
        print(python_code)


if __name__ == '__main__':
    main()
