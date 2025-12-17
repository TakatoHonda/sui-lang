# Isu - Structured Pseudocode for LLMs (in the Sui project)

This repository is shifting its primary focus from the original line-based **Sui** language to **Isu**, a structured pseudocode designed for deterministic parsing and step-level repair loops.

[日本語版 README](README_ja.md) [简体中文版 README](README_zh_CN.md)

## Status

- **Isu (new)**: implemented as a minimal v0 pipeline (`isu/`) — Isu text ⇄ **IIR** (JSON-compatible AST) ⇄ canonical Isu.
- **Sui (legacy)**: moved to `sui_legacy/` and kept behind compatibility wrappers (`sui.py`, `sui2py.py`, etc.).

## What is Isu?

Isu is the **primary artifact** an LLM reads/writes. It is parsed deterministically into **IIR (Isu Intermediate Representation)**, a closed-vocabulary AST designed for:

- deterministic parsing and canonicalization (`AUTO_ID`, fixed shapes)
- step-level error localization and patch workflows
- backend independence (Python/Wasm/LLVM IR planned; not implemented yet)

Design docs:

- `isu/implementation-plan_en.md`
- `isu/implementation-plan_ja.md`

## Quick start (from source)

Isu is currently a repository-local Python package. Run it from the repo root:

```bash
python -c 'from isu import parse_isu, pretty_print_isu; \
src = """META:\n  AUTO_ID: true\nFUNC:\n  NAME: f\nIO:\n  INPUT: []\n  OUTPUT: []\nSTATE:\n  []\nLOCAL:\n  []\nSTEPS:\n  SEQ: BEGIN\n    ASSIGN:\n      TARGET: x\n      EXPR: (const 1)\n    RETURN:\n      EXPR: (var x)\n  END\n"""; \
p = parse_isu(src); print(pretty_print_isu(p))'
```

## Repository layout (high-level)

```text
isu/          # Isu v0 pipeline (parser/canonicalizer/pretty-printer/validator)
tests/        # pytest (includes Isu v0 round-trip tests)
sui_legacy/   # legacy Sui implementation (interpreter/transpilers/wasm tools)
sui.py        # compatibility wrapper -> sui_legacy.sui
```

## Legacy Sui (kept for now)

The original Sui language/tooling remains available:

- Playground: `playground/index.html`
- Examples: `examples/`
- Tools: `sui.py`, `sui2py.py`, `py2sui.py`, `sui2wasm.py`, `suiwasm.py` (wrappers)

It is explicitly treated as **legacy**, and new work should target **Isu/IIR**.

## License

MIT License
