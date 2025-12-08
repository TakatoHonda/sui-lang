"""
Tests for sui2wasm (Sui to WebAssembly binary compiler)
"""

import pytest
import subprocess
import sys
import os
import tempfile


class TestSui2WasmCLI:
    """Test sui2wasm CLI"""

    def test_help(self):
        """Test --help flag"""
        result = subprocess.run(
            [sys.executable, 'sui2wasm.py', '--help'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        assert result.returncode == 0
        assert 'Usage' in result.stdout

    def test_compile_fibonacci(self):
        """Test compiling fibonacci.sui to wasm"""
        with tempfile.NamedTemporaryFile(suffix='.wasm', delete=False) as f:
            output_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, 'sui2wasm.py', 'examples/fibonacci.sui', '-o', output_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # Check if wat2wasm is available
            if 'wat2wasm not found' in result.stderr:
                pytest.skip("wat2wasm not installed")
            
            assert result.returncode == 0
            assert os.path.exists(output_path)
            
            # Check it's a valid wasm file (magic number)
            with open(output_path, 'rb') as f:
                magic = f.read(4)
                assert magic == b'\x00asm', "Invalid Wasm magic number"
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_compile_fizzbuzz(self):
        """Test compiling fizzbuzz.sui to wasm"""
        with tempfile.NamedTemporaryFile(suffix='.wasm', delete=False) as f:
            output_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, 'sui2wasm.py', 'examples/fizzbuzz.sui', '-o', output_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            if 'wat2wasm not found' in result.stderr:
                pytest.skip("wat2wasm not installed")
            
            assert result.returncode == 0
            assert os.path.exists(output_path)
            
            # Verify file size is reasonable
            size = os.path.getsize(output_path)
            assert size > 50, "Wasm file too small"
            assert size < 10000, "Wasm file too large"
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_file_not_found(self):
        """Test error handling for missing file"""
        result = subprocess.run(
            [sys.executable, 'sui2wasm.py', 'nonexistent.sui'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        assert result.returncode == 1
        assert 'not found' in result.stderr.lower()

    def test_default_output_name(self):
        """Test default output filename"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test sui file
            sui_path = os.path.join(tmpdir, 'test.sui')
            with open(sui_path, 'w') as f:
                f.write('= g0 42\n. g0')
            
            result = subprocess.run(
                [sys.executable, 'sui2wasm.py', sui_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            if 'wat2wasm not found' in result.stderr:
                pytest.skip("wat2wasm not installed")
            
            # Should create test.wasm in same directory
            expected_output = os.path.join(tmpdir, 'test.wasm')
            assert result.returncode == 0
            assert os.path.exists(expected_output)


class TestSui2WasmModule:
    """Test sui2wasm module functions"""

    def test_compile_to_wasm_simple(self):
        """Test compile_to_wasm with simple code"""
        try:
            from sui2wasm import compile_to_wasm
        except ImportError:
            # Add parent directory to path
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from sui2wasm import compile_to_wasm
        
        wasm_bytes = compile_to_wasm('= g0 42\n. g0')
        
        if wasm_bytes is None:
            pytest.skip("wat2wasm not installed")
        
        assert isinstance(wasm_bytes, bytes)
        assert wasm_bytes[:4] == b'\x00asm'  # Wasm magic number

    def test_compile_to_wasm_with_function(self):
        """Test compile_to_wasm with function definition"""
        try:
            from sui2wasm import compile_to_wasm
        except ImportError:
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from sui2wasm import compile_to_wasm
        
        code = """
# 0 1 {
+ v0 a0 1
^ v0
}
= g0 10
$ g1 0 g0
. g1
"""
        wasm_bytes = compile_to_wasm(code)
        
        if wasm_bytes is None:
            pytest.skip("wat2wasm not installed")
        
        assert isinstance(wasm_bytes, bytes)
        assert len(wasm_bytes) > 50

