# Human Facing 呈现模板（6 机制 × 4 场景 即用版）

**DOC_STATUS:** `TEMPLATE`（配套 `protocols/HUMAN_FACING_PSYCHOLOGY.md`，非独立规范）
**SOURCE:** protocols/HUMAN_FACING_PSYCHOLOGY.md（ADT-2026-08-06-008，已合并）
**PURPOSE:** 把协议的 6 个心理机制 × 4 个落地场景固化为"直接套用"的模板——每个场景给出触发点、固定结构、填空位、对照示例与禁用项，让 Human gate / Holder Summary / 收工汇报 / Dispatch Card 下一次真正按协议风格长出来。
**READ FIRST:** 协议全文仍是规范来源；本文件只负责"怎么摆"，不改变任何字段、状态或治理规则。

---

## 0. 总览：4 场景 × 6 机制映射

| 场景 | 主用机制（2-3 个，必须） | 可用（轻量） | 不用（禁用） |
|---|---|---|---|
| ① Dispatch Card 呈现 | 进度效应、承诺一致性 | 反馈间隔（一行决策影响） | 蔡格尼克效应（本卡不列历史未关闭项）、损失厌恶 |
| ② Holder Summary | 进度效应、蔡格尼克效应、损失厌恶 | — | 选择架构（Summary 不替用户摆默认动作） |
| ③ Human gate | 承诺一致性、选择架构 | 反馈间隔（决策后即时确认） | 进度效应（gate 上不堆完成度，避免"差一点"压力） |
| ④ 收工汇报 / 跨机接力 | 反馈间隔、蔡格尼克效应 | 损失厌恶（一行已沉淀） | 选择架构、承诺一致性（不重申承诺，只留缺口） |

规则：每个场景**主用 2-3 个机制**，其余机制不得堆砌。四个场景合起来恰好覆盖 6 机制，无遗漏、无重复主用。

---

## 1. 模板 ①：Dispatch Card 呈现（进度效应 + 承诺一致性）

### 触发点
- 向 Human 呈现一个新任务（Dispatch Card / 派卡）。
- 用户看到的是"孤立的单点任务"而不是"连续推进的链"时，必用本模板。

### 结构（固定骨架）
```text
已完成链（近 {N} 项，均已验收）：
  {DONE_LIST}            ← 一行一项：TASK_ID → 产物 → ACCEPT/REJECT
本任务：{TASK_ID} → {ARTIFACT}
与你此前确认方向的关系：{DIRECTION_LINK}
```

### 填空位
| 占位符 | 内容 | 示例 |
|---|---|---|
| `{N}` | 已完成链长度（默认 3，不得超过 5） | 3 |
| `{DONE_LIST}` | 近 N 项已验收任务，一行一项 | `ADT-2026-08-06-005 → protocols/CONCURRENCY_LIMIT.md → ACCEPT` |
| `{TASK_ID}` | 本任务编号 | ADT-2026-08-06-010 |
| `{ARTIFACT}` | 本任务产物路径 | docs/human-facing-templates.md |
| `{DIRECTION_LINK}` | 与用户此前确认方向的对应关系（必须真实、可追溯） | 延续 ROADMAP.md § PT 心理机制指示（你于 2026-08-06 确认 STRATEGY_ADOPTED） |

### 对照示例
```text
报告版（不推荐）：
  新任务：ADT-2026-08-06-010
  内容：把心理机制协议固化为呈现模板
  产物：docs/human-facing-templates.md
  请确认。

机制版（推荐）：
  已完成链（近 3 项，均已验收）：
    ADT-2026-08-06-005 → protocols/CONCURRENCY_LIMIT.md → ACCEPT
    ADT-2026-08-06-003 → ROADMAP.md § PT（后训练轨道）  → ACCEPT
    ADT-2026-08-06-008 → protocols/HUMAN_FACING_PSYCHOLOGY.md → ACCEPT
  本任务：ADT-2026-08-06-010 → docs/human-facing-templates.md
  与你此前确认方向的关系：延续 § PT 心理机制落地（协议 §3 场景的即用化）
```

