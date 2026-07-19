# Project State

This file is the single runtime binding record for the ADT organization
repository. It serves as the authoritative `.adt/project-binding.yaml`
equivalent for this repo. All runtime binding fields defined in
`protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` § 1.1 apply.

```yaml
# ── Schema and identity ──
schema_version: "1"
adt_repository: butbutbutbutbutbut/adaptive-digital-team
adt_pin: d6c49342d50af1173cfe7a93b8771564a1b9b059

# ── Governance base (where rules are read from) ──
governance_base:
  branch: main
  sha: d6c49342d50af1173cfe7a93b8771564a1b9b059

# ── Authoritative fact source (what the current product truth is) ──
# Resolved live at every gate. The sha field here is a cache only;
# the live resolution in § 1.2 governs.
authoritative_fact_source:
  type: HUMAN_EXPLICIT
  evidence: "AUTHORIZATION_ID: ADT-REPOSITORY-AS-PROMPT-RUNTIME-BINDING-20260720-001"
  branch: main
  sha: d6c49342d50af1173cfe7a93b8771564a1b9b059

# ── Product repository binding
product_repository: butbutbutbutbutbut/he-weizhi-site

# ── Active candidate ──
active_candidate:
  branch: hermes/adt-main-push-ci-coverage-r1
  resolved_head: TBD  # will be set after commit
  status: GOVERNANCE_REPAIR
  task_id: ADT-MAIN-PUSH-CI-COVERAGE-R1
  authorization_id: ADT-MAIN-PUSH-CI-COVERAGE-20260720-001
  design_status: NOT_APPLICABLE
  implementation_status: NOT_AUTHORIZED
  next_gate: EXTERNAL_INDEPENDENT_WORKFLOW_AUDIT

# ── Comparison candidates ──
comparison_candidates: []

# ── Historical references ──
historical_references:
  - branch: pr-35
    sha: dc86f4e56024ad2905ff6be49798da5b02451b7f
    role: "Historical visual baseline (he-weizhi-site)"

# ── Invalidated candidates ──
invalidated_candidates: []

# ── Deployment plan ──
deployment_plan:
  version: v0.2
  status: ARCHITECTURE_CANDIDATE
  implementation: NOT_AUTHORIZED
  next_stage: PERSONA_MEMORY_BACKUP_AND_PROFILE_ISOLATION_PREFLIGHT

# ── Current gate ──
current_gate: EXTERNAL_INDEPENDENT_WORKFLOW_AUDIT

# ── Visual status ──
visual_status:
  active_candidate: DESIGN_CANDIDATE

# ── Decision register ──
decisions:
  D6:
    status: CLOSED
    result: EMPTY_PROFILE_PLUS_SKILL_ALLOWLIST
  B4:
    status: DESIGN_CANDIDATE
    design_document: docs/architecture/ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md
    implementation: NOT_AUTHORIZED
  D9:
    status: DESIGN_CANDIDATE
    design_document: docs/architecture/ADT_PERSONA_MEMORY_BACKUP_AND_CREDENTIAL_BOUNDARY_R1.md
    implementation: NOT_AUTHORIZED

# ── Authorized action and write scope ──
authorized_action: "ADT main push CI coverage repair R1"
authorized_write_scope:
  - .github/workflows/validate.yml
  - PROJECT_STATE.md

# ── Counter-objectives ──
counter_objectives:
  - "不得用更多长提示替代仓库状态"
  - "不得要求用户每轮重复 SHA、分支、门禁和禁止项"
  - "不得为每个微小状态创建新的治理分支"
  - "不得制造多个互相竞争的状态文件"
  - "不得仅凭 main、PR、提交时间或最近打开的 worktree 推断最新产品基线"
  - "不得让候选'已上传'等同于'已视觉接受'"
  - "不得让子代理完成等同于任务完成"
  - "不得让系统以'处理中'隐藏当前动作"
  - "不得修改任何绑定产品仓库"
  - "不得直接修改 main、Ready、Merge 或改写历史"
  - "不得上传或复制 state.db"
  - "不得读取真实记忆正文"
  - "不得创建 PAT"
  - "不得轮换真实凭据"
  - "不得创建四个私有仓库"
  - "不得创建 Hermes Profile"
  - "不得修改小禾 Profile"
  - "不得创建安鼎人格"
  - "不得实施备份"
  - "不得生成正式 age 密钥"
  - "不得接入飞书"
  - "不得实施 Gateway 或记忆桥"
  - "不得授予自动 Ready / Merge"
  - "不得建立第二套状态系统"
  - "不得把设计要求描述为已实施事实"

# ── Progress ──
progress:
  completed: 2
  total: 3
  display: "[######----] 66%"

# ── Human action ──
user_action_required: NO
system_next_step: "Await external independent workflow audit of main push CI coverage."
last_verified_at: "2026-07-19T20:49:25Z"

# ── Legacy fields (preserved for backward compatibility) ──
PHASE: PHASE_1
BOOTSTRAP_STATUS: ACCEPTED
CURRENT_MAIN_BASE_FOR_THIS_CANDIDATE: 0e9b39d57a4c5a8e306cf848dcbc6eb3f212e9f7
ACTIVE_PROJECT_BINDING: butbutbutbutbutbut/he-weizhi-site
PROJECT_BINDING_STATE_SHA: dc86f4e56024ad2905ff6be49798da5b02451b7f
PROJECT_BINDING_COUNT: 1
ACTIVE_CONTROL_LEASE: NONE
RUNTIME_ASSIGNMENTS: NONE
AUTOMATION: NONE
PROJECT_CLOSEOUT_PROTOCOL_SPECIFICATION: PRESENT
PROJECT_CLOSEOUT_RUNTIME: NOT_IMPLEMENTED
PERSISTENT_HOLDER_PROTOCOL: ADOPTED_GOVERNANCE_SPECIFICATION
PERSISTENT_HOLDER_PROTOCOL_AUDIT: ACCEPTED_WITH_RECORDED_LIMITS
PERSISTENT_HOLDER_RUNTIME: NOT_IMPLEMENTED
RUNTIME_ACTIVATION: NOT_AUTHORIZED
HERMES_R1: NOT_AUTHORIZED
REPOSITORY_STATE_SCOPE: DURABLE_GOVERNANCE_FACTS_ONLY
LIVE_PR_STATE_SOURCE: GITHUB_PR_METADATA
LIVE_AUTHORITY_STATE_SOURCE: EXPLICIT_HUMAN_AUTHORIZATION
LIVE_AUDIT_STATE_SOURCE: HEAD_BOUND_INDEPENDENT_AUDIT_RECEIPT
LIVE_GATE_STATE_SOURCE: PERSISTENT_HOLDER_STATE_REGISTRY
```
