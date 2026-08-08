> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# Holder 令牌协议（Holder Token）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
RUNTIME_STATUS: `IMPLEMENTABLE`
RUNTIME_ACTIVATION: `AUTHORIZED_FOR_DISPATCH_TIME_BINDING_WRITE`

## 规范声明

本文档是 ADT 运行时令牌（Holder Token）机制的规范来源。它扩展既有协议
（Workspace Isolation、Concurrency Limit、Persistent Holder Control Plane），
**不创建**新的调度系统，不改变任何角色的既有权限边界，不修改候选生命周期
状态机。

核心机制：**一个任务 = 一枚令牌**。持令牌者拥有
`.hermes/CANDIDATE_BINDING.json` 的写权；令牌随派发自动发放、随 Human gate
决策完成自动释放。P0 三件套的分工因此闭合：隔离协议（P0-001）解决"空间"
冲突（谁的工作区），并发上限（P0-002）解决"时间"冲突（同时做几件事），
令牌机制解决"归属"冲突（谁当前持有绑定写权）。

## 1. 问题陈述

### 1.1 现状

- **CANDIDATE_BINDING 是单点**：`.hermes/CANDIDATE_BINDING.json` 是单一
  跟踪文件，同时只记录一个任务的授权事实。每次派发新任务前必须手动
  rebind（改写 authorization_id / branch / base_sha / task_id 等字段），
  否则 CI 读到的绑定与分支不符，fail-closed。
- **实操案例（ADT-2026-08-06-001）**：P0-001（工作区隔离协议）任务在飞
  期间，PR #78 的 CI 因绑定过期失败——绑定文件在派发时序中被其他任务
  改写，`validate_binding.py` 校验出 binding 与 PR 分支不一致，CI
  fail-closed；靠人工 rebind 后重跑才恢复。根因不是校验逻辑，而是
  "谁当前持有绑定"从未被显式记录。
- **令牌有定义无执行**：ROADMAP 的 P0（隔离 / 并发 / 令牌）把令牌列为
  预训练基建之一，但 runtime 没有任何令牌机制——没有令牌发放、没有持有
  状态记录、没有释放流程。
- **多任务争抢绑定**：并行在飞任务共享同一个绑定文件的事实源。worktree
  隔离（P0-001）已让每个 worktree 持有自己分支的 binding 副本，但
  Controller 侧（main）的绑定仍是单点，派发顺序即绑定顺序；任何 rebind
  遗漏或时序交错都会让后续任务的 CI 读到过期绑定。
- **当前状态佐证**：main 上 `CANDIDATE_BINDING.json` 的 `base_sha` 仍指向
  已合并任务的旧基线（536a34f，P0-002 已合并而绑定未更新）——"绑定过期"
  是常态而非偶发，手动 rebind 的维护负担真实存在。

### 1.2 设计目标

1. 一个任务 = 一枚令牌，持令牌者拥有绑定文件写权，归属显式化；
2. 令牌状态落盘、可查询、可审计，随绑定文件原子更新；
3. rebind 从"手动"变"自动"：派发时自动写绑定 + 令牌，消除手动 rebind；
4. 令牌数 ≤ 并发上限 N，与并发控制正交互补；
5. 纯增量：不改变 `validate_binding.py` 的检查逻辑与既有必填字段。

## 2. 令牌模型

### 2.1 一个任务 = 一枚令牌

- 令牌与任务一一对应（`ONE_TASK = ONE_TOKEN`），令牌 ID 在任务派发时生成；
- 令牌不转让、不继承、不可分割：任务关闭即令牌作废；
- 令牌是"写权凭证"而非"任务状态"：任务的受理状态（QUEUED / IN_FLIGHT /
  AGGREGATED / CLOSED）仍由并发上限协议与候选生命周期定义，令牌只回答
  "谁可以写绑定文件"。

### 2.2 令牌与 CANDIDATE_BINDING.json 的关系

- 持令牌者拥有对 `.hermes/CANDIDATE_BINDING.json` 的写权；
- 写权 = 在派发时刻更新绑定文件的授权字段（authorization_id / branch /
  base_sha / task_id / authorized_write_scope），使其与当前任务一致；
- 未持令牌者不得写绑定文件：任何 rebind 动作必须先持有令牌，否则
  fail-closed（`TOKEN_NOT_HELD`）；
