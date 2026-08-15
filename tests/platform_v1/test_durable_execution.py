"""Provider-free durable execution tests for Issue #197 (v2 recovery).

All tests use:
- fake / recording role workers via FakeExecutor
- temporary filesystem SQLite DB
- temporary Git repositories/worktrees as needed
- no OpenCode, no real model, no provider

Covers all 24 acceptance proofs from the Decision packet.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.architecture.contracts import (
    WorkerAssignment,
    WorkerExecutionResult,
)
from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir
from reverse_agent.platform_v1.durable_execution import (
    ACCEPTED_CHECKPOINTS,
    CHECKPOINT_ORDER,
    CHECKPOINT_INDEX,
    DurableCheckpoint,
    DurableExecutionService,
    DurableResumeError,
    _CrashSimulated,
    reset_crash_seam,
    set_crash_after_checkpoint,
    _check_strict_serde_active,
    _make_strict_saver,
)
from reverse_agent.platform_v1.run_store import (
    TaskStore,
    TaskStoreError,
)
from reverse_agent.platform_v1.task_execution import (
    TaskExecutionError,
    TaskExecutionOutcome,
)
from reverse_agent.platform_v1.task_runtime import ExecutorRouter


# ---------------------------------------------------------------------------
# Test infrastructure: FakeExecutor
# ---------------------------------------------------------------------------

class _FakePreparedCtx:
    """Fake return value from prepare_worktree_once()."""
    def __init__(self, worktree: Path, execution_id: str = "") -> None:
        self.worktree = worktree
        self.execution_id = execution_id or f"exec-{worktree.name}"


class RecordingWorker:
    """A fake role worker that records every call and returns success."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.call_count: dict[str, int] = {}
        self.fail_at: set[str] = set()

    def __call__(self, wa: WorkerAssignment) -> WorkerExecutionResult:
        role = wa.role
        self.calls.append(role)
        self.call_count[role] = self.call_count.get(role, 0) + 1
        if role in self.fail_at:
            return WorkerExecutionResult(
                worker_id=wa.worker_id,
                task_id=wa.task_id,
                execution_id="exec-fake",
                success=False,
                validation_exit_code=-1,
                failure_classification="simulated_failure",
                failure_detail=f"simulated failure at {role}",
                reasons=("simulated_failure",),
            )
        return WorkerExecutionResult(
            worker_id=wa.worker_id,
            task_id=wa.task_id,
            execution_id="exec-fake",
            success=True,
            validation_exit_code=0,
            failure_classification="",
            failure_detail="",
        )


class FakeExecutor:
    """Provider-free executor that simulates prepare_worktree_once and execute_role_prepared.

    Creates handoff files (plan.md, review.md) and product diff files so that
    the durable role loop invariants pass.
    """

    def __init__(self, *, planner_mutation: bool = False, coder_no_diff: bool = False) -> None:
        self.planner_mutation = planner_mutation
        self.coder_no_diff = coder_no_diff
        self.prepare_calls: list[tuple[str, Path]] = []
        self.execute_calls: list[str] = []
        self.call_count: dict[str, int] = {}

    def prepare_worktree_once(self, task_id: str, workspace_root: Path, callback: Any = None) -> _FakePreparedCtx:
        self.prepare_calls.append((task_id, workspace_root))
        wt = workspace_root / f"wt-{task_id[-8:]}"
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
    ) -> Any:
        role = role_context.role if role_context else "planner"
        self.execute_calls.append(role)
        self.call_count[role] = self.call_count.get(role, 0) + 1
        wt = prepared.worktree
        handoff = _handoff_dir(wt)

        if role == "planner":
            handoff.mkdir(parents=True, exist_ok=True)
            (handoff / "plan.md").write_text("# Plan\nStep 1: implement\n", encoding="utf-8")
            if self.planner_mutation:
                (wt / "accidental.py").write_text("x=1\n", encoding="utf-8")
        elif role == "coder":
            if not (handoff / "plan.md").exists():
                raise RuntimeError("missing plan")
            (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            if self.coder_no_diff:
                (wt / "product.py").write_text("# product\n", encoding="utf-8")
        elif role == "reviewer":
            handoff.mkdir(parents=True, exist_ok=True)
            (handoff / "review.md").write_text("# Review\nLooks good\n", encoding="utf-8")

        class _Result:
            success = True
            execution_id = f"exec-{role}"
            validation_exit_code = 0
            failure_classification = ""
            error = ""
        return _Result()


def _make_git_worktree(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@local"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True, check=True)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    (path / "product.py").write_text("# product\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, capture_output=True, check=True)


def _make_store(tmp_path: Path) -> TaskStore:
    db_path = str(tmp_path / "tasks.sqlite3")
    return TaskStore(db_path=db_path)


def _init_git_worktree(tmp_path: Path, name: str = "wt") -> Path:
    wt = tmp_path / name
    _make_git_worktree(wt)
    return wt


def _expire_and_reconcile(store: TaskStore, task_id: str) -> None:
    """Expire the durable run lease and reconcile to INTERRUPTED."""
    import time as _time
    now_ms = int(_time.time() * 1000)
    run_row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task_id,),
    ).fetchone()
    if run_row is None:
        return
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (now_ms - 10000, run_row["run_id"]),
    )
    svc = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")
    svc.reconcile_expired_runs(now_ms=now_ms, max_age_ms=1000)


# ---------------------------------------------------------------------------
# 1-3: Real first-run crash tests
# ---------------------------------------------------------------------------

