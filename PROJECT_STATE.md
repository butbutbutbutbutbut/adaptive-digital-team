# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-CANDIDATE-LIFECYCLE-ADOPTION-STATUS-R1
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-candidate-lifecycle-adoption-status-r1
starting_base_sha: ddaac86bc86220e3435dd0cc32c2093bc9f9356e
authorized_write_scope:
  - protocols/CANDIDATE_LIFECYCLE.md
  - governance/NORMATIVE_MAP.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  project_control: CURRENT_WINDOW
  task_holder: CURRENT_WINDOW
  maker: HERMES_MAKER
  checker: INDEPENDENT_CHECKER
current_gate: POST_CI_REVALIDATION_COMPLETE
implementation_status: AUDIT_PASSED
summary: >
  ADT Candidate Lifecycle Adoption Status R1 — promotes
  protocols/CANDIDATE_LIFECYCLE.md from CANDIDATE to ADOPTED status,
  updates governance/NORMATIVE_MAP.md accordingly.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
