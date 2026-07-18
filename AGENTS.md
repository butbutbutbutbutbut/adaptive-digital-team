# Agent Governance

- Maker and Checker responsibilities must remain separate.
- Self-acceptance is forbidden.
- Automatic merge is forbidden.
- Do not reset, force-push, or amend a submitted candidate.
- Do not commit secrets, private material, or unapproved binary assets.
- After the initial bootstrap commit, every change must use a separate branch and pull request.
- Rollback must use a new revert branch and a reviewed revert commit.
- Missing authority, state conflicts, or incomplete evidence must fail closed.

## Multimodal evidence

Metadata integrity does not establish semantic evidence acceptance.

When a claim depends on images, audio, video, traces, or other external
binaries, the independent Checker must obtain and review the actual
evidence modality before acceptance or merge authorization.

Missing binary access or unperformed modal review fails closed and
cannot be downgraded to a recorded limitation.

## Instruction routing and authority

All cross-Agent, cross-window, cross-repository, repository-write,
audit, and merge instructions must follow
`protocols/INSTRUCTION_ROUTING_AND_AUTHORITY.md`.

Missing or conflicting FROM, TO, EXECUTOR, CHECKER, REPOSITORY, or
AUTHORIZATION_ID fields fail closed.

CC status grants no execution, acceptance, audit, or merge authority.

Maker, Checker, PR-creation authority, evidence acceptance, and merge
authority must remain distinct.

## Persistent Holder adopted governance specification

`protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` is a
`ADOPTED_GOVERNANCE_SPECIFICATION`. The Persistent Holder is the resident
control-plane interface and Task Router, not a third Maker. Makers and
Checkers are temporary task roles; the Holder may be Checker only when the
independence test in that protocol passes.

The Holder routes publication but does not Push directly. A task-scoped
Publish Lease cannot expand its parent authorization. Ready, Merge, branch
deletion, final acceptance, and final visual or engineering acceptance are
Human-only. PR10 is a read-only source candidate and must not be merged,
cherry-picked, updated, closed, or deleted.

Persistent Holder runtime, Hermes R1, and automatic scheduling remain
unimplemented and unauthorized.

## Human-facing control-plane interface

### Purpose

All control-plane feedback directed at Human must satisfy five requirements:

1. Preserve exact machine fields, status values, SHAs, and authorization IDs.
2. Provide readable explanation in the user's current language.
3. This project defaults to Simplified Chinese（简体中文）annotations.
4. Make explicit whether the user must act right now.
5. Never require the user to infer gates, blocks, or next steps on their own.

### Context-sensitive priority（上下文敏感判定优先级）

`USER_ACTION_REQUIRED` must be decided based on actual tools, permissions,
connectors, received receipts, and recovery paths available in the current
execution environment. No gate may have an unconditional YES or NO.

Gate-specific defaults in protocol files are conditional starting points
only. Actual tool availability, received evidence, permissions, and
recovery paths override any node default. When the environment cannot be
determined, the system must diagnose before making a user-action claim.

### Evidence-before-status（证据先于状态）

Execution status claims require evidence:

- `PLANNED`: action is intended but not yet dispatched.
- `DISPATCHED / EXECUTION_NOT_YET_VERIFIED`: task sent to executor but no
  receipt, tool result, or connector confirmation has been received.
- `RECEIPT_RECEIVED`: a receipt has been returned but its content has not
  yet been independently verified.
- `EXECUTION_VERIFIED`: the receipt content has been independently
  confirmed against live facts.
- `COMPLETED`: verified execution with final result registered.

Without tool invocation, connector result, or receipt evidence, the system
must not claim: Maker begins, Checker begins, system continues
automatically, or task is running in background. SYSTEM_NEXT_STEP
describing a future plan must use future semantics and must not be
written as a fact already in progress.

### Per-round repair statement（本轮修复）

The title "本轮修复" is fixed. It describes the current governance gap,
fact uncertainty, process issue, or candidate defect being resolved. It
does not automatically imply that candidate files are being modified.

At the start of each new governance round, action phase, or gate phase,
the system must first output a repair statement covering four items:

- 正在修什么（what is being fixed）
- 为什么要修（why it needs fixing）
- 修完后解决什么风险（what risk is resolved after repair）
- 本轮不处理什么（what this round does NOT handle）

None of the four items may be omitted. Content must be specific to the
current round — generic templates are not acceptable. "本轮不处理什么" must
prevent the user from mistakenly assuming that related tasks are also in
progress. This statement applies before GitHub write operations, Human-only
gates, audits, repairs, and block handling.

