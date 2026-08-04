# Artifact Delivery Layer

**PROTOCOL_STATUS:** `ADOPTED_GOVERNANCE_SPECIFICATION`
**TASK_ID:** ADT-S2-003-ARTIFACT-DELIVERY-R1
**INPUT:** S2-002-A Runtime Experiment § Correction

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

`Artifact` 和 `Location` 不是可选的备注——它们是完成的一部分。
没有这两个字段的任务不算完成。

---

## 3. Artifact Delivery Card

每次任务完成时，Maker Progress Receipt 和 Holder Summary 必须包含以下字段：

| 字段 | 含义 | 示例 |
|---|---|---|
| `artifact_type` | 产物类型 | `PR`, `file`, `commit`, `document`, `branch` |
| `artifact_location` | 产物位置（人类可访问） | `https://github.com/.../pull/55`, `MEDIA:/path/to/file`, `docs/xxx.md` |
| `artifact_format` | 交付格式 | `markdown`, `JSON`, `HTML`, `source-code` |
| `verification_command` | 如何验证产物存在 | `gh pr view 55`, `ls path/to/file`, `python scripts/validate.py` |
| `human_access_path` | 人类最简单的访问方式 | "点击链接"、"打开文件"、"运行命令" |

### 3.1 最小示例

```yaml
artifact:
  type: PR
  location: https://github.com/butbutbutbutbutbut/adaptive-digital-team/pull/55
  format: markdown + diff
  verification: gh pr view 55 --json state,mergeable
  human_access: 打开链接即可查看代码变更和 CI 状态
```

### 3.2 多产物

一个任务可能产出多个产物（例如：PR + 生成的文档 + 证据截图）。
Delivery Card 使用列表：

```yaml
artifacts:
  - type: PR
    location: https://github.com/.../pull/55
    ...
  - type: file
    location: docs/delivery/result.md
    ...
  - type: file
    location: MEDIA:/path/to/screenshot.png
    ...
```

---

## 4. 集成位置

### 4.1 Maker Progress Receipt

Maker 完成任务后，Progress Receipt 必须包含 `artifact` 或 `artifacts` 字段。

```
TASK_ID: ADT-xxx
HEAD_SHA: abc123
artifact:
  type: commit
  location: branch hermes/adt-xxx-r1@abc123
  verification: git show abc123
  human_access: PR 链接
```

### 4.2 Checker Receipt

Checker 独立验证产物存在：`artifact_exists: true/false`，验证命令输出。

### 4.3 Holder Summary

Holder 聚合时必须将 artifact 信息不变形地传递给 Human。
Holder 不得将 `MEDIA:/path/to/file` 转换为"文件已生成"——必须保留原始路径。

### 4.4 Controller / Project Control 回报

Controller 回报 Human 时，Artifact Location 必须作为首要信息呈现——不是附注，
不是脚注，是完成通知的核心内容。

---

## 5. 反目标

- 不为产物增加"确认产物已收到"的人类确认步骤（那是 Human Point Budget 的事）
- 不为验证失败自动创建修复任务（那是独立决策）
- 不要求每个 commit 都带 Delivery Card（只在任务完成节点触发）
- 产物位置不替代内容审查——位置正确 ≠ 内容正确

---

## 6. 与现有机制的关系

| 机制 | 关系 |
|---|---|
| Evidence Card | Evidence Card 记录"怎么做的"；Delivery Card 记录"产物在哪" |
| Candidate Identity | Candidate 的 SHA 是产物标识；Delivery Card 补充人类可读位置 |
| Checker | Checker 在审计时验证 artifact_exists |
| Scope Enforcement | 产物文件必须在 authorized_write_scope 内 |

---

## 7. 最低可行实施

第一期只要求 Maker Progress Receipt 和 Holder Summary 包含 artifact 字段。
Checker 附加 artifact_exists 验证。Controller 回报中 artifact 前置。

不要求自动化 enforcement——先在 Humans 使用中验证格式是否能覆盖所有场景。
