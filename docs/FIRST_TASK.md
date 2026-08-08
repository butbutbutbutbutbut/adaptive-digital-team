# 第一次派单：端到端操作手册

本手册面向第一次给 Maker 派写任务的 Holder。流程：拍板 → 派单 → 写 binding → 执行 → 验收。全程约 30 分钟。

## 1. 前置阅读

- [`protocols/PHILOSOPHY.md`](../protocols/PHILOSOPHY.md)（131 行）——5 条原则 + 判断指南。先对齐判断，再动手。

## 2. 角色确认

| 角色 | 职责 |
|------|------|
| Human Holder | 拍板：授权范围、验收标准、最终决定权 |
| Maker | 在授权范围内执行，产出 Progress Receipt |
| Checker | 独立验收，产出 checker_receipt.json |

硬规则：**一人不得兼任 Maker + Checker**；Maker 不得自验收自己的输出。

## 3. 派单（Dispatch Card）

模板见 [`protocols/BINDING.md`](../protocols/BINDING.md) §9（Authority Dispatch Card）。必填：TASK_ID / AUTHORITY_SOURCE / HUMAN_ROLE / BOUNDARY（REPOSITORY + BASE_SHA + BRANCH + FILES_IN_SCOPE）/ TOKEN_ID / 验收标准（模板外附加行）。

```text
AUTHORITY DISPATCH CARD
  TASK_ID: ADT-2026-08-08-001
  AUTHORITY_SOURCE: Human Holder 拍板记录（2026-08-08）
  HUMAN_ROLE: HUMAN_HOLDER
  ISSUED_AT: 2026-08-08T10:00:00Z
  EXPIRES_AT: 2026-08-08T18:00:00Z
  AUTHORIZED_ACTIONS: [write, commit]
  BOUNDARY:
    REPOSITORY: butbutbutbutbutbut/adaptive-digital-team
    BASE_SHA: c4615f310482dfd7cbd9c1f0b024807cd3974d63
    BRANCH: maker/docs-fix-r1
    FILES_IN_SCOPE: [README.md, docs/FIRST_TASK.md]
  PUBLISH_LEASE:
    PUSH_ALLOWED: NO
    DRAFT_PR_ALLOWED: NO
    READY_ALLOWED: NO
    MERGE_ALLOWED: NO
    BRANCH_DELETE_ALLOWED: NO
  TOKEN_ID: TKN-2026-08-08-001
  RESOURCE_TIER: economy
  验收标准: diff 仅限 FILES_IN_SCOPE；validate_binding.py PASS；Checker 独立验收
```

## 4. 写 binding（UNGRANTED → 授权态）

文件：`.hermes/CANDIDATE_BINDING.json`。空闲态为 `authorization_id: UNGRANTED`；派单后整文件替换为：

```json
{
  "authorization_id": "AUTH-2026-08-08-001",
  "authority_source": "HUMAN_HOLDER",
  "human_role": "HUMAN_HOLDER",
  "repository": "butbutbutbutbutbut/adaptive-digital-team",
  "base_sha": "c4615f310482dfd7cbd9c1f0b024807cd3974d63",
  "branch": "maker/docs-fix-r1",
  "task_id": "ADT-2026-08-08-001",
  "authorized_write_scope": ["README.md", "docs/FIRST_TASK.md"],
  "authorized_actions": ["write", "commit"],
  "approved": true,
  "approved_at": "2026-08-08T10:00:00Z"
}
```

`base_sha` 换成当前 main 的 HEAD（`git rev-parse origin/main`）。字段速查：

| 字段 | 必填 | 说明 |
|------|------|------|
| authorization_id | ✅ | 授权标识，如 AUTH-{date}-{seq} |
| authority_source | ✅ | 授权来源（HUMAN_HOLDER 等） |
| human_role | ✅ | 授权 Human 的角色 |
| repository | ✅ | owner/repo 格式，必须与 PROJECT_STATE.md 一致 |
| base_sha | ✅ | 40 位完整 SHA（当前 main HEAD） |
| branch | ✅ | 任务分支名 |
| authorized_write_scope | ✅ | 授权文件列表；**不得包含 binding 文件自身** |
| authorized_actions | ✅ | 非空操作列表（write/commit/pr） |
| task_id / approved / approved_at | 建议 | 与 Dispatch Card 保持一致 |

实测：`python scripts/validate_binding.py` → 输出 `PASS: All validations passed` 即授权生效。

## 5. 执行

Maker 在 scope 内干活，[`scripts/validate_gate.py`](../scripts/validate_gate.py)（GATE 核）自动拦越界。遇 BLOCKED：查错误码表 [`protocols/GATE.md`](../protocols/GATE.md) §8（Token 异常回收恢复表）与 §10（fail-closed 行为表）。

## 6. 验收闭环

Checker 独立验收（独立窗口/进程，不继承 Maker 会话）→ 写 `.hermes/checker_receipt.json`。回执必须含 17 字段，缺一即不完整：见 [`protocols/RECEIPT.md`](../protocols/RECEIPT.md) §5（17 字段回执完备性校验）。无独立验收不合并（RECEIPT 铁律）。

## 7. 常见错误速查

| 错误 | 含义 | 处理 |
|------|------|------|
| `SCOPE_VIOLATION` | 改了 scope 外文件 | 移回 scope 内，或回 Holder 重新授权 |
| `SELF_REFERENTIAL_SCOPE` | scope 含 binding 文件自身 | 从 scope 移除 `.hermes/CANDIDATE_BINDING.json` |
| `BASE_DRIFT` / `STOPPED_BASE_DRIFT` | 基座 SHA 漂移 | 停手，回 Holder 重新授权（BINDING 不变量 I2） |
| `TOKEN_LOST` | binding 缺 token 字段 | 按 GATE §8 恢复：以派发记录重建，报告 Human |
