"""Provider-free rebind of stranded Goals to a new explicit window (#1277)."""
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _payload(policy_id, **overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "policy_id": policy_id, "policy_revision": 1, "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "resume_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE",
    }
    payload.update(overrides)
    return payload


def _services(db=":memory:"):
    store = TaskStore(db)
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    return SimpleNamespace(store=store, control=control, autonomy=autonomy,
                           goals=GoalService(store=store, control_store=control))


def _stranded(db=":memory:", *, receipt=True):
    """T005 was running when the host died (INTERRUPTED, stale claim); T006 never started."""
    s = _services(db)
    goal = s.goals.create({"objective": "Survive a window renewal", "idempotency_key": "stranded",
                           "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    s.goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T005", "title": "running", "instruction": "was running"},
        {"id": "T006", "title": "queued", "instruction": "never started"}])
    s.goals.approve(goal.id, expected_revision=1)
    old = s.autonomy.activate(_payload("old-window"))
    s.goals.launch(goal.id, expected_revision=1, window_id=old.id)
    tasks = {link["plan_task_id"]: link["task_id"] for link in s.control.list_goal_tasks(goal.id)}
    s.control.claim_task(window_id=old.id, task_id=tasks["T005"], owner="old-host", lease_ms=60_000)
    s.store.set_state(tasks["T005"], "INTERRUPTED")
    db_conn = s.store._conn
    db_conn.execute("INSERT INTO durable_runs (run_id, task_id, execution_id, worktree_path, lease_epoch, "
                    "lease_expiry_ms, created_at, updated_at) VALUES ('run-1', ?, 'exec-1', 'fixture', 1, 1, 'x', 'x')",
                    (tasks["T005"],))
    if receipt:
        # A recorded external operation: recovery has a durable checkpoint, not UNKNOWN effects.
        db_conn.execute("INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, "
                        "idempotency_key, request_digest, state, created_at, updated_at) "
                        "VALUES ('op-1', 'run-1', ?, 'k', 'i', 'd', 'SUCCEEDED', 'x', 'x')", (tasks["T005"],))
    db_conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms = 1 WHERE task_id = ?", (tasks["T005"],))
    db_conn.execute("UPDATE platform_autonomous_windows SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?",
                    (old.id,))
    assert s.control.active_window() is None
    assert s.control.get_window(old.id).status == "EXPIRED"
    return s, goal, old, tasks


def _claim(s, task_id):
    return s.store._conn.execute("SELECT * FROM platform_coordinator_claims WHERE task_id = ?",
                                 (task_id,)).fetchone()


def _receipts(s, operation_type):
    return s.store._conn.execute("SELECT * FROM platform_operation_receipts WHERE operation_type = ?",
                                 (operation_type,)).fetchall()


def _coordinator(s, tmp_path, authorized):
    def authorize(**kwargs):
        allowed = s.autonomy.authorize(**kwargs)
        authorized.append((kwargs["subject_id"], kwargs["operation"], allowed))
        return allowed
    return UnattendedCoordinator(store=s.store, control_store=s.control,
                                 autonomy=SimpleNamespace(authorize=authorize),
                                 router=SimpleNamespace(), workspace_root=tmp_path)


