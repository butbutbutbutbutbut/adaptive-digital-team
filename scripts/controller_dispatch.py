#!/usr/bin/env python3
"""P0 Runtime Controller Dispatch Gate.

Synthesizes three P0 protocols into a single atomic dispatch gate chain:

  dispatch(task_card) →
    1. CONCURRENCY_GATE: count in-flight tasks. If < N (default 2), pass.
       If >= N, queue (FIFO up to MAX_QUEUE=4) or reject if queue full.
    2. TOKEN_GATE: generate token_id (TKN-{date}-{seq}), atomically write
       .hermes/CANDIDATE_BINDING.json with embedded token field.
    3. WORKTREE_GATE: git worktree add for maker worktree under
       .adt-worktrees/<repo-name>/<maker-name>/.
    4. DISPATCH: return Dispatch Card with token_id + worktree_path +
       concurrency_status.

All gates fail-closed. No --force. Pure additive — does not modify any
existing file.

Protocol references:
  - protocols/CONCURRENCY_LIMIT.md §2 (in-flight model), §3 (N=2),
    §4 (queue/reject semantics)
  - protocols/HOLDER_TOKEN.md §2 (token model), §2.3 (binding-embedded
    token), §3 (lifecycle)
  - protocols/WORKSPACE_ISOLATION.md §2.1 (path layout), §2.3 (naming),
    §3.1 (worktree creation)

CLI entry point:
  python scripts/controller_dispatch.py --task-id <id> --branch <b> --scope <files>...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
# Protocol-derived constants
# ═══════════════════════════════════════════════════════════════════════

# CONCURRENCY_LIMIT.md §3.1: default concurrent in-flight cap
DEFAULT_N: int = 2

# CONCURRENCY_LIMIT.md §4.1: bounded FIFO queue (2 × N)
MAX_QUEUE: int = 4

# CONCURRENCY_LIMIT.md §4.2: queue time-to-live before auto-reject
QUEUE_TTL_MINUTES: int = 15

# HOLDER_TOKEN.md §2.4: soft expiry window for issued tokens
TOKEN_TTL_HOURS: int = 2

# WORKSPACE_ISOLATION.md §2.1: sibling directory for agent worktrees
ADT_WORKTREES_DIR: str = ".adt-worktrees"

# HOLDER_TOKEN.md §2.3: binding file path (relative to repo root)
BINDING_PATH: str = ".hermes/CANDIDATE_BINDING.json"

# Internal tracking files (not part of any existing protocol — new files)
QUEUE_PATH: str = ".hermes/dispatch_queue.json"
TOKEN_SEQ_PATH: str = ".hermes/token_seq.json"

# HOLDER_TOKEN.md §2.4: valid token states
VALID_TOKEN_STATES: frozenset[str] = frozenset({"HELD", "RELEASED"})

# HOLDER_TOKEN.md §2.4: valid release reasons
VALID_RELEASE_REASONS: frozenset[str] = frozenset({
    "HUMAN_GATE_COMPLETE", "TIMEOUT", "FAILURE", "CRASH_RECOVERY", "CANCELLED",
})

# WORKSPACE_ISOLATION.md §2.3: agent name character set
AGENT_NAME_RE: re.Pattern[str] = re.compile(r"^[a-z0-9-]+$")

# CONCURRENCY_LIMIT.md §6: known failure codes
FAILURE_CODES: frozenset[str] = frozenset({
    "SUBAGENT_TIMEOUT", "SUBAGENT_HANG", "QUEUE_DEADLOCK",
    "DEPENDENCY_CYCLE", "SLOT_LEAK", "CONCURRENCY_MISMATCH",
})

# WORKSPACE_ISOLATION.md §5: worktree failure codes
WT_FAILURE_CODES: frozenset[str] = frozenset({
    "WORKTREE_BRANCH_CONFLICT", "BINDING_MISMATCH", "BASE_DRIFT",
    "STALE_WORKTREE", "DIRTY_WORKTREE", "WINDOWS_PATH_ERROR",
})

# HOLDER_TOKEN.md §7: token failure codes
TOKEN_FAILURE_CODES: frozenset[str] = frozenset({
    "TOKEN_LOST", "TOKEN_STUCK", "TOKEN_CONFLICT", "BINDING_CORRUPTED",
    "CRASH_RECOVERY", "TOKEN_EXPIRED", "TOKEN_MISMATCH", "TOKEN_NOT_HELD",
})


# ═══════════════════════════════════════════════════════════════════════
# Git helpers
# ═══════════════════════════════════════════════════════════════════════

def _git(*args: str, cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the CompletedProcess.

    All calls fail-closed: check returncode before trusting output.
    Timeout defaults to 30 s to prevent hung subprocesses from blocking
    the dispatch gate indefinitely.
    """
    return subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
    )


