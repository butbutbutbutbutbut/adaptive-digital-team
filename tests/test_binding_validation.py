from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_binding import BindingValidator, HARD_STOP, STACKED_PR_PROHIBITED  # noqa: E402

REPO = "butbutbutbutbutbut/adaptive-digital-team"
BASE, HEAD = "a" * 40, "b" * 40
BRANCH = "hermes/adt-candidate-identity-single-pr-gate-r1"
SCOPE = [
    "AGENTS.md", "protocols/LIGHTWEIGHT_EXECUTION_FLOW.md",
    "protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md", ".github/workflows/validate.yml",
    "scripts/validate_binding.py", "tests/test_binding_validation.py",
    "tests/run_tests.py", "PROJECT_STATE.md",
]


def state(**changes):
    value = {
        "schema_version": "2", "task_id": "ADT-CANDIDATE-IDENTITY-AND-SINGLE-PR-GATE-R1",
        "repository": REPO, "branch": BRANCH, "starting_base_sha": BASE,
        "authorized_write_scope": list(SCOPE),
        "authority": {"authorization_id": "ADT-CANDIDATE-IDENTITY-AND-SINGLE-PR-GATE-20260720-001"},
        "current_gate": "EXTERNAL_INDEPENDENT_GOVERNANCE_AUDIT",
        "implementation_status": "NOT_AUTHORIZED",
    }
    for key, item in changes.items():
        if item is DELETE:
            value.pop(key, None)
        else:
            value[key] = item
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


class Delete: pass
DELETE = Delete()


def fields(**changes):
    value = {"repository": REPO, "base_ref": "main", "base_sha": BASE,
             "head_ref": BRANCH, "head_sha": HEAD, "changed_files": list(SCOPE)}
    value.update(changes)
    return value


def patch_runtime(monkeypatch, v, runtime=HEAD, main=BASE, remote=HEAD, changed=None, clean=True):
    monkeypatch.setattr(v, "_runtime_head", lambda: runtime)
    monkeypatch.setattr(v, "_current_branch", lambda: BRANCH)
    monkeypatch.setattr(v, "_remote_head", lambda branch: main if branch == "main" else remote)
    monkeypatch.setattr(v, "_changed_files", lambda base, head: list(SCOPE if changed is None else changed))
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


# Preserved baseline regression coverage (34+ collected cases).
def test_static_valid(): assert BindingValidator(state()).validate()

@pytest.mark.parametrize("key", ["task_id", "repository", "branch", "starting_base_sha",
                                  "authorized_write_scope", "authority", "current_gate", "implementation_status"])
def test_required_stable_fields(key):
    v = BindingValidator(state(**{key: DELETE})); assert not v.validate()

@pytest.mark.parametrize("key", ["current_head_sha", "current_main_sha", "current_event_sha",
                                  "current_remote_branch_sha", "current_candidate_fingerprint",
                                  "candidate_fingerprint", "runtime_fingerprint"])
def test_no_runtime_cache(key):
    v = BindingValidator(state(**{key: HEAD})); assert not v.validate()

def test_scope_wildcard_fails(): assert not BindingValidator(state(authorized_write_scope=["protocols/**"])).validate()
def test_wrong_repo_fails(): assert not BindingValidator(state(repository="other/repo")).validate()
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


# Candidate Lifecycle R1 required cases.
def test_push_feature_identity_pass(monkeypatch):
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    assert v.validate()

def test_push_main_identity_pass(monkeypatch):
    v = BindingValidator(state(branch="main"), live_mode=True); push_env(monkeypatch, "main"); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_remote_head", lambda branch: HEAD)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE})
    assert v.validate() and v.runtime_fields["base_sha"] == BASE

def test_invalid_github_ref_hard_stop(monkeypatch):
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v1"); assert not v.validate()
    assert any(HARD_STOP in x for x in v.errors)

def test_pr_base_main_pass(monkeypatch, tmp_path):
    v = BindingValidator(state(), live_mode=True); pr_env(monkeypatch, tmp_path); patch_runtime(monkeypatch, v)
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

@pytest.mark.parametrize("changed", [[*SCOPE, "outside"], SCOPE[:-1]])
def test_changed_files_drift(monkeypatch, changed):
    v = BindingValidator(state(), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v, changed=changed)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE}); assert not v.validate()

def premerge(monkeypatch, expected, **changes):
    v = BindingValidator(state(), pre_merge=True, expected_fingerprint=expected,
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
    v = BindingValidator(state(resolved_head="1" * 40), live_mode=True); push_env(monkeypatch); patch_runtime(monkeypatch, v)
    monkeypatch.setattr(v, "_event_payload", lambda: {"before": BASE}); assert v.validate()

def test_workflow_all_pr_and_source_head():
    text = (ROOT / ".github/workflows/validate.yml").read_text()
    section = text.split("pull_request:", 1)[1].split("jobs:", 1)[0]
    assert "branches:" not in section and "github.event.pull_request.head.sha" in text

def test_workflow_push_branches_and_no_soft_fail():
    text = (ROOT / ".github/workflows/validate.yml").read_text()
    assert all(x in text for x in ("main", "hermes/**", "codex/**", "agent/**", "maker/**"))
    assert "continue-on-error" not in text

def test_project_state_and_protocol_contracts():
    state_text = (ROOT / "PROJECT_STATE.md").read_text()
    assert all(x not in state_text for x in ("current_head_sha", "candidate_fingerprint", "runtime_fingerprint"))
    assert BindingValidator(state_text).parse_yaml()["authorized_write_scope"] == SCOPE
    docs = "\n".join((ROOT / p).read_text() for p in ["AGENTS.md", "protocols/LIGHTWEIGHT_EXECUTION_FLOW.md", "protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md"])
    assert "ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN" in docs
    assert "PRE_MERGE_REALTIME_GATE" in docs