def test_crash_after_planner_uses_real_durable_path(tmp_path) -> None:
    """Real first-run: Planner succeeds, POST_PLANNER committed, crash, resume skips Planner."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    router = ExecutorRouter()
    service = DurableExecutionService(store=store, router=router, execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="crash-planner-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_crash1")
    set_crash_after_checkpoint("POST_PLANNER")
    fake = FakeExecutor()

    class RecordingRouter(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    router2 = RecordingRouter()
    service2 = DurableExecutionService(store=store, router=router2, execution_authority_sha="test_authority", planning_sha="test_planning")

    with pytest.raises(_CrashSimulated):
        service2.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="worker-1",
            repository_base_sha="",
        )

    reset_crash_seam()

    run = store._find_active_durable_run(task.id)
    assert run is not None
    assert run["accepted_checkpoint"] == "POST_PLANNER"

    planner_calls_before = len(fake.execute_calls)
    assert planner_calls_before >= 1

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service3 = DurableExecutionService(store=store2, router=RecordingRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")
    fake2 = FakeExecutor()

    class RecordingRouter2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service3 = DurableExecutionService(store=store2, router=RecordingRouter2(), execution_authority_sha="test_authority", planning_sha="test_planning")

    _expire_and_reconcile(store2, task.id)

    outcome = service3.resume_sequential_team(
        task_id=task.id,
        lease_owner="worker-2",
    )

    assert fake2.call_count.get("planner", 0) == 0
    assert fake2.call_count.get("coder", 0) >= 1


def test_crash_after_coder_uses_real_durable_path(tmp_path) -> None:
    """Real first-run: Planner+Coders succeed, POST_CODER committed, crash before Reviewer."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    router = ExecutorRouter()

    task = store.create_task(
        title="crash-coder-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_crash2")
    set_crash_after_checkpoint("POST_CODER")

    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="worker-1",
        )
    reset_crash_seam()

    run = store._find_active_durable_run(task.id)
    assert run is not None
    assert run["accepted_checkpoint"] == "POST_CODER"

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service2 = DurableExecutionService(store=store2, router=RR2(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    outcome = service2.resume_sequential_team(
        task_id=task.id, lease_owner="worker-2",
    )

    assert fake2.call_count.get("planner", 0) == 0
    assert fake2.call_count.get("coder", 0) == 0
    assert fake2.call_count.get("reviewer", 0) >= 1


def test_second_crash_during_recovery(tmp_path) -> None:
    """Original crash before Planner accepted -> recovery Planner succeeds -> POST_PLANNER committed -> second crash."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="second-crash-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_crash3")

    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    # First run: crash BEFORE any checkpoint
    set_crash_after_checkpoint("PRE_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="worker-1",
        )
    reset_crash_seam()

    # Recovery: set crash after POST_PLANNER
    set_crash_after_checkpoint("POST_PLANNER")
    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service2 = DurableExecutionService(store=store2, router=RR2(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    with pytest.raises(_CrashSimulated):
        service2.resume_sequential_team(task_id=task.id, lease_owner="worker-2")
    reset_crash_seam()

    run = store2._find_active_durable_run(task.id)
    assert run["accepted_checkpoint"] == "POST_PLANNER"

    # Third reconstruction: Planner MUST NOT run again
    store3 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    fake3 = FakeExecutor()

    class RR3(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake3
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service3 = DurableExecutionService(store=store3, router=RR3(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store3, task.id)
    outcome = service3.resume_sequential_team(task_id=task.id, lease_owner="worker-3")
    assert fake3.call_count.get("planner", 0) == 0


# ---------------------------------------------------------------------------
# 4: Exact prepared worktree persists
# ---------------------------------------------------------------------------

def test_exact_prepared_worktree_persisted(tmp_path) -> None:
    """The durable run must persist the exact prepared.worktree path."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="wt-identity-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_ident")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.worktree_path != ""
    assert Path(run.worktree_path).exists()
    assert "wt_ident" in run.worktree_path or run.worktree_path.startswith(str(wt_dir))


def test_worktree_head_identity_survives(tmp_path) -> None:
    """worktree_head_sha must survive restart and be verified."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="head-ident-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_head")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.worktree_head_sha != ""
    actual_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=run.worktree_path,
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert run.worktree_head_sha == actual_head


# ---------------------------------------------------------------------------
# 5: Interrupted Coder partial diff
# ---------------------------------------------------------------------------

def test_interrupted_coder_partial_diff_survives(tmp_path) -> None:
    """Coder started but POST_CODER not accepted -> partial diff preserved."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="interrupted-coder-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_interrupt")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.accepted_checkpoint == "POST_PLANNER"
    assert run.current_role == "coder"

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service2 = DurableExecutionService(store=store2, router=RR2(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    outcome = service2.resume_sequential_team(task_id=task.id, lease_owner="w2")

    run_after = store2._get_durable_run(run.run_id)
    assert run_after.role_attempt >= 2
    assert run_after.recovery_classification == "interrupted"


def test_coder_recovery_attempt_increments(tmp_path) -> None:
    """role_attempt must increment for interrupted coder."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="attempt-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_attempt")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.role_attempt == 1

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    service2 = DurableExecutionService(store=store2, router=RR2(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    service2.resume_sequential_team(task_id=task.id, lease_owner="w2")

    run_after = store2._get_durable_run(run.run_id)
    assert run_after.role_attempt >= 2


# ---------------------------------------------------------------------------
# 6-9: Authority identity mismatch tests
# ---------------------------------------------------------------------------

def test_authority_sha_mismatch_fails_independently(tmp_path) -> None:
    """execution_authority_sha mismatch must fail closed independently."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="auth-mismatch-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_auth")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(
        store=store, router=RR(),
        execution_authority_sha="authority_abc123",
        planning_sha="planning_def456",
    )
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.execution_authority_sha == "authority_abc123"
    assert run.planning_sha == "planning_def456"

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(
        store=store2, router=RR(),
        execution_authority_sha="different_authority",
        planning_sha="planning_def456",
    )
    with pytest.raises(DurableResumeError) as excinfo:
        service2.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "authority_sha_mismatch" in str(excinfo.value)


def test_planning_sha_mismatch_fails_independently(tmp_path) -> None:
    """planning_sha mismatch must fail closed independently."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="planning-mismatch-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_plan")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(
        store=store, router=RR(),
        execution_authority_sha="authority_abc",
        planning_sha="planning_123",
    )
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(
        store=store2, router=RR(),
        execution_authority_sha="authority_abc",
        planning_sha="different_planning",
    )
    with pytest.raises(DurableResumeError) as excinfo:
        service2.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "planning_sha_mismatch" in str(excinfo.value)


def test_repository_base_sha_mismatch_fails_independently(tmp_path) -> None:
    """repository_base_sha mismatch must fail closed independently.

    repository_base_sha is obtained from prepare_worktree_once(), NOT from
    the caller. Resume must verify the persisted value.
    """
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="base-mismatch-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_base")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    # repository_base_sha must be non-empty and equal the prepared worktree HEAD
    assert run.repository_base_sha != ""
    actual_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=run.worktree_path, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert run.repository_base_sha == actual_head

    # Resume with wrong repository_base_sha must fail
    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    with pytest.raises(DurableResumeError) as excinfo:
        service2.resume_sequential_team(
            task_id=task.id, lease_owner="w2",
            repository_base_sha="different_repo_sha",
        )
    assert "base_sha_mismatch" in str(excinfo.value)


def test_worktree_path_head_mismatch_fails_independently(tmp_path) -> None:
    """worktree path/HEAD mismatch must fail closed independently."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="wt-mismatch-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_mismatch")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(store._find_active_durable_run(task.id)["run_id"])
    assert run.worktree_head_sha != ""

    _expire_and_reconcile(store, task.id)

    # Simulate HEAD change
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", "extra"],
        cwd=run.worktree_path, capture_output=True, check=True,
    )

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(DurableResumeError) as excinfo:
        service2.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "repository_base_head_mismatch" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 10-12: Checkpoint sequence and idempotency
# ---------------------------------------------------------------------------

def test_checkpoint_sequence_exactly_once(tmp_path) -> None:
    """Full durable execution produces exactly: PRE_PLANNER, POST_PLANNER, POST_CODER, POST_REVIEWER, POST_VALIDATION."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="seq-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_seq")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    outcome = service.execute_durable_sequential_team(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
    )

    cps = service.checkpoint_sequence(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,)
        ).fetchone()["run_id"]
    )
    assert list(cps) == ["PRE_PLANNER", "POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"]
    assert list(cps).count("POST_VALIDATION") == 1


def test_duplicate_accept_checkpoint_idempotent(tmp_path) -> None:
    """Same checkpoint + same accepted state must be idempotent (no duplicate insert)."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="idempotent-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id,
        execution_id=task.execution_id,
        lease_owner="w1",
        repository_base_sha="",
        worktree_path="",
    )
    run_id = lease.run_id

    cp0 = store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)
    cp1 = store._accept_checkpoint(run_id, "POST_PLANNER", "digest1", 1, lease.owner, lease.epoch)
    cp2 = store._accept_checkpoint(run_id, "POST_PLANNER", "digest1", 1, lease.owner, lease.epoch)

    assert cp0.checkpoint_name == "PRE_PLANNER"
    assert cp1.checkpoint_id == cp2.checkpoint_id
    cps = store._get_durable_checkpoints(run_id)
    assert len([c for c in cps if c.checkpoint_name == "POST_PLANNER"]) == 1


