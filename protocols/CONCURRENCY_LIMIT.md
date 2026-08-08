> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# 并发上限协议（Concurrency Limit）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
RUNTIME_STATUS: `IMPLEMENTABLE`
RUNTIME_ACTIVATION: `AUTHORIZED_FOR_CONTROLLER_DISPATCH_GATE`

## 规范声明

本文档是 ADT 运行时并发上限规则的规范来源。它扩展既有协议（Workspace
Isolation、Resource Allocator Integration、Persistent Holder Control Plane），
**不创建**新的调度系统，不改变任何角色的既有权限边界，不修改候选生命周期
状态机。

核心机制：**Controller 同时最多持有 N 个在飞任务（默认 N=2）**。超出上限的
新任务进入有界 FIFO 队列，队列溢出或排队超时即拒绝。这是 runtime 执行层的
第一块约束：隔离协议（P0-001）解决"空间"冲突（谁的工作区），并发上限解决
"时间"冲突（同时做几件事、占多少资源）。

## 1. 问题陈述

### 1.1 现状

Controller 无限制地并行派发子代理任务，实际观测到的失败：

- **600s 超时常态化**：DS 模型下，复杂子代理链超过 600s 任务级超时是常态。
  多个任务并行时争抢模型推理带宽，每个任务的有效推进速度下降，超时更频繁；
- **并行争抢**：即使工作区已隔离（P0-001 已解决），并行任务仍争抢共享的
  推理配额、token 预算与 Controller/Holder 的调度注意力；
- **资源耗尽**：token 预算与上下文窗口被并行任务分摊，单个任务可用的推理
  深度下降，错误率上升；
- **调度认知过载**：Controller 同时跟踪的任务越多，核对 worktree、分支、
  Dispatch Card、Progress Receipt 的认知开销越大，状态漂移与漏核对的风险
  越高；
- **具体观察**：并行派发 3+ 复杂子代理任务时，超时率显著高于串行或 2
  并行；超时任务返回 `TIMEOUT` 且无 Progress Receipt，重派导致重复分支与
  worktree 清理负担。

### 1.2 设计目标

1. Controller 同时最多 N 个在飞任务，N 默认 2；
2. 上限是调度层的硬约束（fail closed），不是建议值；
3. 与工作区隔离正交：隔离解决空间冲突，并发上限解决时间/资源冲突；
4. 上限可调，但调整权在 Human；Controller 只能 fail-safe 降级，不能自行
   升限。

## 2. 并发模型

### 2.1 在飞任务（IN_FLIGHT）定义

**在飞 = 已派发未聚合**：

- 起点：Controller 发出 Dispatch Card（含 WORKTREE 分配）——占用一个在飞名额；
- 终点：任务聚合——候选合并到 main、任务被取消、或收到最终 Progress
  Receipt 并关闭；
- 在飞计数 = 已派发且未聚合的写任务数。

### 2.2 计数规则

- 只读任务（Checker 审查、审计、分析）不占用在飞名额；
- 排队任务（`QUEUED`）不占用在飞名额、不分配 worktree；
- 被拒绝任务（`REJECTED`）不占用任何资源；
- 名额生命周期：派发时 +1，聚合/取消/关闭时 -1。

### 2.3 与 worktree 的一一对应

沿用 WORKSPACE_ISOLATION 的 `ONE_WORKTREE = ONE_BRANCH = ONE_TASK`：

```text
ONE_IN_FLIGHT = ONE_BRANCH = ONE_WORKTREE = ONE_TASK
```

- 一个在飞任务 = 一个分支 = 一个写 worktree；
- Checker 的只读 worktree 与写 worktree 同分支，属于同一任务的审查阶段，
  不单独计数；
- 主工作区（main）不承载并行写任务，永远不占用在飞名额；
- 因此 N 同时约束：并行写 worktree 数 ≤ N、并行候选分支数 ≤ N。

### 2.4 任务受理状态

```text
受理（QUEUED）→ 派发（IN_FLIGHT）→ 聚合（AGGREGATED）→ 关闭（CLOSED）
                    ↘ 超时/取消 → 关闭（CLOSED）
受理（QUEUED）→ 排队超时/队列满 → 拒绝（REJECTED）
```

