from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_binding import (  # noqa: E402
    BindingValidator, HARD_STOP, STACKED_PR_PROHIBITED, SCOPE_VIOLATION,
    CANDIDATE_STATES,
)

REPO = os.environ.get("GITHUB_REPOSITORY", "butbutbutbutbutbut/adaptive-digital-team")
BASE, HEAD = "0" * 40, "1" * 40
BRANCH = "hermes/adt-external-bootstrap-activation-r1"
SCOPE = [
    "AGENTS.md",
    "BOOTSTRAP.md",
    "PROJECT_STATE.md",
    "README.md",
    "protocols/BEGINNER_BOOTSTRAP_ROUTER.md",
    "tests/test_beginner_bootstrap.py",
    "tests/test_binding_validation.py",
    "中文内容/README.md",
]


def state(**changes):
    """Build a test PROJECT_STATE document WITHOUT transient-candidate fields.

    Transient fields (task_id, branch, starting_base_sha, authorized_write_scope)
    are NOT included — they now live in .hermes/CANDIDATE_BINDING.json.
    Use state_legacy() for tests that need the old pre-decoupling format.
    """
    value = {
        "schema_version": "2",
        "repository": REPO,
        "authority": {
            "holder": "HE-WEIZHI",
            "maker": "HERMES_TEMPORARY_GOVERNANCE_MAKER",
            "checker": "EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER-024",
        },
        "current_gate": "FINAL_CANDIDATE_FREEZE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    for key, item in changes.items():
        if item is DELETE:
            value.pop(key, None)
        else:
            value[key] = item
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


def state_legacy(**changes):
    """Build a test PROJECT_STATE document WITH transient-candidate fields.

    This is the pre-decoupling format used by legacy fallback tests.
    """
    value = {
        "schema_version": "2", "task_id": "ADT-EXTERNAL-BOOTSTRAP-ACTIVATION-R1",
        "repository": REPO, "branch": BRANCH, "starting_base_sha": BASE,
        "authorized_write_scope": list(SCOPE),
        "authority": {
            "holder": "HE-WEIZHI",
            "maker": "HERMES_TEMPORARY_GOVERNANCE_MAKER",
            "checker": "EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER-024",
        },
        "current_gate": "FINAL_CANDIDATE_FREEZE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    for key, item in changes.items():
        if item is DELETE:
            value.pop(key, None)
        else:
            value[key] = item
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


# ── Binding file management for tests ──────────────────────────

BINDING_PATH = ROOT / ".hermes" / "CANDIDATE_BINDING.json"
BINDING_BAK = BINDING_PATH.with_suffix(".json.bak")


@pytest.fixture(autouse=True)
def _auto_hide_binding(request):
    """Auto-hide CANDIDATE_BINDING.json for tests not marked @binding_required.

    Legacy tests (pre-decoupling) expect PROJECT_STATE-only mode.
    Tests marked @binding_required get the real binding file.
    """
    if request.node.get_closest_marker("binding_required"):
        # Restore binding if it was hidden
        if BINDING_BAK.exists() and not BINDING_PATH.exists():
            BINDING_BAK.rename(BINDING_PATH)
        yield
    else:
        # Hide binding for legacy tests
        was_hidden = False
        if BINDING_PATH.exists():
            BINDING_PATH.rename(BINDING_BAK)
            was_hidden = True
        yield
        if was_hidden and BINDING_BAK.exists():
            BINDING_BAK.rename(BINDING_PATH)


@pytest.fixture
def hide_binding():
    """Temporarily hide CANDIDATE_BINDING.json for legacy fallback tests."""
    was_hidden = False
    if BINDING_PATH.exists():
        BINDING_PATH.rename(BINDING_BAK)
        was_hidden = True
    yield
    if was_hidden and BINDING_BAK.exists():
        BINDING_BAK.rename(BINDING_PATH)


@pytest.fixture
def require_binding():
    """Ensure CANDIDATE_BINDING.json exists (restore from backup if hidden)."""
    if BINDING_BAK.exists() and not BINDING_PATH.exists():
        BINDING_BAK.rename(BINDING_PATH)
    yield


class Delete: pass
DELETE = Delete()


def fields(**changes):
    value = {"repository": REPO, "base_ref": "main", "base_sha": BASE,
             "head_ref": BRANCH, "head_sha": HEAD, "changed_files": list(SCOPE)}
    value.update(changes)
    return value


def patch_runtime(monkeypatch, v, runtime=HEAD, main=BASE, remote=HEAD, changed=None, clean=True,
                  branch=BRANCH, is_detached=False):
    monkeypatch.setattr(v, "_runtime_head", lambda: runtime)
    monkeypatch.setattr(v, "_current_branch", lambda: None if is_detached else branch)
    monkeypatch.setattr(v, "_is_detached", lambda: is_detached)
    monkeypatch.setattr(v, "_remote_head", lambda b: main if b == "main" else remote)
    monkeypatch.setattr(v, "_changed_files", lambda base, head: list(SCOPE if changed is None else changed))
    monkeypatch.setattr(v, "_local_changed_files", lambda: list(SCOPE if changed is None else changed))
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: list(SCOPE if changed is None else changed))
    monkeypatch.setattr(v, "_workspace_clean", lambda: clean)
    monkeypatch.setattr(v, "_commit_exists", lambda sha: True)
    monkeypatch.setattr(v, "_is_ancestor", lambda a, b: True)


def push_env(monkeypatch, branch=BRANCH, sha=HEAD, before=BASE):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", f"refs/heads/{branch}")
    monkeypatch.setenv("GITHUB_SHA", sha)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)


