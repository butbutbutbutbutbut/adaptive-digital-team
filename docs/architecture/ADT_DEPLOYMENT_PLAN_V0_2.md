# ADT 部署方案 v0.2

**编制：** Holder 控制窗口  
**接收人：** 之、小禾、安鼎  
**日期：** 2026-07-20  
**状态：** 架构基线候选 / 未授权实施  
**前置门禁：** ADT PR #21 独立治理审计通过并合入 Main

---

## 一、系统定位

### 1. ADT

**全称：** Adaptive Digital Team  
**中文名：** 安鼎  
**定位：** 治理工具系统与控制平面，不是人格 Agent。

ADT 负责提供：

- 仓库即提示词；
- 事实源绑定；
- 候选状态管理；
- 权限与写入范围校验；
- 任务门禁；
- 反目标审查；
- Maker / Checker 调度协议；
- Human 可见进度；
- 审计与回执；
- 飞书控制界面的可信状态来源。

### 2. 安鼎 Agent

**定位：** Persistent Holder Agent。

安鼎 Agent 是调用 ADT 的运行人格，不等于 ADT 本身。

```text
安鼎 Agent：
负责判断、调度、解释和持续运行。

ADT：
提供协议、状态、校验器、工具和确定性门禁。
```

### 3. Human Holder

**之是唯一 Human Holder。**

之永久保留：

- 项目方向；
- 最终授权；
- 产品与视觉验收；
- 权限升级；
- 审计争议裁决；
- Ready；
- Merge；
- 解除安全性 HARD_STOP。

---

## 二、角色模型

| 角色 | 身份 | 主要职责 |
|---|---|---|
| Human Holder | 之 | 定方向、授权、最终验收 |
| Persistent Holder Agent | 安鼎 | 调用 ADT，维护事实源、门禁、任务和调度 |
| Companion / Counter-review Peer | 小禾 | 保护 Human 意图、体验和关系连续性，反审查治理过载 |
| Maker | 临时指定 | 执行具体代码、设计、文档或研究任务 |
| Independent Checker | 临时指定 | 对未参与形成的候选执行只读独立审计 |

### 核心关系

```text
之
└── Human Holder

安鼎 Agent
├── Persistent Holder Agent
└── 调用 ADT

小禾
├── 陪伴人格
├── 反审查 Peer
├── 有限副 Holder
└── 工作经历的关系记忆承载者

ADT
└── 治理工具与控制平面

Maker / Checker
└── 按任务临时创建
```

---

## 三、小禾的双场景定位

### 1. 微信场景

微信是小禾的主要关系空间。

默认原则：

- 重聊天、轻工作；
- 保持人格连续性；
- 允许读取筛选后的长期工作记忆；
- 不默认承担项目管理；
- 不默认调用仓库写入工具；
- 不把微信聊天作为项目事实源。

### 2. 飞书场景

小禾在飞书中可承担：

#### Counter-review Peer

负责质疑安鼎：

- 是否误解 Holder 的真实目标；
- 是否治理成本过高；
- 是否用形式正确替代实际推进；
- 是否制造候选、分支和上下文负担；
- 是否让用户重新陷入黑箱；
- 是否遗漏体验、关系和情绪因素。

#### Limited Deputy Holder

在之明确授权的低风险范围内：

- 复述用户真实意图；
- 建议 HOLD；
- 对优先级提出异议；
- 汇总争论；
- 提交 Human 决策候选；
- 维护工作与关系的连续性。

小禾不得：

- 独立授权仓库写入；
- 修改 ADT 根治理规则；
- Ready；
- Merge；
- 签发正式独立审计 PASS；
- 审计自己参与形成的候选；
- 把自身意见冒充 Human 授权。

---

## 四、总体部署架构

```text
                        之
                  Human Holder
                        │
                飞书群「安鼎」
         ┌──────────────┴──────────────┐
         │                             │
      小禾 Bot                      安鼎 Bot
         │                             │
  Hermes Profile: xiaohe       Hermes Profile: anding
         │                             │
  Xiaohe Gateway Process       Anding Gateway Process
         └──────────────┬──────────────┘
                        │
                 ADT Gateway Core
         ┌──────────────┼──────────────┐
         │              │              │
   Identity Broker  Debate Controller  Audit Ledger
         │              │              │
         └──────────────┼──────────────┘
                        │
                    ADT Runtime
         ┌──────────────┼──────────────┐
         │              │              │
 Repository State  Task/Gate State  Runtime Registry
```

