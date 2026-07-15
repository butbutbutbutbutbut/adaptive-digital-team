# Isolated Task Tree Orchestration

Status:
CANDIDATE_FOR_INDEPENDENT_REVIEW

Authorization:
ADT-ISOLATED-TASK-TREE-ORCHESTRATION-R1-20260716-001

Base:
215143bf8e1c05fa915deb5c3816f181451a6a57

Depends on:
`protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md`

## 1. Purpose

This protocol defines a reusable execution methodology for multi-window and multi-Agent engineering work.

The method separates:

- task intake and routing;
- context selection;
- task-tree isolation;
- model and reasoning selection;
- repository authority;
- execution evidence;
- independent checking;
- failure containment and recovery.

An isolated task tree is not merely a Git worktree. It is the complete bounded execution unit containing one task, one responsibility domain, one authority envelope, one repository state, one execution context, one model assignment, one evidence set, and one next gate.

## 2. Core flow

```text
Human or Control Plane issues governed task
→ Orchestrator reads task and authority
→ Orchestrator chooses reuse or isolation
→ Orchestrator chooses execution window and model
→ Executor works inside the fixed task boundary
→ Executor returns evidence and a state card
→ Independent Checker audits the candidate
→ Human or authorized authority decides acceptance or merge
```

The Orchestrator routes work. It does not gain acceptance or merge authority by routing it.

## 3. Required orchestration decisions

Before execution, the Orchestrator must emit a dispatch card containing:

```text
TASK:
WORKSTREAM:
WINDOW_DECISION:
WINDOW:
WINDOW_REASON:
TASK_TREE_DECISION:
TASK_TREE_REASON:
WORKTREE_DECISION:
MODEL:
REASONING_LEVEL:
MODEL_REASON:
BASE:
HEAD:
BRANCH:
AUTHORITY:
FILES_IN_SCOPE:
HERMES_DELEGATION:
ESCALATION_RULE:
STOP_RULE:
CHECKER:
NEXT_GATE:
```

No execution may begin before this card exists.

The card supplements but does not replace the required instruction header defined by `INSTRUCTION_ROUTING_AND_AUTHORITY.md`.

## 4. Window decision

Allowed values:

```text
WINDOW_DECISION:
REUSE_EXISTING | CREATE_NEW
```

### Reuse an existing window only when all conditions pass

- The responsibility domain is continuous with the prior task.
- The repository, branch, Base and current Head are known.
- The prior authority is still valid for the same Executor and scope.
- The window is not acting as Checker for the same candidate.
- The context is not superseded, stale, polluted or ambiguous.
- Reuse reduces cost without reducing traceability.

### Create a new window when any condition applies

- The task begins from a new Base.
- The responsibility or role changes.
- The task requires independent checking.
- Existing context contains conflicting or superseded instructions.
- A legacy branch is only a selective source and must not be continued.
- The task requires a different model, tool environment or authority envelope.
- Reuse would make evidence, ownership or rollback ambiguous.

A new window does not automatically require a new Git worktree. The worktree decision is separate.

## 5. Task-tree isolation

Allowed values:

```text
TASK_TREE_DECISION:
REUSE | CREATE_ISOLATED
```

An isolated task tree must have:

- one named task;
- one workstream;
- one Executor;
- one independent Checker;
- one authorization ID;
- one fixed repository Base;
- one allowed file and action scope;
- one model assignment;
- one stop rule;
- one evidence location;
- one unique next gate.

Sibling task trees may run in parallel, but they must not share mutable authority, uncommitted repository state, or acceptance decisions.

A parent Orchestrator may collect results from child task trees. It must not silently merge their scopes or transfer authority between them.

## 6. Git worktree decision

Allowed values:

```text
WORKTREE_DECISION:
REUSE_CLEAN | CREATE_ISOLATED | NOT_REQUIRED
```

Create an isolated Git worktree when repository writes must be separated from legacy branches, parallel work, uncommitted state or a different fixed Base.

Reuse a worktree only when it is clean, bound to the correct branch and Base, and contains no unrelated task state.

A documentation-only or external analysis task may use `NOT_REQUIRED` when no repository write occurs.

A worktree is an implementation mechanism. It does not replace the wider task-tree method.

## 7. Model prompt requirement

Every delegated execution task must state:

```text
MODEL:
REASONING_LEVEL:
MODEL_REASON:
ESCALATION_RULE:
STOP_RULE:
```

The exact model must be selected from models currently available in the execution environment. Historical or assumed model names must not be treated as valid without verification.

Selection principles:

1. Use the lowest sufficient model for the bounded task.
2. Use stronger reasoning only for genuine architectural, integration or diagnostic complexity.
3. Do not escalate models to compensate for browser-controller, path, permission or other infrastructure failures.
4. Do not spend engineering-model compute on long summaries, evidence indexing or report formatting when a lower-cost analysis Agent can perform that work.
5. Record why the selected model is sufficient.

`HERMES_DELEGATION` should identify analysis, documentation, test-matrix, evidence-index or state-card work delegated away from the engineering Executor. Delegation does not grant repository write, audit, acceptance or merge authority.

## 8. Authority containment

Authority is bound to the named task-tree node.

It must not be inherited from:

- the parent window;
- an old window;
- an adjacent branch;
- a previous task;
- the selected model;
- access to repository tools;
- the existence of a worktree;
- CC status.

Creating a child task tree does not expand the parent authorization.

Changing Executor, Checker, repository, Base, branch, file scope, action scope or merge target requires a new or explicitly amended authorization.

## 9. Execution lifecycle

### Intake

- Read the governed instruction.
- Verify required header fields and authority.
- Resolve the project-first repository state.

### Dispatch

- Choose window reuse or creation.
- Choose task-tree reuse or isolation.
- Choose worktree treatment.
- Select model and reasoning level.
- Emit the dispatch card.

### Preflight

- Verify repository default-branch Head when relevant.
- Verify fixed Base and branch.
- Verify clean worktree status.
- Verify files and actions in scope.
- Verify required local references are accessible.
- Fail closed on drift or ambiguity.

### Execution

- Modify only authorized files and behavior.
- Keep one responsibility domain per task tree.
- Preserve raw evidence outside Git unless evidence files are explicitly in scope.
- Stop before crossing any scope boundary.

### Receipt

- Return Base, Head, branch, changed files, validation results, evidence path, known limits, authority status and next gate.
- Mark one-time authority consumed when the authorized action completes.

### Audit

- The independent Checker verifies repository facts and evidence.
- The Executor must not accept its own work.
- Audit passage does not imply merge readiness.

## 10. Minimal task state card

Each active work item must maintain one canonical state card:

```text
WORK_ITEM:
BASE:
HEAD:
OWNER:
AUTHORITY:
GATE:
EVIDENCE:
BLOCKER:
UNIQUE_NEXT_ACTION:
UPDATED_AT:
```

Routine progress uses a normal delta update. Full recovery reporting is reserved for interruption, lost state, stale Base, orphaned work or unresolved authority.

## 11. Stop and escalation rules

Execution must stop when:

- Base drift is detected;
- required authority is missing or consumed;
- the task would modify files outside scope;
- the task would change an excluded state machine, route, contract or architecture;
- the same infrastructure failure repeats under the stated stop rule;
- evidence can no longer be bound to the fixed Head;
- Executor and Checker independence is lost;
- an old task tree is discovered to be superseded or ambiguous.

A stopped task returns a state card. It must not improvise a broader task, create unrequested recovery work, rewrite history or escalate model cost without authority.

## 12. Recovery and reuse

Use `NORMAL_DELTA` for routine updates.

Use `FULL_RECOVERY` only when one or more conditions apply:

- execution was interrupted;
- context or task state was lost;
- the local default branch is stale or uncertain;
- a worktree or branch is orphaned;
- authority consumption is unclear;
- unpushed unique commits may exist.

Recovery must establish facts before new execution. Recovery does not revive expired authority or authorize continuation of a superseded branch.

## 13. Anti-patterns

Forbidden patterns include:

- every new instruction automatically creates another window or worktree;
- every task reuses the current window regardless of context;
- model selection is omitted or chosen only by maximum capability;
- infrastructure failures trigger model escalation;
- a legacy candidate becomes the new Base without explicit migration authority;
- task-tree creation is treated as authorization;
- the Orchestrator performs independent checking of its own implementation;
- long reports replace the minimal state card;
- multiple responsibility domains are combined to save one branch or one PR;
- history rewrite is used to clean up task-tree mistakes.

## 14. Candidate gate

```text
PROTOCOL_STATUS:
CANDIDATE_FOR_INDEPENDENT_REVIEW

SELF_ACCEPTANCE:
FORBIDDEN

AUTO_MERGE:
FORBIDDEN

HISTORY_REWRITE:
FORBIDDEN

PR_CREATION_AUTHORITY:
AUTHORIZED

MERGE_AUTHORITY:
NOT_AUTHORIZED

NEXT_GATE:
INDEPENDENT_ISOLATED_TASK_TREE_PROTOCOL_AUDIT
```
