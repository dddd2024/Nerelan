from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
import time
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


@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("mutation", [None, "goal", "window", "task", "revision", "epoch", "future", "missing_result", "false_result", "artifact", "policy"])
def test_strict_owner_terminal_recovery_through_coordinator(tmp_path, monkeypatch, failed, mutation):
    from test_goal_service import _persisted_host_result
    from reverse_agent.platform_v1.task_runtime import LocalValidationRunner
    from reverse_agent.platform_v1.control_store import sha256_json

    store, control, window, goal, task_id = _persisted_host_result(
        tmp_path, monkeypatch, strict=True, failed=failed)
    try:
        store._conn.execute("UPDATE platform_autonomous_windows SET expires_at=? WHERE id=?",
            ((datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(), window.id))
        store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?", (task_id,))
        task = store.get_task(task_id)
        store.append_usage_observation(task_id, observation_id="original-unknown", execution_id=task.execution_id,
            role="executor", model_id="fixture", provider_id="", source_kind="fixture", source_id="original", status="UNKNOWN")
        if mutation == "goal":
            store._conn.execute("UPDATE platform_goals SET window_id='' WHERE id=?", (goal.id,))
        elif mutation == "window":
            store._conn.execute("UPDATE platform_coordinator_claims SET window_id='foreign' WHERE task_id=?", (task_id,))
        elif mutation == "task":
            foreign = store.create_task(title="Foreign", repository=goal.repository, executor_kind=goal.executor_kind)
            store._conn.execute("UPDATE platform_goal_task_links SET task_id=? WHERE task_id=?", (foreign.id, task_id))
        elif mutation == "revision":
            store._conn.execute("UPDATE platform_goal_task_links SET goal_revision=2 WHERE task_id=?", (task_id,))
        elif mutation == "epoch":
            store._conn.execute("UPDATE platform_coordinator_claims SET epoch=epoch+1 WHERE task_id=?", (task_id,))
        elif mutation == "future":
            store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=9999999999999 WHERE task_id=?", (task_id,))
        elif mutation == "missing_result":
            store._conn.execute("UPDATE tasks SET validation_output_digest='' WHERE id=?", (task_id,))
        elif mutation == "false_result":
            store._conn.execute("UPDATE tasks SET validation_exit_code=? WHERE id=?", (0 if failed else 1, task_id))
        elif mutation == "artifact":
            store._conn.execute("UPDATE platform_goals SET artifact_digest=? WHERE id=?", ("f" * 64, goal.id))
        elif mutation == "policy":
            store._conn.execute("UPDATE platform_autonomous_windows SET policy_digest=? WHERE id=?", ("f" * 64, window.id))
        def forbidden(*args, **kwargs):
            pytest.fail("Result-only recovery dispatched work")
        router = ExecutorRouter()
        monkeypatch.setattr(router, "create_executor", forbidden)
        monkeypatch.setattr(router, "dispatch_execute", forbidden)
        monkeypatch.setattr(LocalValidationRunner, "run", forbidden)
        autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
        assert not autonomy.authorize(window_id=window.id, operation="validate_task", repository=task.repository,
            subject_id=task_id, input_payload={"task_id": task_id})
        monkeypatch.setattr(autonomy, "authorize", forbidden)
        monkeypatch.setattr(control, "claim_task", forbidden)
        coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
            router=router, workspace_root=tmp_path, task_executor=forbidden)
        if mutation is not None:
            # Even a stale/foreign candidate from discovery must fail at the
            # transactional completion boundary without admission side effects.
            monkeypatch.setattr(control, "runnable_tasks", lambda *args, **kwargs: (task_id,))
        # tick is the actual single-pass coordinator entry point in this checkout.
        before = tuple(store._conn.iterdump())
        assert coordinator.tick() == (1 if mutation is None else 0)
        if mutation is not None:
            assert tuple(store._conn.iterdump()) == before
            with pytest.raises(TaskStoreError):
                control.complete_persisted_host_claim(window_id=window.id, task_id=task_id)
            assert tuple(store._conn.iterdump()) == before
        else:
            assert store.get_task(task_id) == task
            final = control.get_window(window.id)
            assert (final.tasks_started, final.tasks_completed, final.retries_used) == (1, 1, 0)
            assert final.capabilities == ("execute_task",)
            assert final.unknown_observation_count == 1
            claim = store._conn.execute("SELECT * FROM platform_coordinator_claims WHERE task_id=?", (task_id,)).fetchone()
            assert claim["status"] == "COMPLETE" and claim["epoch"] == 1 and claim["owner"] == "original"
            reservation = store._conn.execute("SELECT * FROM platform_budget_reservations").fetchone()
            assert reservation["state"] == "UNKNOWN" and reservation["claim_epoch"] == 1
            assert store._conn.execute("SELECT COUNT(*) FROM platform_budget_reservations").fetchone()[0] == 1
            assert store._conn.execute("SELECT COUNT(*) FROM platform_usage_charges").fetchone()[0] == 1
            receipts = control.list_receipts(window_id=window.id)
            reconciled = [r for r in receipts if r.operation_type == "task_claim_reconciliation"]
            assert len(reconciled) == 1
            receipt = reconciled[0]
            assert receipt.capability == "not_applicable" and receipt.decision == "not_evaluated"
            assert receipt.reason == "coordinator_persisted_result_reconciled"
            assert receipt.result == "persisted_host_result:UNKNOWN"
            assert receipt.subject_id == task_id and receipt.repository == task.repository
            assert receipt.actor == final.owner_identity
            assert receipt.policy_revision == final.policy_revision
            assert receipt.policy_digest == final.policy_digest
            assert receipt.confirmation_mode == control.window_policy_binding(window.id)["confirmation_mode"]
            assert receipt.input_digest == sha256_json({"task_id": task_id, "claim_epoch": 1,
                "claim_owner": "original", "persisted_result_only": True})
            assert not any(r.decision == "allowed" and r.capability in {"validate_task", "execute_task"}
                           for r in receipts)
            assert not any(r.operation_type == "task_execution" for r in receipts)
            assert all(r.decision != "allowed" for r in reconciled)
            assert control.receipt_totals(window_id=window.id)["total"] == len(receipts)
            assert coordinator.tick() == 0
            with pytest.raises(TaskStoreError):
                control.complete_persisted_host_claim(window_id=window.id, task_id=task_id)
            assert control.list_receipts(window_id=window.id) == receipts
    finally:
        store._conn.close()


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


@pytest.mark.parametrize("wip", [1, 2])
def test_coordinator_executes_reversed_dependency_chain_and_restart_once(tmp_path, wip):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "reversed-dag", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": wip, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = goals.create({
        "objective": "Execute a reversed dependency chain", "idempotency_key": "reversed-dag",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[
        {"id": "C", "title": "third", "instruction": "third", "dependencies": ["B"]},
        {"id": "B", "title": "second", "instruction": "second", "dependencies": ["A"]},
        {"id": "A", "title": "first", "instruction": "first"},
    ])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    tasks = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}
    calls = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    def coordinator():
        return UnattendedCoordinator(
            store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
            workspace_root=tmp_path, task_executor=execute,
        )

    assert coordinator().tick() == 1
    restarted = coordinator()
    assert restarted.tick() == 1
    assert restarted.tick() == 1
    assert restarted.tick() == 0
    assert calls == [tasks["A"], tasks["B"], tasks["C"]]
    assert control.get_goal(goal.id).status == "COMPLETED"
    budget = control.get_window(window.id)
    assert (budget.tasks_started, budget.tasks_completed) == (3, 3)


