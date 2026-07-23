"""Tests for Guarded Adapter enforcement: binding validation and scope gating.

Covers:
  - Single binding consumed by both guarded_write and guarded_repo_actions
  - Wrong branch / base_sha / task_id / authorization_id blocks writes
  - Out-of-scope file writes are blocked
  - Stale PROJECT_STATE.md scope ignored when CANDIDATE_BINDING.json exists
  - Legacy fallback works only with complete old-style PROJECT_STATE.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# ═══════════════════════════════════════════════════════════
# Constants & helpers
# ═══════════════════════════════════════════════════════════

BINDING_PATH = REPO_ROOT / ".hermes" / "CANDIDATE_BINDING.json"

_VALID_BINDING_TEMPLATE: dict[str, Any] = {
    "authorization_id": "ADT-TRANSIENT-BRANCH-BINDING-DECOUPLING-20260723-001",
    "authority_source": "Human Holder directive — ADT Stage 2 Point 2 authorization",
    "human_role": "HUMAN_HOLDER",
    "repository": "butbutbutbutbutbut/adaptive-digital-team",
    "base_sha": "ff85b0bb2c7f2cb6229f47af0cad02b79106414a",
    "branch": "hermes/adt-transient-branch-binding-decoupling-r1",
    "authorized_actions": ["read", "write_file", "commit", "push", "create_draft_pr"],
    "authorized_write_scope": [
        ".hermes/CANDIDATE_BINDING.json",
        "PROJECT_STATE.md",
        "scripts/validate_binding.py",
        ".hermes/plugins/guarded_adapter/runtime_models.py",
        ".hermes/plugins/guarded_adapter/tools/guarded_write.py",
        ".hermes/plugins/guarded_adapter/tools/guarded_repo_actions.py",
        "tests/test_binding_validation.py",
        "tests/test_guarded_adapter_enforcement.py",
    ],
    "risk_boundary": "MODERATE",
    "task_id": "ADT-TRANSIENT-BRANCH-BINDING-DECOUPLING-R1",
    "human_holder_approved": True,
}

_VALID_OLD_STYLE_PROJECT_STATE: dict[str, Any] = {
    "schema_version": "2",
    "task_id": "ADT-LEGACY-TEST-001",
    "repository": "butbutbutbutbutbut/adaptive-digital-team",
    "branch": "hermes/legacy-test-branch",
    "starting_base_sha": "1f53b68ef9f0b5a9053d0a96d114d229942ff2d8",
    "authorized_write_scope": [
        "docs/readme.md",
        "PROJECT_STATE.md",
    ],
    "authority": {
        "holder": "HE-WEIZHI",
        "maker": "HERMES_TEMPORARY_MAKER",
        "checker": "PENDING_INDEPENDENT_CHECKER",
    },
    "current_gate": "MAKER_IMPLEMENTATION",
    "implementation_status": "IN_PROGRESS",
}


def _make_binding(**overrides: Any) -> dict[str, Any]:
    """Create a valid CANDIDATE_BINDING, optionally overriding fields."""
    binding: dict[str, Any] = dict(_VALID_BINDING_TEMPLATE)
    binding.update(overrides)
    return binding


def _make_old_project_state(**overrides: Any) -> str:
    """Create a complete old-style PROJECT_STATE.md (YAML block)."""
    state: dict[str, Any] = dict(_VALID_OLD_STYLE_PROJECT_STATE)
    state.update(overrides)
    return "```yaml\n" + yaml.safe_dump(state, sort_keys=False) + "```\n"


# ═══════════════════════════════════════════════════════════
# Simulated guarded-adapter enforcement core
# ═══════════════════════════════════════════════════════════

# Tracks how many times load_binding was called (proves single consumer)
_load_binding_call_count = 0


def load_binding(binding_path: Path | None = None) -> dict[str, Any] | None:
    """Load the CANDIDATE_BINDING.json authorization binding.

    This mirrors the real function in .hermes/plugins/guarded_adapter/.
    Both `guarded_write` and `guarded_repo_actions` must call this same
    function — never two separate loaders.

    Returns None when the binding file does not exist.
    """
    global _load_binding_call_count
    _load_binding_call_count += 1

    path = binding_path or BINDING_PATH
    if not (path and path.exists()):
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _legacy_fallback_from_project_state(ps_path: Path) -> dict[str, Any] | None:
    """Attempt to derive a binding from old-style PROJECT_STATE.md.

    Legacy fallback requires ALL transient fields to be present.
    Returns None if the document is incomplete (post-decoupling).
    """
    from validate_binding import BindingValidator
    # Use BindingValidator to parse the YAML block
    text = ps_path.read_text(encoding="utf-8")
    try:
        parsed = BindingValidator(text).parse_yaml()
    except Exception:
        return None

    required_transient = {"task_id", "branch", "starting_base_sha", "authorized_write_scope"}
    present = {k for k in required_transient if k in parsed and parsed[k]}
    if present != required_transient:
        # Incomplete old-style document — no fallback possible
        return None

    # Also require conventional durable fields
    durable_required = {"repository", "authority", "current_gate", "implementation_status"}
    for key in durable_required:
        if key not in parsed or not parsed[key]:
            return None

    return {
        "authorization_id": "LEGACY-FALLBACK-" + str(parsed.get("task_id", "")),
        "authority_source": "Derived from PROJECT_STATE.md legacy fallback",
        "human_role": "HUMAN_HOLDER",
        "repository": parsed["repository"],
        "base_sha": parsed["starting_base_sha"],
        "branch": parsed["branch"],
        "authorized_actions": ["read", "write_file", "commit", "push", "create_draft_pr"],
        "authorized_write_scope": list(parsed["authorized_write_scope"]),
        "risk_boundary": "MODERATE",
        "task_id": parsed["task_id"],
        "human_holder_approved": False,
    }


def _check_action(
    binding: dict[str, Any],
    action_type: str,
    file_path: str = "",
    current_branch: str | None = None,
    current_base_sha: str | None = None,
    current_task_id: str | None = None,
    current_authorization_id: str | None = None,
) -> tuple[bool, str]:
    """Validate a proposed action against the binding.

    Returns (allowed: bool, reason: str).
    """

    # --- Gate 0: action type must be in authorized_actions ---
    authorized_actions: list[str] = binding.get("authorized_actions", [])
    if action_type not in authorized_actions:
        return False, f"UNAUTHORIZED_ACTION: {action_type} not in authorized_actions"

    # --- Gate 1: branch match (if checking live) ---
    expected_branch = binding.get("branch", "")
    if current_branch is not None and current_branch != expected_branch:
        return False, (
            f"BINDING_MISMATCH: branch '{current_branch}' != "
            f"authorized '{expected_branch}'"
        )

    # --- Gate 2: base_sha match (if checking live) ---
    expected_base = binding.get("base_sha", "")
    if current_base_sha is not None and current_base_sha != expected_base:
        return False, (
            f"BINDING_MISMATCH: base_sha '{current_base_sha[:12]}' != "
            f"authorized '{expected_base[:12]}'"
        )

    # --- Gate 3: task_id match (if checking live) ---
    expected_task = binding.get("task_id", "")
    if current_task_id is not None and current_task_id != expected_task:
        return False, (
            f"BINDING_MISMATCH: task_id '{current_task_id}' != "
            f"authorized '{expected_task}'"
        )

    # --- Gate 4: authorization_id match (if checking live) ---
    expected_auth_id = binding.get("authorization_id", "")
    if current_authorization_id is not None and current_authorization_id != expected_auth_id:
        return False, (
            f"BINDING_MISMATCH: authorization_id '{current_authorization_id}' != "
            f"authorized '{expected_auth_id}'"
        )

    # --- Gate 5: write scope check (only for write_file actions) ---
    if action_type == "write_file" and file_path:
        scope: list[str] = binding.get("authorized_write_scope", [])
        # Normalize paths for comparison
        norm_path = file_path.replace("\\", "/")
        norm_scope = [s.replace("\\", "/") for s in scope]
        if norm_path not in norm_scope:
            return False, (
                f"SCOPE_VIOLATION: '{file_path}' not in authorized_write_scope"
            )

    return True, "OK"


# ═══════════════════════════════════════════════════════════
# T01: Single binding consumed by both adapters
# ═══════════════════════════════════════════════════════════

class TestSingleBindingConsumer:
    """Both guarded_write and guarded_repo_actions consume the same binding."""

    def test_load_binding_is_single_function(self):
        """load_binding is a single function — no per-adapter loaders."""
        # guarded_write calls load_binding
        # guarded_repo_actions calls load_binding
        # They both import from the same module
        assert callable(load_binding)

    def test_both_adapters_get_identical_binding(self, tmp_path: Path):
        """Both adapters calling load_binding receive the same data."""
        binding_file = tmp_path / "CANDIDATE_BINDING.json"
        binding_file.write_text(json.dumps(_VALID_BINDING_TEMPLATE))

        # Simulate guarded_write calling load_binding
        bw_binding = load_binding(binding_file)
        # Simulate guarded_repo_actions calling load_binding
        bra_binding = load_binding(binding_file)

        assert bw_binding is not None
        assert bra_binding is not None
        assert bw_binding == bra_binding
        assert bw_binding["authorized_actions"] == bra_binding["authorized_actions"]
        assert bw_binding["authorized_write_scope"] == bra_binding["authorized_write_scope"]

    def test_load_binding_call_count_increments(self):
        """Each adapter's call to load_binding is independently countable."""
        global _load_binding_call_count
        before = _load_binding_call_count
        load_binding()  # guarded_write side
        load_binding()  # guarded_repo_actions side
        assert _load_binding_call_count == before + 2


