#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy Sui implementation.

The legacy implementation lives in `sui_legacy.sui`.
This module keeps the original import path for tests and external users.
"""

from sui_legacy.sui import SuiInterpreter, validate_line, get_version  # noqa: F401
from sui_legacy.sui import main as _legacy_main


def main() -> None:
    _legacy_main()


if __name__ == "__main__":
    main()

