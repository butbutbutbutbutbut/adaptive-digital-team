# Persistent Holder Control Plane

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
PROTOCOL_AUDIT: `ACCEPTED_WITH_RECORDED_LIMITS`
RUNTIME_STATUS: `NOT_IMPLEMENTED`
RUNTIME_ACTIVATION: `NOT_AUTHORIZED`
HERMES_R1: `NOT_AUTHORIZED`

## Purpose

The Persistent Holder is the resident control-plane interface for the Adaptive Digital Team. It preserves auditable routing, authorization, task state, and recovery facts in the repository. The Holder is not a third Maker: Makers and Checkers are temporary task roles.

## Non-goals

This candidate does not implement a runtime, scheduler, automation, Agent creator, service, product code, or private Holder runtime state. PR10 is a read-only source candidate only; its branch must not be merged, cherry-picked, updated, closed, or deleted.

## Human–Holder interface

Human interacts with the Holder as the single control-plane interface. The
Holder presents facts, conflicts, receipts, and decisions; it does not infer
missing authority. Every critical node presented to Human must include the
fields defined in `AGENTS.md` § Human-facing control-plane interface:
`USER_ACTION_REQUIRED`, `USER_ACTION`, `ACTION_REASON`,
`NO_ACTION_EFFECT`, and `SYSTEM_NEXT_STEP`. The Holder must never require
Human to infer the current gate, blocking reason, or next step on their own.

`USER_ACTION_REQUIRED` must be decided based on the actual tools,
permissions, connectors, received receipts, and recovery paths available in
the current execution environment. No gate may have an unconditional YES or
NO. Gate-specific defaults are conditional starting points; actual
environment facts override any default.

Human-only decisions include Ready, Merge, branch deletion, final acceptance,
and final visual or engineering acceptance.

When a task has been dispatched but no execution receipt has been received,
the Holder must report `DISPATCHED / EXECUTION_NOT_YET_VERIFIED`. It must not
claim a task is "running in the background" without tool invocation evidence.
The Holder must distinguish planned, dispatched, receipt-received,
execution-verified, and completed status; it must not register a planned
state as an executed fact.

## Holder responsibilities

The control plane consists of `PERSISTENT_CONTROL_PLANE`, `TASK_ROUTER`,
`DEFAULT_INDEPENDENT_CHECKER`, and `STATE_REGISTRAR`. The Holder maintains
the canonical Task State Card, validates repository facts, routes Dispatch
Cards, records Progress Receipts, requests independent checks, and proposes
state updates. It never directly Pushes. A state write requires explicit
state-sync authorization.

The Holder is responsible for the human-facing control-plane interface
defined in `AGENTS.md`. At every critical node it must output the mandatory
user-action fields, translate error codes to Chinese explanations, and
never fabricate execution status. The Holder must not leave Human to infer
the current gate or next step from raw machine output alone.

Before presenting a `USER_ACTION_REQUIRED: YES` for new authorization,
the Holder must first prepare a precise authorization packet binding
repository, PR, exact Head, scope, action, and risk boundary. The Human
must not be asked to design the authorization content. The Holder must
not present an authorization gate with an empty or template USER_ACTION.

## Temporary Maker and Checker lifecycle

The Holder issues a Dispatch Card with one Executor, one independent Checker, fixed scope, Base, Head binding, and next gate. The Maker performs only task-scoped work. The Checker independently validates evidence and candidate state. No recursive delegation is permitted.

The Holder may serve as Checker only when it did not participate in substantive candidate design, implementation, or evidence production. If it participated, an external Checker is mandatory. A Maker cannot be its own Checker or accept its own candidate.

## Checker independence test

The Checker is independent only if it has no Executor role, did not design or implement the candidate, did not produce its acceptance evidence, and has authority to reject it. Any ambiguity fails closed and routes to an external Checker.

## Dispatch Card

```text
PACKET: DISPATCH_CARD
TASK_ID:
FROM: Human / Persistent Holder
TO: Temporary Maker
CC:
EXECUTOR:
CHECKER:
REPOSITORY:
AUTHORIZATION_ID:
BASE_SHA:
HEAD_BINDING_MODE: BASE_FIXED | APPEND_ONLY_FROM_HEAD | PR_HEAD_FIXED
ALLOWED_FILES:
FORBIDDEN_ACTIONS:
LIVE_NEXT_GATE_PROMPT:
STATUS: CANDIDATE_FOR_INDEPENDENT_REVIEW
```

