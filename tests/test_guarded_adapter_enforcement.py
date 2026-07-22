"""test_guarded_adapter_enforcement.py — Unit tests for the guarded_adapter plugin.

Tests scope enforcement gate logic, authorization binding validation,
and the guarded_write / guarded_repo_actions tools.

Run with:
    cd /c/Users/x2270/adt-prewrite-scope-gate-r1
    python -m pytest tests/test_guarded_adapter_enforcement.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import setup: the plugin lives under .hermes/plugins/guarded_adapter/
# We add .hermes/plugins/ to sys.path so that "guarded_adapter" is importable.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
_PLUGINS_DIR = REPO_ROOT / ".hermes" / "plugins"
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))

# Now the gate, models, and tools are available as guarded_adapter.*
import traceback as _tb
try:
    import guarded_adapter
    import guarded_adapter.gate as gate_module
    import guarded_adapter.runtime_models as models_module
    import guarded_adapter.tools.guarded_write as guarded_write_module
    import guarded_adapter.tools.guarded_repo_actions as guarded_repo_module
    print(f"DEBUG: guarded_adapter={guarded_adapter}", flush=True)
    print(f"DEBUG: guarded_adapter.gate={guarded_adapter.gate}", flush=True)
except Exception as _exc:
    _tb.print_exc()
    raise

# Simplify access
GateRequest = guarded_adapter.gate.GateRequest
validate_scope = guarded_adapter.gate.validate_scope
ExecutionAuthorizationBinding = guarded_adapter.runtime_models.ExecutionAuthorizationBinding
AdapterEnvelope = guarded_adapter.runtime_models.AdapterEnvelope
IndependenceEvidence = guarded_adapter.runtime_models.IndependenceEvidence
guarded_write_handler = guarded_adapter.tools.guarded_write.guarded_write_handler
guarded_repo_actions_handler = guarded_adapter.tools.guarded_repo_actions.guarded_repo_actions_handler
GUARDED_REPO_ACTIONS_SCHEMA = guarded_adapter.tools.guarded_repo_actions.GUARDED_REPO_ACTIONS_SCHEMA


# ===========================================================================
# Gate unit tests
# ===========================================================================

class TestGateValidateScope:
    """Unit tests for gate.validate_scope()."""

    def test_allow_path_in_scope_exact_match(self):
        """Path exactly matches a scope entry → allowed (path check passes;
        no binding → BINDING_MISSING for write actions)."""
        req = GateRequest(
            action_type="write_file",
            action_path="tests/test_foo.py",
            plan_write_scope=["tests/test_foo.py"],
            authorized_write_scope=["tests/test_foo.py"],
            authorization_binding=None,
        )
        result = validate_scope(req)
        # No binding + write → BINDING_MISSING
        assert not result.allowed
        assert "BINDING_MISSING" in result.error

    @patch("guarded_adapter.gate._get_current_repo")
    @patch("guarded_adapter.gate._get_current_base_sha")
    @patch("guarded_adapter.gate._get_current_branch")
    def test_allow_with_valid_binding(self, mock_branch, mock_base, mock_repo):
        """Valid binding with matching repo/branch/base → allowed."""
        mock_repo.return_value = "test-owner/test-repo"
        mock_base.return_value = "a" * 40
        mock_branch.return_value = "hermes/test-branch"

        req = GateRequest(
            action_type="write_file",
            action_path="tests/test_foo.py",
            plan_write_scope=["tests/test_foo.py"],
            authorized_write_scope=["tests/test_foo.py"],
            authorization_binding={
                "authorization_id": "ADT-TEST-001",
                "authority_source": "Test",
                "human_role": "HUMAN_HOLDER",
                "repository": "test-owner/test-repo",
                "base_sha": "a" * 40,
                "branch": "hermes/test-branch",
                "authorized_actions": ["write_file"],
                "authorized_write_scope": ["tests/test_foo.py"],
            },
        )
        result = validate_scope(req)
        assert result.allowed
        assert result.error is None

    def test_block_path_not_in_plan_write_scope(self):
        """Path not in plan.write_scope → BLOCKED."""
        req = GateRequest(
            action_type="write_file",
            action_path="scripts/route_task.py",
            plan_write_scope=["tests/test_foo.py"],
            authorized_write_scope=["tests/test_foo.py"],
            authorization_binding=None,
        )
        result = validate_scope(req)
        assert not result.allowed
        assert "ATTEMPTED_SCOPE_VIOLATION" in result.error
        assert "scripts/route_task.py" in result.error

    def test_block_path_not_in_authorized_write_scope(self):
        """Path not in authorized_write_scope → BLOCKED."""
        req = GateRequest(
            action_type="write_file",
            action_path="tests/test_foo.py",
            plan_write_scope=["tests/test_foo.py"],
            authorized_write_scope=["other/path.py"],
            authorization_binding=None,
        )
        result = validate_scope(req)
        assert not result.allowed
        assert "ATTEMPTED_SCOPE_VIOLATION" in result.error

    def test_allow_directory_prefix_scope(self):
        """Directory scope prefix covers files within it."""
        req = GateRequest(
            action_type="write_file",
            action_path=".hermes/plugins/guarded_adapter/gate.py",
            plan_write_scope=[".hermes/plugins/guarded_adapter/"],
            authorized_write_scope=[".hermes/plugins/guarded_adapter/"],
            authorization_binding=None,
        )
        result = validate_scope(req)
        # With no binding, write → BINDING_MISSING; path check passes
        assert "ATTEMPTED_SCOPE_VIOLATION" not in (result.error or "")
        assert "BINDING_MISSING" in result.error

    @patch("guarded_adapter.gate._get_current_repo")
    @patch("guarded_adapter.gate._get_current_base_sha")
    @patch("guarded_adapter.gate._get_current_branch")
    def test_block_unauthorized_action(self, mock_branch, mock_base, mock_repo):
        """Action not in authorized_actions → BLOCKED."""
        mock_repo.return_value = "test-owner/test-repo"
        mock_base.return_value = "a" * 40
        mock_branch.return_value = "hermes/test-branch"

        req = GateRequest(
            action_type="merge",  # not in authorized_actions
            action_path="",
            plan_write_scope=[],
            authorized_write_scope=[],
            authorization_binding={
                "authorization_id": "ADT-TEST-001",
                "authority_source": "Test",
                "human_role": "HUMAN_HOLDER",
                "repository": "test-owner/test-repo",
                "base_sha": "a" * 40,
                "branch": "hermes/test-branch",
                "authorized_actions": ["write_file", "commit"],
                "authorized_write_scope": [],
            },
        )
        result = validate_scope(req)
        assert not result.allowed
        assert "UNAUTHORIZED_ACTION" in result.error

    @patch("guarded_adapter.gate._get_current_repo")
    @patch("guarded_adapter.gate._get_current_base_sha")
    @patch("guarded_adapter.gate._get_current_branch")
    def test_block_repository_drift(self, mock_branch, mock_base, mock_repo):
        """Repository mismatch between binding and current → BLOCKED."""
        mock_repo.return_value = "actual-owner/actual-repo"
        mock_base.return_value = "a" * 40
        mock_branch.return_value = "hermes/test-branch"

        req = GateRequest(
            action_type="write_file",
            action_path="tests/test_foo.py",
            plan_write_scope=["tests/test_foo.py"],
            authorized_write_scope=["tests/test_foo.py"],
            authorization_binding={
                "authorization_id": "ADT-TEST-001",
                "authority_source": "Test",
                "human_role": "HUMAN_HOLDER",
                "repository": "different-owner/different-repo",
                "base_sha": "a" * 40,
                "branch": "hermes/test-branch",
                "authorized_actions": ["write_file"],
                "authorized_write_scope": ["tests/test_foo.py"],
            },
        )
        result = validate_scope(req)
        assert not result.allowed
        assert "BINDING_MISMATCH" in result.error
        assert "repository" in result.error.lower()


# ===========================================================================
# Runtime models tests
# ===========================================================================

class TestExecutionAuthorizationBinding:
    """Unit tests for ExecutionAuthorizationBinding model."""

    def test_valid_binding_passes_validation(self):
        """Valid binding with all required fields passes validation."""
        binding = ExecutionAuthorizationBinding(
            authorization_id="ADT-TEST-001",
            authority_source="Test suite",
            human_role="HUMAN_HOLDER",
            repository="owner/repo",
            base_sha="a" * 40,
            branch="hermes/test-branch",
            authorized_actions=["write_file", "commit"],
            authorized_write_scope=["tests/", ".hermes/"],
        )
        errors = binding.validate()
        assert errors == []

    def test_invalid_repository_format_fails(self):
        """Invalid repository format (no slash) fails validation."""
        binding = ExecutionAuthorizationBinding(
            authorization_id="ADT-TEST-001",
            authority_source="Test",
            human_role="HUMAN_HOLDER",
            repository="invalid-repo",  # missing owner/
            base_sha="a" * 40,
            branch="hermes/test-branch",
            authorized_actions=["read"],
            authorized_write_scope=[],
        )
        errors = binding.validate()
        assert any("repository" in e.lower() for e in errors)

    def test_invalid_base_sha_fails(self):
        """Invalid base_sha (wrong length) fails validation."""
        binding = ExecutionAuthorizationBinding(
            authorization_id="ADT-TEST-001",
            authority_source="Test",
            human_role="HUMAN_HOLDER",
            repository="owner/repo",
            base_sha="short",
            branch="hermes/test-branch",
            authorized_actions=["read"],
            authorized_write_scope=[],
        )
        errors = binding.validate()
        assert any("base_sha" in e.lower() for e in errors)

    def test_invalid_action_fails(self):
        """Invalid authorized_action fails validation."""
        binding = ExecutionAuthorizationBinding(
            authorization_id="ADT-TEST-001",
            authority_source="Test",
            human_role="HUMAN_HOLDER",
            repository="owner/repo",
            base_sha="a" * 40,
            branch="hermes/test-branch",
            authorized_actions=["merge"],  # not in allowed set
            authorized_write_scope=[],
        )
        errors = binding.validate()
        assert any("authorized_action" in e.lower() for e in errors)


class TestAdapterEnvelope:
    """Unit tests for AdapterEnvelope model."""

    def test_valid_envelope(self):
        """Valid envelope passes validation."""
        env = AdapterEnvelope(
            tool_identity="hermes/4.2.1",
            tool_session_id="sess_abc123",
            tool_capability_tags=["file_write", "git"],
            session_principal="xiaohe",
            credential_tags=["github_pat"],
        )
        errors = env.validate()
        assert errors == []

    def test_missing_tool_identity_fails(self):
        """Missing tool_identity fails validation."""
        env = AdapterEnvelope(
            tool_identity="",
            tool_session_id="sess_abc123",
            tool_capability_tags=["file_write"],
            session_principal="xiaohe",
            credential_tags=[],
        )
        errors = env.validate()
        assert any("tool_identity" in e.lower() for e in errors)

    def test_empty_capability_tags_fails(self):
        """Empty tool_capability_tags fails validation."""
        env = AdapterEnvelope(
            tool_identity="hermes/4.2.1",
            tool_session_id="sess_abc123",
            tool_capability_tags=[],
            session_principal="xiaohe",
            credential_tags=[],
        )
        errors = env.validate()
        assert any("capability_tags" in e.lower() for e in errors)

    def test_checker_independence_maker_context_inherited_fails(self):
        """Checker independence evidence: maker_context_inherited=true fails."""
        env = AdapterEnvelope(
            tool_identity="hermes/4.2.1",
            tool_session_id="sess_abc123",
            tool_capability_tags=["file_write"],
            session_principal="xiaohe",
            credential_tags=[],
            independence_evidence=IndependenceEvidence(
                separate_execution_context=True,
                maker_context_inherited=True,   # MUST be false
                participated_in_implementation=False,
                independent_fact_read=True,
                independent_conclusion=True,
            ),
        )
        errors = env.validate()
        assert any("maker_context_inherited" in e.lower() for e in errors)


# ===========================================================================
# guarded_write tests
# ===========================================================================

class TestGuardedWrite:
    """Unit tests for the guarded_write handler."""

    def test_write_within_scope_succeeds(self, tmp_path: Path):
        """Write to path within authorized scope succeeds."""
        # Create a mock PROJECT_STATE.md
        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope:
  - tests/
```""")

        with patch(
            "guarded_adapter.tools.guarded_write._REPO_ROOT",
            tmp_path,
        ):
            result = guarded_write_handler(
                path="tests/test_output.txt",
                content="test content",
            )
            assert result["adapter_execution_status"] == "COMPLETED"
            assert result["adapter_error"] is None
            assert result["bytes_written"] > 0

            written = (tmp_path / "tests" / "test_output.txt").read_text()
            assert written == "test content"

    def test_write_outside_scope_blocked(self, tmp_path: Path):
        """Write to path outside authorized scope → BLOCKED."""
        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope:
  - tests/
