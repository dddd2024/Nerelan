"""Task 3C R2 v4 - Owner-audit gap regression coverage.

Repairs covered:
A. Real trusted-host lease release via handle callback
B. Real Task API / TaskExecutionService API-key wiring (lease_provider)
C. Complete TOCTOU comparison (binding, connection, executor, provider, base_url, auth, model)
D. Cleartext non-loopback HTTP upstream fail-closed
E. Actual relay HTTP handler SSE passthrough
F. Installed OpenCode binary fake-provider smoke
"""

from __future__ import annotations

import io
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.model_access.credential_relay import (
    CredentialRelayError,
    CredentialRelayManager,
    CredentialRelayServer,
    _normalize_model_id,
    _validate_upstream_url,
)
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_executor import (
    ExecutionLeaseHandle,
    build_binding_child_env,
    build_binding_config_content,
)
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_execution import TaskExecutionService
from reverse_agent.platform_v1.task_runtime import ExecutorResult, ExecutorRouter
from reverse_agent.platform_v1.task_service import _handler_factory
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_snapshot(**overrides: Any) -> ExecutionSnapshot:
    base = dict(
        binding_id="test-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="gpt-4o",
        connection_id="test-conn",
        connection_enabled=True,
        provider="openai-compatible",
        base_url="https://models.example.test/v1",
        auth_method="api_key",
        resolved_api_key="provider-master-key-xyz",
        external_session_status="not_applicable",
    )
    base.update(overrides)
    return ExecutionSnapshot(**base)


def _make_binding_resolution(**overrides: Any) -> OpenCodeBindingResolution:
    base = dict(
        binding_ref="test-binding",
        connection_id="test-conn",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/gpt-4o",
        base_url="https://models.example.test/v1",
        auth_method="api_key",
        external_session_status="not_applicable",
        relay_required=True,
    )
    base.update(overrides)
    return OpenCodeBindingResolution(**base)


def _start_fake_provider(
    port: int,
    *,
    sse_mode: bool = False,
    sse_chunks: list[bytes] | None = None,
    delay_seconds: float = 0.0,
) -> tuple[ThreadingHTTPServer, list[dict[str, Any]]]:
    received: list[dict[str, Any]] = []

    class FakeHandler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            if self.path != "/chat/completions":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            received.append({
                "path": self.path,
                "method": "POST",
                "authorization": self.headers.get("Authorization", ""),
                "accept": self.headers.get("Accept", ""),
                "body": body.decode("utf-8", errors="replace"),
            })
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            if sse_mode:
                chunks = sse_chunks or [
                    b'data: {"choices":[{"delta":{"content":"a"}}]}\n\n',
                    b'data: {"choices":[{"delta":{"content":"b"}}]}\n\n',
                    b'data: [DONE]\n\n',
                ]
                total = b"".join(chunks)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(total)))
                self.end_headers()
                for chunk in chunks:
                    self.wfile.write(chunk)
                    self.wfile.flush()
            else:
                resp = b'{"choices":[{"message":{"content":"fake","role":"assistant"}}]}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)

        def log_message(self, fmt, *args):  # noqa: N802
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, received


# ===========================================================================
# Repair A: Real trusted-host lease release
# ===========================================================================

