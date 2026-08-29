"""tests/test_self_authorization.py — P0-2 self-authorization closure regression (Maker M2).

Attack PoCs (all must be BLOCKED / HARD_STOP):
  ① scope 自指 binding（authorized_write_scope 含 .hermes/CANDIDATE_BINDING.json）→ validator FAIL
  ② 删除 binding 文件后 guarded_write → BLOCKED（不得走 PROJECT_STATE 合成授权）
  ③ 篡改 binding（human_holder_approved 翻 true + 过期 base_sha / 错误 branch / 损坏 JSON）→ BLOCKED
  ④ UNGRANTED 空闲态：validate_binding.py 静态模式与 --ci 模式均 PASS
  ⑤ legacy 合成路径：PROJECT_STATE.md 独载授权字段不再放行

Plus positive controls: valid granted binding + in-scope write → COMPLETED.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate_binding import BindingValidator, HARD_STOP  # noqa: E402

REPO = "Kairos-zhi/adaptive-digital-team"

# ---------------------------------------------------------------------------
# Validator fixtures
# ---------------------------------------------------------------------------


def _stable_state(**changes) -> str:
    """PROJECT_STATE.md with only stable fields (schema v2)."""
    import yaml

    value = {
        "schema_version": "2",
        "repository": REPO,
        "authority": {"holder": "Kairos", "maker": "UNASSIGNED", "checker": "UNASSIGNED"},
        "current_gate": "NO_ACTIVE_CANDIDATE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    value.update(changes)
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


def _legacy_state(**changes) -> str:
    """PROJECT_STATE.md WITH transient fields (pre-decoupling format)."""
    import yaml

    value = {
        "schema_version": "2",
        "task_id": "ADT-LEGACY-001",
        "repository": REPO,
        "branch": "maker/legacy",
        "starting_base_sha": "0" * 40,
        "authorized_write_scope": ["docs/"],
        "authority": {"holder": "Kairos", "maker": "UNASSIGNED", "checker": "UNASSIGNED"},
        "current_gate": "FINAL_CANDIDATE_FREEZE",
        "implementation_status": "NOT_AUTHORIZED",
    }
    value.update(changes)
    return "```yaml\n" + yaml.safe_dump(value, sort_keys=False) + "```\n"


def _make_binding(**overrides) -> dict:
    binding = {
        "authorization_id": "ADT-M2-TEST-001",
        "authority_source": "Human Holder directive",
        "human_role": "HUMAN_HOLDER",
        "repository": REPO,
        "base_sha": "0" * 40,
        "branch": "maker/test",
        "authorized_actions": ["read", "write_file", "commit", "push"],
        "authorized_write_scope": ["docs/"],
        "task_id": "ADT-M2-TEST-001",
        "human_holder_approved": True,
    }
    binding.update(overrides)
    return binding


UNGRANTED = {
    "authorization_id": "UNGRANTED",
    "authority_source": "NO_AUTHORIZATION",
    "human_role": "HUMAN_HOLDER",
    "repository": REPO,
    "base_sha": "",
    "branch": "",
    "authorized_actions": [],
    "authorized_write_scope": [],
    "risk_boundary": None,
    "task_id": "",
    "human_holder_approved": False,
}


def _write_binding(tmp_path: Path, binding: dict) -> Path:
    hermes_dir = tmp_path / ".hermes"
    hermes_dir.mkdir(parents=True, exist_ok=True)
    path = hermes_dir / "CANDIDATE_BINDING.json"
    path.write_text(json.dumps(binding, ensure_ascii=False))
    return path


# ═══════════════════════════════════════════════════════════════════
# ① 自指 scope → validator FAIL
# ═══════════════════════════════════════════════════════════════════


class TestSelfReferentialScope:
    def test_self_referential_scope_fails(self, tmp_path, monkeypatch):
        binding = _make_binding(authorized_write_scope=[".hermes/CANDIDATE_BINDING.json"])
        _write_binding(tmp_path, binding)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state())
        assert not v.validate()
        assert any("SELF_REFERENTIAL_SCOPE" in e for e in v.errors)

    def test_self_referential_scope_with_backslash_fails(self, tmp_path, monkeypatch):
        binding = _make_binding(authorized_write_scope=[".hermes\\CANDIDATE_BINDING.json"])
        _write_binding(tmp_path, binding)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state())
        assert not v.validate()
        assert any("SELF_REFERENTIAL_SCOPE" in e for e in v.errors)

    def test_normal_scope_not_flagged(self, tmp_path, monkeypatch):
        binding = _make_binding(authorized_write_scope=["docs/", "protocols/"])
        _write_binding(tmp_path, binding)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state())
        assert v.validate()


# ═══════════════════════════════════════════════════════════════════
# ② binding 缺失 → validator HARD_STOP（legacy 合成移除）
# ═══════════════════════════════════════════════════════════════════


class TestMissingBindingFailClosed:
    def test_missing_binding_with_legacy_transient_fields_hard_stops(self, tmp_path, monkeypatch):
        """PROJECT_STATE.md alone (even with transient fields) no longer authorizes."""
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_legacy_state())
        assert not v.validate()
        assert any("CANDIDATE_BINDING.json missing" in e for e in v.errors)
        assert any(HARD_STOP in e for e in v.errors)

    def test_missing_binding_with_stable_only_hard_stops(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state())
        assert not v.validate()
        assert any("CANDIDATE_BINDING.json missing" in e for e in v.errors)


# ═══════════════════════════════════════════════════════════════════
# ④ UNGRANTED 空闲态 → 静态 + --ci 均 PASS
# ═══════════════════════════════════════════════════════════════════


class TestUngrantedIdleState:
    def test_idle_static_passes(self, tmp_path, monkeypatch):
        _write_binding(tmp_path, UNGRANTED)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state())
        assert v.validate()
        assert v.candidate_state == "UNGRANTED_IDLE"

    def test_idle_ci_mode_passes(self, tmp_path, monkeypatch):
        """Simulate CI push to main with UNGRANTED idle binding → PASS."""
        _write_binding(tmp_path, UNGRANTED)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state(), live_mode=True)
        monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
        monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
        monkeypatch.setenv("GITHUB_SHA", "a" * 40)
        monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
        monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
        v._runtime_head = lambda: "a" * 40
        v._remote_head = lambda b: "a" * 40
        v._changed_files = lambda base, head: [".hermes/CANDIDATE_BINDING.json"]
        v._ci_changed_files = lambda ev: [".hermes/CANDIDATE_BINDING.json"]
        v._local_changed_files = lambda: [".hermes/CANDIDATE_BINDING.json"]
        v._commit_exists = lambda sha: True
        v._is_ancestor = lambda a, b: True
        v._event_payload = lambda: {"before": "b" * 40}
        assert v.validate()
        assert v.candidate_state == "UNGRANTED_IDLE"

    def test_idle_ci_bare_local_mode_passes(self, tmp_path, monkeypatch):
        """Bare `--ci` run (no GitHub env vars) with UNGRANTED idle → PASS.

        Regression for the M2 打回: idle state previously fell into the
        local-mode pre-write gate (exact base not declared) and local identity
        resolution (identity mismatch), producing HARD_STOP under --ci.
        """
        _write_binding(tmp_path, UNGRANTED)
        monkeypatch.chdir(tmp_path)
        # Clear any GitHub CI env vars — bare local run
        for var in ("GITHUB_EVENT_NAME", "GITHUB_REF", "GITHUB_SHA",
                    "GITHUB_REPOSITORY", "GITHUB_EVENT_PATH"):
            monkeypatch.delenv(var, raising=False)
        v = BindingValidator(_stable_state(), live_mode=True)
        assert v.validate()
        assert v.candidate_state == "UNGRANTED_IDLE"
        assert not any(HARD_STOP in e for e in v.errors)

    def test_idle_does_not_trip_scope_checks(self, tmp_path, monkeypatch):
        """Idle template has empty scope — must NOT raise SCOPE_VIOLATION."""
        _write_binding(tmp_path, UNGRANTED)
        monkeypatch.chdir(tmp_path)
        v = BindingValidator(_stable_state(), live_mode=True)
        monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
        monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
        monkeypatch.setenv("GITHUB_SHA", "a" * 40)
        monkeypatch.setenv("GITHUB_REPOSITORY", REPO)
        monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
        v._runtime_head = lambda: "a" * 40
        v._remote_head = lambda b: "a" * 40
        v._changed_files = lambda base, head: [".hermes/CANDIDATE_BINDING.json"]
        v._ci_changed_files = lambda ev: [".hermes/CANDIDATE_BINDING.json"]
        v._local_changed_files = lambda: [".hermes/CANDIDATE_BINDING.json"]
        v._commit_exists = lambda sha: True
        v._is_ancestor = lambda a, b: True
        v._event_payload = lambda: {"before": "b" * 40}
        assert v.validate()
        assert not any("SCOPE_VIOLATION" in e for e in v.errors)


# ═══════════════════════════════════════════════════════════════════
# guarded_write 运行时门控（真实插件模块）
# ═══════════════════════════════════════════════════════════════════

PLUGIN_DIR = REPO_ROOT / ".hermes" / "plugins" / "guarded_adapter"
PKG = "adt_ga_m2_under_test"


def _load(name: str, path: Path, is_pkg: bool = False):
    spec = importlib.util.spec_from_file_location(
        name,
        str(path),
        submodule_search_locations=[str(path.parent)] if is_pkg else None,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_pkg = _load(PKG, PLUGIN_DIR / "__init__.py", is_pkg=True)
runtime_models = _load(f"{PKG}.runtime_models", PLUGIN_DIR / "runtime_models.py")
gate = _load(f"{PKG}.gate", PLUGIN_DIR / "gate.py")
if (PLUGIN_DIR / "tools" / "__init__.py").exists():
    _load(f"{PKG}.tools", PLUGIN_DIR / "tools" / "__init__.py", is_pkg=True)
else:
    import types

    _tp = types.ModuleType(f"{PKG}.tools")
    _tp.__path__ = [str(PLUGIN_DIR / "tools")]  # type: ignore[attr-defined]
    sys.modules[f"{PKG}.tools"] = _tp
guarded_write = _load(f"{PKG}.tools.guarded_write", PLUGIN_DIR / "tools" / "guarded_write.py")


@pytest.fixture()
def tmp_repo(tmp_path, monkeypatch):
    """Redirect plugin _REPO_ROOT to tmp repo and stub drift probes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    monkeypatch.setattr(runtime_models, "_REPO_ROOT", repo)
    monkeypatch.setattr(guarded_write, "_REPO_ROOT", repo)
    monkeypatch.setattr(gate, "_REPO_ROOT", repo)  # resolve_repo_target uses gate._REPO_ROOT
    monkeypatch.setattr(gate, "_get_current_repo", lambda: REPO)
    monkeypatch.setattr(gate, "_get_current_base_sha", lambda: "0" * 40)
    monkeypatch.setattr(gate, "_get_current_branch", lambda: "maker/test")
    return repo