- 令牌释放后，绑定文件保留最后一次写入内容作为历史事实，下一任务派发时
  原子覆盖。

### 2.3 持有状态记录在哪里（设计取舍）

**方案 A——绑定文件内嵌 `token` 字段（采用）**：

```json
"token": {
  "token_id": "TKN-2026-08-06-006",
  "task_id": "ADT-2026-08-06-006",
  "state": "HELD",
  "holder": "maker-adt-2026-08-06-006",
  "issued_at": "2026-08-06T12:00:00+08:00",
  "expires_at": "2026-08-06T14:00:00+08:00",
  "released_at": null,
  "release_reason": null
}
```

- 理由：绑定与令牌同文件、同生命周期，一次写操作原子完成"绑定任务 +
  发放令牌"，不存在两个文件不一致的窗口；
- 取舍：绑定文件语义从"纯授权"扩展为"授权 + 占用"，需按本协议字段文档
  理解；`validate_binding.py` 只校验必填字段，新增字段纯增量、不破坏 CI
  （见 §6）。

**方案 B——独立 `.hermes/HOLDER_TOKEN.json`（不采用）**：

- 取舍：令牌生命周期可与绑定解耦、职责分离；但引入第二个事实源，双文件
  原子性无法保证，违反"单一事实源"原则，且需要额外的冲突检测与恢复路径。

结论：**采用方案 A**。令牌字段由 Controller 在派发时与绑定字段同一次写入。

### 2.4 令牌字段规范

| 字段 | 类型 | 说明 |
|------|------|------|
| `token_id` | string | 令牌 ID，`TKN-{yyyy-mm-dd}-{seq}`，全局唯一 |
| `task_id` | string | 绑定的任务 ID，与绑定顶层 `task_id` 字段一致 |
| `state` | string | `HELD`（持有中）\| `RELEASED`（已释放） |
| `holder` | string | 持有者（Maker worktree 名，如 `maker-adt-2026-08-06-006`） |
| `issued_at` | string | 发放时间（ISO8601） |
| `expires_at` | string | 软过期时间（ISO8601），默认发放后 2 小时，可依任务调整 |
| `released_at` | string\|null | 释放时间；`null` 表示未释放 |
| `release_reason` | string\|null | 释放原因：`HUMAN_GATE_COMPLETE` \| `TIMEOUT` \| `FAILURE` \| `CRASH_RECOVERY` \| `CANCELLED` |

- `state=HELD` 的判定以 `released_at == null` 佐证，两者矛盾时以
  `released_at` 为准并报告（见 §7 `TOKEN_STUCK`）；
- 字段命名与绑定顶层字段同风格（snake_case）。

## 3. 令牌生命周期

```text
申请（REQUEST）→ 持有（HOLD）→ 使用（USE）→ 释放（RELEASE）
                              ↘ 异常释放（ABNORMAL_RELEASE）
```

### 3.1 申请（REQUEST）

- 时机：Controller 派发闸门通过、获得在飞名额后，与绑定写入同一次操作；
- 动作：生成 `token_id`，写绑定字段 + 令牌字段（`state=HELD`）；
- 申请即发放：令牌无 PENDING 态；名额不足（并发上限未通过）→ 任务排队，
  不生成令牌；
- 申请失败（写入失败 / 文件损坏）→ fail-closed，任务不派发
  （见 §7 `BINDING_CORRUPTED`）。

### 3.2 持有（HOLD）

- 令牌随 Dispatch Card 交付给 Maker（Dispatch Card 增加可选字段
  `TOKEN_ID`，沿用 RESOURCE_ALLOCATOR_INTEGRATION 的扩展先例）；
- 持有期间，持令牌者是绑定文件的唯一合法写者；
- 持有状态的权威记录 = 磁盘 `CANDIDATE_BINDING.json` 的 `token` 字段 +
  Controller 派发记录；两者冲突时以派发记录 + git 事实裁决（见 §7
  `TOKEN_CONFLICT`）。

### 3.3 使用（USE）

- 持令牌者在自己的 worktree 内开工；
- 绑定文件的更新（如 rebind 到自己的分支）只在持有期间发生；
- worktree 内绑定副本的 `token` 字段与 Dispatch Card `TOKEN_ID` 必须一致，
  不一致 → `TOKEN_MISMATCH` fail-closed（沿用 WORKSPACE_ISOLATION §5
  `BINDING_MISMATCH` 的恢复路径）。