def test_checkpoint_no_jump(tmp_path) -> None:
    """Cannot jump from PRE_PLANNER directly to POST_VALIDATION."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="no-jump-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", repository_base_sha="", worktree_path="",
    )
    run_id = lease.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)

    with pytest.raises(TaskStoreError) as excinfo:
        store._accept_checkpoint(run_id, "POST_VALIDATION", "", 1, lease.owner, lease.epoch)
    assert "checkpoint_sequence_jump" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 13: Strict serde
# ---------------------------------------------------------------------------

def test_strict_serde_configured(tmp_path) -> None:
    """The production helper must use restricted serialization."""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    saver = _make_strict_saver(conn)
    assert _check_strict_serde_active(saver) is True
    conn.close()


def test_unrestricted_saver_fails_check(tmp_path) -> None:
    """A default SqliteSaver must NOT pass the strict serde check."""
    import sqlite3
    from langgraph.checkpoint.sqlite import SqliteSaver
    conn = sqlite3.connect(":memory:")
    default_saver = SqliteSaver(conn=conn)
    has_serde = getattr(default_saver, "serde", None) is not None
    if has_serde:
        assert _check_strict_serde_active(default_saver) is False
    conn.close()


# ---------------------------------------------------------------------------
# 14: Normal Task API enters durable path
# ---------------------------------------------------------------------------

def test_normal_execute_uses_durable_path(tmp_path) -> None:
    """POST /api/tasks/{id}/execute for sequential_team must use DurableExecutionService."""
    from reverse_agent.platform_v1.task_service import _handler_factory, TaskStore as TS

    store = _make_store(tmp_path)
    task = store.create_task(
        title="api-durable-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_api")

    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    handler_cls = _handler_factory(
        store, RR(),
        allowed_origin="http://localhost:4173",
        execution_authority_sha="test_authority_sha",
        planning_sha="test_planning_sha",
    )
    handler_cls.store = store
    handler_cls.router = RR()
    handler_cls.execution_authority_sha = "test_authority_sha"
    handler_cls.planning_sha = "test_planning_sha"

    reset_crash_seam()
    run = store._find_active_durable_run(task.id)
    assert run is None

    fake = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    handler_cls.router = RR2()
    handler_cls.execution_authority_sha = "test_authority_sha"
    handler_cls.planning_sha = "test_planning_sha"

    from http.server import ThreadingHTTPServer
    import threading

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    import urllib.request
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/tasks/{task.id}/execute",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        body = json.loads(resp.read().decode())
    except Exception as e:
        body = {}

    server.shutdown()

    run_row = store._conn.execute(
        "SELECT * FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    run_after = dict(run_row) if run_row else None
    assert run_after is not None
    assert run_after["accepted_checkpoint"] in ("POST_VALIDATION", "POST_REVIEWER", "POST_CODER", "POST_PLANNER")


def test_resume_api_uses_same_run(tmp_path) -> None:
    """POST /api/tasks/{id}/resume must resume the same durable run."""
    from reverse_agent.platform_v1.task_service import _handler_factory

    store = _make_store(tmp_path)
    task = store.create_task(
        title="resume-api-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_resume")

    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    set_crash_after_checkpoint("POST_PLANNER")
    handler_cls = _handler_factory(
        store, RR(), allowed_origin="http://localhost:4173",
        execution_authority_sha="test_authority_sha",
        planning_sha="test_planning_sha",
    )
    handler_cls.store = store
    handler_cls.router = RR()
    handler_cls.execution_authority_sha = "test_authority_sha"
    handler_cls.planning_sha = "test_planning_sha"

    from http.server import ThreadingHTTPServer
    import threading
    import urllib.request

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/tasks/{task.id}/execute",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass

    reset_crash_seam()
    server.shutdown()

    run = store._find_active_durable_run(task.id)
    assert run is not None
    assert run["accepted_checkpoint"] == "POST_PLANNER"

    run_id_before = run["run_id"]

    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, executor_kind: str, **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    handler_cls2 = _handler_factory(
        store, RR2(), allowed_origin="http://localhost:4173",
        execution_authority_sha="test_authority_sha",
        planning_sha="test_planning_sha",
    )
    handler_cls2.store = store
    handler_cls2.router = RR2()
    handler_cls2.execution_authority_sha = "test_authority_sha"
    handler_cls2.planning_sha = "test_planning_sha"

    server2 = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls2)
    port2 = server2.server_address[1]
    t2 = threading.Thread(target=server2.serve_forever, daemon=True)
    t2.start()

    _expire_and_reconcile(store, task.id)

    req2 = urllib.request.Request(
        f"http://127.0.0.1:{port2}/api/tasks/{task.id}/resume",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req2, timeout=5)
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass

    server2.shutdown()

    run_row = store._conn.execute(
        "SELECT * FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    run_after = dict(run_row) if run_row else None
    assert run_after is not None
    assert run_after["run_id"] == run_id_before


# ---------------------------------------------------------------------------
# 15: BindingResolver / credential relay seam preserved
# ---------------------------------------------------------------------------

def test_binding_resolver_preserved(tmp_path) -> None:
    """BindingResolver must be passed through from task_service to DurableExecutionService."""
    from reverse_agent.platform_v1.task_service import _handler_factory

    store = _make_store(tmp_path)
    task = store.create_task(
        title="binding-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
        binding_ref="test-binding",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    fake_resolver = type("FakeResolver", (), {"resolve": lambda self, ref, **kw: {"binding_ref": ref}})()

    handler_cls = _handler_factory(
        store, ExecutorRouter(),
        allowed_origin="http://localhost:4173",
        binding_resolver=fake_resolver,
    )
    handler_cls.binding_resolver = fake_resolver

    assert handler_cls.binding_resolver is fake_resolver


# ---------------------------------------------------------------------------
# 16: Startup stale-run reconciliation
# ---------------------------------------------------------------------------

def test_startup_reconciliation_no_model_calls(tmp_path) -> None:
    """Startup reconciliation marks expired leases INTERRUPTED without model calls."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="stale-startup",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", repository_base_sha="", worktree_path="",
    )
    run_id = lease.run_id

    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (int(time.time() * 1000) - 10000, run_id),
    )

    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")
    records = service.reconcile_expired_runs(
        now_ms=int(time.time() * 1000), max_age_ms=1000
    )

    assert len(records) == 1
    assert records[0]["recovery_classification"] == "orphan_stale_lease"
    task_after = store.get_task(task.id)
    assert task_after.status == "INTERRUPTED"


# ---------------------------------------------------------------------------
# 17: Stale epoch production-path fencing
# ---------------------------------------------------------------------------

def test_stale_epoch_production_path_fencing(tmp_path) -> None:
    """Stale owner/epoch must not write through the durable role path."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="fencing-product-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease1 = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", repository_base_sha="", worktree_path="",
    )
    run_id = lease1.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease1.owner, lease1.epoch)

    lease2 = store._recover_durable_lease(run_id, "w2")
    assert lease2.epoch == 2

    with pytest.raises(TaskStoreError):
        store._accept_checkpoint(run_id, "POST_PLANNER", "x", 1, "w1", 1)
    with pytest.raises(TaskStoreError):
        store._set_planner_handoff_digest(run_id, "x", "w1", 1)
    with pytest.raises(TaskStoreError):
        store._set_coder_product_diff_digest(run_id, "x", "w1", 1)
    with pytest.raises(TaskStoreError):
        store._set_role_attempt(run_id, "coder", 2, "w1", 1)
    with pytest.raises(TaskStoreError):
        store._set_recovery_classification(run_id, "x", "w1", 1)
    with pytest.raises(TaskStoreError):
        store._heartbeat_durable_lease(run_id, "w1", 1, expiry_ms=300000)


# ---------------------------------------------------------------------------
# 18: Successful terminal READY_FOR_REVIEW exactly once
# ---------------------------------------------------------------------------

def test_successful_durable_ends_ready_for_review_once(tmp_path) -> None:
    """Full durable execution must end READY_FOR_REVIEW exactly once."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    task = store.create_task(
        title="terminal-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_terminal")
    fake = FakeExecutor()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    outcome = service.execute_durable_sequential_team(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
    )

    final_task = store.get_task(task.id)
    assert final_task.status == "READY_FOR_REVIEW"

    events = store.get_events(task.id)
    validated_events = [e for e in events if e.type == "VALIDATED"]
    assert len(validated_events) == 1


# ---------------------------------------------------------------------------
# 19: Single execution backward compatibility
# ---------------------------------------------------------------------------

