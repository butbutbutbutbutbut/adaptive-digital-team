#!/usr/bin/env python3
"""ADT GATE-phase entry (thin).

GATE = during-execution phase: pre-write execution gate + live scope
enforcement. Runs the GATE-phase checks of BindingValidator on the shared
core (scripts/binding_core.py) and exits 0 on PASS, 1 on FAIL.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from binding_core import BindingValidator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GATE phase: pre-write execution gate + live scope enforcement"
    )
    parser.add_argument("--file", "-f", default="PROJECT_STATE.md")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--candidate", action="store_true",
                        help="Enable pre-write gate + scope enforcement for candidate branch")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 2

    validator = BindingValidator(
        path.read_text(),
        live_mode=args.ci or args.live,
        candidate_mode=args.candidate,
    )
    try:
        validator.parsed = validator.parse()
    except (ValueError, yaml.YAMLError) as exc:
        validator.errors.append(f"VALIDATION-YAML: {exc}")
        return 0 if validator._finish() else 1
    validator._binding = validator._load_binding()
    validator.check_binding()
    validator.check_static()
    validator.check_prewrite_gate()
    validator.check_live()
    return 0 if validator._finish() else 1


if __name__ == "__main__":
    raise SystemExit(main())
