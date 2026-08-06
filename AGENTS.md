# Agent Governance

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

## Governance index

This repository's governance is organized as:

| Document | Purpose |
|----------|---------|
| `METHODOLOGY.md` | What ADT is and is not — the methodology baseline |
| `ROADMAP.md` | Current development baseline and phase status |
| `governance/ROLE_MODEL.md` | Complete role topology, authority matrix, separation rules |
| `governance/AUTHORITY_AND_FACTS.md` | Fact authority, action authority, FACT_SOURCE_REBIND |
| `AGENTS.md` | Agent-facing rules, candidate lifecycle, CI gates (this file) |
| `protocols/ARTIFACT_DELIVERY.md` | Artifact Delivery Layer — required delivery fields at task completion |
| `protocols/ADT_SELF_ITERATION.md` | ADT self-iteration — how ADT discovers and fixes its own governance defects |
| `protocols/RESOURCE_ALLOCATOR_INTEGRATION.md` | Resource Allocator Integration — dispatch-time resource allocation flow |
| `protocols/WORKSPACE_ISOLATION.md` | Workspace isolation — git worktree per agent for parallel execution |
| `protocols/CONCURRENCY_LIMIT.md` | Concurrency limit — in-flight task cap per Controller (default N=2) |
| `protocols/HOLDER_TOKEN.md` | Holder token — one task one token; CANDIDATE_BINDING write-right arbitration |
| `protocols/ADT_ANTI_OBJECTIVE_PROMPT.md` | Anti-objective prompt system — per-role self-checks and Authority Dispatch Card template |
| `protocols/HUMAN_FACING_PSYCHOLOGY.md` | Human Facing 心理机制 — 用认知心理学推动用户反思与推进 |
| `protocols/*.md` | Detailed protocol specifications |

These documents are read in a chain: a new agent window starts from AGENTS.md and follows the index.

## Protocol activation

Protocol activation is defined by `BOOTSTRAP.md` — the single normative source.
A repository read activates the ADT protocol and assigns the Anding
interface identity (`ANDING_INTERFACE`). Activation alone grants no write,
Ready, Merge, or Control authority. The full activation specification, read
order, and two-layer Anding identity model are in `BOOTSTRAP.md`.

## First-contact routing

First-contact routing uses the A/B/C protocol. The authoritative complete
definition is at `protocols/BEGINNER_BOOTSTRAP_ROUTER.md`. The Human-facing
entry is at `README.md`.

Summary:
- Link-only first message: show only A/B/C
- Message already carries a task, files, repo link, or control packet: skip menu, route directly
- A/B modes never require GitHub operations
- C mode does not auto-grant write permission
- Mode lock: A/B never auto-upgrade to repo mode; C never auto-upgrades to write mode

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
- User-facing entry points (`README.md` and the A/B/C routing in `protocols/BEGINNER_BOOTSTRAP_ROUTER.md`) are protected product assets. Their functional structure (Human/AI routing, A/B/C as operational entry paths, auto-skip logic) must not be removed, diluted into navigation links, or overwritten without explicit Human authorization. A README rewrite that removes A/B/C as functional entry points is a scope violation — the README is not just documentation, it is the product's first-contact interface.
- Project Control is the single Human-facing entry point. It routes to Task Holders but does not directly implement candidates and defaults to no repository write access.
- A read, analysis, review, or decision request must not be expanded into repair, implementation, or repository writes without explicit Human authorization.
- A material Human premise must be judged `SUPPORTED`, `PARTIAL`, `REJECTED`, or `UNVERIFIED`; agreeable wording is not evidence.
- The same task continues by default. Restart requires role isolation, invalidated fact source, context contamination, or an explicit Human request.
- Safety risk, resource tier, and Checker timing are separate controls. HIGH risk alone does not authorize strong resources or an early Checker.
- Human restatement, frustration, or scope correction is a control signal: shorten the response, discard inferred scope, and restore the latest explicit authorization.
- Controller / Project Control / Holder returns to Human MUST include at minimum: FACT, AUTHORITY, ACTION, RESULT, ARTIFACT_TYPE, ARTIFACT_LOCATION. Any return missing one of these fields is an incomplete return — fail-closed until the missing fields are supplied. A narrative summary is not a substitute.
- Governance file changes (AGENTS.md, METHODOLOGY.md, ROADMAP.md, protocols/, governance/) require independent Checker verification. A PR touching these files without a valid Checker receipt fails CI.

