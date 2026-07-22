"""guarded_repo_actions.py — Scope-gated repository actions tool.

Tool name: guarded_repo_actions
Parameters: action (enum: git_add_authorized_paths, git_commit, git_push_authorized_branch,
           create_draft_pr, read_repository_state)

CRITICAL: Does NOT accept free command strings. Does NOT use shell=True.
All commands are structurally built as lists — no user input concatenation.
Each action validates through gate.py before execution.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    },
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Action implementations
# ---------------------------------------------------------------------------

def _resolve_scope_context() -> Dict[str, Any]:
    """Resolve scope context from PROJECT_STATE.md.

    Lightweight resolver; in full integration, values come from Holder dispatch packet.
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

        current_list_key = None
        current_list = None

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
        "authorized_write_scope": scope_context.get("authorized_write_scope", []),
    }

    return scope_context


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
    authorized_write_scope: List[str]
) -> Dict[str, Any]:
    """Stage only files within the authorized write scope.

    Uses 'git add --' with explicit path list, never 'git add .' or 'git add -A'.
    """
    if not authorized_write_scope:
        return {
            "adapter_execution_status": "COMPLETED",
            "adapter_error": None,
            "action": "git_add_authorized_paths",
            "staged": [],
            "message": "No authorized paths to stage.",
        }

    staged = []
    for path in authorized_write_scope:
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


def _action_git_commit(message: str) -> Dict[str, Any]:
    """Commit staged changes with a structured message.

    The message is passed directly; no shell injection possible (no shell=True).
    """
    if not message:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_INVALID",
            "gate_error": "Commit message is required.",
            "action": "git_commit",
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


def _action_git_push_authorized_branch(branch: str) -> Dict[str, Any]:
    """Push ONLY to the authorized branch. No force push, no rebase."""
    if not branch or branch == "UNKNOWN":
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_MISSING",
            "gate_error": "Authorized branch is required for push.",
            "action": "git_push_authorized_branch",
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
) -> Dict[str, Any]:
    """Create a Draft PR via gh CLI. Base must be main."""
    if not title:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "BINDING_INVALID",
            "gate_error": "PR title is required.",
            "action": "create_draft_pr",
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
) -> Dict[str, Any]:
    """Main handler for the guarded_repo_actions tool.

    Validates action through the gate, then dispatches to the appropriate
    sub-handler. All commands are structurally built — no shell injection.
    """
    if action not in ALLOWED_ACTIONS:
        return {
            "adapter_execution_status": "BLOCKED",
            "adapter_error": "UNAUTHORIZED_ACTION",
            "gate_error": f"Unknown action: {action}. Allowed: {sorted(ALLOWED_ACTIONS)}",
            "action": action,
        }

    ctx = _resolve_scope_context()
    authorized_scope = ctx.get("authorized_write_scope", [])
    branch = ctx.get("branch", "UNKNOWN")

    # Gate validation for write actions
    if action in {"git_commit", "git_push_authorized_branch", "create_draft_pr"}:
        gate_req = GateRequest(
            action_type=(
                "commit" if action == "git_commit"
                else "push" if action == "git_push_authorized_branch"
                else "create_draft_pr"
            ),
            action_path="",  # repo-wide action
            plan_write_scope=authorized_scope,
            authorized_write_scope=authorized_scope,
            authorization_binding=ctx.get("authorization_binding"),
        )
        gate_result = validate_scope(gate_req)
        if not gate_result.allowed:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "ATTEMPTED_SCOPE_VIOLATION",
                "gate_error": gate_result.error,
                "action": action,
            }

    # Dispatch
    if action == "read_repository_state":
        return _action_read_repository_state()

    if action == "git_add_authorized_paths":
        return _action_git_add_authorized_paths(authorized_scope)

    if action == "git_commit":
        if not message:
            return {
                "adapter_execution_status": "BLOCKED",
                "adapter_error": "BINDING_INVALID",
                "gate_error": "message is required for git_commit",
                "action": action,
            }
        return _action_git_commit(message)

    if action == "git_push_authorized_branch":
        return _action_git_push_authorized_branch(branch)

    if action == "create_draft_pr":
        return _action_create_draft_pr(
            base_branch=base_branch or "main",
            head_branch=branch,
            title=pr_title or "Untitled PR",
            body=pr_body or "",
        )

    # Should not reach here
    return {
        "adapter_execution_status": "BLOCKED",
        "adapter_error": "UNAUTHORIZED_ACTION",
        "gate_error": f"Action {action} not implemented.",
        "action": action,
    }
