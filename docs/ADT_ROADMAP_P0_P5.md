# ADT Roadmap P0–P5 R1

Status: `FORMAL_CANDIDATE`
Ratified: 2026-07-21
Authorization: ADT-ROADMAP-P0-P5-20260721-002

## Phase Boundary Principle

```text
PLANNED ≠ AUTHORIZED ≠ IMPLEMENTED ≠ OPERATIONAL
```

A phase listed as `PLANNED` is a design intent only. It carries zero
implementation authorization. Each phase requires a separate authorization
with exact repository, branch, base, and scope before any write may occur.

This roadmap is a reference document. It is not a grant of authority.

---

## P0 — Operational Baseline & Continuing Maintenance

**Status: `OPERATIONAL_BASELINE` / `CONTINUING_MAINTENANCE`**

### Objectives

- Maintain the existing ADT governance baseline as the single source of truth.
- Harden identity resolution, scope enforcement, and pre-write safety gates.
- Ensure every candidate passes deterministic machine validation before human review.
- Keep the governance repository the durable prompt; never allow chat to override facts.

### Dependencies

- None. P0 is the foundation.

### Deliverables (Completed)

| Item | Status |
|------|--------|
| Repository-as-prompt startup protocol | `OPERATIONAL` |
| Single-PR candidate topology (`ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN`) | `OPERATIONAL` |
| Runtime-derived identity (push, PR, local) | `OPERATIONAL` |
| Candidate fingerprint (SHA-256, deterministic) | `OPERATIONAL` |
| Durable state boundary (`PROJECT_STATE.md` + forbidden cache keys) | `OPERATIONAL` |
| Final realtime gate (pre-merge) | `OPERATIONAL` |
| CI gate (push + PR, continue-on-error zero) | `OPERATIONAL` |
| Audit receipt validation | `OPERATIONAL` |
| Lightweight repair and merge safety rules | `OPERATIONAL` |
| Adaptive counter-objective governance | `OPERATIONAL` |
| R1 preservation contract | `OPERATIONAL` |
| Pre-write Machine Gate | `OPERATIONAL` |
| `authorized_write_scope` runtime enforcement | `OPERATIONAL` |
| `LOCAL_DRAFT` / `FORMAL_CANDIDATE` / `AUDIT_ELIGIBLE` state distinction | `OPERATIONAL` |
| Conditional write authorization | `OPERATIONAL` |
| Detached HEAD fail-closed | `OPERATIONAL` |
| Stacked PR prohibition | `OPERATIONAL` |
| Scope violation detection with glob support | `OPERATIONAL` |
| Base drift detection | `OPERATIONAL` |
| Cross-platform absolute path detection | `OPERATIONAL` |

### Entry Gate

- Every agent session. P0 rules are always active for any candidate branch.

### Prohibitions

- Self-acceptance by Maker or Holder
- Automatic Ready, automatic Merge, automatic branch deletion
- Committing runtime fingerprints to candidate history
- Stacked PR topology (`base_ref != main`)
- Force-push, amend, rebase of submitted candidates
- `BLACKBOX_STATUS` — any unverified claim of completion or safety

### Model Tier

- Any model that can follow deterministic rules. Governance tasks are
  rule-application, not generation. Prefer the cheapest capable model.

### Human Holder Permissions

- Ready, Merge, branch deletion, final acceptance, visual/engineering
  acceptance, scope expansion, destructive external action — all
  `HUMAN_ONLY`.

---

## P1 — Dynamic Governance R1: Holder Runtime

**Status: `PLANNED` / `NOT_AUTHORIZED`**

### Objectives

- Implement a persistent Holder agent that survives across sessions.
- Holder becomes the resident control-plane interface and State Registrar.
- Holder verifies facts, prepares exact packets, routes work to Makers and
  Checkers, validates receipts, and presents executable Human actions.
- Holder does not self-implement, self-accept, or push without separate
  Maker appointment.

### Dependencies

- P0 `OPERATIONAL`. Holder relies on all identity, scope, fingerprint, and
  CI gate primitives.

### Deliverables (Planned)