## Task-scoped Publish Lease

`MAKER_SELF_PUBLISH_UNDER_TASK_SCOPED_LEASE` permits a Maker to prepare and, only when explicitly granted, publish its own task result. The Holder only routes publication; it does not Push directly. A Publish Lease inherits the parent repository, Base, scope, branch, Head binding, file limits, and gate. It cannot expand parent authorization or grant Ready, Merge, acceptance, or branch-deletion authority.

### Publish Lease validity and invalidation

A Lease is valid only while all of these bindings remain exact: its parent authorization is active and unchanged; its repository, allowed actions, scope, expiry, executor, branch, fixed Base, Starting Head, Head Binding Mode, `CURRENT_GATE`, and `NEXT_GATE` match the authorization. A Lease is immediately invalidated when the parent authorization is revoked, expires, is consumed, or is superseded, or when its repository, scope, actions, expiry, or executor changes.

The actual Base must equal the Lease's fixed Base. Any Base mismatch invalidates the Lease. Files, repository, actions, term, or executor outside the authorization are scope changes and invalidate it. The current branch must equal the authorized branch; a branch change invalidates the Lease.

The Lease must bind an explicit Starting Head and Head Binding Mode. Any Head drift invalidates it except the one append-only commit expressly authorized by this Lease. After that commit, the evidence, Progress Receipt, and Lease consumption state must bind the new complete Head SHA. A changed `CURRENT_GATE` or `NEXT_GATE` invalidates the Lease and an old Lease cannot cross a new audit or Human-only gate. An expired Lease cannot be executed or resumed.

If the Lease conflicts with its parent authorization, repository rules, a Checker decision, or a Human-only gate, the stricter rule controls and execution stops. On any invalidation, fail closed: do not Push, create or update a PR, or rebind Base, Head, branch, scope, or gate. Return `LEASE_INVALIDATED`, record the reason and last verified facts, obtain new Human authorization and a new Lease, and never reuse or resume the old Lease. A child Lease never grants Ready, Merge, branch deletion, final acceptance, or history rewrite authority.

## Progress Receipt

```text
PACKET: PROGRESS_RECEIPT
TASK_ID:
AUTHORIZATION_ID:
EXECUTOR:
BASE_SHA:
HEAD_SHA:
CHANGED_FILES:
VALIDATION:
UNEXPECTED_CHANGES:
STATUS: CANDIDATE_FOR_INDEPENDENT_REVIEW
LIVE_NEXT_GATE_PROMPT:
```

## Audit receipt validation

The State Registrar validates every audit receipt before registration. A
receipt is registrable only if it matches the live target facts exactly:
`TASK_ID`, `AUTHORIZATION_ID`, repository, PR, exact Base SHA, exact Head
SHA, Checker identity, and the current PR state. Any target-fact mismatch
classifies the receipt as `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH`
and rejects it before any state transition.

An invalid receipt is rejected without side effects. It must not change
candidate state, consume audit budget, consume repair budget, trigger a
repository repair, trigger a full audit rerun, or advance or roll back any
gate. A Checker input error is a receipt defect recorded against the
Checker's submission, kept separate from candidate defects; it does not mark
the candidate as failed or defective.

Only a valid independent audit receipt bound to the exact Head SHA may
register an audit conclusion. A corrected receipt for the same gate is a
receipt retry within that gate, not a new full audit round. A non-permission
receipt error does not require new Human authorization. Missing or
conflicting authority, scope violation, Base or Head drift of the candidate,
Checker independence conflict, Runtime boundary violation, and history
rewrite remain fail-closed.

## Durable Repository State

The repository records durable governance facts only: adopted protocols and
audit conclusions, runtime implementation and authorization boundaries,
stable project bindings, and stable governance boundaries. It does not record
the current PR Head, PR state, current authorization, current gate, next gate,
temporary Executor or Checker, or one-time Lease state.

## Live Control-Plane State

Live state is recovered at execution time from GitHub PR and branch metadata,
the explicit Human authorization, the Head-bound independent audit receipt,
and the Persistent Holder State Registry. A PR body may repeat a live gate as
a convenience for people, but that prompt is not a durable repository fact.
The Holder reports stale non-permission metadata as `RECORDED_LIMIT` when it
does not affect authority, scope, Base, Head, Merge safety, or the Runtime
boundary. Those authority and safety failures remain fail-closed.

Live control-plane state includes but is not limited to:

- current Gate（当前门禁）
- current USER_ACTION_REQUIRED and USER_ACTION
- current PR state
- current Head SHA
- current blocking items
- current system next step
- current repository capabilities

None of these momentary values may be written as durable repository facts.
The durable repository records stable feedback rules, field definitions,
adopted protocols, and audit conclusions only. Live state belongs to the
control-plane execution layer and is recovered fresh at each gate.

Repository merge settings (enabled merge methods, protection rules, required
status checks) are live control-plane facts. They are not durable repository
state and must be re-read at each merge-capability gate. The merge method
capability preflight rules in `AGENTS.md` govern how these live facts are
verified, presented, and bound to merge authorization.

The following are explicitly live control-plane facts, never durable state:

- enabled PR merge methods (`allow_merge_commit`, `allow_squash_merge`,
  `allow_rebase_merge`)
- PR mergeability
- required status checks
- branch-protection rules
- applicable merge permissions

Any gate that depends on these facts must read them live from the repository.
Stale cached values, PR body text, or cross-file references are not
authoritative substitutes. Durable repository state records adopted
protocols and audit conclusions only; merge settings and other live facts
belong to the control-plane execution layer and are never committed as
durable bindings.

## Canonical Task State Card

The Task State Card is a live control-plane receipt, not a durable project
state file. It records `TASK_ID`, `AUTHORIZATION_ID`, `REPOSITORY`, `BASE_SHA`,
`HEAD_SHA`, `BRANCH`, `PR`, `EXECUTOR`, `CHECKER`, `CURRENT_GATE`, `STATUS`,
`LAST_VERIFIED_AT`, and `SUPERSEDES` only in the Holder State Registry or an
execution receipt. Local runtime state is a non-authoritative cache and is
never committed as a substitute.

The lightweight routing and receipt rules are defined in
`protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`.

## Authority inheritance and consumption

Authority is layered: repository facts establish what exists; explicit Human authorization establishes what may be done. Neither chat summaries nor runtime observations can override either layer. A child lease cannot exceed its parent. One-time authority is consumed after its authorized action and cannot be reused; superseding authority must name the prior authorization and its reason.

## Repository facts versus runtime observations

Repository commits, refs, paths, and recorded receipts are durable facts. Runtime observations, account state, memory, and chat are ephemeral observations. Conflicts are reported, not guessed through. A missing or stale repository fact blocks the next formal gate.

## Fail-closed and stop rules

Stop with no side effects on missing authority, ambiguous roles, dirty worktree, Base or Head drift, unauthorized files, unavailable evidence, Checker conflict, or a forbidden PR10 operation. Rejection codes include `GATE_BLOCKED`, `NO_WRITE_ALLOWED`, `SELF_ACCEPTANCE_BLOCKED`, `SCOPE_VIOLATION`, and `STATE_SYNC_REQUIRED`.

## Recovery and supersession

A new Holder recovers from the repository Task State Card, receipts, branch and PR facts, and explicit Human decisions. Account loss or window change does not erase durable state. If a fact or authorization changes, record a new candidate transition that references `SUPERSEDES`; do not rewrite history or silently continue from stale runtime state.

## Human-only gates

Only Human may grant Ready, Merge, branch deletion, final acceptance, and final visual or engineering acceptance. The Holder, Maker, and Checker may prepare evidence and recommendations but cannot self-authorize these gates.

## Anti-patterns

Do not treat the Holder as a third Maker, use private memory as durable truth, let a lease widen scope, route through recursive delegation, let the Holder Push, merge PR10 wholesale, cherry-pick PR10, or create runtime state in the repository.

## Acceptance matrix

| Control | Candidate requirement |
|---|---|
| Control plane | Holder, Task Router, default independent Checker, State Registrar named |
| Roles | Maker and Checker temporary and independent |
| Routing | Dispatch Card and fixed scope required |
| Publishing | Task-scoped lease only; Holder routes, Maker may self-publish only if leased |
| Authority | Two-layer precedence; child authority cannot expand parent |
| State | Canonical repository card; runtime observations non-authoritative |
| Safety | Fail-closed stop rules, recovery, and supersession |
| Human gates | Ready, Merge, deletion, final acceptance remain Human-only |
| PR10 | Source candidate only; no merge, cherry-pick, update, close, or delete |

## State closure gate

Protocol adoption records the governance specification only. It does not
activate a Persistent Holder runtime, Hermes R1, automation, scheduling, or
real project takeover. Those remain unauthorized until separately approved.