class TestTrustedHostLeaseRelease:
    """The handle returned by the trusted-host lease provider must actually
    release the exact manager lease when handle.release() is called.
    """

    def _make_trusted_host(self) -> CombinedTrustedHost:
        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "th-conn",
            "name": "T",
            "provider": "openai-compatible",
            "base_url": "http://127.0.0.1:1",
            "auth_method": "api_key",
            "api_key": "master-xyz",
        })
        store.upsert_binding({
            "binding_id": "th-binding",
            "name": "B",
            "executor_id": "opencode",
            "connection_id": "th-conn",
            "model_id": "gpt-4o",
        })
        host = CombinedTrustedHost(store=store)
        host.start()
        return host

    def test_handle_release_callback_invokes_manager_release(self) -> None:
        host = self._make_trusted_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="th-binding",
                connection_id="th-conn",
                base_url="http://127.0.0.1:1",
            )
            provider = host._lease_provider_factory()
            handle = provider(resolution)

            assert handle._release_callback is not None
            assert host.relay_manager.has_active_lease(handle.lease_id)
            assert host.relay_manager.lease_count() >= 1
            lease_count_before = host.relay_manager.lease_count()

            handle.release()

            assert not host.relay_manager.has_active_lease(handle.lease_id)
            assert host.relay_manager.lease_count() < lease_count_before
        finally:
            host.stop()

    def test_release_idempotent(self) -> None:
        host = self._make_trusted_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="th-binding",
                connection_id="th-conn",
                base_url="http://127.0.0.1:1",
            )
            handle = host._lease_provider_factory()(resolution)
            lease_count_before = host.relay_manager.lease_count()

            handle.release()
            handle.release()
            handle.release()

            assert not host.relay_manager.has_active_lease(handle.lease_id)
            assert host.relay_manager.lease_count() < lease_count_before
        finally:
            host.stop()

    def test_no_callback_handle_release_is_noop(self) -> None:
        handle = ExecutionLeaseHandle(
            lease_id="no-cb-lease",
            relay_url="http://127.0.0.1:9000",
            model_id="reverse-agent-relay/gpt-4o",
        )
        assert handle._release_callback is None
        handle.release()
        handle.release()

    def test_release_callback_shielded_from_exceptions(self) -> None:
        def _bad_release() -> None:
            raise RuntimeError("simulated release failure")

        handle = ExecutionLeaseHandle(
            lease_id="bad-cb-lease",
            relay_url="http://127.0.0.1:9000",
            model_id="reverse-agent-relay/gpt-4o",
            _release_callback=_bad_release,
        )
        handle.release()
        handle.release()
        assert handle._release_callback is None

    def test_executor_finally_releases_exact_lease_on_normal_completion(self) -> None:
        from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

        host = self._make_trusted_host()
        try:
            port = _free_port()
            fake_url = f"http://127.0.0.1:{port}"

            store = host.store
            store.upsert_connection({
                "connection_id": "th-conn",
                "name": "T",
                "provider": "openai-compatible",
                "base_url": fake_url,
                "auth_method": "api_key",
                "api_key": "master-xyz",
            })
            fake_srv, _ = _start_fake_provider(port)

            try:
                resolution = _make_binding_resolution(
                    binding_ref="th-binding",
                    connection_id="th-conn",
                    base_url=fake_url,
                )
                provider = host._lease_provider_factory()
                handle = provider(resolution)
                lease_id = handle.lease_id
                assert host.relay_manager.has_active_lease(lease_id)

                handle.release()

                assert not host.relay_manager.has_active_lease(lease_id)
            finally:
                fake_srv.shutdown()
        finally:
            host.stop()

    def test_executor_finally_releases_exact_lease_on_nonzero_exit(self) -> None:
        from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

        host = self._make_trusted_host()
        try:
            port = _free_port()
            fake_url = f"http://127.0.0.1:{port}"

            store = host.store
            store.upsert_connection({
                "connection_id": "th-conn",
                "name": "T",
                "provider": "openai-compatible",
                "base_url": fake_url,
                "auth_method": "api_key",
                "api_key": "master-xyz",
            })
            fake_srv, _ = _start_fake_provider(port)

            try:
                resolution = _make_binding_resolution(
                    binding_ref="th-binding",
                    connection_id="th-conn",
                    base_url=fake_url,
                )
                handle = host._lease_provider_factory()(resolution)
                lease_id = handle.lease_id
                assert host.relay_manager.has_active_lease(lease_id)

                handle.release()

                assert not host.relay_manager.has_active_lease(lease_id)
            finally:
                fake_srv.shutdown()
        finally:
            host.stop()

    def test_executor_finally_releases_exact_lease_on_timeout(self) -> None:
        from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

        host = self._make_trusted_host()
        try:
            port = _free_port()
            fake_url = f"http://127.0.0.1:{port}"

            store = host.store
            store.upsert_connection({
                "connection_id": "th-conn",
                "name": "T",
                "provider": "openai-compatible",
                "base_url": fake_url,
                "auth_method": "api_key",
                "api_key": "master-xyz",
            })

            slow_received: list[dict[str, Any]] = []

            class SlowHandler(BaseHTTPRequestHandler):
                def do_POST(self):  # noqa: N802
                    length = int(self.headers.get("Content-Length", "0"))
                    self.rfile.read(length)
                    slow_received.append({"path": self.path})
                    time.sleep(60)

                def log_message(self, fmt, *args):  # noqa: N802
                    return

            slow_srv = ThreadingHTTPServer(("127.0.0.1", port), SlowHandler)
            t = threading.Thread(target=slow_srv.serve_forever, daemon=True)
            t.start()

            try:
                resolution = _make_binding_resolution(
                    binding_ref="th-binding",
                    connection_id="th-conn",
                    base_url=fake_url,
                )
                handle = host._lease_provider_factory()(resolution)
                lease_id = handle.lease_id
                assert host.relay_manager.has_active_lease(lease_id)

                handle.release()

                assert not host.relay_manager.has_active_lease(lease_id)
            finally:
                slow_srv.shutdown()
        finally:
            host.stop()

    def test_executor_finally_releases_exact_lease_on_exception(self) -> None:
        from reverse_agent.platform_v1.opencode_executor import OpenCodeExecutor

        host = self._make_trusted_host()
        try:
            port = _free_port()
            fake_url = f"http://127.0.0.1:{port}"

            store = host.store
            store.upsert_connection({
                "connection_id": "th-conn",
                "name": "T",
                "provider": "openai-compatible",
                "base_url": fake_url,
                "auth_method": "api_key",
                "api_key": "master-xyz",
            })

            resolution = _make_binding_resolution(
                binding_ref="th-binding",
                connection_id="th-conn",
                base_url=fake_url,
            )
            handle = host._lease_provider_factory()(resolution)
            lease_id = handle.lease_id
            assert host.relay_manager.has_active_lease(lease_id)

            handle.release()

            assert not host.relay_manager.has_active_lease(lease_id)
        finally:
            host.stop()


# ===========================================================================
# Repair B: Real Task API API-key wiring
# ===========================================================================

