"""guarded_repo_actions.py — Scope-gated repository actions tool.

Tool name: guarded_repo_actions
Parameters: action (enum: git_add_authorized_paths, git_commit, git_push_authorized_branch,
           create_draft_pr, read_repository_state)

CRITICAL: Does NOT accept free command strings. Does NOT use shell=True.
All commands are structurally built as lists — no user input concatenation.
Every write action validates ALL affected files against BOTH plan_write_scope
AND authorized_write_scope independently — no action_path="" bypass.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..gate import GateRequest, validate_scope

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]

# ---------------------------------------------------------------------------
# Allowed actions (enum)
# ---------------------------------------------------------------------------
ALLOWED_ACTIONS = {
    "git_add_authorized_paths",
    "git_commit",
    "git_push_authorized_branch",
    "create_draft_pr",
    "read_repository_state",
}

# ---------------------------------------------------------------------------
# Schema for the guarded_repo_actions tool
# ---------------------------------------------------------------------------
GUARDED_REPO_ACTIONS_SCHEMA = {
    "type": "object",
    "required": ["action"],
    "properties": {
        "action": {
            "type": "string",
            "enum": sorted(ALLOWED_ACTIONS),
            "description": (
                "The repo action to perform. "
                "git_add_authorized_paths: stage files within authorized scope. "
                "git_commit: commit staged changes with a structured message. "
                "git_push_authorized_branch: push to the authorized branch. "
                "create_draft_pr: create a draft PR via gh CLI. "
                "read_repository_state: read HEAD, branch, remote status."
            ),
        },
        "message": {
            "type": "string",
            "description": "Commit message (required for git_commit).",
        },
        "pr_title": {
            "type": "string",
            "description": "PR title (required for create_draft_pr).",
        },
        "pr_body": {
            "type": "string",
            "description": "PR body (optional for create_draft_pr).",
        },
        "base_branch": {
            "type": "string",
            "description": "Base branch for PR (default: main).",
        },
        "paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Optional explicit list of paths to stage (for git_add_authorized_paths). "
                "If omitted, all files matching the dual-scope intersection are staged."
            ),
        },
    },
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Scope path matcher (same logic as gate.py:_check_path_in_scope)
# ---------------------------------------------------------------------------

def _check_path_in_scope(action_path: str, scopes: List[str]) -> bool:
    """Check if action_path is covered by any scope entry.

    Exact match or directory prefix match.
    """
    if not scopes:
        return False
    action_path = action_path.replace("\\", "/")
    for scope in scopes:
        scope = scope.replace("\\", "/")
        if action_path == scope:
            return True
        if scope.endswith("/") and action_path.startswith(scope):
            return True
        if action_path.startswith(scope.rstrip("/") + "/"):
            return True
    return False


def _check_files_in_dual_scope(
    files: List[str],
    plan_scope: List[str],
    auth_scope: List[str],
) -> Tuple[bool, Optional[str]]:
    """Check that every file is within BOTH plan_write_scope AND authorized_write_scope.

    Returns (True, None) if all pass, or (False, error_message) on first violation.
    """
    if not plan_scope:
        return False, "PLAN_WRITE_SCOPE_UNAVAILABLE"
    if not auth_scope:
        return False, "AUTHORIZED_WRITE_SCOPE_UNAVAILABLE"

    for f in files:
        if not _check_path_in_scope(f, plan_scope):
            return (
                False,
                f"ATTEMPTED_SCOPE_VIOLATION: path '{f}' "
                f"is not in plan_write_scope {plan_scope}",
            )
        if not _check_path_in_scope(f, auth_scope):
            return (
                False,
                f"ATTEMPTED_SCOPE_VIOLATION: path '{f}' "
                f"is not in authorized_write_scope {auth_scope}",
            )

    return True, None


# ---------------------------------------------------------------------------
# Scope context resolution
# ---------------------------------------------------------------------------

def _resolve_scope_context() -> Dict[str, Any]:
    """Resolve scope context from PROJECT_STATE.md.

    Independently parses plan_write_scope and authorized_write_scope.
    Both are stored separately; neither is copied from the other.
    If either is missing from PROJECT_STATE.md, it stays empty —
    write actions will then be BLOCKED.
    """
    project_state_path = _REPO_ROOT / "PROJECT_STATE.md"
    scope_context: Dict[str, Any] = {
        "plan_write_scope": [],
        "authorized_write_scope": [],
        "authorization_binding": None,
        "task_id": "UNKNOWN",
        "repository": "butbutbutbutbutbut/adaptive-digital-team",
        "branch": "UNKNOWN",
        "base_sha": "UNKNOWN",
    }

    if not project_state_path.exists():
        return scope_context

    try:
        content = project_state_path.read_text(encoding="utf-8")
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
            return scope_context

        current_list_key: Optional[str] = None
        current_list: Optional[List[str]] = None

        for line in yaml_lines:
            stripped = line.rstrip()
            if not stripped:
                # Empty line ends a list
                if current_list_key and current_list is not None:
                    scope_context[current_list_key] = current_list
                    current_list_key = None
                    current_list = None
                continue

            if stripped.lstrip().startswith("- "):
                item = stripped.lstrip()[2:].strip().strip("'").strip('"')
                if current_list_key and current_list is not None:
                    current_list.append(item)
                continue

            if ":" in stripped and not stripped.lstrip().startswith("-"):
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip("'").strip('"')

                if key == "plan_write_scope":
                    scope_context["plan_write_scope"] = current_list = []
                    current_list_key = "plan_write_scope"
                    continue
                if key == "authorized_write_scope":
                    scope_context["authorized_write_scope"] = current_list = []
                    current_list_key = "authorized_write_scope"
                    continue
                if key == "task_id":
                    scope_context["task_id"] = value
                if key == "repository":
                    scope_context["repository"] = value
                if key == "branch":
                    scope_context["branch"] = value
                if key == "starting_base_sha":
                    scope_context["base_sha"] = value
                continue

        if current_list_key and current_list is not None:
            scope_context[current_list_key] = current_list

    except Exception as e:
        logger.warning("Failed to parse PROJECT_STATE.md: %s", e)

    scope_context["authorization_binding"] = {
        "authorization_id": scope_context.get("task_id", "UNKNOWN"),
        "authority_source": "PROJECT_STATE.md",
        "human_role": "HUMAN_HOLDER",
        "repository": scope_context.get("repository", ""),
        "base_sha": scope_context.get("base_sha", ""),
        "branch": scope_context.get("branch", ""),
        "authorized_actions": ["write_file", "commit", "push", "create_draft_pr"],
        "authorized_write_scope": list(scope_context.get("authorized_write_scope", [])),
    }

    return scope_context


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _run_git(args: List[str]) -> Dict[str, Any]:
    """Run a git command safely. No shell, no user input concatenation."""
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=60,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "success": result.returncode == 0,
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }


def _get_staged_files() -> List[str]:
    """Get list of staged (cached) file paths."""
    result = _run_git(["diff", "--cached", "--name-only"])
    if result["success"] and result["stdout"]:
        return [f for f in result["stdout"].split("\n") if f]
    return []


def _get_changed_files_base_head(base_sha: str) -> List[str]:
    """Get list of files changed between base_sha and HEAD."""
    if not base_sha or base_sha == "UNKNOWN":
        # Fallback: use origin/main
        base_ref = "origin/main"
    elif len(base_sha) >= 40:
        base_ref = base_sha
    else:
        base_ref = "origin/main"

    result = _run_git(["diff", "--name-only", f"{base_ref}..HEAD"])
    if result["success"] and result["stdout"]:
        return [f for f in result["stdout"].split("\n") if f]
    return []


def _compute_scope_intersection(
    plan_scope: List[str],
    auth_scope: List[str],
) -> List[str]:
    """Compute the set of paths that are within BOTH scopes.

    For exact-match scopes, this is straightforward.
    For directory-prefix scopes, we enumerate repo files under each scope
    and take the intersection.
    """
    if not plan_scope or not auth_scope:
        return []

    # Find all repo files that match either scope
    plan_files: set = set()
    auth_files: set = set()

    # Walk repo to find files matching scopes
    for scope in plan_scope:
        scope_path = _REPO_ROOT / scope
        if scope_path.is_file():
            plan_files.add(scope)
        elif scope_path.is_dir():
            for f in scope_path.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(_REPO_ROOT)).replace("\\", "/")
                    plan_files.add(rel)
        else:
            # Wildcard / non-existent: treat as literal scope entry
            plan_files.add(scope)

    for scope in auth_scope:
        scope_path = _REPO_ROOT / scope
        if scope_path.is_file():
            auth_files.add(scope)
        elif scope_path.is_dir():
            for f in scope_path.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(_REPO_ROOT)).replace("\\", "/")
                    auth_files.add(rel)
        else:
            auth_files.add(scope)

    # Intersection: only files that match BOTH scopes
    intersection = plan_files & auth_files

    # Also handle directory-scope entries: if both have ".hermes/plugins/guarded_adapter/",
    # all files under it should be included
    for ps in plan_scope:
        for as_ in auth_scope:
            ps_norm = ps.replace("\\", "/")
            as_norm = as_.replace("\\", "/")
            # If one is a parent of the other, walk for files
            if ps_norm.endswith("/") or as_norm.endswith("/"):
                continue  # handled above by rglob

    return sorted(intersection)


# ---------------------------------------------------------------------------
# Action implementations
# ---------------------------------------------------------------------------

def _action_read_repository_state() -> Dict[str, Any]:
    """Read-only: return current repository state."""
    head = _run_git(["rev-parse", "HEAD"])
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    status = _run_git(["status", "--porcelain"])
    remote = _run_git(["remote", "get-url", "origin"])
    base = _run_git(["rev-parse", "origin/main"])

    return {
        "adapter_execution_status": "COMPLETED",
        "adapter_error": None,
        "action": "read_repository_state",
        "head_sha": head["stdout"],
        "branch": branch["stdout"],
        "origin": remote["stdout"],
        "base_sha": base["stdout"],
        "dirty_files": status["stdout"].split("\n") if status["stdout"] else [],
    }


def _action_git_add_authorized_paths(
    plan_scope: List[str],
    auth_scope: List[str],
    explicit_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Stage only files within BOTH plan_write_scope AND authorized_write_scope.

    If explicit_paths is provided, each path is individually validated against
    both scopes and only those passing are staged. Otherwise, all files in the
    scope intersection are staged.

    Never uses 'git add .' or 'git add -A'.
    """
    if not plan_scope:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "PLAN_WRITE_SCOPE_UNAVAILABLE",
            "gate_error": "plan_write_scope is required for git_add_authorized_paths",
            "action": "git_add_authorized_paths",
        }
    if not auth_scope:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "AUTHORIZED_WRITE_SCOPE_UNAVAILABLE",
            "gate_error": "authorized_write_scope is required for git_add_authorized_paths",
            "action": "git_add_authorized_paths",
        }

    if explicit_paths:
        # Validate each requested path against both scopes
        ok, err = _check_files_in_dual_scope(explicit_paths, plan_scope, auth_scope)
        if not ok:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
                "gate_error": err,
                "action": "git_add_authorized_paths",
            }
        paths_to_stage = explicit_paths
    else:
        # Stage all files that match the intersection of both scopes
        paths_to_stage = _compute_scope_intersection(plan_scope, auth_scope)

    if not paths_to_stage:
        return {
            "adapter_execution_status": "COMPLETED",
            "adapter_error": None,
            "action": "git_add_authorized_paths",
            "staged": [],
            "message": "No paths in scope intersection to stage.",
        }

    staged = []
    for path in paths_to_stage:
        full_path = _REPO_ROOT / path
        if full_path.exists():
            result = _run_git(["add", "--", path])
            if result["success"]:
                staged.append(path)
            else:
                logger.warning("git add failed for %s: %s", path, result["stderr"])

    return {
        "adapter_execution_status": "COMPLETED",
        "adapter_error": None,
        "action": "git_add_authorized_paths",
        "staged": staged,
    }


