"""Executor turn timeout is trusted host configuration with safe bounds."""
import pytest

from reverse_agent.platform_v1 import durable_execution as de


@pytest.mark.parametrize("raw,expected", [
    (None, 600), ("", 600), ("not-a-number", 600),
    ("900", 840), ("10", 60), ("420", 420),
])
def test_executor_timeout_is_bounded_host_configuration(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("REVERSE_AGENT_EXECUTOR_TIMEOUT_SECONDS", raw)
    assert de.executor_timeout_seconds() == expected


def test_native_executors_never_exceed_their_own_cap():
    assert de.NATIVE_EXECUTOR_TIMEOUT_MAX_SECONDS == 600
    assert de.MAX_EXECUTOR_TIMEOUT_SECONDS * 1000 < 15 * 60 * 1000  # below the coordinator claim lease