def test_runnable_limit_does_not_hide_later_goal_behind_waiting_rows(tmp_path):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "later-goal", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    older = goals.create({
        "objective": "Older blocked goal", "idempotency_key": "older-blocked",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(older.id, expected_revision=1, tasks=[
        {"id": "A", "title": "first", "instruction": "first"},
        *[{"id": f"B{i}", "title": "waiting", "instruction": "wait", "dependencies": ["A"]}
          for i in range(5)],
    ])
    goals.approve(older.id, expected_revision=1)
    goals.launch(older.id, expected_revision=1, window_id=window.id)
    store.set_state(control.list_goal_tasks(older.id)[0]["task_id"], "RUNNING")
    later = _parallel_goal(goals, window.id, key="later-ready", count=3)
    control._conn.execute(
        "UPDATE platform_goals SET created_at = ? WHERE id = ?", ("2000-01-01T00:00:00Z", older.id)
    )
    later_tasks = [link["task_id"] for link in control.list_goal_tasks(later.id)]
    assert control.runnable_tasks(window.id, limit=2) == tuple(later_tasks[:2])
    calls = []

    def execute(task_id):
        calls.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 2
    assert set(calls) == set(later_tasks[:2])
    assert coordinator.tick() == 1
    assert set(calls) == set(later_tasks)


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


def test_parallel_restart_reclaims_interrupted_task_once_with_retained_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("REVERSE_AGENT_MULTI_ACCOUNT_ENABLED", "1")
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
    coordinator._attempt_clock = lambda: pytest.fail("resume sampled fresh-attempt timing")
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
    router.replace("deterministic_fixture", lambda **_: BarrierFixtureExecutor())
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


@pytest.mark.parametrize("exhausted", ["retries", "fresh_tasks"])
def test_exhausted_attempt_budget_does_not_starve_other_work(tmp_path, exhausted):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "mixed-attempt-budgets", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task", "resume_task"],
        "max_concurrent_tasks": 1, "max_tasks": 2 if exhausted == "retries" else 1,
        "max_retries": 0 if exhausted == "retries" else 1, "confirmation": "ACTIVATE",
    })
    goal = _parallel_goal(goals, window.id, key="mixed-attempt-budgets")
    held_id, eligible_id = (link["task_id"] for link in control.list_goal_tasks(goal.id))
    interrupted_id = held_id if exhausted == "retries" else eligible_id
    control.claim_task(window_id=window.id, task_id=interrupted_id, owner="old", lease_ms=60000)
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?",
                        (interrupted_id,))
    store.set_state(interrupted_id, "INTERRUPTED")
    assert control.reconcile_expired_budget_reservations() == (
        f"budget_reservation_retained:{interrupted_id}",
    )
    dispatched = []

    def execute(task_id):
        dispatched.append(task_id)
        if store.get_task(task_id).status == "INTERRUPTED":
            store.transition_to(task_id, "RUNNING_FIXTURE")
            store.transition_to(task_id, "VALIDATING")
            store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
            return SimpleNamespace(success=True)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute)
    before = store.get_task(held_id).status
    assert control.runnable_tasks(window.id, limit=1) == (held_id,)
    assert control.runnable_tasks(window.id, limit=1, respect_attempt_limits=True) == (eligible_id,)
    assert coordinator.tick() == 1
    assert dispatched == [eligible_id]
    assert store.get_task(held_id).status == before
    assert control.get_window(window.id).retries_used == (1 if exhausted == "fresh_tasks" else 0)
    assert coordinator.tick() == 0


@pytest.mark.parametrize("budget_field,reservation_field", [
    ("max_token_units", "per_task_token_reservation"),
    ("max_cost_micro_units", "per_task_cost_reservation"),
])
@pytest.mark.parametrize("capacity,read_fails", [(100, False), (120, False), (120, True)])
def test_budget_pressure_does_not_starve_retained_reservation(
    tmp_path, monkeypatch, budget_field, reservation_field, capacity, read_fails,
):
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "retained-capacity", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task", "resume_task"],
        "max_concurrent_tasks": 2, "max_tasks": 4, "max_retries": 1,
        budget_field: capacity, reservation_field: 60,
        "provider_quota_state": "OBSERVED", "confirmation": "ACTIVATE",
    })
    goal = _parallel_goal(goals, window.id, key="retained-capacity", count=4)
    first, second, third, resumed = (link["task_id"] for link in control.list_goal_tasks(goal.id))
    original_epoch, _ = control.claim_task(
        window_id=window.id, task_id=resumed, owner="old", lease_ms=60_000,
    )
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=0 WHERE task_id=?",
                        (resumed,))
    store.set_state(resumed, "INTERRUPTED")
    assert control.reconcile_expired_budget_reservations() == (f"budget_reservation_retained:{resumed}",)
    dispatched = []
    prepared = []

    def execute(task_id):
        dispatched.append(task_id)
        if task_id == resumed:
            store.transition_to(task_id, "RUNNING_FIXTURE")
            store.transition_to(task_id, "VALIDATING")
            store.transition_to(task_id, "READY_FOR_REVIEW_FIXTURE")
            return SimpleNamespace(success=True)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
        quota_preparer=lambda task: prepared.append(task.id))
    assert control.runnable_tasks(window.id, limit=1) == (first,)
    assert control.runnable_tasks(window.id, limit=1, respect_reservation_limits=True) == (
        (resumed,) if capacity == 100 else (first,)
    )
    expected = {resumed} if capacity == 100 else {first, resumed}
    with monkeypatch.context() as faults:
        if read_fails:
            import sqlite3

            def fail_read(window_id):
                raise sqlite3.OperationalError("fixture reservation lookup failure")

            faults.setattr(control, "active_reservation_task_ids", fail_read)
            expected = {first}
        assert coordinator.tick() == len(expected)
    assert set(dispatched) == expected
    assert prepared == ([resumed] if capacity == 100 else
                        [first, second] if read_fails else [first, second, resumed])
    assert store.get_task(second).status == "QUEUED"
    if read_fails:
        assert coordinator.status()["last_error"] == "reservation_candidates_unavailable"
        assert control.get_window(window.id).tasks_completed == 1
        assert store.get_task(resumed).status == "INTERRUPTED"
    for _ in range(3):
        coordinator.tick()
    rows = store._conn.execute(
        "SELECT claim_epoch,state FROM platform_budget_reservations WHERE task_id=?", (resumed,),
    ).fetchall()
    assert [tuple(row) for row in rows] == [(original_epoch + 1, "RECONCILED")]
    assert control.get_window(window.id).retries_used == 1
    assert sorted(dispatched) == sorted([first, second, third, resumed])
    assert control.get_window(window.id).tasks_completed == 4
    assert coordinator.tick() == 0


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
    # #1504 cost-equivalent units: 30 + 10 + 5 + 5 * 0.1 = 45.5, rounded to 46.
    assert budget["observed_token_units"] == 46
    assert budget["observed_cost_micro_units"] == 1000
    assert budget["reserved_token_units"] == 0
    assert budget["remaining_token_units"] == 54
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


def test_unknown_usage_in_an_unbudgeted_window_is_counted_but_does_not_stop_it():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "post-run-observed", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0, "confirmation": "ACTIVATE",
    })
    assert window.enforcement_class == "POST_RUN_OBSERVED"
    first, second = (store.create_task(title=f"native {i}", executor_kind="codex", binding_ref="chatgpt-gpt")
                     for i in range(2))
    epoch, _ = control.claim_task(window_id=window.id, task_id=first.id, owner="owner", lease_ms=60_000)
    store.append_usage_observation(first.id, observation_id="usage-native", execution_id="exec-native",
                                   role="executor", model_id="gpt", provider_id="codex",
                                   source_kind="assistant_message", source_id="codex-turn-1", status="UNKNOWN")
    control.complete_task_claim(window_id=window.id, task_id=first.id, owner="owner", epoch=epoch, result="terminal")
    current = control.get_window(window.id)
    assert (current.status, current.stop_reason, current.unknown_observation_count) == ("ACTIVE", "", 1)
    assert current.enforcement_class == "POST_RUN_OBSERVED"
    control.claim_task(window_id=window.id, task_id=second.id, owner="owner", lease_ms=60_000)  # still dispatches


