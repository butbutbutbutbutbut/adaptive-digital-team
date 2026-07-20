#!/usr/bin/env python3
"""Collect and run the complete ADT binding-validation regression suite."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
MINIMUM_TESTS = 110


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    collected = run("--collect-only", "-q", str(TESTS_DIR))
    sys.stdout.write(collected.stdout)
    sys.stderr.write(collected.stderr)
    if collected.returncode != 0:
        return collected.returncode

    match = re.search(r"(\d+) tests? collected", collected.stdout)
    if not match:
        print("FAIL: unable to determine collected test count", file=sys.stderr)
        return 2
    count = int(match.group(1))
    if count < MINIMUM_TESTS:
        print(f"FAIL: {count} tests collected; minimum is {MINIMUM_TESTS}", file=sys.stderr)
        return 1

    result = run("-q", str(TESTS_DIR))
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
