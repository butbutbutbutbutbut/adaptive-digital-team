# ADT 人格记忆备份与凭据边界设计 R1

**AUTHORIZATION_ID:** ADT-PERSONA-MEMORY-BACKUP-CREDENTIAL-BOUNDARY-20260720-001
**TASK_ID:** ADT-PERSONA-MEMORY-BACKUP-AND-CREDENTIAL-BOUNDARY-R1
**STATUS:** DESIGN_CANDIDATE / IMPLEMENTATION_NOT_AUTHORIZED
**BASE:** main@0e9b39d57a4c5a8e306cf848dcbc6eb3f212e9f7
**PRECEDING:** ADT 部署方案 v0.2 § B4 + D9（`deployment_plan_v0_2.md`）
**INPUT:** Holder 提供的《ADT 部署预检纠偏与下一轮交接.md》

---

## 本轮修复

- **正在修什么：** ADT 部署方案 v0.2 中 B4（记忆备份语义）和 D9（凭据边界）的设计缺口——原方案方向正确但缺少冻结级设计规范。
- **为什么要修：** 记忆层模糊会导致过收集、遗忘权失效、加密密钥混入运行环境；凭据边界未冻结会导致 PAT 权限被误解、Token 生命周期不明确、Maker 能力边界被滑移。
- **修完后解决什么风险：** 记忆备份从"全量状态上传"纠正为"筛选加密快照"；凭据从"临时提升权限"纠正为"固定权限 Token + 任务租约挂载"；安鼎 Maker/Checker 边界从硬禁止纠正为能力-角色-授权三层分离。
- **本轮不处理什么：** 不实施备份、不创建 PAT、不创建私有仓库、不轮换凭据、不接入飞书、不实施 Gateway 或记忆桥、不授予自动 Ready/Merge。

---

## 一、MEMORY_LAYER_MODEL — 三层记忆模型

### 1.1 本地运行状态层（Layer 0: Runtime State）

```
state.db
```

| 属性 | 值 |
|---|---|
| 用途 | 会话状态、工具运行状态、缓存、索引、本地短期上下文 |
| 读取 | 仅本地 Agent 运行时 |
| 写入 | Hermes 运行时自动 |
| 上传 | **禁止** — 不进入 GitHub、不进入人格记忆仓库、不作为跨设备恢复对象 |
| 灾备 | 使用独立本地磁盘级备份机制，与人格记忆仓库完全分离 |
| 加密上传 | **即使加密也不得上传** |
| 恢复 | 不作为正式跨设备恢复对象 |

**硬约束：**

```text
FULL_STATE_DB_UPLOAD: PROHIBITED
FULL_STATE_DB_IN_PERSONA_REPO: PROHIBITED
FULL_STATE_DB_AS_RECOVERY_TARGET: PROHIBITED
FULL_STATE_DB_ENCRYPTED_UPLOAD: PROHIBITED
```

完整 `state.db` 不进入任何 GitHub 仓库、不进入人格备份、不作为正式跨设备恢复对象。本地灾备与人格记忆恢复是两个独立系统。

### 1.2 正式加密长期记忆快照层（Layer 1: Encrypted Long-Term Memory Snapshots）

```
memory-snapshot/
├── durable_facts.jsonl
├── preferences.jsonl
├── relationship_context.jsonl
├── project_decisions.jsonl
├── unresolved_commitments.jsonl
└── manifest.json
```

**应保留（INCLUDE）：**

- 稳定人格偏好
- 长期沟通习惯
- Human 明确确认的约束
- 已确认项目决策
- 角色关系
- 长期承诺
- 对未来交互确有价值的经历摘要

**应排除（EXCLUDE）：**

- 完整聊天原文
- 寒暄和重复内容
- 临时情绪
- 工具日志
- 缓存与索引
- Secret、Token、Cookie
- 未脱敏第三方隐私
- 已失效或被推翻的推论
- 可从正式仓库恢复的冗余内容

**硬约束：**

```text
SNAPSHOT_MUST_BE_FILTERED: TRUE
SNAPSHOT_MUST_BE_ENCRYPTED: TRUE
SNAPSHOT_MUST_HAVE_MANIFEST: TRUE
SNAPSHOT_MUST_HAVE_SHA256: TRUE
RAW_CHAT_IN_SNAPSHOT: PROHIBITED
SECRETS_IN_SNAPSHOT: PROHIBITED
UNSCRUBBED_THIRD_PARTY_PII_IN_SNAPSHOT: PROHIBITED
```