### 禁用项
- 不列本卡之外的未关闭项清单（蔡格尼克留给 Holder Summary / 接力，不塞进派卡）。
- 不写"这是第 N 个任务，快完成了"之类的进度催促；已完成链只陈述事实。
- 不堆 6 个机制：本场景只做"链 + 方向重申"两件事。
- `{DIRECTION_LINK}` 不得捏造：用户未确认过的方向不得引用。

---

## 2. 模板 ②：Holder Summary（进度效应 + 蔡格尼克效应 + 损失厌恶）

### 触发点
- 阶段性汇报、任务窗口收束、向 Human 汇总多个任务状态时。
- 用户需要"看清全局再决定下一步"的节点。

### 结构（固定骨架，三段顺序不可调换）
```text
已完成：本阶段 {DONE_COUNT}/{PLAN_DENOM}（分母来自 {PLAN_SOURCE}）
  {DONE_LIST}
未完成：
  {OPEN_ITEMS}           ← 每项带"下一步：{NEXT_STEP}"
已沉淀（不可回退价值）：
  {MERGED_ASSETS}        ← 已 merge 成果，标注"回退需新 revert 任务"
```

### 填空位
| 占位符 | 内容 | 规则 |
|---|---|---|
| `{DONE_COUNT}` / `{PLAN_DENOM}` | 阶段完成度 | 分母必须来自预绑定计划（如 PT 授权计划），遵守进度反膨胀；禁止自造分母 |
| `{DONE_LIST}` | 已完成项，✅ 前缀，一行一项 | 只列真实验收结论 |
| `{OPEN_ITEMS}` | 未关闭项/待办/被 REJECT 项，⬜ 前缀 | 显式列表，**不淹没在完成列表里**；每项必须带下一步 |
| `{NEXT_STEP}` | 每项开放项的下一个动作 | 如 CHECKER_AUDIT / 等待 Human 授权 |
| `{MERGED_ASSETS}` | 已 merge 成果，🔒 前缀 | 标注"已进入 main，回退需新 revert 任务" |

### 对照示例
```text
报告版（不推荐）：
  已完成 3 项，剩余 2 项在推进中，详见各分支。

机制版（推荐）：
  已完成：本阶段 3/5（分母来自 PT 轨道授权计划）
    ✅ ADT-...-005 / ✅ ADT-...-003 / ✅ ADT-...-006
  未完成：
    ⬜ ADT-...-008 心理机制协议 — 下一步：CHECKER_AUDIT
    ⬜ PT 数据管道最小闭环 — 下一步：等待 Human 授权
  已沉淀（不可回退价值）：
    🔒 P0 三件（隔离/并发/令牌）已 merge 进 main；PT 轨道已固化进 ROADMAP.md
```

### 禁用项
- 三段顺序不可调换；不得把未完成项藏在完成列表里"显得都做完了"。
- 完成度分母只来自预绑定计划：不写"50%"，除非有分母；不因接近完成而放大进度。
- 不替用户设计默认动作（选择架构留给 Human gate）。
- 未关闭项必须真实：蔡格尼克只显式化真实开放项，不得为了"整齐"隐藏 REJECT / 阻塞。

---

## 3. 模板 ③：Human gate（承诺一致性 + 选择架构）

### 触发点
- 任何需要 Human 做 ACCEPT / REJECT / MODIFY 决策的节点（验收 PR、验收协议、黄金标签）。
- 用户有可能"机械验收"（不看证据直接点 ACCEPT）时，必用本模板。

### 结构（固定骨架：验收标准 → 证据 → 决策）
```text
你此前确认的验收标准：{ACCEPT_CRITERIA}
证据摘要：{EVIDENCE_SUMMARY} — 见 {EVIDENCE_LOCATION}
决策：[ 查看证据 ]（默认）  [ ACCEPT ]  [ REJECT ]  [ MODIFY ]
```

