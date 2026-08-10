> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# 工作区隔离协议（Workspace Isolation）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
RUNTIME_STATUS: `IMPLEMENTABLE`
RUNTIME_ACTIVATION: `AUTHORIZED_FOR_GIT_WORKTREE`

## 规范声明

本文档是 ADT 工作区隔离规则的规范来源。它扩展既有协议（Candidate Lifecycle、
Resource Allocator Integration、Repository-as-Prompt Runtime Binding），
**不创建**并行的路由、接收或授权系统，不改变任何角色的既有权限边界。

核心机制：`git worktree` —— 每个 agent 拥有独立的 working tree（工作目录），
隔离由 Git 原生机制保证，不依赖 agent 自律。

## 1. 问题陈述

### 1.1 现状

当前所有 agent 共享同一个工作区（单个 working tree）。多 agent 并行执行写任务时：

- **Checkout 互相覆盖**：agent A 在分支 A 上工作时，agent B 执行
  `git checkout branchB` 会把共享工作区切走，A 的未提交工作被覆盖、
  丢失或混入 B 的变更集；
- **分支切换冲突**：脏工作区（未提交、未 stash 的文件）会阻塞 checkout，
  或把 A 的未提交文件带进 B 的提交，造成 `UNEXPECTED_CHANGES`；
- **CANDIDATE_BINDING 单点争抢**：`.hermes/CANDIDATE_BINDING.json` 与
  `.hermes/checker_receipt.json` 是跟踪文件。同一工作区内切换分支会覆盖其
  磁盘内容；两个并行 agent 各自写入自己的 binding 时互相践踏，绑定事实漂移，
  触发虚假的 `FINGERPRINT_MISMATCH` 或 `STATE_DRIFT`；
- **被迫串行化**：为避免上述问题，并行任务只能排队执行，浪费资源。

### 1.2 设计目标

1. 每个 agent 拥有独立的 working tree，互不可见、互不覆盖；
2. 隔离由 Git 原生机制（一个分支同时只能被一个 worktree checkout）保证，
   不需要 agent 之间协商锁；
3. 与既有治理正交配合：Dispatch Card 授权、CANDIDATE_BINDING 绑定、
   Resource Allocator 资源分配均不改变语义，只改变文件落盘位置；
4. 主工作区（main）保持干净，作为治理读操作与合并的固定基座。

## 2. Worktree 布局规范

### 2.1 路径约定

规范布局根目录位于**主工作区之外**（仓库的兄弟目录），每个仓库一个子目录：

```text
<repo-parent>/
  <repository-name>/                          # 主工作区：仅 main，只读治理操作
  .adt-worktrees/
    <repository-name>/
      <agent-name>/                           # 单个 agent 的 worktree
```

本仓库（`butbutbutbutbutbut/adaptive-digital-team`）示例：

```text
C:\Users\<USER>\
  adaptive-digital-team\                      # 主工作区（main）
  .adt-worktrees\
    adaptive-digital-team\
      maker-adt-2026-08-06-001\               # Maker worktree
      checker-adt-2026-08-06-001\             # Checker worktree（只读）
```

### 2.2 为什么不用仓库内的 `.worktrees/`

任务模板中常见的 `.worktrees/<agent-name>/`（仓库内）形式**不采用**，原因：

- 仓库内 worktree 目录会作为未跟踪内容污染主工作区，需修改 `.gitignore`
  （超出协议文件范围，且污染每次 diff）；
- 嵌套目录易被 CI、扫描器与工具误判为仓库内容；
- Git 允许仓库内 worktree，但主工作区的 `git status` 永远带着未跟踪目录噪音，
  破坏 `Repository as Prompt` 的干净恢复语义。

因此规范采用**主工作区之外的兄弟目录** `.adt-worktrees/<repository-name>/`，
命名模式仍保留 `<agent-name>/` 约定。

### 2.3 命名规则

