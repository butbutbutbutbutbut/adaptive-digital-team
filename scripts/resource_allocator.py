#!/usr/bin/env python3
"""ADT Resource Allocator — Deterministic model and resource allocation.

Consumes a GovernancePlan, a pre-resolved frozen model catalog snapshot,
and a Human-authorized budget boundary. Produces a deterministic
ResourcePlan consumed by the Hermes Runtime Adapter.

Rules (deterministic, pure function):
  LOW        → economy tier, no checker
  MODERATE   → standard tier, conditional checker
  HIGH       → strong tier, mandatory checker
  CRITICAL   → strongest tier, mandatory checker (typically blocked upstream)
  Budget exceeded → BLOCKED
  Model unavailable → BLOCKED
  Same inputs → same outputs

Usage:
    from scripts.resource_allocator import allocate
    plan = allocate(governance_plan, model_catalog, budget_boundary)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# ═══════════════════════════════════════════════════════════
# Frozen allocation tables
# ═══════════════════════════════════════════════════════════

# Risk → model tier
TIER_MAP: dict[str, str] = {
    "LOW": "economy",
    "MODERATE": "standard",
    "HIGH": "strong",
    "CRITICAL": "strong",
}

# Tier → APPROXIMATE token budget
BUDGET_MAP: dict[str, int] = {
    "economy": 8000,
    "standard": 32000,
    "strong": 128000,
}

# Tier → reasoning effort
REASONING_MAP: dict[str, str] = {
    "economy": "minimal",
    "standard": "medium",
    "strong": "high",
}

# Tier → default max_iterations
ITERATIONS_MAP: dict[str, int] = {
    "economy": 20,
    "standard": 40,
    "strong": 50,
}

# Risk → max_repair_attempts
REPAIR_MAP: dict[str, int] = {
    "LOW": 0,
    "MODERATE": 2,
    "HIGH": 2,
    "CRITICAL": 0,
}

# Valid risk values
VALID_RISKS = {"LOW", "MODERATE", "HIGH", "CRITICAL"}

# Valid tiers
VALID_TIERS = {"economy", "standard", "strong"}

# ═══════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════

def _validate_governance_plan(plan: dict[str, Any]) -> str | None:
    """Validate that the GovernancePlan has required fields. Returns error or None."""
    if not isinstance(plan, dict):
        return "GovernancePlan must be a dict"
    risk = plan.get("risk", "")
    if risk not in VALID_RISKS:
        return f"Invalid or missing risk: {risk!r}"
    return None


def _validate_model_catalog(catalog: dict[str, Any]) -> str | None:
    """Validate the model catalog snapshot. Returns error or None."""
    if not isinstance(catalog, dict):
        return "Model catalog must be a dict"

    if "fingerprint" not in catalog:
        return "Model catalog missing fingerprint — must be a pre-resolved frozen snapshot"

    providers = catalog.get("providers", {})
    if not isinstance(providers, dict) or len(providers) == 0:
        return "Model catalog has no providers"

    defaults = catalog.get("defaults", {})
    for tier in VALID_TIERS:
        if tier not in defaults:
            return f"Model catalog defaults missing tier: {tier}"
        d = defaults[tier]
        if not isinstance(d, dict):
            return f"Invalid default for tier {tier}"
        provider = d.get("provider", "")
        model = d.get("model", "")
        if not provider or not model:
            return f"Incomplete default for tier {tier}"
        # Verify the default model actually exists
        if provider not in providers:
            return f"Default provider {provider!r} (tier={tier}) not in catalog providers"
        if model not in providers[provider].get("models", {}):
            return f"Default model {model!r} (provider={provider}, tier={tier}) not in catalog"

    return None


def _validate_budget_boundary(boundary: int) -> str | None:
    """Validate budget boundary. Returns error or None."""
    if not isinstance(boundary, int) or boundary < 0:
        return f"Invalid budget boundary: {boundary!r}"
    return None


# ═══════════════════════════════════════════════════════════
# Model selection
# ═══════════════════════════════════════════════════════════

def _select_model(
    catalog: dict[str, Any],
    tier: str,
    preferred_provider: str | None = None,
    preferred_model: str | None = None,
) -> dict[str, str] | None:
    """Select a model from the catalog at the given tier.

    Uses defaults from catalog, optionally overridden by explicit preferences.
    Returns {"provider": ..., "model": ...} or None if no model found at tier.
    """
    defaults = catalog.get("defaults", {})
    providers = catalog.get("providers", {})

    # Determine provider and model
    if preferred_provider and preferred_model:
        provider = preferred_provider
        model = preferred_model
    else:
        tier_default = defaults.get(tier, {})
        provider = tier_default.get("provider", "")
        model = tier_default.get("model", "")

    if not provider or not model:
        return None

    # Verify provider exists
    provider_models = providers.get(provider, {}).get("models", {})
    if model not in provider_models:
        return None

    model_info = provider_models[model]

    # Verify tier matches
    if model_info.get("tier") != tier:
        return None

    return {"provider": provider, "model": model}


def _build_agent_config(
    catalog: dict[str, Any],
    tier: str,
    role: str,
) -> dict[str, Any] | None:
    """Build a complete agent config (provider, model, reasoning_effort, max_iterations)."""
    selected = _select_model(catalog, tier)
    if selected is None:
        return None

    provider = selected["provider"]
    model = selected["model"]

    # Get reasoning effort — pick best supported that matches tier
    model_info = catalog["providers"][provider]["models"][model]
    supported_efforts = set(model_info.get("reasoning_effort_support", []))
    desired_effort = REASONING_MAP.get(tier, "medium")

    # Use desired effort if supported, otherwise fall back to the closest supported
    if desired_effort in supported_efforts:
        reasoning_effort = desired_effort
    else:
        # Fall back: pick the highest supported effort
        effort_order = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"]
        supported_ordered = [e for e in effort_order if e in supported_efforts]
        reasoning_effort = supported_ordered[-1] if supported_ordered else "minimal"

    max_iterations = ITERATIONS_MAP.get(tier, 40)

    return {
        "provider": provider,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "max_iterations": max_iterations,
    }


# ═══════════════════════════════════════════════════════════
# Main allocator
# ═══════════════════════════════════════════════════════════

def allocate(
    governance_plan: dict[str, Any],
    model_catalog: dict[str, Any],
    budget_boundary: int,
) -> dict[str, Any]:
    """Deterministic resource allocation.

    Args:
        governance_plan: GovernancePlan from route_task.py (dict form).
        model_catalog: Pre-resolved, frozen model catalog snapshot with
            fingerprint. Must NOT be fetched live during allocation.
        budget_boundary: Human-authorized maximum token budget (integer).

    Returns:
        dict: ResourcePlan conforming to resource-plan.schema.json.
    """
    # ── Validate inputs ──────────────────────────────────
    err = _validate_governance_plan(governance_plan)
    if err:
        return _blocked(f"Invalid governance plan: {err}")

    err = _validate_model_catalog(model_catalog)
    if err:
        return _blocked(f"Invalid model catalog: {err}")

    err = _validate_budget_boundary(budget_boundary)
    if err:
        return _blocked(f"Invalid budget boundary: {err}")

    # ── Extract plan fields ──────────────────────────────
    risk = governance_plan["risk"]
    checker_required = bool(governance_plan.get("checker_required", False))
    write_scope = governance_plan.get("write_scope", [])
    route = governance_plan.get("route", "")

    # ── Determine tier ───────────────────────────────────
    tier = TIER_MAP.get(risk, "standard")

    # ── Select maker model ───────────────────────────────
    maker = _build_agent_config(model_catalog, tier, "maker")
    if maker is None:
        return _blocked(
            f"No model available at tier {tier!r} for risk={risk}. "
            f"Catalog fingerprint: {model_catalog.get('fingerprint', 'unknown')}"
        )

    # ── Determine checker ────────────────────────────────
    checker = None
    context_strategy = "shared"

    if checker_required:
        # Per amendment 4: checker independence = separate context + role,
        # not necessarily different model. Use same tier.
        checker = _build_agent_config(model_catalog, tier, "checker")
        if checker is None:
            return _blocked(
                f"Checker required but no model available at tier {tier!r}. "
                f"Catalog fingerprint: {model_catalog.get('fingerprint', 'unknown')}"
            )
        context_strategy = "isolated"

    # ── Calculate budget ─────────────────────────────────
    token_budget = BUDGET_MAP.get(tier, 32000)

    if token_budget > budget_boundary:
        return _blocked(
            f"Token budget {token_budget} exceeds Human boundary {budget_boundary}. "
            f"Risk={risk}, tier={tier}. Allocation blocked — will not silently overspend."
        )

    # ── Determine other fields ───────────────────────────
    max_repair_attempts = REPAIR_MAP.get(risk, 0)
    parallelism = 1  # Default serial; checker runs after maker

    # ── Build ResourcePlan ───────────────────────────────
    return {
        "plan_status": "ALLOCATED",
        "maker": maker,
        "checker": checker,
        "budget": {
            "token_budget": token_budget,
            "status": "WITHIN_BUDGET",
            "accuracy": "APPROXIMATE",
        },
        "max_repair_attempts": max_repair_attempts,
        "context_strategy": context_strategy,
        "parallelism": parallelism,
    }


def _blocked(reason: str) -> dict[str, Any]:
    """Produce a BLOCKED ResourcePlan."""
    return {
        "plan_status": "BLOCKED",
        "block_reason": reason,
        "maker": {
            "provider": "",
            "model": "",
            "reasoning_effort": "minimal",
            "max_iterations": 0,
        },
        "checker": None,
        "budget": {
            "token_budget": 0,
            "status": "BLOCKED_BUDGET_EXCEEDED",
            "accuracy": "APPROXIMATE",
        },
        "max_repair_attempts": 0,
        "context_strategy": "shared",
        "parallelism": 0,
    }


# ═══════════════════════════════════════════════════════════
# Determinism utility
# ═══════════════════════════════════════════════════════════

def compute_input_fingerprint(
    governance_plan: dict[str, Any],
    model_catalog: dict[str, Any],
    budget_boundary: int,
) -> str:
    """Compute SHA-256 fingerprint of the allocation inputs.

    Used to verify determinism: same fingerprint → same ResourcePlan.
    """
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
