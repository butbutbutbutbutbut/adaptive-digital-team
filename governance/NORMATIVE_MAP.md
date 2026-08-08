# Normative Map

This document establishes the single normative source for every ADT governance
concept. No concept may have two authoritative definitions. All other documents
that reference a concept are secondary, compatibility, or executable detail.

## Normative sources

| Concept | Normative Source | Status | Compatibility Entries |
|---|---|---|---|
| ADT definition | `METHODOLOGY.md` | ADOPTED | `README.md` § What ADT provides |
| Role model | `governance/ROLE_MODEL.md` | ADOPTED | `AGENTS.md` § Roles, `README.md` § Roles |
| Fact/action separation | `governance/AUTHORITY_AND_FACTS.md` | ADOPTED | `AGENTS.md` § FACT_SOURCE_REBIND |
| Candidate lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` | ADOPTED | `AGENTS.md`, `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`, `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Agent-facing rules | `AGENTS.md` | ADOPTED | — |
| Protocol activation | `BOOTSTRAP.md` | ADOPTED | `AGENTS.md` § Protocol activation, `README.md` § AI ACTIVATION DIRECTIVE |
| First-contact routing | `README.md` | ADOPTED | `BOOTSTRAP.md`, `AGENTS.md` § First-contact routing |
| Human-facing evidence | `AGENTS.md` § Human-facing evidence discipline | ADOPTED | — |
| Lightweight execution flow | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | ADOPTED | — |
| Beginner bootstrap | `protocols/BEGINNER_BOOTSTRAP_ROUTER.md` | ADOPTED | — |
| Multimodal evidence | `protocols/MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md` | ADOPTED | — |
| Instruction routing | `protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md` | ADOPTED | — |
| Project closeout | `protocols/PROJECT_CLOSEOUT_PROTOCOL.md` | ADOPTED | — |
| Dynamic governance routing | `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` | ADOPTED | `AGENTS.md` § R1 preservation contract |
| Runtime adapter contract | `protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md` | ADOPTED | — |

## Status definitions

| Status | Meaning |
|---|---|
| `ADOPTED` | Normative; all other references must defer. |
| `CANDIDATE` | Proposed normative, under independent review. |
| `EXPERIMENTAL` | Not yet normative; subject to change without preserving compatibility. |

## Deprecated / replaced concepts