- `<agent-name>` = `<role>-<task-id>`，全部小写；
- `<role>` ∈ `{maker, checker, holder, control}`；
- `<task-id>` 取 Dispatch Card 的 `TASK_ID`，转小写；
- 字符集限制：`[a-z0-9-]`，禁止点号、下划线、空格、非 ASCII；
- 示例：
  - `maker-adt-2026-08-06-001`
  - `checker-adt-2026-08-06-001`
  - `holder-adt-2026-08-06-001`

### 2.4 绑定不变量

```text
ONE_WORKTREE = ONE_BRANCH = ONE_TASK
```

（扩展自 Candidate Lifecycle 的 `ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN`）

- 一个 worktree 同时只 checkout 一个分支；
- 一个分支同时只能被一个 worktree checkout —— Git 原生强制：
  第二次 `git worktree add` 同一分支会失败并报
  `fatal: '<branch>' is already checked out at '<path>'`；
- 主工作区永远停留在 `main`，不承载任何并行写任务；
- 违反上述不变量即失败关闭（fail closed），不得用 `--force` 绕过。

## 3. Worktree 生命周期

### 3.1 创建（CREATE）

- 由 Task Holder 在 dispatch 时创建，或显式授权 Maker 自行创建；
- Maker（写任务，从 Base 拉新分支）：

```bash
git worktree add -b <branch> "<path>" <base_sha>
```

- Checker（只读审查，检出候选分支）：

```bash
git worktree add --detach "<path>" <candidate_head_sha>
```

- 创建后必须验证（见 `docs/worktree-quickstart.md` § 验证）：

```text
- git rev-parse HEAD            == Dispatch Card BASE_SHA（Maker）
- git branch --show-current     == Dispatch Card BRANCH（Maker）
- git status                    干净
- git worktree list             路径与分支绑定正确
```

### 3.2 使用（USE）

- 所有写操作（编辑、add、commit）只在本 worktree 内发生；
- 提交只推送到本 worktree 绑定的分支；`main` 的推送仍需 Publish Lease；
- `.hermes/CANDIDATE_BINDING.json` 与 `.hermes/checker_receipt.json` 是
  跟踪文件：每个 worktree 持有**自己分支的版本**，天然消除单点争抢；
- worktree 内禁止 `git checkout` 切换到其他分支（违反绑定不变量）。

### 3.3 关闭（CLOSE）

- Maker 完成提交后，worktree **保留**，供独立 Checker 在同一分支上只读审查；
- Checker 完成审查后，worktree 按 Dispatch Card 的 `NEXT_GATE` 决定去留；
- 关闭 = 提交完成 + 工作区干净；关闭不等于删除。

### 3.4 清理（CLEANUP）

- 仅在候选合并完成后（或任务被显式取消且获得授权时）清理；
- 清理命令（在**主工作区**或任意 worktree 中执行均可）：

```bash
git worktree remove "<path>"      # 工作区必须干净；必要时先 commit 或 discard
git worktree prune                # 清理过期 bookkeeping
```

- 分支删除仍需 Publish Lease（`BRANCH_DELETE_ALLOWED=YES`），
  遵循既有分支生命周期规则；
- 清理后再次验证 `git worktree list` 只剩主工作区。

## 4. 与现有协议的关系

### 4.1 Dispatch Card

沿用 `protocols/RESOURCE_ALLOCATOR_INTEGRATION.md` 的扩展先例，
Dispatch Card 增加一个可选字段：

```text
PACKET: DISPATCH_CARD
...
BRANCH:
WORKTREE: <absolute path of the agent worktree, or PENDING>
NEXT_GATE:
```

- `WORKTREE=PENDING`：Holder 尚未创建 worktree，Maker 须先自建再开工；
- Maker 开工前必须确认 worktree 路径与 Dispatch Card 一致（路径即授权的一部分）。

### 4.2 CANDIDATE_BINDING.json（单点争抢的消除）

- 绑定文件随分支隔离：每个 agent 只写**自己分支的副本**，互不可见、互不覆盖；
- 合并时仅被合并分支的 binding 进入 `main`；`main` 上 binding 的更新与失效
  遵循 `protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` 既有规则，本协议不改变；
