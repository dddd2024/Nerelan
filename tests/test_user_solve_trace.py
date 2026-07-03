import pytest

from reverse_agent.fallback_ladder import FallbackLadder
from reverse_agent.user_solve_contract import UserSolveResult, UserSolveStatus, ValidationStatus, contains_internal_reference
from reverse_agent.user_solve_trace import (
    ArtifactReference,
    CandidateSource,
    FallbackStepRecord,
    UserSolveTaskTrace,
    ValidationRecord,
)


def test_trace_serialization_redacts_user_payload_and_keeps_developer_refs() -> None:
    trace = UserSolveTaskTrace(
        task_id="task-1",
        user_status=UserSolveStatus.CANDIDATE_FOUND,
        engineering_status="building",
        validation=ValidationRecord(
            status=ValidationStatus.PENDING,
            result="waiting on project_state/gates/user_solve_trace_fallback_result.json",
            developer_trace_ref="project_state/decision_packet.md",
        ),
        candidate_sources=[
            CandidateSource(
                name="fast wrapper",
                source_type="in_memory",
                confidence=0.8,
                developer_trace_ref="project_state/artifact_index.json",
            )
        ],
        fallback_steps=[
            FallbackStepRecord(
                name="ida_summary",
                sequence=1,
                missing_evidence=["project_state/artifact_index.json"],
            )
        ],
        artifact_references=[
            ArtifactReference(
                label="gate artifact",
                path="project_state/gates/user_solve_trace_fallback_result.json",
                public=False,
            )
        ],
        developer_trace_ref="project_state/decision_packet.md",
    )

    user_payload = trace.to_user_dict()
    developer_payload = trace.to_developer_dict()

    assert user_payload["user_status"] == "candidate_found"
    assert not user_payload["artifact_references"]
    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["developer_trace_ref"])
    assert contains_internal_reference(developer_payload["artifact_references"])


def test_trace_rejects_verified_without_passed_validation() -> None:
    with pytest.raises(ValueError, match="verified trace requires passed validation"):
        UserSolveTaskTrace(
            task_id="task-verified",
            user_status=UserSolveStatus.VERIFIED,
            engineering_status="complete",
            validation=ValidationRecord(status=ValidationStatus.PENDING),
        )


def test_trace_from_result_includes_fallback_metadata_without_execution() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.DEEP_ANALYSIS_RUNNING,
        validation_status=ValidationStatus.UNAVAILABLE,
        message="More evidence needed.",
    )
    fallback = FallbackLadder.default().select_next(
        missing_evidence=["targeted_decompile_missing"],
    )

    trace = UserSolveTaskTrace.from_result(
        task_id="task-from-result",
        result=result,
        fallback_decision=fallback,
        missing_evidence=["targeted_decompile_missing"],
    )

    payload = trace.to_user_dict()

    assert payload["fallback_steps"][0]["name"] == "fast_strings"
    assert payload["fallback_steps"][0]["executed"] is False
    assert payload["validation"]["status"] == "unavailable"