- Persistent Holder runtime (process or daemon)
- Task classification and TASK_ID generation
- Dispatch Card generation with all required fields
- Maker designation and worktree isolation
- Checker designation with independence verification
- Progress Receipt aggregation
- Checker Receipt validation
- Holder Summary generation for Human gates
- Cross-session state durability (Hermes memory + session DB)
- All Publish Lease fields enforced at `NO` until separately authorized

### Entry Gate

- Separate Human authorization with exact scope. P1 implementation is a
  governance candidate subject to P0 rules.

### Prohibitions

- Holder MUST NOT modify product files, implement tasks, push, self-accept,
  mark Ready, Merge, or delete branches.
- Holder MUST NOT expand its own authorization beyond the parent
  Authorization.

### Model Tier

- Primary: capable reasoning model (GPT-5.x or equivalent). Holder is the
  Human-facing control plane; quality matters.

### Human Holder Permissions

- Authorization of P1 scope, acceptance of Holder runtime behavior, and
  all P0-level gates remain `HUMAN_ONLY`.

---

## P2 — Dynamic Governance R1: Maker Execution

**Status: `PLANNED` / `NOT_AUTHORIZED`**

### Objectives

- Implement the Maker role as an executable agent that receives Dispatch
  Cards, implements within exact scope, runs validation, commits locally,
  and returns Progress Receipts.
- Maker NEVER pushes, creates PRs, or self-accepts without a valid Publish
  Lease.
- Base drift detection: Maker stops and returns to Human if base has
  advanced since dispatch.

### Dependencies

- P1 `OPERATIONAL`. Maker receives Dispatch Cards from Holder.

### Deliverables (Planned)

- Maker agent with Dispatch Card ingestion
- Exact scope enforcement (only `FILES_IN_SCOPE`, only `ACTIONS_IN_SCOPE`)
- Base drift detection and fail-closed behavior
- Publish Lease enforcement (all fields `NO` in R0/R1 until explicitly
  authorized)
- Progress Receipt generation with all required fields
- Append-only commit discipline (no amend, no rebase, no force-push)

### Entry Gate

- Separate Human authorization with exact task scope. Maker implementation
  is itself a governance candidate subject to P0 rules.

### Prohibitions

- Maker MUST NOT push, create PRs, Ready, Merge, delete branches, or expand
  scope without explicit Publish Lease.
- Maker MUST NOT self-accept its own output.

### Model Tier

- Task-dependent. Code changes may use stronger coding models; documentation
  tasks may use lighter models. Holder designates per-task.

### Human Holder Permissions

- All Publish Lease fields (`PUSH_ALLOWED`, `DRAFT_PR_ALLOWED`,
  `READY_ALLOWED`, `MERGE_ALLOWED`, `BRANCH_DELETE_ALLOWED`) default to
  `NO` and require explicit Human authorization per task.

---

## P3 — Dynamic Governance R1: Independent Checker

**Status: `PLANNED` / `NOT_AUTHORIZED`**

### Objectives

- Implement an independent Checker agent that performs read-only
  verification of Maker output.
- Checker must not have designed or implemented the candidate, must not
  have produced its evidence, and can reject it.
- Independence ambiguity fails closed.

### Dependencies

- P2 `OPERATIONAL`. Checker audits Maker output.

### Deliverables (Planned)

- Checker agent with candidate ingestion (branch, PR, fingerprint)
- Independence verification (did not participate in implementation)
- Full audit: scope compliance, fingerprint match, validation pass, CI
  pass, no prohibited artifacts
- Checker Receipt generation with all required fields
- Rejection path with specific findings

### Entry Gate

- Separate Human authorization with exact audit scope. Checker
  implementation is itself a governance candidate subject to P0 rules.

### Prohibitions

- Checker MUST NOT modify candidate files, implement fixes, or become the
  Maker for the same task.
- Checker MUST NOT self-authorize a pass when independence is ambiguous.

### Model Tier

- Strong reasoning model. Audit quality directly affects governance safety.

### Human Holder Permissions

- Checker designation, Checker Receipt acceptance, and all P0-level gates
  remain `HUMAN_ONLY`.

---

## P4 — Design Baseline (Partial) / Implementation Not Authorized

**Status: `DESIGN_BASELINE_PARTIAL` / `IMPLEMENTATION_NOT_AUTHORIZED`**

