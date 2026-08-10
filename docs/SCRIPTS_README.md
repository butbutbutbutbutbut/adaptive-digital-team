# scripts/ 脚本说明

本目录存放之lab 治理链的辅助脚本。所有脚本均为**脱敏归档版**：不含任何真实凭据，凭据一律通过环境变量注入。

## daily_inspection.py —— 每日朝报（巡检）

### 用途

每日早 9:00 由 cron 触发的朝报生成器（三省六部版）。对飞书表格（反馈/任务/节点/决定四表）、GitHub PR（gh CLI）与本地 repo 实查三源并列读取，产出：

- **尚书省·昨日成果**：昨日完成的节点/任务 + 昨日合入的 PR（正反馈为主）
- **六部进展**：ADT / Workshop（之lab 业务线）/ 个人网站 各线进行中节点（空态以 ○ 标注，不带 ✅）
- **门下省·决定**：累计已批准决定数（头部统计行）
- **奏本**：状态过期（备注已闭环但状态未更新）、待审核、阻塞、7 天内截止、反馈表待处理、本地 repo 未推送提交/工作区脏、已完成节点未填实际结束日期、飞书/GitHub 读取失败
- **本地实查**：对本地 repo 执行 git fetch + 未推送提交计数 + 工作区脏检测（真查不宣称，不做无依据的"一致"断言）
- **落盘归档**：朝报全文追加写入 `~/hermes-sync/daily-reports/YYYY-MM-DD.md`（静默，不打印归档提示）

输出为纯文本朝报，由本地 cron 推送到微信。

### 运行方式

```bash
# 1. 注入环境变量（凭据只存在本地环境，不入库）
export LARK_BASE_TOKEN=<飞书 Base token>
# 可选：lark-cli 路径（缺省为 <USER>\AppData\Local\hermes\node\lark-cli，<USER> 为当前用户名）
export LARK_CLI_PATH=<lark-cli 完整路径>

# 2. 运行（需已登录 gh CLI）
python scripts/daily_inspection.py
```

缺少 `LARK_BASE_TOKEN` 时脚本会立即退出并提示，不会静默空跑。

### 输出限额

- 尚书省成果最多显示 8 条（`praise[:8]`），超出显示"…另有 N 项"
- 奏本最多显示 5 条（`issues[:5]`）
- 反馈表待处理最多逐条显示 4 条，超出显示"另有 K 条"

### 依赖

- `gh` CLI（GitHub 认证，用于昨日合入 PR 交叉验证）
- `lark-cli`（飞书表格读取，路径见上方环境变量）
- Python 3.8+（仅标准库，无第三方依赖）

### 凭据边界

- **飞书 Base token 永不入库**（本仓库公开）。必须通过环境变量 `LARK_BASE_TOKEN` 注入。
- 含真实凭据的本地 cron 运行版位于 `<USER>\AppData\Local\hermes\scripts\daily_inspection.py`（`<USER>` 为当前用户名），**永不提交到本仓库**。
- 本仓库内任何文件出现 token 字样均视为安全事故，需立即清除。

### 变更历史

- **v1.2**：fail-open 修复（任一源读取失败必须在朝报中明说，不静默空跑：飞书读取失败置顶横幅、GitHub 读取失败入奏本、本地 fetch 失败/rev-list 异常入奏本）；三源命名降级为"三源并列读取 + 本地同步自检"，删除"一致"断言，尾注只输出"本地同步 ✓/✗"；HEAD 分支盲修复（HEAD vs origin/main 对比改为未推送提交计数 `git rev-list --count origin/main..HEAD`）；决定计数移入头部统计行（累计已批准决定）；已完成节点未填实际结束日期兜底提示（补录后才会进昨日成果）；渲染修复（截断统一加省略号、7 天内截止改"MM-DD 标题"格式并剥标题括号尾巴、反馈待处理带条数、英文星期改中文、"皇帝待批"改"待你拍板"）；lark() 去掉 `shell=True`（bash -lc 白名单）；`<USER>` 路径脱敏占位；朝报全文落盘归档（追加模式）。
- **v1.1**：反馈表纳入奏本扫描；本地 repo 实查第三源（三源真查不宣称）。
