> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# Artifact Delivery Layer

**PROTOCOL_STATUS:** `ADOPTED_GOVERNANCE_SPECIFICATION` / `ENFORCEMENT_NOT_IMPLEMENTED`
**TASK_ID:** ADT-S2-003-ARTIFACT-DELIVERY-R2
**INPUT:** S2-002-A Runtime Experiment § Correction
**ANTI_OBJECTIVE_REVIEW:** #59 post-merge review (6 findings, all resolved in R2)

---

## 1. 问题

ADT 当前完成链：

```
Decision → Status → Completion
```

Human 知道系统做了什么，但不知道最终产物在哪里。任务完成通知里写着"已完成"，
但没有指向产物的路径。

---

## 2. 修正

完成链增加两个节点：

```
Decision → Action → Artifact → Location → Verification
```

`Artifact` 和 `Location` 是完成的一部分。没有这两个字段的任务不算完成。

**当前实施范围（R2）：** Maker Progress Receipt 和 Holder Summary 必须包含
artifact 字段。Checker Receipt 附加 `artifact_exists` 验证。Controller
回报中 artifact 前置。自动化 enforcement 待后续协议实现。

---

## 3. Artifact Delivery Card

### 3.1 必填字段

每次任务完成时，Maker Progress Receipt 必须包含：

| 字段 | 含义 | 示例 |
|---|---|---|
| `artifact_type` | 产物类型 | `PR`, `file`, `commit`, `document`, `branch`, `conclusion` |
| `artifact_location` | 产物位置（人类可访问） | `https://github.com/.../pull/55`, `MEDIA:/path/to/file` |
| `verification_hint` | 建议的验证方式（非强制） | `gh pr view 55`, `ls path/to/file` |

### 3.2 可选字段

| 字段 | 含义 |
|---|---|
| `artifact_format` | 交付格式（`markdown`, `JSON`, `source-code` 等） |
| `human_access_note` | 额外的人类访问说明 |

### 3.3 最小示例

```yaml
artifact:
  type: PR
  location: https://github.com/Kairos-zhi/adaptive-digital-team/pull/55
  verification_hint: gh pr view 55 --json state,mergeable
```

### 3.4 多产物

一个任务可能产出多个产物。Delivery Card 使用列表：

```yaml
artifacts:
  - type: PR
    location: https://github.com/.../pull/55
  - type: file
    location: docs/delivery/result.md
```

### 3.5 零文件产物：`conclusion` 类型

调研、审查、分析类任务不产生独立文件。使用 `conclusion` 类型：

```yaml
artifact:
  type: conclusion
  location: 本 receipt 上文（见 §Analysis 节）
  verification_hint: 阅读本 receipt 的 Analysis 和 Recommendation 部分
```

---

## 4. 集成位置

### 4.1 Maker Progress Receipt（强制）

Maker 完成任务后，Progress Receipt 必须包含 `artifact` 或 `artifacts` 字段。

```
TASK_ID: ADT-xxx
HEAD_SHA: abc123
artifact:
  type: commit
  location: branch hermes/adt-xxx-r1@abc123
  verification_hint: git show abc123
```

### 4.2 Checker Receipt

Checker 独立验证产物存在：`artifact_exists: true/false`。
Checker 在自己的环境中判断——不依赖 Maker 提供的 `verification_hint`。

### 4.3 Holder Summary（强制）

Holder 聚合时必须将 artifact 信息不变形地传递给 Human。
Holder 不得将 `MEDIA:/path/to/file` 转换为"文件已生成"——必须保留原始路径。

### 4.4 Controller / Project Control 回报

Controller 回报 Human 时，Artifact Location 必须作为首要信息呈现——不是附注，
不是脚注，是完成通知的核心内容。

---

## 5. 反目标

- 不增加"确认产物已收到"的人类确认步骤
- 不为验证失败自动创建修复任务
- 不要求每个 commit 都带 Delivery Card（只在任务完成节点触发）
- 产物位置不替代内容审查——位置正确 ≠ 内容正确
- `verification_hint` 是建议，不是强制验证——Checker 用自己的环境判断 artifact_exists

---

## 6. 与现有机制的关系

| 机制 | 关系 |
|---|---|
| Evidence Card | Evidence Card 记录"怎么做的"；Delivery Card 记录"产物在哪" |
| Candidate Identity | Candidate 的 SHA 是产物标识；Delivery Card 补充人类可读位置 |
| Checker | Checker 在审计时独立验证 artifact_exists |
| Scope Enforcement | 产物文件必须在 authorized_write_scope 内 |
