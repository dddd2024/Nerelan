from reverse_agent.user_solve_contract import (
    CONTRACT_SCHEMA_VERSION,
    UserSolveCandidate,
    UserSolveResult,
    UserSolveStatus,
    UserSolveTask,
    ValidationStatus,
    contains_internal_reference,
)
from reverse_agent.user_solve_errors import BlockedReason, FailedReason
from reverse_agent.user_solve_views import (
    build_blocked_view,
    build_failed_view,
    build_result_view,
    build_summary_view,
    build_task_view,
)


def test_build_task_view_includes_schema_version() -> None:
    task = UserSolveTask(task_id="task-001", sample_label="sample-A")
    view = build_task_view(task)
    assert view["schema_version"] == CONTRACT_SCHEMA_VERSION
    assert view["task_id"] == "task-001"


def test_build_result_view_redacts_internal_references() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.CANDIDATE_FOUND,
        validation_status=ValidationStatus.PENDING,
        candidates=[UserSolveCandidate("flag{test}")],
        message="see project_state/decision_packet.md",
        developer_trace_ref="project_state/gates/command_plan.json",
        internal_references=["project_state/artifact_index.json"],
    )
    view = build_result_view(result)
    assert not contains_internal_reference(view)
    assert view["schema_version"] == CONTRACT_SCHEMA_VERSION


def test_build_blocked_view_includes_reason() -> None:
    view = build_blocked_view(BlockedReason.TOOL, message="tool unavailable")
    assert view["status"] == "blocked"
    assert view["reason"] == "tool"
    assert view["retryable"] is True
    assert view["schema_version"] == CONTRACT_SCHEMA_VERSION
    assert not contains_internal_reference(view)


def test_build_failed_view_includes_reason() -> None:
    view = build_failed_view(FailedReason.ANALYSIS, message="analysis failed")
    assert view["status"] == "failed"
    assert view["reason"] == "analysis"
    assert view["retryable"] is False
    assert view["schema_version"] == CONTRACT_SCHEMA_VERSION


def test_build_summary_view_provides_safe_summary() -> None:
    result = UserSolveResult(
        status=UserSolveStatus.CANDIDATE_FOUND,
        validation_status=ValidationStatus.PENDING,
        candidates=[UserSolveCandidate("flag{a}"), UserSolveCandidate("flag{b}")],
        message="found candidates",
    )
    summary = build_summary_view(result)
    assert summary["status"] == "candidate_found"
    assert summary["candidate_count"] == 2
    assert summary["has_answer"] is False
    assert summary["schema_version"] == CONTRACT_SCHEMA_VERSION
    assert not contains_internal_reference(summary)


def test_build_blocked_view_accepts_string_reason() -> None:
    view = build_blocked_view("environment")
    assert view["reason"] == "environment"
    assert view["retryable"] is True


def test_build_failed_view_accepts_string_reason() -> None:
    view = build_failed_view("validation")
    assert view["reason"] == "validation"
