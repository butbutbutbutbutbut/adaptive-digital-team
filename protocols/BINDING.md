# BINDING — 授权绑定核（事前）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PHASE: `BEFORE`（事前 —— 派单时刻与绑定原子写）
LAYER: `EXECUTION_CORE_1_OF_3`
NORMATIVE_SOURCE: 本文档是执行层三核之一。候选生命周期、路由、指令授权的完整底层规则仍以 `protocols/CANDIDATE_LIFECYCLE.md`、`protocols/DYNAMIC_GOVERNANCE_ROUTER.md`、`protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md` 为准；本文档只做相位归集与强制力声明，不创造新规则。

## 1. 相位定义

BINDING 核管辖**写任务开始之前**的全部授权事实：任务是谁的、绑在哪个仓库、哪个 Base、哪个分支、哪些文件、什么动作、谁持有令牌。它只回答一个问题：**"这枝笔凭什么能动？"**

- 适用：任何有仓库写意图的任务（候选实现、修复、治理文件变更、外部项目绑定）。
- 不适用：纯对话 / 只读任务（A/B 模式）不强制完整 BINDING，但证据纪律（FACT/AUTHORITY/RESULT 一行留痕）仍然适用。
- 一个任务只能发生一次 BINDING（派单时刻）；事后改绑定属于跨相位升级（见 §12）。

## 2. 铁律

```text
无绑定不动笔
```

任何写入动作（edit / add / commit / push / PR / merge / close / delete）之前，必须存在一个**有效绑定**：精确仓库 + 精确 Base SHA + 精确分支 + 精确授权文件集 + 精确授权动作集 + 有效令牌。缺任一项 → fail-closed，停笔上报。

```text
NO_UNBOUND_EXECUTION（全局不变量）
```

## 3. 不变量清单

| # | 不变量 | 违反后果 |
|---|--------|----------|
| I1 | `ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN`，候选 PR 直指 main | `STACKED_PR_PROHIBITED` |
| I2 | Base 必须精确匹配（`BASE_SHA` 是 commit 且为当前 HEAD 祖先），禁止 base 漂移开工 | `HARD_STOP` / `BASE_DRIFT` |
| I3 | 候选分支必须派生自 main（无非 main 父提交） | `HARD_STOP` |
| I4 | `authorized_write_scope` 静态定义授权文件集（显式路径 / fnmatch 模式），禁绝对路径、禁 `..`、禁重复项 | `SCOPE_VIOLATION` |
| I5 | 授权动作集默认不含 ready / merge / close_pr / delete_branch；出现即拒绝 | `UNAUTHORIZED_ACTION` |
| I6 | 一任务一令牌：`ONE_IN_FLIGHT = ONE_TOKEN = ONE_BRANCH = ONE_WORKTREE = ONE_TASK` | `TOKEN_CONFLICT` |
| I7 | 事实源唯一：启动时解析出唯一权威事实源，冲突即 `FACT_SOURCE_REBIND` | `FACT_SOURCE_REBIND` |
| I8 | 指纹绑定：repository / base_ref / base_sha / head_ref / head_sha / sorted(changed_files) 六字段 SHA-256 指纹贯穿 BINDING→GATE→RECEIPT | `FINGERPRINT_MISMATCH` |

## 4. 机器载体

| 载体 | 作用 |
|------|------|
| `.hermes/CANDIDATE_BINDING.json` | 唯一运行时绑定记录（授权 + 令牌同文件原子写） |
| `scripts/validate_binding.py` | 绑定校验器：身份、scope、base、指纹、UNGRANTED 空闲态豁免 |
| Dispatch Card | 派单时刻携带 TASK_ID / AUTHORIZATION_ID / BASE_SHA / BRANCH / ALLOWED_FILES / FORBIDDEN_ACTIONS / TOKEN_ID |
| `.adt/project-binding.yaml` | 外部项目绑定文件（拔牙②，见 §8） |

## 5. 事实源优先级阶梯

启动（新窗口 / 新任务 / 事实冲突 / 新 Human receipt / 绑定 SHA 变化 / gate 变化）时必须解析唯一权威事实源，优先级从高到低：

| 优先级 | 来源 | 条件 |
|--------|------|------|
| 5（最高） | Human 显式声明 branch + SHA | 必须在下一次授权写时持久化到绑定文件 |
| 4 | 绑定记录中的 active_candidate | `resolved_head` 与线上远程一致（live 解析，禁止信任陈旧缓存） |
| 3 | 含 Human 绑定证据的开放 PR | PR 描述或 commit message 含 Human 绑定声明 |
| 2 | 含 ADT 绑定记录的分支 HEAD | 远程分支 tip 提交含有效 `.adt/project-binding.yaml` 或绑定声明 |
| 1（最低） | main（仅治理源） | main 默认只作治理源，未经 Human 显式声明不得自动当作产品事实源 |

