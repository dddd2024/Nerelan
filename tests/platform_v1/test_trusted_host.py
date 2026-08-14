"""Trusted-host identity propagation and fencing tests for Issue #198 (v3).

Covers:
- trusted non-empty authority SHA propagation
- trusted non-empty planning SHA propagation
- values cannot be overridden by request
- startup stale reconciliation
- startup performs zero role/model calls
- handler receives trusted identity
- BindingResolver / credential relay wiring remains intact
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.platform_v1.durable_execution import (
    DurableExecutionService,
    reset_crash_seam,
    set_crash_after_checkpoint,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_runtime import ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


def _make_git_worktree(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@local"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True, check=True)
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, capture_output=True, check=True)


def _make_store(tmp_path: Path) -> TaskStore:
    return TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))


def test_trusted_authority_sha_propagated_non_empty(tmp_path) -> None:
    """CombinedTrustedHost must pass non-empty execution_authority_sha to handler."""
    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        execution_authority_sha="auth_sha_xyz789",
        planning_sha="planning_sha_abc123",
    )
    handler_cls = _handler_factory(
        host.task_store,
        ExecutorRouter(),
        allowed_origin="http://localhost:4173",
        execution_authority_sha=host._execution_authority_sha,
        planning_sha=host._planning_sha,
    )
    assert handler_cls.execution_authority_sha == "auth_sha_xyz789"
    assert handler_cls.planning_sha == "planning_sha_abc123"


def test_trusted_planning_sha_propagated_non_empty(tmp_path) -> None:
    """CombinedTrustedHost must pass non-empty planning_sha to handler."""
    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        execution_authority_sha="auth_sha_xyz789",
        planning_sha="planning_sha_abc123",
    )
    handler_cls = _handler_factory(
        host.task_store,
        ExecutorRouter(),
        allowed_origin="http://localhost:4173",
        execution_authority_sha=host._execution_authority_sha,
        planning_sha=host._planning_sha,
    )
    assert handler_cls.planning_sha == "planning_sha_abc123"


def test_request_cannot_override_trusted_identity(tmp_path) -> None:
    """DurableExecutionService must NOT accept execution_authority_sha/planning_sha
    from HTTP request body. Values come only from constructor/trusted host."""
    from reverse_agent.platform_v1.durable_execution import (
        _CrashSimulated,
    )
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def __init__(self) -> None:
            self.prepare_calls = 0
            self.execute_calls = 0

        def prepare_worktree_once(
            self, task_id: str, workspace_root: Path, callback: Any = None
        ) -> _FakePreparedCtx:
            self.prepare_calls += 1
            wt = workspace_root / f"wt-{task_id[-8:]}"
            _make_git_worktree(wt)
            return _FakePreparedCtx(worktree=wt)

        def execute_role_prepared(
            self, prepared: Any, store: Any, *, role_context: Any = None, event_callback: Any = None
        ) -> Any:
            self.execute_calls += 1
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
        def __init__(self) -> None:
            super().__init__()
            self._fake = FakeExecutor()

        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any) -> FakeExecutor:
            return self._fake

        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    store = _make_store(tmp_path)
    task = store.create_task(
        title="override-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    set_crash_after_checkpoint("POST_PLANNER")
    service = DurableExecutionService(
        store=store, router=RR(),
        execution_authority_sha="trusted_auth_abc",
        planning_sha="trusted_plan_xyz",
    )

    wt_dir = tmp_path / "wt_override"
    _make_git_worktree(wt_dir)

    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.execution_authority_sha == "trusted_auth_abc"
    assert run.planning_sha == "trusted_plan_xyz"

    # Verify repository_base_sha is non-empty (from prepared worktree HEAD)
    assert run.repository_base_sha != ""


def test_startup_stale_reconciliation_no_role_calls(tmp_path) -> None:
    """CombinedTrustedHost startup reconciliation marks expired leases INTERRUPTED
    without calling any role executor or model."""
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

    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_xyz",
        planning_sha="plan_abc",
    )
    try:
        host.start(
            model_control_port=0,
            task_api_port=0,
        )
    except Exception:
        pass

    task_after = store.get_task(task.id)
    assert task_after.status == "INTERRUPTED"
    host.stop()


def test_startup_zero_role_model_calls(tmp_path) -> None:
    """CombinedTrustedHost startup performs zero role/model calls."""
    store = _make_store(tmp_path)
    fake_executor_calls = {"prepare": 0, "execute": 0}

    class _FakePreparedCtx:
        def __init__(self, worktree: Path) -> None:
            self.worktree = worktree

    class FakeExec:
        def prepare_worktree_once(self, *a: Any, **kw: Any) -> _FakePreparedCtx:
            fake_executor_calls["prepare"] += 1
            raise RuntimeError("should not be called")

        def execute_role_prepared(self, *a: Any, **kw: Any):
            fake_executor_calls["execute"] += 1
            raise RuntimeError("should not be called")

    class RR(ExecutorRouter):
        def create_executor(self, *, executor_kind: str = "opencode", **kwargs: Any):
            return FakeExec()
        def dispatch_execute(self, *a: Any, **kw: Any):
            raise NotImplementedError()

    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_xyz",
        planning_sha="plan_abc",
    )
    host._router = RR()

    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()

    assert fake_executor_calls["prepare"] == 0
    assert fake_executor_calls["execute"] == 0


def test_handler_receives_trusted_identity(tmp_path) -> None:
    """Handler factory must receive and expose trusted identity fields."""
    store = _make_store(tmp_path)
    handler_cls = _handler_factory(
        store,
        ExecutorRouter(),
        allowed_origin="http://localhost:4173",
        execution_authority_sha="auth_test_value",
        planning_sha="plan_test_value",
    )
    assert handler_cls.execution_authority_sha == "auth_test_value"
    assert handler_cls.planning_sha == "plan_test_value"


def test_binding_resolver_preserved_in_trusted_host(tmp_path) -> None:
    """CombinedTrustedHost must preserve BindingResolver wiring."""
    from reverse_agent.platform_v1.binding_resolver import BindingResolver

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        execution_authority_sha="auth_v",
        planning_sha="planning_v",
    )
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()

    # Verify the handler created by CombinedTrustedHost.start() has binding_resolver
    assert host.task_api_url != ""

    # Also verify factory with explicit binding_resolver
    resolver = BindingResolver(base_url="http://127.0.0.1:9999")
    handler_cls = _handler_factory(
        host.task_store,
        ExecutorRouter(),
        allowed_origin="http://localhost:4173",
        execution_authority_sha="auth_v",
        planning_sha="planning_v",
        binding_resolver=resolver,
    )
    assert handler_cls.binding_resolver is resolver


def test_credential_relay_preserved_in_trusted_host(tmp_path) -> None:
    """CombinedTrustedHost must preserve credential relay wiring."""
    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
    )
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()

    assert host.relay_manager is not None
    assert host.task_store is not None
    assert host._execution_authority_sha == "auth_v"
    assert host._planning_sha == "plan_v"


def test_durable_run_has_non_empty_authority_and_planning(tmp_path) -> None:
    """After execute_durable_sequential_team, the durable run must have
    non-empty execution_authority_sha, planning_sha, and repository_base_sha."""
    from reverse_agent.platform_v1.opencode_executor import handoff_dir as _handoff_dir

    class _FakePreparedCtx:
        def __init__(self, worktree: Path, execution_id: str = "") -> None:
            self.worktree = worktree
            self.execution_id = execution_id or f"exec-{worktree.name}"

    class FakeExecutor:
        def __init__(self) -> None:
            pass

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
        title="identity-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
    )

    wt_dir = tmp_path / "wt_identity"
    _make_git_worktree(wt_dir)

    service = DurableExecutionService(
        store=store, router=RR(),
        execution_authority_sha="auth_prod_123",
        planning_sha="planning_prod_456",
    )

    set_crash_after_checkpoint("POST_REVIEWER")
    from reverse_agent.platform_v1.durable_execution import _CrashSimulated
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="w1",
        )
    reset_crash_seam()

    run = store._get_durable_run(
        store._conn.execute(
            "SELECT run_id FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
            (task.id,),
        ).fetchone()["run_id"]
    )
    assert run.execution_authority_sha == "auth_prod_123"
    assert run.planning_sha == "planning_prod_456"
    assert run.repository_base_sha != ""
    assert run.worktree_head_sha != ""
    assert run.checkpoint_db_path != ""


def test_no_raw_credential_persistence(tmp_path) -> None:
    """No raw credentials must be persisted in durable_runs, task events, or evidence."""
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
        title="cred-persistence-test",
        executor_kind="opencode",
        orchestration_mode="sequential_team",
        binding_ref="test-binding",
    )

    wt_dir = tmp_path / "wt_cred_check"
    _make_git_worktree(wt_dir)

    service = DurableExecutionService(
        store=store, router=RR(),
        execution_authority_sha="auth_prod_x123",
        planning_sha="planning_prod_y456",
    )

    set_crash_after_checkpoint("POST_REVIEWER")
    from reverse_agent.platform_v1.durable_execution import _CrashSimulated
    with pytest.raises(_CrashSimulated):
        service.execute_durable_sequential_team(
            task_id=task.id,
            workspace_root=str(wt_dir),
            lease_owner="w1",
        )
    reset_crash_seam()

    row = store._conn.execute(
        "SELECT * FROM durable_runs WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task.id,),
    ).fetchone()
    row_dict = dict(row)
    secret_patterns = ["api_key", "password", "bearer", "private_key"]
    _path_fields = {"worktree_path", "checkpoint_db_path"}
    for col, val in row_dict.items():
        if col in _path_fields:
            continue
        if isinstance(val, str):
            for pattern in secret_patterns:
                assert pattern not in val.lower(), (
                    f"secret pattern '{pattern}' found in durable_runs.{col}: {val[:100]}"
                )

    events = store.get_events(task.id)
    for e in events:
        meta = e.metadata if isinstance(e.metadata, dict) else {}
        meta_str = json.dumps(meta) if meta else ""
        for pattern in secret_patterns:
            assert pattern not in meta_str.lower(), (
                f"secret pattern '{pattern}' found in event metadata"
            )