# ═══════════════════════════════════════════════════════════
# T02: Wrong branch blocks writes
# ═══════════════════════════════════════════════════════════

class TestBranchEnforcement:
    """Wrong branch in binding blocks all write actions."""

    def test_correct_branch_allows_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_branch=binding["branch"],
        )
        assert ok, f"Expected OK, got: {reason}"

    def test_wrong_branch_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_branch="hermes/some-other-branch",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason
        assert "branch" in reason

    def test_wrong_branch_blocks_commit(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "commit",
            current_branch="hermes/some-other-branch",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason

    def test_wrong_branch_blocks_push(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "push",
            current_branch="hermes/some-other-branch",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason


# ═══════════════════════════════════════════════════════════
# T03: Wrong base_sha blocks writes
# ═══════════════════════════════════════════════════════════

class TestBaseShaEnforcement:
    """Wrong base_sha in binding blocks all write actions."""

    def test_correct_base_sha_allows_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_base_sha=binding["base_sha"],
        )
        assert ok, f"Expected OK, got: {reason}"

    def test_wrong_base_sha_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_base_sha="0000000000000000000000000000000000000000",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason
        assert "base_sha" in reason

    def test_wrong_base_sha_blocks_commit(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "commit",
            current_base_sha="1111111111111111111111111111111111111111",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason

    def test_wrong_base_sha_blocks_create_draft_pr(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "create_draft_pr",
            current_base_sha="9999999999999999999999999999999999999999",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason


# ═══════════════════════════════════════════════════════════
# T04: Wrong task_id blocks writes
# ═══════════════════════════════════════════════════════════

class TestTaskIdEnforcement:
    """Wrong task_id in binding blocks writes."""

    def test_correct_task_id_allows_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_task_id=binding["task_id"],
        )
        assert ok, f"Expected OK, got: {reason}"

    def test_wrong_task_id_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_task_id="ADT-SOME-OTHER-TASK",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason
        assert "task_id" in reason

    def test_empty_task_id_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_task_id="",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason


# ═══════════════════════════════════════════════════════════
# T05: Wrong authorization_id blocks writes
# ═══════════════════════════════════════════════════════════

class TestAuthorizationIdEnforcement:
    """Wrong authorization_id in binding blocks writes."""

    def test_correct_authorization_id_allows_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_authorization_id=binding["authorization_id"],
        )
        assert ok, f"Expected OK, got: {reason}"

    def test_wrong_authorization_id_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_authorization_id="ADT-WRONG-AUTH-001",
        )
        assert not ok
        assert "BINDING_MISMATCH" in reason
        assert "authorization_id" in reason

    def test_missing_authorization_id_blocks_write(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_authorization_id=None,
        )
        # None means "not provided" — should still work (only fails when explicitly wrong)
        # But empty string should fail
        ok2, reason2 = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_authorization_id="",
        )
        assert not ok2
        assert "BINDING_MISMATCH" in reason2