During audit, fact-verification, Ready, Merge, and result-registration
phases where no verified new commit exists, the statement must explicitly
include: "候选内容未修改". Only when a verified commit or Head change is
present may the statement claim candidate content has been modified.

ACTION and RESULT fields must distinguish:

- planned action（计划动作）
- executed action（已执行动作）
- verified result（已验证结果）

An action that has been planned but not yet executed must not be reported
as a result.

### Key-node Chinese annotation format（关键节点中文注释）

The following nodes are critical and must include both machine fields and
Chinese explanation:

- Dispatch（分派）
- Progress Receipt（进度回执）
- Target-Fact Validation（目标事实核验）
- Audit Receipt（审计回执）
- Invalid Audit Receipt（无效审计回执）
- Blocking Finding（阻塞发现）
- Incremental Repair（增量修复）
- Ready Decision（就绪决定）
- Merge Capability Preflight（合并能力预检）
- Merge Decision（合并决定）
- Merge Result（合并结果）
- Branch Deletion Decision（分支删除决定）
- Task Completion（任务完成）
- Fail-Closed / Capability Unknown / State Drift（失败关闭 / 能力未知 / 状态漂移）

Recommended format for each critical node:

```
FACT（事实）
AUTHORITY（授权边界）
ACTION（当前动作）
RESULT（结果）
TASK_PROGRESS（任务进度）
CURRENT_STAGE_PROGRESS（当前环节进度）
PROGRESS_BASIS（进度依据）
PROGRESS_BLOCKER（阻塞项）
CURRENT_GATE（当前门禁）
USER_ACTION_REQUIRED（用户是否需要操作）
USER_ACTION（用户现在需要操作）
ACTION_REASON（为什么需要操作）
NO_ACTION_EFFECT（不操作会怎样）
SYSTEM_NEXT_STEP（系统下一步）
```

### USER_ACTION_REQUIRED（mandatory field）

Every critical node must output:

```
USER_ACTION_REQUIRED: YES | NO
USER_ACTION: <precise action; must be NONE when not required>
ACTION_REASON: <the Human-only gate, authorization gap, or external
               resource requirement behind this action>
NO_ACTION_EFFECT: <the actual state if the user takes no action>
SYSTEM_NEXT_STEP: <what the Holder, Maker, Checker, or system does next>
```

Never output only `NEXT_GATE` and leave the user to infer the rest.

### USER_ACTION_REQUIRED decision rules

Set to YES only when:

- Human-only Ready（就绪）
- Human-only Merge（合并）
- branch deletion（分支删除）
- final visual / engineering acceptance（最终验收）
- scope, authority, or high-risk action authorization（范围/授权/高风险动作）
- an external action that must be performed manually by the user
- the current system lacks tools or permissions and the action is genuinely
  necessary

Set to NO when:

- Maker is executing an already-authorized task
- Checker is performing read-only audit
- Holder is performing live fact verification
- waiting on GitHub status or CI
- the system already has authority to continue a non-risky action
- the user does not need to provide new judgment or new authorization

Never present "waiting" as a user action.

### Executable user actions（可直接执行）

Prohibited vague expressions:

- "请确认"（please confirm）
- "请处理"（please handle）
- "下一步需要授权"（next step requires authorization）
- "请选择是否继续"（please choose whether to continue）

Authorization requests must bind the relevant facts precisely:

- repository
- PR
- exact Head SHA
- exact action
- exact merge method
- branch deletion decision
- scope or risk boundary

The user must be able to copy the authorization or reply with an explicit
yes/no to a precisely-scoped request.

### Real executable options only（真实可执行选项）

Before presenting Merge method, Ready, branch deletion, or other
capability options:

- verify target facts and capabilities live
- do not present options the repository does not currently enable or
  cannot currently execute
- when capability cannot be read:
  `CAPABILITY_UNKNOWN / FAIL_CLOSED`
  with Chinese blocking reason and user action status

### Error and block human-readable translation（错误阻塞翻译）

Never output only an error code. Distinguish:

- `INVALID_AUDIT_RECEIPT`
  中文：审计目标或 Checker 身份无效，不代表候选实现失败。

- `CANDIDATE_FAILURE`
  中文：候选实现本身存在阻塞问题。

- `MERGE_METHOD_CAPABILITY_MISMATCH`
  中文：仓库拒绝了指定合并方式，但候选和有效审计未失效。

