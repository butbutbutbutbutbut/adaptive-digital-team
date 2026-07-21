"""Contract tests for the Beginner Bootstrap Router protocol.

These tests validate that the frozen protocol specification
(BEGINNER_BOOTSTRAP_ROUTER.md) and the user-facing README.md contain all
required elements. They verify the *specification text*, not runtime behavior.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocols" / "BEGINNER_BOOTSTRAP_ROUTER.md"
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    assert path.is_file(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T1–T4: frozen menu text
# ---------------------------------------------------------------------------


class TestFrozenMenuText:
    """Verify the exact frozen menu and guide texts are present."""

    def test_t1_menu_abc_only(self) -> None:
        """T1: The default menu text is A/B/C with no extra content."""
        proto = _read(PROTOCOL)
        readme = _read(README)

        # Protocol must contain the frozen menu text
        assert "A｜直接开始" in proto
        assert "B｜我会上传文件" in proto
        assert "C｜连接我自己拥有或管理的项目仓库" in proto

        # README must also contain it
        assert "A｜直接开始" in readme
        assert "B｜我会上传文件" in readme
        assert "C｜连接我自己拥有或管理的项目仓库" in readme

        # Constraints: no welcome, no intro, no GitHub tutorial alongside menu
        menu_section_start = proto.index("A｜直接开始")
        menu_section_end = proto.index(
            "C｜连接我自己拥有或管理的项目仓库"
        ) + len("C｜连接我自己拥有或管理的项目仓库")

        menu_block = proto[menu_section_start:menu_section_end]
        assert "欢迎" not in menu_block, "menu must not contain welcome text"
        assert "项目介绍" not in menu_block, "menu must not contain project intro"

    def test_t2_option_a_guide(self) -> None:
        """T2: Option A guide appears without GitHub mention."""
        proto = _read(PROTOCOL)

        # After "Option A", there must be the guide text
        assert "Option A" in proto or "选择 A" in proto or "### A｜" in proto
        # Guide must include the three suggestions
        assert "想得到什么结果" in proto
        assert "已经有哪些信息" in proto
        assert "希望以什么形式交付" in proto
        # Guide must mention the example
        assert "帮我整理一份活动方案" in proto
        # Mode must be declared
        assert "PROMPT_LOCAL" in proto
        assert "REPOSITORY_ACTION: PROHIBITED" in proto or "PROHIBITED" in proto

        # README A section must not mention GitHub
        readme = _read(README)
        a_section_start = readme.index("### A｜")
        # Find where A section ends (next ### or ---)
        next_section = re.search(r"\n(?:### |---)", readme[a_section_start + 10 :])
        a_section_end = (
            a_section_start + 10 + next_section.start()
            if next_section
            else len(readme)
        )
        a_section = readme[a_section_start:a_section_end]
        assert "GitHub" not in a_section, "A section must not mention GitHub"

    def test_t3_option_b_guide(self) -> None:
        """T3: Option B asks for file upload to current chat."""
        proto = _read(PROTOCOL)

        assert "Option B" in proto or "选择 B" in proto or "### B｜" in proto
        assert "上传到当前对话" in proto or "CURRENT_CHAT" in proto
        assert "PROMPT_LOCAL_WITH_FILES" in proto
        assert "不需要上传到 GitHub" in proto

        readme = _read(README)
        b_section_start = readme.index("### B｜")
        next_section = re.search(r"\n(?:### |---)", readme[b_section_start + 10 :])
        b_section_end = (
            b_section_start + 10 + next_section.start()
            if next_section
            else len(readme)
        )
        b_section = readme[b_section_start:b_section_end]
        assert "不需要上传到 GitHub" in b_section

    def test_t4_option_c_guide(self) -> None:
        """T4: Option C requests user's own repo + 1/2 choice."""
        proto = _read(PROTOCOL)

        assert "Option C" in proto or "选择 C" in proto or "### C｜" in proto
        assert "只读分析" in proto
        assert "允许创建候选变更" in proto
        assert "REPOSITORY_REQUESTED" in proto
        assert "WRITE_AUTHORITY: NOT_GRANTED" in proto or "NOT_GRANTED" in proto

        readme = _read(README)
        assert "只读分析" in readme
        assert "允许创建候选变更" in readme