约束：`resolved_head` 每次绑定读取都必须 `git ls-remote` 现查；"最近提交时间"不得单独决定事实源；PR Head 不得自动覆盖独立声明的候选分支；`visual_status` 独立于上传 / 构建 / CI 状态。治理基座与产品事实源可同分支但必须显式声明，未声明即 `GOVERNANCE_PRODUCT_BASE_CONFLATED` fail-closed。

## 6. 指令路由与授权（吸收 INSTRUCTION_ROUTING_AND_AUTHORITY）

### 6.1 受治理指令必须携带完整头部

```text
FROM:            # 签发者与授权责任主体
TO:              # 正式接收者
CC:              # 仅知会，无执行/验收/合并权
EXECUTOR:        # 唯一执行者
CHECKER:         # 独立验收者（不得与 EXECUTOR 相同）
REPOSITORY:      # 单一 owner/repository
SUBJECT:         # 精确授权事项
AUTHORIZATION_ID: # 唯一授权标识
```

### 6.2 头部缺失的 fail-closed 表

| 缺失字段 | 后果 |
|----------|------|
| FROM / TO / 角色冲突或歧义 | `GATE_BLOCKED` |
| EXECUTOR | `NO_WRITE_ALLOWED` |
| CHECKER | `NO_ACCEPTANCE_OR_MERGE_ALLOWED` |
| REPOSITORY | `NO_REPOSITORY_ACTION_ALLOWED` |
| AUTHORIZATION_ID | `NO_WRITE_ALLOWED` |
| EXECUTOR 与 CHECKER 同一人 | `SELF_ACCEPTANCE_BLOCKED` |

缺失角色不得从窗口名、上下文、历史习惯、相邻任务推断。转发指令必须保留完整原头部与 AUTHORIZATION_ID；转发不得把 CC 变 EXECUTOR、不得替换 CHECKER、不得扩大仓库 / 路径 / 动作 / scope；改 EXECUTOR / CHECKER / 仓库 / scope 需要新授权。一次性授权用后标 `CONSUMED`；未消费授权不得转移；已消费不得复用。

## 7. 动态治理路由的分派包部分（吸收 DYNAMIC_GOVERNANCE_ROUTER）

### 7.1 HARD_STOP 路由表（BINDING 事前拦截，违反即 STOP）

| 情形 | 结果 |
|------|------|
| auto-Ready / auto-Merge / auto-delete 分支 | `HARD_STOP` |
| force-push / rebase / amend / 任何未授权历史改写 | `HARD_STOP` |
| 能力推断授权（有工具 ≠ 有权限） | `HARD_STOP` |
| Maker 与 Checker 角色坍缩（同一窗口 / 同一上下文兼任） | `HARD_STOP` |
| base_ref != main（叠 PR） | `STACKED_PR_PROHIBITED` |
| Control Packet 不完整（缺 authorization_id / from / to / executor / repository / base_sha） | `HUMAN_DECISION_REQUIRED`，零写权 |
| 只读请求扩张为修复 / 实现 / 写 | 拒绝扩张 |
| 无验证 Base 就请求仓库写 | 阻断直至 Base 验证通过 |
| 缺失精确 write scope | `HUMAN_DECISION_REQUIRED` |

### 7.2 路由只产出候选计划

路由输出 `GovernancePlan` 只是候选/拒绝规划态；Human Holder 授权是独立闸门，不可从计划推断。`route` 绝不被 `adapter_error` 覆盖。

## 8. 拔牙②：外部项目绑定固定全量 SHA 校验（fail-closed）

外部项目仓库通过固定绑定进入 ADT 治理：

```yaml
# .adt/project-binding.yaml（外部项目仓库根）
schema_version: "1"
adt_repository: <owner>/adaptive-digital-team
adt_pin: <ADT 组织仓库固定全量 commit SHA>
product_repository: <owner/repo>
governance_base:
  branch: main
  sha: <full SHA>
```

校验规则（fail-closed，任一不满足即拒绝开工并上报）：

| 条件 | 结果 |
|------|------|
| 绑定文件缺失 | 拒绝（`BINDING_MISSING`） |
| 绑定文件冲突（多个绑定 / 字段互相矛盾） | 拒绝（`BINDING_CONFLICT`） |
| 绑定过期（`adt_pin` 或 `governance_base.sha` 与实测不符 / 陈旧缓存） | 拒绝（`BINDING_STALE`），必须 live 解析 |
| 绑定引用的 ADT 仓库不可访问 | 拒绝（`BINDING_UNREACHABLE`） |
| `adt_pin` 不是固定全量 SHA（短 SHA / 分支名 / 通配） | 拒绝（`BINDING_PIN_INVALID`） |
| 通过绑定进入后：先读项目 AGENTS.md → 项目 binding → 经固定 SHA 解析 ADT 仓库 → 读 PROJECT_STATE.md → 验证项目 git 状态 → 读授权/Control Lease（存在时） | 顺序错即重来 |

## 9. 拔牙①：Authority Dispatch Card 模板

Controller 在派发任何写任务之前，MUST 生成 Authority Dispatch Card。字段即契约：

