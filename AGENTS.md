# Agent Governance

Status: `ADOPTED_GOVERNANCE_SPECIFICATION`

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

The Persistent Holder is the resident control-plane interface and State Registrar, not a third Maker. It verifies facts, prepares exact packets, routes work, validates receipts, and presents executable Human actions. It does not directly Push unless separately appointed as Maker for the task, and it never self-authorizes.

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

## Candidate Lifecycle R1

### Single formal candidate topology

The normative equation is:

```text
ONE_TASK = ONE_BRANCH = ONE_PR = BASE_MAIN
```

Rules:

- Every formal candidate PR targets `main` directly.
- A PR whose `base_ref` is not `main` fails as `STACKED_PR_PROHIBITED`.
- CI must trigger for every pull request, including a pull request aimed at another candidate branch; a stacked PR cannot hide by avoiding validation.
- Do not repair an unmerged parent candidate through a child PR.
- Before independent audit, append repair commits directly to the original candidate branch and audit the new Head.
- After a candidate is merged, a newly discovered problem starts from the latest `main` as a new task, new branch, and new PR.
- A former child PR must not be retargeted to `main` after its parent is squash-merged.
- One task may contain multiple append-only commits on its single branch, but it still has exactly one PR and one direct Base: `main`.

### Runtime-derived identity

Current identity is never trusted from committed state.

#### Push

- `push_branch` is derived only from `GITHUB_REF`.
- Only `refs/heads/<branch>` is accepted.
- Missing, empty, tag, notes, pull-merge, or any other ref format is `HARD_STOP`.
- The identity chain is exact: `git HEAD = GITHUB_SHA = origin/<push_branch>`.
- There is no fallback to a branch cached in `PROJECT_STATE.md`.

#### Pull request

- `head_ref` and `head_sha` come from the pull-request event source Head.
- `base_ref` and `base_sha` come from the pull-request event Base.
- `base_ref` must be `main`.
- `refs/pull/*/merge` and synthetic merge commits are not candidate identity.
- The source Head must equal `origin/<head_ref>` and the checkout used for validation must be that source Head.

#### Local and pre-merge

- Current Head is `git rev-parse HEAD`.
- Current main is `origin/main`.
- Candidate remote is `origin/<candidate_branch>`.
- Current Base, Head, remote refs, changed files, and fingerprint must not be read from committed cache fields.

### Durable state boundary

`PROJECT_STATE.md` stores stable task facts only:

- `task_id`
- `repository`
- `branch`
- `starting_base_sha`
- `authorized_write_scope`
- `authority`
- `current_gate`
- `implementation_status`

It must not store the current Head, current main, current event SHA, current remote branch SHA, or current candidate hash. A `resolved_head`, when present in historical material, is only a historical anchor: it need not equal the current Head, but it must be a commit reachable from current history. It must never reintroduce SHA self-reference.

### Candidate fingerprint

A deterministic SHA-256 fingerprint binds the normalized fields:

```text
repository
base_ref
base_sha
head_ref
head_sha
sorted(changed_files)
```

Validation output must show both the raw normalized fields and the hash. The hash is runtime evidence and is not committed into the candidate it identifies.

The independent audit receipt, Holder Ready authorization, and Holder Merge authorization must bind the same runtime fingerprint. A change to repository, branch, Base SHA, Head SHA, or changed files immediately produces:

```text
AUDIT_BINDING: INVALID
READY_AUTHORIZATION: INVALID
MERGE_AUTHORIZATION: INVALID
```

Old audit or authorization cannot be silently rebound to a new candidate identity.

### Final realtime gate

Immediately before Ready or Merge, the control plane executes `PRE_MERGE_REALTIME_GATE` with the expected audit fingerprint and freshly resolves:

- repository;
- `origin/main`;
- `origin/<candidate_branch>`;
- current Head;
- Base ref and SHA;
- candidate branch and Head SHA;
- sorted changed files;
- workspace cleanliness;
- exact authorized scope coverage.

It must confirm Base is still `main`, Base SHA unchanged, Head unchanged, files unchanged, runtime fingerprint equals the expected fingerprint, workspace is clean, and actual changed files equal the authorized path list. Any mismatch is `HARD_STOP` and invalidates old audit, Ready authorization, and Merge authorization.

### CI gate

The control plane must verify live that:

- push CI is attached to the current source Head and succeeded;
- pull-request CI is attached to the current source Head and succeeded;
- static validation, complete tests, and live validation all actually ran;
- no required step was skipped or soft-failed;
- `continue-on-error` occurrences are zero.

CI success does not grant Ready or Merge authority.

## Audit receipt validation

Before registering a receipt, the Holder verifies task, authorization, repository, PR, `base_ref`, Base SHA, `head_ref`, Head SHA, sorted changed files, Checker identity, PR state, and candidate fingerprint. A transcription or target mismatch is `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH`; it is a receipt defect, not automatically a candidate defect, and it consumes no audit or repair budget.

A valid receipt becomes invalid as soon as any fingerprint field changes. A corrected receipt for unchanged candidate facts is a retry within the same gate. Authority conflict, scope violation, candidate drift, Checker conflict, runtime activation, or history rewrite remains fail-closed.

## Lightweight repair and merge safety

A non-blocking metadata defect does not justify a new PR. A real pre-audit candidate defect is repaired on the same branch. Scope expansion requires new Human authorization. Merge capability must be read live before presenting options. Merge-method capability mismatch alone may route to precise method reauthorization only when repository, PR, Base, Head, fingerprint, scope, state, mergeability, checks, and valid audit are unchanged.

## Runtime and automation boundaries

Persistent Holder runtime, Hermes R1, automatic scheduling, automatic merge, Persona, Memory, Token, Profile, Gateway, Feishu integration, memory bridge, and credential operations remain unimplemented and unauthorized unless separately adopted and explicitly activated.

## Adaptive counter-objective governance

Governance must not multiply candidates, duplicate state systems, or create formally correct but unnecessary work. When governance cost exceeds product or safety value, use the smallest safe path. Activity completion never equals product progress, and tooling work never inherits product acceptance.

## R1 preservation contract

Candidate Lifecycle R1 consolidates identity rules; it does not revoke existing
adopted governance outside an explicit conflict. The following earlier controls
remain normative and must be interpreted together with this file:

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

## ADT Roadmap

`docs/ADT_ROADMAP_P0_P5.md` 记录 P0–P5 路线图：各阶段目标、交付物、依赖、
状态、门禁和模型挡位分配。

### Read requirement

Every new Holder, Maker, or Checker receiving a task involving ADT governance
scope, deployment, or phase planning SHALL read
`docs/ADT_ROADMAP_P0_P5.md` during the mandatory startup protocol to
understand the current phase and NOT_AUTHORIZED boundaries.

### Authority

The roadmap is a reference document only. It does not grant execution
authority, override existing gates, or expand authorized write scope.
PLANNED ≠ AUTHORIZED ≠ IMPLEMENTED ≠ OPERATIONAL. Each phase requires
its own independent task: design → authorization → implementation →
audit → merge. A roadmap entry is not implementation authorization.
