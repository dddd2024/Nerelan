"""Real Goal/Git/SQLite/test-process integration; only model execution is local fake."""
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

import pytest

from test_goal_functional_checks import goal_checks, launch_checks
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.durable_execution import (
    DurableExecutionService, _CrashSimulated, reset_crash_seam, set_crash_after_checkpoint)
from reverse_agent.platform_v1.functional_validation import (
    FUNCTIONAL_COMMAND_ID, RESULT_CATEGORY, functional_evidence, run_task_validation)
from reverse_agent.platform_v1.opencode_executor import _collect_final_product_files, handoff_dir
from reverse_agent.platform_v1.run_read_model import RunReadModel
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_execution import TaskExecutionService
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter
from reverse_agent.platform_v1.task_service import _map_task_to_frontend


class LocalImplementation:
    def __init__(self, source, base, code):
        self.source, self.base, self.code = source, base, code
        self.calls = []
        self.prepared = None

    def prepare_worktree_once(self, task_id, workspace_root, callback=None):
        worktree = Path(workspace_root) / task_id
        worktree.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(self.source), "worktree", "add", "--detach", str(worktree), self.base],
                       check=True, capture_output=True)
        self.prepared = SimpleNamespace(worktree=worktree, base_sha=self.base, execution_id=f"exec-{task_id}")
        if callback is not None:
            callback(task_id, {"type": "WORKSPACE_READY", "title": "Prepared local acceptance worktree",
                "metadata": {"workspace": str(worktree), "base_sha": self.base, "execution_id": self.prepared.execution_id}})
        return self.prepared

    def execute_role_prepared(self, prepared, store, *, role_context, event_callback=None):
        role = role_context.role
        self.calls.append(role)
        if role in {"coder", "executor"}:
            (prepared.worktree / "app.py").write_text(self.code, encoding="utf-8")
        else:
            handoff = handoff_dir(prepared.worktree)
            handoff.mkdir(parents=True, exist_ok=True)
            name = "plan.md" if role == "planner" else "review.md"
            (handoff / name).write_text("# Plan\nImplement value two and verify the acceptance test.\n" if role == "planner"
                                      else "# Review\nThe code is ready for the server-owned acceptance check.\n", encoding="utf-8")
        return ExecutorResult(success=True, validation_exit_code=0, validation_command_id="git_diff_check",
            validation_output_digest="", validation_output_summary="Only executor hygiene claim",
            changed_files=_collect_final_product_files(prepared.worktree), workspace=str(prepared.worktree),
            execution_id=prepared.execution_id)

    def execute(self, task_id, store, *, workspace_root, event_callback=None):
        prepared = self.prepare_worktree_once(task_id, workspace_root, event_callback)
        return self.execute_role_prepared(prepared, store, role_context=SimpleNamespace(role="executor"))


def setup_execution(fixture, mode, code):
    root, base, store, control, goals, goal, _ = fixture
    if mode == "sequential_team":
        goals.amend(goal.id, expected_revision=goal.revision, objective=goal.objective, orchestration_mode=mode)
        goal = control.get_goal(goal.id)
        fixture = (*fixture[:5], goal, fixture[6])
    launched = launch_checks(fixture)
    task_id = control.list_goal_tasks(launched.id)[0]["task_id"]
    executor = LocalImplementation(root, base, code)
    router = ExecutorRouter()
    router.replace("opencode", lambda **kwargs: executor)
    return task_id, executor, router


def durable(store, router):
    return DurableExecutionService(store=store, router=router, binding_resolver=LocalBinding(),
        execution_authority_sha="test-functional-authority", planning_sha="test-functional-plan")


class LocalBinding:
    def resolve(self, binding_ref, *, task_executor):
        assert binding_ref == "local-test-binding" and task_executor == "opencode"
        return OpenCodeBindingResolution(binding_ref=binding_ref, connection_id="test-connection",
            executor_id="opencode", provider_id="local", model_id="local/test", base_url="",
            auth_method="none", external_session_status="not_required")


def ordinary(store, router):
    return TaskExecutionService(store=store, router=router, binding_resolver=LocalBinding())


@pytest.mark.parametrize("engine,mode", [("ordinary", "single"), ("ordinary", "sequential_team"),
                                        ("durable", "single"), ("durable", "sequential_team")])