def _valid_binding_ctx():
    return {
        "plan_write_scope": ["docs/"],
        "authorized_write_scope": ["docs/"],
        "authorization_binding": _make_binding(),
        "branch": "maker/test",
        "base_sha": "0" * 40,
    }


class TestGuardedWriteSelfAuth:
    def test_missing_binding_blocks_no_fallback(self, tmp_repo, monkeypatch):
        """② 删除 binding 文件 → BLOCKED，绝不从 PROJECT_STATE 合成授权。"""
        # tmp_repo has no .hermes/CANDIDATE_BINDING.json and no PROJECT_STATE.md
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert "AUTHORIZED" in resp.get("adapter_error", "") or "PLAN_WRITE_SCOPE" in resp.get("adapter_error", "")

    def test_missing_binding_blocks_even_with_project_state(self, tmp_repo, monkeypatch):
        """即使 PROJECT_STATE.md 携带授权字段也不得合成（legacy fallback 已删）。"""
        (tmp_repo / "PROJECT_STATE.md").write_text(
            "```yaml\n"
            "task_id: ADT-LEGACY\n"
            "branch: maker/test\n"
            "starting_base_sha: '0000000000000000000000000000000000000000'\n"
            "authorized_write_scope: ['docs/']\n"
            "```\n",
            encoding="utf-8",
        )
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"

    def test_tampered_approval_with_stale_base_blocks(self, tmp_repo, monkeypatch):
        """③ 篡改 human_holder_approved=true + 过期 base_sha → drift → BLOCKED。"""
        # Stub probes to REAL current values ("0"*40 repo / branch maker/test)
        binding = _make_binding(human_holder_approved=True, base_sha="1" * 40)
        _write_binding(tmp_repo, binding)
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert "BINDING" in resp.get("gate_error", "") or "BINDING" in resp.get("adapter_error", "")

    def test_tampered_wrong_branch_blocks(self, tmp_repo, monkeypatch):
        binding = _make_binding(branch="hermes/wrong-branch")
        _write_binding(tmp_repo, binding)
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert "BINDING" in resp.get("gate_error", "")

    def test_corrupted_binding_blocks(self, tmp_repo):
        hermes = tmp_repo / ".hermes"
        hermes.mkdir(parents=True, exist_ok=True)
        (hermes / "CANDIDATE_BINDING.json").write_text("not json {{{")
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"

    def test_ungranted_template_blocks(self, tmp_repo):
        """空闲态模板不授权任何写入。"""
        _write_binding(tmp_repo, UNGRANTED)
        resp = guarded_write.guarded_write_handler("docs/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"

    def test_valid_binding_in_scope_completes(self, tmp_repo, monkeypatch):
        """正向对照：合法授权 + 范围内路径 → COMPLETED。"""
        _write_binding(tmp_repo, _make_binding())
        resp = guarded_write.guarded_write_handler("docs/new.md", "hello")
        assert resp["adapter_execution_status"] == "COMPLETED", resp
        assert (tmp_repo / "docs" / "new.md").read_text(encoding="utf-8") == "hello"

    def test_valid_binding_out_of_scope_blocks(self, tmp_repo):
        _write_binding(tmp_repo, _make_binding())
        resp = guarded_write.guarded_write_handler("secret/x.md", "content")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert "ATTEMPTED_SCOPE_VIOLATION" in resp.get("adapter_error", "")


class TestLoadBindingFailClosed:
    def test_missing_raises(self, tmp_repo):
        with pytest.raises(Exception):
            runtime_models.load_binding()

    def test_ungranted_raises(self, tmp_repo):
        _write_binding(tmp_repo, UNGRANTED)
        with pytest.raises(ValueError):
            runtime_models.load_binding()

    def test_corrupted_raises(self, tmp_repo):
        hermes = tmp_repo / ".hermes"
        hermes.mkdir(parents=True, exist_ok=True)
        (hermes / "CANDIDATE_BINDING.json").write_text("{broken")
        with pytest.raises(ValueError):
            runtime_models.load_binding()