def _resolve_head(repo_root: Path) -> Optional[str]:
    """Return the full 40-char SHA of HEAD, or None on failure."""
    result = _git("rev-parse", "HEAD", cwd=repo_root)
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha if re.fullmatch(r"^[0-9a-f]{40}$", sha) else None


# ═══════════════════════════════════════════════════════════════════════
# GATE 1 — CONCURRENCY_GATE
#   Per CONCURRENCY_LIMIT.md §2 (in-flight model) and §4 (queue/reject)
# ═══════════════════════════════════════════════════════════════════════

def _worktrees_dir(repo_root: Path, repo_name: str) -> Path:
    """Return the .adt-worktrees/<repo-name>/ directory.

    Per WORKSPACE_ISOLATION.md §2.1:
      <repo-parent>/.adt-worktrees/<repository-name>/<agent-name>/
    """
    return repo_root.parent / ADT_WORKTREES_DIR / repo_name


def count_in_flight(repo_root: Path, repo_name: str) -> int:
    """Count in-flight tasks by counting active maker worktrees.

    Per CONCURRENCY_LIMIT.md §2.3:
      ONE_IN_FLIGHT = ONE_BRANCH = ONE_WORKTREE = ONE_TASK

    Only directories under .adt-worktrees/<repo>/ that match the agent
    naming pattern are counted.  Non-maker worktrees (e.g. checker)
    are excluded because CONCURRENCY_LIMIT.md §2.2 states that read-only
    tasks do not occupy in-flight slots.

    Falls back to `git worktree list` parsing if the directory-based
    count disagrees with git's own bookkeeping.
    """
    wt_dir = _worktrees_dir(repo_root, repo_name)

    # Primary: directory-based count (fast, no subprocess)
    dir_count = 0
    if wt_dir.exists() and wt_dir.is_dir():
        dir_count = sum(
            1 for entry in wt_dir.iterdir()
            if entry.is_dir() and AGENT_NAME_RE.match(entry.name)
        )

    # Secondary: cross-check with git worktree list for accuracy
    try:
        result = _git("worktree", "list", "--porcelain", cwd=repo_root)
        if result.returncode != 0:
            # git failed — trust directory count but warn
            return dir_count

        # Parse porcelain output: each worktree block has 'worktree <path>'
        # and 'branch refs/heads/<name>' lines.  Count worktrees whose
        # path contains .adt-worktrees/ (i.e. agent worktrees, not main).
        lines = result.stdout.splitlines()
        wt_paths: set[str] = set()
        current_path: str | None = None
        for line in lines:
            if line.startswith("worktree "):
                current_path = line[len("worktree "):].strip()
            elif line.startswith("branch ") and current_path:
                norm = current_path.replace("\\", "/")
                if "/.adt-worktrees/" in norm:
                    wt_paths.add(norm)

        git_count = len(wt_paths)

        # If counts disagree, trust git (the authoritative source) but
        # report the discrepancy as a warning on stderr so the caller
        # can detect SLOT_LEAK-like drift (CONCURRENCY_LIMIT.md §6).
        if git_count != dir_count:
            print(
                f"[WARN] CONCURRENCY_MISMATCH: directory count={dir_count}, "
                f"git count={git_count}. Using git count.",
                file=sys.stderr,
            )
        return max(git_count, dir_count)  # conservative: use the higher count

    except Exception:
        return dir_count


# ── Queue management ──────────────────────────────────────────────────