@pytest.mark.parametrize("code,expected", [("value = 2\n", True), ("value = 3\n", False)])
def test_goal_execution_and_persistent_readback_prove_actual_tests(goal_checks, tmp_path, engine, mode, code, expected):
    _, _, store, control, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, mode, code)
    service = durable(store, router) if engine == "durable" else ordinary(store, router)
    method = getattr(service, ("execute_durable_" + mode) if engine == "durable" else (
        "execute" if mode == "single" else "execute_sequential_team"))
    outcome = method(task_id, workspace_root=str(tmp_path / "worktrees"))
    assert outcome.success is expected, outcome
    assert outcome.validation_command_id == FUNCTIONAL_COMMAND_ID
    assert executor.calls == (["executor"] if mode == "single" else ["planner", "coder", "reviewer"])
    assert not handoff_dir(executor.prepared.worktree).exists()
    reopened = TaskStore(store.db_path)
    try:
        task = reopened.get_task(task_id)
        assert task.status == ("READY_FOR_REVIEW" if expected else "FAILED")
        proof = functional_evidence(task)
        assert proof["verified"] is expected, proof
        assert proof["checks"][0]["test_report"]["tests"] == 1
        assert _map_task_to_frontend(task)["testStatus"] == ("PASS" if expected else "FAIL")
        run = RunReadModel(store=reopened, control_store=control).run_detail(task_id)
        assert run["validation"]["functional"]["verified"] is expected
        assert any(row["category"] == RESULT_CATEGORY for row in task.evidence_refs)
    finally:
        reopened._conn.close()


@pytest.mark.parametrize("mode", ["single", "sequential_team"])
@pytest.mark.parametrize("checkpoint", ["POST_CODER", "POST_REVIEWER", "POST_VALIDATION"])
def test_restart_keeps_accepted_roles_and_checks_exact_artifact(goal_checks, tmp_path, mode, checkpoint):
    _, _, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, mode, "value = 2\n")
    service = durable(store, router)
    set_crash_after_checkpoint(checkpoint)
    try:
        with pytest.raises(_CrashSimulated):
            getattr(service, "execute_durable_" + mode)(task_id, workspace_root=str(tmp_path / "worktrees"))
    finally:
        reset_crash_seam()
    before = list(executor.calls)
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, task_id))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    reopened = TaskStore(store.db_path)
    try:
        recovered = durable(reopened, router)
        outcome = getattr(recovered, "resume_" + mode)(task_id, lease_owner="restart-owner")
        assert outcome.success is True, outcome
        assert executor.calls[:len(before)] == before
        assert executor.calls.count("coder") <= 1 and executor.calls.count("executor") <= 1
        assert functional_evidence(reopened.get_task(task_id))["verified"] is True
        assert reopened.get_task(task_id).status == "READY_FOR_REVIEW"
    finally:
        reopened._conn.close()


def test_terminal_resume_rejects_artifact_changed_after_validation(goal_checks, tmp_path):
    _, _, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, "single", "value = 2\n")
    service = durable(store, router)
    assert service.execute_durable_single(task_id, workspace_root=str(tmp_path / "worktrees")).success
    (executor.prepared.worktree / "app.py").write_text("value = 99\n", encoding="utf-8")
    result = service.resume_single(task_id)
    assert result.success is False and result.failure_detail == "functional_checkpoint_artifact_changed"
    assert executor.calls == ["executor"]


def test_missing_result_evidence_cannot_promote_exit_zero(goal_checks, tmp_path):
    _, _, store, *_ = goal_checks
    task_id, _, router = setup_execution(goal_checks, "single", "value = 2\n")
    assert ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees")).success
    store._conn.execute("DELETE FROM task_evidence WHERE task_id = ? AND category = ?", (task_id, RESULT_CATEGORY))
    task = store.get_task(task_id)
    assert task.validation_exit_code == 0
    assert functional_evidence(task)["verified"] is False
    assert _map_task_to_frontend(task)["testStatus"] == "PENDING"
    assert RunReadModel._validation(task)["status"] == "UNVERIFIED"


