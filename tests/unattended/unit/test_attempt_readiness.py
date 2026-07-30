from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterable

import pytest

from reverse_agent.unattended.readiness import (
    ALIVE_OBSERVATION,
    READINESS_DEADLINE_SECONDS,
    READINESS_MAX_POLL_INTERVAL_SECONDS,
    AttemptReadinessTerminal,
    AttemptReadinessTimeout,
    ReadinessObservation,
    retryable_observation,
    terminal_observation,
    wait_for_attempt_readiness,
)
from reverse_agent.unattended.sandbox import AttemptContainerMetadata
from reverse_agent.unattended.temporal_contracts import AttemptReadinessProgress
from reverse_agent.unattended.activities import wait_attempt_server


def _metadata(state: str = "running") -> AttemptContainerMetadata:
    return AttemptContainerMetadata(
        container_name="reverse-agent-attempt-fixed",
        state=state,
        image_digest="sha256:" + ("a" * 64),
        workspace_destination="/workspace/attempt",
        network_name="issue84_model-executor",
        privileged=False,
        no_new_privileges=True,
        read_only_rootfs=True,
    )


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.delays: list[float] = []

    def monotonic(self) -> float:
        return self.value

    async def sleep(self, delay: float) -> None:
        self.delays.append(delay)
        self.value += delay


async def _run(
    observations: Iterable[ReadinessObservation],
    *,
    states: Iterable[str] = (),
    deadline_seconds: float = READINESS_DEADLINE_SECONDS,
    cancelled=lambda: False,
):
    pending_observations = iter(observations)
    pending_states = iter(states)
    clock = FakeClock()
    progress: list[AttemptReadinessProgress] = []
    inspect_count = 0

    async def inspect_container():
        nonlocal inspect_count
        inspect_count += 1
        return _metadata(next(pending_states, "running"))

    async def probe_loopback():
        return next(pending_observations)

    result = await wait_for_attempt_readiness(
        inspect_container=inspect_container,
        probe_loopback=probe_loopback,
        heartbeat=progress.append,
        cancelled=cancelled,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
        deadline_seconds=deadline_seconds,
    )
    return result, progress, clock, inspect_count


def test_connection_refused_then_refused_then_alive() -> None:
    result, progress, clock, inspections = asyncio.run(
        _run(
            (
                retryable_observation("connection_refused"),
                retryable_observation("connection_refused"),
                ALIVE_OBSERVATION,
            )
        )
    )
    assert result.poll_count == 3
    assert result.last_state == "alive"
    assert [item.state for item in progress] == [
        "connection_refused",
        "connection_refused",
    ]
    assert inspections == 3
    assert clock.delays == [0.25, 0.5]


def test_timeout_then_http_not_ready_then_alive() -> None:
    result, progress, _, inspections = asyncio.run(
        _run(
            (
                retryable_observation("timeout"),
                retryable_observation("HTTP_not_ready_status"),
                ALIVE_OBSERVATION,
            )
        )
    )
    assert result.alive and result.health
    assert [item.state for item in progress] == [
        "timeout",
        "HTTP_not_ready_status",
    ]
    assert inspections == 3


@pytest.mark.parametrize(
    "state",
    (
        "container_contract_drift",
        "malformed_bounded_response",
        "transport_protocol_violation",
        "unexpected_authentication_requirement",
        "credential_leakage_signal",
        "unexpected_terminal_failure",
    ),
)
def test_terminal_observation_fails_immediately(state: str) -> None:
    with pytest.raises(AttemptReadinessTerminal, match=state):
        asyncio.run(_run((terminal_observation(state),)))


@pytest.mark.parametrize("state", ("exited", "dead", "paused"))
def test_nonrunning_container_fails_before_transport(state: str) -> None:
    with pytest.raises(AttemptReadinessTerminal, match="container_not_running"):
        asyncio.run(_run((ALIVE_OBSERVATION,), states=(state,)))


def test_deadline_maps_to_exact_timeout() -> None:
    with pytest.raises(
        AttemptReadinessTimeout,
        match="ATTEMPT_READINESS_TIMEOUT",
    ):
        asyncio.run(
            _run(
                tuple(
                    retryable_observation("connection_refused")
                    for _ in range(20)
                ),
                deadline_seconds=0.5,
            )
        )


def test_cancellation_is_not_converted_to_retry_or_terminal() -> None:
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            _run(
                (retryable_observation("connection_refused"),),
                cancelled=lambda: True,
            )
        )


def test_retry_reinspects_same_container_without_launch_surface() -> None:
    result, _, _, inspections = asyncio.run(
        _run(
            (
                retryable_observation("connection_refused"),
                ALIVE_OBSERVATION,
            )
        )
    )
    assert result.poll_count == 2
    assert inspections == 2


def test_policy_is_bounded_and_documented() -> None:
    assert READINESS_DEADLINE_SECONDS == 90.0
    assert READINESS_MAX_POLL_INTERVAL_SECONDS == 3.0


def test_activity_does_not_use_generic_exception_retry() -> None:
    source = inspect.getsource(wait_attempt_server)
    assert "except Exception" not in source
    assert "ATTEMPT_READINESS_TIMEOUT" in source
    assert "ATTEMPT_READINESS_CONTRACT" in source
