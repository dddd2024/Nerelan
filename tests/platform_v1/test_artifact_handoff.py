"""Explicit artifact contracts and real producer/consumer acceptance."""
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from test_goal_functional_checks import goal_checks, planned_check
from test_functional_execution import LocalImplementation, durable, ordinary

from reverse_agent.platform_v1.artifact_handoff import normalize_input
from reverse_agent.platform_v1.goal_service import GoalService
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.functional_validation import functional_evidence, run_task_validation
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


def plan_task(task_id, *, dependencies=(), source=None, checks=True):
    return {"id": task_id, "title": task_id, "instruction": f"Perform {task_id}",
            "dependencies": list(dependencies), "artifact_input": source,
            "validation_checks": ([{"profile_id": "python_pytest", "working_directory": "."}]
                                  if checks else [])}


@pytest.mark.parametrize("value", ["A", [], {}, [{"plan_task_id": "A"}],
    {"plan_task_id": "A", "commit": "caller-selected"}, {"plan_task_id": ["A", "B"]},
    {"plan_task_id": None}, {"plan_task_id": 1}, {"plan_task_id": "../A"},
    {"plan_task_id": " A"}, {"plan_task_id": "A\n"}, {"plan_task_id": "A" * 41}])
def test_input_rejects_caller_objects_multiple_sources_and_invalid_ids(value):
    with pytest.raises(TaskStoreError, match="artifact_input_invalid"):
        normalize_input(value)


def test_input_is_an_explicit_closed_copy():
    assert normalize_input(None) is None
    source = {"plan_task_id": "T001"}
    actual = normalize_input(source)
    source["plan_task_id"] = "T002"
    assert actual == {"plan_task_id": "T001"}


@pytest.fixture
def goals(tmp_path):
    store = TaskStore(str(tmp_path / "handoff.sqlite3"))
    control = PlatformControlStore(store)
    service = GoalService(store=store, control_store=control)
    goal = service.create({"objective": "Implement and verify the same artifact",
                           "repository": "owner/artifact", "idempotency_key": "artifact-plan"})
    yield store, control, service, goal
    store._conn.close()


@pytest.mark.parametrize("producer,consumer,reason", [
    (plan_task("A"), plan_task("B", source={"plan_task_id": "A"}), "artifact_input_not_dependency"),
    (plan_task("A", checks=False), plan_task("B", dependencies=["A"], source={"plan_task_id": "A"}), "artifact_input_requires_functional_checks"),
    (plan_task("A"), plan_task("B", dependencies=["A"], source={"plan_task_id": "A"}, checks=False), "artifact_input_requires_functional_checks"),
    (plan_task("A"), plan_task("B", dependencies=["A"], source={"plan_task_id": "B"}), "artifact_input_not_dependency"),
    (plan_task("A"), plan_task("B", dependencies=["A"], source={"plan_task_id": "missing"}), "artifact_input_not_dependency"),
])
def test_invalid_input_cannot_enter_reviewable_plan(goals, producer, consumer, reason):
    store, control, service, goal = goals
    with pytest.raises(TaskStoreError, match=reason):
        service.plan(goal.id, expected_revision=goal.revision, tasks=[producer, consumer])
    assert control.get_goal(goal.id).status == "DRAFT"
    assert store.count_tasks() == 0


def test_selected_input_survives_sqlite_reopen_and_appears_in_review(goals):
    store, _, service, goal = goals
    selected = service.plan(goal.id, expected_revision=goal.revision, tasks=[plan_task("A"),
        plan_task("B", dependencies=["A"], source={"plan_task_id": "A"})]).goal
    assert selected.tasks[1]["artifact_input"] == {"plan_task_id": "A"}
    assert "Accepted artifact input: `A`" in selected.plan_markdown
    reopened = TaskStore(store.db_path)
    try:
        persisted = PlatformControlStore(reopened).get_goal(goal.id)
        assert persisted.tasks == selected.tasks
        assert persisted.artifact_digest == selected.artifact_digest
    finally:
        reopened._conn.close()


def test_order_only_dependency_does_not_infer_artifact_input(goals):
    _, _, service, goal = goals
    selected = service.plan(goal.id, expected_revision=goal.revision,
                           tasks=[plan_task("A", checks=False),
                                  plan_task("B", dependencies=["A"], checks=False)]).goal
    assert selected.tasks[1]["artifact_input"] is None
    assert "Accepted artifact input" not in selected.plan_markdown


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], encoding="utf-8").strip()


