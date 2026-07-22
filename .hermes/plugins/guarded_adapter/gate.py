"""gate.py — Scope enforcement gate for the guarded_adapter plugin.

Checks:
  1. Repository / base / branch has not drifted
  2. action.type ∈ authorized_actions
  3. action.path ∈ plan.write_scope
  4. action.path ∈ authorized_write_scope
  5. External Authorization Binding is valid

Returns: {allowed: bool, error: str|None}
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .runtime_models import ExecutionAuthorizationBinding

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass
class GateRequest:
    """Input to the scope enforcement gate."""
    action_type: str           # e.g., 'write_file', 'commit', 'push', 'create_draft_pr'
    action_path: str           # relative path within the repo, or '' for repo-wide actions
    plan_write_scope: List[str]
    authorized_write_scope: List[str]
    authorization_binding: Optional[Dict[str, Any]] = None


@dataclass
class GateResult:
    """Output from the scope enforcement gate."""
    allowed: bool
    error: Optional[str] = None


def _get_current_repo() -> str:
    """Get the current repository origin (owner/repo)."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
            timeout=10,
        )
        url = result.stdout.strip()
        # Extract owner/repo from git URL
        # Supports: https://github.com/owner/repo.git and git@github.com:owner/repo.git
        if "github.com" in url:
            # HTTPS: https://github.com/owner/repo.git or https://github.com/owner/repo
            path = url.split("github.com/")[-1] if "github.com/" in url else url.split("github.com:")[-1]
            path = path.removesuffix(".git")
            return path
        # Fallback: try git@ format
        if ":" in url and "@" in url:
            path = url.split(":")[-1].removesuffix(".git")
            return path
        return url
    except Exception as e:
        logger.warning("Failed to get current repo: %s", e)
        return ""


def _get_current_base_sha() -> str:
    """Get the current main branch HEAD SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
            timeout=10,
        )
        return result.stdout.strip()
    except Exception as e:
        logger.warning("Failed to get current base SHA: %s", e)
        return ""


def _get_current_branch() -> str:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(_REPO_ROOT),
            timeout=10,
        )
        return result.stdout.strip()
    except Exception as e:
        logger.warning("Failed to get current branch: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Scope validation
# ---------------------------------------------------------------------------

def _check_path_in_scope(action_path: str, scopes: List[str]) -> bool:
    """Check if action_path is covered by any scope entry.

    Exact match or directory prefix match (e.g., scope '.hermes/' covers '.hermes/plugins/...').
    """
    if not scopes:
        return False
    action_path = action_path.replace("\\", "/")
    for scope in scopes:
        scope = scope.replace("\\", "/")
        # Exact match
        if action_path == scope:
            return True
        # Directory prefix: scope ".hermes/plugins/guarded_adapter/" covers
        # any path under it
        if scope.endswith("/") and action_path.startswith(scope):
            return True
        # Parent directory match (e.g., scope ".hermes/" covers ".hermes/plugins/guarded_adapter/...")
        if action_path.startswith(scope.rstrip("/") + "/"):
            return True
    return False


def validate_scope(request: GateRequest) -> GateResult:
    """Validate a gate request against all scope boundaries.

    Args:
        request: GateRequest with action_type, action_path, scopes, and optional binding.

    Returns:
        GateResult with allowed flag and optional error message.
    """
    errors: List[str] = []

    # --- Check 1: Validate authorization binding if provided ---
    if request.authorization_binding:
        try:
            binding = ExecutionAuthorizationBinding.from_dict(request.authorization_binding)
            binding_errors = binding.validate()
            if binding_errors:
                errors.append(f"BINDING_INVALID: {'; '.join(binding_errors)}")
            else:
                # Check repository drift
                current_repo = _get_current_repo()
                if current_repo and binding.repository != current_repo:
                    errors.append(
                        f"BINDING_MISMATCH: repository '{binding.repository}' != "
                        f"current '{current_repo}'"
                    )

                # Check base SHA drift
                current_base = _get_current_base_sha()
                if current_base and binding.base_sha != current_base:
                    errors.append(
                        f"BINDING_MISMATCH: base_sha '{binding.base_sha}' != "
                        f"current '{current_base}'"
                    )

                # Check branch drift
                current_branch = _get_current_branch()
                if current_branch and binding.branch != current_branch:
                    errors.append(
                        f"BINDING_MISMATCH: branch '{binding.branch}' != "
                        f"current '{current_branch}'"
                    )
        except Exception as e:
            errors.append(f"BINDING_INVALID: Failed to parse authorization binding: {e}")
    elif request.action_type in {"write_file", "commit", "push", "create_draft_pr"}:
        # Write actions require a valid binding
        errors.append("BINDING_MISSING: write actions require an authorization binding")

    # --- Check 2: Validate action type is authorized ---
    if request.authorization_binding:
        try:
            binding = ExecutionAuthorizationBinding.from_dict(request.authorization_binding)
            if request.action_type not in binding.authorized_actions:
                errors.append(
                    f"UNAUTHORIZED_ACTION: '{request.action_type}' not in "
                    f"authorized_actions {binding.authorized_actions}"
                )
        except Exception:
            pass  # Already captured above

    # --- Check 3: Check path against plan write_scope ---
    if request.action_path and request.action_type in {"write_file", "commit"}:
        if not _check_path_in_scope(request.action_path, request.plan_write_scope):
            errors.append(
                f"ATTEMPTED_SCOPE_VIOLATION: path '{request.action_path}' "
                f"is not in plan write_scope {request.plan_write_scope}"
            )

    # --- Check 4: Check path against authorized_write_scope ---
    if request.action_path and request.action_type in {"write_file", "commit"}:
        if not _check_path_in_scope(request.action_path, request.authorized_write_scope):
            errors.append(
                f"ATTEMPTED_SCOPE_VIOLATION: path '{request.action_path}' "
                f"is not in authorized_write_scope {request.authorized_write_scope}"
            )

    if errors:
        return GateResult(allowed=False, error="; ".join(errors))

    return GateResult(allowed=True, error=None)
