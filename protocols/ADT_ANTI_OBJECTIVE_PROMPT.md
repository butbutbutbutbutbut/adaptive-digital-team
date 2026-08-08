> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# ADT Anti-Objective Prompt Protocol

Status: ADOPTED_GOVERNANCE_SPECIFICATION

## Overview

此协议定义了 ADT 各 Agent 角色的反目标自检系统。每个角色在执行完成、即将
交付出结果之前，必须执行反目标自检。自检通过方可交付；触发关注则记录
Defect Card。此协议是 ADT Adaptive Counter-Objective Governance 的执行层。

## Anti-Objective Definition

Anti-Objective (反目标) 是指治理行为本身产生的负面效应超过其保护的正面价值。
ADT 治理系统的核心约束之一：治理成本不得超过任务或产品价值。反目标自检确保
每个角色在交付前审视自身的工作是否违反了这一原则。

## Per-Role Self-Check Questions

### Maker (交付前)

1. "Am I adding unnecessary steps for false safety?"
   （我是否为了虚假安全添加了不必要的步骤？）
2. "Is governance heavier than the task itself?"
   （治理流程是否比任务本身更重？）
3. "Did I modify files outside FILES_IN_SCOPE?"
   （我是否在 FILES_IN_SCOPE 之外做了修改？）
4. "Did I embed unauthorized scope expansion in the result?"
   （我是否在结果中混入了未经授权的扩展？）
5. "Could this change have been accomplished with a smaller diff?"
   （我的修改是否可以用更小的变更完成？）

### Checker (审计决策前)

1. "Is my audit itself consuming more Human attention than the defect it catches?"
   （我的审计本身消耗的 Human 注意力是否超过它捕获的缺陷？）
2. "Did I expand the audit scope beyond what was requested?"
   （我是否在审计中扩大了检查范围？）
3. "Did I make substantive modifications while in READ_ONLY mode?"
   （我是否在 READ_ONLY 模式下做了实质性修改？）
4. "Is my AUDIT_DECISION backed by concrete evidence?"
   （我的 AUDIT_DECISION 是否有具体证据支撑？）
5. "Am I blocking a valid change due to excessive caution?"
   （我是否因为过于谨慎而阻塞了合理的变更？）

### Holder (聚合前)

1. "Is my summary generating more governance than product value?"
   （我的摘要是否产生了比产品价值更多的治理？）
2. "Am I restating raw Artifacts instead of passing them through?"
   （我是否在聚合中重述而非传递原始 Artifact？）
3. "Am I expanding scope without Human authorization?"
   （我是否在没有获得 Human 授权的情况下扩展了范围？）
4. "Is the TODO list growing instead of shrinking?"
   （待办事项列表是否在增长而非减少？）
5. "Am I adding communication rounds without new information?"
   （我是否在没有新增信息的情况下增加了沟通轮次？）

### Controller (返回 Human 前)

1. "Am I presenting evidence fields or just narrative?"
   （我呈现的是证据字段还是纯粹的叙述？）
2. "Does the return include FACT, AUTHORITY, ACTION, RESULT, ARTIFACT_TYPE, ARTIFACT_LOCATION?"
   （返回内容是否包含必要字段？）
3. "Am I asking Human to decide when no decision is needed?"
   （我是否在 Human 不需要决策时要求其决策？）
4. "Am I hiding any blockers or uncertainty?"
   （我是否隐藏了任何阻塞项或不确定性？）
5. "Can I convey the same decision with fewer words?"
   （我是否可以用更少的文字传达相同的决策信息？）

## Trigger Mechanism

每个角色在其最终 Gate（交付/决策/聚合/返Human）之前执行自检。
自检是静默执行的，不消耗 Point，不生成独立 Receipt。

## Output

如果自检通过: 正常交付。
如果自检触发关注: 注册 Defect Card，格式如下：

```
DEFECT_CARD
  DEFECT_ID: ADT-DEFECT-{date}-{seq}
  SOURCE_ROLE: MAKER|CHECKER|HOLDER|CONTROLLER
  TRIGGER_QUESTION: 触发关注的自检问题
  SEVERITY: LOW|MEDIUM|HIGH
  DESCRIPTION: 具体描述
  RECOMMENDATION: 建议的修复方向
  TASK_ID: 关联的 TASK_ID
```

## Authority Dispatch Card Template

Controller 在派发任何 L1 或 L2 任务之前，MUST 生成 Authority Dispatch Card。

```
AUTHORITY DISPATCH CARD
  TASK_ID: ADT-{date}-{seq}
  AUTHORITY_SOURCE: 授权来源
  HUMAN_ROLE: 授权 Human 的角色
  ISSUED_AT: ISO 8601 timestamp
  EXPIRES_AT: 过期时间或 SESSION_SCOPE
  AUTHORIZED_ACTIONS: [枚举授权操作列表]
  BOUNDARY:
    REPOSITORY: 仓库路径
    BASE_SHA: 基准 commit
    BRANCH: 分支名
    FILES_IN_SCOPE: [授权文件列表]
  PUBLISH_LEASE:
    PUSH_ALLOWED: NO
    DRAFT_PR_ALLOWED: NO
    READY_ALLOWED: NO
    MERGE_ALLOWED: NO
    BRANCH_DELETE_ALLOWED: NO
```

## Integration

此协议与以下现有治理组件集成：

- `METHODOLOGY.md` — Adaptive Counter-Objective Governance 的方法论基础
- `AGENTS.md` — Agent 治理规则（反目标部分由本协议具体化）
- `protocols/ADT_SELF_ITERATION.md` — ADT 自迭代治理协议
- 各角色 Skill 文件 — 在最终 Gate 前嵌入自检步骤

本协议不创建新的状态系统、Task Tier 或 Candidate State。