def test_unknown_usage_still_stops_a_zero_budget_hard_admission_window():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "zero-budget-hard", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(), "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 3, "max_retries": 0, "confirmation": "ACTIVATE",
    })
    # Delegated windows are HARD_ADMISSION_ENFORCED with zero token/cost limits.
    control._conn.execute("UPDATE platform_autonomous_windows SET enforcement_class='HARD_ADMISSION_ENFORCED' WHERE id=?",
                          (window.id,))
    control._conn.commit()
    task = store.create_task(title="unexpected model work", executor_kind="codex", binding_ref="chatgpt-gpt")
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000)
    store.append_usage_observation(task.id, observation_id="usage-hard", execution_id="exec-hard",
                                   role="executor", model_id="gpt", provider_id="codex",
                                   source_kind="assistant_message", source_id="codex-turn-hard", status="UNKNOWN")
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, result="terminal")
    stopped = control.get_window(window.id)
    assert (stopped.status, stopped.stop_reason, stopped.enforcement_class) == ("BLOCKED", "usage_unknown", "USAGE_UNKNOWN")


def _owner_window_with_unknown_attempt(max_tokens, reservation, partial_units, *, already=0):
    """An Owner window whose one attempt ended with partial (unknown) usage, e.g. a timeout."""
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="owner-unknown", max_tokens=max_tokens, reservation=reservation)
    task = store.create_task(title="timed out", executor_kind="opencode", binding_ref="coding-glm")
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000)
    # Marked after the claim: Owner-window claim admission (receipts) is tested in test_owner_window;
    # this exercises only the settlement of an unknown-usage attempt.
    control._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode='OWNER_WINDOW', "
                          "enforcement_class='HARD_ADMISSION_ENFORCED', observed_token_units=? WHERE id=?",
                          (already, window.id))
    control._conn.commit()
    store.append_usage_observation(task.id, observation_id="usage-partial", execution_id="exec-partial",
                                   role="executor", model_id="glm", provider_id="relay", source_kind="step_finish",
                                   source_id="part-1", status="PARTIAL", input_units=partial_units, output_units=0,
                                   reasoning_units=0, cache_read_units=0, cache_write_units=0, cost_micro_units=0)
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, result="terminal")
    reservation_row = control._conn.execute(
        "SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id=?", (task.id,)).fetchone()
    return control, window, reservation_row


def test_unknown_usage_in_an_owner_window_charges_the_reservation_and_continues():
    # Owner decision 2026-11-08: a timed-out attempt no longer stops the whole Owner window.
    control, window, reservation = _owner_window_with_unknown_attempt(2_000_000, 200_000, 70_000)
    after = control.get_window(window.id)
    assert after.status == "ACTIVE" and after.stop_reason in ("", None)
    assert after.observed_token_units == 200_000  # the whole reservation, not the 70k partial reading
    assert after.unknown_observation_count == 1
    assert (reservation["state"], reservation["observed_token_units"]) == ("UNKNOWN", None)  # not released
    summary = control.window_budget_summary(window.id)
    assert summary["remaining_token_units"] == 1_800_000  # charged once, not twice


def test_partial_usage_above_the_reservation_is_charged_in_full():
    control, window, _ = _owner_window_with_unknown_attempt(2_000_000, 200_000, 350_000)
    assert control.get_window(window.id).observed_token_units == 350_000


def test_a_charge_that_reaches_the_cap_stops_the_owner_window():
    control, window, _ = _owner_window_with_unknown_attempt(1_000_000, 200_000, 10, already=850_000)
    stopped = control.get_window(window.id)
    assert (stopped.status, stopped.stop_reason) == ("BLOCKED", "usage_unknown_budget_reached")
    assert stopped.observed_token_units == 1_050_000


def _owner_window_attempt(max_tokens, reservation, units, *, status="OBSERVED", cost_class=None, already=0):
    """An Owner window whose one attempt reported ``units`` tokens; optionally routed with a cost class."""
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="owner-attempt", max_tokens=max_tokens, reservation=reservation)
    task = store.create_task(title="attempt", executor_kind="opencode", binding_ref="coding-glm")
    if cost_class is not None:
        store.add_event(task.id, event_type="MODEL_SELECTED", title="Model selected", description="routed",
                        metadata={"binding_ref": "coding-glm", "reason": "cheapest_qualifying",
                                  "candidates": [{"binding_id": "coding-glm", "cost_class": cost_class},
                                                 {"binding_id": "other", "cost_class": "subscription"}]})
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000)
    control._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode='OWNER_WINDOW', "
                          "enforcement_class='HARD_ADMISSION_ENFORCED', observed_token_units=? WHERE id=?",
                          (already, window.id))
    control._conn.commit()
    store.append_usage_observation(task.id, observation_id="usage-1", execution_id="exec-1",
                                   role="executor", model_id="glm", provider_id="relay", source_kind="step_finish",
                                   source_id="part-1", status=status, input_units=units, output_units=0,
                                   reasoning_units=0, cache_read_units=0, cache_write_units=0, cost_micro_units=0)
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, result="terminal")
    row = control._conn.execute(
        "SELECT state, observed_token_units FROM platform_budget_reservations WHERE task_id=?", (task.id,)).fetchone()
    return control, window, row


def test_an_owner_window_overrun_is_charged_in_full_and_the_window_continues():
    # Owner decision 2026-11-09: 936k tokens against a 0 reservation stopped batch 1.
    control, window, reservation = _owner_window_attempt(20_000_000, 100_000, 936_532)
    after = control.get_window(window.id)
    assert (after.status, after.stop_reason or "") == ("ACTIVE", "")
    assert after.observed_token_units == 936_532
    assert reservation["state"] == "OVERRUN"  # recorded truthfully


def test_an_owner_window_overrun_that_reaches_the_cap_stops_it():
    control, window, _ = _owner_window_attempt(1_000_000, 100_000, 300_000, already=800_000)
    stopped = control.get_window(window.id)
    assert (stopped.status, stopped.stop_reason) == ("BLOCKED", "usage_budget_reached")


def test_other_windows_still_stop_on_an_overrun():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    window = _budget_window(autonomy, policy_id="plain", max_tokens=20_000_000, reservation=100_000)
    task = store.create_task(title="attempt", executor_kind="opencode", binding_ref="coding-glm")
    epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="owner", lease_ms=60_000)
    store.append_usage_observation(task.id, observation_id="usage-1", execution_id="exec-1",
                                   role="executor", model_id="glm", provider_id="relay", source_kind="step_finish",
                                   source_id="part-1", status="OBSERVED", input_units=936_532, output_units=0,
                                   reasoning_units=0, cache_read_units=0, cache_write_units=0, cost_micro_units=0)
    control.complete_task_claim(window_id=window.id, task_id=task.id, owner="owner", epoch=epoch, result="terminal")
    stopped = control.get_window(window.id)
    assert (stopped.status, stopped.stop_reason) == ("BLOCKED", "usage_reservation_overrun")