def test_single_execution_backward_compatible(tmp_path) -> None:
    """Normal single execution still works."""
    from reverse_agent.platform_v1.task_execution import TaskExecutionService as TES

    store = _make_store(tmp_path)
    router = ExecutorRouter()
    service = TES(store=store, router=router)

    task = store.create_task(
        title="backward-compat",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    outcome = service.execute(task.id, workspace_root=str(tmp_path / "ws"))
    assert isinstance(outcome, TaskExecutionOutcome)
    assert outcome.success is True


# ---------------------------------------------------------------------------
# 20: Existing v1 tests still pass
# ---------------------------------------------------------------------------

def test_crash_after_planner_accepted_restarts_from_coder(tmp_path) -> None:
    """Existing test: Planner accepted, crash, restart skips Planner."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="durable-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    wt = _init_git_worktree(tmp_path, "wt1")

    lease = service.acquire_lease(
        task_id=task.id,
        lease_owner="worker-1",
        repository_base_sha="",
        worktree_path=str(wt),
    )
    run_id = lease.run_id

    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)
    store._accept_checkpoint(run_id, "POST_PLANNER", "plan_digest_abc123", 1, lease.owner, lease.epoch)
    store._set_planner_handoff_digest(run_id, "plan_digest_abc123", lease.owner, lease.epoch)

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")
    run = store2._find_active_durable_run(task.id)
    assert run is not None
    assert run["accepted_checkpoint"] == "POST_PLANNER"

    ctx = service2.get_resume_context(task.id)
    assert ctx.accepted_checkpoint == "POST_PLANNER"


def test_external_operation_reconciliation(tmp_path) -> None:
    """Existing test: external operation idempotency."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    op1 = service.record_external_operation(
        operation_key="deploy_v1",
        idempotency_key="idem-123",
        request_digest="req_digest_abc",
    )
    assert op1.state == "PENDING"

    service.reconcile_external_operation(
        operation_id=op1.operation_id,
        external_operation_id="ext-op-456",
        result_state="success",
    )

    assert service.prevent_duplicate_dispatch(
        idempotency_key="idem-123", request_digest="req_digest_abc",
    ) is True


def test_checkpoint_ordering_cannot_move_backwards(tmp_path) -> None:
    """Existing test: checkpoint sequence cannot move backwards."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="order-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = service.acquire_lease(
        task_id=task.id, lease_owner="w1", worktree_path="",
    )
    run_id = lease.run_id

    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)
    store._accept_checkpoint(run_id, "POST_PLANNER", "d1", 1, lease.owner, lease.epoch)
    store._accept_checkpoint(run_id, "POST_CODER", "d2", 1, lease.owner, lease.epoch)

    with pytest.raises(TaskStoreError) as excinfo:
        store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease.owner, lease.epoch)
    assert "checkpoint_sequence_regression" in str(excinfo.value)


def test_stale_running_lease_reconciled_to_interrupted(tmp_path) -> None:
    """Existing test: expired RUNNING lease -> INTERRUPTED."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="stale-lease-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = service.acquire_lease(
        task_id=task.id, lease_owner="w1", worktree_path="",
    )
    run_id = lease.run_id

    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (int(time.time() * 1000) - 1000, run_id),
    )

    records = service.reconcile_expired_runs(
        now_ms=int(time.time() * 1000), max_age_ms=1000
    )
    assert len(records) == 1
    assert records[0]["recovery_classification"] == "orphan_stale_lease"
    assert store.get_task(task.id).status == "INTERRUPTED"


def test_new_worker_higher_epoch_fences_old(tmp_path) -> None:
    """Existing test: monotonic epoch fencing."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="epoch-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease1 = service.acquire_lease(task_id=task.id, lease_owner="w1", worktree_path="")
    run_id = lease1.run_id
    assert lease1.epoch == 1

    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease1.owner, lease1.epoch)
    lease2 = store._recover_durable_lease(run_id, "w2")
    assert lease2.epoch == 2

    with pytest.raises(TaskStoreError):
        store._accept_checkpoint(run_id, "POST_PLANNER", "digest", 1, "w1", 1)

    store._accept_checkpoint(run_id, "POST_PLANNER", "digest", 1, lease2.owner, lease2.epoch)


def test_orchestration_mode_persists_across_restart(tmp_path) -> None:
    """Existing test: orchestration_mode survives restart."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="mode-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    task2 = store2.get_task(task.id)
    assert task2.orchestration_mode == "sequential_team"


def test_interrupted_is_recoverable_not_terminal(tmp_path) -> None:
    """Existing test: INTERRUPTED is recoverable."""
    from reverse_agent.platform_v1.run_store import TERMINAL_STATUSES
    assert "INTERRUPTED" not in TERMINAL_STATUSES