## Repository-as-prompt startup

Every new Holder, Maker, Checker, window, or agent must, before write:

1. read `AGENTS.md` and `PROJECT_STATE.md`;
2. fetch origin and verify the checked-out branch, HEAD, worktree, open PRs, and candidate branches;
3. compare durable state with live GitHub and Git facts;
4. resolve one authoritative fact source;
5. stop in `FACT_SOURCE_REBIND` if facts conflict;
6. verify task authority, exact repository, exact Base, exact branch, exact allowed files, and next gate.

For `SAME_TASK_CONTINUATION`, do not replay the full startup. Re-verify only the
live delta, authorization boundary, current stage, and next gate. The complete
continuity classification is in `BOOTSTRAP.md`; the adaptive cost judgment is
normative only in `METHODOLOGY.md`.

Governance base and product fact source remain distinct. Main is the governance base by default and does not silently become a product fact source.

## Workspace isolation

Parallel agents MUST NOT share a single working tree. Every write task runs in its
own `git worktree`, created outside the main working tree:

```text
<repo-parent>/.adt-worktrees/<repository-name>/<agent-name>/
```

Invariants:

- `ONE_WORKTREE = ONE_BRANCH = ONE_TASK` — one worktree checks out exactly one branch;
  Git natively forbids checking out the same branch in two worktrees.
- The main working tree stays on `main` and carries no parallel write task.
- `.hermes/CANDIDATE_BINDING.json` and `.hermes/checker_receipt.json` are tracked
  per-branch files: each worktree holds its own branch's copy, eliminating
  single-point binding contention.
- A worktree mismatch with the Dispatch Card (`WORKTREE` field, `BASE_SHA`,
  `BRANCH`) fails closed — never force, never bypass.

Full specification: `protocols/WORKSPACE_ISOLATION.md`. Commands:
`docs/worktree-quickstart.md`.

## Concurrency limit

A Controller MUST NOT hold more than `N` in-flight tasks at the same time
(default `N=2`). In-flight means dispatched but not yet aggregated: from
Dispatch Card emission to merge, cancel, or close.

Rules:

- `ONE_IN_FLIGHT = ONE_BRANCH = ONE_WORKTREE = ONE_TASK` — each in-flight
  task holds one write worktree on its own branch; read-only Checker worktrees
  do not consume an in-flight slot.
- When the cap is reached, new tasks queue FIFO with a bounded queue
  (`MAX_QUEUE = 2 × N`); queue overflow or queue timeout returns
  `CONCURRENCY_REJECTED`.
- Only the Human Holder may change `N`. The Controller may fail-safe degrade to
  `N=1` on sustained subagent timeouts and must report to Human; it never
  raises `N` on its own (`N_MAX = 4`).
- The concurrency cap is orthogonal to resource tiers: a tier bounds a single
  task's budget; the cap bounds concurrent tasks.

Full specification: `protocols/CONCURRENCY_LIMIT.md`.

## Holder token

A task owns exactly one token (`ONE_TASK = ONE_TOKEN`). The token holder is
the only writer of `.hermes/CANDIDATE_BINDING.json` while its task is in
flight: dispatch writes binding + token atomically (no manual rebind), and the
token is released when the Human gate (ACCEPT / REJECT / MODIFY) completes.

Rules:

- `ONE_IN_FLIGHT = ONE_TOKEN = ONE_BRANCH = ONE_WORKTREE = ONE_TASK` — token
  count ≤ concurrency cap N; queued tasks hold no token.
- Token state is recorded in the `token` field of `CANDIDATE_BINDING.json`
  (`HELD` / `RELEASED`); binding and token update in one write, leaving no
  dual-file inconsistency window.
- Rebind is automatic at dispatch: the Controller writes binding + token
  together; manual rebind is obsolete.
- `validate_binding.py` checks are unchanged — the `token` field is additive
  and optional; CI still fails closed on binding mismatch.
- Abnormal release (timeout / failure / crash) recycles the token before the
  next task is dispatched; recovery never guesses.

Full specification: `protocols/HOLDER_TOKEN.md`.

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

