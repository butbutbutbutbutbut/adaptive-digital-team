# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-DYNAMIC-GOVERNANCE-ROUTER-REBASELINE-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-dynamic-governance-router-rebaseline-r1
starting_base_sha: 4dc0eb25173e92208b347bbfd23a6b101fa0b571
authorized_write_scope:
  - protocols/DYNAMIC_GOVERNANCE_ROUTER.md
  - schemas/task-intake.schema.json
  - schemas/governance-plan.schema.json
  - scripts/route_task.py
  - tests/test_dynamic_governance_router.py
  - AGENTS.md
  - governance/NORMATIVE_MAP.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_MAKER
  checker: PENDING_INDEPENDENT_CHECKER
authorization_id: ADT-DYNAMIC-GOVERNANCE-ROUTER-REBASELINE-20260723-001
current_gate: IMPLEMENTATION_IN_PROGRESS
implementation_status: IN_PROGRESS
source_reference:
  pr: 39
  head_sha: ecfe2fe22cbda64b1c5bf6057abe94f680387e8c
  usage: READ_ONLY_REFERENCE_ONLY
role_normalization:
  rule: TASK_HOLDER is normative; HOLDER accepted as input alias only
  enforced_in:
    - scripts/route_task.py
    - schemas/governance-plan.schema.json
    - protocols/DYNAMIC_GOVERNANCE_ROUTER.md
summary: >
  Dynamic Governance Router Rebaseline R1 — clean rebuild from current main
  (4dc0eb2). Ports the five Router core files from PR #39 with HOLDER →
  TASK_HOLDER role normalization. Excludes PR #39's README / 中文 README
  / AGENTS.md structural changes. Adds minimal normative reference to
  AGENTS.md R1 preservation contract and NORMATIVE_MAP.md entry.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