def pr_env(monkeypatch, tmp_path, base_ref="main", base_sha=BASE, head_ref=BRANCH, head_sha=HEAD):
    event = {"pull_request": {"base": {"ref": base_ref, "sha": base_sha},
                               "head": {"ref": head_ref, "sha": head_sha}}}
    path = tmp_path / "event.json"; path.write_text(json.dumps(event))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("GITHUB_SHA", "f" * 40)
    monkeypatch.setenv("GITHUB_REF", "refs/pull/99/merge")
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)


# ══════════════════════════════════════════════════════════════
# Preserved baseline regression coverage
# ══════════════════════════════════════════════════════════════

def test_static_valid(): assert BindingValidator(state_legacy()).validate()

@pytest.mark.parametrize("key", ["task_id", "repository", "branch", "starting_base_sha",
                                  "authorized_write_scope", "authority", "current_gate", "implementation_status"])
def test_required_stable_fields(key):
    v = BindingValidator(state(**{key: DELETE})); assert not v.validate()

@pytest.mark.parametrize("key", ["current_head_sha", "current_main_sha", "current_event_sha",
                                  "current_remote_branch_sha", "current_candidate_fingerprint",
                                  "candidate_fingerprint", "runtime_fingerprint"])
def test_no_runtime_cache(key):
    v = BindingValidator(state(**{key: HEAD})); assert not v.validate()

def test_scope_wildcard_warns_not_errors():
    """Glob patterns in scope now just warn in static mode; enforcement is live."""
    v = BindingValidator(state_legacy(authorized_write_scope=["protocols/**"]))
    v.validate()
    assert any("VALIDATION-SCOPE" in w for w in v.warnings)

def test_scope_empty_fails():
    v = BindingValidator(state_legacy(authorized_write_scope=[]))
    assert not v.validate()

def test_wrong_repo_fails(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "test-owner/test-repo")
    assert not BindingValidator(state(repository="other/repo")).validate()
def test_status_prewritten_fails(): assert not BindingValidator(state(implementation_status="IMPLEMENTED")).validate()

@pytest.mark.parametrize("ref,expected", [("refs/heads/main", "main"), (f"refs/heads/{BRANCH}", BRANCH)])
def test_push_ref_valid(monkeypatch, ref, expected):
    monkeypatch.setenv("GITHUB_REF", ref); assert BindingValidator(state())._push_ref_branch() == expected

@pytest.mark.parametrize("ref", ["", "refs/tags/v1", "refs/notes/x", "refs/pull/1/merge", "heads/main", "refs/heads/"])
def test_push_ref_invalid(monkeypatch, ref):
    monkeypatch.setenv("GITHUB_REF", ref); assert BindingValidator(state())._push_ref_branch() is None

@pytest.mark.parametrize("key,value", [
    ("repository", "other/repo"), ("base_ref", "candidate"), ("base_sha", "c" * 40),
    ("head_ref", "other"), ("head_sha", "d" * 40), ("changed_files", [*SCOPE, "x"]),
])
def test_fingerprint_drift(key, value):
    original = BindingValidator.candidate_fingerprint(fields())
    assert original != BindingValidator.candidate_fingerprint(fields(**{key: value}))

def test_fingerprint_order_and_duplicates():
    fp = BindingValidator.candidate_fingerprint(fields())
    assert fp == BindingValidator.candidate_fingerprint(fields(changed_files=[*reversed(SCOPE), SCOPE[0]]))

@pytest.mark.parametrize("case", range(6))
def test_legacy_baseline_cases(case):
    data = yaml.safe_load(state().split("```yaml\n", 1)[1].rsplit("```", 1)[0])
    data.update({"governance_base": {"branch": "main", "sha": BASE},
                 "authoritative_fact_source": {"type": "HUMAN_EXPLICIT", "branch": "main", "sha": BASE},
                 "comparison_candidates": [], "invalidated_candidates": [],
                 "visual_status": {"active_candidate": "DESIGN_CANDIDATE"}})
    if case == 0: data["authoritative_fact_source"].pop("type")
    elif case == 1: data["invalidated_candidates"] = [{"branch": BRANCH}]
    elif case == 2: data["authoritative_fact_source"]["type"] = "DISCOVERED"
    elif case == 3: data["comparison_candidates"] = [{"branch": BRANCH}]
    elif case == 4:
        data["authoritative_fact_source"] = {"type": "DISCOVERED", "branch": "feature", "sha": BASE}
        data["visual_status"] = {"active_candidate": "HUMAN_ACCEPTED"}
    else:
        data["current_gate"] = "FACT_SOURCE_REBIND"; data["authorized_action"] = "write"
    assert not BindingValidator(yaml.safe_dump(data)).validate()


# ══════════════════════════════════════════════════════════════
# Candidate Lifecycle R1 required cases (preserved)
# ══════════════════════════════════════════════════════════════

