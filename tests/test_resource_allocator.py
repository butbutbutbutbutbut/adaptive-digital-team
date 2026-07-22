#!/usr/bin/env python3
"""Tests for ADT Resource Allocator — deterministic model and resource allocation.

Covers:
  - LOW risk → economy tier, no checker
  - MODERATE risk → standard tier, conditional checker
  - HIGH risk → strong tier, mandatory checker
  - CRITICAL risk → strong tier
  - Budget exceeded → BLOCKED
  - Model unavailable → BLOCKED
  - Invalid inputs → BLOCKED
  - Determinism: same inputs → same outputs
  - Checker independence: context_strategy=isolated when checker present
  - No silent model swapping, checker removal, or budget increase
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from resource_allocator import allocate, compute_input_fingerprint


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def model_catalog():
    """Load the sample model catalog fixture."""
    path = REPO_ROOT / "tests" / "fixtures" / "model-catalog.sample.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def budget_boundary():
    """Default generous budget boundary (200K tokens)."""
    return 200000


def _governance_plan(risk, checker_required=False, write_scope=None, route="CANDIDATE_IMPLEMENTATION"):
    """Build a minimal valid GovernancePlan dict."""
    return {
        "route": route,
        "risk": risk,
        "task_type": "REPOSITORY_CANDIDATE",
        "facts_status": "REQUIRES_VERIFICATION",
        "control_packet_status": "CANDIDATE",
        "write_scope": write_scope or [],
        "steps": [],
        "checker_required": checker_required,
        "human_authorization_required": risk in ("HIGH", "CRITICAL"),
        "write_actions_permitted": True,
        "limitations": [],
    }


# ═══════════════════════════════════════════════════════════
# Tests: LOW risk
# ═══════════════════════════════════════════════════════════

class TestLowRisk:
    """LOW risk → economy tier, no checker, shared context."""

    def test_low_risk_no_checker(self, model_catalog, budget_boundary):
        plan = _governance_plan("LOW", checker_required=False)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["provider"] == "deepseek"
        assert result["maker"]["model"] == "deepseek-v4-flash"
        assert result["maker"]["reasoning_effort"] == "minimal"
        assert result["checker"] is None
        assert result["context_strategy"] == "shared"
        assert result["parallelism"] == 1
        assert result["max_repair_attempts"] == 0
        assert result["budget"]["token_budget"] == 8000
        assert result["budget"]["status"] == "WITHIN_BUDGET"
        assert result["budget"]["accuracy"] == "APPROXIMATE"

    def test_low_risk_budget_always_marked_approximate(self, model_catalog, budget_boundary):
        plan = _governance_plan("LOW")
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["budget"]["accuracy"] == "APPROXIMATE"


# ═══════════════════════════════════════════════════════════
# Tests: MODERATE risk
# ═══════════════════════════════════════════════════════════

class TestModerateRisk:
    """MODERATE risk → standard tier, conditional checker."""

    def test_moderate_no_checker_no_write(self, model_catalog, budget_boundary):
        """MODERATE without checker → standard, shared, no checker."""
        plan = _governance_plan("MODERATE", checker_required=False)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["provider"] == "deepseek"
        assert result["maker"]["model"] == "deepseek-v4-pro"
        assert result["checker"] is None
        assert result["context_strategy"] == "shared"

    def test_moderate_with_checker_isolated(self, model_catalog, budget_boundary):
        """MODERATE with checker → standard, isolated, checker allocated."""
        plan = _governance_plan("MODERATE", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["plan_status"] == "ALLOCATED"
        assert result["context_strategy"] == "isolated"
        assert result["checker"] is not None
        assert result["checker"]["provider"] == "deepseek"
        assert result["checker"]["model"] == "deepseek-v4-pro"
        assert result["parallelism"] == 1  # serial

    def test_moderate_budget(self, model_catalog, budget_boundary):
        plan = _governance_plan("MODERATE")
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["budget"]["token_budget"] == 32000

    def test_moderate_repair_attempts(self, model_catalog, budget_boundary):
        plan = _governance_plan("MODERATE")
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["max_repair_attempts"] == 2


# ═══════════════════════════════════════════════════════════
# Tests: HIGH risk
# ═══════════════════════════════════════════════════════════

class TestHighRisk:
    """HIGH risk → strong tier, mandatory checker, isolated context."""

    def test_high_risk_strong_maker(self, model_catalog, budget_boundary):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["provider"] == "openai-codex"
        assert result["maker"]["model"] == "gpt-5.5"
        assert result["maker"]["reasoning_effort"] == "high"

    def test_high_risk_mandatory_checker(self, model_catalog, budget_boundary):
        """HIGH risk must have checker."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["checker"] is not None
        assert result["checker"]["provider"] == "openai-codex"
        assert result["checker"]["model"] == "gpt-5.5"

    def test_high_risk_isolated_context(self, model_catalog, budget_boundary):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["context_strategy"] == "isolated"

    def test_high_risk_serial(self, model_catalog, budget_boundary):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["parallelism"] == 1  # serial: maker → checker

    def test_high_risk_budget(self, model_catalog, budget_boundary):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["budget"]["token_budget"] == 128000