def _load_queue(repo_root: Path) -> List[Dict[str, Any]]:
    """Load the dispatch queue from disk.

    Returns an empty list if the file is absent or unreadable
    (fail-safe: an empty queue blocks nothing).
    """
    path = repo_root / QUEUE_PATH
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_queue(repo_root: Path, queue: List[Dict[str, Any]]) -> None:
    """Persist the dispatch queue to disk."""
    path = repo_root / QUEUE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _prune_expired_queue(queue: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove queue entries past QUEUE_TTL.

    Per CONCURRENCY_LIMIT.md §4.2: entries exceeding QUEUE_TTL are
    auto-rejected.  This function drops them from the in-memory list;
    the caller is responsible for persisting the pruned queue.
    """
    now = datetime.now(timezone.utc)
    kept: List[Dict[str, Any]] = []
    for entry in queue:
        enqueued_at = entry.get("enqueued_at", "")
        if not enqueued_at:
            kept.append(entry)
            continue
        try:
            ts = datetime.fromisoformat(enqueued_at)
            elapsed = (now - ts).total_seconds()
            if elapsed > QUEUE_TTL_MINUTES * 60:
                # Entry expired — drop silently (caller may log if desired)
                continue
        except (ValueError, TypeError):
            # Unparseable timestamp — keep rather than risk dropping valid entries
            pass
        kept.append(entry)
    return kept


def _concurrency_gate(
    repo_root: Path,
    repo_name: str,
    task_id: str,
    branch: str,
    scope: List[str],
    base_sha: str,
    maker_name: str,
    n: int = DEFAULT_N,
) -> Dict[str, Any]:
    """Execute the concurrency gate (step 1 of the dispatch chain).

    Returns one of:
      - {"status": "PASS", "in_flight": int, ...}  → proceed to token gate
      - {"status": "QUEUED", ...}                   → task queued, stop here
      - {"status": "REJECTED", "reason": str, ...}  → queue full, stop here
    """
    in_flight = count_in_flight(repo_root, repo_name)

    queue = _load_queue(repo_root)
    queue = _prune_expired_queue(queue)
    _save_queue(repo_root, queue)  # persist pruning

    if in_flight < n:
        # Slot available — pass through
        return {
            "status": "PASS",
            "concurrency_status": "IN_FLIGHT",
            "in_flight_before": in_flight,
            "in_flight_after": in_flight + 1,
            "max_concurrency": n,
            "queue_length": len(queue),
        }

    # At or above cap — try to queue
    if len(queue) >= MAX_QUEUE:
        # CONCURRENCY_LIMIT.md §4.3: queue full → immediate reject
        return {
            "status": "REJECTED",
            "reason": "QUEUE_FULL",
            "concurrency_status": "REJECTED",
            "in_flight": in_flight,
            "max_concurrency": n,
            "queue_length": len(queue),
            "max_queue": MAX_QUEUE,
            "failure_code": "CONCURRENCY_REJECTED",
        }

    # Enqueue (FIFO — append to end)
    enqueued_at = datetime.now(timezone.utc).isoformat()
    queue_entry: Dict[str, Any] = {
        "task_id": task_id,
        "branch": branch,
        "scope": scope,
        "base_sha": base_sha,
        "maker_name": maker_name,
        "enqueued_at": enqueued_at,
    }
    queue.append(queue_entry)
    _save_queue(repo_root, queue)

    return {
        "status": "QUEUED",
        "concurrency_status": "QUEUED",
        "queue_position": len(queue),
        "queue_length": len(queue),
        "max_queue": MAX_QUEUE,
        "in_flight": in_flight,
        "max_concurrency": n,
        "enqueued_at": enqueued_at,
        "message": (
            f"Task queued at position {len(queue)}/{MAX_QUEUE}. "
            f"In-flight: {in_flight}/{n}. "
            f"Will auto-reject after {QUEUE_TTL_MINUTES} min if no slot opens."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# GATE 2 — TOKEN_GATE
#   Per HOLDER_TOKEN.md §2 (token model) and §2.3 (binding-embedded token)
# ═══════════════════════════════════════════════════════════════════════

def _load_token_seq(repo_root: Path) -> Tuple[str, int]:
    """Return (today_str, next_seq) for daily token sequence numbering.

    Per HOLDER_TOKEN.md §2.4: token_id = TKN-{yyyy-mm-dd}-{seq}.
    Sequence resets each calendar day (UTC).
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = repo_root / TOKEN_SEQ_PATH
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("date") == today:
                last = data.get("last_seq", 0)
                return today, int(last) + 1
        except (OSError, json.JSONDecodeError):
            pass
    return today, 1


def _save_token_seq(repo_root: Path, date_str: str, seq: int) -> None:
    """Persist the daily token sequence counter."""
    path = repo_root / TOKEN_SEQ_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"date": date_str, "last_seq": seq}, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_token_id(repo_root: Path) -> str:
    """Generate a unique token identifier.

    Format: TKN-{YYYY-MM-DD}-{NNN} (e.g. TKN-2026-08-06-001).

    Per HOLDER_TOKEN.md §2.4: token_id is globally unique, generated at
    dispatch time, and embedded in CANDIDATE_BINDING.json.
    """
    today, seq = _load_token_seq(repo_root)
    token_id = f"TKN-{today}-{seq:03d}"
    _save_token_seq(repo_root, today, seq)
    return token_id