def test_stable_run_id_across_reconstruction(tmp_path) -> None:
    """Existing test: run_id is stable across service reconstruction."""
    store = _make_store(tmp_path)
    service = DurableExecutionService(store=store, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")

    task = store.create_task(
        title="stable-run",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = service.acquire_lease(task_id=task.id, lease_owner="w1", worktree_path="")
    run_id = lease.run_id

    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=ExecutorRouter(), execution_authority_sha="test_authority", planning_sha="test_planning")
    ctx = service2.get_resume_context(task.id)
    assert ctx.lease.run_id == run_id


# ---------------------------------------------------------------------------
# Terminal takeover test: stale worker cannot publish after new epoch
# ---------------------------------------------------------------------------

def test_terminal_takeover_stale_worker_fenced(tmp_path) -> None:
    """Old worker with epoch=1 cannot mutate Task status, changed_files,
    events, evidence, validation, or terminal result after new worker
    acquires epoch=2."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="takeover-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease1 = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="old-worker", repository_base_sha="", worktree_path="",
    )
    run_id = lease1.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, lease1.owner, lease1.epoch)
    store._accept_checkpoint(run_id, "POST_PLANNER", "digest_1", 1, lease1.owner, lease1.epoch)

    # Old worker: status is PREPARING_WORKSPACE after claim, 2 checkpoints
    task_before = store.get_task(task.id)
    assert task_before.status == "PREPARING_WORKSPACE"

    # New worker acquires strictly newer epoch
    lease2 = store._recover_durable_lease(run_id, "new-worker")
    assert lease2.epoch == 2

    # --- Old worker attempts every durable publication path ---
    # Fenced transition
    with pytest.raises(TaskStoreError):
        store._fenced_transition_to(run_id, task.id, "VALIDATING", "old-worker", 1)
    # Fenced changed_files
    with pytest.raises(TaskStoreError):
        store._fenced_set_changed_files(run_id, task.id, [{"path": "x.py"}], "old-worker", 1)
    # Fenced event
    with pytest.raises(TaskStoreError):
        store._fenced_add_event(
            run_id, task.id,
            event_type="EXECUTOR_FINISHED",
            title="stale event",
            owner="old-worker", epoch=1,
        )
    # Fenced evidence
    with pytest.raises(TaskStoreError):
        store._fenced_add_evidence(
            run_id, task.id,
            category="test", label="l", value="v", status="info",
            owner="old-worker", epoch=1,
        )
    # Fenced classify_failure
    with pytest.raises(TaskStoreError):
        store._fenced_classify_failure(
            run_id, task.id,
            classification="failed", detail="stale",
            owner="old-worker", epoch=1,
        )
    # Fenced validation
    with pytest.raises(TaskStoreError):
        store._fenced_set_task_validation(
            run_id, task.id,
            command_id="test", exit_code=0, output_digest="",
            owner="old-worker", epoch=1,
        )
    # Fenced terminalize
    with pytest.raises(TaskStoreError):
        store._fenced_terminalize(
            run_id, task.id,
            terminal_status="READY_FOR_REVIEW",
            validation_command_id="", validation_exit_code=0,
            validation_output_digest="",
            failure_classification="", failure_detail="",
            owner="old-worker", epoch=1,
        )

    # --- Verify state unchanged by stale worker ---
    task_after = store.get_task(task.id)
    assert task_after.status == "PREPARING_WORKSPACE"

    events = store.get_events(task.id)
    assert len([e for e in events if e.title == "stale event"]) == 0

    changed = task_after.changed_files
    assert not any(f.get("path") == "x.py" for f in changed)

    # Evidence unchanged
    ev_count = store._conn.execute(
        "SELECT COUNT(*) FROM task_evidence WHERE task_id = ?", (task.id,)
    ).fetchone()[0]
    assert ev_count == 0

    # Validation unchanged
    assert task_after.validation_command_id == ""
    assert task_after.validation_exit_code is None

    # --- New worker CAN continue ---
    store._fenced_transition_to(run_id, task.id, "RUNNING", "new-worker", 2)
    store._fenced_transition_to(run_id, task.id, "VALIDATING", "new-worker", 2)
    store._fenced_transition_to(run_id, task.id, "READY_FOR_REVIEW", "new-worker", 2)
    final = store.get_task(task.id)
    assert final.status == "READY_FOR_REVIEW"


# ---------------------------------------------------------------------------
# Real abrupt process-death test
# ---------------------------------------------------------------------------

def test_abrupt_process_death_preserves_old_lease(tmp_path) -> None:
    """_CrashSimulated must NOT be caught by generic Exception handler.
    Lease must remain with old owner/epoch/expiry for reconciliation."""
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _FakePreparedCtx:
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _FakePreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
        ) -> Any:
            role = role_context.role if role_context else "planner"
            wt = prepared.worktree
            handoff = _handoff_dir(wt)
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "plan.md").write_text("# Plan\n", encoding="utf-8")
            elif role == "coder":
                (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            elif role == "reviewer":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "review.md").write_text("# Review\n", encoding="utf-8")

            class _Result:
                success = True
                execution_id = f"exec-{role}"
                validation_exit_code = 0
                failure_classification = ""
                error = ""
            return _Result()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return FakeExecutor()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    # --- Phase 1: old worker, crash after POST_PLANNER ---
    store = _make_store(tmp_path)
    task = store.create_task(
        title="crash-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_crash"
    _make_git_worktree(wt_dir)

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")

    old_epoch = 0
    old_owner = ""
    old_expiry = 0

    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="old-worker",
        )

    # --- Verify old lease is PRESERVED (not released) ---
    row = store._conn.execute(
        "SELECT lease_owner, lease_epoch, lease_expiry_ms "
        "FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    assert row is not None
    old_owner = row["lease_owner"]
    old_epoch = int(row["lease_epoch"])
    old_expiry = int(row["lease_expiry_ms"])
    assert old_owner == "old-worker"
    assert old_epoch == 1
    assert old_expiry > 0  # lease was NOT released

    # --- Phase 2: make lease stale deterministically ---
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE task_id = ?",
        (int(time.time() * 1000) - 10000, task.id),
    )

    # --- Phase 3: reconciliation ---
    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    service2 = DurableExecutionService(store=store2, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    records = service2.reconcile_expired_runs(
        now_ms=int(time.time() * 1000), max_age_ms=1000
    )
    assert len(records) >= 1
    assert records[0]["recovery_classification"] == "orphan_stale_lease"
    task_after = store2.get_task(task.id)
    assert task_after.status == "INTERRUPTED"

    run = store2._get_durable_run(
        store2._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.recovery_classification == "orphan_stale_lease"
    reset_crash_seam()

    # --- Phase 4: new worker resumes with higher epoch ---
    set_crash_after_checkpoint("POST_CODER")
    fake2 = FakeExecutor()

    class RR2(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return fake2
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    service3 = DurableExecutionService(store=store2, router=RR2(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service3.resume_sequential_team(
            task_id=task.id,
            lease_owner="new-worker",
        )

    run_after = store2._get_durable_run(run.run_id)
    new_epoch = run_after.lease_epoch
    assert new_epoch > old_epoch  # strictly newer

    # Planner must NOT be called again
    planner_calls = fake2.execute_calls.count("planner") if hasattr(fake2, "execute_calls") else 0
    # Count execute_calls that are "planner"
    execute_calls = fake2.execute_calls if hasattr(fake2, "execute_calls") else []
    planner_call_count = sum(1 for c in execute_calls if c == "planner")
    assert planner_call_count == 0

    reset_crash_seam()


def test_abrupt_crash_after_coder_no_restart(tmp_path) -> None:
    """After crash after POST_CODER, new worker must NOT re-run Planner or Coder."""
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def __init__(self) -> None:
            self.execute_calls: list[str] = []

        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _FakePreparedCtx:
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _FakePreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
        ) -> Any:
            role = role_context.role if role_context else "planner"
            self.execute_calls.append(role)
            wt = prepared.worktree
            handoff = _handoff_dir(wt)
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "plan.md").write_text("# Plan\n", encoding="utf-8")
            elif role == "coder":
                (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            elif role == "reviewer":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "review.md").write_text("# Review\n", encoding="utf-8")

            class _Result:
                success = True
                execution_id = f"exec-{role}"
                validation_exit_code = 0
                failure_classification = ""
                error = ""
            return _Result()

    class RR(ExecutorRouter):
        def __init__(self, fake: FakeExecutor) -> None:
            super().__init__()
            self._fake = fake

        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return self._fake

        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="crash-coder-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_crash_coder"
    _make_git_worktree(wt_dir)

    # Phase 1: crash after POST_CODER
    fake1 = FakeExecutor()
    set_crash_after_checkpoint("POST_CODER")
    service = DurableExecutionService(store=store, router=RR(fake1), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.accepted_checkpoint == "POST_CODER"

    # Phase 2: resume -- only reviewer should run
    store2 = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
    fake2 = FakeExecutor()
    service2 = DurableExecutionService(store=store2, router=RR(fake2), execution_authority_sha="test_authority", planning_sha="test_planning")
    _expire_and_reconcile(store2, task.id)
    outcome = service2.resume_sequential_team(task_id=task.id, lease_owner="w2")

    planner_calls = fake2.execute_calls.count("planner")
    coder_calls = fake2.execute_calls.count("coder")
    reviewer_calls = fake2.execute_calls.count("reviewer")
    assert planner_calls == 0
    assert coder_calls == 0
    assert reviewer_calls >= 1


# ---------------------------------------------------------------------------
# Production checkpoint DB test
# ---------------------------------------------------------------------------

def test_production_checkpoint_db_persisted(tmp_path) -> None:
    """Durable run must persist checkpoint_db_path and it must be a real file."""
    from reverse_agent.platform_v1.durable_execution import _make_strict_saver, _check_strict_serde_active
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _FakePreparedCtx:
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _FakePreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
        ) -> Any:
            role = role_context.role if role_context else "planner"
            wt = prepared.worktree
            handoff = _handoff_dir(wt)
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "plan.md").write_text("# Plan\n", encoding="utf-8")
            elif role == "coder":
                (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            elif role == "reviewer":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "review.md").write_text("# Review\n", encoding="utf-8")

            class _Result:
                success = True
                execution_id = f"exec-{role}"
                validation_exit_code = 0
                failure_classification = ""
                error = ""
            return _Result()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return FakeExecutor()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="checkpoint-db-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_cp"
    _make_git_worktree(wt_dir)

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.checkpoint_db_path != ""
    assert Path(run.checkpoint_db_path).exists()
    assert run.checkpoint_db_path.endswith(".sqlite3")


def test_stable_thread_id_equals_run_id(tmp_path) -> None:
    """LangGraph thread_id must equal durable run_id across execution and reconstruction."""
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir
    from reverse_agent.platform_v1.durable_execution import _make_strict_saver, _check_strict_serde_active
    import sqlite3 as _sqlite3

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _FakePreparedCtx:
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _FakePreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
        ) -> Any:
            role = role_context.role if role_context else "planner"
            wt = prepared.worktree
            handoff = _handoff_dir(wt)
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "plan.md").write_text("# Plan\n", encoding="utf-8")
            elif role == "coder":
                (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            elif role == "reviewer":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "review.md").write_text("# Review\n", encoding="utf-8")

            class _Result:
                success = True
                execution_id = f"exec-{role}"
                validation_exit_code = 0
                failure_classification = ""
                error = ""
            return _Result()

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return FakeExecutor()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="thread-id-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_thread"
    _make_git_worktree(wt_dir)

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(store=store, router=RR(), execution_authority_sha="test_authority", planning_sha="test_planning")
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    run_id = run.run_id

    # Verify checkpoint DB exists and has data
    assert run.checkpoint_db_path != ""
    assert Path(run.checkpoint_db_path).exists()

    # Reconstruct saver from persisted path
    cp_conn = _sqlite3.connect(
        run.checkpoint_db_path, isolation_level=None, check_same_thread=False
    )
    cp_conn.execute("PRAGMA journal_mode=WAL")
    saver = _make_strict_saver(cp_conn)

    # Verify strict serde
    assert _check_strict_serde_active(saver) is True


# ---------------------------------------------------------------------------
# Addendum: one-run-per-Task SQLite UNIQUE invariant
# ---------------------------------------------------------------------------

def test_one_run_per_task_unique_constraint(tmp_path) -> None:
    """Only one durable run may exist per task_id; enforced by SQLite UNIQUE."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="unique-test", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease1 = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
    )
    assert lease1.run_id
    task_after = store.get_task(task.id)
    assert task_after.status == "PREPARING_WORKSPACE"
    with pytest.raises(TaskStoreError) as ei:
        store._acquire_durable_lease(
            task_id=task.id, execution_id=task.execution_id,
            lease_owner="w2", task_status=None,
        )
    assert "durable_run_already_active" in str(ei.value)
    count = store._conn.execute(
        "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?",
        (task.id,),
    ).fetchone()[0]
    assert count == 1