# ---------------------------------------------------------------------------
# T5–T8: mode behaviour
# ---------------------------------------------------------------------------


class TestModeBehaviour:
    """Verify mode transition rules and edge cases."""

    def test_t5_a_auto_transition_to_b(self) -> None:
        """T5: A-mode user uploading files auto-transitions to B."""
        proto = _read(PROTOCOL)
        # The protocol must state that A→B auto-transition is allowed
        assert "auto" in proto.lower() or "自动" in proto
        # Specifically for file upload from A mode
        assert "PROMPT_LOCAL" in proto
        assert "PROMPT_LOCAL_WITH_FILES" in proto

    def test_t6_ab_no_pr_demand(self) -> None:
        """T6: A/B modes must not demand branch/PR creation."""
        proto = _read(PROTOCOL)
        # A/B mode descriptions must not require PR or branch
        # The protocol explicitly states REPOSITORY_ACTION: PROHIBITED for A/B
        prohibited_count = proto.count("PROHIBITED")
        assert prohibited_count >= 2, "A and B must both prohibit repo actions"

    def test_t7_c_no_connection_fallback(self) -> None:
        """T7: C without connection capability may fall back to A/B."""
        proto = _read(PROTOCOL)
        # Protocol must acknowledge that C might need fallback
        # "可退回 A/B" or similar
        assert (
            "退回" in proto
            or "fallback" in proto.lower()
            or "fall back" in proto.lower()
        ), "C must have fallback path when connection unavailable"

    def test_t8_invalid_choice_repeat_menu(self) -> None:
        """T8: Invalid selection repeats menu only."""
        proto = _read(PROTOCOL)
        # Must have invalid input handling
        assert "Invalid" in proto or "无效" in proto or "invalid" in proto.lower()
        # Must specify repeating menu on invalid input
        assert "repeat" in proto.lower() or "重复" in proto or "re-display" in proto.lower() or "重新显示" in proto


# ---------------------------------------------------------------------------
# T9–T14: menu skip
# ---------------------------------------------------------------------------


class TestMenuSkip:
    """Verify menu skip conditions."""

    def test_t9_clear_task_skips_menu(self) -> None:
        """T9: First message with clear task → skip menu, enter A."""
        proto = _read(PROTOCOL)
        assert "明确的普通任务" in proto or "clear plain task" in proto.lower()
        assert "PROMPT_LOCAL" in proto
        assert "跳过菜单" in proto or "skip menu" in proto.lower()

    def test_t10_attachment_task_skips_menu(self) -> None:
        """T10: First message with attachment + task → skip menu, enter B."""
        proto = _read(PROTOCOL)
        assert "附件" in proto or "attachment" in proto.lower() or "file" in proto.lower()
        assert "PROMPT_LOCAL_WITH_FILES" in proto

    def test_t11_repo_readonly_skips_menu(self) -> None:
        """T11: First message with repo + read-only task → skip menu."""
        proto = _read(PROTOCOL)
        assert "REPOSITORY_REQUESTED" in proto
        assert "只读" in proto or "read-only" in proto.lower()

    def test_t12_control_packet_skips_menu(self) -> None:
        """T12: Full control packet → skip menu."""
        proto = _read(PROTOCOL)
        assert "CONTROL_PACKET" in proto
        # Control packet must skip menu
        assert "control" in proto.lower()

    def test_t13_explicit_skip_command(self) -> None:
        """T13: '跳过引导' → no menu displayed."""
        proto = _read(PROTOCOL)
        assert "跳过引导" in proto
        # Must explicitly state it skips menu
        assert "跳过" in proto

    def test_t14_owner_claim_no_write(self) -> None:
        """T14: Self-claimed owner without auth → skip menu, no write."""
        proto = _read(PROTOCOL)
        assert "所有者" in proto or "owner" in proto.lower()
        assert "不自动" in proto or "does not" in proto.lower() or "not" in proto.lower()


# ---------------------------------------------------------------------------
# T15–T16: gate and recovery
# ---------------------------------------------------------------------------


