from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from reverse_agent.platform_v1.window_report import build_report, render_markdown

from tests.platform_v1.test_unattended_coordinator import (
    _budget_window,
    _parallel_goal,
    _ready_fixture,
)


def _completed_task_window(tmp_path, key="report-completed"):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    window = _budget_window(autonomy, policy_id=key, max_tokens=0, reservation=0)
    goal = _parallel_goal(goals, window.id, key=key, count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    def execute(task_id):
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert store.get_task(task_id).status == "READY_FOR_REVIEW_FIXTURE"
    return store, control, window, goal, task_id


def _failed_task_window(tmp_path, key="report-failed"):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    window = _budget_window(autonomy, policy_id=key, max_tokens=0, reservation=0)
    goal = _parallel_goal(goals, window.id, key=key, count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    def execute(task_id):
        store.transition_to(task_id, "PREPARING_WORKSPACE")
        store.transition_to(task_id, "RUNNING_FIXTURE")
        store.transition_to(task_id, "FAILED")
        store._conn.execute(
            "UPDATE tasks SET failure_classification=? WHERE id=?",
            ("execution_failed", task_id),
        )
        return SimpleNamespace(success=False)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert store.get_task(task_id).status == "FAILED"
    return store, control, window, goal, task_id


def _blocked_usage_window(tmp_path, key="report-blocked"):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    window = _budget_window(autonomy, policy_id=key, max_tokens=0, reservation=0)
    goal = _parallel_goal(goals, window.id, key=key, count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    def execute(task_id):
        store.transition_to(task_id, "PREPARING_WORKSPACE")
        store.transition_to(task_id, "RUNNING_FIXTURE")
        store.transition_to(task_id, "FAILED")
        return SimpleNamespace(success=False)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    store._conn.execute(
        "UPDATE platform_autonomous_windows SET status='BLOCKED', "
        "stop_reason='usage_unknown', unknown_observation_count=3 WHERE id=?",
        (window.id,),
    )
    return store, control, window, goal, task_id


def test_report_completed_task_includes_goal_task_and_binding(tmp_path):
    store, control, window, goal, task_id = _completed_task_window(tmp_path)
    report = build_report(control, store, window.id)
    assert report["window_id"] == window.id
    assert report["window"]["status"] in {"ACTIVE", "COMPLETED"}
    assert report["window"]["stop_reason"] == ""
    assert report["window"]["unknown_observation_count"] == 0

    assert len(report["goals"]) == 1
    goal_block = report["goals"][0]
    assert goal_block["id"] == goal.id
    assert goal_block["status"] == "COMPLETED"
    assert len(goal_block["tasks"]) == 1
    task_block = goal_block["tasks"][0]
    assert task_block["id"] == task_id
    assert task_block["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert task_block["failure_classification"] == ""
    assert task_block["executor_kind"] == "deterministic_fixture"
    assert task_block["binding_ref"] == ""

    bindings = report["bindings"]
    assert "" in bindings
    assert bindings[""]["task_count"] == 1
    assert bindings[""]["success_count"] == 1

    markdown = render_markdown(report)
    assert f"# Window report: {window.id}" in markdown
    assert "## Goals" in markdown
    assert goal.title in markdown
    assert "READY_FOR_REVIEW_FIXTURE" in markdown


def test_report_failed_task_counts_failure_classification(tmp_path):
    store, control, window, goal, task_id = _failed_task_window(tmp_path)
    report = build_report(control, store, window.id)

    task_block = report["goals"][0]["tasks"][0]
    assert task_block["status"] == "FAILED"
    assert task_block["failure_classification"] == "execution_failed"

    assert report["failures_by_class"] == {"execution_failed": 1}
    assert report["bindings"][""]["success_count"] == 0

    markdown = render_markdown(report)
    assert "## Failures by class" in markdown
    assert "execution_failed" in markdown


def test_report_blocked_window_shows_stop_reason_and_unknown_observations(tmp_path):
    store, control, window, goal, task_id = _blocked_usage_window(tmp_path)
    report = build_report(control, store, window.id)

    assert report["window"]["status"] == "BLOCKED"
    assert report["window"]["stop_reason"] == "usage_unknown"
    assert report["window"]["unknown_observation_count"] == 3

    markdown = render_markdown(report)
    assert "status: BLOCKED" in markdown
    assert "stop_reason: usage_unknown" in markdown
    assert "unknown_observation_count: 3" in markdown


def test_report_includes_draft_pr_url_when_present(tmp_path):
    store, control, window, goal, task_id = _completed_task_window(tmp_path)
    control.upsert_publication(
        task_id=task_id,
        repository="dddd2024/reverse-agent",
        base_branch="main",
        branch="agent/report",
        status="PENDING",
        request_digest="digest-report",
        pr_number=7,
        pr_url="https://github.com/dddd2024/reverse-agent/pull/7",
    )
    report = build_report(control, store, window.id)
    task_block = report["goals"][0]["tasks"][0]
    assert task_block["draft_pr_url"] == "https://github.com/dddd2024/reverse-agent/pull/7"
    assert report["draft_prs"] == [
        {"task_id": task_id, "pr_url": "https://github.com/dddd2024/reverse-agent/pull/7"}
    ]
    markdown = render_markdown(report)
    assert "https://github.com/dddd2024/reverse-agent/pull/7" in markdown


def test_report_aggregates_tokens_per_binding(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    window = _budget_window(autonomy, policy_id="report-tokens", max_tokens=0, reservation=0)
    goal = _parallel_goal(goals, window.id, key="report-tokens", count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]

    def execute(task_id):
        store.transition_to(task_id, "PREPARING_WORKSPACE")
        store.transition_to(task_id, "RUNNING_FIXTURE")
        task = store.get_task(task_id)
        store.append_usage_observation(
            task_id,
            observation_id="report-tokens-1",
            execution_id=task.execution_id,
            role="executor",
            model_id="fixture",
            provider_id="",
            source_kind="fixture",
            source_id="run",
            status="OBSERVED",
            input_units=100,
            output_units=50,
            reasoning_units=10,
            cache_read_units=5,
            cache_write_units=3,
            cost_micro_units=200,
        )
        store.transition_to(task_id, "VALIDATING")
        store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
        return SimpleNamespace(success=True)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    report = build_report(control, store, window.id)
    assert report["bindings"][""]["total_tokens"] == 168
    markdown = render_markdown(report)
    assert "168" in markdown


def test_build_report_unknown_window_raises(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    with pytest.raises(Exception):
        build_report(control, store, "missing-window")


def test_report_keeps_finished_task_after_goal_rebound(tmp_path):
    """A goal rebound to a successor window appears in both reports, each
    listing only the tasks that ran in that window (#1436)."""
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)

    window_a = _budget_window(autonomy, policy_id="report-rebound-a", max_tokens=0, reservation=0)
    goal = _parallel_goal(goals, window_a.id, key="report-rebound", count=2)
    links = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}
    finished_id, queued_id = links["T001"], links["T002"]

    epoch, _ = control.claim_task(window_id=window_a.id, task_id=finished_id, owner="host", lease_ms=60_000)
    store.transition_to(finished_id, "PREPARING_WORKSPACE")
    store.transition_to(finished_id, "RUNNING_FIXTURE")
    store.transition_to(finished_id, "VALIDATING")
    store.transition_to(finished_id, "READY_FOR_REVIEW_FIXTURE")
    control.complete_task_claim(
        window_id=window_a.id, task_id=finished_id, owner="host", epoch=epoch, result="success",
    )

    report_a_before = build_report(control, store, window_a.id)
    goal_block = report_a_before["goals"][0]
    assert goal_block["id"] == goal.id
    assert {t["id"] for t in goal_block["tasks"]} == {finished_id, queued_id}

    store._conn.execute(
        "UPDATE platform_autonomous_windows SET status='EXPIRED', "
        "expires_at='2000-01-01T00:00:00+00:00' WHERE id=?",
        (window_a.id,),
    )
    window_b = _budget_window(autonomy, policy_id="report-rebound-b", max_tokens=0, reservation=0)
    outcome = control.rebind_goal_to_window(goal.id, window_id=window_b.id, reason="standing_window_adoption")
    assert outcome["status"] == "REBOUND"
    assert control.get_goal(goal.id).window_id == window_b.id

    report_a = build_report(control, store, window_a.id)
    report_b = build_report(control, store, window_b.id)

    assert len(report_a["goals"]) == 1
    assert report_a["goals"][0]["id"] == goal.id
    assert [t["id"] for t in report_a["goals"][0]["tasks"]] == [finished_id]
    assert report_a["goals"][0]["tasks"][0]["status"] == "READY_FOR_REVIEW_FIXTURE"
    assert report_a["bindings"][""]["task_count"] == 1
    assert report_a["bindings"][""]["success_count"] == 1

    assert len(report_b["goals"]) == 1
    assert report_b["goals"][0]["id"] == goal.id
    assert [t["id"] for t in report_b["goals"][0]["tasks"]] == [queued_id]
    assert report_b["goals"][0]["tasks"][0]["status"] == "QUEUED"
    assert report_b["bindings"][""]["task_count"] == 1
    assert report_b["bindings"][""]["success_count"] == 0

    markdown_a = render_markdown(report_a)
    markdown_b = render_markdown(report_b)
    assert goal.title in markdown_a and goal.title in markdown_b
    assert store.get_task(finished_id).title in markdown_a
    assert store.get_task(finished_id).title not in markdown_b
    assert store.get_task(queued_id).title in markdown_b
    assert store.get_task(queued_id).title not in markdown_a
