# ADT 路线图 P0–P5

**文档类型：** 路线图正文
**版本：** R1
**状态：** CANDIDATE_FOR_INDEPENDENT_REVIEW
**日期：** 2026-07-21
**编制：** Holder Control Plane → Maker（DeepSeek V4 Pro）
**基准：** main@3272a565576ec41db99d427efb9ed687b765ac06

---

## 模型挡位分配

全路线图统一模型挡位：

| 角色 | 模型 | 用途 |
|---|---|---|
| CONTROL / HOLDER | DeepSeek V4 Pro Max | 范围裁定、路线语义、最终门禁 |
| PRIMARY MAKER | DeepSeek V4 Pro | 文档落库与入口同步 |
| INDEPENDENT CHECKER | DeepSeek V4 Pro Max | 独立上下文、只读审计 |
| SUBAGENTS | 0 | 不派生子代理 |
| MAX_ACTIVE_AGENTS | 1 | 串行执行 |

---

## 状态语义

```
PLANNED          ≠ AUTHORIZED
AUTHORIZED       ≠ IMPLEMENTED
IMPLEMENTED      ≠ OPERATIONAL
```

每个阶段必须通过独立任务完成：设计 → 授权 → 实现 → 审计 → 合并。一条路线图条目不等于实施授权。

---

## P0 — 协议基础与治理运行基线

**状态：** OPERATIONAL_BASELINE / CONTINUING_MAINTENANCE
**治理挡位：** 不适用（已完成）

### 已交付

| 交付物 | 状态 | 位置 |
|---|---|---|
| ADT 治理根仓库 | OPERATIONAL | `butbutbutbutbutbut/adaptive-digital-team` |
| AGENTS.md（含 Candidate Lifecycle R1） | ADOPTED_GOVERNANCE_SPECIFICATION | 根目录 |
| PROJECT_STATE.md（schema v2） | OPERATIONAL | 根目录 |
| 仓库即提示词原则 | ADOPTED | `docs/REPOSITORY_AS_PROMPT_PRINCIPLE_R1.md` |
| 冷启动协议 | ADOPTED | `BOOTSTRAP.md` |
| Persistent Holder Control Plane | ADOPTED_GOVERNANCE_SPECIFICATION | `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` |
| Lightweight Execution Flow | ADOPTED_GOVERNANCE_SPECIFICATION | `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` |
| Adaptive Counter-Objective Governance | ADOPTED_GOVERNANCE_SPECIFICATION | `protocols/ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` |
| 仓库绑定运行时协议 | ADOPTED | `protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` |
| 指令路由与授权协议 | ADOPTED | `protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md` |
| 多模态证据验收门禁 | ADOPTED | `protocols/MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md` |
| 项目关停协议 | ADOPTED | `protocols/PROJECT_CLOSEOUT_PROTOCOL.md` |
| 部署方案 v0.2 | ARCHITECTURE_CANDIDATE | `docs/architecture/ADT_DEPLOYMENT_PLAN_V0_2.md` |
| 人格记忆备份与凭据边界 R1 | DESIGN_CANDIDATE | `docs/architecture/ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md` |
| 存储提案 R1 | ADOPTED | `docs/ADAPTIVE_DIGITAL_TEAM_REPOSITORY_PROPOSAL_R1.md` |
| Candidate Identity & Single-PR Gate R1 | 当前 active_candidate | `hermes/adt-candidate-identity-single-pr-gate-r1` |
| Push Ref Branch Binding Repair | 当前 active_candidate | `hermes/adt-push-ref-branch-binding-r1` |

### P0 门禁结论

- 治理协议栈完整，但 **运行时未授权**。
- PERSISTENT_HOLDER_RUNTIME: NOT_IMPLEMENTED
- RUNTIME_ACTIVATION: NOT_AUTHORIZED
- HERMES_R1: NOT_AUTHORIZED

---

## P1 — 治理收敛与架构基线冻结

**状态：** PLANNED / NOT_AUTHORIZED
**治理挡位：** STANDARD
**依赖：** P0

### 目标

将 ADT 治理层从"已采纳但分散"收敛到"架构基线冻结"。包括：采纳反目标治理协议、冻结部署方案 v0.2、接受人格记忆备份设计。

### 关键交付