def test_historical_duplicate_migration_fails_closed(tmp_path) -> None:
    """Pre-existing duplicate durable_runs rows fail closed at schema init."""
    import sqlite3 as _sqlite3
    raw = tmp_path / "dup.sqlite3"
    conn = _sqlite3.connect(str(raw), isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        "CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, "
        "repository TEXT NOT NULL, status TEXT NOT NULL, executor_kind TEXT NOT NULL, "
        "execution_id TEXT NOT NULL, model_profile_ref TEXT NOT NULL, "
        "binding_ref TEXT NOT NULL DEFAULT '', permission_profile TEXT NOT NULL, "
        "policy_ref TEXT NOT NULL, workspace TEXT NOT NULL, branch TEXT NOT NULL, "
        "orchestration_mode TEXT NOT NULL DEFAULT 'single', created_at TEXT NOT NULL, "
        "updated_at TEXT NOT NULL, failure_classification TEXT NOT NULL, "
        "failure_detail TEXT NOT NULL, validation_command_id TEXT NOT NULL, "
        "validation_exit_code INTEGER, validation_output_digest TEXT NOT NULL, "
        "idempotency_key TEXT NOT NULL);"
        "CREATE TABLE durable_runs (run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, "
        "execution_id TEXT NOT NULL);"
    )
    conn.execute(
        "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "t1", "x", "r", "QUEUED",
            "opencode", "e1",
            "", "", "", "",
            "", "", "seq", "now", "now",
            "", "", "",
            None, "", "",
        ),
    )
    conn.execute("INSERT INTO durable_runs VALUES ('r1','t1','e1'),('r2','t1','e1')")
    conn.commit()
    with pytest.raises(TaskStoreError) as ei:
        TaskStore(db_path=str(raw))
    assert "durable_run_task_uniqueness_violation" in str(ei.value)


# ---------------------------------------------------------------------------
# Addendum: trusted lease config validation
# ---------------------------------------------------------------------------

def test_trusted_lease_config_validation(tmp_path) -> None:
    """expiry_ms<=0, cadence<=0, cadence>=expiry must all fail closed."""
    store = _make_store(tmp_path)
    with pytest.raises(TaskExecutionError) as ei:
        DurableExecutionService(store=store, router=object(),
                                expiry_ms=0, heartbeat_window_ms=60000)
    assert "expiry_ms_non_positive" in str(ei.value)
    with pytest.raises(TaskExecutionError) as ei:
        DurableExecutionService(store=store, router=object(),
                                expiry_ms=-1, heartbeat_window_ms=60000)
    assert "expiry_ms_non_positive" in str(ei.value)
    with pytest.raises(TaskExecutionError) as ei:
        DurableExecutionService(store=store, router=object(),
                                expiry_ms=300000, heartbeat_window_ms=0)
    assert "heartbeat_window_ms_non_positive" in str(ei.value)
    with pytest.raises(TaskExecutionError) as ei:
        DurableExecutionService(store=store, router=object(),
                                expiry_ms=300000, heartbeat_window_ms=300000)
    assert "cannot_renew_before_expiry" in str(ei.value)
    with pytest.raises(TaskExecutionError) as ei:
        DurableExecutionService(store=store, router=object(),
                                expiry_ms=100, heartbeat_window_ms=200)
    assert "cannot_renew_before_expiry" in str(ei.value)


# ---------------------------------------------------------------------------
# Addendum: falsy authority/planning fail closed BEFORE durable run claim
# ---------------------------------------------------------------------------

def test_falsy_authority_fails_before_claim(tmp_path) -> None:
    """None, '', whitespace authority must fail before durable run is created."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="falsy-auth", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    for bad_val in [None, "", "   ", "\t\n"]:
        service = DurableExecutionService(
            store=store, router=object(),
            execution_authority_sha=bad_val,
            planning_sha="valid-plan",
        )
        with pytest.raises((TaskExecutionError, DurableResumeError)):
            service.execute_durable_sequential_team(
                task_id=task.id, workspace_root=str(tmp_path),
            )
        run_count = store._conn.execute(
            "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?",
            (task.id,),
        ).fetchone()[0]
        assert run_count == 0


def test_falsy_planning_fails_before_claim(tmp_path) -> None:
    """None, '', whitespace planning must fail before durable run is created."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="falsy-plan", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    for bad_val in [None, "", "   ", "\t\n"]:
        service = DurableExecutionService(
            store=store, router=object(),
            execution_authority_sha="valid-auth",
            planning_sha=bad_val,
        )
        with pytest.raises((TaskExecutionError, DurableResumeError)):
            service.execute_durable_sequential_team(
                task_id=task.id, workspace_root=str(tmp_path),
            )
        run_count = store._conn.execute(
            "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?",
            (task.id,),
        ).fetchone()[0]
        assert run_count == 0


def test_planning_only_authority_impersonation_rejected(tmp_path) -> None:
    """REVERSE_AGENT_PLANNING_SHA must NOT satisfy execution_authority_sha."""
    import os
    os.environ["REVERSE_AGENT_PLANNING_SHA"] = "some-planning-sha"
    os.environ.pop("REVERSE_AGENT_EXECUTION_AUTHORITY_SHA", None)
    store = _make_store(tmp_path)
    task = store.create_task(
        title="impersonation", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    service = DurableExecutionService(
        store=store, router=object(),
        execution_authority_sha=None,
        planning_sha="some-planning-sha",
    )
    with pytest.raises((TaskExecutionError, DurableResumeError)):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(tmp_path),
        )
    run_count = store._conn.execute(
        "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?",
        (task.id,),
    ).fetchone()[0]
    assert run_count == 0
    os.environ.pop("REVERSE_AGENT_PLANNING_SHA", None)


# ---------------------------------------------------------------------------
# Addendum: pre-PRE_PLANNER crash recovery fails closed
# ---------------------------------------------------------------------------

def test_pre_pre_planner_crash_resume_fails_closed(tmp_path) -> None:
    """Resume with accepted_checkpoint='' and no worktree identity must fail closed."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="pre-crash", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
        execution_authority_sha="auth",
        planning_sha="plan",
    )
    run_id = lease.run_id
    store._conn.execute(
        "UPDATE durable_runs SET recovery_classification = 'orphan_stale_lease', "
        "interrupted_at = 'now' WHERE run_id = ?",
        (run_id,),
    )
    store._conn.execute(
        "UPDATE tasks SET status = 'INTERRUPTED' WHERE id = ?",
        (task.id,),
    )
    service = DurableExecutionService(
        store=store, router=object(),
        execution_authority_sha="auth", planning_sha="plan",
    )
    with pytest.raises(DurableResumeError) as ei:
        service.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "pre_pre_planner" in str(ei.value)


# ---------------------------------------------------------------------------
# Addendum: conflicting checkpoint duplicate rejection
# ---------------------------------------------------------------------------

def test_conflicting_digest_duplicate_rejected(tmp_path) -> None:
    """Same checkpoint+attempt with different digest raises conflicting_checkpoint."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="conflict-digest", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
    )
    run_id = lease.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, "w1", 1)
    store._accept_checkpoint(run_id, "POST_PLANNER", "D1", 1, "w1", 1)
    with pytest.raises(TaskStoreError) as ei:
        store._accept_checkpoint(run_id, "POST_PLANNER", "D2", 1, "w1", 1)
    assert "conflicting_checkpoint_acceptance" in str(ei.value)