### 3.4 释放（RELEASE）

正常释放条件：**Human gate 决策完成**（ACCEPT / REJECT / MODIFY）：

| Human gate 决策 | 释放时机 | 后续 |
|-----------------|----------|------|
| ACCEPT | 候选合并到 main 后 | 令牌作废；清理按 WORKSPACE_ISOLATION §3.4 |
| REJECT | 任务关闭后 | 令牌作废；任务不再受理（除非 Human 重新派发为新任务） |
| MODIFY | 修改决策完成后 | 令牌释放；修改轮次重新排队、重新申请令牌 |

释放动作（Controller 执行）：

```text
token.state = RELEASED
token.released_at = <now>
token.release_reason = HUMAN_GATE_COMPLETE
```

- 释放令牌 ≠ 释放在飞名额：在飞名额按并发上限协议由任务聚合状态决定；
  但名额释放（聚合 / 取消 / 关闭）前必须已完成令牌释放；
- 释放后、下一任务派发前，绑定文件不被任何任务写入（空闲窗口），
  消除"派发即践踏"的时序窗口。

### 3.5 异常释放（ABNORMAL_RELEASE）

| 触发 | 判定依据 | 释放动作 |
|------|----------|----------|
| 子代理超时（>600s） | 并发上限协议 `SUBAGENT_TIMEOUT` | 终止子代理 → 回收 worktree → 令牌置 RELEASED（`TIMEOUT`） |
| 子代理卡死（>30min） | 并发上限协议 `SUBAGENT_HANG` | 强制终止会话 → 清理 worktree → 令牌置 RELEASED（`TIMEOUT`） |
| 任务失败关闭 | Human / Controller 决策 | 任务关闭后令牌置 RELEASED（`FAILURE`） |
| 窗口崩溃 / 进程消失 | 无活动进程 + worktree 遗留 | 按 STALE_WORKTREE 清理后令牌置 RELEASED（`CRASH_RECOVERY`） |
| 任务取消 | Human 显式取消 | 令牌置 RELEASED（`CANCELLED`） |

异常释放完成后才能派发下一个任务；释放前必须核对 git/GitHub 事实
（分支、PR、worktree 状态），**不绕过、不强制、不猜测**。

## 4. 与并发上限的关系

- **正交但互补**：并发上限限制"同时几个任务在飞"（时间 / 资源维度）；
  令牌限制"谁可以写绑定文件"（写权仲裁维度）；
- **令牌数 ≤ 并发上限 N**：每枚令牌随一个在飞名额发放，不存在无名额的
  令牌；排队任务（QUEUED）不持有令牌、不占用绑定；
- 在飞不变量扩展为：

```text
ONE_IN_FLIGHT = ONE_TOKEN = ONE_BRANCH = ONE_WORKTREE = ONE_TASK
```

- 名额释放与令牌释放的次序：令牌先释放，名额后释放（聚合 / 取消时）；
  逆序视为异常（见 §7 `TOKEN_STUCK`）。

## 5. 与 worktree 隔离的关系

- worktree 隔离解决 agent 工作区文件的物理隔离；令牌解决 Controller 侧
  绑定单点的逻辑归属；
- 每个 worktree 持有自己分支的 binding 副本，副本内 `token` 字段记录该
  分支任务的令牌；同一时刻至多一个副本处于 `HELD` 状态（由 Controller
  派发记录保证）；
- 合并时仅被合并分支的 binding（含 token）进入 `main`；`main` 上
  binding + token 的更新与失效遵循 REPOSITORY_AS_PROMPT_RUNTIME_BINDING
  既有规则，本协议不改变；
- 不变量合并：`ONE_TOKEN = ONE_WORKTREE = ONE_BRANCH = ONE_TASK`。

## 6. 与 CI gate 的关系

- `validate_binding.py` 的检查逻辑**不变**：必填字段校验、与
  PROJECT_STATE.md 的交叉校验、scope 校验全部保持；
- `token` 字段是**新增可选字段**，脚本不校验它——老版本 CI 与新版本 CI
  行为一致，纯增量；
- 令牌机制让 rebind 从"手动"变"自动"：派发时 Controller 原子写入
  绑定 + 令牌，PR 的 CI 读到的绑定必然与分支任务一致；ADT-2026-08-06-001
  的"绑定过期导致 CI fail-closed"根因（手动 rebind 遗漏 / 时序交错）
  被消除；