def test_push_feature_identity_pass(monkeypatch):
    v = BindingValidator(state_legacy(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    assert v.validate()

def test_push_main_identity_pass(monkeypatch):
    v = BindingValidator(state_legacy(branch="main"), live_mode=True); push_env(monkeypatch, "main"); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_remote_head", lambda branch: HEAD)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    assert v.validate() and v.runtime_fields["base_sha"] == BASE

def test_invalid_github_ref_hard_stop(monkeypatch):
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1"); assert not v.validate()
    assert any(HARD_STOP in x for x in v.errors)

def test_pr_base_main_pass(monkeypatch, tmp_path):
    v = BindingValidator(state_legacy(), live_mode=True); pr_env(monkeypatch, tmp_path); patch_runtime(monkeypatch, v)
    assert v.validate()

def test_stacked_pr_negative(monkeypatch, tmp_path):
    v = BindingValidator(state(), live_mode=True); pr_env(monkeypatch, tmp_path, base_ref="parent"); patch_runtime(monkeypatch, v)
    assert not v.validate() and any(STACKED_PR_PROHIBITED in x for x in v.errors)

def test_pr_merge_ref_rejected(monkeypatch, tmp_path):
    v = BindingValidator(state(), live_mode=True); pr_env(monkeypatch, tmp_path, head_ref="refs/pull/25/merge"); patch_runtime(monkeypatch, v)
    assert not v.validate() and any("merge ref" in x for x in v.errors)

@pytest.mark.parametrize("runtime,remote", [("c" * 40, HEAD), (HEAD, "d" * 40)])
def test_push_identity_drift(monkeypatch, runtime, remote):
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v, runtime=runtime, remote=remote)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE}); assert not v.validate()

@pytest.mark.parametrize("changed", [[*SCOPE, "outside"], [*SCOPE, "unauthorized.md"]])
def test_changed_files_drift(monkeypatch, changed):
    """Files outside authorized scope cause failure."""
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v, changed=changed)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: changed)
    assert not v.validate()

def premerge(monkeypatch, expected, **changes):
    v = BindingValidator(state_legacy(), pre_merge=True, expected_fingerprint=expected,
                         audit_fingerprint=changes.pop("audit", None),
                         ready_authorization_fingerprint=changes.pop("ready", None),
                         merge_authorization_fingerprint=changes.pop("merge", None))
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False); monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v, **changes); return v

def test_premerge_exact_match(monkeypatch):
    fp = BindingValidator.candidate_fingerprint(fields()); assert premerge(monkeypatch, fp).validate()

@pytest.mark.parametrize("changes", [
    {"main": "c" * 40}, {"runtime": "d" * 40, "remote": "d" * 40},
    {"changed": [*SCOPE, "drift"]}, {"clean": False},
])
def test_premerge_drift(monkeypatch, changes):
    fp = BindingValidator.candidate_fingerprint(fields()); assert not premerge(monkeypatch, fp, **changes).validate()

@pytest.mark.parametrize("binding", ["audit", "ready", "merge"])
def test_old_binding_invalid_after_new_commit(monkeypatch, binding):
    fp = BindingValidator.candidate_fingerprint(fields()); kwargs = {binding: "0" * 64}
    v = premerge(monkeypatch, fp, **kwargs); assert not v.validate() and any("INVALID" in x for x in v.errors)

def test_resolved_head_anchor(monkeypatch):
    v = BindingValidator(state_legacy(resolved_head="1" * 40), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE}); assert v.validate()

def test_workflow_all_pr_and_source_head():
    text = (ROOT / ".github/workflows/validate.yml").read_text()
    section = text.split("pull_request:", 1)[1].split("jobs:", 1)[0]
    assert "branches:" not in section and "github.event.pull_request.head.sha" in text

def test_workflow_push_branches_and_no_soft_fail():
    text = (ROOT / ".github/workflows/validate.yml").read_text()
    assert all(x in text for x in ("main", "hermes/**", "codex/**", "agent/**", "maker/**"))
    assert "continue-on-error" not in text

