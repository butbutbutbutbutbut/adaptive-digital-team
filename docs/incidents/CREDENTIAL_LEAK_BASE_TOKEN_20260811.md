# Credential Leak — Base Token in Public Repo — 2026-08-11

```text
INCIDENT_ID:
ADT-INCIDENT-CREDENTIAL-LEAK-20260811-001

INCIDENT_TYPE:
CREDENTIAL_LEAK

TRIGGER:
GUARDRAILS_DOC_INCLUDED_REAL_BASE_TOKEN

ROOT_CAUSE:
DOCUMENTATION_WRITE_WITHOUT_CREDENTIAL_SCAN
(红牌纪律文档 v1.0 起草时把飞书 base token 写入"适用范围"段，
未做凭据扫描即合入公开仓，违反后来才立下的红牌第 11 条)

REPOSITORY_INTEGRITY:
PASS (当前 HEAD 已清除)

HISTORY_REWRITE:
FORBIDDEN_BY_DECISION
(之拍板：不重写历史；改用门禁+留痕，见下)
```

## 1. 泄漏事实

- 泄漏值：飞书多维表格 base token（app_token，base 链接标识）
- 位置：`docs/FEISHU_BITABLE_GUARDRAILS.md` v1.0 适用范围段（PR #94 合入）
- 历史提交（仍含该字符串）：`be28b52`（#94 合入 main）、`c043ba3`（#94 分支）
- 当前 HEAD 已清除：#97（`4a00e0d`）将 token 占位化
- 引入者：小禾（中控起草 #94 文档时写入）——责任归属：中控

## 2. 风险评估（实查结论）

```text
BASE_SHARE_LINK:        NOT_ENABLED（之确认未开分享，外部无访问入口）
BOT_APP_SECRET:         NOT_LEAKED（环境变量注入，零泄漏）
TOKEN_NATURE:           APP_TOKEN（飞书定位为链接标识，非密钥）
PRACTICAL_RISK:         LOW
```

结论：组织外人员持有该字符串也无法访问 base（无分享入口+登录权限拦截+bot 无法以该 token 单独读数据）。

## 3. 补救动作

```text
REMEDIATION_A_CONFIRM_NO_SHARE:   DONE（之确认，8/11）
REMEDIATION_C_CI_SECRET_GATE:     DONE（.github/workflows/secretscan.yml，8/11）
REMEDIATION_D_INCIDENT_RECORD:    THIS_DOCUMENT
REMEDIATION_B_HISTORY_REWRITE:    REJECTED_BY_HUMAN_HOLDER（代价>收益，克隆副本无法清除）
```

## 4. 教训与防线

- 红牌纪律新增第 11 条：禁止凭据入公开仓/文档，写文档用占位符（`<USER>`/`${ENV}`）
- 新增 CI 门禁：`secretscan.yml` 扫描已知凭据模式+通用密钥模式，命中即 CI 失败
- 写文档/脚本时先问：这里要不要放真值？——答案永远是"不要，用占位符"
- 中控责任：起草任何含 token/路径/名称的文档前，先跑一遍凭据扫描

## 5. 状态

```text
HEAD_CLEAN:             YES
GLOBAL_SCAN_TOKEN:      0 HITS
GLOBAL_SCAN_X2270:      0 HITS
GATE_CLOSED:            YES（除历史提交字符串无法清除外，全部处置完成）
```
