#!/usr/bin/env python3
"""
Sui (粋) Interpreter
A line-based programming language optimized for LLM code generation
"""

import sys
from dataclasses import dataclass, field
from typing import Any, Optional
from repl import run_repl


@dataclass
class Function:
    """Function definition"""
    id: int
    arg_count: int
    body: list[str]


@dataclass
class Context:
    """Execution context"""
    local_vars: dict = field(default_factory=dict)
    args: list = field(default_factory=list)
    return_value: Any = None
    returned: bool = False


class SuiInterpreter:
    """Sui language interpreter"""

    def __init__(self):
        self.global_vars: dict[int, Any] = {}
        self.functions: dict[int, Function] = {}
        self.context_stack: list[Context] = []
        self.context: Context = Context()
        self.output: list = []

    def parse(self, code: str) -> list[list[str]]:
        """
        Parse code into token lists
        Each line becomes [instruction, arg1, arg2, ...]
        """
        lines = []
        for line in code.strip().split('\n'):
            # Remove comments
            if ';' in line:
                line = line[:line.index(';')]
            line = line.strip()
            if not line:
                continue

            # Tokenize (preserving string literals)
            tokens = self._tokenize_line(line)
            if tokens:
                lines.append(tokens)

        return lines

    def _tokenize_line(self, line: str) -> list[str]:
        """Tokenize a line while preserving string literals"""
        tokens = []
        i = 0
        while i < len(line):
            # Skip whitespace
            if line[i] in ' \t':
                i += 1
                continue

            # String literal
            if line[i] == '"':
                j = i + 1
                while j < len(line) and line[j] != '"':
                    if line[j] == '\\':
                        j += 2
                    else:
                        j += 1
                tokens.append(line[i:j + 1])
                i = j + 1
                continue

            # Regular token
            j = i
            while j < len(line) and line[j] not in ' \t':
                j += 1
            tokens.append(line[i:j])
            i = j

        return tokens

    def collect_functions(self, lines: list[list[str]]):
        """Collect function definitions"""
        i = 0
        while i < len(lines):
            tokens = lines[i]

            if tokens[0] == '#':
                # # func_id arg_count {
                func_id = int(tokens[1])
                arg_count = int(tokens[2])

                # Collect function body until }
                body = []
                i += 1
                depth = 1

                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#' and '{' in lines[i]:
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    body.append(lines[i])
                    i += 1

                self.functions[func_id] = Function(func_id, arg_count, body)

            i += 1

    def resolve(self, val: str) -> Any:
        """Resolve a value"""
        if val.startswith('v'):
            return self.context.local_vars.get(int(val[1:]), 0)
        elif val.startswith('g'):
            return self.global_vars.get(int(val[1:]), 0)
        elif val.startswith('a'):
            idx = int(val[1:])
            return self.context.args[idx] if idx < len(self.context.args) else 0
        elif val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        elif '.' in val:
            return float(val)
        else:
            try:
                return int(val)
            except ValueError:
                return val

    def assign(self, var: str, value: Any):
        """Assign a value to a variable"""
        if var.startswith('v'):
            self.context.local_vars[int(var[1:])] = value
        elif var.startswith('g'):
            self.global_vars[int(var[1:])] = value

    def execute_line(self, tokens: list[str]) -> tuple[bool, Optional[int]]:
        """
        Execute a single line
        Returns: (should_continue, jump_label or None)
        """
        if not tokens:
            return True, None

        op = tokens[0]

        # Block boundaries (except array write)
        if op == '}':
            return True, None
        if op == '{' and len(tokens) < 4:
            # Not enough args = block start
            return True, None

        # Skip function definitions (already collected)
        if op == '#':
            return True, None

        if op == '=':
            # Assignment: = var value
            self.assign(tokens[1], self.resolve(tokens[2]))

        elif op == '+':
            # Addition: + result a b
            self.assign(tokens[1], self.resolve(tokens[2]) + self.resolve(tokens[3]))

        elif op == '-':
            # Subtraction: - result a b
            self.assign(tokens[1], self.resolve(tokens[2]) - self.resolve(tokens[3]))

        elif op == '*':
            # Multiplication: * result a b
            self.assign(tokens[1], self.resolve(tokens[2]) * self.resolve(tokens[3]))

        elif op == '/':
            # Division: / result a b
            self.assign(tokens[1], self.resolve(tokens[2]) / self.resolve(tokens[3]))

        elif op == '%':
            # Modulo: % result a b
            self.assign(tokens[1], self.resolve(tokens[2]) % self.resolve(tokens[3]))

        elif op == '<':
            # Less than: < result a b
            result = 1 if self.resolve(tokens[2]) < self.resolve(tokens[3]) else 0
            self.assign(tokens[1], result)

        elif op == '>':
            # Greater than: > result a b
            result = 1 if self.resolve(tokens[2]) > self.resolve(tokens[3]) else 0
            self.assign(tokens[1], result)

        elif op == '~':
            # Equality: ~ result a b
            result = 1 if self.resolve(tokens[2]) == self.resolve(tokens[3]) else 0
            self.assign(tokens[1], result)

        elif op == '!':
            # NOT: ! result a
            result = 0 if self.resolve(tokens[2]) else 1
            self.assign(tokens[1], result)

        elif op == '&':
            # AND: & result a b
            result = 1 if self.resolve(tokens[2]) and self.resolve(tokens[3]) else 0
            self.assign(tokens[1], result)

        elif op == '|':
            # OR: | result a b
            result = 1 if self.resolve(tokens[2]) or self.resolve(tokens[3]) else 0
            self.assign(tokens[1], result)

        elif op == '?':
            # Conditional jump: ? cond label
            if self.resolve(tokens[1]):
                return True, int(tokens[2])

        elif op == '@':
            # Unconditional jump: @ label
            return True, int(tokens[1])

        elif op == ':':
            # Label definition: : label
            pass

        elif op == '$':
            # Function call: $ result func_id args...
            result_var = tokens[1]
            func_id = int(tokens[2])
            call_args = [self.resolve(a) for a in tokens[3:]]

            if func_id in self.functions:
                func = self.functions[func_id]

                # Save context
                self.context_stack.append(self.context)
                self.context = Context(args=call_args)

                # Execute function
                self.execute_block(func.body)

                # Get return value
                return_val = self.context.return_value

                # Restore context
                self.context = self.context_stack.pop()

                # Store result
                self.assign(result_var, return_val)

        elif op == '^':
            # Return: ^ value
            self.context.return_value = self.resolve(tokens[1])
            self.context.returned = True
            return False, None

        elif op == '[':
            # Array create: [ var size
            size = int(self.resolve(tokens[2]))
            self.assign(tokens[1], [0] * size)

        elif op == ']':
            # Array read: ] result arr idx
            arr = self.resolve(tokens[2])
            idx = int(self.resolve(tokens[3]))
            self.assign(tokens[1], arr[idx] if idx < len(arr) else 0)

        elif op == '{':
            # Array write: { arr idx value
            if len(tokens) >= 4:
                arr = self.resolve(tokens[1])
                idx = int(self.resolve(tokens[2]))
                if isinstance(arr, list) and idx < len(arr):
                    arr[idx] = self.resolve(tokens[3])

        elif op == '.':
            # Output: . value
            val = self.resolve(tokens[1])
            self.output.append(val)
            print(val)

        elif op == ',':
            # Input: , var
            val = input()
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            self.assign(tokens[1], val)

        return True, None

    def execute_block(self, lines: list[list[str]]):
        """Execute a block of instructions"""
        # Collect label positions
        labels = {}
        for i, tokens in enumerate(lines):
            if tokens and tokens[0] == ':':
                labels[int(tokens[1])] = i

        i = 0
        while i < len(lines):
            if self.context.returned:
                break

            cont, jump_label = self.execute_line(lines[i])

            if not cont:
                break

            if jump_label is not None and jump_label in labels:
                i = labels[jump_label]
            else:
                i += 1

    def run(self, code: str, args: list = None) -> list:
        """
        Execute code
        args: Command-line arguments (accessible as g100=argc, g101=argv[0], ...)
        """
        self.output = []
        self.global_vars = {}
        self.functions = {}
        self.context = Context()
        self.context_stack = []

        # Set command-line arguments as global variables
        # g100 = argc (number of arguments)
        # g101, g102, ... = argv[0], argv[1], ...
        if args:
            self.global_vars[100] = len(args)
            for i, arg in enumerate(args):
                try:
                    self.global_vars[101 + i] = int(arg)
                except ValueError:
                    try:
                        self.global_vars[101 + i] = float(arg)
                    except ValueError:
                        self.global_vars[101 + i] = arg
        else:
            self.global_vars[100] = 0

        lines = self.parse(code)

        # Collect function definitions
        self.collect_functions(lines)

        # Execute non-function code
        main_lines = []
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                # Skip function definition
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#' and len(lines[i]) > 3 and lines[i][-1] == '{':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                    i += 1
            else:
                main_lines.append(lines[i])
                i += 1

        self.execute_block(main_lines)

        return self.output


    def run_snippet(self, code: str) -> list:
        """
        Execute code without resetting interpreter/global state (for REPL use).
        """
        # Keep vars/functions as-is, but clear transient state
        self.output = []
        self.context.returned = False
        self.context.return_value = None
        self.context_stack = []

        lines = self.parse(code)

        # Update/collect any new function definitions
        self.collect_functions(lines)

        # Execute non-function code
        main_lines = []
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                depth = 1
                i += 1
                while i < len(lines) and depth > 0:
                    if lines[i][0] == '#' and len(lines[i]) > 3 and lines[i][-1] == '{':
                        depth += 1
                    elif lines[i][0] == '}':
                        depth -= 1
                    i += 1
            else:
                main_lines.append(lines[i])
                i += 1

        self.execute_block(main_lines)
        return self.output


