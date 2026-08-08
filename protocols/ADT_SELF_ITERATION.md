> **DEPRECATED — 归档态（2026-08-08）**：本协议已被双层重构取代。
> 完整规范见 `protocols/BINDING.md` / `GATE.md` / `RECEIPT.md` / `PHILOSOPHY.md`；
> 去向登记见 `governance/NORMATIVE_MAP.md`（唯一活入口）。
> 文件保留仅为维持历史引用（84+ PR）不断链，不参与新作业。

# ADT 自迭代治理协议

**PROTOCOL_STATUS:** `ADOPTED_GOVERNANCE_SPECIFICATION`
**TASK_ID:** ADT-SELF-ITERATION-R1
**SCOPE:** ADT 治理自身缺陷的发现、分类、修复流程

---

## 1. 问题

ADT 当前治理外部仓库的流程已成熟——分类、授权、Maker、Checker、证据、交付。
但 ADT 治理**自身**的流程不存在。

当 ADT 的一个协议层缺陷被发现——
比如 Human Facing 回报缺少必报字段、反目标审查未自动触发、
Holder 越权执行 Maker 工作——修复路径依赖 Human 注意到问题并主动发起。

这违背 ADT 的核心承诺：
> 不是帮 AI 写得更快，而是让你在 AI 替你干活时还能保持掌控。

如果 ADT 不能发现并修复自己的缺陷，
那它对用户的承诺是可质疑的。

---

## 2. 自迭代范围

### 2.1 允许自修复的资产

| 类别 | 文件 | 自修复授权 |
|---|---|---|
| 协议规范 | `protocols/*.md` | L0 级（文档修正） |
| Agent 行为约束 | `AGENTS.md` § Non-negotiable boundaries | L1 级（控制面变更） |
| 治理索引 | `AGENTS.md` § Governance index | L0 级 |
| Roadmap | `ROADMAP.md` | L0 级 |
| 项目状态 | `PROJECT_STATE.md` § summary | L0 级 |
| Validator 脚本 | `scripts/validate_*.py` | L1 级 |
| 测试 | `tests/*.py` | L1 级 |

### 2.2 禁止自修复的资产

| 类别 | 原因 |
|---|---|
| 角色模型 | `governance/ROLE_MODEL.md` — Human 角色定义不可自改 |
| Human 授权门 | Merge、Ready、branch deletion — 不可自授权 |
| 方法论基线 | `METHODOLOGY.md` — 需要 Human 确认方向变更 |
| 非 ADT 治理仓库 | 其他仓库的代码和配置 |

### 2.3 自修复上限

- 禁止自授权 Merge、自提升风险等级、自扩展授权范围
- 修复产生的 PR 必须经过独立的 Human Merge Decision
- 修复不得绕过现有的 CI gate 和 scope enforcement

---

## 3. 缺陷发现机制

### 3.1 主动触发

| 触发器 | 检测内容 |
|---|---|
| 反目标审查 | 每次 Human 要求审查时，结果自动注册为潜在缺陷 |
| CI 失败 | scope violation、validation failure → 自动分类 |
| Human 纠正 | Human 指出行为不符合协议 → 注册为缺陷 |
| Human Facing 缺失 | Controller/Holder 回报缺少必报字段 → 标记 |

### 3.2 缺陷注册

缺陷发现后，Controller 或 Project Control 注册一张 Defect Card：

```yaml
defect:
  id: ADT-DEFECT-{timestamp}
  discovered_by: <CONTROLLER | CHECKER | HUMAN>
  trigger: <ANTI_OBJECTIVE_REVIEW | CI_FAILURE | HUMAN_CORRECTION | FACING_GAP>
  affected_file: <path>
  protocol_ref: <引用违反的协议条款>
  description: <单句描述缺陷>
  severity: <LOW | MEDIUM | HIGH>
  proposed_fix_type: <L0_GOVERNANCE_DOCUMENTATION | L1_CONTROL_PLANE_CHANGE>
```

### 3.3 注册位置

Defect Card 不写入协议文件。写入 `docs/defects/DEFECT_LOG.md`（追加），
或作为独立 candidate 的 TASK_ID 引用源。

---

## 4. 修复流程

### 4.1 标准链路

```
缺陷发现
  ↓
Controller 注册 Defect Card
  ↓
Controller 分类（L0 / L1）
  ↓
L0 → 自动生成 Dispatch Card，排入任务队列
L1 → 暂停，等待 Human 授权
  ↓
Holder 接收 Dispatch Card → 派 Maker
  ↓
Maker 在 authorized_write_scope 内修复
  ↓
Checker 独立审计
  ↓
Holder 聚合 → Controller 回报 Human
  ↓
Human Merge Decision
```

### 4.2 L0 级（文档/索引/描述修正）

- 自动生成 Dispatch Card
- 不需要额外的 Human 授权即可派发
- 修复 PR 仍需 Human Merge Decision
- 示例：README 链接修复、证据字段补充、协议措辞澄清

### 4.3 L1 级（控制面/验证逻辑变更）

- Controller 暂停自动派发
- 向 Human 呈报 Defect Card + 建议修复方案
- Human 授权后进入标准 Maker/Checker 流程
- 示例：新增 non-negotiable boundary、修改 validator 校验逻辑

### 4.4 L2 级（不可自修复）

- 立即停止
- 仅呈报 Defect Card，不生成 Dispatch Card
- Human 决定是否启动独立治理任务
- 示例：角色模型重构、Human 授权门修改

---

## 5. 与现有治理的关系

| 现有机制 | 自迭代中的角色 |
|---|---|
| CANDIDATE_LIFECYCLE | 自修复 PR 遵循相同的 ONE_TASK_ONE_BRANCH_ONE_PR |
| Scope Enforcement | 修复文件的 scope 必须在 CANDIDATE_BINDING 内 |
| Independent Checker | 自修复的 Checker 不得是发现缺陷的同一个 agent |
| Human Merge Decision | 所有自修复 PR 最终由 Human 决定合并 |
| Anti-Objective Controls | 自修复不得产生比缺陷本身更重的治理成本 |

---

## 6. 反目标

- 不自激：发现一个缺陷不得自动产生三个修复任务
- 不越权：L0 自修复的授权不得被扩展为 L1 变更
- 不隐藏：所有 Defect Card 可被 Human 审查
- 不替代 Human 判断：修复建议 ≠ 修复授权
- 不降低标准：自修复 PR 通过相同的 CI gate 和 Checker 审查

---

## 7. 当前实施状态

R1 为协议定义。实施阶段：

1. Defect Card 格式已定义，可以在每次发现缺陷时手动注册
2. Controller 的自分类逻辑待纳入 ADT Controller skill
3. `docs/defects/DEFECT_LOG.md` 待创建
4. 自动触发（CI 失败 → 缺陷注册）待 Runtime 层支持
