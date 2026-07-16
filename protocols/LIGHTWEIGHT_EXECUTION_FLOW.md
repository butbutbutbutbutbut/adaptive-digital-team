# Lightweight Holder Execution Flow

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

## Purpose

This protocol reduces repeated state synchronization for small governance
tasks while preserving fail-closed protection for authority, scope, Base,
Head, Merge safety, Runtime boundaries, and history.

## R0 efficiency baseline

The previous real flow recorded approximately 111 minutes, 5 PR commits, 4
changed files, at least 6 Human interventions, and repeated waste from state
synchronization, Head rebinding, and full gate replay.

## R1 targets

- L0 documentation work completes within 30 minutes.
- Human normally intervenes twice: initial scope authorization and final
  Merge decision.
- Default path uses one Maker and one independent Checker.
- At most one incremental repair is allowed.
- A small repair receives incremental re-review rather than a full audit
  replay.
- Non-permission metadata defects are `RECORDED_LIMIT` and do not block Merge.
-越权、Base/Head drift、范围外文件、Runtime activation, and history rewrite
  remain fail-closed blockers.

## Risk levels

`L0_GOVERNANCE_DOCUMENTATION` covers bounded documentation-only changes with
no Runtime, dependency, Workflow, product, or destructive external action.
`L1_CONTROL_PLANE_CHANGE` covers changes to routing, authorization, state
registration, or audit behavior and requires an explicit independent audit.
`L2_RUNTIME_OR_EXTERNAL_ACTION` covers Runtime activation, permissions,
dependencies, Workflows, product changes, destructive actions, or Merge
execution; it is never treated as L0.

## Verifiable Progress Accounting

All L0, L1, and L2 tasks must maintain verifiable dual-layer progress per
`AGENTS.md` § Verifiable task progress.

### Equal-weight floor calculation

Progress uses equal-weight verification units. The percentage is
`floor(verified_units * 100 / total_bound_units)`. Ten-block bars use
`floor(percentage / 10)` filled blocks.

### UNKNOWN before binding

Before `PROGRESS_PLAN` and `CURRENT_STAGE_PLAN` are bound, both
`TASK_PROGRESS` and `CURRENT_STAGE_PROGRESS` are `UNKNOWN`.
The denominator must not be guessed.

### Freeze during wait

While waiting on GitHub, CI, Maker, Checker, or Human, progress stays
frozen. Elapsed time, token consumption, or background-execution claims
do not increase progress.

### Recalculation on scope or fact change

When Human expands scope, Base/Head facts are validly rebound, a new
authorized gate is added, or a valid audit requires fix + re-review,
progress is recalculated. The old and new percentages and the reason
must be output. Silent modification of the denominator or percentage
is forbidden.

Authority drift, unauthorized scope change, and state drift fail closed
and are not absorbed by progress recalculation.

### Incremental repair stage binding

An audit finding that requires fix + re-review is a blocker, not a
completion. The Audit stage denominator is frozen at its pre-audit value
and must not be retroactively modified.

Before any repair action is taken, the following must occur in order:

1. Human explicitly authorizes the repair scope.
2. A new repair / re-review stage is created.
3. A finite, ordered `CURRENT_STAGE_PLAN` is bound for the new stage.
4. If the repair adds a new authorized gate, `PROGRESS_PLAN` is extended
   and explained.
5. Before any file change, output:

   ```
   PROGRESS_RECALCULATED: <old>% -> <new>%
   RECALCULATION_REASON: VALID_AUDIT_REQUIRED_AUTHORIZED_REPAIR_AND_RE_REVIEW
   ```

Repair and incremental re-review units count toward progress only after
they are pre-bound in the new stage. They must not be appended to the
denominator after the repair is complete.

Forbidden:

- appending units to a denominator after repair completion
- retroactively modifying an old Audit stage denominator
- adding task gates without Human authorization
- using recalculation to absorb authority drift, scope drift, or state
  drift

### Audit rejection and blocker routing

Audit rejection:

