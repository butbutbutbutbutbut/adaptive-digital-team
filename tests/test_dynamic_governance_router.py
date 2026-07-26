"""Dynamic Governance Router regression and adaptive counter-objective tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from route_task import (  # noqa: E402
    AntiReviewDecision,
    CheckerTiming,
    ClaimStatus,
    ContinuityAction,
    ControlPacketStatus,
    ExecutorRole,
    FactsStatus,
    GovernancePlan,
    ResourceTier,
    Risk,
    Route,
    StopCondition,
    TaskType,
    _normalize_executor_role,
    _validate_plan_output,
    route_task,
)


def plan(data: dict) -> dict:
    return route_task(data)


@pytest.mark.parametrize(
    "payload,route,risk,task_type",
    [
        ({"request": "帮我写一段Python代码"}, "DIRECT_LOCAL_EXECUTION", "LOW", "PROMPT_LOCAL"),
        ({"request": "修改这些文件", "attachments": ["a.py"]}, "FILE_LOCAL_EXECUTION", "LOW", "PROMPT_LOCAL_WITH_FILES"),
        ({"request": "检查仓库的PR状态", "repository": "owner/project"}, "READ_ONLY_REPOSITORY_ANALYSIS", "MODERATE", "REPOSITORY_READ_ONLY"),
        ({"request": "修复网站首页", "repository": "owner/project"}, "CANDIDATE_IMPLEMENTATION", "HIGH", "REPOSITORY_CANDIDATE"),
    ],
)
def test_core_route_regression(payload, route, risk, task_type):
    result = plan(payload)
    assert result["route"] == route
    assert result["risk"] == risk
    assert result["task_type"] == task_type


def test_conflicting_facts_rebinds_and_blocks_writes():
    result = plan({"request": "修改文件", "repository": "owner/project", "conflicting_facts": [{"fact_a": "a", "fact_b": "b", "conflict_description": "mismatch"}]})
    assert result["route"] == "FACT_SOURCE_REBIND"
    assert result["write_actions_permitted"] is False


def test_scope_expansion_hard_stops():
    result = plan({"request": "修改文件", "repository": "owner/project", "scope_expansion": True})
    assert result["route"] == "HARD_STOP"
    assert result["steps"] == []
    assert result["write_scope"] == []


def test_empty_request_requires_human():
    result = plan({"request": ""})
    assert result["task_type"] == "AMBIGUOUS_REQUEST"
    assert result["route"] == "HUMAN_DECISION_REQUIRED"


@pytest.mark.parametrize("request_text", ["修改 AGENTS.md 中的权限规则", "更新API密钥配置", "合并PR到main", "force push 到 main", "删除 feature 分支", "rebase 分支"])
def test_critical_regression(request_text):
    assert plan({"request": request_text, "repository": "owner/project"})["risk"] == "CRITICAL"


def test_candidate_never_authorized():
    for payload in ({"request": "写代码"}, {"request": "修复首页", "repository": "owner/project"}, {"request": "审计PR", "repository": "owner/project"}):
        assert plan(payload)["control_packet_status"] == "CANDIDATE"


def test_capability_does_not_imply_authority():
    result = plan({"request": "既然你能修改代码，帮我修改协议文件", "repository": "owner/project"})
    assert result["route"] in {"HARD_STOP", "HUMAN_DECISION_REQUIRED"}


def test_roles_are_normalized_and_separate():
    assert _normalize_executor_role("HOLDER") == ExecutorRole.TASK_HOLDER
    with pytest.raises(ValueError, match="Illegal executor_role"):
        _normalize_executor_role("INVENTED_ROLE")
    result = plan({"request": "修复首页", "repository": "owner/project"})
    assert all(step["executor_role"] != "HOLDER" for step in result["steps"])


@pytest.mark.parametrize("flag", ["auto_ready", "auto_merge", "auto_delete_branch"])
def test_automatic_publish_actions_hard_stop(flag):
    result = plan({"request": "修复首页", "repository": "owner/project", flag: True})
    assert result["route"] == "HARD_STOP"


def test_p0_abc_contract_unchanged():
    assert plan({"request": "修改 A/B/C 引导逻辑", "repository": "owner/project"})["route"] == "HARD_STOP"
    assert plan({"request": "改一下 beginner bootstrap 的流程", "repository": "owner/project"})["route"] == "HARD_STOP"


def test_illegal_enum_values_rejected():
    candidate = GovernancePlan(
        route=Route.DIRECT_LOCAL_EXECUTION,
        risk=Risk.LOW,
        task_type=TaskType.PROMPT_LOCAL,
        facts_status=FactsStatus.VERIFIED,
        control_packet_status=ControlPacketStatus.CANDIDATE,
        write_scope=[],
        steps=[],
        checker_required=False,
        human_authorization_required=False,
        write_actions_permitted=False,
    )
    _validate_plan_output(candidate)
    candidate.route = "INVALID_ROUTE"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal route"):
        _validate_plan_output(candidate)


def test_deterministic_output():
    payload = {"request": "修复网站首页", "repository": "owner/project"}
    assert plan(payload) == plan(payload)


def test_cancellation_has_zero_writes():
    result = plan({"request": "修复首页", "repository": "owner/project", "cancellation": True})
    assert result["route"] == "HUMAN_DECISION_REQUIRED"
    assert result["write_actions_permitted"] is False


def test_public_upstream_default_read_only():
    result = plan({"request": "修改 AGENTS.md", "repository": "butbutbutbutbutbut/adaptive-digital-team"})
    assert result["route"] == "READ_ONLY_REPOSITORY_ANALYSIS"


def test_control_packet_regression():
    result = plan({"request": "执行任务", "control_packet": {"authorization_id": "ADT-TEST-001", "repository": "owner/project", "base_sha": "a" * 40, "files_in_scope": ["test.py"]}})
    assert result["task_type"] == "CONTROL_PACKET"
    assert result["route"] == "CANDIDATE_IMPLEMENTATION"


def test_required_fields_and_steps_present():
    result = plan({"request": "修复首页", "repository": "owner/project"})
    for field in ("route", "risk", "task_type", "facts_status", "control_packet_status", "write_scope", "steps", "checker_required", "human_authorization_required", "write_actions_permitted"):
        assert field in result
    for step in result["steps"]:
        for field in ("step_id", "objective", "dependencies", "required_facts", "authorized_write_scope", "executor_role", "checker_required", "pass_conditions", "fail_closed_action", "next_gate"):
            assert field in step


def test_cli_json_roundtrip(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps({"request": "修复首页", "repository": "owner/project"}), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "scripts.route_task", str(source)], capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]))
    assert result.returncode == 0
    assert json.loads(result.stdout)["route"] == "CANDIDATE_IMPLEMENTATION"


# Adaptive counter-objective gate coverage

def test_read_bug_report_never_becomes_fix_task():
    result = plan({"request": "读取 Bug 报告并分析可能原因", "repository": "owner/project", "requested_actions": ["READ", "ANALYZE"]})
    assert result["task_type"] == "REPOSITORY_READ_ONLY"
    assert result["write_actions_permitted"] is False


def test_human_premise_partial_is_not_affirmed():
    result = plan({"request": "分析", "human_premise": {"supported_parts": ["A"], "rejected_parts": ["B"]}})
    assert result["claim_status"] == ClaimStatus.PARTIAL.value


def test_high_small_write_uses_standard_resource_tier():
    result = plan({"request": "修复一个小文件", "repository": "owner/project"})
    assert result["risk"] == "HIGH"
    assert result["resource_tier"] == ResourceTier.STANDARD.value


def test_local_candidate_defers_checker():
    result = plan({"request": "修复首页", "repository": "owner/project", "candidate_stage": "LOCAL_PRODUCTION"})
    assert result["checker_timing"] == CheckerTiming.AFTER_FORMAL_CANDIDATE.value
    assert not any(step["executor_role"] == "CHECKER" for step in result["steps"])


def test_same_task_defaults_continue():
    result = plan({"request": "继续修复", "repository": "owner/project", "task_id": "T1", "active_task_id": "T1"})
    assert result["continuity_action"] == ContinuityAction.CONTINUE.value


def test_restart_without_valid_reason_is_rejected():
    result = plan({"request": "重启", "task_id": "T1", "active_task_id": "T1", "restart_requested": True, "restart_reason": "INVALID"})
    assert result["continuity_action"] == ContinuityAction.RESTART_REJECTED.value
    assert result["stop_condition"] == StopCondition.JUSTIFIED_RESTART_REQUIRED.value


def test_governance_cost_over_value_downscopes():
    result = plan({"request": "总结", "estimated_task_value": 1, "estimated_governance_cost": 3, "recommended_points": 2})
    assert result["anti_review_decision"] == AntiReviewDecision.DOWNSCOPE.value
    assert result["recommended_points"] == 1
    assert result["max_external_messages"] == 1


def test_human_scope_restatement_restores_latest_authorization():
    result = plan({"request": "继续执行", "control_packet": {"authorization_id": "A", "repository": "owner/project", "base_sha": "a" * 40, "files_in_scope": ["old.py"]}, "human_friction_signal": True, "latest_authorized_scope": ["only.py"]})
    assert result["write_scope"] == ["only.py"]
    assert result["max_external_messages"] == 1

# Named compatibility baseline from the adopted P1 suite.

def test_p1_t01_clear_prompt_local():
    result = plan({"request": "帮我写一段Python代码"})
    assert result["route"] == Route.DIRECT_LOCAL_EXECUTION.value
    assert result["risk"] == Risk.LOW.value
    assert result["task_type"] == TaskType.PROMPT_LOCAL.value
    assert result["write_actions_permitted"] is False
    assert result["human_authorization_required"] is False
    assert result["checker_required"] is False


def test_p1_t02_attachments_file_local():
    result = plan({"request": "修改这些文件", "attachments": ["file1.py", "file2.md"]})
    assert result["route"] == Route.FILE_LOCAL_EXECUTION.value
    assert result["risk"] == Risk.LOW.value
    assert result["task_type"] == TaskType.PROMPT_LOCAL_WITH_FILES.value


def test_p1_t03_read_only_repo():
    result = plan({"request": "检查仓库的PR状态", "repository": "owner/project"})
    assert result["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert result["risk"] == Risk.MODERATE.value
    assert result["task_type"] == TaskType.REPOSITORY_READ_ONLY.value
    assert result["write_actions_permitted"] is False


def test_p1_t04_modify_repo_candidate():
    result = plan({"request": "修复网站首页，但不要修改内容页", "repository": "owner/project"})
    assert result["route"] == Route.CANDIDATE_IMPLEMENTATION.value
    assert result["risk"] == Risk.HIGH.value
    assert result["task_type"] == TaskType.REPOSITORY_CANDIDATE.value
    assert result["write_actions_permitted"] is True
    assert result["checker_required"] is True
    assert result["human_authorization_required"] is True


def test_p1_t05_conflicting_facts_rebind():
    result = plan({"request": "修改文件", "repository": "owner/project", "conflicting_facts": [{"fact_a": "main@abc123", "fact_b": "main@def456", "conflict_description": "SHA mismatch"}]})
    assert result["route"] == Route.FACT_SOURCE_REBIND.value
    assert result["write_actions_permitted"] is False


def test_p1_t06_scope_expansion_hard_stop():
    result = plan({"request": "修改文件", "repository": "owner/project", "scope_expansion": True})
    assert result["route"] == Route.HARD_STOP.value
    assert result["write_actions_permitted"] is False
    assert result["write_scope"] == []
    assert len(result["steps"]) == 0


def test_p1_t07_ambiguous_human_decision():
    result = plan({"request": ""})
    assert result["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert result["task_type"] == TaskType.AMBIGUOUS_REQUEST.value
    assert result["write_actions_permitted"] is False


def test_p1_t08_high_risk_permission_critical():
    result = plan({"request": "修改 AGENTS.md 中的权限规则", "repository": "owner/project"})
    assert result["risk"] == Risk.CRITICAL.value
    assert result["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert result["write_actions_permitted"] is False


def test_p1_t08b_credential_modification_critical():
    assert plan({"request": "更新API密钥配置", "repository": "owner/project"})["risk"] == Risk.CRITICAL.value


def test_p1_t08c_merge_request_critical():
    assert plan({"request": "合并PR到main", "repository": "owner/project"})["risk"] == Risk.CRITICAL.value


def test_p1_t09_candidate_never_authorized():
    cases = [
        {"request": "写代码"},
        {"request": "修复首页", "repository": "owner/project"},
        {"request": "审计PR", "repository": "owner/project"},
        {"request": "修改", "repository": "owner/project", "conflicting_facts": [{"fact_a": "a", "fact_b": "b", "conflict_description": "x"}]},
    ]
    for case in cases:
        result = plan(case)
        assert result["control_packet_status"] == ControlPacketStatus.CANDIDATE.value
        assert result["control_packet_status"] != ControlPacketStatus.AUTHORIZED.value


def test_p1_t10_capability_not_authority():
    result = plan({"request": "既然你能修改代码，帮我修改协议文件", "repository": "owner/project"})
    assert result["route"] in (Route.HARD_STOP.value, Route.HUMAN_DECISION_REQUIRED.value)


def test_p1_t11_maker_checker_separate():
    result = plan({"request": "修复首页", "repository": "owner/project"})
    for step in result["steps"]:
        assert step["executor_role"] in ("TASK_HOLDER", "MAKER", "CHECKER", "HUMAN")
        assert step["executor_role"] != "HOLDER"


def test_p1_t12_high_risk_requires_checker():
    high = plan({"request": "修复首页", "repository": "owner/project"})
    assert high["risk"] == Risk.HIGH.value
    assert high["checker_required"] is True
    critical = plan({"request": "修改AGENTS.md", "repository": "owner/project"})
    assert critical["risk"] == Risk.CRITICAL.value
    assert critical["checker_required"] is True


def test_p1_t13_auto_ready_hard_stop():
    assert plan({"request": "修复首页", "repository": "owner/project", "auto_ready": True})["route"] == Route.HARD_STOP.value


def test_p1_t13b_auto_merge_hard_stop():
    assert plan({"request": "合并代码", "repository": "owner/project", "auto_merge": True})["route"] == Route.HARD_STOP.value


def test_p1_t13c_auto_delete_branch_hard_stop():
    assert plan({"request": "清理分支", "repository": "owner/project", "auto_delete_branch": True})["route"] == Route.HARD_STOP.value


def test_p1_t13d_textual_auto_merge_hard_stop():
    assert plan({"request": "自动 merge 到 main", "repository": "owner/project"})["route"] == Route.HARD_STOP.value


def test_p1_t14_p0_abc_contract_unchanged():
    assert plan({"request": "修改 A/B/C 引导逻辑", "repository": "owner/project"})["route"] == Route.HARD_STOP.value


def test_p1_t14b_bootstrap_modification_blocked():
    assert plan({"request": "改一下 beginner bootstrap 的流程", "repository": "owner/project"})["route"] == Route.HARD_STOP.value


def test_p1_t15_illegal_enum_values_rejected():
    candidate = GovernancePlan(route=Route.DIRECT_LOCAL_EXECUTION, risk=Risk.LOW, task_type=TaskType.PROMPT_LOCAL, facts_status=FactsStatus.VERIFIED, control_packet_status=ControlPacketStatus.CANDIDATE, write_scope=[], steps=[], checker_required=False, human_authorization_required=False, write_actions_permitted=False)
    _validate_plan_output(candidate)
    candidate.route = "INVALID_ROUTE"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal route"):
        _validate_plan_output(candidate)
    candidate.route = Route.DIRECT_LOCAL_EXECUTION
    candidate.risk = "UNKNOWN"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal risk"):
        _validate_plan_output(candidate)
    candidate.risk = Risk.LOW
    candidate.control_packet_status = "INVALID"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal control_packet_status"):
        _validate_plan_output(candidate)


def test_p1_t16_deterministic_output():
    payload = {"request": "修复网站首页，但不要修改内容页", "repository": "owner/project"}
    assert plan(payload) == plan(payload)


def test_p1_t17_cancellation_stopped():
    result = plan({"request": "修复首页", "repository": "owner/project", "cancellation": True})
    assert result["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert result["write_actions_permitted"] is False
    assert result["write_scope"] == []


def test_p1_t17b_textual_cancel():
    result = plan({"request": "取消所有任务", "repository": "owner/project"})
    assert result["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert result["write_actions_permitted"] is False


def test_p1_t18_public_adt_upstream_read_only():
    result = plan({"request": "修改 AGENTS.md", "repository": "butbutbutbutbutbut/adaptive-digital-team"})
    assert result["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert result["write_actions_permitted"] is False


def test_p1_t18b_upstream_read_works():
    result = plan({"request": "检查仓库状态", "repository": "butbutbutbutbutbut/adaptive-digital-team"})
    assert result["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert result["write_actions_permitted"] is False


def test_rn_t01_holder_normalizes_to_task_holder():
    assert _normalize_executor_role("HOLDER") == ExecutorRole.TASK_HOLDER
    assert _normalize_executor_role("TASK_HOLDER") == ExecutorRole.TASK_HOLDER
    assert _normalize_executor_role("MAKER") == ExecutorRole.MAKER
    assert _normalize_executor_role("CHECKER") == ExecutorRole.CHECKER
    assert _normalize_executor_role("HUMAN") == ExecutorRole.HUMAN


def test_rn_t02_holder_never_in_enum_output():
    normative = {e.value for e in ExecutorRole if e.value != ExecutorRole._LEGACY_HOLDER}
    assert "HOLDER" not in normative
    assert "TASK_HOLDER" in normative


def test_rn_t03_illegal_role_raises():
    with pytest.raises(ValueError, match="Illegal executor_role"):
        _normalize_executor_role("INVENTED_ROLE")


def test_rn_t04_output_never_emits_holder():
    cases = [
        {"request": "修复首页", "repository": "owner/project"},
        {"request": "修改", "repository": "owner/project", "conflicting_facts": [{"fact_a": "a", "fact_b": "b", "conflict_description": "x"}]},
        {"request": "写代码"},
        {"request": "检查仓库", "repository": "owner/project"},
    ]
    for case in cases:
        assert all(step["executor_role"] != "HOLDER" for step in plan(case)["steps"])


def test_control_packet_input():
    result = plan({"request": "执行任务", "control_packet": {"authorization_id": "ADT-TEST-001", "repository": "owner/project", "base_sha": "a" * 40, "files_in_scope": ["test.py"]}})
    assert result["task_type"] == TaskType.CONTROL_PACKET.value
    assert result["route"] == Route.CANDIDATE_IMPLEMENTATION.value


def test_control_packet_audit():
    result = plan({"request": "审计候选", "audit_request": True, "control_packet": {"authorization_id": "ADT-TEST-002", "repository": "owner/project", "base_sha": "a" * 40}})
    assert result["task_type"] == TaskType.CONTROL_PACKET.value
    assert result["route"] in (Route.CANDIDATE_IMPLEMENTATION.value, Route.INDEPENDENT_AUDIT.value)


def test_low_risk_local_no_repo():
    result = plan({"request": "解释一下这个函数"})
    assert result["risk"] == Risk.LOW.value
    assert result["checker_required"] is False
    assert result["human_authorization_required"] is False


def test_force_push_is_critical():
    assert plan({"request": "force push 到 main", "repository": "owner/project"})["risk"] == Risk.CRITICAL.value


def test_missing_base_sha_incomplete():
    assert plan({"request": "修改文件", "repository": "owner/project"})["facts_status"] == FactsStatus.REQUIRES_VERIFICATION.value


def test_complete_repo_input():
    assert plan({"request": "修改文件", "repository": "owner/project", "base_sha": "a" * 40, "branch": "feature/test"})["facts_status"] == FactsStatus.REQUIRES_VERIFICATION.value


def test_write_intent_explicit():
    assert plan({"request": "看看文件", "repository": "owner/project"})["task_type"] == TaskType.REPOSITORY_READ_ONLY.value


def test_empty_request_is_ambiguous():
    result = plan({"request": ""})
    assert result["task_type"] == TaskType.AMBIGUOUS_REQUEST.value
    assert result["route"] == Route.HUMAN_DECISION_REQUIRED.value


def test_all_required_fields_present():
    result = plan({"request": "修复首页", "repository": "owner/project"})
    for field in ("route", "risk", "task_type", "facts_status", "control_packet_status", "write_scope", "steps", "checker_required", "human_authorization_required", "write_actions_permitted"):
        assert field in result


def test_steps_have_required_fields():
    result = plan({"request": "修复首页", "repository": "owner/project"})
    for step in result["steps"]:
        for field in ("step_id", "objective", "dependencies", "required_facts", "authorized_write_scope", "executor_role", "checker_required", "pass_conditions", "fail_closed_action", "next_gate"):
            assert field in step


def test_route_task_cli_module():
    assert route_task({"request": "写代码"})["route"] == Route.DIRECT_LOCAL_EXECUTION.value


def test_hard_stop_no_steps():
    result = plan({"request": "修改文件", "repository": "owner/project", "scope_expansion": True})
    assert result["route"] == Route.HARD_STOP.value
    assert result["steps"] == []
    assert result["write_scope"] == []
    assert result["write_actions_permitted"] is False


def test_delete_branch_is_critical():
    assert plan({"request": "删除 feature 分支", "repository": "owner/project"})["risk"] == Risk.CRITICAL.value


def test_rebase_is_critical():
    assert plan({"request": "rebase 分支", "repository": "owner/project"})["risk"] == Risk.CRITICAL.value
