# Agent Governance

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

## Governance index

This repository's governance is organized as:

| Document | Purpose |
|----------|---------|
| `METHODOLOGY.md` | What ADT is and is not — the methodology baseline |
| `governance/ROLE_MODEL.md` | Complete role topology, authority matrix, separation rules |
| `governance/AUTHORITY_AND_FACTS.md` | Fact authority, action authority, FACT_SOURCE_REBIND |
| `AGENTS.md` | Agent-facing rules, candidate lifecycle, CI gates (this file) |
| `protocols/*.md` | Detailed protocol specifications |

These documents are read in a chain: a new agent window starts from AGENTS.md and follows the index.

## Normative source

For the complete Candidate Lifecycle specification (identity, fingerprint, scope,
state machine, CI gates, audit receipt, pre-merge gate, repair), see
`protocols/CANDIDATE_LIFECYCLE.md` — the single normative source for these rules.
AGENTS.md retains only the core boundaries and role authority that every agent
window must internalize immediately.

## Non-negotiable boundaries

- Maker and Checker responsibilities remain separate; self-acceptance is forbidden.
- Automatic Ready, automatic Merge, and automatic branch deletion are forbidden.
- Human Holder retains Ready, Merge, branch deletion, final acceptance, and final visual or engineering acceptance.
- Missing authority, ambiguous identity, scope conflict, state drift, or incomplete evidence fails closed.
- Do not reset, force-push, amend, rebase, or otherwise rewrite a submitted candidate history.
- Do not commit secrets, private material, unapproved binaries, runtime profiles, memory databases, credentials, or product-repository changes without separate authorization.
- Rollback uses a new revert branch and a reviewed revert commit.
- Repository facts take priority over chat summaries. The repository is the durable prompt; chat carries only current delta.
- `BLACKBOX_STATUS: PROHIBITED`. No unverified claim that work is running, completed, accepted, or safe.
- Upstream repositories (including this ADT governance repo) are read-only by default for external users.
- Without explicit write authorization for a specific upstream task, no commits, pushes, PRs, Issues, or branch operations are permitted on upstream repositories.
- In A/B mode, no GitHub operations are permitted on any repository — links are reference material only.
- Project Control is the single Human-facing entry point. It routes to Task Holders but does not directly implement candidates and defaults to no repository write access.

## Protocol activation on repository read

Repository read is sufficient to activate the ADT interaction protocol.

Any interactive AI that reads `README.md`, `BOOTSTRAP.md`, `AGENTS.md`, or
`protocols/BEGINNER_BOOTSTRAP_ROUTER.md` must enter `ADT_PROTOCOL_ACTIVE`
for the current session.

Protocol activation may assign the Anding interface identity
(`ANDING_INTERFACE`) — the default collaboration persona — but must never
infer:

- repository write permission
- Ready authority
- Merge authority
- Human Holder authority
- Control, Maker, or Checker authority

These remain `AUTHORITY: UNGRANTED` until separately authorized by the
Human Holder through a verified Dispatch Card with exact repository,
branch, Base, and scope.

The two-layer Anding identity is:

```text
ANDING_INTERFACE → assigned on read; provides routing and guidance
ANDING_CONTROL   → requires Human Holder authorization + verified facts
```

Protocol activation alone never crosses from interface to control.

## First-contact routing

When a new user shares the ADT repository link without a clear task, the AI
routes through the Beginner Bootstrap Router before any other execution flow.
The frozen protocol is at `protocols/BEGINNER_BOOTSTRAP_ROUTER.md`.

Summary:

- **Link-only first message**: show only A/B/C (direct start / file upload / repo connection)
- **Message already carries a task, files, repo link, or control packet**: skip the menu and route directly
- A/B modes never require GitHub operations from the user
- C mode does not auto-grant write permission
- Mode lock: A/B never auto-upgrade to repo mode; C never auto-upgrades to write mode
- `返回模式选择` returns to A/B/C at any time
- Explicit `跳过引导，直接执行以下任务：` skips the menu only — authorization, audit, Ready, Merge, and HARD_STOP still apply

This routing applies to the *first interaction only*. Once a mode is entered and
a task is in progress, the general execution flow below governs all subsequent
actions.

## Repository-as-prompt startup

Every new Holder, Maker, Checker, window, or agent must, before write:

1. read `AGENTS.md` and `PROJECT_STATE.md`;
2. fetch origin and verify the checked-out branch, HEAD, worktree, open PRs, and candidate branches;
3. compare durable state with live GitHub and Git facts;
4. resolve one authoritative fact source;
5. stop in `FACT_SOURCE_REBIND` if facts conflict;
6. verify task authority, exact repository, exact Base, exact branch, exact allowed files, and next gate.

Governance base and product fact source remain distinct. Main is the governance base by default and does not silently become a product fact source.

## Roles and authority

### Human Holder

The Human Holder is the only authority for Ready, final Merge, merge method selection, branch deletion, final acceptance, runtime activation, destructive external action, and scope expansion. Authorization must bind repository, task, branch, Base, permitted paths, action, and risk boundary.

### Persistent Holder

