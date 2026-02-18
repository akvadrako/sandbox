#!/usr/bin/env python3
"""Minimal CLI-driven test runner for sdlang parse/serialize checks.

Directory layout:
  tests/
    parse/<case_name>/{input.txt,transform.txt,output.txt}
    serialize/<case_name>/{input.txt,transform.txt,output.txt}

Use --parse-cmd and --serialize-cmd templates with {input} placeholder.
Example:
  python run_tests.py \\
    --parse-cmd 'sdlang-cli parse {input}' \\
    --serialize-cmd 'sdlang-cli serialize {input}'
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class TestCase:
    mode: str
    name: str
    input_path: Path
    transform_path: Path
    output_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sdlang CLI parse/serialize tests")
    parser.add_argument(
        "--tests-dir",
        default=Path(__file__).parent / "tests",
        type=Path,
        help="Directory containing parse/ and serialize/ test cases",
    )
    parser.add_argument(
        "--parse-cmd",
        default="",
        help="Command template to run parse tests (must include {input})",
    )
    parser.add_argument(
        "--serialize-cmd",
        default="",
        help="Command template to run serialize tests (must include {input})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered tests and exit",
    )
    return parser.parse_args()


def discover_tests(tests_dir: Path) -> list[TestCase]:
    cases: list[TestCase] = []
    for mode in ("parse", "serialize"):
        mode_dir = tests_dir / mode
        if not mode_dir.exists():
            continue
        for case_dir in sorted(path for path in mode_dir.iterdir() if path.is_dir()):
            case = TestCase(
                mode=mode,
                name=case_dir.name,
                input_path=case_dir / "input.txt",
                transform_path=case_dir / "transform.txt",
                output_path=case_dir / "output.txt",
            )
            for required in (case.input_path, case.transform_path, case.output_path):
                if not required.exists():
                    raise FileNotFoundError(f"Missing required file: {required}")
            cases.append(case)
    return cases


def load_transforms(path: Path) -> list[str]:
    transforms: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        transforms.append(line)
    return transforms


def apply_transforms(value: str, transforms: Iterable[str]) -> str:
    result = value
    for transform in transforms:
        if transform == "identity":
            continue
        if transform == "strip":
            result = result.strip()
            continue
        if transform == "collapse-whitespace":
            result = " ".join(result.split())
            continue
        if transform == "lowercase":
            result = result.lower()
            continue
        raise ValueError(f"Unknown transform '{transform}'")
    return result


def run_command(template: str, input_path: Path) -> str:
    if "{input}" not in template:
        raise ValueError("Command template must include '{input}' placeholder")
    command = template.format(input=shlex.quote(str(input_path)))
    completed = subprocess.run(command, shell=True, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed.stdout


def run_tests(cases: List[TestCase], parse_cmd: str, serialize_cmd: str) -> int:
    failures = 0
    for case in cases:
        template = parse_cmd if case.mode == "parse" else serialize_cmd
        if not template:
            print(f"SKIP [{case.mode}] {case.name}: no command provided")
            continue

        transforms = load_transforms(case.transform_path)
        expected = apply_transforms(case.output_path.read_text(encoding="utf-8"), transforms)

        try:
            actual_raw = run_command(template, case.input_path)
            actual = apply_transforms(actual_raw, transforms)
        except Exception as exc:  # noqa: BLE001 - show any CLI/test error
            failures += 1
            print(f"FAIL [{case.mode}] {case.name}: {exc}")
            continue

        if actual != expected:
            failures += 1
            print(f"FAIL [{case.mode}] {case.name}")
            print("--- expected ---")
            print(expected)
            print("--- actual ---")
            print(actual)
            continue

        print(f"PASS [{case.mode}] {case.name}")

    return failures


def main() -> int:
    args = parse_args()
    cases = discover_tests(args.tests_dir)

    if args.list:
        for case in cases:
            print(f"{case.mode}/{case.name}")
        return 0

    failures = run_tests(cases, args.parse_cmd, args.serialize_cmd)
    if failures:
        print(f"\n{failures} test(s) failed.")
        return 1

    print("\nAll tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
