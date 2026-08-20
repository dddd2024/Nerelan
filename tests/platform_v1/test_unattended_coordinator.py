from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _ready_fixture(store: TaskStore, task_id: str):
    store.transition_to(task_id, "PREPARING_WORKSPACE")
    store.transition_to(task_id, "RUNNING_FIXTURE")
    store.transition_to(task_id, "VALIDATING")
    store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
    return SimpleNamespace(success=True)


def test_coordinator_respects_dependencies_and_restart_does_not_duplicate(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "unattended-1", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = goals.create({
        "objective": "Run two dependent tasks", "idempotency_key": "coord-goal-1",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "first", "instruction": "do first"},
        {"id": "T002", "title": "second", "instruction": "do second", "dependencies": ["T001"]},
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    calls = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert len(calls) == 1
    assert coordinator.tick() == 1
    assert len(calls) == 2
    assert control.get_goal(goal.id).status == "COMPLETED"

    restarted = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert restarted.tick() == 0
    assert len(calls) == 2
    summary = autonomy.summary(window.id)
    assert summary["window"]["tasks_started"] == 2
    assert summary["window"]["tasks_completed"] == 2


def _parallel_goal(goals, window_id, *, key, count=2):
    goal = goals.create({
        "objective": f"Run {count} independent tasks concurrently",
        "idempotency_key": key,
        "executor_kind": "deterministic_fixture",
        "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {
            "id": f"T{index:03d}",
            "title": f"worker {index}",
            "instruction": f"run worker {index}",
        }
        for index in range(1, count + 1)
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window_id)
    return goal


def test_coordinator_uses_langgraph_send_for_real_parallel_batch(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-batch", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = _parallel_goal(goals, window.id, key="parallel-goal")
    barrier = threading.Barrier(2)
    worker_threads: set[int] = set()
    worker_lock = threading.Lock()

    def execute(task_id):
        with worker_lock:
            worker_threads.add(threading.get_ident())
        barrier.wait(timeout=5)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 2
    assert len(worker_threads) == 2
    assert control.get_goal(goal.id).status == "COMPLETED"
    status = coordinator.status()
    assert status["last_batch"]["accepted"] is True
    assert status["last_batch"]["size"] == 2
    assert status["last_batch"]["task_ids"] == sorted(
        link["task_id"] for link in control.list_goal_tasks(goal.id)
    )


def test_parallel_batch_admission_shrinks_before_dispatch_on_budget_limit(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(
        autonomy, policy_id="parallel-admission-budget",
        max_tokens=100, reservation=60,
    )
    goals = GoalService(store=store, control_store=control)
    _parallel_goal(goals, window.id, key="parallel-budget-goal")
    calls: list[str] = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert len(calls) == 1
    assert coordinator.status()["last_batch"]["size"] == 1
    assert control.window_budget_summary(window.id)["active_reservation_count"] == 0
    assert coordinator.tick() == 1
    assert len(calls) == 2


def test_parallel_batch_never_exceeds_window_wip_one(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-wip-one", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 2, "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    _parallel_goal(goals, window.id, key="parallel-wip-one-goal")
    calls: list[str] = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert coordinator.status()["last_batch"]["size"] == 1
    assert len(calls) == 1
    assert coordinator.tick() == 1
    assert len(calls) == 2


def test_parallel_batch_isolates_worker_exception_and_claim_finalization(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-mixed", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = _parallel_goal(goals, window.id, key="parallel-mixed-goal")
    good_id, bad_id = [
        link["task_id"] for link in control.list_goal_tasks(goal.id)
    ]
    barrier = threading.Barrier(2)

    def execute(task_id):
        barrier.wait(timeout=5)
        if task_id == bad_id:
            raise RuntimeError("bounded-worker-failure")
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 1
    assert store.get_task(good_id).status == "READY_FOR_REVIEW_FIXTURE"
    assert store.get_task(bad_id).status == "QUEUED"
    claims = {
        row["task_id"]: row["status"]
        for row in control._conn.execute(
            "SELECT task_id, status FROM platform_coordinator_claims"
        ).fetchall()
    }
    assert claims == {good_id: "COMPLETE", bad_id: "FAILED"}
    assert control.window_budget_summary(window.id)["active_reservation_count"] == 0
    assert coordinator.status()["last_batch"]["accepted"] is False


def test_parallel_restart_reclaims_interrupted_task_once_with_retained_budget(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-restart", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "resume_task"],
        "max_concurrent_tasks": 2, "max_tasks": 1, "max_retries": 1,
        "max_token_units": 100, "per_task_token_reservation": 60,
        "provider_quota_state": "OBSERVED", "confirmation": "ACTIVATE",
    })
    goals = GoalService(store=store, control_store=control)
    goal = _parallel_goal(goals, window.id, key="parallel-restart-goal", count=1)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    epoch_one, _ = control.claim_task(
        window_id=window.id, task_id=task_id, owner="old-owner", lease_ms=60_000
    )
    control._conn.execute(
        "UPDATE platform_coordinator_claims SET expires_at_ms = 0 WHERE task_id = ?",
        (task_id,),
    )
    store.set_state(task_id, "INTERRUPTED")
    assert control.reconcile_expired_budget_reservations() == (
        f"budget_reservation_retained:{task_id}",
    )
    calls: list[str] = []

    def resume(task_id):
        calls.append(task_id)
        assert store.get_task(task_id).status == "INTERRUPTED"
        store.transition_to(task_id, "RUNNING_FIXTURE")
        store.transition_to(task_id, "VALIDATING")
        store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
        return SimpleNamespace(success=True)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path,
        task_executor=resume, owner="new-owner",
    )
    assert coordinator.tick() == 1
    assert calls == [task_id]
    claim = control._conn.execute(
        "SELECT owner, epoch, status FROM platform_coordinator_claims WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    assert dict(claim) == {
        "owner": "new-owner", "epoch": epoch_one + 1, "status": "COMPLETE"
    }
    summary = control.get_window(window.id)
    assert summary.tasks_started == 1
    assert summary.retries_used == 1
    assert summary.tasks_completed == 1
    assert control.window_budget_summary(window.id)["active_reservation_count"] == 0


def test_parallel_batch_reuses_shared_connection_durable_fixture_runs_repeatedly(tmp_path):
    store = TaskStore(str(tmp_path / "parallel-durable.sqlite3"))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-durable", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 20, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    executor_barrier = threading.Barrier(2, timeout=5)

    class BarrierFixtureExecutor:
        def execute(
            self, task_id, task_store, *, workspace_root="", event_callback=None
        ):
            executor_barrier.wait()
            return ExecutorResult(
                success=True,
                validation_exit_code=0,
                validation_command_id="git_diff_check",
                validation_output_digest="barrier-fixture",
                validation_output_summary="provider-free barrier completed",
                changed_files=[],
                execution_id=f"exec-{task_id}",
            )

    router = ExecutorRouter()
    router.register("deterministic_fixture", lambda **_: BarrierFixtureExecutor())
    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=router, workspace_root=tmp_path / "workspaces",
        execution_authority_sha="a" * 64, planning_sha="b" * 64,
    )
    all_task_ids: list[str] = []
    for iteration in range(10):
        goal = _parallel_goal(
            goals, window.id, key=f"parallel-durable-goal-{iteration}"
        )
        all_task_ids.extend(
            link["task_id"] for link in control.list_goal_tasks(goal.id)
        )
        assert coordinator.tick() == 2
        assert control.get_goal(goal.id).status == "COMPLETED"
    runs = store._conn.execute(
        "SELECT task_id, accepted_checkpoint FROM durable_runs ORDER BY task_id"
    ).fetchall()
    assert len(runs) == 20
    assert {row["task_id"] for row in runs} == set(all_task_ids)
    assert {row["accepted_checkpoint"] for row in runs} == {"POST_VALIDATION"}
    assert store._conn.execute(
        "SELECT COUNT(*) AS c FROM durable_checkpoint_history"
    ).fetchone()["c"] == 100


def test_coordinator_is_inert_without_active_window(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=lambda task_id: None,
    )
    assert coordinator.tick() == 0
    assert coordinator.status()["active_window_id"] == ""


def _budget_window(
    service: AutonomyService,
    *,
    policy_id: str,
    max_tokens: int,
    reservation: int,
    max_tasks: int = 10,
    max_retries: int = 2,
):
    now = datetime.now(timezone.utc)
    return service.activate({
        "policy_id": policy_id, "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2,
        "max_tasks": max_tasks,
        "max_retries": max_retries,
        "max_token_units": max_tokens,
        "per_task_token_reservation": reservation,
        "provider_quota_state": "OBSERVED",
        "confirmation": "ACTIVATE",
    })


def test_concurrent_claims_cannot_reserve_past_token_budget(tmp_path):
    db_path = str(tmp_path / "concurrent-budget.sqlite3")
    store_a = TaskStore(db_path)
    control_a = PlatformControlStore(store_a)
    service = AutonomyService(control_store=control_a, capabilities=CapabilityRegistry())
    window = _budget_window(service, policy_id="concurrent-budget", max_tokens=100, reservation=60)
    first = store_a.create_task(title="first", executor_kind="opencode")
    second = store_a.create_task(title="second", executor_kind="opencode")
    store_b = TaskStore(db_path)
    control_b = PlatformControlStore(store_b)
    barrier = threading.Barrier(2)

    def claim(control, task_id, owner):
        barrier.wait(timeout=5)
        try:
            return control.claim_task(
                window_id=window.id, task_id=task_id, owner=owner, lease_ms=60_000
            )[0]
        except TaskStoreError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(
            lambda args: claim(*args),
            ((control_a, first.id, "owner-a"), (control_b, second.id, "owner-b")),
        ))
    assert sum(isinstance(value, int) for value in outcomes) == 1
    assert outcomes.count("window_token_budget_exhausted") == 1
    budget = control_a.window_budget_summary(window.id)
    assert budget["reserved_token_units"] == 60
    assert budget["remaining_token_units"] == 40
    assert budget["active_reservation_count"] == 1


def test_crash_reuses_reservation_and_completion_is_exactly_once():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    service = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(
        service,
        policy_id="crash-budget",
        max_tokens=100,
        reservation=60,
        max_tasks=1,
        max_retries=1,
    )
    task = store.create_task(title="crash", executor_kind="opencode")
    epoch_one, _ = control.claim_task(
        window_id=window.id, task_id=task.id, owner="owner-one", lease_ms=60_000
    )
    first_claim_window = control.get_window(window.id)
    assert first_claim_window.tasks_started == 1
    assert first_claim_window.retries_used == 0
    control._conn.execute(
        "UPDATE platform_coordinator_claims SET expires_at_ms = 0 WHERE task_id = ?",
        (task.id,),
    )
    store.set_state(task.id, "INTERRUPTED")
    assert control.reconcile_expired_budget_reservations() == (
        f"budget_reservation_retained:{task.id}",
    )
    epoch_two, _ = control.claim_task(
        window_id=window.id, task_id=task.id, owner="owner-two", lease_ms=60_000
    )
    assert epoch_two == epoch_one + 1
    retry_window = control.get_window(window.id)
    assert retry_window.tasks_started == 1
    assert retry_window.retries_used == 1
    budget = control.window_budget_summary(window.id)
    assert budget["reserved_token_units"] == 60
    assert budget["active_reservation_count"] == 1
    store.append_usage_observation(
        task.id,
        observation_id="usage-crash-exact-once",
        execution_id="exec-crash",
        role="coder",
        model_id="provider/model",
        provider_id="provider",
        source_kind="step_finish",
        source_id="msg-crash:part-crash",
        status="OBSERVED",
        input_units=30,
        output_units=10,
        reasoning_units=5,
        cache_read_units=5,
        cache_write_units=0,
        cost_micro_units=1000,
    )
    control.complete_task_claim(
        window_id=window.id, task_id=task.id, owner="owner-two",
        epoch=epoch_two, result="success",
    )
    with pytest.raises(TaskStoreError, match="coordinator_claim_fenced"):
        control.complete_task_claim(
            window_id=window.id, task_id=task.id, owner="owner-two",
            epoch=epoch_two, result="replay",
        )
    budget = control.window_budget_summary(window.id)
    assert budget["observed_token_units"] == 50
    assert budget["observed_cost_micro_units"] == 1000
    assert budget["reserved_token_units"] == 0
    assert budget["remaining_token_units"] == 50
    assert control._conn.execute(
        "SELECT COUNT(*) AS c FROM platform_usage_charges"
    ).fetchone()["c"] == 1
    with pytest.raises(TaskStoreError, match="window_retry_budget_exhausted"):
        control.claim_task(
            window_id=window.id,
            task_id=task.id,
            owner="owner-three",
            lease_ms=60_000,
        )
    fresh_task = store.create_task(title="fresh after retry", executor_kind="opencode")
    with pytest.raises(TaskStoreError, match="window_task_budget_exhausted"):
        control.claim_task(
            window_id=window.id,
            task_id=fresh_task.id,
            owner="owner-three",
            lease_ms=60_000,
        )


def test_admission_denial_performs_zero_executor_dispatches(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(
        autonomy, policy_id="deny-before-dispatch", max_tokens=60, reservation=60
    )
    blocker = store.create_task(title="budget holder", executor_kind="opencode")
    control.claim_task(
        window_id=window.id, task_id=blocker.id, owner="budget-holder", lease_ms=60_000
    )
    goals = GoalService(store=store, control_store=control)
    goal = goals.create({
        "objective": "must not dispatch", "idempotency_key": "no-dispatch-goal",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "T001", "title": "denied", "instruction": "never called"},
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    calls: list[str] = []
    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=lambda task_id: calls.append(task_id),
    )
    assert coordinator.tick() == 0
    assert calls == []
    assert control.window_budget_summary(window.id)["reserved_token_units"] == 60


@pytest.mark.parametrize("unknown,observed_tokens,stop_reason", [
    (True, 0, "usage_unknown"),
    (False, 61, "usage_reservation_overrun"),
])
def test_unknown_or_overrun_usage_blocks_future_dispatch(
    unknown, observed_tokens, stop_reason
):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(
        autonomy,
        policy_id=f"stop-{stop_reason}",
        max_tokens=100,
        reservation=60,
    )
    task = store.create_task(title="usage stop", executor_kind="opencode")
    epoch, _ = control.claim_task(
        window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000
    )
    kwargs = dict(
        observation_id=f"usage-{stop_reason}",
        execution_id="exec-stop",
        role="executor",
        model_id="provider/model",
        provider_id="provider",
        source_kind="step_finish",
        source_id=f"msg-stop:part-{stop_reason}",
        status="UNKNOWN" if unknown else "OBSERVED",
    )
    if not unknown:
        kwargs.update(
            input_units=observed_tokens,
            output_units=0,
            reasoning_units=0,
            cache_read_units=0,
            cache_write_units=0,
            cost_micro_units=0,
        )
    store.append_usage_observation(task.id, **kwargs)
    control.complete_task_claim(
        window_id=window.id, task_id=task.id, owner="owner",
        epoch=epoch, result="terminal",
    )
    stopped = control.get_window(window.id)
    assert stopped.status == "BLOCKED"
    assert stopped.stop_reason == stop_reason
    if unknown:
        assert stopped.enforcement_class == "USAGE_UNKNOWN"
        assert stopped.unknown_observation_count == 1
    assert control.active_window() is None
