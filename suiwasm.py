#!/usr/bin/env python3
"""
Sui (粋) WebAssembly Runtime
Execute Sui code directly via WebAssembly using wasmtime
"""

import sys
import os

try:
    from wasmtime import Store, Module, Func, FuncType, ValType, Linker, Engine
    WASMTIME_AVAILABLE = True
except ImportError:
    WASMTIME_AVAILABLE = False

from sui2wasm import Sui2WatTranspiler

def get_version() -> str:
    """Get package version"""
    try:
        from importlib.metadata import version
        return version("sui-lang")
    except Exception:
        return "0.4.1"


class SuiWasmRuntime:
    """Runtime for executing Sui code via WebAssembly"""

    def __init__(self):
        if not WASMTIME_AVAILABLE:
            raise RuntimeError("wasmtime is required. Install with: pip install wasmtime")
        
        self.engine = Engine()
        self.output: list[int] = []

    def run(self, sui_code: str) -> tuple[int, list[int]]:
        """
        Execute Sui code via WebAssembly
        
        Args:
            sui_code: Sui source code
            
        Returns:
            Tuple of (return_value, output_list)
        """
        self.output = []
        
        # Transpile Sui to WAT
        transpiler = Sui2WatTranspiler()
        wat_code = transpiler.transpile(sui_code)
        
        # Create store and compile module
        store = Store(self.engine)
        
        try:
            module = Module(self.engine, wat_code)
        except Exception as e:
            raise RuntimeError(f"WAT compilation error: {e}\n\nGenerated WAT:\n{wat_code}")
        
        # Create linker and define imports
        linker = Linker(self.engine)
        
        # Define print_i32 function
        print_type = FuncType([ValType.i32()], [])
        def print_i32(value: int):
            self.output.append(value)
            print(value)
        linker.define_func("env", "print_i32", print_type, print_i32)
        
        # Instantiate module
        try:
            instance = linker.instantiate(store, module)
        except Exception as e:
            raise RuntimeError(f"Wasm instantiation error: {e}")
        
        # Get and call main function
        main_func = instance.exports(store).get("main")
        if main_func is None:
            raise RuntimeError("No main function exported")
        
        result = main_func(store)
        
        return result, self.output

    def run_file(self, filename: str) -> tuple[int, list[int]]:
        """Execute a Sui file via WebAssembly"""
        with open(filename, 'r') as f:
            code = f.read()
        return self.run(code)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ('--version', '-V'):
        print(f"sui-lang {get_version()}")
        return
    
    if not WASMTIME_AVAILABLE:
        print("Error: wasmtime is required")
        print("Install with: pip install wasmtime")
        sys.exit(1)

    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Sui (粋) WebAssembly Runtime")
        print("=" * 50)
        print("")
        print("Usage:")
        print("  suiwasm <file.sui>       # Execute Sui file via WebAssembly")
        print("  suiwasm --wat <file.sui> # Show generated WAT code")
        print("  suiwasm --version        # Show version")
        print("")
        print("This runtime:")
        print("  1. Transpiles Sui code to WebAssembly Text Format (WAT)")
        print("  2. Compiles WAT to WebAssembly binary")
        print("  3. Executes in wasmtime runtime")
        print("")
        print("Sample:")
        print("-" * 50)

        sample = """
= v0 1
: 0
> v1 v0 5
? v1 1
. v0
+ v0 v0 1
@ 0
: 1
"""
        print("Sui (print 1-5):")
        print(sample.strip())
        print("")
        print("Executing via WebAssembly:")
        print("-" * 50)
        
        try:
            runtime = SuiWasmRuntime()
            result, output = runtime.run(sample)
            print("-" * 50)
            print(f"Return value: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        return

    # Check for --wat flag
    if sys.argv[1] == '--wat':
        if len(sys.argv) < 3:
            print("Error: Please specify a file")
            sys.exit(1)
        
        filename = sys.argv[2]
        with open(filename, 'r') as f:
            code = f.read()
        
        transpiler = Sui2WatTranspiler()
        wat_code = transpiler.transpile(code)
        print(wat_code)
        return

    # Execute file
    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        sys.exit(1)

    try:
        runtime = SuiWasmRuntime()
        result, output = runtime.run_file(filename)
        # Return value is shown only if non-zero or if there's no output
        if result != 0 or not output:
            print(f"[Return: {result}]")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