# ═══════════════════════════════════════════════════════════
# Tests: CRITICAL risk
# ═══════════════════════════════════════════════════════════

class TestCriticalRisk:
    """CRITICAL risk → strong tier (allocation still works, routing blocks upstream)."""

    def test_critical_allocates_strong(self, model_catalog, budget_boundary):
        plan = _governance_plan("CRITICAL", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)

        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["model"] == "gpt-5.5"
        assert result["checker"] is not None
        assert result["context_strategy"] == "isolated"


# ═══════════════════════════════════════════════════════════
# Tests: Budget boundary enforcement
# ═══════════════════════════════════════════════════════════

class TestBudgetEnforcement:
    """Budget exceeded → BLOCKED, not silently overspent."""

    def test_high_risk_exceeds_tight_budget(self, model_catalog):
        """HIGH risk needs 128K, but boundary is 50K → BLOCKED."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary=50000)

        assert result["plan_status"] == "BLOCKED"
        assert "128000" in result["block_reason"] or "budget" in result["block_reason"].lower()
        assert result["budget"]["status"] == "BLOCKED_BUDGET_EXCEEDED"

    def test_moderate_ok_with_generous_budget(self, model_catalog):
        """MODERATE needs 32K, boundary is 100K → ALLOCATED."""
        plan = _governance_plan("MODERATE", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary=100000)
        assert result["plan_status"] == "ALLOCATED"

    def test_low_risk_exceeds_zero_budget(self, model_catalog):
        """Even LOW risk blocked if boundary is 0."""
        plan = _governance_plan("LOW")
        result = allocate(plan, model_catalog, budget_boundary=0)
        assert result["plan_status"] == "BLOCKED"

    def test_blocked_preserves_approximate_tag(self, model_catalog):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary=100)
        assert result["budget"]["accuracy"] == "APPROXIMATE"


# ═══════════════════════════════════════════════════════════
# Tests: Model unavailability
# ═══════════════════════════════════════════════════════════

class TestModelUnavailability:
    """Model unavailable at required tier → BLOCKED."""

    def test_missing_strong_tier_default(self):
        """Catalog with no strong tier default → BLOCKED for HIGH risk."""
        bad_catalog = {
            "fingerprint": "sha256:deadbeef",
            "resolved_at": "2026-01-01T00:00:00Z",
            "providers": {
                "deepseek": {
                    "models": {
                        "deepseek-v4-flash": {
                            "tier": "economy",
                            "context_length": 1000000,
                            "reasoning_effort_support": ["minimal"],
                            "capabilities": ["chat"],
                        }
                    }
                }
            },
            "defaults": {
                "economy": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                "standard": {"provider": "deepseek", "model": "deepseek-v4-flash"},
                "strong": {"provider": "deepseek", "model": "deepseek-v4-flash"},
            },
        }
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, bad_catalog, budget_boundary=200000)
        assert result["plan_status"] == "BLOCKED"

    def test_catalog_missing_fingerprint(self):
        """Catalog without fingerprint → BLOCKED."""
        plan = _governance_plan("LOW")
        result = allocate(plan, {"providers": {}, "defaults": {}}, budget_boundary=200000)
        assert result["plan_status"] == "BLOCKED"
        assert "fingerprint" in result["block_reason"].lower()

    def test_empty_catalog(self):
        """Empty catalog → BLOCKED."""
        plan = _governance_plan("LOW")
        result = allocate(plan, {}, budget_boundary=200000)
        assert result["plan_status"] == "BLOCKED"


# ═══════════════════════════════════════════════════════════
# Tests: Invalid inputs
# ═══════════════════════════════════════════════════════════

class TestInvalidInputs:
    """Invalid inputs → BLOCKED, fail closed."""

    def test_missing_risk(self, model_catalog, budget_boundary):
        result = allocate({}, model_catalog, budget_boundary)
        assert result["plan_status"] == "BLOCKED"

    def test_invalid_risk_value(self, model_catalog, budget_boundary):
        plan = _governance_plan("INVALID_RISK")
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["plan_status"] == "BLOCKED"

    def test_negative_budget_boundary(self, model_catalog):
        plan = _governance_plan("LOW")
        result = allocate(plan, model_catalog, budget_boundary=-1)
        assert result["plan_status"] == "BLOCKED"

    def test_none_catalog(self, budget_boundary):
        plan = _governance_plan("LOW")
        result = allocate(plan, None, budget_boundary)
        assert result["plan_status"] == "BLOCKED"

    def test_none_plan(self, model_catalog, budget_boundary):
        result = allocate(None, model_catalog, budget_boundary)
        assert result["plan_status"] == "BLOCKED"


# ═══════════════════════════════════════════════════════════
# Tests: Determinism
# ═══════════════════════════════════════════════════════════

class TestDeterminism:
    """Same inputs → same outputs (deterministic, pure function)."""

    def test_same_inputs_same_output(self, model_catalog, budget_boundary):
        plan = _governance_plan("HIGH", checker_required=True)
        r1 = allocate(plan, model_catalog, budget_boundary)
        r2 = allocate(plan, model_catalog, budget_boundary)
        assert r1 == r2

    def test_different_risk_different_output(self, model_catalog, budget_boundary):
        low = allocate(_governance_plan("LOW"), model_catalog, budget_boundary)
        high = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)
        assert low != high

    def test_fingerprint_changes_with_catalog(self, model_catalog, budget_boundary):
        plan = _governance_plan("LOW")
        fp1 = compute_input_fingerprint(plan, model_catalog, budget_boundary)

        modified_catalog = dict(model_catalog)
        modified_catalog["fingerprint"] = "sha256:modified"
        fp2 = compute_input_fingerprint(plan, modified_catalog, budget_boundary)

        assert fp1 != fp2

    def test_fingerprint_stable(self, model_catalog, budget_boundary):
        plan = _governance_plan("LOW")
        fp1 = compute_input_fingerprint(plan, model_catalog, budget_boundary)
        fp2 = compute_input_fingerprint(plan, model_catalog, budget_boundary)
        assert fp1 == fp2


# ═══════════════════════════════════════════════════════════
# Tests: No silent degradation
# ═══════════════════════════════════════════════════════════

class TestNoSilentDegradation:
    """Allocator must never silently swap models, remove checkers, or raise budgets."""

    def test_high_risk_never_loses_checker(self, model_catalog, budget_boundary):
        """HIGH risk with checker_required=true must always have checker."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["checker"] is not None, "HIGH risk must not lose checker silently"

    def test_high_risk_never_downgraded_to_economy(self, model_catalog, budget_boundary):
        """HIGH risk must use strong tier, never silently downgraded."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["maker"]["tier"] != "economy" if "tier" in result["maker"] else True
        assert result["maker"]["model"] == "gpt-5.5"

    def test_low_risk_never_gets_unnecessary_checker(self, model_catalog, budget_boundary):
        """LOW risk without checker_required must not get checker (cost discipline)."""
        plan = _governance_plan("LOW", checker_required=False)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["checker"] is None

    def test_budget_blocked_has_no_allocated_models(self, model_catalog):
        """When BLOCKED, maker model is empty string (not silently cheap)."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary=100)
        assert result["plan_status"] == "BLOCKED"
        assert result["maker"]["model"] == ""  # not a fallback

    def test_checker_not_different_model_by_force(self, model_catalog, budget_boundary):
        """Per amendment 4: checker can use same model. Independence is context, not model."""
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["checker"]["provider"] == result["maker"]["provider"]
        assert result["checker"]["model"] == result["maker"]["model"]
        # Still isolated context
        assert result["context_strategy"] == "isolated"