- `STATE_DRIFT`
  中文：Base、Head、PR 状态、范围或检查条件已变化，旧授权不能继续使用。

- `CAPABILITY_UNKNOWN`
  中文：无法可靠读取当前仓库能力，流程停止且不猜测。

### Information density control（信息密度）

The chat window retains only:

- current conclusion
- exact SHAs, PR, state
- blocking items
- user action
- system next step

Long logs, full patches, repeated evidence, and process details go into:

- Progress Receipt
- Audit Receipt
- PR body
- repository documents
- traceable evidence files

Do not bury the current gate and user action under long logs.

### No fabricated background execution（不得虚构后台执行）

The protocol must be explicit:

- when no tool has been called and no execution receipt has been received,
  do not claim a task is "running in the background"
- when a task has been dispatched but no evidence has been received, write:
  `DISPATCHED / EXECUTION_NOT_YET_VERIFIED`
- user action required status must reflect this accurately

### Durable vs live state separation

Stable feedback rules and field definitions are recorded in the repository.

The following are live control-plane state and must never have their
momentary values written as durable facts:

- current Gate
- current USER_ACTION
- current PR state
- current Head
- current blocking items
- current system next step
- current repository capabilities
- current TASK_PROGRESS percentage
- current CURRENT_STAGE_PROGRESS percentage
- current PROGRESS_BASIS
- current PROGRESS_BLOCKER
- current PROGRESS_PLAN and CURRENT_STAGE_PLAN completion state

### Verifiable task progress（可核验任务进度）

All Human-facing critical nodes must output verifiable dual-layer progress
with the four fields listed above.

#### Progress plan binding（进度计划先绑定）

Before a numeric percentage can appear, finite, explicit, ordered
`PROGRESS_PLAN` and `CURRENT_STAGE_PLAN` must exist. These are live
control-plane state and may be recorded in the Dispatch Card, Task
State Card, or execution receipt.

If total gates or current-stage verification units are not yet bound:

```
TASK_PROGRESS: UNKNOWN
CURRENT_STAGE_PROGRESS: UNKNOWN
```

The denominator must not be guessed.

#### Calculation rules（计算规则）

Numeric progress is computed as:

- Only units confirmed by tools, connectors, valid receipts, or
  independent verification count as complete.
- `PLANNED` does not count as complete.
- `DISPATCHED / EXECUTION_NOT_YET_VERIFIED` does not count as complete.
- `RECEIPT_RECEIVED` but not yet verified does not count as complete.
- Only `EXECUTION_VERIFIED` or formally registered Human decisions count.
- Equal-weight verification units are used.
- Percentage: `floor(verified_units * 100 / total_bound_units)`
- Ten-block bar filled blocks: `floor(percentage / 10)`
- 100% may be shown only after every in-task gate is complete and Task
  Completion is registered.

Do not self-weight to make progress "appear closer to done."

#### Current-stage progress（当前环节进度）

`CURRENT_STAGE_PROGRESS` uses pre-bound verification units internal to
the current gate.

Example gates and their pre-bound units (ILLUSTRATIVE_ONLY):

- Dispatch stage: Packet prepared, Dispatch confirmed
- Audit stage: Checker independence verified, target facts verified,
  file scope verified, decision registered

Units must be bound before the stage begins, not reverse-selected after
completion.

#### Waiting does not auto-increment（等待不会自动增长）

While waiting on GitHub, CI, Maker, Checker, or Human:

- Progress stays frozen.
- Do not increment by elapsed time.
- Do not claim "processing in background."
- `PROGRESS_BLOCKER` may record `WAITING_ON_*`.
- `WAITING_ON_*` is not `CANDIDATE_FAILURE`.
- `USER_ACTION_REQUIRED` is decided by existing context-sensitive rules.

#### Progress may decrease, but must explain（进度允许下降但必须解释）

Recalculation and decrease are permitted when:

- Human explicitly expands scope.
- Base / Head or target facts undergo valid rebinding.
- A newly authorized gate is added.
- A valid audit finding requires fix + re-review stages.

Output required:

```
PROGRESS_RECALCULATED: <old>% -> <new>%
RECALCULATION_REASON: <exact reason>
```

Do not silently modify the denominator or percentage.

Authority drift, unauthorized scope change, or state drift must still
fail closed and must not be absorbed through progress recalculation.

#### PROGRESS_BASIS anti-black-box（进度依据防黑箱）

`PROGRESS_BASIS` must not contain only:

- `estimated`
- `nearly complete`
- `most work done`
- `almost finished`

It must include at minimum:

- verified units numerator
- bound total denominator
- completed gate/unit names
- pending gate/unit names

Long lists may go to the Receipt or PR body, but the chat must retain
the numeric basis and current blocker.

#### Progress visualization（进度可视化）

Each progress field must include both the machine-readable value and a
Simplified Chinese explanation with a ten-block visual bar. Example
(ILLUSTRATIVE_ONLY):

```
TASK_PROGRESS: 80%
CURRENT_STAGE_PROGRESS: 0%

当前任务  [████████░░] 80% — 4/5 个门禁已验证
当前环节  [░░░░░░░░░░] 0%  — 等待独立审计回执
```

The machine field and Chinese display must not contradict each other.

#### Progress and existing gates（进度与现有门禁）

Progress percentages are informational. They must not be treated as:

- substitutes for acceptance
- substitutes for audit pass
- substitutes for Ready
- substitutes for Merge

All existing Human-only and fail-closed gates remain unchanged.

### Existing authority and safety boundary preservation

This interface section must not:

- expand Holder, Maker, or Checker authority
- permit Maker self-acceptance
- permit Checker write operations
- lower Human-only Ready / Merge / branch deletion
- activate Runtime
- authorize Hermes R1
- enable automatic scheduling
- enable automatic merge
- modify existing merge capability preflight safety rules

## Lightweight execution routing

Use `protocols/LIGHTWEIGHT_EXECUTION_FLOW.md` for L0/L1/L2 routing. L0
defaults to one Maker, one independent Checker, and one final Human decision.
Non-blocking metadata must be recorded as a limit and must not create a new
commit loop. Human-only Ready, Merge, branch deletion, final acceptance, and
runtime activation remain unchanged.

## Audit receipt validation

Audit receipts must be validated against the exact target facts (`TASK_ID`,
`AUTHORIZATION_ID`, repository, PR, exact Base, exact Head, Checker
identity, current PR state) before any state registration, per
`protocols/PERSISTENT_HOLDER_CONTROL_PLANE.md` and
`protocols/LIGHTWEIGHT_EXECUTION_FLOW.md`.

A target-fact mismatch is `INVALID_AUDIT_RECEIPT / TARGET_FACT_MISMATCH`:
the receipt is rejected without changing candidate state, consuming audit or
repair budget, triggering repository repair or a full audit rerun, or moving
any gate. Checker input errors are receipt defects, not candidate defects.
A corrected receipt is a receipt retry within the same gate, not a new full
audit, and non-permission receipt errors do not require new Human
authorization. Authority, scope, Base/Head drift, Checker conflict, Runtime,
and history-rewrite violations remain fail-closed.

## Merge method capability preflight

### Branch sync vs. final merge

`BRANCH_SYNC_METHOD` and `PR_FINAL_MERGE_METHOD` are distinct.

`allow_merge_commit`, `allow_squash_merge`, and `allow_rebase_merge` are
GitHub Pull Request final merge method settings. They control how GitHub
merges a PR into the target branch via the PR Merge API. They do not control
ordinary git operations on the feature branch.

`allow_merge_commit=false` means GitHub will not offer or execute a merge
commit when merging the PR. It does not forbid a developer from running
`git merge <target>` on the feature branch to produce an ordinary merge
commit for branch synchronization.

`BRANCH_SYNC_METHOD` must not be treated as `PR_FINAL_MERGE_METHOD`, and
vice versa. Branch sync operations (bringing target changes into the feature
branch during development) and PR final merge (closing the PR into the
target branch) are separate action classes. They must be separately
authorized and separately verified.

### Pre-authorization verification

Before requesting Human authorization for `PR_FINAL_MERGE_METHOD`, the
Holder or its delegate must verify live repository facts:

- repository identity
- PR number and state (must be OPEN)
- exact Base SHA
- exact Head SHA
- mergeability (`MERGEABLE`, `UNKNOWN`, or `CONFLICTING`)
- enabled PR merge methods (from repository settings)
- required checks and protection rules (when accessible)

Only the target repository's currently enabled PR merge methods may be
presented to Human. Disabled or unavailable methods must not appear as
options.

### Merge capability unknown

When merge capability cannot be read from the repository (API failure,
insufficient permissions, ambiguous response) or when enabled methods
conflict with each other:

`MERGE_CAPABILITY_UNKNOWN / FAIL_CLOSED`

