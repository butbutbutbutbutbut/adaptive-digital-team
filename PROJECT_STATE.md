# Project State

This file stores stable facts for the current ADT governance candidate. Current
Base, Head, event SHA, remote refs, changed files, PR state, CI state, and the
candidate hash are resolved live and are not durable fields in this record.

```yaml
schema_version: "2"
task_id: ADT-RUNTIME-ADAPTER-CONTRACT-R1
authorization_id: ADT-RUNTIME-ADAPTER-CONTRACT-20260723-001
repository: butbutbutbutbutbut/adaptive-digital-team
branch: hermes/adt-runtime-adapter-contract-r1
starting_base_sha: 1f53b68ef9f0b5a9053d0a96d114d229942ff2d8
authorized_write_scope:
  - protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md
  - schemas/adapter-envelope.schema.json
  - schemas/adapter-output.schema.json
  - schemas/execution-authorization-binding.schema.json
  - scripts/validate_adapter.py
  - tests/test_runtime_adapter_contract.py
  - governance/NORMATIVE_MAP.md
  - AGENTS.md
  - PROJECT_STATE.md
authority:
  holder: HE-WEIZHI
  task_holder: HERMES_TEMPORARY_TASK_HOLDER-002
  maker: PENDING
  checker: PENDING_INDEPENDENT_CHECKER
current_gate: MAKER_IMPLEMENTATION
implementation_status: IMPLEMENTATION_COMPLETE
system_next_step: COMMIT_PUSH_DRAFT_PR
summary: >
  Implement ADT Runtime Adapter Contract R1. Architecture frozen at Phase A R2.
  Deliverables: protocol spec, 3 JSON schemas (adapter-envelope, adapter-output,
  execution-authorization-binding), validate_adapter.py, test suite,
  NORMATIVE_MAP + AGENTS.md updates.
  Four mandatory clauses from Phase A Acceptance govern AuthorizationBinding,
  per-action scope gating, two-phase independence evidence, and schema $ref
  integrity.
```

This file does not activate Runtime, Hermes R1, automatic scheduling,
product implementation, Ready, Merge, branch deletion, or final visual or
engineering acceptance.