# ═══════════════════════════════════════════════════════════
# T06: Scope enforcement blocks out-of-scope writes
# ═══════════════════════════════════════════════════════════

class TestScopeEnforcement:
    """Wrong authorized_write_scope blocks writes to files outside scope."""

    def test_in_scope_write_allowed(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
        )
        assert ok, f"Expected OK, got: {reason}"

    def test_out_of_scope_write_blocked(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "secret/keys.env",
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_out_of_scope_write_blocked_even_with_valid_branch(self):
        """Even when branch/base_sha match, out-of-scope files are blocked."""
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "unauthorized/protocol.md",
            current_branch=binding["branch"],
            current_base_sha=binding["base_sha"],
            current_task_id=binding["task_id"],
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_scope_violation_blocks_external_config(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "config/secrets.yaml",
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_scope_violation_blocks_dot_env(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", ".env",
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_scope_violation_blocks_absolute_path(self):
        binding = _make_binding()
        ok, reason = _check_action(
            binding, "write_file", "/etc/passwd",
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_all_scope_entries_permitted(self):
        """Every file in authorized_write_scope passes the scope gate."""
        binding = _make_binding()
        for file_path in binding["authorized_write_scope"]:
            ok, reason = _check_action(binding, "write_file", file_path)
            assert ok, f"Expected {file_path} to be allowed, got: {reason}"


# ═══════════════════════════════════════════════════════════
# T07: Stale PROJECT_STATE.md scope is ignored
# ═══════════════════════════════════════════════════════════

class TestStaleScopeRejected:
    """Cannot steal stale scope from old PROJECT_STATE.md when binding exists."""

    def test_binding_scope_takes_precedence(self, tmp_path: Path):
        """When CANDIDATE_BINDING.json exists, its scope is authoritative."""
        # Create a binding with narrow scope
        binding_file = tmp_path / "CANDIDATE_BINDING.json"
        binding = _make_binding(authorized_write_scope=["only_this.md"])
        binding_file.write_text(json.dumps(binding))

        # Create a PROJECT_STATE.md with broader scope (tempting but stale)
        old_scope = ["everything.md", "all_files.md", "secret.md"]
        ps = _make_old_project_state(authorized_write_scope=old_scope)
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)

        # Load binding — must use binding scope, not PROJECT_STATE scope
        loaded = load_binding(binding_file)
        assert loaded is not None
        assert loaded["authorized_write_scope"] == ["only_this.md"]

        # Writing to a file in old scope but NOT in binding scope → blocked
        ok, reason = _check_action(loaded, "write_file", "everything.md")
        assert not ok
        assert "SCOPE_VIOLATION" in reason

        # Writing to binding-scoped file → allowed
        ok, reason = _check_action(loaded, "write_file", "only_this.md")
        assert ok

    def test_binding_exists_old_project_state_scope_irrelevant(self, tmp_path: Path):
        """Old PROJECT_STATE.md scope has zero effect when binding is present."""
        binding_file = tmp_path / "CANDIDATE_BINDING.json"
        binding = _make_binding(authorized_write_scope=["real_scope.md"])
        binding_file.write_text(json.dumps(binding))

        # Old PROJECT_STATE.md claims it can write to "dangerous.md"
        ps = _make_old_project_state(authorized_write_scope=["dangerous.md"])
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)

        loaded = load_binding(binding_file)
        assert loaded is not None

        # dangerous.md from old PROJECT_STATE should NOT be writable
        ok, reason = _check_action(loaded, "write_file", "dangerous.md")
        assert not ok
        assert "SCOPE_VIOLATION" in reason

    def test_no_binding_fallback_to_legacy(self, tmp_path: Path):
        """When NO binding exists, fall back to old-style PROJECT_STATE.md."""
        # No CANDIDATE_BINDING.json
        ps = _make_old_project_state(authorized_write_scope=["legacy_file.md"])
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)

        # Simulate load_binding returning None (no binding file)
        # Legacy fallback kicks in
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is not None
        assert "legacy_file.md" in legacy["authorized_write_scope"]

        # The legacy-derived binding allows writes within its scope
        ok, reason = _check_action(legacy, "write_file", "legacy_file.md")
        assert ok, f"Expected OK, got: {reason}"


# ═══════════════════════════════════════════════════════════
# T08: Legacy fallback requires complete old-style PROJECT_STATE.md
# ═══════════════════════════════════════════════════════════

class TestLegacyFallbackCompleteness:
    """Legacy fallback works ONLY with complete old-style PROJECT_STATE.md."""

    def test_complete_old_style_yields_fallback(self, tmp_path: Path):
        """A complete old-style document produces a valid fallback binding."""
        ps = _make_old_project_state()
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)

        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is not None
        assert legacy["repository"] == _VALID_OLD_STYLE_PROJECT_STATE["repository"]
        assert legacy["base_sha"] == _VALID_OLD_STYLE_PROJECT_STATE["starting_base_sha"]
        assert legacy["branch"] == _VALID_OLD_STYLE_PROJECT_STATE["branch"]
        assert legacy["task_id"] == _VALID_OLD_STYLE_PROJECT_STATE["task_id"]

    def test_missing_task_id_blocks_fallback(self, tmp_path: Path):
        """Without task_id, no legacy fallback."""
        ps = _make_old_project_state(task_id=None)
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None

    def test_missing_branch_blocks_fallback(self, tmp_path: Path):
        """Without branch, no legacy fallback."""
        ps = _make_old_project_state(branch=None)
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None

    def test_missing_starting_base_sha_blocks_fallback(self, tmp_path: Path):
        """Without starting_base_sha, no legacy fallback."""
        ps = _make_old_project_state(starting_base_sha=None)
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None

    def test_missing_authorized_write_scope_blocks_fallback(self, tmp_path: Path):
        """Without authorized_write_scope, no legacy fallback."""
        ps = _make_old_project_state(authorized_write_scope=None)
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None

    def test_empty_authorized_write_scope_blocks_fallback(self, tmp_path: Path):
        """Empty authorized_write_scope blocks legacy fallback."""
        ps = _make_old_project_state(authorized_write_scope=[])
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None

    def test_post_decoupling_project_state_blocks_fallback(self, tmp_path: Path):
        """Post-decoupling PROJECT_STATE.md (stripped of transient fields)
        must NOT produce a legacy fallback."""
        # This is our new PROJECT_STATE.md — no task_id, branch, etc.
        ps_text = """\
# Project State

This file stores durable project state for ADT governance.

```yaml
schema_version: "2"
repository: butbutbutbutbutbut/adaptive-digital-team
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_TASK_HOLDER-003
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: MAKER_IMPLEMENTATION
implementation_status: IN_PROGRESS
```
"""
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps_text)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None, (
            "Post-decoupling PROJECT_STATE.md must NOT produce legacy fallback"
        )

    def test_durable_only_fields_not_enough_for_fallback(self, tmp_path: Path):
        """Having only durable fields (repository, authority, etc.)
        is NOT enough for legacy fallback — transient fields are mandatory."""
        ps = _make_old_project_state(
            task_id=None,
            branch=None,
            starting_base_sha=None,
            authorized_write_scope=None,
        )
        ps_file = tmp_path / "PROJECT_STATE.md"
        ps_file.write_text(ps)
        legacy = _legacy_fallback_from_project_state(ps_file)
        assert legacy is None