| Old Concept | Old Location | Replaced By | New Location |
|---|---|---|---|
| Persistent Holder (role) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Project Control + Task Holder | `governance/ROLE_MODEL.md` |
| Holder responsibilities | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Role definitions | `governance/ROLE_MODEL.md` |
| Candidate lifecycle (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Candidate Lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate lifecycle (duplicate) | `AGENTS.md` § Candidate Lifecycle R1 | Candidate Lifecycle | `protocols/CANDIDATE_LIFECYCLE.md` |
| Runtime identity registrar | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Runtime-derived identity | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate fingerprint registrar | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Candidate fingerprint | `protocols/CANDIDATE_LIFECYCLE.md` |
| Audit receipt registration | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Audit receipt validation | `protocols/CANDIDATE_LIFECYCLE.md` |
| Ready/Merge authorization registry | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Receipt and authorization binding | `protocols/CANDIDATE_LIFECYCLE.md` |
| PRE_MERGE_REALTIME_GATE (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Final realtime gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| CI verification (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | CI gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate state machine (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Candidate state machine | `protocols/CANDIDATE_LIFECYCLE.md` |
| Pre-write execution gate (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Pre-write execution gate | `protocols/CANDIDATE_LIFECYCLE.md` |
| Scope enforcement (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Scope enforcement | `protocols/CANDIDATE_LIFECYCLE.md` |
| Remote candidate history immutability (duplicate) | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Remote candidate history immutability | `protocols/CANDIDATE_LIFECYCLE.md` |
| Runtime candidate identity (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Runtime-derived identity | `protocols/CANDIDATE_LIFECYCLE.md` |
| Candidate fingerprint (duplicate) | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | Candidate fingerprint | `protocols/CANDIDATE_LIFECYCLE.md` |

## Deprecation / absorption map（19→4 重构登记，2026-08-07）

双层重构（19 协议 → 哲学层 + 3 执行核）的推翻留痕登记。处置分两类：**吸收**（强制力已迁入 3 核，机器继续看守）与**哲学化**（降级为判断指南）。登记去向以 `protocols/BINDING.md` / `protocols/GATE.md` / `protocols/RECEIPT.md` / `protocols/PHILOSOPHY.md` 实际章节为准。

### 11 个带牙协议（强制力已迁入 3 核）

| 旧协议 | 处置 | 取代者 | 强制力新位置 | 说明 |
|---|---|---|---|---|
| CANDIDATE_LIFECYCLE.md | 吸收 | BINDING + GATE | 身份/指纹/状态机→BINDING（不变量 I1/I8、§11 对照）；预写执行门→GATE §3 G6/G7 | 拓扑 `ONE_TASK=ONE_BRANCH=ONE_PR=BASE_MAIN` 进 BINDING §7.1 |
| HOLDER_TOKEN.md | 吸收（Token 三段切） | BINDING + GATE + RECEIPT | 发放与登记→BINDING §10；每动作校验/异常回收→GATE §7/§8；释放→RECEIPT §9 | 一任务一令牌；回收必须报告 Human |
| INSTRUCTION_ROUTING_AND_AUTHORITY.md | 吸收 | BINDING | §6 指令路由与授权 | 头部字段、fail-closed 表、转发规则 |
| DYNAMIC_GOVERNANCE_ROUTER.md | 吸收 | BINDING | §7 分派包部分（HARD_STOP 路由表） | 路由只出候选计划；授权是独立闸门 |
| WORKSPACE_ISOLATION.md | 吸收 | GATE | §3 G1/G2、§10 | worktree 布局、不变量、清理规则 |
| CONCURRENCY_LIMIT.md | 吸收 | GATE | §3 G3/G4、§6、§8 | N=2 默认 / N_MAX=4；SUBAGENT_TIMEOUT / SUBAGENT_HANG |
| ADT_RUNTIME_ADAPTER_CONTRACT.md | 吸收 | GATE | §4、§10 | 三层隔离；SESSION_PRINCIPAL ≠ Human Holder |
| ARTIFACT_DELIVERY.md | 吸收 | RECEIPT | §10.1 产物交付 | artifact_type / artifact_location |
| MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md | 吸收 | RECEIPT | §10.2 多模态证据门 | 实看要求；`MERGE_ALLOWED: NO` 条件 |
| PROJECT_CLOSEOUT_PROTOCOL.md | 吸收 | RECEIPT | §10.3 项目关闭 | 关闭状态机、材料分类、attestation |
| PERSISTENT_HOLDER_CONTROL_PLANE.md | 半废弃 | PHILOSOPHY（对照）+ BINDING（格式） | 格式定义→BINDING §4/§9（Dispatch Card / Authority Card） | 角色部分已被 ROLE_MODEL 取代（见上文 Deprecated 表） |

### 8 个哲学化协议（降级为判断指南）

| 旧协议 | 处置 | 取代者 | 强制力新位置 | 说明 |
|---|---|---|---|---|
| ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md | 哲学化 | PHILOSOPHY 原则一 | `NO_UNBOUND_EXECUTION` 强制力在 BINDING §2 | 判断级：治理成本 ≤ 保护价值 |
| ADT_ANTI_OBJECTIVE_PROMPT.md | 哲学化 | PHILOSOPHY 原则一 | 拔牙①授权卡模板→BINDING §9 | 自检问题留哲学层 |
| ADT_SELF_ITERATION.md | 哲学化 | PHILOSOPHY 原则三 | — | 流程约定级 |
| BEGINNER_BOOTSTRAP_ROUTER.md | 哲学化 | PHILOSOPHY 原则四 | 入口结构保持冻结（产品资产，不参与切割） | 路由判断哲学化 |
| HUMAN_FACING_PSYCHOLOGY.md | 哲学化 | PHILOSOPHY 原则二（§2 呈现纪律） | 呈现纪律原文保留；心理学机制全砍 | 模板库砍掉；检验扳机防回潮 |
| LIGHTWEIGHT_EXECUTION_FLOW.md | 哲学化 | PHILOSOPHY 原则四 | 拓扑/身份/scope 强制力在 CANDIDATE_LIFECYCLE + 三核 | 流程判断哲学化 |
| REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md | 哲学化 | PHILOSOPHY 原则五 | 拔牙②外部绑定固定 SHA 校验→BINDING §8 | 事实源阶梯判断哲学化 |
| RESOURCE_ALLOCATOR_INTEGRATION.md | 哲学化 | PHILOSOPHY 原则四 | 拔牙③人类上限 BLOCKED→GATE §9 | tier 判断哲学化 |

## Rules

1. **One concept = one normative source.** No exceptions. Every ADT concept has exactly one document that defines it authoritatively.
2. **Compatibility entries may exist** but MUST point to the normative source. They are summaries, not alternatives.
3. **This map itself is normative** — disputes about "which document is authoritative" resolve here.
4. **New concepts** that are introduced in a compatibility document and not yet mapped to a normative source are EXPERIMENTAL until mapped.
5. **Deprecation** must be recorded in this map before a compatibility entry is removed.