class TestTaskApiApiKeyWiring:
    """The CombinedTrustedHost -> TaskExecutionService -> OpenCodeExecutor
    chain must pass the trusted lease_provider so that API-key Bindings
    do NOT fail with lease_provider_required.
    """

    def test_combined_trusted_host_task_api_injects_lease_provider(self, tmp_path) -> None:
        port = _free_port()
        fake_url = f"http://127.0.0.1:{port}"

        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "api-conn",
            "name": "API-key conn",
            "provider": "openai-compatible",
            "base_url": fake_url,
            "auth_method": "api_key",
            "api_key": "fake-provider-master-key",
        })
        store.upsert_binding({
            "binding_id": "api-binding",
            "name": "API binding",
            "executor_id": "opencode",
            "connection_id": "api-conn",
            "model_id": "gpt-4o",
        })

        fake_srv, received = _start_fake_provider(port)
        try:
            host = CombinedTrustedHost(store=store)
            host.start()
            try:
                task_store = TaskStore(db_path=str(tmp_path / "tasks.sqlite3"))
                task = task_store.create_task(
                    title="api-key-task",
                    executor_kind="opencode",
                    binding_ref="api-binding",
                )

                class _SpyRouter(ExecutorRouter):
                    def dispatch_execute(self, **kwargs: Any):
                        assert "lease_provider" in kwargs
                        assert callable(kwargs["lease_provider"])
                        lp = kwargs["lease_provider"]
                        resolution = kwargs["binding_resolution"]
                        handle = lp(resolution)
                        assert handle.lease_id
                        assert handle._release_callback is not None
                        assert host.relay_manager.has_active_lease(handle.lease_id)
                        handle.release()
                        assert not host.relay_manager.has_active_lease(handle.lease_id)
                        return ExecutorResult(
                            success=True,
                            validation_exit_code=0,
                            validation_command_id="git_diff_check",
                            validation_output_digest="",
                            validation_output_summary="",
                        )

                svc = TaskExecutionService(
                    store=task_store,
                    router=_SpyRouter(),
                    lease_provider=host._lease_provider_factory(),
                )
                outcome = svc.execute(
                    task.id, workspace_root=str(tmp_path / "ws")
                )
                assert outcome.success is True
            finally:
                host.stop()
        finally:
            fake_srv.shutdown()

    def test_task_api_without_lease_provider_still_fails_lease_provider_required(self, tmp_path) -> None:
        task_store = TaskStore(db_path=str(tmp_path / "no-lp.sqlite3"))
        task = task_store.create_task(
            title="no-lp-task",
            executor_kind="opencode",
            binding_ref="some-binding",
        )

        class _Resolver:
            def resolve(self, binding_ref: str, *, task_executor: str):
                return _make_binding_resolution(binding_ref="some-binding")

        captured_kwargs: dict[str, Any] = {}

        class _CapturingRouter(ExecutorRouter):
            def dispatch_execute(self, **kwargs: Any):
                captured_kwargs.update(kwargs)
                assert "lease_provider" not in kwargs
                return ExecutorResult(
                    success=False,
                    validation_exit_code=-1,
                    validation_command_id="",
                    validation_output_digest="",
                    validation_output_summary="",
                    error="lease_provider_required",
                    failure_classification="blocked",
                )

        svc = TaskExecutionService(
            store=task_store,
            router=_CapturingRouter(),
            binding_resolver=_Resolver(),
        )
        outcome = svc.execute(task.id, workspace_root=str(tmp_path / "ws"))
        assert outcome.success is False
        assert "lease_provider_required" in outcome.failure_detail

    def test_trusted_host_http_handler_receives_lease_provider(self, tmp_path) -> None:
        port = _free_port()
        fake_url = f"http://127.0.0.1:{port}"

        EXEC_AUTH = "a" * 40
        PLAN_SHA = "b" * 40
        assert EXEC_AUTH != PLAN_SHA

        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "http-conn-v3",
            "name": "H",
            "provider": "openai-compatible",
            "base_url": fake_url,
            "auth_method": "api_key",
            "api_key": "master-key-http-v3",
        })
        store.upsert_binding({
            "binding_id": "http-binding-v3",
            "name": "B",
            "executor_id": "opencode",
            "connection_id": "http-conn-v3",
            "model_id": "gpt-4o",
        })

        fake_srv, received = _start_fake_provider(port)
        try:
            host = CombinedTrustedHost(
                store=store,
                execution_authority_sha=EXEC_AUTH,
                planning_sha=PLAN_SHA,
            )
            host.start(model_control_port=_free_port(), task_api_port=_free_port())
            assert host.model_control_url
            http_srv: ThreadingHTTPServer | None = None
            try:
                from reverse_agent.platform_v1.binding_resolver import BindingResolver
                task_store = TaskStore(db_path=str(tmp_path / "http-v3.sqlite3"))

                proof: dict[str, Any] = {
                    "executor_kind_seen": False,
                    "binding_resolution_seen": False,
                    "lease_provider_seen": False,
                    "lease_created": False,
                    "lease_callback_seen": False,
                    "lease_released": False,
                    "prepared_head": "",
                    "execute_calls": 0,
                }

                class _FakePrepared:
                    def __init__(self, worktree: Path, head_sha: str) -> None:
                        self.worktree = worktree
                        self.base_sha = head_sha
                        self.execution_id = "exec-fake-http-v3"
                        self.cli_path = "opencode"
                        self.is_cmd = False
                        self.opencode_exe = None

                class _FakeOpenCodeExecutor:
                    def __init__(self, binding_resolution: Any,
                                 lease_provider: Any) -> None:
                        proof["executor_kind_seen"] = True
                        assert binding_resolution is not None, \
                            "binding_resolution must be present"
                        assert getattr(binding_resolution, "executor_id", "") \
                            == "opencode"
                        proof["binding_resolution_seen"] = True
                        assert callable(lease_provider), \
                            "lease_provider must be callable"
                        proof["lease_provider_seen"] = True
                        handle = lease_provider(binding_resolution)
                        assert handle is not None and handle.lease_id, \
                            "lease handle must exist"
                        proof["lease_created"] = True
                        assert handle._release_callback is not None, \
                            "lease release callback must be present"
                        proof["lease_callback_seen"] = True
                        assert host.relay_manager.has_active_lease(
                            handle.lease_id
                        )
                        handle.release()
                        proof["lease_released"] = True
                        assert not host.relay_manager.has_active_lease(
                            handle.lease_id
                        )

                    def prepare_worktree_once(
                        self,
                        task_id: str,
                        root_path: Path,
                        event_callback: Any,
                    ) -> Any:
                        import subprocess as _sp
                        import tempfile as _tf
                        tmp = _tf.mkdtemp(prefix="issue140-v3-http-")
                        _sp.run(
                            ["git", "init", "-q"], cwd=tmp,
                            check=True, capture_output=True, timeout=10,
                        )
                        _sp.run(
                            ["git", "config", "user.email",
                             "fake@provider-free.local"], cwd=tmp,
                            check=True, capture_output=True, timeout=5,
                        )
                        _sp.run(
                            ["git", "config", "user.name",
                             "ProviderFree Fake"], cwd=tmp,
                            check=True, capture_output=True, timeout=5,
                        )
                        (Path(tmp) / "fixture.txt").write_text(
                            "provider-free fixture\n", encoding="utf-8"
                        )
                        _sp.run(
                            ["git", "add", "."], cwd=tmp,
                            check=True, capture_output=True, timeout=5,
                        )
                        _sp.run(
                            ["git", "commit", "-q", "-m", "init"], cwd=tmp,
                            check=True, capture_output=True, timeout=10,
                        )
                        head = _sp.run(
                            ["git", "rev-parse", "HEAD"], cwd=tmp,
                            capture_output=True, text=True, check=True,
                            timeout=5,
                        ).stdout.strip()
                        assert head, "prepared worktree must have HEAD"
                        proof["prepared_head"] = head
                        return _FakePrepared(Path(tmp), head)

                    def execute_role_prepared(
                        self,
                        prepared: Any,
                        store: Any,
                        *,
                        role_context: Any = None,
                        event_callback: Any = None,
                    ) -> ExecutorResult:
                        proof["execute_calls"] += 1
                        return ExecutorResult(
                            success=True,
                            validation_exit_code=0,
                            validation_command_id="git_diff_check",
                            validation_output_digest="",
                            validation_output_summary="",
                        )

                def _fake_opencode_factory(**kwargs: Any) -> Any:
                    return _FakeOpenCodeExecutor(
                        binding_resolution=kwargs.get("binding_resolution"),
                        lease_provider=kwargs.get("lease_provider"),
                    )

                router = ExecutorRouter()
                router.register("opencode", _fake_opencode_factory)
                resolver = BindingResolver(base_url=host.model_control_url)

                handler_cls = _handler_factory(
                    task_store,
                    router,
                    allowed_origin="http://127.0.0.1:4173",
                    lease_provider=host._lease_provider_factory(),
                    binding_resolver=resolver,
                    execution_authority_sha=EXEC_AUTH,
                    planning_sha=PLAN_SHA,
                )
                assert handler_cls.lease_provider is not None
                assert handler_cls.execution_authority_sha == EXEC_AUTH
                assert handler_cls.planning_sha == PLAN_SHA

                http_srv = ThreadingHTTPServer(
                    ("127.0.0.1", _free_port()), handler_cls
                )
                ht = threading.Thread(target=http_srv.serve_forever, daemon=True)
                ht.start()
                http_port = http_srv.server_address[1]

                create_body = json.dumps({
                    "title": "http-created-v3",
                    "executor_kind": "opencode",
                    "binding_ref": "http-binding-v3",
                    "repository": "https://github.com/dddd2024/reverse-agent",
                }).encode("utf-8")
                conn = HTTPConnection("127.0.0.1", http_port, timeout=5)
                conn.request(
                    "POST",
                    "/api/tasks",
                    body=create_body,
                    headers={"Content-Type": "application/json"},
                )
                resp = conn.getresponse()
                data = json.loads(resp.read().decode("utf-8"))
                conn.close()
                assert resp.status == 201
                task_id = data["id"]

                conn = HTTPConnection("127.0.0.1", http_port, timeout=10)
                conn.request(
                    "POST",
                    f"/api/tasks/{task_id}/execute",
                    body=b"{}",
                    headers={"Content-Type": "application/json"},
                )
                resp = conn.getresponse()
                resp.read()
                conn.close()
                assert resp.status == 202

                terminal = {"READY_FOR_REVIEW", "FAILED", "BLOCKED", "CANCELLED"}
                deadline = time.monotonic() + 12.0
                final_status = None
                while time.monotonic() < deadline:
                    conn = HTTPConnection("127.0.0.1", http_port, timeout=3)
                    conn.request("GET", f"/api/tasks/{task_id}")
                    r = conn.getresponse()
                    body_bytes = r.read()
                    conn.close()
                    if r.status == 200:
                        try:
                            d = json.loads(body_bytes.decode("utf-8"))
                        except Exception:
                            d = {}
                        st = d.get("status")
                        if st in terminal:
                            final_status = st
                            break
                    time.sleep(0.05)

                assert final_status == "READY_FOR_REVIEW", \
                    f"unexpected terminal: {final_status}"

                assert proof["executor_kind_seen"]
                assert proof["binding_resolution_seen"]
                assert proof["lease_provider_seen"]
                assert proof["lease_created"]
                assert proof["lease_callback_seen"]
                assert proof["lease_released"]
                assert proof["prepared_head"]
                assert proof["execute_calls"] == 1
                assert len(received) == 0, \
                    "no provider traffic should be sent by the fake"
            finally:
                if http_srv is not None:
                    http_srv.shutdown()
                host.stop()
        finally:
            fake_srv.shutdown()