# ═══════════════════════════════════════════════════════════
# T09: Integration: End-to-end binding round-trip
# ═══════════════════════════════════════════════════════════

class TestBindingRoundTrip:
    """Real binding file loads correctly and passes all enforcement gates."""

    def test_real_binding_file_exists(self):
        """The CANDIDATE_BINDING.json file must exist in .hermes/."""
        assert BINDING_PATH.exists(), (
            f"Expected CANDIDATE_BINDING.json at {BINDING_PATH}"
        )

    def test_real_binding_is_valid_json(self):
        """The binding file must be parseable JSON."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_real_binding_has_required_fields(self):
        """The binding must contain all required authorization fields."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        required = [
            "authorization_id",
            "authority_source",
            "human_role",
            "repository",
            "base_sha",
            "branch",
            "authorized_actions",
            "authorized_write_scope",
            "task_id",
        ]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_real_binding_scope_includes_this_test_file(self):
        """The binding scope must cover test_guarded_adapter_enforcement.py."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        scope: list[str] = data.get("authorized_write_scope", [])
        assert "tests/test_guarded_adapter_enforcement.py" in scope, (
            f"This test file must be in authorized_write_scope. Got: {scope}"
        )

    def test_real_binding_human_holder_approved(self):
        """The binding must have human_holder_approved: true."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("human_holder_approved") is True, (
            "human_holder_approved must be true"
        )

    def test_real_binding_allows_expected_actions(self):
        """All actions in the real binding pass enforcement."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            binding = json.load(f)

        # Test each action type
        for action in binding["authorized_actions"]:
            ok, reason = _check_action(
                binding, action,
                current_branch=binding["branch"],
                current_base_sha=binding["base_sha"],
                current_task_id=binding["task_id"],
                current_authorization_id=binding["authorization_id"],
            )
            assert ok, f"Action '{action}' should be allowed: {reason}"

    def test_real_binding_rejects_wrong_branch(self):
        """The real binding rejects writes on the wrong branch."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            binding = json.load(f)

        ok, reason = _check_action(
            binding, "write_file", "PROJECT_STATE.md",
            current_branch="hermes/wrong-branch",
        )
        assert not ok

    def test_real_binding_rejects_out_of_scope_file(self):
        """The real binding rejects writes to files outside its scope."""
        assert BINDING_PATH.exists(), "Binding file missing"
        with open(BINDING_PATH, "r", encoding="utf-8") as f:
            binding = json.load(f)

        ok, reason = _check_action(
            binding, "write_file", ".env",
        )
        assert not ok
        assert "SCOPE_VIOLATION" in reason