### 1.3 可过期短期工作记忆层（Layer 2: Expiring Short-Term Working Memory）

| 属性 | 值 |
|---|---|
| 用途 | 跨任务临时上下文、近期工作线索 |
| 保留期 | 7–14 天（可配置） |
| 到期行为 | 自动删除或重新筛选 |
| 与 Layer 1 关系 | 不混入永久人格记忆 |

**硬约束：**

```text
SHORT_TERM_MUST_EXPIRE: TRUE
SHORT_TERM_DEFAULT_TTL_DAYS: [7, 14]
SHORT_TERM_MERGE_INTO_LONG_TERM: PROHIBITED_WITHOUT_FILTERING
```

---

## 二、MEMORY_CANDIDATE_PIPELINE — 记忆候选筛选流程

### 2.1 冻结流程

```text
state.db (只读)
  → Memory Candidate Extractor（候选提取）
  → Secret / PII Scanner（Secret / 第三方隐私扫描）
  → Categorizer（分类）
  → Deduplicator + Compressor（去重与压缩）
  → Stability + Future Value Evaluator（稳定性与未来价值判断）
  → Human Approval Gate（Human 敏感项审批）
  → Encryptor（加密快照）
  → Private Repository Archive（私有仓库存档）
```

### 2.2 各阶段硬约束

| 阶段 | 约束 |
|---|---|
| 候选提取 | 只读 state.db；不得输出真实聊天正文 |
| Secret 扫描 | 必须扫描 API Key、Token、Cookie、密码、私钥模式 |
| PII 扫描 | 必须扫描第三方姓名、手机号、地址、身份证号等 |
| 分类 | 按允许类别归类 |
| 去重与压缩 | 合并重复信息；摘要化长文本 |
| 稳定性判断 | 一次性事件、临时情绪不进入长期记忆 |
| Human 审批 | 敏感/高置信度低项必须经 Human 确认 |
| 加密 | 加密必须在本地完成，先加密再上传 |
| 归档 | 仅推送加密快照 + manifest + checksum |

**硬约束：**

```text
PIPELINE_MUST_BE_READ_ONLY_TO_STATE_DB: TRUE
PIPELINE_MUST_NOT_OUTPUT_RAW_CHAT: TRUE
PIPELINE_MUST_SCAN_SECRETS: TRUE
PIPELINE_MUST_SCAN_THIRD_PARTY_PII: TRUE
PIPELINE_MUST_ENCRYPT_BEFORE_UPLOAD: TRUE
```

---

## 三、MEMORY_RECORD_SCHEMA — 正式记忆记录规范

### 3.1 字段定义

```yaml
memory_id:            # 全局唯一标识符，格式: {agent_identity}-mem-{uuid_short}
category:             # 允许类别之一（见 3.2）
summary:              # 单句摘要，不含原文
source_time_range:    # 源数据时间范围 {start: ISO8601, end: ISO8601}
source_hash:          # 源 state.db 片段或会话 hash（用于可审计性）
sensitivity:          # none | low | medium | high | critical
confidence:           # 0.0–1.0，提取时的置信度
retention:            # permanent | long | medium | short
expires_at:           # ISO8601 或 null（permanent 时）
supersedes:           # 被本记录替代的旧 memory_id 列表，可为空
human_approved:       # true | false — Human 是否已审批
created_at:           # ISO8601 记录创建时间
invalidated_at:       # ISO8601 或 null — 记录失效时间
deletion_reason:      # null 或失效原因（见 6.2）
```

### 3.2 允许类别

```text
durable_facts          — 持久事实（如用户姓名、身份、环境配置）
preferences            — 用户偏好与风格
relationship_context   — 关系上下文与角色动态
project_decisions      — 已确认的项目决策
unresolved_commitments — 未解决的承诺与待办
```

**禁止类别：**

```text
raw_chat               — 原始聊天内容
temporary_emotion       — 一次性情绪
tool_logs               — 工具调用日志
secrets_and_credentials — 凭据与密钥
uncorroborated_inference — 未确认推断
```

### 3.3 示例（仅结构示意，不含真实数据）

