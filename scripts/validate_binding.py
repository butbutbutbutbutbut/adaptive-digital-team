#!/usr/bin/env python3
"""ADT BINDING-phase entry (thin wrapper).

All validation logic lives in scripts/binding_core.py (shared core).
This module keeps the original CLI contract (--file / --ci / --live /
--candidate / --pre-merge / --expected-fingerprint / ...) and re-exports
the public symbols that tests and callers import from validate_binding.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from binding_core import (  # noqa: F401  — re-exported for back-compat
    BindingValidator,
    CANDIDATE_STATES,
    FINGERPRINT_KEYS,
    FORBIDDEN_STATE_KEYS,
    HARD_STOP,
    SCOPE_VIOLATION,
    STACKED_PR_PROHIBITED,
    VALID_IMPLEMENTATION_STATUSES,
    canonical_fields,
    candidate_fingerprint,
    push_ref_branch,
)

__all__ = [
    "BindingValidator",
    "CANDIDATE_STATES",
    "FINGERPRINT_KEYS",
    "FORBIDDEN_STATE_KEYS",
    "HARD_STOP",
    "SCOPE_VIOLATION",
    "STACKED_PR_PROHIBITED",
    "VALID_IMPLEMENTATION_STATUSES",
    "canonical_fields",
    "candidate_fingerprint",
    "push_ref_branch",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", default="PROJECT_STATE.md")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--candidate", action="store_true",
                        help="Enable pre-write gate + scope enforcement for candidate branch")
    parser.add_argument("--pre-merge", action="store_true")
    parser.add_argument("--expected-fingerprint")
    parser.add_argument("--audit-fingerprint")
    parser.add_argument("--ready-authorization-fingerprint")
    parser.add_argument("--merge-authorization-fingerprint")
    parser.add_argument("--scope", nargs="*", default=None,
                        help="Explicit authorized write scope (overrides PROJECT_STATE.md)")
    args = parser.parse_args()
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        return 2
    validator = BindingValidator(
        path.read_text(),
        live_mode=args.ci or args.live,
        candidate_mode=args.candidate,
        pre_merge=args.pre_merge,
        expected_fingerprint=args.expected_fingerprint,
        audit_fingerprint=args.audit_fingerprint,
        ready_authorization_fingerprint=args.ready_authorization_fingerprint,
        merge_authorization_fingerprint=args.merge_authorization_fingerprint,
        explicit_scope=list(args.scope) if args.scope is not None else None,
    )
    return 0 if validator.validate() else 1


if __name__ == "__main__":
    raise SystemExit(main())