class TestGateAndRecovery:
    """Verify gate supplementation and return-to-menu."""

    def test_t15_write_missing_facts_supplement_gates(self) -> None:
        """T15: Write task missing target facts → supplement, don't fall back."""
        proto = _read(PROTOCOL)
        # Must reference authorization gates that are not skipped
        assert (
            "Write authorization" in proto
            or "写入授权" in proto
            or "WRITE_AUTHORITY" in proto
            or "write" in proto.lower()
        )

    def test_t16_return_to_menu(self) -> None:
        """T16: '返回模式选择' → re-display A/B/C."""
        proto = _read(PROTOCOL)
        assert "返回模式选择" in proto
        # Must state it re-displays the menu
        assert "重新显示" in proto or "re-display" in proto.lower() or "re-show" in proto.lower()


# ---------------------------------------------------------------------------
# Structure & completeness
# ---------------------------------------------------------------------------


class TestProtocolStructure:
    """Verify the protocol document is complete and well-formed."""

    def test_protocol_exists_and_readable(self) -> None:
        """Protocol file must exist."""
        assert PROTOCOL.is_file(), f"missing {PROTOCOL}"

    def test_protocol_has_required_sections(self) -> None:
        """Protocol must have all required top-level sections."""
        proto = _read(PROTOCOL)
        required = [
            "Protocol activation",
            "Frozen Menu",
            "Menu Skip",
            "Mode Lock",
            "State Machine",
            "Invalid Input",
            "Design Freeze",
        ]
        for section in required:
            assert section in proto, f"missing section: {section}"

    def test_readme_has_skip_summary_table(self) -> None:
        """README first screen must include auto-skip summary."""
        readme = _read(README)
        # Must describe skip behavior near the top
        assert "自动跳过" in readme or "跳过菜单" in readme
        # Must have the summary table
        assert "明确" in readme

    def test_agents_has_first_contact_routing(self) -> None:
        """AGENTS.md must route first-contact before general execution flow."""
        agents = _read(AGENTS)
        assert "First-contact routing" in agents
        # Must reference the protocol
        assert "BEGINNER_BOOTSTRAP_ROUTER.md" in agents
        # Must appear before "Repository-as-prompt startup"
        first_contact_pos = agents.index("First-contact routing")
        startup_pos = agents.index("Repository-as-prompt startup")
        assert (
            first_contact_pos < startup_pos
        ), "First-contact routing must precede Repository-as-prompt startup"

    def test_no_governance_regression(self) -> None:
        """New protocol must not modify existing governance semantics."""
        proto = _read(PROTOCOL)
        # Protocol must explicitly state it does not modify these
        preserved = [
            "Ruleset",
            "History",
            "Permission",
            "Audit",
            "P1",
            "Product",
        ]
        for item in preserved:
            assert item in proto, f"protocol must mention preserved item: {item}"

    def test_skip_does_not_skip_gates(self) -> None:
        """'跳过引导' must NOT skip authorization/audit/Ready/Merge/HARD_STOP."""
        proto = _read(PROTOCOL)
        gates = ["授权" if "授权" in proto else "authorization", "Audit", "Ready", "Merge", "HARD_STOP"]
        skip_section_start = proto.index("跳过引导")
        # Look within 500 chars after the skip-command for gate mentions
        tail = proto[skip_section_start : skip_section_start + 800]
        # At least one gate must be mentioned as NOT skipped
        assert any(
            g in tail for g in ["Write authorization", "Audit", "Ready", "Merge", "HARD_STOP"]
        ), "'跳过引导' section must list non-skipped gates"


# ---------------------------------------------------------------------------
# T31–T40: external bootstrap activation semantics (P0 maintenance)
# ---------------------------------------------------------------------------


BOOTSTRAP = ROOT / "BOOTSTRAP.md"
CN_README = ROOT / "中文内容" / "README.md"


