#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy `py2sui` tool.

The implementation lives in `sui_legacy.py2sui`.
"""

from sui_legacy.py2sui import Py2SuiTranspiler, get_version  # noqa: F401
from sui_legacy.py2sui import main as _legacy_main


def main() -> None:
    _legacy_main()


if __name__ == "__main__":
    main()