def export_task(fixture, mode="single", consumer_capability="validate_task"):
    root, base, store, control, service, goal, window = fixture
    if mode != goal.orchestration_mode:
        goal = service.amend(goal.id, expected_revision=goal.revision, objective=goal.objective,
                             orchestration_mode=mode)
    planned = service.plan(goal.id, expected_revision=goal.revision, tasks=[planned_check("A"),
        {**planned_check("B"), "dependencies": ["A"], "capability": consumer_capability,
         "artifact_input": {"plan_task_id": "A"}}]).goal
    service.approve(goal.id, expected_revision=planned.revision)
    service.launch(goal.id, expected_revision=planned.revision, window_id=window.id)
    return control.list_goal_tasks(goal.id)[0]["task_id"]


@pytest.mark.parametrize("engine,mode", [("ordinary", "single"), ("ordinary", "sequential_team"),
                                        ("durable", "single"), ("durable", "sequential_team")])
def test_real_uncommitted_output_retained_without_changing_head_or_index(goal_checks, tmp_path, engine, mode):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence
    root, base, store, *_ = goal_checks
    task_id = export_task(goal_checks, mode)
    executor = LocalImplementation(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    service = durable(store, router) if engine == "durable" else ordinary(store, router)
    method = getattr(service, "execute_durable_" + mode if engine == "durable" else
                     ("execute" if mode == "single" else "execute_sequential_team"))
    outcome = method(task_id, workspace_root=str(tmp_path / "worktrees"))
    assert outcome.success is True, outcome
    task = store.get_task(task_id)
    proof = functional_evidence(task)
    binding = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
    assert proof["verified"] is True and proof["checks"][0]["test_report"]["tests"] == 1
    assert binding["result_digest"] == proof["result_digest"]
    assert binding["base_commit"] == base and binding["tree"] == proof["tree"]
    assert git(root, "show", f"{binding['commit']}:app.py") == "value = 2"
    assert git(root, "rev-parse", f"{binding['ref']}^{{tree}}") == proof["tree"]
    assert git(executor.prepared.worktree, "rev-parse", "HEAD") == base
    assert git(executor.prepared.worktree, "diff", "--cached", "--name-only") == ""
    assert git(executor.prepared.worktree, "diff", "--name-only") == "app.py"
    assert git(root, "status", "--porcelain") == ""
    reopened = TaskStore(store.db_path)
    try:
        assert _load_evidence(reopened.get_task(task_id), ACCEPTED_CATEGORY, task.execution_id) == binding
    finally:
        reopened._conn.close()


def test_retention_replay_reuses_real_test_proof_and_rejects_later_workspace_change(goal_checks, tmp_path, monkeypatch):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence
    root, base, store, *_ = goal_checks
    task_id = export_task(goal_checks)
    executor = LocalImplementation(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    assert ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    task = store.get_task(task_id)
    original = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
    index_path = Path(git(executor.prepared.worktree, "rev-parse", "--path-format=absolute", "--git-path", "index"))
    index_before = index_path.read_bytes()
    def unexpected_test(*args, **kwargs):
        raise AssertionError("Already persisted real checks must not run again during retention recovery")
    monkeypatch.setattr("reverse_agent.platform_v1.functional_validation._run_check", unexpected_test)
    result = run_task_validation(store, task_id, worktree=executor.prepared.worktree,
                                 base_commit=base, execution_id=task.execution_id)
    assert result[1] == 0 and result[3] == original["result_digest"]
    assert index_path.read_bytes() == index_before
    assert _load_evidence(store.get_task(task_id), ACCEPTED_CATEGORY, task.execution_id) == original
    assert len([row for row in store.get_task(task_id).evidence_refs if row["category"] == ACCEPTED_CATEGORY]) == 1
    (executor.prepared.worktree / "app.py").write_text("value = 3\n", encoding="utf-8")
    rejected = run_task_validation(store, task_id, worktree=executor.prepared.worktree,
                                   base_commit=base, execution_id=task.execution_id)
    assert rejected[1] == 1 and rejected[2] == "artifact_workspace_changed"
    assert git(root, "rev-parse", original["ref"]) == original["commit"]
    assert _load_evidence(store.get_task(task_id), ACCEPTED_CATEGORY, task.execution_id) == original


def test_preexisting_wrong_ref_cannot_be_replaced_or_claimed_accepted(goal_checks, tmp_path):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence
    root, base, store, *_ = goal_checks
    task_id = export_task(goal_checks)
    class Collision(LocalImplementation):
        def execute_role_prepared(self, prepared, store, **kwargs):
            result = super().execute_role_prepared(prepared, store, **kwargs)
            self.ref = f"refs/nerelan/accepted-artifacts/{task_id}/{prepared.execution_id}"
            git(root, "update-ref", self.ref, base, "0" * 40)
            return result
    executor = Collision(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    outcome = ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees"))
    assert outcome.success is False
    task = store.get_task(task_id)
    assert functional_evidence(task)["verified"] is False
    assert _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id) is None
    assert git(root, "rev-parse", executor.ref) == base


def test_retention_gap_recovery_uses_persisted_tests_and_same_git_commit(goal_checks, tmp_path, monkeypatch):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence
    root, base, store, *_ = goal_checks
    task_id = export_task(goal_checks)
    executor = LocalImplementation(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    class ProcessLost(BaseException):
        pass
    original = store._bind_artifact_evidence
    def lose_after_git(*args, **kwargs):
        if kwargs.get("category") == ACCEPTED_CATEGORY:
            raise ProcessLost()
        return original(*args, **kwargs)
    monkeypatch.setattr(store, "_bind_artifact_evidence", lose_after_git)
    with pytest.raises(ProcessLost):
        ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees"))
    pending = store.get_task(task_id)
    assert pending.status == "RUNNING"
    assert _load_evidence(pending, ACCEPTED_CATEGORY, pending.execution_id) is None
    ref = f"refs/nerelan/accepted-artifacts/{task_id}/{pending.execution_id}"
    retained_commit = git(root, "rev-parse", ref)
    before_calls = list(executor.calls)
    def unexpected_test(*args, **kwargs):
        raise AssertionError("The persisted real test proof must survive retention recovery")
    monkeypatch.setattr("reverse_agent.platform_v1.functional_validation._run_check", unexpected_test)
    reopened = TaskStore(store.db_path)
    try:
        recovered = run_task_validation(reopened, task_id, worktree=executor.prepared.worktree,
                                        base_commit=base, execution_id=pending.execution_id)
        assert recovered[1] == 0, recovered
        binding = _load_evidence(reopened.get_task(task_id), ACCEPTED_CATEGORY, pending.execution_id)
        assert binding["commit"] == retained_commit and binding["result_digest"] == recovered[3]
        assert executor.calls == before_calls
        assert git(root, "rev-parse", ref) == retained_commit
        assert len([row for row in reopened.get_task(task_id).evidence_refs
                    if row["category"] == "FunctionalValidation"]) == 1
    finally:
        reopened._conn.close()


def test_stale_owner_cannot_rebind_even_identical_retained_artifact(goal_checks, tmp_path):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence, retain_validated_artifact
    root, base, store, *_ = goal_checks
    task_id = export_task(goal_checks)
    executor = LocalImplementation(root, base, "value = 2\n")
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    assert durable(store, router).execute_durable_single(task_id, workspace_root=str(tmp_path / "worktrees")).success
    task = store.get_task(task_id)
    binding = _load_evidence(task, ACCEPTED_CATEGORY, task.execution_id)
    run = store._get_durable_run(binding["run_id"])
    stale = SimpleNamespace(run_id=run.run_id, owner="unowned-stale-attempt", epoch=run.lease_epoch)
    with pytest.raises(TaskStoreError, match="lease"):
        retain_validated_artifact(store, task_id, binding["result_digest"],
                                  worktree=executor.prepared.worktree, lease=stale)
    with pytest.raises(TaskStoreError, match="lease"):
        store._bind_artifact_evidence(task_id, category=ACCEPTED_CATEGORY, label=task.execution_id,
                                      document=binding, lease=stale)
    assert git(root, "rev-parse", binding["ref"]) == binding["commit"]
    assert _load_evidence(store.get_task(task_id), ACCEPTED_CATEGORY, task.execution_id) == binding


def execution_method(service, engine, mode):
    return getattr(service, "execute_durable_" + mode if engine == "durable" else
                   ("execute" if mode == "single" else "execute_sequential_team"))


def dependent_execution(fixture, engine, mode, *, consumer_code="value = 2\n", ignore_input=False,
                        consumer_capability="validate_task"):
    root, base, store, control, *_ = fixture
    producer_id = export_task(fixture, mode, consumer_capability)
    goal_id = control.goal_id_for_task(producer_id)
    consumer_id = control.list_goal_tasks(goal_id)[1]["task_id"]
    created = []
    router = ExecutorRouter()
    def factory(**kwargs):
        input_commit = kwargs.get("base_ref") or base
        code = "value = 2\n" if not created else consumer_code
        executor = LocalImplementation(root, base if ignore_input else input_commit, code)
        if created and consumer_capability == "validate_task" and code != "value = 2\n":
            prepare = executor.prepare_worktree_once
            def altered_preparation(*args, **kwargs):
                prepared = prepare(*args, **kwargs)
                (prepared.worktree / "app.py").write_text(code, encoding="utf-8")
                return prepared
            executor.prepare_worktree_once = altered_preparation
        created.append(executor)
        return executor
    router.replace("opencode", factory)
    service = durable(store, router) if engine == "durable" else ordinary(store, router)
    return producer_id, consumer_id, created, router, service


@pytest.mark.parametrize("engine,mode", [("ordinary", "single"), ("ordinary", "sequential_team"),
                                        ("durable", "single"), ("durable", "sequential_team")])
def test_consumer_executes_actual_accepted_tree_and_preserves_original_approval(goal_checks, tmp_path, engine, mode):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY, _load_evidence, load_input_binding
    root, base, store, *_ = goal_checks
    producer_id, consumer_id, created, _, service = dependent_execution(goal_checks, engine, mode)
    execute = execution_method(service, engine, mode)
    assert execute(producer_id, workspace_root=str(tmp_path / "worktrees")).success
    producer = store.get_task(producer_id)
    exported = _load_evidence(producer, ACCEPTED_CATEGORY, producer.execution_id)
    outcome = execute(consumer_id, workspace_root=str(tmp_path / "worktrees"))
    assert outcome.success is True, outcome
    consumer = store.get_task(consumer_id)
    bound = load_input_binding(consumer)
    proof = functional_evidence(consumer)
    assert proof["verified"] is True and proof["checks"][0]["test_report"]["tests"] == 1
    assert proof["base_commit"] == bound["base_commit"] == base
    assert proof["head"] == bound["producer"]["commit"] == exported["commit"] != base
    assert proof["tree"] == exported["tree"]
    assert proof["artifact_input"]["task_id"] == producer_id
    assert proof["artifact_input"]["result_digest"] == producer.validation_output_digest
    assert created[1].base == exported["commit"]
    assert created[1].calls == []
    assert git(created[1].prepared.worktree, "show", "HEAD:app.py") == "value = 2"
    assert git(root, "rev-parse", "HEAD") == base
    if engine == "durable":
        run = store._get_durable_run(bound["run_id"])
        assert run.repository_base_sha == base
        assert run.worktree_head_sha == exported["commit"]
    reopened = TaskStore(store.db_path)
    try:
        assert load_input_binding(reopened.get_task(consumer_id)) == bound
        assert functional_evidence(reopened.get_task(consumer_id)) == proof
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("ignore_input,code", [(True, "value = 2\n"), (False, "value = 3\n")])
def test_consumer_rejects_old_head_or_changed_validation_input(goal_checks, tmp_path, ignore_input, code):
    _, _, store, *_ = goal_checks
    producer, consumer, _, _, service = dependent_execution(goal_checks, "ordinary", "single",
                                                           consumer_code=code, ignore_input=ignore_input)
    assert service.execute(producer, workspace_root=str(tmp_path / "worktrees")).success
    rejected = service.execute(consumer, workspace_root=str(tmp_path / "worktrees"))
    assert rejected.success is False
    assert functional_evidence(store.get_task(consumer))["verified"] is False
    assert "artifact_" in rejected.failure_detail


@pytest.mark.parametrize("engine,mode", [("ordinary", "single"), ("ordinary", "sequential_team"),
                                        ("durable", "single"), ("durable", "sequential_team")])
@pytest.mark.parametrize("changes", [True, False])
def test_implementation_consumer_requires_new_diff_from_accepted_input(goal_checks, tmp_path, engine, mode, changes):
    _, base, store, *_ = goal_checks
    code = "value = 2\n" + ("additional = True\n" if changes else "")
    producer, consumer, created, _, service = dependent_execution(goal_checks, engine, mode,
        consumer_capability="execute_task", consumer_code=code)
    execute = execution_method(service, engine, mode)
    assert execute(producer, workspace_root=str(tmp_path / "worktrees")).success
    result = execute(consumer, workspace_root=str(tmp_path / "worktrees"))
    assert result.success is changes, result
    proof = functional_evidence(store.get_task(consumer))
    assert proof["verified"] is changes
    if changes:
        assert proof["base_commit"] == base
        assert proof["head"] == created[1].base != base
        assert created[1].calls == (["executor"] if mode == "single" else ["planner", "coder", "reviewer"])
        assert (created[1].prepared.worktree / "app.py").read_text() == code


@pytest.mark.parametrize("mode", ["single", "sequential_team"])
@pytest.mark.parametrize("checkpoint", ["PRE_PLANNER", "POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"])
def test_validation_input_restart_never_dispatches_model_or_prepares_twice(goal_checks, tmp_path, mode, checkpoint):
    import time
    from reverse_agent.platform_v1.artifact_handoff import load_input_binding
    from reverse_agent.platform_v1.durable_execution import _CrashSimulated, set_crash_after_checkpoint, reset_crash_seam
    _, _, store, *_ = goal_checks
    producer, consumer, created, router, service = dependent_execution(goal_checks, "durable", mode)
    execute = execution_method(service, "durable", mode)
    assert execute(producer, workspace_root=str(tmp_path / "worktrees")).success
    set_crash_after_checkpoint(checkpoint)
    try:
        with pytest.raises(_CrashSimulated):
            execute(consumer, workspace_root=str(tmp_path / "worktrees"))
    finally:
        reset_crash_seam()
    bound = load_input_binding(store.get_task(consumer))
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, consumer))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    reopened = TaskStore(store.db_path)
    try:
        outcome = getattr(durable(reopened, router), "resume_" + mode)(consumer, lease_owner="input-restart")
        assert outcome.success is True, outcome
        assert len(created) == 2 and created[1].calls == []
        assert load_input_binding(reopened.get_task(consumer)) == bound
        assert functional_evidence(reopened.get_task(consumer))["verified"] is True
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("mutation", ["missing_proof", "missing_retention", "failed", "fixture", "execution",
                                      "repository", "revision", "changed_tree", "missing_object"])
def test_input_admission_rejects_unaccepted_or_changed_producer_before_dispatch(goal_checks, tmp_path, monkeypatch, mutation):
    from reverse_agent.platform_v1.artifact_handoff import ACCEPTED_CATEGORY
    from reverse_agent.platform_v1 import functional_validation as validation
    _, _, store, control, *_ = goal_checks
    producer, consumer, created, _, service = dependent_execution(goal_checks, "ordinary", "single")
    assert service.execute(producer, workspace_root=str(tmp_path / "worktrees")).success
    if mutation in {"missing_proof", "missing_retention"}:
        store._conn.execute("DELETE FROM task_evidence WHERE task_id = ? AND category = ?",
            (producer, validation.RESULT_CATEGORY if mutation == "missing_proof" else ACCEPTED_CATEGORY))
    elif mutation in {"failed", "fixture"}:
        store._conn.execute("UPDATE tasks SET status = ? WHERE id = ?",
                            ("FAILED" if mutation == "failed" else "READY_FOR_REVIEW_FIXTURE", producer))
    elif mutation == "execution":
        store._conn.execute("UPDATE tasks SET execution_id = ? WHERE id = ?", ("exec-other", producer))
    elif mutation == "repository":
        store._conn.execute("UPDATE tasks SET repository = ? WHERE id = ?", ("owner/other", producer))
    elif mutation == "revision":
        goal = control.get_goal(control.goal_id_for_task(producer))
        # Simulate a changed authoritative revision without altering the frozen task contract.
        original = control.get_goal
        from dataclasses import replace
        monkeypatch.setattr(type(control), "get_goal", lambda self, goal_id: replace(original(goal_id), revision=goal.revision + 1))
    elif mutation == "changed_tree":
        (created[0].prepared.worktree / "app.py").write_text("value = 99\n", encoding="utf-8")
    else:
        original_git = validation.git_output
        def unavailable(root, *args):
            if any(str(arg).startswith("refs/nerelan/accepted-artifacts/") for arg in args):
                raise subprocess.CalledProcessError(128, ["git", *args])
            return original_git(root, *args)
        monkeypatch.setattr(validation, "git_output", unavailable)
    result = service.execute(consumer, workspace_root=str(tmp_path / "worktrees"))
    assert result.success is False
    assert len(created) == 1
    assert functional_evidence(store.get_task(consumer))["verified"] is False


def test_parallel_conflicting_producers_remain_separate_exact_inputs(goal_checks, tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from reverse_agent.platform_v1.artifact_handoff import load_input_binding
    root, base, store, control, goals, goal, window = goal_checks
    tasks = [planned_check("A"), planned_check("C")]
    tasks += [{**planned_check(name), "dependencies": ["A", "C"], "capability": "validate_task",
               "artifact_input": {"plan_task_id": source}} for name, source in (("BA", "A"), ("BC", "C"))]
    planned = goals.plan(goal.id, expected_revision=goal.revision, tasks=tasks).goal
    goals.approve(goal.id, expected_revision=planned.revision)
    goals.launch(goal.id, expected_revision=planned.revision, window_id=window.id)
    ids = {link["plan_task_id"]: link["task_id"] for link in control.list_goal_tasks(goal.id)}
    def produce(name):
        connection = TaskStore(store.db_path)
        executor = LocalImplementation(root, base, f"value = 2\nmarker = '{name}'\n")
        router = ExecutorRouter()
        router.replace("opencode", lambda **kwargs: executor)
        try:
            return ordinary(connection, router).execute(ids[name], workspace_root=str(tmp_path / "worktrees"))
        finally:
            connection._conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(produce, name) for name in ("A", "C")]
        assert all(future.result(timeout=120).success for future in futures)
    created = []
    router = ExecutorRouter()
    def consumer_factory(**kwargs):
        executor = LocalImplementation(root, kwargs["base_ref"], "must never execute")
        created.append(executor)
        return executor
    router.replace("opencode", consumer_factory)
    for index, (name, source) in enumerate((("BA", "A"), ("BC", "C"))):
        assert ordinary(store, router).execute(ids[name], workspace_root=str(tmp_path / "worktrees")).success
        bound = load_input_binding(store.get_task(ids[name]))
        assert bound["producer"]["task_id"] == ids[source]
        assert created[index].calls == []
        assert (created[index].prepared.worktree / "app.py").read_text() == f"value = 2\nmarker = '{source}'\n"
    assert load_input_binding(store.get_task(ids["BA"]))["producer"]["tree"] != load_input_binding(store.get_task(ids["BC"]))["producer"]["tree"]
    assert git(root, "rev-parse", "HEAD") == base


def test_consumer_binding_is_idempotent_and_rejects_stale_or_conflicting_writes(goal_checks, tmp_path):
    from copy import deepcopy
    from reverse_agent.platform_v1.artifact_handoff import INPUT_CATEGORY, bind_consumer_input, load_input_binding
    _, _, store, *_ = goal_checks
    producer, consumer, _, router, service = dependent_execution(goal_checks, "ordinary", "single")
    assert service.execute(producer, workspace_root=str(tmp_path / "worktrees")).success
    lease = durable(store, router).acquire_lease(task_id=consumer, lease_owner="input-owner")
    bound = bind_consumer_input(store, consumer, lease=lease)
    assert bind_consumer_input(store, consumer, lease=lease) == bound
    stale = SimpleNamespace(run_id=lease.run_id, owner="stale-owner", epoch=lease.epoch)
    with pytest.raises(TaskStoreError, match="lease"):
        bind_consumer_input(store, consumer, lease=stale)
    conflicting = deepcopy(bound)
    conflicting["producer"]["tree"] = "0" * 40
    with pytest.raises(TaskStoreError, match="artifact_binding_conflict"):
        store._bind_artifact_evidence(consumer, category=INPUT_CATEGORY, label=store.get_task(consumer).execution_id,
                                      document=conflicting, lease=lease)
    assert load_input_binding(store.get_task(consumer)) == bound
