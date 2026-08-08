# PHILOSOPHY — ADT 哲学层（判断对齐）

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
LAYER: `PHILOSOPHY`（对标 Agile Manifesto：可记忆、可判断）
SCOPE: 对齐判断，不设门禁——读它是为了想得对，不读机器也不会拦你。
NORMATIVE_SOURCE: 方法论基线 `METHODOLOGY.md`；强制力全部落在执行层三核（`protocols/BINDING.md` / `protocols/GATE.md` / `protocols/RECEIPT.md`）；废弃对照见 `governance/NORMATIVE_MAP.md`（M7 登记）。

## 0. 适用域声明

- 执行层三核（BINDING / GATE / RECEIPT）只管**"有仓库写"的任务生命周期**。
- 纯对话 / 只读任务（A/B 模式）不强制 BINDING；但哲学层的证据纪律仍然适用：**FACT / AUTHORITY / RESULT 一行留痕**。
- 本层不设机器门禁；判断分歧时以三核机器事实为准，以 Human 裁决为准。

## 1. 五原则

### 原则一：反目标治理（Anti-objective）

治理行为本身产生的负面效应不得超过它保护的正面价值。

- **判断指南**：
  1. 这一步治理是在保护价值，还是在自我增殖？
  2. 证据留痕成本是否超过任务本身的 20%？
  3. 一个机制连续 3 个任务没被用到，能否砍掉？
  4. 任何"这个不能动"——能说出一行 FACT 依据吗？说不出就可以动。
- 覆盖协议：ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE、ADT_ANTI_OBJECTIVE_PROMPT（判断部分）。

### 原则二：如实呈现（Truthful presentation）

如实呈现本身就是最强的心理机制，不需要额外加装。

- **判断指南**：
  1. 我呈现的是证据字段（FACT / AUTHORITY / ACTION / RESULT / ARTIFACT_TYPE / ARTIFACT_LOCATION），还是叙述？
  2. 进度、承诺基线、未闭环项是否全部如实列出？
  3. 我是否在替 Human 做决定，或隐藏了任何 blocker？
  4. 呈现技巧能写出一行 FACT 证明"帮你做了更好的决定"吗？写不出就是话术，砍。
- 覆盖协议：HUMAN_FACING_PSYCHOLOGY（呈现纪律部分；心理学名词框架与模板库已砍，见 §2）。

### 原则三：自迭代（Self-iteration）

ADT 必须能发现并修复自己的缺陷，否则它对用户的承诺是可质疑的。

- **判断指南**：
  1. 缺陷被发现了，修复路径是否依赖 Human 主动发起？
  2. 修复是否遵守既有授权门（不自我授权 Merge / 不扩权 / 不绕过 CI）？
  3. 推翻留痕了吗？旧结构可以推翻，历史记录不能抹掉。
- 覆盖协议：ADT_SELF_ITERATION。

### 原则四：轻量执行（Lightweight execution）

治理必须比任务轻。小步交付、一任务一分支、检查点硬门槛；推翻一天的工作量不需要勇气。

- **判断指南**：
  1. 这个流程是让任务更快到达真实产物，还是让任务更重？
  2. 一任务一分支一 PR 了吗？叠 PR 就是在给治理放假。
  3. 资源（tier / Point / token / 消息）是按需最小还是习惯性最大？
  4. 只读任务是否被扩张成了写任务？
- 覆盖协议：LIGHTWEIGHT_EXECUTION_FLOW、BEGINNER_BOOTSTRAP_ROUTER（路由判断部分）、RESOURCE_ALLOCATOR_INTEGRATION（资源判断部分）。

### 原则五：事实优先（Fact first）

仓库事实优先于聊天摘要；单一权威事实源；live 解析永远胜过缓存信任。

- **判断指南**：
  1. 我说的事实能指向一个可验证来源（git / 文件 / 测试输出 / 派发记录）吗？
  2. 当前权威事实源是哪个？冲突时是否已停机（FACT_SOURCE_REBIND）？
  3. SHA 是 live 解析的还是缓存里的？
  4. "看起来没问题"是结论吗？不是——是没查。
- 覆盖协议：REPOSITORY_AS_PROMPT_RUNTIME_BINDING（事实源判断部分）。

## 2. 呈现纪律（拍板④，原文照抄）

