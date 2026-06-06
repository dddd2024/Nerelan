"""Tests for local_reverse_console_pair_validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from reverse_agent.local_reverse_console_pair_validator import (
    _generate_negative_control,
    validate_console_pair,
)


def _triage(**overrides: object) -> dict[str, object]:
    triage: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "relative_path": "逆向课程2025春03/CPP2.exe",
        "analysis_mode": "local_reverse_single_sample_static_triage",
        "source_artifact_freshness": "current",
        "mainline": "reverse_solving",
        "status": "STATIC_TRIAGE_COMPLETE",
        "executed_sample": False,
        "static_only": True,
        "runtime_validated": False,
        "solved": False,
        "tool_status": "success",
        "blocked_reason": "",
        "source_tool": "IDA",
        "sha256": "2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1",
        "size_bytes": 196689,
        "file_type": "pe",
        "category": "cpp",
    }
    triage.update(overrides)
    return triage


def _handoff(**overrides: object) -> dict[str, object]:
    handoff: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "analysis_mode": "direct_strcmp_static_handoff",
        "mainline": "reverse_solving",
        "source_artifact_freshness": "current",
        "static_candidate_text": "ippio",
        "static_candidate_hex": "697070696f",
        "static_candidate_printable": True,
        "known_candidate": "",
        "candidate": None,
        "validation_status": "not_validated",
        "solved": False,
        "status": "READY_FOR_RUNTIME_VALIDATION",
        "blocked_reason": "",
    }
    handoff.update(overrides)
    return handoff


class TestGenerateNegativeControl:
    def test_basic_mutation(self):
        assert _generate_negative_control("ippio") == "jppio"

    def test_same_length(self):
        control = _generate_negative_control("ippio")
        assert len(control) == len("ippio")

    def test_not_equal(self):
        control = _generate_negative_control("ippio")
        assert control != "ippio"

    def test_empty_input(self):
        assert _generate_negative_control("") == ""

    def test_single_char(self):
        control = _generate_negative_control("a")
        assert control == "b"

    def test_non_alpha(self):
        control = _generate_negative_control("12345")
        assert len(control) == 5
        assert control != "12345"


class TestValidateConsolePairBlocked:
    def test_candidate_missing(self, tmp_path: Path):
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff(static_candidate_text=None)), encoding="utf-8")

        result = validate_console_pair(triage_file, handoff_file, "static_candidate_text")
        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "CANDIDATE_MISSING"
        assert result["solved"] is False

    def test_target_missing(self, tmp_path: Path):
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(
            json.dumps(_triage(relative_path="nonexistent/path/binary.exe")),
            encoding="utf-8",
        )
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(triage_file, handoff_file, "static_candidate_text")
        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "TARGET_MISSING"
        assert result["solved"] is False


class TestValidateConsolePairSchema:
    def test_output_has_required_fields(self, tmp_path: Path):
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(triage_file, handoff_file, "static_candidate_text")

        # Required top-level fields
        assert result["schema_version"] == 1
        assert result["sample_id"] == "cpp2_2f64e68d"
        assert result["analysis_mode"] == "console_runtime_pair_validation"
        assert result["mainline"] == "reverse_solving"
        assert result["source_artifact_freshness"] == "current"
        assert result["candidate_source_field"] == "static_candidate_text"
        assert result["candidate_input"] == "ippio"
        assert result["negative_control_input"] != "ippio"
        assert len(result["negative_control_input"]) == len("ippio")
        assert result["negative_control_strategy"] == "single_char_mutation"
        assert result["max_runs"] == 2
        assert result["validation_status"] in (
            "VALIDATED_SUCCESS",
            "VALIDATED_FAILURE",
            "AMBIGUOUS_OUTPUT",
            "BLOCKED",
        )

        # Run records
        assert "candidate_run" in result
        assert "negative_control_run" in result
        for run_key in ("candidate_run", "negative_control_run"):
            run = result[run_key]
            assert "input" in run
            assert "executed" in run
            assert "timed_out" in run
            assert "return_code" in run
            assert "stdout_tail" in run
            assert "stderr_tail" in run

        # Conservative invariants
        assert result["candidate"] in (None, "ippio")
        assert result["known_candidate"] in ("", "ippio")
        if result["solved"]:
            assert result["validation_status"] == "VALIDATED_SUCCESS"
            assert result["candidate"] == "ippio"
            assert result["known_candidate"] == "ippio"
        else:
            assert result["known_candidate"] == ""

    def test_solved_false_when_blocked(self, tmp_path: Path):
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(
            json.dumps(_triage(relative_path="nonexistent/path/binary.exe")),
            encoding="utf-8",
        )
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(triage_file, handoff_file, "static_candidate_text")
        assert result["solved"] is False
        assert result["known_candidate"] == ""
