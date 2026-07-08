import json

import pytest

from reverse_agent.user_solve_contract import (
    CONTRACT_SCHEMA_VERSION,
    CandidateResult,
    EvidenceStatus,
    UserSolveCandidate,
    UserSolveMode,
    UserSolveResult,
    UserSolveStatus,
    UserSolveTask,
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


def test_failed_requires_reason_or_message() -> None:
    with pytest.raises(ValueError, match="failed requires"):
        UserSolveResult(status=UserSolveStatus.FAILED)


def test_static_verified_requires_validation_status() -> None:
    with pytest.raises(ValueError, match="static_verified requires validation_status"):
        UserSolveResult(
            status=UserSolveStatus.STATIC_VERIFIED,
            validation_status=ValidationStatus.PENDING,
            answer="flag{static}",
        )
    result = UserSolveResult(
        status=UserSolveStatus.STATIC_VERIFIED,
        validation_status=ValidationStatus.STATIC_VERIFIED,
        answer="flag{static}",
    )
    assert result.status == UserSolveStatus.STATIC_VERIFIED


def test_runtime_validated_requires_evidence() -> None:
    with pytest.raises(ValueError, match="runtime_validated requires runtime validation evidence"):
        UserSolveResult(
            status=UserSolveStatus.RUNTIME_VALIDATED,
            validation_status=ValidationStatus.RUNTIME_VALIDATED,
            answer="flag{runtime}",
        )
    result = UserSolveResult(
        status=UserSolveStatus.RUNTIME_VALIDATED,
        validation_status=ValidationStatus.RUNTIME_VALIDATED,
        answer="flag{runtime}",
        internal_references=["evidence/runtime_trace_001.json"],
    )
    assert result.status == UserSolveStatus.RUNTIME_VALIDATED


def test_static_verified_distinct_from_runtime_validated() -> None:
    with pytest.raises(ValueError, match="static_verified must not have validation_status=runtime_validated"):
        UserSolveResult(
            status=UserSolveStatus.STATIC_VERIFIED,
            validation_status=ValidationStatus.RUNTIME_VALIDATED,
            answer="flag{test}",
        )


def test_candidate_result_rejects_runtime_validated() -> None:
    with pytest.raises(ValueError, match="CandidateResult must not imply runtime validation"):
        CandidateResult(
            value="flag{test}",
            validation_status=ValidationStatus.RUNTIME_VALIDATED,
        )


def test_candidate_result_default_validation_is_candidate_only() -> None:
    candidate = CandidateResult(value="flag{test}")
    assert candidate.validation_status == ValidationStatus.CANDIDATE_ONLY


def test_user_solve_task_creation() -> None:
    task = UserSolveTask(task_id="task-001", sample_label="sample-A")
    assert task.task_id == "task-001"
    assert task.mode == UserSolveMode.AUTO
    assert task.requested_validation == ValidationStatus.PENDING


def test_user_solve_task_rejects_empty_id() -> None:
    with pytest.raises(ValueError, match="task_id must be non-empty"):
        UserSolveTask(task_id="")


def test_schema_version_in_user_dict() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.CANDIDATE_FOUND,
        validation_status=ValidationStatus.PENDING,
        candidates=[UserSolveCandidate("flag{test}")],
    )
    payload = result.to_user_dict()
    assert payload["schema_version"] == CONTRACT_SCHEMA_VERSION


def test_to_json_from_json_roundtrip() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.STATIC_VERIFIED,
        validation_status=ValidationStatus.STATIC_VERIFIED,
        answer="flag{test}",
        confidence=0.85,
        developer_trace_ref="evidence/static_trace.json",
        internal_references=["evidence/trace_001.json"],
    )
    data = result.to_json()
    assert data["schema_version"] == CONTRACT_SCHEMA_VERSION
    restored = UserSolveResult.from_json(data)
    assert restored.status == UserSolveStatus.STATIC_VERIFIED
    assert restored.answer == "flag{test}"
    assert restored.confidence == 0.85


def test_from_json_rejects_missing_schema_version() -> None:
    with pytest.raises(ValueError, match="schema_version is required"):
        UserSolveResult.from_json({"payload": {"status": "candidate_found"}})


def test_from_json_rejects_future_schema_version() -> None:
    with pytest.raises(ValueError, match="unsupported schema_version"):
        UserSolveResult.from_json({"schema_version": 99, "payload": {"status": "candidate_found"}})


def test_from_json_ignores_unknown_optional_fields() -> None:
    data = {
        "schema_version": 1,
        "payload": {
            "status": "candidate_found",
            "validation_status": "pending",
            "candidates": [{"value": "flag{test}"}],
            "unknown_future_field": "ignored",
        },
    }
    result = UserSolveResult.from_json(data)
    assert result.status == UserSolveStatus.CANDIDATE_FOUND


def test_json_serialization_is_deterministic() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.CANDIDATE_FOUND,
        validation_status=ValidationStatus.PENDING,
        candidates=[UserSolveCandidate("flag{test}", confidence=0.5)],
    )
    json1 = json.dumps(result.to_json(), sort_keys=True)
    json2 = json.dumps(result.to_json(), sort_keys=True)
    assert json1 == json2