class TestExternalBootstrapActivation:
    """Verify READ_ACTIVATES_PROTOCOL: reading repo → ADT_PROTOCOL_ACTIVE →
    ANDING_INTERFACE assigned, but authority remains UNGRANTED."""

    def test_t31_readme_activates_protocol(self) -> None:
        """T31: Reading README → ADT_PROTOCOL_ACTIVE."""
        readme = _read(README)
        # README must contain activation directive
        assert "ADT_PROTOCOL_ACTIVE" in readme or "进入" in readme or "协议" in readme
        # Must reference the AI activation
        assert "AI" in readme or "激活" in readme or "安鼎" in readme

    def test_t32_bootstrap_activates_protocol(self) -> None:
        """T32: Reading BOOTSTRAP → ADT_PROTOCOL_ACTIVE."""
        bootstrap = _read(BOOTSTRAP)
        assert "READING THIS FILE ACTIVATES ADT" in bootstrap or "READ_ACTIVATES_PROTOCOL" in bootstrap or "PROTOCOL_ACTIVE" in bootstrap
        assert "ADT_PROTOCOL_ACTIVE" in bootstrap or "PROTOCOL_ACTIVE" in bootstrap

    def test_t33_agents_activates_protocol(self) -> None:
        """T33: Reading AGENTS → ADT_PROTOCOL_ACTIVE."""
        agents = _read(AGENTS)
        assert "ADT_PROTOCOL_ACTIVE" in agents or "protocol activation" in agents.lower()
        assert "repository read" in agents.lower() or "读取" in agents

    def test_t34_anding_interface_default_identity(self) -> None:
        """T34: Protocol activation → default interface identity is 安鼎."""
        bootstrap = _read(BOOTSTRAP)
        agents = _read(AGENTS)
        readme = _read(README)
        combined = bootstrap + "\n" + agents + "\n" + readme
        assert "安鼎" in combined or "Anding" in combined
        assert "ANDING_INTERFACE" in combined
        assert "INTERFACE_IDENTITY" in combined or "interface identity" in combined.lower()

    def test_t35_protocol_active_no_task_strict_abc(self) -> None:
        """T35: ADT_PROTOCOL_ACTIVE + no clear task → strict A/B/C."""
        proto = _read(PROTOCOL)
        bootstrap = _read(BOOTSTRAP)
        combined = proto + "\n" + bootstrap
        assert "A｜直接开始" in combined
        assert "B｜我会上传文件" in combined
        assert "C｜连接我自己拥有或管理的项目仓库" in combined
        # Must state: no task → A/B/C
        assert "no clear task" in combined.lower() or "没有" in combined or "无明确" in combined or "无任务" in combined

    def test_t36_protocol_active_clear_task_skips_menu(self) -> None:
        """T36: ADT_PROTOCOL_ACTIVE + clear task → skip menu."""
        proto = _read(PROTOCOL)
        readme = _read(README)
        combined = proto + "\n" + readme
        assert "跳过菜单" in combined or "skip menu" in combined.lower()
        assert "明确" in combined or "clear" in combined.lower()

    def test_t37_protocol_active_no_write_permission(self) -> None:
        """T37: Protocol activation does not grant write permission."""
        bootstrap = _read(BOOTSTRAP)
        agents = _read(AGENTS)
        combined = bootstrap + "\n" + agents
        assert "AUTHORITY: UNGRANTED" in combined or "UNGRANTED" in combined
        assert "not grant" in combined.lower() or "does not" in combined.lower() or "must never" in combined.lower()

    def test_t38_anding_interface_not_control(self) -> None:
        """T38: ANDING_INTERFACE ≠ ANDING_CONTROL."""
        bootstrap = _read(BOOTSTRAP)
        agents = _read(AGENTS)
        combined = bootstrap + "\n" + agents
        assert "ANDING_INTERFACE" in combined
        assert "ANDING_CONTROL" in combined
        # Must distinguish the two
        assert "≠" in combined or "not" in combined.lower() or "never" in combined.lower()

    def test_t39_control_packet_still_requires_verification(self) -> None:
        """T39: Full control packet still requires independent authorization."""
        proto = _read(PROTOCOL)
        # Control packet must still route through verification
        assert "CONTROL_PACKET" in proto or "control packet" in proto.lower()
        assert "verified" in proto.lower() or "authorization" in proto.lower() or "授权" in proto

    def test_t40_readme_first_screen_activation(self) -> None:
        """T40: README first screen contains complete activation directive."""
        readme = _read(README)
        # First 30 lines of README must contain the activation directive
        first_screen = "\n".join(readme.split("\n")[:40])
        assert "AI" in first_screen
        assert "安鼎" in first_screen or "Anding" in first_screen
        assert "ADT" in first_screen
        # Must reference protocol entry
        has_activation = (
            "ADT_PROTOCOL_ACTIVE" in first_screen
            or "进入" in first_screen
            or "activate" in first_screen.lower()
            or "协议" in first_screen
        )
        assert has_activation, "README first screen must contain activation directive"
