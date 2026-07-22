# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-METHODOLOGY-ROLE-BASELINE-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-methodology-role-baseline-r1
starting_base_sha: c2f992b9855581a95aa4eae52b7d079560217d10
authorized_write_scope:
  - METHODOLOGY.md
  - governance/ROLE_MODEL.md
  - governance/AUTHORITY_AND_FACTS.md
  - AGENTS.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  project_control: CURRENT_WINDOW
  task_holder: CURRENT_WINDOW
  maker: HERMES_TEMPORARY_MAKER_A
  checker: HERMES_TEMPORARY_CHECKER_B
current_gate: POST_CI_REVALIDATION_COMPLETE
implementation_status: AUDIT_PASSED
summary: >
  ADT Methodology and Role Baseline R1 — establishes the formal definition of
  ADT, the complete role topology (Human Holder → Project Control → Task Holder
  → Maker/Checker), the authority matrix, fact/action separation, and governance
  layering. Authorization: ADT-METHODOLOGY-ROLE-BASELINE-20260723-001.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
