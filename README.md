# Adaptive Digital Team

> 你把 ADT 仓库链接发给 AI 之后，它会根据你的情况给你最合适的入口。

---

## 发给 AI 这个链接，你会看到

**如果只发了链接、没有说具体要做什么：**

AI 只会回复三个选项：

```text
A｜直接开始
B｜我会上传文件
C｜连接我自己拥有或管理的项目仓库
```

**如果附带说了要做什么：**

AI 会**自动跳过菜单**，直接开始处理你的任务——不管是聊天、处理文件、还是连接仓库。

| 你发的消息里带了什么 | AI 会怎么做 |
|---|---|
| 明确的普通任务 | 跳过菜单，直接开始（A 模式） |
| 文件 + 明确任务 | 跳过菜单，直接处理文件（B 模式） |
| 你的仓库 + 仓库任务 | 跳过菜单，进入仓库连接核验（C 模式） |
| 完整治理控制包 | 跳过菜单，进入控制包处理 |

A / B 模式**永不要求你操作 GitHub**。C 模式**不自动获得写权限**。

任何时候想回到菜单，说 `返回模式选择`。

---

### A｜直接开始

```text
你可以直接告诉我想完成什么。

建议包含：
1. 想得到什么结果
2. 已经有哪些信息
3. 希望以什么形式交付

例如：
"帮我整理一份活动方案，最后输出成可复制的正文。"
```

### B｜我会上传文件

```text
请把文件上传到当前对话，然后告诉我：

1. 需要修改、分析还是整理
2. 最终需要什么格式

可以一次上传多个文件，不需要上传到 GitHub。
```

### C｜连接我自己拥有或管理的项目仓库

```text
请提供你自己拥有或管理的项目仓库链接。

然后选择：

1｜只读分析，不修改仓库
2｜允许创建候选变更，但最终提交和合并仍由你确认
```

---

## What ADT provides

ADT is a **governance tool system and control plane** — a set of protocols, validators,
and reusable checks that help humans and AI agents work together safely on multi-agent
projects. It is not a runtime, not a scheduler, and not a single AI personality.

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
