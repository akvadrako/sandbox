#!/usr/bin/env python3
"""Single-file case runner for sdlang parse/serialize CLI checks.

Case files live in suite/*.txt and use section headers:
  :::: mode

  :::: input

  :::: transform

  :::: output

A typical invocation uses uv:
  uv run sdlang/testsuite/run_tests.py --list
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class TestCase:
    name: str
    mode: str
    input_text: str
    transforms: list[str]
    output_text: str


REQUIRED_SECTIONS = ("mode", "input", "transform", "output")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sdlang CLI parse/serialize tests")
    parser.add_argument(
        "--suite-dir",
        default=Path(__file__).parent / "suite",
        type=Path,
        help="Directory containing *.txt case files",
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
    parser.add_argument("--list", action="store_true", help="List discovered tests and exit")
    return parser.parse_args()


def parse_case_file(path: Path) -> TestCase:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("::::"):
            header = line[4:].strip().lower()
            if header not in REQUIRED_SECTIONS:
                raise ValueError(f"{path}: unknown section '{header}'")
            current = header
            sections.setdefault(current, [])
            continue

        if current is None:
            if line.strip():
                raise ValueError(f"{path}: content found before first ':::: <section>' header")
            continue

        sections[current].append(line)

    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        raise ValueError(f"{path}: missing sections: {', '.join(missing)}")

    mode = "\n".join(sections["mode"]).strip().lower()
    if mode not in {"parse", "serialize"}:
        raise ValueError(f"{path}: mode must be parse or serialize, got '{mode}'")

    transforms = [ln.strip() for ln in sections["transform"] if ln.strip() and not ln.strip().startswith("#")]

    return TestCase(
        name=path.stem,
        mode=mode,
        input_text="\n".join(sections["input"]),
        transforms=transforms,
        output_text="\n".join(sections["output"]),
    )


def discover_tests(suite_dir: Path) -> list[TestCase]:
    if not suite_dir.exists():
        return []
    return [parse_case_file(path) for path in sorted(suite_dir.glob("*.txt"))]


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


def run_command(template: str, input_text: str) -> str:
    if "{input}" not in template:
        raise ValueError("Command template must include '{input}' placeholder")

    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".sdlang", delete=True) as fp:
        fp.write(input_text)
        fp.flush()
        command = template.format(input=shlex.quote(fp.name))
        completed = subprocess.run(command, shell=True, text=True, capture_output=True)

    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {command}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    return completed.stdout


def run_tests(cases: list[TestCase], parse_cmd: str, serialize_cmd: str) -> int:
    failures = 0
    for case in cases:
        template = parse_cmd if case.mode == "parse" else serialize_cmd
        if not template:
            print(f"SKIP [{case.mode}] {case.name}: no command provided")
            continue

        expected = apply_transforms(case.output_text, case.transforms)

        try:
            actual = apply_transforms(run_command(template, case.input_text), case.transforms)
        except Exception as exc:  # noqa: BLE001
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
    cases = discover_tests(args.suite_dir)

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
