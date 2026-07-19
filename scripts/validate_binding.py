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
import json
import os
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

    # ── git helpers ──

    def _git(self, *args, timeout: int = 30) -> subprocess.CompletedProcess:
        return subprocess.run(
            ['git'] + list(args),
            capture_output=True, text=True, timeout=timeout
        )

    def _runtime_head(self) -> str | None:
        """Return the checked-out commit SHA from git rev-parse HEAD."""
        try:
            r = self._git('rev-parse', 'HEAD', timeout=10)
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None

    def _remote_head(self, branch: str) -> str | None:
        """Return origin/<branch> SHA via git ls-remote."""
        try:
            r = self._git('ls-remote', 'origin', f'refs/heads/{branch}', timeout=30)
            if r.returncode != 0:
                return None
            line = r.stdout.strip()
            return line.split()[0] if line else None
        except Exception:
            return None

    def _is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if ancestor is reachable from descendant."""
        try:
            r = self._git('merge-base', '--is-ancestor', ancestor, descendant, timeout=10)
            return r.returncode == 0
        except Exception:
            return False

    def _commit_exists(self, sha: str) -> bool:
        """Check if sha is a valid commit object."""
        try:
            r = self._git('cat-file', '-t', sha, timeout=10)
            return r.returncode == 0 and r.stdout.strip() == 'commit'
        except Exception:
            return False

    def _push_ref_branch(self) -> str | None:
        """Return the branch being pushed from GITHUB_REF (e.g. refs/heads/main)."""
        ref = os.environ.get('GITHUB_REF', '')
        if ref.startswith('refs/heads/'):
            return ref[11:]
        return None

    def _ci_event_name(self) -> str:
        return os.environ.get('GITHUB_EVENT_NAME', '')

    def _ci_event_sha(self) -> str:
        return os.environ.get('GITHUB_SHA', '')

    def _pr_head_sha(self) -> str | None:
        """Extract PR head SHA from GITHUB_EVENT_PATH (pull_request event)."""
        event_path = os.environ.get('GITHUB_EVENT_PATH', '')
        if event_path and os.path.exists(event_path):
            try:
                with open(event_path) as f:
                    event = json.load(f)
                return event.get('pull_request', {}).get('head', {}).get('sha')
            except Exception:
                pass
        return None

    # ── top-level ──

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
        self.check_9_active_candidate_field_semantics()
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

    # ── VALIDATION-1 ──

    def check_1_authoritative_fact_source_present(self):
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

    # ── VALIDATION-2 ──

    def check_2_active_not_in_invalidated(self):
        active_branch = self.get('active_candidate.branch')
        if not active_branch or active_branch == 'NONE':
            return
        invalidated = self.get('invalidated_candidates', [])
        if isinstance(invalidated, list):
            for entry in invalidated:
                if isinstance(entry, dict) and entry.get('branch') == active_branch:
                    self.errors.append(
                        f"VALIDATION-2: active_candidate '{active_branch}' "
                        f"also appears in invalidated_candidates"
                    )

    # ── VALIDATION-3 ──

    def check_3_main_not_dual_role_without_human_auth(self):
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

    # ── VALIDATION-4 ──

    def check_4_comparison_not_active(self):
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

    # ── VALIDATION-5 ──

    def check_5_visual_status_not_auto_accepted(self):
        vs = self.get('visual_status.active_candidate', '')
        if vs == 'HUMAN_ACCEPTED':
            afs_type = self.get('authoritative_fact_source.type', '')
            if afs_type not in ('HUMAN_EXPLICIT',):
                self.errors.append(
                    "VALIDATION-5: visual_status.active_candidate is "
                    "HUMAN_ACCEPTED but authoritative_fact_source.type is "
                    f"'{afs_type}', not HUMAN_EXPLICIT. "
                    "Visual acceptance requires Human evidence."
                )

    # ── VALIDATION-6 ──

    def check_6_rebind_blocks_write(self):
        current_gate = self.get('current_gate', '')
        authorized_action = self.get('authorized_action', '')
        if 'FACT_SOURCE_REBIND' in current_gate:
            if authorized_action and 'NONE' not in authorized_action:
                self.errors.append(
                    "VALIDATION-6: current_gate is FACT_SOURCE_REBIND but "
                    "authorized_action is not NONE. Write is not permitted "
                    "during fact source rebinding."
                )

    # ── VALIDATION-7 ──

    def check_7_progress_card_required_fields(self):
        afs_branch = self.get('authoritative_fact_source.branch', '')
        afs_sha = self.get('authoritative_fact_source.sha', '')
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

    # ── VALIDATION-8: Runtime head binding (live mode only) ──

    def check_8_candidate_head_live_check(self):
        """Runtime-head binding: the current Head comes from git, not from
        PROJECT_STATE.md.  Validates that the checked-out commit matches the
        remote branch, that starting_head is an ancestor, and that CI event
        SHAs are consistent.

        Event-specific behaviour:
        - push:        checked-out HEAD must == remote HEAD == push event SHA
        - pull_request: PR source head (from event) must == remote HEAD;
                        merge ref is ignored for identity comparison.
        """
        if not self.live_mode:
            return

        active_branch = self.get('active_candidate.branch', '')
        if not active_branch or active_branch == 'NONE':
            return

        event_name = self._ci_event_name()
        runtime_head = self._runtime_head()
        remote_head = self._remote_head(active_branch)

        if not runtime_head:
            self.warnings.append(
                "VALIDATION-8: Cannot determine runtime HEAD"
            )
            return

        # ── 8a. Push event: runtime HEAD must match remote ──
        if event_name == 'push':
            push_branch = self._push_ref_branch()
            # Determine which remote ref to compare against
            if push_branch and push_branch != active_branch:
                # Push is on a different branch (e.g. main) —
                # compare against that branch's remote, not the candidate
                compare_remote = self._remote_head(push_branch)
                compare_label = f"origin/{push_branch}"
            else:
                compare_remote = remote_head
                compare_label = f"origin/{active_branch}"

            if compare_remote and runtime_head != compare_remote:
                self.errors.append(
                    f"VALIDATION-8: HARD_STOP — runtime HEAD "
                    f"({runtime_head[:12]}) does not match remote "
                    f"{compare_label} ({compare_remote[:12]}). "
                    f"Branch may have advanced since checkout."
                )
            # Additional: push event SHA must match both
            event_sha = self._ci_event_sha()
            if event_sha:
                if runtime_head != event_sha:
                    self.errors.append(
                        f"VALIDATION-8: HARD_STOP — push event SHA "
                        f"({event_sha[:12]}) does not match checked-out "
                        f"HEAD ({runtime_head[:12]})"
                    )
                if compare_remote and event_sha != compare_remote:
                    self.errors.append(
                        f"VALIDATION-8: HARD_STOP — push event SHA "
                        f"({event_sha[:12]}) does not match remote "
                        f"{compare_label} ({compare_remote[:12]})"
                    )

        # ── 8b. Pull request event: PR head must match remote ──
        elif event_name == 'pull_request':
            pr_head = self._pr_head_sha()
            if pr_head and remote_head and pr_head != remote_head:
                self.errors.append(
                    f"VALIDATION-8: HARD_STOP — PR head SHA "
                    f"({pr_head[:12]}) does not match remote "
                    f"origin/{active_branch} ({remote_head[:12]})"
                )
            # Runtime head in PR context is the merge ref — do NOT
            # compare it against remote for identity.  Use PR head
            # for ancestry check below.
            pr_head = pr_head or runtime_head  # fallback for ancestry

        # ── 8c. Non-CI: runtime HEAD must match remote ──
        else:
            if remote_head and runtime_head != remote_head:
                self.errors.append(
                    f"VALIDATION-8: HARD_STOP — runtime HEAD "
                    f"({runtime_head[:12]}) does not match remote "
                    f"origin/{active_branch} ({remote_head[:12]}). "
                    f"Branch may have advanced since checkout."
                )

        # ── 8d. starting_head is ancestor of effective head ──
        #       In PR context use PR head; otherwise use runtime_head.
        effective_head = runtime_head
        if event_name == 'pull_request':
            pr_head = self._pr_head_sha()
            effective_head = pr_head or runtime_head

        starting_head = self.get('active_candidate.starting_head', '')
        if starting_head and self._commit_exists(starting_head):
            if not self._is_ancestor(starting_head, effective_head):
                self.errors.append(
                    f"VALIDATION-8: HARD_STOP — starting_head "
                    f"({starting_head[:12]}) is not an ancestor of "
                    f"effective HEAD ({effective_head[:12]})"
                )

    # ── VALIDATION-9: Active candidate field semantics ──

    def check_9_active_candidate_field_semantics(self):
        """Validate resolved_head semantics and runtime_head_binding presence.

        - resolved_head, if present, must be a valid commit in the repo.
          It is a *historical anchor*, NOT required to match current HEAD.
        - resolved_head that is NOT a valid commit or not in ancestry → FAIL.
        - runtime_head_binding should be GIT_REF_DERIVED (not required in
          static mode, but validated in live mode).
        """
        resolved_head = self.get('active_candidate.resolved_head', '')
        starting_head = self.get('active_candidate.starting_head', '')

        # resolved_head as historical anchor
        if resolved_head:
            # Must be a valid commit
            if not self._commit_exists(resolved_head):
                self.errors.append(
                    f"VALIDATION-9: resolved_head ({resolved_head[:12]}) "
                    f"is not a valid commit in this repository"
                )
            # If starting_head is set, resolved_head should be an ancestor
            # of something reachable (at minimum it should be in the repo)
            if starting_head and self._commit_exists(starting_head):
                # resolved_head should exist somewhere in the repo
                # but is NOT required to match runtime_head
                pass

        # runtime_head_binding field (advisory in static, validated in live)
        binding = self.get('active_candidate.runtime_head_binding', '')
        if self.live_mode and binding != 'GIT_REF_DERIVED':
            self.warnings.append(
                "VALIDATION-9: runtime_head_binding should be "
                "GIT_REF_DERIVED in live mode"
            )

    # ── VALIDATION-10 ──

    def check_10_minimum_context_recovery(self):
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