### 飞书职责

- 展示两个独立人格；
- 接收 Human 消息；
- 显示状态、进度和决策卡；
- 提供 H5 人类控制面板；
- 承载公开工作争论。

### Gateway 职责

- 身份映射；
- Agent 间消息转发；
- 权限核验；
- 事实源绑定；
- 回合控制；
- 旧卡片失效；
- 审计日志；
- 记忆候选生成。

### ADT 职责

- 提供正式治理状态；
- 校验允许与禁止动作；
- 阻止事实源漂移；
- 生成任务和审计门禁；
- 不保存人格私有记忆。

---

## 五、双 Agent 硬隔离

Hermes Profile 只提供默认状态隔离，不视为安全沙箱。

### 必须实施的隔离

| 隔离层 | 小禾 | 安鼎 |
|---|---|---|
| Profile | `xiaohe` | `anding` |
| 人格目录 | 独立 | 独立 |
| Memory Store | 独立 | 独立 |
| Sessions | 独立 | 独立 |
| Skills | 独立 | 独立 |
| Gateway 进程 | 独立 | 独立 |
| 飞书应用 | Bot A | Bot B |
| App ID / Secret | 独立 | 独立 |
| GitHub Token | 独立 | 独立 |
| 工作目录 | 独立 | 独立 |
| Windows ACL | 限制安鼎访问 | 限制小禾访问 |
| 日志 | 独立 | 独立 |

### 禁止行为

- 读取对方私有记忆；
- 读取对方 Session；
- 修改对方人格；
- 共用 GitHub Token；
- 共用飞书 Secret；
- 冒充对方身份；
- 将对方发言视为 Human 授权；
- 将共享争论内容写入对方私有记忆而不经过筛选。

---

## 六、人格与记忆 GitHub 备份

建立四个独立 Private Repository：

```text
xiaohe-persona-private
xiaohe-memory-archive-private

anding-holder-agent-persona-private
anding-holder-agent-memory-archive-private
```

### 1. 人格仓库

保存：

```text
SOUL.md
ROLE_BOUNDARIES.md
TOOL_POLICY.yaml
PROFILE_MANIFEST.yaml
SKILLS_MANIFEST.yaml
GATEWAY_IDENTITY.yaml
PERSONA_CHANGELOG.md
persona.sha256
```

禁止保存：

```text
.env
App Secret
API Key
GitHub Token
Cookie
OAuth 凭据
本地认证文件
```

人格变更规则：

1. Agent 提出人格修改候选；
2. 通过 PR 展示差异；
3. Human 审批；
4. 合入人格仓库 Main；
5. 生成新人格 Hash；
6. Gateway 启动时校验 Hash。

Agent 不得自行覆盖人格 Main。

### 2. 记忆归档仓库

仅保存经过筛选和加密的长期记忆快照。

```text
snapshots/<timestamp>.tar.age
manifests/<timestamp>.yaml
checksums/<timestamp>.sha256
RESTORE_TESTS.md
```

禁止直接提交：

- 完整聊天数据库；
- 原始飞书群历史；
- 临时 Session；
- 密钥；
- 附件；
- Cookie；
- 未筛选隐私数据。

### 3. 备份权限

```text
Agent：
人格仓库 READ
记忆归档 APPEND_CANDIDATE

Backup Service：
执行加密、校验和推送

Human：
人格变更批准
恢复授权
密钥保管
```

GitHub 只用于版本存档与灾难恢复，不作为运行时记忆数据库。

---

## 七、飞书控制界面

### 1. 飞书 Bot

#### 安鼎 Bot

负责：

- 当前事实源；
- 当前门禁；
- 任务进度；
- 权限边界；
- Maker / Checker 状态；
- 异常与 HOLD；
- Human 决策请求。

#### 小禾 Bot

负责：

