#!/usr/bin/env python3
"""ADT RECEIPT-phase entry (thin).

RECEIPT = post-execution phase: governance critical gate (independent
Checker receipt), pre-merge final acceptance point, and candidate state
determination. Runs the RECEIPT-phase checks of BindingValidator on the
shared core (scripts/binding_core.py) and exits 0 on PASS, 1 on FAIL.

NOTE: named validate_receipt_phase.py (not validate_receipt.py) because
scripts/validate_receipt.py is an existing #86 upstream asset — the
six-field receipt validator (parse_receipt/validate) with its own tests.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from binding_core import BindingValidator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RECEIPT phase: governance gate + pre-merge final acceptance + candidate state"
    )
    parser.add_argument("--file", "-f", default="PROJECT_STATE.md")
    parser.add_argument("--pre-merge", action="store_true")
    parser.add_argument("--expected-fingerprint")
    parser.add_argument("--audit-fingerprint")
    parser.add_argument("--ready-authorization-fingerprint")
    parser.add_argument("--merge-authorization-fingerprint")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 2

    validator = BindingValidator(
        path.read_text(),
        live_mode=True,
        pre_merge=args.pre_merge,
        expected_fingerprint=args.expected_fingerprint,
        audit_fingerprint=args.audit_fingerprint,
        ready_authorization_fingerprint=args.ready_authorization_fingerprint,
        merge_authorization_fingerprint=args.merge_authorization_fingerprint,
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
    validator.check_governance_gate()
    validator.check_premerge()
    validator.determine_candidate_state()
    return 0 if validator._finish() else 1


if __name__ == "__main__":
    raise SystemExit(main())
