# ADT 自适应数字团队

> 让 AI 不只是能干活，而是能一起把活干对。

---

## 你是人类还是 AI？

- **人类用户** → 往下读，选你的使用方式（A / B / C）
- **AI / Agent** → 跳转 [BOOTSTRAP.md](./BOOTSTRAP.md)，按 [AGENTS.md](./AGENTS.md) 执行

---

## A / B / C 快速开始

完整路由定义见 [protocols/BEGINNER_BOOTSTRAP_ROUTER.md](./protocols/BEGINNER_BOOTSTRAP_ROUTER.md)。
如果第一条消息已包含明确任务、附件或仓库链接，系统会自动跳过这里。

### A ｜ 直接开始

告诉我你想完成什么。此模式不涉及仓库，一切在对话里完成。

### B ｜ 我会上传文件

把文件上传到对话里，告诉我怎么处理。不需要 GitHub。

### C ｜ 连接我的项目仓库

提供你的仓库链接，选择只读分析或允许创建候选变更。最终提交和合并仍由你确认。

输入 **返回模式选择** 可随时回到这里。

---

## 想象一个下午

你打开一个 AI 窗口，说："帮我加一个用户登录功能。"

AI 很快写了几百行代码。登录确实能用了。但你还发现了一些你不确定该不该存在的东西——多了一个你不知道为什么引入的依赖、一段看起来跟登录无关的数据处理逻辑、三个你没要求的配置文件改动。

你开始往回翻对话记录，试图理解 AI 当时在想什么。但对话太长了，你找不到那个决策节点。

这个下午的代价不是"AI 写错了"——而是**你不知道 AI 做了什么、为什么这样做、改了什么你没让它改的东西**。

---

## ADT 做了什么不一样的事

同样的任务，在 ADT 下是这样的：

**开始之前**，AI 会先跟你确认：这次改哪些文件、不改哪些文件、成功的标准是什么。这个确认不是聊天，是一份结构化的授权——你能看到边界。

**执行过程中**，AI 的一举一动都被限定在这份授权里。它不能顺手改一个"顺便优化一下"的文件。改了就会被拦住。

**完成后**，另一个独立的 AI（不是刚才干活那个）会帮你审查：改的文件是不是都在授权范围内、有没有越界、有没有隐藏的副作用。审查结果不是"看起来没问题"——是一份可以追查的记录。

**发现问题时**，你不用从头理解整个变更。你只需要看：哪个文件被改了、在哪个步骤、为什么授权允许它被改。你可以回到那个节点做决定，而不是推倒重来。

---

## ADT 凭什么能做到

| 如果你的担心是…… | ADT 用这个来兜底 |
|---|---|
| AI 改了我没让改的文件 | **Scope Enforcement** — 每个任务有精确的授权文件列表 |
| 改了之后不知道对不对 | **Independent Checker** — 独立审查，不是同一个人既干活又验收 |
| 找不到当时的决策依据 | **Evidence Card** — 关键节点自动留痕 |
| 小修改变成大翻车 | **Candidate State Machine** — 每一步都可以回退 |
| 治理流程本身太重了 | **Dynamic Governance Router** — 低风险任务轻量过，高风险才加验证 |
| 换个 AI 窗口就丢了上下文 | **Repository as Prompt** — 上下文存在仓库里，不是存在聊天记录里 |

---

## 这不是理念——这些机制已经在跑了

### 你授权什么，它就只改什么

每个任务的授权不是聊天约定，是一份机器可读的 JSON。CI 会校验：

```json
{
  "task_id": "ADT-S2-002-A-ARTIFACT-PACKAGE",
  "authorized_write_scope": [
    "README.md",
    "PROJECT_STATE.md",
    ".hermes/CANDIDATE_BINDING.json"
  ]
}
```

改了这个列表之外的文件 → CI 直接拒绝。

第 55 号 PR 就是这样被拦下来的：Maker 修了一个测试文件，但忘了把它加入授权范围。CI 日志里只写了一行：

```
SCOPE_VIOLATION: files outside authorized_write_scope:
    ['tests/test_beginner_bootstrap.py']
```

不是"建议不要改"——是**合并被阻断**。

### 每一个候选都有身份

仓库里的每一次变更不是一个模糊的"新版本"，而是有确定 SHA-256 指纹的候选：

```
TASK_ID      ADT-S2-002-A-ARTIFACT-PACKAGE
BRANCH       hermes/adt-s2-002-a-artifact-package-r1
HEAD         a470e21
BASE         6665e84
SCOPE        README.md, PROJECT_STATE.md, ...
STATE        FORMAL_CANDIDATE
```

你可以随时回到任意一个候选，比对它跟基准之间的 diff，追溯它经过了谁的审查。

### 三秒验证一切

```bash
python scripts/validate_binding.py
```

输出：

```
CANDIDATE_STATE: COMMITTED_CANDIDATE
PASS: All validations passed
  ✓ Branch ancestry verified
  ✓ Base SHA matches main
  ✓ Authorized write scope intact
  ✓ No files outside scope modified
```

不需要理解整套架构。一条命令，全或无。

### 治理强度跟着风险走

不是所有任务都值得拉满检查：

```
低风险（文档修正）    →  轻量验证
中风险（配置变更）    →  独立 Checker 审查
高风险（核心逻辑）    →  完整证据链 + 多重审计
```

这套分层在 ADT 的动态治理路由器里运行——任务分类、Checker 分配、验证深度由系统根据风险等级自动匹配，最终由你确认。

---

## ADT 的治理哲学

这些机制背后是五条原则：

### 1. 目标优先

跑起来之前，先对齐目标和边界。

### 2. 最小必要

治理强度匹配风险。不是所有事都值得拉满检查——治理不能比产品价值更贵。

### 3. 证据驱动

不留"我觉得没问题"。每一个关键决策有据可查。

### 4. 人类掌舵

AI 负责执行，人类负责方向、边界和关键判断。授权是分层的，最终决定权始终在人手里。

### 5. 持续纠正

检查 → 反馈 → 修正。每一步都是可回退的尝试。

---

## 一个最小协作流程

```
你（人类）  ——→  定义目标、授权范围
     ↓
  Maker     ——→  在授权范围内执行
     ↓
  Checker   ——→  独立审查、比对授权
     ↓
  Evidence  ——→  自动记录审查结果
     ↓
你（人类）  ——→  看证据、做决定
```

---

## 当前推荐运行方式

当前阶段，推荐 **1 名人类 + 2 个独立 AI 窗口**：

- 一个窗口推进和执行（Maker）
- 另一个窗口独立检查（Checker）
- 你保留授权、方向和最终决定权

设计目标将收敛为单一 Project Control 窗口，内部编排多个子代理。

---

## 快速开始

```bash
git clone https://github.com/butbutbutbutbutbut/adaptive-digital-team.git
cd adaptive-digital-team
pip install pytest pyyaml
python scripts/validate_binding.py
python tests/run_tests.py
```

---

## 深入阅读

- Agent 入口 → [`BOOTSTRAP.md`](./BOOTSTRAP.md) | [`AGENTS.md`](./AGENTS.md)
- 架构 → [`docs/architecture/`](./docs/architecture/)
- 治理模型 → [`governance/`](./governance/)
- Runtime 层 → [`protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md`](./protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md)

---

## License

Apache License 2.0 — [LICENSE](LICENSE)

## Contributing

一个任务 = 一个分支 = 一个 PR。禁止堆叠 PR、force-push、自验收。
见 [CONTRIBUTING.md](CONTRIBUTING.md)