### 填空位
| 占位符 | 内容 | 规则 |
|---|---|---|
| `{ACCEPT_CRITERIA}` | 用户此前确认的验收标准 | 必须来自 Dispatch Card 的成功标准，逐条可核对 |
| `{EVIDENCE_SUMMARY}` | 证据摘要 | 只陈述事实（机制数/场景数/测试输出），不写评价性结论 |
| `{EVIDENCE_LOCATION}` | 证据位置 | branch@HEAD diff / CI 输出 / receipt 文件路径 |

### 对照示例
```text
报告版（不推荐）：
  协议已完成，符合全部要求，请验收：ACCEPT / REJECT。

机制版（推荐）：
  你此前确认的验收标准：协议包含 ≥5 个心理机制、≥4 个落地场景、边界与伦理、轻量版兼容。
  证据摘要：6 个机制 / 4 个场景 / 7 条伦理边界 / 轻量版兼容表 — 见 branch@HEAD diff。
  决策：[ 查看证据 ]（默认）  [ ACCEPT ]  [ REJECT ]  [ MODIFY ]
```

### 禁用项
- 默认动作永远只能是"查看证据 / 继续反思"，**不得默认勾选 ACCEPT**。
- REJECT 与 MODIFY 永远可用，不附带任何劝阻性文案（不写"REJECT 将导致……"）。
- 不重申完成度、不展示进度条（进度效应在 gate 上禁用，避免"差一点"施压）。
- 验收标准重申是温和提醒：用户改变方向永远合法，不得用旧承诺绑住用户。

---

## 4. 模板 ④：收工汇报 / 跨机接力（反馈间隔 + 蔡格尼克效应）

### 触发点
- 每次任务收尾（Progress Receipt / 收工汇报）。
- 跨机接力、跨会话交接、下一个窗口/下一次会话开始前。

### 结构（固定骨架：决策影响 → 未关闭项）
```text
本次决策影响：{DECISION_IMPACT}
未关闭项（交接给下一个窗口）：
  {UNCLOSED_ITEMS}
```

### 填空位
| 占位符 | 内容 | 规则 |
|---|---|---|
| `{DECISION_IMPACT}` | 本次结果对后续任务/训练轨道的影响 | 一行即可；必须真实（下一步 gate / 验收后成为哪份正式协议） |
| `{UNCLOSED_ITEMS}` | 未关闭项清单，编号列表 | **必须是交接摘要的第一节**；每项带归属（谁做 / 什么 gate） |

### 对照示例
```text
报告版（不推荐）：
  任务完成，产物已提交，branch 为 hermes/adt-psych-templates-r1，下一步照常。

机制版（推荐）：
  本次决策影响：协议已提交至 hermes/adt-human-facing-psych-r1，下一步 CHECKER_AUDIT；
  验收后即成为 PT 轨道"心理机制落地"的第一份正式协议。
  未关闭项（交接给下一个窗口）：
    1. CHECKER_AUDIT — 独立审计本协议与 AGENTS.md 引用
    2. Human ACCEPT / REJECT / MODIFY — 黄金标签决策
```

### 禁用项
- 未关闭项必须是交接摘要**第一节**——不得把"已完成"放前面把缺口淹没。
- 不重申承诺、不给默认选项（承诺一致性与选择架构留给别的场景）。
- 决策影响行不夸大：不得写"本成果将改变一切"，只写真实的下游影响。
- 跨机接力不得只留"详见上次汇报"——缺口必须当场显式列出。

---

## 5. 使用规则

### 5.1 何时用全套、何时用简版
- **全套（三段式/三要素完整）**：Human gate、Holder Summary——用户在场、是决策节点。
- **简版（每场景 ≤ 3 行）**：Dispatch Card 呈现、收工汇报；轻量流（公司机 WorkBuddy）一律简版。
- 简版可省略 Holder Summary 的完整三段式，但"已完成 / 未完成"的区分不得省略。
- **纯状态模式**：用户要求"只报状态"时，全部心理呈现关闭，只留证据纪律字段；关闭不影响任何治理功能。

