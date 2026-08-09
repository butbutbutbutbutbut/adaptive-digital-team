# scripts/ 脚本说明

本目录存放之lab 治理链的辅助脚本。所有脚本均为**脱敏归档版**：不含任何真实凭据，凭据一律通过环境变量注入。

## daily_inspection.py —— 每日朝报（巡检）

### 用途

每日早 9:00 由 cron 触发的朝报生成器（三省六部版）。对飞书表格（三源交叉验证的一源）与 GitHub PR（gh CLI）做交叉验证，产出：

- **尚书省·昨日成果**：昨日完成的节点/任务 + 昨日合入的 PR（正反馈为主）
- **六部进展**：ADT / Workshop（之lab 业务线）/ 个人网站 各线进行中节点
- **门下省·决定**：已批准决定记录数
- **奏本**：状态过期（备注已闭环但状态未更新）、待审核、阻塞、7 天内截止任务

输出为纯文本朝报，由本地 cron 推送到微信。

### 运行方式

```bash
# 1. 注入环境变量（凭据只存在本地环境，不入库）
export LARK_BASE_TOKEN=<飞书 Base token>
# 可选：lark-cli 路径（缺省为 C:\Users\x2270\AppData\Local\hermes\node\lark-cli）
export LARK_CLI_PATH=<lark-cli 完整路径>

# 2. 运行（需已登录 gh CLI）
python scripts/daily_inspection.py
```

缺少 `LARK_BASE_TOKEN` 时脚本会立即退出并提示，不会静默空跑。

### 依赖

- `gh` CLI（GitHub 认证，用于昨日合入 PR 交叉验证）
- `lark-cli`（飞书表格读取，路径见上方环境变量）
- Python 3.8+（仅标准库，无第三方依赖）

### 凭据边界

- **飞书 Base token 永不入库**（本仓库公开）。必须通过环境变量 `LARK_BASE_TOKEN` 注入。
- 含真实凭据的本地 cron 运行版位于 `C:\Users\x2270\AppData\Local\hermes\scripts\daily_inspection.py`，**永不提交到本仓库**。
- 本仓库内任何文件出现 token 字样均视为安全事故，需立即清除。