def test_lease_handoff_during_checks_rejects_stale_evidence(goal_checks, tmp_path, monkeypatch):
    _, base, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, "single", "value = 2\n")
    service = durable(store, router)
    lease = service.acquire_lease(task_id=task_id, lease_owner="first-owner")
    prepared = executor.prepare_worktree_once(task_id, tmp_path / "worktrees")
    executor.execute_role_prepared(prepared, store, role_context=SimpleNamespace(role="executor"))
    original = store._fenced_add_evidence
    def superseded(*args, **kwargs):
        store._conn.execute("UPDATE durable_runs SET lease_epoch = lease_epoch + 1, lease_owner = 'second-owner' WHERE run_id = ?", (lease.run_id,))
        return original(*args, **kwargs)
    monkeypatch.setattr(store, "_fenced_add_evidence", superseded)
    with pytest.raises(TaskStoreError, match="lease_fenced"):
        run_task_validation(store, task_id, worktree=prepared.worktree, base_commit=base,
                            execution_id=prepared.execution_id, lease=lease)
    assert not any(row["category"] == RESULT_CATEGORY for row in store.get_task(task_id).evidence_refs)
    assert store.get_task(task_id).validation_output_digest == ""


def test_failed_validation_checkpoint_never_recovers_as_success(goal_checks, tmp_path):
    _, _, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, "single", "value = 3\n")
    service = durable(store, router)
    set_crash_after_checkpoint("POST_VALIDATION")
    try:
        with pytest.raises(_CrashSimulated):
            service.execute_durable_single(task_id, workspace_root=str(tmp_path / "worktrees"))
    finally:
        reset_crash_seam()
    now = int(time.time() * 1000)
    store._conn.execute("UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?", (now - 10000, task_id))
    service.reconcile_expired_runs(now_ms=now, max_age_ms=1000)
    result = service.resume_single(task_id, lease_owner="restart-owner")
    assert result.success is False and store.get_task(task_id).status == "FAILED"
    assert functional_evidence(store.get_task(task_id))["verified"] is False
    assert executor.calls == ["executor"]


@pytest.mark.parametrize("engine", ["ordinary", "durable"])
def test_preparation_from_a_moved_source_base_cannot_claim_implementation(goal_checks, tmp_path, engine):
    root, _, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, "single", "value = 2\n")
    (root / "app.py").write_text("value = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "--", "app.py"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "concurrent base change"], check=True, capture_output=True)
    executor.base = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], encoding="utf-8").strip()
    service = ordinary(store, router) if engine == "ordinary" else durable(store, router)
    result = getattr(service, "execute" if engine == "ordinary" else "execute_durable_single")(
        task_id, workspace_root=str(tmp_path / "worktrees"))
    assert result.success is False and result.failure_detail == "functional_base_mismatch"
    assert functional_evidence(store.get_task(task_id))["verified"] is False


def test_missing_preparation_identity_does_not_fall_back_to_current_head(goal_checks, tmp_path, monkeypatch):
    _, _, store, *_ = goal_checks
    task_id, executor, router = setup_execution(goal_checks, "single", "value = 2\n")
    original = executor.prepare_worktree_once
    monkeypatch.setattr(executor, "prepare_worktree_once", lambda task_id, root, callback=None: original(task_id, root))
    result = ordinary(store, router).execute(task_id, workspace_root=str(tmp_path / "worktrees"))
    assert result.success is False and result.failure_detail == "functional_base_mismatch"


def test_terminal_replay_rejects_task_run_result_binding_mismatch(goal_checks, tmp_path):
    _, _, store, *_ = goal_checks
    task_id, _, router = setup_execution(goal_checks, "single", "value = 2\n")
    service = durable(store, router)
    assert service.execute_durable_single(task_id, workspace_root=str(tmp_path / "worktrees")).success
    store.set_validation_result(task_id, command_id=FUNCTIONAL_COMMAND_ID, exit_code=0, output_digest="c" * 64)
    result = service.resume_single(task_id)
    assert result.success is False and result.failure_detail == "functional_checkpoint_binding_mismatch"


def test_completed_validation_does_not_override_terminal_task_failure(goal_checks, tmp_path):
    _, _, store, *_ = goal_checks
    task_id, _, router = setup_execution(goal_checks, "single", "value = 2\n")
    service = durable(store, router)
    assert service.execute_durable_single(task_id, workspace_root=str(tmp_path / "worktrees")).success
    run_id = store._conn.execute("SELECT run_id FROM durable_runs WHERE task_id = ?", (task_id,)).fetchone()[0]
    store._conn.execute("UPDATE tasks SET status = 'FAILED', failure_classification = 'execution_failed' WHERE id = ?", (task_id,))
    result = service._functional_checkpoint_outcome(task_id, store._get_durable_run(run_id))
    assert result.success is False and result.failure_detail == "functional_terminal_task_requires_new_execution"
    assert store.get_task(task_id).status == "FAILED"
