#!/usr/bin/env python3
"""
Sui to WebAssembly Compiler

Compiles Sui code to WebAssembly Text Format (WAT) and binary (.wasm).
"""

import sys
import subprocess
import tempfile
import os
from typing import Optional

def get_version() -> str:
    """Get package version"""
    try:
        from importlib.metadata import version
        return version("sui-lang")
    except Exception:
        return "0.4.1"


class Sui2WatTranspiler:
    """Sui to WAT transpiler"""

    def __init__(self):
        self.output: list[str] = []
        self.indent = 0
        self.functions: dict[int, dict] = {}
        self.used_globals: set[int] = set()
        self.used_cmd_args: set[int] = set()  # Command-line arguments (c0, c1, ...)
        self.use_memory = False

    def emit(self, line: str):
        """Emit a line with proper indentation"""
        self.output.append("  " * self.indent + line)

    def parse_line(self, line: str) -> list[str] | None:
        """Parse a single line"""
        if ';' in line:
            line = line[:line.index(';')]
        line = line.strip()
        if not line:
            return None
        
        tokens = []
        i = 0
        while i < len(line):
            if line[i] in ' \t':
                i += 1
                continue
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
            j = i
            while j < len(line) and line[j] not in ' \t':
                j += 1
            tokens.append(line[i:j])
            i = j
        return tokens if tokens else None

    def collect_info(self, lines: list[list[str]]):
        """Collect used variables and check if memory is needed"""
        for tokens in lines:
            if not tokens:
                continue
            op = tokens[0]
            if op in ['[', ']', '{']:
                self.use_memory = True
            for token in tokens[1:]:
                if token.startswith('g'):
                    try:
                        self.used_globals.add(int(token[1:]))
                    except ValueError:
                        pass
                elif token.startswith('c'):
                    try:
                        self.used_cmd_args.add(int(token[1:]))
                    except ValueError:
                        pass

    def resolve_value(self, val: str) -> str:
        """Resolve a value to WAT code"""
        if val.startswith('v'):
            idx = int(val[1:])
            return f"(local.get $v{idx})"
        elif val.startswith('g'):
            idx = int(val[1:])
            return f"(global.get $g{idx})"
        elif val.startswith('a'):
            idx = int(val[1:])
            return f"(local.get $a{idx})"
        elif val.startswith('c'):
            # Command-line arguments (read-only globals)
            idx = int(val[1:])
            return f"(global.get $c{idx})"
        elif val.startswith('"'):
            return "(i32.const 0)"
        elif '.' in val:
            return f"(i32.const {int(float(val))})"
        else:
            try:
                return f"(i32.const {int(val)})"
            except ValueError:
                return "(i32.const 0)"

    def set_var(self, var: str) -> str:
        """Generate WAT instruction to set a variable"""
        if var.startswith('v'):
            idx = int(var[1:])
            return f"(local.set $v{idx})"
        elif var.startswith('g'):
            idx = int(var[1:])
            return f"(global.set $g{idx})"
        elif var.startswith('c'):
            # Command-line arguments are read-only, ignore writes
            return ""
        return ""

    def transpile_block(self, lines: list[list[str]], local_vars: set[int], is_function: bool = False) -> list[str]:
        """Transpile a block using state machine pattern for labels/jumps"""
        result = []
        
        labels: set[int] = set()
        for tokens in lines:
            if tokens and tokens[0] == ':':
                labels.add(int(tokens[1]))

        if labels:
            state_map: dict[int, int] = {}
            state_num = 1
            for label in sorted(labels):
                state_map[label] = state_num
                state_num += 1

            states: dict[int, list] = {0: []}
            current_state = 0
            
            for tokens in lines:
                if not tokens:
                    continue
                if tokens[0] == ':':
                    label_id = int(tokens[1])
                    current_state = state_map[label_id]
                    if current_state not in states:
                        states[current_state] = []
                elif tokens[0] == '}':
                    continue
                else:
                    if current_state not in states:
                        states[current_state] = []
                    states[current_state].append(tokens)

            result.append("(local $_state i32)")
            result.append("(local.set $_state (i32.const 0))")
            result.append("(block $exit")
            result.append("  (loop $loop")
            
            for state_id in sorted(states.keys()):
                result.append(f"    ;; State {state_id}")
                result.append(f"    (if (i32.eq (local.get $_state) (i32.const {state_id}))")
                result.append("      (then")
                
                state_lines = states[state_id]
                has_jump = False
                
                for tokens in state_lines:
                    if tokens[0] == '?':
                        cond_code = self.resolve_value(tokens[1])
                        target_label = int(tokens[2])
                        target_state = state_map.get(target_label, 0)
                        result.append(f"        {cond_code}")
                        result.append(f"        (if")
                        result.append(f"          (then")
                        result.append(f"            (local.set $_state (i32.const {target_state}))")
                        result.append(f"            (br $loop)")
                        result.append(f"          )")
                        result.append(f"        )")
                    elif tokens[0] == '@':
                        target_label = int(tokens[1])
                        target_state = state_map.get(target_label, 0)
                        result.append(f"        (local.set $_state (i32.const {target_state}))")
                        result.append(f"        (br $loop)")
                        has_jump = True
                    elif tokens[0] == '^':
                        val_code = self.resolve_value(tokens[1])
                        result.append(f"        {val_code}")
                        result.append(f"        (return)")
                        has_jump = True
                    elif tokens[0] == '$':
                        result_var = tokens[1]
                        func_id = tokens[2]
                        args = tokens[3:]
                        for arg in args:
                            result.append(f"        {self.resolve_value(arg)}")
                        result.append(f"        (call $f{func_id})")
                        result.append(f"        {self.set_var(result_var)}")
                    else:
                        insts = self.transpile_instruction(tokens)
                        for inst in insts:
                            result.append(f"        {inst}")
                
                if not has_jump:
                    next_state = state_id + 1
                    if next_state in states:
                        result.append(f"        (local.set $_state (i32.const {next_state}))")
                        result.append(f"        (br $loop)")
                    else:
                        result.append(f"        (br $exit)")
                
                result.append("      )")
                result.append("    )")
            
            result.append("    (br $exit)")
            result.append("  )")
            result.append(")")
        else:
            for tokens in lines:
                if not tokens or tokens[0] == '}':
                    continue
                if tokens[0] == '^':
                    val_code = self.resolve_value(tokens[1])
                    result.append(val_code)
                    result.append("(return)")
                elif tokens[0] == '$':
                    result_var = tokens[1]
                    func_id = tokens[2]
                    args = tokens[3:]
                    for arg in args:
                        result.append(self.resolve_value(arg))
                    result.append(f"(call $f{func_id})")
                    result.append(self.set_var(result_var))
                else:
                    insts = self.transpile_instruction(tokens)
                    for inst in insts:
                        result.append(inst)

        return result

    def transpile_instruction(self, tokens: list[str]) -> list[str]:
        """Transpile a single instruction to WAT"""
        if not tokens:
            return []
        
        op = tokens[0]
        result = []

        if op == '=':
            val_code = self.resolve_value(tokens[2])
            result.append(val_code)
            result.append(self.set_var(tokens[1]))

        elif op in ['+', '-', '*', '/', '%']:
            a_code = self.resolve_value(tokens[2])
            b_code = self.resolve_value(tokens[3])
            op_map = {'+': 'i32.add', '-': 'i32.sub', '*': 'i32.mul', '/': 'i32.div_s', '%': 'i32.rem_s'}
            result.append(a_code)
            result.append(b_code)
            result.append(f"({op_map[op]})")
            result.append(self.set_var(tokens[1]))

        elif op == '<':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.lt_s)")
            result.append(self.set_var(tokens[1]))

        elif op == '>':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.gt_s)")
            result.append(self.set_var(tokens[1]))

        elif op == '~':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.eq)")
            result.append(self.set_var(tokens[1]))

        elif op == '!':
            result.append(self.resolve_value(tokens[2]))
            result.append("(i32.eqz)")
            result.append(self.set_var(tokens[1]))

        elif op == '&':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.and)")
            result.append(self.set_var(tokens[1]))

        elif op == '|':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.or)")
            result.append(self.set_var(tokens[1]))

        elif op == '.':
            result.append(self.resolve_value(tokens[1]))
            result.append("(call $print_i32)")

        elif op == '[':
            size_code = self.resolve_value(tokens[2])
            result.append("(global.get $heap_ptr)")
            result.append(self.set_var(tokens[1]))
            result.append("(global.get $heap_ptr)")
            result.append(size_code)
            result.append("(i32.const 4)")
            result.append("(i32.mul)")
            result.append("(i32.add)")
            result.append("(global.set $heap_ptr)")
            self.use_memory = True

        elif op == ']':
            result.append(self.resolve_value(tokens[2]))
            result.append(self.resolve_value(tokens[3]))
            result.append("(i32.const 4)")
            result.append("(i32.mul)")
            result.append("(i32.add)")
            result.append("(i32.load)")
            result.append(self.set_var(tokens[1]))
            self.use_memory = True

        elif op == '{':
            if len(tokens) >= 4:
                result.append(self.resolve_value(tokens[1]))
                result.append(self.resolve_value(tokens[2]))
                result.append("(i32.const 4)")
                result.append("(i32.mul)")
                result.append("(i32.add)")
                result.append(self.resolve_value(tokens[3]))
                result.append("(i32.store)")
                self.use_memory = True

        return result

    def transpile_function(self, func_id: int, argc: int, body: list[list[str]]) -> list[str]:
        """Transpile a function to WAT"""
        result = []
        
        local_vars: set[int] = set()
        for tokens in body:
            if not tokens:
                continue
            for token in tokens:
                if token.startswith('v'):
                    try:
                        local_vars.add(int(token[1:]))
                    except ValueError:
                        pass

        params = " ".join(f"(param $a{i} i32)" for i in range(argc))
        result.append(f'(func $f{func_id} (export "f{func_id}") {params} (result i32)')
        
        for v in sorted(local_vars):
            result.append(f"  (local $v{v} i32)")
        
        body_code = self.transpile_block(body, local_vars, is_function=True)
        for line in body_code:
            result.append(f"  {line}")
        
        result.append("  (i32.const 0)")
        result.append(")")
        
        return result

    def transpile(self, code: str) -> str:
        """Transpile Sui code to WAT"""
        self.output = []
        self.used_globals = set()
        self.used_cmd_args = set()
        self.use_memory = False
        self.functions = {}
        
        lines_raw = code.strip().split('\n')
        lines = []
        for line in lines_raw:
            parsed = self.parse_line(line)
            if parsed:
                lines.append(parsed)

        self.collect_info(lines)

        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
                func_id = int(lines[i][1])
                argc = int(lines[i][2])
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
                self.collect_info(body)
            i += 1

        self.emit("(module")
        self.indent += 1

        self.emit(";; External function imports")
        self.emit('(import "env" "print_i32" (func $print_i32 (param i32)))')
        self.emit("")

        if self.use_memory:
            self.emit(";; Linear memory for arrays")
            self.emit("(memory 1)")
            self.emit("(global $heap_ptr (mut i32) (i32.const 0))")
            self.emit("")

        if self.used_globals:
            self.emit(";; Global variables")
            for g in sorted(self.used_globals):
                self.emit(f"(global $g{g} (export \"g{g}\") (mut i32) (i32.const 0))")
            self.emit("")

        if self.used_cmd_args:
            self.emit(";; Command-line arguments (set by host)")
            for c in sorted(self.used_cmd_args):
                self.emit(f"(global $c{c} (export \"c{c}\") (mut i32) (i32.const 0))")
            self.emit("")

        if self.functions:
            self.emit(";; Function definitions")
            for func_id, func_info in sorted(self.functions.items()):
                func_lines = self.transpile_function(func_id, func_info['argc'], func_info['body'])
                for line in func_lines:
                    self.emit(line)
                self.emit("")

        self.emit(";; Main function")
        self.emit("(func $main (export \"main\") (result i32)")
        self.indent += 1

        main_locals: set[int] = set()
        main_lines = []
        i = 0
        while i < len(lines):
            if lines[i][0] == '#':
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
                for token in lines[i]:
                    if token.startswith('v'):
                        try:
                            main_locals.add(int(token[1:]))
                        except ValueError:
                            pass
                i += 1

        for v in sorted(main_locals):
            self.emit(f"(local $v{v} i32)")

        body_code = self.transpile_block(main_lines, main_locals)
        for line in body_code:
            self.emit(line)

        self.emit("(i32.const 0)")
        self.indent -= 1
        self.emit(")")

        self.indent -= 1
        self.emit(")")

        return '\n'.join(self.output)


