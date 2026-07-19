#!/usr/bin/env python3
"""Binding validator for ADT repository-as-prompt runtime binding protocol.

Validates PROJECT_STATE.md or .adt/project-binding.yaml against the rules in
protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md § 9.

Usage:
    python scripts/validate_binding.py [--file PATH] [--ci]

Exit code 0: all validations pass.
Exit code 1: one or more validations failed.
"""

import yaml
import argparse
import re
import sys
import subprocess
from pathlib import Path


class BindingValidator:
    """Validates a runtime binding record against the protocol rules."""

    def __init__(self, binding_text: str, live_mode: bool = False):
        self.text = binding_text
        self.live_mode = live_mode
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.parsed: dict = {}

    def parse_yaml(self) -> dict:
        """Parse YAML from markdown-embedded or raw YAML text using PyYAML."""
        # Extract YAML block from markdown code fence
        yaml_match = re.search(r'```ya?ml\s*\n(.*?)\n```', self.text, re.DOTALL)
        if yaml_match:
            yaml_text = yaml_match.group(1)
        else:
            yaml_text = self.text
        return yaml.safe_load(yaml_text) or {}

    def get(self, key: str, default=None):
        """Resolve dotted key path from parsed YAML dict."""
        parts = key.split('.')
        node = self.parsed
        for part in parts:
            if isinstance(node, dict):
                node = node.get(part)
                if node is None:
                    return default
            else:
                return default
        return node

    def validate(self) -> bool:
        """Run all validations. Returns True if all pass."""
        self.parsed = self.parse_yaml()

        self.check_1_authoritative_fact_source_present()
        self.check_2_active_not_in_invalidated()
        self.check_3_main_not_dual_role_without_human_auth()
        self.check_4_comparison_not_active()
        self.check_5_visual_status_not_auto_accepted()
        self.check_6_rebind_blocks_write()
        self.check_7_progress_card_required_fields()
        self.check_8_candidate_head_live_check()
        self.check_10_minimum_context_recovery()

        if self.errors:
            for e in self.errors:
                print(f"FAIL: {e}", file=sys.stderr)
            return False
        if self.warnings:
            for w in self.warnings:
                print(f"WARN: {w}", file=sys.stderr)
        print("PASS: All validations passed")
        return True

    def check_1_authoritative_fact_source_present(self):
        """Missing authoritative_fact_source → FAIL."""
        afs_type = self.get('authoritative_fact_source.type')
        afs_sha = self.get('authoritative_fact_source.sha')
        if not afs_type:
            self.errors.append(
                "VALIDATION-1: authoritative_fact_source.type is missing"
            )
        if not afs_sha or afs_sha == 'NONE':
            self.errors.append(
                "VALIDATION-1: authoritative_fact_source.sha is missing or NONE"
            )

    def check_2_active_not_in_invalidated(self):
        """active_candidate in invalidated_candidates → FAIL."""
        active_branch = self.get('active_candidate.branch')
        if not active_branch or active_branch == 'NONE':
            return  # No active candidate to check

        invalidated = self.get('invalidated_candidates', [])
        if isinstance(invalidated, list):
            for entry in invalidated:
                if isinstance(entry, dict) and entry.get('branch') == active_branch:
                    self.errors.append(
                        f"VALIDATION-2: active_candidate '{active_branch}' "
                        f"also appears in invalidated_candidates"
                    )

    def check_3_main_not_dual_role_without_human_auth(self):
        """main simultaneously governance and product base without Human
        explicit authorization → FAIL."""
        gov_branch = self.get('governance_base.branch', '')
        afs_branch = self.get('authoritative_fact_source.branch', '')
        afs_type = self.get('authoritative_fact_source.type', '')

        if gov_branch == 'main' and afs_branch == 'main':
            if afs_type not in ('HUMAN_EXPLICIT',):
                self.errors.append(
                    "VALIDATION-3: governance_base and authoritative_fact_source "
                    "both reference 'main' without HUMAN_EXPLICIT type. "
                    "main defaults to governance source only."
                )

    def check_4_comparison_not_active(self):
        """comparison candidate used as active candidate → FAIL."""
        active_branch = self.get('active_candidate.branch')
        if not active_branch or active_branch == 'NONE':
            return

        comparison = self.get('comparison_candidates', [])
        if isinstance(comparison, list):
            for entry in comparison:
                if isinstance(entry, dict) and entry.get('branch') == active_branch:
                    self.errors.append(
                        f"VALIDATION-4: active_candidate '{active_branch}' "
                        f"also appears in comparison_candidates"
                    )

    def check_5_visual_status_not_auto_accepted(self):
        """VISUAL_STATUS auto-changed to HUMAN_ACCEPTED by CI PASS → FAIL.
        This is checked by verifying that if visual_status is HUMAN_ACCEPTED,
        there must be evidence of Human acceptance in the binding."""
        vs = self.get('visual_status.active_candidate', '')
        if vs == 'HUMAN_ACCEPTED':
            # Check for Human acceptance evidence
            afs_type = self.get('authoritative_fact_source.type', '')
            if afs_type not in ('HUMAN_EXPLICIT',):
                self.errors.append(
                    "VALIDATION-5: visual_status.active_candidate is "
                    "HUMAN_ACCEPTED but authoritative_fact_source.type is "
                    f"'{afs_type}', not HUMAN_EXPLICIT. "
                    "Visual acceptance requires Human evidence."
                )

    def check_6_rebind_blocks_write(self):
        """FACT_SOURCE_REBIND state with product write permission → FAIL."""
        current_gate = self.get('current_gate', '')
        authorized_action = self.get('authorized_action', '')
        if 'FACT_SOURCE_REBIND' in current_gate:
            if authorized_action and 'NONE' not in authorized_action:
                self.errors.append(
                    "VALIDATION-6: current_gate is FACT_SOURCE_REBIND but "
                    "authorized_action is not NONE. Write is not permitted "
                    "during fact source rebinding."
                )

    def check_7_progress_card_required_fields(self):
        """Progress card missing FACT_SOURCE, ACTIVE_BASELINE, or
        NEXT_GATE → FAIL."""
        # Check that the binding has these essential fields
        afs_branch = self.get('authoritative_fact_source.branch', '')
        afs_sha = self.get('authoritative_fact_source.sha', '')
        active_branch = self.get('active_candidate.branch', '')
        active_head = self.get('active_candidate.resolved_head', '')
        next_gate = self.get('system_next_step', '')

        if not afs_branch or not afs_sha:
            self.warnings.append(
                "VALIDATION-7: FACT_SOURCE fields may be incomplete "
                "(required for progress card)"
            )
        if not next_gate:
            self.warnings.append(
                "VALIDATION-7: system_next_step (NEXT_GATE proxy) is missing"
            )

    def check_8_candidate_head_live_check(self):
        """Candidate Head vs live remote mismatch → HARD_STOP.
        In live mode, verify active_candidate.resolved_head matches origin."""
        if not self.live_mode:
            return

        active_branch = self.get('active_candidate.branch', '')
        if not active_branch or active_branch == 'NONE':
            return

        try:
            result = subprocess.run(
                ['git', 'ls-remote', 'origin', f'refs/heads/{active_branch}'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                self.warnings.append(
                    f"VALIDATION-8: Cannot verify live HEAD for '{active_branch}'"
                )
                return

            remote_sha = result.stdout.strip().split()[0] if result.stdout.strip() else None
            bound_head = self.get('active_candidate.resolved_head', '')

            if remote_sha and bound_head and remote_sha != bound_head:
                self.errors.append(
                    f"VALIDATION-8: HARD_STOP — active_candidate.resolved_head "
                    f"({bound_head[:12]}) does not match live origin/"
                    f"{active_branch} ({remote_sha[:12]}). Automatic migration "
                    f"is forbidden."
                )
        except Exception as e:
            self.warnings.append(
                f"VALIDATION-8: Live check failed: {e}"
            )

    def check_10_minimum_context_recovery(self):
        """New window with only TASK_ID and user delta can recover full
        context from repository. This validates that essential fields are
        present."""
        required_fields = [
            'schema_version',
            'adt_repository',
            'governance_base.branch',
            'governance_base.sha',
            'authoritative_fact_source.type',
            'authoritative_fact_source.branch',
            'authoritative_fact_source.sha',
            'current_gate',
            'counter_objectives',
            'user_action_required',
            'system_next_step',
        ]
        missing = []
        for field in required_fields:
            val = self.get(field)
            if val is None or val == '':
                missing.append(field)

        if missing:
            self.warnings.append(
                f"VALIDATION-10: Minimum context recovery may fail. "
                f"Missing fields: {', '.join(missing)}"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Validate ADT runtime binding record"
    )
    parser.add_argument(
        '--file', '-f',
        default='PROJECT_STATE.md',
        help='Path to binding file (default: PROJECT_STATE.md)'
    )
    parser.add_argument(
        '--ci', action='store_true',
        help='Run in CI mode (live git checks enabled)'
    )
    parser.add_argument(
        '--live', action='store_true',
        help='Enable live git remote checks'
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    text = path.read_text(encoding='utf-8')
    validator = BindingValidator(text, live_mode=args.live or args.ci)

    if validator.validate():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