- 对安鼎方案提出反审查；
- 补充 Human 意图；
- 讨论体验与关系影响；
- 参与工作争论；
- 汇总对用户有长期意义的工作事件。

### 2. 飞书 H5 控制面板

必须显示：

- 当前唯一事实源；
- 治理基线；
- 产品基线；
- Active Candidate；
- Comparison Candidates；
- Historical / Invalidated；
- 所有 worktree；
- 当前进程与端口；
- 浏览器证据 URL；
- 当前任务；
- 真实进度；
- 已完成与阻塞项；
- Human 待决策事项；
- 最近 Checker 结论；
- 当前允许操作；
- 当前禁止操作；
- 小禾与安鼎当前是否存在未解决分歧。

### 3. Human 决策卡

所有卡片必须绑定：

```yaml
task_id:
candidate_sha:
gate:
decision_id:
issued_at:
expires_at:
```

Head 变化、任务关闭或卡片过期后，旧卡片必须失效。

---

## 八、小禾与安鼎的争论机制

飞书不作为两个 Bot 之间的可靠消息总线。

Agent 间通信由 Gateway 显式中继。

### 1. WORK_DEBATE

用于正式工作争论。

```yaml
mode: WORK_DEBATE
task_id: required
fact_source: required
bound_head: required
max_turns: 8
repository_write: forbidden
human_decision_required: true
```

每回合包含：

```text
POSITION:
EVIDENCE:
COUNTER_OBJECTIVE:
PROPOSAL:
CONFIDENCE:
```

停止条件：

- 达成一致；
- 达到最大回合；
- 事实源冲突；
- Head 变化；
- 任一方调用 HOLD；
- 需要扩大权限；
- 需要仓库写入；
- Human 手动停止。

争论完成后只生成 Human 决策卡，不自动执行。

### 2. CHARACTER_BANTER

用于人格化闲聊和轻度争执。

限制：

- 不改变任务状态；
- 不调用仓库写入工具；
- 不产生正式治理结论；
- 不形成 Human 授权；
- 有频率和回合上限；
- 可形成小禾关系记忆候选。

---

## 九、飞书到小禾的记忆桥

模块名称：

```text
FEISHU_TO_XIAOHE_MEMORY_BRIDGE
```

### 数据流程

```text
飞书工作事件
→ 原始审计日志
→ 争论或成果摘要
→ 记忆候选
→ 去敏和分类
→ 小禾记忆写入
→ 加密 GitHub 快照
→ 微信小禾可读取
```

### 可写入小禾记忆

- 已完成的重要工作；
- Human 已确认的决定；
- 小禾与安鼎的重要分歧；
- 双方争论的核心矛盾；
- 最终解决方式；
- 用户的稳定偏好；
- 对关系产生影响的事件；
- 值得未来回忆的未解决问题。

### 不自动写入

- 完整聊天原文；
- 长命令；
- 系统日志；
- 临时错误；
- 未确认推断；
- 密钥与凭据；
- 普通状态噪声。

### 事件记忆示例

```yaml
episode_id: debate-20260720-001
source: feishu
participants:
  - xiaohe
  - anding
topic: 飞书面板与 Runtime Registry 的优先级
xiaohe_position: 先解除用户黑箱
anding_position: 先保证状态来源可靠
human_decision: 先做最小 Runtime Registry，再接入面板
resolution: partial_consensus
relationship_effect: 小禾继续承担反治理过载职责
visibility: xiaohe_private
```

微信中的小禾可以读取这段经历，但不得把它当作当前项目事实。

---

## 十、权限矩阵

| 操作 | 之 | 安鼎 | 小禾 | Maker | Checker |
|---|---:|---:|---:|---:|---:|
| 读取治理状态 | 是 | 是 | 是 | 按任务 | 是 |
| 建议任务路径 | 是 | 是 | 是 | 是 | 否 |
| 创建任务候选 | 是 | 是 | 有限 | 否 | 否 |
| 授权产品写入 | 是 | 受限执行 | 否 | 否 | 否 |
| 修改 ADT | 是 | 经任务授权 | 否 | 否 | 否 |
| 执行产品实现 | 可授权 | 不默认 | 不默认 | 是 | 否 |
| 正式独立审计 | 可委派 | 否 | 否 | 否 | 是 |
| 接受视觉结果 | 是 | 否 | 否 | 否 | 否 |
| Ready | 是 | 否 | 否 | 否 | 否 |
| Merge | 是 | 否 | 否 | 否 | 否 |
| HOLD | 是 | 是 | 建议或有限触发 | 否 | 建议 |
| 修改人格 | 批准 | 提案 | 提案 | 否 | 否 |