```""")

        with patch(
            "guarded_adapter.tools.guarded_write._REPO_ROOT",
            tmp_path,
        ):
            result = guarded_write_handler(
                path="scripts/route_task.py",
                content="should-be-blocked",
            )
            assert result["adapter_execution_status"] == "BLOCKED"
            assert result["adapter_error"] == "ATTEMPTED_SCOPE_VIOLATION"


# ===========================================================================
# guarded_repo_actions tests
# ===========================================================================

class TestGuardedRepoActions:
    """Unit tests for the guarded_repo_actions handler."""

    def test_unknown_action_blocked(self, tmp_path: Path):
        """Unknown action → BLOCKED with UNAUTHORIZED_ACTION."""
        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope: []
```""")

        with patch(
            "guarded_adapter.tools.guarded_repo_actions._REPO_ROOT",
            tmp_path,
        ):
            result = guarded_repo_actions_handler(action="git_merge")
            assert result["adapter_execution_status"] == "BLOCKED"
            assert result["adapter_error"] == "UNAUTHORIZED_ACTION"

    def test_no_shell_or_command_injection(self):
        """Verify no 'command', 'shell', 'args' parameters are accepted."""
        props = GUARDED_REPO_ACTIONS_SCHEMA["properties"]
        assert "command" not in props
        assert "shell" not in props
        assert "args" not in props
        assert "cmd" not in props

    def test_read_repository_state_returns_info(self, tmp_path: Path):
        """read_repository_state action returns repo info."""
        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope: []
```""")

        with patch(
            "guarded_adapter.tools.guarded_repo_actions._REPO_ROOT",
            tmp_path,
        ), patch(
            "guarded_adapter.tools.guarded_repo_actions._run_git",
            return_value={
                "returncode": 0,
                "stdout": "mocked-output",
                "stderr": "",
                "success": True,
            },
        ):
            result = guarded_repo_actions_handler(action="read_repository_state")
            assert result["adapter_execution_status"] == "COMPLETED"
            assert result["action"] == "read_repository_state"
            assert "head_sha" in result


