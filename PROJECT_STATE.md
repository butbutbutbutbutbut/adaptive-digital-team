# Project State

This file stores durable project state for ADT governance. Per-candidate
transient facts (branch, Base SHA, authorized write scope, authorization ID,
task ID) are now held in `.hermes/CANDIDATE_BINDING.json`. Live facts (Head,
main, CI state, remote refs, changed files, PR state) are resolved at every
gate and are never durable fields in this record.

```yaml
schema_version: "2"
repository: Kairos-zhi/adaptive-digital-team
authority:
  holder: Kairos
  maker: UNASSIGNED
  checker: UNASSIGNED
current_gate: NO_ACTIVE_CANDIDATE
implementation_status: NOT_AUTHORIZED
system_next_step: AWAIT_HUMAN_DIRECTIVE
summary: >
  As of 2026-08-09 the Human Holder finalized ADT positioning: ADT is not a
  product — it is a personal development milestone and a purely personal
  alignment-granularity tool, running as the base layer of the Holder's lab
  (Workshop / website / comics). Its real value is the governance discipline
  the Holder worked out for himself (holder / evidence trail / fail-closed /
  maker-checker separation), not the mechanisms themselves, which larger
  companies already cover; tools can be copied, discipline cannot — it differs
  by who follows it. The adopted ADT governance baseline includes the Runtime Adapter Contract,
  guarded scope-gated writes, resource allocation, transient candidate binding
  separation, and adaptive counter-objective controls. No active implementation
  candidate is represented in durable state; candidate-specific authority and
  execution facts belong in .hermes/CANDIDATE_BINDING.json.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