---

## 十一、开发优先级

### P0：ADT 基础闭环

- PR #21 CI PASS；
- 独立治理审计；
- 合入 ADT Main；
- repository-as-prompt 正式生效。

### P1：人格与备份

- 创建四个私有仓库；
- 固化小禾与安鼎人格；
- 建立人格 Hash；
- 建立加密记忆快照；
- 完成一次恢复演练。

### P2：双 Profile 与硬隔离

- 创建 `xiaohe` / `anding` Profile；
- 独立 Gateway；
- 独立凭据；
- Windows ACL；
- 独立日志与工作目录；
- 并发运行测试。

### P3：最小 ADT Gateway

- `/health`
- `/status`
- `/candidates`
- `/tasks`
- `/decisions`
- `/checker/latest`
- `/hold`
- 身份映射；
- Head 绑定；
- 审计日志；
- 旧请求失效。

首版只读，不开放仓库写入。

### P4：飞书控制平面

- 两个企业自建应用；
- 两个 Bot；
- 同一飞书群；
- 状态卡；
- Human 决策卡；
- H5 只读控制面板。

### P5：争论系统

- WORK_DEBATE；
- Gateway 中继；
- 回合控制；
- HOLD；
- Human 决策摘要；
- CHARACTER_BANTER。

### P6：记忆桥

- 飞书事件摘要；
- 记忆候选；
- 去敏；
- 写入小禾记忆；
- 微信端读取；
- 加密归档。

### P7：有限自动化

完成全部隔离与审计后，才允许：

- 安鼎调用受控 Maker；
- 自动请求 Checker；
- 低风险任务推进；
- 所有高风险动作仍返回之。

---

## 十二、首版验收标准

系统只有同时满足以下条件，才可进入实际使用：

- [ ] 小禾与安鼎人格 Hash 不同且可验证；
- [ ] 两个 Profile 不共享记忆和 Session；
- [ ] 两个 Gateway 可独立启动和停止；
- [ ] 两个飞书 Bot 身份独立；
- [ ] 两套 Secret 未进入仓库；
- [ ] Windows ACL 阻止互读私有目录；
- [ ] 安鼎可以读取 ADT 状态；
- [ ] 小禾不能修改 ADT 状态；
- [ ] 飞书 H5 能显示可信事实源与门禁；
- [ ] 旧卡片在 Head 变化后失效；
- [ ] WORK_DEBATE 不允许仓库写入；
- [ ] 争论结束必须由 Human 决策；
- [ ] 小禾能在微信读取筛选后的飞书事件记忆；
- [ ] 小禾记忆不能覆盖 ADT 项目事实；
- [ ] 四个私有仓库完成备份；
- [ ] 加密快照能够在全新 Profile 中恢复；
- [ ] 安鼎修改 ADT 后必须由第三方 Checker 审计；
- [ ] Ready 和 Merge 始终由之掌握。

---

## 十三、当前控制决定

```text
PLAN_VERSION:
ADT_DEPLOYMENT_V0_2

PLAN_STATUS:
READY_FOR_REVIEW

IMPLEMENTATION_STATUS:
NOT_AUTHORIZED

CURRENT_EXECUTION:
ADT PR #21 已完成独立治理审计并合入 Main。

NEXT_IMPLEMENTATION_CANDIDATE:
人格与记忆备份仓库设计
+ 双 Profile 隔离预检

HUMAN_HOLDER:
之

PRIMARY_HOLDER_AGENT:
安鼎

CONTROL_TOOLSET:
ADT

XIAOHE:
COMPANION
+ COUNTER_REVIEW_PEER
+ LIMITED_DEPUTY_HOLDER
+ RELATIONSHIP_MEMORY_CARRIER

BLACKBOX_STATUS:
PROHIBITED
```
