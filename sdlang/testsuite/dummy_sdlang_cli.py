#!/usr/bin/env python3
"""Dummy sdlang CLI for testsuite smoke tests.

Implements:
  dummy_sdlang_cli.py parse <input_file>
  dummy_sdlang_cli.py serialize <input_file>

Both commands echo the file content unchanged.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dummy sdlang parse/serialize CLI")
    parser.add_argument("command", choices=("parse", "serialize"))
    parser.add_argument("input_file", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _ = args.command  # reserved for future behavior changes

    if not args.input_file.exists():
        print(f"Input file not found: {args.input_file}", file=sys.stderr)
        return 1

    sys.stdout.write(args.input_file.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