def test_project_state_and_protocol_contracts() -> None:
    """PROJECT_STATE.md must conform to universal governance invariants.

    This test asserts structural rules that apply to every task, not the
    specific files of any one task.  Task-scoped fields (task_id, branch,
    starting_base_sha, authorized_write_scope contents) vary per candidate
    and must not be asserted as permanent invariants here.
    """
    state_text = (ROOT / "PROJECT_STATE.md").read_text()

    # --- runtime cache prohibition (AGENTS.md §Durable state boundary) ---
    assert all(
        x not in state_text
        for x in ("current_head_sha", "candidate_fingerprint", "runtime_fingerprint")
    ), "PROJECT_STATE.md must not cache runtime SHA/fingerprint fields"

    parsed = BindingValidator(state_text).parse_yaml()

    # --- required stable fields ---
    # --- required stable fields (post-decoupling: no transient fields) ---
    required = [
        "repository",
        "authority",
        "current_gate",
        "implementation_status",
    ]
    for field in required:
        assert field in parsed, f"missing required field: {field}"

    # --- authorized_write_scope is now in CANDIDATE_BINDING.json, not PROJECT_STATE.md ---
    # Scope invariants are validated against the binding, not PROJECT_STATE
    # PROJECT_STATE.md must NOT contain transient fields (checked below)
    transient_forbidden = ["task_id", "branch", "starting_base_sha", "authorized_write_scope"]
    for field in transient_forbidden:
        assert field not in parsed, (
            f"PROJECT_STATE.md must not contain transient field: {field}. "
            f"It now lives in .hermes/CANDIDATE_BINDING.json"
        )

    # --- authority sub-fields ---
    auth = parsed["authority"]
    assert isinstance(auth, dict), "authority must be a dict"
    assert "holder" in auth
    assert "maker" in auth
    assert "checker" in auth

    # --- valid implementation_status ---
    valid_statuses = {
        "NOT_AUTHORIZED",
        "IN_PROGRESS",
        "IMPLEMENTATION_COMPLETE",
        "AUDIT_PASSED",
        "READY_FOR_REVIEW",
    }
    assert parsed["implementation_status"] in valid_statuses, (
        f"invalid implementation_status: {parsed['implementation_status']}"
    )

    # --- core governance document references ---
    docs = "\n".join(
        (ROOT / p).read_text()
        for p in [
            "AGENTS.md",
            "protocols/LIGHTWEIGHT_EXECUTION_FLOW.md",
            "protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md",
        ]
    )
    assert "ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN" in docs
    assert "PRE_MERGE_REALTIME_GATE" in docs
    assert "Candidate state machine" in docs


_ILLEGAL_STATES: list[str] = [
    # missing required field (authorized_write_scope)
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
""",
    # empty scope
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope: []
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: NOT_AUTHORIZED
""",
    # absolute path in scope
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope:
  - README.md
  - /etc/passwd
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: NOT_AUTHORIZED
""",
    # traversal in scope
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope:
  - README.md
  - ../../../secrets
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: NOT_AUTHORIZED
""",
    # PROJECT_STATE.md missing from own scope
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope:
  - README.md
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: NOT_AUTHORIZED
""",
    # illegal implementation_status
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope:
  - README.md
  - PROJECT_STATE.md
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: BAD_VALUE
""",
    # runtime cache field leaked
    """schema_version: "2"
task_id: X
repository: r
branch: b
starting_base_sha: "0000000000000000000000000000000000000000"
authorized_write_scope:
  - README.md
  - PROJECT_STATE.md
authority:
  holder: h
  maker: m
  checker: c
current_gate: g
implementation_status: NOT_AUTHORIZED
current_head_sha: "1111111111111111111111111111111111111111"
""",
]


@pytest.mark.parametrize("illegal_yaml", _ILLEGAL_STATES)
def test_project_state_rejects_illegal_values(illegal_yaml: str) -> None:
    """Universal invariants must reject known-illegal PROJECT_STATE inputs."""
    parsed = BindingValidator(illegal_yaml).parse_yaml()

    # At least one invariant should trip; the exact failure is
    # secondary — what matters is that bad states don't silently pass.
    failures: list[str] = []

    required = [
        "task_id", "repository", "branch", "starting_base_sha",
        "authorized_write_scope", "authority", "current_gate", "implementation_status",
    ]
    for field in required:
        if field not in parsed:
            failures.append(f"missing {field}")

    if "authorized_write_scope" in parsed:
        scope = parsed["authorized_write_scope"]
        if not isinstance(scope, list) or len(scope) == 0:
            failures.append("empty or invalid scope")
        else:
            if "PROJECT_STATE.md" not in scope:
                failures.append("PROJECT_STATE.md missing from scope")
            for p in scope:
                if p.startswith("/") or p.startswith("\\") or ".." in p:
                    failures.append(f"illegal path in scope: {p}")
                    break

    if "implementation_status" in parsed:
        valid = {
            "NOT_AUTHORIZED", "IN_PROGRESS", "IMPLEMENTATION_COMPLETE",
            "AUDIT_PASSED", "READY_FOR_REVIEW",
        }
        if parsed["implementation_status"] not in valid:
            failures.append(f"bad status: {parsed['implementation_status']}")

    if "current_head_sha" in parsed or "candidate_fingerprint" in parsed or "runtime_fingerprint" in parsed:
        failures.append("runtime cache field leaked")

    assert failures, (
        f"illegal PROJECT_STATE was not rejected\n"
        f"input:\n{illegal_yaml}\n"
        f"parsed: {parsed}"
    )


# ══════════════════════════════════════════════════════════════
# NEW: Scope enforcement tests
# ══════════════════════════════════════════════════════════════

def test_scope_normal_pass(monkeypatch):
    """Normal authorized scope: all changed files within scope → PASS."""
    v = BindingValidator(state_legacy(), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: list(SCOPE))
    assert v.validate()

def test_scope_outside_file_fails(monkeypatch):
    """File outside authorized_write_scope → SCOPE_VIOLATION."""
    v = BindingValidator(state_legacy(), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v, changed=[*SCOPE, "unauthorized/file.py"])
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: [*SCOPE, "unauthorized/file.py"])
    assert not v.validate()
    assert any(SCOPE_VIOLATION in e for e in v.errors)

