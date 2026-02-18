#!/usr/bin/env python3
"""Simple CLI-driven test suite for SDLang parse/serialize behavior.

Each case directory in ./tests must contain:
  - input.txt       : SDLang source text
  - transform.txt   : expected parse transformation output
  - output.txt      : expected serialized SDLang output

The test runner executes a target CLI with command templates:
  parse:     {cli} parse {input}
  serialize: {cli} serialize {transform}

Override templates with --parse-cmd / --serialize-cmd.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CaseResult:
    name: str
    parse_ok: bool
    serialize_ok: bool
    message: str = ""


def normalize(text: str) -> str:
    # Keep comparisons stable across minor newline differences.
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_command(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def evaluate_case(case_dir: Path, cli: str, parse_cmd_tpl: str, serialize_cmd_tpl: str) -> CaseResult:
    name = case_dir.name
    input_path = case_dir / "input.txt"
    transform_path = case_dir / "transform.txt"
    output_path = case_dir / "output.txt"

    missing = [p.name for p in (input_path, transform_path, output_path) if not p.exists()]
    if missing:
        return CaseResult(name, False, False, f"missing files: {', '.join(missing)}")

    expected_transform = normalize(read_text(transform_path))
    expected_output = normalize(read_text(output_path))

    parse_cmd = parse_cmd_tpl.format(cli=cli, input=str(input_path), transform=str(transform_path), output=str(output_path))
    parse_code, parse_stdout, parse_stderr = run_command(parse_cmd)
    parse_actual = normalize(parse_stdout)
    parse_ok = parse_code == 0 and parse_actual == expected_transform

    serialize_cmd = serialize_cmd_tpl.format(cli=cli, input=str(input_path), transform=str(transform_path), output=str(output_path))
    serialize_code, serialize_stdout, serialize_stderr = run_command(serialize_cmd)
    serialize_actual = normalize(serialize_stdout)
    serialize_ok = serialize_code == 0 and serialize_actual == expected_output

    if parse_ok and serialize_ok:
        return CaseResult(name, True, True)

    details = []
    if not parse_ok:
        details.append(
            "parse failed"
            f" (exit={parse_code}, stderr={parse_stderr.strip()!r}, expected={expected_transform!r}, actual={parse_actual!r})"
        )
    if not serialize_ok:
        details.append(
            "serialize failed"
            f" (exit={serialize_code}, stderr={serialize_stderr.strip()!r}, expected={expected_output!r}, actual={serialize_actual!r})"
        )

    return CaseResult(name, parse_ok, serialize_ok, "; ".join(details))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SDLang parse/serialize fixture tests against a CLI.")
    parser.add_argument("--cli", required=True, help="CLI executable to test (e.g. sdlang)")
    parser.add_argument(
        "--tests-dir",
        default=Path(__file__).resolve().parent / "tests",
        type=Path,
        help="Directory containing case subdirectories (default: ./tests)",
    )
    parser.add_argument(
        "--parse-cmd",
        default="{cli} parse {input}",
        help="Template for parse command; placeholders: {cli}, {input}, {transform}, {output}",
    )
    parser.add_argument(
        "--serialize-cmd",
        default="{cli} serialize {transform}",
        help="Template for serialize command; placeholders: {cli}, {input}, {transform}, {output}",
    )

    args = parser.parse_args()

    tests_dir: Path = args.tests_dir
    if not tests_dir.exists() or not tests_dir.is_dir():
        print(f"ERROR: tests dir not found: {tests_dir}")
        return 2

    case_dirs = sorted(p for p in tests_dir.iterdir() if p.is_dir())
    if not case_dirs:
        print(f"ERROR: no test cases found in {tests_dir}")
        return 2

    results = [evaluate_case(d, args.cli, args.parse_cmd, args.serialize_cmd) for d in case_dirs]

    passed = 0
    for r in results:
        if r.parse_ok and r.serialize_ok:
            passed += 1
            print(f"PASS {r.name}")
        else:
            print(f"FAIL {r.name}: {r.message}")

    total = len(results)
    print(f"\nSummary: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
