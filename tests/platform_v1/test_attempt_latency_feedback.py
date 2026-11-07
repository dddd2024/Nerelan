"""Host attempt intervals are numeric fenced-settlement facts, never task age."""
import json

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.multi_account import MultiAccountOrchestrator, dispatch
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator
from reverse_agent.platform_v1.usage_ledger import task_feedback_metrics
from tests.platform_v1.test_account_feedback_integrity import observation, completed_attempt
from tests.platform_v1.test_model_router import fixture_host
from tests.platform_v1.test_unattended_coordinator import _budget_window, _parallel_goal, _ready_fixture


def coordinator_fixture(monkeypatch, tmp_path, times):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="attempt-timing", max_tokens=0, reservation=0)
    goals = GoalService(store=store, control_store=control)
    goal = _parallel_goal(goals, window.id, key="attempt-timing", count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    store._conn.execute("UPDATE tasks SET binding_ref='cheap', created_at='2020-01-01T00:00:00Z' WHERE id=?", (task_id,))
    host = fixture_host(monkeypatch, tmp_path)
    host._task_store, host._control_store = store, control
    host._store.upsert_connection(dict(connection_id="free-api", name="api", provider="openai-compatible",
        base_url="https://example.invalid/v1", auth_method="none", enabled=True, account_ref="account"))
    brain = MultiAccountOrchestrator(store_path=tmp_path / "feedback.json")
    monkeypatch.setattr(dispatch, "get_orchestrator", lambda *args, **kwargs: brain)
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
    def execute(task_id):
        claim = store._conn.execute("SELECT epoch FROM platform_coordinator_claims WHERE task_id=?", (task_id,)).fetchone()
        observation(store, store.get_task(task_id), "observed", window=window.id, epoch=claim["epoch"])
        return _ready_fixture(store, task_id)
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
        quota_preparer=host._prepare_task_quota, account_feedback=host._report_account_feedback_to_brain)
    clock = iter(times)
    coordinator._attempt_clock = lambda: next(clock)
    return store, control, coordinator, brain, window, task_id


@pytest.mark.parametrize("times,expected", [([100, 107.25], 7.25), ([100, 100], 0)])
def test_real_coordinator_settlement_trains_measured_attempt_not_queue_age(monkeypatch, tmp_path, times, expected):
    store, control, coordinator, brain, window, task_id = coordinator_fixture(monkeypatch, tmp_path, times)
    try:
        assert coordinator.tick() == 1
        metrics = task_feedback_metrics(store, task_id)
        assert metrics["wall_seconds"] == expected and metrics["wall_time_basis"] == "attempt_elapsed"
        assert brain.scores.get("account").mean_wall_seconds == expected
        assert brain.scores.get("account").latency_samples == 1
        assert control.get_window(window.id).tasks_completed == 1
        settlement = json.loads(store._conn.execute("SELECT settlement_json FROM platform_budget_reservations "
                                                   "WHERE task_id=?", (task_id,)).fetchone()[0])
        assert settlement["attempt_metrics"]["basis"] == "executor_attempt_elapsed"
        assert settlement["attempt_metrics"]["wall_seconds"] == expected
    finally:
        store._conn.close()


@pytest.mark.parametrize("times", [[float("nan"), 10], [10, 9], [-1e308, 1e308], [True, 10]])
def test_bad_host_clock_keeps_latency_unknown_and_execution_continues(monkeypatch, tmp_path, caplog, times):
    store, control, coordinator, brain, window, task_id = coordinator_fixture(monkeypatch, tmp_path, times)
    try:
        assert coordinator.tick() == 1 and control.get_window(window.id).tasks_completed == 1
        metrics = task_feedback_metrics(store, task_id)
        assert metrics["wall_seconds"] is None and metrics["wall_time_basis"] == "UNKNOWN"
        assert brain.scores.get("account").mean_wall_seconds is None
        assert brain.scores.get("account").latency_samples == 0
        assert "attempt_timing_unavailable" in caplog.text
    finally:
        store._conn.close()


