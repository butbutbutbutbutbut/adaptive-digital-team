"""tests/test_gate_path_security.py — P0-1 path traversal regression suite (Maker M1).

Attack PoCs (all must be BLOCKED):
  1. "a/../secret" with scope ["a/"]         (interior ".." traversal)
  2. Absolute paths ("/etc/passwd", "C:/Windows/x", UNC)
  3. Repo-internal symlink pointing outside the repo
  4. Case/separator variants ("A\\..\\secret")

Plus positive controls: legitimate in-scope writes must still COMPLETE.

The real plugin modules under .hermes/plugins/guarded_adapter/ are loaded via
importlib (the ".hermes" directory is not an importable package name).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = REPO_ROOT / ".hermes" / "plugins" / "guarded_adapter"

PKG = "adt_guarded_adapter_under_test"


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


# Load the REAL plugin modules (no mirrors, no re-implementations)
_pkg = _load(PKG, PLUGIN_DIR / "__init__.py", is_pkg=True)
runtime_models = _load(f"{PKG}.runtime_models", PLUGIN_DIR / "runtime_models.py")
gate = _load(f"{PKG}.gate", PLUGIN_DIR / "gate.py")
_tools_pkg = _load(f"{PKG}.tools", PLUGIN_DIR / "tools" / "__init__.py", is_pkg=True) \
    if (PLUGIN_DIR / "tools" / "__init__.py").exists() else None
if _tools_pkg is None:
    # Synthesize an empty package module for the namespace "tools" directory
    import types

    _tools_pkg = types.ModuleType(f"{PKG}.tools")
    _tools_pkg.__path__ = [str(PLUGIN_DIR / "tools")]  # type: ignore[attr-defined]
    sys.modules[f"{PKG}.tools"] = _tools_pkg
guarded_write = _load(f"{PKG}.tools.guarded_write", PLUGIN_DIR / "tools" / "guarded_write.py")
guarded_repo_actions = _load(
    f"{PKG}.tools.guarded_repo_actions", PLUGIN_DIR / "tools" / "guarded_repo_actions.py"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_BINDING = {
    "authorization_id": "ADT-TEST-P0-1",
    "authority_source": "TEST_FIXTURE",
    "human_role": "HUMAN_HOLDER",
    "repository": "owner/repo",
    "base_sha": "0" * 40,
    "branch": "maker/test",
    "authorized_actions": ["write_file", "commit"],
    "authorized_write_scope": ["a/"],
    "human_holder_approved": True,
}


@pytest.fixture()
def tmp_repo(tmp_path, monkeypatch):
    """Redirect the gate/tools _REPO_ROOT to a tmp repo and stub git probes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a").mkdir()
    (repo / "a" / "ok.txt").write_text("ok", encoding="utf-8")
    (repo / "secret.txt").write_text("TOP SECRET", encoding="utf-8")

    for mod in (gate, guarded_write, guarded_repo_actions):
        monkeypatch.setattr(mod, "_REPO_ROOT", repo)

    # Stub git drift probes so a synthetic binding validates cleanly
    monkeypatch.setattr(gate, "_get_current_repo", lambda: "owner/repo")
    monkeypatch.setattr(gate, "_get_current_base_sha", lambda: "0" * 40)
    monkeypatch.setattr(gate, "_get_current_branch", lambda: "maker/test")
    return repo


def _gate_request(path: str, scopes=("a/",)) -> gate.GateRequest:
    binding = dict(VALID_BINDING)
    binding["authorized_write_scope"] = list(scopes)
    return gate.GateRequest(
        action_type="write_file",
        action_path=path,
        plan_write_scope=list(scopes),
        authorized_write_scope=list(scopes),
        authorization_binding=binding,
    )


# ---------------------------------------------------------------------------
# PoC 1: interior ".." traversal — "a/../secret" with scope ["a/"]
# ---------------------------------------------------------------------------

class TestDotDotTraversal:
    def test_normalize_rejects_interior_dotdot(self):
        assert gate.normalize_repo_path("a/../secret") is None

    def test_normalize_rejects_leading_dotdot(self):
        assert gate.normalize_repo_path("../secret") is None

    def test_normalize_rejects_trailing_dotdot(self):
        assert gate.normalize_repo_path("a/..") is None

    def test_gate_blocks_dotdot_with_parent_scope(self, tmp_repo):
        result = gate.validate_scope(_gate_request("a/../secret"))
        assert not result.allowed
        assert "PATH_TRAVERSAL_REJECTED" in (result.error or "")

    def test_write_handler_blocks_dotdot(self, tmp_repo, monkeypatch):
        monkeypatch.setattr(
            guarded_write,
            "_resolve_scope_context",
            lambda: {
                "plan_write_scope": ["a/"],
                "authorized_write_scope": ["a/"],
                "authorization_binding": dict(VALID_BINDING),
            },
        )
        resp = guarded_write.guarded_write_handler("a/../secret.txt", "pwned")
        assert resp["adapter_execution_status"] == "BLOCKED"
        # The secret file outside scope must be untouched
        assert (tmp_repo / "secret.txt").read_text(encoding="utf-8") == "TOP SECRET"


# ---------------------------------------------------------------------------
# PoC 2: absolute paths
# ---------------------------------------------------------------------------