### 5.2 优先级（资源有限时按此顺序保级）
```text
Human gate > Holder Summary > 收工汇报 > Dispatch Card
```
- Human gate 是黄金标签节点，机制缺失代价最高，永远保级；
- 收工汇报与 Dispatch Card 可压缩为一行"链 + 决策影响"，但不可退化为纯状态报告之外的东西；
- 任何场景都不得因保级而伪造进度、分母或承诺引用。

### 5.3 通用禁用项（所有场景）
- 不制造虚假紧迫感：无 deadline、倒计时、稀缺性文案；"差一点完成"只能来自真实预绑定分母。
- 不诱导 ACCEPT：机制是"帮助看见"，不是"推动同意"。
- 不堆砌机制：每场景主用 2-3 个，其余禁用。
- 不隐藏任何失败 / REJECT / 阻塞信息：心理呈现不得美化或省略字段值。
- 不改数据结构、不新增状态字段：只重组现有字段的呈现。

---

## 6. 完整成品示例：验收一个协议 PR

场景：验收 `hermes/adt-human-facing-psych-r1`（HUMAN_FACING_PSYCHOLOGY.md 协议 PR）。以下是把 ②③④ 按真实流程串起来的成品。

```text
【Holder Summary】
已完成：本阶段 3/5（分母来自 PT 轨道授权计划）
  ✅ ADT-...-005 并发上限协议 / ✅ ADT-...-003 PT 轨道 / ✅ ADT-...-006 Holder 令牌协议
未完成：
  ⬜ ADT-...-008 心理机制协议 — 下一步：CHECKER_AUDIT（已过）
  ⬜ ADT-...-008 心理机制协议 — 下一步：Human gate（你在这里）
  ⬜ PT 数据管道最小闭环 — 下一步：等待 Human 授权
已沉淀（不可回退价值）：
  🔒 P0 三件（隔离/并发/令牌）已 merge 进 main；PT 轨道已固化进 ROADMAP.md

【Human gate】
你此前确认的验收标准：协议包含 ≥5 个心理机制、≥4 个落地场景、边界与伦理、轻量版兼容。
证据摘要：6 个机制 / 4 个场景 / 7 条伦理边界 / 轻量版兼容表 — 见 branch@HEAD diff。
决策：[ 查看证据 ]（默认）  [ ACCEPT ]  [ REJECT ]  [ MODIFY ]

【ACCEPT 后的即时确认（反馈间隔，一行）】
本次决策影响：心理机制协议已进入 main，下一步是把模板落地到 docs/human-facing-templates.md；
验收后即成为 PT 轨道"心理机制落地"的第一份正式协议。

【收工交接（未关闭项为第一节）】
未关闭项（交接给下一个窗口）：
  1. 心理机制即用模板 — 下一步：派卡给 Maker（本模板即该派卡的产物）
  2. Human 验收模板 PR — 黄金标签决策
  3. PT 数据管道最小闭环 — 等待 Human 授权
```

---

## 7. 与既有文档的关系

| 文档 | 关系 |
|---|---|
| `protocols/HUMAN_FACING_PSYCHOLOGY.md` | 规范来源；本文件是其 §3 场景的即用化，不新增机制、不改变边界 |
| `AGENTS.md § Human-facing evidence discipline` | 字段纪律不变；本模板只组织呈现，FACT/AUTHORITY/ACTION/RESULT/ARTIFACT_* 仍必须完整真实 |
| `protocols/ARTIFACT_DELIVERY.md` | "产物在哪"仍由 Delivery Card 负责；本模板在其周围组织完成链呈现 |
| `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` | 轻量流一律简版（§5.1），§0 总览的"可用（轻量）"列即轻量平移位 |

---

## 8. 反目标（沿用协议 §7，不新增）
- 不新增"人类确认步骤"、不新增状态系统、不新增字段。
- 不把"用户没点 ACCEPT"当系统故障施压。
- 心理呈现不得隐藏或弱化任何失败、REJECT、阻塞信息。