## 3. 上限值

### 3.1 默认值：N = 2

理由：

- **N=1（完全串行）**：浪费 worktree 隔离带来的并行能力；一个任务等待
  Checker/CI 时，其他任务无法推进；
- **N=2**：允许两个任务交错推进（一个等 Checker/CI 时另一个在写），同时
  DS 模型下的推理争抢仍在可控范围；观测表明 2 并行与串行的超时率差距
  可接受；
- **N≥3**：DS 模型推理带宽有限，复杂子代理链并行争抢导致 600s 超时明显
  增多，是观测到的最差区间；
- 与 tier 的组合：strong tier 任务（高 token 预算、高推理深度）并行时争抢
  更严重，N=2 是**上限**而非目标值——Controller 在 strong 任务占多数时
  不应追求满额并行。

### 3.2 调整条件与权限

- **谁有权调整：只有 Human Holder**。调整属于资源与调度决策，Controller
  与 Holder 均无升限权；
- **调低（N=1）**：Human 显式指示；或 Controller 观测到持续超时（如最近
  10 个已派发任务中超时 ≥ 3 个）时自动 fail-safe 降级至 N=1，并向 Human
  报告；恢复 N=2 需 Human 确认；
- **调高（N=3）**：仅 Human 显式指示，且需满足观测条件（近期超时率低、
  任务平均耗时下降、模型或 runtime 能力升级）；协议设硬上限
  `N_MAX = 4`，防止无界并行回归；
- N 的当前值由 Controller 维护并随每次派发可见；本文档的默认值（N=2）是
  事实基线，调整后以 Human 最新指示为准。

## 4. 排队与拒绝语义

### 4.1 排队（默认）

- 超出上限时，新任务默认进入 FIFO 队列，按受理顺序排队，状态 `QUEUED`；
- 排队任务不占用在飞名额、不分配 worktree、不产生隔离资源消耗；
- 队列有界：`MAX_QUEUE = 2 × N`（默认 4），防止无界堆积。

### 4.2 排队超时

- `QUEUE_TTL`（默认 15 分钟）：任务在队列中等待超过 QUEUE_TTL 仍未获得
  名额 → 自动拒绝；
- 拒绝返回 `CONCURRENCY_REJECTED`，附原因（`QUEUE_TIMEOUT`），由调用方
  （Human 或上层编排）决定是否稍后重试；
- 被拒绝的任务不创建分支、不创建 worktree、不产生任何资源占用。

### 4.3 拒绝

- 队列满（超出 `MAX_QUEUE`）→ 立即拒绝 `CONCURRENCY_REJECTED`
  （`QUEUE_FULL`）；
- 被拒绝任务可稍后重新受理（作为新任务），或在任务性质允许时降级为
  只读/分析任务；
- 拒绝不是任务失败：不进入候选生命周期，不影响任何 gate。

### 4.4 优先级与插队

- 队列严格 FIFO，不引入优先级机制；
- Human 需要优先时，可指示 Controller 先聚合/取消某个在飞任务释放名额，
  再派发新任务；不提供插队通道。

## 5. 与现有协议的关系

### 5.1 Workspace Isolation（P0-001）

- 隔离协议解决"空间"：每个写任务独立 worktree；本协议解决"时间"：同时
  多少个任务在飞；
- worktree 的分配时机与在飞名额一致：派发时同时获得名额与 worktree；
  聚合后释放名额并清理 worktree（按 WORKSPACE_ISOLATION § 3.4 清理规则）；
- `ONE_IN_FLIGHT = ONE_BRANCH = ONE_WORKTREE = ONE_TASK` 是
  `ONE_WORKTREE = ONE_BRANCH = ONE_TASK` 在调度层的扩展。

### 5.2 Resource Allocator

- tier 是单任务的资源约束（token 预算、推理深度、迭代上限）；N 是跨任务
  的调度约束（同时几个任务）；
- 两者正交：tier 不因并行而重算，N 不因 tier 而改变；
- 组合建议：在飞任务中 strong tier 占多数时，Controller 向 Human 建议
  调低 N；economy tier 任务并行时维持 N=2。

### 5.3 Dispatch Card

