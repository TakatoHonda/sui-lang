"""Tests for Sui interpreter"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sui import SuiInterpreter, validate_line


class TestBasicOperations:
    """Test basic arithmetic and assignment operations"""

    def test_assignment(self):
        interp = SuiInterpreter()
        result = interp.run("= g0 42\n. g0")
        assert result == [42]

    def test_addition(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 10\n= v1 20\n+ v2 v0 v1\n. v2")
        assert result == [30]

    def test_subtraction(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 50\n= v1 30\n- v2 v0 v1\n. v2")
        assert result == [20]

    def test_multiplication(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 6\n= v1 7\n* v2 v0 v1\n. v2")
        assert result == [42]

    def test_division(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 100\n= v1 4\n/ v2 v0 v1\n. v2")
        assert result == [25.0]

    def test_modulo(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 17\n= v1 5\n% v2 v0 v1\n. v2")
        assert result == [2]


class TestComparisons:
    """Test comparison operations"""

    def test_less_than_true(self):
        interp = SuiInterpreter()
        result = interp.run("< v0 5 10\n. v0")
        assert result == [1]

    def test_less_than_false(self):
        interp = SuiInterpreter()
        result = interp.run("< v0 10 5\n. v0")
        assert result == [0]

    def test_greater_than_true(self):
        interp = SuiInterpreter()
        result = interp.run("> v0 10 5\n. v0")
        assert result == [1]

    def test_greater_than_false(self):
        interp = SuiInterpreter()
        result = interp.run("> v0 5 10\n. v0")
        assert result == [0]

    def test_equality_true(self):
        interp = SuiInterpreter()
        result = interp.run("~ v0 42 42\n. v0")
        assert result == [1]

    def test_equality_false(self):
        interp = SuiInterpreter()
        result = interp.run("~ v0 42 43\n. v0")
        assert result == [0]


class TestLogicalOperations:
    """Test logical operations"""

    def test_not_true(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 0\n! v1 v0\n. v1")
        assert result == [1]

    def test_not_false(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 1\n! v1 v0\n. v1")
        assert result == [0]

    def test_and(self):
        interp = SuiInterpreter()
        result = interp.run("& v0 1 1\n. v0")
        assert result == [1]

    def test_or(self):
        interp = SuiInterpreter()
        result = interp.run("| v0 0 1\n. v0")
        assert result == [1]


class TestControlFlow:
    """Test control flow operations"""

    def test_unconditional_jump(self):
        interp = SuiInterpreter()
        result = interp.run("@ 0\n. 1\n: 0\n. 2")
        assert result == [2]

    def test_conditional_jump_taken(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 1\n? v0 0\n. 1\n: 0\n. 2")
        assert result == [2]

    def test_conditional_jump_not_taken(self):
        interp = SuiInterpreter()
        result = interp.run("= v0 0\n? v0 0\n. 1\n@ 1\n: 0\n. 2\n: 1")
        assert result == [1]

    def test_loop(self):
        """Test simple loop: sum 1 to 5"""
        code = """
= v0 0
= v1 1
: 0
> v2 v1 5
? v2 1
+ v0 v0 v1
+ v1 v1 1
@ 0
: 1
. v0
"""
        interp = SuiInterpreter()
        result = interp.run(code)
        assert result == [15]  # 1+2+3+4+5


class TestFunctions:
    """Test function definitions and calls"""

    def test_simple_function(self):
        code = """
# 0 1 {
+ v0 a0 10
^ v0
}
$ g0 0 5
. g0
"""
        interp = SuiInterpreter()
        result = interp.run(code)
        assert result == [15]

    def test_recursive_function(self):
        """Test factorial function"""
        code = """
# 0 1 {
< v0 a0 2
! v1 v0
? v1 1
^ 1
: 1
- v2 a0 1
$ v3 0 v2
* v4 a0 v3
^ v4
}
$ g0 0 5
. g0
"""
        interp = SuiInterpreter()
        result = interp.run(code)
        assert result == [120]  # 5!

    def test_fibonacci(self):
        """Test fibonacci function"""
        code = """
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
$ g0 0 10
. g0
"""
        interp = SuiInterpreter()
        result = interp.run(code)
        assert result == [55]


class TestArrays:
    """Test array operations"""

    def test_array_create_and_write(self):
        interp = SuiInterpreter()
        result = interp.run("[ g0 3\n{ g0 0 10\n{ g0 1 20\n{ g0 2 30\n] v0 g0 1\n. v0")
        assert result == [20]

    def test_array_sum(self):
        code = """
[ g0 5
{ g0 0 1
{ g0 1 2
{ g0 2 3
{ g0 3 4
{ g0 4 5
= g1 0
= v0 0
: 0
< v1 v0 5
! v2 v1
? v2 1
] v3 g0 v0
+ g1 g1 v3
+ v0 v0 1
@ 0
: 1
. g1
"""
        interp = SuiInterpreter()
        result = interp.run(code)
        assert result == [15]


class TestStrings:
    """Test string operations"""

    def test_string_output(self):
        interp = SuiInterpreter()
        result = interp.run('. "Hello"')
        assert result == ["Hello"]

    def test_string_with_spaces(self):
        interp = SuiInterpreter()
        result = interp.run('. "Hello World"')
        assert result == ["Hello World"]


class TestCommandLineArgs:
    """Test command-line argument handling"""

    def test_args_count(self):
        interp = SuiInterpreter()
        result = interp.run(". g100", args=["10", "20"])
        assert result == [2]

    def test_args_values(self):
        interp = SuiInterpreter()
        result = interp.run("+ v0 g101 g102\n. v0", args=["10", "20"])
        assert result == [30]

    def test_no_args(self):
        interp = SuiInterpreter()
        result = interp.run(". g100", args=[])
        assert result == [0]


class TestValidation:
    """Test line validation"""

    def test_valid_assignment(self):
        valid, msg = validate_line("= v0 10")
        assert valid is True

    def test_valid_addition(self):
        valid, msg = validate_line("+ v0 v1 v2")
        assert valid is True

    def test_invalid_addition_missing_args(self):
        valid, msg = validate_line("+ v0 v1")
        assert valid is False
        assert "requires" in msg

    def test_valid_function_def(self):
        valid, msg = validate_line("# 0 2 {")
        assert valid is True

    def test_invalid_function_def(self):
        valid, msg = validate_line("# 0 2")
        assert valid is False

    def test_comment(self):
        valid, msg = validate_line("; this is a comment")
        assert valid is True

    def test_empty_line(self):
        valid, msg = validate_line("")
        assert valid is True

    def test_invalid_unknown_instruction(self):
        valid, msg = validate_line(".v1")
        assert valid is False
        assert "Unknown instruction" in msg

    def test_invalid_typo_instruction(self):
        valid, msg = validate_line("abc v0 v1")
        assert valid is False
        assert "Unknown instruction" in msg

