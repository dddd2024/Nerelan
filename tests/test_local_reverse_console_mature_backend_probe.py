"""Tests for local_reverse_console_mature_backend_probe."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from reverse_agent.local_reverse_console_mature_backend_probe import (
    build_probe_artifact,
    detect_platform_info,
    detect_python_backend_availability,
    detect_windows_conpty_api_presence,
)


def _runtime(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "analysis_mode": "console_runtime_pair_validation",
        "candidate_input": "ippio",
        "negative_control_input": "jppio",
        "max_runs": 2,
        "executed_sample": True,
        "runtime_validated": False,
        "validation_status": "AMBIGUOUS_OUTPUT",
        "outputs_differ": False,
        "candidate": None,
        "known_candidate": "",
        "solved": False,
        "blocked_reason": "AMBIGUOUS_OUTPUT",
        "candidate_accepted": False,
        "control_rejected": False,
    }
    base.update(overrides)
    return base


def _handoff(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "analysis_mode": "direct_strcmp_static_handoff",
        "static_candidate_text": "ippio",
        "candidate": None,
        "known_candidate": "",
        "validation_status": "not_validated",
        "solved": False,
        "status": "READY_FOR_RUNTIME_VALIDATION",
        "blocked_reason": "",
    }
    base.update(overrides)
    return base


def _triage(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "status": "STATIC_TRIAGE_COMPLETE",
        "solved": False,
        "blocked_reason": "",
    }
    base.update(overrides)
    return base


class TestDetectPythonBackendAvailability:
    def test_returns_dict_with_all_keys(self):
        result = detect_python_backend_availability()
        assert "pywinpty_available" in result
        assert "winpty_available" in result
        assert "wexpect_available" in result
        assert "pexpect_available" in result
        for v in result.values():
            assert isinstance(v, bool)


class TestDetectPlatformInfo:
    def test_returns_dict_with_all_keys(self):
        result = detect_platform_info()
        assert "windows_platform" in result
        assert "platform_system" in result
        assert "sys_platform" in result
        assert "os_name" in result
        assert isinstance(result["windows_platform"], bool)
        assert isinstance(result["platform_system"], str)


class TestDetectWindowsConptyApiPresence:
    def test_returns_checked_true(self):
        result = detect_windows_conpty_api_presence()
        assert result["conpty_api_checked"] is True
        assert isinstance(result["conpty_api_available"], bool)

    @patch("sys.platform", "linux")
    def test_non_windows_returns_unavailable(self):
        result = detect_windows_conpty_api_presence()
        assert result["conpty_api_available"] is False
        assert result["conpty_api_checked"] is True


class TestBuildProbeArtifact:
    def _write_artifacts(self, tmp_path: Path, **runtime_overrides):
        runtime_path = tmp_path / "runtime.json"
        handoff_path = tmp_path / "handoff.json"
        triage_path = tmp_path / "triage.json"
        runtime_path.write_text(json.dumps(_runtime(**runtime_overrides)), encoding="utf-8")
        handoff_path.write_text(json.dumps(_handoff()), encoding="utf-8")
        triage_path.write_text(json.dumps(_triage()), encoding="utf-8")
        return runtime_path, handoff_path, triage_path

    def test_basic_schema(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path)
        result = build_probe_artifact(rp, hp, tp)

        assert result["schema_version"] == 1
        assert result["sample_id"] == "cpp2_2f64e68d"
        assert result["analysis_mode"] == "console_mature_backend_availability_probe"
        assert result["mainline"] == "tool_integration"
        assert result["source_artifact_freshness"] == "current"
        assert result["candidate_input"] == "ippio"
        assert result["previous_validation_status"] == "AMBIGUOUS_OUTPUT"
        assert result["previous_known_candidate"] == ""
        assert result["previous_solved"] is False
        assert result["mature_backend_priority"] is True
        assert result["no_custom_conpty_runner"] is True
        assert result["no_expect_state_machine"] is True
        assert result["no_terminal_emulator"] is True
        assert result["executed_target"] is False
        assert result["runtime_validated"] is False
        assert result["known_candidate"] == ""
        assert result["solved"] is False
        assert result["candidate"] is None

    def test_probe_status_in_valid_range(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path)
        result = build_probe_artifact(rp, hp, tp)
        assert result["probe_status"] in (
            "READY_FOR_MATURE_BACKEND_VALIDATION",
            "BLOCKED_NON_WINDOWS_ENVIRONMENT",
            "BLOCKED_MATURE_BACKEND_MISSING",
            "BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY",
            "BLOCKED_SOURCE_ARTIFACT_MISMATCH",
        )

    def test_preferred_backend_order(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path)
        result = build_probe_artifact(rp, hp, tp)
        assert result["preferred_backend_order"] == [
            "pywinpty_or_winpty",
            "wexpect",
            "windows_conpty_api_presence",
            "pexpect_posix_reference_only",
        ]

    def test_blocked_when_runtime_solved(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path, solved=True)
        result = build_probe_artifact(rp, hp, tp)
        assert result["probe_status"] == "BLOCKED_SOURCE_ARTIFACT_MISMATCH"
        assert "solved" in result["blocked_reason"]

    def test_blocked_when_runtime_not_ambiguous(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path, validation_status="VALIDATED_SUCCESS")
        result = build_probe_artifact(rp, hp, tp)
        assert result["probe_status"] == "BLOCKED_SOURCE_ARTIFACT_MISMATCH"

    def test_blocked_when_handoff_not_ready(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path)
        hp.write_text(json.dumps(_handoff(status="NOT_READY")), encoding="utf-8")
        result = build_probe_artifact(rp, hp, tp)
        assert result["probe_status"] == "BLOCKED_SOURCE_ARTIFACT_MISMATCH"

    def test_blocked_when_triage_not_complete(self, tmp_path: Path):
        rp, hp, tp = self._write_artifacts(tmp_path)
        tp.write_text(json.dumps(_triage(status="INCOMPLETE")), encoding="utf-8")
        result = build_probe_artifact(rp, hp, tp)
        assert result["probe_status"] == "BLOCKED_SOURCE_ARTIFACT_MISMATCH"

    def test_conpty_only_blocked(self, tmp_path: Path):
        """ConPTY API present but no mature Python backend → must be blocked."""
        rp, hp, tp = self._write_artifacts(tmp_path)
        with (
            patch("reverse_agent.local_reverse_console_mature_backend_probe.detect_python_backend_availability") as mock_pkg,
            patch("reverse_agent.local_reverse_console_mature_backend_probe.detect_windows_conpty_api_presence") as mock_conpty,
            patch("reverse_agent.local_reverse_console_mature_backend_probe.detect_platform_info") as mock_platform,
        ):
            mock_pkg.return_value = {
                "pywinpty_available": False,
                "winpty_available": False,
                "wexpect_available": False,
                "pexpect_available": False,
            }
            mock_conpty.return_value = {
                "conpty_api_available": True,
                "conpty_api_checked": True,
            }
            mock_platform.return_value = {
                "windows_platform": True,
                "platform_system": "Windows",
                "sys_platform": "win32",
                "os_name": "nt",
            }
            result = build_probe_artifact(rp, hp, tp)

        # Must NOT be READY
        assert result["probe_status"] != "READY_FOR_MATURE_BACKEND_VALIDATION"
        assert result["can_attempt_interactive_console_validation_next"] is False
        # recommended_backend must NOT be windows_conpty_api
        assert result["recommended_backend"] != "windows_conpty_api"
        # Safety flags must remain true
        assert result["no_custom_conpty_runner"] is True
        assert result["no_expect_state_machine"] is True
        assert result["no_terminal_emulator"] is True
        # Must be one of the blocked statuses
        assert result["probe_status"] in (
            "BLOCKED_MATURE_BACKEND_MISSING",
            "BLOCKED_MATURE_BACKEND_MISSING_CONPTY_ONLY",
        )
        # solved/candidate must remain false/null
        assert result["solved"] is False
        assert result["known_candidate"] == ""
        assert result["candidate"] is None