@pytest.mark.parametrize("status", ["OBSERVED", "PARTIAL"])
def test_a_free_model_does_not_count_toward_the_owner_window_cap(status):
    # Owner decision 2026-11-09: only Claude and Codex are paid; free usage is not charged.
    control, window, reservation = _owner_window_attempt(1_000_000, 100_000, 5_000_000, status=status,
                                                         cost_class="free", already=900_000)
    after = control.get_window(window.id)
    assert (after.status, after.stop_reason or "") == ("ACTIVE", "")
    assert after.observed_token_units == 900_000
    assert reservation["state"] in ("OVERRUN", "UNKNOWN")  # the observation itself is kept


@pytest.mark.parametrize("cost_class", [None, "subscription", "paid_api"])
def test_a_route_not_recorded_as_free_is_charged(cost_class):
    control, window, _ = _owner_window_attempt(20_000_000, 100_000, 300_000, cost_class=cost_class)
    assert control.get_window(window.id).observed_token_units == 300_000


@pytest.mark.parametrize("mutation", ["owner", "epoch", "window", "status", "expired", "gone"])
def test_renew_claim_is_fenced(monkeypatch, mutation):
    from reverse_agent.platform_v1 import control_store as cs

    store = TaskStore(":memory:")
    try:
        control = PlatformControlStore(store)
        autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
        window = _budget_window(autonomy, policy_id="renew", max_tokens=0, reservation=0)
        task = store.create_task(title="renew", executor_kind="deterministic_fixture")
        epoch, _ = control.claim_task(window_id=window.id, task_id=task.id, owner="worker", lease_ms=300)
        original = store._conn.execute("SELECT expires_at_ms FROM platform_coordinator_claims").fetchone()[0]
        monkeypatch.setattr(cs, "_utc_now_ms", lambda: original - 200)
        kwargs = dict(window_id=window.id, task_id=task.id, owner="worker", epoch=epoch, lease_ms=600)
        assert control.renew_claim(**kwargs)
        extended = store._conn.execute("SELECT expires_at_ms FROM platform_coordinator_claims").fetchone()[0]
        assert extended == original + 400
        if mutation == "owner":
            kwargs["owner"] = "other"
        elif mutation == "epoch":
            kwargs["epoch"] += 1
        elif mutation == "window":
            kwargs["window_id"] = "other"
        elif mutation == "status":
            store._conn.execute("UPDATE platform_coordinator_claims SET status='COMPLETED'")
        elif mutation == "expired":
            monkeypatch.setattr(cs, "_utc_now_ms", lambda: extended)
        else:
            store._conn.execute("DELETE FROM platform_coordinator_claims")
        assert not control.renew_claim(**{**kwargs, "lease_ms": 1000})
        row = store._conn.execute("SELECT expires_at_ms FROM platform_coordinator_claims").fetchone()
        assert row is None or row[0] == extended
    finally:
        store._conn.close()


def test_coordinator_renews_claim_through_long_execution(tmp_path, monkeypatch):
    import time

    store = TaskStore(":memory:")
    try:
        control = PlatformControlStore(store)
        autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
        window = _budget_window(autonomy, policy_id="long-turn", max_tokens=0, reservation=0)
        goals = GoalService(store=store, control_store=control)
        goal = _parallel_goal(goals, window.id, key="long-turn", count=1)
        task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
        renewed = []
        original = control.renew_claim

        def renew(**kwargs):
            result = original(**kwargs)
            renewed.append(result)
            return result

        monkeypatch.setattr(control, "renew_claim", renew)

        def execute(task_id):
            initial = store._conn.execute("SELECT expires_at_ms FROM platform_coordinator_claims").fetchone()[0]
            time.sleep(0.9)  # Three times the injected lease.
            with store._lock:
                claim = store._conn.execute("SELECT * FROM platform_coordinator_claims").fetchone()
            assert claim["status"] == "ACTIVE"
            assert claim["expires_at_ms"] > initial
            assert claim["expires_at_ms"] > int(time.time() * 1000)
            return _ready_fixture(store, task_id)

        coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy,
            router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute, claim_lease_ms=300)
        assert coordinator.tick() == 1
        assert renewed and all(renewed)
        count = len(renewed)
        time.sleep(0.15)
        assert len(renewed) == count
        assert store.get_task(task_id).status == "READY_FOR_REVIEW_FIXTURE"
    finally:
        store._conn.close()


@pytest.mark.parametrize("raises", [False, True])
def test_failed_claim_renewal_is_logged_and_stops(tmp_path, monkeypatch, caplog, raises):
    import time

    calls = []
    def renew(**kwargs):
        calls.append(kwargs)
        if raises:
            raise TaskStoreError("fixture_fenced")
        return False

    coordinator = UnattendedCoordinator(store=None, control_store=SimpleNamespace(renew_claim=renew),
        autonomy=None, router=ExecutorRouter(), workspace_root=tmp_path, claim_lease_ms=30)
    def execute(task_id):
        time.sleep(0.12)
        return "finished"
    monkeypatch.setattr(coordinator, "_execute_task", execute)
    assert coordinator._execute_with_claim_renewal("window", "task", 1) == "finished"
    assert len(calls) == 1
    assert "claim renewal" in caplog.text


def test_parallel_batch_execution_intervals_overlap_in_recorded_evidence(tmp_path):
    """#1267 evidence basis: prove interval overlap from platform timestamps.

    The barrier proves the two executors were genuinely running at the same
    wall-clock moment; the interval markers are written through the store's own
    event log (its created_at is host-owned, not test-supplied), so the
    overlap holds in recorded evidence, not just in the test's own clocks.
    """
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "parallel-intervals", "policy_revision": 1,
        "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = _parallel_goal(goals, window.id, key="parallel-interval-evidence")
    barrier = threading.Barrier(2)

    def execute(task_id):
        store.add_event(task_id, event_type="EXECUTOR_RUNNING",
                        title="fixture interval start", metadata={"executor_kind": "deterministic_fixture"})
        barrier.wait(timeout=10)
        # Hold the overlap across a second boundary: store timestamps have
        # one-second resolution, so the proof needs the earlier task's
        # recorded finish to land in a strictly later second.
        time.sleep(1.2)
        result = _ready_fixture(store, task_id)
        store.add_event(task_id, event_type="EXECUTOR_FINISHED",
                        title="fixture interval end", metadata={"executor_kind": "deterministic_fixture"})
        return result

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path, task_executor=execute,
    )
    assert coordinator.tick() == 2
    assert control.get_goal(goal.id).status == "COMPLETED"
    intervals = {}
    for link in control.list_goal_tasks(goal.id):
        task_id = link["task_id"]
        events = store.get_events(task_id)
        starts = [e.timestamp for e in events if e.type == "EXECUTOR_RUNNING"]
        ends = [e.timestamp for e in events if e.type == "EXECUTOR_FINISHED"]
        assert len(starts) == 1 and len(ends) == 1, events
        intervals[task_id] = (starts[0], ends[0])
    (first_start, first_end), (second_start, second_end) = sorted(intervals.values())
    # Recorded overlap: the later task started strictly before the earlier
    # task's recorded finish — impossible under serial dispatch.
    assert second_start < first_end, intervals




