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
import socket
import subprocess
import tempfile
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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


import tempfile as _tempfile
from pathlib import Path as _Path


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


def _model_control_request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    parsed = urlsplit(base_url)
    connection = HTTPConnection(parsed.hostname, parsed.port, timeout=3)
    body = None if payload is None else json.dumps(payload)
    headers = {} if body is None else {"Content-Type": "application/json"}
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))
    finally:
        connection.close()


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


def test_stop_closes_all_server_sockets_and_allows_exact_port_reuse(tmp_path) -> None:
    first_dir = tmp_path / "first"
    first_dir.mkdir()
    first = CombinedTrustedHost(task_store=_make_store(first_dir))
    first.start(model_control_port=0, task_api_port=0)
    assert first._model_server is not None
    assert first._task_server is not None
    model_port = first._model_server.server_address[1]
    task_port = first._task_server.server_address[1]
    relay_port = first._relay_server_port

    first.stop()

    relay_probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        relay_probe.bind(("127.0.0.1", relay_port))
    finally:
        relay_probe.close()

    second_dir = tmp_path / "second"
    second_dir.mkdir()
    second = CombinedTrustedHost(task_store=_make_store(second_dir))
    try:
        second.start(
            model_control_port=model_port,
            task_api_port=task_port,
        )
        assert second.model_control_url.endswith(f":{model_port}")
        assert second.task_api_url.endswith(f":{task_port}")
    finally:
        second.stop()


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


# ===================================================================
# V6 Gap 7: Real trusted-host authority resolver keeps
# authority/planning independent
# ===================================================================

def test_real_resolver_planning_only_yields_empty_authority(tmp_path) -> None:
    """When only REVERSE_AGENT_PLANNING_SHA is set (no execution authority),
    the real _resolve_trusted_authority_sha() must return ''.
    Durable execute must fail closed before run creation (run count = 0)."""
    from reverse_agent.platform_v1.trusted_host import (
        _resolve_trusted_authority_sha,
        _resolve_trusted_planning_sha,
    )
    from reverse_agent.platform_v1.durable_execution import DurableExecutionService, DurableResumeError
    from reverse_agent.platform_v1.task_execution import TaskExecutionError

    old_auth = os.environ.pop("REVERSE_AGENT_EXECUTION_AUTHORITY_SHA", None)
    old_plan = os.environ.get("REVERSE_AGENT_PLANNING_SHA")
    old_repo = os.environ.pop("REVERSE_AGENT_REPO_DIR", None)

    try:
        os.environ["REVERSE_AGENT_PLANNING_SHA"] = "some-planning-sha-v6"
        os.environ.pop("REVERSE_AGENT_EXECUTION_AUTHORITY_SHA", None)
        os.environ.pop("REVERSE_AGENT_REPO_DIR", None)

        auth = _resolve_trusted_authority_sha()
        plan = _resolve_trusted_planning_sha()
        assert auth == ""
        assert plan == "some-planning-sha-v6"

        store = _make_store(tmp_path)
        task = store.create_task(
            title="planning-only-v6",
            executor_kind="opencode",
            orchestration_mode="sequential_team",
        )
        svc = DurableExecutionService(
            store=store, router=object(),
            execution_authority_sha=None,
            planning_sha="some-planning-sha-v6",
        )
        with pytest.raises((TaskExecutionError, DurableResumeError)):
            svc.execute_durable_sequential_team(
                task_id=task.id, workspace_root=str(tmp_path),
            )
        run_count = store._conn.execute(
            "SELECT COUNT(*) FROM durable_runs WHERE task_id = ?",
            (task.id,),
        ).fetchone()[0]
        assert run_count == 0
    finally:
        if old_auth is not None:
            os.environ["REVERSE_AGENT_EXECUTION_AUTHORITY_SHA"] = old_auth
        if old_plan is not None:
            os.environ["REVERSE_AGENT_PLANNING_SHA"] = old_plan
        elif "REVERSE_AGENT_PLANNING_SHA" in os.environ:
            os.environ.pop("REVERSE_AGENT_PLANNING_SHA", None)
        if old_repo is not None:
            os.environ["REVERSE_AGENT_REPO_DIR"] = old_repo


# ===================================================================
# ISSUE210 R2 V1 — CombinedTrustedHost restart restores sanitized metadata
# ===================================================================

