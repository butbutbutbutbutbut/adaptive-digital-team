# RECEIPT — 回执验收核（事后）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PHASE: `AFTER`（事后 —— 回执写入与验收决策）
LAYER: `EXECUTION_CORE_3_OF_3`
NORMATIVE_SOURCE: 本文档是执行层三核之一。候选生命周期、审计回执、多模态证据、产物交付、项目关闭、Token 释放的完整底层规则仍以 `protocols/CANDIDATE_LIFECYCLE.md`、`protocols/MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md`、`protocols/ARTIFACT_DELIVERY.md`、`protocols/PROJECT_CLOSEOUT_PROTOCOL.md`、`protocols/HOLDER_TOKEN.md` 为准；本文档只做相位归集与强制力声明，不创造新规则。

## 1. 相位定义

RECEIPT 核管辖**任务收尾阶段**的全部验收事实：Maker 回执、Checker 独立验收、回执完备性、终态验收点、Human gate、Token 释放。它只回答一个问题：**"这枝笔写出来的东西凭什么能合并？"**

- 回执写一次（任务结束时）；验收决策是 Human 独有权利。
- 回执不是验收；CI 通过不是验收；Maker 自述不是验收。
- 合并前的一切验收检查在本核收敛（含 PRE_MERGE_REALTIME_GATE）。

## 2. 铁律

```text
无独立验收不合并
```

任何候选合并（merge / ready / 最终接受）之前，必须存在**独立的 Checker 验收**：独立上下文、独立证据路径、未参与实现、可否决，且回执完备、指纹绑定、终态验收点通过。缺任一项 → fail-closed，禁止合并。

```text
SELF_ACCEPTANCE_BLOCKED（自我验收拦截）
AUTO_READY: FORBIDDEN
AUTO_MERGE: FORBIDDEN
```

## 3. 不变量清单

| # | 不变量 | 违反后果 |
|---|--------|----------|
| R1 | Checker 与 Maker 必须独立：`EXECUTOR ≠ CHECKER`，两阶段独立性证据 5 字段齐全 | `SELF_ACCEPTANCE_BLOCKED` / `INDEPENDENCE_FAILED` |
| R2 | 回执必须完备：17 字段回执完备性校验（§5） | `INCOMPLETE_RECEIPT`，fail-closed |
| R3 | 回执必须绑定同一候选指纹（repository / base / head / changed_files 六字段指纹） | `FINGERPRINT_MISMATCH`，旧回执失效 |
| R4 | 治理文件变更必须有独立 Checker receipt 且 `task_id` 匹配 | CI fail（GOVERNANCE_CRITICAL 闸，§7） |
| R5 | 合并前必须执行 `PRE_MERGE_REALTIME_GATE` 终态验收点（§8） | `HARD_STOP` / `FINGERPRINT_MISMATCH` |
| R6 | auto-Ready / auto-Merge 禁令必须作为验收检查项显式核对 | `HARD_STOP` |
| R7 | Token 释放随 Human 验收完成（ACCEPT / REJECT / MODIFY 门闭合，§9） | `TOKEN_STUCK` |
| R8 | 产物必须可定位：artifact_type + artifact_location（+ 可选 verification_hint） | 任务不算完成 |
| R9 | 多模态证据门：声明依赖非文本证据时，独立 Checker 必须实看（§10） | `EVIDENCE_ACCEPTANCE: BLOCKED` |

## 4. 机器载体

| 载体 | 作用 |
|------|------|
| `.hermes/checker_receipt.json` | 独立 Checker 回执（**由 Checker 提交，Maker 不得代写**） |
| `scripts/validate_receipt.py` / `scripts/validate_binding.py` | 回执完备性与治理文件闸校验（含 task_id 匹配） |
| Progress Receipt | Maker 证据（**非**验收；候选待独立审查） |
| Audit Receipt | 独立审计记录，绑定指纹 |
| CI 门禁 | 治理文件 PR 无有效 receipt → fail |

## 5. 17 字段回执完备性校验

任何 Controller / Project Control / Holder 返回 Human 的完成回执，必须包含以下 17 个字段，缺一即不完整回执，fail-closed 直至补齐；叙述性总结不可替代字段：

