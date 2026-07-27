#!/usr/bin/env python3
"""ADT Resource Allocator.

Consumes GovernancePlan.resource_tier and GovernancePlan.checker_timing.
Safety risk remains descriptive and is not the primary allocation key.
Legacy symbols and call signatures remain available for existing consumers.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

LEGACY_TIER_MAP = {"LOW": "economy", "MODERATE": "standard", "HIGH": "strong", "CRITICAL": "strong"}
# Backward-compatible public name used by the adopted allocator tests/consumers.
TIER_MAP = LEGACY_TIER_MAP
BUDGET_MAP = {"economy": 8000, "standard": 32000, "strong": 128000}
REASONING_MAP = {"economy": "minimal", "standard": "medium", "strong": "high"}
ITERATIONS_MAP = {"economy": 20, "standard": 40, "strong": 50}
REPAIR_MAP = {"LOW": 0, "MODERATE": 2, "HIGH": 2, "CRITICAL": 0}
VALID_RISKS = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
VALID_TIERS = {"economy", "standard", "strong"}
VALID_CHECKER_TIMINGS = {"NONE", "AFTER_FORMAL_CANDIDATE", "NOW"}


def _validate_governance_plan(plan: dict[str, Any]) -> str | None:
    if not isinstance(plan, dict):
        return "GovernancePlan must be a dict"
    risk = plan.get("risk", "")
    if risk not in VALID_RISKS:
        return f"Invalid or missing risk: {risk!r}"
    tier = plan.get("resource_tier")
    if tier is not None and tier not in VALID_TIERS:
        return f"Invalid resource_tier: {tier!r}"
    timing = plan.get("checker_timing")
    if timing is not None and timing not in VALID_CHECKER_TIMINGS:
        return f"Invalid checker_timing: {timing!r}"
    recommended = plan.get("recommended_points", 0)
    hard_max = plan.get("hard_max_points", 2)
    if not isinstance(recommended, int) or not isinstance(hard_max, int) or recommended < 0 or hard_max < 0:
        return "Point boundaries must be non-negative integers"
    if recommended > hard_max:
        return f"Recommended points {recommended} exceed Human hard max {hard_max}"
    return None


def _validate_model_catalog(catalog: dict[str, Any]) -> str | None:
    if not isinstance(catalog, dict):
        return "Model catalog must be a dict"
    if "fingerprint" not in catalog:
        return "Model catalog missing fingerprint — must be a pre-resolved frozen snapshot"
    providers = catalog.get("providers", {})
    if not isinstance(providers, dict) or not providers:
        return "Model catalog has no providers"
    defaults = catalog.get("defaults", {})
    for tier in VALID_TIERS:
        d = defaults.get(tier)
        if not isinstance(d, dict):
            return f"Model catalog defaults missing tier: {tier}"
        provider, model = d.get("provider", ""), d.get("model", "")
        if not provider or not model:
            return f"Incomplete default for tier {tier}"
        if provider not in providers or model not in providers[provider].get("models", {}):
            return f"Default model {provider}/{model} for tier={tier} not in catalog"
    return None


def _validate_budget_boundary(boundary: int) -> str | None:
    """Legacy integer-boundary validator retained for compatibility."""
    if not isinstance(boundary, int) or boundary < 0:
        return f"Invalid budget boundary: {boundary!r}"
    return None


def _normalize_boundary(boundary: int | dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(boundary, int):
        err = _validate_budget_boundary(boundary)
        if err:
            return None, err
        return {"token_budget": boundary, "point_budget": 2, "checker_allowed": True}, None
    if not isinstance(boundary, dict):
        return None, f"Invalid budget boundary: {boundary!r}"
    token_budget = boundary.get("token_budget")
    point_budget = boundary.get("point_budget", 2)
    checker_allowed = boundary.get("checker_allowed", True)
    if not isinstance(token_budget, int) or token_budget < 0:
        return None, f"Invalid token boundary: {token_budget!r}"
    if not isinstance(point_budget, int) or point_budget < 0:
        return None, f"Invalid point boundary: {point_budget!r}"
    if not isinstance(checker_allowed, bool):
        return None, "checker_allowed must be boolean"
    return {"token_budget": token_budget, "point_budget": point_budget, "checker_allowed": checker_allowed}, None


def _select_model(
    catalog: dict[str, Any],
    tier: str,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
) -> dict[str, str] | None:
    """Select a tier-matching model; preserve the adopted optional overrides."""
    if preferred_provider and preferred_model:
        provider, model = preferred_provider, preferred_model
    else:
        default = catalog.get("defaults", {}).get(tier, {})
        provider, model = default.get("provider", ""), default.get("model", "")
    info = catalog.get("providers", {}).get(provider, {}).get("models", {}).get(model)
    if not info or info.get("tier") != tier:
        return None
    return {"provider": provider, "model": model}


def _build_agent_config(
    catalog: dict[str, Any],
    tier: str,
    role: str = "maker",
) -> dict[str, Any] | None:
    """Build an agent config; role is retained as a compatibility argument."""
    del role
    selected = _select_model(catalog, tier)
    if selected is None:
        return None
    info = catalog["providers"][selected["provider"]]["models"][selected["model"]]
    supported = set(info.get("reasoning_effort_support", []))
    desired = REASONING_MAP[tier]
    if desired in supported:
        effort = desired
    else:
        order = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"]
        available = [item for item in order if item in supported]
        effort = available[-1] if available else "minimal"
    return {
        "provider": selected["provider"],
        "model": selected["model"],
        "reasoning_effort": effort,
        "max_iterations": ITERATIONS_MAP[tier],
    }


def allocate(
    governance_plan: dict[str, Any],
    model_catalog: dict[str, Any],
    budget_boundary: int | dict[str, Any],
) -> dict[str, Any]:
    err = _validate_governance_plan(governance_plan)
    if err:
        return _blocked(f"Invalid governance plan: {err}")
    err = _validate_model_catalog(model_catalog)
    if err:
        return _blocked(f"Invalid model catalog: {err}")
    boundary, err = _normalize_boundary(budget_boundary)
    if err or boundary is None:
        return _blocked(err or "Invalid Human boundary")

    risk = governance_plan["risk"]
    tier = governance_plan.get("resource_tier") or TIER_MAP[risk]
    timing = governance_plan.get("checker_timing")
    if timing is None:
        checker_now = bool(governance_plan.get("checker_required", False))
        timing = "NOW" if checker_now else "NONE"
    else:
        checker_now = timing == "NOW"

    recommended_points = int(governance_plan.get("recommended_points", 0))
    hard_max_points = int(governance_plan.get("hard_max_points", 2))
    if recommended_points > hard_max_points:
        return _blocked(f"Point request {recommended_points} exceeds plan hard max {hard_max_points}.")
    if hard_max_points > boundary["point_budget"] or recommended_points > boundary["point_budget"]:
        return _blocked(
            f"Point boundary exceeded: recommended={recommended_points}, hard_max={hard_max_points}, Human={boundary['point_budget']}."
        )
    if checker_now and not boundary["checker_allowed"]:
        return _blocked("Checker allocation exceeds the Human checker boundary.")

    maker = _build_agent_config(model_catalog, tier, "maker")
    if maker is None:
        return _blocked(
            f"No model available at tier {tier!r}. Catalog fingerprint: {model_catalog.get('fingerprint', 'unknown')}"
        )

    token_budget = BUDGET_MAP[tier]
    if token_budget > boundary["token_budget"]:
        return _blocked(
            f"Token budget {token_budget} exceeds Human boundary {boundary['token_budget']}. "
            f"Risk={risk}, tier={tier}. Allocation blocked — will not silently overspend."
        )

    checker = None
    context_strategy = "shared"
    if checker_now:
        checker = _build_agent_config(model_catalog, tier, "checker")
        if checker is None:
            return _blocked(f"Checker required now but no model is available at tier {tier!r}.")
        context_strategy = "isolated"

    return {
        "plan_status": "ALLOCATED",
        "resource_tier": tier,
        "checker_timing": timing,
        "maker": maker,
        "checker": checker,
        "budget": {"token_budget": token_budget, "status": "WITHIN_BUDGET", "accuracy": "APPROXIMATE"},
        "points": {"recommended": recommended_points, "hard_max": hard_max_points, "status": "WITHIN_BOUNDARY"},
        "max_repair_attempts": REPAIR_MAP.get(risk, 0),
        "context_strategy": context_strategy,
        "parallelism": 1,
    }


def _blocked(reason: str) -> dict[str, Any]:
    return {
        "plan_status": "BLOCKED",
        "block_reason": reason,
        "resource_tier": "economy",
        "checker_timing": "NONE",
        "maker": {"provider": "", "model": "", "reasoning_effort": "minimal", "max_iterations": 0},
        "checker": None,
        "budget": {"token_budget": 0, "status": "BLOCKED_BUDGET_EXCEEDED", "accuracy": "APPROXIMATE"},
        "points": {"recommended": 0, "hard_max": 0, "status": "BLOCKED_BOUNDARY_EXCEEDED"},
        "max_repair_attempts": 0,
        "context_strategy": "shared",
        "parallelism": 0,
    }


def compute_input_fingerprint(
    governance_plan: dict[str, Any],
    model_catalog: dict[str, Any],
    budget_boundary: int | dict[str, Any],
) -> str:
    canonical = json.dumps(
        {
            "governance_plan": governance_plan,
            "catalog_fingerprint": model_catalog.get("fingerprint", ""),
            "budget_boundary": budget_boundary,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