Do not proceed to Human authorization. Do not default to any merge method.
Do not guess.

### Merge authorization binding

A PR final merge authorization must precisely bind:

- repository
- PR number
- exact Head SHA at time of authorization
- exact PR merge method (one of the currently enabled methods)
- branch deletion decision (delete / retain after merge)

Any drift in these bindings between authorization and execution fails closed.

### Pre-execution re-verification

Immediately before calling the PR Merge API, re-verify live facts:

- repository identity
- PR identity
- exact Base SHA
- exact Head SHA
- PR state
- mergeability
- the authorized merge method is still enabled in repository settings
- applicable required checks
- applicable branch-protection and permission facts (when accessible)

If any authorized binding fact has changed since authorization, stop and
fail closed. Do not proceed to merge.

### Merge method capability mismatch

`MERGE_METHOD_CAPABILITY_MISMATCH` applies only when ALL of the following
facts remain unchanged since authorization:

- repository identity
- PR identity
- Base SHA
- Head SHA
- scope (files and actions in authorization)
- candidate files and their content
- PR state
- mergeability
- a valid independent audit conclusion bound to the exact Head SHA

When repository policy rejects the authorized merge method but all the
above facts are unchanged:

- candidate state is unchanged
- valid independent audit conclusion remains valid
- audit budget is not consumed
- repair budget is not consumed
- repository repair is not triggered
- a full audit rerun is not triggered
- the candidate does not enter a failure gate

The situation routes to `HUMAN_MERGE_METHOD_REAUTHORIZATION` only. The
new authorization may only replace the exact merge method with a different
enabled method. It must not expand any other permission, scope, or gate.

### Drift (not eligible for lightweight re-authorization)

The following changes are genuine drift. None of them may use
`HUMAN_MERGE_METHOD_REAUTHORIZATION` or any lightweight path:

- repository change
- PR identity change
- Base drift (Base SHA differs from authorization)
- Head drift (Head SHA differs from authorization)
- scope change (files or actions outside authorization)
- candidate file change or candidate content change
- PR state change (e.g. CLOSED, MERGED, converted from Draft)
- mergeability change
- permission change
- required-check change
- branch-protection change

When any of the above occurs, stop. Do not silently rebind the old
authorization. Return to the appropriate fact-verification, audit, or
Human gate for the changed fact.

### Merge settings as live facts

The following are live control-plane facts, read from the repository at
execution time. They are not durable repository state and must never be
written to committed files, the PR body, or any durable record as
authoritative bindings:

- enabled PR merge methods (`allow_merge_commit`, `allow_squash_merge`,
  `allow_rebase_merge`)
- PR mergeability
- required status checks
- branch-protection rules
- applicable merge permissions

Each merge-capability gate must re-read these facts live. Stale cached
values are not authoritative.

### Runtime and automation boundaries

Automatic merge, Hermes R1, and automatic scheduling remain unauthorized.
Merge capability preflight is a pre-authorization verification step, not a
Runtime activation.

## Adaptive counter-objective governance

`protocols/ADAPTIVE_COUNTER_OBJECTIVE_GOVERNANCE.md` is the adaptive
extension of this canonical Holder and Lightweight Flow, not a parallel
governance system. Every task, child, tooling task, repair, candidate, and
audit must carry one valid `GOVERNANCE_BINDING_ID`; missing or drifting
fields fail closed as `GOVERNANCE_BINDING_INVALID`.

Before Maker dispatch, `ENHANCED` or `CRITICAL` work requires
`COUNTER_OBJECTIVE_REVIEW: STRATEGY_ACCEPTED` and a separate execution
budget authorization. Exactly one of `LIGHT`, `STANDARD`, `ENHANCED`, or
`CRITICAL` is active. Profile changes do not reset budget, failed candidates,
parentage, Human-only gates, forbidden scope, or product baselines.

Evidence conflict, repeated failure, scope expansion, tooling drift, or
missing product delta triggers `SUSPENDED_FOR_COUNTER_REVIEW` and
fail-closed stopping. Tooling is a separate inherited child task with its
own budget and `PRODUCT_PROGRESS_IMPACT: NO`; activity completion never
equals product progress.

Governance overhead is budgeted and may trigger
`SUSPENDED_FOR_GOVERNANCE_SIMPLIFICATION`. Human-facing critical nodes retain
the existing structured fields, precise user-action decision, and
three-sentence summary. This protocol does not activate Runtime, Hermes R1,
automation, or any Human-only gate.