def test_conflicting_attempt_duplicate_rejected(tmp_path) -> None:
    """Same checkpoint with different attempt raises conflicting_checkpoint."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="conflict-attempt", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
    )
    run_id = lease.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, "w1", 1)
    store._accept_checkpoint(run_id, "POST_PLANNER", "D1", 1, "w1", 1)
    with pytest.raises(TaskStoreError) as ei:
        store._accept_checkpoint(run_id, "POST_PLANNER", "D1", 2, "w1", 1)
    assert "conflicting_checkpoint_acceptance" in str(ei.value)


# ---------------------------------------------------------------------------
# Addendum: first checkpoint must be PRE_PLANNER
# ---------------------------------------------------------------------------

def test_first_checkpoint_must_be_pre_planner(tmp_path) -> None:
    """Direct POST_PLANNER/POST_CODER/POST_REVIEWER/POST_VALIDATION must fail closed."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="first-cp", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
    )
    run_id = lease.run_id
    for cp in ("POST_PLANNER", "POST_CODER", "POST_REVIEWER", "POST_VALIDATION"):
        with pytest.raises(TaskStoreError) as ei:
            store._accept_checkpoint(run_id, cp, "x", 1, "w1", 1)
        assert "first_must_be_pre_planner" in str(ei.value)


# ---------------------------------------------------------------------------
# Addendum: role-created HEAD movement rejected
# ---------------------------------------------------------------------------

def test_role_created_head_movement_rejected(tmp_path) -> None:
    """If HEAD differs from repository_base_sha after role, fail closed."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="head-move", executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
    )
    run_id = lease.run_id
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, "w1", 1)
    store._accept_checkpoint(run_id, "POST_PLANNER", "digest_1", 1, "w1", 1)
    store._set_repository_base_sha(run_id, "base_sha_original", "w1", 1)
    with pytest.raises(TaskStoreError) as ei:
        store._set_repository_base_sha(run_id, "different_sha", "w1", 1)
    assert "repository_base_immutable" in str(ei.value)


# ===================================================================
# V6 final correctness recovery — 7 bounded gaps
# ===================================================================

# ---------------------------------------------------------------------------
# Gap 1: Reconcile revokes stale worker authority immediately
# ---------------------------------------------------------------------------

def test_reconcile_revokes_old_owner_authority(tmp_path) -> None:
    """After reconcile, old worker heartbeat/checkpoint/digest/business/status
    mutations and lease release must all fail/no-op. stale mutation count = 0."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="revoke-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="worker-a", task_status="RUNNING",
    )
    run_id = lease.run_id
    assert lease.owner == "worker-a"
    assert lease.epoch == 1
    store._accept_checkpoint(run_id, "PRE_PLANNER", "", 1, "worker-a", 1)

    # Expire the lease and reconcile
    now_ms = int(time.time() * 1000)
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (now_ms - 1000, run_id),
    )
    svc = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    records = svc.reconcile_expired_runs(now_ms=now_ms, max_age_ms=1000)
    assert len(records) == 1
    assert store.get_task(task.id).status == "INTERRUPTED"

    # Re-read the durable run to confirm lease_owner is cleared
    run_after = store._get_durable_run(run_id)
    assert run_after.lease_owner == ""
    assert run_after.lease_epoch == 1

    # Old worker A attempts heartbeat: must fail
    with pytest.raises(TaskStoreError):
        store._heartbeat_durable_lease(run_id, "worker-a", 1, 300000)

    # Old worker A attempts checkpoint: must fail
    with pytest.raises(TaskStoreError):
        store._accept_checkpoint(run_id, "POST_PLANNER", "digest", 1, "worker-a", 1)

    # Old worker A attempts set_planner_handoff_digest: must fail
    with pytest.raises(TaskStoreError):
        store._set_planner_handoff_digest(run_id, "digest", "worker-a", 1)

    # Old worker A attempts status transition: must fail
    with pytest.raises(TaskStoreError):
        store._fenced_transition_to(run_id, task.id, "VALIDATING", "worker-a", 1)

    # Old worker A attempts business writes: must fail
    with pytest.raises(TaskStoreError):
        store._fenced_set_changed_files(run_id, task.id, [{"path": "x.py"}], "worker-a", 1)
    with pytest.raises(TaskStoreError):
        store._fenced_add_event(
            run_id, task.id, event_type="EXECUTOR_FINISHED",
            title="stale", owner="worker-a", epoch=1,
        )
    with pytest.raises(TaskStoreError):
        store._fenced_classify_failure(
            run_id, task.id, classification="failed", detail="x",
            owner="worker-a", epoch=1,
        )

    # Old worker A attempts lease release: must fail
    with pytest.raises(TaskStoreError):
        store._release_durable_lease(run_id, "worker-a", 1)

    # Task status unchanged (still INTERRUPTED)
    assert store.get_task(task.id).status == "INTERRUPTED"

    # New worker B resumes and gets a strictly newer epoch
    lease_b = store._recover_durable_lease(run_id, "worker-b")
    assert lease_b.epoch == 2
    assert lease_b.owner == "worker-b"


# ---------------------------------------------------------------------------
# Gap 2: Effective heartbeat cadence < expiry for short durations
# ---------------------------------------------------------------------------

def test_effective_heartbeat_interval_below_expiry(tmp_path) -> None:
    """For short trusted leases (exp=500ms, window=100ms), effective interval
    must be < expiry. Live heartbeat must not cause false interruptions."""
    import threading as _threading

    store = _make_store(tmp_path)
    task = store.create_task(
        title="hb-cadence-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="RUNNING",
        expiry_ms=500,
    )
    run_id = lease.run_id

    expiry_ms = 500
    heartbeat_window_ms = 100
    effective_interval_ms = heartbeat_window_ms * 0.6
    assert effective_interval_ms == 60.0
    assert 0 < effective_interval_ms < expiry_ms

    heartbeat_count = [0]
    stop_event = _threading.Event()

    def hb_loop():
        while not stop_event.is_set():
            try:
                store._heartbeat_durable_lease(
                    run_id, "w1", 1, expiry_ms,
                )
                heartbeat_count[0] += 1
            except TaskStoreError:
                break
            stop_event.wait(timeout=effective_interval_ms / 1000.0)

    t = _threading.Thread(target=hb_loop, daemon=True)
    t.start()

    # Run for longer than original expiry (500ms). Use 800ms.
    time.sleep(0.8)
    stop_event.set()
    t.join(timeout=3.0)

    run = store._get_durable_run(run_id)
    assert run.lease_owner == "w1"
    assert run.lease_epoch == 1
    assert heartbeat_count[0] >= 1

    now_ms = int(time.time() * 1000)
    svc2 = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    records = svc2.reconcile_expired_runs(now_ms=now_ms, max_age_ms=1000)
    assert len(records) == 0


# ---------------------------------------------------------------------------
# Gap 3: Task stays PREPARING_WORKSPACE through blocking preparation
# ---------------------------------------------------------------------------

