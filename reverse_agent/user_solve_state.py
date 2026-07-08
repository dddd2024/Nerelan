from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .user_solve_contract import UserSolveStatus, ValidationStatus


ALLOWED_TRANSITIONS: dict[UserSolveStatus, set[UserSolveStatus]] = {
    UserSolveStatus.UPLOADED: {
        UserSolveStatus.FAST_ANALYZING,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.FAST_ANALYZING: {
        UserSolveStatus.CANDIDATE_FOUND,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.CANDIDATE_FOUND: {
        UserSolveStatus.STATIC_VERIFIED,
        UserSolveStatus.RUNTIME_VALIDATION_PENDING,
        UserSolveStatus.VALIDATING,
        UserSolveStatus.VERIFIED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.STATIC_VERIFIED: {
        UserSolveStatus.RUNTIME_VALIDATION_PENDING,
        UserSolveStatus.VALIDATING,
        UserSolveStatus.VERIFIED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.RUNTIME_VALIDATION_PENDING: {
        UserSolveStatus.RUNTIME_VALIDATED,
        UserSolveStatus.STATIC_VERIFIED,
        UserSolveStatus.VERIFIED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.RUNTIME_VALIDATED: {
        UserSolveStatus.VERIFIED,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.VALIDATING: {
        UserSolveStatus.VERIFIED,
        UserSolveStatus.STATIC_VERIFIED,
        UserSolveStatus.RUNTIME_VALIDATED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.DEEP_ANALYSIS_RUNNING: {
        UserSolveStatus.CANDIDATE_FOUND,
        UserSolveStatus.STATIC_VERIFIED,
        UserSolveStatus.RUNTIME_VALIDATION_PENDING,
        UserSolveStatus.VALIDATING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.VERIFIED: set(),
    UserSolveStatus.FAILED: set(),
    UserSolveStatus.BLOCKED: set(),
}

STATES_REQUIRING_EVIDENCE: set[UserSolveStatus] = {
    UserSolveStatus.STATIC_VERIFIED,
    UserSolveStatus.RUNTIME_VALIDATED,
    UserSolveStatus.VERIFIED,
}


@dataclass(frozen=True)
class StateTransition:
    from_status: UserSolveStatus
    to_status: UserSolveStatus
    message: str = ""
    reason: str = ""
    evidence_refs: list[str] = field(default_factory=list)


class UserSolveStateMachine:
    def __init__(self, initial_status: UserSolveStatus | str = UserSolveStatus.UPLOADED):
        self._status = UserSolveStatus(initial_status)
        self._history: list[StateTransition] = []

    @property
    def status(self) -> UserSolveStatus:
        return self._status

    @property
    def history(self) -> list[StateTransition]:
        return list(self._history)

    def can_transition(self, to_status: UserSolveStatus | str) -> bool:
        target = UserSolveStatus(to_status)
        return target in ALLOWED_TRANSITIONS.get(self._status, set())

    def transition(
        self,
        to_status: UserSolveStatus | str,
        *,
        message: str = "",
        reason: str = "",
        evidence_refs: list[str] | None = None,
    ) -> StateTransition:
        target = UserSolveStatus(to_status)
        if target == UserSolveStatus.BLOCKED and not (message or reason):
            raise ValueError("blocked transition requires message or reason")
        if target == UserSolveStatus.FAILED and not (message or reason):
            raise ValueError("failed transition requires message or reason")
        if not self.can_transition(target):
            raise ValueError(f"invalid user solve transition: {self._status.value} -> {target.value}")
        if target in STATES_REQUIRING_EVIDENCE:
            refs = evidence_refs or []
            if not refs and not message:
                raise ValueError(f"{target.value} transition requires evidence_refs or message with evidence")
        transition = StateTransition(
            from_status=self._status,
            to_status=target,
            message=message,
            reason=reason,
            evidence_refs=list(evidence_refs or []),
        )
        self._history.append(transition)
        self._status = target
        return transition
