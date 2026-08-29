# -*- coding: utf-8 -*-
"""之lab 每日朝报（三省六部版）——早 9:00 推微信 + 落盘归档（脱敏归档版）

正反馈为主：尚书省成果（昨日完成节点/任务/合入 PR）+ 六部进展
奏本为次：状态过期/阻塞/待审核/7天内截止/反馈表待处理/未推送提交/缺日期待补录/读取失败
数据：飞书表格（反馈/任务/节点/决定四表）+ GitHub PR（gh）+ 本地 repo 自检
诚实契约：三源并列读取 + 本地同步自检（不做无依据的"一致"断言）；读源失败必须明说

┌────────────────────── 凭据边界 ──────────────────────┐
│ 本仓库为公开仓库。飞书 Base token 不入库，必须通过     │
│ 环境变量 LARK_BASE_TOKEN 提供；lark-cli 路径通过      │
│ LARK_CLI_PATH 提供（缺省使用本机默认安装路径）。       │
│ 含真实凭据的本地 cron 运行版位于                     │
│ <USER>\\AppData\\Local\\hermes\\scripts\\       │
│ daily_inspection.py，永不入库。                       │
└──────────────────────────────────────────────────────┘
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

DEFAULT_LARK_CLI = os.path.expanduser("~/AppData/Local/hermes/node/lark-cli")
# 显式解析 bash 绝对路径：CreateProcess 按裸名 "bash" 会先命中 System32 的 WSL 启动器
BASH = shutil.which("bash") or "bash"

TASKS_TBL = "tblArqwuZQtzIIdt"
NODES_TBL = "tblwEKyFdDDKG6aB"
DECISIONS_TBL = "tblZHOwWWZtWpv9b"
FEEDBACK_TBL = "tbldnGHlDjb9zfU5"
REPOS = ["Kairos-zhi/adaptive-digital-team"]
LOCAL_REPOS = {"Kairos-zhi/adaptive-digital-team": os.path.expanduser("~/adaptive-digital-team")}
REPORT_DIR = os.path.expanduser("~/hermes-sync/daily-reports")
WEEK_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def env_required(name):
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"[daily_inspection] 缺少必需环境变量 {name} —— 请 export {name}=<value> 后重试（凭据不得入库）")
    return v


def lark(args):
    cli = os.environ.get("LARK_CLI_PATH", "").strip() or DEFAULT_LARK_CLI
    r = subprocess.run([BASH, "-lc", f'"{cli}" {args}'], capture_output=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"ok": False, "raw": (r.stdout or b"").decode("utf-8", errors="replace")[:200]}


def load_rows(table_id):
    token = env_required("LARK_BASE_TOKEN")
    d = lark(f"base +record-list --as bot --base-token {token} --table-id {table_id} --json --limit 200")
    if not d.get("ok"):
        return None
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


def clip(s, n):
    s = str(s or "")
    if len(s) <= n:
        return s
    return s[:n].rstrip("（「,，、") + "…"


def save_report(text):
    try:
        os.makedirs(REPORT_DIR, exist_ok=True)
        path = os.path.join(REPORT_DIR, f"{date.today().isoformat()}.md")
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception:
        pass


def main():
    today = date.today()
    yesterday = today - timedelta(days=1)
    ys = str(yesterday)
    lines = []
    issues = []
    praise = []
    read_fails = []
    gh_fail = False

    tasks = load_rows(TASKS_TBL)
    if tasks is None:
        read_fails.append("任务表")
        tasks = []
    nodes = load_rows(NODES_TBL)
    if nodes is None:
        read_fails.append("节点表")
        nodes = []
    decisions = load_rows(DECISIONS_TBL)
    if decisions is None:
        read_fails.append("决定表")
        decisions = []
    feedbacks = load_rows(FEEDBACK_TBL)
    if feedbacks is None:
        read_fails.append("反馈表")
        feedbacks = []

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
        praise.append(f"任务『{clip(val(t.get('任务标题')), 24)}』完成")

    # ===== 尚书省：昨日合入 PR（gh） =====
    merged_prs = []
    for repo in REPOS:
        r = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--state", "merged", "--search", f"merged:{ys}",
             "--json", "number,title", "--limit", "10"],
            capture_output=True, text=True)
        try:
            prs = json.loads(r.stdout)
            for p in prs:
                merged_prs.append(f"PR #{p['number']} {clip(p['title'], 30)}")
        except Exception:
            gh_fail = True
    for m in merged_prs:
        praise.append(f"合入 {m}")

    # ===== 本地 repo 自检（第三源：真查不宣称） =====
    local_sync = True
    for repo, local_path in LOCAL_REPOS.items():
        try:
            r = subprocess.run(["git", "-C", local_path, "fetch", "origin", "--quiet"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                local_sync = False
                issues.append("本地检查失败: git fetch 失败")
                continue
            rc = subprocess.run(["git", "-C", local_path, "rev-list", "--count", "origin/main..HEAD"],
                                capture_output=True, text=True)
            if rc.returncode != 0 or not rc.stdout.strip():
                local_sync = False
                issues.append("本地检查失败: 无法统计未推送提交")
                continue
            n_unpushed = int(rc.stdout.strip())
            dirty = subprocess.run(["git", "-C", local_path, "status", "--porcelain"],
                                   capture_output=True, text=True).stdout.strip()
            if n_unpushed > 0:
                local_sync = False
                issues.append(f"本地有 {n_unpushed} 个未推送提交")
            if dirty:
                local_sync = False
                issues.append("本地 repo 工作区有未提交改动")
        except Exception as e:
            local_sync = False
            issues.append(f"本地 repo 检查失败: {str(e)[:40]}")
    if local_sync:
        praise.append("本地 repo 已同步（自检通过）")

    # ===== 六部：各线进展（空态不带 ✅） =====
    six_empty = []
    for proj in ["ADT", "Workshop（之lab 业务线）", "个人网站"]:
        active = [n for n in nodes if val(n.get("所属项目")) == proj and val(n.get("节点状态")) == "进行中"]
        if active:
            praise.append(f"{proj.split('（')[0]}线：进行中 {len(active)} 项（{'/'.join(clip(val(n.get('节点名称')), 10) for n in active[:3])}）")
        else:
            six_empty.append(f"{proj.split('（')[0]}线：无进行中节点")

    # ===== 门下省+都察院：累计已批准决定（头部统计行） =====
    approved_decisions = [d for d in decisions if str(val(d.get("决定状态"))) == "已批准"]

    # ===== 奏本：问题检测（保持巡检功能） =====
    for t in tasks:
        remark = val(t.get("备注"))
        status = val(t.get("任务状态"))
        if status != "已完成" and remark and ("已闭环" in remark or "已完成" in remark):
            issues.append(f"状态过期:『{clip(val(t.get('任务标题')), 22)}』备注已闭环但状态={status}")

    waiting = [t for t in tasks if val(t.get("任务状态")) == "待审核"]
    blocked = [t for t in tasks if val(t.get("任务状态")) == "阻塞"]

    # ===== 反馈表奏本：待处理反馈/洞察 =====
    fb_pending = [f for f in feedbacks if val(f.get("处理状态")) == "待处理"]
    if fb_pending:
        shown = fb_pending[:4]
        for f in shown:
            issues.append(f"{len(fb_pending)} 条待处理（前{len(shown)}）: 『{clip(val(f.get('反馈内容')), 20)}』")
        if len(fb_pending) > len(shown):
            issues.append(f"另有 {len(fb_pending) - len(shown)} 条")

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

    # ===== 昨日成果兜底：已完成但未填实际结束日期 =====
    completed_no_date = [n for n in nodes
                         if val(n.get("节点状态")) == "已完成"
                         and not str(val(n.get("实际结束")) or "").strip()]
    if completed_no_date:
        issues.append(f"{len(completed_no_date)} 个已完成节点未填实际结束日期（补录后才会进昨日成果）")

    # 昨日无成果记录：仅在三源全部读取成功时才触发（读取失败时不得下此结论）
    if not read_fails and not gh_fail and not done_nodes and not done_tasks and not merged_prs:
        issues.append("昨日无成果记录")

    # ===== 朝报排版 =====
    lines.append(f"📜 之lab 朝报 · {today.strftime('%m-%d')} {WEEK_CN[today.weekday()]}")
    lines.append(f"任务 {len(tasks)} | 节点 {len(nodes)} | 累计已批准决定 {len(approved_decisions)}")
    for tbl in read_fails:
        lines.append(f"⚠️ 飞书读取失败（{tbl}），该源数据不可信")
    if gh_fail:
        issues.append("GitHub 读取失败")
    if praise:
        lines.append("🏛️ 尚书省·昨日成果:")
        for p in praise[:8]:
            lines.append(f"  ✅ {p}")
        if len(praise) > 8:
            lines.append(f"  …另有 {len(praise)-8} 项")
    else:
        lines.append("🏛️ 尚书省·昨日成果:（空，昨日无完成记录）")
    if six_empty:
        for e in six_empty:
            lines.append(f"  ○ {e}")
    if waiting:
        lines.append(f"👑 待你拍板: " + "、".join(clip(val(t.get("任务标题")), 14) for t in waiting[:4]))
    if soon:
        soon_s = "、".join(f"{d.strftime('%m-%d')} {clip(t.split('（')[0], 10)}" for d, t in sorted(soon)[:5])
        lines.append(f"⏰ 7天内截止: {soon_s}")
    if blocked:
        lines.append(f"🚫 奏本·阻塞: " + "、".join(clip(val(t.get("任务标题")), 14) for t in blocked[:3]))
    if issues:
        lines.append("📢 奏本·需修正:")
        for i in issues[:5]:
            lines.append(f"  ⚠️ {i}")
    if not issues and not blocked and not read_fails:
        lines.append("📢 奏本: 无")
    tail = "本地同步 ✓" if local_sync else "本地同步 ✗（见奏本）"
    lines.append(f"— 三源并列读取 + 本地同步自检 · {tail} —")

    report = "\n".join(lines)
    save_report(report)
    print(report)


if __name__ == "__main__":
    main()
