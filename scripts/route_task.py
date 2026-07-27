#!/usr/bin/env python3
"""ADT Dynamic Governance Router.

The router classifies intent, keeps safety risk separate from resource cost and
Checker timing, and emits a deterministic Candidate GovernancePlan. It never
authorizes execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    PROMPT_LOCAL = "PROMPT_LOCAL"
    PROMPT_LOCAL_WITH_FILES = "PROMPT_LOCAL_WITH_FILES"
    REPOSITORY_READ_ONLY = "REPOSITORY_READ_ONLY"
    REPOSITORY_CANDIDATE = "REPOSITORY_CANDIDATE"
    CONTROL_PACKET = "CONTROL_PACKET"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    CONFLICTING_FACTS = "CONFLICTING_FACTS"


class Risk(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Route(str, Enum):
    DIRECT_LOCAL_EXECUTION = "DIRECT_LOCAL_EXECUTION"
    FILE_LOCAL_EXECUTION = "FILE_LOCAL_EXECUTION"
    READ_ONLY_REPOSITORY_ANALYSIS = "READ_ONLY_REPOSITORY_ANALYSIS"
    CANDIDATE_IMPLEMENTATION = "CANDIDATE_IMPLEMENTATION"
    INDEPENDENT_AUDIT = "INDEPENDENT_AUDIT"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    FACT_SOURCE_REBIND = "FACT_SOURCE_REBIND"
    HARD_STOP = "HARD_STOP"


class ControlPacketStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    AUTHORIZED = "AUTHORIZED"


class FactsStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
    CONFLICTING = "CONFLICTING"
    INCOMPLETE = "INCOMPLETE"


class ExecutorRole(str, Enum):
    TASK_HOLDER = "TASK_HOLDER"
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    HUMAN = "HUMAN"
    _LEGACY_HOLDER = "HOLDER"


class FailClosedAction(str, Enum):
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"
    HARD_STOP = "HARD_STOP"
    HUMAN = "HUMAN"


class AntiReviewDecision(str, Enum):
    PROCEED = "PROCEED"
    DOWNSCOPE = "DOWNSCOPE"
    BLOCK = "BLOCK"


class ClaimStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    UNVERIFIED = "UNVERIFIED"


class ContinuityAction(str, Enum):
    NEW_TASK_START = "NEW_TASK_START"
    CONTINUE = "CONTINUE"
    RESTART = "RESTART"
    RESTART_REJECTED = "RESTART_REJECTED"


class ResourceTier(str, Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    STRONG = "strong"


class CheckerTiming(str, Enum):
    NONE = "NONE"
    AFTER_FORMAL_CANDIDATE = "AFTER_FORMAL_CANDIDATE"
    NOW = "NOW"


class StopCondition(str, Enum):
    TASK_COMPLETE = "TASK_COMPLETE"
    HUMAN_BOUNDARY_REACHED = "HUMAN_BOUNDARY_REACHED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    FACT_SOURCE_REBIND_REQUIRED = "FACT_SOURCE_REBIND_REQUIRED"
    JUSTIFIED_RESTART_REQUIRED = "JUSTIFIED_RESTART_REQUIRED"
    GOVERNANCE_COST_EXCEEDS_VALUE = "GOVERNANCE_COST_EXCEEDS_VALUE"
    HARD_STOP = "HARD_STOP"


def _normalize_executor_role(raw: str) -> ExecutorRole:
    if raw == "HOLDER":
        return ExecutorRole.TASK_HOLDER
    try:
        return ExecutorRole(raw)
    except ValueError as exc:
        raise ValueError(
            f"Illegal executor_role: {raw!r}. Valid: TASK_HOLDER, MAKER, CHECKER, HUMAN"
        ) from exc


GOVERNANCE_FILES = {
    "agents.md", "bootstrap.md", "methodology.md", "readme.md",
    "project_state.md", "license", "contributing.md",
}
GOVERNANCE_DIRS = ("protocols/", ".github/workflows/", "schemas/")
PERMISSION_KEYWORDS = ("permission", "权限", "authority", "授权", "access", "访问", "role", "角色")
CREDENTIAL_KEYWORDS = ("secret", "密钥", "token", "令牌", "password", "密码", "credential", "凭据")
PUBLISH_KEYWORDS = ("ready", "merge", "合并", "push", "推送", "deploy", "部署", "release", "发布", "publish")
WRITE_KEYWORDS = (
    "修改", "修复", "fix", "添加", "add", "创建", "create", "删除", "delete",
    "更新", "update", "改", "写", "write", "实现", "implement", "开发", "build",
    "commit", "提交", "push", "推送", "open pr", "create pr", "开 pr", "合并", "merge",
    "force push", "rebase", "amend",
)
READ_KEYWORDS = (
    "查看", "检查", "分析", "审计", "review", "audit", "读取", "读", "read",
    "看", "inspect", "总结", "summarize", "verify", "验证", "决定", "decide",
)
READ_ONLY_ACTIONS = {"READ", "ANALYZE", "DECIDE", "REVIEW", "AUDIT", "VERIFY", "SUMMARIZE"}
WRITE_ACTIONS = {"WRITE", "MODIFY", "FIX", "CREATE", "DELETE", "COMMIT", "PUSH", "OPEN_PR", "IMPLEMENT"}
CONTROL_PACKET_REQUIRED_FIELDS = {
    "authorization_id", "from", "to", "executor", "repository", "base_sha"
}
CANCEL_KEYWORDS = ("取消", "cancel", "停止", "stop", "中止", "abort")
P0_CONTRACT_KEYWORDS = ("a/b/c", "first-contact", "beginner bootstrap", "初学者引导", "模式选择")
UPSTREAM_KEYWORDS = ("butbutbutbutbutbut/adaptive-digital-team", "adaptive-digital-team")
VALID_RESTART_REASONS = {
    "ROLE_ISOLATION", "FACT_SOURCE_INVALID", "CONTEXT_CONTAMINATION", "HUMAN_EXPLICIT_REQUEST"
}


@dataclass
class TaskIntake:
    request: str = ""
    repository: str = ""
    attachments: list[str] = field(default_factory=list)
    claimed_authority: str = ""
    base_sha: str = ""
    branch: str = ""
    control_packet: dict[str, Any] | None = None
    write_intent: bool | None = None
    audit_request: bool = False
    cancellation: bool = False
    auto_ready: bool = False
    auto_merge: bool = False
    auto_delete_branch: bool = False
    scope_expansion: bool = False
    conflicting_facts: list[dict[str, str]] = field(default_factory=list)
    requested_actions: list[str] = field(default_factory=list)
    task_id: str = ""
    active_task_id: str = ""
    restart_requested: bool = False
    restart_reason: str = ""
    human_premise: dict[str, Any] | None = None
    human_friction_signal: bool = False
    latest_authorized_scope: list[str] = field(default_factory=list)
    estimated_task_value: int = 1
    estimated_governance_cost: int = 1
    requested_resource_tier: str = ""
    recommended_points: int | None = None
    hard_max_points: int = 2
    max_external_messages: int = 3
    candidate_stage: str = "LOCAL_PRODUCTION"


@dataclass
class ExecutionStep:
    step_id: str
    objective: str
    dependencies: list[str]
    required_facts: list[str]
    authorized_write_scope: list[str]
    executor_role: ExecutorRole
    checker_required: bool
    pass_conditions: list[str]
    fail_closed_action: FailClosedAction
    next_gate: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "objective": self.objective,
            "dependencies": list(self.dependencies),
            "required_facts": list(self.required_facts),
            "authorized_write_scope": list(self.authorized_write_scope),
            "executor_role": self.executor_role.value,
            "checker_required": self.checker_required,
            "pass_conditions": list(self.pass_conditions),
            "fail_closed_action": self.fail_closed_action.value,
            "next_gate": self.next_gate,
        }


@dataclass
class GovernancePlan:
    route: Route
    risk: Risk
    task_type: TaskType
    facts_status: FactsStatus
    control_packet_status: ControlPacketStatus
    write_scope: list[str]
    steps: list[ExecutionStep]
    checker_required: bool
    human_authorization_required: bool
    write_actions_permitted: bool
    anti_review_decision: AntiReviewDecision = AntiReviewDecision.PROCEED
    claim_status: ClaimStatus = ClaimStatus.UNVERIFIED
    continuity_action: ContinuityAction = ContinuityAction.NEW_TASK_START
    recommended_points: int = 0
    hard_max_points: int = 2
    resource_tier: ResourceTier = ResourceTier.ECONOMY
    checker_timing: CheckerTiming = CheckerTiming.NONE
    max_external_messages: int = 3
    stop_condition: StopCondition = StopCondition.TASK_COMPLETE
    limitations: list[str] = field(default_factory=list)
    hard_stop_reason: str = ""
    authorization_id: str = ""
    task_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = {
            "route": self.route.value,
            "risk": self.risk.value,
            "task_type": self.task_type.value,
            "facts_status": self.facts_status.value,
            "control_packet_status": self.control_packet_status.value,
            "write_scope": list(self.write_scope),
            "steps": [s.to_dict() for s in self.steps],
            "checker_required": self.checker_required,
            "human_authorization_required": self.human_authorization_required,
            "write_actions_permitted": self.write_actions_permitted,
            "anti_review_decision": self.anti_review_decision.value,
            "claim_status": self.claim_status.value,
            "continuity_action": self.continuity_action.value,
            "recommended_points": self.recommended_points,
            "hard_max_points": self.hard_max_points,
            "resource_tier": self.resource_tier.value,
            "checker_timing": self.checker_timing.value,
            "max_external_messages": self.max_external_messages,
            "stop_condition": self.stop_condition.value,
            "limitations": list(self.limitations),
        }
        if self.hard_stop_reason:
            result["hard_stop_reason"] = self.hard_stop_reason
        if self.authorization_id:
            result["authorization_id"] = self.authorization_id
        if self.task_id:
            result["task_id"] = self.task_id
        return result


class GovernanceRouter:
    def __init__(self, intake: TaskIntake):
        self.intake = intake
        self._limitations: list[str] = []

    def _requested_action_set(self) -> set[str]:
        return {str(action).upper() for action in self.intake.requested_actions if str(action)}

    def _control_packet_action_set(self) -> set[str]:
        packet = self.intake.control_packet or {}
        actions = packet.get("actions_in_scope", [])
        if not isinstance(actions, list):
            return set()
        return {str(action).upper() for action in actions if str(action)}

    def _control_packet_complete(self) -> bool:
        packet = self.intake.control_packet
        if not isinstance(packet, dict):
            return False
        return all(isinstance(packet.get(field), str) and packet.get(field).strip() for field in CONTROL_PACKET_REQUIRED_FIELDS)

    def _pure_read_only_actions(self) -> bool:
        actions = self._requested_action_set()
        return bool(actions) and actions <= READ_ONLY_ACTIONS

    def _control_packet_is_read_only(self) -> bool:
        if self.intake.audit_request or self._pure_read_only_actions():
            return True
        requested = self._requested_action_set()
        packet_actions = self._control_packet_action_set()
        effective = requested or packet_actions
        if effective:
            return effective <= READ_ONLY_ACTIONS
        return self._detect_read_intent() and not self._detect_write_intent()

    def _control_packet_has_explicit_write(self) -> bool:
        if self.intake.audit_request or self._pure_read_only_actions():
            return False
        actions = self._requested_action_set() | self._control_packet_action_set()
        if actions & WRITE_ACTIONS:
            return True
        return self._detect_write_intent()

    def _detect_write_intent(self) -> bool:
        if self.intake.audit_request or self._pure_read_only_actions():
            return False
        if self.intake.write_intent is not None:
            return bool(self.intake.write_intent)
        actions = self._requested_action_set() | self._control_packet_action_set()
        if actions:
            if actions <= READ_ONLY_ACTIONS:
                return False
            if actions & WRITE_ACTIONS:
                return True
        req = self.intake.request.lower()
        read_prefix = any(marker in req for marker in ("只读", "读取 bug", "读取bug", "分析 bug", "分析bug", "read bug", "review bug"))
        if read_prefix and not any(marker in req for marker in ("并修复", "直接修复", "implement the fix", "apply the fix")):
            return False
        return any(kw in req for kw in WRITE_KEYWORDS)

    def _detect_read_intent(self) -> bool:
        actions = self._requested_action_set() | self._control_packet_action_set()
        return bool(actions & READ_ONLY_ACTIONS) or any(kw in self.intake.request.lower() for kw in READ_KEYWORDS)

    def classify(self) -> TaskType:
        i = self.intake
        req = i.request.lower()
        if i.cancellation or any(kw in req for kw in CANCEL_KEYWORDS):
            return TaskType.AMBIGUOUS_REQUEST
        if isinstance(i.control_packet, dict):
            return TaskType.CONTROL_PACKET
        if i.conflicting_facts:
            return TaskType.CONFLICTING_FACTS
        if i.repository:
            return TaskType.REPOSITORY_CANDIDATE if self._detect_write_intent() else TaskType.REPOSITORY_READ_ONLY
        if i.attachments:
            return TaskType.PROMPT_LOCAL_WITH_FILES
        if req.strip():
            return TaskType.PROMPT_LOCAL
        return TaskType.AMBIGUOUS_REQUEST

    def _detect_hard_stop(self) -> str | None:
        i = self.intake
        req = i.request.lower()
        if i.auto_ready or "auto ready" in req or "自动 ready" in req:
            return "Auto-Ready is forbidden. HARD_STOP."
        if i.auto_merge or "auto merge" in req or "自动 merge" in req or "自动合并" in req:
            return "Auto-Merge is forbidden. HARD_STOP."
        if i.auto_delete_branch or "auto delete branch" in req or "自动删除分支" in req:
            return "Auto-delete branch is forbidden. HARD_STOP."
        if i.scope_expansion:
            return "SCOPE_EXPANSION_REQUIRED: scope expansion beyond authorization. HARD_STOP."
        if any(kw in req for kw in P0_CONTRACT_KEYWORDS) and self._detect_write_intent():
            return "P0 A/B/C first-contact contracts are frozen. Modification forbidden. HARD_STOP."
        if ("since you can" in req or "既然你能" in req or "you are capable" in req) and self._detect_write_intent():
            return "Authority must be explicitly granted, not inferred from capability. HARD_STOP."
        return None

    def assess_risk(self, task_type: TaskType) -> Risk:
        req = self.intake.request.lower()
        if task_type in (TaskType.PROMPT_LOCAL, TaskType.PROMPT_LOCAL_WITH_FILES):
            return Risk.LOW
        if task_type in (TaskType.CONFLICTING_FACTS, TaskType.REPOSITORY_READ_ONLY, TaskType.AMBIGUOUS_REQUEST):
            return Risk.MODERATE
        if task_type == TaskType.CONTROL_PACKET:
            if not self._control_packet_complete() or self._control_packet_is_read_only():
                return Risk.MODERATE
            actions = " ".join(str(a).lower() for a in self._control_packet_action_set())
            req = f"{req} {actions}"
        if any(name in req for name in GOVERNANCE_FILES) or any(path in req for path in GOVERNANCE_DIRS):
            return Risk.CRITICAL
        if any(kw in req for kw in PERMISSION_KEYWORDS + CREDENTIAL_KEYWORDS + PUBLISH_KEYWORDS):
            return Risk.CRITICAL
        if any(x in req for x in ("force push", "rebase", "amend")):
            return Risk.CRITICAL
        if ("删除" in req and "分支" in req) or ("delete" in req and "branch" in req):
            return Risk.CRITICAL
        return Risk.HIGH

    def _is_upstream_repo(self) -> bool:
        repository = self.intake.repository or str((self.intake.control_packet or {}).get("repository", ""))
        return any(up in repository.lower() for up in UPSTREAM_KEYWORDS)

    def determine_route(self, task_type: TaskType, risk: Risk) -> tuple[Route, str | None]:
        hard_stop = self._detect_hard_stop()
        if hard_stop:
            return Route.HARD_STOP, hard_stop
        if task_type == TaskType.CONTROL_PACKET:
            if not self._control_packet_complete():
                self._limitations.append("Control Packet incomplete: authorization_id/from/to/executor/repository/base_sha are required.")
                return Route.HUMAN_DECISION_REQUIRED, None
            if self.intake.audit_request:
                return Route.INDEPENDENT_AUDIT, None
            if self._control_packet_is_read_only():
                return Route.READ_ONLY_REPOSITORY_ANALYSIS, None
            if not self._control_packet_has_explicit_write():
                self._limitations.append("Control Packet has no explicit write or implementation action.")
                return Route.HUMAN_DECISION_REQUIRED, None
            if risk == Risk.CRITICAL:
                return Route.HUMAN_DECISION_REQUIRED, None
            return Route.CANDIDATE_IMPLEMENTATION, None
        if task_type == TaskType.REPOSITORY_CANDIDATE and self._is_upstream_repo():
            self._limitations.append("Upstream public repository: read-only without separate verified authorization.")
            return Route.READ_ONLY_REPOSITORY_ANALYSIS, None
        if task_type == TaskType.CONFLICTING_FACTS:
            return Route.FACT_SOURCE_REBIND, None
        if task_type == TaskType.AMBIGUOUS_REQUEST:
            return Route.HUMAN_DECISION_REQUIRED, None
        if task_type == TaskType.PROMPT_LOCAL:
            return Route.DIRECT_LOCAL_EXECUTION, None
        if task_type == TaskType.PROMPT_LOCAL_WITH_FILES:
            return Route.FILE_LOCAL_EXECUTION, None
        if task_type == TaskType.REPOSITORY_READ_ONLY:
            return Route.READ_ONLY_REPOSITORY_ANALYSIS, None
        if task_type == TaskType.REPOSITORY_CANDIDATE:
            if risk == Risk.CRITICAL:
                return Route.HUMAN_DECISION_REQUIRED, None
            return Route.CANDIDATE_IMPLEMENTATION, None
        return Route.HUMAN_DECISION_REQUIRED, f"Unroutable combination: {task_type.value}/{risk.value}"

    def determine_facts_status(self, task_type: TaskType) -> FactsStatus:
        if task_type == TaskType.CONFLICTING_FACTS:
            return FactsStatus.CONFLICTING
        if task_type in (TaskType.REPOSITORY_CANDIDATE, TaskType.REPOSITORY_READ_ONLY):
            return FactsStatus.REQUIRES_VERIFICATION if self.intake.repository else FactsStatus.INCOMPLETE
        if task_type == TaskType.CONTROL_PACKET:
            return FactsStatus.REQUIRES_VERIFICATION if self._control_packet_complete() else FactsStatus.INCOMPLETE
        return FactsStatus.VERIFIED

    def determine_claim_status(self) -> ClaimStatus:
        premise = self.intake.human_premise or {}
        supported = list(premise.get("supported_parts", []) or [])
        rejected = list(premise.get("rejected_parts", []) or [])
        unverifiable = list(premise.get("unverifiable_parts", []) or [])
        if supported and (rejected or unverifiable):
            return ClaimStatus.PARTIAL
        if rejected and not supported:
            return ClaimStatus.REJECTED
        if supported and not rejected and not unverifiable:
            return ClaimStatus.SUPPORTED
        return ClaimStatus.UNVERIFIED

    def determine_continuity(self) -> ContinuityAction:
        intake = self.intake
        if intake.restart_requested:
            return ContinuityAction.RESTART if intake.restart_reason in VALID_RESTART_REASONS else ContinuityAction.RESTART_REJECTED
        if intake.task_id and intake.active_task_id and intake.task_id == intake.active_task_id:
            return ContinuityAction.CONTINUE
        return ContinuityAction.NEW_TASK_START

    def _derive_write_scope(self) -> list[str]:
        if self.intake.human_friction_signal and self.intake.latest_authorized_scope:
            return list(self.intake.latest_authorized_scope)
        packet = self.intake.control_packet or {}
        scope = packet.get("files_in_scope", [])
        return list(scope) if isinstance(scope, list) else []

    def determine_resource_tier(self, risk: Risk) -> ResourceTier:
        requested = self.intake.requested_resource_tier
        if requested in {tier.value for tier in ResourceTier}:
            return ResourceTier(requested)
        if risk == Risk.LOW:
            return ResourceTier.ECONOMY
        if risk == Risk.CRITICAL:
            return ResourceTier.STRONG
        return ResourceTier.STANDARD

    def determine_checker_timing(self, route: Route) -> CheckerTiming:
        if route == Route.INDEPENDENT_AUDIT:
            return CheckerTiming.NOW
        if route != Route.CANDIDATE_IMPLEMENTATION:
            return CheckerTiming.NONE
        return CheckerTiming.NOW if self.intake.candidate_stage == "FORMAL_CANDIDATE" else CheckerTiming.AFTER_FORMAL_CANDIDATE

    def determine_anti_review(self) -> AntiReviewDecision:
        if self._detect_hard_stop():
            return AntiReviewDecision.BLOCK
        if self.intake.estimated_governance_cost > self.intake.estimated_task_value:
            return AntiReviewDecision.DOWNSCOPE
        return AntiReviewDecision.PROCEED

    def generate_steps(self, task_type: TaskType, risk: Risk, route: Route, checker_timing: CheckerTiming) -> list[ExecutionStep]:
        del task_type, risk
        if route == Route.HARD_STOP:
            return []
        if route == Route.FACT_SOURCE_REBIND:
            return [ExecutionStep("STEP-001", "Re-verify facts from the authoritative repository source", [], ["repository", "base_sha", "branch", "open_prs"], [], ExecutorRole.TASK_HOLDER, False, ["Facts resolve from one authoritative source"], FailClosedAction.HUMAN, "FACT_SOURCE_REBIND_RESOLVED_OR_HARD_STOP")]
        if route in (Route.DIRECT_LOCAL_EXECUTION, Route.FILE_LOCAL_EXECUTION):
            return [ExecutionStep("STEP-001", "Execute the bounded local request", [], [], [], ExecutorRole.MAKER, False, ["Output matches the request without scope expansion"], FailClosedAction.RETRY, "HUMAN_REVIEW")]
        if route == Route.INDEPENDENT_AUDIT:
            return [ExecutionStep("STEP-001", "Independently audit the authorized candidate using read-only evidence", [], ["authorization_id", "repository", "base_sha", "candidate_state", "role_independence"], [], ExecutorRole.CHECKER, True, ["Facts verified from authoritative sources", "No write or implementation action performed"], FailClosedAction.HUMAN, "AUDIT_GATE")]
        if route == Route.READ_ONLY_REPOSITORY_ANALYSIS:
            return [ExecutionStep("STEP-001", "Read and analyze repository facts without writes", [], ["repository", "base_sha", "branch"], [], ExecutorRole.CHECKER, False, ["Facts verified against live source", "No repair task created"], FailClosedAction.HUMAN, "HUMAN_REVIEW")]
        if route == Route.CANDIDATE_IMPLEMENTATION:
            checker_now = checker_timing == CheckerTiming.NOW
            steps = [
                ExecutionStep("STEP-001", "Verify repository facts", [], ["repository", "base_sha", "branch", "open_prs"], [], ExecutorRole.TASK_HOLDER, False, ["Facts verified", "No conflicting facts"], FailClosedAction.HARD_STOP, "FACT_VERIFICATION_GATE"),
                ExecutionStep("STEP-002", "Continue or create the authorized candidate branch", ["STEP-001"], ["continuity_action", "verified_base_sha", "branch_name"], [], ExecutorRole.MAKER, False, ["Same task continues by default", "Restart has a valid reason"], FailClosedAction.HARD_STOP, "BRANCH_CREATION_GATE"),
                ExecutionStep("STEP-003", "Implement only the authorized scope", ["STEP-002"], ["authorized_write_scope", "task_requirements"], self._derive_write_scope(), ExecutorRole.MAKER, False, ["No scope expansion", "Validation passes"], FailClosedAction.ESCALATE, "IMPLEMENTATION_GATE"),
                ExecutionStep("STEP-004", "Run local validation", ["STEP-003"], ["test_suite_path"], [], ExecutorRole.MAKER, False, ["Existing and new tests pass"], FailClosedAction.HUMAN, "FORMAL_CANDIDATE_GATE"),
            ]
            if checker_now:
                steps.append(ExecutionStep("STEP-005", "Independent Checker audit of the formal candidate", ["STEP-004"], ["diff", "scope", "validation_evidence"], [], ExecutorRole.CHECKER, True, ["Scope and evidence verified", "Independence confirmed"], FailClosedAction.HUMAN, "AUDIT_GATE"))
            return steps
        return [ExecutionStep("STEP-001", "Present the bounded decision to the Human Holder", [], ["task_type", "risk", "route"], [], ExecutorRole.HUMAN, False, ["Human direction received"], FailClosedAction.HUMAN, "HUMAN_DECISION_GATE")]

    def route(self) -> GovernancePlan:
        task_type = self.classify()
        risk = self.assess_risk(task_type)
        route, hard_stop_reason = self.determine_route(task_type, risk)
        facts_status = self.determine_facts_status(task_type)
        claim_status = self.determine_claim_status()
        continuity = self.determine_continuity()
        anti_review = self.determine_anti_review()
        resource_tier = self.determine_resource_tier(risk)
        checker_timing = self.determine_checker_timing(route)

        write_permitted = route == Route.CANDIDATE_IMPLEMENTATION and risk != Risk.CRITICAL
        checker_required = route == Route.INDEPENDENT_AUDIT or risk in (Risk.HIGH, Risk.CRITICAL) or route == Route.CANDIDATE_IMPLEMENTATION
        human_required = route in (Route.HUMAN_DECISION_REQUIRED, Route.CANDIDATE_IMPLEMENTATION, Route.FACT_SOURCE_REBIND) or risk == Risk.CRITICAL
        write_scope = self._derive_write_scope() if write_permitted else []

        recommended = self.intake.recommended_points
        if recommended is None:
            recommended = 0 if route in (Route.DIRECT_LOCAL_EXECUTION, Route.FILE_LOCAL_EXECUTION, Route.READ_ONLY_REPOSITORY_ANALYSIS) else 1
        recommended = max(0, min(int(recommended), 2))
        hard_max = max(0, min(int(self.intake.hard_max_points), 2))
        max_messages = max(0, min(int(self.intake.max_external_messages), 10))

        if anti_review == AntiReviewDecision.DOWNSCOPE:
            recommended = min(recommended, 1)
            max_messages = min(max_messages, 1)
            self._limitations.append("Governance cost exceeds task value; use the smallest safe path.")
        if continuity == ContinuityAction.RESTART_REJECTED:
            self._limitations.append("Restart rejected: no valid role, fact-source, context, or explicit Human reason.")
        if self.intake.human_friction_signal:
            max_messages = min(max_messages, 1)
            self._limitations.append("Human friction signal: shorten output and restore the latest explicit scope.")
        if not self.intake.base_sha and task_type in (TaskType.REPOSITORY_CANDIDATE, TaskType.REPOSITORY_READ_ONLY):
            self._limitations.append("BASE_SHA must be verified before write.")

        if route == Route.HARD_STOP:
            stop = StopCondition.HARD_STOP
        elif route == Route.FACT_SOURCE_REBIND:
            stop = StopCondition.FACT_SOURCE_REBIND_REQUIRED
        elif anti_review == AntiReviewDecision.DOWNSCOPE:
            stop = StopCondition.GOVERNANCE_COST_EXCEEDS_VALUE
        elif continuity == ContinuityAction.RESTART_REJECTED:
            stop = StopCondition.JUSTIFIED_RESTART_REQUIRED
        elif human_required:
            stop = StopCondition.AUTHORIZATION_REQUIRED
        else:
            stop = StopCondition.TASK_COMPLETE

        return GovernancePlan(
            route=route,
            risk=risk,
            task_type=task_type,
            facts_status=facts_status,
            control_packet_status=ControlPacketStatus.CANDIDATE,
            write_scope=write_scope,
            steps=self.generate_steps(task_type, risk, route, checker_timing),
            checker_required=checker_required,
            human_authorization_required=human_required,
            write_actions_permitted=write_permitted,
            anti_review_decision=anti_review,
            claim_status=claim_status,
            continuity_action=continuity,
            recommended_points=recommended,
            hard_max_points=hard_max,
            resource_tier=resource_tier,
            checker_timing=checker_timing,
            max_external_messages=max_messages,
            stop_condition=stop,
            limitations=self._limitations,
            hard_stop_reason=hard_stop_reason or "",
            authorization_id=str((self.intake.control_packet or {}).get("authorization_id", "")),
            task_id=self.intake.task_id,
        )


def parse_intake(data: dict[str, Any]) -> TaskIntake:
    return TaskIntake(
        request=str(data.get("request", "")), repository=str(data.get("repository", "")),
        attachments=list(data.get("attachments", []) or []), claimed_authority=str(data.get("claimed_authority", "")),
        base_sha=str(data.get("base_sha", "")), branch=str(data.get("branch", "")), control_packet=data.get("control_packet"),
        write_intent=data.get("write_intent"), audit_request=bool(data.get("audit_request", False)), cancellation=bool(data.get("cancellation", False)),
        auto_ready=bool(data.get("auto_ready", False)), auto_merge=bool(data.get("auto_merge", False)), auto_delete_branch=bool(data.get("auto_delete_branch", False)),
        scope_expansion=bool(data.get("scope_expansion", False)), conflicting_facts=list(data.get("conflicting_facts", []) or []),
        requested_actions=list(data.get("requested_actions", []) or []), task_id=str(data.get("task_id", "")), active_task_id=str(data.get("active_task_id", "")),
        restart_requested=bool(data.get("restart_requested", False)), restart_reason=str(data.get("restart_reason", "")), human_premise=data.get("human_premise"),
        human_friction_signal=bool(data.get("human_friction_signal", False)), latest_authorized_scope=list(data.get("latest_authorized_scope", []) or []),
        estimated_task_value=int(data.get("estimated_task_value", 1)), estimated_governance_cost=int(data.get("estimated_governance_cost", 1)),
        requested_resource_tier=str(data.get("requested_resource_tier", "")), recommended_points=data.get("recommended_points"),
        hard_max_points=int(data.get("hard_max_points", 2)), max_external_messages=int(data.get("max_external_messages", 3)),
        candidate_stage=str(data.get("candidate_stage", "LOCAL_PRODUCTION")),
    )


def _validate_plan_output(plan: GovernancePlan) -> None:
    def val(value: Any) -> str:
        return value.value if hasattr(value, "value") else str(value)

    enum_checks = [
        (plan.route, Route, "route"), (plan.risk, Risk, "risk"), (plan.task_type, TaskType, "task_type"),
        (plan.facts_status, FactsStatus, "facts_status"), (plan.anti_review_decision, AntiReviewDecision, "anti_review_decision"),
        (plan.claim_status, ClaimStatus, "claim_status"), (plan.continuity_action, ContinuityAction, "continuity_action"),
        (plan.resource_tier, ResourceTier, "resource_tier"), (plan.checker_timing, CheckerTiming, "checker_timing"),
        (plan.stop_condition, StopCondition, "stop_condition"),
    ]
    for value, enum_cls, name in enum_checks:
        if val(value) not in {item.value for item in enum_cls}:
            raise ValueError(f"Illegal {name}: {val(value)}")
    if val(plan.control_packet_status) not in {ControlPacketStatus.CANDIDATE.value, ControlPacketStatus.NOT_AUTHORIZED.value}:
        raise ValueError(f"Illegal control_packet_status: {val(plan.control_packet_status)}")
    if not (0 <= plan.recommended_points <= plan.hard_max_points <= 2):
        raise ValueError("Illegal point boundary")
    for step in plan.steps:
        if val(step.executor_role) not in {"TASK_HOLDER", "MAKER", "CHECKER", "HUMAN"}:
            raise ValueError(f"Illegal executor_role: {val(step.executor_role)}")
        if val(step.fail_closed_action) not in {item.value for item in FailClosedAction}:
            raise ValueError(f"Illegal fail_closed_action: {val(step.fail_closed_action)}")


def route_task(intake_data: dict[str, Any]) -> dict[str, Any]:
    plan = GovernanceRouter(parse_intake(intake_data)).route()
    assert plan.control_packet_status != ControlPacketStatus.AUTHORIZED
    _validate_plan_output(plan)
    return plan.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="ADT Dynamic Governance Router")
    parser.add_argument("input", nargs="?")
    parser.add_argument("--request", "-r")
    parser.add_argument("--repository")
    parser.add_argument("--base-sha")
    args = parser.parse_args()
    if args.request:
        data = {"request": args.request, "repository": args.repository or "", "base_sha": args.base_sha or ""}
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        data = json.load(sys.stdin)
    json.dump(route_task(data), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