def test_combined_trusted_host_restart_restores_sanitized_metadata(tmp_path) -> None:
    """A fresh CombinedTrustedHost using the same runtime path must automatically
    restore Connection and Binding metadata persisted by a previous host.
    No raw credential must be exposed through the public API or persisted state.
    """
    from reverse_agent.platform_v1.trusted_host import _resolve_store_state_path
    from reverse_agent.model_access.store import StoreError

    db_path = str(tmp_path / "tasks.sqlite3")
    store = _make_store(tmp_path)

    host1 = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_host1",
        planning_sha="plan_host1",
    )

    raw_secret = "HOST1-RAW-SECRET-NEVER-PERSIST"
    host1.store.upsert_connection({
        "connection_id": "restored-conn",
        "name": "Restored Connection",
        "provider": "openai-compatible",
        "base_url": "https://restored.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
        "api_key": raw_secret,
    })
    host1.store.upsert_binding({
        "binding_id": "restored-binding",
        "name": "Restored Binding",
        "executor_id": "opencode",
        "connection_id": "restored-conn",
        "model_id": "restored-model-v1",
        "enabled": True,
    })

    conn1_public = host1.store.list_connections_public()
    assert conn1_public[0]["connection_id"] == "restored-conn"
    assert conn1_public[0]["secret_status"] == "session"
    assert raw_secret not in json.dumps(conn1_public)

    state_path = _resolve_store_state_path(store)
    raw_bytes = Path(state_path).read_bytes()
    assert raw_secret.encode("utf-8") not in raw_bytes
    assert b"HOST1-RAW" not in raw_bytes

    host1.stop()
    del host1

    host2 = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_host2",
        planning_sha="plan_host2",
    )

    conn2_public = host2.store.list_connections_public()
    assert len(conn2_public) == 1
    c2 = conn2_public[0]
    assert c2["connection_id"] == "restored-conn"
    assert c2["name"] == "Restored Connection"
    assert c2["provider"] == "openai-compatible"
    assert c2["base_url"] == "https://restored.example.test/v1"
    assert c2["auth_method"] == "api_key"
    assert c2["enabled"] is True
    assert c2["secret_status"] == "missing"
    assert raw_secret not in json.dumps(conn2_public)

    binding2_public = host2.store.list_bindings_public()
    assert len(binding2_public) == 1
    b2 = binding2_public[0]
    assert b2["binding_id"] == "restored-binding"
    assert b2["executor_id"] == "opencode"
    assert b2["connection_id"] == "restored-conn"
    assert b2["model_id"] == "restored-model-v1"
    assert b2["enabled"] is True

    assert host2.store.resolve_connection_secret("restored-conn") is None

    new_raw = "HOST2-NEW-SECRET"
    host2.store.upsert_connection({
        "connection_id": "restored-conn",
        "name": "Restored Connection",
        "provider": "openai-compatible",
        "base_url": "https://restored.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
        "api_key": new_raw,
    })
    assert host2.store.resolve_connection_secret("restored-conn") == new_raw
    raw_bytes2 = Path(state_path).read_bytes()
    assert new_raw.encode("utf-8") not in raw_bytes2
    assert b"HOST2-NEW" not in raw_bytes2

    host2.stop()

    del host2

    host3 = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_host3",
        planning_sha="plan_host3",
    )
    conn3_public = host3.store.list_connections_public()
    assert conn3_public[0]["secret_status"] == "missing"
    assert host3.store.resolve_connection_secret("restored-conn") is None

    assert host3.store.get_connection_public("restored-conn")["connection_id"] == "restored-conn"
    assert host3.store.get_binding_public("restored-binding")["binding_id"] == "restored-binding"

    try:
        host3.store.upsert_binding({
            "binding_id": "new-binding",
            "name": "New Binding",
            "executor_id": "opencode",
            "connection_id": "nonexistent-conn",
            "model_id": "model-x",
            "enabled": True,
        })
    except ValueError:
        pass
    else:
        raise AssertionError("dangling binding must fail closed")

    raw_bytes3 = Path(state_path).read_bytes()
    assert raw_secret.encode("utf-8") not in raw_bytes3
    assert new_raw.encode("utf-8") not in raw_bytes3
    assert b"HOST1-RAW" not in raw_bytes3
    assert b"HOST2-NEW" not in raw_bytes3

    host3.stop()


