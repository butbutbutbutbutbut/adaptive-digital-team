# GATE — 执行门控核（事中）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PHASE: `DURING`（事中 —— 每个动作时刻评估）
LAYER: `EXECUTION_CORE_2_OF_3`
NORMATIVE_SOURCE: 本文档是执行层三核之一。工作区隔离、并发上限、Runtime Adapter、资源分配、候选生命周期的完整底层规则仍以 `protocols/WORKSPACE_ISOLATION.md`、`protocols/CONCURRENCY_LIMIT.md`、`protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md`、`protocols/RESOURCE_ALLOCATOR_INTEGRATION.md`、`protocols/CANDIDATE_LIFECYCLE.md` 为准；本文档只做相位归集与强制力声明，不创造新规则。

## 1. 相位定义

GATE 核管辖**写任务执行期间**的每一个动作：文件写入、git add / commit / push、worktree 操作、令牌使用。它只回答一个问题：**"这个动作此刻是否在授权内？"**

- 每个动作都过闸：写入前检查 scope、路径、分支、base、drift、令牌。
- 治理失效只发生在动词上 —— 本核是"动作时刻"的唯一拦截者。
- BINDING 定义 what（授权集静态定义），GATE 校验 when（动作时刻评估）。

## 2. 铁律

```text
越界即拦，故障关闭
```

任何越界（scope 外、路径逃逸、未授权动作、令牌异常、并发超限）→ 当场 BLOCKED；任何不确定（探测失败、事实冲突、无法判定）→ 按故障关闭处理，不得放行、不得降级、不得猜测。

```text
不绕过、不强制、不猜测
```

## 3. 不变量清单

| # | 不变量 | 违反后果 |
|---|--------|----------|
| G1 | `ONE_WORKTREE = ONE_BRANCH = ONE_TASK`：一个 worktree 只 checkout 一个分支；一个分支同时只能被一个 worktree 占用（Git 原生强制） | `WORKTREE_BRANCH_CONFLICT` |
| G2 | 主工作区（main）不承载并行写任务；写任务全部在 `.adt-worktrees/<repo>/<agent>/` 内 | 布局违规即 fail-closed |
| G3 | 并发上限 `N=2`（默认）；仅 Human Holder 可调整；硬上限 `N_MAX=4`；Controller 只能 fail-safe 降级到 N=1（持续超时 ≥3/10 时）并报告 Human | `CONCURRENCY_REJECTED` / `SLOT_LEAK` |
| G4 | 队列有界 `MAX_QUEUE = 2×N`（默认 4），`QUEUE_TTL` 默认 15 分钟，超时/满 → `CONCURRENCY_REJECTED` | `QUEUE_DEADLOCK` |
| G5 | 路径安全：拒绝绝对路径、拒绝 `..` 段、拒绝 symlink 逃逸；写入前 resolve 并强制仓库内 | `SCOPE_VIOLATION` / `ATTEMPTED_SCOPE_VIOLATION` |
| G6 | 写入前 scope 校验：实际变更文件 ⊆ `authorized_write_scope`；scope 缺失/为空 → fail-closed | `SCOPE_VIOLATION` |
| G7 | base drift 检查：git 探测失败 → 写操作 BLOCKED，不得跳过 drift 检查 | `HARD_STOP` / `BASE_DRIFT` |
| G8 | 令牌每动作校验：动作必须对应 HELD 令牌；异常走恢复表（§8） | `TOKEN_NOT_HELD` / `TOKEN_LOST` / `TOKEN_MISMATCH` |
| G9 | 人类上限：Point / 资源 / 消息 / token / scope 上限超出 → `BLOCKED` | 分配阻断（拔牙③，§9） |

## 4. 机器载体

| 载体 | 作用 |
|------|------|
| `.hermes/plugins/guarded_adapter/gate.py` | 动作校验核心：scope 匹配、路径归一化、drift 检查、令牌校验 |
| `.hermes/plugins/guarded_adapter/tools/guarded_write.py` | 受控写入：路径 resolve、越界拒绝、绑定缺失拒绝（无 fallback） |
| `.hermes/plugins/guarded_adapter/tools/guarded_repo_actions.py` | 受控 git 动作：commit / push / PR 等，按授权动作集放行 |
| `git worktree` | 空间隔离的物理载体 |
| `scripts/validate_binding.py` / `scripts/validate_adapter.py` | 静态校验器（CI），binding 损坏 → `HARD_STOP` |

## 5. 路径安全（G5 细化）

统一路径处理管线：

```text
1. 规范化前置：path.replace("\\", "/")           # 双平台统一
2. os.path.normpath 归一化
3. 拒绝绝对路径
4. 规范化后仍含 ".." 段 → 拒绝
5. target = (_REPO_ROOT / path).resolve()          # 解析 symlink
6. 强制 target.relative_to(_REPO_ROOT.resolve())   # 越界抛异常 → BLOCKED
```

