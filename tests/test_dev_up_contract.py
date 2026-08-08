from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_UP = ROOT / "dev-up.ps1"
DEV_DOWN = ROOT / "dev-down.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


_DEV_UP = _text(DEV_UP)
_DEV_DOWN = _text(DEV_DOWN)


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
    # "npm --prefix frontend run dev" is a dev-server invocation, not an install.
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
    assert 'npm' in _DEV_UP and "--prefix" in _DEV_UP and '"frontend"' in _DEV_UP and '"run"' in _DEV_UP and '"dev"' in _DEV_UP


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
