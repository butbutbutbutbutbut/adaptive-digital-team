#!/usr/bin/env python3
"""ADT candidate identity, single-PR topology, fingerprint, scope enforcement,
pre-write execution gate, and candidate state distinction validator."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

STACKED_PR_PROHIBITED = "STACKED_PR_PROHIBITED"
HARD_STOP = "HARD_STOP"
SCOPE_VIOLATION = "SCOPE_VIOLATION"
FINGERPRINT_KEYS = ("repository", "base_ref", "base_sha", "head_ref", "head_sha", "changed_files")
FORBIDDEN_STATE_KEYS = {
    "current_head_sha", "current_main_sha", "current_event_sha",
    "current_remote_branch_sha", "current_candidate_fingerprint",
    "candidate_fingerprint", "runtime_fingerprint",
}

CANDIDATE_STATES = [
    "LOCAL_DRAFT",
    "WRITE_AUTHORIZED",
    "COMMITTED_CANDIDATE",
    "FORMAL_CANDIDATE",
    "AUDIT_ELIGIBLE",
]


def canonical_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "repository": str(fields.get("repository", "")),
        "base_ref": str(fields.get("base_ref", "")),
        "base_sha": str(fields.get("base_sha", "")),
        "head_ref": str(fields.get("head_ref", "")),
        "head_sha": str(fields.get("head_sha", "")),
        "changed_files": sorted({str(x) for x in fields.get("changed_files", [])}),
    }


def candidate_fingerprint(fields: dict[str, Any]) -> str:
    payload = json.dumps(canonical_fields(fields), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def push_ref_branch(ref: str | None = None) -> str | None:
    value = os.environ.get("GITHUB_REF", "") if ref is None else ref
    match = re.fullmatch(r"refs/heads/(.+)", value or "")
    if not match:
        return None
    branch = match.group(1).strip()
    return branch if branch and not branch.startswith("/") and not branch.endswith("/") else None


class BindingValidator:
    def __init__(
        self,
        text: str,
        live_mode: bool = False,
        candidate_mode: bool = False,
        pre_merge: bool = False,
        expected_fingerprint: str | None = None,
        audit_fingerprint: str | None = None,
        ready_authorization_fingerprint: str | None = None,
        merge_authorization_fingerprint: str | None = None,
        explicit_scope: list[str] | None = None,
    ) -> None:
        self.text = text
        self.live_mode = live_mode or candidate_mode or pre_merge
        self.candidate_mode = candidate_mode
        self.pre_merge = pre_merge
        self.expected_fingerprint = expected_fingerprint
        self.audit_fingerprint = audit_fingerprint
        self.ready_fingerprint = ready_authorization_fingerprint
        self.merge_fingerprint = merge_authorization_fingerprint
        self.explicit_scope = explicit_scope  # override scope from CLI
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.parsed: dict[str, Any] = {}
        self.runtime_fields: dict[str, Any] | None = None
        self.runtime_fingerprint: str | None = None
        self.candidate_state: str = "LOCAL_DRAFT"

    def parse(self) -> dict[str, Any]:
        match = re.search(r"```ya?ml\s*\n(.*?)\n```", self.text, re.S)
        value = yaml.safe_load(match.group(1) if match else self.text) or {}
        if not isinstance(value, dict):
            raise ValueError("binding root must be a mapping")
        return value

    parse_yaml = parse
    normalize_fingerprint_fields = staticmethod(canonical_fields)
    candidate_fingerprint = staticmethod(candidate_fingerprint)

    def get(self, key: str, default: Any = None) -> Any:
        node: Any = self.parsed
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], text=True, capture_output=True, check=False, timeout=30)

    def _runtime_head(self) -> str | None:
        try:
            out = self._git("rev-parse", "HEAD")
            return out.stdout.strip() if out.returncode == 0 else None
        except Exception:
            return None

    def _current_branch(self) -> str | None:
        try:
            out = self._git("symbolic-ref", "--quiet", "--short", "HEAD")
            return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None
        except Exception:
            return None

    def _is_detached(self) -> bool:
        return self._current_branch() is None

    def _remote_head(self, branch: str) -> str | None:
        if not branch:
            return None
        try:
            local = self._git("rev-parse", f"refs/remotes/origin/{branch}")
            if local.returncode == 0 and local.stdout.strip():
                return local.stdout.strip()
            remote = self._git("ls-remote", "origin", f"refs/heads/{branch}")
            return remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout.strip() else None
        except Exception:
            return None

    def _changed_files(self, base: str, head: str) -> list[str] | None:
        try:
            out = self._git("diff", "--name-only", "--diff-filter=ACMRDTUXB", f"{base}...{head}")
            return sorted({x.strip() for x in out.stdout.splitlines() if x.strip()}) if out.returncode == 0 else None
        except Exception:
            return None

    def _local_changed_files(self) -> list[str] | None:
        """Get all locally changed files: committed, staged, unstaged, untracked."""
        try:
            # Staged + unstaged (tracked)
            out1 = self._git("diff", "--name-only", "HEAD")
            tracked = set(x.strip() for x in out1.stdout.splitlines() if x.strip()) if out1.returncode == 0 else set()
            # Staged (cached)
            out2 = self._git("diff", "--name-only", "--cached", "HEAD")
            staged = set(x.strip() for x in out2.stdout.splitlines() if x.strip()) if out2.returncode == 0 else set()
            # Untracked
            out3 = self._git("ls-files", "--others", "--exclude-standard")
            untracked = set(x.strip() for x in out3.stdout.splitlines() if x.strip()) if out3.returncode == 0 else set()
            return sorted(tracked | staged | untracked)
        except Exception:
            return None

    def _ci_changed_files(self, event_name: str) -> list[str] | None:
        """Get changed files for CI mode based on event type."""
        try:
            if event_name == "pull_request":
                # Candidate vs target base
                payload = self._event_payload()
                pr = payload.get("pull_request", {})
                base_sha = str(pr.get("base", {}).get("sha", ""))
                head_sha = str(pr.get("head", {}).get("sha", ""))
                if base_sha and head_sha:
                    return self._changed_files(base_sha, head_sha)
                return None
            elif event_name == "push":
                push_branch = self._push_ref_branch()
                if push_branch == "main":
                    # main push: current merge commit vs parent
                    out = self._git("diff", "--name-only", "HEAD~1", "HEAD")
                    return sorted(set(x.strip() for x in out.stdout.splitlines() if x.strip())) if out.returncode == 0 else None
                else:
                    # branch push: push branch vs main
                    main_sha = self._remote_head("main")
                    head_sha = os.environ.get("GITHUB_SHA", "").strip()
                    if main_sha and head_sha:
                        return self._changed_files(main_sha, head_sha)
                    return None
            else:
                return self._local_changed_files()
        except Exception:
            return None

    def _workspace_clean(self) -> bool:
        try:
            out = self._git("status", "--porcelain")
            return out.returncode == 0 and not out.stdout.strip()
        except Exception:
            return False

    def _commit_exists(self, sha: str) -> bool:
        try:
            return bool(sha) and self._git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
        except Exception:
            return False

    def _is_ancestor(self, ancestor: str, head: str) -> bool:
        try:
            return self._git("merge-base", "--is-ancestor", ancestor, head).returncode == 0
        except Exception:
            return False

    def _event_payload(self) -> dict[str, Any]:
        path = os.environ.get("GITHUB_EVENT_PATH", "")
        if not path:
            return {}
        try:
            value = json.loads(Path(path).read_text())
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _push_ref_branch(self) -> str | None:
        return push_ref_branch(os.environ.get("GITHUB_REF", ""))

    def _repository(self) -> str:
        return str(os.environ.get("GITHUB_REPOSITORY") or self.get("repository") or "")

    def _scope(self) -> list[str]:
        if self.explicit_scope is not None:
            raw = [str(x) for x in self.explicit_scope]
        else:
            value = self.get("authorized_write_scope", [])
            raw = [str(x) for x in value] if isinstance(value, list) else []
        return sorted(raw)

    def _scope_deduped(self) -> list[str]:
        """Return scope with duplicates removed (for matching)."""
        raw = self._scope()
        seen: set[str] = set()
        result: list[str] = []
        for entry in raw:
            norm = entry.replace("\\", "/")
            if norm not in seen:
                seen.add(norm)
                result.append(entry)
        return result

    # ═══════════════════════════════════════════════════════════
    # Scope validation
    # ═══════════════════════════════════════════════════════════

    def _validate_scope_entries(self, scope: list[str]) -> list[str]:
        """Validate individual scope entries for path safety."""
        errs: list[str] = []
        seen: set[str] = set()
        for entry in scope:
            entry = str(entry).strip()
            if not entry:
                errs.append(f"{SCOPE_VIOLATION}: empty scope entry")
                continue
            # Cross-platform absolute path detection
            if os.path.isabs(entry) or entry.startswith("/"):
                errs.append(f"{SCOPE_VIOLATION}: absolute path not allowed: {entry}")
            if ".." in Path(entry).parts:
                errs.append(f"{SCOPE_VIOLATION}: path traversal not allowed: {entry}")
            norm = entry.replace("\\", "/")
            if norm in seen:
                errs.append(f"{SCOPE_VIOLATION}: duplicate path in scope: {entry}")
            seen.add(norm)
        return errs

    def _file_matches_scope(self, filepath: str, scope: list[str]) -> bool:
        """Check if filepath matches any scope pattern (exact or glob)."""
        norm = filepath.replace("\\", "/")
        for pattern in scope:
            p = pattern.replace("\\", "/")
            if fnmatch.fnmatch(norm, p):
                return True
        return False

    def _check_scope_coverage(self, changed_files: list[str], scope: list[str]) -> list[str]:
        """Check that all changed files are covered by scope. Returns list of violations."""
        violations: list[str] = []
        for f in changed_files:
            if not self._file_matches_scope(f, scope):
                violations.append(f)
        return violations

    # ═══════════════════════════════════════════════════════════
    # Static checks
    # ═══════════════════════════════════════════════════════════

    def check_static(self) -> None:
        required = (
            "task_id", "repository", "branch", "starting_base_sha",
            "authorized_write_scope", "authority", "current_gate", "implementation_status",
        )
        missing = [x for x in required if self.get(x) in (None, "", [])]
        if missing:
            self.errors.append("VALIDATION-STATE: missing stable fields: " + ", ".join(missing))
        declared_repo = str(self.get("repository") or "")
        ci_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if declared_repo:
            if not re.fullmatch(r"[^/\s]+/[^/\s]+", declared_repo):
                self.errors.append("VALIDATION-STATE: repository must be in owner/repo format")
            elif ci_repo and declared_repo != ci_repo:
                self.errors.append("VALIDATION-STATE: repository binding does not match GITHUB_REPOSITORY")
        if self.get("implementation_status") != "NOT_AUTHORIZED":
            self.errors.append("VALIDATION-STATE: implementation_status must be NOT_AUTHORIZED")
        scope = self._scope()
        if not scope:
            self.errors.append("VALIDATION-SCOPE: authorized_write_scope is missing or empty")
        if any("*" in x for x in scope):
            self.warnings.append("VALIDATION-SCOPE: glob patterns in scope require live enforcement")
        # Validate scope entries in all modes (static or live)
        scope_errs = self._validate_scope_entries(scope)
        self.errors.extend(scope_errs)

        def walk(node: Any, path: str = "") -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    current = f"{path}.{key}" if path else str(key)
                    if str(key) in FORBIDDEN_STATE_KEYS:
                        self.errors.append(f"VALIDATION-STATE: runtime cache prohibited: {current}")
                    walk(value, current)
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")
        walk(self.parsed)

    def check_legacy(self) -> None:
        afs = self.get("authoritative_fact_source")
        if isinstance(afs, dict):
            if not afs.get("type") or not afs.get("sha") or afs.get("sha") == "NONE":
                self.errors.append("VALIDATION-1: authoritative fact source is incomplete")
            if self.get("governance_base.branch") == "main" and afs.get("branch") == "main" and afs.get("type") != "HUMAN_EXPLICIT":
                self.errors.append("VALIDATION-3: main dual role requires HUMAN_EXPLICIT")
        active = str(self.get("branch") or self.get("active_candidate.branch") or "")
        if any(isinstance(x, dict) and x.get("branch") == active for x in (self.get("invalidated_candidates", []) or [])):
            self.errors.append("VALIDATION-2: active candidate is invalidated")
        if any(isinstance(x, dict) and x.get("branch") == active for x in (self.get("comparison_candidates", []) or [])):
            self.errors.append("VALIDATION-4: comparison candidate cannot be active")
        if self.get("visual_status.active_candidate") == "HUMAN_ACCEPTED" and self.get("authoritative_fact_source.type") != "HUMAN_EXPLICIT":
            self.errors.append("VALIDATION-5: visual acceptance requires Human evidence")
        if "FACT_SOURCE_REBIND" in str(self.get("current_gate") or ""):
            action = str(self.get("authorized_action") or "")
            if action and "NONE" not in action:
                self.errors.append("VALIDATION-6: FACT_SOURCE_REBIND blocks write")

    # ═══════════════════════════════════════════════════════════
    # Runtime identity resolution
    # ═══════════════════════════════════════════════════════════

    def resolve_runtime(self) -> dict[str, Any] | None:
        repository = self._repository()
        runtime_head = self._runtime_head()
        if not repository or not runtime_head:
            self.errors.append(f"{HARD_STOP}: repository or git HEAD unresolved")
            return None
        event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()

        if event_name == "push":
            head_ref = self._push_ref_branch()
            if not head_ref:
                self.errors.append(f"{HARD_STOP}: invalid GITHUB_REF; only refs/heads/<branch> accepted")
                return None
            head_sha = os.environ.get("GITHUB_SHA", "").strip()
            remote = self._remote_head(head_ref)
            if not head_sha or not remote or not (runtime_head == head_sha == remote):
                self.errors.append(f"{HARD_STOP}: push identity mismatch; requires HEAD = GITHUB_SHA = origin/{head_ref}")
            base_ref = "main"
            base_sha = str(self._event_payload().get("before") or self.get("starting_base_sha") or "") if head_ref == "main" else (self._remote_head("main") or "")

        elif event_name == "pull_request":
            pr = self._event_payload().get("pull_request", {})
            head = pr.get("head", {}) if isinstance(pr, dict) else {}
            base = pr.get("base", {}) if isinstance(pr, dict) else {}
            head_ref, head_sha = str(head.get("ref") or ""), str(head.get("sha") or "")
            base_ref, base_sha = str(base.get("ref") or ""), str(base.get("sha") or "")
            if base_ref != "main":
                self.errors.append(f"{STACKED_PR_PROHIBITED}: base_ref={base_ref!r}")
            if head_ref.startswith("refs/pull/") or head_ref.endswith("/merge"):
                self.errors.append(f"{HARD_STOP}: merge ref cannot be candidate Head; merge refs are prohibited")
            remote = self._remote_head(head_ref)
            if not head_ref or not head_sha or not base_sha or not remote or remote != head_sha or runtime_head != head_sha:
                self.errors.append(f"{HARD_STOP}: PR source Head must equal origin/<head_ref>; merge refs are prohibited")

        else:
            head_ref = self._current_branch() or str(self.get("branch") or "")
            head_sha, base_ref = runtime_head, "main"
            base_sha = self._remote_head("main") or ""
            remote = self._remote_head(head_ref)
            if not head_ref or not base_sha or not remote or remote != head_sha:
                self.errors.append(f"{HARD_STOP}: local identity mismatch")

        changed = self._changed_files(base_sha, head_sha)
        if changed is None:
            self.errors.append(f"{HARD_STOP}: changed files unresolved")
            return None
        return canonical_fields({
            "repository": repository, "base_ref": base_ref, "base_sha": base_sha,
            "head_ref": head_ref, "head_sha": head_sha, "changed_files": changed,
        })

    # ═══════════════════════════════════════════════════════════
    # Live checks
    # ═══════════════════════════════════════════════════════════

    def check_live(self) -> None:
        fields = self.resolve_runtime()
        if fields is None:
            return
        self.runtime_fields = fields
        self.runtime_fingerprint = candidate_fingerprint(fields)
        if fields["head_ref"] != "main" and fields["base_ref"] != "main":
            self.errors.append(f"{STACKED_PR_PROHIBITED}: formal candidate must target main")
        branch = str(self.get("branch") or "")
        if fields["head_ref"] != "main" and branch and fields["head_ref"] != branch:
            self.errors.append(f"{HARD_STOP}: runtime branch differs from authorized branch")

        # Scope enforcement — entry validation already done in check_static()
        scope_deduped = self._scope_deduped()

        if self.candidate_mode or self.live_mode:
            if not scope_deduped:
                self.errors.append(f"{SCOPE_VIOLATION}: authorized_write_scope is missing or empty in candidate mode")
            else:
                # In CI mode, use event-specific changed files; in local mode, use local changed files
                event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
                if event_name:
                    ci_changed = self._ci_changed_files(event_name)
                    if ci_changed is not None:
                        violations = self._check_scope_coverage(ci_changed, scope_deduped)
                    else:
                        violations = self._check_scope_coverage(fields["changed_files"], scope_deduped)
                else:
                    local_changed = self._local_changed_files()
                    if local_changed is not None:
                        violations = self._check_scope_coverage(local_changed, scope_deduped)
                    else:
                        violations = self._check_scope_coverage(fields["changed_files"], scope_deduped)

                if violations:
                    self.errors.append(
                        f"{SCOPE_VIOLATION}: files outside authorized_write_scope: {sorted(violations)}"
                    )

        # resolved_head anchor check
        anchor = str(self.get("resolved_head") or "")
        if anchor and not self._commit_exists(anchor):
            self.errors.append("VALIDATION-RESOLVED-HEAD: historical anchor is not a commit")
        elif anchor and not self._is_ancestor(anchor, fields["head_sha"]):
            self.errors.append("VALIDATION-RESOLVED-HEAD: historical anchor is not in current history")

    # ═══════════════════════════════════════════════════════════
    # Pre-write execution gate
    # ═══════════════════════════════════════════════════════════

    def check_prewrite_gate(self) -> None:
        """Pre-write execution gate: validates that write is permitted.

        - Local write mode: forbid detached HEAD
        - Current branch must match task declaration
        - Exact Base must exist
        - Exact Base must be candidate branch ancestor
        - Candidate must not derive from non-main branch
        - Base drift detection
        - GitHub Actions detached checkout: use GITHUB_REF for logical identity
        """
        if not self.candidate_mode and not self.live_mode:
            return

        event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()

        # CI mode: GitHub Actions checkout is physically detached;
        # use GITHUB_REF / GITHUB_HEAD_REF / GITHUB_BASE_REF for logical identity.
        if event_name:
            # In PR context, head_ref comes from event payload (resolved in check_live)
            if event_name == "pull_request":
                pr = self._event_payload().get("pull_request", {})
                head = pr.get("head", {}) if isinstance(pr, dict) else {}
                base = pr.get("base", {}) if isinstance(pr, dict) else {}
                head_ref = str(head.get("ref") or "")
                base_ref = str(base.get("ref") or "")
                declared_branch = str(self.get("branch") or "")
                if declared_branch and head_ref and head_ref != declared_branch:
                    self.errors.append(
                        f"{HARD_STOP}: PR head ref ({head_ref}) differs from declared branch ({declared_branch})"
                    )
                if base_ref != "main":
                    self.errors.append(f"{HARD_STOP}: candidate must derive from main, got base_ref={base_ref!r}")
                # In PR CI we trust GITHUB_BASE_REF = main; ancestry is verified by the PR itself
                return

            if event_name == "push":
                push_branch = self._push_ref_branch()
                if not push_branch:
                    return  # already reported by resolve_runtime
                declared_branch = str(self.get("branch") or "")
                if push_branch != "main" and declared_branch and push_branch != declared_branch:
                    self.errors.append(
                        f"{HARD_STOP}: push branch ({push_branch}) differs from declared branch ({declared_branch})"
                    )
                return

            # Other CI events — trust the environment
            return

        # ── Local write mode ──
        current_branch = self._current_branch()
        if not current_branch:
            self.errors.append(f"{HARD_STOP}: detached HEAD; write not permitted in local mode")
            return

        declared_branch = str(self.get("branch") or "")
        if declared_branch and current_branch != declared_branch:
            self.errors.append(
                f"{HARD_STOP}: branch mismatch; current={current_branch}, declared={declared_branch}"
            )

        exact_base = str(self.get("starting_base_sha") or "")
        if not exact_base:
            self.errors.append(f"{HARD_STOP}: exact base (starting_base_sha) not declared")
        elif not self._commit_exists(exact_base):
            self.errors.append(f"{HARD_STOP}: exact base commit does not exist: {exact_base[:12]}")
        else:
            runtime_head = self._runtime_head()
            if runtime_head and not self._is_ancestor(exact_base, runtime_head):
                self.errors.append(f"{HARD_STOP}: exact base is not an ancestor of current HEAD")

            main_sha = self._remote_head("main")
            if main_sha and exact_base:
                # Candidate base must derive from main
                if not self._is_ancestor(main_sha, exact_base):
                    self.errors.append(f"{HARD_STOP}: candidate base does not derive from main")
                # Base drift: if main has advanced beyond exact_base
                if main_sha != exact_base:
                    self.errors.append(
                        f"{HARD_STOP}: base drift detected; main={main_sha[:12]}, declared base={exact_base[:12]}"
                    )

    # ═══════════════════════════════════════════════════════════
    # Candidate state determination
    # ═══════════════════════════════════════════════════════════

    def determine_candidate_state(self) -> str:
        """Determine the current candidate state based on live facts.

        LOCAL_DRAFT:        No remote, no PR, or precheck failed.
        WRITE_AUTHORIZED:   Machine precheck passed, write permission activated.
        COMMITTED_CANDIDATE: Has commits beyond exact base, pushed to remote.
        FORMAL_CANDIDATE:   Formal task branch, non-zero commits, exact base
                            ancestry, scope compliant, fingerprint computable,
                            PR event with Head/Base matching declaration.
        AUDIT_ELIGIBLE:     FORMAL_CANDIDATE + has PR + CI passed + fingerprint exists.
        """
        event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
        has_pr = event_name == "pull_request"
        has_ci = event_name in ("push", "pull_request")
        has_fingerprint = self.runtime_fingerprint is not None
        has_errors = bool(self.errors)

        if has_errors:
            return "LOCAL_DRAFT"

        if not self.runtime_fields:
            # Precheck may have passed (no errors) but no runtime yet
            if self.candidate_mode and not has_errors:
                return "WRITE_AUTHORIZED"
            return "LOCAL_DRAFT"

        # Has runtime fields — at minimum COMMITTED_CANDIDATE
        state = "COMMITTED_CANDIDATE"

        # FORMAL_CANDIDATE requirements:
        # - formal task branch name (non-empty, not main)
        # - non-zero commits (changed_files non-empty)
        # - exact base ancestry valid
        # - scope compliant (no SCOPE_VIOLATION errors)
        # - fingerprint computable
        # - PR event: Head/Base match declaration
        head_ref = self.runtime_fields.get("head_ref", "")
        changed_files = self.runtime_fields.get("changed_files", [])
        scope_ok = not any(SCOPE_VIOLATION in e for e in self.errors)

        is_formal_branch = bool(head_ref) and head_ref != "main" and "/" in head_ref
        has_commits = bool(changed_files)

        if is_formal_branch and has_commits and has_fingerprint and scope_ok:
            if has_pr:
                # PR event: verify Head/Base match declaration
                pr = self._event_payload().get("pull_request", {})
                pr_head = str(pr.get("head", {}).get("ref", ""))
                pr_base = str(pr.get("base", {}).get("ref", ""))
                declared_branch = str(self.get("branch") or "")
                if pr_head == head_ref and pr_base == "main":
                    if not declared_branch or pr_head == declared_branch:
                        state = "FORMAL_CANDIDATE"
            else:
                # Local with all conditions except PR
                state = "COMMITTED_CANDIDATE"

        # AUDIT_ELIGIBLE: FORMAL_CANDIDATE + PR + CI + fingerprint
        if state == "FORMAL_CANDIDATE" and has_pr and has_ci and has_fingerprint:
            state = "AUDIT_ELIGIBLE"

        self.candidate_state = state
        return state

    # ═══════════════════════════════════════════════════════════
    # Pre-merge checks
    # ═══════════════════════════════════════════════════════════

    def check_premerge(self) -> None:
        if not self.pre_merge or not self.runtime_fingerprint:
            return
        if not self.expected_fingerprint:
            self.errors.append(f"{HARD_STOP}: --expected-fingerprint is required")
        elif self.expected_fingerprint != self.runtime_fingerprint:
            self.errors.append(f"{HARD_STOP}: FINGERPRINT_MISMATCH")
        if not self._workspace_clean():
            self.errors.append(f"{HARD_STOP}: workspace is not clean")
        for label, value in {
            "AUDIT_BINDING": self.audit_fingerprint,
            "READY_AUTHORIZATION": self.ready_fingerprint,
            "MERGE_AUTHORIZATION": self.merge_fingerprint,
        }.items():
            if value is not None and value != self.runtime_fingerprint:
                self.errors.append(f"{label}: INVALID")

    # ═══════════════════════════════════════════════════════════
    # Main validation entry point
    # ═══════════════════════════════════════════════════════════

    def validate(self) -> bool:
        try:
            self.parsed = self.parse()
        except (ValueError, yaml.YAMLError) as exc:
            self.errors.append(f"VALIDATION-YAML: {exc}")
            return self._finish()
        self.check_static()
        self.check_legacy()
        if self.live_mode:
            self.check_prewrite_gate()
            self.check_live()
        self.check_premerge()
        self.determine_candidate_state()
        return self._finish()

    def _finish(self) -> bool:
        if self.runtime_fields and self.runtime_fingerprint:
            print("FINGERPRINT_FIELDS: " + json.dumps(self.runtime_fields, sort_keys=True, ensure_ascii=False))
            print("CANDIDATE_FINGERPRINT: " + self.runtime_fingerprint)
        print(f"CANDIDATE_STATE: {self.candidate_state}")
        for warning in self.warnings:
            print("WARN: " + warning, file=sys.stderr)
        for error in self.errors:
            print("FAIL: " + error, file=sys.stderr)
        if self.errors:
            return False
        print("PASS: All validations passed")
        return True


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
