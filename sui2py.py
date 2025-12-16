#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy `sui2py` tool.

The implementation lives in `sui_legacy.sui2py`.
"""

from sui_legacy.sui2py import Sui2PyTranspiler, get_version  # noqa: F401
from sui_legacy.sui2py import main as _legacy_main


def main() -> None:
    _legacy_main()


if __name__ == "__main__":
    main()

