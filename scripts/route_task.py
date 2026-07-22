#!/usr/bin/env python3
"""ADT Dynamic Governance Router — P1.

Converts user input into a constrained, deterministic governance plan.
Generates Candidate Control Packets only. Never auto-authorizes execution.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ═══════════════════════════════════════════════════════════
# Frozen Enums
# ═══════════════════════════════════════════════════════════

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
    """Normative executor roles.

    TASK_HOLDER is the normative role.  The legacy value HOLDER is accepted
    as a backward-compatible input alias via `_normalize_executor_role` and
    immediately normalized to TASK_HOLDER.  Output must never emit HOLDER.
    """
    TASK_HOLDER = "TASK_HOLDER"
    MAKER = "MAKER"
    CHECKER = "CHECKER"
    HUMAN = "HUMAN"

    # Legacy alias — accepted on input only, never emitted.
    _LEGACY_HOLDER = "HOLDER"


class FailClosedAction(str, Enum):
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"
    HARD_STOP = "HARD_STOP"
    HUMAN = "HUMAN"


# ═══════════════════════════════════════════════════════════
# Role normalization
# ═══════════════════════════════════════════════════════════

def _normalize_executor_role(raw: str) -> ExecutorRole:
    """Normalize a raw role string to a valid ExecutorRole.

    ``HOLDER`` (legacy input alias) is mapped to ``TASK_HOLDER``.
    Unknown values raise ``ValueError``.
    """
    if raw == "HOLDER":
        return ExecutorRole.TASK_HOLDER
    try:
        return ExecutorRole(raw)
    except ValueError:
        raise ValueError(
            f"Illegal executor_role: {raw!r}. "
            f"Valid: TASK_HOLDER, MAKER, CHECKER, HUMAN"
        )


# ═══════════════════════════════════════════════════════════
# Governance keywords for intent detection
# ═══════════════════════════════════════════════════════════

GOVERNANCE_FILES = {
    "AGENTS.md", "BOOTSTRAP.md", "README.md", "PROJECT_STATE.md",
    "LICENSE", "CONTRIBUTING.md",
}

GOVERNANCE_DIRS = {
    "protocols/", ".github/workflows/", "schemas/",
}

PERMISSION_KEYWORDS = [
    "permission", "权限", "authority", "授权", "access", "访问",
    "role", "角色", "scope", "范围",
]

CREDENTIAL_KEYWORDS = [
    "secret", "密钥", "token", "令牌", "password", "密码",
    "credential", "凭据", "key", "env",
]

PUBLISH_KEYWORDS = [
    "ready", "merge", "合并", "push", "推送", "deploy", "部署",
    "release", "发布", "publish",
]

DELETE_BRANCH_INDICATORS = [
    ("delete", "branch"), ("删除", "分支"), ("remove", "branch"),
    ("清理", "分支"), ("clean", "branch"),
]

WRITE_KEYWORDS = [
    "修改", "修复", "fix", "添加", "add", "创建", "create",
    "删除", "delete", "更新", "update", "改", "写", "write",
    "实现", "implement", "开发", "build", "改一下", "改改",
    "commit", "提交", "push", "推送",
    "create pr", "开 pr", "新建 pr", "open pr", "submit pr",
    "merge", "合并", "deploy", "部署", "release", "发布",
    "force push", "rebase", "amend", "删除分支", "delete branch",
]

READ_KEYWORDS = [
    "查看", "检查", "分析", "审计", "review", "audit",
    "读", "read", "看", "look", "check", "inspect",
    "了解", "总结", "概括", "summarize",
]

AUTO_KEYWORDS = [
    "自动 ready", "auto ready", "自动 merge", "auto merge",
    "自动合并", "自动 ready", "自动删除分支", "auto delete branch",
]

CANCEL_KEYWORDS = [
    "取消", "cancel", "停止", "stop", "中止", "abort",
]

UPSTREAM_KEYWORDS = [
    "butbutbutbutbutbut/adaptive-digital-team",
    "adaptive-digital-team",
]

P0_CONTRACT_KEYWORDS = [
    "a/b/c", "first-contact", "bootstrap", "beginner bootstrap",
    "初学者引导", "模式选择",
]


# ═══════════════════════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════════════════════

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
            "dependencies": self.dependencies,
            "required_facts": self.required_facts,
            "authorized_write_scope": self.authorized_write_scope,
            "executor_role": self.executor_role.value,
            "checker_required": self.checker_required,
            "pass_conditions": self.pass_conditions,
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
    limitations: list[str] = field(default_factory=list)
    hard_stop_reason: str = ""
    authorization_id: str = ""
    task_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
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
            "limitations": list(self.limitations),
        }
        if self.hard_stop_reason:
            result["hard_stop_reason"] = self.hard_stop_reason
        if self.authorization_id:
            result["authorization_id"] = self.authorization_id
        if self.task_id:
            result["task_id"] = self.task_id
        return result


# ═══════════════════════════════════════════════════════════
# Router
# ═══════════════════════════════════════════════════════════

class GovernanceRouter:

    def __init__(self, intake: TaskIntake):
        self.intake = intake
        self._limitations: list[str] = []

    # ── Validation ────────────────────────────────────────

    def _validate_route(self, value: str) -> bool:
        return value in {r.value for r in Route}

    def _validate_risk(self, value: str) -> bool:
        return value in {r.value for r in Risk}

    def _validate_control_status(self, value: str) -> bool:
        return value in {
            ControlPacketStatus.CANDIDATE.value,
            ControlPacketStatus.NOT_AUTHORIZED.value,
        }

    # ── Task Type Classification ──────────────────────────

    def classify(self) -> TaskType:
        i = self.intake
        req = i.request.lower() if i.request else ""

        # Cancellation takes highest priority
        if i.cancellation or any(kw in req for kw in CANCEL_KEYWORDS):
            return TaskType.AMBIGUOUS_REQUEST

        # Control packet
        if i.control_packet and i.control_packet.get("authorization_id"):
            return TaskType.CONTROL_PACKET

        # Conflicting facts
        if i.conflicting_facts:
            return TaskType.CONFLICTING_FACTS

        # Repository-scoped
        has_repo = bool(i.repository)
        has_write = self._detect_write_intent()
        has_read = self._detect_read_intent()

        if has_repo:
            if has_write:
                return TaskType.REPOSITORY_CANDIDATE
            if has_read:
                return TaskType.REPOSITORY_READ_ONLY
            # Has repo reference but unclear intent
            return TaskType.REPOSITORY_READ_ONLY

        # No repository
        if i.attachments:
            return TaskType.PROMPT_LOCAL_WITH_FILES
        if req.strip():
            return TaskType.PROMPT_LOCAL

        return TaskType.AMBIGUOUS_REQUEST

    def _detect_write_intent(self) -> bool:
        i = self.intake
        if i.write_intent is True:
            return True
        req = i.request.lower() if i.request else ""
        return any(kw in req for kw in WRITE_KEYWORDS)

    def _detect_read_intent(self) -> bool:
        req = self.intake.request.lower() if self.intake.request else ""
        return any(kw in req for kw in READ_KEYWORDS)

    # ── Hard Stop Detection ───────────────────────────────

    def _detect_hard_stop(self) -> str | None:
        i = self.intake
        req = i.request.lower() if i.request else ""

        # Auto-Ready
        if i.auto_ready or "auto ready" in req or "自动 ready" in req:
            return "Auto-Ready is forbidden. HARD_STOP."

        # Auto-Merge
        if i.auto_merge or "auto merge" in req or "自动 merge" in req or "自动合并" in req:
            return "Auto-Merge is forbidden. HARD_STOP."

        # Auto-delete branch
        if i.auto_delete_branch or "auto delete branch" in req or "自动删除分支" in req:
            return "Auto-delete branch is forbidden. HARD_STOP."

        # Scope expansion
        if i.scope_expansion:
            return "SCOPE_EXPANSION_REQUIRED: scope expansion beyond authorization. HARD_STOP."

        # P0 contract modification
        if any(kw in req for kw in P0_CONTRACT_KEYWORDS):
            has_write = self._detect_write_intent()
            if has_write:
                return "P0 A/B/C first-contact contracts are frozen. Modification forbidden. HARD_STOP."

        # Capability-based authority inference attempt
        if "since you can" in req or "既然你能" in req or "you are capable" in req:
            if self._detect_write_intent():
                return "Authority must be explicitly granted, not inferred from capability. HARD_STOP."

        return None

    # ── Risk Assessment ───────────────────────────────────

    def assess_risk(self, task_type: TaskType) -> Risk:
        i = self.intake
        req = i.request.lower() if i.request else ""

        if task_type in (TaskType.PROMPT_LOCAL, TaskType.PROMPT_LOCAL_WITH_FILES):
            return Risk.LOW

        if task_type == TaskType.CONFLICTING_FACTS:
            return Risk.MODERATE

        if task_type in (TaskType.REPOSITORY_READ_ONLY, TaskType.AMBIGUOUS_REQUEST):
            return Risk.MODERATE

        if task_type == TaskType.REPOSITORY_CANDIDATE:
            return self._assess_candidate_risk(req)

        if task_type == TaskType.CONTROL_PACKET:
            return self._assess_control_packet_risk()

        return Risk.MODERATE

    def _assess_candidate_risk(self, req: str) -> Risk:
        i = self.intake

        # Check for CRITICAL indicators
        # 1. Governance files
        if any(gf.lower() in req for gf in GOVERNANCE_FILES):
            return Risk.CRITICAL
        if any(gd.lower() in req for gd in GOVERNANCE_DIRS):
            return Risk.CRITICAL

        # 2. Permission modification
        if any(kw in req for kw in PERMISSION_KEYWORDS):
            return Risk.CRITICAL

        # 3. Credentials
        if any(kw in req for kw in CREDENTIAL_KEYWORDS):
            return Risk.CRITICAL

        # 4. Publishing (Ready, Merge, push, deploy)
        if any(kw in req for kw in PUBLISH_KEYWORDS):
            return Risk.CRITICAL

        # 5. Branch deletion
        if any(a in req and b in req for a, b in DELETE_BRANCH_INDICATORS):
            return Risk.CRITICAL

        # 6. History mutation
        if "force push" in req or "rebase" in req or "amend" in req:
            return Risk.CRITICAL

        # 7. External systems
        if "deploy" in req or "webhook" in req or "api" in req:
            # Only CRITICAL if combined with publish intent
            if any(kw in req for kw in PUBLISH_KEYWORDS):
                return Risk.CRITICAL

        # 8. Repository write with scope → HIGH
        return Risk.HIGH

    def _assess_control_packet_risk(self) -> Risk:
        cp = self.intake.control_packet or {}
        actions = cp.get("actions_in_scope", [])
        action_str = " ".join(str(a).lower() for a in actions)

        if any(kw in action_str for kw in PUBLISH_KEYWORDS):
            return Risk.CRITICAL
        if any(kw in action_str for kw in CREDENTIAL_KEYWORDS):
            return Risk.CRITICAL
        if any(kw in action_str for kw in PERMISSION_KEYWORDS):
            return Risk.CRITICAL

        return Risk.HIGH

    # ── Route Determination ───────────────────────────────

    def determine_route(self, task_type: TaskType, risk: Risk) -> tuple[Route, str | None]:
        # Check hard stops first
        hard_stop = self._detect_hard_stop()
        if hard_stop:
            return Route.HARD_STOP, hard_stop

        # Check public ADT upstream read-only
        if self._is_public_adt_upstream_write(task_type):
            return Route.READ_ONLY_REPOSITORY_ANALYSIS, (
                "Public ADT upstream repository is read-only for external users. "
                "Write operations are not permitted."
            )

        # Check upstream write
        if task_type == TaskType.REPOSITORY_CANDIDATE and self._is_upstream_repo():
            self._limitations.append("Upstream public repository: read-only. Fork and submit PR from fork.")
            return Route.READ_ONLY_REPOSITORY_ANALYSIS, None

        # CONFLICTING_FACTS and AMBIGUOUS_REQUEST always map regardless of risk
        if task_type == TaskType.CONFLICTING_FACTS:
            return Route.FACT_SOURCE_REBIND, None
        if task_type == TaskType.AMBIGUOUS_REQUEST:
            return Route.HUMAN_DECISION_REQUIRED, None

        # Route table
        mapping = {
            (TaskType.PROMPT_LOCAL, Risk.LOW): Route.DIRECT_LOCAL_EXECUTION,
            (TaskType.PROMPT_LOCAL_WITH_FILES, Risk.LOW): Route.FILE_LOCAL_EXECUTION,
            (TaskType.REPOSITORY_READ_ONLY, Risk.MODERATE): Route.READ_ONLY_REPOSITORY_ANALYSIS,
            (TaskType.REPOSITORY_READ_ONLY, Risk.HIGH): Route.READ_ONLY_REPOSITORY_ANALYSIS,
            (TaskType.REPOSITORY_CANDIDATE, Risk.MODERATE): Route.CANDIDATE_IMPLEMENTATION,
            (TaskType.REPOSITORY_CANDIDATE, Risk.HIGH): Route.CANDIDATE_IMPLEMENTATION,
            (TaskType.REPOSITORY_CANDIDATE, Risk.CRITICAL): Route.HUMAN_DECISION_REQUIRED,
            (TaskType.CONTROL_PACKET, Risk.MODERATE): Route.CANDIDATE_IMPLEMENTATION,
            (TaskType.CONTROL_PACKET, Risk.HIGH): Route.CANDIDATE_IMPLEMENTATION,
            (TaskType.CONTROL_PACKET, Risk.CRITICAL): Route.HUMAN_DECISION_REQUIRED,
        }

        result = mapping.get((task_type, risk))
        if result:
            return result, None

        # Fallback
        return Route.HUMAN_DECISION_REQUIRED, (
            f"Unroutable combination: task_type={task_type.value}, risk={risk.value}"
        )

    def _is_upstream_repo(self) -> bool:
        repo = self.intake.repository.lower() if self.intake.repository else ""
        return any(up in repo for up in UPSTREAM_KEYWORDS)

    def _is_public_adt_upstream_write(self, task_type: TaskType) -> bool:
        """Block writes to public ADT upstream unless explicitly authorized."""
        if task_type not in (TaskType.REPOSITORY_CANDIDATE,):
            return False
        return self._is_upstream_repo()

    # ── Fact Status ───────────────────────────────────────

    def determine_facts_status(self, task_type: TaskType) -> FactsStatus:
        i = self.intake

        if task_type == TaskType.CONFLICTING_FACTS:
            return FactsStatus.CONFLICTING

        if task_type in (TaskType.REPOSITORY_CANDIDATE, TaskType.REPOSITORY_READ_ONLY):
            if not i.repository:
                return FactsStatus.INCOMPLETE
            if not i.base_sha:
                return FactsStatus.REQUIRES_VERIFICATION
            return FactsStatus.REQUIRES_VERIFICATION

        if task_type == TaskType.CONTROL_PACKET:
            cp = i.control_packet or {}
            if not cp.get("base_sha") or not cp.get("repository"):
                return FactsStatus.INCOMPLETE
            return FactsStatus.REQUIRES_VERIFICATION

        return FactsStatus.VERIFIED

    # ── Step Generation ───────────────────────────────────

    def generate_steps(
        self, task_type: TaskType, risk: Risk, route: Route
    ) -> list[ExecutionStep]:
        if route == Route.HARD_STOP:
            return []

        if route == Route.FACT_SOURCE_REBIND:
            return [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Re-verify facts from authoritative source (repository, not chat)",
                    dependencies=[],
                    required_facts=["repository", "base_sha", "branch", "open_prs"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.TASK_HOLDER,
                    checker_required=True,
                    pass_conditions=["All facts resolved from single authoritative source"],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="FACT_SOURCE_REBIND_RESOLVED_OR_HARD_STOP",
                )
            ]

        if route in (Route.DIRECT_LOCAL_EXECUTION, Route.FILE_LOCAL_EXECUTION):
            return [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Execute the requested task in the local session",
                    dependencies=[],
                    required_facts=[],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.MAKER,
                    checker_required=False,
                    pass_conditions=["Task output matches user request"],
                    fail_closed_action=FailClosedAction.RETRY,
                    next_gate="HUMAN_REVIEW",
                )
            ]

        if route == Route.READ_ONLY_REPOSITORY_ANALYSIS:
            return [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Fetch and read repository facts (read-only)",
                    dependencies=[],
                    required_facts=["repository", "base_sha", "branch"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.CHECKER,
                    checker_required=False,
                    pass_conditions=["Repository facts verified against live source"],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="HUMAN_REVIEW",
                )
            ]

        if route == Route.CANDIDATE_IMPLEMENTATION:
            steps = [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Verify repository facts (BASE_SHA, branch, open PRs)",
                    dependencies=[],
                    required_facts=["repository", "base_sha", "branch", "open_prs"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.TASK_HOLDER,
                    checker_required=True,
                    pass_conditions=["All facts verified against origin", "No conflicting facts"],
                    fail_closed_action=FailClosedAction.HARD_STOP,
                    next_gate="FACT_VERIFICATION_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-002",
                    objective="Create candidate branch from verified BASE_SHA",
                    dependencies=["STEP-001"],
                    required_facts=["verified_base_sha", "branch_name"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.MAKER,
                    checker_required=False,
                    pass_conditions=["Branch created from exact BASE_SHA", "Branch name follows convention"],
                    fail_closed_action=FailClosedAction.HARD_STOP,
                    next_gate="BRANCH_CREATION_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-003",
                    objective="Implement changes within authorized write scope",
                    dependencies=["STEP-002"],
                    required_facts=["authorized_write_scope", "task_requirements"],
                    authorized_write_scope=self._derive_write_scope(),
                    executor_role=ExecutorRole.MAKER,
                    checker_required=True,
                    pass_conditions=[
                        "All changes within authorized write scope",
                        "No files outside scope modified",
                        "Validation passes",
                    ],
                    fail_closed_action=FailClosedAction.ESCALATE,
                    next_gate="IMPLEMENTATION_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-004",
                    objective="Run local validation (tests, lint)",
                    dependencies=["STEP-003"],
                    required_facts=["test_suite_path"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.MAKER,
                    checker_required=True,
                    pass_conditions=["All existing tests pass", "New tests pass"],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="VALIDATION_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-005",
                    objective="Independent Checker audit",
                    dependencies=["STEP-004"],
                    required_facts=["diff", "scope", "validation_evidence"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.CHECKER,
                    checker_required=True,
                    pass_conditions=[
                        "All files within scope",
                        "Validation evidence verified",
                        "Maker-Checker independence confirmed",
                    ],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="AUDIT_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-006",
                    objective="Present candidate to Human Holder for authorization",
                    dependencies=["STEP-005"],
                    required_facts=["audit_decision", "candidate_fingerprint"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.HUMAN,
                    checker_required=False,
                    pass_conditions=["Human Holder explicitly authorizes Ready"],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="HUMAN_AUTHORIZATION_GATE",
                ),
            ]
            return steps

        if route == Route.HUMAN_DECISION_REQUIRED:
            return [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Present ambiguous or high-risk request to Human Holder",
                    dependencies=[],
                    required_facts=["task_type", "risk", "route"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.HUMAN,
                    checker_required=False,
                    pass_conditions=["Human Holder provides explicit direction"],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="HUMAN_DECISION_GATE",
                )
            ]

        if route == Route.INDEPENDENT_AUDIT:
            return [
                ExecutionStep(
                    step_id="STEP-001",
                    objective="Verify independence from Maker",
                    dependencies=[],
                    required_facts=["maker_identity", "checker_identity"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.CHECKER,
                    checker_required=False,
                    pass_conditions=["Checker confirmed independent from Maker"],
                    fail_closed_action=FailClosedAction.HARD_STOP,
                    next_gate="INDEPENDENCE_GATE",
                ),
                ExecutionStep(
                    step_id="STEP-002",
                    objective="Audit candidate against Dispatch Card",
                    dependencies=["STEP-001"],
                    required_facts=["dispatch_card", "diff", "validation_evidence"],
                    authorized_write_scope=[],
                    executor_role=ExecutorRole.CHECKER,
                    checker_required=True,
                    pass_conditions=[
                        "All checks pass",
                        "No scope violations",
                        "No publish violations",
                    ],
                    fail_closed_action=FailClosedAction.HUMAN,
                    next_gate="AUDIT_RESULT_GATE",
                ),
            ]

        return []

    def _derive_write_scope(self) -> list[str]:
        i = self.intake
        if i.control_packet:
            scope = i.control_packet.get("files_in_scope", [])
            return list(scope) if isinstance(scope, list) else []
        # For non-control-packet candidate tasks, scope is empty until authorized
        return []

    # ── Main Entry Point ──────────────────────────────────

    def route(self) -> GovernancePlan:
        task_type = self.classify()
        hard_stop = self._detect_hard_stop()
        risk = self.assess_risk(task_type)
        route, hs_reason = self.determine_route(task_type, risk)
        facts_status = self.determine_facts_status(task_type)

        # Hard stop from determine_route overrides
        if hs_reason and route == Route.HARD_STOP:
            hard_stop = hs_reason

        # Final hard stop reason (from detection or routing)
        final_hs = hard_stop if route == Route.HARD_STOP else ""

        # Determine if write is permitted
        write_permitted = route in (
            Route.CANDIDATE_IMPLEMENTATION,
        ) and risk not in (Risk.CRITICAL,)

        # Checker requirement
        checker_required = risk in (Risk.HIGH, Risk.CRITICAL) or route in (
            Route.CANDIDATE_IMPLEMENTATION,
            Route.INDEPENDENT_AUDIT,
        )

        # Human authorization required
        human_required = route in (
            Route.HUMAN_DECISION_REQUIRED,
            Route.CANDIDATE_IMPLEMENTATION,
            Route.FACT_SOURCE_REBIND,
        ) or risk == Risk.CRITICAL

        # Generate steps (empty for HARD_STOP)
        steps = self.generate_steps(task_type, risk, route)

        # Write scope
        write_scope = self._derive_write_scope()

        # Additional limitations
        if task_type == TaskType.AMBIGUOUS_REQUEST:
            self._limitations.append("Request intent is ambiguous. Human clarification required.")
        if not self.intake.base_sha and task_type in (
            TaskType.REPOSITORY_CANDIDATE, TaskType.REPOSITORY_READ_ONLY,
        ):
            self._limitations.append("BASE_SHA not provided. Must be verified from live repository before any write.")
        if risk == Risk.CRITICAL and route == Route.HUMAN_DECISION_REQUIRED:
            self._limitations.append("CRITICAL risk task requires explicit Human Holder authorization with exact scope.")
        if route == Route.FACT_SOURCE_REBIND:
            self._limitations.append("Conflicting facts detected. All writes prohibited until resolved.")

        # Control packet status — must NEVER be AUTHORIZED from router
        control_status = ControlPacketStatus.CANDIDATE

        return GovernancePlan(
            route=route,
            risk=risk,
            task_type=task_type,
            facts_status=facts_status,
            control_packet_status=control_status,
            write_scope=write_scope,
            steps=steps,
            checker_required=checker_required,
            human_authorization_required=human_required,
            write_actions_permitted=write_permitted,
            limitations=self._limitations,
            hard_stop_reason=final_hs or "",
        )


# ═══════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════

def parse_intake(data: dict[str, Any]) -> TaskIntake:
    """Parse raw dict into a validated TaskIntake."""
    return TaskIntake(
        request=str(data.get("request", "")),
        repository=str(data.get("repository", "")),
        attachments=list(data.get("attachments", []) or []),
        claimed_authority=str(data.get("claimed_authority", "")),
        base_sha=str(data.get("base_sha", "")),
        branch=str(data.get("branch", "")),
        control_packet=data.get("control_packet"),
        write_intent=data.get("write_intent"),
        audit_request=bool(data.get("audit_request", False)),
        cancellation=bool(data.get("cancellation", False)),
        auto_ready=bool(data.get("auto_ready", False)),
        auto_merge=bool(data.get("auto_merge", False)),
        auto_delete_branch=bool(data.get("auto_delete_branch", False)),
        scope_expansion=bool(data.get("scope_expansion", False)),
        conflicting_facts=list(data.get("conflicting_facts", []) or []),
    )


def route_task(intake_data: dict[str, Any]) -> dict[str, Any]:
    """Main entry point: classify → assess → route → decompose → output.

    Returns a candidate control packet as a dict. The control_packet_status
    is always CANDIDATE — this function never authorizes execution.
    """
    intake = parse_intake(intake_data)

    # Validate enum values in output (fail-closed on illegal values)
    router = GovernanceRouter(intake)
    plan = router.route()

    # P1-T09: Control packet must NEVER be AUTHORIZED
    assert plan.control_packet_status != ControlPacketStatus.AUTHORIZED, (
        "BUG: router generated AUTHORIZED status — this must never happen"
    )

    # P1-T15: Validate all output values are legal
    _validate_plan_output(plan)

    return plan.to_dict()


def _validate_plan_output(plan: GovernancePlan) -> None:
    """Fail-closed: validate that all output values are legal enum members."""
    valid_routes = {r.value for r in Route}
    valid_risks = {r.value for r in Risk}
    valid_task_types = {t.value for t in TaskType}
    valid_facts = {f.value for f in FactsStatus}
    valid_control = {ControlPacketStatus.CANDIDATE.value, ControlPacketStatus.NOT_AUTHORIZED.value}
    valid_executor_roles = {e.value for e in ExecutorRole if e.value != ExecutorRole._LEGACY_HOLDER}

    def _val(v: Any) -> str:
        return v.value if hasattr(v, 'value') else str(v)

    if _val(plan.route) not in valid_routes:
        raise ValueError(f"Illegal route: {_val(plan.route)}")
    if _val(plan.risk) not in valid_risks:
        raise ValueError(f"Illegal risk: {_val(plan.risk)}")
    if _val(plan.task_type) not in valid_task_types:
        raise ValueError(f"Illegal task_type: {_val(plan.task_type)}")
    if _val(plan.facts_status) not in valid_facts:
        raise ValueError(f"Illegal facts_status: {_val(plan.facts_status)}")
    if _val(plan.control_packet_status) not in valid_control:
        raise ValueError(f"Illegal control_packet_status: {_val(plan.control_packet_status)}")

    for step in plan.steps:
        role_val = _val(step.executor_role)
        if role_val not in valid_executor_roles:
            raise ValueError(f"Illegal executor_role: {role_val}")
        if _val(step.fail_closed_action) not in {f.value for f in FailClosedAction}:
            raise ValueError(f"Illegal fail_closed_action: {_val(step.fail_closed_action)}")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ADT Dynamic Governance Router — P1"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to JSON input file (reads from stdin if omitted)",
    )
    parser.add_argument(
        "--request", "-r",
        help="Inline request text (bypasses JSON input)",
    )
    parser.add_argument(
        "--repository",
        help="Repository in owner/project format",
    )
    parser.add_argument(
        "--base-sha",
        help="Base commit SHA",
    )
    args = parser.parse_args()

    if args.request:
        intake_data: dict[str, Any] = {
            "request": args.request,
            "repository": args.repository or "",
            "base_sha": args.base_sha or "",
        }
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            intake_data = json.load(f)
    else:
        intake_data = json.load(sys.stdin)

    plan = route_task(intake_data)
    json.dump(plan, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
