#!/usr/bin/env python3
"""Candidate history immutability validator.

Runs in CI on push, delete, and pull_request events for formal candidate
branches matching hermes/**, codex/**, agent/**, maker/**.

Detects forced pushes, branch deletions, non-fast-forward ancestry, missing
or unresolvable event fields, illegal branch-creation bases, and PRs from
permanently disqualified branches.

The ruleset (non_fast_forward + deletion) is the primary physical block;
this validator is the detection and audit layer. It MUST NOT claim that CI
prevents force-push — the ruleset does.

On history-rewrite detection, persists a permanent disqualification record
outside the candidate branch via refs/adt/disqualified/<safe-branch-name>.
Once disqualified, the branch and any associated PR permanently lose
Audit, Ready, and Merge eligibility.  Subsequent normal commits on the same
branch do not auto-recover.  A new branch and new PR are required.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# ── Constants ──────────────────────────────────────────────────
CANDIDATE_PREFIXES = ("refs/heads/hermes/", "refs/heads/codex/",
                      "refs/heads/agent/", "refs/heads/maker/")
DISQUALIFIED_REF_PREFIX = "refs/adt/disqualified/"
ZERO_SHA = "0" * 40

# Result codes
PASS = "PASS"
HARD_STOP = "HARD_STOP"
DISQUALIFY = "DISQUALIFY"
BLOCKED_BY_HISTORY = "BLOCKED_BY_HISTORY"


# ── Helpers ─────────────────────────────────────────────────────
def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], text=True, capture_output=True,
                          check=False, timeout=30)


def _is_ancestor(ancestor: str, head: str) -> bool | None:
    """Return True if ancestor is reachable from head, False if not,
    None if unresolvable."""
    try:
        cp = _git("merge-base", "--is-ancestor", ancestor, head)
        return cp.returncode == 0
    except Exception:
        return None


def _commit_exists(sha: str) -> bool:
    """Check if a commit object exists in the local clone."""
    if not sha or sha == ZERO_SHA:
        return False
    try:
        return _git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
    except Exception:
        return False


def _is_candidate_branch(ref: str) -> bool:
    """Check if a ref matches formal candidate branch prefixes."""
    return ref.startswith(CANDIDATE_PREFIXES)


def _safe_name(branch: str) -> str:
    """Strip refs/heads/ and replace / with - for a safe ref component."""
    name = branch.removeprefix("refs/heads/")
    return name.replace("/", "-")


# ── GitHub API helpers (gh CLI) ─────────────────────────────────
def _gh_api(*args: str) -> dict[str, Any] | None:
    """Call gh api and return parsed JSON, or None on failure."""
    try:
        cp = subprocess.run(["gh", "api", *args], text=True,
                            capture_output=True, check=False, timeout=30)
        if cp.returncode == 0 and cp.stdout.strip():
            return json.loads(cp.stdout)
    except Exception:
        pass
    return None


def _get_repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "")


def _ref_exists(repo: str, ref: str) -> bool:
    """Check if a Git ref exists via the GitHub API."""
    safe_ref = ref.removeprefix("refs/").replace("/", "%2F")
    result = _gh_api(f"repos/{repo}/git/ref/{safe_ref}")
    return result is not None


def _create_ref(repo: str, ref: str, sha: str) -> bool:
    """Create a Git ref via the GitHub API. Returns True on success."""
    result = _gh_api("--method", "POST",
                     f"repos/{repo}/git/refs",
                     "-f", f"ref={ref}",
                     "-f", f"sha={sha}")
    return result is not None


# ── Disqualification persistence ─────────────────────────────────
def _disqualification_ref(branch: str) -> str:
    """Build the disqualification ref for a branch."""
    return f"{DISQUALIFIED_REF_PREFIX}{_safe_name(branch)}"


def is_disqualified(repo: str, branch: str) -> bool:
    """Check if a candidate branch has been permanently disqualified."""
    ref = _disqualification_ref(branch)
    return _ref_exists(repo, ref)


def persist_disqualification(repo: str, branch: str, pr_number: int | None,
                             violation_type: str, evidence: dict[str, Any],
                             target_sha: str) -> bool:
    """Create a permanent disqualification ref for a branch.

    The ref points to the violating commit SHA, encoding the violation
    facts as a durable evidence record outside the candidate branch.
    """
    ref = _disqualification_ref(branch)
    try:
        return _create_ref(repo, ref, target_sha)
    except Exception:
        return False


# ── Event parsing ───────────────────────────────────────────────
def get_event_info() -> dict[str, Any]:
    """Parse GitHub event from environment and event payload."""
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    repo = _get_repo()
    info: dict[str, Any] = {
        "event_name": event_name,
        "repo": repo,
        "ref": os.environ.get("GITHUB_REF", ""),
        "sha": os.environ.get("GITHUB_SHA", ""),
    }
    if event_path and Path(event_path).exists():
        try:
            payload = json.loads(Path(event_path).read_text())
            info["payload"] = payload
        except (OSError, json.JSONDecodeError):
            info["payload"] = {}
    else:
        info["payload"] = {}
    return info


def _push_branch_from_info(info: dict[str, Any]) -> str | None:
    """Extract push branch from event info."""
    ref = info.get("ref", "")
    if ref.startswith("refs/heads/"):
        return ref
    # Fallback to event payload
    payload = info.get("payload", {})
    event_ref = payload.get("ref", "")
    if event_ref.startswith("refs/heads/"):
        return event_ref
    return None


# ── Push event validation ───────────────────────────────────────
def check_push(info: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Validate a push event on a candidate branch.

    Returns (result_code, message, evidence_dict).
    """
    payload = info.get("payload", {})
    ref = _push_branch_from_info(info) or payload.get("ref", "")
    before = payload.get("before", "")
    after = payload.get("after", "")
    forced = payload.get("forced", False)
    deleted = payload.get("deleted", False)
    repo = info.get("repo", "")
    evidence: dict[str, Any] = {"ref": ref, "before": before,
                                 "after": after, "forced": forced}

    # Not a candidate branch → skip (not an error)
    if not _is_candidate_branch(ref):
        return PASS, "not a candidate branch", evidence

    # Missing critical fields → fail-closed
    if not before or not after:
        return (HARD_STOP,
                "HARD_STOP: push event missing before/after fields", evidence)

    # Branch creation (before = zeros) → verify base is main
    if before == ZERO_SHA:
        return _check_branch_creation(ref, after, evidence)

    # Deletion via push event (after = zeros) → disqualify
    if after == ZERO_SHA:
        return (DISQUALIFY,
                "DISQUALIFY: branch deletion detected via push event",
                evidence)

    # Forced push → disqualify immediately
    if forced:
        evidence["violation"] = "forced_push"
        return (DISQUALIFY,
                "DISQUALIFY: forced push detected (event.forced=true)",
                evidence)

    # Check ancestry for non-fast-forward
    if not _commit_exists(before):
        # The 'before' commit was demolished → evidence of force push
        evidence["violation"] = "before_commit_missing"
        evidence["note"] = "before commit no longer exists; history was overwritten"
        return (DISQUALIFY,
                "DISQUALIFY: before commit missing — history was overwritten",
                evidence)

    ancestry = _is_ancestor(before, after)
    if ancestry is None:
        return (HARD_STOP,
                "HARD_STOP: cannot resolve ancestry between before and after",
                evidence)
    if not ancestry:
        evidence["violation"] = "non_fast_forward"
        return (DISQUALIFY,
                "DISQUALIFY: non-fast-forward update (before is not ancestor of after)",
                evidence)

    return PASS, "ok", evidence


