# Lightweight Holder Execution Flow

Status: `CANDIDATE_FOR_INDEPENDENT_REVIEW`

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
Merge condition, or history rewrite. Stop and fail closed.

`RECORDED_LIMIT` applies to stale or imperfect non-permission metadata that
does not change authority, scope, Base, Head, Merge safety, or Runtime
boundaries. Record it in the receipt and continue only if the Checker and
Human gate accept the limit.

## Holder routing contract

Before dispatch, the Holder verifies Base, scope, risk, independent Checker,
and acceptance conditions once and emits a Dispatch Card. An authorization
addendum contains only changed fields; it does not repeat the entire parent
authorization. The Holder routes publication under the existing task-scoped
lease and never widens it.

## Human interaction budget

Human normally handles only initial scope and final high-risk gates. Human
remains the sole authority for Ready, Merge, branch deletion, final visual or
engineering acceptance, final acceptance, Runtime activation, and destructive
external action.

## Non-L0 exclusions

Runtime, permission changes, dependencies, Workflows, scripts, tests,
product code, destructive external actions, and history rewrites are not L0
work. They require their own authorization and risk treatment. Hermes R1 and
automatic scheduling remain `NOT_AUTHORIZED`.

## Candidate gate

This protocol is `CANDIDATE_FOR_INDEPENDENT_REVIEW`. The next review is an
independent lightweight execution-flow audit; this document does not activate
Runtime or create a scheduler.