class TestAbsolutePaths:
    @pytest.mark.parametrize(
        "path",
        ["/etc/passwd", "/abs/evil.txt", "C:/Windows/evil.txt", "c:\\windows\\evil.txt", "//host/share/evil.txt"],
    )
    def test_normalize_rejects_absolute(self, path):
        assert gate.normalize_repo_path(path) is None

    @pytest.mark.parametrize("path", ["/etc/passwd", "C:/Windows/evil.txt"])
    def test_gate_blocks_absolute(self, tmp_repo, path):
        result = gate.validate_scope(_gate_request(path))
        assert not result.allowed
        assert "PATH_TRAVERSAL_REJECTED" in (result.error or "")

    def test_write_handler_blocks_absolute(self, tmp_repo, monkeypatch, tmp_path):
        outside = tmp_path / "outside_abs.txt"
        monkeypatch.setattr(
            guarded_write,
            "_resolve_scope_context",
            lambda: {
                "plan_write_scope": ["a/"],
                "authorized_write_scope": ["a/"],
                "authorization_binding": dict(VALID_BINDING),
            },
        )
        resp = guarded_write.guarded_write_handler(str(outside).replace("\\", "/"), "pwned")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert not outside.exists()


# ---------------------------------------------------------------------------
# PoC 3: symlink inside the repo pointing outside
# ---------------------------------------------------------------------------

class TestSymlinkEscape:
    def test_resolve_rejects_symlink_escape(self, tmp_repo, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        link = tmp_repo / "a" / "link"
        try:
            os.symlink(str(outside), str(link), target_is_directory=True)
        except (OSError, NotImplementedError) as e:
            pytest.skip(f"symlink creation not permitted on this platform: {e}")

        # "a/link/evil.txt" passes the scope string check ("a/" prefix) but
        # resolves outside the repo — must be rejected by resolve_repo_target.
        assert gate._check_path_in_scope("a/link/evil.txt", ["a/"]) is True  # string-level only
        assert gate.resolve_repo_target("a/link/evil.txt") is None

    def test_write_handler_blocks_symlink_escape(self, tmp_repo, tmp_path, monkeypatch):
        outside = tmp_path / "outside"
        outside.mkdir()
        link = tmp_repo / "a" / "link"
        try:
            os.symlink(str(outside), str(link), target_is_directory=True)
        except (OSError, NotImplementedError) as e:
            pytest.skip(f"symlink creation not permitted on this platform: {e}")

        monkeypatch.setattr(
            guarded_write,
            "_resolve_scope_context",
            lambda: {
                "plan_write_scope": ["a/"],
                "authorized_write_scope": ["a/"],
                "authorization_binding": dict(VALID_BINDING),
            },
        )
        resp = guarded_write.guarded_write_handler("a/link/evil.txt", "pwned")
        assert resp["adapter_execution_status"] == "BLOCKED"
        assert not (outside / "evil.txt").exists()


# ---------------------------------------------------------------------------
# PoC 4: case / separator variants
# ---------------------------------------------------------------------------

class TestCaseSeparatorVariants:
    @pytest.mark.parametrize(
        "path",
        ["A\\..\\secret", "a\\..\\secret.txt", "./a/../secret", "a//..//secret"],
    )
    def test_variants_rejected(self, tmp_repo, path):
        assert gate.normalize_repo_path(path) is None
        result = gate.validate_scope(_gate_request(path))
        assert not result.allowed

    def test_backslash_in_scope_path_normalized(self):
        # Legitimate backslash-separated relative path still works
        assert gate.normalize_repo_path("a\\sub\\file.txt") == "a/sub/file.txt"
        assert gate._check_path_in_scope("a\\sub\\file.txt", ["a/"]) is True


# ---------------------------------------------------------------------------
# Positive controls — legitimate writes must keep working
# ---------------------------------------------------------------------------

class TestPositiveControls:
    def test_normalize_simple(self):
        assert gate.normalize_repo_path("a/ok.txt") == "a/ok.txt"

    def test_normalize_strips_dot_segments(self):
        assert gate.normalize_repo_path("./a/ok.txt") == "a/ok.txt"

    def test_scope_exact_file_match(self):
        assert gate._check_path_in_scope("x.md", ["x.md"]) is True
        assert gate._check_path_in_scope("x.md", ["y.md"]) is False

    def test_scope_prefix_match(self):
        assert gate._check_path_in_scope("a/b/c.txt", ["a/"]) is True
        assert gate._check_path_in_scope("ab/c.txt", ["a/"]) is False

    def test_gate_allows_in_scope_write(self, tmp_repo):
        result = gate.validate_scope(_gate_request("a/new.txt"))
        assert result.allowed, result.error

    def test_write_handler_completes_in_scope(self, tmp_repo, monkeypatch):
        monkeypatch.setattr(
            guarded_write,
            "_resolve_scope_context",
            lambda: {
                "plan_write_scope": ["a/"],
                "authorized_write_scope": ["a/"],
                "authorization_binding": dict(VALID_BINDING),
            },
        )
        resp = guarded_write.guarded_write_handler("a/new.txt", "hello")
        assert resp["adapter_execution_status"] == "COMPLETED", resp
        assert (tmp_repo / "a" / "new.txt").read_text(encoding="utf-8") == "hello"

    def test_out_of_scope_relative_path_blocked(self, tmp_repo):
        result = gate.validate_scope(_gate_request("b/new.txt"))
        assert not result.allowed
        assert "ATTEMPTED_SCOPE_VIOLATION" in (result.error or "")

    def test_repo_actions_add_rejects_traversal(self, tmp_repo, monkeypatch):
        monkeypatch.setattr(
            guarded_repo_actions,
            "_resolve_scope_context",
            lambda: {
                "plan_write_scope": ["a/"],
                "authorized_write_scope": ["a/"],
                "authorization_binding": dict(VALID_BINDING),
                "branch": "maker/test",
                "base_sha": "0" * 40,
            },
        )
        resp = guarded_repo_actions.guarded_repo_actions_handler(
            action="git_add_authorized_paths", paths=["a/../secret.txt"]
        )
        assert resp["adapter_execution_status"] == "BLOCKED"
