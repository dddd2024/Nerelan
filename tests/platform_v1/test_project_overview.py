"""Project overview facade and the provider-free coordination fixture (#1286 §5.2)."""

from datetime import datetime, timedelta, timezone
import threading
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.project_overview import (
    OWNER_ACTIONS, TASK_STATES, ProjectOverview, task_state, window_state,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _ready_fixture(store, task_id):
    store.transition_to(task_id, "PREPARING_WORKSPACE")
    store.transition_to(task_id, "RUNNING_FIXTURE")
    store.transition_to(task_id, "VALIDATING")
    store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
    return SimpleNamespace(success=True)


def _services(database=":memory:"):
    store = TaskStore(database)
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    return store, control, autonomy, goals


def _window(autonomy, *, policy_id, wip=2, hours=1):
    now = datetime.now(timezone.utc)
    return autonomy.activate({
        "policy_id": policy_id, "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=hours)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": wip, "max_tasks": 10, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })


def _goal(goals, *, key, tasks, window_id=None, stop_at="launched"):
    goal = goals.create({
        "objective": f"Coordination fixture {key}", "idempotency_key": key,
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    if stop_at == "draft":
        return goal
    goals.plan(goal.id, expected_revision=1, tasks=tasks)
    if stop_at == "planned":
        return goal
    goals.approve(goal.id, expected_revision=1)
    if stop_at == "approved":
        return goal
    goals.launch(goal.id, expected_revision=1, window_id=window_id)
    return goal


TWO_INDEPENDENT_ONE_DEPENDENT = [
    {"id": "A", "title": "independent a", "instruction": "a"},
    {"id": "B", "title": "independent b", "instruction": "b"},
    {"id": "C", "title": "dependent c", "instruction": "c", "dependencies": ["A"]},
]


def _snapshot(overview):
    """Comparable view without wall-clock fields."""
    return [
        (goal["goal_id"], goal["status"],
         [(task["plan_task_id"], task["status"], task["state"]) for task in goal["tasks"]],
         [(action["action"], action["task_id"]) for action in goal["owner_actions"]])
        for goal in overview["goals"]
    ]


def test_coordination_fixture_concurrency_handoff_order_restart_and_zero_model_calls(tmp_path):
    database = str(tmp_path / "project.sqlite3")
    store, control, autonomy, goals = _services(database)
    window = _window(autonomy, policy_id="coordination-fixture", wip=2)
    goal = _goal(goals, key="coordination-fixture", tasks=TWO_INDEPENDENT_ONE_DEPENDENT, window_id=window.id)
    ids = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}

    before = ProjectOverview(store=store, control_store=control).overview()
    states = {task["plan_task_id"]: task["state"] for task in before["goals"][0]["tasks"]}
    assert states == {"A": "queued", "B": "queued", "C": "waiting_dependencies"}
    assert before["owner_actions"] == [] and before["authority"] == "NONE"

    barrier = threading.Barrier(2)
    threads: set[int] = set()
    calls: list[str] = []
    lock = threading.Lock()

    def execute(task_id):
        with lock:
            threads.add(threading.get_ident())
            calls.append(task_id)
        if task_id in {ids["A"], ids["B"]}:
            barrier.wait(timeout=5)
        return _ready_fixture(store, task_id)

    router = ExecutorRouter()

    def forbidden(**_kwargs):
        pytest.fail("model executor reached by provider-free fixture")

    router.create_executor = forbidden
    router.dispatch_execute = forbidden
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=router, workspace_root=tmp_path / "workspaces", task_executor=execute)

    # The two independent tasks run concurrently; the dependent one waits for A.
    assert coordinator.tick() == 2
    assert set(calls) == {ids["A"], ids["B"]} and len(threads) == 2
    middle = ProjectOverview(store=store, control_store=control).overview()
    assert {t["plan_task_id"]: t["state"] for t in middle["goals"][0]["tasks"]}["C"] == "queued"
    store._conn.close()

    # Restart from the same database: state is rebuilt from durable rows only.
    store, control, autonomy, goals = _services(database)
    reopened = ProjectOverview(store=store, control_store=control).overview()
    assert _snapshot(reopened) == _snapshot(middle)
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=router, workspace_root=tmp_path / "workspaces", task_executor=execute)
    assert coordinator.tick() == 1
    assert coordinator.tick() == 0
    assert calls.count(ids["A"]) == calls.count(ids["B"]) == calls.count(ids["C"]) == 1

    final = ProjectOverview(store=store, control_store=control).overview()
    summary = final["goals"][0]
    assert summary["status"] == "COMPLETED"
    assert summary["task_counts"] == {"ready_for_review": 3}
    assert [a["action"] for a in final["owner_actions"]] == ["review_result"] * 3
    assert all(task["usage"] == store.usage_summary(task["task_id"]) for task in summary["tasks"])
    assert all(store.list_usage_observations(task_id) == () for task_id in ids.values())
    budget = summary["window"]["budget"]
    assert (budget["observed_token_units"], budget["observed_cost_micro_units"]) == (0, 0)
    store._conn.close()


