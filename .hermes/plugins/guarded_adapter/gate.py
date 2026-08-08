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
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .runtime_models import ExecutionAuthorizationBinding

logger = logging.getLogger(__name__)

# Write actions that require drift checks to be conclusive (P1-4: fail-closed
# when a git probe returns empty — an unverifiable probe is treated as drift).
WRITE_ACTION_TYPES = frozenset({"write_file", "commit", "push", "create_draft_pr"})


def _resolve_repo_root() -> Path:
    """Resolve the repository root dynamically (git worktree-safe).

    Path arithmetic (parents[4]) breaks inside git worktrees, where the
    plugin lives one level deeper than in the main checkout — the resolved
    root silently points one level ABOVE the worktree, so writes land
    outside it. Use the canonical git answer instead, falling back to the
    parents[4] heuristic only if git is unavailable.
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
# Path normalization (P0-1: path-traversal hardening)
# ---------------------------------------------------------------------------

# Windows drive-letter absolute path, e.g. "C:/..." or "c:\..."
_DRIVE_ABS_RE = re.compile(r"^[A-Za-z]:[/\\]")


def normalize_repo_path(path: str) -> Optional[str]:
    """Normalize a repo-relative path to canonical POSIX form.

    Returns the normalized path (forward slashes, no "." / duplicate
    separators), or None if the path is unsafe:
      - absolute paths (POSIX "/x", Windows "C:/x", UNC "//host/x")
      - any ".." segment (path traversal), checked BEFORE collapsing so
        that "a/../secret" is rejected rather than silently rewritten

    Fail-closed: anything unusual returns None.
    """
    if not path or not isinstance(path, str):
        return None
    p = path.strip()
    if not p:
        return None
    # Reject absolute paths before separator unification
    if _DRIVE_ABS_RE.match(p):
        return None
    p = p.replace("\\", "/")
    if p.startswith("/"):  # POSIX absolute and UNC ("//host/share")
        return None
    # Reject ANY ".." segment in the raw path (pre-collapse): "a/../b"
    # must be rejected, not silently normalized to "b".
    raw_parts = p.split("/")
    if any(seg == ".." for seg in raw_parts):
        return None
    # Canonicalize residual "." segments and duplicate separators
    norm = os.path.normpath(p).replace("\\", "/")
    if norm in ("", "."):
        return None
    # Defense in depth: normpath output must not retain traversal segments
    if any(seg == ".." for seg in norm.split("/")):
        return None
    return norm


def resolve_repo_target(path: str) -> Optional[Path]:
    """Resolve a repo-relative path to an absolute Path inside the repo.

    Returns None if the path is unsafe (absolute / traversal) or escapes
    the repository root after symlink resolution. Covers the case where a
    symlink inside the repo points outside it.
    """
    norm = normalize_repo_path(path)
    if norm is None:
        return None
    target = (_REPO_ROOT / norm).resolve()
    try:
        target.relative_to(_REPO_ROOT.resolve())
    except ValueError:
        return None
    return target


# ---------------------------------------------------------------------------
# Scope validation
# ---------------------------------------------------------------------------

def _check_path_in_scope(action_path: str, scopes: List[str]) -> bool:
    """Check if action_path is covered by any scope entry.

    Exact match or directory prefix match (e.g., scope '.hermes/' covers '.hermes/plugins/...').
    The action path is normalized first; unsafe paths (absolute / traversal)
    are never in scope.
    """
    if not scopes:
        return False
    norm = normalize_repo_path(action_path)
    if norm is None:
        return False
    for scope in scopes:
        scope = scope.replace("\\", "/")
        if not scope:
            continue
        # Exact match (with or without trailing slash on the scope entry)
        if norm == scope.rstrip("/"):
            return True
        # Directory prefix: scope ".hermes/" covers ".hermes/plugins/..."
        if norm.startswith(scope.rstrip("/") + "/"):
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
                # Check repository drift (fail-closed: an empty probe result on
                # a write action is treated as drift — unverifiable = blocked)
                current_repo = _get_current_repo()
                if current_repo:
                    if binding.repository != current_repo:
                        errors.append(
                            f"BINDING_MISMATCH: repository '{binding.repository}' != "
                            f"current '{current_repo}'"
                        )
                elif request.action_type in WRITE_ACTION_TYPES:
                    errors.append(
                        "BINDING_MISMATCH: repository drift check unavailable "
                        "(git probe returned empty)"
                    )

                # Check base SHA drift
                current_base = _get_current_base_sha()
                if current_base:
                    if binding.base_sha != current_base:
                        errors.append(
                            f"BINDING_MISMATCH: base_sha '{binding.base_sha}' != "
                            f"current '{current_base}'"
                        )
                elif request.action_type in WRITE_ACTION_TYPES:
                    errors.append(
                        "BINDING_MISMATCH: base_sha drift check unavailable "
                        "(git probe returned empty)"
                    )

                # Check branch drift
                current_branch = _get_current_branch()
                if current_branch:
                    if binding.branch != current_branch:
                        errors.append(
                            f"BINDING_MISMATCH: branch '{binding.branch}' != "
                            f"current '{current_branch}'"
                        )
                elif request.action_type in WRITE_ACTION_TYPES:
                    errors.append(
                        "BINDING_MISMATCH: branch drift check unavailable "
                        "(git probe returned empty)"
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
        if normalize_repo_path(request.action_path) is None:
            errors.append(
                f"PATH_TRAVERSAL_REJECTED: path '{request.action_path}' is "
                f"absolute, contains '..' segments, or is otherwise unsafe"
            )
        elif not _check_path_in_scope(request.action_path, request.plan_write_scope):
            errors.append(
                f"ATTEMPTED_SCOPE_VIOLATION: path '{request.action_path}' "
                f"is not in plan write_scope {request.plan_write_scope}"
            )

    # --- Check 4: Check path against authorized_write_scope ---
    if request.action_path and request.action_type in {"write_file", "commit"}:
        if normalize_repo_path(request.action_path) is None:
            # Already reported above; keep a single traversal error.
            pass
        elif not _check_path_in_scope(request.action_path, request.authorized_write_scope):
            errors.append(
                f"ATTEMPTED_SCOPE_VIOLATION: path '{request.action_path}' "
                f"is not in authorized_write_scope {request.authorized_write_scope}"
            )

    if errors:
        return GateResult(allowed=False, error="; ".join(errors))

    return GateResult(allowed=True, error=None)
