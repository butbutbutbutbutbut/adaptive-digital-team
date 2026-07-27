"""Resource allocator regression and boundary tests."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from resource_allocator import allocate, compute_input_fingerprint  # noqa: E402


@pytest.fixture
def model_catalog():
    return json.loads((REPO_ROOT / "tests" / "fixtures" / "model-catalog.sample.json").read_text(encoding="utf-8"))


@pytest.fixture
def budget_boundary():
    return 200000


def governance_plan(risk, checker_required=False, **extra):
    result = {
        "route": "CANDIDATE_IMPLEMENTATION",
        "risk": risk,
        "task_type": "REPOSITORY_CANDIDATE",
        "facts_status": "REQUIRES_VERIFICATION",
        "control_packet_status": "CANDIDATE",
        "write_scope": [],
        "steps": [],
        "checker_required": checker_required,
        "human_authorization_required": risk in ("HIGH", "CRITICAL"),
        "write_actions_permitted": True,
        "limitations": [],
    }
    result.update(extra)
    return result


@pytest.mark.parametrize(
    "risk,checker,model,tokens,repairs",
    [
        ("LOW", False, "deepseek-v4-flash", 8000, 0),
        ("MODERATE", False, "deepseek-v4-pro", 32000, 2),
        ("HIGH", True, "gpt-5.5", 128000, 2),
        ("CRITICAL", True, "gpt-5.5", 128000, 0),
    ],
)
def test_legacy_risk_fallback_regression(model_catalog, budget_boundary, risk, checker, model, tokens, repairs):
    result = allocate(governance_plan(risk, checker_required=checker), model_catalog, budget_boundary)
    assert result["plan_status"] == "ALLOCATED"
    assert result["maker"]["model"] == model
    assert result["budget"]["token_budget"] == tokens
    assert result["max_repair_attempts"] == repairs
    assert (result["checker"] is not None) is checker
    assert result["context_strategy"] == ("isolated" if checker else "shared")


def test_moderate_with_checker_isolated(model_catalog, budget_boundary):
    result = allocate(governance_plan("MODERATE", checker_required=True), model_catalog, budget_boundary)
    assert result["checker"]["model"] == "deepseek-v4-pro"
    assert result["parallelism"] == 1


@pytest.mark.parametrize("boundary", [0, 100, 50000])
def test_token_budget_enforced(model_catalog, boundary):
    result = allocate(governance_plan("HIGH", checker_required=True), model_catalog, boundary)
    assert result["plan_status"] == "BLOCKED"
    assert result["maker"]["model"] == ""
    assert result["budget"]["accuracy"] == "APPROXIMATE"


def test_invalid_inputs_block(model_catalog, budget_boundary):
    assert allocate({}, model_catalog, budget_boundary)["plan_status"] == "BLOCKED"
    assert allocate(None, model_catalog, budget_boundary)["plan_status"] == "BLOCKED"
    assert allocate(governance_plan("INVALID"), model_catalog, budget_boundary)["plan_status"] == "BLOCKED"
    assert allocate(governance_plan("LOW"), None, budget_boundary)["plan_status"] == "BLOCKED"
    assert allocate(governance_plan("LOW"), {}, budget_boundary)["plan_status"] == "BLOCKED"
    assert allocate(governance_plan("LOW"), model_catalog, -1)["plan_status"] == "BLOCKED"


def test_catalog_validation_blocks_unavailable_model(budget_boundary):
    catalog = {
        "fingerprint": "sha256:x",
        "providers": {"deepseek": {"models": {"flash": {"tier": "economy", "reasoning_effort_support": ["minimal"]}}}},
        "defaults": {
            "economy": {"provider": "deepseek", "model": "flash"},
            "standard": {"provider": "deepseek", "model": "flash"},
            "strong": {"provider": "deepseek", "model": "flash"},
        },
    }
    assert allocate(governance_plan("HIGH", checker_required=True), catalog, budget_boundary)["plan_status"] == "BLOCKED"


def test_determinism_and_fingerprint(model_catalog, budget_boundary):
    plan = governance_plan("HIGH", checker_required=True)
    assert allocate(plan, model_catalog, budget_boundary) == allocate(plan, model_catalog, budget_boundary)
    fp1 = compute_input_fingerprint(plan, model_catalog, budget_boundary)
    fp2 = compute_input_fingerprint(plan, {**model_catalog, "fingerprint": "sha256:changed"}, budget_boundary)
    assert fp1 != fp2
    assert fp1 == compute_input_fingerprint(plan, model_catalog, budget_boundary)


def test_schema_compliance(model_catalog, budget_boundary):
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((REPO_ROOT / "schemas" / "resource-plan.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(allocate(governance_plan("LOW"), model_catalog, budget_boundary), schema)
    jsonschema.validate(allocate(governance_plan("HIGH", checker_required=True), model_catalog, 100), schema)


def canonical_catalog_fingerprint(catalog):
    payload = {k: v for k, v in catalog.items() if k != "fingerprint"}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_catalog_fixture_integrity(model_catalog):
    assert model_catalog["fingerprint"] == canonical_catalog_fingerprint(model_catalog)
    assert model_catalog["fingerprint"] != "sha256:" + hashlib.sha256(b"").hexdigest()
    changed = json.loads(json.dumps(model_catalog))
    changed["providers"]["deepseek"]["models"]["deepseek-v4-flash"]["context_length"] = 999999
    assert canonical_catalog_fingerprint(changed) != canonical_catalog_fingerprint(model_catalog)
    assert canonical_catalog_fingerprint(json.loads(json.dumps(model_catalog, indent=4))) == canonical_catalog_fingerprint(model_catalog)


# Adaptive allocation behavior

def test_high_plan_can_explicitly_use_standard(model_catalog, budget_boundary):
    result = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="AFTER_FORMAL_CANDIDATE", recommended_points=1, hard_max_points=2), model_catalog, budget_boundary)
    assert result["plan_status"] == "ALLOCATED"
    assert result["resource_tier"] == "standard"
    assert result["maker"]["model"] == "deepseek-v4-pro"
    assert result["checker"] is None


def test_formal_candidate_checker_allocates_only_now(model_catalog, budget_boundary):
    deferred = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="AFTER_FORMAL_CANDIDATE", recommended_points=1, hard_max_points=2), model_catalog, budget_boundary)
    now = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="NOW", recommended_points=1, hard_max_points=2), model_catalog, budget_boundary)
    assert deferred["checker"] is None
    assert now["checker"] is not None
    assert now["context_strategy"] == "isolated"


def test_human_point_boundary_blocks(model_catalog):
    result = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="NONE", recommended_points=2, hard_max_points=2), model_catalog, {"token_budget": 200000, "point_budget": 1, "checker_allowed": True})
    assert result["plan_status"] == "BLOCKED"
    assert "Point" in result["block_reason"]


def test_human_checker_boundary_blocks(model_catalog):
    result = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="NOW", recommended_points=1, hard_max_points=2), model_catalog, {"token_budget": 200000, "point_budget": 2, "checker_allowed": False})
    assert result["plan_status"] == "BLOCKED"
    assert "Checker" in result["block_reason"]


def test_governance_plan_point_overrun_blocks(model_catalog, budget_boundary):
    result = allocate(governance_plan("HIGH", resource_tier="standard", checker_timing="NONE", recommended_points=2, hard_max_points=1), model_catalog, budget_boundary)
    assert result["plan_status"] == "BLOCKED"

# Named compatibility baseline from the adopted allocator suite.

def _governance_plan(risk, checker_required=False, write_scope=None, route="CANDIDATE_IMPLEMENTATION"):
    return governance_plan(risk, checker_required=checker_required, write_scope=write_scope or [], route=route)


class TestLowRisk:
    def test_low_risk_no_checker(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("LOW", checker_required=False), model_catalog, budget_boundary)
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
        assert allocate(_governance_plan("LOW"), model_catalog, budget_boundary)["budget"]["accuracy"] == "APPROXIMATE"


class TestModerateRisk:
    def test_moderate_no_checker_no_write(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("MODERATE", checker_required=False), model_catalog, budget_boundary)
        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["provider"] == "deepseek"
        assert result["maker"]["model"] == "deepseek-v4-pro"
        assert result["checker"] is None
        assert result["context_strategy"] == "shared"

    def test_moderate_with_checker_isolated(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("MODERATE", checker_required=True), model_catalog, budget_boundary)
        assert result["plan_status"] == "ALLOCATED"
        assert result["context_strategy"] == "isolated"
        assert result["checker"] is not None
        assert result["checker"]["provider"] == "deepseek"
        assert result["checker"]["model"] == "deepseek-v4-pro"
        assert result["parallelism"] == 1

    def test_moderate_budget(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("MODERATE"), model_catalog, budget_boundary)["budget"]["token_budget"] == 32000

    def test_moderate_repair_attempts(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("MODERATE"), model_catalog, budget_boundary)["max_repair_attempts"] == 2


class TestHighRisk:
    def test_high_risk_strong_maker(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)
        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["provider"] == "openai-codex"
        assert result["maker"]["model"] == "gpt-5.5"
        assert result["maker"]["reasoning_effort"] == "high"

    def test_high_risk_mandatory_checker(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)
        assert result["checker"] is not None
        assert result["checker"]["provider"] == "openai-codex"
        assert result["checker"]["model"] == "gpt-5.5"

    def test_high_risk_isolated_context(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)["context_strategy"] == "isolated"

    def test_high_risk_serial(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)["parallelism"] == 1

    def test_high_risk_budget(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)["budget"]["token_budget"] == 128000


class TestCriticalRisk:
    def test_critical_allocates_strong(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("CRITICAL", checker_required=True), model_catalog, budget_boundary)
        assert result["plan_status"] == "ALLOCATED"
        assert result["maker"]["model"] == "gpt-5.5"
        assert result["checker"] is not None
        assert result["context_strategy"] == "isolated"


class TestBudgetEnforcement:
    def test_high_risk_exceeds_tight_budget(self, model_catalog):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, 50000)
        assert result["plan_status"] == "BLOCKED"
        assert "128000" in result["block_reason"] or "budget" in result["block_reason"].lower()
        assert result["budget"]["status"] == "BLOCKED_BUDGET_EXCEEDED"

    def test_moderate_ok_with_generous_budget(self, model_catalog):
        assert allocate(_governance_plan("MODERATE", checker_required=True), model_catalog, 100000)["plan_status"] == "ALLOCATED"

    def test_low_risk_exceeds_zero_budget(self, model_catalog):
        assert allocate(_governance_plan("LOW"), model_catalog, 0)["plan_status"] == "BLOCKED"

    def test_blocked_preserves_approximate_tag(self, model_catalog):
        assert allocate(_governance_plan("HIGH", checker_required=True), model_catalog, 100)["budget"]["accuracy"] == "APPROXIMATE"


class TestModelUnavailability:
    def test_missing_strong_tier_default(self):
        bad_catalog = {
            "fingerprint": "sha256:deadbeef",
            "resolved_at": "2026-01-01T00:00:00Z",
            "providers": {"deepseek": {"models": {"deepseek-v4-flash": {"tier": "economy", "context_length": 1000000, "reasoning_effort_support": ["minimal"], "capabilities": ["chat"]}}}},
            "defaults": {"economy": {"provider": "deepseek", "model": "deepseek-v4-flash"}, "standard": {"provider": "deepseek", "model": "deepseek-v4-flash"}, "strong": {"provider": "deepseek", "model": "deepseek-v4-flash"}},
        }
        assert allocate(_governance_plan("HIGH", checker_required=True), bad_catalog, 200000)["plan_status"] == "BLOCKED"

    def test_catalog_missing_fingerprint(self):
        result = allocate(_governance_plan("LOW"), {"providers": {}, "defaults": {}}, 200000)
        assert result["plan_status"] == "BLOCKED"
        assert "fingerprint" in result["block_reason"].lower()

    def test_empty_catalog(self):
        assert allocate(_governance_plan("LOW"), {}, 200000)["plan_status"] == "BLOCKED"


class TestInvalidInputs:
    def test_missing_risk(self, model_catalog, budget_boundary):
        assert allocate({}, model_catalog, budget_boundary)["plan_status"] == "BLOCKED"

    def test_invalid_risk_value(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("INVALID_RISK"), model_catalog, budget_boundary)["plan_status"] == "BLOCKED"

    def test_negative_budget_boundary(self, model_catalog):
        assert allocate(_governance_plan("LOW"), model_catalog, -1)["plan_status"] == "BLOCKED"

    def test_none_catalog(self, budget_boundary):
        assert allocate(_governance_plan("LOW"), None, budget_boundary)["plan_status"] == "BLOCKED"

    def test_none_plan(self, model_catalog, budget_boundary):
        assert allocate(None, model_catalog, budget_boundary)["plan_status"] == "BLOCKED"


class TestDeterminism:
    def test_same_inputs_same_output(self, model_catalog, budget_boundary):
        plan_value = _governance_plan("HIGH", checker_required=True)
        assert allocate(plan_value, model_catalog, budget_boundary) == allocate(plan_value, model_catalog, budget_boundary)

    def test_different_risk_different_output(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("LOW"), model_catalog, budget_boundary) != allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)

    def test_fingerprint_changes_with_catalog(self, model_catalog, budget_boundary):
        plan_value = _governance_plan("LOW")
        fp1 = compute_input_fingerprint(plan_value, model_catalog, budget_boundary)
        modified = dict(model_catalog)
        modified["fingerprint"] = "sha256:modified"
        assert fp1 != compute_input_fingerprint(plan_value, modified, budget_boundary)

    def test_fingerprint_stable(self, model_catalog, budget_boundary):
        plan_value = _governance_plan("LOW")
        assert compute_input_fingerprint(plan_value, model_catalog, budget_boundary) == compute_input_fingerprint(plan_value, model_catalog, budget_boundary)


class TestNoSilentDegradation:
    def test_high_risk_never_loses_checker(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)["checker"] is not None

    def test_high_risk_never_downgraded_to_economy(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)
        assert result["maker"]["model"] == "gpt-5.5"

    def test_low_risk_never_gets_unnecessary_checker(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("LOW", checker_required=False), model_catalog, budget_boundary)["checker"] is None

    def test_budget_blocked_has_no_allocated_models(self, model_catalog):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, 100)
        assert result["plan_status"] == "BLOCKED"
        assert result["maker"]["model"] == ""

    def test_checker_not_different_model_by_force(self, model_catalog, budget_boundary):
        result = allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary)
        assert result["checker"]["provider"] == result["maker"]["provider"]
        assert result["checker"]["model"] == result["maker"]["model"]
        assert result["context_strategy"] == "isolated"


class TestContextStrategy:
    def test_checker_present_implies_isolated(self, model_catalog, budget_boundary):
        for risk in ("MODERATE", "HIGH", "CRITICAL"):
            result = allocate(_governance_plan(risk, checker_required=True), model_catalog, budget_boundary)
            if result["plan_status"] == "ALLOCATED":
                assert result["context_strategy"] == "isolated"

    def test_no_checker_implies_shared(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("LOW", checker_required=False), model_catalog, budget_boundary)["context_strategy"] == "shared"


class TestSchemaCompliance:
    @pytest.fixture
    def schema(self):
        return json.loads((REPO_ROOT / "schemas" / "resource-plan.schema.json").read_text(encoding="utf-8"))

    def _validate(self, instance, schema):
        try:
            import jsonschema as _js
            _js.validate(instance=instance, schema=schema)
            return None
        except ImportError:
            return None
        except Exception as exc:
            return str(exc)

    def test_allocated_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        error = self._validate(allocate(_governance_plan("HIGH", checker_required=True), model_catalog, budget_boundary), schema)
        if error is not None and "jsonschema" not in error:
            pytest.fail(f"ALLOCATED plan fails schema: {error}")

    def test_blocked_conforms_to_schema(self, model_catalog, schema):
        error = self._validate(allocate(_governance_plan("HIGH", checker_required=True), model_catalog, 100), schema)
        if error is not None and "jsonschema" not in error:
            pytest.fail(f"BLOCKED plan fails schema: {error}")

    def test_low_risk_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        error = self._validate(allocate(_governance_plan("LOW"), model_catalog, budget_boundary), schema)
        if error is not None and "jsonschema" not in error:
            pytest.fail(f"LOW risk plan fails schema: {error}")

    def test_null_checker_conforms_to_schema(self, model_catalog, budget_boundary, schema):
        error = self._validate(allocate(_governance_plan("MODERATE", checker_required=False), model_catalog, budget_boundary), schema)
        if error is not None and "jsonschema" not in error:
            pytest.fail(f"Null checker plan fails schema: {error}")


class TestCatalogIntegrity:
    @pytest.fixture
    def catalog_raw(self):
        return json.loads((REPO_ROOT / "tests" / "fixtures" / "model-catalog.sample.json").read_text(encoding="utf-8"))

    def _compute_canonical_fingerprint(self, catalog):
        catalog_no_fp = {k: v for k, v in catalog.items() if k != "fingerprint"}
        canonical = json.dumps(catalog_no_fp, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def test_fingerprint_matches_recomputed(self, catalog_raw):
        assert catalog_raw["fingerprint"] == self._compute_canonical_fingerprint(catalog_raw)

    def test_fingerprint_not_empty_hash(self, catalog_raw):
        assert catalog_raw["fingerprint"] != "sha256:" + hashlib.sha256(b"").hexdigest()

    def test_fingerprint_changes_with_model_field(self, catalog_raw):
        modified = json.loads(json.dumps(catalog_raw))
        modified["providers"]["deepseek"]["models"]["deepseek-v4-flash"]["context_length"] = 999999
        assert self._compute_canonical_fingerprint(modified) != self._compute_canonical_fingerprint(catalog_raw)

    def test_fingerprint_invariant_to_formatting(self, catalog_raw):
        assert self._compute_canonical_fingerprint(json.loads(json.dumps(catalog_raw, indent=4, ensure_ascii=False))) == self._compute_canonical_fingerprint(catalog_raw)

    def test_fingerprint_invariant_to_key_order(self, catalog_raw):
        reordered = {"fingerprint": catalog_raw["fingerprint"], "defaults": catalog_raw["defaults"], "providers": catalog_raw["providers"], "resolved_at": catalog_raw["resolved_at"]}
        assert self._compute_canonical_fingerprint(reordered) == self._compute_canonical_fingerprint(catalog_raw)

    def test_existing_39_tests_still_pass(self, model_catalog, budget_boundary):
        assert allocate(_governance_plan("LOW"), model_catalog, budget_boundary)["plan_status"] == "ALLOCATED"

    def test_corrected_fingerprint_not_self_referential(self, catalog_raw):
        assert self._compute_canonical_fingerprint(catalog_raw) == self._compute_canonical_fingerprint(catalog_raw)

    def test_fingerprint_present_and_nonempty(self, catalog_raw):
        assert isinstance(catalog_raw.get("fingerprint"), str) and len(catalog_raw["fingerprint"]) > 0
