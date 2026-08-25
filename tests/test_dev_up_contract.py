from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEV_UP = ROOT / "dev-up.ps1"
DEV_DOWN = ROOT / "dev-down.ps1"
COMPOSER = ROOT / "frontend/src/components/new-task-composer.tsx"
FRONTEND_TEST = ROOT / "frontend/tests/real-executor-task-plane.test.tsx"
LAUNCHER = ROOT / "launch_reverse_agent.bat"

_PWSH = shutil.which("powershell") or shutil.which("pwsh")
requires_powershell = pytest.mark.skipif(
    _PWSH is None, reason="requires powershell or pwsh"
)
requires_windows_powershell = pytest.mark.skipif(
    sys.platform != "win32" or shutil.which("powershell") is None,
    reason="requires Windows powershell",
)


def _run_ps(script: str, timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_PWSH or "powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, timeout=timeout,
    )


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_DEV_UP = _text(DEV_UP)
_DEV_DOWN = _text(DEV_DOWN)
_COMPOSER = _text(COMPOSER)
_FRONTEND_TEST = _text(FRONTEND_TEST)
_LAUNCHER = _text(LAUNCHER)


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


def test_unattended_coordinator_is_enabled_but_requires_runtime_window() -> None:
    assert '"REVERSE_AGENT_AUTONOMOUS" = "1"' in _DEV_UP
    assert "owner-activated window" in _DEV_UP


def test_desktop_launcher_starts_platform_stack_not_legacy_solver() -> None:
    lowered = _LAUNCHER.lower()
    assert "dev-up.ps1" in lowered
    assert "app.py" not in lowered


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
    assert "reverse_agent.platform_v1.trusted_host" in _DEV_UP
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


# ── V4-F2 deterministic regression coverage ──────────────────────────

def test_dev_down_has_process_start_time_comparison() -> None:
    """V4-F2: dev-down must contain a start_time comparison helper."""
    assert "Compare-ProcessStartTime" in _DEV_DOWN
    assert "ToUniversalTime" in _DEV_DOWN
    assert "TotalMilliseconds" in _DEV_DOWN
    assert "100" in _DEV_DOWN


def test_dev_down_checks_start_time_before_kill() -> None:
    """V4-F2: start_time must be validated before any Kill()/taskkill call."""
    try_stop = _DEV_DOWN[_DEV_DOWN.index("function Try-Stop-Child"):]
    kill_idx = try_stop.index("taskkill")
    compare_idx = try_stop.index("Compare-ProcessStartTime")
    assert compare_idx < kill_idx, "start_time comparison must precede any taskkill call"
    assert "refused_identity_mismatch" in try_stop[compare_idx:kill_idx], \
        "refused_identity_mismatch must be set between comparison and kill"


def test_dev_down_reads_start_time_from_record() -> None:
    """V4-F2: dev-down must extract start_time from the recorded child entry."""
    assert "start_time" in _DEV_DOWN
    assert "recordedStartTime" in _DEV_DOWN


@requires_powershell
def test_dev_down_refuses_missing_start_time() -> None:
    """V4-F2: missing start_time must produce refused_identity_mismatch, not a kill."""
    ps1 = r'''
function Compare-ProcessStartTime([string]$s, [datetime]$a) {
  if ([string]::IsNullOrWhiteSpace($s)) { return $false }
  $parsed = [datetime]::MinValue
  if (-not [datetime]::TryParse($s, [ref]$parsed)) { return $false }
  $recorded = $parsed
  if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
    $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
  }
  $recordedUtc = $recorded.ToUniversalTime()
  try { $actualUtc = $a.ToUniversalTime() } catch { return $false }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}
Compare-ProcessStartTime "" (Get-Date)
'''
    result = _run_ps(ps1)
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "False" in result.stdout.strip(), f"expected False for missing start_time, got: {result.stdout}"


