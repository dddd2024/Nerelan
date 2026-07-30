"""Finite sanitized states for the Attempt Agent Server readiness boundary."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .sandbox import AttemptContainerMetadata
from .temporal_contracts import AttemptReadinessProgress, AttemptReadinessResult

READINESS_DEADLINE_SECONDS = 90.0
READINESS_POLL_SCHEDULE_SECONDS = (0.25, 0.5, 1.0, 2.0, 3.0)
READINESS_MAX_POLL_INTERVAL_SECONDS = max(READINESS_POLL_SCHEDULE_SECONDS)

RETRYABLE_READINESS_STATES = frozenset(
    {
        "connection_refused",
        "timeout",
        "HTTP_not_ready_status",
    }
)
TERMINAL_READINESS_STATES = frozenset(
    {
        "container_not_running",
        "malformed_bounded_response",
        "transport_protocol_violation",
        "container_contract_drift",
        "unexpected_authentication_requirement",
        "credential_leakage_signal",
        "unexpected_terminal_failure",
    }
)
_ALL_READINESS_STATES = (
    RETRYABLE_READINESS_STATES
    | TERMINAL_READINESS_STATES
    | {"alive"}
)


@dataclass(frozen=True, slots=True)
class ReadinessObservation:
    state: str
    retryable: bool
    alive: bool

    def __post_init__(self) -> None:
        if self.state not in _ALL_READINESS_STATES:
            raise ValueError("invalid_readiness_state")
        if not isinstance(self.retryable, bool) or not isinstance(self.alive, bool):
            raise ValueError("invalid_readiness_flags")
        if self.state == "alive":
            if self.retryable or not self.alive:
                raise ValueError("alive_readiness_inconsistent")
        elif self.alive:
            raise ValueError("nonalive_readiness_inconsistent")
        elif self.retryable != (self.state in RETRYABLE_READINESS_STATES):
            raise ValueError("readiness_retryability_inconsistent")


def retryable_observation(state: str) -> ReadinessObservation:
    if state not in RETRYABLE_READINESS_STATES:
        raise ValueError("readiness_state_not_retryable")
    return ReadinessObservation(state=state, retryable=True, alive=False)


def terminal_observation(state: str) -> ReadinessObservation:
    if state not in TERMINAL_READINESS_STATES:
        raise ValueError("readiness_state_not_terminal")
    return ReadinessObservation(state=state, retryable=False, alive=False)


ALIVE_OBSERVATION = ReadinessObservation(
    state="alive",
    retryable=False,
    alive=True,
)


class AttemptReadinessTimeout(RuntimeError):
    """The fixed readiness deadline expired."""


class AttemptReadinessTerminal(RuntimeError):
    """A finite non-retryable readiness state."""

    def __init__(self, state: str) -> None:
        if state not in TERMINAL_READINESS_STATES:
            raise ValueError("invalid_terminal_readiness_state")
        super().__init__(state)
        self.state = state


async def wait_for_attempt_readiness(
    *,
    inspect_container: Callable[[], Awaitable[AttemptContainerMetadata | None]],
    probe_loopback: Callable[[], Awaitable[ReadinessObservation]],
    heartbeat: Callable[[AttemptReadinessProgress], None],
    cancelled: Callable[[], bool],
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    deadline_seconds: float = READINESS_DEADLINE_SECONDS,
    poll_schedule_seconds: tuple[float, ...] = READINESS_POLL_SCHEDULE_SECONDS,
) -> AttemptReadinessResult:
    """Wait only through finite startup states without creating a container."""

    if deadline_seconds <= 0 or not poll_schedule_seconds:
        raise ValueError("invalid_readiness_policy")
    if any(delay <= 0 for delay in poll_schedule_seconds):
        raise ValueError("invalid_readiness_poll_schedule")
    started = monotonic()
    deadline = started + deadline_seconds
    poll_count = 0
    last_state = "connection_refused"

    while True:
        if cancelled():
            raise asyncio.CancelledError
        metadata = await inspect_container()
        if metadata is None or metadata.state != "running":
            raise AttemptReadinessTerminal("container_not_running")

        observation = await probe_loopback()
        poll_count += 1
        last_state = observation.state
        if observation.alive:
            return AttemptReadinessResult(
                alive=True,
                health=True,
                poll_count=poll_count,
                last_state=last_state,
            )
        if not observation.retryable:
            raise AttemptReadinessTerminal(observation.state)

        now = monotonic()
        remaining = deadline - now
        if remaining <= 0:
            raise AttemptReadinessTimeout("ATTEMPT_READINESS_TIMEOUT")
        selected = poll_schedule_seconds[
            min(poll_count - 1, len(poll_schedule_seconds) - 1)
        ]
        delay = min(selected, remaining)
        elapsed_milliseconds = max(0, int((now - started) * 1000))
        heartbeat(
            AttemptReadinessProgress(
                state=last_state,
                poll_count=poll_count,
                elapsed_milliseconds=elapsed_milliseconds,
                next_delay_milliseconds=max(1, int(delay * 1000)),
            )
        )
        await sleep(delay)
