# ADT Migration Guide — 双层重构（19 协议 → 哲学层 + 3 执行核）

> **STATUS**: `ARCHIVED_STRUCTURE_MIGRATION`（2026-08-08 生效）
> 本指南面向：84+ 历史 PR 读者、外部接入者、新窗口 Agent。
> 唯一活入口：`governance/NORMATIVE_MAP.md` —— 一切概念去向以它为准。

## Breaking-change 声明

2026-08-08 起，ADT 治理结构从 **19 协议堆叠** 重构为 **双层结构**：

```text
哲学层  PHILOSOPHY      —— 5 原则 + 判断指南（对齐判断，不设门禁，<200 行）
执行核  BINDING         —— 事前：无绑定不动笔（授权事实、指纹、令牌发放）
        GATE            —— 事中：越界即拦，故障关闭（scope 执行、drift、令牌校验）
        RECEIPT         —— 事后：无独立验收不合并（回执、pre-merge 终态、令牌释放）
登记    NORMATIVE_MAP   —— 19→4 废弃对照（推翻留痕，唯一活入口）
```

**变了的**：

| 维度 | 旧 | 新 |
|---|---|---|
| 文档结构 | 19 个平级协议 | 4 份新文档（3 执行核 + 1 哲学层） |
| 旧协议状态 | 活文档 | **归档态**（DEPRECATED 标注，文件保留仅维持历史引用不断链） |
| 强制力位置 | 散落 19 协议 | 3 核机器载体：`binding_core.py` + `validate_binding.py` / `validate_gate.py` / `validate_receipt_phase.py`（相位拆分，行为等价） |
| 概念去向 | 各协议自述 | NORMATIVE_MAP 对照表（唯一活入口） |

**没变的**：入口层（README / BOOTSTRAP / AGENTS）产品接触面不变；A/B/C 路由不变；497 测试与双校验器全绿不回退；历史 PR 与提交不可变。

## 迁移路径（读者版）

```text
读到旧协议文件（如 protocols/CANDIDATE_LIFECYCLE.md）
  └─ 顶部 DEPRECATED 标注已指向 NORMATIVE_MAP
       └─ NORMATIVE_MAP 废弃对照 → 旧概念 → 取代者 → 强制力新位置
            └─ 新文档：protocols/BINDING.md / GATE.md / RECEIPT.md / PHILOSOPHY.md
```

**84+ 历史 PR 兼容**：所有旧协议文件物理保留（不断链），仅顶部加归档标注。
历史 PR 中的链接继续有效；链接指向的语义以 NORMATIVE_MAP 对照为准。

## 机器载体迁移路径（执行器版）

| 旧 | 新 | 行为 |
|---|---|---|
| `scripts/validate_binding.py`（979 行单文件） | `scripts/binding_core.py`（共享核心）+ `validate_binding.py`（BINDING 薄入口） | 原 CLI 契约不变（CI 调用点零改动） |
| — | `scripts/validate_gate.py`（GATE 薄入口） | 预写执行门 + live scope 执行 |
| — | `scripts/validate_receipt_phase.py`（RECEIPT 薄入口） | 治理门 + pre-merge 终态 + 候选状态 |

`scripts/validate_receipt.py`（#86 引入的回执六字段校验器）是独立资产，与本拆分无关，保留原名原功能。

## 归档复核扳机（3 个月）

- **触发条件**（任一）：归档满 3 个月（2026-11-08 起评估）且旧协议文件被外部引用量低于阈值（如 30 天内新 PR/Issue 引用 < 3 次）
- **动作**：旧协议正文压缩为单页指针（仅保留标题 + DEPRECATED 标注 + NORMATIVE_MAP 链接），完整历史由 git 保存
- **决策权**：Human Holder 拍板；不自动执行
- **对称纪律**：扳机未触发，不动旧协议——推翻留痕，不抹历史

## 对照速查

| 需要什么 | 去哪里 |
|---|---|
| 概念的唯一权威定义 | `governance/NORMATIVE_MAP.md` |
| 写任务授权规则 | `protocols/BINDING.md` |
| 动作时刻拦截规则 | `protocols/GATE.md` |
| 验收与合并规则 | `protocols/RECEIPT.md` |
| 判断对齐 / 反目标原则 | `protocols/PHILOSOPHY.md` |
| 历史协议全文 | `protocols/*.md`（归档态，DEPRECATED 标注） |
