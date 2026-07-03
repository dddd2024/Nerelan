import pytest

from reverse_agent.user_solve_contract import UserSolveStatus
from reverse_agent.user_solve_state import UserSolveStateMachine


def test_user_solve_state_machine_accepts_valid_flow() -> None:
    machine = UserSolveStateMachine()

    machine.transition(UserSolveStatus.FAST_ANALYZING)
    machine.transition(UserSolveStatus.CANDIDATE_FOUND)
    machine.transition(UserSolveStatus.VALIDATING)
    machine.transition(UserSolveStatus.VERIFIED)

    assert machine.status == UserSolveStatus.VERIFIED
    assert [item.to_status for item in machine.history] == [
        UserSolveStatus.FAST_ANALYZING,
        UserSolveStatus.CANDIDATE_FOUND,
        UserSolveStatus.VALIDATING,
        UserSolveStatus.VERIFIED,
    ]


def test_user_solve_state_machine_rejects_invalid_transition() -> None:
    machine = UserSolveStateMachine()

    with pytest.raises(ValueError, match="invalid user solve transition"):
        machine.transition(UserSolveStatus.VERIFIED)


def test_blocked_transition_requires_reason() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.FAST_ANALYZING)

    with pytest.raises(ValueError, match="blocked transition requires"):
        machine.transition(UserSolveStatus.BLOCKED)

    transition = machine.transition(UserSolveStatus.BLOCKED, reason="tool unavailable")
    assert transition.to_status == UserSolveStatus.BLOCKED
    assert transition.reason == "tool unavailable"