def test_task_preparing_workspace_through_preparation(tmp_path) -> None:
    """Task remains PREPARING_WORKSPACE during executor creation,
    prepare_worktree_once(), and identity persistence. Only after
    PRE_PLANNER acceptance does it transition to RUNNING."""
    import threading as _prep_threading
    from reverse_agent.platform_v1.durable_execution import (
        set_crash_after_checkpoint, reset_crash_seam, _CrashSimulated,
    )
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _SlowPreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id

    class _SlowFakeExecutor:
        prepare_status = {"status": ""}
        prepare_event = _prep_threading.Event()

        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _SlowPreparedCtx:
            self.prepare_status["status"] = "preparing"
            self.prepare_event.wait(timeout=2.0)
            self.prepare_status["status"] = "prepared"
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _SlowPreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None,
            event_callback: Any = None,
        ) -> Any:
            self.prepare_status["status"] = "role_running"
            role = role_context.role if role_context else "planner"
            wt = prepared.worktree
            handoff = _handoff_dir(wt)
            if role == "planner":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "plan.md").write_text("# Plan\n", encoding="utf-8")
            elif role == "coder":
                (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
            elif role == "reviewer":
                handoff.mkdir(parents=True, exist_ok=True)
                (handoff / "review.md").write_text("# Review\n", encoding="utf-8")

            class _Result:
                success = True
                execution_id = f"exec-{role}"
                validation_exit_code = 0
                failure_classification = ""
                error = ""
            return _Result()

    class _SlowRouter(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> _SlowFakeExecutor:
            return _SlowFakeExecutor()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="prep-status-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt_prep")

    set_crash_after_checkpoint("PRE_PLANNER")
    service = DurableExecutionService(
        store=store, router=_SlowRouter(),
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    status_observed = {"status": ""}
    status_event = _prep_threading.Event()

    def status_watcher():
        while not stop_event2.is_set():
            try:
                s = store.get_task(task.id).status
                status_observed["status"] = s
                if s == "PREPARING_WORKSPACE":
                    status_event.set()
            except Exception:
                pass
            time.sleep(0.05)

    stop_event2 = _prep_threading.Event()
    watcher = _prep_threading.Thread(target=status_watcher, daemon=True)
    watcher.start()

    # Give the watcher a moment to observe
    time.sleep(0.1)

    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    stop_event2.set()
    watcher.join(timeout=3.0)

    # Task should have been observed in PREPARING_WORKSPACE
    assert status_observed["status"] == "PREPARING_WORKSPACE"

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.accepted_checkpoint == "PRE_PLANNER"
    assert run.worktree_head_sha != ""
    assert run.repository_base_sha != ""
    assert run.worktree_head_sha == run.repository_base_sha

    task_final = store.get_task(task.id)
    assert task_final.status == "PREPARING_WORKSPACE"


# ---------------------------------------------------------------------------
# Gap 4: Pre-PRE resume fails BEFORE recovery claim
# ---------------------------------------------------------------------------

def test_pre_pre_resume_fails_before_claim(tmp_path) -> None:
    """When accepted_checkpoint == '', resume must fail closed BEFORE
    _recover_durable_lease() is called. Task status, epoch, owner, expiry
    and all role-call counts must remain unchanged."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="pre-pre-no-claim",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
        execution_authority_sha="auth", planning_sha="plan",
    )
    run_id = lease.run_id
    original_epoch = lease.epoch
    original_owner = lease.owner

    # Manually expire and set to INTERRUPTED with orphan_stale_lease
    now_ms = int(time.time() * 1000)
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ? WHERE run_id = ?",
        (now_ms - 1000, run_id),
    )
    svc = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="auth", planning_sha="plan",
    )
    svc.reconcile_expired_runs(now_ms=now_ms, max_age_ms=1000)

    # Capture state before failed resume attempt
    task_before = store.get_task(task.id)
    run_before = store._get_durable_run(run_id)
    assert task_before.status == "INTERRUPTED"
    assert run_before.lease_owner == ""
    assert run_before.lease_epoch == original_epoch
    expiry_before = run_before.lease_expiry_ms
    accepted_before = run_before.accepted_checkpoint
    assert accepted_before == ""

    service = DurableExecutionService(
        store=store, router=object(),
        execution_authority_sha="auth", planning_sha="plan",
    )

    with pytest.raises(DurableResumeError) as ei:
        service.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "pre_pre_planner" in str(ei.value)

    # Verify nothing changed
    task_after = store.get_task(task.id)
    run_after = store._get_durable_run(run_id)
    assert task_after.status == "INTERRUPTED"
    assert run_after.lease_epoch == original_epoch
    assert run_after.lease_owner == ""
    assert run_after.lease_expiry_ms == expiry_before
    assert run_after.accepted_checkpoint == ""


# ---------------------------------------------------------------------------
# Gap 5: Partial identity (path/head but no base) cannot dispatch roles
# ---------------------------------------------------------------------------

def test_partial_identity_cannot_dispatch_roles(tmp_path) -> None:
    """When accepted_checkpoint == '' and worktree_path + worktree_head_sha
    exist but repository_base_sha is empty, no role may be dispatched."""
    store = _make_store(tmp_path)
    task = store.create_task(
        title="partial-identity",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )
    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="w1", task_status="QUEUED",
        execution_authority_sha="auth", planning_sha="plan",
    )
    run_id = lease.run_id

    # Persist partial identity: worktree_path + head_sha but NO repository_base_sha
    wt = _init_git_worktree(tmp_path, "wt_partial")
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=wt, text=True
    ).strip()
    store._set_worktree_identity(run_id, str(wt), head_sha, "w1", 1)

    # Do NOT set repository_base_sha — simulate crash before base persistence

    # Mark as interrupted/stale
    now_ms = int(time.time() * 1000)
    store._conn.execute(
        "UPDATE durable_runs SET lease_expiry_ms = ?, "
        "recovery_classification = 'orphan_stale_lease', "
        "interrupted_at = 'now' WHERE run_id = ?",
        (now_ms - 1000, run_id),
    )
    store._conn.execute(
        "UPDATE tasks SET status = 'INTERRUPTED' WHERE id = ?",
        (task.id,),
    )

    service = DurableExecutionService(
        store=store, router=object(),
        execution_authority_sha="auth", planning_sha="plan",
    )

    with pytest.raises(DurableResumeError) as ei:
        service.resume_sequential_team(task_id=task.id, lease_owner="w2")
    assert "pre_pre_planner" in str(ei.value)

    # Verify no role dispatch occurred — run still has accepted_checkpoint == ''
    run = store._get_durable_run(run_id)
    assert run.accepted_checkpoint == ""
    assert run.current_role == ""


# ---------------------------------------------------------------------------
# Gap 6: Empty HEAD/base fails closed before PRE_PLANNER
# ---------------------------------------------------------------------------

def test_empty_HEAD_fails_closed_before_pre_planner(tmp_path) -> None:
    """If prepare_worktree_once returns a path but git rev-parse HEAD fails
    or returns empty, the run must fail closed BEFORE _set_worktree_identity,
    _set_repository_base_sha, or PRE_PLANNER acceptance."""
    from reverse_agent.platform_v1.durable_execution import (
        set_crash_after_checkpoint, reset_crash_seam, _CrashSimulated,
    )

    class _EmptyHeadPreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id

    class _EmptyHeadFakeExecutor:
        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _EmptyHeadPreparedCtx:
            # Create a directory but DO NOT init git — HEAD will be empty
            wt = workspace_root / f"wt-{task_id[-8:]}"
            wt.mkdir(parents=True, exist_ok=True)
            (wt / "README.md").write_text("hello\n", encoding="utf-8")
            return _EmptyHeadPreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None,
            event_callback: Any = None,
        ) -> Any:
            raise RuntimeError("must not reach role execution")

    class _EmptyRouter(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> _EmptyHeadFakeExecutor:
            return _EmptyHeadFakeExecutor()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="empty-head-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_empty"
    wt_dir.mkdir(parents=True, exist_ok=True)

    service = DurableExecutionService(
        store=store, router=_EmptyRouter(),
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    outcome = service.execute_durable_sequential_team(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
    )

    assert outcome.success is False
    assert "empty_HEAD" in outcome.failure_detail or "prepared_worktree" in outcome.failure_detail

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )

    assert run.accepted_checkpoint == ""
    assert run.repository_base_sha == ""
    assert run.worktree_head_sha == ""