def test_rebind_resumes_interrupted_once_and_runs_queued(tmp_path, monkeypatch):
    s, goal, old, tasks = _stranded()
    new = s.autonomy.activate(_payload("new-window"))
    stranded = s.control.stranded_goals()
    assert [(g["goal_id"], g["window_id"], g["window_status"], g["queued"], g["interrupted"])
            for g in stranded] == [(goal.id, old.id, "EXPIRED", 1, 1)]

    outcome = s.goals.rebind(goal.id, window_id=new.id)

    assert outcome["status"] == "REBOUND" and outcome["from_window_id"] == old.id
    assert {(t["task_id"], t["operation"]) for t in outcome["tasks"]} == {
        (tasks["T005"], "resume_task"), (tasks["T006"], "execute_task")}
    assert outcome["retired_claims"] == [{"task_id": tasks["T005"], "window_id": old.id, "epoch": 1}]
    assert s.control.get_goal(goal.id).window_id == new.id
    assert s.control.stranded_goals() == ()
    claim = _claim(s, tasks["T005"])
    assert (claim["status"], claim["window_id"]) == ("RETIRED", old.id)
    reservation = s.store._conn.execute(
        "SELECT state FROM platform_budget_reservations WHERE task_id = ? AND claim_epoch = 1",
        (tasks["T005"],)).fetchone()
    assert reservation["state"] == "UNKNOWN"  # no refund for the abandoned attempt
    assert len(_receipts(s, "claim_retirement")) == 1
    assert len(_receipts(s, "goal_window_rebind")) == 1
    assert s.control.get_window(old.id).status == "EXPIRED"  # never extended

    authorized, dispatched = [], []
    coordinator = _coordinator(s, tmp_path, authorized)
    monkeypatch.setattr(coordinator, "_execute_claimed_batch",
                        lambda **kw: dispatched.append(dict(kw["claimed"])) or len(kw["claimed"]))
    assert coordinator.tick() == 2
    assert dispatched == [{tasks["T005"]: 2, tasks["T006"]: 1}]
    assert sorted(authorized) == sorted([(tasks["T005"], "resume_task", True),
                                         (tasks["T006"], "execute_task", True)])
    window = s.control.get_window(new.id)
    assert (window.retries_used, window.tasks_started) == (1, 1)  # charged anew in the new window
    # Live claims keep the same tasks from being admitted a second time.
    assert coordinator.tick() == 0 and len(dispatched) == 1


def test_without_rebind_nothing_runs(tmp_path, monkeypatch):
    s, goal, old, tasks = _stranded()
    new = s.autonomy.activate(_payload("new-window"))
    coordinator = _coordinator(s, tmp_path, [])
    monkeypatch.setattr(coordinator, "_execute_claimed_batch", lambda **kw: pytest.fail("dispatched"))
    assert s.control.runnable_tasks(new.id) == ()
    assert coordinator.tick() == 0
    assert coordinator.status()["stranded_goals"][0]["goal_id"] == goal.id
    with pytest.raises(TaskStoreError, match="window_not_active"):
        s.control.claim_task(window_id=old.id, task_id=tasks["T006"], owner="late", lease_ms=1000)


def _refusal_setup(case):
    s, goal, old, tasks = _stranded()
    payload = {}
    if case == "terminal_only":
        s.store.set_state(tasks["T005"], "READY_FOR_REVIEW")
        s.store.set_state(tasks["T006"], "CANCELLED")
    elif case == "wrong_repository":
        payload = {"repositories": ["dddd2024/other"]}
    elif case == "missing_capability":
        payload = {"capabilities": ["execute_task"]}
    elif case == "retry_budget":
        payload = {"max_retries": 0}
    elif case == "task_budget":
        s.store._conn.execute("UPDATE tasks SET status = 'QUEUED' WHERE id = ?", (tasks["T005"],))
        payload = {"max_tasks": 1}
    elif case == "in_flight":
        s.store.set_state(tasks["T006"], "RUNNING")
    elif case == "live_claim":
        s.store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms = 99999999999999 "
                              "WHERE task_id = ?", (tasks["T005"],))
    new = s.autonomy.activate(_payload("new-window", **payload))
    if case == "stopped_window":
        s.control.stop_window(new.id)
    return s, goal, old, tasks, new


