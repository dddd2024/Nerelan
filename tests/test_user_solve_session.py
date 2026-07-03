import pytest

from reverse_agent.fallback_ladder import FallbackLadder
from reverse_agent.user_solve import FastSolveWrapper, adapt_fast_session_bundle
from reverse_agent.user_solve_contract import (
    EvidenceStatus,
    UserSolveResult,
    UserSolveStatus,
    ValidationStatus,
    contains_internal_reference,
)
from reverse_agent.user_solve_session import UserSolveSessionBundle, build_session_bundle
from reverse_agent.user_solve_trace import UserSolveTaskTrace


def test_session_user_serialization_redacts_internal_refs() -> None:
    bundle = adapt_fast_session_bundle(
        {
            "session_id": "session-redacted",
            "task_id": "task-redacted",
            "selected_flag": "flag{candidate}",
            "report_path": "project_state/codex_execution_report.md",
            "developer_trace_ref": "project_state/decision_packet.md",
        }
    )

    user_payload = bundle.to_user_dict()
    developer_payload = bundle.to_developer_dict()

    assert user_payload["session_id"] == "session-redacted"
    assert user_payload["result"]["status"] == "candidate_found"
    assert user_payload["next_action"]["kind"] == "validate_candidate"
    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["developer_trace_refs"])
    assert contains_internal_reference(developer_payload["artifact_references"])


def test_session_developer_serialization_preserves_trace_refs() -> None:
    bundle = FastSolveWrapper().adapt_session_bundle(
        {
            "task_id": "task-dev",
            "missing_evidence": ["targeted_decompile_missing", "project_state/artifact_index.json"],
            "artifact_path": "project_state/gates/user_solve_session_bundle_result.json",
            "developer_trace_ref": "project_state/decision_packet.md",
        }
    )

    developer_payload = bundle.to_developer_dict()

    assert developer_payload["result"]["status"] == "deep_analysis_running"
    assert developer_payload["fallback_decision"]["executed"] is False
    assert contains_internal_reference(developer_payload["trace"]["developer_trace_ref"])
    assert not contains_internal_reference(bundle.to_user_dict())


def test_session_rejects_verified_without_passed_validation() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.VERIFIED,
        validation_status=ValidationStatus.PASSED,
        evidence_status=EvidenceStatus.COMPLETE,
        answer="flag{verified}",
    )
    trace = UserSolveTaskTrace.from_result(
        task_id="task-bad",
        result=result,
        fallback_decision=FallbackLadder.default().select_next(),
    )

    with pytest.raises(ValueError, match="verified session requires passed validation"):
        UserSolveSessionBundle(
            session_id="bad-verified",
            result=result,
            trace=trace,
            fallback_decision=FallbackLadder.default().select_next(),
            validation_status=ValidationStatus.PENDING,
            evidence_status=EvidenceStatus.COMPLETE,
        )


def test_verified_session_rejects_unresolved_missing_evidence() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.VERIFIED,
        validation_status=ValidationStatus.PASSED,
        evidence_status=EvidenceStatus.COMPLETE,
        answer="flag{verified}",
    )
    trace = UserSolveTaskTrace.from_result(
        task_id="task-verified",
        result=result,
        fallback_decision=FallbackLadder.default().select_next(),
    )

    with pytest.raises(ValueError, match="verified session cannot carry unresolved missing evidence"):
        build_session_bundle(
            session_id="bad-missing",
            result=result,
            trace=trace,
            fallback_decision=FallbackLadder.default().select_next(),
            missing_evidence=["runtime_validation_missing"],
        )


def test_session_verified_payload_preserves_verified_status() -> None:
    bundle = adapt_fast_session_bundle(
        {
            "session_id": "session-verified",
            "candidate": "flag{verified}",
            "validation": {"status": "passed"},
        }
    )

    user_payload = bundle.to_user_dict()

    assert user_payload["result"]["status"] == "verified"
    assert user_payload["validation_status"] == "passed"
    assert user_payload["evidence_status"] == "complete"
    assert user_payload["next_action"]["kind"] == "return_answer"


def test_session_missing_evidence_payload_selects_fallback() -> None:
    bundle = adapt_fast_session_bundle(
        {
            "session_id": "session-missing",
            "missing_evidence": ["targeted_decompile_missing"],
        }
    )

    user_payload = bundle.to_user_dict()

    assert user_payload["result"]["status"] == "deep_analysis_running"
    assert user_payload["fallback_decision"]["selected_step"]["name"] == "fast_strings"
    assert user_payload["next_action"]["kind"] == "fallback"
    assert not contains_internal_reference(user_payload)
