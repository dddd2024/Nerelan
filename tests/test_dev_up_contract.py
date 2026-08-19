from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_UP = ROOT / "dev-up.ps1"
DEV_DOWN = ROOT / "dev-down.ps1"
COMPOSER = ROOT / "frontend/src/components/new-task-composer.tsx"
FRONTEND_TEST = ROOT / "frontend/tests/real-executor-task-plane.test.tsx"
LAUNCHER = ROOT / "launch_reverse_agent.bat"


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
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps1],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "False" in result.stdout.strip(), f"expected False for missing start_time, got: {result.stdout}"


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
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps1],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "False" in result.stdout.strip(), \
        f"expected False for unparseable start_time, got: {result.stdout}"


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
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps1],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"powershell exit={result.returncode}: {result.stderr}"
    assert "True" in result.stdout.strip(), \
        f"expected True for matching start_time, got: {result.stdout}"


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
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps1],
        capture_output=True, text=True, timeout=15,
    )
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