def compile_to_wasm(sui_code: str) -> bytes | None:
    """Compile Sui code to Wasm binary"""
    transpiler = Sui2WatTranspiler()
    wat_code = transpiler.transpile(sui_code)
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wat', delete=False) as f:
            f.write(wat_code)
            wat_path = f.name
        
        wasm_path = wat_path.replace('.wat', '.wasm')
        
        result = subprocess.run(
            ['wat2wasm', wat_path, '-o', wasm_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error: wat2wasm failed: {result.stderr}", file=sys.stderr)
            return None
        
        with open(wasm_path, 'rb') as f:
            wasm_bytes = f.read()
        
        os.unlink(wat_path)
        os.unlink(wasm_path)
        
        return wasm_bytes
        
    except FileNotFoundError:
        print("Error: wat2wasm not found. Install wabt: brew install wabt", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ('--version', '-V'):
        print(f"sui-lang {get_version()}")
        return
    
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("Usage: sui2wasm <input.sui> [-o <output.wasm>]")
        print()
        print("Compile Sui code to WebAssembly binary.")
        print()
        print("Options:")
        print("  -o FILE      Output file (default: input.wasm)")
        print("  --version    Show version")
        print()
        print("Requirements:")
        print("  wat2wasm     Install via: brew install wabt")
        sys.exit(0 if '-h' in sys.argv or '--help' in sys.argv else 1)
    
    input_file = sys.argv[1]
    
    output_file = input_file.rsplit('.', 1)[0] + '.wasm'
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    try:
        with open(input_file, 'r') as f:
            sui_code = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    
    wasm_bytes = compile_to_wasm(sui_code)
    
    if wasm_bytes is None:
        sys.exit(1)
    
    with open(output_file, 'wb') as f:
        f.write(wasm_bytes)
    
    print(f"✓ Compiled to {output_file} ({len(wasm_bytes)} bytes)")


if __name__ == '__main__':
    main()