| 交付物 | 当前状态 | 目标状态 |
|---|---|---|
| 部署方案 v0.2 | ARCHITECTURE_CANDIDATE | ARCHITECTURE_FROZEN |
| 人格记忆备份与凭据边界 R1 | DESIGN_CANDIDATE | DESIGN_ACCEPTED |

### 说明

- P1 是文档和设计审查层，**无代码实施，无运行时激活**。
- P1 未授权。当前仅有路线图文档候选（ADT-ROADMAP-P0-P5-R1）处于独立审计门禁中。
- 门禁范围仅限于路线图文档自身的内容审核。
- **本轮审计不会冻结或授权 P1。**
- P1 必须另开独立任务完成设计、授权、实现和审计。

---

## P2 — 身份与凭据基础

**状态：** PLANNED / NOT_AUTHORIZED
**治理挡位：** ENHANCED
**依赖：** P1 完成（ARCHITECTURE_FROZEN）

### 目标

建立双 Agent 身份和最小权限凭据基础。不实施运行时。

### 关键交付

- Hermes Profile: `xiaohe`（空 Profile + Skill Allowlist）
- Hermes Profile: `anding`（空 Profile + Skill Allowlist）
- 四个私有 GitHub 仓库（人格 ×2 + 记忆归档 ×2）
- GitHub PAT: `anding-default-readonly`
- GitHub PAT: `checker-default-readonly`
- Windows ACL 隔离
- age 密钥对生成（私钥仅 Human 持有）

---

## P3 — Gateway 与通信层

**状态：** PLANNED / NOT_AUTHORIZED
**治理挡位：** CRITICAL
**依赖：** P2 完成

### 目标

实施 ADT Gateway 核心、飞书 Bot 集成和记忆桥管道。

### 关键交付

- ADT Gateway Core（Identity Broker、Debate Controller、Audit Ledger）
- 飞书 Bot: 安鼎 + 小禾（独立 App ID/Secret）
- FEISHU_TO_XIAOHE_MEMORY_BRIDGE
- Memory Candidate Pipeline
- WORK_DEBATE / CHARACTER_BANTER 机制

---

## P4 — 集成与部署

**状态：** DESIGN_BASELINE_PARTIAL / IMPLEMENTATION_NOT_AUTHORIZED
**治理挡位：** CRITICAL
**依赖：** P3 完成

### 目标

xiaohe 接入微信、anding 接入飞书、部署 H5 控制面板。

### 说明

部署方案 v0.2 和人格记忆备份设计 R1 已产出部分设计基线（DESIGN_BASELINE_PARTIAL），但实施未授权（IMPLEMENTATION_NOT_AUTHORIZED）。

---

## P5 — 运维与优化

**状态：** PLANNED / NOT_AUTHORIZED
**治理挡位：** STANDARD
**依赖：** P4 完成

### 目标

生产监控、自动备份、恢复测试、治理开销度量与优化。

---

## 当前审计范围

```text
TASK_ID: ADT-ROADMAP-P0-P5-R1
CURRENT_TASK_GATE: EXTERNAL_INDEPENDENT_GOVERNANCE_AUDIT
IMPLEMENTATION_STATUS: NOT_AUTHORIZED

审计对象: 本文档候选（文档内容、状态语义、门禁对齐）
审计范围外: P1–P5 实施授权、架构冻结、Profile 创建、凭据操作
```

**本轮审计通过后：** 路线图作为参考文档被采纳，P1–P5 仍为 NOT_AUTHORIZED。

---

## 附录 A — 当前环境参考文献

| 文件 | 用途 |
|---|---|
| `AGENTS.md` | Candidate Lifecycle R1、身份派生、指纹、单 PR 拓扑 |
| `PROJECT_STATE.md` | schema v2，当前任务 ADT-CANDIDATE-IDENTITY-AND-SINGLE-PR-GATE-R1 |
| `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Holder 职责、Dispatch Card、Publish Lease |
| `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | L0/L1/L2 路由、增量修复 |
| `protocols/ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` | 动态治理挡位、预算门禁 |
| `docs/architecture/ADT_DEPLOYMENT_PLAN_V0_2.md` | 部署架构、双 Agent 隔离 |
| `docs/architecture/ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md` | 三层记忆模型、凭据矩阵 |
