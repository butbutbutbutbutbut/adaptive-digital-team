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
every final Human merge gate. Before presenting merge options or requesting
Human merge authorization, live repository merge settings must be verified.
`MERGE_CAPABILITY_UNKNOWN` blocks the gate. `MERGE_METHOD_CAPABILITY_MISMATCH`
does not consume audit or repair budget and routes to
`HUMAN_MERGE_METHOD_REAUTHORIZATION`. Base, Head, scope, PR state, or
mergeability drift remains fail-closed.

## Adoption gate

This protocol is an `ADOPTED_GOVERNANCE_SPECIFICATION` recorded as a durable
repository governance fact. Adoption records routing, receipt, and validation
rules only; it does not activate a Runtime, Hermes R1, automatic scheduling,
or any scheduler, and it grants no execution authority by itself.