def test_expired_window_parks_unfinished_goal_on_owner_without_writing(tmp_path):
    store, control, autonomy, goals = _services()
    window = _window(autonomy, policy_id="expiring", wip=1)
    goal = _goal(goals, key="expiring", tasks=TWO_INDEPENDENT_ONE_DEPENDENT[:2], window_id=window.id)
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    view = ProjectOverview(store=store, control_store=control, clock=lambda: later).goal_summary(control.get_goal(goal.id))
    assert view["window"]["status"] == "ACTIVE"
    assert view["window"]["effective_status"] == "EXPIRED"
    assert {task["state"] for task in view["tasks"]} == {"waiting_window"}
    assert [a["action"] for a in view["owner_actions"]] == ["renew_window"]
    assert view["owner_actions"][0]["reason"] == "expired"
    # Read-only: the stored window was not expired by the overview.
    assert control.get_window(window.id).status == "ACTIVE"


def test_unlaunched_goals_need_owner_steps():
    store, control, autonomy, goals = _services()
    tasks = [{"id": "A", "title": "a", "instruction": "a"}]
    draft = _goal(goals, key="draft", tasks=tasks, stop_at="draft")
    planned = _goal(goals, key="planned", tasks=tasks, stop_at="planned")
    approved = _goal(goals, key="approved", tasks=tasks, stop_at="approved")
    overview = ProjectOverview(store=store, control_store=control).overview()
    actions = {a["goal_id"]: a["action"] for a in overview["owner_actions"]}
    assert actions == {draft.id: "plan_goal", planned.id: "approve_plan", approved.id: "launch_goal"}
    assert set(actions.values()) <= OWNER_ACTIONS


def test_stale_blocked_and_failed_tasks_are_listed_for_owner():
    store, control, autonomy, goals = _services()
    window = _window(autonomy, policy_id="stale", wip=3)
    goal = _goal(goals, key="stale", window_id=window.id, tasks=[
        {"id": "R", "title": "running", "instruction": "r"},
        {"id": "I", "title": "interrupted", "instruction": "i"},
        {"id": "F", "title": "failed", "instruction": "f"},
    ])
    ids = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}
    store.set_state(ids["R"], "RUNNING")
    store.set_state(ids["I"], "INTERRUPTED")
    store.set_state(ids["F"], "FAILED")
    later = datetime.now(timezone.utc) + timedelta(minutes=30)
    view = ProjectOverview(store=store, control_store=control, clock=lambda: later).goal_summary(control.get_goal(goal.id))
    states = {task["plan_task_id"]: task["state"] for task in view["tasks"]}
    assert states == {"R": "stale", "I": "stale", "F": "failed"}
    assert set(states.values()) <= TASK_STATES
    actions = {(a["action"], a["task_id"]) for a in view["owner_actions"]}
    assert actions == {
        ("inspect_stale_task", ids["R"]),
        ("inspect_stale_task", ids["I"]),
        ("resolve_blocked_task", ids["F"]),
    }


@pytest.mark.parametrize("status, liveness, met, active, expected", [
    ("READY_FOR_REVIEW", "OWNER_ACTION_REQUIRED", True, True, "ready_for_review"),
    ("BLOCKED", "BLOCKED", True, True, "blocked"),
    ("CANCELLED", "TERMINAL", True, True, "failed"),
    ("RUNNING", "STALE", True, True, "stale"),
    ("RUNNING", "ACTIVE", True, True, "running"),
    ("RUNNING", "UNKNOWN", True, True, "unknown"),
    ("VALIDATING", "VALIDATING", True, True, "validating"),
    ("QUEUED", "WAITING", False, True, "waiting_dependencies"),
    ("QUEUED", "WAITING", True, False, "waiting_window"),
    ("QUEUED", "WAITING", True, True, "queued"),
])
def test_task_state_vocabulary(status, liveness, met, active, expected):
    assert task_state({"status": status, "liveness": liveness},
                      dependencies_met=met, window_active=active) == expected


def test_window_state_reads_expiry_and_future_start_without_store():
    now = datetime(2026, 10, 20, tzinfo=timezone.utc)
    base = dict(status="ACTIVE", starts_at="2026-10-19T00:00:00Z", expires_at="2026-10-21T00:00:00Z")
    assert window_state(SimpleNamespace(**base), now) == "ACTIVE"
    assert window_state(SimpleNamespace(**{**base, "expires_at": "2026-10-19T12:00:00Z"}), now) == "EXPIRED"
    assert window_state(SimpleNamespace(**{**base, "starts_at": "2026-10-20T01:00:00Z"}), now) == "PENDING"
    assert window_state(SimpleNamespace(**{**base, "status": "STOPPED"}), now) == "STOPPED"