```text
FACT                 # 机器事实（SHA、分支、文件、测试输出原文）
AUTHORITY            # 授权依据（AUTHORIZATION_ID / 拍板记录）
ACTION               # 实际执行的动作（计划 ≠ 执行）
RESULT               # 执行结果（CREATED/UPDATED/MERGED/CLOSED/COMPLETED/GATE_BLOCKED/FAILED）
ARTIFACT_TYPE        # 产物类型（PR/file/commit/document/branch/conclusion）
ARTIFACT_LOCATION    # 产物位置（人类可访问路径/URL）
TASK_PROGRESS        # 任务级进度
CURRENT_STAGE_PROGRESS  # 当前阶段进度
PROGRESS_BASIS       # 进度依据（预绑定有限分母 + 验证单位）
PROGRESS_BLOCKER     # 阻塞项（无则 NONE）
CURRENT_GATE         # 当前闸门标识
USER_ACTION_REQUIRED # YES/NO
USER_ACTION          # 需要人类执行的动作
ACTION_REASON        # 该动作的理由
NO_ACTION_EFFECT     # 不动作的后果
SYSTEM_NEXT_STEP     # 系统下一步精确动作
TASK_ID              # 任务标识（与 binding / receipt 一致）
```

禁止项：`BLACKBOX_STATUS`（无证据声称处理中/已完成/安全）；"等待即进度"；"CI 通过即接受"；数字进度无预绑定分母与验证单位。

## 6. 两阶段独立性证据（5 字段）

Checker 独立性是两阶段证据对象，不是单一布尔值。**全部 5 字段必须存在**：

```json
{
  "separate_execution_context": true,
  "maker_context_inherited": false,
  "participated_in_implementation": false,
  "independent_fact_read": true,
  "independent_conclusion": true
}
```

- **阶段一（执行前）**：`separate_execution_context=true`（独立进程/窗口/容器）；`maker_context_inherited=false`（未继承 Maker 会话状态、记忆、对话上下文）。
- **阶段二（执行后）**：`participated_in_implementation=false`（未设计/编写/贡献实现）；`independent_fact_read=true`（从独立来源读事实：仓库、git log、文件内容、测试输出，而非 Maker 声明）；`independent_conclusion=true`（独立得出自己的结论）。
- 时序约束：执行前校验只看阶段一字段；执行后校验看全部五字段。
- 独立性边界："同一 API key / 同一 provider"不破坏独立性——只要不共享会话状态与实现参与。
- 任何独立性歧义 → fail-closed（`INDEPENDENCE_FAILED`）。

## 7. GOVERNANCE_CRITICAL 治理文件闸

治理文件变更（AGENTS.md、METHODOLOGY.md、ROADMAP.md、protocols/、governance/）适用特殊闸门：

1. 变更治理文件的 PR 必须附带**独立 Checker receipt**，且 receipt 的 `task_id` 与当前 binding 的 `task_id` 一致（M4 P1-5 已机器化：`validate_binding.py` 校验 receipt 的 task_id）。
2. 无有效 receipt 的治理文件 PR → CI fail。
3. **Maker 不得代写 checker_receipt.json**：receipt 由非执行者（Checker）在验收后亲自提交（两阶段：先查 Maker diff ⊆ 授权清单，Checker 提交 receipt 后复查全量 diff）。
4. 自我验收拦截（红队 B 牙位①）：任何 Maker 自写 receipt / 自验通过 → `SELF_ACCEPTANCE_BLOCKED`。
5. auto-Ready / auto-Merge 禁令（红队 B 牙位③）在验收检查项中显式核对：验收记录必须声明未发生 auto-Ready / auto-Merge，且 Human 是 Ready / Merge / 删分支的唯一权威。

## 8. PRE_MERGE_REALTIME_GATE 终态验收点

Ready 或 Merge 之前立即执行，用预期审计指纹重新解析全部实时事实：

```text
repository
origin/main
origin/<candidate_branch>
current Head
Base ref 和 SHA
candidate branch 和 Head SHA
sorted changed files
workspace cleanliness
exact authorized scope coverage
```

必须确认（全部成立才放行）：

```text
base_ref == main
base_sha 不变
head_sha 不变
changed_files 不变
runtime fingerprint == 预期指纹
workspace clean
sorted(changed_files) == sorted(authorized_write_scope)
```