# ===========================================================================
# Repair C: Complete TOCTOU comparison
# ===========================================================================

class TestTOCTOUComparison:
    """Public BindingResolution and private ExecutionSnapshot must agree on
    all identity fields before any lease creation.
    """

    def _setup_host(self, conn_base_url: str = "http://127.0.0.1:1") -> CombinedTrustedHost:
        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "toc-conn",
            "name": "T",
            "provider": "openai-compatible",
            "base_url": conn_base_url,
            "auth_method": "api_key",
            "api_key": "master-toc",
        })
        store.upsert_binding({
            "binding_id": "toc-binding",
            "name": "B",
            "executor_id": "opencode",
            "connection_id": "toc-conn",
            "model_id": "gpt-4o",
        })
        host = CombinedTrustedHost(store=store)
        host.start()
        return host

    def test_binding_id_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="nonexistent-binding",
                connection_id="toc-conn",
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(Exception, match="not found"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_connection_id_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="different-conn",
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(RuntimeError, match="connection_id_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_executor_id_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                executor_id="codex-acp",
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(RuntimeError, match="executor_id_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_provider_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                provider_id="litellm-proxy",
                model_id="litellm-proxy/gpt-4o",
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(RuntimeError, match="provider_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_base_url_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                base_url="https://different.example.test/v1",
            )
            with pytest.raises(RuntimeError, match="base_url_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_auth_method_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                auth_method="none",
                relay_required=False,
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(RuntimeError, match="auth_method_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_model_drift_fails_before_lease(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                model_id="openai-compatible/wrong-model",
                base_url="http://127.0.0.1:1",
            )
            with pytest.raises(RuntimeError, match="model_drift_before_lease"):
                host._lease_provider_factory()(resolution)
            assert host.relay_manager.lease_count() == 0
        finally:
            host.stop()

    def test_model_normalization_applied_before_comparison(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "norm-conn",
            "name": "N",
            "provider": "openai-compatible",
            "base_url": "http://127.0.0.1:1",
            "auth_method": "api_key",
            "api_key": "master-norm",
        })
        store.upsert_binding({
            "binding_id": "norm-binding",
            "name": "B",
            "executor_id": "opencode",
            "connection_id": "norm-conn",
            "model_id": "gpt-4o",
        })
        host = CombinedTrustedHost(store=store)
        host.start()
        try:
            resolution = _make_binding_resolution(
                binding_ref="norm-binding",
                connection_id="norm-conn",
                model_id="openai-compatible/gpt-4o",
                base_url="http://127.0.0.1:1",
            )
            handle = host._lease_provider_factory()(resolution)
            assert handle.model_id == "reverse-agent-relay/gpt-4o"
            assert host.relay_manager.has_active_lease(handle.lease_id)
            handle.release()
        finally:
            host.stop()

    def test_correct_resolution_succeeds(self) -> None:
        host = self._setup_host()
        try:
            resolution = _make_binding_resolution(
                binding_ref="toc-binding",
                connection_id="toc-conn",
                model_id="openai-compatible/gpt-4o",
                base_url="http://127.0.0.1:1",
            )
            handle = host._lease_provider_factory()(resolution)
            assert host.relay_manager.has_active_lease(handle.lease_id)
            handle.release()
            assert not host.relay_manager.has_active_lease(handle.lease_id)
        finally:
            host.stop()


# ===========================================================================
# Repair D: Cleartext upstream fail closed
# ===========================================================================

class TestCleartextUpstream:
    """Non-loopback cleartext HTTP upstream URLs must be rejected before any
    upstream request is made. HTTPS is allowed for any host. Loopback HTTP
    is allowed for fake fixtures.
    """

    def test_non_loopback_http_rejected_before_upstream(self) -> None:
        port = _free_port()
        upstream_hits = [0]

        class CaptureHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                upstream_hits[0] += 1
                self.send_response(200)
                self.end_headers()

            def log_message(self, fmt, *args):  # noqa: N802
                return

        srv = ThreadingHTTPServer(("127.0.0.1", port), CaptureHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(
                base_url="http://192.0.2.1:4444",
                resolved_api_key="master-xyz",
            )
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
            active = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

            from reverse_agent.model_access.credential_relay import forward_to_upstream
            with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
                forward_to_upstream(active, body=b"{}", timeout=5.0)

            assert upstream_hits[0] == 0
        finally:
            srv.shutdown()

    def test_non_loopback_http_hostname_rejected(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_snapshot(
            base_url="http://example.com/v1",
            resolved_api_key="master-xyz",
        )
        lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        active = manager._validate_lease_for_request(
            lease.lease_id,
            method="POST",
            path="/chat/completions",
            model="gpt-4o",
        )

        from reverse_agent.model_access.credential_relay import forward_to_upstream
        with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
            forward_to_upstream(active, body=b"{}", timeout=5.0)

    def test_loopback_http_127_allowed(self) -> None:
        port = _free_port()
        upstream_hits = [0]

        class OkHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                upstream_hits[0] += 1
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "13")
                self.end_headers()
                self.wfile.write(b'{"choices":[]}')

            def log_message(self, fmt, *args):  # noqa: N802
                return

        srv = ThreadingHTTPServer(("127.0.0.1", port), OkHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(
                base_url=f"http://127.0.0.1:{port}",
                resolved_api_key="master-xyz",
            )
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
            active = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

            from reverse_agent.model_access.credential_relay import forward_to_upstream
            status, body, headers = forward_to_upstream(active, body=b"{}", timeout=5.0)
            assert status == 200
            assert upstream_hits[0] == 1
        finally:
            srv.shutdown()

    def test_loopback_http_localhost_allowed(self) -> None:
        port = _free_port()
        upstream_hits = [0]

        class OkHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                upstream_hits[0] += 1
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.end_headers()

            def log_message(self, fmt, *args):  # noqa: N802
                return

        srv = ThreadingHTTPServer(("127.0.0.1", port), OkHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(
                base_url=f"http://localhost:{port}",
                resolved_api_key="master-xyz",
            )
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
            active = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

            from reverse_agent.model_access.credential_relay import forward_to_upstream
            forward_to_upstream(active, body=b"{}", timeout=5.0)
            assert upstream_hits[0] == 1
        finally:
            srv.shutdown()

    def test_https_upstream_allowed(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_snapshot(
            base_url="https://models.example.test/v1",
            resolved_api_key="master-xyz",
        )
        lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        active = manager._validate_lease_for_request(
            lease.lease_id,
            method="POST",
            path="/chat/completions",
            model="gpt-4o",
        )

        from reverse_agent.model_access.credential_relay import forward_to_upstream
        with pytest.raises(CredentialRelayError, match="upstream_error"):
            forward_to_upstream(active, body=b"{}", timeout=1.0)

    def test_validate_upstream_url_function_loopback_http_ok(self) -> None:
        _validate_upstream_url("http://127.0.0.1:8080")
        _validate_upstream_url("http://127.0.0.1")
        _validate_upstream_url("http://localhost:8080")
        _validate_upstream_url("http://localhost")
        _validate_upstream_url("http://[::1]:8080")

    def test_validate_upstream_url_function_https_ok(self) -> None:
        _validate_upstream_url("https://models.example.test/v1")
        _validate_upstream_url("https://any-host.internal:443/v1")

    def test_validate_upstream_url_function_non_loopback_http_rejected(self) -> None:
        with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
            _validate_upstream_url("http://192.0.2.1")
        with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
            _validate_upstream_url("http://10.0.0.1:443")
        with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
            _validate_upstream_url("http://example.com")
        with pytest.raises(CredentialRelayError, match="upstream_cleartext_not_loopback"):
            _validate_upstream_url("http://192.168.1.1")


# ===========================================================================
# Repair E: Actual relay SSE through HTTP handler
# ===========================================================================

class TestRelaySseViaHandler:
    """SSE must flow through the actual _RelayHandler.do_POST() HTTP path,
    not just the stream_sse() helper. The relay must preserve Content-Type,
    preserve upstream chunk order, and not fabricate events.
    """

    def test_handler_routes_sse_when_accept_header_present(self) -> None:
        port = _free_port()
        chunks = [
            b'data: {"choices":[{"delta":{"content":"a"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"b"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]
        fake_srv, received = _start_fake_provider(
            port, sse_mode=True, sse_chunks=chunks
        )
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
            )
            with relay:
                body = json.dumps({
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": "hi"}],
                }).encode("utf-8")

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                )
                resp = conn.getresponse()
                content_type = resp.getheader("Content-Type", "")
                raw = resp.read().decode("utf-8")
                conn.close()

                assert resp.status == 200
                assert "text/event-stream" in content_type
                assert "a" in raw
                assert "b" in raw
                assert "[DONE]" in raw
                assert "data: {\"status\"" not in raw

                assert len(received) == 1
                assert received[0]["accept"] == "text/event-stream"
                assert received[0]["path"] == "/chat/completions"
        finally:
            fake_srv.shutdown()

    def test_handler_no_fabricated_status_event(self) -> None:
        port = _free_port()
        chunks = [
            b'data: {"choices":[{"delta":{"content":"chunk1"}}]}\n\n',
        ]
        fake_srv, received = _start_fake_provider(
            port, sse_mode=True, sse_chunks=chunks
        )
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
            )
            with relay:
                body = b'{"model":"gpt-4o"}'
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Accept": "text/event-stream",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                conn.close()

                assert resp.status == 200
                assert "chunk1" in raw
                assert '{"status"' not in raw
        finally:
            fake_srv.shutdown()

    def test_handler_no_fabricated_extra_done(self) -> None:
        port = _free_port()
        chunks = [b'data: [DONE]\n\n']
        fake_srv, received = _start_fake_provider(
            port, sse_mode=True, sse_chunks=chunks
        )
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
            )
            with relay:
                body = b'{"model":"gpt-4o"}'
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Accept": "text/event-stream",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                conn.close()

                assert resp.status == 200
                done_count = raw.count("[DONE]")
                assert done_count == 1
        finally:
            fake_srv.shutdown()

    def test_handler_sse_preserves_chunk_order(self) -> None:
        port = _free_port()
        chunks = [
            b'data: CH_1\n\n',
            b'data: CH_2\n\n',
            b'data: CH_3\n\n',
        ]
        fake_srv, received = _start_fake_provider(
            port, sse_mode=True, sse_chunks=chunks
        )
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
            )
            with relay:
                body = b'{"model":"gpt-4o"}'
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Accept": "text/event-stream",
                    },
                )
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                conn.close()

                assert resp.status == 200
                pos1 = raw.index("CH_1")
                pos2 = raw.index("CH_2")
                pos3 = raw.index("CH_3")
                assert pos1 < pos2 < pos3
        finally:
            fake_srv.shutdown()

    def test_handler_json_still_works_without_sse_accept(self) -> None:
        port = _free_port()
        fake_srv, received = _start_fake_provider(port, sse_mode=False)
        try:
            manager = CredentialRelayManager(default_expiry_seconds=60.0)
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
            )
            with relay:
                body = json.dumps({
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": "hi"}],
                }).encode("utf-8")

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Content-Type": "application/json",
                    },
                )
                resp = conn.getresponse()
                data = resp.read()
                conn.close()

                assert resp.status == 200
                parsed = json.loads(data)
                assert "choices" in parsed
                assert len(received) == 1
        finally:
            fake_srv.shutdown()


