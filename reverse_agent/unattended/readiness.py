"""Finite sanitized states for the Attempt Agent Server readiness boundary."""

from __future__ import annotations

from dataclasses import dataclass

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
