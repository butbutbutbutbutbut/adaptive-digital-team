# Adaptive Digital Team（自适应数字团队|ADT）

The governance root for the Adaptive Digital Team (ADT).

ADT is a **governance tool system and control plane** — a set of protocols, validators,
and reusable checks that help humans and AI agents work together safely on multi-agent
projects. It is not a runtime, not a scheduler, and not a single AI personality.

## What ADT provides

- **Repository-as-prompt** — durable context that any fresh agent window reads before acting
- **Maker/Checker separation** — independent implementation and audit roles
- **Candidate state machine** — from LOCAL_DRAFT through FORMAL_CANDIDATE to AUDIT_ELIGIBLE
- **Scope enforcement** — every task has an exact authorized file list; drift fails closed
- **Fingerprint binding** — deterministic SHA-256 identity for every candidate
- **Pre-write execution gate** — branch, Base, ancestry, and scope validated before any commit
- **Human-facing evidence cards** — machine facts + Simplified Chinese explanation at critical nodes
- **Adaptive counter-objective controls** — governance must never cost more than product value

## Key boundary — 安鼎 (Anding) Agent ≠ ADT repository

- **安鼎 Agent** is the Persistent Holder — the manager persona that calls ADT tools
- **ADT repository** is the public governance toolkit: protocols, validator, tests, schemas
- The Agent is not the tools; the tools do not become the Agent

## Roles

| Role | Who | Authority |
|------|-----|-----------|
| **Human Holder** | Human project owner | Direction, authorization, final acceptance, Ready, Merge |
| **Persistent Holder Agent** | 安鼎 | Maintain fact source, route tasks, validate receipts |
| **Maker** | Temporary, task-scoped | Implement exactly the authorized task on the authorized branch |
| **Independent Checker** | Temporary, read-only | Independently audit a candidate it did not create |

## Three-layer architecture

| Layer | Repository | Contents |
|-------|-----------|----------|
| **PUBLIC CORE** | `adaptive-digital-team` (this repo) | Protocols, validator, tests, schemas, CI — everything needed to fork and run |
| **PRIVATE OPS** | `adaptive-digital-team-ops` (private) | Runtime台账, deployment instances, account bindings, environment configuration |
| **SECRETS / VAULT** | GitHub Secrets, external vault | Tokens, passwords, encryption keys, decryption material |
| **PROJECT REPOS** | Individual project repos | Actual applications, products, design assets — separate from governance |

Public architecture design does **not** mean public credentials or private memories.

## Quick start

```bash
# Clone
git clone https://github.com/butbutbutbutbutbut/adaptive-digital-team.git
cd adaptive-digital-team

# Install dependencies (Python 3.11+)
pip install pytest pyyaml

# Run validator (static mode — no Git or CI context needed)
python scripts/validate_binding.py

# Run test suite
python tests/run_tests.py
```

## Current roadmap

| Phase | Status |
|-------|--------|
| P0 — Operational Baseline | `OPERATIONAL_BASELINE` / `CONTINUING_MAINTENANCE` |
| P1–P3 — Dynamic Governance R1 | `PLANNED` / `NOT_AUTHORIZED` |
| P4 — Public Release Readiness | `DESIGN_BASELINE_PARTIAL` / `IMPLEMENTATION_NOT_AUTHORIZED` |
| P5 — ADT Ops Org Bootstrap | `PLANNED` / `NOT_AUTHORIZED` |

**Making this repository public does not authorize any P1–P5 implementation.**
Every phase requires separate Human authorization with exact repository, branch, Base, and scope.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). One task = one branch = one PR targeting `main`.
No stacked PRs, no force-push, no self-acceptance.