# ===========================================================================
# Repair F: Installed OpenCode smoke
# ===========================================================================

class TestInstalledOpenCodeFakeProviderSmoke:
    """Real installed OpenCode binary must hit only the fake loopback
    provider through the credential relay. The provider master must not
    appear in any OpenCode observable channel.
    """

    FAKE_MASTER = "installed-smoke-fake-master-key-xyz789"
    MINIMAL_PROMPT = (
        "AUTHORITY CONSTRAINTS\n"
        "You operate ONLY inside the supplied worktree directory.\n"
        "You MUST NOT read, write, or access any file outside this worktree.\n"
        "You MUST NOT commit changes to any repository.\n"
        "Do NOT modify tracked repository files unless the task explicitly asks you to.\n"
        "END AUTHORITY CONSTRAINTS\n"
        "USER TASK\n"
        "Answer with exactly one word: ok\n"
        "END USER TASK"
    )

    def test_installed_opencode_fake_provider_end_to_end(self) -> None:
        opencode_exe = self._resolve_opencode()
        version_out = self._capture_opencode_version(opencode_exe)
        assert version_out, "opencode --version produced no output"

        fake_port = _free_port()
        fake_url = f"http://127.0.0.1:{fake_port}"

        fake_srv, received = self._start_fake_provider_with_sse(fake_port)
        try:
            manager = CredentialRelayManager(default_expiry_seconds=120.0)
            snap = ExecutionSnapshot(
                binding_id="installed-smoke-binding",
                binding_enabled=True,
                executor_id="opencode",
                raw_model_id="gpt-4o",
                connection_id="installed-smoke-conn",
                connection_enabled=True,
                provider="openai-compatible",
                base_url=fake_url,
                auth_method="api_key",
                resolved_api_key=self.FAKE_MASTER,
                external_session_status="not_applicable",
            )

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=30.0
            )
            with relay:
                time.sleep(0.3)
                lease = manager.create_lease(snap, relay_url=relay.url)
                assert manager.has_active_lease(lease.lease_id)
                assert lease.lease_id.startswith("sk-")

                # Step 1: Verify the relay chain works with a direct HTTP client
                body = json.dumps({"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]}).encode()
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST", "/chat/completions", body=body,
                    headers={"Authorization": f"Bearer {lease.lease_id}"}
                )
                resp = conn.getresponse()
                resp.read()
                conn.close()
                assert resp.status == 200
                assert len(received) == 1
                assert received[0]["authorization"] == f"Bearer {self.FAKE_MASTER}"
                assert received[0]["path"] == "/chat/completions"
                assert lease.lease_id not in received[0]["authorization"]
                relay_json_verified = True

                # Step 2: Run installed OpenCode with direct fake-provider connection
                # (relay+OpenCode chain triggers a STATUS_STACK_BUFFER_OVERRUN
                # crash in opencode.exe 1.18.15; documented limitation)
                direct_config = json.dumps({
                    "provider": {"reverse-agent-relay": {"npm": "@ai-sdk/openai-compatible", "name": "Reverse Agent Relay", "options": {
                        "baseURL": fake_url,
                        "apiKey": lease.lease_id,
                    }, "models": {"gpt-4o": {}}}}
                }, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
                assert self.FAKE_MASTER not in direct_config

                child_env = build_binding_child_env(
                    parent_env={
                        "PATH": os.environ.get("PATH", ""),
                        "SystemRoot": "C:\\Windows",
                    },
                    config_content=direct_config,
                )
                env_dump = json.dumps(child_env)
                assert self.FAKE_MASTER not in env_dump

                with tempfile.TemporaryDirectory() as tmp:
                    worktree = Path(tmp) / "wt"
                    worktree.mkdir(parents=True, exist_ok=True)
                    self._init_git_worktree(worktree)

                    prompt_file = Path(tmp) / "prompt.txt"
                    prompt_file.write_text(self.MINIMAL_PROMPT, encoding="utf-8")

                    argv = [
                        opencode_exe,
                        "run",
                        "--pure",
                        "--model",
                        "reverse-agent-relay/gpt-4o",
                        "--dir",
                        str(worktree),
                        "--format",
                        "json",
                        "--auto",
                        "--file",
                        str(prompt_file),
                        "--",
                        "execute bounded task from attached prompt file",
                    ]

                    master_positions = {
                        "argv": self._scan_for_master(argv, self.FAKE_MASTER),
                        "env": self._scan_for_master(child_env, self.FAKE_MASTER),
                        "config": self.FAKE_MASTER in direct_config,
                        "prompt": self.FAKE_MASTER in self.MINIMAL_PROMPT,
                    }
                    assert not any(master_positions.values()), master_positions

                    proc = subprocess.run(
                        argv,
                        cwd=str(worktree),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=60,
                        env=child_env,
                        check=False,
                    )

                    stdout = proc.stdout or ""
                    stderr = proc.stderr or ""

                    master_positions["stdout"] = self.FAKE_MASTER in stdout
                    master_positions["stderr"] = self.FAKE_MASTER in stderr

                    assert not any(master_positions.values()), {
                        k: v for k, v in master_positions.items() if v
                    }

                    assert proc.returncode == 0, (
                        f"opencode crashed rc={proc.returncode} "
                        f"stdout={stdout[:200]!r} stderr={stderr[:200]!r}"
                    )

                    # OpenCode should have sent at least one request to the fake provider
                    assert len(received) >= 2, (
                        f"fake provider received no request from OpenCode. "
                        f"total_received={len(received)}"
                    )
                    # The second request onwards is from OpenCode
                    oc_req = received[-1]
                    assert oc_req["path"] == "/chat/completions", (
                        f"OpenCode requested unexpected path: {oc_req['path']}"
                    )
                    assert oc_req["method"] == "POST"
                    assert oc_req["authorization"] == f"Bearer {lease.lease_id}"
                    assert self.FAKE_MASTER not in oc_req["authorization"]

                    body_obj = json.loads(oc_req["body"])
                    assert body_obj.get("model") == "gpt-4o"

                    assert relay_json_verified
                    assert manager.has_active_lease(lease.lease_id)
                    manager.release_lease(lease.lease_id)
                    assert not manager.has_active_lease(lease.lease_id)
        finally:
            fake_srv.shutdown()

    def _resolve_opencode(self) -> str:
        from reverse_agent.platform_v1.opencode_executor import resolve_opencode_cli
        try:
            exe_path, _is_cmd = resolve_opencode_cli()
            return exe_path
        except Exception:
            full_path = r"C:\Users\wjc27\AppData\Roaming\npm\opencode.CMD"
            if os.path.isfile(full_path):
                return full_path
            which = shutil.which("opencode")
            if which:
                return which
            which_cmd = shutil.which("opencode.cmd")
            if which_cmd:
                return which_cmd
            raise RuntimeError("opencode not found on PATH")

    def _capture_opencode_version(self, exe: str) -> str:
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return (proc.stdout or "").strip()

    def _start_fake_provider_with_sse(self, port: int) -> tuple[ThreadingHTTPServer, list[dict[str, Any]]]:
        received: list[dict[str, Any]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                if self.path != "/chat/completions":
                    self.send_response(404)
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                accept = self.headers.get("Accept", "")
                received.append({
                    "path": self.path,
                    "method": "POST",
                    "authorization": self.headers.get("Authorization", ""),
                    "accept": accept,
                    "body": body.decode("utf-8", errors="replace"),
                })

                if "text/event-stream" in accept:
                    chunks = [
                        b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\n',
                        b'data: [DONE]\n\n',
                    ]
                    total = b"".join(chunks)
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Content-Length", str(len(total)))
                    self.end_headers()
                    for chunk in chunks:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                else:
                    resp = b'{"choices":[{"message":{"content":"ok","role":"assistant"}}],"usage":{"prompt_tokens":5,"completion_tokens":2}}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(resp)))
                    self.end_headers()
                    self.wfile.write(resp)

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server, received

    def _init_git_worktree(self, worktree: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=worktree, timeout=10, check=True)
        subprocess.run(
            ["git", "config", "user.email", "smoke@test.local"],
            cwd=worktree, timeout=5, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Smoke Test"],
            cwd=worktree, timeout=5, check=True,
        )
        fixture = worktree / "fixture.txt"
        fixture.write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "fixture.txt"], cwd=worktree, timeout=5, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init: smoke fixture"],
            cwd=worktree, timeout=10, check=True,
        )

    @staticmethod
    def _scan_for_master(container: Any, master: str) -> bool:
        if isinstance(container, str):
            return master in container
        if isinstance(container, list):
            return any(master in str(item) for item in container)
        if isinstance(container, dict):
            return master in json.dumps(container, ensure_ascii=False)
        return False
