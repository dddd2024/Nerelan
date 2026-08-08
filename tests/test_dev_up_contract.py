from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_UP = ROOT / "dev-up.ps1"
DEV_DOWN = ROOT / "dev-down.ps1"
COMPOSER = ROOT / "frontend/src/components/new-task-composer.tsx"
FRONTEND_TEST = ROOT / "frontend/tests/real-executor-task-plane.test.tsx"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_DEV_UP = _text(DEV_UP)
_DEV_DOWN = _text(DEV_DOWN)
_COMPOSER = _text(COMPOSER)
_FRONTEND_TEST = _text(FRONTEND_TEST)


def test_dev_up_uses_loopback_ports_only() -> None:
    for port in ("4173", "8765", "8766"):
        assert f"127.0.0.1:{port}" in _DEV_UP
    assert "0.0.0.0" not in _DEV_UP


def test_model_control_origin_is_frontend() -> None:
    assert '"REVERSE_AGENT_MODEL_CONTROL_ORIGIN"' in _DEV_UP
    assert "http://127.0.0.1:4173" in _DEV_UP


def test_task_api_origin_is_frontend() -> None:
    assert '"REVERSE_AGENT_TASK_SERVICE_ORIGIN"' in _DEV_UP


def test_repo_dir_is_provided() -> None:
    assert '"REVERSE_AGENT_REPO_DIR"' in _DEV_UP


def test_opencode_model_is_provided() -> None:
    assert '"REVERSE_AGENT_OPENCODE_MODEL"' in _DEV_UP


def test_frontend_api_bases_are_set() -> None:
    assert '"VITE_TASK_API_BASE"' in _DEV_UP
    assert '"VITE_MODEL_CONTROL_API_BASE"' in _DEV_UP
    assert "http://127.0.0.1:8766" in _DEV_UP
    assert "${ModelControlPort}/api" in _DEV_UP


def test_dev_up_has_no_package_install_commands() -> None:
    forbidden = [
        "pip install",
        "pip3 install",
        "python -m pip",
        "npx --yes",
        "npx -y",
        "winget",
        "choco",
        "scoop",
        "npm -g",
        "install -g",
        "npm ci ",
    ]
    lowered = _DEV_UP.lower()
    for cmd in forbidden:
        assert cmd not in lowered, f"forbidden package install command: {cmd}"
    assert "--prefix" in _DEV_UP and "run" in _DEV_UP and '"dev"' in _DEV_UP


def test_dev_up_has_no_credential_dump() -> None:
    sensitive = [
        "SECRET",
        "TOKEN",
        "api_key",
        "apiKey",
        "password",
        "Authorization",
    ]
    for tok in sensitive:
        assert tok not in _DEV_UP, f"possible credential exposure: {tok}"


def test_dev_down_has_no_blanket_process_kill() -> None:
    forbidden = [
        "Get-Process python | Stop-Process",
        "Get-Process node | Stop-Process",
        "Get-Process cmd | Stop-Process",
        "taskkill /IM python.exe",
        "taskkill /IM node.exe",
        "taskkill /IM opencode",
        "Stop-Process -Force",
        "Get-Process | Stop-Process",
    ]
    for pattern in forbidden:
        assert pattern not in _DEV_DOWN, f"blanket kill present: {pattern}"


def test_dev_down_reads_its_own_pid_file() -> None:
    assert "devup_pids.json" in _DEV_DOWN
    assert "Get-Process -Id" in _DEV_DOWN


def test_dev_up_runtime_state_is_under_platform_v1_runtime() -> None:
    assert ".platform_v1_runtime" in _DEV_UP
    assert "devup_pids.json" in _DEV_UP


def test_dev_up_only_checks_opencode_prerequisite() -> None:
    assert 'Find-Executable "opencode"' in _DEV_UP
    assert "opencode run" not in _DEV_UP
    assert "opencode.exe" not in _DEV_UP


def test_dev_up_starts_only_existing_service_entrypoints() -> None:
    assert "reverse_agent.model_access.service" in _DEV_UP
    assert "reverse_agent.platform_v1.task_service" in _DEV_UP
    assert (
        "npm" in _DEV_UP
        and "--prefix" in _DEV_UP
        and '"frontend"' in _DEV_UP
        and '"run"' in _DEV_UP
        and '"dev"' in _DEV_UP
    )


def test_dev_up_reports_open_code_model() -> None:
    assert "sensetime/sensenova-6.7-flash-lite" in _DEV_UP


def test_dev_down_only_stops_owned_pids() -> None:
    assert "expectedPid" in _DEV_DOWN
    assert "refusing to kill" in _DEV_DOWN


def test_dev_up_fails_closed_on_occupied_ports() -> None:
    assert "Is-PortInUse" in _DEV_UP
    assert "occupi" in _DEV_UP
    assert "Get-PortProcess" in _DEV_UP


def test_dev_up_records_pid_metadata() -> None:
    assert "pid" in _DEV_UP
    assert "children" in _DEV_UP
    assert "ConvertTo-Json" in _DEV_UP


def test_no_secret_references_anywhere() -> None:
    for text, name in ((_DEV_UP, "dev-up"), (_DEV_DOWN, "dev-down")):
        lowered = text.lower()
        for forbidden in ("bearer ", "token=", "api_key=", "secret="):
            assert forbidden not in lowered, f"{name}: {forbidden}"


# ── V3 deterministic regression coverage ─────────────────────────────