```yaml
memory_id: "xiaohe-mem-a1b2c3d4"
category: "preferences"
summary: "用户偏好简短对话风格，在微信中不喜欢分析性回复"
source_time_range: {start: "2026-07-01T00:00:00Z", end: "2026-07-15T00:00:00Z"}
source_hash: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
sensitivity: "low"
confidence: 0.95
retention: "permanent"
expires_at: null
supersedes: []
human_approved: true
created_at: "2026-07-15T12:00:00Z"
invalidated_at: null
deletion_reason: null
```

---

## 四、SNAPSHOT_AND_MANIFEST_SCHEMA — 快照与清单结构

### 4.1 快照结构

```text
snapshots/<snapshot_id>.tar.age
```

- 格式：tar 归档，age 加密
- 内容：所有类别 `.jsonl` 文件 + `manifest.json`
- SHA-256 校验：加密后对整个 `.tar.age` 文件计算

### 4.2 Manifest Schema

```yaml
snapshot_id:              # 格式: {agent_identity}-snap-{ISO8601_basic}-{uuid_short}
agent_identity:           # "xiaohe" | "anding"
persona_hash:             # 创建快照时的 SOUL.md + ROLE_BOUNDARIES.md 的 SHA-256
created_at:               # ISO8601
source_range:             # {start: ISO8601, end: ISO8601}
record_count:             # 总记录数
category_counts:          # 按类别统计
  durable_facts: 0
  preferences: 0
  relationship_context: 0
  project_decisions: 0
  unresolved_commitments: 0
encryption_format:        # "age-v1"
encrypted_file_sha256:    # 加密后 .tar.age 文件的 SHA-256
schema_version:           # "1"
supersedes_snapshot:      # 被本快照替代的旧 snapshot_id 或 null
restoration_status:       # "UNTESTED" | "TEST_PASSED" | "TEST_FAILED"
human_approval_status:    # "PENDING" | "APPROVED" | "REJECTED"
```

### 4.3 Manifest 示例（结构示意）

```yaml
snapshot_id: "xiaohe-snap-20260720T120000Z-a1b2c3d4"
agent_identity: "xiaohe"
persona_hash: "sha256:abc123def456..."
created_at: "2026-07-20T12:00:00Z"
source_range:
  start: "2026-06-01T00:00:00Z"
  end: "2026-07-20T00:00:00Z"
record_count: 42
category_counts:
  durable_facts: 8
  preferences: 15
  relationship_context: 10
  project_decisions: 7
  unresolved_commitments: 2
encryption_format: "age-v1"
encrypted_file_sha256: "sha256:..."
schema_version: "1"
supersedes_snapshot: "xiaohe-snap-20260701T000000Z-e5f6g7h8"
restoration_status: "UNTESTED"
human_approval_status: "PENDING"
```

**本设计仅定义 Schema，不实施生成器。**

---

## 五、RETENTION_AND_FORGETTING — 保留与遗忘规则

### 5.1 临时记忆到期删除

| 类型 | TTL | 到期行为 |
|---|---|---|
| 短期工作记忆 | 7–14 天 | 自动删除，不进入长期快照 |
| 临时候选记忆 | 任务结束 + 7 天 | 标记失效，下次快照时排除 |

### 5.2 长期记忆失效

长期记忆（`retention: permanent | long`）在以下条件下失效：

| 条件 | 行为 |
|---|---|
| `expires_at` 到期 | `invalidated_at` 设为到期时间 |
| Human 显式删除 | `invalidated_at` 设为删除时间，`deletion_reason` 记录原因 |
| `supersedes` 被新记录覆盖 | 旧记录 `invalidated_at` 设为新记录 `created_at` |

### 5.3 Supersedes 覆盖关系

- 新记录创建时，`supersedes` 字段列出被替代的旧 `memory_id` 列表
- 旧记录标记 `invalidated_at` 和 `deletion_reason: "SUPERSEDED_BY_{new_memory_id}"`
- 下一次快照时，带 `invalidated_at` 的记录不进入新快照
- 旧快照中仍保留已失效记录（加密快照不可变），但 manifest 中标记 `supersedes_snapshot`

### 5.4 Human 删除权与 Tombstone 机制

```text
HUMAN_DELETE_RIGHT: ABSOLUTE
HUMAN_DELETE_SCOPE: ANY_MEMORY_RECORD
HUMAN_DELETE_EFFECT: IMMEDIATE_INVALIDATION + NEXT_SNAPSHOT_EXCLUSION
HUMAN_DELETE_TOMBSTONE: TRUE
```

Human 可随时要求删除任何记忆记录。删除后：

