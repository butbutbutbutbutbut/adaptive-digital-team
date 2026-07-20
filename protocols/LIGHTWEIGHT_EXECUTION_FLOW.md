# Lightweight Holder Execution Flow

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

## Purpose

This protocol provides a bounded execution route while preserving exact authority, candidate identity, independent audit, and Human-only Ready and Merge gates. It does not authorize runtime activation, automatic scheduling, automatic merge, or product-repository write.

## Risk routing

- `L0_GOVERNANCE_DOCUMENTATION`: bounded documentation-only work.
- `L1_CONTROL_PLANE_CHANGE`: routing, identity, validation, authorization, audit, workflow, script, or state behavior; requires independent governance audit.
- `L2_RUNTIME_OR_EXTERNAL_ACTION`: runtime, permissions, dependency, destructive action, or product change; requires separate explicit authority.

This Candidate Lifecycle R1 task is L1.

## Delta-only operation

The repository carries stable context. Chat carries only task delta and new evidence. A full startup is required for a new task or window, binding change, gate change, fact conflict, or new candidate receipt. When facts conflict, enter `FACT_SOURCE_REBIND` and block write.

## One-task execution topology

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
2. Machine precheck must pass before any write (see Candidate state machine below).
3. Create the one authorized candidate branch from exact main.
4. Modify only exact authorized paths.
5. Stage explicit paths; wildcard staging is prohibited.
6. Run static validation and the complete regression suite.
7. Verify actual changed files are within authorized scope (scope enforcement).
8. Push the same branch and create one Draft PR targeting main.
9. Keep Draft; do not Ready or Merge.
10. Obtain push and pull-request CI attached to the source Head.
11. Route to an independent Checker.

A Maker cannot create a subtask, stacked PR, self-audit, or self-acceptance path to complete the same candidate.

## Runtime candidate identity

Identity is derived at execution time:

### Push events

```text
push_branch := parse(GITHUB_REF)
accepted format := refs/heads/<branch>
required equality := git HEAD = GITHUB_SHA = origin/<push_branch>
```

Missing, empty, tag, notes, or pull-merge refs are `HARD_STOP`. No `PROJECT_STATE.md` branch fallback is allowed.

### Pull-request events

```text
head_ref, head_sha := pull_request.head
base_ref, base_sha := pull_request.base
required base_ref := main
required source equality := head_sha = origin/<head_ref> = checked-out HEAD
```

The synthetic `refs/pull/*/merge` identity is excluded.

### Local and final gate

```text
current Head := git rev-parse HEAD
current main := origin/main
candidate remote := origin/<candidate_branch>
changed files := sorted(git diff base...head)
```

## Candidate fingerprint

`CANDIDATE_FINGERPRINT` is SHA-256 over canonical normalized JSON containing:

- repository;
- base ref;
- Base SHA;
- head ref;
- Head SHA;
- sorted changed files.

Output includes the complete `FINGERPRINT_FIELDS` and `CANDIDATE_FINGERPRINT`. The hash is not written into the commit it identifies.

## Receipt and authorization binding

The audit receipt and Holder authorizations for Ready and Merge must bind the same fingerprint.

Any repository, Base SHA, Head SHA, branch, or changed-file drift yields:

```text
AUDIT_BINDING: INVALID
READY_AUTHORIZATION: INVALID
MERGE_AUTHORIZATION: INVALID
```

Old evidence cannot cross a Head change, repair commit, Base update, branch change, file change, or repository change. A new Head requires new runtime fields, new fingerprint, and new independent audit.

## PRE_MERGE_REALTIME_GATE

Input: the expected fingerprint from the valid independent audit.

Freshly resolve:

- repository;
- Base ref and `origin/main` SHA;
- candidate branch and `origin/<candidate_branch>` SHA;
- current Head;
- sorted changed files;
- clean workspace;
- exact authorized scope.

Required result:

```text
base_ref == main
base_sha unchanged
head_sha unchanged
changed_files unchanged
runtime fingerprint == expected fingerprint
workspace clean
sorted(changed_files) == sorted(authorized_write_scope)
```

Any mismatch is `HARD_STOP / FINGERPRINT_MISMATCH`. No Ready or Merge decision may continue on old evidence.

## CI evidence gate

The Holder verifies, from live GitHub facts:

- push workflow run exists for current source Head and succeeded;
- pull-request workflow run exists for current source Head and succeeded;
- static validator ran;
- complete tests ran with at least the bound minimum and zero failures;
- live CI validator ran;
- no required job or step was skipped;
- no soft-fail path exists;
- `continue-on-error = 0`.

Waiting on CI is not candidate failure and does not advance progress. CI success is evidence only, not acceptance.

## Incremental repair

