"""Focused tests for ollydbg_preflight — hermetic, no external tool dependency."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from reverse_agent.ollydbg_preflight import (
    _olly_script_module_available,
    _resolve_ollydbg_exe,
    _step_audit_script_exists,
    run_ollydbg_preflight,
)


class TestOllydbgPreflight:
    """Hermetic preflight tests — no dependency on real OllyDbg/ollyscript/sample installation."""

    def test_step_audit_script_exists(self) -> None:
        """The compare_handoff_post_entry_step_audit.py script must exist."""
        assert _step_audit_script_exists() is True

    def test_olly_script_module_not_available_when_spec_missing(self) -> None:
        """_olly_script_module_available returns False when importlib.util.find_spec finds nothing."""
        with patch("importlib.util.find_spec", return_value=None):
            assert _olly_script_module_available() is False

    # ------------------------------------------------------------------
    # _resolve_ollydbg_exe path validation tests
    # ------------------------------------------------------------------

    def test_resolve_ollydbg_exe_direct_file(self, tmp_path: Path) -> None:
        """Env var pointing directly to ollydbg.exe resolves correctly."""
        exe = tmp_path / "ollydbg.exe"
        exe.write_text("", encoding="utf-8")
        result = _resolve_ollydbg_exe(exe)
        assert result == exe

    def test_resolve_ollydbg_exe_directory_with_exe(self, tmp_path: Path) -> None:
        """Env var pointing to a directory containing ollydbg.exe resolves correctly."""
        exe = tmp_path / "ollydbg.exe"
        exe.write_text("", encoding="utf-8")
        result = _resolve_ollydbg_exe(tmp_path)
        assert result == exe

    def test_resolve_ollydbg_exe_directory_without_exe(self, tmp_path: Path) -> None:
        """Env var pointing to a directory without ollydbg.exe returns None."""
        result = _resolve_ollydbg_exe(tmp_path)
        assert result is None

    def test_resolve_ollydbg_exe_nonexistent_path(self, tmp_path: Path) -> None:
        """Env var pointing to a non-existent path returns None."""
        result = _resolve_ollydbg_exe(tmp_path / "does_not_exist")
        assert result is None

    def test_resolve_ollydbg_exe_directory_not_marked_executable(self, tmp_path: Path) -> None:
        """A directory path must not be misclassified as an executable."""
        result = _resolve_ollydbg_exe(tmp_path)
        assert result is None

    # ------------------------------------------------------------------
    # Preflight readiness tests
    # ------------------------------------------------------------------

    def test_preflight_all_false_when_nothing_configured(self, tmp_path: Path) -> None:
        """Preflight returns ready=False when no backend is configured."""
        out = tmp_path / "preflight.json"

        with (
            patch("reverse_agent.ollydbg_preflight._ollydbg_exe_path", return_value=None),
            patch("reverse_agent.ollydbg_preflight._olly_script_module_available", return_value=False),
            patch("reverse_agent.ollydbg_preflight._sample_path", return_value=None),
        ):
            result = run_ollydbg_preflight(output_path=out)

        assert result["preflight_name"] == "ollydbg_backend_preflight"
        assert result["preflight_version"] == 2
        assert result["ready"] is False
        assert result["backend_ready"] is False
        assert result["runtime_ready"] is False
        assert result["checks"]["olly_scripts_directory_exists"] is True
        assert result["checks"]["step_audit_script_exists"] is True
        assert result["checks"]["ollydbg_executable_found"] is False
        assert result["checks"]["olly_script_module_importable"] is False
        assert result["checks"]["sample_path_resolvable"] is False
        assert result["recommendation"] == "preflight_not_configured_user_env_needed"
        assert out.exists()

    def test_preflight_backend_ready_but_sample_missing(self, tmp_path: Path) -> None:
        """Backend ready but missing sample produces backend_ready=true, runtime_ready=false."""
        out = tmp_path / "preflight.json"

        with (
            patch(
                "reverse_agent.ollydbg_preflight._ollydbg_exe_path",
                return_value=tmp_path / "ollydbg.exe",
            ),
            patch(
                "reverse_agent.ollydbg_preflight._olly_script_module_available",
                return_value=True,
            ),
            patch("reverse_agent.ollydbg_preflight._sample_path", return_value=None),
        ):
            result = run_ollydbg_preflight(output_path=out)

        assert result["backend_ready"] is True
        assert result["runtime_ready"] is False
        assert result["ready"] is False
        assert result["checks"]["sample_path_resolvable"] is False
        assert result["recommendation"] == "preflight_not_configured_user_env_needed"

    def test_preflight_fully_ready_when_all_mocked(self, tmp_path: Path) -> None:
        """Preflight returns ready=True when backend and sample are both available."""
        out = tmp_path / "preflight.json"
        fake_sample = tmp_path / "samplereverse.exe"
        fake_sample.write_text("", encoding="utf-8")

        with (
            patch(
                "reverse_agent.ollydbg_preflight._ollydbg_exe_path",
                return_value=tmp_path / "ollydbg.exe",
            ),
            patch(
                "reverse_agent.ollydbg_preflight._olly_script_module_available",
                return_value=True,
            ),
            patch(
                "reverse_agent.ollydbg_preflight._sample_path",
                return_value=fake_sample,
            ),
        ):
            result = run_ollydbg_preflight(output_path=out)

        assert result["ready"] is True
        assert result["backend_ready"] is True
        assert result["runtime_ready"] is True
        assert result["checks"]["ollydbg_executable_found"] is True
        assert result["checks"]["olly_script_module_importable"] is True
        assert result["checks"]["olly_scripts_directory_exists"] is True
        assert result["checks"]["step_audit_script_exists"] is True
        assert result["checks"]["sample_path_resolvable"] is True
        assert result["recommendation"] == "preflight_ready_for_bounded_ollydbg_runtime_decision"
        assert out.exists()

        # Verify JSON is valid and round-trips
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["ready"] is True
        assert data["backend_ready"] is True
        assert data["runtime_ready"] is True
        assert data["preflight_version"] == 2

    def test_preflight_respects_explicit_paths(self, tmp_path: Path) -> None:
        """Explicit ollydbg_path and sample_path override discovery."""
        fake_olly = tmp_path / "fake_olly.exe"
        fake_olly.write_text("", encoding="utf-8")
        fake_sample = tmp_path / "fake_sample.exe"
        fake_sample.write_text("", encoding="utf-8")

        result = run_ollydbg_preflight(
            ollydbg_path=fake_olly,
            sample_path=fake_sample,
        )

        assert result["checks"]["ollydbg_executable_path"] == str(fake_olly)
        assert result["checks"]["sample_path"] == str(fake_sample)
        # With explicit paths, backend_ready depends on olly + module
        # Since module is not mocked here, backend_ready may be false

    def test_preflight_main_cli_exit_code_when_not_ready(self, tmp_path: Path) -> None:
        """main([]) returns exit code 1 when preflight is not ready."""
        from reverse_agent.ollydbg_preflight import main

        with (
            patch("reverse_agent.ollydbg_preflight._ollydbg_exe_path", return_value=None),
            patch("reverse_agent.ollydbg_preflight._olly_script_module_available", return_value=False),
            patch("reverse_agent.ollydbg_preflight._sample_path", return_value=None),
        ):
            exit_code = main([])

        assert exit_code == 1

    def test_preflight_main_cli_exit_code_when_ready(self, tmp_path: Path) -> None:
        """main([]) returns exit code 0 when preflight is fully ready."""
        from reverse_agent.ollydbg_preflight import main
        fake_sample = tmp_path / "samplereverse.exe"
        fake_sample.write_text("", encoding="utf-8")

        with (
            patch(
                "reverse_agent.ollydbg_preflight._ollydbg_exe_path",
                return_value=tmp_path / "ollydbg.exe",
            ),
            patch(
                "reverse_agent.ollydbg_preflight._olly_script_module_available",
                return_value=True,
            ),
            patch(
                "reverse_agent.ollydbg_preflight._sample_path",
                return_value=fake_sample,
            ),
        ):
            exit_code = main([])

        assert exit_code == 0