### Objectives

- Define the design baseline for ADT features beyond Dynamic Governance R1:
  multi-agent debate, Gateway Debate Controller, Feishu integration, memory
  bridge, credential isolation, dual-profile architecture.
- P4 is a design document phase. No code, no runtime, no deployment.

### Dependencies

- P0 `OPERATIONAL`. P4 does not depend on P1–P3 for design work.
- P4 and Dynamic Governance R1 are **decoupled** — design can proceed
  independently of Holder/Maker/Checker runtime implementation.

### Deliverables (Planned)

- Multi-agent debate protocol design
- Gateway Debate Controller architecture
- Feishu integration design (dual bot, dual App ID/Secret)
- Memory bridge design (Feishu → encrypted audit archive → memory candidate
  → filtered de-identified snapshot → Xiaohe memory)
- Credential isolation design (separate GitHub credentials per profile)
- Dual-profile architecture (Xiaohe / Anding hard isolation)
- Nine isolation boundaries specification

### Entry Gate

- Separate Human authorization for design-phase work. No implementation
  authorization is granted by design-phase authorization.

### Prohibitions

- Implementation of any P4 feature without separate authorization.
- Committing credentials, secrets, tokens, or private material.
- Activating runtime, gateway, Feishu, or memory bridge without explicit
  activation authorization.

### Model Tier

- Design tasks: capable reasoning model. No code execution required.

### Human Holder Permissions

- Design acceptance, scope expansion for design work, and decision to
  authorize implementation separately.

---

## P5 — Future Architecture & Exploration

**Status: `PLANNED` / `NOT_AUTHORIZED`**

### Objectives

- Define exploration space for ADT capabilities beyond P4.
- P5 is a placeholder for capabilities that are currently out of scope but
  recognized as future directions.

### Dependencies

- P4 `DESIGN_BASELINE_COMPLETE`. P5 is decoupled from Dynamic Governance R1.

### Deliverables (Planned)

- Autonomous agent spawning and orchestration
- Multi-repository governance (cross-repo task routing)
- External service integration (notification, monitoring, logging)
- Human-in-the-loop UI/UX for governance decisions
- Training and fine-tuning of governance-specific models
- Public governance specification and community adoption

### Entry Gate

- P4 design baseline complete. P5 exploration requires separate Human
  authorization.

### Prohibitions

- Implementation without separate authorization.
- Premature commitment to any P5 direction before P4 design is complete.

### Model Tier

- Not applicable until authorized.

### Human Holder Permissions

- All P5 exploration and authorization decisions are `HUMAN_ONLY`.

---

## Phase Dependency Graph

```text
P0 (OPERATIONAL)
 ├── P1 (Holder Runtime) ──→ P2 (Maker) ──→ P3 (Checker)
 │    └── Dynamic Governance R1 ──────────────┘
 │
 └── P4 (Design Baseline) ──→ P5 (Future)
      └── Decoupled from Dynamic Governance R1
```

P1, P2, P3 form the **Dynamic Governance R1** chain. They must be
implemented in order.

P4 and P5 are **decoupled** from Dynamic Governance R1. Design work on
P4 can proceed independently of P1–P3 implementation.

---

## Authorization Protocol

1. This roadmap is a reference document. It does not authorize any
   implementation.
2. Each phase transition from `PLANNED` to `AUTHORIZED` requires:
   - Separate Human authorization with exact repository, branch, base,
     and scope.
   - Machine precheck (P0 rules) passing.
   - Conditional write authorization activated.
3. Phase completion from `AUTHORIZED` to `IMPLEMENTED` requires:
   - All P0 validation passing.
   - Independent Checker audit.
   - Human Holder acceptance.
4. Phase transition from `IMPLEMENTED` to `OPERATIONAL` requires:
   - Human Holder final acceptance.
   - Merge to main.
   - All prior phase dependencies satisfied.

---

## Governance

This roadmap is governed by the rules in `AGENTS.md` (Status:
`ADOPTED_GOVERNANCE_SPECIFICATION`). In any conflict between this roadmap
and `AGENTS.md`, `AGENTS.md` takes precedence.