- 记录标记 `invalidated_at` 和 `deletion_reason`
- 该 `memory_id` 进入 **tombstone / invalidation 清单**
- 新快照不包含该记录
- Tombstone 清单随 manifest 持久化，作为恢复时的硬排除过滤器
- 审计日志记录删除动作

### 5.4.1 恢复与反删除（Undelete）

任何恢复操作（包括从旧快照恢复、跨设备迁移、灾备恢复）**必须**应用 tombstone / invalidation 清单：

```text
RESTORE_MUST_APPLY_TOMBSTONE_LIST: TRUE
RESTORE_MUST_NOT_REACTIVATE_INVALIDATED_RECORDS: TRUE
RESTORE_MUST_NOT_REACTIVATE_DELETED_RECORDS: TRUE
DIRECT_RESURRECTION_OF_OLD_RECORD: PROHIBITED
```

Human 反删除（undelete）必须遵循以下流程：

1. **创建新 `memory_id`** — 禁止直接复活旧记录的 `memory_id`
2. **`supersedes` 引用原记录** — 新记录的 `supersedes` 字段列出被恢复的原 `memory_id`
3. **记录恢复理由** — `deletion_reason` 记录恢复原因和 Human 批准信息
4. **更新 Tombstone** — 原 tombstone 条目更新，标记 `undeleted_by: {new_memory_id}`
5. **经标准审批入快照** — 新记录经 Human 审批后进入下次快照

```yaml
# 反删除示例（结构示意）
memory_id: "xiaohe-mem-f9e0d1c2"           # 新 memory_id
category: "preferences"
summary: "（恢复）用户偏好简短对话风格"       # 保留原内容摘要
supersedes: ["xiaohe-mem-a1b2c3d4"]        # 引用被恢复的原记录
deletion_reason: "UNDELETED_BY_HUMAN — 原始删除原因已过时，Human 批准恢复"
human_approved: true
```

### 5.5 第三方隐私删除

如果记忆候选扫描发现第三方 PII（如联系人姓名、手机号）：

```text
THIRD_PARTY_PII_ACTION: BLOCK_AT_SCAN
THIRD_PARTY_PII_IN_SNAPSHOT: PROHIBITED
```

如果 Human 要求删除涉及第三方的已存储记忆记录，执行标准 Human 删除流程。

### 5.6 被推翻项目结论的 Invalidation

```text
OVERTURNED_DECISION_ACTION:
  - 旧 decision 记录: invalidated_at = now, deletion_reason = "OVERTURNED_BY_{new_decision_id}"
  - 新 decision 记录: supersedes = [old_decision_id]
  - 旧快照: 不变（不可变）
  - 新快照: 仅包含新 decision，不包含旧 decision
```

### 5.7 删除后的快照处置

| 场景 | 旧加密快照 | 新快照 | 审计记录 |
|---|---|---|---|
| 记录失效 | 保持不变（不可变） | 排除失效记录 | 记录 invalidation 事件 |
| Human 删除 | 保持不变 | 排除已删除记录 | 记录 deletion 事件（不含被删内容） |
| 全量清除请求 | 旧快照保留（不可变），Human 可选择删除旧快照文件 | 空快照或最小快照 | 记录清除事件 |

### 5.8 审计记录保留粒度

审计日志记录：

- 谁发起了什么操作（Human / Agent / Automated Pipeline）
- 操作时间
- 操作类型（create / invalidate / delete / snapshot）
- 目标 memory_id 或 snapshot_id
- 操作结果

审计日志不记录：

- 被删除的记忆内容本身
- 加密密钥
- Token

---

## 六、ENCRYPTION_AND_KEY_SEPARATION — 加密与密钥分离

### 6.1 密钥分离原则

```text
GITHUB_TOKEN_AND_MEMORY_DECRYPTION_KEY: FULLY_SEPARATE
AGENT_RUNTIME_HOLDS_LONG_TERM_DECRYPTION_KEY: PROHIBITED
HUMAN_HOLDS_PRIVATE_KEY: TRUE
ENCRYPT_BEFORE_UPLOAD: TRUE
```

GitHub Token 与记忆解密密钥**完全分离**。Agent Runtime 不持有长期解密私钥。

### 6.2 密钥模型

