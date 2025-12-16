#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy `suiwasm` tool.

The implementation lives in `sui_legacy.suiwasm`.
"""

from sui_legacy.suiwasm import SuiWasmRuntime, get_version  # noqa: F401
from sui_legacy.suiwasm import main as _legacy_main


def main() -> None:
    _legacy_main()


if __name__ == "__main__":
    main()

