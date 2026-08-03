# ADT 自适应数字团队

> 一个帮助人和 AI 团队稳定协作的治理系统。

## 当你和 AI 一起完成一个项目时

AI 可以快速生成代码、设计方案、文档和分析结果。

但真正困难的问题通常不是“AI 能不能做”。

而是：

- AI 是否理解了真实目标？
- 执行过程中是否发生方向漂移？
- 团队成员是否知道 AI 为什么这样决定？
- 错误是否能在低成本阶段被发现？

ADT 解决的是这些协作问题。

## 从这里开始

**人类用户** → A. 了解 ADT（继续阅读） | B. [开始使用](#开始使用) | C. [开发者文档](#开发者文档)
**AI / Agent** → 从 [`BOOTSTRAP.md`](./BOOTSTRAP.md) 开始，按 [`AGENTS.md`](./AGENTS.md) 操作

---

# ADT 是什么？

ADT（Adaptive Digital Team）是一套帮助人和 AI 协作的治理系统。

它让 AI 不只是执行任务，而是在：

- 明确目标
- 理解约束
- 接受验证
- 保留证据
- 持续修正

的情况下参与团队工作。

ADT 不是简单的 Agent 工具集合。

它关注的是：

> 如何让 AI 具备行动能力，同时保持可靠、透明和可纠正。

---

# 为什么需要治理？

AI 的执行速度越来越快。

但速度提升并不会自动带来可靠性。

没有治理机制时：

- 小错误会快速扩大
- 目标容易漂移
- 团队无法理解 AI 决策
- 后续修改成本增加

因此，一个 AI 团队需要的不只是执行能力，还需要协作规则。

---

# ADT 治理哲学

## 1. Objective First（目标优先）

执行之前明确：

- 目标是什么
- 成功标准是什么
- 哪些边界不能突破

---

## 2. Minimum Necessary Governance（最小必要治理）

不是所有任务都需要同等强度的检查。

治理强度应该匹配风险。

低风险任务：

快速执行。

高风险任务：

增加验证。

---

## 3. Evidence Driven（证据驱动）

AI 不只提交结果。

需要能够说明：

- 做了什么
- 为什么这样做
- 如何验证

---

## 4. Human Authority（人类掌握关键决策）

Human 不负责替 AI 完成所有步骤。

Human 负责：

- 定义目标
- 设置边界
- 判断关键变化

---

# ADT 如何工作？

一个基础协作流程：

```

Human
|
Objective
|
Maker
|
Checker
|
Evidence
|
Correction

```

---

# 核心机制

## Governance Control Plane

管理团队协作规则。

## Maker / Checker

执行和验证分离。

## State Machine

管理任务状态。

## Validator

检查结果是否符合要求。

## Evidence Card

记录决策依据和验证过程。

## Adaptive Runtime Layer

根据任务风险动态调整治理方式。

---

# 开始使用

一次最小 ADT 任务：

1. 定义目标
2. 判断任务风险
3. 执行任务
4. 必要时触发检查
5. 保存关键证据
6. 输出可追踪成果

**入口**：[`BOOTSTRAP.md`](./BOOTSTRAP.md) → [`AGENTS.md`](./AGENTS.md) → [`protocols/BEGINNER_BOOTSTRAP_ROUTER.md`](./protocols/BEGINNER_BOOTSTRAP_ROUTER.md)

---

# 开发者文档

深入了解：

- Architecture → [`docs/architecture/`](./docs/architecture/)
- Governance → [`governance/`](./governance/)
- Runtime Layer → [`protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md`](./protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md)
- Protocol Design → [`protocols/`](./protocols/)
- Agent 入口 → [`BOOTSTRAP.md`](./BOOTSTRAP.md) | [`AGENTS.md`](./AGENTS.md)
