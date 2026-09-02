from datetime import datetime, timedelta, timezone
import threading
from types import SimpleNamespace

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _ready_fixture(store: TaskStore, task_id: str):
    store.transition_to(task_id, "PREPARING_WORKSPACE")
    store.transition_to(task_id, "RUNNING_FIXTURE")
    store.transition_to(task_id, "VALIDATING")
    store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
    return SimpleNamespace(success=True)


def _runtime_with_one_task(tmp_path, *, task_executor=None):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(
        control_store=control,
        capabilities=CapabilityRegistry(),
    )
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate(
        {
            "policy_id": "coordinator-shutdown",
            "policy_revision": 1,
            "owner_identity": "owner",
            "starts_at": (now - timedelta(seconds=2)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "repositories": ["dddd2024/reverse-agent"],
            "capabilities": ["execute_task"],
            "max_concurrent_tasks": 1,
            "max_tasks": 2,
            "max_retries": 1,
            "confirmation": "ACTIVATE",
        }
    )
    goal = goals.create(
        {
            "objective": "Exercise coordinator shutdown lifecycle",
            "idempotency_key": "coordinator-shutdown-goal",
            "executor_kind": "deterministic_fixture",
            "orchestration_mode": "single",
        }
    )
    goals.plan(
        goal.id,
        expected_revision=1,
        tasks=[
            {
                "id": "T001",
                "title": "shutdown race task",
                "instruction": "exercise the bounded shutdown path",
            }
        ],
    )
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    coordinator = UnattendedCoordinator(
        store=store,
        control_store=control,
        autonomy=autonomy,
        router=ExecutorRouter(),
        workspace_root=tmp_path,
        task_executor=task_executor,
        poll_interval=60.0,
    )
    return store, control, coordinator, task_id


def test_idle_start_stop_converges_to_stopped(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(
        control_store=control,
        capabilities=CapabilityRegistry(),
    )
    coordinator = UnattendedCoordinator(
        store=store,
        control_store=control,
        autonomy=autonomy,
        router=ExecutorRouter(),
        workspace_root=tmp_path,
        poll_interval=60.0,
    )

    assert coordinator.status()["lifecycle"] == "STOPPED"
    coordinator.start()
    owned = coordinator._thread
    assert owned is not None
    assert owned.is_alive()
    assert coordinator.status()["lifecycle"] == "RUNNING"

    coordinator.stop(timeout=2.0)

    status = coordinator.status()
    assert status["lifecycle"] == "STOPPED"
    assert status["enabled"] is False
    assert status["accepting_work"] is False
    assert coordinator._thread is None


def test_short_stop_timeout_retains_owned_thread_until_drained_and_blocks_restart(tmp_path):
    entered = threading.Event()
    release = threading.Event()

    store_holder: dict[str, TaskStore] = {}

    def execute(task_id: str):
        entered.set()
        assert release.wait(timeout=5.0)
        return _ready_fixture(store_holder["store"], task_id)

    store, _control, coordinator, _task_id = _runtime_with_one_task(
        tmp_path,
        task_executor=execute,
    )
    store_holder["store"] = store

    coordinator.start()
    assert entered.wait(timeout=5.0)
    owned = coordinator._thread
    assert owned is not None and owned.is_alive()

    coordinator.stop(timeout=0.001)

    status = coordinator.status()
    assert coordinator._thread is owned
    assert owned.is_alive()
    assert status["lifecycle"] == "DRAINING"
    assert status["enabled"] is True
    assert status["accepting_work"] is False
    assert status["inflight_batch"] is True
    assert status["last_error"] == "coordinator_stop_timeout"

    coordinator.start()
    assert coordinator._thread is owned
    assert coordinator.status()["lifecycle"] == "DRAINING"
    assert coordinator.status()["last_error"] == "coordinator_still_draining"

    coordinator.stop(timeout=0.0)
    assert coordinator._thread is owned
    assert coordinator.status()["lifecycle"] == "DRAINING"

    release.set()
    owned.join(timeout=5.0)
    assert not owned.is_alive()

    status = coordinator.status()
    assert status["lifecycle"] == "STOPPED"
    assert status["enabled"] is False
    assert status["inflight_batch"] is False
    assert coordinator._thread is None

    coordinator.start()
    fresh = coordinator._thread
    assert fresh is not None
    assert fresh is not owned
    assert fresh.is_alive()
    coordinator.stop(timeout=2.0)
    assert coordinator.status()["lifecycle"] == "STOPPED"


def test_stop_intent_before_tick_prevents_admission(tmp_path):
    calls: list[str] = []

    def execute(task_id: str):
        calls.append(task_id)
        raise AssertionError("executor must not run after stop intent")

    _store, control, coordinator, task_id = _runtime_with_one_task(
        tmp_path,
        task_executor=execute,
    )

    coordinator.stop(timeout=0.0)

    assert coordinator.tick() == 0
    assert calls == []
    claim = control._conn.execute(
        "SELECT status FROM platform_coordinator_claims WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    assert claim is None


def test_stop_winning_after_claim_abandons_before_dispatch(tmp_path, monkeypatch):
    calls: list[str] = []

    def execute(task_id: str):
        calls.append(task_id)
        raise AssertionError("post-stop claimed task must not dispatch")

    store, control, coordinator, task_id = _runtime_with_one_task(
        tmp_path,
        task_executor=execute,
    )
    original_claim = control.claim_task
    claim_acquired = threading.Event()
    allow_claim_return = threading.Event()

    def delayed_claim(**kwargs):
        result = original_claim(**kwargs)
        claim_acquired.set()
        assert allow_claim_return.wait(timeout=5.0)
        return result

    monkeypatch.setattr(control, "claim_task", delayed_claim)
    results: list[int] = []
    tick_thread = threading.Thread(target=lambda: results.append(coordinator.tick()))
    tick_thread.start()
    assert claim_acquired.wait(timeout=5.0)

    coordinator.stop(timeout=0.0)
    allow_claim_return.set()
    tick_thread.join(timeout=5.0)
    assert not tick_thread.is_alive()

    assert results == [0]
    assert calls == []
    assert store.get_task(task_id).status == "QUEUED"
    claim = control._conn.execute(
        "SELECT owner, status FROM platform_coordinator_claims WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    assert claim is not None
    assert dict(claim) == {"owner": coordinator.owner, "status": "FAILED"}
    assert control.window_budget_summary(
        control.active_window().id
    )["active_reservation_count"] == 0
    status = coordinator.status()
    assert status["lifecycle"] == "STOPPED"
    assert status["last_batch"]["accepted"] is False
    assert status["last_batch"]["claimed_size"] == 1
    assert status["last_batch"]["task_ids"] == [task_id]
    assert status["last_batch"]["reasons"] == [
        "coordinator_stop_requested_before_dispatch"
    ]
