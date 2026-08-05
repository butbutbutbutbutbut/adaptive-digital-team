# ADT Roadmap

> 最后更新：2026-08-06
> 
> 每个阶段需要独立的 Human 授权，包含确切的仓库、分支、Base 和 scope。
> 仓库公开不等于授权实施。

## P0 — Operational Baseline

**状态：** `OPERATIONAL_BASELINE` / `CONTINUING_MAINTENANCE`

已交付并持续维护：

| 能力 | 载体 |
|---|---|
| Scope Enforcement（授权范围强制执行） | `CANDIDATE_BINDING.json` + CI gate |
| Candidate Lifecycle（候选状态机） | `protocols/CANDIDATE_LIFECYCLE.md` |
| Maker / Checker 分离 | `governance/ROLE_MODEL.md` |
| Repository as Prompt | `AGENTS.md` § Repository-as-prompt startup |
| Fingerprint Binding（SHA-256 候选身份） | `protocols/CANDIDATE_LIFECYCLE.md` § Candidate fingerprint |
| Evidence Card（证据留痕） | `AGENTS.md` § Human-facing evidence discipline |
| Pre-write Execution Gate | `scripts/validate_binding.py` |
| Adaptive Counter-Objective Controls | `METHODOLOGY.md` |
| Beginner Bootstrap Router（A/B/C 路由） | `protocols/BEGINNER_BOOTSTRAP_ROUTER.md` |
| Human Facing README | `README.md` |
| User-facing Asset Protection | `AGENTS.md` § Non-negotiable boundaries |

P0 是地基。后续所有阶段在 P0 之上增量构建。

---

## P1-P3 — Dynamic Governance R1

**状态：** `SPECIFICATION_ADOPTED` / `RUNTIME_NOT_AUTHORIZED`

协议已通过并被引用，但尚未作为持续运行的 Runtime 实例激活。

| 组件 | 文件 | 状态 |
|---|---|---|
| Dynamic Governance Router（任务分类、风险路由） | `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` | `ADOPTED_GOVERNANCE_SPECIFICATION` |
| Runtime Adapter Contract（三层隔离边界） | `protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md` | `ADOPTED_GOVERNANCE_SPECIFICATION` |
| Resource Allocator（资源/模型分配） | PR #49 | Merged |
| Adaptive Counter-Objective Gate | PR #52 | Merged |
| Transient Candidate Binding | PR #51 | Merged |

**已完成的链路测试（PR #56）：**

- Controller → Holder → Maker + Checker 分派链 ✅
- Scope enforcement 跨角色生效 ✅
- Handoff Envelope FROM/TO/CONSUMER 全链追溯 ✅
- Holder HARD GATE 防止 self-implement ✅

**S2-002-A 实验发现（待办）：**

- ~~Artifact Delivery Layer — 产物位置对人类可见~~ → ✅ PR #59/#60
- Human Point Budget — 低风险任务轻量治理
- Artifact Existence Gate — "做完了"和"能看到产物"之间的验证

**已完成的新增协议：**

- 自迭代治理 — `protocols/ADT_SELF_ITERATION.md`（ADT 发现并修复自身缺陷的标准流程）

**当前阻止 RUNTIME 激活的因素：**

- `PROJECT_STATE.md`: `implementation_status: NOT_AUTHORIZED`
- 缺少持续运行的 Runtime 实例
- S2 Adaptive Runtime Layer 仍是实验概念，未形成正式协议文档

---

## P4 — Public Release Readiness

**状态：** `PARTIALLY_READY` / `IMPLEMENTATION_NOT_AUTHORIZED`

| 检查项 | 状态 |
|---|---|
| README 产品叙事 + A/B/C 功能入口 | ✅ PR #57 |
| Apache 2.0 License | ✅ |
| Contributing 指南 | ✅ |
| 用户接触面保护规则 | ✅ AGENTS.md |
| 中文用户完整认知链 | ✅ README |
| 独立部署文档 | ❌ 缺失 |
| 公开示例 / Demo 仓库 | ❌ 缺失 |
| 外部用户 onboarding 路径 | ❌ 缺失 |