| 密钥 | 持有者 | 用途 | 存储位置 |
|---|---|---|---|
| 加密公钥 | Agent Runtime | 加密记忆快照 | Agent 环境（生命周期内） |
| 解密私钥 | Human | 解密恢复记忆 | Human 安全保管（不进入 Agent 环境） |
| GitHub PAT | Agent（按租约） | 推送快照到私有仓库 | Agent 环境（任务租约内） |
| GitHub PAT | Agent（常驻只读） | 校验 manifest 完整性 | Agent 环境 |

### 6.3 加密流程

```text
1. Agent Runtime 生成 age 密钥对（或使用预配置公钥）
2. 用公钥加密 tar 归档 → .tar.age
3. 计算 encrypted_file_sha256
4. 生成 manifest.json
5. 推送 .tar.age + manifest.json + checksums 到私有仓库
6. 私钥由 Human 保管，不进入 Agent 环境
```

### 6.4 每个 Agent 使用独立密钥对

```text
XIAOHE_KEY_PAIR: 独立生成
ANDING_KEY_PAIR: 独立生成
CHECKER_DOES_NOT_HOLD_MEMORY_DECRYPTION_KEY: TRUE
```

两个 Agent 不共享密钥对。

### 6.5 恢复流程

```text
1. Human 临时提供解密私钥
2. Agent Runtime 用私钥解密 .tar.age
3. 校验 manifest 声明的 SHA-256
4. 导入记录到新 state.db 或新 Profile
5. 恢复完成后 Human 收回私钥
6. Agent Runtime 不保留私钥
```

### 6.6 硬约束

```text
PRIVATE_KEY_IN_REPO: PROHIBITED
PRIVATE_KEY_IN_ENV_FILE: PROHIBITED
PRIVATE_KEY_IN_LOG: PROHIBITED
PRIVATE_KEY_IN_AGENT_MEMORY: PROHIBITED
PRIVATE_KEY_IN_CONFIG_YAML: PROHIBITED
SHA256_CHECKSUM_REQUIRED_PER_SNAPSHOT: TRUE
```

---

## 七、CREDENTIAL_MODEL — 最终凭据模型

### 7.1 凭据矩阵

| 凭据 | 是否常驻 | 能力 | 生命周期 |
|---|---:|---|---|
| `anding-default-readonly` | 是 | ADT 仓库、产品仓库、必要索引仓库只读 | 30–90 天，轮换 |
| `anding-governance-writer` | 否 | 预设仓库级 Contents Write | 任务授权后临时挂载，任务结束卸载 |
| `checker-default-readonly` | 是（Checker 环境内） | 指定仓库 Contents Read + PR Read + Metadata Read | 30–90 天，独立存储 |
| Human 网页身份 | 是 | Ready、Merge、仓库管理 | 2FA / Passkey 保护 |
| Human 临时 CLI Token | 否 | 单仓库、短生命周期、精确操作 | 按需创建，任务结束吊销 |
| 记忆解密密钥 | 否 | 解密恢复记忆快照 | Human 保管，仅恢复时临时提供 |

### 7.2 凭据详细定义

#### anding-default-readonly

```yaml
credential_id: "anding-default-readonly"
persistent: true
permissions:
  contents: "read"
  pull_requests: "read"
  metadata: "read"
repositories:
  - butbutbutbutbutbut/adaptive-digital-team
  - butbutbutbutbutbut/he-weizhi-site
  - butbutbutbutbutbut/xiaohe-memory-index-private  # 如存在
validity_days: 90
storage: "anding_agent_environment"
```

#### anding-governance-writer

```yaml
credential_id: "anding-governance-writer"
persistent: false
permissions:
  contents: "write"
mount_trigger:
  - HUMAN_EXPLICIT_AUTHORIZATION
  - TASK_ID_BOUND
  - REPOSITORY_BOUND
  - BASE_SHA_BOUND
  - FILE_PATH_BOUND
  - ACTION_BOUND
unmount_trigger: TASK_COMPLETE_OR_REVOKE
validity_days: 7  # 即使未使用，创建后 7 天自动过期
```

#### checker-default-readonly

```yaml
credential_id: "checker-default-readonly"
persistent: true
permissions:
  contents: "read"
  pull_requests: "read"
  metadata: "read"
repositories:
  - butbutbutbutbutbut/adaptive-digital-team
  - butbutbutbutbutbut/he-weizhi-site
validity_days: 90
storage: "independent_checker_environment"
independence_requirement:
  - SEPARATE_PROFILE
  - SEPARATE_SESSION
  - READ_ONLY_TOKEN
  - NO_SHARED_TOKEN_WITH_ANDING_OR_XIAOHE
```