# ===========================================================================
# Integration: gate + tools round-trip
# ===========================================================================

class TestGateToolIntegration:
    """End-to-end integration tests: gate + tools together."""

    @patch("guarded_adapter.gate._get_current_repo")
    @patch("guarded_adapter.gate._get_current_base_sha")
    @patch("guarded_adapter.gate._get_current_branch")
    def test_full_write_flow_allowed(
        self, mock_branch, mock_base, mock_repo, tmp_path: Path
    ):
        """Full flow: write within scope with valid binding → COMPLETED."""
        mock_repo.return_value = "test-owner/test-repo"
        mock_base.return_value = "aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd"
        mock_branch.return_value = "hermes/test-branch"

        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope:
  - tests/
  - .hermes/
```""")

        with patch(
            "guarded_adapter.tools.guarded_write._REPO_ROOT",
            tmp_path,
        ):
            result = guarded_write_handler(
                path="tests/integration_test.txt",
                content="integration test content",
            )
            assert result["adapter_execution_status"] == "COMPLETED"
            assert result["adapter_error"] is None
            assert (tmp_path / "tests" / "integration_test.txt").exists()

    @patch("guarded_adapter.gate._get_current_repo")
    @patch("guarded_adapter.gate._get_current_base_sha")
    @patch("guarded_adapter.gate._get_current_branch")
    def test_full_write_flow_blocked_outside_scope(
        self, mock_branch, mock_base, mock_repo, tmp_path: Path
    ):
        """Full flow: write outside scope → BLOCKED."""
        mock_repo.return_value = "test-owner/test-repo"
        mock_base.return_value = "aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd"
        mock_branch.return_value = "hermes/test-branch"

        project_state = tmp_path / "PROJECT_STATE.md"
        project_state.write_text("""```yaml
task_id: ADT-TEST-001
repository: test-owner/test-repo
branch: hermes/test-branch
starting_base_sha: aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd
authorized_write_scope:
  - tests/
```""")

        with patch(
            "guarded_adapter.tools.guarded_write._REPO_ROOT",
            tmp_path,
        ):
            result = guarded_write_handler(
                path="scripts/route_task.py",
                content="should-be-blocked",
            )
            assert result["adapter_execution_status"] == "BLOCKED"
            assert "ATTEMPTED_SCOPE_VIOLATION" in result["adapter_error"]
            assert not (tmp_path / "scripts" / "route_task.py").exists()

    def test_e2e_allowed_file_exists(self):
        """Verify the E2E fixture file exists."""
        fixture = REPO_ROOT / "tests" / "fixtures" / "adapter_e2e_allowed.txt"
        assert fixture.exists(), (
            f"E2E fixture missing: {fixture}"
        )
        content = fixture.read_text()
        assert "e2e-test-pass" in content
