"""Provider-free live slot-refill checks for delayed independent goals."""

from datetime import datetime, timedelta, timezone
import threading
import time
from types import SimpleNamespace

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _setup(tmp_path, *, max_concurrent=3):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "refill-window", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": max_concurrent, "max_tasks": 3,
        "max_retries": 0, "confirmation": "ACTIVATE",
    })
    return store, control, autonomy, goals, window


def _goal(goals, control, window, name, count=1):
    goal = goals.create({
        "objective": name, "repository": "dddd2024/Nerelan", "idempotency_key": "refill-" + name,
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": f"T{i:03d}", "title": f"{name} worker {i}", "instruction": name}
        for i in range(count)
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    return goal, [row["task_id"] for row in control.list_goal_tasks(goal.id)]


def _done(store, task_id):
    for status in ("PREPARING_WORKSPACE", "RUNNING_FIXTURE", "VALIDATING", "READY_FOR_REVIEW_FIXTURE"):
        store.transition_to(task_id, status)
    return SimpleNamespace(success=True)


def _wait_for(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.03)
    return False


def test_late_goals_start_while_first_batch_still_running(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path)
    first_goal, [first] = _goal(goals, control, window, "first")
    first_started = threading.Event()
    release = threading.Event()
    seen = set()
    mutex = threading.Lock()

    def execute(task_id):
        with mutex:
            seen.add(task_id)
        if task_id == first:
            first_started.set()
            assert release.wait(timeout=10)
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    try:
        coordinator.start()
        assert first_started.wait(5)
        second_goal, later = _goal(goals, control, window, "later", count=2)
        assert _wait_for(lambda: set(later) <= seen), "new goals must run before slow A finishes"
        assert store.get_task(first).status == "QUEUED", "first fixture has not completed"
        assert _wait_for(lambda: all(store.get_task(t).status == "READY_FOR_REVIEW_FIXTURE" for t in later))
        assert control.get_window(window.id).tasks_started == 3
        assert coordinator.status()["inflight_task_count"] >= 1
    finally:
        release.set()
        coordinator.stop(timeout=5)
    assert _wait_for(lambda: store.get_task(first).status == "READY_FOR_REVIEW_FIXTURE")
    assert control.get_window(window.id).tasks_completed == 3
    assert control.get_goal(first_goal.id).status == "COMPLETED"
    assert control.get_goal(second_goal.id).status == "COMPLETED"


def test_refill_never_exceeds_persisted_window_wip_limit(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _first_goal, [first] = _goal(goals, control, window, "wip-first")
    first_started = threading.Event()
    release = threading.Event()
    release_second = threading.Event()
    seen = []
    active = set()
    peak = 0
    mutex = threading.Lock()

    def execute(task_id):
        nonlocal peak
        with mutex:
            seen.append(task_id)
            active.add(task_id)
            peak = max(peak, len(active))
        try:
            if task_id == first:
                first_started.set()
                assert release.wait(timeout=10)
            else:
                assert release_second.wait(timeout=10)
            return _done(store, task_id)
        finally:
            with mutex:
                active.remove(task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    try:
        coordinator.start()
        assert first_started.wait(5)
        _later_goal, later = _goal(goals, control, window, "wip-later", count=2)
        assert _wait_for(lambda: any(t in seen for t in later))
        assert _wait_for(lambda: sum(t in seen for t in later) == 1)
        # One slot remains occupied by the first slow worker; a third
        # dispatch is forbidden until that lease/claim finishes.
        time.sleep(0.35)
        assert sum(t in seen for t in later) == 1
        assert peak <= 2
        assert control.get_window(window.id).tasks_started == 2
        release_second.set()
        assert _wait_for(lambda: all(t in seen for t in later))
    finally:
        release_second.set()
        release.set()
        assert _wait_for(lambda: all(store.get_task(t).status == "READY_FOR_REVIEW_FIXTURE" for t in [first] + later))
        coordinator.stop(timeout=5)
    assert len(seen) == len(set(seen)) == 3
    assert peak <= 2
    assert control.get_window(window.id).tasks_completed == 3


def test_stop_drains_running_batch_and_does_not_admit_late_goal(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _goal1, [first] = _goal(goals, control, window, "stop-first")
    started = threading.Event()
    release = threading.Event()
    calls = []

    def execute(task_id):
        calls.append(task_id)
        started.set()
        assert release.wait(timeout=10)
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    coordinator.start()
    assert started.wait(5)
    _goal2, [late] = _goal(goals, control, window, "stop-late")
    coordinator.stop(timeout=0.001)
    assert coordinator.status()["lifecycle"] == "DRAINING"
    assert coordinator.status()["inflight_batch"] is True
    release.set()
    assert _wait_for(lambda: coordinator.status()["lifecycle"] == "STOPPED")
    assert store.get_task(late).status == "QUEUED"
    assert calls == [first]
    assert coordinator.status()["inflight_batch"] is False

def test_fast_worker_frees_slot_while_slow_sibling_in_same_batch(tmp_path):
    """Refill must follow each completed worker, not the enclosing graph batch."""
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _initial, initial = _goal(goals, control, window, "initial-pair", count=2)
    slow, fast = initial
    slow_started = threading.Event()
    fast_finished = threading.Event()
    late_started = threading.Event()
    release_slow = threading.Event()
    seen = []
    mutex = threading.Lock()

    def execute(task_id):
        with mutex:
            seen.append(task_id)
        if task_id == slow:
            slow_started.set()
            assert release_slow.wait(timeout=10)
        elif task_id == fast:
            fast_finished.set()
        else:
            late_started.set()
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    try:
        coordinator.start()
        assert slow_started.wait(5)
        assert fast_finished.wait(5)
        assert _wait_for(lambda: store.get_task(fast).status == "READY_FOR_REVIEW_FIXTURE")
        _later_goal, [late] = _goal(goals, control, window, "after-fast")
        assert late_started.wait(5), "slot must refill before the original slow batch exits"
        assert store.get_task(slow).status == "QUEUED"
        assert control.get_window(window.id).tasks_started == 3
    finally:
        release_slow.set()
        coordinator.stop(timeout=5)
    assert all(store.get_task(task).status == "READY_FOR_REVIEW_FIXTURE" for task in (slow, fast, late))
    assert control.get_window(window.id).tasks_completed == 3
    assert len(seen) == len(set(seen)) == 3


def test_worker_initiated_stop_does_not_self_join(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=1)
    _goal1, [task] = _goal(goals, control, window, "worker-stop")
    called = threading.Event()
    coordinator = None

    def execute(task_id):
        coordinator.stop(timeout=0.1)
        called.set()
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    coordinator.start()
    assert called.wait(5), "stop from graph worker must not deadlock host poller"
    assert _wait_for(lambda: coordinator.status()["lifecycle"] == "STOPPED", timeout=5)
    assert store.get_task(task).status == "READY_FOR_REVIEW_FIXTURE"
    assert control.get_window(window.id).tasks_completed == 1


def test_expired_lease_does_not_relaunch_a_still_running_local_executor(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _first_goal, [first] = _goal(goals, control, window, "lease-running")
    entered = threading.Event()
    release = threading.Event()
    late_started = threading.Event()
    seen = []
    lock = threading.Lock()

    def execute(task_id):
        with lock:
            seen.append(task_id)
        if task_id == first:
            entered.set()
            assert release.wait(10)
        else:
            late_started.set()
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    try:
        coordinator.start()
        assert entered.wait(5)
        # Simulate an overdue lease while the original local executor is alive.
        # Claim epochs alone must not license a second invocation.
        with store._lock:
            store._conn.execute(
                "UPDATE platform_coordinator_claims SET expires_at_ms = 1 WHERE task_id = ?",
                (first,),
            )
        _later_goal, [later] = _goal(goals, control, window, "lease-later")
        assert late_started.wait(5), "an independent free slot should still refill"
        time.sleep(0.35)
        with lock:
            assert seen.count(first) == 1, "a still-live task was dispatched twice"
            assert seen.count(later) == 1
    finally:
        release.set()
        coordinator.stop(timeout=6)


def test_synchronous_tick_is_drained_and_not_raced_by_background_poller(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _initial, [first] = _goal(goals, control, window, "manual-first")
    entered = threading.Event()
    release = threading.Event()
    seen = []

    def execute(task_id):
        seen.append(task_id)
        if task_id == first:
            entered.set()
            assert release.wait(10)
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    manual = threading.Thread(target=coordinator.tick)
    try:
        manual.start()
        assert entered.wait(5)
        coordinator.start()
        _later, [later] = _goal(goals, control, window, "manual-later")
        time.sleep(0.35)
        assert store.get_task(later).status == "QUEUED"
        assert seen == [first], "background poller raced the synchronous tick"
        coordinator.stop(timeout=0.05)
        assert coordinator.status()["lifecycle"] == "DRAINING"
    finally:
        release.set()
        manual.join(timeout=6)
        coordinator.stop(timeout=6)
    assert not manual.is_alive()
    assert _wait_for(lambda: coordinator.status()["lifecycle"] == "STOPPED")
    assert store.get_task(first).status == "READY_FOR_REVIEW_FIXTURE"
    assert store.get_task(later).status == "QUEUED"


def test_old_batch_cleanup_cannot_clear_later_epoch_active_marker(tmp_path):
    store, control, autonomy, goals, window = _setup(tmp_path, max_concurrent=2)
    _initial, tasks = _goal(goals, control, window, "epoch-ownership", count=2)
    slow, fast = tasks
    entered = threading.Event()
    release = threading.Event()

    def execute(task_id):
        if task_id == slow:
            entered.set()
            assert release.wait(10)
        return _done(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=execute, poll_interval=0.1,
    )
    try:
        coordinator.start()
        assert entered.wait(5)
        assert _wait_for(
            lambda: store.get_task(fast).status == "READY_FOR_REVIEW_FIXTURE"
        )
        # A newer retry can start while the old batch waits on a slow sibling.
        # Its epoch owns its marker; the old graph finalizer must not erase it.
        with coordinator._lifecycle_lock:
            assert slow in coordinator._active_task_ids
            coordinator._active_task_epochs[fast] = 99
            coordinator._active_task_ids.add(fast)
        release.set()
        assert _wait_for(lambda: not coordinator._batch_threads)
        with coordinator._lifecycle_lock:
            assert coordinator._active_task_epochs[fast] == 99
            assert fast in coordinator._active_task_ids
            coordinator._active_task_epochs.pop(fast)
            coordinator._active_task_ids.discard(fast)
    finally:
        release.set()
        coordinator.stop(timeout=6)