- 绑定校验（`scripts/validate_binding.py`）在 worktree 内读取本地文件，
  读取语义不变。

### 4.3 Resource Allocator

- 工作区隔离是**无条件的**：无论 `RESOURCE_TIER` 是 economy 还是 strong，
  每个写任务都使用独立 worktree，不共享、不降级；
- tier 只影响 token 预算、推理深度、迭代上限，不影响布局。

### 4.4 Candidate Lifecycle 与 Checker 独立性

- Checker 在自己的 worktree 中以只读方式检出候选分支，
  与 Maker 的工作目录物理隔离，强化 Checker 独立性要求；
- 候选指纹（fingerprint）按 `protocols/CANDIDATE_LIFECYCLE.md` 计算，
  worktree 布局不进入指纹字段。

### 4.5 Repository-as-Prompt 启动

- `AGENTS.md` 的启动清单已包含 worktree 校验；
- 每个新 worktree 都是一次干净启动：读 `AGENTS.md`、`PROJECT_STATE.md`，
  核对分支、HEAD、绑定，再开工。

## 5. 失败模式与恢复

| 代码 | 症状 | 判定 | 恢复 |
|------|------|------|------|
| `WORKTREE_BRANCH_CONFLICT` | `git worktree add` 报 `already checked out at '<path>'` | 分支已被另一 worktree 占用 | STOP；`git worktree list` 定位占用者；`FACT_SOURCE_REBIND`，禁止 `--force` |
| `BINDING_MISMATCH` | worktree 内 `CANDIDATE_BINDING.json` 与 Dispatch Card 不一致（authorization_id / branch / base_sha） | 绑定事实漂移 | fail closed：`STOPPED_BINDING_MISMATCH`，回到 Holder 重新绑定 |
| `BASE_DRIFT` | worktree HEAD != Dispatch Card `BASE_SHA` | 基线漂移 | STOP；`STOPPED_BASE_DRIFT`，等待 Human 重新授权（与既有 Base Drift 规则一致） |
| `STALE_WORKTREE` | 崩溃/断电遗留 worktree | 无进程占用但目录存在 | `git worktree list` 定位；确认无活动任务后 `git worktree remove` + `prune` |
| `DIRTY_WORKTREE` | `git worktree remove` 因未提交变更失败 | 有未提交内容 | 先 commit 到绑定分支，或确认丢弃后 `git worktree remove --force`（仅限已授权丢弃） |
| `WINDOWS_PATH_ERROR` | 路径含空格/超长路径/大小写问题导致 add 失败 | 路径不规范 | 用短路径、引号包裹；agent 名保持 `[a-z0-9-]`；必要时启用 Windows 长路径支持 |

所有恢复路径的共同原则：**不绕过、不强制、不猜测**。任何需要 `--force`
或改写历史的操作都必须先获得显式授权。

## 6. 与既有协议的兼容性

本协议是纯增量的：

- 不修改任何现有协议文件、CI 配置、schema 或脚本；
- 不改变 Dispatch Card / Progress Receipt 的既有必填字段；
- 不改变绑定、指纹、审计、合并的任何既有判定规则；
- 单一 worktree（当前状态）继续合法：主工作区即唯一 worktree，
  本协议只约束**并行**写任务必须隔离。

## 7. 参考

| 参考 | 关系 |
|------|------|
| `protocols/CANDIDATE_LIFECYCLE.md` | 候选生命周期、指纹、`ONE_TASK=ONE_BRANCH=ONE_PR` |
| `protocols/RESOURCE_ALLOCATOR_INTEGRATION.md` | Dispatch Card 扩展先例、资源层级 |
| `protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` | 绑定模型、事实源 |
| `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` | Dispatch Card / Progress Receipt 格式 |
| `docs/worktree-quickstart.md` | 操作命令速查（agent 与人类） |
| `AGENTS.md` | 启动清单、角色边界、非协商边界 |