A valid audit finding may be repaired only after authority is verified. The repair remains on the original branch and PR, inside scope. The new Head invalidates the previous fingerprint and audit. The Checker reviews the new Head and new fingerprint. A second PR is prohibited for the same unmerged candidate.

## Audit receipt validation

Before registration, verify task, authorization, repository, PR, Base ref/SHA, head ref/SHA, changed files, Checker independence, PR state, and fingerprint. A target transcription mismatch is `INVALID_AUDIT_RECEIPT`, not automatically `CANDIDATE_FAILURE`, and consumes no audit or repair budget. Real authority, scope, Base, Head, branch, repository, file, runtime, or history drift fails closed.

## Progress accounting

Numeric progress requires a finite pre-bound plan. Only independently verified units or registered Human decisions count. Planned, dispatched, receipt-received, waiting, elapsed time, token use, and unverified background claims do not count. Recalculation must show old percentage, new percentage, and exact reason. Progress never substitutes for audit, Ready, Merge, or acceptance.

## Human interaction and merge

Human normally provides initial exact scope and final high-risk decisions. Ready, merge method, Merge, branch deletion, final acceptance, runtime activation, and destructive external action remain Human-only. Merge settings, mergeability, checks, permissions, and protection are live facts and are re-read immediately before authorization and execution.

## Candidate state machine

Every formal candidate transitions through this state machine:

```
TASK_AUTHORIZED
    → MACHINE_PRECHECK
    → WRITE_AUTHORIZED
    → COMMITTED
    → PUSHED
    → DRAFT_PR
    → CI_PASS
    → FORMAL_CANDIDATE
    → INDEPENDENT_AUDIT
```

### State definitions

| State | Condition |
|-------|-----------|
| `LOCAL_DRAFT` | Local branch; no machine precheck passed or precheck failed. Not a formal candidate. |
| `TASK_AUTHORIZED` | Human has pre-granted conditional write authorization (AUTHORIZATION_ID + scope). |
| `WRITE_AUTHORIZED` | Machine precheck passed; write authorization activated. Local writes permitted within scope. |
| `COMMITTED_CANDIDATE` | At least one commit beyond exact base; pushed to remote. |
| `FORMAL_CANDIDATE` | Formal task branch, non-zero commits, exact base ancestry valid, scope compliant, candidate fingerprint computable. PR event: Head/Base match declaration. |
| `AUDIT_ELIGIBLE` | FORMAL_CANDIDATE + has open PR + CI passed + fingerprint exists. Ready for independent audit. |

### State rules

- Human can pre-grant conditional write permission; only machine precheck activates it.
- Human does not need to re-carry precheck results between windows.
- Agent self-reported PASS cannot substitute for machine facts.
- Local drafts are not formal candidates and cannot be audited.
- `LOCAL_DRAFT` cannot declare `AUDIT_ELIGIBLE`.
- Zero commits cannot declare `FORMAL_CANDIDATE`.
- No fingerprint cannot declare `AUDIT_ELIGIBLE`.
- No PR or CI cannot declare `AUDIT_ELIGIBLE`.

### Pre-write execution gate (machine-enforceable)

Before any local write, the validator enforces:

1. Detached HEAD → `HARD_STOP` (except CI checkout using `GITHUB_REF` / `GITHUB_HEAD_REF` / `GITHUB_BASE_REF`)
2. Current branch must match task-declared branch
3. Exact Base must exist as a commit
4. Exact Base must be an ancestor of current HEAD
5. Candidate must derive from `main` (no non-main parent)
6. Base drift (main advanced beyond declared base) → `HARD_STOP`

### Scope enforcement (machine-enforceable)

The Validator reads `authorized_write_scope` and verifies all actual changed
files are within the authorized set:

- Supports explicit file paths and controlled glob patterns (`fnmatch`)
- Duplicate paths in scope → `SCOPE_VIOLATION`
- Absolute paths in scope → `SCOPE_VIOLATION`
- `..` traversal paths → `SCOPE_VIOLATION`
- Files outside scope → `SCOPE_VIOLATION`
- Missing or empty scope in live candidate mode → fail-closed
- Static text validation does not depend on Git

Coverage modes:
- **Local live**: committed + staged + unstaged + untracked files
- **CI `pull_request`**: candidate Head vs target Base
- **CI push (branch)**: push branch vs `origin/main`
- **CI push (main)**: merge commit vs parent commit

## Compatibility preservation

This R1 flow is an additive narrowing of candidate topology, not permission to
remove prior gates. Dispatch Cards, Progress Receipts, valid-vs-invalid audit
receipt classification, finite repair handling, Human-action clarity, live
merge-capability preflight, reviewed revert rollback, and counter-objective
checks remain required wherever their conditions apply. The existing baseline
regression cases remain part of the complete suite; the single-PR, fingerprint,
and realtime-gate cases extend that suite.
