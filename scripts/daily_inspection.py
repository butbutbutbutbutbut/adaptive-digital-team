# -*- coding: utf-8 -*-
"""之lab 每日朝报（三省六部版）——早 9:00 推微信（脱敏归档版）

正反馈为主：尚书省成果（昨日完成节点/任务/合入 PR）+ 六部进展
奏本为次：状态过期/阻塞/待审核/7天内截止
数据：飞书表格（三源之一）+ GitHub PR（gh）

┌────────────────────── 凭据边界 ──────────────────────┐
│ 本仓库为公开仓库。飞书 Base token 不入库，必须通过     │
│ 环境变量 LARK_BASE_TOKEN 提供；lark-cli 路径通过      │
│ LARK_CLI_PATH 提供（缺省使用本机默认安装路径）。       │
│ 含真实凭据的本地 cron 运行版位于                     │
│ C:\\Users\\x2270\\AppData\\Local\\hermes\\scripts\\       │
│ daily_inspection.py，永不入库。                       │
└──────────────────────────────────────────────────────┘
"""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

DEFAULT_LARK_CLI = r"C:\Users\x2270\AppData\Local\hermes\node\lark-cli"

TASKS_TBL = "tblArqwuZQtzIIdt"
NODES_TBL = "tblwEKyFdDDKG6aB"
DECISIONS_TBL = "tblZHOwWWZtWpv9b"
REPOS = ["butbutbutbutbutbut/adaptive-digital-team"]


def env_required(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"[daily_inspection] 缺少必需环境变量 {name} —— 请 export {name}=<value> 后重试（凭据不得入库）")
    return v


def lark(args):
    cli = os.environ.get("LARK_CLI_PATH", "").strip() or DEFAULT_LARK_CLI
    r = subprocess.run(f'"{cli}" {args}', capture_output=True, text=True, encoding="utf-8", shell=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"ok": False, "raw": r.stdout[:200]}


def load_rows(table_id):
    token = env_required("LARK_BASE_TOKEN")
    d = lark(f"base +record-list --as bot --base-token {token} --table-id {table_id} --json --limit 200")
    if not d.get("ok"):
        return []
    data = d["data"]
    fields, rids, rows = data["fields"], data["record_id_list"], data["data"]
    out = []
    for i, row in enumerate(rows):
        rec = {"_id": rids[i]}
        for j, f in enumerate(fields):
            rec[f] = row[j]
        out.append(rec)
    return out


def val(v):
    if isinstance(v, list):
        return v[0] if v else ""
    return v or ""


def main():
    today = date.today()
    yesterday = today - timedelta(days=1)
    ys = str(yesterday)
    lines = []
    issues = []
    praise = []

    tasks = load_rows(TASKS_TBL)
    nodes = load_rows(NODES_TBL)
    decisions = load_rows(DECISIONS_TBL)

    # ===== 尚书省：昨日成果（正反馈） =====
    done_nodes = [n for n in nodes
                  if val(n.get("节点状态")) == "已完成"
                  and str(val(n.get("实际结束")) or "")[:10] == ys]
    done_tasks = [t for t in tasks
                  if val(t.get("任务状态")) == "已完成"
                  and str(val(t.get("实际结束")) or "")[:10] == ys]
    for n in done_nodes:
        praise.append(f"节点『{val(n.get('节点名称'))}』完成（{val(n.get('所属项目'))}）")
    for t in done_tasks:
        praise.append(f"任务『{val(t.get('任务标题'))[:24]}』完成")

    # ===== 尚书省：昨日合入 PR（gh 交叉验证） =====
    merged_prs = []
    for repo in REPOS:
        r = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--state", "merged", "--search", f"merged:{ys}",
             "--json", "number,title", "--limit", "10"],
            capture_output=True, text=True, shell=True)
        try:
            prs = json.loads(r.stdout)
            for p in prs:
                merged_prs.append(f"PR #{p['number']} {p['title'][:30]}")
        except Exception:
            pass
    for m in merged_prs:
        praise.append(f"合入 {m}")

    # ===== 六部：各线进展 =====
    for proj in ["ADT", "Workshop（之lab 业务线）", "个人网站"]:
        active = [n for n in nodes if val(n.get("所属项目")) == proj and val(n.get("节点状态")) == "进行中"]
        if active:
            praise.append(f"{proj.split('（')[0]}线：进行中 {len(active)} 项（{'/'.join(val(n.get('节点名称'))[:10] for n in active[:3])}）")
        else:
            praise.append(f"{proj.split('（')[0]}线：无进行中节点")

    # ===== 门下省+都察院：昨日决定与合规 =====
    new_decisions = [d for d in decisions if str(val(d.get("决定状态"))) == "已批准"]
    if new_decisions:
        praise.append(f"决定记录 {len(new_decisions)} 条已批准")

    # ===== 奏本：问题检测（保持巡检功能） =====
    for t in tasks:
        remark = val(t.get("备注"))
        status = val(t.get("任务状态"))
        if status != "已完成" and remark and ("已闭环" in remark or "已完成" in remark):
            issues.append(f"状态过期:『{val(t.get('任务标题'))[:22]}』备注已闭环但状态={status}")

    waiting = [t for t in tasks if val(t.get("任务状态")) == "待审核"]
    blocked = [t for t in tasks if val(t.get("任务状态")) == "阻塞"]
    soon = []
    for t in tasks:
        end = val(t.get("计划结束"))
        if end:
            try:
                d = datetime.strptime(str(end)[:10], "%Y-%m-%d").date()
                if today <= d <= today + timedelta(days=7) and val(t.get("任务状态")) not in ("已完成", "已取消"):
                    soon.append((d, val(t.get("任务标题"))))
            except Exception:
                pass

    new_nodes_today = [n for n in nodes if str(val(n.get("实际开始")) or "")[:10] == str(today)]
    if not new_nodes_today and not praise:
        issues.append("昨日无成果入轴，事实未记录？")

    # ===== 朝报排版 =====
    lines.append(f"📜 之lab 朝报 · {today.strftime('%m-%d %A')}")
    lines.append(f"任务 {len(tasks)} | 节点 {len(nodes)} | 已批准决定 {len(new_decisions)}")
    if praise:
        lines.append("🏛️ 尚书省·昨日成果:")
        for p in praise[:8]:
            lines.append(f"  ✅ {p}")
        if len(praise) > 8:
            lines.append(f"  …另有 {len(praise)-8} 项")
    else:
        lines.append("🏛️ 尚书省·昨日成果:（空，昨日无完成记录）")
    if waiting:
        lines.append(f"👑 皇帝待批: " + "、".join(val(t.get("任务标题"))[:14] for t in waiting[:4]))
    if soon:
        soon_s = "、".join(f"{d.strftime('%m-%d')}{t[:10]}" for d, t in sorted(soon)[:5])
        lines.append(f"⏰ 7天内截止: {soon_s}")
    if blocked:
        lines.append(f"🚫 奏本·阻塞: " + "、".join(val(t.get("任务标题"))[:14] for t in blocked[:3]))
    if issues:
        lines.append("📢 奏本·需修正:")
        for i in issues[:5]:
            lines.append(f"  ⚠️ {i}")
    if not issues and not blocked:
        lines.append("📢 奏本: 无")
    lines.append("— 三源一致 · 本地|飞书|GitHub —")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
