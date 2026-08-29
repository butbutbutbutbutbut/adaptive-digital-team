"""tests/test_p1_regressions.py — M4 P1 batch regression suite (Maker M4).

Five P1 fixes, one regression each (must be RED on pre-fix code, GREEN on
this branch):
  P1-1 validate_adapter: negative cases must fail the suite if the invalid
        document slips through (validate_document_should_reject)
  P1-2 validate_candidate_history: GitHub delete events carry a BARE branch
        name — _is_candidate_branch must normalize before matching
  P1-3 validate_candidate_history: gh API failure must fail-closed (block
        the PR) instead of releasing it
  P1-4 gate.py: empty git probe results must BLOCK write actions (drift
        unverifiable = drift)
  P1-5 validate_binding: governance gate must verify receipt task_id against
        the binding, and match governance paths case-insensitively
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_adapter  # noqa: E402
import validate_candidate_history as vch  # noqa: E402
from validate_binding import BindingValidator, HARD_STOP  # noqa: E402

REPO_ID = "Kairos-zhi/adaptive-digital-team"

# ═══════════════════════════════════════════════════════════
# Load the REAL gate module (as in M3)
# ═══════════════════════════════════════════════════════════

PLUGIN_DIR = REPO_ROOT / ".hermes" / "plugins" / "guarded_adapter"
PKG = "adt_ga_p1"


def _load(name: str, path: Path, is_pkg: bool = False):
    spec = importlib.util.spec_from_file_location(
        name, str(path), submodule_search_locations=[str(path.parent)] if is_pkg else None
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_pkg = _load(PKG, PLUGIN_DIR / "__init__.py", is_pkg=True)
runtime_models = _load(f"{PKG}.runtime_models", PLUGIN_DIR / "runtime_models.py")
gate = _load(f"{PKG}.gate", PLUGIN_DIR / "gate.py")

VALID_BINDING = {
    "authorization_id": "ADT-P1-001",
    "authority_source": "Human Holder directive",
    "human_role": "HUMAN_HOLDER",
    "repository": REPO_ID,
    "base_sha": "0" * 40,
    "branch": "maker/test",
    "authorized_actions": ["read", "write_file", "commit", "push"],
    "authorized_write_scope": ["docs/"],
    "task_id": "ADT-P1-001",
    "human_holder_approved": True,
}


def _stable_state(**changes) -> str:
    import yaml

    value = {
        "schema_version": "2",
        "repository": REPO_ID,
        "authority": {"holder": "Kairos", "maker": "UNASSIGNED", "checker": "UNASSIGNED"},
        "current_gate": "NO_ACTIVE_CANDIDATE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    value.update(changes)
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


# ═══════════════════════════════════════════════════════════
# P1-1: validate_adapter negative-case fail-open
# ═══════════════════════════════════════════════════════════


class TestP1_1NegativeFailClosed:
    def test_should_reject_returns_false_when_document_passes(self):
        """A negative case that unexpectedly PASSES must fail the suite.

        Pre-fix: validate_document returned True for both outcomes — a
        negative document that slipped through could never fail the run.
        The new function must exist AND return False for a passing doc.
        """
        fn = getattr(validate_adapter, "validate_document_should_reject", None)
        assert fn is not None, "validate_document_should_reject missing (fail-open not fixed)"
        assert fn({"type": "object"}, {"x": 1}, "negative-probe") is False

    def test_should_reject_returns_true_when_document_rejected(self):
        """Expected rejection still passes."""
        fn = getattr(validate_adapter, "validate_document_should_reject", None)
        assert fn is not None
        assert fn({"type": "object", "required": ["must_have"]}, {"x": 1}, "negative-probe") is True

    def test_valid_document_still_passes(self):
        assert validate_adapter.validate_document_should_pass(
            {"type": "object"}, {"x": 1}, "positive-probe"
        ) is True


# ═══════════════════════════════════════════════════════════
# P1-2: delete-event bare-branch detection
# ═══════════════════════════════════════════════════════════


class TestP1_2DeleteDetection:
    def test_bare_branch_name_matches_candidate(self):
        """GitHub delete events carry 'hermes/x' (no refs/heads/ prefix)."""
        assert vch._is_candidate_branch("hermes/feature") is True
        assert vch._is_candidate_branch("codex/x") is True
        assert vch._is_candidate_branch("maker/x") is True

    def test_full_ref_form_still_matches(self):
        """Push/PR form ('refs/heads/...') must keep matching."""
        assert vch._is_candidate_branch("refs/heads/hermes/feature") is True

    def test_non_candidate_branch_not_matched(self):
        assert vch._is_candidate_branch("refs/heads/main") is False
        assert vch._is_candidate_branch("main") is False
        assert vch._is_candidate_branch("feature/x") is False

    def test_delete_event_triggers_disqualify(self):
        """A delete event on a candidate branch must DISQUALIFY.

        Pre-fix: bare branch name never matched CANDIDATE_PREFIXES →
        check_delete returned PASS → history rewrite went undetected.
        """
        info = {
            "event_name": "delete", "repo": "owner/repo", "ref": "",
            "payload": {"ref": "hermes/feature", "ref_type": "branch"},
        }
        code, reason, _ev = vch.check_delete(info)
        assert code == vch.DISQUALIFY, reason


# ═══════════════════════════════════════════════════════════
# P1-3: gh API failure must fail-closed
# ═══════════════════════════════════════════════════════════


class TestP1_3GhFailureFailClosed:
    def test_gh_exception_blocks(self, monkeypatch):
        """API exception → cannot prove eligibility → disqualify (block).

        Pre-fix: _gh_api swallowed the exception → _ref_exists returned
        False → is_disqualified False → PR released (fail-open).
        """
        def boom(*args, **kwargs):
            raise OSError("gh CLI unavailable")

        monkeypatch.setattr(subprocess, "run", boom)
        assert vch.is_disqualified("owner/repo", "hermes/feature") is True

    def test_clean_404_does_not_block(self, monkeypatch):
        """A clean 404 (ref genuinely absent) must NOT block."""

        class _Ok:
            returncode = 1  # gh api exit 1 for 404
            stdout = ""
            stderr = ""

        monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Ok())
        assert vch.is_disqualified("owner/repo", "hermes/feature") is False


# ═══════════════════════════════════════════════════════════
# P1-4: gate empty-probe fail-closed
# ═══════════════════════════════════════════════════════════


class TestP1_4EmptyProbeBlocksWrite:
    def test_empty_probes_block_write(self, monkeypatch):
        """Write action + empty git probes → BLOCKED (drift unverifiable).

        Pre-fix: 'if current_repo and ...' skipped the checks on empty
        probes → write allowed (fail-open).
        """
        monkeypatch.setattr(gate, "_get_current_repo", lambda: "")
        monkeypatch.setattr(gate, "_get_current_base_sha", lambda: "")
        monkeypatch.setattr(gate, "_get_current_branch", lambda: "")
        req = gate.GateRequest(
            action_type="write_file", action_path="docs/x.md",
            plan_write_scope=["docs/"], authorized_write_scope=["docs/"],
            authorization_binding=dict(VALID_BINDING),
        )
        result = gate.validate_scope(req)
        assert not result.allowed
        assert "BINDING_MISMATCH" in (result.error or "")

    def test_empty_probes_do_not_block_read(self, monkeypatch):
        """Read-only action keeps working with empty probes."""
        monkeypatch.setattr(gate, "_get_current_repo", lambda: "")
        monkeypatch.setattr(gate, "_get_current_base_sha", lambda: "")
        monkeypatch.setattr(gate, "_get_current_branch", lambda: "")
        req = gate.GateRequest(
            action_type="read", action_path="",
            plan_write_scope=["docs/"], authorized_write_scope=["docs/"],
            authorization_binding=dict(VALID_BINDING),
        )
        result = gate.validate_scope(req)
        assert result.allowed, result.error

    def test_probes_matching_binding_still_pass(self, monkeypatch):
        monkeypatch.setattr(gate, "_get_current_repo", lambda: REPO_ID)
        monkeypatch.setattr(gate, "_get_current_base_sha", lambda: "0" * 40)
        monkeypatch.setattr(gate, "_get_current_branch", lambda: "maker/test")
        req = gate.GateRequest(
            action_type="write_file", action_path="docs/x.md",
            plan_write_scope=["docs/"], authorized_write_scope=["docs/"],
            authorization_binding=dict(VALID_BINDING),
        )
        result = gate.validate_scope(req)
        assert result.allowed, result.error


# ═══════════════════════════════════════════════════════════
# P1-5: governance gate — receipt task_id + case-insensitive match
# ═══════════════════════════════════════════════════════════


class TestP1_5GovernanceGate:
    @pytest.fixture()
    def gov_validator(self, tmp_path, monkeypatch):
        """BindingValidator with a loaded binding and controlled changed files."""
        hermes = tmp_path / ".hermes"
        hermes.mkdir(parents=True, exist_ok=True)
        (hermes / "CANDIDATE_BINDING.json").write_text(json.dumps(VALID_BINDING))
        monkeypatch.chdir(tmp_path)
        for var in ("GITHUB_EVENT_NAME", "GITHUB_EVENT_PATH", "GITHUB_REF",
                    "GITHUB_SHA", "GITHUB_REPOSITORY"):
            monkeypatch.delenv(var, raising=False)
        v = BindingValidator(_stable_state())
        v._binding = v._load_binding()
        assert v._binding is not None
        return v

    def test_stale_receipt_task_id_fails(self, gov_validator):
        """Receipt from a different task must NOT satisfy the gate.

        Pre-fix: only existence was checked — a stale receipt satisfied the
        governance gate forever.
        """
        receipt_path = Path(".hermes/checker_receipt.json")
        receipt_path.write_text(json.dumps({"task_id": "ADT-OTHER-TASK"}))
        gov_validator._local_changed_files = lambda: ["AGENTS.md"]
        gov_validator.check_governance_gate()
        assert any("task_id" in e and "GOVERNANCE" in e for e in gov_validator.errors)

    def test_matching_receipt_task_id_passes(self, gov_validator):
        receipt_path = Path(".hermes/checker_receipt.json")
        receipt_path.write_text(json.dumps({"task_id": "ADT-P1-001"}))
        gov_validator._local_changed_files = lambda: ["AGENTS.md"]
        gov_validator.check_governance_gate()
        assert not any("GOVERNANCE_CHECK_MISSING" in e for e in gov_validator.errors)

    def test_case_variant_hits_governance_gate(self, gov_validator):
        """'agents.md' (lowercase) must hit the AGENTS.md governance gate.

        Pre-fix: fnmatch is case-sensitive on Linux → 'agents.md' bypassed
        the gate entirely (no receipt required).
        """
        gov_validator._local_changed_files = lambda: ["agents.md"]
        gov_validator.check_governance_gate()
        assert any("GOVERNANCE_CHECK_MISSING" in e for e in gov_validator.errors)