@pytest.mark.parametrize("timing", ["not-json", "[]", '{"attempt_metrics":{"wall_seconds":true}}',
    '{"attempt_metrics":{"schema_version":true,"state":"OBSERVED","basis":"executor_attempt_elapsed","wall_seconds":1}}',
    json.dumps({"attempt_metrics": {"schema_version": 1, "state": "OBSERVED", "basis": "executor_attempt_elapsed", "wall_seconds": 10 ** 400}})])
def test_invalid_timing_never_hides_valid_cost_observations(timing):
    store = TaskStore(":memory:")
    try:
        task = store.create_task(title="t", executor_kind="opencode", repository="o/r")
        completed_attempt(store, task)
        observation(store, task, "usage", epoch=2, window="window")
        store._conn.execute("UPDATE platform_budget_reservations SET settlement_json=?", (timing,))
        metrics = task_feedback_metrics(store, task.id)
        assert metrics["cost_units"] > 0 and metrics["wall_seconds"] is None
    finally:
        store._conn.close()


def settlement_fixture():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="settlement-timing", max_tokens=0, reservation=0)
    task = store.create_task(title="t", executor_kind="deterministic_fixture")
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="fixture", lease_ms=60000)
    _ready_fixture(store, task.id)
    return store, control, window, task, epoch


def test_timing_is_rolled_back_with_failed_completion_receipt(monkeypatch):
    store, control, window, task, epoch = settlement_fixture()
    try:
        def fail(**kwargs):
            raise TaskStoreError("receipt_persistence_failed")
        monkeypatch.setattr(control, "append_receipt", fail)
        with pytest.raises(TaskStoreError, match="receipt_persistence_failed"):
            control.complete_task_claim(window_id=window.id, task_id=task.id, owner="fixture", epoch=epoch,
                                        result="success", attempt_elapsed_seconds=7.25)
        row = store._conn.execute("SELECT state,settlement_json FROM platform_budget_reservations WHERE task_id=?", (task.id,)).fetchone()
        assert row["state"] == "ACTIVE" and "attempt_metrics" not in json.loads(row["settlement_json"])
        assert store._conn.execute("SELECT status FROM platform_coordinator_claims WHERE task_id=?", (task.id,)).fetchone()[0] == "ACTIVE"
    finally:
        store._conn.close()


@pytest.mark.parametrize("invalid", [True, -1, float("nan"), float("inf"), 10 ** 400])
def test_invalid_optional_timing_cannot_poison_settlement_or_stop_completion(invalid):
    store, control, window, task, epoch = settlement_fixture()
    try:
        control.complete_task_claim(window_id=window.id, task_id=task.id, owner="fixture", epoch=epoch,
                                    result="success", attempt_elapsed_seconds=invalid)
        assert control.get_window(window.id).tasks_completed == 1
        row = store._conn.execute("SELECT settlement_json FROM platform_budget_reservations WHERE task_id=?", (task.id,)).fetchone()
        settlement = json.loads(row[0])
        assert settlement["attempt_metrics"]["state"] == "UNKNOWN"
        json.dumps(settlement, allow_nan=False)
    finally:
        store._conn.close()


def test_master_off_does_not_measure_or_extend_settlement(monkeypatch, tmp_path):
    store, control, coordinator, brain, window, task_id = coordinator_fixture(monkeypatch, tmp_path, [])
    monkeypatch.delenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED")
    coordinator._attempt_clock = lambda: pytest.fail("disabled telemetry measured a clock")
    try:
        assert coordinator.tick() == 1
        row = store._conn.execute("SELECT settlement_json FROM platform_budget_reservations WHERE task_id=?", (task_id,)).fetchone()
        assert "attempt_metrics" not in json.loads(row[0])
        assert brain.account_scores() == {}
    finally:
        store._conn.close()
