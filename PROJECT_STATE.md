# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-DYNAMIC-GOVERNANCE-ROUTER-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/p1-dynamic-governance-router-r1
starting_base_sha: c2f992b9855581a95aa4eae52b7d079560217d10
authorized_write_scope:
  - AGENTS.md
  - PROJECT_STATE.md
  - README.md
  - 中文内容/README.md
  - protocols/DYNAMIC_GOVERNANCE_ROUTER.md
  - schemas/task-intake.schema.json
  - schemas/governance-plan.schema.json
  - scripts/route_task.py
  - tests/test_dynamic_governance_router.py
authority:
  holder: HE-WEIZHI
  maker: HERMES_TEMPORARY_MAKER
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: IMPLEMENTATION_IN_PROGRESS
implementation_status: IN_PROGRESS
phase: P1_AUTHORIZED
summary: >
  P1 Dynamic Governance Router R1 — deterministic governance plan generation
  from user input. Classifies task type, assesses risk, determines route,
  decomposes tasks into ordered execution units, and produces Candidate
  Control Packets. CANDIDATE status only; AUTHORIZED requires explicit
  Human Holder approval. P0 158 tests unchanged; 41 new P1 tests added.
  Authorization: ADT-P1-DYNAMIC-GOVERNANCE-ROUTER-20260721-001.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