A Checker performs read-only verification, did not design or implement the candidate, did not produce its evidence, and can reject it. Any independence ambiguity fails closed. Checker capacity is allocated only when `checker_timing=NOW`, after a formal candidate exists; `AFTER_FORMAL_CANDIDATE` reserves the later gate without starting a Checker during local production.

## Human-facing evidence discipline

Critical nodes must preserve exact machine facts and provide readable Simplified Chinese explanation. At minimum report:

```text
FACT
AUTHORITY
ACTION
RESULT
ARTIFACT_TYPE
ARTIFACT_LOCATION
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

## Human-facing psychology discipline

Human Facing 接触面不只是状态报告，还要帮助用户看见自己的进度、承诺与未完成项，
在关键节点做出有反思的决策（ROADMAP.md § PT）。心理机制清单、落地场景与伦理边界
见 `protocols/HUMAN_FACING_PSYCHOLOGY.md`。核心约束：

- 心理机制是呈现层的组织方式，不替代证据纪律——FACT、AUTHORITY、ACTION、RESULT、
  ARTIFACT_TYPE、ARTIFACT_LOCATION 等字段仍必须完整、真实。
- 帮助看见，不是诱导决策；禁止制造虚假紧迫感、虚假进度、虚假稀缺。
- 用户随时可关闭心理呈现（纯状态模式），关闭不影响任何治理功能。
- 承诺重申是温和提醒，不阻止用户改变方向；方向改变后立即更新承诺基线。
- 机制服务于用户决策质量，间接改善 PT 训练数据（黄金标签）质量，禁止反向操控。

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

### Runtime adapter boundary

The Runtime Adapter Contract (`protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md`,
status: ADOPTED_GOVERNANCE_SPECIFICATION) defines a three-layer isolation boundary between tool-native
runtimes (Hermes, Codex, etc.) and the ADT Governance Core:

- **Layer 1** (Tool-Native Context): process state, API keys, and credential
  values that NEVER enter ADT Core.
- **Layer 2** (Adapter Envelope): tool identity, session metadata, capability
  tags, and credential tags (descriptive only — no values). Stripped before
  reaching Layer 3.
- **Layer 3** (TaskIntake): the existing ADT Core input contract — UNCHANGED.

Key constraints:
- `SESSION_PRINCIPAL` (tool login) is NOT the Human Holder — zero mappings.
- Authorization comes ONLY from external `ExecutionAuthorizationBinding`, never
  from the adapter or tool identity.
- `plan.write_scope ⊆ auth.authorized_write_scope` (subset, not equality).
- Every file-targeting action is gated by scope; out-of-scope attempts →
  `ATTEMPTED_SCOPE_VIOLATION`, credential capability irrelevant.
- Checker independence uses two-phase evidence (5 fields), not a single boolean.
- Default-forbidden actions (ready, merge, close_pr, delete_branch) MUST NOT
  appear in `authorized_actions`.
- `plan.route` is NEVER overwritten by `adapter_error`.

The adapter (`scripts/validate_adapter.py`) performs validation ONLY — no
authorization generation, no action execution.

## Adaptive counter-objective governance

Governance must not multiply candidates, duplicate state systems, or create formally correct but unnecessary work. When governance cost exceeds product or safety value, use the smallest safe path. Activity completion never equals product progress, and tooling work never inherits product acceptance.

Operationally:

- the anti-review runs silently and consumes zero Point;
- `anti_review_decision=DOWNSCOPE` reduces work rather than generating another receipt;
- `recommended_points`, `hard_max_points`, approximate token budget, Checker permission, and external-message limit remain Human ceilings;
- local candidate production may use economy or standard resources even when safety risk is HIGH;
- CRITICAL governance modification defaults to strong resources;
- resource allocation exceeding any Human boundary returns `BLOCKED`;
- friction restores the most recent explicit scope and reduces external messages.

The sole normative rationale is `METHODOLOGY.md`; frozen data values and routing behavior are in the existing schemas and router/allocator. No second anti-objective protocol, task tier, candidate state, or lifecycle is created.

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
  authorized task;
- dynamic governance routing that classifies task type, assesses risk,
  decomposes tasks into ordered execution units, and produces Candidate
  Control Packets — never AUTHORIZED without Human Holder approval
  (`protocols/DYNAMIC_GOVERNANCE_ROUTER.md`).

The pre-existing regression set remains a compatibility baseline. New R1 tests
are additive coverage; passing new identity tests cannot waive an older safety
or authority rule.
