# Lightweight Holder Execution Flow

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

> This document defines execution flow and routing. For the complete Candidate
> Lifecycle specification (identity, fingerprint, scope, state machine, CI,
> audit, pre-merge gate), see `protocols/CANDIDATE_LIFECYCLE.md` — the single
> normative source.

## Purpose

This protocol provides a bounded execution route while preserving exact authority,
candidate identity, independent audit, and Human-only Ready and Merge gates. It
does not authorize runtime activation, automatic scheduling, automatic merge,
or product-repository write.

## Risk routing

- `L0_GOVERNANCE_DOCUMENTATION`: bounded documentation-only work.
- `L1_CONTROL_PLANE_CHANGE`: routing, identity, validation, authorization,
  audit, workflow, script, or state behavior; requires independent governance audit.
- `L2_RUNTIME_OR_EXTERNAL_ACTION`: runtime, permissions, dependency, destructive
  action, or product change; requires separate explicit authority.

This Candidate Lifecycle R1 task is L1.

## Delta-only operation

The repository carries stable context. Chat carries only task delta and new
evidence. A full startup is required for a new task or window, binding change,
gate change, fact conflict, or new candidate receipt. When facts conflict, enter
`FACT_SOURCE_REBIND` and block write.

## One-task execution topology

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Single formal candidate topology

```text
ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN
```

- Every formal candidate branch starts from verified `origin/main`.
- Every formal candidate PR directly targets `main`.
- `base_ref != main` is `STACKED_PR_PROHIBITED`.
- Pull-request validation runs regardless of requested Base, so stacked candidates fail visibly.
- A defect discovered before audit is fixed by an append-only commit on the same branch and the new Head is re-audited.
- A defect discovered after merge starts a new task from the latest main.
- A child PR is never the repair mechanism for an unmerged parent and is never retargeted after parent squash merge.

## Maker path

1. Verify exact Base, branch, repository, authority, and scope.
2. Machine precheck must pass before any write (see `protocols/CANDIDATE_LIFECYCLE.md` § Pre-write execution gate).
3. Create the one authorized candidate branch from exact main.
4. Modify only exact authorized paths.
5. Stage explicit paths; wildcard staging is prohibited.
6. Run static validation and the complete regression suite.
7. Verify actual changed files are within authorized scope (see `protocols/CANDIDATE_LIFECYCLE.md` § Scope enforcement).
8. Push the same branch and create one Draft PR targeting main.
9. Keep Draft; do not Ready or Merge.
10. Obtain push and pull-request CI attached to the source Head.
11. Route to an independent Checker.

A Maker cannot create a subtask, stacked PR, self-audit, or self-acceptance
path to complete the same candidate.

## Runtime candidate identity

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Runtime-derived identity

Identity is derived at execution time from `GITHUB_REF` (push), pull-request
event Head/Base (PR), or `git rev-parse HEAD` + `origin/*` (local). The full
algorithm with push, PR, and local modes is defined in
`protocols/CANDIDATE_LIFECYCLE.md`.

## Candidate fingerprint

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Candidate fingerprint

The fingerprint is SHA-256 over canonical JSON of `{repository, base_ref,
base_sha, head_ref, head_sha, sorted(changed_files)}`. Full description and
the canonical Python implementation are in `protocols/CANDIDATE_LIFECYCLE.md`.

## Receipt and authorization binding

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Receipt and authorization binding

## PRE_MERGE_REALTIME_GATE

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Final realtime gate (PRE_MERGE_REALTIME_GATE)

## CI evidence gate

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § CI gate

## Incremental repair

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Lightweight repair and merge safety

## Audit receipt validation

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Audit receipt validation

## Progress accounting

> **Normative principle**: Numeric progress requires a finite pre-bound plan.
> Only independently verified units or registered Human decisions count.
> Planned, dispatched, receipt-received, waiting, elapsed time, token use, and
> unverified background claims do not count. Recalculation must show old
> percentage, new percentage, and exact reason. Progress never substitutes for
> audit, Ready, Merge, or acceptance.
>
> See also `protocols/CANDIDATE_LIFECYCLE.md` § Progress accounting.

## Human interaction and merge

Human normally provides initial exact scope and final high-risk decisions.
Ready, merge method, Merge, branch deletion, final acceptance, runtime
activation, and destructive external action remain Human-only. Merge settings,
mergeability, checks, permissions, and protection are live facts and are
re-read immediately before authorization and execution.

## Candidate state machine

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Candidate state machine

## Pre-write execution gate

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Pre-write execution gate

## Scope enforcement

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Scope enforcement

## Remote candidate history immutability

> **Normative source**: `protocols/CANDIDATE_LIFECYCLE.md` § Remote candidate history immutability

## Compatibility preservation

This R1 flow is an additive narrowing of candidate topology, not permission to
remove prior gates. Dispatch Cards, Progress Receipts, valid-vs-invalid audit
receipt classification, finite repair handling, Human-action clarity, live
merge-capability preflight, reviewed revert rollback, counter-objective checks,
and remote history immutability remain required wherever their conditions apply.
The existing baseline regression cases remain part of the complete suite; the
single-PR, fingerprint, realtime-gate, and history-immutability cases extend
that suite.
