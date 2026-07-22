#!/usr/bin/env python3
"""ADT Runtime Adapter — Schema Validator.

Validates all three Runtime Adapter schemas against JSON Schema draft 2020-12.
Performs validation ONLY — does NOT generate authorization or execute actions.

Usage:
    python scripts/validate_adapter.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator, validate
    from referencing import Registry, Resource
except ImportError:
    print("ERROR: jsonschema library not installed. Run: pip install jsonschema")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"

SCHEMA_FILES = {
    "adapter-envelope": SCHEMAS_DIR / "adapter-envelope.schema.json",
    "adapter-output": SCHEMAS_DIR / "adapter-output.schema.json",
    "execution-authorization-binding": SCHEMAS_DIR / "execution-authorization-binding.schema.json",
}

# ═══════════════════════════════════════════════════════════
# Sample documents for validation
# ═══════════════════════════════════════════════════════════

VALID_ADAPTER_ENVELOPE = {
    "tool_identity": "hermes/4.2.1",
    "tool_session_id": "sess_abc123",
    "tool_capability_tags": ["git", "file_write", "terminal"],
    "session_principal": "xiaohe",
    "claimed_actor": "xiaohe",
    "credential_tags": ["github_pat"],
    "independence_evidence": {
        "separate_execution_context": True,
        "maker_context_inherited": False,
        "participated_in_implementation": False,
        "independent_fact_read": True,
        "independent_conclusion": True,
    },
}

INVALID_ADAPTER_ENVELOPE_MISSING_REQUIRED = {
    "tool_identity": "hermes/4.2.1",
    # missing tool_session_id, tool_capability_tags, session_principal, credential_tags
}

INVALID_ADAPTER_ENVELOPE_BAD_CAPABILITY = {
    "tool_identity": "hermes/4.2.1",
    "tool_session_id": "sess_abc",
    "tool_capability_tags": ["git", "INVALID_CAPABILITY"],
    "session_principal": "xiaohe",
    "credential_tags": [],
}

VALID_EXECUTION_AUTHORIZATION_BINDING = {
    "authorization_id": "ADT-RUNTIME-ADAPTER-CONTRACT-20260723-001",
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

INVALID_AUTH_BINDING_FORBIDDEN_ACTION = {
    "authorization_id": "ADT-BAD-001",
    "authority_source": "test",
    "human_role": "HUMAN_HOLDER",
    "repository": "owner/repo",
    "base_sha": "1f53b68ef9f0b5a9053d0a96d114d229942ff2d8",
    "branch": "feature/test",
    "authorized_actions": ["merge"],  # merge is DEFAULT FORBIDDEN
    "authorized_write_scope": [],
}

INVALID_AUTH_BINDING_MISSING_FIELDS = {
    "authorization_id": "ADT-BAD-002",
    # missing many required fields
}

VALID_ADAPTER_OUTPUT = {
    "governance_plan": {
        "route": "CANDIDATE_IMPLEMENTATION",
        "risk": "HIGH",
        "task_type": "REPOSITORY_CANDIDATE",
        "facts_status": "REQUIRES_VERIFICATION",
        "control_packet_status": "CANDIDATE",
        "write_scope": ["protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md"],
        "steps": [
            {
                "step_id": "STEP-001",
                "objective": "Verify repository facts",
                "dependencies": [],
                "required_facts": ["repository"],
                "authorized_write_scope": [],
                "executor_role": "TASK_HOLDER",
                "checker_required": True,
                "pass_conditions": ["Facts verified"],
                "fail_closed_action": "HARD_STOP",
                "next_gate": "FACT_VERIFICATION_GATE",
            }
        ],
        "checker_required": True,
        "human_authorization_required": True,
        "write_actions_permitted": True,
    },
    "adapter_error": None,
    "route": "CANDIDATE_IMPLEMENTATION",
}

INVALID_ADAPTER_OUTPUT_MISSING_ROUTE = {
    "governance_plan": {
        "route": "DIRECT_LOCAL_EXECUTION",
        "risk": "LOW",
        "task_type": "PROMPT_LOCAL",
        "facts_status": "VERIFIED",
        "control_packet_status": "CANDIDATE",
        "write_scope": [],
        "steps": [],
        "checker_required": False,
        "human_authorization_required": False,
        "write_actions_permitted": False,
    },
    "adapter_error": None,
    # missing "route"
}

# ═══════════════════════════════════════════════════════════
# Validation functions
# ═══════════════════════════════════════════════════════════

def load_json(path: Path) -> dict:
    """Load a JSON file, returning the parsed dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema_against_metaschema(schema: dict, name: str) -> bool:
    """Validate that a schema is valid JSON Schema draft 2020-12."""
    try:
        Draft202012Validator.check_schema(schema)
        print(f"  ✓ {name}: valid JSON Schema draft 2020-12")
        return True
    except jsonschema.exceptions.SchemaError as e:
        print(f"  ✗ {name}: INVALID schema — {e}")
        return False


def validate_document(schema: dict, document: dict, name: str, label: str,
                     registry: Registry | None = None) -> bool:
    """Validate a document against a schema."""
    try:
        if registry:
            validator = Draft202012Validator(schema, registry=registry)
            validator.validate(document)
        else:
            validate(instance=document, schema=schema)
        print(f"  ✓ {label}: valid")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"  ✓ {label}: correctly rejected — {e.message}")
        return True  # expected rejection
    except Exception as e:
        print(f"  ✗ {label}: unexpected error — {e}")
        return False


def validate_document_should_pass(schema: dict, document: dict, label: str,
                                  registry: Registry | None = None) -> bool:
    """Validate a document that SHOULD pass."""
    try:
        if registry:
            validator = Draft202012Validator(schema, registry=registry)
            validator.validate(document)
        else:
            validate(instance=document, schema=schema)
        print(f"  ✓ {label}: valid (expected)")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"  ✗ {label}: REJECTED unexpectedly — {e.message}")
        return False


