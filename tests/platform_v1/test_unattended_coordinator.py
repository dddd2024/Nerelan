from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
import threading
import subprocess
from types import SimpleNamespace

import pytest

from reverse_agent.platform_v1.autonomy import AutonomyService
from reverse_agent.platform_v1.capability_registry import CapabilityRegistry
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter
from reverse_agent.platform_v1.unattended_coordinator import UnattendedCoordinator


def _real_checker_fixture(tmp_path, monkeypatch, *, reopen=False):
    """Synthetic authority loader plus actual Git/checker, durable DB and coordinator."""
    from reverse_agent.platform_v1.authority_adapter import PolicyAuthority
    from reverse_agent.platform_v1.autonomy import policy_digest
    from reverse_agent.platform_v1.task_runtime import load_host_validation_contract
    root = tmp_path / "repository"
    database = tmp_path / "checker.sqlite3"
    if not reopen:
        root.mkdir()
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        for name, value in (("core.autocrlf", "false"), ("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                            ("remote.origin.url", "https://github.com/dddd2024/Nerelan.git")):
            subprocess.run(["git", "-C", str(root), "config", name, value], check=True)
        (root / "input.txt").write_bytes(b"baseline\n")
        subprocess.run(["git", "-C", str(root), "add", "input.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m", "fixture"], check=True, capture_output=True)
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    monkeypatch.setenv("REVERSE_AGENT_REPO_DIR", str(root))
    store = TaskStore(str(database))
    control = PlatformControlStore(store)
    if reopen:
        saved = control.window_policy_binding("checker-window")
        policy = saved["canonical_policy"]
        authority_binding = saved["authority"]
    else:
        now = datetime.now(timezone.utc)
        quotas = {name: 0 for name in ("maxPrsOpened", "maxMergesToMain", "maxReleasesCreated", "maxDeploysToEnvironment")}
        policy = {"mode": "CONTROLLER_REVIEW", "repository": "dddd2024/Nerelan",
            "resourceAccess": {"filesystem": {"allowedPaths": ["input.txt"], "writablePaths": []},
                "network": {"allowedDomains": [], "allowWrite": False},
                "shell": {"allowedCommands": ["git_diff_check"], "deniedCommands": []},
                "secrets": {"access": "none", "allowedKeys": []},
                "workerApproval": {"required": False, "approvers": []}},
            "githubCapabilities": [], "publicationCapabilities": [],
            "publicationPolicy": {"allowedArtifactOrPackage": [], "allowedRegistry": [],
                "allowedRepository": [], "allowedEnvironment": []},
            "mergePolicy": {"allowedRepositories": [], "allowedBaseBranches": [], "requiredChecks": [],
                "allowedMergeMethods": [], "requireExactHead": True},
            "autonomousWindow": {"enabled": True, "startsAt": (now - timedelta(seconds=2)).isoformat(),
                "expiresAt": (now + timedelta(hours=1)).isoformat(), **quotas,
                "stopConditions": [{"type": "window_expired", "scope": "window"}]}, "budgets": dict(quotas)}
        authority_binding = {"schema_version": 1, "confirmation_mode": "DELEGATED_CONTROLLER",
            "personally_human": False, "controller_identity": "fixture-controller",
            "upper_proposal_sha256": "a" * 64, "upper_expires_at": (now + timedelta(hours=2)).isoformat(),
            "phase_ordinal": 6, "policy_id": "checker-policy", "policy_revision": 1, "policy": policy,
            "policy_digest_sha256": policy_digest(policy), "window_id": "checker-window",
            "delegation_slot_id": "checker-slot", "slot_ordinal": 1, "max_real_window_activations": 1,
            "host_instance_id": "fixture-host", "runtime_instance_kind": "acceptance",
            "database_path": str(database), "workspace_path": str(root), "allowed_operations": ["validate_task"],
            "validation_command_ids": ["git_diff_check"], "validation_paths": ["input.txt"], "max_tasks": 1,
            "max_retries": 0, "max_concurrent_tasks": 1, "model_call_limit": 0, "provider_call_limit": 0,
            "github_write_limit": 0, "goal_idempotency_key": "checker-goal", "plan_task_id": "CHECK001"}
    authority = PolicyAuthority("decision_fixture", "round_fixture", "b" * 64, head,
        "c" * 64, "dddd2024/Nerelan", "codex/fixture", head, head, authority_binding)
    autonomy = AutonomyService(control_store=control, capabilities=CapabilityRegistry(),
        authority_loader=lambda: authority, task_scope_resolver=lambda task_id: load_host_validation_contract(store.get_task(task_id)))
    goals = GoalService(store=store, control_store=control)
    if not reopen:
        window = autonomy.activate_policy({"policy_id": "checker-policy", "policy_revision": 1, "policy": policy})
        goal = goals.create({"objective": "Check pinned hygiene", "repository": "dddd2024/Nerelan",
            "idempotency_key": "checker-goal", "executor_kind": "opencode", "orchestration_mode": "single"})
        goals.plan(goal.id, expected_revision=1, tasks=[{"id": "CHECK001", "title": "Hygiene",
            "instruction": "Only check pinned paths", "capability": "validate_task", "validation_command_id": "git_diff_check"}])
        goals.approve(goal.id, expected_revision=1)
        goals.launch(goal.id, expected_revision=1, window_id=window.id)
    else:
        window = control.get_window("checker-window")
        goal = control.list_window_goals(window.id)[0]
    task_id = control.list_goal_tasks(goal.id)[0]["task_id"]
    router = ExecutorRouter()
    def forbidden(**kwargs):
        pytest.fail("Provider/model executor reached by host checker")
    monkeypatch.setattr(router, "create_executor", forbidden)
    monkeypatch.setattr(router, "dispatch_execute", forbidden)
    coordinator = UnattendedCoordinator(store=store, control_store=control, autonomy=autonomy, router=router,
        workspace_root=tmp_path / "workspaces", execution_authority_sha=head, planning_sha=head)
    return store, control, autonomy, goals, window, task_id, coordinator


def test_actual_host_checker_coordinator_finalizes_zero_model_usage_and_exact_receipt(tmp_path, monkeypatch):
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(tmp_path, monkeypatch)
    try:
        assert coordinator.tick() == 1
        task = store.get_task(task_id)
        assert task.status == "READY_FOR_REVIEW" and task.validation_exit_code == 0
        assert task.validation_command_id == "git_diff_check"
        observed = store.get_latest_durable_run_observation(task_id)
        assert observed.accepted_checkpoint == "POST_VALIDATION"
        final = control.get_window(window.id)
        assert (final.tasks_started, final.tasks_completed, final.retries_used) == (1, 1, 0)
        assert final.unknown_observation_count == 0
        assert (final.observed_token_units, final.observed_cost_micro_units) == (0, 0)
        receipts = control.list_receipts(window_id=window.id)
        completed = [row for row in receipts if row.operation_type == "task_execution"]
        assert len(completed) == 1 and completed[0].capability == "validate_task"
        assert completed[0].confirmation_mode == "DELEGATED_CONTROLLER"
        assert completed[0].actor == "fixture-controller"
        assert completed[0].policy_digest == final.policy_digest
        assert store.list_usage_observations(task_id) == ()
        assert coordinator.tick() == 0
        assert control.get_window(window.id).tasks_started == 1
    finally:
        store._conn.close()


@pytest.mark.parametrize("after_effect", [True, False])
def test_host_checker_reopen_only_completes_accepted_result_without_new_retry(tmp_path, monkeypatch, after_effect):
    from reverse_agent.platform_v1.task_runtime import LocalValidationRunner
    class AfterEffectCrash(BaseException):
        pass
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(tmp_path, monkeypatch)
    runs = []
    original_check = LocalValidationRunner.run
    original_transition = store._fenced_transition_to
    def observe_check(self, **kwargs):
        if not after_effect:
            raise AfterEffectCrash("fixture crash before checker")
        runs.append(kwargs["task_id"])
        return original_check(self, **kwargs)
    def crash_after_result(*args, **kwargs):
        if args[2] == "VALIDATING":
            assert store._get_durable_run(args[0]).accepted_checkpoint == "POST_VALIDATION"
            raise AfterEffectCrash("fixture crash after accepted checker result")
        return original_transition(*args, **kwargs)
    monkeypatch.setattr(LocalValidationRunner, "run", observe_check)
    if after_effect:
        monkeypatch.setattr(store, "_fenced_transition_to", crash_after_result)
    with pytest.raises(AfterEffectCrash):
        coordinator.tick()
    before = control.get_window(window.id)
    assert (before.tasks_started, before.tasks_completed, before.retries_used) == (1, 0, 0)
    observed = store.get_latest_durable_run_observation(task_id)
    assert observed.accepted_checkpoint == ("POST_VALIDATION" if after_effect else "POST_REVIEWER")
    original_run = store._get_durable_run(observed.run_id)
    assert original_run.lease_owner == coordinator.owner and original_run.lease_expiry_ms > 0
    # Simulate expiration of the original process's admission claim; never
    # rewrite spending, original result, policy, task identity or checkpoint.
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=1 WHERE task_id=?", (task_id,))
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms=1 WHERE task_id=?", (task_id,))
    store._conn.close()
    def forbidden_check(*args, **kwargs):
        pytest.fail("Recovery reran checker despite zero retry allowance")
    monkeypatch.setattr(LocalValidationRunner, "run", forbidden_check)
    reopened, next_control, next_autonomy, next_goals, next_window, same_task_id, restarted = _real_checker_fixture(
        tmp_path, monkeypatch, reopen=True)
    try:
        assert same_task_id == task_id and next_window.id == window.id
        restarted.reconcile()
        assert reopened.get_task(task_id).status == "INTERRUPTED"
        assert restarted.tick() == (1 if after_effect else 0)
        final = next_control.get_window(window.id)
        assert (final.tasks_started, final.tasks_completed, final.retries_used) == (1, 1 if after_effect else 0, 0)
        assert reopened.get_task(task_id).status == ("READY_FOR_REVIEW" if after_effect else "INTERRUPTED")
        assert len(runs) == (1 if after_effect else 0)
        assert reopened._conn.execute("SELECT COUNT(*) FROM durable_runs WHERE task_id=?", (task_id,)).fetchone()[0] == 1
        assert reopened.list_usage_observations(task_id) == ()
        if after_effect:
            complete = [row for row in next_control.list_receipts(window_id=window.id)
                        if row.reason == "coordinator_claim_completed"]
            assert len(complete) == 1 and complete[0].capability == "validate_task"
            assert final.unknown_observation_count == 0
        assert restarted.tick() == 0
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("checker_passes", [True, False])
def test_terminal_host_effect_reopen_finalizes_original_claim_without_checker_or_counter_reset(
    tmp_path, monkeypatch, checker_passes
):
    from reverse_agent.platform_v1.task_runtime import LocalValidationRunner
    class BeforeClaimCompletionCrash(BaseException):
        pass
    store, control, autonomy, goals, window, task_id, coordinator = _real_checker_fixture(tmp_path, monkeypatch)
    if not checker_passes:
        (tmp_path / "repository" / "input.txt").write_bytes(b"actual trailing whitespace  \n")
    actual_checks = []
    original_check = LocalValidationRunner.run
    def observed_check(self, **kwargs):
        actual_checks.append(kwargs["task_id"])
        return original_check(self, **kwargs)
    def crash_before_claim_completion(**kwargs):
        assert kwargs["task_id"] == task_id
        actual = store.get_latest_durable_run_observation(task_id)
        assert actual.accepted_checkpoint == "POST_VALIDATION"
        raise BeforeClaimCompletionCrash("fixture producer exited before admission receipt")
    monkeypatch.setattr(LocalValidationRunner, "run", observed_check)
    monkeypatch.setattr(control, "complete_task_claim", crash_before_claim_completion)
    with pytest.raises(BeforeClaimCompletionCrash):
        coordinator.tick()
    terminal = store.get_task(task_id)
    expected_status = "READY_FOR_REVIEW" if checker_passes else "FAILED"
    assert terminal.status == expected_status
    assert (terminal.validation_exit_code == 0) is checker_passes
    preserved_result = (terminal.validation_command_id, terminal.validation_exit_code, terminal.validation_output_digest)
    before = control.get_window(window.id)
    assert (before.tasks_started, before.tasks_completed, before.retries_used) == (1, 0, 0)
    assert actual_checks == [task_id]
    claim = store._conn.execute("SELECT * FROM platform_coordinator_claims WHERE task_id=?", (task_id,)).fetchone()
    original_epoch = claim["epoch"]
    assert claim["status"] == "ACTIVE"
    # Only the original admission lease timer expires. Terminal checker/run
    # result and all spending remain exactly as the first producer wrote them.
    store._conn.execute("UPDATE platform_coordinator_claims SET expires_at_ms=1 WHERE task_id=?", (task_id,))
    store._conn.close()
    def forbidden_check(*args, **kwargs):
        pytest.fail("Terminal-effect recovery reran checker")
    monkeypatch.setattr(LocalValidationRunner, "run", forbidden_check)
    reopened, resumed_control, resumed_autonomy, resumed_goals, same_window, same_task, restarted = _real_checker_fixture(
        tmp_path, monkeypatch, reopen=True)
    monkeypatch.setattr(restarted, "_execute_task", forbidden_check)
    try:
        restarted.reconcile()
        assert same_task == task_id and same_window.id == window.id
        linked_goal = resumed_control.list_window_goals(window.id)[0]
        # An ordinary history read can already reconcile the Goal from the
        # terminal Task. That read must not hide the unfinished original claim.
        assert resumed_goals.detail(linked_goal.id)["status"] == ("COMPLETED" if checker_passes else "BLOCKED")
        assert restarted.tick() == 1
        final = reopened.get_task(task_id)
        assert final.status == expected_status
        assert (final.validation_command_id, final.validation_exit_code, final.validation_output_digest) == preserved_result
        budget = resumed_control.get_window(window.id)
        assert (budget.tasks_started, budget.tasks_completed, budget.retries_used) == (1, 1, 0)
        assert budget.unknown_observation_count == 0
        assert reopened.list_usage_observations(task_id) == ()
        done = reopened._conn.execute("SELECT * FROM platform_coordinator_claims WHERE task_id=?", (task_id,)).fetchone()
        assert done["status"] == "COMPLETE" and done["epoch"] == original_epoch + 1
        receipts = [row for row in resumed_control.list_receipts(window_id=window.id)
                    if row.reason == "coordinator_claim_completed"]
        assert len(receipts) == 1 and receipts[0].capability == "validate_task"
        goal = resumed_control.list_window_goals(window.id)[0]
        assert goal.status == ("COMPLETED" if checker_passes else "BLOCKED")
        assert restarted.tick() == 0 and actual_checks == [task_id]
        assert reopened._conn.execute("SELECT COUNT(*) FROM durable_runs WHERE task_id=?", (task_id,)).fetchone()[0] == 1
    finally:
        reopened._conn.close()


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