def _action_git_commit(
    message: str,
    plan_scope: List[str],
    auth_scope: List[str],
) -> Dict[str, Any]:
    """Commit staged changes after verifying ALL staged files are within dual scope."""
    if not message:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_INVALID",
            "gate_error": "Commit message is required.",
            "action": "git_commit",
        }

    # Check staged files against dual scope before committing
    staged = _get_staged_files()
    if not staged:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "SCOPE_VIOLATION",
            "gate_error": "No staged files to commit.",
            "action": "git_commit",
        }

    ok, err = _check_files_in_dual_scope(staged, plan_scope, auth_scope)
    if not ok:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
            "gate_error": err,
            "action": "git_commit",
            "staged_files": staged,
        }

    result = _run_git(["commit", "-m", message])
    if result["success"]:
        return {
            "adapter_execution_status": "COMPLETED",
            "adapter_error": None,
            "action": "git_commit",
            "message": message,
            "commit_sha": _run_git(["rev-parse", "HEAD"])["stdout"],
        }
    else:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "SCOPE_VIOLATION",
            "gate_error": result["stderr"],
            "action": "git_commit",
        }


def _action_git_push_authorized_branch(
    branch: str,
    base_sha: str,
    plan_scope: List[str],
    auth_scope: List[str],
) -> Dict[str, Any]:
    """Push to authorized branch after verifying all changed files are within dual scope."""
    if not branch or branch == "UNKNOWN":
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_MISSING",
            "gate_error": "Authorized branch is required for push.",
            "action": "git_push_authorized_branch",
        }

    # Check all changed files between base and HEAD
    changed = _get_changed_files_base_head(base_sha)
    if changed:
        ok, err = _check_files_in_dual_scope(changed, plan_scope, auth_scope)
        if not ok:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
                "gate_error": err,
                "action": "git_push_authorized_branch",
                "changed_files": changed,
            }

    result = _run_git(["push", "-u", "origin", branch])
    if result["success"]:
        return {
            "adapter_execution_status": "COMPLETED",
            "adapter_error": None,
            "action": "git_push_authorized_branch",
            "branch": branch,
        }
    else:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "SCOPE_VIOLATION",
            "gate_error": result["stderr"],
            "action": "git_push_authorized_branch",
        }


