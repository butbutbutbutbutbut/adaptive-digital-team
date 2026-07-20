"""Tests for candidate history immutability validator.

Covers forced push, branch deletion, non-fast-forward ancestry, missing
event fields, unresolvable ancestry, legal/illegal branch creation,
persistent disqualification, PR blocking, fork security, and non-candidate
branch non-interference.

All tests use fixed event fixtures; no real force-push, branch deletion,
or ruleset bypass is attempted.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_candidate_history as vch  # noqa: E402

REPO = "test-owner/test-repo"
BRANCH = "hermes/adt-test-candidate-r1"
REF = f"refs/heads/{BRANCH}"
BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40
NEW_SHA = "c" * 40
ZEROS = "0" * 40
PR_NUMBER = 42


# ── Fixtures ────────────────────────────────────────────────────
def _push_payload(**overrides) -> dict:
    """Build a push event payload."""
    base = {
        "ref": REF,
        "before": BASE_SHA,
        "after": HEAD_SHA,
        "forced": False,
        "deleted": False,
        "commits": [],
    }
    base.update(overrides)
    return base


def _delete_payload(ref: str = REF) -> dict:
    return {"ref": ref, "ref_type": "branch"}


def _pr_payload(head_ref: str = BRANCH, head_sha: str = HEAD_SHA,
                base_ref: str = "main", base_sha: str = BASE_SHA,
                number: int = PR_NUMBER) -> dict:
    return {
        "pull_request": {
            "head": {"ref": head_ref, "sha": head_sha},
            "base": {"ref": base_ref, "sha": base_sha},
            "number": number,
        }
    }


def _make_info(event_name: str, payload: dict,
               repo: str = REPO, ref: str = REF) -> dict:
    return {
        "event_name": event_name,
        "repo": repo,
        "ref": ref,
        "sha": HEAD_SHA,
        "payload": payload,
    }


# ── Mock helpers ────────────────────────────────────────────────
def _mock_ancestry(monkeypatch, is_ancestor: bool | None = True):
    monkeypatch.setattr(vch, "_is_ancestor", lambda a, b: is_ancestor)


def _mock_commit_exists(monkeypatch, exists: bool = True):
    monkeypatch.setattr(vch, "_commit_exists", lambda sha: exists)


def _mock_ref_exists(monkeypatch, exists: bool = False):
    monkeypatch.setattr(vch, "_ref_exists", lambda repo, ref: exists)


def _mock_create_ref(monkeypatch, success: bool = True):
    monkeypatch.setattr(vch, "_create_ref", lambda repo, ref, sha: success)


def _mock_git_revparse(monkeypatch, main_sha: str = BASE_SHA):
    def _fake(*args):
        m = MagicMock()
        if args[0] == "rev-parse" and "main" in str(args):
            m.returncode = 0
            m.stdout = main_sha + "\n"
        else:
            m.returncode = 128
            m.stdout = ""
        return m
    monkeypatch.setattr(vch, "_git", _fake)


# ═══════════════════════════════════════════════════════════════
# 1. forced=true → DISQUALIFY
# ═══════════════════════════════════════════════════════════════
def test_forced_push_disqualifies(monkeypatch):
    info = _make_info("push", _push_payload(forced=True, after=NEW_SHA))
    _mock_commit_exists(monkeypatch, True)
    code, msg, ev = vch.check_push(info)
    assert code == vch.DISQUALIFY, msg
    assert "forced" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 2. deleted branch (delete event) → DISQUALIFY
# ═══════════════════════════════════════════════════════════════
def test_delete_event_disqualifies(monkeypatch):
    info = _make_info("delete", _delete_payload(), ref=REF)
    code, msg, ev = vch.check_delete(info)
    assert code == vch.DISQUALIFY, msg
    assert "deleted" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 3. non-fast-forward ancestry → DISQUALIFY
# ═══════════════════════════════════════════════════════════════
def test_non_fast_forward_disqualifies(monkeypatch):
    info = _make_info("push", _push_payload(forced=False, after=NEW_SHA))
    _mock_commit_exists(monkeypatch, True)
    _mock_ancestry(monkeypatch, False)  # not an ancestor
    code, msg, ev = vch.check_push(info)
    assert code == vch.DISQUALIFY, msg
    assert "non-fast-forward" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 4. missing before/after → HARD_STOP
# ═══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("missing", ["before", "after"])
def test_missing_before_after_hard_stop(monkeypatch, missing):
    payload = _push_payload()
    payload[missing] = ""
    info = _make_info("push", payload)
    code, msg, ev = vch.check_push(info)
    assert code == vch.HARD_STOP, msg


# ═══════════════════════════════════════════════════════════════
# 5. unresolvable ancestry → HARD_STOP
# ═══════════════════════════════════════════════════════════════
def test_unresolvable_ancestry_hard_stop(monkeypatch):
    info = _make_info("push", _push_payload(forced=False, after=NEW_SHA))
    _mock_commit_exists(monkeypatch, True)
    _mock_ancestry(monkeypatch, None)  # unresolvable
    code, msg, ev = vch.check_push(info)
    assert code == vch.HARD_STOP, msg


# ═══════════════════════════════════════════════════════════════
# 6. legal branch creation (from main) → PASS
# ═══════════════════════════════════════════════════════════════
def test_legal_branch_creation_pass(monkeypatch):
    info = _make_info("push", _push_payload(before=ZEROS, after=HEAD_SHA))
    _mock_git_revparse(monkeypatch, BASE_SHA)
    _mock_ancestry(monkeypatch, True)  # HEAD descends from main
    code, msg, ev = vch.check_push(info)
    assert code == vch.PASS, msg


# ═══════════════════════════════════════════════════════════════
# 7. illegal branch creation base → DISQUALIFY
# ═══════════════════════════════════════════════════════════════
def test_illegal_branch_creation_base_disqualifies(monkeypatch):
    info = _make_info("push", _push_payload(before=ZEROS, after=HEAD_SHA))
    _mock_git_revparse(monkeypatch, BASE_SHA)
    _mock_ancestry(monkeypatch, False)  # HEAD does NOT descend from main
    code, msg, ev = vch.check_push(info)
    assert code == vch.DISQUALIFY, msg
    assert "does not derive from main" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 8. before commit missing after force push → DISQUALIFY
# ═══════════════════════════════════════════════════════════════
def test_before_commit_missing_disqualifies(monkeypatch):
    info = _make_info("push", _push_payload(forced=False, after=NEW_SHA))
    _mock_commit_exists(monkeypatch, False)  # before was demolished
    code, msg, ev = vch.check_push(info)
    assert code == vch.DISQUALIFY, msg
    assert "before commit missing" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 9. subsequent normal commit on disqualified branch → still BLOCKED
# ═══════════════════════════════════════════════════════════════
def test_disqualified_branch_pr_blocked(monkeypatch):
    info = _make_info("pull_request", _pr_payload())
    _mock_ref_exists(monkeypatch, True)  # branch is disqualified
    code, msg, ev = vch.check_pr_eligibility(info)
    assert code == vch.BLOCKED_BY_HISTORY, msg


# ═══════════════════════════════════════════════════════════════
# 10. non-disqualified branch PR → PASS
# ═══════════════════════════════════════════════════════════════
def test_clean_branch_pr_pass(monkeypatch):
    info = _make_info("pull_request", _pr_payload())
    _mock_ref_exists(monkeypatch, False)  # branch is clean
    code, msg, ev = vch.check_pr_eligibility(info)
    assert code == vch.PASS, msg


# ═══════════════════════════════════════════════════════════════
# 11. non-candidate branch push → PASS (not flagged)
# ═══════════════════════════════════════════════════════════════
def test_non_candidate_branch_not_flagged(monkeypatch):
    ref = "refs/heads/feature/random"
    payload = _push_payload(ref=ref, forced=True)
    info = _make_info("push", payload, ref=ref)
    code, msg, ev = vch.check_push(info)
    assert code == vch.PASS, msg
    assert "not a candidate branch" in msg.lower()


# ═══════════════════════════════════════════════════════════════
# 12. non-candidate branch delete → PASS (not flagged)
# ═══════════════════════════════════════════════════════════════
def test_non_candidate_delete_not_flagged(monkeypatch):
    info = _make_info("delete", _delete_payload(ref="refs/heads/feature/random"),
                      ref="refs/heads/feature/random")
    code, msg, ev = vch.check_delete(info)
    assert code == vch.PASS


# ═══════════════════════════════════════════════════════════════
# 13. delete event for non-branch (tag) → PASS
# ═══════════════════════════════════════════════════════════════
def test_tag_delete_not_flagged(monkeypatch):
    payload = {"ref": "refs/tags/v1.0", "ref_type": "tag"}
    info = _make_info("delete", payload, ref="refs/tags/v1.0")
    code, msg, ev = vch.check_delete(info)
    assert code == vch.PASS


# ═══════════════════════════════════════════════════════════════
# 14. PR from fork — no special write permission, but read works
# ═══════════════════════════════════════════════════════════════
def test_fork_pr_read_only_check(monkeypatch):
    # Fork PRs use a different repo but we still check eligibility
    # The check is read-only (reads refs/adt/disqualified/...)
    fork_info = _make_info("pull_request", _pr_payload(
        head_ref="hermes/fork-contribution-r1"))
    # Simulate that the fork branch is NOT disqualified
    _mock_ref_exists(monkeypatch, False)
    code, msg, ev = vch.check_pr_eligibility(fork_info)
    assert code == vch.PASS  # Read check passes, no write attempted


# ═══════════════════════════════════════════════════════════════
# 15. disqualification ref naming
# ═══════════════════════════════════════════════════════════════
def test_disqualification_ref_naming():
    ref = vch._disqualification_ref("hermes/adt-test-candidate-r1")
    assert ref.startswith(vch.DISQUALIFIED_REF_PREFIX)
    assert "hermes-adt-test-candidate-r1" in ref
    assert "/" not in ref.removeprefix(vch.DISQUALIFIED_REF_PREFIX)


# ═══════════════════════════════════════════════════════════════
# 16. main() with push DISQUALIFY calls persist (mock)
# ═══════════════════════════════════════════════════════════════
def test_main_push_disqualify_persists(monkeypatch, tmp_path):
    event_file = tmp_path / "event.json"
    payload = _push_payload(forced=True, after=NEW_SHA)
    event_file.write_text(json.dumps(payload))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.setenv("GITHUB_REF", REF)
    monkeypatch.setenv("GITHUB_SHA", NEW_SHA)
    _mock_commit_exists(monkeypatch, True)
    _mock_create_ref(monkeypatch, True)
    _mock_git_revparse(monkeypatch, BASE_SHA)

    # Should not raise; exit code 0 means persisted ok
    result = vch.main()
    assert result == 0


# ═══════════════════════════════════════════════════════════════
# 17. safe_name edge cases
# ═══════════════════════════════════════════════════════════════
@pytest.mark.parametrize("branch,expected_suffix", [
    ("hermes/simple", "hermes-simple"),
    ("refs/heads/hermes/nested/path", "hermes-nested-path"),
    ("codex/deep/nested/branch-r1", "codex-deep-nested-branch-r1"),
])
def test_safe_name(branch, expected_suffix):
    name = vch._safe_name(branch)
    assert name == expected_suffix
