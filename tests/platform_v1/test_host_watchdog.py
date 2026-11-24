"""Host watchdog (2026-11-18): restart a host that died on its own, never a deliberate stop.

Provider-free: the PowerShell script runs with -DryRun against a temporary repo folder and
a local health stub; it starts no host, Magpie or browser.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WATCH = ROOT / "scripts" / "windows" / "Watch-NerelanHost.ps1"
INSTALL = ROOT / "scripts" / "windows" / "Install-HostWatchdog.ps1"

_PWSH = shutil.which(os.environ.get("NERELAN_TEST_POWERSHELL", "powershell")) or shutil.which("pwsh")
# The watchdog reads the Windows process list (Win32_Process); off Windows it never restarts.
requires_powershell = pytest.mark.skipif(_PWSH is None or os.name != "nt", reason="requires Windows PowerShell")
CLOSED = "http://127.0.0.1:9/api/health"  # discard port: nothing answers


def decide(repo: Path, health: str = CLOSED) -> str:
    env = dict(os.environ, LOCALAPPDATA=str(repo / "appdata"))
    result = subprocess.run(
        [_PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(WATCH), "-RepoDir", str(repo),
         "-HealthUrl", health, "-HealthAttempts", "1", "-DryRun"],
        capture_output=True, text=True, timeout=60, env=env)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def record(repo: Path, **fields) -> None:
    runtime = repo / ".platform_v1_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "devup_pids.json").write_text(json.dumps({"created_at": "2026-11-18T05:07:43Z", **fields}),
                                             encoding="utf-8")


@requires_powershell
def test_a_host_that_died_on_its_own_is_restarted(tmp_path):
    record(tmp_path, children=[{"name": "combined-trusted-host", "pid": 1}])
    assert decide(tmp_path) == "restart"


@requires_powershell
def test_a_deliberate_stop_or_missing_record_is_left_alone(tmp_path):
    assert decide(tmp_path) == "no_record"
    record(tmp_path, stopped_at="2026-11-18T09:06:52Z", children=[])
    assert decide(tmp_path) == "stopped_deliberately"


@requires_powershell
def test_a_recent_watchdog_restart_cools_down(tmp_path):
    record(tmp_path, children=[])
    marker = tmp_path / ".platform_v1_runtime" / "watchdog_last_restart.txt"
    marker.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    assert decide(tmp_path) == "restart_cooling_down"
    marker.write_text("2026-11-01T00:00:00+00:00", encoding="utf-8")
    assert decide(tmp_path) == "restart"


@requires_powershell
def test_a_ready_host_is_healthy(tmp_path):
    class Ready(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - http.server API
            body = b'{"ready":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Ready)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        record(tmp_path, children=[])
        assert decide(tmp_path, f"http://127.0.0.1:{server.server_port}/api/health") == "healthy"
    finally:
        server.shutdown()


def test_the_scheduled_task_never_times_out_or_overlaps():
    text = INSTALL.read_text(encoding="utf-8")
    assert "-ExecutionTimeLimit (New-TimeSpan -Seconds 0)" in text
    assert "-MultipleInstances IgnoreNew" in text
    assert "-RunLevel Limited" in text and "Watch-NerelanHost.ps1" in text


def test_dev_up_runs_the_host_with_the_crash_trace_on():
    text = (ROOT / "dev-up.ps1").read_text(encoding="utf-8")
    block = text[text.index("$combinedTrustedHostEnv = [ordered]@{"):text.index("$combinedProc = Start-ServiceProcess")]
    assert '"PYTHONFAULTHANDLER" = "1"' in block


def test_a_restart_keeps_the_dead_hosts_log_and_the_browser_setting():
    text = WATCH.read_text(encoding="utf-8")
    assert "Copy-Item -LiteralPath $hostLog" in text
    assert r"dev-down\.ps1" in text  # a stop in progress also blocks a restart
    assert 'if ($NoBrowser) { $arguments += "-NoBrowser" }' in text
    assert 'if ($NoBrowser) { $arguments += " -NoBrowser" }' in INSTALL.read_text(encoding="utf-8")


def test_the_watchdog_never_opens_a_window_that_takes_the_foreground():
    # 2026-11-18: a task starting powershell.exe directly flashed a console every 5 minutes
    # and threw the Owner out of full-screen games.
    install = INSTALL.read_text(encoding="utf-8")
    assert r'System32\conhost.exe' in install and '"--headless `"$powershell`" $arguments"' in install
    watch = WATCH.read_text(encoding="utf-8")
    assert "-NoNewWindow -PassThru" in watch and "-WindowStyle Hidden -PassThru" not in watch
