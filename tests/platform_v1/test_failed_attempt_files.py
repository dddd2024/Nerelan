"""A failed attempt keeps the files it changed, so the run page does not say "0 files"."""
import subprocess
from pathlib import Path
from typing import Any

from reverse_agent.platform_v1.durable_execution import DurableExecutionService, reset_crash_seam
from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir
from reverse_agent.platform_v1.task_execution import TaskExecutionService

from test_durable_execution_v5 import FakeSingleExecutor, _init_git_worktree, _matching_source_dir, _make_router, _make_store


# ---------------------------------------------------------------------------
# Single-mode (existing)
# ---------------------------------------------------------------------------

def _run(tmp_path, fake):
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(title="edit product", executor_kind="opencode", orchestration_mode="single")
    service = DurableExecutionService(store=store, router=_make_router(fake),
                                      execution_authority_sha="test_authority", planning_sha="test_planning")
    outcome = service.execute_durable_single(task_id=task.id, workspace_root=str(_init_git_worktree(tmp_path)),
                                             lease_owner="test")
    return outcome, store.get_task(task.id)


def test_failed_attempt_records_its_changed_files(tmp_path, _matching_source_dir):
    outcome, task = _run(tmp_path, FakeSingleExecutor(success=False, validation_exit_code=-1))
    assert outcome.success is False
    assert task.status == "FAILED"
    assert [f["path"] for f in task.changed_files] == ["product.py"]


def test_failed_attempt_without_readable_files_stays_empty(tmp_path, _matching_source_dir):
    fake = FakeSingleExecutor(success=False, validation_exit_code=-1)
    original = fake.execute_role_prepared

    def unreadable(*args, **kwargs):
        result = original(*args, **kwargs)
        result.changed_files = []  # e.g. cleanup unconfirmed: the tree was not read
        return result

    fake.execute_role_prepared = unreadable
    outcome, task = _run(tmp_path, fake)
    assert outcome.success is False
    assert list(task.changed_files) == []


# ---------------------------------------------------------------------------
# Sequential-team mode (#1489)
# ---------------------------------------------------------------------------

class _FakePreparedCtx:
    def __init__(self, worktree: Path, execution_id: str = "") -> None:
        self.worktree = worktree
        self.execution_id = execution_id or f"exec-{worktree.name}"


class _FakeRoleResult:
    def __init__(
        self,
        success: bool = True,
        execution_id: str = "exec-fake",
        validation_exit_code: int = 0,
        failure_classification: str = "",
        error: str = "",
    ) -> None:
        self.success = success
        self.execution_id = execution_id
        self.validation_exit_code = validation_exit_code
        self.validation_command_id = "git_diff_check"
        self.validation_output_digest = ""
        self.failure_classification = failure_classification
        self.error = error


class FakeSequentialExecutor:
    """Provider-free executor for sequential-team tests.

    Planner creates a plan handoff; coder modifies ``product.py``; the role
    named by ``fail_role`` returns failure.  This lets a reviewer failure
    leave the coder's changed files in the worktree for the failure handler
    to collect.
    """

    def __init__(self, *, fail_role: str = "") -> None:
        self.fail_role = fail_role

    def prepare_worktree_once(
        self, task_id: str, workspace_root: Path, callback: Any = None
    ) -> _FakePreparedCtx:
        wt = Path(workspace_root) / f"wt-{task_id[-8:]}"
        wt.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=wt, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@local"], cwd=wt, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=wt, capture_output=True, check=True)
        (wt / "README.md").write_text("hello\n", encoding="utf-8")
        (wt / "product.py").write_text("# product\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=wt, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=wt, capture_output=True, check=True)
        return _FakePreparedCtx(worktree=wt)

    def execute_role_prepared(
        self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
    ) -> _FakeRoleResult:
        wt = prepared.worktree
        handoff = _handoff_dir(wt)
        role = role_context.role if role_context else "planner"
        if role == "planner":
            handoff.mkdir(parents=True, exist_ok=True)
            (handoff / "plan.md").write_text("# Plan\nStep 1\n", encoding="utf-8")
        elif role == "coder":
            (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
        if role == self.fail_role:
            return _FakeRoleResult(
                success=False,
                validation_exit_code=-1,
                failure_classification="simulated_failure",
                error="simulated failure at %s" % role,
            )
        return _FakeRoleResult()


def _run_durable_seq(tmp_path, fake):
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(title="seq edit", executor_kind="opencode", orchestration_mode="sequential_team")
    service = DurableExecutionService(store=store, router=_make_router(fake),
                                      execution_authority_sha="test_authority", planning_sha="test_planning")
    outcome = service.execute_durable_sequential_team(
        task_id=task.id, workspace_root=str(_init_git_worktree(tmp_path)),
        lease_owner="test")
    return outcome, store.get_task(task.id)


def _run_ordinary_seq(tmp_path, fake):
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(title="seq ordinary", executor_kind="opencode", orchestration_mode="sequential_team")
    service = TaskExecutionService(store=store, router=_make_router(fake))
    outcome = service.execute_sequential_team(
        task_id=task.id, workspace_root=str(_init_git_worktree(tmp_path)))
    return outcome, store.get_task(task.id)


def test_failed_sequential_team_durable_keeps_coder_changed_files(tmp_path, _matching_source_dir):
    """A failed durable sequential-team attempt keeps the files its coder changed."""
    outcome, task = _run_durable_seq(tmp_path, FakeSequentialExecutor(fail_role="reviewer"))
    assert outcome.success is False
    assert task.status == "FAILED"
    assert [f["path"] for f in task.changed_files] == ["product.py"]


def test_failed_sequential_team_durable_planner_failure_stays_empty(tmp_path, _matching_source_dir):
    """When the planner fails before any coder change, changed_files stays empty."""
    outcome, task = _run_durable_seq(tmp_path, FakeSequentialExecutor(fail_role="planner"))
    assert outcome.success is False
    assert list(task.changed_files) == []


def test_failed_sequential_team_ordinary_keeps_coder_changed_files(tmp_path, _matching_source_dir):
    """A failed ordinary (non-durable) sequential-team attempt keeps coder changes."""
    outcome, task = _run_ordinary_seq(tmp_path, FakeSequentialExecutor(fail_role="reviewer"))
    assert outcome.success is False
    assert [f["path"] for f in task.changed_files] == ["product.py"]
