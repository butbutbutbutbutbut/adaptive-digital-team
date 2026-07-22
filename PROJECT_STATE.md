# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-PROTOCOL-DEDUP-NORMATIVE-MAP-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-protocol-dedup-normative-map-r1
starting_base_sha: acde00f94644ea5d0f7a19d6b44a05b450b14a6b
authorized_write_scope:
  - protocols/CANDIDATE_LIFECYCLE.md
  - governance/NORMATIVE_MAP.md
  - AGENTS.md
  - protocols/LIGHTWEIGHT_EXECUTION_FLOW.md
  - protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  project_control: CURRENT_WINDOW
  task_holder: CURRENT_WINDOW
  maker: PENDING
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: MAKER_EXECUTION
implementation_status: IN_PROGRESS
summary: >
  ADT Protocol Dedup Normative Map R1 — establishes protocols/CANDIDATE_LIFECYCLE.md
  as the single normative source for candidate lifecycle rules, creates
  governance/NORMATIVE_MAP.md for concept-to-source mapping, deduplicates
  AGENTS.md, LIGHTWEIGHT_EXECUTION_FLOW.md, and PERSISTENT_HOLDER_CONTROL_PLANE.md.
  Authorization: ADT-PROTOCOL-DEDUP-NORMATIVE-MAP-20260723-001.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
