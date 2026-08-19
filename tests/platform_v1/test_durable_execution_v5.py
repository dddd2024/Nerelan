"""V5 provider-free repair tests for Issue #230 durable single execution.

These tests verify the V5 repair requirements:
A. Non-fenced helper poison: _dispatch_executor is NEVER called
B. Checkpoint matrix: explicit resume state machine
C. Prepare callback fencing
D. Facade capability safety
E. Executor evidence through fenced acceptance
F. Task validation truth readback
G. Terminal status (READY_FOR_REVIEW vs READY_FOR_REVIEW_FIXTURE)
H. Ambiguous PENDING op zero-dispatch
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

from reverse_agent.platform_v1.durable_execution import (
    _DurableFencedExecutorStore,
    _DurableFencedCallback,
    DurableExecutionService,
    DurableResumeError,
    _CrashSimulated,
    reset_crash_seam,
    set_crash_after_checkpoint,
    _digest as _dur_digest,
    _json_payload as _dur_json_payload,
)
from reverse_agent.platform_v1.run_store import TaskStore, TaskStoreError
from reverse_agent.platform_v1.task_execution import (
    TaskExecutionError,
    TaskExecutionOutcome,
)
from reverse_agent.platform_v1.task_runtime import (
    ExecutorRouter,
    FixtureExecutorResult,
    LocalValidationRunner,
)
from reverse_agent.platform_v1.opencode_executor import (
    _collect_product_diff,
    _collect_final_product_files,
    handoff_dir as _handoff_dir,
)


# ---------------------------------------------------------------------------
# Fake executor for single-mode
# ---------------------------------------------------------------------------

class _FakePreparedCtx:
    def __init__(self, worktree: Path, execution_id: str = "") -> None:
        self.worktree = worktree
        self.execution_id = execution_id or f"exec-{worktree.name}"


class _FakeResult:
    def __init__(
        self,
        success: bool = True,
        execution_id: str = "exec-fake",
        validation_exit_code: int = 0,
        validation_command_id: str = "git_diff_check",
        validation_output_digest: str = "",
        changed_files: list = None,
        error: str = "",
        failure_classification: str = "",
    ) -> None:
        self.success = success
        self.execution_id = execution_id
        self.validation_exit_code = validation_exit_code
        self.validation_command_id = validation_command_id
        self.validation_output_digest = validation_output_digest
        self.changed_files = changed_files or []
        self.error = error
        self.failure_classification = failure_classification


class FakeSingleExecutor:
    """Provider-free executor for single-mode tests."""

    def __init__(
        self,
        *,
        success: bool = True,
        validation_exit_code: int = 0,
        mutation_cmd: str = "append_to_file",
        fixture_path: str = "fixture.txt",
    ) -> None:
        self.success = success
        self.validation_exit_code = validation_exit_code
        self.mutation_cmd = mutation_cmd
        self.fixture_path = fixture_path
        self.prepare_calls: list[tuple[str, Path]] = []
        self.execute_calls: list[tuple[str, str]] = []
        self._dispatch_executor_calls: int = 0

    def prepare_worktree_once(
        self, task_id: str, workspace_root: Path, callback: Any = None
    ) -> _FakePreparedCtx:
        self.prepare_calls.append((task_id, workspace_root))
        wt = workspace_root / f"wt-{task_id[-8:]}"
        wt.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=wt, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@local"],
            cwd=wt, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=wt, capture_output=True, check=True,
        )
        (wt / "README.md").write_text("hello\n", encoding="utf-8")
        (wt / "product.py").write_text("# product\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=wt, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"],
            cwd=wt, capture_output=True, check=True,
        )
        return _FakePreparedCtx(worktree=wt)

    def execute_role_prepared(
        self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
    ) -> _FakeResult:
        wt = prepared.worktree
        handoff = _handoff_dir(wt)
        if role_context and role_context.role == "planner":
            handoff.mkdir(parents=True, exist_ok=True)
            (handoff / "plan.md").write_text("# Plan\nStep 1\n", encoding="utf-8")
        elif role_context and role_context.role == "coder":
            (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
        elif role_context and role_context.role == "reviewer":
            handoff.mkdir(parents=True, exist_ok=True)
            (handoff / "review.md").write_text("# Review\nOK\n", encoding="utf-8")
        elif role_context and role_context.role == "executor":
            (wt / "product.py").write_text("def hello(): pass\n", encoding="utf-8")
        return _FakeResult(
            success=self.success,
            validation_exit_code=self.validation_exit_code,
            validation_output_digest="",
            changed_files=[{"path": "product.py", "status": "modified", "additions": 1, "deletions": 0, "diff_digest": "abc"}],
        )

    def execute(
        self,
        task_id: str,
        store: Any,
        *,
        workspace_root: str = "",
        event_callback: Any = None,
    ) -> FixtureExecutorResult:
        self.execute_calls.append((task_id, workspace_root))
        root_path = Path(workspace_root)
        root_path.mkdir(parents=True, exist_ok=True)
        worktree = root_path / task_id
        if worktree.exists():
            import shutil
            shutil.rmtree(worktree)
        worktree.mkdir(parents=True, exist_ok=True)

        execution_id = f"exec-{task_id}"
        if event_callback:
            event_callback(task_id, {
                "type": "WORKSPACE_READY",
                "title": "Workspace ready",
                "description": f"Created {worktree}",
                "metadata": {"workspace": str(worktree)},
            })

        try:
            subprocess.run(["git", "init", "-q"], cwd=worktree, capture_output=True, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@local"],
                cwd=worktree, capture_output=True, check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=worktree, capture_output=True, check=True,
            )
            fixture_file = worktree / self.fixture_path
            fixture_file.write_text("provider-free fixture\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=worktree, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=worktree, capture_output=True, check=True)
            fixture_file.write_text("provider-free fixture\nappended\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=worktree, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "mutate"], cwd=worktree, capture_output=True, check=True)

            runner = LocalValidationRunner()
            exit_code, output, digest = runner.run(
                task_id=task_id,
                command_id="git_diff_check",
                cwd=str(worktree),
            )

            if event_callback:
                event_callback(task_id, {
                    "type": "EXECUTOR_FINISHED",
                    "title": "Fixture done",
                    "description": f"exit={exit_code}",
                    "metadata": {"execution_id": execution_id},
                })

            changed = _collect_product_diff(worktree)
            return FixtureExecutorResult(
                success=True,
                validation_command_id="git_diff_check",
                validation_exit_code=exit_code,
                validation_output_digest=digest,
                changed_files=list(changed),
                error="",
                validation_output_summary="",
            )
        except Exception:
            return FixtureExecutorResult(
                success=False,
                validation_command_id="git_diff_check",
                validation_exit_code=-1,
                validation_output_digest="",
                changed_files=[],
                error="executor_failed",
                validation_output_summary="",
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path) -> TaskStore:
    return TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))


def _init_git_worktree(tmp_path: Path, name: str = "wt") -> Path:
    wt = tmp_path / name
    wt.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=wt, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@local"],
        cwd=wt, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=wt, capture_output=True, check=True,
    )
    (wt / "README.md").write_text("hello\n", encoding="utf-8")
    (wt / "product.py").write_text("# product\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=wt, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=wt, capture_output=True, check=True)
    return wt


def _expire_and_reconcile(store: TaskStore, task_id: str) -> None:
    now_ms = int(time.time() * 1000)
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
    svc = DurableExecutionService(
        store=store, router=ExecutorRouter(),
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc.reconcile_expired_runs(now_ms=now_ms, max_age_ms=1000)


def _make_durable_service(tmp_path: Path) -> DurableExecutionService:
    store = _make_store(tmp_path)
    return DurableExecutionService(
        store=store,
        router=ExecutorRouter(),
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )


def _make_router(fake: FakeSingleExecutor) -> ExecutorRouter:
    class RR(ExecutorRouter):
        def create_executor(
            self, *, executor_kind: str = "opencode", **kwargs: Any
        ) -> FakeSingleExecutor:
            return fake
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()
    return RR()


# ===========================================================================
# A. NON-FENCED HELPER POISON TEST
# ===========================================================================

def test_dispatch_executor_never_called_opencode_first_run(tmp_path) -> None:
    """Poison _dispatch_executor and prove opencode-like first-run still works."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    original_dispatch = type(store.__class__.__mro__[0] if False else None).__dict__.get("_dispatch_executor")

    poison_count = [0]

    class PoisonedExecutionService:
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED:_dispatch_executor_must_not_be_called")

    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        pass
    P._dispatch_executor = PoisonedExecutionService._dispatch_executor

    task = store.create_task(
        title="poison-opencode-first",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc._execution_service = P(store=store, router=router)

    wt_dir = _init_git_worktree(tmp_path, "wt-poison-oc")

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert isinstance(outcome, TaskExecutionOutcome)
    assert outcome.success is True
    assert poison_count[0] == 0


def test_dispatch_executor_never_called_fixture_first_run(tmp_path) -> None:
    """Poison _dispatch_executor and prove fixture first-run still works."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    poison_count = [0]

    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED")

    task = store.create_task(
        title="poison-fixture-first",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc._execution_service = P(store=store, router=router)

    wt_dir = tmp_path / "ws-poison-fix"
    wt_dir.mkdir(parents=True, exist_ok=True)

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert isinstance(outcome, TaskExecutionOutcome)
    assert outcome.success is True
    assert poison_count[0] == 0


def test_dispatch_executor_never_called_opencode_resume_pre_planner(
    tmp_path, monkeypatch
) -> None:
    """Poison _dispatch_executor; opencode PRE_PLANNER resume still works."""
    reset_crash_seam()
    store = _make_store(tmp_path)
    monkeypatch.setattr(
        "reverse_agent.platform_v1.opencode_executor.resolve_opencode_cli",
        lambda exe=None: ("synthetic-opencode", False),
    )

    poison_count = [0]

    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED")

    task = store.create_task(
        title="poison-opencode-resume",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc._execution_service = P(store=store, router=router)

    wt_dir = _init_git_worktree(tmp_path, "wt-poison-oc-resume")

    set_crash_after_checkpoint("PRE_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc2._execution_service = P(store=store, router=router2)

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome.success is True
    assert poison_count[0] == 0


def test_dispatch_executor_never_called_fixture_resume_pre_planner(tmp_path) -> None:
    """Poison _dispatch_executor; fixture PRE_PLANNER resume still works."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    poison_count = [0]

    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED")

    task = store.create_task(
        title="poison-fixture-resume",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc._execution_service = P(store=store, router=router)

    wt_dir = tmp_path / "ws-poison-fix-resume"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint("PRE_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc2._execution_service = P(store=store, router=router2)

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome.success is True
    assert poison_count[0] == 0


# ===========================================================================
# B. CHECKPOINT MATRIX
# ===========================================================================

@pytest.mark.parametrize(
    "checkpoint",
    ["POST_PLANNER", "POST_CODER", "POST_REVIEWER"],
)
def test_fixture_resume_checkpoint_no_dispatch(tmp_path, checkpoint) -> None:
    """Resume from POST_PLANNER/POST_CODER/POST_REVIEWER must NOT dispatch executor."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    poison_count = [0]

    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED")

    task = store.create_task(
        title=f"resume-{checkpoint.lower()}",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc._execution_service = P(store=store, router=router)

    wt_dir = tmp_path / f"ws-{checkpoint}"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint(checkpoint)
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc2._execution_service = P(store=store, router=router2)

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome.success is True
    assert poison_count[0] == 0

    cps = store._get_durable_checkpoints(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    cp_names = [c.checkpoint_name for c in cps]
    assert "POST_VALIDATION" in cp_names
    order = [cp_names.index("PRE_PLANNER"), cp_names.index("POST_VALIDATION")]
    assert order[0] < order[1]


def test_fixture_resume_post_validation_returns_terminal(tmp_path) -> None:
    """Resume from POST_VALIDATION returns terminal without any dispatch."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="resume-post-val",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-post-val"
    wt_dir.mkdir(parents=True, exist_ok=True)

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
    )
    assert outcome.success is True

    task_after = store.get_task(task.id)
    assert task_after.status == "READY_FOR_REVIEW_FIXTURE"

    run_row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    assert run_row is not None

    outcome2 = svc.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome2.success is True
    assert outcome2.validation_exit_code == 0


def test_resume_no_unbound_local_error(tmp_path) -> None:
    """Resume from POST_PLANNER must not raise UnboundLocalError."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="no-unbound",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-no-unbound"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint("POST_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome is not None
    assert outcome.success is True


# ===========================================================================
# C. PREPARE CALLBACK FENCING
# ===========================================================================

def test_prepare_uses_fenced_callback(tmp_path) -> None:
    """OpenCode first-run prepare_worktree_once receives fenced callback."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    class RecordingCallback:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []
        def __call__(self, task_id: str, event: dict[str, Any]) -> None:
            self.calls.append({"task_id": task_id, "event": event})

    cb = RecordingCallback()

    task = store.create_task(
        title="prepare-cb-fence",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()

    class CallbackRouter:
        def __init__(self, fake: FakeSingleExecutor) -> None:
            self.fake = fake
            self._registry = {}

        def create_executor(
            self, *, executor_kind: str = "opencode", **kwargs: Any
        ) -> FakeSingleExecutor:
            return self.fake

        def dispatch_execute(self, *a, **kw):
            raise NotImplementedError()

    router = CallbackRouter(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt-prepare-cb")

    original_prepare = fake.prepare_worktree_once
    received_callback = [None]

    def wrapped_prepare(task_id, workspace_root, callback):
        received_callback[0] = callback
        return original_prepare(task_id, workspace_root, callback)
    fake.prepare_worktree_once = wrapped_prepare

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )

    assert received_callback[0] is not None
    assert isinstance(received_callback[0], _DurableFencedCallback)


def test_stale_prepare_callback_no_events(tmp_path) -> None:
    """Advancing epoch after prepare means stale callback events are rejected."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="stale-prepare-cb",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt-stale-cb")

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert outcome.success is True

    run_row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    run_id = run_row["run_id"]

    events_before = store._conn.execute(
        "SELECT COUNT(*) as cnt FROM task_events WHERE task_id = ?",
        (task.id,),
    ).fetchone()["cnt"]

    lease = store._recover_durable_lease(run_id, "new_owner")

    stale_cb = _DurableFencedCallback(
        store, run_id, task.id,
        owner="old_owner", epoch=1,
    )
    stale_cb(task.id, {"type": "WORKSPACE_READY", "title": "stale"})

    events_after = store._conn.execute(
        "SELECT COUNT(*) as cnt FROM task_events WHERE task_id = ?",
        (task.id,),
    ).fetchone()["cnt"]

    assert events_after == events_before


# ===========================================================================
# D. FACADE CAPABILITY SAFETY
# ===========================================================================

def test_facade_allows_get_task(tmp_path) -> None:
    """Facade allows get_task for the bound task_id."""
    store = _make_store(tmp_path)
    task = store.create_task(title="facade-test", executor_kind="opencode", orchestration_mode="single")

    facade = _DurableFencedExecutorStore(store, "run-1", task.id, "owner", 1)
    result = facade.get_task(task.id)
    assert result.id == task.id


def test_facade_rejects_wrong_task_id(tmp_path) -> None:
    """Facade rejects get_task for a different task_id."""
    store = _make_store(tmp_path)
    task = store.create_task(title="facade-test", executor_kind="opencode", orchestration_mode="single")

    facade = _DurableFencedExecutorStore(store, "run-1", task.id, "owner", 1)
    with pytest.raises(TaskStoreError):
        facade.get_task("different-task-id")


def test_facade_allows_fenced_add_evidence(tmp_path) -> None:
    """Facade add_evidence goes through _fenced_add_evidence."""
    store = _make_store(tmp_path)
    task = store.create_task(title="facade-ev", executor_kind="opencode", orchestration_mode="single")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="owner", expiry_ms=300000,
        execution_authority_sha="auth", planning_sha="plan",
    )

    facade = _DurableFencedExecutorStore(
        store, lease.run_id, task.id, lease.owner, lease.epoch
    )

    task_after = facade.add_evidence(
        task.id,
        category="Executor",
        label="executor_kind",
        value="opencode",
        status="pass",
        detail="test",
    )

    evidence = store._conn.execute(
        "SELECT * FROM task_evidence WHERE task_id = ?",
        (task.id,),
    ).fetchall()
    assert len(evidence) >= 1
    assert evidence[-1]["category"] == "Executor"


def test_facade_rejects_wrong_task_evidence(tmp_path) -> None:
    """Facade rejects add_evidence for a different task_id."""
    store = _make_store(tmp_path)
    task = store.create_task(title="facade-ev-wrong", executor_kind="opencode", orchestration_mode="single")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="owner", expiry_ms=300000,
        execution_authority_sha="auth", planning_sha="plan",
    )

    facade = _DurableFencedExecutorStore(
        store, lease.run_id, task.id, lease.owner, lease.epoch
    )

    with pytest.raises(TaskStoreError):
        facade.add_evidence(
            "wrong-task-id",
            category="Test", label="test", value="val", status="pass",
        )


def test_facade_no_getattr_passthrough(tmp_path) -> None:
    """Facade must NOT have __getattr__ passthrough to TaskStore."""
    store = _make_store(tmp_path)
    task = store.create_task(title="facade-passthrough", executor_kind="opencode", orchestration_mode="single")

    facade = _DurableFencedExecutorStore(store, "run-1", task.id, "owner", 1)

    forbidden_attrs = [
        "set_state", "transition_to", "set_changed_files",
        "set_validation_result", "classify_failure", "create_task",
        "create_task_and_execute", "_conn", "_lock", "_update_task_fields",
        "add_event", "get_events", "get_evidence", "transition_to",
    ]
    for attr in forbidden_attrs:
        assert not hasattr(facade, attr), f"Facade must not expose {attr}"


def test_facade_rejects_all_taskstore_methods(tmp_path) -> None:
    """Facade must not expose any TaskStore mutation methods."""
    store = _make_store(tmp_path)
    facade = _DurableFencedExecutorStore(store, "run-1", "task-1", "owner", 1)

    forbidden = [
        "set_state", "transition_to", "set_changed_files",
        "set_validation_result", "classify_failure", "create_task",
        "create_task_and_execute", "_conn", "_lock", "add_event",
        "set_planner_handoff_digest", "_accept_checkpoint",
    ]
    for name in forbidden:
        with pytest.raises((AttributeError, TaskStoreError)):
            getattr(facade, name)


# ===========================================================================
# E. EVIDENCE
# ===========================================================================

def test_executor_evidence_persisted_via_facade(tmp_path) -> None:
    """Valid executor evidence through facade appears in Task.evidence_refs."""
    store = _make_store(tmp_path)
    task = store.create_task(title="evidence-test", executor_kind="opencode", orchestration_mode="single")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="owner", expiry_ms=300000,
        execution_authority_sha="auth", planning_sha="plan",
    )

    facade = _DurableFencedExecutorStore(
        store, lease.run_id, task.id, lease.owner, lease.epoch
    )

    facade.add_evidence(
        task.id,
        category="Executor",
        label="executor_kind",
        value="opencode",
        status="pass",
        detail="executor action",
    )

    task_after = store.get_task(task.id)
    evidence_ids = [e.get("id") for e in task_after.evidence_refs]
    assert len(evidence_ids) >= 1


def test_stale_epoch_evidence_rejected(tmp_path) -> None:
    """Stale epoch evidence write mutates zero rows."""
    store = _make_store(tmp_path)
    task = store.create_task(title="stale-ev", executor_kind="opencode", orchestration_mode="single")
    store.transition_to(task.id, "PREPARING_WORKSPACE")
    store.transition_to(task.id, "RUNNING")

    lease = store._acquire_durable_lease(
        task_id=task.id, execution_id=task.execution_id,
        lease_owner="owner", expiry_ms=300000,
        execution_authority_sha="auth", planning_sha="plan",
    )

    facade = _DurableFencedExecutorStore(
        store, lease.run_id, task.id, lease.owner, lease.epoch
    )

    facade.add_evidence(
        task.id,
        category="Executor", label="test", value="v1", status="pass",
    )

    lease2 = store._recover_durable_lease(lease.run_id, "new_owner")

    stale_facade = _DurableFencedExecutorStore(
        store, lease.run_id, task.id,
        owner="old_owner", epoch=lease.epoch,
    )

    with pytest.raises(TaskStoreError):
        stale_facade.add_evidence(
            task.id,
            category="Executor", label="stale", value="v2", status="pass",
        )

    evidence_count = store._conn.execute(
        "SELECT COUNT(*) as cnt FROM task_evidence WHERE task_id = ?",
        (task.id,),
    ).fetchone()["cnt"]
    assert evidence_count == 1


# ===========================================================================
# F. TASK VALIDATION READBACK
# ===========================================================================

def test_fixture_first_run_task_validation(tmp_path) -> None:
    """Successful fixture first-run has task validation truth."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="val-readback-fixture",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-val-fixture"
    wt_dir.mkdir(parents=True, exist_ok=True)

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert outcome.success is True
    assert outcome.validation_exit_code == 0

    task_after = store.get_task(task.id)
    assert task_after.validation_command_id == "git_diff_check"
    assert task_after.validation_exit_code == 0


def test_opencode_first_run_task_validation(tmp_path) -> None:
    """Successful opencode first-run has task validation truth."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="val-readback-opencode",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt-val-oc")

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert outcome.success is True
    assert outcome.validation_exit_code == 0

    task_after = store.get_task(task.id)
    assert task_after.validation_command_id == "git_diff_check"
    assert task_after.validation_exit_code == 0


def test_fixture_resume_task_validation(tmp_path) -> None:
    """Successful fixture resume from PRE_PLANNER publishes task validation."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="val-readback-fixture-resume",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-val-fixture-resume"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint("PRE_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome.success is True

    task_after = store.get_task(task.id)
    assert task_after.validation_command_id == "git_diff_check"
    assert task_after.validation_exit_code == 0


def test_task_api_exposes_validation(tmp_path) -> None:
    """GET /api/tasks/{id} exposes validation_exit_code == 0."""
    reset_crash_seam()
    from reverse_agent.platform_v1.task_service import _handler_factory
    import json
    from http.server import ThreadingHTTPServer
    import threading
    import urllib.request

    store = _make_store(tmp_path)
    task = store.create_task(
        title="api-val-readback",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    handler_cls = _handler_factory(
        store, router,
        allowed_origin="http://localhost:4173",
        execution_authority_sha="test_authority_sha",
        planning_sha="test_planning_sha",
    )
    handler_cls.store = store
    handler_cls.router = router
    handler_cls.execution_authority_sha = "test_authority_sha"
    handler_cls.planning_sha = "test_planning_sha"

    wt_dir = tmp_path / "ws-api-val"
    wt_dir.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/tasks/{task.id}/execute",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

    server.shutdown()

    task_after = store.get_task(task.id)
    assert task_after.validation_exit_code == 0
    assert task_after.validation_command_id == "git_diff_check"


# ===========================================================================
# G. TERMINAL STATUS
# ===========================================================================

def test_fixture_first_run_terminal_ready_for_review_fixture(tmp_path) -> None:
    """Fixture first-run terminal status is READY_FOR_REVIEW_FIXTURE."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="terminal-fixture-first",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-terminal-fixture"
    wt_dir.mkdir(parents=True, exist_ok=True)

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert outcome.success is True

    task_after = store.get_task(task.id)
    assert task_after.status == "READY_FOR_REVIEW_FIXTURE"


def test_fixture_resume_terminal_ready_for_review_fixture(tmp_path) -> None:
    """Fixture resume terminal status is READY_FOR_REVIEW_FIXTURE."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="terminal-fixture-resume",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-terminal-fixture-resume"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint("POST_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    _expire_and_reconcile(store, task.id)

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    outcome = svc2.resume_single(
        task_id=task.id, lease_owner="w2",
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    assert outcome.success is True

    task_after = store.get_task(task.id)
    assert task_after.status == "READY_FOR_REVIEW_FIXTURE"


def test_opencode_terminal_ready_for_review(tmp_path) -> None:
    """Opencode first-run terminal status is READY_FOR_REVIEW."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="terminal-opencode",
        executor_kind="opencode",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = _init_git_worktree(tmp_path, "wt-terminal-oc")

    outcome = svc.execute_durable_single(
        task_id=task.id, workspace_root=str(wt_dir), lease_owner="test",
    )
    assert outcome.success is True

    task_after = store.get_task(task.id)
    assert task_after.status == "READY_FOR_REVIEW"


# ===========================================================================
# H. AMBIGUOUS PENDING OP
# ===========================================================================

def test_ambiguous_pending_op_zero_dispatch(tmp_path) -> None:
    """PENDING external op on resume -> zero dispatch, ambiguous_external_operation."""
    reset_crash_seam()
    store = _make_store(tmp_path)

    task = store.create_task(
        title="ambiguous-op",
        executor_kind="deterministic_fixture",
        orchestration_mode="single",
    )

    fake = FakeSingleExecutor()
    router = _make_router(fake)

    from reverse_agent.platform_v1.durable_execution import DurableExecutionService as DES
    svc = DES(
        store=store, router=router,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )

    wt_dir = tmp_path / "ws-ambiguous"
    wt_dir.mkdir(parents=True, exist_ok=True)

    set_crash_after_checkpoint("PRE_PLANNER")
    with pytest.raises(_CrashSimulated):
        svc.execute_durable_single(
            task_id=task.id, workspace_root=str(wt_dir), lease_owner="w1",
        )
    reset_crash_seam()

    run_row = store._conn.execute(
        "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    run_id = run_row["run_id"]

    idempotency_key = f"single-exec-{task.id}-{task.execution_id}"
    request_digest = _dur_digest(_dur_json_payload({
        "task_id": task.id,
        "execution_id": task.execution_id,
        "workspace_root": "",
        "repo_base": "",
    }))

    store._record_external_operation(
        operation_key=f"single-exec-{task.id}",
        idempotency_key=idempotency_key,
        request_digest=request_digest,
        run_id=run_id,
        task_id=task.id,
        owner="w1",
        epoch=1,
    )

    _expire_and_reconcile(store, task.id)

    poison_count = [0]
    from reverse_agent.platform_v1 import task_execution
    orig_cls = task_execution.TaskExecutionService

    class P(orig_cls):
        def _dispatch_executor(self, *a, **kw):
            poison_count[0] += 1
            raise RuntimeError("POISONED")

    fake2 = FakeSingleExecutor()
    router2 = _make_router(fake2)

    svc2 = DES(
        store=store, router=router2,
        execution_authority_sha="test_authority", planning_sha="test_planning",
    )
    svc2._execution_service = P(store=store, router=router2)

    outcome = svc2.resume_single(
        task_id=task.id,
        workspace_root="",
        lease_owner="w2",
        execution_authority_sha="test_authority",
        planning_sha="test_planning",
    )
    assert outcome.success is False
    assert outcome.failure_classification == "ambiguous_external_operation"
    assert poison_count[0] == 0