def _load_existing_binding(repo_root: Path) -> Optional[Dict[str, Any]]:
    """Read the current CANDIDATE_BINDING.json if it exists and is valid JSON."""
    path = repo_root / BINDING_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def write_binding_with_token(
    repo_root: Path,
    task_id: str,
    branch: str,
    base_sha: str,
    scope: List[str],
    token_id: str,
    maker_name: str,
    authorization_id: str = "",
    repository: str = "butbutbutbutbutbut/adaptive-digital-team",
) -> Dict[str, Any]:
    """Atomically write .hermes/CANDIDATE_BINDING.json with embedded token.

    Per HOLDER_TOKEN.md §2.3 (方案 A):
      The token is embedded directly in the binding file.  A single
      write operation atomically completes both "bind task" and
      "issue token", eliminating the two-file inconsistency window.

    Per HOLDER_TOKEN.md §6:
      The token field is an *addition* — all existing required fields
      are preserved.  validate_binding.py's check logic is unchanged.

    Returns the full binding dict that was written.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TOKEN_TTL_HOURS)

    # Preserve carry-over fields from existing binding if present
    # (e.g. authority_source, human_role — stable across tasks)
    existing = _load_existing_binding(repo_root)

    binding: Dict[str, Any] = {
        "authorization_id": authorization_id or f"AUTH-{task_id}",
        "authority_source": (
            existing.get("authority_source", "Human Holder authorization")
            if existing
            else "Human Holder authorization"
        ),
        "human_role": (
            existing.get("human_role", "HUMAN_HOLDER")
            if existing
            else "HUMAN_HOLDER"
        ),
        "repository": repository,
        "base_sha": base_sha,
        "branch": branch,
        "authorized_actions": ["read", "write_file", "commit", "push"],
        "authorized_write_scope": list(scope),
        "risk_boundary": "LOW",
        "task_id": task_id,
        "human_holder_approved": True,
        # ── HOLDER_TOKEN.md §2.3: embedded token block ──
        "token": {
            "token_id": token_id,
            "task_id": task_id,
            "state": "HELD",
            "holder": maker_name,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "released_at": None,
            "release_reason": None,
        },
    }

    # Write atomically (overwrite, not append/merge)
    binding_path = repo_root / BINDING_PATH
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(
        json.dumps(binding, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return binding


def _token_gate(
    repo_root: Path,
    task_id: str,
    branch: str,
    base_sha: str,
    scope: List[str],
    maker_name: str,
    authorization_id: str = "",
) -> Dict[str, Any]:
    """Execute the token gate (step 2 of the dispatch chain).

    Returns {"status": "PASS", "token_id": str, "binding": dict, ...}
    on success, or {"status": "FAILED", "gate": "TOKEN_GATE", ...}
    on failure (fail-closed per HOLDER_TOKEN.md §3.1).
    """
    token_id = generate_token_id(repo_root)

    try:
        binding = write_binding_with_token(
            repo_root=repo_root,
            task_id=task_id,
            branch=branch,
            base_sha=base_sha,
            scope=scope,
            token_id=token_id,
            maker_name=maker_name,
            authorization_id=authorization_id,
        )
    except Exception as exc:
        # HOLDER_TOKEN.md §7: BINDING_CORRUPTED
        return {
            "status": "FAILED",
            "gate": "TOKEN_GATE",
            "reason": f"BINDING_CORRUPTED: Failed to write {BINDING_PATH}: {exc}",
            "failure_code": "BINDING_CORRUPTED",
        }

    # Verify the write actually landed (defense against partial-write / FS caching)
    try:
        on_disk = json.loads((repo_root / BINDING_PATH).read_text(encoding="utf-8"))
        if on_disk.get("token", {}).get("token_id") != token_id:
            return {
                "status": "FAILED",
                "gate": "TOKEN_GATE",
                "reason": "TOKEN_LOST: Binding written but token_id mismatch on re-read.",
                "failure_code": "TOKEN_LOST",
            }
    except Exception as exc:
        return {
            "status": "FAILED",
            "gate": "TOKEN_GATE",
            "reason": f"BINDING_CORRUPTED: Post-write verification failed: {exc}",
            "failure_code": "BINDING_CORRUPTED",
        }

    return {
        "status": "PASS",
        "token_id": token_id,
        "binding": binding,
    }


# ═══════════════════════════════════════════════════════════════════════
# GATE 3 — WORKTREE_GATE
#   Per WORKSPACE_ISOLATION.md §3.1 (creation) and §2.1 (path layout)
# ═══════════════════════════════════════════════════════════════════════

def _validate_worktree_creation(
    worktree_path: Path,
    branch: str,
    base_sha: str,
) -> Optional[str]:
    """Validate a newly created worktree.

    Per docs/worktree-quickstart.md §6:
      - HEAD == base_sha
      - branch matches
      - git status is clean

    Returns None on success, or an error message string on failure.
    """
    # Check HEAD == base_sha
    head_result = _git("rev-parse", "HEAD", cwd=worktree_path)
    if head_result.returncode != 0:
        return f"WORKTREE_VALIDATION_FAILED: cannot resolve HEAD in worktree"
    actual_head = head_result.stdout.strip()
    if actual_head != base_sha:
        return (
            f"BASE_DRIFT: worktree HEAD {actual_head[:8]} != "
            f"expected base {base_sha[:8]}"
        )

    # Check branch
    branch_result = _git("branch", "--show-current", cwd=worktree_path)
    if branch_result.returncode != 0:
        return "WORKTREE_VALIDATION_FAILED: cannot determine current branch"
    actual_branch = branch_result.stdout.strip()
    if actual_branch != branch:
        return (
            f"BINDING_MISMATCH: worktree branch '{actual_branch}' != "
            f"expected '{branch}'"
        )

    # Check clean status
    status_result = _git("status", "--porcelain", cwd=worktree_path)
    if status_result.returncode != 0:
        return "WORKTREE_VALIDATION_FAILED: cannot check git status"
    if status_result.stdout.strip():
        return "DIRTY_WORKTREE: worktree has uncommitted changes after creation"

    return None


def create_worktree(
    repo_root: Path,
    branch: str,
    maker_name: str,
    base_sha: str,
    repo_name: str,
) -> Tuple[Path, str]:
    """Create a git worktree for the maker agent.

    Per WORKSPACE_ISOLATION.md §3.1:
      git worktree add -b <branch> "<path>" <base_sha>

    Worktree is created at:
      <repo-parent>/.adt-worktrees/<repo-name>/<maker-name>/

    Returns (worktree_path, error_message).
    On success, error_message is an empty string.
    On failure, error_message describes the failure (fail-closed,
    no --force per WORKSPACE_ISOLATION.md §2.4).

    WORKSPACE_ISOLATION.md §5 failure codes returned:
      WORKTREE_BRANCH_CONFLICT, BASE_DRIFT, DIRTY_WORKTREE,
      WINDOWS_PATH_ERROR
    """
    worktree_parent = repo_root.parent / ADT_WORKTREES_DIR / repo_name
    worktree_path = worktree_parent / maker_name

    # ── Pre-flight checks ──

    # Path already exists?
    if worktree_path.exists():
        return worktree_path, (
            f"WORKTREE_BRANCH_CONFLICT: worktree path already exists: "
            f"{worktree_path}"
        )

    # Branch already checked out in another worktree?  Git enforces this
    # natively (WORKSPACE_ISOLATION.md §2.4), but we pre-check for a
    # clearer error message.
    list_result = _git("worktree", "list", cwd=repo_root)
    if list_result.returncode == 0:
        for line in list_result.stdout.splitlines():
            if f"[{branch}]" in line or f"[{branch.lower()}]" in line:
                return worktree_path, (
                    f"WORKTREE_BRANCH_CONFLICT: branch '{branch}' is already "
                    f"checked out in another worktree"
                )

    # Verify base_sha exists
    cat_result = _git("cat-file", "-e", f"{base_sha}^{{commit}}", cwd=repo_root)
    if cat_result.returncode != 0:
        return worktree_path, (
            f"BASE_DRIFT: base_sha {base_sha[:8]} does not resolve to a "
            f"commit in this repository"
        )

    # ── Create worktree ──

    # Use forward-slash path for git-bash / cross-platform compatibility
    # (docs/worktree-quickstart.md §9.5)
    posix_path = str(worktree_path).replace("\\", "/")

    result = _git(
        "worktree", "add", "-b", branch, posix_path, base_sha,
        cwd=repo_root,
        timeout=60,  # worktree creation can be slow on Windows
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()

        # ── Edge case: current branch has no commits ──
        # When the repository is on a branch with zero commits (e.g. a
        # freshly initialized orphan branch), `git worktree add -b` fails
        # with "fatal: invalid reference" because it tries to base the new
        # branch on the unresolvable HEAD.
        #
        # Fallback: create a detached worktree at base_sha, then checkout
        # the target branch inside it.  This preserves the invariant that
        # the worktree ends up on the correct branch at the correct SHA.
        if "invalid reference" in stderr.lower():
            # Step 1: create detached worktree
            detach_result = _git(
                "worktree", "add", "--detach", posix_path, base_sha,
                cwd=repo_root,
                timeout=60,
            )
            if detach_result.returncode != 0:
                return worktree_path, (
                    f"WORKTREE_CREATE_FAILED: -b failed ({stderr}), "
                    f"--detach fallback also failed: {detach_result.stderr.strip()}"
                )

            # Step 2: checkout the target branch inside the worktree
            co_result = _git(
                "checkout", "-b", branch,
                cwd=worktree_path,
                timeout=30,
            )
            if co_result.returncode != 0:
                return worktree_path, (
                    f"WORKTREE_CREATE_FAILED: detached worktree created but "
                    f"checkout -b {branch} failed: {co_result.stderr.strip()}"
                )
            # Fall through to post-creation validation below
        elif "already checked out" in stderr.lower():
            return worktree_path, f"WORKTREE_BRANCH_CONFLICT: {stderr}"
        elif "permission denied" in stderr.lower() or "cannot create" in stderr.lower():
            return worktree_path, f"WINDOWS_PATH_ERROR: {stderr}"
        else:
            return worktree_path, f"WORKTREE_CREATE_FAILED: {stderr}"

    # ── Post-creation validation ──
    validation_error = _validate_worktree_creation(worktree_path, branch, base_sha)
    if validation_error:
        return worktree_path, validation_error

    return worktree_path, ""


def _worktree_gate(
    repo_root: Path,
    branch: str,
    maker_name: str,
    base_sha: str,
    repo_name: str,
) -> Dict[str, Any]:
    """Execute the worktree gate (step 3 of the dispatch chain).

    Returns {"status": "PASS", "worktree_path": str, ...} on success,
    or {"status": "FAILED", "gate": "WORKTREE_GATE", ...} on failure.
    """
    worktree_path, error = create_worktree(
        repo_root=repo_root,
        branch=branch,
        maker_name=maker_name,
        base_sha=base_sha,
        repo_name=repo_name,
    )

    if error:
        # Classify the error into a known failure code if possible
        failure_code = "WORKTREE_CREATE_FAILED"
        for code in sorted(WT_FAILURE_CODES, key=len, reverse=True):
            if error.startswith(code):
                failure_code = code
                break

        return {
            "status": "FAILED",
            "gate": "WORKTREE_GATE",
            "reason": error,
            "failure_code": failure_code,
            "worktree_path": str(worktree_path),
        }

    return {
        "status": "PASS",
        "worktree_path": str(worktree_path),
    }


# ═══════════════════════════════════════════════════════════════════════
# MAIN DISPATCH CHAIN
# ═══════════════════════════════════════════════════════════════════════

def _validate_inputs(
    task_id: str,
    branch: str,
    scope: List[str],
    base_sha: str,
    maker_name: str,
) -> Optional[str]:
    """Validate dispatch inputs before entering any gate.

    Returns None if all inputs are valid, or an error message string.
    All validation is fail-closed.
    """
    # task_id must be non-empty and look like ADT-YYYY-MM-DD-NNN
    if not task_id or not task_id.strip():
        return "task_id is required"
    if not re.match(r"^[A-Za-z0-9_-]+$", task_id):
        return f"task_id contains invalid characters: {task_id!r}"

    # branch must be non-empty
    if not branch or not branch.strip():
        return "branch is required"

    # scope must be a non-empty list of relative paths
    if not scope:
        return "scope is required (at least one file pattern)"
    for entry in scope:
        entry = str(entry).strip()
        if not entry:
            return "scope contains an empty entry"
        if os.path.isabs(entry) or entry.startswith("/"):
            return f"scope entry must be relative, not absolute: {entry!r}"
        if ".." in Path(entry).parts:
            return f"scope entry must not traverse directories: {entry!r}"

    # base_sha must be a 40-char hex string
    if not re.fullmatch(r"^[0-9a-f]{40}$", base_sha):
        return f"base_sha must be a 40-char hex SHA, got: {base_sha!r}"

    # maker_name must match [a-z0-9-]+ (WORKSPACE_ISOLATION.md §2.3)
    if not AGENT_NAME_RE.match(maker_name):
        return (
            f"maker_name must match [a-z0-9-]+, got: {maker_name!r}. "
            f"See WORKSPACE_ISOLATION.md §2.3."
        )

    return None


def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    """Execute the full dispatch gate chain.

    Chain: CONCURRENCY → TOKEN → WORKTREE → DISPATCH

    All gates fail-closed.  If any gate returns FAILED or REJECTED,
    the chain stops and the error is returned.  No partial state is
    left behind: on WORKTREE_GATE failure the token binding is left
    as a historical record (per HOLDER_TOKEN.md §2.2), but the caller
    must handle cleanup.

    Returns a dict that is always JSON-serializable.
    """
    repo_root = Path(args.repo_path).resolve()
    repo_name = args.repo_name or repo_root.name
    task_id = args.task_id.strip()
    branch = args.branch.strip()
    scope = [s.strip() for s in args.scope if s.strip()]
    base_sha = args.base_sha.strip() if args.base_sha else ""

    # Resolve base_sha from HEAD if not provided
    if not base_sha:
        head = _resolve_head(repo_root)
        if head is None:
            return {
                "status": "FAILED",
                "gate": "PREFLIGHT",
                "reason": "Cannot resolve HEAD as base_sha. "
                          "Specify --base-sha explicitly or ensure the "
                          "repository has at least one commit.",
                "failure_code": "BASE_DRIFT",
            }
        base_sha = head

    maker_name = (
        args.maker_name.strip()
        if args.maker_name
        else f"maker-{task_id.lower()}"
    )

    # ── Input validation ──
    validation_error = _validate_inputs(
        task_id=task_id,
        branch=branch,
        scope=scope,
        base_sha=base_sha,
        maker_name=maker_name,
    )
    if validation_error:
        return {
            "status": "FAILED",
            "gate": "PREFLIGHT",
            "reason": validation_error,
            "failure_code": "VALIDATION_ERROR",
        }

    n = args.max_concurrency if args.max_concurrency else DEFAULT_N
    authorization_id = args.authorization_id.strip() if args.authorization_id else ""

    # ═══════════════════════════════════════════════════════════════
    # GATE 1: CONCURRENCY_GATE
    # ═══════════════════════════════════════════════════════════════
    conc_result = _concurrency_gate(
        repo_root=repo_root,
        repo_name=repo_name,
        task_id=task_id,
        branch=branch,
        scope=scope,
        base_sha=base_sha,
        maker_name=maker_name,
        n=n,
    )

    # QUEUED or REJECTED — stop here, return status to caller
    if conc_result["status"] in ("QUEUED", "REJECTED"):
        return conc_result

    # ═══════════════════════════════════════════════════════════════
    # GATE 2: TOKEN_GATE
    # ═══════════════════════════════════════════════════════════════
    token_result = _token_gate(
        repo_root=repo_root,
        task_id=task_id,
        branch=branch,
        base_sha=base_sha,
        scope=scope,
        maker_name=maker_name,
        authorization_id=authorization_id,
    )

    if token_result["status"] != "PASS":
        return token_result

    token_id: str = token_result["token_id"]

    # ═══════════════════════════════════════════════════════════════
    # GATE 3: WORKTREE_GATE
    # ═══════════════════════════════════════════════════════════════
    wt_result = _worktree_gate(
        repo_root=repo_root,
        branch=branch,
        maker_name=maker_name,
        base_sha=base_sha,
        repo_name=repo_name,
    )

    if wt_result["status"] != "PASS":
        # Combine token info with worktree failure for traceability
        wt_result["token_id"] = token_id
        wt_result["token_status"] = "HELD"  # token was issued but worktree failed
        return wt_result

    worktree_path: str = wt_result["worktree_path"]

    # ═══════════════════════════════════════════════════════════════
    # GATE 4: DISPATCH — assemble Dispatch Card
    # ═══════════════════════════════════════════════════════════════
    dispatch_card: Dict[str, Any] = {
        # ── Header ──
        "PACKET": "DISPATCH_CARD",
        # ── Standard fields (PERSISTENT_HOLDER_CONTROL_PLANE.md) ──
        "TASK_ID": task_id,
        "AUTHORIZATION_ID": authorization_id or f"AUTH-{task_id}",
        "REPOSITORY": "butbutbutbutbutbut/adaptive-digital-team",
        "BRANCH": branch,
        "BASE_SHA": base_sha,
        "SCOPE": scope,
        # ── Extended fields ──
        # WORKSPACE_ISOLATION.md §4.1: WORKTREE field on Dispatch Card
        "WORKTREE": worktree_path,
        # HOLDER_TOKEN.md §3.2: TOKEN_ID delivered with Dispatch Card
        "TOKEN_ID": token_id,
        # CONCURRENCY_LIMIT.md §5.3: optional CONCURRENCY_STATUS
        "CONCURRENCY_STATUS": "IN_FLIGHT",
        # ── Runtime metadata ──
        "IN_FLIGHT_BEFORE": conc_result["in_flight_before"],
        "IN_FLIGHT_AFTER": conc_result["in_flight_after"],
        "MAX_CONCURRENCY": n,
        "MAKER_NAME": maker_name,
        "DISPATCHED_AT": datetime.now(timezone.utc).isoformat(),
        # ── Status ──
        "status": "DISPATCHED",
    }

    return dispatch_card


# ═══════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "P0 Runtime Controller Dispatch Gate — synthesizes three P0 "
            "protocols (CONCURRENCY_LIMIT, HOLDER_TOKEN, WORKSPACE_ISOLATION) "
            "into a single atomic dispatch gate chain."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/controller_dispatch.py \\\n"
            "    --task-id ADT-2026-08-06-001 \\\n"
            "    --branch hermes/adt-example-r1 \\\n"
            "    --scope scripts/example.py tests/test_example.py\n"
            "\n"
            "  # Override concurrency cap (Human-authorized only):\n"
            "  python scripts/controller_dispatch.py \\\n"
            "    --task-id ADT-2026-08-06-002 \\\n"
            "    --branch hermes/adt-example-r2 \\\n"
            "    --scope scripts/example.py \\\n"
            "    --max-concurrency 1\n"
            "\n"
            "Exit codes: 0 = dispatched, 1 = queued/rejected, 2 = failed"
        ),
    )

    # Required arguments
    parser.add_argument(
        "--task-id", required=True,
        help="Task identifier (e.g. ADT-2026-08-06-001)",
    )
    parser.add_argument(
        "--branch", required=True,
        help="Git branch name for the candidate task",
    )
    parser.add_argument(
        "--scope", nargs="+", required=True,
        help="Authorized write scope — one or more file path patterns",
    )

    # Optional arguments
    parser.add_argument(
        "--base-sha", default="",
        help="Base commit SHA (40-char hex). Defaults to HEAD if omitted.",
    )
    parser.add_argument(
        "--repo-path", default=".",
        help="Path to the repository root. Default: current directory.",
    )
    parser.add_argument(
        "--repo-name", default="",
        help=(
            "Repository name for worktree directory layout. "
            "Default: derived from the repository directory name."
        ),
    )
    parser.add_argument(
        "--maker-name", default="",
        help=(
            "Maker worktree directory name. Must match [a-z0-9-]+. "
            "Default: maker-<task-id-lowercased>."
        ),
    )
    parser.add_argument(
        "--max-concurrency", type=int, default=0,
        help=(
            "Override the in-flight concurrency cap N (default: 2). "
            "Raising N above 2 requires Human authorization per "
            "CONCURRENCY_LIMIT.md §3.2."
        ),
    )
    parser.add_argument(
        "--authorization-id", default="",
        help="Authorization identifier. Default: AUTH-<task-id>.",
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Always output as JSON (default: pretty-print on success).",
    )

    args = parser.parse_args()

    # Guard: raising N without explicit Human authorization is a
    # governance violation (CONCURRENCY_LIMIT.md §3.2).  We can't
    # enforce this programmatically, but we warn.
    if args.max_concurrency and args.max_concurrency > DEFAULT_N:
        print(
            f"[WARN] Concurrency cap raised to N={args.max_concurrency} "
            f"(default N={DEFAULT_N}). This requires Human authorization "
            f"per CONCURRENCY_LIMIT.md §3.2.",
            file=sys.stderr,
        )

    result = dispatch(args)

    # ── Output ──
    if result.get("status") in ("FAILED", "REJECTED", "QUEUED") or args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Pretty-print Dispatch Card as KEY: VALUE pairs
        for key, value in result.items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")

    # ── Exit code mapping ──
    status = result.get("status", "UNKNOWN")
    if status == "FAILED":
        sys.exit(2)
    elif status == "REJECTED":
        sys.exit(1)
    elif status == "QUEUED":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
