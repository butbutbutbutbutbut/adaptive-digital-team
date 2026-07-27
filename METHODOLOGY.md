# ADT Methodology

## What ADT is

ADT (Adaptive Digital Team) is a **governance tool system and control plane** — a
set of protocols, validators, and reusable checks that help humans and AI agents
work together safely on multi-agent projects.

ADT provides:

- **Repository-as-prompt** — every fresh agent window reads durable governance
  documents before acting; the repository is the single source of truth.
- **Role separation** — Maker and Checker are independent contexts with distinct
  evidence paths; no role self-audits or self-accepts.
- **Scope enforcement** — every task carries an exact authorized file list;
  drift beyond scope fails closed.
- **Fingerprint binding** — every candidate has a deterministic SHA-256 identity
  that binds repository, Base, Head, and changed files.
- **Fact/action separation** — machine facts cannot be changed through language;
  action authority requires explicit Human authorization.
- **Adaptive counter-objective** — governance must never cost more than the task
  or product value it protects.

ADT defines *how* humans and agents coordinate safely. It does not define *what*
they build.

## What ADT is not

ADT is **not**:

- A product build system or deployment pipeline
- A runtime engine or task scheduler
- A single AI personality or agent identity
- A memory management or conversation persistence layer
- An automatic merge or auto-deploy system
- A replacement for human judgment or accountability

ADT governs the governance layer. Product repositories, runtime infrastructure,
deployment targets, and agent identities are defined and owned separately.

## Replaceability

Every component inside ADT is designed to be replaceable:

- **Tools** — any tool (GitHub CLI, Git, CI platform, terminal) can be swapped
  for an equivalent that provides the same verifiable facts.
- **Models** — any AI model capable of reading protocols and producing verifiable
  output can serve as Maker, Checker, or Holder.
- **Accounts** — GitHub accounts, CI service accounts, and cloud credentials are
  external bindings, not hard-coded identities.
- **Personas** — the Anding interface identity is a convention, not a requirement.
  Any persona that follows the protocol is a valid participant.

Replaceability ensures ADT is not locked to any specific vendor, model, or
operator.

## Governance ceiling

Governance work must never exceed the value of the task or product it protects.

When governance cost exceeds product or safety value, use the smallest safe
path. Activity completion never equals product progress. Tooling work never
inherits product acceptance.

This adaptive counter-objective is not an escape hatch — it is a design
constraint baked into every gate. If a governance step adds friction without
proportional safety gain, the system must route to the lighter path.

### Adaptive counter-objective gate

The gate runs silently at task intake and every material re-route. It costs zero
Point and produces no standalone receipt. Its outputs are fields on the existing
`GovernancePlan`; it does not create a second protocol or state system.

The gate applies these rules:

1. **Do not mechanically agree.** Every material Human premise is classified as
   `SUPPORTED`, `PARTIAL`, `REJECTED`, or `UNVERIFIED`. Agreement language cannot
   substitute for evidence or judgment.
2. **Do not expand the objective.** Read, analysis, review, and decision requests
   remain non-writing tasks unless the Human explicitly authorizes repair or
   repository mutation.
3. **Continue by default.** The same task uses `CONTINUE` and restores only the
   delta. `RESTART` is justified only by role isolation, invalidated fact source,
   context contamination, or an explicit Human request. An unsupported restart
   is `RESTART_REJECTED`.
4. **Separate risk from resources.** `SAFETY_RISK`, `RESOURCE_TIER`, and
   `CHECKER_TIMING` are independent decisions. HIGH safety risk does not itself
   require a strong model or an early Checker. CRITICAL governance modification
   defaults to `strong` unless the Human binds another valid tier.
5. **Delay Checker allocation.** A Checker is configured only after a formal
   candidate exists. Local production may declare `AFTER_FORMAL_CANDIDATE`, but
   it receives no Checker allocation yet.
6. **Respect Human ceilings.** Point, approximate token, Checker, message, and
   scope boundaries fail closed. When governance cost exceeds task value, output
   `DOWNSCOPE`, reduce the plan to the smallest safe path, and stop at the Human
   boundary rather than silently spending more.
7. **Treat friction as a control signal.** When the Human restates or narrows the
   task, restore the latest explicit authorization, shorten external messages,
   and drop inferred scope.

The frozen plan fields and executable rules are defined in
`schemas/governance-plan.schema.json`, `scripts/route_task.py`, and
`scripts/resource_allocator.py`. This section is the single methodology source;
other documents only describe their entry-point obligations.

## Status

All candidates governed by this methodology carry exactly one status:

```
CANDIDATE_FOR_INDEPENDENT_REVIEW
```

Until an independent Checker audits and the Human Holder accepts, no candidate
is Ready, Merged, or Accepted. There is no implicit progression and no automatic
state transition.

## Where to find details

This document defines the methodology baseline. Detailed protocols live in:

| Document | Contains |
|----------|----------|
| `governance/ROLE_MODEL.md` | Complete role topology, authority matrix, separation rules |
| `governance/AUTHORITY_AND_FACTS.md` | Fact authority, action authority, FACT_SOURCE_REBIND |
| `AGENTS.md` | Agent-facing rules, candidate lifecycle, CI gates |
| `protocols/*.md` | Detailed protocol specifications |

Git, PR, CI, fingerprint, and scope algorithms are defined in `AGENTS.md` and
`protocols/` — they are not duplicated here. Specific role behaviors are
defined in `governance/ROLE_MODEL.md`.