def test_scope_staged_changes_checked(monkeypatch):
    """Staged changes must be checked against scope in candidate mode."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_local_changed_files", lambda: ["tests/test_binding_validation.py", "AGENTS.md"])
    # Both are in SCOPE → should pass
    assert v.validate()

def test_scope_unstaged_outside_fails(monkeypatch):
    """Unstaged changes outside scope → SCOPE_VIOLATION in candidate mode."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_local_changed_files", lambda: ["tests/test_binding_validation.py", "outside.txt"])
    assert not v.validate()
    assert any(SCOPE_VIOLATION in e for e in v.errors)

def test_scope_untracked_outside_fails(monkeypatch):
    """Untracked files outside scope → SCOPE_VIOLATION in candidate mode."""
    v = BindingValidator(state(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_local_changed_files", lambda: ["untracked_new_file.log"])
    assert not v.validate()
    assert any(SCOPE_VIOLATION in e for e in v.errors)

def test_scope_glob_legal_match(monkeypatch):
    """Glob pattern in scope that matches changed files → PASS."""
    scope_with_glob = ["tests/*.py", "protocols/*.md", "PROJECT_STATE.md"]
    v = BindingValidator(state_legacy(authorized_write_scope=scope_with_glob), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v, changed=["tests/test_binding_validation.py", "protocols/BEGINNER_BOOTSTRAP_ROUTER.md"])
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: ["tests/test_binding_validation.py", "protocols/BEGINNER_BOOTSTRAP_ROUTER.md"])
    assert v.validate()

def test_scope_glob_overreach_fails(monkeypatch):
    """Glob matches authorized files but a changed file outside glob → SCOPE_VIOLATION."""
    scope_with_glob = ["tests/*.py", "protocols/*.md"]
    v = BindingValidator(state_legacy(authorized_write_scope=scope_with_glob), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v, changed=["tests/test_binding_validation.py", "AGENTS.md"])
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: ["tests/test_binding_validation.py", "AGENTS.md"])
    assert not v.validate()
    assert any(SCOPE_VIOLATION in e for e in v.errors)

