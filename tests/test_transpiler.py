"""Tests for Sui transpilers (sui2py and py2sui)"""

import pytest
import sys
import os
import tempfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sui2py import Sui2PyTranspiler


class TestSui2Py:
    """Test Sui to Python transpiler"""

    def test_assignment(self):
        transpiler = Sui2PyTranspiler()
        code = transpiler.transpile("= g0 42\n. g0")
        assert "g0 = 42" in code
        assert "print(g0)" in code

    def test_arithmetic(self):
        transpiler = Sui2PyTranspiler()
        code = transpiler.transpile("+ v0 10 20")
        assert "v0 = 10 + 20" in code

    def test_function(self):
        transpiler = Sui2PyTranspiler()
        code = transpiler.transpile("# 0 1 {\n^ a0\n}")
        assert "def f0" in code
        assert "return" in code

    def test_execution_fibonacci(self):
        """Test that transpiled fibonacci produces correct result"""
        sui_code = """
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
= g0 10
$ g1 0 g0
. g1
"""
        transpiler = Sui2PyTranspiler()
        python_code = transpiler.transpile(sui_code)
        
        # Execute the transpiled code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
            assert "55" in result.stdout
        finally:
            os.unlink(temp_file)


class TestSui2PyControlFlow:
    """Test control flow transpilation"""

    def test_loop(self):
        """Test that loops are transpiled correctly"""
        sui_code = """
= v0 0
= v1 0
: 0
< v2 v1 5
! v3 v2
? v3 1
+ v0 v0 v1
+ v1 v1 1
@ 0
: 1
. v0
"""
        transpiler = Sui2PyTranspiler()
        python_code = transpiler.transpile(sui_code)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
            assert "10" in result.stdout  # 0+1+2+3+4
        finally:
            os.unlink(temp_file)


class TestSui2PyArrays:
    """Test array transpilation"""

    def test_array_operations(self):
        sui_code = """
[ g0 3
{ g0 0 10
{ g0 1 20
{ g0 2 30
] v0 g0 1
. v0
"""
        transpiler = Sui2PyTranspiler()
        python_code = transpiler.transpile(sui_code)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
            assert "20" in result.stdout
        finally:
            os.unlink(temp_file)


class TestExampleFiles:
    """Test that all example files work correctly"""

    @pytest.fixture
    def examples_dir(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')

    def test_fibonacci_example(self, examples_dir):
        """Test fibonacci.sui"""
        result = subprocess.run(
            [sys.executable, 'sui.py', os.path.join(examples_dir, 'fibonacci.sui')],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=5
        )
        assert result.returncode == 0
        assert "55" in result.stdout

    def test_fizzbuzz_example(self, examples_dir):
        """Test fizzbuzz.sui"""
        result = subprocess.run(
            [sys.executable, 'sui.py', os.path.join(examples_dir, 'fizzbuzz.sui')],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=10
        )
        assert result.returncode == 0
        assert "FizzBuzz" in result.stdout
        assert "Fizz" in result.stdout
        assert "Buzz" in result.stdout

    def test_list_sum_example(self, examples_dir):
        """Test list_sum.sui"""
        result = subprocess.run(
            [sys.executable, 'sui.py', os.path.join(examples_dir, 'list_sum.sui')],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=5
        )
        assert result.returncode == 0
        assert "150" in result.stdout

    def test_fib_args_example(self, examples_dir):
        """Test fib_args.sui with argument"""
        result = subprocess.run(
            [sys.executable, 'sui.py', os.path.join(examples_dir, 'fib_args.sui'), '15'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=5
        )
        assert result.returncode == 0
        assert "610" in result.stdout

    def test_args_demo_example(self, examples_dir):
        """Test args_demo.sui with arguments"""
        result = subprocess.run(
            [sys.executable, 'sui.py', os.path.join(examples_dir, 'args_demo.sui'), '5', '3'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            timeout=5
        )
        assert result.returncode == 0
        assert "8" in result.stdout
