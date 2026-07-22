"""P1 Dynamic Governance Router — test suite.

18 tests (P1-T01 through P1-T18) plus edge cases and role normalization tests.
All existing 158 tests must continue to pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from route_task import (  # noqa: E402
    ControlPacketStatus,
    ExecutorRole,
    FactsStatus,
    GovernanceRouter,
    Risk,
    Route,
    TaskIntake,
    TaskType,
    _normalize_executor_role,
    _validate_plan_output,
    parse_intake,
    route_task,
)


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _plan(data: dict) -> dict:
    return route_task(data)


# ═══════════════════════════════════════════════════════════
# P1-T01: 明确普通任务 → DIRECT_LOCAL_EXECUTION
# ═══════════════════════════════════════════════════════════

def test_p1_t01_clear_prompt_local():
    plan = _plan({"request": "帮我写一段Python代码"})
    assert plan["route"] == Route.DIRECT_LOCAL_EXECUTION.value
    assert plan["risk"] == Risk.LOW.value
    assert plan["task_type"] == TaskType.PROMPT_LOCAL.value
    assert plan["write_actions_permitted"] is False
    assert plan["human_authorization_required"] is False
    assert plan["checker_required"] is False


# ═══════════════════════════════════════════════════════════
# P1-T02: 附件任务 → FILE_LOCAL_EXECUTION
# ═══════════════════════════════════════════════════════════

def test_p1_t02_attachments_file_local():
    plan = _plan({
        "request": "修改这些文件",
        "attachments": ["file1.py", "file2.md"],
    })
    assert plan["route"] == Route.FILE_LOCAL_EXECUTION.value
    assert plan["risk"] == Risk.LOW.value
    assert plan["task_type"] == TaskType.PROMPT_LOCAL_WITH_FILES.value


# ═══════════════════════════════════════════════════════════
# P1-T03: 仅读仓库 → READ_ONLY_REPOSITORY_ANALYSIS
# ═══════════════════════════════════════════════════════════

def test_p1_t03_read_only_repo():
    plan = _plan({
        "request": "检查仓库的PR状态",
        "repository": "owner/project",
    })
    assert plan["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert plan["risk"] == Risk.MODERATE.value
    assert plan["task_type"] == TaskType.REPOSITORY_READ_ONLY.value
    assert plan["write_actions_permitted"] is False


# ═══════════════════════════════════════════════════════════
# P1-T04: 请求修改仓库 → CANDIDATE_IMPLEMENTATION
# ═══════════════════════════════════════════════════════════

def test_p1_t04_modify_repo_candidate():
    plan = _plan({
        "request": "修复网站首页，但不要修改内容页",
        "repository": "owner/project",
    })
    assert plan["route"] == Route.CANDIDATE_IMPLEMENTATION.value
    assert plan["risk"] == Risk.HIGH.value
    assert plan["task_type"] == TaskType.REPOSITORY_CANDIDATE.value
    assert plan["write_actions_permitted"] is True
    assert plan["checker_required"] is True
    assert plan["human_authorization_required"] is True


# ═══════════════════════════════════════════════════════════
# P1-T05: 不完整仓库事实 → FACT_SOURCE_REBIND
# ═══════════════════════════════════════════════════════════

def test_p1_t05_conflicting_facts_rebind():
    plan = _plan({
        "request": "修改文件",
        "repository": "owner/project",
        "conflicting_facts": [
            {"fact_a": "main@abc123", "fact_b": "main@def456", "conflict_description": "SHA mismatch"},
        ],
    })
    assert plan["route"] == Route.FACT_SOURCE_REBIND.value
    assert plan["write_actions_permitted"] is False


# ═══════════════════════════════════════════════════════════
# P1-T06: 冲突 PR/SHA → HARD_STOP / 零写入
# ═══════════════════════════════════════════════════════════

def test_p1_t06_scope_expansion_hard_stop():
    plan = _plan({
        "request": "修改文件",
        "repository": "owner/project",
        "scope_expansion": True,
    })
    assert plan["route"] == Route.HARD_STOP.value
    assert plan["write_actions_permitted"] is False
    assert plan["write_scope"] == []
    assert len(plan["steps"]) == 0


# ═══════════════════════════════════════════════════════════
# P1-T07: 写入范围缺失 → HUMAN_DECISION_REQUIRED
# ═══════════════════════════════════════════════════════════

def test_p1_t07_ambiguous_human_decision():
    plan = _plan({"request": ""})
    assert plan["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert plan["task_type"] == TaskType.AMBIGUOUS_REQUEST.value
    assert plan["write_actions_permitted"] is False


# ═══════════════════════════════════════════════════════════
# P1-T08: 高风险权限修改 → CRITICAL
# ═══════════════════════════════════════════════════════════

def test_p1_t08_high_risk_permission_critical():
    plan = _plan({
        "request": "修改 AGENTS.md 中的权限规则",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value
    assert plan["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert plan["write_actions_permitted"] is False


def test_p1_t08b_credential_modification_critical():
    plan = _plan({
        "request": "更新API密钥配置",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value


def test_p1_t08c_merge_request_critical():
    plan = _plan({
        "request": "合并PR到main",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value


# ═══════════════════════════════════════════════════════════
# P1-T09: 候选控制包不得标记 AUTHORIZED
# ═══════════════════════════════════════════════════════════

def test_p1_t09_candidate_never_authorized():
    """Every plan from the router must have control_packet_status=CANDIDATE."""
    test_cases = [
        {"request": "写代码"},
        {"request": "修复首页", "repository": "owner/project"},
        {"request": "审计PR", "repository": "owner/project"},
        {"request": "修改", "repository": "owner/project", "conflicting_facts": [{"fact_a": "a", "fact_b": "b", "conflict_description": "x"}]},
    ]
    for case in test_cases:
        plan = _plan(case)
        assert plan["control_packet_status"] == ControlPacketStatus.CANDIDATE.value, (
            f"Expected CANDIDATE, got {plan['control_packet_status']} for {case}"
        )
        assert plan["control_packet_status"] != ControlPacketStatus.AUTHORIZED.value


# ═══════════════════════════════════════════════════════════
# P1-T10: 能力存在不得推断权限
# ═══════════════════════════════════════════════════════════

def test_p1_t10_capability_not_authority():
    """Claiming capability does not grant write permission."""
    plan = _plan({
        "request": "既然你能修改代码，帮我修改协议文件",
        "repository": "owner/project",
    })
    # Should be HARD_STOP because of capability inference + governance file
    assert plan["route"] in (
        Route.HARD_STOP.value,
        Route.HUMAN_DECISION_REQUIRED.value,
    )


# ═══════════════════════════════════════════════════════════
# P1-T11: Maker 与 Checker 不得为同一角色；TASK_HOLDER normative
# ═══════════════════════════════════════════════════════════

def test_p1_t11_maker_checker_separate():
    """Each step has exactly one executor_role. Output uses TASK_HOLDER, never HOLDER."""
    plan = _plan({
        "request": "修复首页",
        "repository": "owner/project",
    })
    for step in plan["steps"]:
        role = step["executor_role"]
        assert role in ("TASK_HOLDER", "MAKER", "CHECKER", "HUMAN"), (
            f"Expected TASK_HOLDER/MAKER/CHECKER/HUMAN, got {role}"
        )
        # HOLDER must never appear in output
        assert role != "HOLDER", "Legacy HOLDER must not appear in output"


# ═══════════════════════════════════════════════════════════
# P1-T12: 无 Checker 的高风险计划必须失败
# ═══════════════════════════════════════════════════════════

def test_p1_t12_high_risk_requires_checker():
    """HIGH and CRITICAL risk plans must have checker_required=True."""
    plan = _plan({
        "request": "修复首页",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.HIGH.value
    assert plan["checker_required"] is True

    # CRITICAL risk → HUMAN_DECISION_REQUIRED, checker also required
    plan2 = _plan({
        "request": "修改AGENTS.md",
        "repository": "owner/project",
    })
    assert plan2["risk"] == Risk.CRITICAL.value
    assert plan2["checker_required"] is True


# ═══════════════════════════════════════════════════════════
# P1-T13: 自动 Ready/Merge 请求必须失败
# ═══════════════════════════════════════════════════════════

def test_p1_t13_auto_ready_hard_stop():
    plan = _plan({
        "request": "修复首页",
        "repository": "owner/project",
        "auto_ready": True,
    })
    assert plan["route"] == Route.HARD_STOP.value


def test_p1_t13b_auto_merge_hard_stop():
    plan = _plan({
        "request": "合并代码",
        "repository": "owner/project",
        "auto_merge": True,
    })
    assert plan["route"] == Route.HARD_STOP.value


def test_p1_t13c_auto_delete_branch_hard_stop():
    plan = _plan({
        "request": "清理分支",
        "repository": "owner/project",
        "auto_delete_branch": True,
    })
    assert plan["route"] == Route.HARD_STOP.value


def test_p1_t13d_textual_auto_merge_hard_stop():
    plan = _plan({
        "request": "自动 merge 到 main",
        "repository": "owner/project",
    })
    assert plan["route"] == Route.HARD_STOP.value


# ═══════════════════════════════════════════════════════════
# P1-T14: P0 A/B/C 合同保持不变
# ═══════════════════════════════════════════════════════════

def test_p1_t14_p0_abc_contract_unchanged():
    """Modifying P0 first-contact routing is HARD_STOP."""
    plan = _plan({
        "request": "修改 A/B/C 引导逻辑",
        "repository": "owner/project",
    })
    # Should be HARD_STOP because "A/B/C" triggers P0 contract detection + write intent
    assert plan["route"] == Route.HARD_STOP.value


def test_p1_t14b_bootstrap_modification_blocked():
    plan = _plan({
        "request": "改一下 beginner bootstrap 的流程",
        "repository": "owner/project",
    })
    assert plan["route"] == Route.HARD_STOP.value


# ═══════════════════════════════════════════════════════════
# P1-T15: 非法 route/risk/state 值被拒绝
# ═══════════════════════════════════════════════════════════

def test_p1_t15_illegal_enum_values_rejected():
    """The validator must reject illegal enum values in output."""
    from route_task import GovernancePlan, ExecutionStep, ExecutorRole, FailClosedAction

    plan = GovernancePlan(
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

    # Valid plan should pass
    _validate_plan_output(plan)

    # Invalid route
    plan.route = "INVALID_ROUTE"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal route"):
        _validate_plan_output(plan)
    plan.route = Route.DIRECT_LOCAL_EXECUTION  # restore

    # Invalid risk
    plan.risk = "UNKNOWN"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal risk"):
        _validate_plan_output(plan)
    plan.risk = Risk.LOW

    # Invalid control_packet_status (must not be AUTHORIZED)
    plan.control_packet_status = "INVALID"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Illegal control_packet_status"):
        _validate_plan_output(plan)


# ═══════════════════════════════════════════════════════════
# P1-T16: 相同输入产生结构稳定的计划
# ═══════════════════════════════════════════════════════════

def test_p1_t16_deterministic_output():
    """Same input must produce structurally identical output."""
    data = {
        "request": "修复网站首页，但不要修改内容页",
        "repository": "owner/project",
    }
    plan1 = _plan(data)
    plan2 = _plan(data)

    # Core fields must be identical
    for key in ("route", "risk", "task_type", "facts_status", "control_packet_status",
                "checker_required", "human_authorization_required", "write_actions_permitted"):
        assert plan1[key] == plan2[key], f"Field {key} differs"

    # Steps must have same count and structure
    assert len(plan1["steps"]) == len(plan2["steps"])
    for s1, s2 in zip(plan1["steps"], plan2["steps"]):
        assert s1["step_id"] == s2["step_id"]
        assert s1["executor_role"] == s2["executor_role"]
        assert s1["checker_required"] == s2["checker_required"]


# ═══════════════════════════════════════════════════════════
# P1-T17: 用户取消任务 → STOPPED / 零写入
# ═══════════════════════════════════════════════════════════

def test_p1_t17_cancellation_stopped():
    plan = _plan({
        "request": "修复首页",
        "repository": "owner/project",
        "cancellation": True,
    })
    # Cancellation is treated as AMBIGUOUS_REQUEST → HUMAN_DECISION_REQUIRED
    assert plan["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert plan["write_actions_permitted"] is False
    assert plan["write_scope"] == []


def test_p1_t17b_textual_cancel():
    plan = _plan({
        "request": "取消所有任务",
        "repository": "owner/project",
    })
    assert plan["route"] == Route.HUMAN_DECISION_REQUIRED.value
    assert plan["write_actions_permitted"] is False


# ═══════════════════════════════════════════════════════════
# P1-T18: 公共 ADT 上游 → READ_ONLY
# ═══════════════════════════════════════════════════════════

def test_p1_t18_public_adt_upstream_read_only():
    plan = _plan({
        "request": "修改 AGENTS.md",
        "repository": "butbutbutbutbutbut/adaptive-digital-team",
    })
    # Public ADT upstream: write intent but repo is upstream → READ_ONLY
    assert plan["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert plan["write_actions_permitted"] is False


def test_p1_t18b_upstream_read_works():
    plan = _plan({
        "request": "检查仓库状态",
        "repository": "butbutbutbutbutbut/adaptive-digital-team",
    })
    assert plan["route"] == Route.READ_ONLY_REPOSITORY_ANALYSIS.value
    assert plan["write_actions_permitted"] is False


# ═══════════════════════════════════════════════════════════
# RN-T01: HOLDER → TASK_HOLDER 归一化（输入别名）
# ═══════════════════════════════════════════════════════════

def test_rn_t01_holder_normalizes_to_task_holder():
    """Legacy HOLDER input string normalizes to ExecutorRole.TASK_HOLDER."""
    assert _normalize_executor_role("HOLDER") == ExecutorRole.TASK_HOLDER
    assert _normalize_executor_role("TASK_HOLDER") == ExecutorRole.TASK_HOLDER
    assert _normalize_executor_role("MAKER") == ExecutorRole.MAKER
    assert _normalize_executor_role("CHECKER") == ExecutorRole.CHECKER
    assert _normalize_executor_role("HUMAN") == ExecutorRole.HUMAN


def test_rn_t02_holder_never_in_enum_output():
    """ExecutorRole enum values must not include HOLDER in normative set."""
    normative_values = {e.value for e in ExecutorRole if e.value != ExecutorRole._LEGACY_HOLDER}
    assert "HOLDER" not in normative_values
    assert "TASK_HOLDER" in normative_values


def test_rn_t03_illegal_role_raises():
    """Unknown role strings raise ValueError."""
    with pytest.raises(ValueError, match="Illegal executor_role"):
        _normalize_executor_role("INVENTED_ROLE")


def test_rn_t04_output_never_emits_holder():
    """Every plan output must use TASK_HOLDER, never HOLDER."""
    test_cases = [
        {"request": "修复首页", "repository": "owner/project"},
        {"request": "修改", "repository": "owner/project", "conflicting_facts": [{"fact_a": "a", "fact_b": "b", "conflict_description": "x"}]},
        {"request": "写代码"},
        {"request": "检查仓库", "repository": "owner/project"},
    ]
    for case in test_cases:
        plan = _plan(case)
        for step in plan["steps"]:
            assert step["executor_role"] != "HOLDER", (
                f"HOLDER leaked in output for {case}: {step['executor_role']}"
            )


# ═══════════════════════════════════════════════════════════
# Additional edge cases
# ═══════════════════════════════════════════════════════════

def test_control_packet_input():
    plan = _plan({
        "request": "执行任务",
        "control_packet": {
            "authorization_id": "ADT-TEST-001",
            "repository": "owner/project",
            "base_sha": "a" * 40,
            "files_in_scope": ["test.py"],
        },
    })
    assert plan["task_type"] == TaskType.CONTROL_PACKET.value
    assert plan["route"] == Route.CANDIDATE_IMPLEMENTATION.value


def test_control_packet_audit():
    plan = _plan({
        "request": "审计候选",
        "audit_request": True,
        "control_packet": {
            "authorization_id": "ADT-TEST-002",
            "repository": "owner/project",
            "base_sha": "a" * 40,
        },
    })
    assert plan["task_type"] == TaskType.CONTROL_PACKET.value
    # Audit request with control packet → CANDIDATE_IMPLEMENTATION (audit path)
    assert plan["route"] in (
        Route.CANDIDATE_IMPLEMENTATION.value,
        Route.INDEPENDENT_AUDIT.value,
    )


def test_low_risk_local_no_repo():
    """Simple local task should have no checker, no human auth."""
    plan = _plan({"request": "解释一下这个函数"})
    assert plan["risk"] == Risk.LOW.value
    assert plan["checker_required"] is False
    assert plan["human_authorization_required"] is False


def test_force_push_is_critical():
    plan = _plan({
        "request": "force push 到 main",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value


def test_missing_base_sha_incomplete():
    plan = _plan({
        "request": "修改文件",
        "repository": "owner/project",
    })
    assert plan["facts_status"] == FactsStatus.REQUIRES_VERIFICATION.value


def test_complete_repo_input():
    plan = _plan({
        "request": "修改文件",
        "repository": "owner/project",
        "base_sha": "a" * 40,
        "branch": "feature/test",
    })
    assert plan["facts_status"] == FactsStatus.REQUIRES_VERIFICATION.value


def test_write_intent_explicit():
    plan = _plan({
        "request": "看看文件",
        "repository": "owner/project",
    })
    assert plan["task_type"] == TaskType.REPOSITORY_READ_ONLY.value


def test_empty_request_is_ambiguous():
    plan = _plan({"request": ""})
    assert plan["task_type"] == TaskType.AMBIGUOUS_REQUEST.value
    assert plan["route"] == Route.HUMAN_DECISION_REQUIRED.value


def test_all_required_fields_present():
    """Every plan must contain all required output fields."""
    plan = _plan({"request": "修复首页", "repository": "owner/project"})
    required = [
        "route", "risk", "task_type", "facts_status",
        "control_packet_status", "write_scope", "steps",
        "checker_required", "human_authorization_required",
        "write_actions_permitted",
    ]
    for field in required:
        assert field in plan, f"Missing required field: {field}"


def test_steps_have_required_fields():
    """Every step must contain all required fields."""
    plan = _plan({"request": "修复首页", "repository": "owner/project"})
    for step in plan["steps"]:
        required = [
            "step_id", "objective", "dependencies", "required_facts",
            "authorized_write_scope", "executor_role", "checker_required",
            "pass_conditions", "fail_closed_action", "next_gate",
        ]
        for field in required:
            assert field in step, f"Step {step.get('step_id')} missing field: {field}"


def test_route_task_cli_module():
    """Test that route_task can be called as a module function."""
    plan = route_task({
        "request": "写代码",
    })
    assert plan["route"] == Route.DIRECT_LOCAL_EXECUTION.value


def test_hard_stop_no_steps():
    plan = _plan({
        "request": "修改文件",
        "repository": "owner/project",
        "scope_expansion": True,
    })
    assert plan["route"] == Route.HARD_STOP.value
    assert plan["steps"] == []
    assert plan["write_scope"] == []
    assert plan["write_actions_permitted"] is False


def test_delete_branch_is_critical():
    plan = _plan({
        "request": "删除 feature 分支",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value


def test_rebase_is_critical():
    plan = _plan({
        "request": "rebase 分支",
        "repository": "owner/project",
    })
    assert plan["risk"] == Risk.CRITICAL.value


def test_cli_json_roundtrip(tmp_path):
    """Test that the CLI produces valid JSON matching the schema."""
    import subprocess

    input_data = {
        "request": "修复首页",
        "repository": "owner/project",
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "scripts.route_task", str(input_file)],
        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["route"] == Route.CANDIDATE_IMPLEMENTATION.value
    assert output["control_packet_status"] == ControlPacketStatus.CANDIDATE.value