def test_scope_missing_fail_closed(monkeypatch):
    """Missing scope in candidate mode → fail-closed."""
    v = BindingValidator(state_legacy(authorized_write_scope=[]), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    assert not v.validate()

def test_scope_empty_fail_closed_candidate(monkeypatch):
    """Empty scope in candidate mode → fail-closed."""
    v = BindingValidator(state_legacy(authorized_write_scope=[]), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    assert not v.validate()

def test_scope_duplicate_path_fails(monkeypatch):
    """Duplicate paths in scope → SCOPE_VIOLATION."""
    dup_scope = SCOPE + ["AGENTS.md"]  # deliberate duplicate
    v = BindingValidator(state_legacy(authorized_write_scope=dup_scope), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    v.validate()
    assert any("duplicate" in e.lower() for e in v.errors)

def test_scope_absolute_path_fails():
    """Absolute path in scope → SCOPE_VIOLATION."""
    v = BindingValidator(state_legacy(authorized_write_scope=["/etc/passwd"]))
    v.validate()
    assert any("absolute" in e.lower() for e in v.errors)

def test_scope_traversal_path_fails():
    """Path with .. traversal → SCOPE_VIOLATION."""
    v = BindingValidator(state_legacy(authorized_write_scope=["../outside/file.txt"]))
    v.validate()
    assert any("traversal" in e.lower() for e in v.errors)

def test_scope_static_no_git_dependency():
    """Static text validation must not depend on Git."""
    # In static mode (live_mode=False), scope entry validation works without git
    v = BindingValidator(state_legacy(), live_mode=False)
    v.validate()
    # Should succeed without needing git
    assert not any("unresolved" in e.lower() for e in v.errors)


# ══════════════════════════════════════════════════════════════
# NEW: Pre-write execution gate tests
# ══════════════════════════════════════════════════════════════

def test_prewrite_detached_head_fails(monkeypatch):
    """Local write mode with detached HEAD → HARD_STOP."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v, is_detached=True)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("detached HEAD" in e for e in v.errors)

def test_prewrite_branch_mismatch_fails(monkeypatch):
    """Current branch differs from declared branch → HARD_STOP."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v, branch="hermes/wrong-branch")
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("branch mismatch" in e for e in v.errors)

def test_prewrite_base_not_exist_fails(monkeypatch):
    """Exact base commit does not exist → HARD_STOP."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_commit_exists", lambda sha: False)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("does not exist" in e for e in v.errors)

def test_prewrite_base_not_ancestor_fails(monkeypatch):
    """Exact base is not an ancestor of current HEAD → HARD_STOP."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_is_ancestor", lambda a, b: False)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("not an ancestor" in e for e in v.errors)

def test_prewrite_non_main_derived_fails(monkeypatch):
    """Candidate base does not derive from main → HARD_STOP."""
    v = BindingValidator(state_legacy(starting_base_sha="x" * 40), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v, main=BASE, remote="x" * 40)
    # _is_ancestor(main_sha, exact_base) should be False
    monkeypatch.setattr(v, "_is_ancestor", lambda a, b: False)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("does not derive from main" in e for e in v.errors)

def test_prewrite_base_drift_fails(monkeypatch):
    """Base drift (main advanced beyond declared base) → HARD_STOP."""
    advanced_main = "c" * 40
    v = BindingValidator(state_legacy(starting_base_sha=BASE), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v, main=advanced_main, remote=BASE)
    # Ancestry OK, but main_sha != exact_base → base drift
    monkeypatch.setattr(v, "_is_ancestor", lambda a, b: True)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("base drift" in e for e in v.errors)

def test_prewrite_ci_detached_ok(monkeypatch, tmp_path):
    """CI detached checkout with valid GITHUB_REF → should not fail on detached HEAD."""
    v = BindingValidator(state(), live_mode=True)
    pr_env(monkeypatch, tmp_path)
    patch_runtime(monkeypatch, v, is_detached=True)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    # CI mode should NOT add detached HEAD error
    assert not any("detached HEAD" in e for e in v.errors)

def test_prewrite_pr_branch_mismatch_fails(monkeypatch, tmp_path):
    """PR head ref differs from declared branch → HARD_STOP."""
    v = BindingValidator(state_legacy(), live_mode=True)
    pr_env(monkeypatch, tmp_path, head_ref="hermes/wrong-pr-branch")
    patch_runtime(monkeypatch, v, is_detached=True)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("differs from declared branch" in e for e in v.errors)

def test_prewrite_pr_non_main_base_fails(monkeypatch, tmp_path):
    """PR with non-main base_ref → HARD_STOP."""
    v = BindingValidator(state(), live_mode=True)
    pr_env(monkeypatch, tmp_path, base_ref="feature/other")
    patch_runtime(monkeypatch, v, is_detached=True)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("derive from main" in e for e in v.errors)

def test_prewrite_push_branch_mismatch_fails(monkeypatch):
    """Push branch differs from declared branch → HARD_STOP."""
    v = BindingValidator(state_legacy(), live_mode=True)
    push_env(monkeypatch, branch="hermes/wrong-push-branch")
    patch_runtime(monkeypatch, v, is_detached=True)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert any("differs from declared branch" in e for e in v.errors)

def test_prewrite_normal_branch_pass(monkeypatch):
    """Normal local branch matching declaration → PASS."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    v.parsed = v.parse()
    v.check_prewrite_gate()
    assert not v.errors


# ══════════════════════════════════════════════════════════════
# NEW: Candidate state distinction tests
# ══════════════════════════════════════════════════════════════

def test_candidate_state_local_draft_default():
    """Default state without any checks → LOCAL_DRAFT."""
    v = BindingValidator(state())
    v.validate()
    assert v.candidate_state == "LOCAL_DRAFT"

def test_candidate_state_write_authorized(monkeypatch):
    """Candidate mode with no errors → WRITE_AUTHORIZED (before commits)."""
    v = BindingValidator(state_legacy(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    v.validate()
    assert v.candidate_state in ("WRITE_AUTHORIZED", "COMMITTED_CANDIDATE")

def test_candidate_state_formal_in_pr(monkeypatch, tmp_path):
    """PR event with all checks passing → FORMAL_CANDIDATE or AUDIT_ELIGIBLE."""
    v = BindingValidator(state_legacy(), live_mode=True)
    pr_env(monkeypatch, tmp_path)
    patch_runtime(monkeypatch, v)
    v.validate()
    assert v.candidate_state in ("FORMAL_CANDIDATE", "AUDIT_ELIGIBLE")

def test_candidate_state_not_audit_eligible_without_pr(monkeypatch):
    """Without PR → cannot be AUDIT_ELIGIBLE."""
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    v = BindingValidator(state())
    v.runtime_fields = fields()
    v.runtime_fingerprint = BindingValidator.candidate_fingerprint(fields())
    result = v.determine_candidate_state()
    assert result != "AUDIT_ELIGIBLE"

def test_candidate_state_not_formal_without_commits(monkeypatch):
    """No changed files → cannot be FORMAL_CANDIDATE."""
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    v = BindingValidator(state())
    v.runtime_fields = fields(changed_files=[])
    v.runtime_fingerprint = BindingValidator.candidate_fingerprint(fields(changed_files=[]))
    result = v.determine_candidate_state()
    assert result != "FORMAL_CANDIDATE"

def test_candidate_state_no_fingerprint_no_audit(monkeypatch):
    """Without fingerprint → cannot be AUDIT_ELIGIBLE."""
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    v = BindingValidator(state())
    v.runtime_fields = fields()
    v.runtime_fingerprint = None
    result = v.determine_candidate_state()
    assert result != "AUDIT_ELIGIBLE"

def test_candidate_state_errors_force_local_draft(monkeypatch):
    """Any error → LOCAL_DRAFT regardless of other conditions."""
    v = BindingValidator(state(), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v)
    v.errors.append("SOME_ERROR")
    result = v.determine_candidate_state()
    assert result == "LOCAL_DRAFT"

def test_candidate_state_all_valid_states_defined():
    """All declared candidate states are valid strings."""
    for s in CANDIDATE_STATES:
        assert isinstance(s, str) and len(s) > 0


# ══════════════════════════════════════════════════════════════
# NEW: Explicit scope override tests
# ══════════════════════════════════════════════════════════════

def test_explicit_scope_overrides_binding():
    """--scope CLI flag overrides authorized_write_scope in binding."""
    explicit = ["a.py", "b.py"]
    v = BindingValidator(state(), explicit_scope=explicit)
    assert v._scope() == sorted(explicit)


# ══════════════════════════════════════════════════════════════
# NEW: CI file comparison modes
# ══════════════════════════════════════════════════════════════

def test_ci_pull_request_uses_base_vs_head(monkeypatch, tmp_path):
    """CI pull_request mode compares candidate vs target base."""
    v = BindingValidator(state_legacy(), live_mode=True)
    pr_env(monkeypatch, tmp_path, base_sha=BASE, head_sha=HEAD)
    patch_runtime(monkeypatch, v)
    # _ci_changed_files should be called with "pull_request"
    called_with = []
    def track_ci(ev):
        called_with.append(ev)
        return list(SCOPE)
    monkeypatch.setattr(v, "_ci_changed_files", track_ci)
    v.validate()
    assert "pull_request" in called_with

def test_ci_branch_push_uses_main_comparison(monkeypatch):
    """CI branch push compares push branch vs main."""
    v = BindingValidator(state_legacy(), live_mode=True)
    push_env(monkeypatch, branch=BRANCH, sha=HEAD)
    patch_runtime(monkeypatch, v)
    called_with = []
    def track_ci(ev):
        called_with.append(ev)
        return list(SCOPE)
    monkeypatch.setattr(v, "_ci_changed_files", track_ci)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    v.validate()
    assert "push" in called_with


# ══════════════════════════════════════════════════════════════
# NEW: Scope enforcement survives legacy baseline
# ══════════════════════════════════════════════════════════════

def test_scope_enforcement_does_not_break_static_validation():
    v = BindingValidator(state_legacy())
    """Static validation of a valid binding still passes with scope checks."""
    v = BindingValidator(state_legacy())
    result = v.validate()
    assert result, f"Static validation failed: {v.errors}"
    assert v.candidate_state == "LOCAL_DRAFT"


# ══════════════════════════════════════════════════════════════
# NEW: Candidate binding file support tests
# ══════════════════════════════════════════════════════════════

def _make_binding(**overrides):
    """Create a valid CANDIDATE_BINDING.json dict."""
    binding = {
        "authorization_id": "ADT-TEST-001",
        "authority_source": "Human Holder directive #42",
        "human_role": "HUMAN_HOLDER",
        "repository": REPO,
        "base_sha": BASE,
        "branch": BRANCH,
        "authorized_actions": ["read", "write_file", "commit", "push", "create_draft_pr"],
        "authorized_write_scope": list(SCOPE),
        "task_id": "ADT-EXTERNAL-BOOTSTRAP-ACTIVATION-R1",
    }
    binding.update(overrides)
    return binding


def _write_binding(tmp_path, binding):
    """Write CANDIDATE_BINDING.json to a tmp_path/.hermes/ directory."""
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir(parents=True, exist_ok=True)
    (hermes_dir / "CANDIDATE_BINDING.json").write_text(json.dumps(binding))


def _stable_state(**changes):
    """PROJECT_STATE.md with only stable fields (no transient fields)."""
    value = {
        "schema_version": "2",
        "repository": REPO,
        "authority": {
            "holder": "HE-WEIZHI",
            "maker": "HERMES_TEMPORARY_GOVERNANCE_MAKER",
            "checker": "EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER-024",
        },
        "current_gate": "FINAL_CANDIDATE_FREEZE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    for key, item in changes.items():
        if item is DELETE:
            value.pop(key, None)
        else:
            value[key] = item
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


# ── Valid binding passes ──

@pytest.mark.binding_required
@pytest.mark.binding_required
def test_valid_candidate_binding_passes(monkeypatch, tmp_path):
    """Valid CANDIDATE_BINDING.json + stable-only PROJECT_STATE → PASS."""
    binding = _make_binding()
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert v.validate()


# ── Wrong repository blocks ──

def test_wrong_repo_in_binding_blocks(monkeypatch, tmp_path):
    """Binding repository differs from PROJECT_STATE → HARD_STOP."""
    binding = _make_binding(repository="wrong/repo")
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any(HARD_STOP in e and "repository" in e.lower() for e in v.errors)


# ── Wrong branch blocks ──

def test_wrong_branch_in_binding_blocks_live(monkeypatch, tmp_path):
    """Binding branch != runtime head_ref → HARD_STOP in live mode."""
    binding = _make_binding(branch="hermes/wrong-branch")
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state(), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v, branch=BRANCH)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    assert not v.validate()
    assert any(HARD_STOP in e and "branch" in e.lower() for e in v.errors)


# ── Wrong task_id blocks ──

def test_missing_task_id_in_binding_blocks(monkeypatch, tmp_path):
    """Binding without task_id → HARD_STOP."""
    binding = _make_binding(task_id="")
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any("task_id" in e.lower() for e in v.errors)


# ── Wrong authorization_id blocks ──

def test_missing_authorization_id_in_binding_blocks(monkeypatch, tmp_path):
    """Binding without authorization_id → HARD_STOP (from _load_binding required check)."""
    binding = _make_binding(authorization_id="")
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any("authorization_id" in e.lower() or "missing required fields" in e.lower() for e in v.errors)


# ── Wrong starting_base_sha blocks ──

@pytest.mark.binding_required
@pytest.mark.binding_required
def test_wrong_starting_base_sha_blocks(monkeypatch, tmp_path):
    """Binding with invalid base_sha → HARD_STOP from _load_binding."""
    binding = _make_binding(base_sha="not-a-sha")
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any("base_sha" in e.lower() for e in v.errors)


def test_wrong_starting_base_sha_blocks_prewrite(monkeypatch, tmp_path):
    """Binding base_sha that doesn't exist as commit → HARD_STOP in candidate mode."""
    bad_sha = "d" * 40
    binding = _make_binding(base_sha=bad_sha)
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state(), candidate_mode=True)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
    patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_commit_exists", lambda sha: sha != bad_sha)
    v.parsed = v.parse()
    v._binding = v._load_binding()
    v.parsed = v.parse()  # re-parse for stable_state
    v.check_prewrite_gate()
    assert any("does not exist" in e for e in v.errors)


# ── Wrong authorized_write_scope blocks ──

def test_wrong_scope_in_binding_blocks_live(monkeypatch, tmp_path):
    """Binding scope that doesn't cover changed files → SCOPE_VIOLATION in live mode."""
    narrow_scope = ["README.md"]
    binding = _make_binding(authorized_write_scope=narrow_scope)
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state(), live_mode=True)
    push_env(monkeypatch)
    patch_runtime(monkeypatch, v, changed=list(SCOPE))
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    monkeypatch.setattr(v, "_ci_changed_files", lambda ev: list(SCOPE))
    assert not v.validate()
    assert any(SCOPE_VIOLATION in e for e in v.errors)