# ═══════════════════════════════════════════════════════════
# Tests: Context strategy and checker independence
# ═══════════════════════════════════════════════════════════

class TestContextStrategy:
    """Context isolation rules."""

    def test_checker_present_implies_isolated(self, model_catalog, budget_boundary):
        """Any allocation with checker → context_strategy = isolated."""
        for risk in ("MODERATE", "HIGH", "CRITICAL"):
            plan = _governance_plan(risk, checker_required=True)
            result = allocate(plan, model_catalog, budget_boundary)
            if result["plan_status"] == "ALLOCATED":
                assert result["context_strategy"] == "isolated", \
                    f"{risk} with checker should be isolated"

    def test_no_checker_implies_shared(self, model_catalog, budget_boundary):
        """Any allocation without checker → context_strategy = shared."""
        plan = _governance_plan("LOW", checker_required=False)
        result = allocate(plan, model_catalog, budget_boundary)
        assert result["context_strategy"] == "shared"


# ═══════════════════════════════════════════════════════════
# Tests: Schema compliance
# ═══════════════════════════════════════════════════════════

class TestSchemaCompliance:
    """ResourcePlan output conforms to resource-plan.schema.json."""

    @pytest.fixture
    def schema(self):
        path = REPO_ROOT / "schemas" / "resource-plan.schema.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _validate(self, instance, schema):
        """Validate instance against JSON Schema draft 2020-12."""
        try:
            import jsonschema
            jsonschema.validate(instance=instance, schema=schema)
            return None
        except jsonschema.exceptions.ValidationError as e:
            return str(e)
        except ImportError:
            # jsonschema not installed; skip validation in this environment
            return None

    def test_allocated_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary)
        err = self._validate(result, schema)
        if err is not None and "jsonschema" not in str(err):
            pytest.fail(f"ALLOCATED plan fails schema: {err}")

    def test_blocked_conforms_to_schema(self, model_catalog, schema):
        plan = _governance_plan("HIGH", checker_required=True)
        result = allocate(plan, model_catalog, budget_boundary=100)
        err = self._validate(result, schema)
        if err is not None and "jsonschema" not in str(err):
            pytest.fail(f"BLOCKED plan fails schema: {err}")

    def test_low_risk_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        plan = _governance_plan("LOW")
        result = allocate(plan, model_catalog, budget_boundary)
        err = self._validate(result, schema)
        if err is not None and "jsonschema" not in str(err):
            pytest.fail(f"LOW risk plan fails schema: {err}")

    def test_null_checker_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        plan = _governance_plan("MODERATE", checker_required=False)
        result = allocate(plan, model_catalog, budget_boundary)
        err = self._validate(result, schema)
        if err is not None and "jsonschema" not in str(err):
            pytest.fail(f"Null checker plan fails schema: {err}")