@requires_powershell
def test_dev_down_refuses_unreadable_start_time() -> None:
    """V4-F2: unparseable start_time must produce refused_identity_mismatch, not a kill."""
    ps1 = r'''
function Compare-ProcessStartTime([string]$s, [datetime]$a) {
  if ([string]::IsNullOrWhiteSpace($s)) { return $false }
  $parsed = [datetime]::MinValue
  if (-not [datetime]::TryParse($s, [ref]$parsed)) { return $false }
  $recorded = $parsed
  if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
    $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
  }
  $recordedUtc = $recorded.ToUniversalTime()
  try { $actualUtc = $a.ToUniversalTime() } catch { return $false }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}
Compare-ProcessStartTime "not-a-real-timestamp" (Get-Date)
'''
    result = _run_ps(ps1)
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "False" in result.stdout.strip(), \
        f"expected False for unparseable start_time, got: {result.stdout}"


@requires_powershell
def test_dev_down_accepts_matching_start_time() -> None:
    """V4-F2: same process instance (matching start_time) must be accepted."""
    ps1 = r'''
function Compare-ProcessStartTime([string]$s, [datetime]$a) {
  if ([string]::IsNullOrWhiteSpace($s)) { return $false }
  $parsed = [datetime]::MinValue
  if (-not [datetime]::TryParse($s, [ref]$parsed)) { return $false }
  $recorded = $parsed
  if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
    $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
  }
  $recordedUtc = $recorded.ToUniversalTime()
  try { $actualUtc = $a.ToUniversalTime() } catch { return $false }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}
$now = (Get-Date)
Compare-ProcessStartTime ($now.ToString("o")) $now
'''
    result = _run_ps(ps1)
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "True" in result.stdout.strip(), \
        f"expected True for matching start_time, got: {result.stdout}"


@requires_powershell
def test_dev_down_refuses_recycled_pid_with_different_start_time() -> None:
    """V4-F2: recycled PID with same exe but different start_time must be refused."""
    ps1 = r'''
function Compare-ProcessStartTime([string]$s, [datetime]$a) {
  if ([string]::IsNullOrWhiteSpace($s)) { return $false }
  $parsed = [datetime]::MinValue
  if (-not [datetime]::TryParse($s, [ref]$parsed)) { return $false }
  $recorded = $parsed
  if ($recorded.Kind -eq [System.DateTimeKind]::Unspecified) {
    $recorded = [datetime]::SpecifyKind($recorded, [System.DateTimeKind]::Utc)
  }
  $recordedUtc = $recorded.ToUniversalTime()
  try { $actualUtc = $a.ToUniversalTime() } catch { return $false }
  $diffMs = [math]::Abs(($recordedUtc - $actualUtc).TotalMilliseconds)
  return $diffMs -le 100
}
$old = (Get-Date).AddDays(-1)
$new = (Get-Date)
Compare-ProcessStartTime ($old.ToString("o")) $new
'''
    result = _run_ps(ps1)
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "False" in result.stdout.strip(), \
        f"expected False for recycled PID (different start_time), got: {result.stdout}"


def test_dev_down_output_includes_start_time_validation_fields() -> None:
    """V4-F2: the truthful outcome must signal start_time identity mismatch."""
    assert "refused_identity_mismatch" in _DEV_DOWN
    for word in ("refused", "start_time", "recorded", "identity"):
        assert word in _DEV_DOWN, f"missing keyword in dev-down: {word}"
    for forbidden in ("taskkill /IM", "Get-Process | Stop-Process", "Stop-Process -Force"):
        assert forbidden not in _DEV_DOWN, f"name-wide kill still present: {forbidden}"


# ── V8 entrypoint contract ──────────────────────────────────────────

