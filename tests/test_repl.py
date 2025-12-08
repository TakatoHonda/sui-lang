"""REPL Tests for interactive mode"""

import builtins
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repl.repl import _calculate_block_depth, run_repl


def _run_repl_script(monkeypatch: pytest.MonkeyPatch, lines: list[str]) -> list[str]:
    """
    Run run_repl on the specified input column and return the list of prompts shown during input.
    """
    prompts: list[str] = []
    iterator = iter(lines)

    def _fake_input(prompt: str) -> str:
        prompts.append(prompt)
        try:
            return next(iterator)
        except StopIteration:
            # If the input is exhausted, raise EOFError
            raise EOFError

    monkeypatch.setattr(builtins, "input", _fake_input)
    run_repl()
    return prompts


class TestCalculateBlockDepth:
    def test_nested_blocks_and_comments(self):
        lines = ["# 0 0 {", "; ignore", "# 1 0 {", "}", "}"]
        assert _calculate_block_depth(lines) == 0

    def test_unclosed_block_returns_depth(self):
        lines = ["# 0 0 {", "; still open"]
        assert _calculate_block_depth(lines) == 1

    def test_extra_closing_brace_is_ignored_when_depth_zero(self):
        lines = ["}"]
        assert _calculate_block_depth(lines) == 0


class TestRunRepl:
    def test_runs_snippet_and_exits(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
        prompts = _run_repl_script(monkeypatch, ['. "hello"', "", ".quit"])
        captured = capsys.readouterr()
        assert "Sui REPL" in captured.out
        assert "hello" in captured.out
        assert prompts[:3] == [">>> ", ">>> ", ">>> "]

    def test_reset_creates_fresh_interpreter(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
        _run_repl_script(monkeypatch, [".reset", '. "one"', "", ".quit"])
        captured = capsys.readouterr()
        assert "状態をリセットしました。" in captured.out
        assert "one" in captured.out

    def test_block_prompt_switches_to_continuation(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
        prompts = _run_repl_script(monkeypatch, ["# 0 0 {", "}", "", ".quit"])
        captured = capsys.readouterr()
        assert "... " in prompts  # Block continuation prompt is shown
        assert "Error" not in captured.err