```text
AUTHORITY DISPATCH CARD
  TASK_ID: ADT-{date}-{seq}
  AUTHORITY_SOURCE: 授权来源（Kairos / Human Holder 拍板记录）
  HUMAN_ROLE: 授权 Human 的角色
  ISSUED_AT: ISO 8601 timestamp
  EXPIRES_AT: 过期时间或 SESSION_SCOPE
  AUTHORIZED_ACTIONS: [枚举授权操作列表]
  BOUNDARY:
    REPOSITORY: 仓库路径
    BASE_SHA: 基准 commit（全量 SHA）
    BRANCH: 分支名
    FILES_IN_SCOPE: [授权文件列表]
  PUBLISH_LEASE:
    PUSH_ALLOWED: NO
    DRAFT_PR_ALLOWED: NO
    READY_ALLOWED: NO
    MERGE_ALLOWED: NO
    BRANCH_DELETE_ALLOWED: NO
  TOKEN_ID: TKN-{date}-{seq}     # 与绑定文件 token 字段一致
  RESOURCE_TIER: economy | standard | strong
```

规则：授权卡必须能独立验证才有效（字段齐全、来源可查）；`PUBLISH_LEASE` 全部为 NO 时，任何 push / PR / ready / merge / 删分支 动作都被物理阻断；授权卡与绑定文件任何字段不一致 → `BINDING_MISMATCH` fail-closed。

## 10. Token 的发放与登记（派单时刻与绑定原子写）

- 令牌随派发自动发放：Controller 派发闸门通过、获得在飞名额后，**同一次写操作**完成"绑定任务 + 发放令牌"（`state=HELD`），不存在双文件不一致窗口。
- 令牌字段内嵌于 `CANDIDATE_BINDING.json`：

```json
"token": {
  "token_id": "TKN-{yyyy-mm-dd}-{seq}",
  "task_id": "ADT-{date}-{seq}",
  "state": "HELD",
  "holder": "maker-<task-id>",
  "issued_at": "<ISO8601>",
  "expires_at": "<ISO8601，默认发放后 2h>",
  "released_at": null,
  "release_reason": null
}
```

- 令牌不转让、不继承、不可分割；任务关闭即作废。令牌数 ≤ 并发上限 N；排队任务（QUEUED）不持有令牌、不占用绑定。
- 未持令牌者写绑定文件 → `TOKEN_NOT_HELD` 拒绝。
- 令牌的**校验与回收**属于 GATE 核（见 `protocols/GATE.md` §8），**释放**属于 RECEIPT 核（见 `protocols/RECEIPT.md` §9）。

## 11. 吸收协议对照表

| 源协议 | 被吸收内容 | 新位置 |
|--------|-----------|--------|
| `CANDIDATE_LIFECYCLE.md` | 身份（运行时派生）、指纹（六字段 SHA-256）、状态机、拓扑 `ONE_TASK=ONE_BRANCH=ONE_PR` | 本核 I1/I8 + §7.1 |
| `INSTRUCTION_ROUTING_AND_AUTHORITY.md` | 指令头部、角色规则、转发规则、授权消费 | §6 |
| `DYNAMIC_GOVERNANCE_ROUTER.md` | 分派包部分：路由优先级、HARD_STOP 表、Control Packet 完整性 | §7 |
| `REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` | 单一事实源、事实源优先级阶梯、启动协议、`GOVERNANCE_PRODUCT_BASE_CONFLATED` | §5 |
| `HOLDER_TOKEN.md` | Token 发放与登记（派单时刻原子写） | §10 |
| `ADT_ANTI_OBJECTIVE_PROMPT.md` | **拔牙①** Authority Dispatch Card 模板 | §9 |
| `REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` | **拔牙②** 外部绑定固定全量 SHA 校验 | §8 |
| `ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` | `NO_UNBOUND_EXECUTION` 全局不变量 | §2 |

## 12. 跨相位升级规则

1. **GATE 发现越界请求**（scope 外动作、未授权动作、令牌异常）→ **停机上报本核（BINDING）**：由 Human 重新授权，禁止就地扩权。
2. **base 漂移**（main 已前进、声明 Base 过期）→ 唯一出口：**关闭当前候选，从最新 main 开新任务**（新分支 / 新 PR / 新指纹 / 新授权）。禁止 rebase 救场。
3. **事实源冲突**（任一带牙核自检发现 FACT_SOURCE_REBIND 条件）→ 停机上报 Human，Human 解锁前任何核不得推进产品写。
4. **中途改 scope** → 必须 Human 显式授权 + 绑定文件更新记录新精确路径，之后才可继续。
5. 本核不处理：动作时刻的拦截（→ GATE）、验收与合并（→ RECEIPT）。跨相位决策一律上报，不就地扩权。

## 13. 兼容与边界

- 本文档是 19 协议 → 3 执行核重构的产物，**不废弃**底层源协议；源协议为完整规范，本文档为相位归集与强制力声明。
- 执行层三核只管"有仓库写"的任务生命周期；纯对话 / 只读任务不强制本核。
- 发现旧协议与三核文档冲突 → 登记到 M7 废弃对照（NORMATIVE_MAP），不擅自改旧协议。
