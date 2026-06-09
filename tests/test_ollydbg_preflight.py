"""Focused tests for ollydbg_preflight — mocked, no external tool startup."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from reverse_agent.ollydbg_preflight import (
    _olly_script_module_available,
    _step_audit_script_exists,
    run_ollydbg_preflight,
)


class TestOllydbgPreflight:
    """Non-invasive preflight tests — no OllyDbg process started."""

    def test_step_audit_script_exists(self) -> None:
        """The compare_handoff_post_entry_step_audit.py script must exist."""
        assert _step_audit_script_exists() is True

    def test_olly_script_module_not_available_by_default(self) -> None:
        """OllyDbg Python module is not expected to be installed in CI/test env."""
        assert _olly_script_module_available() is False

    def test_preflight_all_false_when_nothing_configured(self, tmp_path: Path) -> None:
        """Preflight returns ready=False when no backend is configured."""
        out = tmp_path / "preflight.json"
        result = run_ollydbg_preflight(output_path=out)

        assert result["preflight_name"] == "ollydbg_backend_preflight"
        assert result["ready"] is False
        assert result["checks"]["olly_scripts_directory_exists"] is True
        assert result["checks"]["step_audit_script_exists"] is True
        assert result["checks"]["ollydbg_executable_found"] is False
        assert result["checks"]["olly_script_module_importable"] is False
        assert result["recommendation"] == "preflight_not_configured_user_env_needed"
        assert out.exists()

    def test_preflight_ready_when_all_mocked(self, tmp_path: Path) -> None:
        """Preflight returns ready=True when all critical checks are mocked to pass."""
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
            patch(
                "reverse_agent.ollydbg_preflight._sample_path",
                return_value=tmp_path / "samplereverse.exe",
            ),
        ):
            result = run_ollydbg_preflight(output_path=out)

        assert result["ready"] is True
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
        assert data["preflight_version"] == 1

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

    def test_preflight_main_cli_exit_code(self, tmp_path: Path) -> None:
        """CLI returns exit code 1 when not ready."""
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, "-m", "reverse_agent.ollydbg_preflight"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == 1
        data = json.loads(proc.stdout)
        assert data["ready"] is False
