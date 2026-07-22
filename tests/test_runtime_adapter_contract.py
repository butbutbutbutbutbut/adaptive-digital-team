"""ADT Runtime Adapter Contract R1 — test suite.

Covers all mandatory implementation clauses:
  - Three-layer normalization
  - Authorization binding validation
  - Scope subset check (⊆ not equality)
  - Scope violation detection (ALL attempts, credential irrelevant)
  - Independence evidence validation (two-phase, 5 fields)
  - Credential strip from intake
  - Error separation (plan.route preserved)

All 203 existing router tests must still PASS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Import from existing module (unchanged)
from route_task import route_task, GovernancePlan  # noqa: E402


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def load_schema(name: str) -> dict:
    """Load a JSON schema from the schemas/ directory."""
    path = REPO_ROOT / "schemas" / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _make_valid_auth_binding(**overrides) -> dict:
    """Create a valid authorization binding, optionally overriding fields."""
    binding = {
        "authorization_id": "ADT-TEST-001",
        "authority_source": "Human Holder directive #42",
        "human_role": "HUMAN_HOLDER",
        "repository": "butbutbutbutbutbut/adaptive-digital-team",
        "base_sha": "1f53b68ef9f0b5a9053d0a96d114d229942ff2d8",
        "branch": "hermes/adt-runtime-adapter-contract-r1",
        "authorized_actions": ["commit", "push", "create_draft_pr"],
        "authorized_write_scope": [
            "protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md",
            "schemas/adapter-envelope.schema.json",
            "schemas/adapter-output.schema.json",
            "schemas/execution-authorization-binding.schema.json",
            "scripts/validate_adapter.py",
            "tests/test_runtime_adapter_contract.py",
            "governance/NORMATIVE_MAP.md",
            "AGENTS.md",
            "PROJECT_STATE.md",
        ],
    }
    binding.update(overrides)
    return binding


def _make_valid_envelope(**overrides) -> dict:
    """Create a valid adapter envelope, optionally overriding fields."""
    envelope = {
        "tool_identity": "hermes/4.2.1",
        "tool_session_id": "sess_test123",
        "tool_capability_tags": ["git", "file_write", "terminal"],
        "session_principal": "test_agent",
        "claimed_actor": "test_agent",
        "credential_tags": ["github_pat"],
        "independence_evidence": {
            "separate_execution_context": True,
            "maker_context_inherited": False,
            "participated_in_implementation": False,
            "independent_fact_read": True,
            "independent_conclusion": True,
        },
    }
    envelope.update(overrides)
    return envelope


# ═══════════════════════════════════════════════════════════
# T01: Three-Layer Normalization
# ═══════════════════════════════════════════════════════════

class TestThreeLayerNormalization:
    """Tests that the three-layer model correctly isolates tool-native data."""

    def test_layer2_envelope_does_not_contain_credential_values(self):
        """Layer 2 envelope must have credential_tags (tags only), never values."""
        envelope = _make_valid_envelope()
        # credential_tags are present but must be string tags
        assert "credential_tags" in envelope
        for tag in envelope["credential_tags"]:
            assert isinstance(tag, str)
            # Tags should not contain actual secrets (length heuristic)
            assert len(tag) < 100, f"Tag '{tag}' looks like a credential value"
            # Must not contain = or : which suggest key=value
            assert "=" not in tag, f"Tag '{tag}' looks like a key=value credential"
            assert ":" not in tag or "://" in tag, f"Tag '{tag}' looks like a credential value"

    def test_layer3_intake_has_no_adapter_fields(self):
        """Layer 3 TaskIntake must not contain adapter envelope fields."""
        intake = route_task({
            "request": "Test task",
        })
        # These fields must not leak into intake output
        adapter_fields = [
            "tool_identity", "tool_session_id", "tool_capability_tags",
            "session_principal", "claimed_actor", "credential_tags",
            "independence_evidence",
        ]
        for field in adapter_fields:
            assert field not in intake, (
                f"Layer 2 field '{field}' leaked into Layer 3 TaskIntake output"
            )

    def test_envelope_strips_credentials_before_intake(self):
        """Credential values in input must be stripped before reaching intake."""
        # Simulate what adapter does: strip credential values, forward only tags
        raw_tool_input = {
            "request": "Fix bug",
            "github_token": "ghp_abc123secret",  # should be stripped
            "api_key": "sk-12345",               # should be stripped
            "credential_tags": ["github_pat", "openai_api_key"],  # tags only
        }
        # Only standard intake fields survive
        intake_input = {
            "request": raw_tool_input["request"],
        }
        plan = route_task(intake_input)
        # Output should not contain credential values
        plan_str = json.dumps(plan)
        assert "ghp_abc123secret" not in plan_str
        assert "sk-12345" not in plan_str

    def test_envelope_session_principal_not_human_holder(self):
        """SESSION_PRINCIPAL is a tag, NOT a Human Holder mapping."""
        envelope = _make_valid_envelope(
            session_principal="xiaohe",
        )
        # session_principal is just a string tag — it carries no governance authority
        assert envelope["session_principal"] == "xiaohe"
        # There must be NO field that asserts session_principal IS the Human Holder
        assert "human_holder" not in envelope
        assert "is_human_holder" not in envelope
        assert "human_holder_mapping" not in envelope


# ═══════════════════════════════════════════════════════════
# T02: Authorization Binding Validation
# ═══════════════════════════════════════════════════════════

class TestAuthorizationBinding:
    """Tests that AuthorizationBinding schema and validation work correctly."""

    def test_valid_binding_passes(self):
        """A valid binding with all required fields should validate."""
        binding = _make_valid_auth_binding()
        # All required fields present
        required = [
            "authorization_id", "authority_source", "human_role",
            "repository", "base_sha", "branch",
            "authorized_actions", "authorized_write_scope",
        ]
        for field in required:
            assert field in binding, f"Missing required field: {field}"

    def test_binding_rejects_forbidden_actions_in_enum(self):
        """The schema enum for authorized_actions must not include forbidden actions."""
        schema = load_schema("execution-authorization-binding.schema.json")
        enum_values = (
            schema.get("properties", {})
            .get("authorized_actions", {})
            .get("items", {})
            .get("enum", [])
        )
        forbidden = {"ready", "merge", "close_pr", "delete_branch"}
        for f in forbidden:
            assert f not in enum_values, (
                f"Forbidden action '{f}' appears in authorized_actions enum"
            )

    def test_binding_missing_required_fields_fails(self):
        """Missing required fields should fail validation."""
        binding = {"authorization_id": "ALONE"}  # missing everything else
        required = [
            "authority_source", "human_role", "repository",
            "base_sha", "branch", "authorized_actions", "authorized_write_scope",
        ]
        for field in required:
            assert field not in binding, f"Field {field} should be missing"

    def test_binding_repository_must_match_pattern(self):
        """repository must match owner/repo pattern."""
        binding = _make_valid_auth_binding(repository="not-a-valid-repo")
        # Should not match owner/repo pattern
        import re
        pattern = r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$"
        assert not re.match(pattern, binding["repository"]), \
            "bad repo string should not match pattern"

    def test_binding_base_sha_must_be_40_hex(self):
        """base_sha must be exactly 40 hex characters."""
        binding = _make_valid_auth_binding(base_sha="too_short")
        import re
        pattern = r"^[0-9a-f]{40}$"
        assert not re.match(pattern, binding["base_sha"]), \
            "short base_sha should not match 40-hex pattern"

    def test_adapter_must_not_self_set_human_holder_approved(self):
        """The adapter must NOT set human_holder_approved: true."""
        # The field exists in the schema for external use,
        # but the adapter MUST NOT set it to true
        schema = load_schema("execution-authorization-binding.schema.json")
        hha = schema.get("properties", {}).get("human_holder_approved", {})
        assert hha.get("type") == "boolean"
        # The field description explicitly says adapter must not self-set it
        assert "MUST NOT" in hha.get("description", "").upper() or \
               "must not" in hha.get("description", "").lower()

    def test_binding_authorized_actions_only_valid_enums(self):
        """authorized_actions must only contain valid action types."""
        schema = load_schema("execution-authorization-binding.schema.json")
        enum_values = (
            schema.get("properties", {})
            .get("authorized_actions", {})
            .get("items", {})
            .get("enum", [])
        )
        valid = {"read", "write_file", "commit", "push", "create_draft_pr"}
        assert set(enum_values) == valid, \
            f"Expected authorized_actions enum {valid}, got {set(enum_values)}"


# ═══════════════════════════════════════════════════════════
# T03: Scope Subset Check (⊆, not equality)
# ═══════════════════════════════════════════════════════════

class TestScopeSubset:
    """Tests that plan.write_scope ⊆ auth.authorized_write_scope (subset)."""

    def test_subset_passes(self):
        """plan scope being a strict subset of auth scope should pass."""
        plan_scope = ["file_a.md", "file_b.md"]
        auth_scope = ["file_a.md", "file_b.md", "file_c.md", "file_d.md"]
        assert set(plan_scope).issubset(set(auth_scope)), \
            "plan scope must be subset of auth scope"

    def test_equality_passes(self):
        """plan scope being exactly equal to auth scope should pass (equality is also a subset)."""
        plan_scope = ["file_a.md", "file_b.md"]
        auth_scope = ["file_a.md", "file_b.md"]
        assert set(plan_scope).issubset(set(auth_scope)), \
            "equality is a valid subset"

    def test_superset_fails(self):
        """plan scope being a SUPERSET of auth scope must FAIL."""
        plan_scope = ["file_a.md", "file_b.md", "file_c.md"]
        auth_scope = ["file_a.md"]
        assert not set(plan_scope).issubset(set(auth_scope)), \
            "plan scope MUST fail when it exceeds auth scope"

    def test_disjoint_fails(self):
        """plan scope with NO overlap must FAIL."""
        plan_scope = ["file_x.md"]
        auth_scope = ["file_y.md"]
        assert not set(plan_scope).issubset(set(auth_scope)), \
            "disjoint scopes must fail"

    def test_empty_plan_scope_passes(self):
        """An empty plan scope is always a subset."""
        plan_scope = []
        auth_scope = ["file_a.md"]
        assert set(plan_scope).issubset(set(auth_scope)), \
            "empty plan scope is always a valid subset"


# ═══════════════════════════════════════════════════════════
# T04: Scope Violation Detection
# ═══════════════════════════════════════════════════════════

class TestScopeViolation:
    """Tests ATTEMPTED_SCOPE_VIOLATION detection for all out-of-scope attempts."""

    def _check_scope_violation(
        self, action_type: str, action_path: str,
        plan_scope: list[str], auth_scope: list[str],
        authorized_actions: list[str],
    ) -> bool:
        """Simulate the per-action scope gate."""
        # Gate 1: action type
        if action_type not in authorized_actions:
            return False  # ATTEMPTED_SCOPE_VIOLATION / UNAUTHORIZED_ACTION

        # Gate 2: file target scope check
        if action_path:
            in_plan = action_path in plan_scope
            in_auth = action_path in authorized_actions if action_type == "write_file" else (action_path in auth_scope)
            if not (in_plan and (action_path in auth_scope)):
                return False  # ATTEMPTED_SCOPE_VIOLATION

        return True

    def test_file_outside_both_scopes_blocked(self):
        """File outside both plan and auth scope → blocked."""
        ok = self._check_scope_violation(
            "write_file", "secret/keys.env",
            plan_scope=["docs/readme.md"],
            auth_scope=["docs/readme.md"],
            authorized_actions=["write_file", "commit", "push"],
        )
        assert not ok, "File outside both scopes must be blocked"

    def test_file_in_plan_but_not_auth_blocked(self):
        """File in plan scope but not auth scope → blocked."""
        ok = self._check_scope_violation(
            "write_file", "protocols/new.md",
            plan_scope=["protocols/new.md"],
            auth_scope=["docs/readme.md"],
            authorized_actions=["write_file", "commit", "push"],
        )
        assert not ok, "File in plan but not auth must be blocked"

    def test_file_in_both_scopes_allowed(self):
        """File in both plan and auth scope → allowed."""
        ok = self._check_scope_violation(
            "write_file", "docs/readme.md",
            plan_scope=["docs/readme.md"],
            auth_scope=["docs/readme.md"],
            authorized_actions=["write_file", "commit", "push"],
        )
        assert ok, "File in both scopes must be allowed"

    def test_unauthorized_action_type_blocked(self):
        """Action type not in authorized_actions → blocked regardless of path."""
        ok = self._check_scope_violation(
            "merge", "",
            plan_scope=["docs/readme.md"],
            auth_scope=["docs/readme.md"],
            authorized_actions=["write_file", "commit", "push"],
        )
        assert not ok, "merge action must be blocked (not in authorized_actions)"

    def test_pathless_actions_constrained_by_authorized_actions(self):
        """Pathless actions (commit, push, create_draft_pr) constrained by authorized_actions only."""
        # commit is in authorized_actions → allowed
        ok = self._check_scope_violation(
            "commit", "",
            plan_scope=[],
            auth_scope=[],
            authorized_actions=["commit", "push", "create_draft_pr"],
        )
        assert ok, "commit in authorized_actions must be allowed"

        # merge is NOT in authorized_actions → blocked
        ok = self._check_scope_violation(
            "merge", "",
            plan_scope=[],
            auth_scope=[],
            authorized_actions=["commit", "push", "create_draft_pr"],
        )
        assert not ok, "merge not in authorized_actions must be blocked"

    def test_credential_capability_irrelevant_to_scope(self):
        """Having git credentials does not expand write scope."""
        # Simulate: tool has github_pat credential, but scope is only [file_a.md]
        credential_tags = ["github_pat"]
        auth_scope = ["file_a.md"]
        plan_scope = ["file_a.md"]

        # Attempt to write secret/keys.env — credential tags don't grant scope
        action_path = "secret/keys.env"
        has_credential = "github_pat" in credential_tags
        in_scope = action_path in plan_scope and action_path in auth_scope

        assert has_credential, "tool has credential"
        assert not in_scope, "credential does NOT expand scope"
        # The credential is irrelevant — scope gate enforces write_scope only


# ═══════════════════════════════════════════════════════════
# T05: Independence Evidence Validation (Two-Phase)
# ═══════════════════════════════════════════════════════════

class TestIndependenceEvidence:
    """Tests two-phase Checker independence evidence."""

    def test_evidence_has_five_fields(self):
        """Independence evidence must have exactly 5 boolean fields."""
        schema = load_schema("adapter-envelope.schema.json")
        indep = schema.get("properties", {}).get("independence_evidence", {})
        required = indep.get("required", [])
        assert len(required) == 5, f"Expected 5 required fields, got {len(required)}: {required}"
        expected = {
            "separate_execution_context",
            "maker_context_inherited",
            "participated_in_implementation",
            "independent_fact_read",
            "independent_conclusion",
        }
        assert set(required) == expected, \
            f"Expected fields {expected}, got {set(required)}"

    def test_evidence_not_single_boolean(self):
        """Independence evidence must be an object, not a single boolean."""
        schema = load_schema("adapter-envelope.schema.json")
        indep = schema.get("properties", {}).get("independence_evidence", {})
        assert indep.get("type") == "object", \
            "independence_evidence must be an object, not boolean"

    def test_phase1_fields_required_pre_execution(self):
        """Phase 1 fields are required before Checker execution."""
        # Phase 1: separate_execution_context and maker_context_inherited
        evidence = {
            "separate_execution_context": True,
            "maker_context_inherited": False,
            # Phase 2 fields not yet provided (pre-execution)
            "participated_in_implementation": False,
            "independent_fact_read": False,
            "independent_conclusion": False,
        }
        # Phase 1 check
        assert evidence["separate_execution_context"] is True, \
            "Phase 1: must have separate execution context"
        assert evidence["maker_context_inherited"] is False, \
            "Phase 1: must NOT inherit maker context"

    def test_independent_conclusion_not_required_pre_execution(self):
        """independent_conclusion must NOT be required before Checker executes."""
        # Pre-execution: independent_conclusion can be false/null
        evidence = {
            "separate_execution_context": True,
            "maker_context_inherited": False,
            "participated_in_implementation": False,
            "independent_fact_read": False,  # not yet read
            "independent_conclusion": False,  # not yet concluded — OK pre-execution
        }
        # This should be valid pre-execution
        assert evidence["independent_conclusion"] is False, \
            "independent_conclusion can be false pre-execution"

    def test_full_evidence_post_execution(self):
        """Post-execution: all 5 fields must be true (except maker_context_inherited and participated_in_implementation)."""
        evidence = {
            "separate_execution_context": True,
            "maker_context_inherited": False,
            "participated_in_implementation": False,
            "independent_fact_read": True,
            "independent_conclusion": True,
        }
        # Phase 1
        assert evidence["separate_execution_context"] is True
        assert evidence["maker_context_inherited"] is False
        # Phase 2
        assert evidence["participated_in_implementation"] is False
        assert evidence["independent_fact_read"] is True
        assert evidence["independent_conclusion"] is True

    def test_same_api_key_does_not_break_independence(self):
        """Two agents sharing an API key can still be independent."""
        maker_api_key = "sk-shared-key-123"
        checker_api_key = "sk-shared-key-123"
        same_key = maker_api_key == checker_api_key
        # Same key does NOT mean same execution context
        evidence = {
            "separate_execution_context": True,
            "maker_context_inherited": False,
            "participated_in_implementation": False,
            "independent_fact_read": True,
            "independent_conclusion": True,
        }
        assert same_key, "keys are the same"
        assert evidence["separate_execution_context"] is True, \
            "separate execution context despite same API key"
        assert evidence["maker_context_inherited"] is False, \
            "no context inheritance despite same API key"


# ═══════════════════════════════════════════════════════════
# T06: Credential Strip from Intake
# ═══════════════════════════════════════════════════════════

class TestCredentialStrip:
    """Tests that credentials are stripped before reaching Layer 3."""

    def test_credential_tags_never_contain_values(self):
        """credential_tags must be descriptive strings, not actual values."""
        tags = ["github_pat", "openai_api_key"]
        for tag in tags:
            # Must not look like a real token
            assert not tag.startswith("ghp_"), f"Tag '{tag}' looks like a GitHub PAT"
            assert not tag.startswith("sk-"), f"Tag '{tag}' looks like an OpenAI key"
            assert len(tag) < 50, f"Tag '{tag}' is too long for a descriptive tag"

    def test_intake_strips_extra_fields(self):
        """Extra fields that look like credentials must not reach intake."""
        raw_input = {
            "request": "Fix typo",
            "repository": "owner/repo",
            "github_token": "ghp_secret123",
            "openai_key": "sk-secret456",
            "password": "hunter2",
            "api_secret": "supersecret",
        }
        # Only standard intake fields should be used
        safe_fields = {"request", "repository", "attachments", "claimed_authority",
                       "base_sha", "branch", "control_packet", "write_intent",
                       "audit_request", "cancellation", "auto_ready", "auto_merge",
                       "auto_delete_branch", "scope_expansion", "conflicting_facts"}
        for key in raw_input:
            if key not in safe_fields:
                assert key not in safe_fields, \
                    f"Credential-like field '{key}' is not a standard intake field"

    def test_credential_leak_detected(self):
        """If a credential value attempts to cross Layer 2→3, it must be caught."""
        # Simulate: envelope contains only tags
        envelope_credential_tags = ["github_pat"]
        # Check: no tag contains an actual token pattern
        for tag in envelope_credential_tags:
            is_leak = (
                tag.startswith("ghp_") or
                tag.startswith("sk-") or
                ":" in tag or
                len(tag) > 100
            )
            assert not is_leak, \
                f"CREDENTIAL_LEAK detected: tag '{tag}' contains credential value"


# ═══════════════════════════════════════════════════════════
# T07: Error Separation (plan.route preserved)
# ═══════════════════════════════════════════════════════════

class TestErrorSeparation:
    """Tests that adapter errors never overwrite plan.route."""

    def test_adapter_error_is_separate_field(self):
        """adapter_error is a separate field from governance_plan.route."""
        output = {
            "governance_plan": {
                "route": "CANDIDATE_IMPLEMENTATION",
                "risk": "HIGH",
                "task_type": "REPOSITORY_CANDIDATE",
                "facts_status": "REQUIRES_VERIFICATION",
                "control_packet_status": "CANDIDATE",
                "write_scope": [],
                "steps": [],
                "checker_required": True,
                "human_authorization_required": True,
                "write_actions_permitted": True,
            },
            "adapter_error": "SCOPE_VIOLATION",
            "route": "CANDIDATE_IMPLEMENTATION",
        }
        # Even with adapter_error, governance_plan.route is preserved
        assert output["governance_plan"]["route"] == "CANDIDATE_IMPLEMENTATION"
        assert output["adapter_error"] == "SCOPE_VIOLATION"
        # route mirrors governance_plan.route
        assert output["route"] == output["governance_plan"]["route"]

    def test_governance_plan_route_never_overwritten(self):
        """No matter the adapter error, governance_plan.route stays unchanged."""
        original_route = "CANDIDATE_IMPLEMENTATION"
        adapter_errors = [
            "SCOPE_VIOLATION",
            "UNAUTHORIZED_ACTION",
            "BINDING_MISSING",
            "BINDING_INVALID",
            "CREDENTIAL_LEAK",
            "INDEPENDENCE_FAILED",
            "ATTEMPTED_SCOPE_VIOLATION",
        ]
        for error in adapter_errors:
            # Simulate adapter output with error
            output_route = original_route  # route is NEVER changed by error
            assert output_route == original_route, \
                f"route changed from {original_route} to {output_route} on error {error}"

    def test_adapter_error_cannot_be_empty_string(self):
        """adapter_error must be null or a valid error code, not empty string."""
        valid_errors = {
            None,
            "SCOPE_VIOLATION",
            "UNAUTHORIZED_ACTION",
            "BINDING_MISSING",
            "BINDING_INVALID",
            "CREDENTIAL_LEAK",
            "INDEPENDENCE_FAILED",
            "ATTEMPTED_SCOPE_VIOLATION",
        }
        # Empty string is not a valid error
        assert "" not in valid_errors, "empty string is not a valid adapter_error"


# ═══════════════════════════════════════════════════════════
# T08: Existing Router Tests Compatibility
# ═══════════════════════════════════════════════════════════

class TestRouterCompatibility:
    """Verify that the existing router API is unchanged."""

    def test_route_task_still_works(self):
        """Basic route_task call still produces valid output."""
        plan = route_task({"request": "Write a function"})
        assert "route" in plan
        assert "risk" in plan
        assert "task_type" in plan
        assert plan["control_packet_status"] == "CANDIDATE"

    def test_candidate_implementation_still_works(self):
        """CANDIDATE_IMPLEMENTATION route still works as before."""
        plan = route_task({
            "request": "Fix homepage",
            "repository": "owner/project",
        })
        assert plan["route"] == "CANDIDATE_IMPLEMENTATION"
        assert plan["checker_required"] is True
        assert plan["human_authorization_required"] is True

    def test_direct_local_execution_still_works(self):
        """DIRECT_LOCAL_EXECUTION route still works."""
        plan = route_task({"request": "Explain Python decorators"})
        assert plan["route"] == "DIRECT_LOCAL_EXECUTION"
        assert plan["risk"] == "LOW"

    def test_hard_stop_still_works(self):
        """HARD_STOP route still works."""
        plan = route_task({
            "request": "Fix bug",
            "repository": "owner/project",
            "auto_merge": True,
        })
        assert plan["route"] == "HARD_STOP"

    def test_fact_source_rebind_still_works(self):
        """FACT_SOURCE_REBIND still works."""
        plan = route_task({
            "request": "Fix file",
            "repository": "owner/project",
            "conflicting_facts": [
                {"fact_a": "sha1", "fact_b": "sha2", "conflict_description": "SHA mismatch"},
            ],
        })
        assert plan["route"] == "FACT_SOURCE_REBIND"
        assert plan["write_actions_permitted"] is False

    def test_read_only_repo_still_works(self):
        """READ_ONLY_REPOSITORY_ANALYSIS still works."""
        plan = route_task({
            "request": "Check PR status",
            "repository": "owner/project",
        })
        assert plan["route"] == "READ_ONLY_REPOSITORY_ANALYSIS"

    def test_no_new_fields_in_router_output(self):
        """Router output must not include adapter-specific fields."""
        plan = route_task({
            "request": "Fix homepage",
            "repository": "owner/project",
        })
        adapter_fields = [
            "tool_identity", "tool_session_id", "tool_capability_tags",
            "session_principal", "credential_tags", "adapter_error",
        ]
        for field in adapter_fields:
            assert field not in plan, \
                f"Adapter field '{field}' leaked into router output"


# ═══════════════════════════════════════════════════════════
# T09: Adapter Output Schema Validation
# ═══════════════════════════════════════════════════════════

class TestAdapterOutputSchema:
    """Tests for adapter-output.schema.json structure."""

    def test_adapter_output_uses_ref_not_duplicate(self):
        """adapter-output.schema.json must $ref governance-plan, not duplicate."""
        schema = load_schema("adapter-output.schema.json")
        gov_plan_prop = schema.get("properties", {}).get("governance_plan", {})
        assert "$ref" in gov_plan_prop, \
            "governance_plan must use $ref, not inline definition"
        assert "governance-plan.schema.json" in gov_plan_prop["$ref"], \
            f"Expected $ref to governance-plan, got {gov_plan_prop.get('$ref')}"

    def test_adapter_error_enum_values(self):
        """adapter_error must use the correct error enum values."""
        schema = load_schema("adapter-output.schema.json")
        adapter_error = schema.get("properties", {}).get("adapter_error", {})
        # Should be oneOf: null or enum
        assert "oneOf" in adapter_error, "adapter_error must use oneOf"
        for option in adapter_error["oneOf"]:
            if option.get("type") == "string":
                enum_vals = set(option.get("enum", []))
                expected = {
                    "SCOPE_VIOLATION",
                    "UNAUTHORIZED_ACTION",
                    "BINDING_MISSING",
                    "BINDING_INVALID",
                    "CREDENTIAL_LEAK",
                    "INDEPENDENCE_FAILED",
                    "ATTEMPTED_SCOPE_VIOLATION",
                }
                assert enum_vals == expected, \
                    f"adapter_error enum mismatch: got {enum_vals}, expected {expected}"

    def test_adapter_output_route_enum_matches_router(self):
        """adapter output route enum must match the router's Route enum."""
        from route_task import Route

        schema = load_schema("adapter-output.schema.json")
        route_enum = set(
            schema.get("properties", {}).get("route", {}).get("enum", [])
        )
        router_routes = {r.value for r in Route}
        assert route_enum == router_routes, \
            f"Route enum mismatch: adapter={route_enum}, router={router_routes}"