def _redeploy_stranded(tmp_path, *, old_sha="old-authority-sha", old_planning="old-planning-sha",
                       new_sha="new-authority-sha", new_planning="new-planning-sha"):
    """An INTERRUPTED task whose durable run started under the pre-redeploy code (#1515)."""
    store = TaskStore(str(tmp_path / "redeploy.sqlite3"))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "redeploy", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"],
        "capabilities": ["execute_task", "resume_task"],
        "max_concurrent_tasks": 1, "max_tasks": 10, "max_retries": 1,
        "confirmation": "ACTIVATE",
    })
    goal = goals.create({
        "objective": "Survive a redeploy", "idempotency_key": "redeploy-goal",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "Work", "instruction": "Run"}])
    goals.approve(goal.id, expected_revision=1)
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    task = store.get_task(task_id)
    store._acquire_durable_lease(
        task_id=task_id, execution_id=task.execution_id, lease_owner="old-host",
        execution_authority_sha=old_sha, planning_sha=old_planning, task_status="QUEUED",
    )
    # The host restarted (redeployed); the lease expired and the task is INTERRUPTED.
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = 1 WHERE task_id = ?", (task_id,))
    store.set_state(task_id, "INTERRUPTED")
    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy,
        router=ExecutorRouter(), workspace_root=tmp_path / "workspaces",
        execution_authority_sha=new_sha, planning_sha=new_planning, owner="new-host",
    )
    return store, control, coordinator, task_id


def _claim_status(store, task_id):
    row = store._conn.execute(
        "SELECT status FROM platform_coordinator_claims WHERE task_id = ?", (task_id,)).fetchone()
    return None if row is None else row["status"]


def test_redeploy_authority_mismatch_closes_the_attempt_as_host_version_changed(tmp_path):
    """#1515: the resume keeps refusing on the old authority SHA, but the attempt is
    closed as FAILED host_version_changed (a host fault) instead of being stranded."""
    store, _control, coordinator, task_id = _redeploy_stranded(tmp_path)
    assert coordinator.tick() == 1
    final = store.get_task(task_id)
    assert final.status == "FAILED"
    assert final.failure_classification == "host_version_changed"
    assert (final.failure_detail or "").startswith("authority_sha_mismatch:")
    # The claim was settled through the normal completion path, not abandoned.
    assert _claim_status(store, task_id) == "COMPLETE"
    [event] = [e for e in store.get_events(task_id) if e.type == "EXECUTOR_FINISHED"]
    assert event.metadata["failure_classification"] == "host_version_changed"
    # The closed attempt is terminal; a second tick does not busy-loop it.
    assert coordinator.tick() == 0
    assert store.get_task(task_id).status == "FAILED"


def test_redeploy_planning_mismatch_is_also_a_host_version_change(tmp_path):
    """#1515 names any version/identity mismatch: a changed planning SHA closes the attempt too."""
    store, _control, coordinator, task_id = _redeploy_stranded(
        tmp_path, old_sha="same-sha", new_sha="same-sha")
    assert coordinator.tick() == 1
    final = store.get_task(task_id)
    assert final.status == "FAILED" and final.failure_classification == "host_version_changed"
    assert (final.failure_detail or "").startswith("planning_sha_mismatch:")


def test_redeploy_recovery_does_not_swallow_other_resume_refusals(tmp_path, monkeypatch):
    """Only host-version refusals are recovered; any other resume refusal still strands as before."""
    from reverse_agent.platform_v1.durable_execution import DurableResumeError, DurableExecutionService
    store, _control, coordinator, task_id = _redeploy_stranded(
        tmp_path, old_sha="same-sha", old_planning="same-sha", new_sha="same-sha", new_planning="same-sha")

    def refuse(self, task_id, *, lease_owner="", **kwargs):
        raise DurableResumeError("worktree_not_found:/gone")
    monkeypatch.setattr(DurableExecutionService, "resume_single", refuse)
    assert coordinator.tick() == 0
    assert store.get_task(task_id).status == "INTERRUPTED"
    assert _claim_status(store, task_id) != "ACTIVE"


@pytest.mark.parametrize("trace", ["none", "worktree", "checkpoint", "external_operation"])
def test_pre_dispatch_resume_refusal_closes_the_attempt_as_orphaned_preparation(tmp_path, monkeypatch, trace):
    """2026-11-17: a run a restart stopped before PRE_PLANNER has nothing to reconstruct.
    While nothing of it was dispatched the refusal closes the attempt, fenced like a
    redeploy close; with any trace of dispatch the refusal still strands as before."""
    from reverse_agent.platform_v1.durable_execution import DurableResumeError, DurableExecutionService
    store, _control, coordinator, task_id = _redeploy_stranded(
        tmp_path, old_sha="same-sha", old_planning="same-sha", new_sha="same-sha", new_planning="same-sha")
    run_id = store._conn.execute("SELECT run_id FROM durable_runs WHERE task_id = ?", (task_id,)).fetchone()[0]
    if trace == "worktree":
        store._conn.execute("UPDATE durable_runs SET worktree_prepared_at = 'now' WHERE run_id = ?", (run_id,))
    elif trace == "checkpoint":
        store._conn.execute("UPDATE durable_runs SET accepted_checkpoint = 'PRE_PLANNER' WHERE run_id = ?", (run_id,))
    elif trace == "external_operation":
        store._conn.execute(
            "INSERT INTO durable_external_operations (operation_id, run_id, task_id, operation_key, idempotency_key, "
            "request_digest, state, created_at, updated_at) VALUES ('op', ?, ?, 'k', 'i', 'd', 'SUCCESS', 'n', 'n')",
            (run_id, task_id))
    store._conn.commit()

    def refuse(self, task_id, *, lease_owner="", **kwargs):
        raise DurableResumeError(f"pre_pre_planner_no_reconstruction_path:{task_id}:accepted_checkpoint_empty_fail_closed")
    monkeypatch.setattr(DurableExecutionService, "resume_single", refuse)
    feedback = []
    monkeypatch.setattr(coordinator, "_report_account_feedback", lambda *a, **k: feedback.append(a))
    if trace != "none":
        assert coordinator.tick() == 0
        assert store.get_task(task_id).status == "INTERRUPTED"
        assert _claim_status(store, task_id) == "FAILED"
        return
    assert coordinator.tick() == 1
    final = store.get_task(task_id)
    assert (final.status, final.failure_classification) == ("FAILED", "orphaned_preparation")
    assert final.failure_detail.startswith("pre_pre_planner_no_reconstruction_path:")
    assert _claim_status(store, task_id) == "COMPLETE"
    [event] = [e for e in store.get_events(task_id) if e.type == "EXECUTOR_FINISHED"]
    assert event.metadata["failure_classification"] == "orphaned_preparation"
    assert feedback == []  # a host fault is not account evidence
    assert coordinator.tick() == 0


def test_free_host_resume_in_a_continuous_window_spends_no_retry(tmp_path):
    """#1538 / decision B: re-claiming a host-interrupted task in a continuous window is not
    gated by, and does not spend, retries_used; a resume that failed since, or a window
    with an expiry, still is."""
    store, control, _coordinator, task_id = _redeploy_stranded(tmp_path)
    window = control.active_window()
    store._conn.execute("UPDATE durable_runs SET recovery_classification = 'orphan_stale_lease' WHERE task_id = ?",
                        (task_id,))
    store._conn.execute("UPDATE platform_autonomous_windows SET retries_used = max_retries WHERE id = ?", (window.id,))
    store._conn.commit()
    # A window with an expiry: exhausted retries gate the INTERRUPTED task as before.
    assert task_id not in control.runnable_tasks(window.id, respect_attempt_limits=True)
    with pytest.raises(TaskStoreError, match="window_retry_budget_exhausted"):
        control.claim_task(window_id=window.id, task_id=task_id, owner="new-host", lease_ms=60_000)
    goal_id = control.goal_id_for_task(task_id)
    control.append_receipt(window_id=window.id, operation_type="owner_window_admission",
                           capability="execute_task", repository="dddd2024/reverse-agent", subject_id=goal_id,
                           decision="allowed", reason="test", input_payload={}, result="ok")
    from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
    store._conn.execute("UPDATE platform_operation_receipts SET operation_type = ?, confirmation_mode = ? "
                        "WHERE subject_id = ?", (OWNER_WINDOW_RECEIPT, OWNER_WINDOW_MODE, goal_id))
    store._conn.execute("UPDATE platform_autonomous_windows SET confirmation_mode = ?, expires_at = '' WHERE id = ?",
                        (OWNER_WINDOW_MODE, window.id))
    store._conn.commit()
    assert control.get_window(window.id).continuous
    assert task_id in control.runnable_tasks(window.id, respect_attempt_limits=True)
    before = control.get_window(window.id)
    epoch, after = control.claim_task(window_id=window.id, task_id=task_id, owner="new-host", lease_ms=60_000)
    assert (after.retries_used, after.tasks_started) == (before.retries_used, before.tasks_started)
    # That resume fails and abandons its claim: the next re-claim is a normal retry again.
    control.abandon_task_claim(window_id=window.id, task_id=task_id, owner="new-host", epoch=epoch,
                               reason="resume_refused")
    assert task_id not in control.runnable_tasks(window.id, respect_attempt_limits=True)
    with pytest.raises(TaskStoreError, match="window_retry_budget_exhausted"):
        control.claim_task(window_id=window.id, task_id=task_id, owner="new-host", lease_ms=60_000)