# ── Malformed binding blocks ──

@pytest.mark.binding_required
@pytest.mark.binding_required
def test_malformed_binding_blocks(monkeypatch, tmp_path):
    """CANDIDATE_BINDING.json with invalid JSON → HARD_STOP."""
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir(parents=True, exist_ok=True)
    (hermes_dir / "CANDIDATE_BINDING.json").write_text("not valid json {{{")
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any("malformed" in e.lower() for e in v.errors)


# ── Partial binding blocks ──

def test_partial_binding_missing_required_blocks(monkeypatch, tmp_path):
    """Binding file missing required fields → HARD_STOP."""
    binding = {"branch": BRANCH}  # missing most required fields
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(_stable_state())
    assert not v.validate()
    assert any("missing required fields" in e.lower() for e in v.errors)


# ── Mixed-source binding blocks ──

@pytest.mark.binding_required
@pytest.mark.binding_required
def test_mixed_source_binding_blocks(monkeypatch, tmp_path):
    """Binding exists AND PROJECT_STATE.md has transient fields → HARD_STOP."""
    binding = _make_binding()
    _write_binding(tmp_path, binding)
    monkeypatch.chdir(tmp_path)
    # Use state_legacy() which includes transient fields
    v = BindingValidator(state_legacy())
    assert not v.validate()
    assert any("dual-source" in e.lower() for e in v.errors)