#### Human 网页身份

```text
AUTH_METHOD: GITHUB_WEB_LOGIN
SECURITY: 2FA_OR_PASSKEY
CAPABILITIES:
  - READY_PR
  - MERGE_PR
  - DELETE_BRANCH
  - MANAGE_REPOSITORY_SETTINGS
  - MANAGE_RULESETS
  - MANAGE_BRANCH_PROTECTION
```

#### Human 临时 CLI Token

```yaml
credential_id: "human-temporary-cli"
persistent: false
permissions: # 仅授予目标操作需要的权限
  - 目标操作需要的最小权限集
repositories: ["single_target_repo"]
validity_days: 1  # 极短生命周期
storage: "HUMAN_LOCAL_ONLY — 不进入 Agent 环境"
```

#### 记忆解密密钥

```yaml
credential_id: "memory-decryption-key"
type: "age_private_key"
persistent: false
holder: "HUMAN_ONLY"
storage: "HUMAN_SECURE_STORAGE"
agent_access: "TEMPORARY_DURING_RESTORE_ONLY"
```

---

## 八、PAT_TECHNICAL_BOUNDARY — PAT 技术边界

### 8.1 PAT 权限不可在任务中临时提升

```text
PAT 在创建时已具备固定权限。
Human 授权后临时挂载该凭据。
任务结束后卸载、撤销或轮换。

临时的：
  - Token 注入（凭据可用性）
  - 任务租约（时效性）

非临时的：
  - PAT 权限本身（创建时固定）
```

### 8.2 Fine-Grained PAT 不支持路径级写入限制

`Contents: Write` 是仓库级权限，不可限制到特定路径。

路径范围由以下机制约束：

```text
Human 精确授权路径
+ PROJECT_STATE authorized_write_scope
+ ADT Validator（文件范围校验）
+ PR-only（禁止直接写 main）
+ Branch Protection / Ruleset
+ CODEOWNERS / 必需检查
```

推荐表述：

```text
PAT_CAPABILITY: repository-level Contents Write
AUTHORIZED_WRITE_SCOPE: task-level exact paths
ENFORCEMENT: validator + protected branch + PR review
```

### 8.3 禁止显示 Token 的验证命令

```text
PROHIBITED:
  gh auth token
  gh auth status --show-token
  # 或任何输出 Token 值的命令

ALLOWED:
  gh auth status
  gh api repos/{owner}/{repo} --jq '{full_name, permissions}'
```

### 8.4 PAT 不授予 Ready / Merge / 分支删除 / 仓库设置

Fine-Grained PAT 的 `Contents: Write` 权限不授予：

- Ready PR
- Merge PR
- 删除分支
- 修改仓库设置
- 修改 Ruleset / Branch Protection

这些操作需要 Human 网页身份或独立的高权限 Token。

---

## 九、TOKEN_MOUNT_LIFECYCLE — Token 挂载生命周期

### 9.1 完整流程

```text
STEP_0: Token 已创建，权限固定，处于未挂载状态

STEP_1: HUMAN_PRECISE_AUTHORIZATION
  Human 显式授权，绑定：
  - TASK_ID
  - AUTHORIZATION_ID
  - REPOSITORY
  - BASE_SHA
  - 精确文件路径
  - 精确允许动作

STEP_2: TOKEN_MOUNT
  将 anding-governance-writer 临时注入 Agent 环境
  记录挂载时间、绑定 TASK_ID

STEP_3: BRANCH_CREATION
  从 BASE_SHA 创建任务分支
  分支命名: hermes/{task-slug}

STEP_4: PR_ONLY_WRITE
  在任务分支上写入
  仅修改 AUTHORIZED_WRITE_SCOPE 内的文件
  git add 精确文件（禁止 git add .）
  git diff --cached 校验

STEP_5: VALIDATION
  运行 Validator（文件范围、格式、Schema）
  运行现有测试

STEP_6: PUSH_DRAFT_PR
  推送任务分支
  创建 Draft PR，目标为 main

STEP_7: TOKEN_UNMOUNT
  从 Agent 环境移除 writer credential
  记录卸载时间

STEP_8: SESSION_CLEANUP
  清理任务 Session

STEP_9: INDEPENDENT_CHECKER_AUDIT
  Independent Checker 使用 checker-default-readonly 执行审计
  审计完成后返回审计回执
```

