# ADT Public Core / Private Ops / Secrets Boundary

Status: `ADOPTED_BOUNDARY_SPECIFICATION`

This document defines the boundary between the three layers of the Adaptive Digital
Team system. It is the canonical reference for what lives where and why.

---

## Layer 1 — PUBLIC CORE

**Repository:** `adaptive-digital-team` (public)

This is the governance toolkit. Anyone can fork it, run the validator, run the tests,
and submit a PR.

### What belongs here

| Category | Examples |
|----------|----------|
| Governance protocols | `protocols/*.md` — Holder, Maker, Checker, bootstrap, closeout, routing |
| Validator | `scripts/validate_binding.py` |
| Test suite | `tests/test_binding_validation.py`, `tests/run_tests.py` |
| Schemas | `schemas/*.yaml` |
| CI workflow | `.github/workflows/validate.yml` |
| Public documentation | `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` |
| Roadmap | `docs/ADT_ROADMAP_P0_P5.md` — what is planned vs authorized |
| Boundary spec | This file |
| Configuration template | `config.example.yaml` — placeholders only, no real values |
| License | `LICENSE` |

### What does NOT belong here

- Real credentials, tokens, API keys, or passwords
- Deployed instance configuration (which server, which account, which webhook URL)
- Personal memory backups or personality data
- Private project case studies with real names, URLs, or SHAs of private repos
- Internal operations runbooks with staff names and schedules
- Any `.env` file or file containing a real secret

---

## Layer 2 — PRIVATE OPS

**Repository:** `adaptive-digital-team-ops` (private)

This is the manager's operations repository. It contains the running state of an ADT
deployment — what is actually configured, connected, and active.

### What belongs here

| Category | Examples |
|----------|----------|
| Deployment architecture | Which services run where, on which machines or cloud accounts |
| Instance configuration | `config.yaml` with real repository names, account IDs, webhook URLs |
| Runbooks | Step-by-step operational procedures with real service names |
| Internal case studies | Audit reports and post-mortems that reference real projects |
| Contact and routing | Who the Human Holder is, how to reach them (private channels only) |
| Scheduled task definitions | Cron job specs, automation schedules |
| Historical台账 | Task logs, decision records, authorization receipts |

### What does NOT belong here

- Secrets (tokens, keys, passwords) — those go in Layer 3
- Public governance protocols — those stay in Layer 1
- Any material that would be safe to open-source

---

## Layer 3 — SECRETS / VAULT

**Location:** GitHub Secrets, environment variables, external vault (1Password, HashiCorp Vault, etc.)

This is the encrypted credential store. It is never committed to any repository.

### What belongs here

| Category | Examples |
|----------|----------|
| API keys | OpenAI, Anthropic, DeepSeek provider keys |
| GitHub tokens | PATs for cross-repo access, `GITHUB_TOKEN` in CI |
| Feishu credentials | App ID, App Secret for bot integration |
| Encryption keys | Keys for memory snapshot encryption |
| Gateway tokens | Hermes Gateway authentication tokens |
| Webhook secrets | Signing secrets for incoming webhooks |

### Rules

- Secrets are injected at runtime via environment variables or CI secrets.
- They are never written to disk in plaintext outside a secure enclave.
- If a secret is accidentally committed, it is immediately revoked and rotated —
  not just removed from the commit history.
- The `config.example.yaml` in the public core shows the *names* of required
  secrets (so forkers know what to configure) but contains only `${PLACEHOLDER}`
  values.

---

## Layer B — PROJECT REPOSITORIES

**Location:** Individual GitHub repositories (one per project)

Project repositories are separate from the ADT governance system. They contain
application code, design assets, product configurations, and their own CI/CD.

ADT governance references project repos by commit SHA and PR number — it does not
clone, modify, or control them. The relationship is:

```text
ADT Public Core  ──references──→  Project Repo (commit SHA, PR #)
ADT Private Ops  ──knows about──→  Project Repo (deployment targets)
ADT Secrets      ──never touches─→  Project Repo
```

Project repositories remain under their own access control. Making ADT public
does not make any project repository public.

---

## Boundary enforcement

The validator enforces part of this boundary at the file level:

- `authorized_write_scope` in `PROJECT_STATE.md` declares exactly which files a
  task may touch.
- Files outside scope cause `SCOPE_VIOLATION`.
- The public core's `.gitignore` blocks common secret file patterns (`.env`,
  `*.pem`, `*.key`, `credentials.*`).

The rest of the boundary — what goes into Ops vs Secrets vs stays in Core — is
enforced by Human review at PR time, not by automation.

---

## Relationship to 安鼎 Agent

安鼎 Agent is the Persistent Holder — the manager persona. It is not a repository.

```text
安鼎 Agent:
  ├── reads PUBLIC CORE for protocols and rules
  ├── reads/writes PRIVATE OPS for operational state
  ├── accesses SECRETS at runtime (never persisted)
  └── references PROJECT REPOS by SHA/PR (never modifies directly)
```

The Agent persona, its memory, and its credentials are not part of any public
repository. The public core is the Agent's *toolkit*, not its identity.