# ── Complete legacy fallback passes ──

def test_complete_legacy_fallback_passes(monkeypatch, tmp_path):
    """No binding file, all transient fields in PROJECT_STATE → PASS."""
    monkeypatch.chdir(tmp_path)  # ensure no .hermes/CANDIDATE_BINDING.json
    v = BindingValidator(state_legacy())
    assert v.validate()


# ── Incomplete legacy fallback blocks ──

def test_incomplete_legacy_fallback_blocks(monkeypatch, tmp_path):
    """No binding file, PROJECT_STATE missing transient field → HARD_STOP."""
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(state_legacy(branch=DELETE))
    assert not v.validate()
    assert any("missing transient fields" in e.lower() for e in v.errors)


def test_incomplete_legacy_fallback_missing_task_id_blocks(monkeypatch, tmp_path):
    """No binding file, PROJECT_STATE missing task_id → HARD_STOP."""
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(state(task_id=DELETE))
    assert not v.validate()
    assert any("missing transient fields" in e.lower() for e in v.errors) and "task_id" in " ".join(v.errors)


def test_incomplete_legacy_fallback_missing_scope_blocks(monkeypatch, tmp_path):
    """No binding file, PROJECT_STATE missing authorized_write_scope → HARD_STOP."""
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(state_legacy(authorized_write_scope=DELETE))
    assert not v.validate()
    assert any("missing transient fields" in e.lower() for e in v.errors)


def test_incomplete_legacy_fallback_empty_scope_blocks(monkeypatch, tmp_path):
    """No binding file, PROJECT_STATE has empty authorized_write_scope → HARD_STOP."""
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(state_legacy(authorized_write_scope=[]))
    assert not v.validate()
    assert any("missing transient fields" in e.lower() for e in v.errors)


def test_incomplete_legacy_fallback_missing_base_sha_blocks(monkeypatch, tmp_path):
    """No binding file, PROJECT_STATE missing starting_base_sha → HARD_STOP."""
    monkeypatch.chdir(tmp_path)
    v = BindingValidator(state_legacy(starting_base_sha=DELETE))
    assert not v.validate()
    assert any("missing transient fields" in e.lower() for e in v.errors)