### 9.2 异常处置

| 异常 | 行为 |
|---|---|
| Token 挂载失败 | 任务不启动，返回 BLOCKER |
| 写入文件超出 AUTHORIZED_WRITE_SCOPE | Validator 阻止提交 |
| Token 租约到期 | 强制卸载，任务挂起 |
| 任务被 Human 撤销 | 立即卸载 Token，清理分支 |
| CI 失败 | Token 保持已卸载，等待修复授权 |
| Token 泄露 | **HARD_STOP**：立即卸载凭据；立即撤销或轮换泄露的 Token；终止所有关联任务 Session；审计泄露时间窗内所有操作；通知 Human；未经新 Human 授权不得重新挂载任何凭据 |

### 9.3 Token 泄露应急程序

```text
TOKEN_LEAK_DETECTED:
  STEP_1: HARD_STOP — 暂停所有使用该凭据的进行中任务
  STEP_2: IMMEDIATE_UNMOUNT — 从所有 Agent 环境移除泄露凭据
  STEP_3: IMMEDIATE_REVOKE_OR_ROTATE — 撤销或轮换泄露的 Token
  STEP_4: TERMINATE_AFFECTED_SESSIONS — 终止与被泄露凭据关联的所有任务 Session
  STEP_5: AUDIT_EXPOSURE_WINDOW — 审计从疑似泄露时间点到卸载之间的所有操作
  STEP_6: NOTIFY_HUMAN — 通知 Human，提供泄露范围、受影响资源和审计结果
  STEP_7: RE_AUTHORIZATION_REQUIRED — 未经新 Human 授权不得重新挂载任何凭据

TOKEN_LEAK_PREVENTION:
  TOKEN_NEVER_IN_LOG: TRUE
  TOKEN_NEVER_IN_OUTPUT: TRUE
  TOKEN_NEVER_IN_MEMORY: TRUE
  TOKEN_NEVER_IN_ENV_FILE_COMMITTED: TRUE
```

---

## 十、ANDING_CAPABILITY_BOUNDARY — 安鼎能力边界

### 10.1 核心原则

```text
CAPABILITY_PRESENT ≠ ROLE_ASSIGNED ≠ AUTHORITY_GRANTED
```

| 概念 | 含义 | 示例 |
|---|---|---|
| 能力存在 | 系统能理解或调用什么 | 安鼎安装了 Maker / Checker skill |
| 任务身份 | 本轮以何种角色行动 | 安鼎本轮是 Holder，不是 Maker |
| Human 授权 | 本轮具体允许执行什么 | 写入 `docs/architecture/foo.md`，不允许写 `src/` |

### 10.2 安鼎可以

- 安装并读取 Maker / Checker 协议与技能
- 生成 Maker 执行任务
- 调度经 Human 授权的 Maker
- 请求 Independent Checker 审计
- 校验目标事实（Base / Head / 文件范围）
- 校验执行回执与审计回执完整性
- 识别 Base / Head / 文件范围漂移
- 执行 Validator、测试和状态一致性检查
- 在 Human 精确授权后，临时承担有限治理 Maker 任务

### 10.3 安鼎不得

| 禁止行为 | 原因 |
|---|---|
| 因安装 Maker skill 自动获得写入权 | 能力存在 ≠ 授权授予 |
| 因安装 Checker skill 自动签发 `AUDIT_PASS` | 技能存在 ≠ 审计结论 |
| 审计自己参与设计、调度、实现或修复的候选 | 非独立 |
| 同一任务兼任 Maker 与 Independent Checker | 角色分离 |
| 把内部检查冒充独立审计 | 必须标记 |
| 自行扩大仓库、工具、路径或凭据范围 | 授权不可自我扩大 |
| 自动 Ready | Human-only |
| 自动 Merge | Human-only |

### 10.4 非独立检查标记

安鼎执行的内部验证必须标记为以下之一：

```text
INTERNAL_VALIDATION   — 内部校验，非独立审计
TECHNICAL_REVIEW      — 技术审查，非独立审计
```

不得标记为：

```text
INDEPENDENT_AUDIT     — 仅 Independent Checker 可用
AUDIT_PASS            — 仅 Independent Checker 可签发
```

### 10.5 写入凭据的正确触发条件