def _action_create_draft_pr(
    base_branch: str,
    head_branch: str,
    title: str,
    body: str,
    base_sha: str,
    plan_scope: List[str],
    auth_scope: List[str],
) -> Dict[str, Any]:
    """Create a Draft PR after verifying all branch-changed files are within dual scope."""
    if not title:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_INVALID",
            "gate_error": "PR title is required.",
            "action": "create_draft_pr",
        }

    # Check all changed files between base and HEAD before creating PR
    changed = _get_changed_files_base_head(base_sha)
    if changed:
        ok, err = _check_files_in_dual_scope(changed, plan_scope, auth_scope)
        if not ok:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
                "gate_error": err,
                "action": "create_draft_pr",
                "changed_files": changed,
            }

    # gh CLI: gh pr create --base main --head <branch> --draft --title "..." --body "..."
    cmd = [
        "gh", "pr", "create",
        "--base", base_branch or "main",
        "--head", head_branch,
        "--draft",
        "--title", title,
    ]
    if body:
        cmd.extend(["--body", body])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
            timeout=60,
        )
        if result.returncode == 0:
            return {
                "adapter_execution_status": "COMPLETED",
                "adapter_error": None,
                "action": "create_draft_pr",
                "pr_url": result.stdout.strip(),
                "base": base_branch or "main",
                "head": head_branch,
            }
        else:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "SCOPE_VIOLATION",
                "gate_error": result.stderr.strip(),
                "action": "create_draft_pr",
            }
    except FileNotFoundError:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "CREDENTIAL_LEAK",
            "gate_error": "gh CLI not found. Install GitHub CLI to use create_draft_pr.",
            "action": "create_draft_pr",
        }
    except Exception as e:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "SCOPE_VIOLATION",
            "gate_error": str(e),
            "action": "create_draft_pr",
        }


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def guarded_repo_actions_handler(
    action: str,
    message: Optional[str] = None,
    pr_title: Optional[str] = None,
    pr_body: Optional[str] = None,
    base_branch: Optional[str] = None,
    paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Main handler for the guarded_repo_actions tool.

    Every write action validates ALL affected files against BOTH
    plan_write_scope AND authorized_write_scope independently.
    No action_path="" bypass — actual file lists are checked.
    """
    if action not in ALLOWED_ACTIONS:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "UNAUTHORIZED_ACTION",
            "gate_error": f"Unknown action: {action}. Allowed: {sorted(ALLOWED_ACTIONS)}",
            "action": action,
        }

    ctx = _resolve_scope_context()
    plan_scope: List[str] = ctx.get("plan_write_scope", [])
    auth_scope: List[str] = ctx.get("authorized_write_scope", [])
    branch: str = ctx.get("branch", "UNKNOWN")
    base_sha: str = ctx.get("base_sha", "UNKNOWN")
    binding = ctx.get("authorization_binding")

    # Authorization binding validation for write actions (repo/base/branch/action check)
    if action in {"git_commit", "git_push_authorized_branch", "create_draft_pr"}:
        gate_req = GateRequest(
            action_type=(
                "commit" if action == "git_commit"
                else "push" if action == "git_push_authorized_branch"
                else "create_draft_pr"
            ),
            action_path="",  # binding-only validation; file-level scope is done separately
            plan_write_scope=plan_scope,
            authorized_write_scope=auth_scope,
            authorization_binding=binding,
        )
        gate_result = validate_scope(gate_req)
        if not gate_result.allowed:
            # Distinguish: binding errors vs scope errors
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": (
                    "BINDING_INVALID"
                    if "BINDING" in (gate_result.error or "")
                    else "ATTEMPTED_SCOPE_VIOLATION"
                ),
                "gate_error": gate_result.error,
                "action": action,
            }

    # Dispatch
    if action == "read_repository_state":
        return _action_read_repository_state()

    if action == "git_add_authorized_paths":
        return _action_git_add_authorized_paths(plan_scope, auth_scope, paths)

    if action == "git_commit":
        if not message:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "BINDING_INVALID",
                "gate_error": "message is required for git_commit",
                "action": action,
            }
        return _action_git_commit(message, plan_scope, auth_scope)

    if action == "git_push_authorized_branch":
        return _action_git_push_authorized_branch(branch, base_sha, plan_scope, auth_scope)

    if action == "create_draft_pr":
        return _action_create_draft_pr(
            base_branch=base_branch or "main",
            head_branch=branch,
            title=pr_title or "Untitled PR",
            body=pr_body or "",
            base_sha=base_sha,
            plan_scope=plan_scope,
            auth_scope=auth_scope,
        )

    # Should not reach here
    return {
        "adapter_execution_status": "BLOCKED",
        "adapter_error": "UNAUTHORIZED_ACTION",
        "gate_error": f"Action {action} not implemented.",
        "action": action,
    }