@pytest.mark.parametrize("successor", ["durable_resume", "claim_takeover", "re_leased"])
def test_redeploy_close_is_fenced_against_a_successor_that_won_the_race(tmp_path, monkeypatch, successor):
    """Review blocker on 952b366f: a successor that resumes, re-claims or re-runs the task
    between the coordinator's read and its close must never be overwritten as FAILED."""
    from reverse_agent.platform_v1.durable_execution import DurableResumeError, DurableExecutionService
    store, _control, coordinator, task_id = _redeploy_stranded(tmp_path)
    future_ms = int(time.time() * 1000) + 600000

    def resume_then_lose_the_race(self, task_id, *, lease_owner="", **kwargs):
        # The refusal is computed, then a successor wins before the close transaction.
        if successor == "durable_resume":
            store._conn.execute(
                "UPDATE durable_runs SET lease_owner = 'successor', lease_epoch = lease_epoch + 1, "
                "lease_expiry_ms = ? WHERE task_id = ?", (future_ms, task_id))
            store._conn.execute("UPDATE tasks SET status = 'RUNNING' WHERE id = ?", (task_id,))
        elif successor == "claim_takeover":
            store._conn.execute(
                "UPDATE platform_coordinator_claims SET owner = 'successor-host', epoch = epoch + 1 "
                "WHERE task_id = ?", (task_id,))
        else:
            # Re-leased by another owner (one durable run per task), status not yet moved.
            store._conn.execute(
                "UPDATE durable_runs SET lease_owner = 'successor', lease_epoch = lease_epoch + 1, "
                "lease_expiry_ms = ? WHERE task_id = ?", (future_ms, task_id))
        raise DurableResumeError("authority_sha_mismatch:old-authority-sha!=new-authority-sha")
    monkeypatch.setattr(DurableExecutionService, "resume_single", resume_then_lose_the_race)
    refusals = []
    close = coordinator._fail_redeploy_stranded_task

    def recording_close(*args, **kwargs):
        try:
            return close(*args, **kwargs)
        except TaskStoreError as exc:
            refusals.append(str(exc))
            raise
    monkeypatch.setattr(coordinator, "_fail_redeploy_stranded_task", recording_close)
    assert coordinator.tick() == 0  # the stale handler wrote nothing and abandoned its own claim
    final = store.get_task(task_id)
    assert final.failure_classification != "host_version_changed"
    assert final.status == ("RUNNING" if successor == "durable_resume" else "INTERRUPTED")
    assert not [e for e in store.get_events(task_id)
                if e.metadata.get("failure_classification") == "host_version_changed"]
    assert refusals and refusals[0].startswith(f"host_version_close_fenced:{task_id}:"), refusals


def test_redeploy_close_requires_the_callers_claim(tmp_path):
    """The close is only made under the executing worker's own claim identity."""
    store, _control, coordinator, task_id = _redeploy_stranded(tmp_path)
    with pytest.raises(TaskStoreError, match="host_version_close_unfenced"):
        coordinator._fail_redeploy_stranded_task(task_id, detail="authority_sha_mismatch:x!=y",
                                                 observed=coordinator._latest_durable_run_identity(task_id))
    assert store.get_task(task_id).status == "INTERRUPTED"


def _failed_and_queued_fixture(tmp_path, *, failed_count=1):
    store = TaskStore(str(tmp_path / "coordinator.sqlite3"))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(store=store, control_store=control)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "nonblocking-startup-sweep", "policy_revision": 1, "owner_identity": "owner",
        "starts_at": (now - timedelta(seconds=2)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/reverse-agent"], "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1, "max_tasks": 10, "max_retries": 1, "confirmation": "ACTIVATE",
    })
    for idx in range(failed_count):
        goal = goals.create({
            "objective": f"Failed goal {idx}", "idempotency_key": f"failed-goal-{idx}",
            "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
        })
        goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "failed", "instruction": "fail"}])
        goals.approve(goal.id, expected_revision=1)
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
        failed_task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='deterministic_validation_failure' WHERE id=?",
            (failed_task_id,),
        )
    queued_goal = goals.create({
        "objective": "Runnable goal", "idempotency_key": "runnable-goal",
        "executor_kind": "deterministic_fixture", "orchestration_mode": "single",
    })
    goals.plan(queued_goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "run", "instruction": "run"}])
    goals.approve(queued_goal.id, expected_revision=1)
    goals.launch(queued_goal.id, expected_revision=1, window_id=window.id)
    store._conn.commit()
    return store, control, autonomy


def test_start_returns_before_slow_first_escalation_sweep_and_sweeps_before_first_dispatch(tmp_path):
    store, control, autonomy = _failed_and_queued_fixture(tmp_path, failed_count=1)
    order: list[str] = []
    order_lock = threading.Lock()
    sweep_entered = threading.Event()
    allow_finish = threading.Event()
    dispatched_done = threading.Event()

    def escalator(_goal_id: str) -> tuple:
        with order_lock:
            order.append("sweep_start")
        sweep_entered.set()
        allow_finish.wait(timeout=10.0)
        with order_lock:
            order.append("sweep_end")
        return ()

    def execute(task_id: str):
        with order_lock:
            order.append("dispatch")
        result = _ready_fixture(store, task_id)
        dispatched_done.set()
        return result

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path / "workspaces", goal_escalator=escalator,
        task_executor=execute, poll_interval=0.05,
    )
    try:
        started_at = time.monotonic()
        coordinator.start()
        assert time.monotonic() - started_at < 2.0
        assert sweep_entered.wait(timeout=5.0)
        status = coordinator.status()
        assert status["enabled"] is True
        assert status["lifecycle"] == "RECOVERING"
        assert status["recovering"] is True
        assert status["accepting_work"] is False
        assert status["ticks"] == 0
        assert coordinator.tick() == 0
        assert coordinator.tick(background=True) == 0
        with order_lock:
            assert "dispatch" not in order

        allow_finish.set()
        assert dispatched_done.wait(timeout=5.0)
        deadline = time.monotonic() + 2.0
        while coordinator.status()["recovering"] and time.monotonic() < deadline:
            time.sleep(0.02)
        with order_lock:
            assert order[:3] == ["sweep_start", "sweep_end", "dispatch"]
        running = coordinator.status()
        assert running["lifecycle"] == "RUNNING"
        assert running["recovering"] is False
        assert running["accepting_work"] is True
    finally:
        allow_finish.set()
        coordinator.stop(timeout=5.0)
        store._conn.close()


