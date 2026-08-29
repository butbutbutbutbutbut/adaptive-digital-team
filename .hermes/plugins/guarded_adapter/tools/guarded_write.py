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
import subprocess
from pathlib import Path
from typing import Any, Dict

from ..gate import GateRequest, resolve_repo_target, validate_scope

logger = logging.getLogger(__name__)


def _resolve_repo_root() -> Path:
    """Resolve the repository root dynamically (git worktree-safe).

    Path arithmetic (parents[4]) breaks inside git worktrees. Use the
    canonical git answer instead, falling back to parents[4] only if git
    is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent),
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    return Path(__file__).resolve().parents[4]


_REPO_ROOT = _resolve_repo_root()

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
    """Resolve scope context from CANDIDATE_BINDING.json ONLY (fail-closed).

    No fallback: if the binding is missing, malformed, or fails validation,
    load_binding() raises and the scope context stays EMPTY. The handler then
    returns BLOCKED (PLAN_WRITE_SCOPE_UNAVAILABLE / AUTHORIZED_WRITE_SCOPE_UNAVAILABLE).
    Authorization is NEVER synthesized from PROJECT_STATE.md.
    """
    from ..runtime_models import load_binding

    scope_context: Dict[str, Any] = {
        "plan_write_scope": [],
        "authorized_write_scope": [],
        "authorization_binding": None,
        "task_id": "UNKNOWN",
        "repository": "Kairos-zhi/adaptive-digital-team",
        "branch": "UNKNOWN",
        "base_sha": "UNKNOWN",
    }

    # ------------------------------------------------------------------
    # External Authorization Binding is the ONLY authority source
    # ------------------------------------------------------------------
    try:
        binding = load_binding()
    except Exception as e:
        # Missing / malformed / invalid binding → no scope → BLOCKED downstream.
        # Never degrade to PROJECT_STATE.md synthesis.
        logger.warning("guarded_write: no valid authorization binding; writes BLOCKED: %s", e)
        return scope_context

    # Populate ALL scope fields from the binding dataclass — no YAML parsing.
    scope_context["authorized_write_scope"] = list(binding.authorized_write_scope)
    scope_context["plan_write_scope"] = list(binding.authorized_write_scope)
    scope_context["branch"] = binding.branch
    scope_context["base_sha"] = binding.base_sha
    scope_context["task_id"] = binding.task_id or "UNKNOWN"
    scope_context["repository"] = binding.repository
    scope_context["authorization_binding"] = binding.to_dict()
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

    # Scope passed — resolve the target and verify it stays inside the repo
    # (rejects absolute paths, ".." traversal, and symlink escapes)
    target_path = resolve_repo_target(path)
    if target_path is None:
        logger.warning("guarded_write BLOCKED: path=%s resolves outside repo", path)
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
            "gate_error": (
                f"PATH_TRAVERSAL_REJECTED: path '{path}' is unsafe or "
                f"resolves outside the repository root"
            ),
            "path": path,
            "action_type": "write_file",
        }
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
