from __future__ import annotations

from dataclasses import dataclass

from .user_solve_contract import UserSolveStatus


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
        UserSolveStatus.VALIDATING,
        UserSolveStatus.VERIFIED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.VALIDATING: {
        UserSolveStatus.VERIFIED,
        UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.DEEP_ANALYSIS_RUNNING: {
        UserSolveStatus.CANDIDATE_FOUND,
        UserSolveStatus.VALIDATING,
        UserSolveStatus.BLOCKED,
        UserSolveStatus.FAILED,
    },
    UserSolveStatus.VERIFIED: set(),
    UserSolveStatus.FAILED: set(),
    UserSolveStatus.BLOCKED: set(),
}


@dataclass(frozen=True)
class StateTransition:
    from_status: UserSolveStatus
    to_status: UserSolveStatus
    message: str = ""
    reason: str = ""


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
        return target in ALLOWED_TRANSITIONS[self._status]

    def transition(
        self,
        to_status: UserSolveStatus | str,
        *,
        message: str = "",
        reason: str = "",
    ) -> StateTransition:
        target = UserSolveStatus(to_status)
        if target == UserSolveStatus.BLOCKED and not (message or reason):
            raise ValueError("blocked transition requires message or reason")
        if not self.can_transition(target):
            raise ValueError(f"invalid user solve transition: {self._status.value} -> {target.value}")
        transition = StateTransition(
            from_status=self._status,
            to_status=target,
            message=message,
            reason=reason,
        )
        self._history.append(transition)
        self._status = target
        return transition
