#!/usr/bin/env python3
"""ADT receipt field validator — verifies that a receipt contains all six
mandatory fields: FACT, AUTHORITY, ACTION, RESULT, ARTIFACT_TYPE, ARTIFACT_LOCATION.

Usage:
    python scripts/validate_receipt.py --file <path>
    python scripts/validate_receipt.py --stdin
    echo "$receipt" | python scripts/validate_receipt.py --stdin
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "FACT",
    "AUTHORITY",
    "ACTION",
    "RESULT",
    "ARTIFACT_TYPE",
    "ARTIFACT_LOCATION",
]

_KV_RE = re.compile(r"^([A-Z_]+)\s*:\s*", re.IGNORECASE)


def parse_receipt(content: str) -> set[str]:
    """Extract the set of field names present in receipt content.

    Supports two formats:
      - Key-value:   ``FIELD: value`` (one per line)
      - JSON object: ``{"FACT": "...", ...}``
    Returns a set of normalised (upper-case) field names found.
    """
    stripped = content.strip()
    fields: set[str] = set()

    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            import json

            data = json.loads(stripped)
            if isinstance(data, dict):
                for key in data:
                    upper = key.strip().upper()
                    if upper in REQUIRED_FIELDS:
                        fields.add(upper)
        except (json.JSONDecodeError, ValueError):
            pass

    for line in stripped.splitlines():
        m = _KV_RE.match(line)
        if m:
            fields.add(m.group(1).upper())

    return fields & set(REQUIRED_FIELDS)


def validate(content: str) -> tuple:
    """Return (passed, missing_fields)."""
    found = parse_receipt(content)
    missing = [f for f in REQUIRED_FIELDS if f not in found]
    return (len(missing) == 0, missing)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that an ADT receipt contains all 6 mandatory fields."
    )
    parser.add_argument("--file", type=Path, help="Path to receipt file.")
    parser.add_argument("--stdin", action="store_true", help="Read receipt content from stdin.")
    args = parser.parse_args()

    if not args.file and not args.stdin:
        parser.error("Either --file or --stdin is required.")

    if args.file:
        content = args.file.read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()

    passed, missing = validate(content)

    if passed:
        print("PASS")
        sys.exit(0)
    else:
        print(f"FAIL: missing: {', '.join(missing)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
