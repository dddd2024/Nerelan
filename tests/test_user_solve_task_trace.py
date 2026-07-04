import pytest

from reverse_agent.user_solve_contract import contains_internal_reference
from reverse_agent.user_solve_task_trace import WorkbenchTaskTrace, build_workbench_task_trace


def test_task_trace_serializes_without_persistence_or_internal_refs() -> None:
    trace = build_workbench_task_trace(
        fixture_name="candidate",
        response={
            "request": {"request_id": "demo-candidate"},
            "status": "candidate_found",
            "validation_status": "pending",
            "candidates": [{"value": "flag{demo_candidate}"}],
            "fallback_summary": {"missing_evidence": []},
        },
        route_plan={"planned_actions": [{"kind": "validate_candidate"}]},
    ).to_user_dict()

    assert trace["persisted"] is False
    assert trace["candidate_state"] == "present"
    assert not contains_internal_reference(trace)


def test_task_trace_rejects_persistence() -> None:
    with pytest.raises(ValueError):
        WorkbenchTaskTrace(
            trace_id="trace",
            request_id="request",
            fixture_name="candidate",
            source="fixture",
            status="candidate_found",
            validation_state="pending",
            candidate_state="present",
            persisted=True,
        )