---

## P5 — ADT Ops Org Bootstrap

**状态：** `PLANNED` / `NOT_AUTHORIZED`

尚未启动。涉及：

- 运营组织架构
- 生产部署实例
- 多仓库运维
- 飞书 / 外部通知集成
- 密钥与凭证管理

---

## PT — 后训练轨道（Post-Training Track）

**状态：** `STRATEGY_ADOPTED` / `IMPLEMENTATION_NOT_AUTHORIZED`

> 本节固化 Human Holder（之）的方向性战略指示（2026-08-06）：
> ① Human Facing 接触面必须引入心理机制，推动用户反思与推进，而不只是状态报告；
> ② ADT 本质是 harness，前期顶层设计相当于"预训练"，更关键的是用训练 AI 的范式对 ADT 本身做"后训练"。

### 轨道定义

ADT 本质是一个 harness（agent 操控框架）。前期顶层设计（协议、架构、治理）相当于 AI 训练的**预训练**阶段——该阶段已基本完成（P0-P5 即预训练产物）。更重要的阶段是**后训练**：用训练 AI 的那套范式（**数据采集 → 强化/惩罚 → 迭代**）去训练 ADT 本身。后训练的目标不是继续写更多协议，而是从运行数据中调优 harness 的行为。

### 优化目标

| 目标 | 定义 | 度量信号 |
|---|---|---|
| 任务命中率 | 任务成功率——分派的任务被正确、完整、一次通过地完成 | Progress Receipt / Checker Receipt 通过率、Human ACCEPT 比例 |
| 治理推理能力 | Dispatch / 审计 / 验收决策质量——任务分类是否准确、验收是否一致、审计是否发现真问题 | 路由纠偏记录、Defect Card 产出率、Human REJECT 分布 |

### 训练数据源

每次运行都是一条训练样本：

| 数据源 | 内容 | 用途 |
|---|---|---|
| Progress Receipt | Maker 任务结果与自述 | 命中率统计、偏差检测 |
| Checker Receipt | Checker 独立审计结论 | 审计质量、治理推理评估 |
| 缺陷卡（Defect Card） | 治理缺陷的标准化记录 | 惩罚信号——定位需要修复的机制 |
| Human gate ACCEPT / REJECT | 人类验收决策 | **黄金标签**——每次 Human 验收都是一条训练样本 |

### 心理机制（Human Facing）——之的指示

Human Facing 部分非常重要。ADT 本质上要鼓励用户（之）不断反思已有成果并推进任务。接触面设计要引入**心理机制**，推动用户认知升级，而不只是状态报告：

| 机制 | 作用 | 落地示例 |
|---|---|---|
| 进度效应 | 让用户看到进展与"差一点完成"，激发完成动机 | 接触面展示阶段完成度与剩余差距 |
| 承诺一致性 | 用户已做出的承诺被温和地重申，保持行为一致 | 接触面回顾之此前确认的方向与承诺 |
| 蔡格尼克效应 | 未完成事项持续占据认知，驱动推进 | 接触面显式列出未关闭的开放项与下一步 |

> 来源：Human Holder（之）的战略指示，2026-08-06。

### 与 P0-P5 的关系

- **P0（隔离 / 并发 / 令牌）是预训练基建**：它保证训练数据干净——并行不串扰、并发有上限、身份与授权可验证。
- P1-P5（动态治理、发布就绪、Ops 组织）是预训练阶段产出的架构与协议。
- **后训练轨道在 P0-P5 之上增量构建**：不推翻既有协议，而是给它们装上数据闭环——采集运行样本、施加强化/惩罚信号、迭代治理机制本身。

### 当前状态

- 战略方向已由 Human 确认（`STRATEGY_ADOPTED`）
- 具体实现（数据管道、指标仪表、心理机制落地）**尚未授权**
- 下一步：设计后训练数据采集与反馈回路的最小闭环，等待 Human 授权
