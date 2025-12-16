#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy `sui2wasm` tool.

The implementation lives in `sui_legacy.sui2wasm`.
"""

from sui_legacy.sui2wasm import Sui2WatTranspiler, compile_to_wasm, get_version  # noqa: F401
from sui_legacy.sui2wasm import main as _legacy_main


def main() -> None:
    _legacy_main()


if __name__ == "__main__":
    main()