- does not count as completion
- does not automatically change the original task denominator
- freezes the original task progress at its pre-audit value
- routes to the `HUMAN_REPAIR_AUTHORIZATION` gate as a blocker

After Human authorizes repair, the new repair / re-review stage is a
legitimate `PROGRESS_PLAN` extension. The extension must be registered
and the recalculation output before any repair file changes.

### State drift

State drift fails closed. Neither task nor stage progress advances.

### No change to existing gates

Verifiable progress accounting is informational. It does not alter any
existing Human-only, fail-closed, Ready, Merge, branch deletion, or
final-acceptance gate.

## L0 standard flow

```text
Human initial scope authorization
    -> Holder pre-dispatch verification
    -> Maker
    -> Independent Checker
    -> Human Merge Decision
```

The Holder performs one pre-dispatch check of Base, allowed paths, risk,
Checker independence, and acceptance conditions. The Maker makes one bounded
candidate. The Checker performs one independent review. Human decides the
final high-risk gate. A Maker cannot self-accept and the Holder cannot Push
directly.

## Incremental repair

At most one incremental repair may follow the initial Checker result. The
repair must remain within the original scope and receive an incremental
re-review of the changed evidence. It must not restart the full audit or
create a new commit loop for a non-blocking metadata limit. A second repair,
scope expansion, or authority change requires new Human authorization.

## Blockers and recorded limits

`BLOCKING` applies to missing or conflicting authority, Checker conflict,
Base or Head drift, unauthorized files, scope or repository change, Runtime
activation, dependency or Workflow addition, destructive action, unsafe
Merge condition, merge capability unknown, or history rewrite. Stop and fail
closed.

`RECORDED_LIMIT` applies to stale or imperfect non-permission metadata that
does not change authority, scope, Base, Head, Merge safety, or Runtime
boundaries. Record it in the receipt and continue only if the Checker and
Human gate accept the limit.

## Audit receipt validation

Before an audit receipt is registered, the Holder must verify that the
receipt binds the exact target facts: `TASK_ID`, `AUTHORIZATION_ID`,
repository, PR, exact Base SHA, exact Head SHA, Checker identity, and the
current PR state. If any target fact does not match, the receipt is
classified `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH` and rejected
before any state transition.

An invalid audit receipt must not change candidate state, consume the audit
budget, consume the repair budget, trigger a repository repair, trigger a
full audit rerun, or advance or roll back any gate. A Checker input error is
a receipt defect, not a candidate defect; the candidate remains in its
current state and is not treated as failed.

Only a valid independent receipt bound to the exact Head SHA may register an
audit conclusion. A corrected receipt for the same gate is a receipt retry,
not a new full audit round. Non-permission receipt errors do not require new
Human authorization. Missing or conflicting authority, scope violation, Base
or Head drift on the candidate itself, Checker conflict, Runtime activation,
and history rewrite remain fail-closed blockers.

## Holder routing contract

Before dispatch, the Holder verifies Base, scope, risk, independent Checker,
and acceptance conditions once and emits a Dispatch Card. An authorization
addendum contains only changed fields; it does not repeat the entire parent
authorization. The Holder routes publication under the existing task-scoped
lease and never widens it.

## Human interaction budget

Human normally handles only initial scope and final high-risk gates. Human
remains the sole authority for Ready, final merge method selection (per
`AGENTS.md` merge capability preflight), Merge, branch deletion, final visual
or engineering acceptance, final acceptance, Runtime activation, and
destructive external action.

## Non-L0 exclusions

Runtime, permission changes, dependencies, Workflows, scripts, tests,
product code, destructive external actions, and history rewrites are not L0
work. They require their own authorization and risk treatment. Hermes R1 and
automatic scheduling remain `NOT_AUTHORIZED`.

## Merge capability preflight

The merge method capability preflight defined in `AGENTS.md` applies at
every final Human merge gate.

### Pre-gate verification

Before presenting merge options or requesting Human merge authorization,
live repository merge settings must be verified. `MERGE_CAPABILITY_UNKNOWN`
blocks the gate and fails closed.

