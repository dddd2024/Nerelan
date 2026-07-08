import pytest

from reverse_agent.user_solve_contract import UserSolveStatus
from reverse_agent.user_solve_state import (
    ALLOWED_TRANSITIONS,
    STATES_REQUIRING_EVIDENCE,
    UserSolveStateMachine,
)


def test_user_solve_state_machine_accepts_valid_flow() -> None:
    machine = UserSolveStateMachine()

    machine.transition(UserSolveStatus.FAST_ANALYZING)
    machine.transition(UserSolveStatus.CANDIDATE_FOUND)
    machine.transition(UserSolveStatus.STATIC_VERIFIED, message="static evidence", evidence_refs=["evidence/static.json"])
    machine.transition(UserSolveStatus.RUNTIME_VALIDATION_PENDING, message="pending runtime")
    machine.transition(UserSolveStatus.RUNTIME_VALIDATED, message="runtime evidence", evidence_refs=["evidence/runtime.json"])

    assert machine.status == UserSolveStatus.RUNTIME_VALIDATED
    assert [item.to_status for item in machine.history] == [
        UserSolveStatus.FAST_ANALYZING,
        UserSolveStatus.CANDIDATE_FOUND,
        UserSolveStatus.STATIC_VERIFIED,
        UserSolveStatus.RUNTIME_VALIDATION_PENDING,
        UserSolveStatus.RUNTIME_VALIDATED,
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


def test_failed_transition_requires_reason() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.FAST_ANALYZING)

    with pytest.raises(ValueError, match="failed transition requires"):
        machine.transition(UserSolveStatus.FAILED)

    transition = machine.transition(UserSolveStatus.FAILED, reason="analysis error")
    assert transition.to_status == UserSolveStatus.FAILED


def test_static_verified_requires_evidence() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.CANDIDATE_FOUND)

    with pytest.raises(ValueError, match="static_verified transition requires evidence"):
        machine.transition(UserSolveStatus.STATIC_VERIFIED)

    transition = machine.transition(
        UserSolveStatus.STATIC_VERIFIED,
        evidence_refs=["evidence/static.json"],
    )
    assert transition.to_status == UserSolveStatus.STATIC_VERIFIED
    assert transition.evidence_refs == ["evidence/static.json"]


def test_runtime_validated_requires_evidence() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.RUNTIME_VALIDATION_PENDING)

    with pytest.raises(ValueError, match="runtime_validated transition requires evidence"):
        machine.transition(UserSolveStatus.RUNTIME_VALIDATED)

    transition = machine.transition(
        UserSolveStatus.RUNTIME_VALIDATED,
        message="runtime trace captured",
        evidence_refs=["evidence/runtime.json"],
    )
    assert transition.to_status == UserSolveStatus.RUNTIME_VALIDATED


def test_candidate_found_to_static_verified_allowed() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.CANDIDATE_FOUND)
    assert machine.can_transition(UserSolveStatus.STATIC_VERIFIED)
    assert machine.can_transition(UserSolveStatus.RUNTIME_VALIDATION_PENDING)


def test_runtime_validated_to_verified_allowed() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.RUNTIME_VALIDATED)
    assert machine.can_transition(UserSolveStatus.VERIFIED)


def test_states_requiring_evidence_includes_verified_statuses() -> None:
    assert UserSolveStatus.STATIC_VERIFIED in STATES_REQUIRING_EVIDENCE
    assert UserSolveStatus.RUNTIME_VALIDATED in STATES_REQUIRING_EVIDENCE
    assert UserSolveStatus.VERIFIED in STATES_REQUIRING_EVIDENCE


def test_evidence_refs_recorded_in_history() -> None:
    machine = UserSolveStateMachine(UserSolveStatus.CANDIDATE_FOUND)
    transition = machine.transition(
        UserSolveStatus.STATIC_VERIFIED,
        evidence_refs=["evidence/a.json", "evidence/b.json"],
    )
    assert transition.evidence_refs == ["evidence/a.json", "evidence/b.json"]
