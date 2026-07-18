# Adaptive Counter-Objective Governance

PROTOCOL_STATUS: `CANDIDATE_FOR_INDEPENDENT_REVIEW`
TASK_TYPE: `GOVERNANCE_PROTOCOL_UPGRADE`

This protocol is the adaptive extension of the Persistent Holder and
Lightweight Execution Flow. It is not a second routing system. Existing
Holder, Maker, Checker, receipt, audit, Human-only gate, and live-state rules
remain authoritative.

## Unified binding

`NO_UNBOUND_EXECUTION` is a global invariant. A task, child task, tooling
task, repair, candidate, or audit may not be dispatched, receive write
authority, create a formal candidate, Push, start a Checker, increase
product progress, or request Human acceptance without one valid binding.

The same `GOVERNANCE_BINDING_ID` passes unchanged through Holder, Maker,
Candidate, Checker, Human Gate, and Final Record:

```text
GOVERNANCE_BINDING_ID:
PARENT_TASK_ID:
PRIMARY_OBJECTIVE:
COUNTER_OBJECTIVE:
EXPECTED_PRODUCT_DELTA:
EVIDENCE_AUTHORITY:
BUDGET_CLASS:
STOP_CONDITIONS:
PRODUCT_PROGRESS_IMPACT:
HUMAN_ONLY_GATES:
```

Missing, drifting, or unresolvable fields produce
`GOVERNANCE_BINDING_INVALID` and fail closed. A binding never grants
authority by itself; explicit Human authorization, repository facts, scope,
and lease rules still apply.

## Counter-objective review

Before budget authorization, the Holder runs `COUNTER_OBJECTIVE_REVIEW`.
The default position is `EXECUTION_NOT_YET_JUSTIFIED`; the proposer carries
the burden of proof. The review records:

```text
REAL_PROBLEM:
CURRENT_HYPOTHESIS:
FALSIFICATION_TEST:
STRATEGY_VALIDITY:
CHEAPER_ALTERNATIVES:
MINIMUM_USEFUL_RESULT:
WHY_NOW:
NO_ACTION_EFFECT:
NON_PRODUCT_WORK:
CONTINUATION_VALUE:
SUNK_COST_EXCLUDED: YES
```

Only these decisions are valid:
`STRATEGY_ACCEPTED`, `STRATEGY_REDESIGN_REQUIRED`,
`EXECUTION_NOT_JUSTIFIED`, and `HUMAN_DECISION_REQUIRED`. Only
`STRATEGY_ACCEPTED` may proceed to execution budget authorization. Human
questions about direction, cost, necessity, or evidence trigger a new
counter-objective review.

## Execution budget gate

Strategy acceptance is not execution permission. Before Maker dispatch, the
Holder binds:

```text
BUDGET_UNIT:
MAX_BUDGET:
MAX_CANDIDATES:
MAX_TOOL_ATTEMPTS:
MAX_NON_PRODUCT_WORK:
EXPECTED_PRODUCT_DELTA:
FIRST_REVIEW_THRESHOLD:
HARD_STOP_THRESHOLD:
RESERVED_BUDGET:
ESTIMATION_BASIS:
AUTHORIZATION_RESULT: AUTHORIZED_TO_RUN | NOT_AUTHORIZED | HUMAN_AUTHORIZATION_REQUIRED
```

Budget may use a weekly percentage, cost class, candidate count, tool
attempts, or stages when exact tokens are unavailable. The estimate basis
must be stated; exact token usage must not be invented. “Continue until
success” is never authorization. Children inherit budget and cannot reset or
enlarge it.

## Dynamic governance profile

Exactly one profile is active at a time:

| Profile | Minimum control |
|---|---|
| `LIGHT` | Binding, objective, forbidden scope, stop conditions, receipt; no formal remote write |
| `STANDARD` | Holder, Maker, basic validation, Human-only Merge gate |
| `ENHANCED` | Counter review, budget, candidate limit, falsification, continuation review, Human product acceptance |
| `CRITICAL` | Full independent Maker/Checker chain, exact SHAs, rollback path, Human final decision |

The Holder outputs `GOVERNANCE_PROFILE`, `PROFILE_REASON`, and
`PROFILE_REVIEW_TRIGGER`. A higher profile replaces a lower profile; rules
are not blindly stacked. Governance work is not automatically Critical.