def _check_branch_creation(ref: str, after: str,
                           evidence: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Verify a new candidate branch is created from main."""
    # For branch creation, check that the first commit's parent chain
    # reaches main. We verify that the branch HEAD is a descendant of
    # origin/main. If we can't verify, fail-closed.
    main_sha = None
    try:
        cp = _git("rev-parse", "refs/remotes/origin/main")
        if cp.returncode == 0:
            main_sha = cp.stdout.strip()
    except Exception:
        pass

    if not main_sha:
        return (HARD_STOP,
                "HARD_STOP: cannot resolve origin/main for branch creation check",
                evidence)

    ancestry = _is_ancestor(main_sha, after)
    if ancestry is None:
        return (HARD_STOP,
                "HARD_STOP: cannot verify branch creation ancestry to main",
                evidence)
    if not ancestry:
        evidence["violation"] = "illegal_branch_creation_base"
        evidence["main_sha"] = main_sha
        return (DISQUALIFY,
                "DISQUALIFY: new branch does not derive from main",
                evidence)

    return PASS, "branch creation from main verified", evidence


# ── Delete event validation ─────────────────────────────────────
def check_delete(info: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Validate a branch deletion event.

    Branch deletions on candidate branches are treated as history
    rewrite and result in permanent disqualification.
    """
    payload = info.get("payload", {})
    ref = payload.get("ref", "")
    ref_type = payload.get("ref_type", "")
    repo = info.get("repo", "")
    evidence: dict[str, Any] = {"ref": ref, "ref_type": ref_type}

    if ref_type != "branch":
        return PASS, "not a branch deletion", evidence

    if not _is_candidate_branch(ref):
        return PASS, "not a candidate branch", evidence

    evidence["violation"] = "branch_deletion"
    return (DISQUALIFY,
            "DISQUALIFY: candidate branch was deleted",
            evidence)


# ── Pull-request eligibility check ──────────────────────────────
def check_pr_eligibility(info: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Check if a pull request's head branch has been disqualified.

    Block audit/ready/merge for PRs from permanently disqualified branches.
    """
    payload = info.get("payload", {})
    pr_data = payload.get("pull_request", {})
    head = pr_data.get("head", {})
    head_ref = head.get("ref", "")
    head_sha = head.get("sha", "")
    pr_number = pr_data.get("number")
    repo = info.get("repo", "")
    evidence: dict[str, Any] = {"head_ref": head_ref, "head_sha": head_sha,
                                 "pr_number": pr_number}

    if not head_ref:
        return PASS, "no head ref in PR payload", evidence

    if not _is_candidate_branch(f"refs/heads/{head_ref}"):
        return PASS, "not a candidate branch PR", evidence

    if is_disqualified(repo, head_ref):
        evidence["disqualified"] = True
        return (BLOCKED_BY_HISTORY,
                f"BLOCKED_BY_HISTORY: branch {head_ref} is permanently "
                f"disqualified due to prior history rewrite",
                evidence)

    return PASS, "branch not disqualified", evidence


# ── Main entry point ────────────────────────────────────────────
def main() -> int:
    info = get_event_info()
    event_name = info["event_name"]
    repo = info["repo"]
    errors: list[str] = []
    results: list[dict[str, Any]] = []

    if event_name == "push":
        code, msg, evidence = check_push(info)
        result = {"event": "push", "code": code, "message": msg,
                  "evidence": evidence}
        results.append(result)
        if code == HARD_STOP:
            errors.append(msg)
        elif code == DISQUALIFY:
            ref = evidence.get("ref", "")
            pr_number = evidence.get("pr_number")
            after = evidence.get("after", "")
            branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else ref
            if repo and branch and after:
                ok = persist_disqualification(
                    repo, branch, pr_number,
                    evidence.get("violation", "unknown"),
                    evidence, after)
                if not ok:
                    errors.append("FAILED_TO_PERSIST_DISQUALIFICATION")
                else:
                    evidence["disqualification_ref"] = _disqualification_ref(branch)

    elif event_name == "delete":
        code, msg, evidence = check_delete(info)
        result = {"event": "delete", "code": code, "message": msg,
                  "evidence": evidence}
        results.append(result)
        if code == DISQUALIFY:
            ref = evidence.get("ref", "")
            branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else ref
            if repo and branch:
                # For branch deletions, the 'after' SHA doesn't exist.
                # Point the disqualification ref to the repository's
                # default branch HEAD as an anchor.
                main_sha = ""
                try:
                    cp = _git("rev-parse", "refs/remotes/origin/main")
                    if cp.returncode == 0:
                        main_sha = cp.stdout.strip()
                except Exception:
                    pass
                if main_sha:
                    ok = persist_disqualification(
                        repo, branch, None,
                        evidence.get("violation", "unknown"),
                        evidence, main_sha)
                    if not ok:
                        errors.append("FAILED_TO_PERSIST_DISQUALIFICATION")
                    else:
                        evidence["disqualification_ref"] = _disqualification_ref(branch)

    elif event_name == "pull_request":
        code, msg, evidence = check_pr_eligibility(info)
        result = {"event": "pull_request", "code": code, "message": msg,
                  "evidence": evidence}
        results.append(result)
        if code == BLOCKED_BY_HISTORY:
            errors.append(msg)
    else:
        # Unknown event type on a candidate branch — warn but don't fail
        print(f"INFO: unhandled event type '{event_name}' — no history check applied")

    # Output
    for r in results:
        print(f"HISTORY_CHECK: {r['event']} -> {r['code']}")
        if r["code"] != PASS:
            print(f"  {r['message']}")
            if "disqualification_ref" in r.get("evidence", {}):
                print(f"  disqualification_ref: {r['evidence']['disqualification_ref']}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
