#!/usr/bin/env python3
"""ADT candidate identity, single-PR topology, and fingerprint validator."""
from __future__ import annotations

import argparse
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
FINGERPRINT_KEYS = ("repository", "base_ref", "base_sha", "head_ref", "head_sha", "changed_files")
FORBIDDEN_STATE_KEYS = {
    "current_head_sha", "current_main_sha", "current_event_sha",
    "current_remote_branch_sha", "current_candidate_fingerprint",
    "candidate_fingerprint", "runtime_fingerprint",
}


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
        pre_merge: bool = False,
        expected_fingerprint: str | None = None,
        audit_fingerprint: str | None = None,
        ready_authorization_fingerprint: str | None = None,
        merge_authorization_fingerprint: str | None = None,
    ) -> None:
        self.text = text
        self.live_mode = live_mode or pre_merge
        self.pre_merge = pre_merge
        self.expected_fingerprint = expected_fingerprint
        self.audit_fingerprint = audit_fingerprint
        self.ready_fingerprint = ready_authorization_fingerprint
        self.merge_fingerprint = merge_authorization_fingerprint
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.parsed: dict[str, Any] = {}
        self.runtime_fields: dict[str, Any] | None = None
        self.runtime_fingerprint: str | None = None

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
        # Push identity is derived exclusively from GITHUB_REF.
        return push_ref_branch(os.environ.get("GITHUB_REF", ""))

    def _repository(self) -> str:
        return str(os.environ.get("GITHUB_REPOSITORY") or self.get("repository") or "")

    def _scope(self) -> list[str]:
        value = self.get("authorized_write_scope", [])
        return sorted({str(x) for x in value}) if isinstance(value, list) else []

    def check_static(self) -> None:
        required = (
            "task_id", "repository", "branch", "starting_base_sha",
            "authorized_write_scope", "authority", "current_gate", "implementation_status",
        )
        missing = [x for x in required if self.get(x) in (None, "", [])]
        if missing:
            self.errors.append("VALIDATION-STATE: missing stable fields: " + ", ".join(missing))
        if self.get("repository") and self.get("repository") != "butbutbutbutbutbut/adaptive-digital-team":
            self.errors.append("VALIDATION-STATE: repository binding is incorrect")
        if self.get("implementation_status") != "NOT_AUTHORIZED":
            self.errors.append("VALIDATION-STATE: implementation_status must be NOT_AUTHORIZED")
        scope = self._scope()
        if not scope or any("*" in x for x in scope):
            self.errors.append("VALIDATION-SCOPE: exact non-wildcard paths required")

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
        if fields["head_ref"] != "main" and fields["changed_files"] != self._scope():
            actual, allowed = set(fields["changed_files"]), set(self._scope())
            unauthorized = sorted(actual - allowed)
            unchanged = sorted(allowed - actual)
            self.errors.append(f"{HARD_STOP}: authorized_write_scope mismatch; unauthorized={unauthorized}, authorized_but_unchanged={unchanged}")
        anchor = str(self.get("resolved_head") or "")
        if anchor and not self._commit_exists(anchor):
            self.errors.append("VALIDATION-RESOLVED-HEAD: historical anchor is not a commit")
        elif anchor and not self._is_ancestor(anchor, fields["head_sha"]):
            self.errors.append("VALIDATION-RESOLVED-HEAD: historical anchor is not in current history")

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

    def validate(self) -> bool:
        try:
            self.parsed = self.parse()
        except (ValueError, yaml.YAMLError) as exc:
            self.errors.append(f"VALIDATION-YAML: {exc}")
            return self._finish()
        self.check_static()
        self.check_legacy()
        if self.live_mode:
            self.check_live()
        self.check_premerge()
        return self._finish()

    def _finish(self) -> bool:
        if self.runtime_fields and self.runtime_fingerprint:
            print("FINGERPRINT_FIELDS: " + json.dumps(self.runtime_fields, sort_keys=True, ensure_ascii=False))
            print("CANDIDATE_FINGERPRINT: " + self.runtime_fingerprint)
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
        path.read_text(), live_mode=args.ci or args.live, pre_merge=args.pre_merge,
        expected_fingerprint=args.expected_fingerprint,
        audit_fingerprint=args.audit_fingerprint,
        ready_authorization_fingerprint=args.ready_authorization_fingerprint,
        merge_authorization_fingerprint=args.merge_authorization_fingerprint,
    )
    return 0 if validator.validate() else 1


if __name__ == "__main__":
    raise SystemExit(main())
