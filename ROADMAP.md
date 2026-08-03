# ADT Roadmap

> 最后更新：2026-08-04
> 
> 每个阶段需要独立的 Human 授权，包含确切的仓库、分支、Base 和 scope。
> 仓库公开不等于授权实施。

## P0 — Operational Baseline

**状态：** `OPERATIONAL_BASELINE` / `CONTINUING_MAINTENANCE`

已交付并持续维护：

| 能力 | 载体 |
|---|---|
| Scope Enforcement（授权范围强制执行） | `CANDIDATE_BINDING.json` + CI gate |
| Candidate Lifecycle（候选状态机） | `protocols/CANDIDATE_LIFECYCLE.md` |
| Maker / Checker 分离 | `governance/ROLE_MODEL.md` |
| Repository as Prompt | `AGENTS.md` § Repository-as-prompt startup |
| Fingerprint Binding（SHA-256 候选身份） | `protocols/CANDIDATE_LIFECYCLE.md` § Candidate fingerprint |
| Evidence Card（证据留痕） | `AGENTS.md` § Human-facing evidence discipline |
| Pre-write Execution Gate | `scripts/validate_binding.py` |
| Adaptive Counter-Objective Controls | `METHODOLOGY.md` |
| Beginner Bootstrap Router（A/B/C 路由） | `protocols/BEGINNER_BOOTSTRAP_ROUTER.md` |
| Human Facing README | `README.md` |
| User-facing Asset Protection | `AGENTS.md` § Non-negotiable boundaries |

P0 是地基。后续所有阶段在 P0 之上增量构建。

---

## P1-P3 — Dynamic Governance R1

**状态：** `SPECIFICATION_ADOPTED` / `RUNTIME_NOT_AUTHORIZED`

协议已通过并被引用，但尚未作为持续运行的 Runtime 实例激活。

| 组件 | 文件 | 状态 |
|---|---|---|
| Dynamic Governance Router（任务分类、风险路由） | `protocols/DYNAMIC_GOVERNANCE_ROUTER.md` | `ADOPTED_GOVERNANCE_SPECIFICATION` |
| Runtime Adapter Contract（三层隔离边界） | `protocols/ADT_RUNTIME_ADAPTER_CONTRACT.md` | `ADOPTED_GOVERNANCE_SPECIFICATION` |
| Resource Allocator（资源/模型分配） | PR #49 | Merged |
| Adaptive Counter-Objective Gate | PR #52 | Merged |
| Transient Candidate Binding | PR #51 | Merged |

**已完成的链路测试（PR #56）：**

- Controller → Holder → Maker + Checker 分派链 ✅
- Scope enforcement 跨角色生效 ✅
- Handoff Envelope FROM/TO/CONSUMER 全链追溯 ✅
- Holder HARD GATE 防止 self-implement ✅

**S2-002-A 实验发现（待办）：**

- Artifact Delivery Layer — 产物位置对人类可见
- Human Point Budget — 低风险任务轻量治理
- Artifact Existence Gate — "做完了"和"能看到产物"之间的验证

**当前阻止 RUNTIME 激活的因素：**

- `PROJECT_STATE.md`: `implementation_status: NOT_AUTHORIZED`
- 缺少持续运行的 Runtime 实例
- S2 Adaptive Runtime Layer 仍是实验概念，未形成正式协议文档

---

## P4 — Public Release Readiness

**状态：** `PARTIALLY_READY` / `IMPLEMENTATION_NOT_AUTHORIZED`

| 检查项 | 状态 |
|---|---|
| README 产品叙事 + A/B/C 功能入口 | ✅ PR #57 |
| Apache 2.0 License | ✅ |
| Contributing 指南 | ✅ |
| 用户接触面保护规则 | ✅ AGENTS.md |
| 中文用户完整认知链 | ✅ README |
| 独立部署文档 | ❌ 缺失 |
| 公开示例 / Demo 仓库 | ❌ 缺失 |
| 外部用户 onboarding 路径 | ❌ 缺失 |

---

## P5 — ADT Ops Org Bootstrap

**状态：** `PLANNED` / `NOT_AUTHORIZED`

尚未启动。涉及：

- 运营组织架构
- 生产部署实例
- 多仓库运维
- 飞书 / 外部通知集成
- 密钥与凭证管理