def validate_line(line: str) -> tuple[bool, str]:
    """
    Validate a single line
    Returns: (is_valid, error_message)
    """
    if not line.strip() or line.strip().startswith(';'):
        return True, ""

    tokens = line.strip().split()
    if not tokens:
        return True, ""

    op = tokens[0]

    # Valid instructions and their minimum argument counts
    valid_ops = {
        '=': 2, '+': 3, '-': 3, '*': 3, '/': 3, '%': 3,
        '<': 3, '>': 3, '~': 3, '!': 2, '&': 3, '|': 3,
        '?': 2, '@': 1, ':': 1, '^': 1, '.': 1, ',': 1,
        '[': 2, ']': 3, '{': 3, '}': 0, '#': 3, '$': 2
    }

    # Check if instruction is valid
    if op not in valid_ops:
        return False, f"Unknown instruction: '{op}'"

    # Special case: function definition
    if op == '#':
        if len(tokens) < 4 or tokens[-1] != '{':
            return False, "Function definition must be '# id argc {'"
        return True, ""

    # Special case: function call (variable args)
    if op == '$':
        if len(tokens) < 3:
            return False, "'$' requires at least result and function id"
        return True, ""

    # Check argument count
    expected = valid_ops[op]
    actual = len(tokens) - 1
    if actual < expected:
        return False, f"'{op}' requires {expected} arguments, got {actual}"

    return True, ""