- scope 前缀匹配在**规范化后**的路径上做（`a/` 不得匹配 `a/../secret`）。
- 写入 / 暂存前必须走第 5–6 步，覆盖 symlink 指向仓库外场景。
- 路径 / scope 的大小写变体按平台语义归一化后校验。

## 6. 并发上限（G3/G4 细化，吸收 CONCURRENCY_LIMIT）

- 在飞 = 已派发未聚合：从 Dispatch Card 发出占用名额，到合并 / 取消 / 收到最终回执关闭释放名额。
- 只读任务（Checker 审查、审计）不占名额；排队任务不占名额不分配 worktree。
- 名额生命周期：派发 +1，聚合/取消/关闭 -1。
- 调整权：只有 Human Holder。Controller 观测到最近 10 个已派发任务超时 ≥3 → 自动 fail-safe 降级 N=1 并报告；恢复 N=2 需 Human 确认；升 N=3 仅 Human 显式指示且须满足观测条件，`N_MAX=4` 防无界回归。
- 队列严格 FIFO，无插队通道；Human 需要优先时先聚合/取消在飞任务释放名额。

## 7. Token 每动作校验（G8 细化，吸收 HOLDER_TOKEN §3.3/§7）

- 持令牌者是绑定文件的唯一合法写者；绑定更新（rebind）只在持有期间发生。
- worktree 内绑定副本的 `token` 字段与 Dispatch Card `TOKEN_ID` 必须一致，不一致 → `TOKEN_MISMATCH` fail-closed。
- 每个写动作校验：绑定有效 + 令牌 HELD + 动作在授权集内，三者齐备才放行。

## 8. Token 异常回收恢复表（回收必须报告 Human，恢复绝不猜测）

| 代码 | 症状 | 判定 | 恢复 |
|------|------|------|------|
| `TOKEN_LOST` | binding 存在但 `token` 字段缺失/损坏 | 异常写入或旧版本文件 | 以 Controller 派发记录 + git 事实重建；无法判定持有者时停派发（fail-closed）并**报告 Human** |
| `TOKEN_CONFLICT` | 两个任务令牌同时 HELD（双写/双派发） | 派发时序错误 | 以派发记录为单一事实源：后派发者释放；停派发（fail-closed）直到恢复；禁止并发写绑定；**报告 Human** |
| `BINDING_CORRUPTED` | CANDIDATE_BINDING.json JSON 损坏 | validate_binding 报 `HARD_STOP` | 从最近一次 git 提交恢复跟踪文件，或按派发记录重建；绑定更新由 Controller 处理，需显式授权；**报告 Human** |
| `SUBAGENT_TIMEOUT` | 子代理 >600s 未返回 | 任务级超时 | 终止子代理 → 回收 worktree → 令牌置 RELEASED（`TIMEOUT`）→ **报告 Human**；是否重试由 Human 决定（作为新任务） |
| `SUBAGENT_HANG` | 子代理无输出且 >30min（`TASK_MAX_WALL`） | 卡死 | 强制终止会话 → 清理 worktree（未提交内容先 commit 或经授权丢弃）→ 令牌置 RELEASED（`TIMEOUT`）→ **报告 Human**；禁止自动无限重试 |
| `TOKEN_STUCK` | 任务已关闭但 `state` 仍 HELD | 释放动作遗漏/崩溃 | 核对 PR 合并状态与 Human 决策后强制置 RELEASED（`CRASH_RECOVERY`）→ **报告 Human**；之后才可派发新任务 |
| `TOKEN_EXPIRED` | 超过 `expires_at` 仍 HELD | 任务超时 | 按 SUBAGENT_TIMEOUT 路径终止并回收；延长需 Human 授权；**报告 Human** |
| `TOKEN_MISMATCH` | worktree 内 binding 副本 token 与 Dispatch Card 不一致 | 绑定事实漂移 | fail-closed：`STOPPED_BINDING_MISMATCH`，回 Holder 重新绑定 |
| `TOKEN_NOT_HELD` | 未持令牌者尝试写绑定文件 | 写权越界 | 拒绝写入并**报告 Human**；写入方必须先获得令牌（随派发） |
| `CRASH_RECOVERY` | 窗口崩溃遗留 HELD 令牌 | 无活动进程 + 无在飞子代理 | 按 WORKSPACE_ISOLATION 清理 worktree → 回收令牌 → **报告 Human** → 重新派发 |

异常释放完成前不得派发下一个任务；释放前必须核对 git/GitHub 事实（分支、PR、worktree 状态），**不绕过、不强制、不猜测**。

## 9. 拔牙③：人类上限 BLOCKED（吸收 RESOURCE_ALLOCATOR / DYNAMIC_ROUTER §7.2）

人类设定的硬上限是分配闸门，任何超出即 `BLOCKED`，不得静默超支或推断更大边界：