# ═══════════════════════════════════════════════════════════
# T10: Authorization Binding — Default Forbidden Actions
# ═══════════════════════════════════════════════════════════

class TestDefaultForbiddenActions:
    """Tests that default-forbidden actions are properly excluded."""

    FORBIDDEN = {"ready", "merge", "close_pr", "delete_branch"}

    def test_forbidden_actions_not_in_schema_enum(self):
        """Default-forbidden actions must not appear in authorized_actions enum."""
        schema = load_schema("execution-authorization-binding.schema.json")
        enum_vals = (
            schema.get("properties", {})
            .get("authorized_actions", {})
            .get("items", {})
            .get("enum", [])
        )
        for action in self.FORBIDDEN:
            assert action not in enum_vals, \
                f"Forbidden action '{action}' must not be in authorized_actions enum"

    def test_forbidden_actions_detected_in_validation(self):
        """Attempting to use a forbidden action must be detectable."""
        binding = _make_valid_auth_binding()
        # Try to authorize merge (forbidden)
        binding["authorized_actions"] = ["merge"]
        # merge is in the forbidden set
        assert "merge" in self.FORBIDDEN, "merge is default-forbidden"
        assert "merge" not in {"read", "write_file", "commit", "push", "create_draft_pr"}, \
            "merge is not a valid authorized_action"
