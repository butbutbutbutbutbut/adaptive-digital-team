# Repository as Prompt — Runtime Binding Protocol

PROTOCOL_STATUS: `ADOPTED_GOVERNANCE_SPECIFICATION`
TASK_TYPE: `GOVERNANCE_PROTOCOL_UPGRADE`

This protocol is the operational binding layer that makes "repository as prompt"
work at runtime. It extends the Persistent Holder Control Plane and Lightweight
Execution Flow; it does not create a parallel routing or receipt system.

## Purpose

A new window, Holder, Maker, Checker, or child agent must be able to recover
from the repository alone — without the user re-pasting the full governance
context — the following live binding facts:

- current authoritative fact source
- current product baseline
- governance baseline
- active candidate and comparison candidates
- invalidated candidates
- current gate
- write permissions
- counter-objectives
- whether Human action is required

## Scope

This protocol applies to:

- every new Agent window receiving a repository task
- every Holder dispatch
- every Maker execution start
- every Checker audit start
- every child or tooling subagent spawn

It does NOT apply to: same-task iteration within the same window where no
binding facts have changed.

## 1. Single Authoritative Fact Source

### 1.1 Binding model

The repository SHALL maintain exactly one runtime binding record. In the ADT
organization repository, this is `PROJECT_STATE.md`. In product repositories,
this is `.adt/project-binding.yaml`. Both express the same schema.

The binding model MUST express:

```yaml
schema_version: "1"
adt_repository: butbutbutbutbutbut/adaptive-digital-team
adt_pin: <full commit SHA of the ADT org repo>

# product_repository is only present when this binding describes a product repo
product_repository: <owner/repo or NONE>

governance_base:
  branch: main
  sha: <full SHA>

authoritative_fact_source:
  type: HUMAN_EXPLICIT | BINDING_RECORD | PR_HEAD | BRANCH_HEAD
  evidence: <receipt, declaration, or resolution method>
  branch: <branch name>
  sha: <full SHA — MUST be resolved live, never trusted stale>

active_candidate:
  branch: <branch name>
  resolved_head: <full SHA — MUST be resolved live at read time>
  status: ACTIVE

comparison_candidates:
  - branch: <branch name>
    resolved_head: <full SHA>
    status: COMPARISON_ONLY
    comparison_group: <label>

historical_references:
  - branch: <branch name>
    sha: <full SHA>
    role: <description>

invalidated_candidates:
  - branch: <branch name>
    sha: <full SHA>
    invalidation_reason: <reason>

current_gate: <gate identifier>

visual_status:
  active_candidate: CANDIDATE_NOT_ACCEPTED | HUMAN_ACCEPTED | REJECTED

authorized_action: <action description>
authorized_write_scope: <file paths or patterns>

counter_objectives:
  - <counter-objective statement>

progress:
  completed: <int>
  total: <int>
  display: "[##########]"

user_action_required: YES | NO
system_next_step: <step description>
last_verified_at: <ISO 8601 timestamp>
```

### 1.2 Fact-source priority

When determining the authoritative fact source at startup, the following
priority order applies (higher number = higher priority):

| Priority | Source | Condition |
|----------|--------|-----------|
| 5 (highest) | Human explicit branch + SHA binding | Human declares exact branch and SHA as the fact source; must be persisted to the binding file at next authorized write |
| 4 | Active candidate in binding record | Binding file has a valid `active_candidate` with `resolved_head` matching live remote |
| 3 | Open PR with Human binding evidence | PR description or commit message contains a Human binding declaration |
| 2 | Branch HEAD containing ADT binding record | Remote branch whose tip commit contains a valid `.adt/project-binding.yaml` or binding declaration |
| 1 (lowest) | main (governance only) | main SHALL default to governance source only; it MUST NOT be automatically treated as a product source |

Constraints:

- `resolved_head` MUST be resolved via live `git ls-remote` at every binding
  read. Stale cached SHAs from the binding file MUST NOT be trusted.
- main SHALL default to governance source only. Without an explicit Human
  declaration, main MUST NOT be automatically treated as a product source.
- A PR Head MUST NOT automatically override an independently declared candidate
  branch.
- "Most recent commit time" alone MUST NOT determine the fact source.
- Human's explicit binding of branch + SHA has the highest product fact
  priority but MUST be persisted to the binding file at the next authorized
  write.
- `comparison_candidates`, `historical_references`, and `invalidated_candidates`
  MUST be explicitly distinct from `active_candidate`.
- `visual_status` is independent of upload, build, and CI status. CI PASS MUST
  NOT automatically change `visual_status`.

### 1.3 Governance base vs. product base