# ═══════════════════════════════════════════════════════════
# Additional structural checks
# ═══════════════════════════════════════════════════════════

def check_adapter_output_uses_ref() -> bool:
    """Verify adapter-output.schema.json uses $ref for governance_plan."""
    schema = load_json(SCHEMA_FILES["adapter-output"])
    gov_plan_prop = schema.get("properties", {}).get("governance_plan", {})
    has_ref = "$ref" in gov_plan_prop
    if has_ref:
        ref_target = gov_plan_prop["$ref"]
        assert_in_ref = "governance-plan.schema.json" in ref_target
        if assert_in_ref:
            print(f"  ✓ adapter-output uses $ref for governance_plan → {ref_target}")
            return True
        else:
            print(f"  ✗ adapter-output $ref does not point to governance-plan: {ref_target}")
            return False
    else:
        print("  ✗ adapter-output does NOT use $ref for governance_plan — duplicate definition prohibited")
        return False


def check_auth_binding_no_forbidden_actions() -> bool:
    """Verify auth binding schema does not permit default-forbidden actions."""
    schema = load_json(SCHEMA_FILES["execution-authorization-binding"])
    actions_prop = (
        schema.get("properties", {})
        .get("authorized_actions", {})
        .get("items", {})
        .get("enum", [])
    )
    forbidden = {"ready", "merge", "close_pr", "delete_branch"}
    found_forbidden = set(actions_prop) & forbidden
    if found_forbidden:
        print(f"  ✗ authorized_actions enum contains forbidden actions: {found_forbidden}")
        return False
    else:
        print(f"  ✓ authorized_actions enum excludes default-forbidden actions (ready, merge, close_pr, delete_branch)")
        return True


def check_independence_evidence_has_five_fields() -> bool:
    """Verify independence_evidence requires exactly 5 fields."""
    schema = load_json(SCHEMA_FILES["adapter-envelope"])
    indep = schema.get("properties", {}).get("independence_evidence", {})
    required = indep.get("required", [])
    if len(required) == 5:
        print(f"  ✓ independence_evidence has exactly 5 required fields: {required}")
        return True
    else:
        print(f"  ✗ independence_evidence has {len(required)} required fields (expected 5): {required}")
        return False


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main() -> int:
    print("ADT Runtime Adapter — Schema Validator")
    print("=" * 50)

    all_pass = True

    # ── Phase 1: Validate schemas against meta-schema ──
    print("\n[Phase 1] Schema meta-validation (JSON Schema draft 2020-12):")
    schemas = {}
    for name, path in SCHEMA_FILES.items():
        if not path.exists():
            print(f"  ✗ {name}: FILE NOT FOUND at {path}")
            all_pass = False
            continue
        schema = load_json(path)
        schemas[name] = schema
        if not validate_schema_against_metaschema(schema, name):
            all_pass = False

    if not all_pass:
        print("\nFAILED: Schema meta-validation failed.")
        return 1

    # ── Phase 2: Structural checks ──
    print("\n[Phase 2] Structural integrity checks:")
    if not check_adapter_output_uses_ref():
        all_pass = False
    if not check_auth_binding_no_forbidden_actions():
        all_pass = False
    if not check_independence_evidence_has_five_fields():
        all_pass = False

    # ── Phase 3: Document validation ──
    print("\n[Phase 3] Document validation:")

    # Build a registry for $ref resolution (governance-plan is referenced by adapter-output)
    gp_schema = load_json(SCHEMAS_DIR / "governance-plan.schema.json")
    gp_id = gp_schema.get("$id", "")
    registry = Registry().with_resource(gp_id, Resource.from_contents(gp_schema))

    # Adapter Envelope
    print("\n  Adapter Envelope:")
    env_schema = schemas["adapter-envelope"]
    if not validate_document_should_pass(env_schema, VALID_ADAPTER_ENVELOPE, "valid envelope"):
        all_pass = False
    if not validate_document(env_schema, INVALID_ADAPTER_ENVELOPE_MISSING_REQUIRED,
                             "missing required fields", "invalid envelope (missing required)"):
        all_pass = False
    if not validate_document(env_schema, INVALID_ADAPTER_ENVELOPE_BAD_CAPABILITY,
                             "bad capability tag", "invalid envelope (bad capability)"):
        all_pass = False

    # Authorization Binding
    print("\n  Execution Authorization Binding:")
    auth_schema = schemas["execution-authorization-binding"]
    if not validate_document_should_pass(auth_schema, VALID_EXECUTION_AUTHORIZATION_BINDING,
                                         "valid binding"):
        all_pass = False
    if not validate_document(auth_schema, INVALID_AUTH_BINDING_FORBIDDEN_ACTION,
                             "forbidden action", "invalid binding (forbidden action)"):
        all_pass = False
    if not validate_document(auth_schema, INVALID_AUTH_BINDING_MISSING_FIELDS,
                             "missing fields", "invalid binding (missing fields)"):
        all_pass = False

    # Adapter Output
    print("\n  Adapter Output:")
    out_schema = schemas["adapter-output"]
    if not validate_document_should_pass(out_schema, VALID_ADAPTER_OUTPUT, "valid output",
                                         registry=registry):
        all_pass = False
    if not validate_document(out_schema, INVALID_ADAPTER_OUTPUT_MISSING_ROUTE,
                             "missing route", "invalid output (missing route)",
                             registry=registry):
        all_pass = False

    # ── Result ──
    print("\n" + "=" * 50)
    if all_pass:
        print("ALL VALIDATIONS PASSED")
        return 0
    else:
        print("SOME VALIDATIONS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
