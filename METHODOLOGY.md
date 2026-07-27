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