`governance_base` and `authoritative_fact_source` are distinct:

- `governance_base`: the branch and SHA from which governance rules (AGENTS.md,
  protocols) are read. Defaults to `main`.
- `authoritative_fact_source`: the branch and SHA that represents the current
  product truth.

They MAY be the same branch but MUST be explicitly declared as such. Conflating
them without explicit declaration is `GOVERNANCE_PRODUCT_BASE_CONFLATED` and
fails closed.

## 2. Mandatory Repository Startup Protocol

### 2.1 Full startup (triggered on: new window, new task, fact conflict, new Human candidate receipt, binding SHA change, current gate change)

Every new window or agent receiving a repository task MUST execute this
sequence before any product write:

```
1. Read AGENTS.md
2. Read the binding file (PROJECT_STATE.md or .adt/project-binding.yaml)
3. Fetch origin (git fetch origin --prune)
4. Verify current branch, HEAD, and worktree
5. Enumerate:
   a. Currently bound candidate (from binding file)
   b. Open PRs (gh pr list)
   c. Recent remote candidate branches (git ls-remote --heads origin)
   d. Candidate branches containing ADT binding records
   e. Local worktrees
   f. New Human-provided precise receipt (if any)
6. Compare binding record against live Git facts
7. Resolve the single authoritative fact source
8. Only after a unique fact source is closed: product write is permitted
```

### 2.2 FACT_SOURCE_REBIND

Write MUST be automatically suspended and enter `FACT_SOURCE_REBIND` when:

- Browser/render output does not match the binding SHA
- User declares "not the version I saw"
- New A/B or other candidate upload receipt appears
- Worktree, branch, and remote HEAD are inconsistent
- Current candidate has been explicitly invalidated
- Governance base and product base are conflated without declaration
- An unregistered updated candidate is discovered

During `FACT_SOURCE_REBIND`:

- Product write is BLOCKED
- Governance analysis and binding repair are permitted
- The agent MUST NOT create R1/R2, migrate code, or patch governance before
  investigating the fact conflict

### 2.3 Delta-only iteration (same task, same window, no fact drift)

When none of the full startup triggers have fired, the agent SHALL only
verify:

- Binding HEAD is unchanged
- Authorized write scope is unchanged
- Current gate is unchanged

Then proceed directly. Do NOT repeat the full enumeration.

## 3. Chat Carries Only Delta

### 3.1 What the repository already carries (do not repeat in chat)

The following stable facts are carried by the repository and SHALL NOT be
required from the user in every chat round:

- Repository name
- Bound baseline SHAs
- Known prohibited actions
- Current gate
- Historical candidate list
- Fixed receipt specifications
- Governance protocol text
- Counter-objective list

### 3.2 What the user provides (per round)

The user SHALL only provide:

- TASK_ID (or the system resolves it)
- Current-round goal or feedback
- Required Human decisions
- New external evidence (if any)

### 3.3 Minimum prompt shape

```text
TASK_ID: <id>
USER_DELTA: <new goal, feedback, or decision>
NEW_EVIDENCE: <if any, or NONE>
```

Full protocol text remains in the repository; it is never repeated in chat.

## 4. Human-Facing Progress Interface (9-Line Card)

### 4.1 Default short card

Every gate transition SHALL output only the following nine lines:

```text
TASK: <short task description>
STATUS: <current execution status>
FACT_SOURCE: <branch>@<full SHA>
ACTIVE_BASELINE: <candidate branch>@<full Head>
PROGRESS: [##########] XX%
ACTION: <one-line description of current action>
FILES_TOUCHED: <count and key paths, or NONE>
NEXT_GATE: <next gate identifier>
USER_ACTION_REQUIRED: YES | NO
```

### 4.2 Extended fields (only during HARD_STOP, fact conflict, or Human-requested detailed audit)

```text
FAILURE_CLASS: <failure class code>
COUNTER_OBJECTIVE_RESULT: <pass/fail/violation>
SYSTEM_NEXT_STEP: <precise next system action>
```

### 4.3 BLACKBOX prohibition

`BLACKBOX_STATUS: PROHIBITED`

The following status claims are prohibited without evidence:

- "Processing..." (处理中)
- "System status delayed" (系统状态延迟)
- "Completed" (已完成) without SHA + action + file evidence

Every status change MUST bind:

- Exact SHA
- Actual action taken
- Actual files changed
- Current gate
- Next step

"Subagent completed" is NOT task completion. "Uploaded" is NOT visually accepted.
"CI PASS" is NOT Human accepted.

### 4.4 Information density

Full commands, file diffs, prohibition lists, and audit materials go into:

- Progress Receipt
- Audit Receipt
- PR body
- Repository documents

They SHALL NOT be dumped into chat by default.

## 5. Pre-Counter-Objective Gate

Before creating a branch, migrating a baseline, establishing a new candidate,
or repairing governance state, the system MUST first check:

1. Does this action directly increase product value?
2. Does this increase the candidate count?
3. Does this create a new competing fact source?
4. Does this duplicate capability of an existing branch?
5. Can this be folded into the next real product task?
6. Is this formally correct but unnecessary?
7. Does this increase the user's comprehension burden?

If `GOVERNANCE_COST > PRODUCT_OR_SAFETY_VALUE`:

- The action is REJECTED
- A smaller alternative MUST be proposed

This check SHALL NOT be deferred until the user questions it. It runs before
the action, not after.

## 6. Candidate Publication Contract

When any A/B, demo, checkpoint, or visual candidate is uploaded, its branch MUST
declare in its binding record:

```yaml
candidate_status: ACTIVE_CANDIDATE | COMPARISON_ONLY | HISTORICAL | INVALIDATED
visual_status: CANDIDATE_NOT_ACCEPTED | HUMAN_ACCEPTED | REJECTED
source_branch: <branch>
source_sha: <full SHA>
comparison_group: <label or NONE>
supersedes: <branch name or NONE>
current_gate: <gate>
next_recommended_action: <action>
```

Upload success, CI PASS, and mergeability SHALL NOT automatically change
`visual_status`. Only Human explicit acceptance changes `visual_status`.

## 7. Session Drift Control

Full repository startup executes only on:

- New window
- New task
- Fact conflict detection
- Human provides new candidate receipt
- Binding SHA changes
- Current gate changes

Normal same-task iteration only verifies binding HEAD and authorized change
scope. Full scanning SHALL NOT repeat every round, to prevent governance
overhead from consuming product work.

## 8. Integration with Existing Protocols

This protocol is an operational extension of:

- `AGENTS.md` — inherits all governance, Human-facing interface, merge
  preflight, and authority rules
- `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` — the Holder remains the
  single router and State Registrar; this protocol adds binding validation
  and fact-source resolution to the Holder's pre-dispatch verification
- `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` — the L0/L1/L2 flow remains
  authoritative; this protocol adds delta-only prompt rules and drift
  trigger conditions
- `protocols/ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` — the counter-objective
  review remains the pre-execution gate; this protocol adds the pre-action
  counter-objective check (GOVERNANCE_COST vs PRODUCT_OR_SAFETY_VALUE)
- `BOOTSTRAP.md` — the bootstrap sequence is extended with the full startup
  protocol defined here
- `docs/REPOSITORY_AS_PROMPT_PRINCIPLE_R1.md` — the conceptual principle;
  this protocol is its operational implementation

This protocol does NOT:

- Create a second routing system
- Override existing Human-only gates
- Change Publish Lease rules
- Activate Runtime or Hermes R1
- Authorize automatic merge
- Change PR10's read-only status

## 9. Validation

A binding record is valid only when:

1. `authoritative_fact_source` is present and its `sha` resolves live
2. `active_candidate` does not appear in `invalidated_candidates`
3. `governance_base` and `authoritative_fact_source` are not both `main`
   without explicit Human declaration
4. No `comparison_candidates` entry shares a branch with `active_candidate`
5. `visual_status` is not `HUMAN_ACCEPTED` when only CI evidence exists
6. `FACT_SOURCE_REBIND` state does not coexist with product write permission
7. Progress card has `FACT_SOURCE`, `ACTIVE_BASELINE`, and `NEXT_GATE`
8. Candidate `resolved_head` matches live remote; mismatch is HARD_STOP, not
   automatic migration

Validation is performed by `scripts/validate_binding.py` and run in CI.

## 10. A/B Incident Replay Acceptance Test

The following scenario MUST pass:

```
GIVEN:
  - PR #35 = historical visual baseline (HISTORICAL)
  - Version A branch = Human-bound sole active fact source
  - Version B branch = comparison only (COMPARISON_ONLY)
  - R2 branch = invalidated (INVALIDATED)

WHEN: system resolves authoritative fact source

THEN:
  - System selects Version A
  - System does NOT select PR #35
  - System does NOT select main
  - System does NOT select R2
  - System reports FACT_SOURCE: Version A@<sha>
```

This test lives in `tests/test_binding_validation.py`.

## Adoption Boundary

This protocol documents the operational runtime binding rules. It does not
implement a runtime, scheduler, automation, or service. Adoption records the
governance specification only. Runtime activation remains `NOT_AUTHORIZED`.