| 上限 | 默认 | 超出后果 |
|------|------|----------|
| 并发在飞数 N | 2（Human 才能改，≤4） | `CONCURRENCY_REJECTED` |
| 推荐 Point / 硬上限 Point | 0–2（recommended ≤ hard_max） | `BLOCKED` |
| 外部消息数 `max_external_messages` | 0–10 | `BLOCKED` |
| Token 预算 | 按 tier（economy ~8k / standard ~32k / strong ~128k） | `BLOCKED` |
| Checker 分配 | 按 `checker_timing`（NONE / AFTER_FORMAL_CANDIDATE / NOW） | `BLOCKED` |
| 授权 scope | 精确路径集 | `SCOPE_VIOLATION` |

`HUMAN_OVERRIDE=true` 是资源 tier 可偏离风险默认映射的唯一合法情况；下游不得二次推断。SAFETY_RISK / RESOURCE_TIER / CHECKER_TIMING 三控制独立，HIGH 风险不自动选 strong、不自动开 Checker。

## 10. fail-closed 行为表

| 条件 | 行为 |
|------|------|
| 绑定缺失 / 损坏（无 fallback，禁止从 PROJECT_STATE.md 合成授权） | `BLOCKED` |
| scope 自含 `.hermes/CANDIDATE_BINDING.json` | `BLOCKED`（validator 拒绝） |
| 路径逃逸（绝对 / `..` / symlink 出库） | `BLOCKED`（`ATTEMPTED_SCOPE_VIOLATION`） |
| git 探测返回空（drift 无法判定） | 写操作 `BLOCKED`（不得跳过 drift 检查） |
| 动作不在授权动作集（ready/merge/close_pr/delete_branch 未授权） | `UNAUTHORIZED_ACTION` |
| worktree 与 Dispatch Card 不符（WORKTREE / BASE_SHA / BRANCH） | fail-closed，禁止 `--force` 绕过 |
| 分支被另一 worktree 占用 | `WORKTREE_BRANCH_CONFLICT`：STOP → `git worktree list` 定位 → `FACT_SOURCE_REBIND` |
| 绑定事实漂移 | `STOPPED_BINDING_MISMATCH`，回 Holder 重新绑定 |
| base 漂移 | `STOPPED_BASE_DRIFT`，等待 Human 重新授权 |
| 窗口崩溃遗留 worktree | `STALE_WORKTREE`：定位 → 确认无活动任务 → 清理 |
| 令牌异常（§8 表） | 按表恢复，全部报告 Human |
| 名额/计数不确定 | fail-closed 不派发新任务，以派发记录为单一事实源 |

## 11. 吸收协议对照表

| 源协议 | 被吸收内容 | 新位置 |
|--------|-----------|--------|
| `WORKSPACE_ISOLATION.md` | worktree 布局、`ONE_WORKTREE=ONE_BRANCH=ONE_TASK`、清理规则、恢复表 | §3 G1/G2、§10 |
| `CONCURRENCY_LIMIT.md` | N=2 默认 / N_MAX=4 / 队列 / SUBAGENT_TIMEOUT / SUBAGENT_HANG / QUEUE_DEADLOCK / SLOT_LEAK | §3 G3/G4、§6、§8 |
| `ADT_RUNTIME_ADAPTER_CONTRACT.md` | 三层隔离（Layer 1 凭证不进 Core）、`SESSION_PRINCIPAL ≠ Human Holder`、`plan.write_scope ⊆ auth.authorized_write_scope`、强制错误表 | §4、§10 |
| `HOLDER_TOKEN.md` | Token 每动作校验与异常回收（§7/§3.3） | §7、§8 |
| `RESOURCE_ALLOCATOR_INTEGRATION.md` | 人类上限 BLOCKED（**拔牙③**）、tier 一次性解析 | §9 |
| `CANDIDATE_LIFECYCLE.md` | 预写执行门（detached HEAD / 分支 / base / 祖先 / drift）、scope 覆盖模式 | §3 G6/G7、§10 |

## 12. 跨相位升级规则（引用 BINDING）

1. **越界请求**（scope 外 / 未授权动作）→ 停机上报 **BINDING**（Human 重授权），禁止就地扩权。
2. **base 漂移** → 唯一出口：关闭当前候选、从最新 main 开新任务（见 `protocols/BINDING.md` §12）。
3. **事实源冲突** → `FACT_SOURCE_REBIND`：停机上报 Human，任何核不得推进。
4. **crash 异常回收**（§8）→ 回收动作在本核，但结果必须报告 Human；Human 解锁前不派发新任务。
5. **push 后 CI 异步等待** → 不属于本核决策；CI 等待期归 RECEIPT 证据收集态（token 保持 HELD 属正常）。
6. 本核不处理：授权定义（→ BINDING）、验收与合并（→ RECEIPT）。跨相位决策一律上报，不就地扩权。

## 13. 兼容与边界

- 本文档是 19 协议 → 3 执行核重构的产物，**不废弃**底层源协议；源协议为完整规范，本文档为相位归集与强制力声明。
- 只读任务（Checker 审查）不消耗在飞名额，但仍受路径安全与只读纪律约束。
- 发现旧协议与三核文档冲突 → 登记到 M7 废弃对照（NORMATIVE_MAP），不擅自改旧协议。
