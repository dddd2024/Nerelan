"""Combined trusted host for Platform V1.

A single Python process that exposes:
  - Model Control API on 127.0.0.1:8765
  - Task API on 127.0.0.1:8766

Both services share a single :class:`~reverse_agent.model_access.store.
ModelProfileStore`, and the Task API is wired to a
:class:`~reverse_agent.model_access.credential_relay.
CredentialRelayManager` so that api_key Bindings obtain execution-scoped
leases before OpenCode launch.

No DB, no management API, no plugin system, no model catalog.  Only the
existing public GET/PUT/DELETE routes on both ports, plus the private
credential relay used internally during execution.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import os
import threading
from typing import Any

from ..model_access.contracts import ExecutionSnapshot
from ..model_access.credential_relay import (
    CredentialRelayManager,
    ExecutionLease,
    _normalize_model_id,
)
from ..model_access.service import _handler_factory as _model_control_handler_factory
from ..model_access.store import ModelProfileStore
from .github_adapter import LiveGitHubAdapter
from .opencode_executor import ExecutionLeaseHandle
from .run_store import TaskStore
from .task_runtime import ExecutorRouter
from .task_service import _handler_factory as _task_handler_factory
from .durable_execution import DurableExecutionService


class CombinedTrustedHost:
    """One-process host for Model Control + Task API + credential relay."""

    def __init__(
        self,
        *,
        store: ModelProfileStore | None = None,
        task_store: TaskStore | None = None,
        relay_manager: CredentialRelayManager | None = None,
        model_control_host: str = "127.0.0.1",
        model_control_port: int = 8765,
        task_api_host: str = "127.0.0.1",
        task_api_port: int = 8766,
        allowed_origin: str = "http://127.0.0.1:4173",
        task_db_path: str | None = None,
        github_adapter: LiveGitHubAdapter | None = None,
        execution_authority_sha: str = "",
        planning_sha: str = "",
    ) -> None:
        self._store = store or ModelProfileStore()
        self._task_store = task_store or _make_task_store(task_db_path)
        self._relay_manager = relay_manager or CredentialRelayManager()
        self._router = ExecutorRouter()
        self._github_adapter = github_adapter
        self._execution_authority_sha = execution_authority_sha
        self._planning_sha = planning_sha

        self._model_control_host = model_control_host
        self._model_control_port = model_control_port
        self._task_api_host = task_api_host
        self._task_api_port = task_api_port
        self._allowed_origin = allowed_origin

        self._model_server: ThreadingHTTPServer | None = None
        self._task_server: ThreadingHTTPServer | None = None
        self._relay_server: CredentialRelayServer | None = None
        self._threads: list[threading.Thread] = []

        self.model_control_url = ""
        self.task_api_url = ""
        self.relay_url = ""

    @property
    def store(self) -> ModelProfileStore:
        return self._store

    @property
    def task_store(self) -> TaskStore:
        return self._task_store

    @property
    def relay_manager(self) -> CredentialRelayManager:
        return self._relay_manager

    @property
    def github_adapter(self) -> LiveGitHubAdapter | None:
        return self._github_adapter

    def _lease_provider_factory(self) -> Any:
        manager = self._relay_manager
        store = self._store
        relay_url = self.relay_url

        def _provider(resolution: Any) -> ExecutionLeaseHandle:
            snapshot = store.resolve_execution_snapshot(resolution.binding_ref)
            if snapshot.binding_id != resolution.binding_ref:
                raise RuntimeError("binding_id_drift_before_lease")
            if snapshot.connection_id != resolution.connection_id:
                raise RuntimeError("connection_id_drift_before_lease")
            if snapshot.executor_id != resolution.executor_id:
                raise RuntimeError("executor_id_drift_before_lease")
            if snapshot.provider != resolution.provider_id:
                raise RuntimeError("provider_drift_before_lease")
            if snapshot.base_url != resolution.base_url:
                raise RuntimeError("base_url_drift_before_lease")
            if snapshot.auth_method != resolution.auth_method:
                raise RuntimeError("auth_method_drift_before_lease")
            expected_model = _normalize_model_id(snapshot.provider, snapshot.raw_model_id)
            if expected_model != resolution.model_id:
                raise RuntimeError("model_drift_before_lease")

            lease = manager.create_lease(
                snapshot,
                relay_url=relay_url,
            )
            lease_id = lease.lease_id

            provider_facing_model = lease.model_id
            cli_model = f"reverse-agent-relay/{provider_facing_model}"

            def _release() -> None:
                manager.release_lease(lease_id)

            return ExecutionLeaseHandle(
                lease_id=lease.lease_id,
                relay_url=lease.relay_url,
                model_id=cli_model,
                _release_callback=_release,
            )

        return _provider

    def start(
        self,
        *,
        model_control_port: int | None = None,
        task_api_port: int | None = None,
    ) -> None:
        # Startup reconciliation: find expired durable runs, mark stale
        # tasks INTERRUPTED with orphan_stale_lease classification.
        # Does NOT call any model/provider; reconciliation only.
        dur_svc = DurableExecutionService(
            store=self._task_store,
            router=self._router,
        )
        try:
            dur_svc.reconcile_expired_runs()
        except Exception:
            pass

        mcp = model_control_port if model_control_port is not None else self._model_control_port
        tap = task_api_port if task_api_port is not None else self._task_api_port

        live_enabled = os.environ.get("REVERSE_AGENT_MODEL_CONTROL_LIVE") == "1"
        mc_handler = _model_control_handler_factory(
            self._store,
            live_enabled=live_enabled,
            allowed_origin=self._allowed_origin,
        )
        self._model_server = ThreadingHTTPServer(
            (self._model_control_host, mcp), mc_handler
        )
        actual_mc_port = self._model_server.server_address[1]
        self.model_control_url = f"http://{self._model_control_host}:{actual_mc_port}"

        from ..model_access.credential_relay import run_credential_relay_server
        relay_srv = run_credential_relay_server(
            manager=self._relay_manager,
            host="127.0.0.1",
            port=0,
            upstream_timeout=120.0,
        )
        self._relay_server_port = relay_srv.server_address[1]
        self._relay_server_inner = relay_srv
        self.relay_url = f"http://127.0.0.1:{self._relay_server_port}"

        from .binding_resolver import BindingResolver
        binding_resolver = BindingResolver(base_url=self.model_control_url)
        live_github = self._github_adapter
        if live_github is None:
            live_github = LiveGitHubAdapter()
        task_handler = _task_handler_factory(
            self._task_store,
            self._router,
            allowed_origin=self._allowed_origin,
            lease_provider=self._lease_provider_factory(),
            binding_resolver=binding_resolver,
            github_adapter=live_github,
            execution_authority_sha=self._execution_authority_sha,
            planning_sha=self._planning_sha,
        )
        self._task_server = ThreadingHTTPServer(
            (self._task_api_host, tap), task_handler
        )
        actual_task_port = self._task_server.server_address[1]
        self.task_api_url = f"http://{self._task_api_host}:{actual_task_port}"

        for server in (self._model_server, self._task_server, relay_srv):
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        for server in (self._model_server, self._task_server, getattr(self, "_relay_server_inner", None)):
            if server:
                try:
                    server.shutdown()
                except Exception:
                    pass
        for t in self._threads:
            t.join(timeout=3.0)
        self._threads.clear()
        self._relay_manager.release_all()


def _make_task_store(db_path: str | None) -> TaskStore:
    if db_path:
        return TaskStore(db_path=db_path)
    runtime_dir = os.environ.get(
        "REVERSE_AGENT_TASK_DB_DIR",
        os.path.join(os.getcwd(), ".platform_v1_runtime"),
    )
    os.makedirs(runtime_dir, exist_ok=True)
    return TaskStore(
        db_path=os.path.join(runtime_dir, "tasks.sqlite3")
    )


def run_combined_trusted_host() -> None:
    host = CombinedTrustedHost()
    host.start()
    metadata = {
        "model_control_url": host.model_control_url,
        "task_api_url": host.task_api_url,
        "relay_url": host.relay_url,
    }
    runtime_dir = os.environ.get(
        "REVERSE_AGENT_TASK_DB_DIR",
        os.path.join(os.getcwd(), ".platform_v1_runtime"),
    )
    os.makedirs(runtime_dir, exist_ok=True)
    meta_path = os.path.join(runtime_dir, "trusted_host_meta.json")
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    print(f"Combined Trusted Host started")
    print(f"  Model Control: {host.model_control_url}")
    print(f"  Task API:      {host.task_api_url}")
    print(f"  Relay:         {host.relay_url}")

    try:
        host._model_server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        host.stop()


if __name__ == "__main__":
    run_combined_trusted_host()