```text
安鼎获得写入权的充要条件：
  Human 显式授权
  + TASK_ID 绑定
  + AUTHORIZATION_ID 绑定
  + REPOSITORY 绑定
  + BASE_SHA 绑定
  + 精确文件路径
  + 精确允许动作
  + Token 临时挂载
  + PR-only 写入
  + Validator 校验通过
  + 任务结束强制卸载
```

---

## 十一、DECISION_STATE — 决策状态登记

### 11.1 D6 — CLOSED

```text
D6: CLOSED
D6_RESULT: EMPTY_PROFILE_PLUS_SKILL_ALLOWLIST
```

安鼎 Profile 初始化为空，按白名单手动安装 Skills。

**安鼎 Skills 白名单：**

```text
adt/holder/SKILL.md
adt/maker/SKILL.md
adt/checker/SKILL.md
github/github-workflows/SKILL.md
autonomous-ai-agents/hermes-agent/SKILL.md
software-development/plan/SKILL.md
```

以及部署方案要求的辅助能力（repository-as-prompt 状态恢复、权限与事实源校验、Gateway、状态卡、审计日志、Holder 控制平面）。

### 11.2 B4 — DESIGN_CANDIDATE

```text
B4: DESIGN_CANDIDATE
B4_DESIGN_DOCUMENT: ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md
B4_IMPLEMENTATION: NOT_AUTHORIZED
B4_NEXT_GATE: EXTERNAL_INDEPENDENT_DESIGN_AUDIT
```

### 11.3 D9 — DESIGN_CANDIDATE

```text
D9: DESIGN_CANDIDATE
D9_DESIGN_DOCUMENT: ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md
D9_IMPLEMENTATION: NOT_AUTHORIZED
D9_REVISIONS_APPLIED:
  - PAT permissions cannot be elevated per task — 模型已修正为固定权限 + 任务租约挂载
  - PAT cannot enforce path-level write scope — 约束已转移到 Validator + PR-only + Branch Protection
  - Unsafe gh auth token verification command — 已标记为 PROHIBITED
  - Human Admin PAT is over-privileged — 已拆分为网页身份 + 临时 CLI Token
  - PAT-2 merge authority contradiction — 已统一：PAT-2 不可 Ready/Merge
  - Encrypted archive access boundary — 已规定 GitHub Token 与记忆解密密钥分离
D9_NEXT_GATE: EXTERNAL_INDEPENDENT_DESIGN_AUDIT
```

### 11.4 IMPLEMENTATION_STATUS

```text
IMPLEMENTATION_STATUS: NOT_AUTHORIZED
```

本设计文档冻结后，不授权实施。实施需独立设计审计通过 + Human 新授权。

---

## 硬约束汇总

```text
# 记忆层
FULL_STATE_DB_UPLOAD: PROHIBITED
FULL_STATE_DB_ENCRYPTED_UPLOAD: PROHIBITED
RAW_CHAT_IN_SNAPSHOT: PROHIBITED
SECRETS_IN_SNAPSHOT: PROHIBITED
UNSCRUBBED_THIRD_PARTY_PII_IN_SNAPSHOT: PROHIBITED

# 加密
PRIVATE_KEY_IN_REPO: PROHIBITED
PRIVATE_KEY_IN_ENV_FILE: PROHIBITED
PRIVATE_KEY_IN_LOG: PROHIBITED
PRIVATE_KEY_IN_AGENT_MEMORY: PROHIBITED
GITHUB_TOKEN_AND_DECRYPTION_KEY: FULLY_SEPARATE

# 凭据
TOKEN_PERMISSION_CANNOT_BE_ELEVATED_PER_TASK: TRUE
gh auth token: PROHIBITED
WRITE_IS_REPOSITORY_LEVEL_NOT_PATH_LEVEL: TRUE

# 安鼎边界
CAPABILITY_PRESENT ≠ ROLE_ASSIGNED ≠ AUTHORITY_GRANTED
SELF_AUDIT: PROHIBITED
AUTO_READY: PROHIBITED
AUTO_MERGE: PROHIBITED
SELF_AUTHORIZATION_EXPANSION: PROHIBITED

# 实施
IMPLEMENTATION: NOT_AUTHORIZED
```

---

**编制：** HERMES_SEPARATE_GOVERNANCE_MAKER-006
**目标审核：** EXTERNAL_INDEPENDENT_GOVERNANCE_CHECKER-007
**下一门禁：** EXTERNAL_INDEPENDENT_DESIGN_AUDIT
**Human 操作：** 不需要（设计候选，等待独立审计）