def test_combined_trusted_host_module_entrypoint_contract() -> None:
    """V8: trusted_host.py must have an executable __main__ guard that calls run_combined_trusted_host()."""
    import ast
    from reverse_agent.platform_v1 import trusted_host

    source = _text(Path(trusted_host.__file__))
    tree = ast.parse(source, filename="trusted_host.py")

    guard_found = False
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not isinstance(test, ast.Compare):
            continue
        if not (isinstance(test.left, ast.Name) and test.left.id == "__name__"):
            continue
        if not (len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
            continue
        if not (isinstance(test.comparators[0], ast.Constant) and test.comparators[0].value == "__main__"):
            continue
        guard_found = True
        assert len(node.body) >= 1, "guard body must contain at least one statement"
        call = node.body[0]
        assert isinstance(call, ast.Expr), "guard body first stmt must be an expression"
        assert isinstance(call.value, ast.Call), "guard body first expr must be a Call"
        func = call.value.func
        assert isinstance(func, ast.Name), "call target must be a Name"
        assert func.id == "run_combined_trusted_host", \
            f"guard must call run_combined_trusted_host, got {func.id}"
        assert call.value.args == [], "call must take no positional arguments"
        assert call.value.keywords == [], "call must take no keyword arguments"
        break

    assert guard_found, (
        "trusted_host.py is missing a conventional "
        'if __name__ == "__main__": guard that invokes run_combined_trusted_host()'
    )


# ── Idempotent dev-up startup coverage (#317 / #355) ────────────────

def test_dev_up_blank_repo_dir_resolves_to_script_location() -> None:
    """Blank RepoDir must resolve to the script directory, never the caller's CWD."""
    lines = _DEV_UP.splitlines()
    blank_idx = None
    for i, line in enumerate(lines):
        if "IsNullOrWhiteSpace($RepoDir)" in line:
            blank_idx = i
            break
    assert blank_idx is not None, "no RepoDir blank check found"
    block = "\n".join(lines[blank_idx: blank_idx + 8])
    assert "$repoDir = $PSScriptRoot" in block, \
        "blank RepoDir must deterministically resolve to the script directory"
    assert "Resolve-InputPath $RepoDir" in block, \
        "explicit RepoDir must still resolve through Resolve-InputPath"


def test_dev_up_validates_dirs_before_creating_runtime_directory() -> None:
    """Path validation must run before any runtime directory mutation."""
    first_validation = _DEV_UP.index("Get-InvalidDirReason -candidate")
    mkdir_runtime = _DEV_UP.index("New-Item -ItemType Directory -Path $runtimeDir")
    assert first_validation < mkdir_runtime, \
        "directory validation must precede New-Item on the runtime directory"


def test_dev_up_reconciles_record_before_starting_services() -> None:
    """The recorded runtime state must be read and reconciled before any service start."""
    record_read = _DEV_UP.index("Get-Content -LiteralPath $pidFile")
    first_service_start = _DEV_UP.index('-name "combined-trusted-host"')
    assert record_read < first_service_start, \
        "runtime record must be reconciled before starting services"
    assert "Test-RecordedChildOwned" in _DEV_UP
    assert "reusing recorded runtime" in _DEV_UP
    assert "repair: stopping recorded child" in _DEV_UP


def test_dev_up_reports_invalid_runtime_state_with_diagnostic() -> None:
    """A corrupt record must produce an explicit diagnostic naming the record file."""
    assert "invalid runtime state at ${pidFile}" in _DEV_UP
    assert "unparseable record" in _DEV_UP
    assert "empty record" in _DEV_UP


def test_dev_up_refuses_foreign_runtime_records() -> None:
    """A record from a different repo_dir must never be reused or stopped."""
    assert "belongs to a different repo_dir" in _DEV_UP


def test_dev_up_never_assigns_parent_environment() -> None:
    """dev-up must not poison the caller's session with $env: assignments."""
    assert re.search(r"\$env:[A-Za-z_][A-Za-z0-9_]*\s*=", _DEV_UP) is None, \
        "dev-up must not assign $env: in the parent session"


def test_dev_up_fail_log_derives_from_runtime_dir() -> None:
    """The fail-closed log must not depend on the caller's working directory."""
    fail_block = _DEV_UP[
        _DEV_UP.index("function Fail-Closed"): _DEV_UP.index("}", _DEV_UP.index("function Fail-Closed")) + 1
    ]
    assert "(Get-Location)" not in fail_block, \
        "Fail-Closed must not derive its log path from the current location"
    assert "$script:runtimeDir" in fail_block, \
        "Fail-Closed must prefer the validated runtime directory"
    assert "devup.fail.log" in _DEV_UP


def test_dev_up_ports_are_parameterized_with_stable_defaults() -> None:
    """Ports must be parameterizable for hermetic regression runs with unchanged defaults."""
    assert "[int]$FrontendPort = 4173" in _DEV_UP
    assert "[int]$TaskApiPort = 8766" in _DEV_UP
    assert "[int]$ModelControlPort = 8765" in _DEV_UP
    assert "0.0.0.0" not in _DEV_UP


def test_dev_up_service_children_do_not_inherit_parent_stdio() -> None:
    """Service children must not hold dev-up's stdout/stderr pipe handles.

    A long-lived child that inherits the caller's pipe write end blocks any
    orchestrator (pytest, CI) reading dev-up output until EOF — even after
    dev-up exits, and even after a subprocess timeout kills dev-up itself.
    Only a ShellExecute launch (no handle inheritance) avoids this, with
    per-child environment variables carried by `set` commands inside the
    cmd.exe wrapper.
    """
    start_block = _DEV_UP[
        _DEV_UP.index("function Start-ServiceProcess"): _DEV_UP.index(
            "function Wait-ServiceReady", _DEV_UP.index("function Start-ServiceProcess")
        )
    ]
    assert "$psi.UseShellExecute = $true" in start_block, \
        "services must launch via ShellExecute so no handles are inherited"
    assert "$psi.UseShellExecute = $false" not in start_block, \
        "the inheritable-handle launch path must not be used for services"
    assert "/s /c" in start_block, \
        "every service must run behind a cmd.exe /s /c wrapper"
    assert "2>&1" in start_block, \
        "the wrapper must redirect the service's stdio into a per-service log file"
    assert 'Join-Path $logDir "${name}.log"' in start_block, \
        "per-service log files must derive from the runtime log directory"
    assert 'set `"' in start_block, \
        "per-child environment variables must travel as cmd.exe set commands"


@requires_powershell
def test_dev_up_dir_validator_rejects_invalid_values() -> None:
    """The real validator from dev-up.ps1 must reject invalid directory inputs."""
    start = _DEV_UP.index("function Get-InvalidDirReason")
    end = _DEV_UP.index("\nfunction ", start + 1)
    function_source = _DEV_UP[start:end]

    cases = [
        ("", "REJECT"),
        ("   ", "REJECT"),
        ('"F:\\re po"', "REJECT"),
        ("F:\\repo|.platform", "REJECT"),
        ("F:\\repo\\.platform_v1_runtime", "REJECT"),
        ("F:\\repo\\.platform_v1_runtime\\sub", "REJECT"),
        ("F:\\repo", "ACCEPT"),
        ("F:\\my repo", "ACCEPT"),
        ("C:\\Program Files\\app", "ACCEPT"),
    ]
    ps_lines = [function_source, "$results = @()"]
    for value, _ in cases:
        escaped = value.replace("'", "''")
        ps_lines.append(
            "if (Get-InvalidDirReason '" + escaped + "' 'RepoDir') "
            "{ $results += 'REJECT' } else { $results += 'ACCEPT' }"
        )
    ps_lines.append("$results -join ','")

    result = _run_ps("\n".join(ps_lines), timeout=30)
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    got = result.stdout.strip().split(",")
    expected = [expected_outcome for _, expected_outcome in cases]
    assert got == expected, f"validator decisions mismatch: got {got}, expected {expected}"


_STUB_HOST_PS = r'''
param(
  [int]$FrontendPort = 0,
  [int]$TaskApiPort = 0,
  [int]$ModelControlPort = 0
)
$ports = @()
if ($FrontendPort -gt 0) { $ports += $FrontendPort }
if ($TaskApiPort -gt 0) { $ports += $TaskApiPort }
if ($ModelControlPort -gt 0) { $ports += $ModelControlPort }
$loop = {
  param([int]$listenPort)
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $listenPort)
  $listener.Start()
  try {
    while ($true) {
      $client = $listener.AcceptTcpClient()
      try {
        $stream = $client.GetStream()
        $buffer = New-Object byte[] 4096
        $null = $stream.Read($buffer, 0, $buffer.Length)
        $head = [System.Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 OK`r`nContent-Length: 2`r`nConnection: close`r`n`r`n")
        $body = [System.Text.Encoding]::ASCII.GetBytes("ok")
        $stream.Write($head, 0, $head.Length)
        $stream.Write($body, 0, $body.Length)
        $stream.Flush()
      } catch {
      } finally {
        try { $client.Close() } catch {}
      }
    }
  } finally {
    try { $listener.Stop() } catch {}
  }
}
foreach ($listenPort in $ports) {
  $worker = [powershell]::Create().AddScript($loop).AddArgument($listenPort)
  $null = $worker.BeginInvoke()
}
while ($true) { Start-Sleep -Seconds 30 }
'''


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _setup_stub_stack(tmp_path: Path) -> tuple[Path, dict, dict]:
    repo = tmp_path / "repo"
    (repo / "frontend" / "node_modules").mkdir(parents=True)
    stub_dir = tmp_path / "stubbin"
    stub_dir.mkdir()
    (stub_dir / "stub-host.ps1").write_text(_STUB_HOST_PS, encoding="ascii")
    (stub_dir / "python.cmd").write_text(
        "@echo off\r\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0stub-host.ps1\" "
        "-TaskApiPort %REVERSE_AGENT_TASK_SERVICE_PORT% "
        "-ModelControlPort %REVERSE_AGENT_MODEL_CONTROL_PORT% >nul 2>&1\r\n",
        encoding="ascii",
    )
    (stub_dir / "npm.cmd").write_text(
        "@echo off\r\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0stub-host.ps1\" "
        "-FrontendPort %VITE_PORT% >nul 2>&1\r\n",
        encoding="ascii",
    )
    (stub_dir / "node.cmd").write_text("@echo off\r\n", encoding="ascii")
    (stub_dir / "opencode.cmd").write_text("@echo off\r\n", encoding="ascii")

    ports = {"frontend": _free_port(), "task": _free_port(), "model": _free_port()}
    env = os.environ.copy()
    env["PATH"] = str(stub_dir) + os.pathsep + env.get("PATH", "")
    return repo, env, ports


def _run_dev_up(repo: Path, env: dict, ports: dict, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(DEV_UP),
            "-RepoDir", str(repo), "-SourceDir", str(repo),
            "-FrontendPort", str(ports["frontend"]),
            "-TaskApiPort", str(ports["task"]),
            "-ModelControlPort", str(ports["model"]),
            "-NoBrowser",
        ],
        capture_output=True, text=True, timeout=timeout, env=env, cwd=str(repo),
    )


