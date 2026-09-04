"""Focused regression coverage for truthful Task governance projection (#381)."""

import pytest

from reverse_agent.platform_v1.task_service import _map_task_to_frontend


def _task(**overrides):
    task = {
        "id": "task-governance",
        "title": "governance truth",
        "status": "QUEUED",
        "validation_exit_code": None,
        "failure_classification": "",
    }
    task.update(overrides)
    return task


def _assert_fail_closed(projected):
    assert projected["issueNumber"] is None
    assert projected["riskTier"] == "UNKNOWN"
    assert projected["authorityStatus"] == "MISSING"
    assert projected["workflowStatus"] == "UNKNOWN"


def test_absent_governance_fails_closed() -> None:
    _assert_fail_closed(_map_task_to_frontend(_task()))


def test_explicit_valid_snake_case_governance_is_preserved() -> None:
    projected = _map_task_to_frontend(
        _task(
            issue_number=381,
            risk_tier="R2",
            authority_status="APPROVED",
            workflow_status="RUNNING",
        )
    )

    assert projected["issueNumber"] == 381
    assert projected["riskTier"] == "R2"
    assert projected["authorityStatus"] == "APPROVED"
    assert projected["workflowStatus"] == "RUNNING"


def test_explicit_valid_frontend_shaped_governance_is_preserved() -> None:
    projected = _map_task_to_frontend(
        _task(
            issueNumber=607,
            riskTier="R3",
            authorityStatus="REVOKED",
            workflowStatus="NEUTRALIZED",
        )
    )

    assert projected["issueNumber"] == 607
    assert projected["riskTier"] == "R3"
    assert projected["authorityStatus"] == "REVOKED"
    assert projected["workflowStatus"] == "NEUTRALIZED"


@pytest.mark.parametrize(
    "value",
    [None, "", 0, -1, False, True, 1.0, "381", [], {}],
)
def test_missing_or_malformed_issue_number_fails_closed(value) -> None:
    projected = _map_task_to_frontend(_task(issue_number=value))
    assert projected["issueNumber"] is None


def test_invalid_governance_enums_fail_closed() -> None:
    projected = _map_task_to_frontend(
        _task(
            issue_number="381",
            risk_tier="R9",
            authority_status="YES",
            workflow_status="DONE",
        )
    )
    _assert_fail_closed(projected)


def test_test_status_remains_evidence_derived() -> None:
    passed = _map_task_to_frontend(
        _task(status="READY_FOR_REVIEW", validation_exit_code=0)
    )
    failed = _map_task_to_frontend(
        _task(status="READY_FOR_REVIEW", validation_exit_code=7)
    )
    running = _map_task_to_frontend(
        _task(status="VALIDATING", validation_exit_code=None)
    )
    pending = _map_task_to_frontend(_task(status="QUEUED"))

    assert passed["testStatus"] == "PASS"
    assert failed["testStatus"] == "FAIL"
    assert running["testStatus"] == "RUNNING"
    assert pending["testStatus"] == "PENDING"