任何不匹配 → `HARD_STOP` / `FINGERPRINT_MISMATCH`，作废旧审计、旧 Ready 授权、旧 Merge 授权；不得基于旧证据继续 Ready / Merge。CI 等待期属于本核证据收集态（token 保持 HELD 属正常，等待不推进进度）。

## 9. Token 释放（随 Human 验收完成）

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

- 释放令牌 ≠ 释放在飞名额；但名额释放（聚合/取消/关闭）前必须已完成令牌释放，逆序视为异常（`TOKEN_STUCK`）。
- 释放后、下一任务派发前，绑定文件不被任何任务写入（空闲窗口），消除"派发即践踏"时序窗口。
- 异常释放（TIMEOUT / FAILURE / CRASH_RECOVERY / CANCELLED）见 `protocols/GATE.md` §8 恢复表，全部报告 Human。

## 10. 吸收协议（强制力归集）

### 10.1 产物交付（吸收 ARTIFACT_DELIVERY）

- Maker Progress Receipt 必须含 `artifact` / `artifacts` 字段：`type` + `location`（+ 可选 `verification_hint`）。
- Checker 独立验证 `artifact_exists: true/false`——用自己环境判断，不依赖 Maker 的 verification_hint。
- Holder 聚合时 artifact 信息不变形传递（不得把 `MEDIA:/path` 转成"文件已生成"）。
- Controller 回报 Human 时 Artifact Location 是首要信息，不是附注。
- 产物位置 ≠ 内容正确；零文件任务用 `conclusion` 类型。

### 10.2 多模态证据门（吸收 MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE）

声明依赖图像/音频/视频/轨迹/外部二进制证据时，验收记录必须包含：

```text
EVIDENCE_METADATA_AUDIT: PASS / FAIL / NOT_PERFORMED
EVIDENCE_BINARY_AVAILABILITY: PASS / FAIL / NOT_APPLICABLE
ACTUAL_MODAL_REVIEW_PERFORMED: YES / NO
REVIEWED_MODALITIES: TEXT / IMAGE / AUDIO / VIDEO / TRACE / OTHER
REVIEW_SCOPE: FULL / SAMPLED / NONE
MANIFEST_TO_BINARY_MAPPING: PASS / FAIL / NOT_APPLICABLE
SEMANTIC_SUPPORT_AUDIT: PASS / FAIL / NOT_PERFORMED
EVIDENCE_ACCEPTANCE: FINAL / PROVISIONAL / BLOCKED
```

- `EVIDENCE_ACCEPTANCE: FINAL` 需要：metadata PASS + binary PASS（或合理 NOT_APPLICABLE）+ 实看 YES + mapping PASS + semantic PASS。
- 读清单/文件名/哈希/摘要 ≠ 实看。缺任何核心步骤 → `BLOCKED`。
- 采样审查仅当 Task Freeze 执行前显式授权；未授权采样 fail-closed。
- 依赖外部二进制的声明不允许 binary availability 或 mapping 用 NOT_APPLICABLE。
- 合并授权文本必须显式包含实看 YES + 范围 + semantic PASS，缺失 → `MERGE_ALLOWED: NO`。

### 10.3 项目关闭协议（吸收 PROJECT_CLOSEOUT_PROTOCOL）

- `DELIVERABLE_CREATED ≠ PROJECT_CLOSED`；`CLOSED` 只在本核完整闭环后可达：关闭候选 → 独立审计 → 批准合并 → 合并 → post-merge attestation 记录实际仓库状态。
- 授权边界：`AUTO_PREPARE_AND_PUSH` / `AUTO_CREATE_CLOSEOUT_PR` 仅在有有效授权记录时允许；`AUTO_MERGE: FORBIDDEN`；`SELF_ACCEPTANCE: FORBIDDEN`；`INDEPENDENT_CLOSEOUT_AUDIT: REQUIRED`；不可逆外部动作需显式批准。
- 关闭清单分类（GIT_TEXT / GIT_BINARY_APPROVED / EXTERNAL_BINARY / EXCLUDED_SECRET / EXCLUDED_PRIVACY / EXCLUDED_LICENSE / EPHEMERAL / MISSING_REQUIRED）确定性判定；secret/privacy/license 门 fail-closed；`MISSING_REQUIRED` = 证据不完整。
- blocked/incomplete 状态必须保留原因、受影响材料、尝试动作、剩余负责人、恢复路径；不得改写为 `CLOSED`。
- post-merge attestation 用新分支 + 前瞻 commit + 独立审查 PR 记录；不得 reset / amend / rebase / force-push / 擦除旧记录。