def _run_dev_down(repo: Path, env: dict, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(DEV_DOWN), "-RepoDir", str(repo),
        ],
        capture_output=True, text=True, timeout=timeout, env=env, cwd=str(repo),
    )


def _assert_ports_free(ports: dict) -> None:
    time.sleep(1.0)
    for port in ports.values():
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=3)


def _assert_ports_reachable(ports: dict) -> None:
    for port in ports.values():
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            pass


@requires_windows_powershell
def test_dev_up_five_consecutive_runs_are_idempotent(tmp_path: Path) -> None:
    """Five consecutive dev-up runs: fresh start once, pure reuse four times."""
    repo, env, ports = _setup_stub_stack(tmp_path)
    pid_file = repo / ".platform_v1_runtime" / "devup_pids.json"
    runtime_state_paths: list[str] = []
    first_record: str | None = None

    for run_index in range(1, 6):
        result = _run_dev_up(repo, env, ports)
        assert result.returncode == 0, (
            f"run {run_index} failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
        for line in result.stdout.splitlines():
            if line.startswith("Runtime state:"):
                runtime_state_paths.append(line.split(":", 1)[1].strip())
        if run_index == 1:
            assert result.stdout.count("started pid=") == 2, result.stdout
            first_record = pid_file.read_text(encoding="utf-8-sig")
            record = json.loads(first_record)
            assert len(record["children"]) == 2
            for child in record["children"]:
                assert child["pid"]
                assert child["start_time"]
        else:
            assert "reusing recorded runtime" in result.stdout, (
                f"run {run_index} did not reuse the recorded stack:\n{result.stdout}"
            )
            assert "started pid=" not in result.stdout, (
                f"run {run_index} started new services:\n{result.stdout}"
            )
            assert pid_file.read_text(encoding="utf-8-sig") == first_record, (
                f"run {run_index} rewrote the runtime record during pure reuse"
            )

    assert len(runtime_state_paths) == 5
    assert len(set(runtime_state_paths)) == 1, "runtime state path differed across runs"
    assert runtime_state_paths[0].lower() == str(pid_file).lower()
    assert list((repo / ".platform_v1_runtime").glob(".platform_v1_runtime")) == [], \
        "a nested .platform_v1_runtime directory was created"

    _assert_ports_reachable(ports)

    down = _run_dev_down(repo, env)
    assert down.returncode == 0, f"dev-down failed:\n{down.stdout}\n{down.stderr}"
    _assert_ports_free(ports)


@requires_windows_powershell
def test_dev_up_repairs_partial_stack_by_restarting_it(tmp_path: Path) -> None:
    """One dead owned child must be repaired on the next run with exit 0."""
    repo, env, ports = _setup_stub_stack(tmp_path)
    pid_file = repo / ".platform_v1_runtime" / "devup_pids.json"

    first = _run_dev_up(repo, env, ports)
    assert first.returncode == 0, f"{first.stdout}\n{first.stderr}"
    record_before = json.loads(pid_file.read_text(encoding="utf-8-sig"))
    frontend_entry = next(
        child for child in record_before["children"] if child["name"] == "frontend-vite"
    )
    subprocess.run(
        ["taskkill", "/PID", str(frontend_entry["pid"]), "/T", "/F"],
        capture_output=True, timeout=30,
    )

    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", ports["frontend"]), timeout=1):
                pass
            time.sleep(0.2)
        except OSError:
            break
    else:
        pytest.fail("frontend port did not free after killing the frontend child")

    second = _run_dev_up(repo, env, ports)
    assert second.returncode == 0, (
        f"repair run failed:\nstdout={second.stdout}\nstderr={second.stderr}"
    )
    assert "repair: stopping recorded child" in second.stdout, second.stdout
    record_after = json.loads(pid_file.read_text(encoding="utf-8-sig"))
    assert record_after != record_before, "runtime record was not rewritten by the repair run"
    assert len(record_after["children"]) == 2

    _assert_ports_reachable(ports)

    down = _run_dev_down(repo, env)
    assert down.returncode == 0, down.stderr
    _assert_ports_free(ports)


@requires_windows_powershell
def test_dev_up_invalid_runtime_state_produces_diagnostic_and_fresh_start(tmp_path: Path) -> None:
    """A corrupt record with free ports must warn explicitly and start fresh."""
    repo, env, ports = _setup_stub_stack(tmp_path)
    pid_file = repo / ".platform_v1_runtime" / "devup_pids.json"

    first = _run_dev_up(repo, env, ports)
    assert first.returncode == 0, f"{first.stdout}\n{first.stderr}"
    down = _run_dev_down(repo, env)
    assert down.returncode == 0, down.stderr

    pid_file.write_text("{ this is not a valid devup record", encoding="utf-8")

    second = _run_dev_up(repo, env, ports)
    assert second.returncode == 0, (
        f"fresh start after corrupt record failed:\nstdout={second.stdout}\nstderr={second.stderr}"
    )
    combined = second.stdout + second.stderr
    assert "invalid runtime state" in combined, combined
    assert second.stdout.count("started pid=") == 2, second.stdout

    record = json.loads(pid_file.read_text(encoding="utf-8-sig"))
    assert len(record["children"]) == 2

    _assert_ports_reachable(ports)

    down2 = _run_dev_down(repo, env)
    assert down2.returncode == 0, down2.stderr
    _assert_ports_free(ports)
