# Project State

This file is the single runtime binding record for the ADT organization
repository. It serves as the authoritative `.adt/project-binding.yaml`
equivalent for this repo. All runtime binding fields defined in
`protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md` § 1.1 apply.

```yaml
# ── Schema and identity ──
schema_version: "1"
adt_repository: butbutbutbutbutbut/adaptive-digital-team
adt_pin: 8d343f26dfc9f29422b448705bf85e6f0be37362

# ── Governance base (where rules are read from) ──
governance_base:
  branch: main
  sha: 8d343f26dfc9f29422b448705bf85e6f0be37362

# ── Authoritative fact source (what the current product truth is) ──
# Resolved live at every gate. The sha field here is a cache only;
# the live resolution in § 1.2 governs.
authoritative_fact_source:
  type: HUMAN_EXPLICIT
  evidence: "AUTHORIZATION_ID: ADT-REPOSITORY-AS-PROMPT-RUNTIME-BINDING-20260720-001"
  branch: main
  sha: 8d343f26dfc9f29422b448705bf85e6f0be37362

# ── Product repository binding (the project this ADT repo governs) ──
product_repository: butbutbutbutbutbut/he-weizhi-site

# ── Active candidate ──
active_candidate:
  branch: NONE
  resolved_head: NONE
  status: NONE

# ── Comparison candidates ──
comparison_candidates: []

# ── Historical references ──
historical_references:
  - branch: pr-35
    sha: dc86f4e56024ad2905ff6be49798da5b02451b7f
    role: "Historical visual baseline (he-weizhi-site)"

# ── Invalidated candidates ──
invalidated_candidates: []

# ── Current gate ──
current_gate: ADT_REPOSITORY_AS_PROMPT_IMPLEMENTATION

# ── Visual status ──
visual_status:
  active_candidate: NONE

# ── Authorized action and write scope ──
authorized_action: "ADT repository-as-prompt runtime binding repair"
authorized_write_scope:
  - AGENTS.md
  - PROJECT_STATE.md
  - BOOTSTRAP.md
  - protocols/*.md
  - scripts/*.py
  - tests/*.py
  - .github/workflows/*.yml

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

# ── Progress ──
progress:
  completed: 7
  total: 12
  display: "[######----] 58%"

# ── Human action ──
user_action_required: NO
system_next_step: "Create validator, tests, CI; run validation; push branch; create Draft PR"
last_verified_at: "2026-07-20T01:30:00Z"

# ── Legacy fields (preserved for backward compatibility) ──
PHASE: PHASE_1
BOOTSTRAP_STATUS: ACCEPTED
CURRENT_MAIN_BASE_FOR_THIS_CANDIDATE: 8d343f26dfc9f29422b448705bf85e6f0be37362
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