- CI 仍然 fail-closed：若绑定与分支不符（异常流程导致未 rebind），CI
  照常失败，恢复路径见 §7（`TOKEN_MISMATCH` / `BINDING_CORRUPTED`）；
- 未来扩展（另行授权）：在 `validate_binding.py` 增加 token 状态校验
  （`HELD` 令牌必须与 PR 分支的 task_id 一致）。本协议**不授权**修改脚本。

## 7. 失败模式与恢复

| 代码 | 症状 | 判定 | 恢复 |
|------|------|------|------|
| `TOKEN_LOST` | binding 存在但 `token` 字段缺失 / 损坏 | 异常写入或旧版本文件 | 以 Controller 派发记录 + git 事实重建令牌；无法判定持有者时停派发（fail closed）并报告 Human |
| `TOKEN_STUCK` | 任务已关闭但 `state` 仍为 HELD | 释放动作遗漏 / 崩溃 | 核对 PR 合并状态与 Human 决策记录后强制置 RELEASED（`CRASH_RECOVERY`），报告 Human；之后才可派发新任务 |
| `TOKEN_CONFLICT` | 两个任务令牌同时 HELD（双写 / 双派发） | 派发时序错误 | 以派发记录为单一事实源：后派发者释放；停派发（fail closed）直到恢复；禁止并发写绑定 |
| `BINDING_CORRUPTED` | CANDIDATE_BINDING.json JSON 损坏 | validate_binding.py 报 HARD_STOP | 从最近一次 git 提交恢复该跟踪文件，或按派发记录重建；绑定更新由 Controller 处理，需显式授权 |
| `CRASH_RECOVERY` | 窗口崩溃遗留 HELD 令牌 | 无活动进程 + 无在飞子代理 | 按 WORKSPACE_ISOLATION §3.4 清理 worktree 后回收令牌，报告 Human 后重新派发 |
| `TOKEN_EXPIRED` | 超过 `expires_at` 仍 HELD | 任务超时 | 按 CONCURRENCY_LIMIT `SUBAGENT_TIMEOUT` 路径终止并回收令牌；延长需 Human 授权 |
| `TOKEN_MISMATCH` | worktree 内 binding 副本 token 与 Dispatch Card 不一致 | 绑定事实漂移 | fail closed：`STOPPED_BINDING_MISMATCH`，回 Holder 重新绑定（沿用 WORKSPACE_ISOLATION §5） |
| `TOKEN_NOT_HELD` | 未持令牌者尝试写绑定文件 | 写权越界 | 拒绝写入并报告；写入方必须先获得令牌（随派发） |

所有恢复路径的共同原则：**不绕过、不强制、不猜测**——任何强制回收或
重建都要先核对 git/GitHub 事实（分支、PR、worktree、派发记录）。

## 8. 与既有协议的兼容性

本协议是纯增量的：

- 不修改任何现有协议文件、CI 配置、schema 或脚本
  （`validate_binding.py` 不变）；
- `CANDIDATE_BINDING.json` 新增可选 `token` 字段，不改变既有必填字段
  与校验语义；
- 不改变候选生命周期、指纹、审计、合并的任何既有判定规则；
- 不改变并发上限的 N、排队与拒绝语义（令牌是新增的写权仲裁层）；
- 不改变 worktree 布局、命名与清理规则；
- 单一任务（当前状态）继续合法：单任务时令牌随派发自动发放、随 Human
  gate 自动释放，无额外人工步骤。

## 9. 参考

| 参考 | 关系 |
|------|------|
| `protocols/WORKSPACE_ISOLATION.md` | worktree 布局、绑定副本隔离、清理规则 |
| `protocols/CONCURRENCY_LIMIT.md` | 在飞名额、排队 / 拒绝语义、N 上限 |
| `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Dispatch Card / Progress Receipt 格式 |
| `protocols/CANDIDATE_LIFECYCLE.md` | 候选状态机、Human gate、聚合 |
| `protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` | 绑定模型、事实源 |
| `scripts/validate_binding.py` | 绑定校验（CI gate），本协议不改动 |
| `ROADMAP.md` | P0（隔离 / 并发 / 令牌）定义与后训练轨道 |
| `AGENTS.md` | 启动清单、角色边界 |
