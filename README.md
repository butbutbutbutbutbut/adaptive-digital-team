# Adaptive Digital Team

ADT is a **governance tool system and control plane** — a set of protocols, validators,
and reusable checks that help humans and AI agents work together safely on multi-agent
projects. It is not a runtime, not a scheduler, and not a single AI personality.

[中文说明](./中文内容/README.md)

## 你是人类还是 AI？

- **人类 / 普通访问者** → 继续往下读，从 A/B/C 选择使用场景
- **交互式 AI / Agent** → 立即跳转到 [BOOTSTRAP.md](./BOOTSTRAP.md) 激活协议，化身「安鼎」；激活后按 [AGENTS.md](./AGENTS.md) 执行

---

## A / B / C 快速开始

完整路由定义与冻结规范见 [protocols/BEGINNER_BOOTSTRAP_ROUTER.md](./protocols/BEGINNER_BOOTSTRAP_ROUTER.md)。

**菜单自动跳过**：第一条消息已包含明确任务、附件、仓库链接或控制包时，自动跳过菜单。

### A｜直接开始

你可以直接告诉我想完成什么。建议包含：想得到什么结果、已经有哪些信息、希望以什么形式交付。此模式不涉及仓库操作，所有内容在对话中完成。

### B｜我会上传文件

请把文件上传到当前对话，然后告诉我们需要修改、分析还是整理。可以一次上传多个文件，不需要上传到 GitHub。

### C｜连接我自己拥有或管理的项目仓库

请提供你自己拥有或管理的项目仓库链接，然后选择只读分析或允许创建候选变更。最终提交和合并仍由你确认。上游仓库（包括本 ADT 治理仓库）不能被外部用户当作项目仓库。

输入 **返回模式选择** 可随时重新显示菜单。

### 推荐运行方式

建议至少使用 **1 名人类 + 2 个独立 AI 窗口** 运行 ADT：一个窗口负责推进和执行，另一个窗口负责独立检查；人类保留授权、方向和最终决定权。

---

## What ADT provides

- **Repository-as-prompt** — durable context that any fresh agent window reads before acting
- **Maker/Checker separation** — independent implementation and audit roles
- **Candidate state machine** — from LOCAL_DRAFT through FORMAL_CANDIDATE to AUDIT_ELIGIBLE
- **Scope enforcement** — every task has an exact authorized file list; drift fails closed
- **Fingerprint binding** — deterministic SHA-256 identity for every candidate
- **Pre-write execution gate** — branch, Base, ancestry, and scope validated before any commit
- **Human-facing evidence cards** — machine facts + Simplified Chinese explanation at critical nodes
- **Adaptive counter-objective controls** — governance must never cost more than product value

## 安鼎 (Anding)

交互式 AI 读取本仓库后自动进入 ADT 协议并获得「安鼎」界面身份（ANDING_INTERFACE）。
完整激活条件与双层身份模型见 [BOOTSTRAP.md](./BOOTSTRAP.md)。

## Roles

| Role | Who | Authority |
|------|-----|-----------|
| **Human Holder** | Human project owner | Direction, authorization, final acceptance, Ready, Merge |
| **Persistent Holder Agent** | 安鼎 (ANDING_CONTROL) | Maintain fact source, route tasks, validate receipts |
| **Maker** | Temporary, task-scoped | Implement exactly the authorized task on the authorized branch |
| **Independent Checker** | Temporary, read-only | Independently audit a candidate it did not create |

完整的角色拓扑与权限矩阵见 [governance/ROLE_MODEL.md](./governance/ROLE_MODEL.md)。

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
