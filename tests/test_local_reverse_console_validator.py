"""Tests for local_reverse_console_validator.

These tests use temporary Python subprocesses or mocks to avoid depending on
real PE binaries or E:\reverse paths.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from reverse_agent.local_reverse_console_validator import (
    _resolve_target_path,
    _sha256_file,
    validate_console_candidate,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_triage_artifact(tmp_path: Path, relative_path: str = "逆向课程2023春补考01/Cpp1.exe", sha256: str | None = None) -> Path:
    triage: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp1_7b504c54",
        "relative_path": relative_path,
    }
    if sha256 is not None:
        triage["sha256"] = sha256
    p = tmp_path / "triage.json"
    p.write_text(json.dumps(triage), encoding="utf-8")
    return p


def _make_candidate_artifact(tmp_path: Path, candidate: str | None = "WeKnowItOk") -> Path:
    cand = {
        "schema_version": 1,
        "sample_id": "cpp1_7b504c54",
        "static_candidate_text": candidate,
    }
    p = tmp_path / "candidate.json"
    p.write_text(json.dumps(cand), encoding="utf-8")
    return p


def _run_mock_subprocess(mock_path: Path, stdin_payload: str) -> tuple[str, str, int]:
    """Run the mock Python script as a real subprocess and return stdout, stderr, rc."""
    proc = subprocess.run(
        [sys.executable, str(mock_path)],
        input=stdin_payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return proc.stdout, proc.stderr, proc.returncode


def _make_mock_target_script(tmp_path: Path, behavior: str) -> Path:
    """Create a Python script that mimics a console PE behavior."""
    script = tmp_path / "mock_target.py"
    code = f'''import sys

data = sys.stdin.read().strip()
if data.endswith("\\n\\n"):
    data = data[:-2]
if data.endswith("\\n"):
    data = data[:-1]

behavior = "{behavior}"
if behavior == "success":
    if len(data) == 10:
        print("Congratulations! You are right!")
    elif len(data) != 10:
        print("Sorry, the length is wrong!")
    else:
        print("Sorry, you are wrong!")
elif behavior == "failure":
    print("Sorry, you are wrong!")
elif behavior == "length_error":
    print("Sorry, the length is wrong!")
elif behavior == "ambiguous":
    print("Some random output")
elif behavior == "hang":
    import time
    time.sleep(60)
'''
    script.write_text(code, encoding="utf-8")
    return script


# ── Tests for _resolve_target_path ───────────────────────────────────────────


class TestResolveTargetPath:
    def test_finds_via_env(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        target = sub / "a.exe"
        target.write_text("x")
        with patch.dict("os.environ", {"LOCAL_REVERSE_ROOT": str(tmp_path)}):
            result = _resolve_target_path("sub/a.exe")
        assert result == target

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        with patch.dict("os.environ", {"LOCAL_REVERSE_ROOT": str(tmp_path)}):
            result = _resolve_target_path("missing.exe")
        assert result is None


# ── Tests for _sha256_file ───────────────────────────────────────────────────


class TestSha256File:
    def test_known_content(self, tmp_path: Path) -> None:
        p = tmp_path / "f.txt"
        p.write_text("hello", encoding="utf-8")
        h = _sha256_file(p)
        import hashlib
        assert h == hashlib.sha256(b"hello").hexdigest()


# ── Tests for validate_console_candidate ─────────────────────────────────────


class TestValidateConsoleCandidate:
    def test_success_observed(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        mock = _make_mock_target_script(tmp_path, "success")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "VALIDATED_SUCCESS"
        assert result["runtime_validated"] is True
        assert result["success_observed"] is True
        assert result["solved"] is True
        assert result["known_candidate"] == "WeKnowItOk"
        assert result["candidate"] == "WeKnowItOk"
        assert result["executed_sample"] is True
        assert result["blocked_reason"] == ""

    def test_failure_observed(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WrongInput!")
        mock = _make_mock_target_script(tmp_path, "failure")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "VALIDATED_FAILURE"
        assert result["runtime_validated"] is True
        assert result["failure_observed"] is True
        assert result["solved"] is False
        assert result["known_candidate"] == ""

    def test_length_error_observed(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "short")
        mock = _make_mock_target_script(tmp_path, "length_error")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "VALIDATED_FAILURE"
        assert result["runtime_validated"] is True
        assert result["length_error_observed"] is True
        assert result["solved"] is False

    def test_ambiguous_output(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        mock = _make_mock_target_script(tmp_path, "ambiguous")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "AMBIGUOUS_OUTPUT"
        assert result["runtime_validated"] is False
        assert result["solved"] is False

    def test_target_missing(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=None,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "TARGET_MISSING"
        assert result["executed_sample"] is False
        assert result["solved"] is False

    def test_candidate_missing(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, None)
        mock = _make_mock_target_script(tmp_path, "success")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "CANDIDATE_MISSING"
        assert result["executed_sample"] is False
        assert result["solved"] is False

    def test_timeout(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        mock = _make_mock_target_script(tmp_path, "hang")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=0.5,
            )

        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "TIMEOUT"
        # executed_sample may be False because timeout occurs before process completion
        assert result["solved"] is False

    def test_target_mismatch(self, tmp_path: Path) -> None:
        bad_triage = {
            "schema_version": 1,
            "sample_id": "cpp1_7b504c54",
            "relative_path": "sub/Cpp1.exe",
            "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        }
        triage_path = tmp_path / "bad_triage.json"
        triage_path.write_text(json.dumps(bad_triage), encoding="utf-8")
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        mock = _make_mock_target_script(tmp_path, "success")

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            result = validate_console_candidate(
                triage_path=triage_path,
                candidate_artifact_path=cand,
                candidate_field="static_candidate_text",
                success_token="Congratulations! You are right!",
                failure_token="Sorry, you are wrong!",
                length_token="Sorry, the length is wrong!",
                timeout=5.0,
            )

        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "TARGET_MISMATCH"
        assert result["executed_sample"] is False
        assert result["solved"] is False


# ── Tests for main CLI ───────────────────────────────────────────────────────


class TestMainCLI:
    def test_cli_success(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        mock = _make_mock_target_script(tmp_path, "success")
        out = tmp_path / "runtime.json"

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=mock,
        ):
            from reverse_agent.local_reverse_console_validator import main

            rc = main(
                [
                    "--triage", str(triage),
                    "--candidate-artifact", str(cand),
                    "--candidate-field", "static_candidate_text",
                    "--success-token", "Congratulations! You are right!",
                    "--failure-token", "Sorry, you are wrong!",
                    "--length-token", "Sorry, the length is wrong!",
                    "--out", str(out),
                ]
            )

        assert rc == 0
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["validation_status"] == "VALIDATED_SUCCESS"
        assert data["solved"] is True

    def test_cli_target_missing(self, tmp_path: Path) -> None:
        triage = _make_triage_artifact(tmp_path)
        cand = _make_candidate_artifact(tmp_path, "WeKnowItOk")
        out = tmp_path / "runtime.json"

        with patch(
            "reverse_agent.local_reverse_console_validator._resolve_target_path",
            return_value=None,
        ):
            from reverse_agent.local_reverse_console_validator import main

            rc = main(
                [
                    "--triage", str(triage),
                    "--candidate-artifact", str(cand),
                    "--candidate-field", "static_candidate_text",
                    "--success-token", "Congratulations! You are right!",
                    "--failure-token", "Sorry, you are wrong!",
                    "--length-token", "Sorry, the length is wrong!",
                    "--out", str(out),
                ]
            )

        assert rc == 1
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["validation_status"] == "BLOCKED"
        assert data["blocked_reason"] == "TARGET_MISSING"
