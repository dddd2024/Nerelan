import pytest

from reverse_agent.user_solve_contract import (
    EvidenceStatus,
    UserSolveCandidate,
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
    contains_internal_reference,
)


def test_verified_requires_passed_validation_and_answer() -> None:
    with pytest.raises(ValueError, match="verified requires validation_status=passed"):
        UserSolveResult(
            status=UserSolveStatus.VERIFIED,
            validation_status=ValidationStatus.PENDING,
            answer="flag{maybe}",
        )
    with pytest.raises(ValueError, match="verified requires an answer or candidate"):
        UserSolveResult(
            status=UserSolveStatus.VERIFIED,
            validation_status=ValidationStatus.PASSED,
        )


def test_candidate_found_allows_pending_validation() -> None:
    result = UserSolveResult(
        status="candidate_found",
        validation_status="pending",
        evidence_status="building",
        candidates=[UserSolveCandidate("flag{candidate}", confidence=0.72)],
    )

    user_payload = result.to_user_dict()

    assert user_payload["status"] == "candidate_found"
    assert user_payload["validation_status"] == "pending"
    assert user_payload["evidence_status"] == "building"
    assert user_payload["candidates"][0]["value"] == "flag{candidate}"


def test_default_user_serialization_redacts_internal_paths() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.CANDIDATE_FOUND,
        validation_status=ValidationStatus.PENDING,
        evidence_status=EvidenceStatus.BUILDING,
        answer="flag{candidate}",
        message="see project_state/decision_packet.md and command_plan.json",
        reason="pytest_result.txt is internal",
        developer_trace_ref="project_state/gates/command_plan.json",
        internal_references=[
            "project_state/artifact_index.json",
            "project_state/negative_results.json",
            "project_state/codex_execution_report.md",
        ],
    )

    user_payload = result.to_user_dict()
    developer_payload = result.to_developer_dict()

    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["developer_trace_ref"])
    assert contains_internal_reference(developer_payload["internal_references"])


def test_blocked_requires_reason_or_message() -> None:
    with pytest.raises(ValueError, match="blocked requires"):
        UserSolveResult(status=UserSolveStatus.BLOCKED)
