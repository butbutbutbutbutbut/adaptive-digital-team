# Persistent Holder Control Plane

Status: `CANDIDATE_FOR_INDEPENDENT_REVIEW`

## Purpose

The Persistent Holder is the resident control-plane interface for the Adaptive Digital Team. It preserves auditable routing, authorization, task state, and recovery facts in the repository. The Holder is not a third Maker: Makers and Checkers are temporary task roles.

## Non-goals

This candidate does not implement a runtime, scheduler, automation, Agent creator, service, product code, or private Holder runtime state. PR10 is a read-only source candidate only; its branch must not be merged, cherry-picked, updated, closed, or deleted.

## Human–Holder interface

Human interacts with the Holder as the single control-plane interface. The Holder presents facts, conflicts, receipts, and decisions; it does not infer missing authority. Human-only decisions include Ready, Merge, branch deletion, final acceptance, and final visual or engineering acceptance.

## Holder responsibilities

The control plane consists of `PERSISTENT_CONTROL_PLANE`, `TASK_ROUTER`, `DEFAULT_INDEPENDENT_CHECKER`, and `STATE_REGISTRAR`. The Holder maintains the canonical Task State Card, validates repository facts, routes Dispatch Cards, records Progress Receipts, requests independent checks, and proposes state updates. It never directly Pushes. A state write requires explicit state-sync authorization.

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
NEXT_GATE:
STATUS: CANDIDATE_FOR_INDEPENDENT_REVIEW
```

## Task-scoped Publish Lease

`MAKER_SELF_PUBLISH_UNDER_TASK_SCOPED_LEASE` permits a Maker to prepare and, only when explicitly granted, publish its own task result. The Holder only routes publication; it does not Push directly. A Publish Lease inherits the parent repository, Base, scope, branch, Head binding, file limits, and gate. It cannot expand parent authorization or grant Ready, Merge, acceptance, or branch-deletion authority.

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
NEXT_GATE:
```

## Canonical Task State Card

Durable state belongs in the repository and is authoritative over runtime observations. Each card records `TASK_ID`, `AUTHORIZATION_ID`, `REPOSITORY`, `BASE_SHA`, `HEAD_SHA`, `BRANCH`, `PR`, `EXECUTOR`, `CHECKER`, `CURRENT_GATE`, `STATUS`, `LAST_VERIFIED_AT`, and `SUPERSEDES`. Local runtime state is a non-authoritative cache and is never committed as a substitute.

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

## Candidate gate

This document and every protocol status introduced by it are `CANDIDATE_FOR_INDEPENDENT_REVIEW`. It is not Active, Adopted, Accepted, Merged, or State Closed. The next gate is `INDEPENDENT_ADT_PERSISTENT_HOLDER_CONTROL_PLANE_AUDIT`.
