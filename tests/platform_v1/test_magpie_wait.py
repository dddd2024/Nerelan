"""``magpie quota wait`` adapter: bounded, cancellable, never raises.

The danger with a blocking CLI in an unattended loop is not the happy path — it
is a missing binary, a bad target string, a wait that outlives shutdown, or a
child that never exits. Each of those is asserted here without spawning a real
process.
"""
from __future__ import annotations

import subprocess

import pytest

from reverse_agent.platform_v1 import magpie_wait
from reverse_agent.platform_v1.magpie_wait import (
    DEFAULT_TIMEOUT, parse_duration, valid_target, wait_for_allowance,
)


class FakeProc:
    """A child that either finishes with a code or hangs until terminated."""

    def __init__(self, *, returncode: int | None = 0):
        self.returncode = returncode
        self.terminated = False
        self.command = None
        self.kwargs = None

    def wait(self, timeout=None):
        if self.terminated:
            self.returncode = -15
            return -15
        if self.returncode is None:
            raise subprocess.TimeoutExpired(cmd="magpie", timeout=timeout)
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.terminated = True


class FakePopen:
    def __init__(self, proc: FakeProc, *, raises: BaseException | None = None):
        self.proc = proc
        self.raises = raises

    def __call__(self, command, **kwargs):
        if self.raises is not None:
            raise self.raises
        self.proc.command = command
        self.proc.kwargs = kwargs
        return self.proc


class Cancel:
    def __init__(self, already: bool = False):
        self._set = already

    def is_set(self):
        return self._set


def _exe(tmp_path):
    path = tmp_path / "magpie.exe"
    path.write_bytes(b"stub")
    return path


def test_duration_parsing_accepts_magpie_units():
    assert parse_duration("90s") == 90
    assert parse_duration("5m") == 300
    assert parse_duration("2h") == 7200
    assert parse_duration("1d") == 86400
    assert parse_duration("5 minutes") is None
    assert parse_duration("") is None
    assert parse_duration(None) is None


def test_target_validation_rejects_flags_and_metacharacters():
    assert valid_target("codex")
    assert valid_target("workbuddy-ai")
    assert valid_target("me@example.com")
    for bad in ("--timeout", "codex; rm -rf /", "codex && whoami", "codex\ncodex", "", None, "a" * 200):
        assert not valid_target(bad), bad


def test_available_when_magpie_exits_zero(tmp_path):
    proc = FakeProc(returncode=0)
    result = wait_for_allowance("codex", timeout="30s", exe=_exe(tmp_path), popen=FakePopen(proc))
    assert result["available"] is True
    assert result["reason"] == "allowance_available"
    assert proc.command[:3] == [str(_exe(tmp_path)), "quota", "wait"]
    assert proc.command[3] == "codex" and "--quiet" in proc.command
    assert proc.kwargs["shell"] is False  # fixed argv, never a shell


def test_our_bound_fires_before_magpie_hangs(tmp_path, monkeypatch):
    monkeypatch.setattr(magpie_wait, "GRACE_SECONDS", 0.05)
    proc = FakeProc(returncode=None)  # never finishes
    result = wait_for_allowance("codex", timeout="1s", exe=_exe(tmp_path),
                                popen=FakePopen(proc), poll_seconds=0.01)
    assert result["available"] is False
    assert result["reason"] == "timeout"
    assert proc.terminated is True, "a timed-out wait must not leave a child running"
    assert result["waited_seconds"] is not None and result["waited_seconds"] < 5


def test_cancellation_stops_without_waiting_out_the_window(tmp_path):
    """Shutdown must not wait for a multi-minute quota window."""
    proc = FakeProc(returncode=None)
    result = wait_for_allowance("codex", timeout="10m", exe=_exe(tmp_path),
                                popen=FakePopen(proc), cancel=Cancel(already=True))
    assert result["reason"] == "cancelled"
    assert proc.terminated is True
    assert result["waited_seconds"] is not None and result["waited_seconds"] < 1


def test_nonzero_exit_is_an_error_not_a_quota_verdict(tmp_path):
    result = wait_for_allowance("codex", timeout="30s", exe=_exe(tmp_path),
                                popen=FakePopen(FakeProc(returncode=2)))
    assert result["available"] is False and result["reason"] == "magpie_error"


