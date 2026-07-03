from reverse_agent.user_solve import FastSolveWrapper, adapt_fast_result
from reverse_agent.user_solve_contract import contains_internal_reference


def test_fast_wrapper_candidate_before_validation() -> None:
    result = FastSolveWrapper().adapt(
        {
            "selected_flag": "flag{candidate}",
            "confidence": 87,
            "report_path": "project_state/codex_execution_report.md",
        }
    )

    user_payload = result.to_user_dict()

    assert user_payload["status"] == "candidate_found"
    assert user_payload["validation_status"] == "pending"
    assert user_payload["evidence_status"] == "building"
    assert user_payload["answer"] == "flag{candidate}"
    assert user_payload["confidence"] == 0.87
    assert not contains_internal_reference(user_payload)


def test_fast_wrapper_passed_validation_becomes_verified() -> None:
    result = adapt_fast_result(
        {
            "candidate": "flag{verified}",
            "validation": {"status": "passed"},
            "artifact_path": "project_state/gates/final_gate_result.json",
        }
    )

    developer_payload = result.to_developer_dict()

    assert result.status.value == "verified"
    assert result.validation_status.value == "passed"
    assert developer_payload["answer"] == "flag{verified}"
    assert contains_internal_reference(developer_payload["internal_references"])


def test_fast_wrapper_no_candidate_failed_branch() -> None:
    result = FastSolveWrapper().adapt({"selected_flag": "NOT_FOUND"})

    assert result.status.value == "failed"
    assert result.validation_status.value == "unavailable"
    assert "No candidate" in result.message


def test_fast_wrapper_blocked_branch() -> None:
    result = FastSolveWrapper().adapt(
        {
            "status": "blocked",
            "blockers": ["tool_unavailable: debugger forbidden"],
            "developer_trace_ref": "project_state/decision_packet.md",
        }
    )

    user_payload = result.to_user_dict()
    developer_payload = result.to_developer_dict()

    assert user_payload["status"] == "blocked"
    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["developer_trace_ref"])


def test_fast_wrapper_missing_evidence_uses_deep_analysis_status() -> None:
    result = FastSolveWrapper().adapt(
        {
            "missing_evidence": ["targeted_static_decompile", "runtime_validation"],
            "artifact_path": "project_state/artifact_index.json",
        }
    )

    user_payload = result.to_user_dict()

    assert user_payload["status"] == "deep_analysis_running"
    assert user_payload["validation_status"] == "unavailable"
    assert not contains_internal_reference(user_payload)


def test_fast_wrapper_adapt_with_trace_keeps_result_behavior_and_metadata() -> None:
    payload = {
        "task_id": "task-trace",
        "missing_evidence": ["targeted_decompile_missing", "project_state/artifact_index.json"],
        "artifact_path": "project_state/gates/user_solve_trace_fallback_result.json",
    }

    bundle = FastSolveWrapper().adapt_with_trace(payload)
    result = bundle["result"]
    trace = bundle["trace"]
    fallback_decision = bundle["fallback_decision"]

    assert result.status.value == "deep_analysis_running"
    assert fallback_decision.executed is False
    assert trace.to_user_dict()["task_id"] == "task-trace"
    assert not contains_internal_reference(trace.to_user_dict())


def test_fast_wrapper_adapt_session_bundle_is_in_memory_and_redacted() -> None:
    bundle = FastSolveWrapper().adapt_session_bundle(
        {
            "session_id": "session-wrapper",
            "task_id": "task-wrapper",
            "selected_flag": "flag{candidate}",
            "artifact_path": "project_state/gates/user_solve_session_bundle_result.json",
        }
    )

    user_payload = bundle.to_user_dict()
    developer_payload = bundle.to_developer_dict()

    assert user_payload["session_id"] == "session-wrapper"
    assert user_payload["result"]["status"] == "candidate_found"
    assert user_payload["next_action"]["kind"] == "validate_candidate"
    assert not contains_internal_reference(user_payload)
    assert contains_internal_reference(developer_payload["artifact_references"])