沿用 RESOURCE_ALLOCATOR_INTEGRATION 的扩展先例，Dispatch Card 增加
**可选**字段（不改变既有必填字段）：

```text
PACKET: DISPATCH_CARD
...
WORKTREE:
CONCURRENCY_STATUS: IN_FLIGHT | QUEUED | REJECTED   # 可选
```

- `CONCURRENCY_STATUS` 使任务受理状态透明可查；缺省时按调度记录推断。

### 5.4 其他协议

- 候选生命周期（CANDIDATE_LIFECYCLE）：状态机、指纹、审计、合并 gate
  均不变；并发上限只作用于派发前的调度闸门；
- Persistent Holder Control Plane：Dispatch Card / Progress Receipt 格式
  不变；
- Dynamic Governance Router：Controller 完成风险分类与资源分配后、派发前，
  执行并发闸门（CONCURRENCY_GATE）。

## 6. 失败模式与恢复

| 代码 | 症状 | 判定 | 恢复 |
|------|------|------|------|
| `SUBAGENT_TIMEOUT` | 子代理超过 600s 未返回 | 任务级超时 | 终止该子代理，释放名额与 worktree（按 WORKSPACE_ISOLATION 清理规则，确认无活动任务）；标记任务 `TASK_TIMEOUT` 并报告 Human；是否重试由 Human 决定（作为新任务重新受理） |
| `SUBAGENT_HANG` | 子代理无输出且超过 `TASK_MAX_WALL`（默认 30 分钟）仍未返回 | 卡死 | 强制终止会话并回收名额；worktree 按清理规则移除（未提交内容先 commit 或经授权丢弃）；报告 Human；禁止自动无限重试 |
| `QUEUE_DEADLOCK` | 全部在飞名额被卡死/超时任务占用，队列任务永远等不到名额 | 槽位不释放 | 按 `SUBAGENT_HANG` 回收最旧的卡死任务，保证至少一个名额释放；队列任务按 QUEUE_TTL 到期拒绝，不无限等待 |
| `DEPENDENCY_CYCLE` | 任务 A 在队列中等待任务 B 的结果，而 B 尚未派发或也在队列中 | 依赖未就绪 | 依赖任务在依赖完成后才允许受理；Controller 对未就绪依赖返回 `DEPENDENCY_NOT_READY`，禁止依赖链排队 |
| `SLOT_LEAK` | 任务已聚合但名额未释放（记录丢失/窗口崩溃） | 名额泄漏 | 以 git/GitHub 事实为准校正：分支已合并或任务已关闭 → 释放名额；计数不确定时 fail closed，不派发新任务 |
| `CONCURRENCY_MISMATCH` | 不同窗口对 N 或名额计数理解不一致 | 配置/计数漂移 | 以 Controller 的派发记录为单一事实源；分歧时停止派发并向 Human 报告 |

所有恢复路径的共同原则：**不绕过、不强制、不猜测**——任何强制终止或回收
都要先核对事实（worktree 状态、分支状态、是否有活动进程）。

## 7. 与既有协议的兼容性

本协议是纯增量的：

- 不修改任何现有协议文件、CI 配置、schema 或脚本；
- 不改变 Dispatch Card / Progress Receipt 的既有必填字段
  （`CONCURRENCY_STATUS` 为可选）；
- 不改变候选生命周期、绑定、指纹、审计、合并的任何既有判定规则；
- 单一任务（当前状态）继续合法：并发上限只约束并行派发，N≥1 时单任务
  不受影响。

## 8. 参考

| 参考 | 关系 |
|------|------|
| `protocols/WORKSPACE_ISOLATION.md` | worktree 布局、`ONE_WORKTREE=ONE_BRANCH=ONE_TASK`、清理规则 |
| `protocols/RESOURCE_ALLOCATOR_INTEGRATION.md` | 资源层级、Dispatch Card 扩展先例 |
| `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Dispatch Card / Progress Receipt 格式 |
| `protocols/CANDIDATE_LIFECYCLE.md` | 候选状态机、聚合 gate |
| `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` | 任务分类、风险分级、资源分配 |
| `AGENTS.md` | 启动清单、角色边界 |