def test_stop_during_startup_sweep_halts_remaining_goals_without_dispatch(tmp_path):
    store, control, autonomy = _failed_and_queued_fixture(tmp_path, failed_count=2)
    swept: list[str] = []
    dispatched: list[str] = []
    sweep_entered = threading.Event()
    allow_finish = threading.Event()

    def escalator(goal_id: str) -> tuple:
        swept.append(goal_id)
        sweep_entered.set()
        allow_finish.wait(timeout=10.0)
        return ()

    def execute(task_id: str):
        dispatched.append(task_id)
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store, control_store=control, autonomy=autonomy, router=ExecutorRouter(),
        workspace_root=tmp_path / "workspaces", goal_escalator=escalator,
        task_executor=execute, poll_interval=0.05,
    )
    stopper = None
    try:
        coordinator.start()
        assert sweep_entered.wait(timeout=5.0)
        stopper = threading.Thread(target=lambda: coordinator.stop(timeout=5.0), daemon=True)
        stopper.start()
        deadline = time.monotonic() + 2.0
        while not coordinator._stop.is_set() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert coordinator._stop.is_set()
        draining = coordinator.status()
        assert draining["lifecycle"] == "DRAINING"
        assert draining["recovering"] is False
        allow_finish.set()
        stopper.join(timeout=5.0)
        assert not stopper.is_alive()
        assert len(swept) == 1
        assert dispatched == []
        stopped = coordinator.status()
        assert stopped["lifecycle"] == "STOPPED"
        assert stopped["recovering"] is False
    finally:
        allow_finish.set()
        coordinator.stop(timeout=5.0)
        if stopper is not None:
            stopper.join(timeout=2.0)
        store._conn.close()


def _backoff_sweep_case(monkeypatch, *, two_steps: bool = False):
    from reverse_agent.platform_v1 import goal_service as gs
    from reverse_agent.platform_v1 import unattended_coordinator as uc

    wall = [1_800_000_000.0]
    mono = [1000.0]
    monkeypatch.setattr(gs.time, "time", lambda: wall[0])
    monkeypatch.setattr(uc.time, "monotonic", lambda: mono[0])
    monkeypatch.setattr(gs, "resolve_repository_workspace", lambda repository: object())
    monkeypatch.setattr(gs, "repository_base", lambda repository: "b" * 40)

    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(
        store=store,
        control_store=control,
        task_resolver=lambda plan_task, *, goal, **kw: {
            "binding_ref": "bind-a",
            "executor_kind": "opencode",
            "model_id": "m/a",
            "tier": 3,
            "reason": "fixture",
            "context_window": 128000,
        },
    )
    plan_tasks = [{"id": "T001", "title": "Step 1", "instruction": "Step 1", "agent_role": "coder"}]
    if two_steps:
        plan_tasks.append({"id": "T002", "title": "Step 2", "instruction": "Step 2", "agent_role": "coder"})
    goal = goals.create({
        "objective": "Backoff sweep scheduling",
        "repository": "dddd2024/Nerelan",
        "idempotency_key": f"sweep-backoff-{two_steps}",
        "executor_kind": "opencode",
        "orchestration_mode": "agent_team",
        "binding_ref": "",
    })
    goals.plan(goal.id, expected_revision=1, tasks=plan_tasks)
    goals.approve(goal.id, expected_revision=1)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "continuous-sweep-test",
        "policy_revision": 1,
        "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 2,
        "max_tasks": 10,
        "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    control.append_receipt(
        window_id=window.id,
        operation_type="owner_window_admission",
        capability="execute_task",
        repository="dddd2024/Nerelan",
        subject_id=goal.id,
        decision="allowed",
        reason="test",
        input_payload={},
        result="ok",
    )
    from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
    store._conn.execute(
        "UPDATE platform_operation_receipts SET operation_type = ?, confirmation_mode = ? WHERE subject_id = ?",
        (OWNER_WINDOW_RECEIPT, OWNER_WINDOW_MODE, goal.id),
    )
    store._conn.execute(
        "UPDATE platform_autonomous_windows SET confirmation_mode = ?, expires_at = '' WHERE id = ?",
        (OWNER_WINDOW_MODE, window.id),
    )
    store._conn.commit()

    calls: list[str] = []

    def escalator(gid: str) -> tuple:
        calls.append(gid)
        return goals.escalate_failed_tasks(gid)

    coordinator = uc.UnattendedCoordinator.__new__(uc.UnattendedCoordinator)
    coordinator.control_store = control
    coordinator._last_error = ""
    coordinator.goals = goals
    coordinator.goal_escalator = escalator

    def advance(seconds: float) -> None:
        wall[0] += seconds
        mono[0] += seconds

    def link_task(plan_task_id: str) -> str:
        return next(
            row["task_id"] for row in control.list_goal_tasks(goal.id)
            if row["plan_task_id"] == plan_task_id
        )

    return store, control, goals, goal, coordinator, wall, calls, advance, link_task, uc, gs


def test_sweep_reexamines_patient_429_on_first_tick_after_backoff_expiry(monkeypatch):
    store, _, goals, goal, coordinator, wall, calls, advance, link_task, _, gs = _backoff_sweep_case(monkeypatch)
    try:
        monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
        task_id = link_task("T001")
        age = datetime.fromtimestamp(wall[0] - (gs.TRANSIENT_BACKOFF_SECONDS - 30.0), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
            "failure_detail='opencode_server:api_error_429', updated_at=? WHERE id=?",
            (age, task_id),
        )
        store._conn.commit()

        coordinator._sweep_escalations()
        assert len(calls) == 1
        assert goals.next_backoff_delay(goal.id) == pytest.approx(30.0)
        assert link_task("T001") == task_id

        advance(15.0)
        coordinator._sweep_escalations()
        assert len(calls) == 1  # still inside 30 s backoff

        advance(16.0)  # 31 s after initial sweep: 1 s past backoff expiry
        coordinator._sweep_escalations()
        assert len(calls) == 2
        replacement = link_task("T001")
        assert replacement != task_id
        assert store.get_task(replacement).status == "QUEUED"
        assert goals.next_backoff_delay(goal.id) is None
    finally:
        store._conn.close()


