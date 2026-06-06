"""Tests for local_reverse_console_pair_validator."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import reverse_agent.local_reverse_console_pair_validator as pair_validator
from reverse_agent.local_reverse_console_pair_validator import (
    _generate_negative_control,
    _is_winpty_available,
    get_console_backend_capabilities,
    is_console_backend_validator_supported,
    validate_console_pair,
)


def _triage(**overrides: object) -> dict[str, object]:
    triage: dict[str, object] = {
        "schema_version": 1,
        "sample_id": "cpp2_2f64e68d",
        "relative_path": "synthetic/nonexistent/unit_test_binary.exe",
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


def _block_real_target_execution(monkeypatch):
    monkeypatch.setattr(
        pair_validator,
        "_resolve_target_path",
        lambda relative_path: None,
    )

    def fail_if_run(*args, **kwargs):
        raise AssertionError("unit tests must not run target binaries")

    monkeypatch.setattr(pair_validator, "_run_single", fail_if_run)


class TestConsoleBackendCapabilities:
    def test_registry_exposes_subprocess_pywinauto_and_winpty(self):
        capabilities = get_console_backend_capabilities()

        assert sorted(capabilities) == ["pywinauto", "subprocess", "winpty"]
        assert capabilities["subprocess"]["validator_supported"] is True
        assert capabilities["subprocess"]["mature_interactive_console"] is False
        assert capabilities["pywinauto"]["validator_supported"] is False
        assert capabilities["pywinauto"]["mature_interactive_console"] is False
        assert "winpty" in capabilities
        assert "available" in capabilities["winpty"]
        assert "validator_supported" in capabilities["winpty"]
        assert "mature_interactive_console" in capabilities["winpty"]

    def test_registry_is_json_serializable(self):
        capabilities = get_console_backend_capabilities()

        encoded = json.dumps(capabilities, sort_keys=True)

        assert "subprocess" in encoded
        assert "pywinauto" in encoded
        assert "winpty" in encoded

    def test_registry_return_value_does_not_mutate_global_state(self):
        capabilities = get_console_backend_capabilities()
        capabilities["pywinauto"]["validator_supported"] = True
        capabilities["subprocess"]["mature_interactive_console"] = True
        capabilities["winpty"]["available"] = False

        fresh = get_console_backend_capabilities()

        assert fresh["pywinauto"]["validator_supported"] is False
        assert fresh["subprocess"]["mature_interactive_console"] is False
        # winpty availability depends on actual environment, just check it exists
        assert "available" in fresh["winpty"]

    def test_validator_supported_helper(self):
        assert is_console_backend_validator_supported("subprocess") is True
        assert is_console_backend_validator_supported("pywinauto") is False
        assert is_console_backend_validator_supported("missing") is False

    def test_winpty_availability_can_be_monkeypatched(self, monkeypatch):
        """Winpty availability can be overridden via monkeypatch."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: True)
        capabilities = get_console_backend_capabilities()
        assert capabilities["winpty"]["available"] is True
        assert capabilities["winpty"]["validator_supported"] is True
        assert capabilities["winpty"]["mature_interactive_console"] is True

    def test_winpty_unavailable_when_monkeypatched_false(self, monkeypatch):
        """Winpty unavailable when monkeypatched to False."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: False)
        capabilities = get_console_backend_capabilities()
        assert capabilities["winpty"]["available"] is False
        assert capabilities["winpty"]["validator_supported"] is False
        assert capabilities["winpty"]["mature_interactive_console"] is False

    def test_is_winpty_available_returns_bool(self):
        result = _is_winpty_available()
        assert isinstance(result, bool)


class TestWinptyBackendValidation:
    """Tests for winpty backend in validate_console_pair."""

    def test_winpty_supported_true_when_available(self, monkeypatch):
        """is_console_backend_validator_supported('winpty') = True when available."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: True)
        assert is_console_backend_validator_supported("winpty") is True

    def test_winpty_supported_false_when_unavailable(self, monkeypatch):
        """is_console_backend_validator_supported('winpty') = False when unavailable."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: False)
        assert is_console_backend_validator_supported("winpty") is False

    def test_subprocess_backend_preserves_old_behavior(self, tmp_path: Path, monkeypatch):
        """validate_console_pair(..., backend='subprocess') preserves old behavior."""
        _block_real_target_execution(monkeypatch)
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(
            triage_file, handoff_file, "static_candidate_text", backend="subprocess"
        )
        assert result["backend"] == "subprocess"
        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "TARGET_MISSING"

    def test_winpty_backend_selects_winpty_runner(self, tmp_path: Path, monkeypatch):
        """validate_console_pair(..., backend='winpty') selects winpty runner."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: True)
        monkeypatch.setattr(
            pair_validator,
            "_resolve_target_path",
            lambda relative_path: None,
        )

        winpty_run_called = {"count": 0}

        def mock_winpty_run(target_path, input_text, timeout=10.0):
            winpty_run_called["count"] += 1
            return {
                "input": input_text,
                "executed": False,
                "timed_out": False,
                "return_code": None,
                "stdout_tail": "",
                "stderr_tail": "",
                "backend": "winpty",
            }

        monkeypatch.setattr(pair_validator, "_run_single_winpty", mock_winpty_run)

        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(
            triage_file, handoff_file, "static_candidate_text", backend="winpty"
        )
        assert result["backend"] == "winpty"
        assert winpty_run_called["count"] == 0  # blocked before runner

    def test_winpty_mock_same_output_is_ambiguous(self, tmp_path: Path, monkeypatch):
        """Winpty runner mock: same output -> AMBIGUOUS_OUTPUT, known_candidate=''."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: True)

        # Create a fake target
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        target_file = target_dir / "binary.exe"
        target_file.write_bytes(b"\x00" * 100)

        monkeypatch.setattr(
            pair_validator,
            "_resolve_target_path",
            lambda relative_path: target_file,
        )
        monkeypatch.setattr(pair_validator, "_sha256_file", lambda path: "2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1")

        same_output = "some output"
        mock_run = {
            "input": "",
            "executed": True,
            "timed_out": False,
            "return_code": 0,
            "stdout_tail": same_output,
            "stderr_tail": "",
            "backend": "winpty",
        }
        monkeypatch.setattr(pair_validator, "_run_single_winpty", lambda *a, **k: dict(mock_run))

        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(
            triage_file, handoff_file, "static_candidate_text", backend="winpty"
        )
        assert result["validation_status"] == "AMBIGUOUS_OUTPUT"
        assert result["known_candidate"] == ""
        assert result["solved"] is False

    def test_winpty_mock_candidate_success_control_failure(self, tmp_path: Path, monkeypatch):
        """Winpty runner mock: candidate rc=0, control rc!=0 -> VALIDATED_SUCCESS."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: True)

        target_dir = tmp_path / "target"
        target_dir.mkdir()
        target_file = target_dir / "binary.exe"
        target_file.write_bytes(b"\x00" * 100)

        monkeypatch.setattr(
            pair_validator,
            "_resolve_target_path",
            lambda relative_path: target_file,
        )
        monkeypatch.setattr(pair_validator, "_sha256_file", lambda path: "2f64e68d4f8c20b12c2332b7ff7895195c992d834ba6d16be4013de8bb1a92a1")

        def mock_winpty_run(target_path, input_text, timeout=10.0):
            if input_text == "ippio":
                return {
                    "input": input_text, "executed": True, "timed_out": False,
                    "return_code": 0, "stdout_tail": "correct", "stderr_tail": "",
                    "backend": "winpty",
                }
            return {
                "input": input_text, "executed": True, "timed_out": False,
                "return_code": 1, "stdout_tail": "wrong", "stderr_tail": "error",
                "backend": "winpty",
            }

        monkeypatch.setattr(pair_validator, "_run_single_winpty", mock_winpty_run)

        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(
            triage_file, handoff_file, "static_candidate_text", backend="winpty"
        )
        assert result["validation_status"] == "VALIDATED_SUCCESS"
        assert result["known_candidate"] == "ippio"
        assert result["solved"] is True

    def test_unsupported_backend_returns_blocked(self, tmp_path: Path, monkeypatch):
        """Unsupported backend returns BLOCKED, does not run target."""
        monkeypatch.setattr(pair_validator, "_is_winpty_available", lambda: False)

        run_called = {"count": 0}

        def fail_if_run(*args, **kwargs):
            run_called["count"] += 1
            raise AssertionError("must not run target for unsupported backend")

        monkeypatch.setattr(pair_validator, "_run_single", fail_if_run)
        monkeypatch.setattr(pair_validator, "_run_single_winpty", fail_if_run)

        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        result = validate_console_pair(
            triage_file, handoff_file, "static_candidate_text", backend="winpty"
        )
        assert result["validation_status"] == "BLOCKED"
        assert "UNSUPPORTED_BACKEND" in result["blocked_reason"]
        assert run_called["count"] == 0

    def test_cli_backend_arg_parsed(self, tmp_path: Path):
        """CLI --backend argument is parsed and passed to validate_console_pair."""
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        out_file = tmp_path / "out.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff()), encoding="utf-8")

        # Use --backend winpty (will be blocked since no target, but tests arg parsing)
        ret = pair_validator.main([
            "--triage", str(triage_file),
            "--candidate-artifact", str(handoff_file),
            "--candidate-field", "static_candidate_text",
            "--backend", "winpty",
            "--out", str(out_file),
        ])
        # Return code 1 because BLOCKED is not VALIDATED_SUCCESS/VALIDATED_FAILURE
        assert ret == 1

        result = json.loads(out_file.read_text(encoding="utf-8"))
        assert result["backend"] == "winpty"


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
    def test_candidate_missing(self, tmp_path: Path, monkeypatch):
        _block_real_target_execution(monkeypatch)
        triage_file = tmp_path / "triage.json"
        handoff_file = tmp_path / "handoff.json"
        triage_file.write_text(json.dumps(_triage()), encoding="utf-8")
        handoff_file.write_text(json.dumps(_handoff(static_candidate_text=None)), encoding="utf-8")

        result = validate_console_pair(triage_file, handoff_file, "static_candidate_text")
        assert result["validation_status"] == "BLOCKED"
        assert result["blocked_reason"] == "CANDIDATE_MISSING"
        assert result["solved"] is False

    def test_target_missing(self, tmp_path: Path, monkeypatch):
        _block_real_target_execution(monkeypatch)
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
    def test_output_has_required_fields(self, tmp_path: Path, monkeypatch):
        _block_real_target_execution(monkeypatch)
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

    def test_solved_false_when_blocked(self, tmp_path: Path, monkeypatch):
        _block_real_target_execution(monkeypatch)
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
