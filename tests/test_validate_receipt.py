from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = str(ROOT / "scripts" / "validate_receipt.py")

sys.path.insert(0, str(ROOT / "scripts"))
from validate_receipt import validate  # noqa: E402


def _run(file_path: str | None = None, stdin_text: str | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, VALIDATOR]
    if file_path:
        cmd.extend(["--file", file_path])
    elif stdin_text is not None:
        cmd.append("--stdin")
    return subprocess.run(cmd, capture_output=True, text=True, input=stdin_text)


def kv_receipt(**overrides: str) -> str:
    defaults = {
        "FACT": "Branch created with initial scaffold",
        "AUTHORITY": "ADT-VALIDATE-RECEIPT-R1",
        "ACTION": "Created validate_receipt.py",
        "RESULT": "Script passes all tests",
        "ARTIFACT_TYPE": "script",
        "ARTIFACT_LOCATION": "scripts/validate_receipt.py",
    }
    defaults.update(overrides)
    return "\n".join(f"{k}: {v}" for k, v in defaults.items())


def json_receipt(**overrides: str) -> str:
    import json
    defaults = {
        "FACT": "Branch created with initial scaffold",
        "AUTHORITY": "ADT-VALIDATE-RECEIPT-R1",
        "ACTION": "Created validate_receipt.py",
        "RESULT": "Script passes all tests",
        "ARTIFACT_TYPE": "script",
        "ARTIFACT_LOCATION": "scripts/validate_receipt.py",
    }
    defaults.update(overrides)
    return json.dumps(defaults)


class TestValidateFunction:
    def test_all_fields_present_kv(self):
        passed, missing = validate(kv_receipt())
        assert passed is True
        assert missing == []

    def test_all_fields_present_json(self):
        passed, missing = validate(json_receipt())
        assert passed is True
        assert missing == []

    def test_missing_one_field(self):
        content = "\n".join(
            line for line in kv_receipt().splitlines()
            if not line.startswith("FACT:")
        )
        passed, missing = validate(content)
        assert passed is False
        assert missing == ["FACT"]

    def test_missing_multiple_fields(self):
        content = "FACT: something\nAUTHORITY: someone\n"
        passed, missing = validate(content)
        assert passed is False
        assert set(missing) == {"ACTION", "RESULT", "ARTIFACT_TYPE", "ARTIFACT_LOCATION"}

    def test_empty_receipt(self):
        passed, missing = validate("")
        assert passed is False
        assert set(missing) == {
            "FACT", "AUTHORITY", "ACTION", "RESULT",
            "ARTIFACT_TYPE", "ARTIFACT_LOCATION",
        }

    def test_whitespace_only(self):
        passed, missing = validate("   \n  \n  ")
        assert passed is False
        assert set(missing) == {
            "FACT", "AUTHORITY", "ACTION", "RESULT",
            "ARTIFACT_TYPE", "ARTIFACT_LOCATION",
        }

    def test_unknown_fields_ignored(self):
        content = kv_receipt() + "\nMOOD: happy\nWEATHER: cloudy\n"
        passed, missing = validate(content)
        assert passed is True
        assert missing == []


class TestCLI:
    def test_file_argument_pass(self, tmp_path: Path):
        receipt = tmp_path / "receipt.txt"
        receipt.write_text(kv_receipt(), encoding="utf-8")
        proc = _run(file_path=str(receipt))
        assert proc.returncode == 0
        assert proc.stdout.strip() == "PASS"

    def test_file_argument_fail(self, tmp_path: Path):
        receipt = tmp_path / "receipt.txt"
        receipt.write_text("FACT: only one field\n", encoding="utf-8")
        proc = _run(file_path=str(receipt))
        assert proc.returncode == 1
        assert proc.stdout.strip().startswith("FAIL: missing:")

    def test_stdin_pass(self):
        proc = _run(stdin_text=kv_receipt())
        assert proc.returncode == 0
        assert proc.stdout.strip() == "PASS"

    def test_stdin_fail(self):
        proc = _run(stdin_text="FACT: just fact\n")
        assert proc.returncode == 1
        assert "missing:" in proc.stdout

    def test_file_not_found(self):
        proc = _run(file_path="/nonexistent/path/receipt.txt")
        assert proc.returncode != 0

    def test_empty_file(self, tmp_path: Path):
        receipt = tmp_path / "receipt.txt"
        receipt.write_text("", encoding="utf-8")
        proc = _run(file_path=str(receipt))
        assert proc.returncode == 1
        assert "missing:" in proc.stdout