def _print_help():
    print("Sui (粋) - Programming Language for LLMs")
    print("=" * 50)
    print("")
    print("Usage:")
    print("  sui                 # Start REPL (default when no args)")
    print("  sui <file.sui> [args...]")
    print("  sui --help          # Show this help")
    print("  sui --repl          # Force REPL mode")
    print("  sui --validate <file.sui>")
    print("")
    print("Argument access:")
    print("  g100 = argument count (argc)")
    print("  g101 = first argument")
    print("  g102 = second argument")
    print("  ...")
    print("")
    print("Sample execution:")
    print("-" * 50)

    # Fibonacci sample
    fib_code = """
; Fibonacci function
# 0 1 {
  < v0 a0 2
  ! v1 v0
  ? v1 1
  ^ a0
  : 1
  - v2 a0 1
  $ v3 0 v2
  - v4 a0 2
  $ v5 0 v4
  + v6 v3 v5
  ^ v6
}

; Main
= g0 10
$ g1 0 g0
. g1
"""

    print("Sui (Fibonacci):")
    print(fib_code.strip())
    print("")
    print("Result:")
    interp = SuiInterpreter()
    interp.run(fib_code)

    print("")
    print("-" * 50)

    # Loop sample
    loop_code = """
= v0 0
: 0
< v1 v0 10
! v2 v1
? v2 1
. v0
+ v0 v0 1
@ 0
: 1
"""

    print("Sui (0-9 Loop):")
    print(loop_code.strip())
    print("")
    print("Result:")
    interp = SuiInterpreter()
    interp.run(loop_code)
    print("")
    print("-" * 50)


def main():
    args = sys.argv[1:]
    if not args:
        run_repl()
        return
    if args[0] in ('--repl', '-i'):
        run_repl()
        return

    if args[0] in ('--help', '-h'):
        _print_help()
        return

    if args[0] == '--validate':
        # Validation mode
        with open(args[1], 'r') as f:
            code = f.read()

        errors = []
        for i, line in enumerate(code.split('\n'), 1):
            valid, msg = validate_line(line)
            if not valid:
                errors.append(f"Line {i}: {msg}")

        if errors:
            print("Validation errors:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        else:
            print("✓ Validation successful")
            return

    # Unknown option -> fallback to help
    if args[0].startswith('-'):
        print(f"Unknown option: {args[0]}", file=sys.stderr)
        _print_help()
        sys.exit(1)

    # Execution mode
    with open(args[0], 'r') as f:
        code = f.read()

    # Pass additional arguments to the program
    program_args = args[1:]

    interp = SuiInterpreter()
    interp.run(code, args=program_args)


if __name__ == '__main__':
    main()
