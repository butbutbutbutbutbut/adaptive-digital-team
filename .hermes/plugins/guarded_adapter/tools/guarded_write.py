"""guarded_write.py — Scope-gated file write tool for the guarded_adapter plugin.

Tool name: guarded_write
Parameters: path (string), content (string)

Before writing, calls gate.validate_scope() to verify:
  - path is within plan.write_scope
  - path is within authorized_write_scope
  - Authorization binding is valid (no repository/base/branch drift)

Returns adapter_execution_status=COMPLETED on success,
or adapter_execution_status=BLOCKED with adapter_error=ATTEMPTED_SCOPE_VIOLATION on failure.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from ..gate import GateRequest, validate_scope

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]

# ---------------------------------------------------------------------------
# Schema for the guarded_write tool (JSON Schema subset)
# ---------------------------------------------------------------------------
GUARDED_WRITE_SCHEMA = {
    "type": "object",
    "required": ["path", "content"],
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative path within the repository to write to."
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file."
        },
    },
    "additionalProperties": False,
}


def _resolve_scope_context() -> Dict[str, Any]:
    """Resolve scope context from CANDIDATE_BINDING.json, falling back to PROJECT_STATE.md.

    Binding-first: consumes ExecutionAuthorizationBinding via load_binding().
    Falls back to PROJECT_STATE.md YAML parsing only when the binding file is missing.
    No YAML/JSON dual interpretation.
    """
    from ..runtime_models import load_binding

    scope_context: Dict[str, Any] = {
        "plan_write_scope": [],
        "authorized_write_scope": [],
        "authorization_binding": None,
        "task_id": "UNKNOWN",
        "repository": "butbutbutbutbutbut/adaptive-digital-team",
        "branch": "UNKNOWN",
        "base_sha": "UNKNOWN",
    }

    # ------------------------------------------------------------------
    # 1. Try the External Authorization Binding first
    # ------------------------------------------------------------------
    binding = load_binding()

    if binding is not None:
        # Populate ALL scope fields from the binding dataclass — no YAML parsing.
        scope_context["authorized_write_scope"] = list(binding.authorized_write_scope)
        scope_context["plan_write_scope"] = list(binding.authorized_write_scope)
        scope_context["branch"] = binding.branch
        scope_context["base_sha"] = binding.base_sha
        scope_context["task_id"] = binding.task_id or "UNKNOWN"
        scope_context["repository"] = binding.repository
        scope_context["authorization_binding"] = binding.to_dict()
        return scope_context

    # ------------------------------------------------------------------
    # 2. Fallback: PROJECT_STATE.md (legacy path — keep existing logic)
    # ------------------------------------------------------------------
    project_state_path = _REPO_ROOT / "PROJECT_STATE.md"

    if not project_state_path.exists():
        logger.warning("PROJECT_STATE.md not found; scope enforcement will be strict")
        return scope_context

    try:
        content = project_state_path.read_text(encoding="utf-8")
        # Extract YAML block from markdown
        in_yaml = False
        yaml_lines = []
        for line in content.split("\n"):
            if line.strip() == "```yaml":
                in_yaml = True
                continue
            if line.strip() == "```" and in_yaml:
                in_yaml = False
                continue
            if in_yaml:
                yaml_lines.append(line)

        if not yaml_lines:
            logger.warning("No YAML block found in PROJECT_STATE.md")
            return scope_context

        # Simple YAML parser (no PyYAML dependency required)
        current_key = None
        current_list = None
        for line in yaml_lines:
            stripped = line.rstrip()
            if not stripped:
                continue

            # List item
            if stripped.lstrip().startswith("- "):
                item = stripped.lstrip()[2:].strip().strip("'").strip('"')
                if current_key and current_list is not None:
                    current_list.append(item)
                continue

            # Key: value
            if ":" in stripped and not stripped.lstrip().startswith("-"):
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip("'").strip('"')

                if key in {"plan_write_scope", "authorized_write_scope"}:
                    scope_context[key] = []
                    current_key = key
                    current_list = scope_context[key]
                    continue

                # Also read top-level task_id / branch / starting_base_sha / repository
                if key == "task_id":
                    scope_context["task_id"] = value
                if key == "repository":
                    scope_context["repository"] = value
                if key == "branch":
                    scope_context["branch"] = value
                if key == "starting_base_sha":
                    scope_context["base_sha"] = value
                if key == "current_gate":
                    scope_context["current_gate"] = value
                continue

            # End of list
            if current_key and current_list is not None and stripped and ":" not in stripped:
                continue

        # Transfer collected lists
        if "authorized_write_scope" in scope_context and isinstance(scope_context["authorized_write_scope"], list):
            pass  # already populated

        # In current PROJECT_STATE.md schema, the single 'authorized_write_scope' field
        # serves as both the plan's write scope and the authorization's write scope.
        # Both must be independently present for dual-scope gate enforcement.
        auth_scope = scope_context.get("authorized_write_scope")
        if auth_scope:
            scope_context["plan_write_scope"] = list(auth_scope)

    except Exception as e:
        logger.warning("Failed to parse PROJECT_STATE.md: %s", e)

    # Build synthetic authorization binding from PROJECT_STATE.md (legacy)
    scope_context["authorization_binding"] = {
        "authorization_id": scope_context.get("task_id", "UNKNOWN"),
        "authority_source": "PROJECT_STATE.md",
        "human_role": "HUMAN_HOLDER",
        "repository": scope_context.get("repository", ""),
        "base_sha": scope_context.get("base_sha", ""),
        "branch": scope_context.get("branch", ""),
        "authorized_actions": ["write_file", "commit", "push", "create_draft_pr"],
        "authorized_write_scope": scope_context.get("authorized_write_scope", []),
    }

    return scope_context


def guarded_write_handler(path: str, content: str) -> Dict[str, Any]:
    """Handler for the guarded_write tool.

    Validates the write scope through the gate, then executes the write.

    Args:
        path: Relative path within the repository to write to.
        content: Content to write to the file.

    Returns:
        Dict with adapter_execution_status, adapter_error, and metadata.
    """
    # Resolve scope context
    ctx = _resolve_scope_context()

    # Build gate request with independent scope checks
    plan_scope = ctx.get("plan_write_scope")
    auth_scope = ctx.get("authorized_write_scope")

    if not plan_scope:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "PLAN_WRITE_SCOPE_UNAVAILABLE",
            "path": path,
            "action_type": "write_file",
        }

    if not auth_scope:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "AUTHORIZED_WRITE_SCOPE_UNAVAILABLE",
            "path": path,
            "action_type": "write_file",
        }

    gate_req = GateRequest(
        action_type="write_file",
        action_path=path,
        plan_write_scope=plan_scope,
        authorized_write_scope=auth_scope,
        authorization_binding=ctx.get("authorization_binding"),
    )

    # Validate through gate
    result = validate_scope(gate_req)

    if not result.allowed:
        logger.warning("guarded_write BLOCKED: path=%s error=%s", path, result.error)
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
            "gate_error": result.error,
            "path": path,
            "action_type": "write_file",
        }

    # Scope passed — execute write
    target_path = _REPO_ROOT / path
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        logger.info("guarded_write COMPLETED: path=%s bytes=%d", path, len(content))
        return {
            "adapter_execution_status": "COMPLETED",
            "adapter_error": None,
            "path": path,
            "bytes_written": len(content),
            "action_type": "write_file",
        }
    except Exception as e:
        logger.error("guarded_write failed to write %s: %s", path, e)
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "SCOPE_VIOLATION",
            "gate_error": f"Write failed: {e}",
            "path": path,
            "action_type": "write_file",
        }
