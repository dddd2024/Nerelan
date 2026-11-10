"""Contract tests for the Windows logon autostart entry (Issue #1415).

Provider-free: no model, network, credential, or real service access. The static
assertions parse ``scripts/windows/Start-NerelanAtLogon.ps1`` without invoking
Magpie or the host; the PowerShell-driven assertions only evaluate the
environment-loading block against temporary JSON files.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
START_LOGON = ROOT / "scripts" / "windows" / "Start-NerelanAtLogon.ps1"

_WINDOWS_PS_HOST = os.environ.get("NERELAN_TEST_POWERSHELL", "powershell")
_PWSH = shutil.which(_WINDOWS_PS_HOST) or shutil.which("pwsh")
requires_powershell = pytest.mark.skipif(
    _PWSH is None, reason="requires powershell or pwsh"
)


def _run_ps(script: str, timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_PWSH or "powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, timeout=timeout,
    )


_SCRIPT = START_LOGON.read_text(encoding="utf-8")


def _env_block() -> str:
    """Return the body of the environment-loading section for execution in tests."""
    start = _SCRIPT.index("  if (-not $EnvFile) {")
    end = _SCRIPT.index("  $devUp = Join-Path", start)
    return _SCRIPT[start:end].strip()


def test_script_references_run_env_json_beside_task_db() -> None:
    assert "run.env.json" in _SCRIPT
    assert "REVERSE_AGENT_TASK_DB_DIR" in _SCRIPT
    assert "Nerelan\\platform-v1" in _SCRIPT


def test_explicit_env_file_has_priority_over_discovery() -> None:
    assert _SCRIPT.index("if (-not $EnvFile)") < _SCRIPT.index("if ($EnvFile)")


def test_only_reverse_agent_keys_are_accepted() -> None:
    assert "'^REVERSE_AGENT_[A-Z0-9_]+$'" in _SCRIPT
    assert "KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL" in _SCRIPT


def test_path_values_are_normalized_to_forward_slashes() -> None:
    assert "_DIR' -or $name -like '*_PATH'" in _SCRIPT
    assert "$value -replace '\\\\', '/'" in _SCRIPT


def test_dev_up_arguments_quote_paths_with_spaces() -> None:
    assert '`"$devUp`"' in _SCRIPT
    assert '`"$RepoDir`"' in _SCRIPT


@requires_powershell
def test_env_loading_applies_reverse_agent_settings_and_normalizes_paths(tmp_path) -> None:
    env_file = tmp_path / "run.env.json"
    env_file.write_text(json.dumps({
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED": "1",
        "REVERSE_AGENT_TASK_DB_DIR": "F:\\nerelan-run\\tasks",
        "REVERSE_AGENT_MAGPIE_EXE": "C:\\Program Files\\magpie\\magpie.exe",
    }), encoding="utf-8")

    block = _env_block()
    escaped = str(env_file).replace("'", "''")
    script = (
        "$EnvFile = '" + escaped + "'\n"
        + block + "\n"
        + "ConvertTo-Json -Compress -InputObject @{\n"
        + "  MULTI = $env:REVERSE_AGENT_MULTI_ACCOUNT_ENABLED\n"
        + "  TASK_DB_DIR = $env:REVERSE_AGENT_TASK_DB_DIR\n"
        + "  MAGPIE_EXE = $env:REVERSE_AGENT_MAGPIE_EXE\n"
        + "}"
    )
    result = _run_ps(script)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["MULTI"] == "1"
    assert data["TASK_DB_DIR"] == "F:/nerelan-run/tasks"
    assert data["MAGPIE_EXE"] == "C:/Program Files/magpie/magpie.exe"


@requires_powershell
def test_env_loading_refuses_secret_like_names(tmp_path) -> None:
    env_file = tmp_path / "run.env.json"
    env_file.write_text(json.dumps({
        "REVERSE_AGENT_API_KEY": "leaked",
    }), encoding="utf-8")

    block = _env_block()
    escaped = str(env_file).replace("'", "''")
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        "$EnvFile = '" + escaped + "'\n"
        + block + "\n"
        + "'did-not-throw'"
    )
    result = _run_ps(script)
    assert result.returncode != 0, "expected secret-like key to be refused"
    assert "refusing environment name" in (result.stdout + result.stderr)


@requires_powershell
def test_env_loading_discovers_run_env_json_in_task_db_dir(tmp_path, monkeypatch) -> None:
    task_db_dir = tmp_path / "tasks"
    task_db_dir.mkdir()
    env_file = task_db_dir / "run.env.json"
    env_file.write_text(json.dumps({
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED": "1",
    }), encoding="utf-8")

    block = _env_block()
    escaped_dir = str(task_db_dir).replace("'", "''")
    script = (
        "$env:REVERSE_AGENT_TASK_DB_DIR = '" + escaped_dir + "'\n"
        "$EnvFile = ''\n"
        + block + "\n"
        + "$env:REVERSE_AGENT_MULTI_ACCOUNT_ENABLED"
    )
    result = _run_ps(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "1"


@requires_powershell
def test_env_loading_discovers_run_env_json_in_default_task_db_dir(tmp_path, monkeypatch) -> None:
    default_dir = tmp_path / "Nerelan" / "platform-v1"
    default_dir.mkdir(parents=True)
    env_file = default_dir / "run.env.json"
    env_file.write_text(json.dumps({
        "REVERSE_AGENT_MULTI_ACCOUNT_ENABLED": "1",
    }), encoding="utf-8")

    block = _env_block()
    escaped_local = str(tmp_path).replace("'", "''")
    script = (
        "$env:LOCALAPPDATA = '" + escaped_local + "'\n"
        "$env:REVERSE_AGENT_TASK_DB_DIR = ''\n"
        "$EnvFile = ''\n"
        + block + "\n"
        + "$env:REVERSE_AGENT_MULTI_ACCOUNT_ENABLED"
    )
    result = _run_ps(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "1"


@requires_powershell
def test_env_loading_is_noop_when_no_file_exists(tmp_path) -> None:
    block = _env_block()
    script = (
        "$env:REVERSE_AGENT_TASK_DB_DIR = ''\n"
        "$env:LOCALAPPDATA = '" + str(tmp_path).replace("'", "''") + "'\n"
        "$EnvFile = ''\n"
        + block + "\n"
        + "[string]::IsNullOrEmpty($env:REVERSE_AGENT_MULTI_ACCOUNT_ENABLED)"
    )
    result = _run_ps(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().lower() == "true"