### MERGE_METHOD_CAPABILITY_MISMATCH (no-side-effect recovery)

`MERGE_METHOD_CAPABILITY_MISMATCH` is valid only when repository identity,
PR identity, Base SHA, Head SHA, scope, candidate files and content, PR
state, mergeability, and the independent audit conclusion are all unchanged.
When triggered:

- candidate state does not change
- valid audit conclusion remains valid
- audit budget is not consumed
- repair budget is not consumed
- repository repair is not triggered
- full audit rerun is not triggered
- candidate does not enter a failure gate
- routes to `HUMAN_MERGE_METHOD_REAUTHORIZATION` only

The new authorization replaces only the exact merge method; it must not
expand any other permission, scope, or gate.

### Drift (fail-closed)

The following are genuine drift and must not use lightweight re-authorization:
repository change, PR identity change, Base drift, Head drift, scope change,
candidate file or content change, PR state change, mergeability change,
permission change, required-check change, branch-protection change. Any drift
returns to the appropriate fact-verification, audit, or Human gate. No silent
rebinding of old authorization is permitted.

## Adoption gate

This protocol is an `ADOPTED_GOVERNANCE_SPECIFICATION` recorded as a durable
repository governance fact. Adoption records routing, receipt, and validation
rules only; it does not activate a Runtime, Hermes R1, automatic scheduling,
or any scheduler, and it grants no execution authority by itself.

## Human-facing interface integration

Every gate defined in this protocol must include the human-facing fields
specified in `AGENTS.md` § Human-facing control-plane interface. All
`USER_ACTION_REQUIRED` values below are conditional defaults. Actual
tool availability, received evidence, permissions, and recovery paths in
the current execution environment override any default.

### Gate-specific user action requirements

**Dispatch（分派）**

- Normal default: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- Override to YES when: the current system has no Maker scheduling
  capability; the user must manually deliver the exact Dispatch Card to
  a Maker. The user action must specify the recipient and the exact Packet.
- Required evidence for NO: the Holder has completed a real dispatch and
  has confirmation (tool result, connector ACK, or receipt).
- Without confirmation: status is `DISPATCHED / EXECUTION_NOT_YET_VERIFIED`;
  do not claim the Maker has started.

**Progress Receipt（进度回执）**

- Normal default: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- Override to YES when: the system cannot directly invoke a Checker; the
  user must manually create an independent Checker session and forward the
  exact Audit Request with target facts bound.
- Required evidence for NO: the system has directly invoked a Checker or
  has confirmation the Checker received the audit target.
- Without confirmation: do not claim "Checker begins". Status is
  `DISPATCHED / EXECUTION_NOT_YET_VERIFIED` for the audit step.
- The Progress Receipt proves only that the Maker submitted a receipt.
  It does not prove the Checker has started.

**Target-Fact Validation（目标事实核验）**

Two distinct mismatch paths:

A. `RECEIPT_METADATA_ERROR / TARGET_TRANSCRIPTION_ERROR` — e.g. wrong PR
   number, mis-transcribed Base/Head, stale non-permission field, but the
   real GitHub candidate has no authority, scope, or content drift.

   - `USER_ACTION_REQUIRED: NO`.
   - Output `INVALID_AUDIT_RECEIPT` with Chinese explanation.
   - Holder corrects the target within the same gate.
   - Does not consume audit budget, repair budget, or new Human
     authorization. Does not mark candidate as failed.

B. `REAL_STATE_OR_AUTHORITY_DRIFT` — real repository, PR, Base, Head,
   scope, candidate content, authority, or high-risk condition change.

   - `STATE_DRIFT / FAIL_CLOSED`.
   - `USER_ACTION_REQUIRED: YES` only when Human rebinding is genuinely
     required. Must provide a precise rebind / reauthorization request
     binding the changed facts.
   - `USER_ACTION_REQUIRED: NO` when the system can diagnose without
     Human action (e.g. transient mismatch that resolves on re-read).

**Audit Receipt（审计回执）**

- Normal default: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- Valid audit registers conclusion within the current gate.