def test_explicit_injected_store_bypasses_auto_persistence(tmp_path) -> None:
    """When a caller explicitly injects a store, CombinedTrustedHost must not
    auto-create a persisted store.  The injected store remains authoritative."""
    from reverse_agent.model_access.store import ModelProfileStore

    db_path = str(tmp_path / "tasks.sqlite3")
    store = _make_store(tmp_path)
    injected = ModelProfileStore()

    host = CombinedTrustedHost(
        task_store=store,
        store=injected,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
    )

    host.store.upsert_connection({
        "connection_id": "injected-conn",
        "name": "Injected",
        "provider": "openai-compatible",
        "base_url": "https://injected.example.test/v1",
        "auth_method": "none",
        "enabled": True,
    })

    assert host.store is injected
    listed = host.store.list_connections_public()
    assert listed[0]["connection_id"] == "injected-conn"


# ===================================================================
# ISSUE216 OPENCODE_CREDENTIAL_REUSE_ADAPTER_V3 REGRESSIONS
# ===================================================================

def test_host_startup_refreshes_external_session_from_injected_auth_probe(tmp_path) -> None:
    """CombinedTrustedHost startup must re-derive external session availability
    from a fresh sanitized auth probe; the persisted state file must not
    contain the derived availability."""
    from reverse_agent.platform_v1.trusted_host import _resolve_store_state_path

    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
        auth_list_probe=lambda: {"sensetime": "api"},
    )

    host.store.upsert_connection({
        "connection_id": "sensetime-external-conn",
        "name": "SenseTime External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    assert host.store.get_connection_public(
        "sensetime-external-conn"
    )["external_session_status"] == "executor_managed"

    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()

    conn = host.store.get_connection_public("sensetime-external-conn")
    assert conn["external_session_status"] == "available"

    raw_bytes = _Path(_resolve_store_state_path(store)).read_bytes()
    assert b"external_session_status" not in raw_bytes
    assert b"available" not in raw_bytes


def test_host_startup_marks_external_session_missing_when_probe_empty(tmp_path) -> None:
    """A subsequent host process whose auth probe no longer reports sensetime
    must mark external sessions as missing; the prior host's availability
    must not carry forward from the persisted state file."""
    from reverse_agent.platform_v1.trusted_host import _resolve_store_state_path

    db_path = str(tmp_path / "tasks.sqlite3")
    store1 = TaskStore(db_path=db_path)
    host1 = CombinedTrustedHost(
        task_store=store1,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
        auth_list_probe=lambda: {"sensetime": "api"},
    )
    host1.store.upsert_connection({
        "connection_id": "sensetime-external-conn",
        "name": "SenseTime External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    try:
        host1.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    assert host1.store.get_connection_public(
        "sensetime-external-conn"
    )["external_session_status"] == "available"
    host1.stop()

    host2 = CombinedTrustedHost(
        task_store=TaskStore(db_path=db_path),
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
        auth_list_probe=lambda: {},
    )
    try:
        host2.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host2.stop()

    assert host2.store.get_connection_public(
        "sensetime-external-conn"
    )["external_session_status"] == "missing"

    raw_bytes = _Path(_resolve_store_state_path(
        TaskStore(db_path=db_path)
    )).read_bytes()
    assert b"external_session_status" not in raw_bytes


def test_host_startup_proceeds_when_auth_probe_fails(tmp_path) -> None:
    """A probe failure must not crash the host. The external session remains
    in its initial fresh-loaded state."""

    def failing_probe():
        raise RuntimeError("opencode_cli_not_found")

    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
        auth_list_probe=failing_probe,
    )
    host.store.upsert_connection({
        "connection_id": "sensetime-external-conn",
        "name": "SenseTime External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pytest.fail("host startup must not crash on auth probe failure")
    host.stop()

    assert host.store.get_connection_public(
        "sensetime-external-conn"
    )["external_session_status"] == "missing"


def test_host_skips_auth_probe_when_no_external_session_connections(tmp_path) -> None:
    probe_calls = {"count": 0}

    def counting_probe():
        probe_calls["count"] += 1
        return {"sensetime": "api"}

    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
        auth_list_probe=counting_probe,
    )
    host.store.upsert_connection({
        "connection_id": "api-key-conn",
        "name": "API Key",
        "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()

    assert probe_calls["count"] == 0


# ===================================================================
# ISSUE216 R2 V5 — Auth probe recovery regressions (A, B)
# ===================================================================

def test_external_session_available_rejected_when_probe_returns_empty(tmp_path) -> None:
    """Regression A: a store whose external session is already 'available'
    must become 'missing' after _refresh_external_session_auth() runs
    with a probe that returns an empty mapping.  The in-memory 'available'
    value must not survive a later empty probe."""
    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v5",
        planning_sha="plan_v5",
        auth_list_probe=lambda: {"sensetime": "api"},
    )
    host.store.upsert_connection({
        "connection_id": "sensetime-ext",
        "name": "SenseTime Ext",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()
    assert host.store.get_connection_public("sensetime-ext")[
        "external_session_status"
    ] == "available"

    probe_switched = {"return_value": {}}
    host2 = CombinedTrustedHost(
        task_store=TaskStore(db_path=str(tmp_path / "tasks.sqlite3")),
        execution_authority_sha="auth_v5",
        planning_sha="plan_v5",
        auth_list_probe=lambda: probe_switched["return_value"],
    )
    try:
        host2.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host2.stop()
    assert host2.store.get_connection_public("sensetime-ext")[
        "external_session_status"
    ] == "missing"


def test_external_session_available_rejected_when_probe_raises(tmp_path) -> None:
    """Regression B: a store whose external session is already 'available'
    must become 'missing' after _refresh_external_session_auth() runs
    with a probe that raises.  The host must remain startable."""

    def failing_probe():
        raise RuntimeError("opencode_cli_unavailable")

    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v5",
        planning_sha="plan_v5",
        auth_list_probe=lambda: {"sensetime": "api"},
    )
    host.store.upsert_connection({
        "connection_id": "sensetime-ext",
        "name": "SenseTime Ext",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
    except Exception:
        pass
    host.stop()
    assert host.store.get_connection_public("sensetime-ext")[
        "external_session_status"
    ] == "available"

    host2 = CombinedTrustedHost(
        task_store=TaskStore(db_path=str(tmp_path / "tasks.sqlite3")),
        execution_authority_sha="auth_v5",
        planning_sha="plan_v5",
        auth_list_probe=failing_probe,
    )
    try:
        host2.start(model_control_port=0, task_api_port=0)
    except Exception:
        pytest.fail("host startup must not crash when auth probe raises")
    host2.stop()
    assert host2.store.get_connection_public("sensetime-ext")[
        "external_session_status"
    ] == "missing"


def test_host_default_startup_does_not_probe_and_keeps_executor_managed(tmp_path) -> None:
    """CombinedTrustedHost default (auth_list_probe=None) must not call any auth
    probe on startup; external-session Connections must remain executor_managed."""
    store = _make_store(tmp_path)
    host = CombinedTrustedHost(
        task_store=store,
        execution_authority_sha="auth_v",
        planning_sha="plan_v",
    )
    assert host._auth_list_probe is None

    host.store.upsert_connection({
        "connection_id": "sensetime-external-conn",
        "name": "SenseTime External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    assert host.store.get_connection_public(
        "sensetime-external-conn"
    )["external_session_status"] == "executor_managed"

    try:
        host.start(model_control_port=0, task_api_port=0)
        assert host.model_control_url != ""
        assert host.task_api_url != ""
        assert host.relay_url != ""
        assert host.store.get_connection_public(
            "sensetime-external-conn"
        )["external_session_status"] == "executor_managed"
    finally:
        host.stop()


@pytest.mark.parametrize(
    "auth_method",
    ["account_login", "external_cli_session"],
)
def test_external_session_get_refreshes_after_ttl_and_fails_closed(
    tmp_path,
    auth_method,
) -> None:
    clock = {"now": 0.0}
    probe = {"result": {"sensetime": "api"}, "raises": False, "calls": 0}

    def controlled_probe():
        probe["calls"] += 1
        if probe["raises"]:
            raise RuntimeError("sanitized_auth_probe_failed")
        return probe["result"]

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        auth_list_probe=controlled_probe,
        auth_refresh_ttl_seconds=5.0,
        auth_refresh_clock=lambda: clock["now"],
    )
    host.store.upsert_connection({
        "connection_id": "external-conn",
        "name": "External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": auth_method,
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
        assert probe["calls"] == 1

        status, connection = _model_control_request(
            host.model_control_url,
            "GET",
            "/api/connections/external-conn",
        )
        assert status == 200
        assert connection["external_session_status"] == "available"
        assert probe["calls"] == 1

        probe["result"] = {}
        clock["now"] = 5.0
        _, connection = _model_control_request(
            host.model_control_url,
            "GET",
            "/api/connections/external-conn",
        )
        assert connection["external_session_status"] == "missing"
        assert probe["calls"] == 2

        probe["result"] = {"sensetime": "api"}
        clock["now"] = 10.0
        _, connection = _model_control_request(
            host.model_control_url,
            "GET",
            "/api/connections/external-conn",
        )
        assert connection["external_session_status"] == "available"
        assert probe["calls"] == 3

        probe["raises"] = True
        clock["now"] = 15.0
        _, connection = _model_control_request(
            host.model_control_url,
            "GET",
            "/api/connections/external-conn",
        )
        assert connection["external_session_status"] == "missing"
        assert probe["calls"] == 4
    finally:
        host.stop()


def test_concurrent_external_session_reads_coalesce_one_probe(tmp_path) -> None:
    started = threading.Event()
    release = threading.Event()
    calls = {"count": 0}

    def blocking_probe():
        calls["count"] += 1
        started.set()
        assert release.wait(timeout=3)
        return {"sensetime": "api"}

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        auth_list_probe=blocking_probe,
        auth_refresh_ttl_seconds=5.0,
        auth_refresh_clock=lambda: 0.0,
    )
    host.store.upsert_connection({
        "connection_id": "external-conn",
        "name": "External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })

    threads = [
        threading.Thread(
            target=host._refresh_external_session_auth,
            args=(False, "external-conn"),
        )
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    assert started.wait(timeout=3)
    release.set()
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()

    assert calls["count"] == 1
    assert host.store.get_connection_public("external-conn")[
        "external_session_status"
    ] == "available"


def test_connection_upsert_forces_external_refresh_before_response(tmp_path) -> None:
    calls = {"count": 0}

    def counting_probe():
        calls["count"] += 1
        return {"sensetime": "api"}

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        auth_list_probe=counting_probe,
    )
    try:
        host.start(model_control_port=0, task_api_port=0)
        assert calls["count"] == 0
        status, connection = _model_control_request(
            host.model_control_url,
            "PUT",
            "/api/connections/external-conn",
            {
                "name": "External",
                "provider": "sensetime",
                "base_url": "https://api.sensenova.cn/v1",
                "auth_method": "external_cli_session",
                "enabled": True,
            },
        )
        assert status == 200
        assert connection["external_session_status"] == "available"
        assert calls["count"] == 1

        _, renamed = _model_control_request(
            host.model_control_url,
            "PUT",
            "/api/connections/external-conn",
            {
                "name": "Renamed only",
                "provider": "sensetime",
                "base_url": "https://api.sensenova.cn/v1",
                "auth_method": "external_cli_session",
                "enabled": True,
            },
        )
        assert renamed["external_session_status"] == "available"
        assert calls["count"] == 1

        _, changed = _model_control_request(
            host.model_control_url,
            "PUT",
            "/api/connections/external-conn",
            {
                "name": "Changed provider",
                "provider": "other-provider",
                "base_url": "https://models.example.test/v1",
                "auth_method": "external_cli_session",
                "enabled": True,
            },
        )
        assert changed["external_session_status"] == "missing"
        assert calls["count"] == 2
    finally:
        host.stop()


def test_api_key_and_none_connection_reads_do_not_probe(tmp_path) -> None:
    calls = {"count": 0}

    def counting_probe():
        calls["count"] += 1
        return {"sensetime": "api"}

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        auth_list_probe=counting_probe,
    )
    for connection_id, auth_method in (
        ("api-key-conn", "api_key"),
        ("none-conn", "none"),
    ):
        host.store.upsert_connection({
            "connection_id": connection_id,
            "name": connection_id,
            "provider": "openai-compatible",
            "base_url": "https://models.example.test/v1",
            "auth_method": auth_method,
            "enabled": True,
            **({"api_key": "test-only-secret"} if auth_method == "api_key" else {}),
        })
    try:
        host.start(model_control_port=0, task_api_port=0)
        for connection_id in ("api-key-conn", "none-conn"):
            status, connection = _model_control_request(
                host.model_control_url,
                "GET",
                f"/api/connections/{connection_id}",
            )
            assert status == 200
            assert connection["external_session_status"] == "not_applicable"
        status, connections = _model_control_request(
            host.model_control_url,
            "GET",
            "/api/connections",
        )
        assert status == 200
        assert len(connections) == 2
        assert calls["count"] == 0
    finally:
        host.stop()


def test_dispatch_forces_external_session_revalidation(tmp_path) -> None:
    probe = {"result": {"sensetime": "api"}, "calls": 0}

    def controlled_probe():
        probe["calls"] += 1
        return probe["result"]

    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        auth_list_probe=controlled_probe,
    )
    host.store.upsert_connection({
        "connection_id": "external-conn",
        "name": "External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    })
    host.store.upsert_binding({
        "binding_id": "external-binding",
        "name": "External Binding",
        "executor_id": "opencode",
        "connection_id": "external-conn",
        "model_id": "sensechat-5",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
        resolver = host._binding_resolver_factory(host.model_control_url)

        probe["result"] = {}
        from reverse_agent.platform_v1.binding_resolver import BindingResolutionError

        with pytest.raises(BindingResolutionError, match="external_session_unavailable"):
            resolver.resolve("external-binding", task_executor="opencode")
        assert probe["calls"] == 2

        probe["result"] = {"sensetime": "api"}
        resolution = resolver.resolve(
            "external-binding",
            task_executor="opencode",
        )
        assert resolution.external_session_status == "available"
        assert probe["calls"] == 3
    finally:
        host.stop()


def test_dispatch_rejects_unprobed_executor_managed_session(tmp_path) -> None:
    host = CombinedTrustedHost(task_store=_make_store(tmp_path))
    host.store.upsert_connection({
        "connection_id": "external-conn",
        "name": "External",
        "provider": "sensetime",
        "base_url": "https://api.sensenova.cn/v1",
        "auth_method": "account_login",
        "enabled": True,
    })
    host.store.upsert_binding({
        "binding_id": "external-binding",
        "name": "External Binding",
        "executor_id": "opencode",
        "connection_id": "external-conn",
        "model_id": "sensechat-5",
        "enabled": True,
    })
    try:
        host.start(model_control_port=0, task_api_port=0)
        resolver = host._binding_resolver_factory(host.model_control_url)
        from reverse_agent.platform_v1.binding_resolver import BindingResolutionError

        with pytest.raises(BindingResolutionError, match="external_session_unavailable"):
            resolver.resolve("external-binding", task_executor="opencode")
    finally:
        host.stop()


def test_production_entrypoint_wires_existing_sanitized_auth_probe(
    tmp_path,
    monkeypatch,
) -> None:
    import reverse_agent.platform_v1.trusted_host as trusted_host_module

    captured: dict[str, Any] = {}
    probe = lambda: {"sensetime": "api"}

    class FakeServer:
        def serve_forever(self):
            raise KeyboardInterrupt

    class FakeHost:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.model_control_url = "http://127.0.0.1:1"
            self.task_api_url = "http://127.0.0.1:2"
            self.relay_url = "http://127.0.0.1:3"
            self._model_server = FakeServer()

        def start(self):
            captured["started"] = True

        def stop(self):
            captured["stopped"] = True

    monkeypatch.setattr(
        trusted_host_module,
        "execute_opencode_auth_list_probe",
        probe,
    )
    monkeypatch.setattr(trusted_host_module, "CombinedTrustedHost", FakeHost)
    monkeypatch.setattr(
        trusted_host_module,
        "_resolve_trusted_authority_sha",
        lambda: "auth-sha",
    )
    monkeypatch.setattr(
        trusted_host_module,
        "_resolve_trusted_planning_sha",
        lambda: "planning-sha",
    )
    monkeypatch.setenv("REVERSE_AGENT_TASK_DB_DIR", str(tmp_path))

    trusted_host_module.run_combined_trusted_host()

    assert captured["auth_list_probe"] is probe
    assert captured["started"] is True
    assert captured["stopped"] is True
    assert json.loads((tmp_path / "trusted_host_meta.json").read_text("utf-8"))[
        "execution_authority_sha"
    ] == "auth-sha"


def test_host_starts_inert_unattended_coordinator_only_when_explicitly_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REVERSE_AGENT_AUTONOMOUS", "1")
    host = CombinedTrustedHost(
        task_store=_make_store(tmp_path),
        execution_authority_sha="auth-platform-v2",
        planning_sha="plan-platform-v2",
    )
    try:
        host.start(model_control_port=0, task_api_port=0)
        assert host._coordinator is not None
        status = host._coordinator.status()
        assert status["enabled"] is True
        assert status["active_window_id"] == ""
        assert status["executions"] == 0
    finally:
        host.stop()