def test_blank_source_dir_falls_back_to_repo_dir() -> None:
    """V3-F2: blank/absent SourceDir must become resolved RepoDir, not CWD."""
    lines = _DEV_UP.splitlines()
    resolved_source_idx = None
    blank_check_idx = None
    for i, line in enumerate(lines):
        if "IsNullOrWhiteSpace($SourceDir)" in line and resolved_source_idx is None:
            blank_check_idx = i
        if "$sourceDir = Resolve-InputPath" in line:
            resolved_source_idx = i

    assert blank_check_idx is not None, "no SourceDir blank check found"
    assert resolved_source_idx is not None, "no SourceDir resolve found"
    assert (
        blank_check_idx < resolved_source_idx
    ), "blank check must precede Resolve-InputPath so blank never reaches CWD"

    fallback_block = "\n".join(lines[blank_check_idx: blank_check_idx + 8])
    assert "$repoDir" in fallback_block, "blank SourceDir must fall back to repoDir"
    assert "Resolve-InputPath" in fallback_block, "explicit SourceDir must still be resolved"


def test_explicit_source_dir_remains_separate_from_repo_dir() -> None:
    """V3-F1: REVERSE_AGENT_REPO_DIR must be SourceDir, not RepoDir."""
    assert '"REVERSE_AGENT_REPO_DIR"' in _DEV_UP
    repo_line = None
    for line in _DEV_UP.splitlines():
        stripped = line.strip()
        if stripped.startswith('"REVERSE_AGENT_REPO_DIR"') and "=" in stripped:
            repo_line = line
            break
    assert repo_line is not None, "REVERSE_AGENT_REPO_DIR assignment not found"
    assert "$sourceDir" in repo_line, "REVERSE_AGENT_REPO_DIR must receive SourceDir"
    assert "$repoDir" not in repo_line, "REVERSE_AGENT_REPO_DIR must NOT receive RepoDir"


def test_repo_dir_used_for_node_modules_and_runtime() -> None:
    """RepoDir is the trusted host: frontend/node_modules and runtime metadata."""
    assert "Join-Path $repoDir" in _DEV_UP
    assert "frontend\\node_modules" in _DEV_UP
    assert ".platform_v1_runtime" in _DEV_UP
    assert "$runtimeDir = Join-Path $repoDir" in _DEV_UP


def test_exact_pid_process_tree_ownership_exists() -> None:
    """V3-F3: exact-PID tree ownership must exist; no name-wide kill."""
    assert "taskkill" in _DEV_DOWN
    assert "/PID" in _DEV_DOWN
    assert "/T" in _DEV_DOWN
    assert "expected_exe" in _DEV_UP
    assert "start_time" in _DEV_UP
    assert "wrapped" in _DEV_UP


def test_no_name_wide_kill_anywhere() -> None:
    """V3-F3: absolutely no image-wide or name-wide termination."""
    for text, name in ((_DEV_UP, "dev-up"), (_DEV_DOWN, "dev-down")):
        forbidden_patterns = [
            "taskkill /IM",
            "Get-Process python | Stop-Process",
            "Get-Process node | Stop-Process",
            "Get-Process cmd | Stop-Process",
            "Get-Process | Stop-Process",
            "Stop-Process -Force",
        ]
        for pat in forbidden_patterns:
            assert pat not in text, f"{name}: name-wide kill present: {pat}"


def test_partial_startup_has_centralized_cleanup() -> None:
    """V3-F4: centralized cleanup must exist; Stop-Owned-Children called before Fail-Closed."""
    assert "Stop-Owned-Children" in _DEV_UP
    assert "startedChildren" in _DEV_UP
    fail_closed_block = _DEV_UP[
        _DEV_UP.index("function Fail-Closed"): _DEV_UP.index("}", _DEV_UP.index("function Fail-Closed")) + 1
    ]
    assert "Stop-Owned-Children" in fail_closed_block, "Fail-Closed must invoke centralized cleanup"
    start_service_block = _DEV_UP[
        _DEV_UP.index("function Start-ServiceProcess"): _DEV_UP.index(
            "function Wait-ServiceReady", _DEV_UP.index("function Start-ServiceProcess")
        )
    ]
    assert "startedChildren.Add" in start_service_block, "started children must be tracked"
    assert "Stop-Owned-Children" in start_service_block, "start failure must trigger cleanup"


def test_dev_down_truthful_outcome_states() -> None:
    """V3-F5: shutdown outcome must not be blanket stopped=true."""
    assert "stopped" in _DEV_DOWN
    assert "already_exited" in _DEV_DOWN
    assert "refused_identity_mismatch" in _DEV_DOWN
    assert "stop_failed" in _DEV_DOWN
    assert "outcome" in _DEV_DOWN
    for line in _DEV_DOWN.splitlines():
        assert "stopped = `$true" not in line, "no blanket stopped=true"
        assert 'stopped = $true' not in line, "no blanket stopped=true"


def test_dev_down_cmd_exe_wrapped_frontend_accepted() -> None:
    """V3-F3: cmd.exe-wrapped frontend-vite must be accepted for shutdown."""
    assert "cmd.exe" in _DEV_DOWN
    assert "wrapped" in _DEV_DOWN
    assert "taskkill" in _DEV_DOWN


def test_single_opencode_model_note_in_frontend() -> None:
    """V3-F6: exactly one opencode-model-note in the composer."""
    count = _COMPOSER.count('data-testid="opencode-model-note"')
    assert count == 1, f"expected exactly 1 opencode-model-note, found {count}"


def test_single_opencode_model_note_regression_test_exists() -> None:
    """V3-F6: frontend regression must assert exactly one note."""
    assert "opencode-model-note" in _FRONTEND_TEST
    assert "notes.length" in _FRONTEND_TEST or "getByTestId" in _FRONTEND_TEST
    assert "toBe(1)" in _FRONTEND_TEST