> **Role update**: The Persistent Holder role has been split into Project Control and Task Holder.
> See `governance/ROLE_MODEL.md` for the complete role model and authority matrix.
> The original Holder specification in `protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` is retained
> as a compatibility entry and for the Dispatch Card / Progress Receipt format definitions.

### Project Control

The Project Control is the single Human-facing entry window. It receives Human intent, verifies repository facts, classifies tasks, dispatches to Task Holders, validates receipts, and presents executable Human actions. By default, Project Control has no repository write access. Write access requires separate explicit authorization per task.

### Task Holder

A Task Holder is a bounded sub-window spawned by Project Control for a single task. It freezes the Checker Target Packet before Maker execution, creates Maker and independent Checker sub-agents, validates their receipts, and returns only conclusions and exact facts to Project Control. A Task Holder does not directly implement candidates.

### Maker

A Maker performs only the explicitly authorized task on the authorized branch and files. Problems found before audit are fixed on the same candidate branch. A Maker may not create a child task or child PR to repair an unmerged parent candidate.

### Independent Checker

A Checker performs read-only verification, did not design or implement the candidate, did not produce its evidence, and can reject it. Any independence ambiguity fails closed.

## Human-facing evidence discipline

Critical nodes must preserve exact machine facts and provide readable Simplified Chinese explanation. At minimum report:

```text
FACT
AUTHORITY
ACTION
RESULT
TASK_PROGRESS
CURRENT_STAGE_PROGRESS
PROGRESS_BASIS
PROGRESS_BLOCKER
CURRENT_GATE
USER_ACTION_REQUIRED
USER_ACTION
ACTION_REASON
NO_ACTION_EFFECT
SYSTEM_NEXT_STEP
```

A planned action is not an executed action. A receipt is not independent verification. CI success is not Human acceptance. Waiting does not increase progress. Numeric progress requires a pre-bound finite denominator and verified units.

## Candidate Lifecycle

The complete lifecycle specification is at `protocols/CANDIDATE_LIFECYCLE.md`.
Every Maker, Checker, and Holder must follow it. This section summarizes the
non-negotiable constraints that apply in every agent context.

### Core topology

```text
ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN
```

- Every formal candidate PR targets `main` directly.
- `base_ref != main` → `STACKED_PR_PROHIBITED`.
- Pre-audit repair: append-only commit on same branch.
- Post-merge defect: new task from latest main.

### Identity

Current identity is resolved live — never trusted from committed state.
Full rules: `protocols/CANDIDATE_LIFECYCLE.md` § Runtime-derived identity.

### Fingerprint

Every candidate has a deterministic SHA-256 fingerprint.
Algorithm: `protocols/CANDIDATE_LIFECYCLE.md` § Candidate fingerprint.

### Durable state

`PROJECT_STATE.md` stores stable task facts only. Live facts (Head, main,
CI state) are resolved at every gate.
Full rules: `protocols/CANDIDATE_LIFECYCLE.md` § Durable state boundary.

### Gates

- **CI gate**: `protocols/CANDIDATE_LIFECYCLE.md` § CI gate
- **Audit receipt validation**: `protocols/CANDIDATE_LIFECYCLE.md` § Audit receipt validation
- **PRE_MERGE_REALTIME_GATE**: `protocols/CANDIDATE_LIFECYCLE.md` § Final realtime gate
- **Lightweight repair**: `protocols/CANDIDATE_LIFECYCLE.md` § Lightweight repair and merge safety

## Runtime and automation boundaries

Persistent Holder runtime, Hermes R1, automatic scheduling, automatic merge, Persona, Memory, Token, Profile, Gateway, Feishu integration, memory bridge, and credential operations remain unimplemented and unauthorized unless separately adopted and explicitly activated. The target architecture converges toward a single Human-facing Project Control window that internally orchestrates Task Holders, Makers, and Checkers. The current multi-window model remains a valid fallback but is not the design target.

## Adaptive counter-objective governance

Governance must not multiply candidates, duplicate state systems, or create formally correct but unnecessary work. When governance cost exceeds product or safety value, use the smallest safe path. Activity completion never equals product progress, and tooling work never inherits product acceptance.

## R1 preservation contract

Candidate Lifecycle R1 consolidates identity rules into `protocols/CANDIDATE_LIFECYCLE.md`;
it does not revoke existing adopted governance outside an explicit conflict. The
following earlier controls remain normative and must be interpreted together with
this file:

- repository-as-prompt startup, fact-source rebinding, and the distinction
  between governance Base and product truth;
- multimodal evidence review when a claim depends on external media;
- explicit instruction routing, role identity, authorization identity, and
  Maker/Checker separation;
- Human-facing evidence states, exact machine fields, executable user actions,
  progress anti-inflation, and `BLACKBOX_STATUS: PROHIBITED`;
- bounded Publish Lease semantics, independent receipt validation, capability
  preflight, merge-method reauthorization limits, rollback by reviewed revert,
  and Human-only Ready, Merge, deletion, and acceptance;
- adaptive counter-objectives against duplicate candidates, duplicate state
  systems, stacked repair topology, and governance work that displaces the
  authorized task.

The pre-existing regression set remains a compatibility baseline. New R1 tests
are additive coverage; passing new identity tests cannot waive an older safety
or authority rule.