> **每次交付如实呈现进度、承诺基线、未闭环项——如实呈现本身就是最强的心理机制，不需要额外加装。**

**砍掉项**（防回潮）：

- 原 Human Facing 的心理学名词框架（进度效应 / 承诺一致性 / 蔡格尼克 / 损失厌恶 / 选择架构 / 反馈间隔）。
- 6 机制 × 4 场景模板库。
- "间接改善训练数据"的双重目的。

**砍的理由**：自我监督的伦理线最弱（呈现者自审）；双重目的结构性冲突（为 user 好 vs 为数据好同坐一张椅子）；模板库免除判断。

**检验扳机**：呈现技巧能写出一行 FACT 证明"帮你做了更好的决定"→ 留；写不出 → 话术 → 砍。

## 3. Checker 独立性（立场人验）

- **字段机器验**：两阶段独立性证据（5 字段）由 RECEIPT 核机器校验（`protocols/RECEIPT.md` §6）。
- **立场人验**：哲学层标准——**独立性存疑即故障关闭**。不满足"未参与实现、独立上下文、独立证据路径、可否决"任一 → 视为不独立，不得验收。

## 4. 8 协议对照表（哲学化协议 → 原则 → 强制力去向）

| 源协议（8 个哲学化） | 归属原则 | 强制力去向 |
|----------------------|----------|-----------|
| ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md | 原则一 | 哲学层（判断级）；`NO_UNBOUND_EXECUTION` 强制力在 BINDING |
| ADT_ANTI_OBJECTIVE_PROMPT.md | 原则一 | 自检判断留哲学层；**拔牙①授权卡模板 → BINDING §9** |
| ADT_SELF_ITERATION.md | 原则三 | 哲学层（流程约定级） |
| BEGINNER_BOOTSTRAP_ROUTER.md | 原则四 | 路由判断哲学化；入口结构保持冻结（产品资产，不参与切割） |
| HUMAN_FACING_PSYCHOLOGY.md | 原则二 | 呈现纪律一条保留（§2）；心理学机制全部砍掉 |
| LIGHTWEIGHT_EXECUTION_FLOW.md | 原则四 | 流程判断哲学化；拓扑/身份/scope 强制力在 CANDIDATE_LIFECYCLE + 三核 |
| REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md | 原则五 | 事实源阶梯判断哲学化；**拔牙②外部绑定固定 SHA 校验 → BINDING §8** |
| RESOURCE_ALLOCATOR_INTEGRATION.md | 原则四 | tier 判断哲学化；**拔牙③人类上限 BLOCKED → GATE §9** |

对照关系：11 个带牙协议的强制力已迁入三核（详见各核"吸收协议对照表"）；本表 8 个哲学化协议**只留判断**，牙齿全部拔净。

## 5. 与三核的关系

```text
哲学层：对齐判断 —— 读它是为了想得对，不读机器也不会拦你
BINDING：事前设门禁 —— 无绑定不动笔（机器）
GATE：  事中设门禁 —— 越界即拦，故障关闭（机器）
RECEIPT：事后设门禁 —— 无独立验收不合并（机器）
```

- 哲学层不替代三核：判断不能绕过门禁；门禁不能免除判断。
- 哲学层不创造新规则：不设新状态、新 receipt、新 gate。五原则是判断指南，不是第四核。
- 哲学层是呈现纪律的**唯一归属**；呈现纪律是哲学层的**唯一硬要求**（Human 可见、可对照、可检验）。

## 6. 推翻纪律

- **扳机触发，果断推翻；扳机没触发，闭嘴干活。**
- 预置扳机（不凭感觉）：
  1. 一个机制连续 3 个任务没被用到 → 砍；
  2. 证据留痕成本超过任务本身 20% → 砍流程；
  3. 任何"这个不能动"说不出 FACT 依据 → 就可以动。
- 推翻留痕，不抹历史：旧概念 → 被什么取代 → 新位置，登记到 NORMATIVE_MAP 废弃对照（M7）。
- 对称纪律：推翻和重启是同一种诱惑的两面——防止"感觉不顺就推倒重来"。

## 7. 指针

- 方法论基线：`METHODOLOGY.md`
- 执行层三核：`protocols/BINDING.md`、`protocols/GATE.md`、`protocols/RECEIPT.md`
- 废弃对照登记：`governance/NORMATIVE_MAP.md`（M7 后生效）