def test_missing_binary_and_bad_input_never_spawn(tmp_path):
    assert wait_for_allowance("codex", env={})["reason"] == "magpie_not_configured"
    assert wait_for_allowance("--help", exe=_exe(tmp_path))["reason"] == "invalid_target"
    assert wait_for_allowance("codex", timeout="soon", exe=_exe(tmp_path))["reason"] == "invalid_timeout"


def test_spawn_failure_degrades_quietly(tmp_path):
    result = wait_for_allowance("codex", timeout="30s", exe=_exe(tmp_path),
                                popen=FakePopen(FakeProc(), raises=OSError("no exec")))
    assert result["available"] is False and result["reason"] == "magpie_error"


def test_terminate_falls_back_to_kill_when_the_child_ignores_it(tmp_path):
    class Stubborn(FakeProc):
        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="magpie", timeout=timeout)

        def terminate(self):
            self.terminated = True

    proc = Stubborn(returncode=None)
    result = wait_for_allowance("codex", timeout="10m", exe=_exe(tmp_path),
                                popen=FakePopen(proc), cancel=Cancel(already=True))
    assert result["reason"] == "cancelled"
    assert proc.terminated is True


def test_default_timeout_is_a_parseable_duration():
    assert parse_duration(DEFAULT_TIMEOUT) == 600


# --- coordinator integration: delegated wait is opt-in and cancellable ----------

def _coordinator(**attrs):
    from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
    coordinator = object.__new__(UnattendedCoordinator)
    coordinator._last_error = ""
    coordinator._stop = __import__("threading").Event()
    coordinator.quota_wait_target = None
    for key, value in attrs.items():
        setattr(coordinator, key, value)
    return coordinator


def test_coordinator_does_not_delegate_without_a_target(monkeypatch):
    called = []
    monkeypatch.setattr(magpie_wait, "wait_for_allowance",
                        lambda *a, **k: called.append(a) or {"available": True})
    coordinator = _coordinator()
    assert coordinator.quota_wait(600.0) is False
    assert called == []


def test_coordinator_delegates_only_long_waits_and_reports_capacity(monkeypatch):
    seen = {}

    def fake_wait(target, *, timeout, cancel):
        seen.update(target=target, timeout=timeout, cancelled=cancel.is_set())
        return {"available": True, "reason": "allowance_available", "waited_seconds": 1.0}

    monkeypatch.setattr(magpie_wait, "wait_for_allowance", fake_wait)
    coordinator = _coordinator(quota_wait_target="codex")

    assert coordinator.quota_wait(30.0) is False          # below the delegation floor
    assert seen == {}
    assert coordinator.quota_wait(900.0) is True           # long idle wait delegated
    assert seen["target"] == "codex"
    assert seen["timeout"] == "900s"
    assert seen["cancelled"] is False
    assert coordinator._last_error == ""


def test_coordinator_caps_the_delegated_window_and_surfaces_failures(monkeypatch):
    from reverse_agent.platform_v1.unattended_coordinator import QUOTA_WAIT_MAX_SECONDS

    seen = {}

    def fake_wait(target, *, timeout, cancel):
        seen["timeout"] = timeout
        return {"available": False, "reason": "magpie_error", "waited_seconds": 0.1}

    monkeypatch.setattr(magpie_wait, "wait_for_allowance", fake_wait)
    coordinator = _coordinator(quota_wait_target="codex")
    assert coordinator.quota_wait(48 * 3600.0) is False
    assert seen["timeout"] == f"{int(QUOTA_WAIT_MAX_SECONDS)}s"
    assert coordinator._last_error == "quota_wait_magpie_error"


def test_coordinator_passes_its_stop_event_as_the_cancel_token(monkeypatch):
    seen = {}

    def fake_wait(target, *, timeout, cancel):
        seen["is_stop"] = cancel is coordinator._stop
        return {"available": False, "reason": "cancelled", "waited_seconds": 0.2}

    monkeypatch.setattr(magpie_wait, "wait_for_allowance", fake_wait)
    coordinator = _coordinator(quota_wait_target="codex")
    coordinator.quota_wait(120.0)
    assert seen["is_stop"] is True  # stop() can interrupt a delegated wait
    assert coordinator._last_error == "quota_wait_cancelled"