Upgrade triggers include a failed candidate, evidence conflict, scope
expansion, budget growth, new tooling, Human direction challenge, falling
root-cause confidence, debugging instead of implementation, a forbidden-scope
request, or missing product delta. Downgrade requires independent premise
confirmation, narrower scope, reversible work, resolved evidence conflict,
Human strategy acceptance, and rebound limits. Profile changes never reset
budget, failures, parentage, forbidden scope, Human-only gates, or product
baseline. An upgrade invalidates the old execution authorization.

## Continuation review

Pause as `SUSPENDED_FOR_COUNTER_REVIEW` when two candidates fail against the
same hypothesis, trusted and automated evidence conflict, tooling exceeds
product work, scope expands, a review threshold is reached, no bound product
delta appears, a Maker starts an unauthorized problem, a child diverges, a
Checker finds no independent premise validation, or Human repeatedly
challenges direction.

While paused, do not make another candidate, switch strategy automatically,
expand scope, create tooling, enter Checker, or consume the next budget
stage. Re-answer the problem, hypothesis, strategy, cheaper path, value of
continuation, and remaining budget for the minimum result. Resume only with
the existing binding and valid new authorization where required.

## Evidence authority

For visual work, evidence precedence is:

```text
Human normal-device interaction
> human recording or screenshot of that flow
> proven-equivalent automation
> direct-state/debug capture
> pixel sampling
> source/build/static inference
```

On conflict, the higher authority wins; product modification stops; the task
changes from `REPAIR` to `EVIDENCE_VALIDATION`; tooling failure is not a
product defect; repair resumes only after the highest-trust source reproduces
the issue. A Checker acceptance cannot override a false premise.

## Controlled exploration

Within the binding, Maker may perform read-only analysis, local temporary
experiments, option comparison, temporary diagnostics, and fast local
validation without step-by-step reauthorization. Exploration may not Push,
commit a formal candidate, expand files, change Main or Human-only gates, or
turn temporary tooling into a deliverable. Before formal candidate creation,
rebind exact solution, files, budget, and stop conditions.

## Child and tooling containment

When a product task needs a script, screenshot tool, test framework, or other
infrastructure, dispatch a separate `TASK_TYPE: TOOLING` task. It inherits
the binding, parent objective, counter-objective, evidence authority,
cumulative budget, stop conditions, forbidden scope, and Human-only gates,
but receives a separate budget, `PRODUCT_PROGRESS_IMPACT: NO`, and an
explicit `RETURN_CONDITION`.

Every child inherits the same fields. It may not widen the objective, change
the product source of truth, hide tooling work, reset budget or failures,
impersonate a new task, or bypass a parent pause. A paused parent pauses
unauthorized children.

## Maker, Checker, and product progress

Maker Dispatch adds the binding, strategy decision, profile, complete budget
authorization, candidate limit, allowed files, expected delta, stop
conditions, current consumption, and next review threshold. Maker Receipt
echoes the binding unchanged.

Checker reviews problem reality, strategy, budget and candidate limits,
unauthorized tooling, product value, evidence independence, stop triggers,
child containment, and profile fit in addition to technical correctness.
Checker decisions are:

```text
IMPLEMENTATION_ACCEPTED
STRATEGY_PREMISE_INVALID
BUDGET_VIOLATION
GOVERNANCE_BINDING_INVALID
PRODUCT_VALUE_NOT_ESTABLISHED
GOVERNANCE_OVERHEAD_EXCESSIVE
```

`ACTIVITY_COMPLETION` is not `PRODUCT_PROGRESS`. Failed candidates,
debugging documents, screenshot scripts, smoke tests, low-authority fixes,
wrong-target audits, and unrelated infrastructure add no product progress.
Progress increases only for a Human-visible capability, usable normal
interaction, real blocker removed, Human product/visual acceptance, or the
bound `EXPECTED_PRODUCT_DELTA`.

High-consumption receipts expose:

```text
BUDGET_STATUS:
BUDGET_CONSUMED:
PRODUCT_VALUE_GAINED:
FAILED_HYPOTHESES:
FAILED_CANDIDATES:
STRATEGY_CONFIDENCE:
CHEAPER_ALTERNATIVE:
CONTINUATION_JUSTIFICATION:
NEXT_REVIEW_THRESHOLD:
HARD_STOP_THRESHOLD:
```

## Governance overhead and circuit breaker

Governance overhead includes state cards, repeated protocol text, prechecks,
audits, role changes, evidence preparation, and tooling diagnosis. Target
ceilings are `LIGHT` minimal, `STANDARD` 10%, `ENHANCED` 20%, and `CRITICAL`
only as justified. Exceeding the target triggers
`GOVERNANCE_OVERHEAD_REVIEW` to merge steps, inherit fields, remove duplicate
Checkers, or downgrade only if safe.

Pause as `SUSPENDED_FOR_GOVERNANCE_SIMPLIFICATION` when state cards exceed
candidates, protocol text dominates implementation, a fact is checked more
than three times, Maker cannot understand the fields, Human cannot understand
the task, product has no visible change for two stages, overhead exceeds
budget, Agent judgment is replaced by waiting, or a simple task has three or
more roles. Return `HUMAN_SUMMARY`, `CURRENT_PRODUCT_VALUE`,
`UNNECESSARY_GOVERNANCE`, and `SIMPLIFIED_NEXT_STEP`.

## Human-facing minimum

Every critical Holder node uses the existing Human-facing interface and
includes machine fields plus a maximum three-sentence `HUMAN_SUMMARY`:
what is happening, why, and whether Human must act. It also includes
`USER_ACTION_REQUIRED`, precise `USER_ACTION` or `NONE`, `ACTION_REASON`,
`NO_ACTION_EFFECT`, `CURRENT_GATE`, and `SYSTEM_NEXT_STEP`. No percentage is
shown without a pre-bound progress plan and current-stage plan. Waiting does
not increase progress.

## Required examples

### LIGHT

```text
TASK_TYPE: DOCUMENTATION
GOVERNANCE_PROFILE: LIGHT
EXPECTED_PRODUCT_DELTA: corrected local wording
MAX_CANDIDATES: 1
PRODUCT_PROGRESS_IMPACT: NO
```

One binding, one local candidate, receipt, and no formal remote write.

### STANDARD

```text
TASK_TYPE: NORMAL_CODE_CHANGE
GOVERNANCE_PROFILE: STANDARD
EXPECTED_PRODUCT_DELTA: one user-visible behavior
HUMAN_ONLY_GATES: MERGE
```

Holder dispatches one Maker, basic validation runs, and Human decides Merge.

### ENHANCED

```text
TASK_TYPE: HIGH_COST_VISUAL_CHANGE
GOVERNANCE_PROFILE: ENHANCED
COUNTER_OBJECTIVE_REVIEW: STRATEGY_ACCEPTED
MAX_CANDIDATES: 1
EXPECTED_PRODUCT_DELTA: verified normal-device visual behavior
```

Trusted interaction evidence, budget thresholds, continuation review, and
Human product acceptance are required.

### CRITICAL

```text
TASK_TYPE: GOVERNANCE_BASELINE_CHANGE
GOVERNANCE_PROFILE: CRITICAL
EXPECTED_PRODUCT_DELTA: adopted protocol only
HUMAN_ONLY_GATES: FINAL_ACCEPTANCE, MERGE
```

Exact Base/Head, independent Maker and Checker, rollback path, and Human
final decision are mandatory.

### Automatic screenshot anomaly

```text
AUTOMATED_SCREENSHOT_RESULT: CONFLICTS_WITH_NORMAL_INTERACTION
ACTION: SUSPENDED_FOR_COUNTER_REVIEW
TASK_RECLASSIFICATION: EVIDENCE_VALIDATION
PRODUCT_MODIFICATION: FORBIDDEN
```

The tool anomaly is not registered as a product defect until the highest
trusted source reproduces it.

## Adoption boundary

This protocol changes governance documentation only. It does not implement
Holder runtime, scheduling, Hermes R1, automatic merge, permission changes,
product code, or a second task-routing system. Existing Human-only Ready,
Merge, branch deletion, final acceptance, and destructive-action gates remain
unchanged. PR10 remains a read-only source candidate.