@pytest.mark.parametrize("case,error", [
    ("terminal_only", "goal_has_no_unfinished_tasks"),
    ("wrong_repository", "rebind_window_repository_mismatch"),
    ("missing_capability", "rebind_window_missing_resume_task_capability"),
    ("retry_budget", "rebind_window_retry_budget_insufficient"),
    ("task_budget", "rebind_window_task_budget_insufficient"),
    ("in_flight", "goal_task_in_flight"),
    ("live_claim", "goal_task_claim_live"),
    ("stopped_window", "rebind_window_not_active"),
])
def test_rebind_refusals_change_nothing(case, error):
    s, goal, old, tasks, new = _refusal_setup(case)
    with pytest.raises(TaskStoreError, match=error):
        s.control.rebind_goal_to_window(goal.id, window_id=new.id)
    assert s.control.get_goal(goal.id).window_id == old.id
    assert _claim(s, tasks["T005"])["status"] == "ACTIVE"
    assert _receipts(s, "goal_window_rebind") == [] and _receipts(s, "claim_retirement") == []


def test_rebind_refuses_while_old_window_can_still_dispatch():
    s = _services()
    goal = s.goals.create({"objective": "Still active", "idempotency_key": "active",
                           "executor_kind": "deterministic_fixture", "orchestration_mode": "single"})
    s.goals.plan(goal.id, expected_revision=1)
    s.goals.approve(goal.id, expected_revision=1)
    window = s.autonomy.activate(_payload("only-window"))
    s.goals.launch(goal.id, expected_revision=1, window_id=window.id)
    assert s.control.rebind_goal_to_window(goal.id, window_id=window.id)["status"] == "ALREADY_BOUND"
    with pytest.raises(TaskStoreError, match="goal_window_still_active"):
        s.control.rebind_goal_to_window(goal.id, window_id="window-other")


def test_unknown_side_effects_stay_on_hold():
    s, goal, old, tasks = _stranded(receipt=False)
    new = s.autonomy.activate(_payload("new-window"))
    outcome = s.control.rebind_goal_to_window(goal.id, window_id=new.id)
    assert outcome["held_tasks"] == [tasks["T005"]] and outcome["retired_claims"] == []
    claim = _claim(s, tasks["T005"])
    assert (claim["status"], claim["window_id"]) == ("ACTIVE", old.id)  # retained, never released
    assert s.control.runnable_tasks(new.id) == (tasks["T006"],)
    with pytest.raises(TaskStoreError, match="unknown_claim_task_held"):
        s.control.claim_task(window_id=new.id, task_id=tasks["T005"], owner="new", lease_ms=1000)


def test_concurrent_rebind_is_idempotent_and_retires_once(tmp_path):
    db = str(tmp_path / "platform.sqlite3")
    s, goal, old, tasks = _stranded(db)
    new = s.autonomy.activate(_payload("new-window"))
    outcomes, errors = [], []
    barrier = threading.Barrier(4)

    def rebind():
        other = _services(db)
        barrier.wait()
        try:
            outcomes.append(other.control.rebind_goal_to_window(goal.id, window_id=new.id)["status"])
        except Exception as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=rebind) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert sorted(outcomes) == ["ALREADY_BOUND"] * 3 + ["REBOUND"]
    assert len(_receipts(s, "claim_retirement")) == 1
    assert len(_receipts(s, "goal_window_rebind")) == 1


def test_activation_adopts_only_explicitly_listed_goals():
    s, goal, old, tasks = _stranded()
    with pytest.raises(TaskStoreError, match="goal_not_found"):
        s.autonomy.activate(_payload("new-window", adopt_unfinished_goals=["goal-missing"]))
    assert s.control.active_window() is None  # adoption and activation commit together
    window = s.autonomy.activate(_payload("new-window", adopt_unfinished_goals=[goal.id]))
    assert s.control.get_goal(goal.id).window_id == window.id
    assert s.autonomy.summary(window.id)["adopted_goals"] == [goal.id]
    assert set(s.control.runnable_tasks(window.id)) == set(tasks.values())


def test_activation_without_adoption_list_keeps_goal_stranded():
    s, goal, old, tasks = _stranded()
    window = s.autonomy.activate(_payload("new-window"))
    assert s.control.get_goal(goal.id).window_id == old.id
    assert s.autonomy.summary(window.id)["adopted_goals"] == []
    assert [g["goal_id"] for g in s.control.stranded_goals()] == [goal.id]