def test_sweep_reexamines_stalled_step_after_backoff_and_clamps_long_backoff(monkeypatch):
    store, _, goals, goal, coordinator, wall, calls, advance, link_task, uc, gs = _backoff_sweep_case(monkeypatch)
    try:
        monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
        goals.roster_resolver = lambda role: ("opencode", "bind-a")
        goals.task_resolver = None  # same binding resumes once backoff expires
        task_id = link_task("T001")
        # 30 s remaining on a 120 s stall backoff.
        age_30 = datetime.fromtimestamp(wall[0] - (gs.TRANSIENT_BACKOFF_SECONDS - 30.0), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='server_stream_stalled', "
            "failure_detail='opencode_server:server_stream_stalled', updated_at=? WHERE id=?",
            (age_30, task_id),
        )
        store._conn.commit()

        coordinator._sweep_escalations()
        assert len(calls) == 1
        assert goals.next_backoff_delay(goal.id) == pytest.approx(30.0)
        advance(31.0)
        coordinator._sweep_escalations()
        assert len(calls) == 2
        second_task = link_task("T001")
        assert second_task != task_id

        # A backoff longer than SWEEP_REPEAT_SECONDS (2000 s left) clamps to 900 s upper bound.
        monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 2500)
        age_2000 = datetime.fromtimestamp(wall[0] - 500.0, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
            "failure_detail='opencode_server:api_error_429', updated_at=? WHERE id=?",
            (age_2000, second_task),
        )
        store._conn.commit()

        coordinator._sweep_escalations()
        assert len(calls) == 3
        # Second retry (free_used=1): 2500 * 2**1 - 500 = 4500 s remaining, clamped to 900 s.
        assert goals.next_backoff_delay(goal.id) == pytest.approx(4500.0)

        advance(uc.SWEEP_REPEAT_SECONDS - 1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 3

        advance(1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 4
        assert link_task("T001") == second_task
    finally:
        store._conn.close()


def test_sweep_keeps_repeat_interval_for_unroutable_and_earliest_for_mixed_steps(monkeypatch):
    store, _, goals, goal, coordinator, wall, calls, advance, link_task, uc, gs = _backoff_sweep_case(
        monkeypatch, two_steps=True
    )
    try:
        # Both steps initially unroutable / held -> SWEEP_REPEAT_SECONDS applies without event spam.
        t1 = link_task("T001")
        t2 = link_task("T002")
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', updated_at='2026-11-22T00:00:00Z' WHERE id=?",
            (t1,),
        )
        store._conn.execute("UPDATE tasks SET status='BLOCKED' WHERE id=?", (t2,))
        store._conn.commit()

        def no_model(*args, **kwargs):
            raise TaskStoreError("no_runnable_model")

        goals.task_resolver = no_model
        coordinator._sweep_escalations()
        assert len(calls) == 1
        assert goals.next_backoff_delay(goal.id) is None
        assert len([e for e in store.get_events(t1) if e.type == "MODEL_SELECTION_FAILED"]) == 1

        # Sweep 2 sees t1.updated_at updated by Sweep 1; after that, unchanged tasks wait 900 s.
        advance(10.0)
        coordinator._sweep_escalations()
        assert len(calls) == 2
        advance(uc.SWEEP_REPEAT_SECONDS - 1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 2
        advance(1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 3
        assert len([e for e in store.get_events(t1) if e.type == "MODEL_SELECTION_FAILED"]) == 1

        # Mixed goal: T001 held BLOCKED, T002 has a 30 s patient backoff -> wakes at 30 s for T002.
        monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
        goals.task_resolver = lambda plan_task, *, goal, **kw: {
            "binding_ref": "bind-a",
            "executor_kind": "opencode",
            "model_id": "m/a",
            "tier": 3,
            "reason": "fixture",
            "context_window": 128000,
        }
        store._conn.execute("UPDATE tasks SET status='BLOCKED' WHERE id=?", (t1,))
        age_30 = datetime.fromtimestamp(wall[0] - (gs.TRANSIENT_BACKOFF_SECONDS - 30.0), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        store._conn.execute(
            "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
            "failure_detail='opencode_server:api_error_429', updated_at=? WHERE id=?",
            (age_30, t2),
        )
        store._conn.commit()

        coordinator._sweep_escalations()
        assert len(calls) == 4
        assert goals.next_backoff_delay(goal.id) == pytest.approx(30.0)

        advance(29.0)
        coordinator._sweep_escalations()
        assert len(calls) == 4

        advance(2.0)  # 31 s: T002 escalates to QUEUED, leaving only held T001
        coordinator._sweep_escalations()
        assert len(calls) == 5
        assert link_task("T002") != t2
        assert goals.next_backoff_delay(goal.id) is None

        # Next sweep observes the smaller stuck set ([T001] only) once and settles on 900 s.
        advance(1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 6
        assert goals.next_backoff_delay(goal.id) is None

        # Only held T001 remains -> next sweep waits the full SWEEP_REPEAT_SECONDS.
        advance(uc.SWEEP_REPEAT_SECONDS - 1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 6
        advance(1.0)
        coordinator._sweep_escalations()
        assert len(calls) == 7
    finally:
        store._conn.close()


def test_live_coordinator_runs_due_backoff_sweep_before_reconcile_interval(tmp_path, monkeypatch):
    from reverse_agent.platform_v1 import goal_service as gs

    monkeypatch.setattr(gs, "MAX_TRANSIENT_RETRIES", 0)
    monkeypatch.setattr(gs, "TRANSIENT_BACKOFF_SECONDS", 1)
    monkeypatch.setattr(gs, "resolve_repository_workspace", lambda repository: object())
    monkeypatch.setattr(gs, "repository_base", lambda repository: "b" * 40)

    store = TaskStore(str(tmp_path / "live_backoff.sqlite3"))
    control = PlatformControlStore(store)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry())
    goals = GoalService(
        store=store,
        control_store=control,
        task_resolver=lambda plan_task, *, goal, **kw: {
            "binding_ref": "bind-a",
            "executor_kind": "opencode",
            "model_id": "m/a",
            "tier": 3,
            "reason": "fixture",
            "context_window": 128000,
        },
    )
    goal = goals.create({
        "objective": "Live backoff wake",
        "repository": "dddd2024/Nerelan",
        "idempotency_key": "live-backoff-wake",
        "executor_kind": "opencode",
        "orchestration_mode": "agent_team",
        "binding_ref": "",
    })
    goals.plan(goal.id, expected_revision=1, tasks=[{"id": "T001", "title": "Step", "instruction": "Step", "agent_role": "coder"}])
    goals.approve(goal.id, expected_revision=1)
    now = datetime.now(timezone.utc)
    window = autonomy.activate({
        "policy_id": "live-backoff-window",
        "policy_revision": 1,
        "owner_identity": "owner@example",
        "starts_at": (now - timedelta(seconds=5)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "repositories": ["dddd2024/Nerelan"],
        "capabilities": ["execute_task"],
        "max_concurrent_tasks": 1,
        "max_tasks": 10,
        "max_retries": 0,
        "confirmation": "ACTIVATE",
    })
    goals.launch(goal.id, expected_revision=1, window_id=window.id)
    control.append_receipt(
        window_id=window.id,
        operation_type="owner_window_admission",
        capability="execute_task",
        repository="dddd2024/Nerelan",
        subject_id=goal.id,
        decision="allowed",
        reason="test",
        input_payload={},
        result="ok",
    )
    from reverse_agent.platform_v1.control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
    store._conn.execute(
        "UPDATE platform_operation_receipts SET operation_type = ?, confirmation_mode = ? WHERE subject_id = ?",
        (OWNER_WINDOW_RECEIPT, OWNER_WINDOW_MODE, goal.id),
    )
    store._conn.execute(
        "UPDATE platform_autonomous_windows SET confirmation_mode = ?, expires_at = '' WHERE id = ?",
        (OWNER_WINDOW_MODE, window.id),
    )
    store._conn.commit()

    first_task = control.list_goal_tasks(goal.id)[0]["task_id"]
    # Failed at current second -> 1 s backoff expires in ~1 s, well before 60 s reconcile_interval.
    recent = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    store._conn.execute(
        "UPDATE tasks SET status='FAILED', failure_classification='api_error_429', "
        "failure_detail='opencode_server:api_error_429', updated_at=? WHERE id=?",
        (recent, first_task),
    )
    store._conn.commit()

    dispatched = threading.Event()

    def fake_execute(task_id: str):
        if task_id != first_task:
            dispatched.set()
        return _ready_fixture(store, task_id)

    coordinator = UnattendedCoordinator(
        store=store,
        control_store=control,
        autonomy=autonomy,
        router=ExecutorRouter(),
        workspace_root=tmp_path / "workspaces",
        goal_escalator=goals.escalate_failed_tasks,
        goals=goals,
        task_executor=fake_execute,
        poll_interval=0.1,
        reconcile_interval=60.0,
    )
    try:
        coordinator.start()
        assert dispatched.wait(timeout=5.0)
        replacement = control.list_goal_tasks(goal.id)[0]["task_id"]
        assert replacement != first_task
    finally:
        coordinator.stop(timeout=5.0)
        store._conn.close()