## 11. fail-closed 行为表

| 条件 | 行为 |
|------|------|
| Maker 自写 checker_receipt.json / 自我验收 | `SELF_ACCEPTANCE_BLOCKED` |
| 独立性 5 字段缺失或任一项不成立 | `INDEPENDENCE_FAILED`，无验收 |
| 回执 17 字段缺失任一项 | `INCOMPLETE_RECEIPT`，fail-closed |
| 回执指纹与候选指纹不一致 | `FINGERPRINT_MISMATCH`，旧回执作废 |
| 治理文件 PR 无有效 receipt / task_id 不匹配 | CI fail |
| 终态验收点任何事实漂移 | `HARD_STOP`，旧审计/Ready/Merge 全作废 |
| auto-Ready / auto-Merge / auto-delete 被发现 | `HARD_STOP` |
| 多模态证据门缺实看 | `EVIDENCE_ACCEPTANCE: BLOCKED`，`MERGE_ALLOWED: NO` |
| Token 未释放 / 任务已关闭仍 HELD | `TOKEN_STUCK`，报告 Human |
| 回执与目标事实不匹配（transcription/target mismatch） | `INVALID_AUDIT_RECEIPT`（回执缺陷，非候选缺陷，不消耗修复预算） |

## 12. 吸收协议对照表

| 源协议 | 被吸收内容 | 新位置 |
|--------|-----------|--------|
| `CANDIDATE_LIFECYCLE.md` | 审计回执验证、PRE_MERGE_REALTIME_GATE、指纹绑定、失败路由 | §3 R3/R5、§8、§11 |
| `ADT_RUNTIME_ADAPTER_CONTRACT.md` | Checker 两阶段独立性证据（5 字段） | §6 |
| `ARTIFACT_DELIVERY.md` | artifact_type / artifact_location / verification_hint | §3 R8、§10.1 |
| `MULTIMODAL_EVIDENCE_ACCEPTANCE_GATE.md` | 多模态证据门、实看要求、合并授权条件 | §10.2 |
| `PROJECT_CLOSEOUT_PROTOCOL.md` | 关闭状态机、材料分类、secret/privacy/license 门、attestation | §10.3 |
| `HOLDER_TOKEN.md` | Token 释放（ACCEPT/REJECT/MODIFY 门闭合） | §9 |
| `INSTRUCTION_ROUTING_AND_AUTHORITY.md` | SELF_ACCEPTANCE_BLOCKED（**红队 B 牙位①**） | §2、§7 |
| `AGENTS.md` + `validate_binding.py` | GOVERNANCE_CRITICAL 治理文件闸（**红队 B 牙位②**，M4 已机器化） | §7 |
| `DYNAMIC_GOVERNANCE_ROUTER.md` | auto-Ready/auto-Merge 禁令（**红队 B 牙位③**） | §3 R6、§7 |

## 13. 跨相位升级规则

1. **验收中发现越界或未授权动作** → 上报 BINDING（Human 重授权），本核不就地扩权。
2. **事实源冲突 / 候选漂移** → `FACT_SOURCE_REBIND`：停机上报 Human，任何核不得推进。
3. **base 漂移** → 唯一出口：关闭当前候选、从最新 main 开新任务（见 `protocols/BINDING.md` §12）。
4. **CI 等待期** = 本核证据收集态：token 保持 HELD 属正常；等待不推进进度，不产生新证据。
5. **修复**：合并前缺陷在同分支 append-only 修复，新 Head 使旧指纹与审计失效，Checker 复查新 Head 新指纹；同一未合并候选禁止第二 PR。
6. 本核不处理：授权定义（→ BINDING）、动作拦截（→ GATE）。跨相位决策一律上报，不就地扩权。

## 14. 兼容与边界

- 本文档是 19 协议 → 3 执行核重构的产物，**不废弃**底层源协议；源协议为完整规范，本文档为相位归集与强制力声明。
- Progress Receipt 是 Maker 证据，Audit Receipt / Checker Receipt 是独立验收证据，两者不可互换。
- 发现旧协议与三核文档冲突 → 登记到 M7 废弃对照（NORMATIVE_MAP），不擅自改旧协议。