**Blocking Finding（阻塞发现）**

- Normal default: `USER_ACTION_REQUIRED: YES` if repair budget remains.
  The user authorizes one incremental repair at the exact scope.
- Override to NO when: the system can autonomously prepare the repair
  authorization and the user has pre-authorized the repair scope.

**Repair Budget Exhausted（修复预算耗尽）**

Two sequential stages. Do not output `USER_ACTION_REQUIRED: NO` and
`NEW_HUMAN_AUTHORIZATION_REQUIRED` simultaneously.

Stage A — Authorization Request Preparation:
  - `USER_ACTION_REQUIRED: NO`.
  - `CURRENT_GATE`: not `NEW_HUMAN_AUTHORIZATION_REQUIRED`.
  - `SYSTEM_NEXT_STEP`: Holder prepares a precise new authorization
    packet binding repository, PR, exact Head, scope, action, and risk
    boundary.

Stage B — New Human Authorization Required:
  - `USER_ACTION_REQUIRED: YES`.
  - `USER_ACTION`: the exact authorization packet prepared in Stage A.
    The user must not be asked to design the authorization content.
  - `CURRENT_GATE`: `NEW_HUMAN_AUTHORIZATION_REQUIRED`.

**Incremental Repair（增量修复）**

- Normal default: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- Maker executes within authorized scope.

**Ready Decision（就绪决定）**

- `USER_ACTION_REQUIRED: YES`. Human-only gate.
- Authorization must bind repository, PR, exact Head SHA, and scope.

**Merge Capability Preflight（合并能力预检）**

- Normal default: `USER_ACTION_REQUIRED: NO` when capability verified.
- `MERGE_METHOD_CAPABILITY_MISMATCH`: `USER_ACTION_REQUIRED: YES`.
  Human selects a different enabled method.
- `CAPABILITY_UNKNOWN` — classify cause first:
  - Transient API failure / system can retry: `USER_ACTION_REQUIRED: NO`.
    `SYSTEM_NEXT_STEP` is retry or further read-only verification.
  - Permission or access gap Human can resolve: `USER_ACTION_REQUIRED: YES`.
    Provide precise permission authorization or external verification action.
  - No user-remediable path: `USER_ACTION_REQUIRED: NO`. `FAIL_CLOSED`.
    State explicitly that user action cannot resolve this block.
  - Cause not yet known: `USER_ACTION_REQUIRED: NO`. System diagnoses
    first. Do not present a vague action to the user.

**Merge Decision（合并决定）**

- `USER_ACTION_REQUIRED: YES`. Human-only.
- Must bind repository, PR, exact Head SHA, exact merge method, and
  branch deletion decision.

**Merge Result（合并结果）**

- Success: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- Failure: system must classify the failure before requesting user action:
  - method capability mismatch
  - state drift
  - permission failure
  - required-check failure
  - transient API failure
  - unknown failure
- `USER_ACTION_REQUIRED: NO` when the system can continue diagnosis or
  safely retry without new authorization.
- `USER_ACTION_REQUIRED: YES` only when a precise new authorization,
  permission change, or external manual action is required. `USER_ACTION`
  must be directly executable — never "Human diagnosis."

**Branch Deletion（分支删除）**

- If the final Merge authorization already bound a branch deletion
  decision (DELETE / RETAIN) and that decision has not changed, the
  merge result executes or retains the authorized decision. Do not
  open a separate Human YES gate.
- If no prior binding exists, or Human requests a change to the bound
  decision: re-verify live state, obtain precise new authorization
  binding the changed decision. `USER_ACTION_REQUIRED: YES` only in
  this case.

**Task Completion（任务完成）**

- Normal default: `USER_ACTION_REQUIRED: NO`, `USER_ACTION: NONE`.
- System records completion; no further action.

### No-action default

When `USER_ACTION_REQUIRED: NO`, `USER_ACTION` must be exactly `NONE`.
Never leave `USER_ACTION` empty, implied, or to-be-determined. The field
is mandatory at every critical node.
