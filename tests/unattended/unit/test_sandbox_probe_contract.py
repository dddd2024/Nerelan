from __future__ import annotations

from reverse_agent.unattended.sandbox_probe import _ENVIRONMENT_COMMAND


def test_session_state_scan_detects_assignments_not_its_own_probe_name() -> None:
    assert 'name + b"=" in candidate.read_bytes()' in _ENVIRONMENT_COMMAND
    assert "name in candidate.read_bytes()" not in _ENVIRONMENT_COMMAND
