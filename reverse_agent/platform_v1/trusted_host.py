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

from collections.abc import Callable
from http.server import ThreadingHTTPServer
import json
import os
import subprocess
import threading
import time
from typing import Any

from ..model_access.contracts import ExecutionSnapshot
from ..model_access.credential_relay import (
    CredentialRelayManager,
    ExecutionLease,
    _normalize_model_id,
)
from ..model_access.os_vault import default_vault_adapter
from ..model_access.account_auth import AccountAuthManager, ServerFactory
from ..model_access.service import _handler_factory as _model_control_handler_factory
from ..model_access.store import ModelProfileStore
from .github_adapter import LiveGitHubAdapter
from .opencode_executor import (
    ExecutionLeaseHandle,
    execute_opencode_auth_list_probe,
    start_opencode_account_auth_server,
)
from .run_store import TaskStore
from .task_runtime import ExecutorRouter
from .task_service import _handler_factory as _task_handler_factory
from .durable_execution import DurableExecutionService
from .autonomy import AutonomyService
from .capability_registry import CapabilityRegistry
from .control_store import PlatformControlStore
from .goal_service import GoalService
from .publication_controller import PublicationController
from .unattended_coordinator import UnattendedCoordinator


class CombinedTrustedHost:
    """One-process host for Model Control + Task API + credential relay."""

    # Sentinel: auto-constructed stores use the platform vault adapter
    # (``default_vault_adapter()``). Passing ``vault=None`` forces the exact
    # legacy process-local behavior; tests inject a fake adapter.
    _PLATFORM_VAULT: Any = object()

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
        auth_list_probe: Callable[[], dict[str, str]] | None = None,
        auth_refresh_ttl_seconds: float = 5.0,
        auth_refresh_clock: Callable[[], float] = time.monotonic,
        account_auth_server_factory: ServerFactory | None = None,
        vault: Any = _PLATFORM_VAULT,
    ) -> None:
        if auth_refresh_ttl_seconds < 0:
            raise ValueError("auth_refresh_ttl_seconds must be non-negative")
        task_store = task_store or _make_task_store(task_db_path)
        if store is not None:
            self._store = store
        else:
            state_path = _resolve_store_state_path(task_store)
            # Platforms without a supported OS vault adapter (None) keep the
            # exact legacy process-local behavior; there is no plaintext
            # fallback for durable storage.
            resolved_vault = (
                default_vault_adapter()
                if vault is CombinedTrustedHost._PLATFORM_VAULT
                else vault
            )
            self._store = ModelProfileStore(
                state_path=state_path,
                vault=resolved_vault,
            )
        self._task_store = task_store
        self._relay_manager = relay_manager or CredentialRelayManager()
        self._router = ExecutorRouter()
        self._github_adapter = github_adapter
        self._execution_authority_sha = execution_authority_sha
        self._planning_sha = planning_sha
        self._auth_list_probe = auth_list_probe
        self._auth_refresh_ttl_seconds = float(auth_refresh_ttl_seconds)
        self._auth_refresh_clock = auth_refresh_clock
        self._auth_refresh_condition = threading.Condition()
        self._auth_refresh_in_progress = False
        self._auth_refresh_last_completed: float | None = None
        self._account_auth = AccountAuthManager(
            store=self._store,
            server_factory=account_auth_server_factory,
            refresh=self._refresh_external_session_auth,
        )
        self._control_store = PlatformControlStore(self._task_store)
        self._capability_registry = CapabilityRegistry(
            pack_dir=os.environ.get("REVERSE_AGENT_CAPABILITY_PACK_DIR") or None
        )
        self._autonomy_service = AutonomyService(
            control_store=self._control_store,
            capabilities=self._capability_registry,
        )
        self._goal_service = GoalService(
            store=self._task_store,
            control_store=self._control_store,
        )
        self._publication_controller: PublicationController | None = None
        self._coordinator: UnattendedCoordinator | None = None

        self._model_control_host = model_control_host
        self._model_control_port = model_control_port
        self._task_api_host = task_api_host
        self._task_api_port = task_api_port
        self._allowed_origin = allowed_origin

        self._model_server: ThreadingHTTPServer | None = None
        self._task_server: ThreadingHTTPServer | None = None
        self._relay_server: CredentialRelayServer | None = None
        self._relay_server_inner: ThreadingHTTPServer | None = None
        self._threads: list[threading.Thread] = []
        self._started_servers: list[ThreadingHTTPServer] = []

        self.model_control_url = ""
        self.task_api_url = ""
        self.relay_url = ""

    @property
    def store(self) -> ModelProfileStore:
        return self._store

    def _refresh_external_session_auth(
        self,
        force: bool = False,
        connection_id: str | None = None,
    ) -> None:
        probe = self._auth_list_probe
        if probe is None:
            return
        if not self._connection_needs_external_session_refresh(connection_id):
            return

        with self._auth_refresh_condition:
            now = self._auth_refresh_clock()
            last_completed = self._auth_refresh_last_completed
            if (
                not force
                and last_completed is not None
                and now - last_completed < self._auth_refresh_ttl_seconds
            ):
                return
            if self._auth_refresh_in_progress:
                while self._auth_refresh_in_progress:
                    self._auth_refresh_condition.wait()
                return
            self._auth_refresh_in_progress = True

        provider_metadata: dict[str, str] = {}
        try:
            result = probe()
            if isinstance(result, dict):
                provider_metadata = result
        except Exception:
            provider_metadata = {}
        finally:
            try:
                self._store.refresh_external_session_status(provider_metadata)
            finally:
                with self._auth_refresh_condition:
                    self._auth_refresh_last_completed = self._auth_refresh_clock()
                    self._auth_refresh_in_progress = False
                    self._auth_refresh_condition.notify_all()

    def _connection_needs_external_session_refresh(
        self,
        connection_id: str | None,
    ) -> bool:
        if connection_id is None:
            return self._has_external_session_connections()
        try:
            connection = self._store.get_connection_public(connection_id)
        except KeyError:
            return False
        return connection["auth_method"] in {
            "account_login",
            "external_cli_session",
        }

    def _has_external_session_connections(self) -> bool:
        return self._store.has_external_session_connections()

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

    def _binding_resolver_factory(self, base_url: str) -> Any:
        from .binding_resolver import BindingResolutionError, BindingResolver

        host = self
        delegate = BindingResolver(base_url=base_url)

        class FreshExternalSessionBindingResolver:
            def resolve(self, binding_ref: str, *, task_executor: str) -> Any:
                snapshot = host._store.resolve_execution_snapshot(binding_ref)
                if snapshot.auth_method in {
                    "account_login",
                    "external_cli_session",
                }:
                    host._refresh_external_session_auth(
                        True,
                        snapshot.connection_id,
                    )
                resolution = delegate.resolve(
                    binding_ref,
                    task_executor=task_executor,
                )
                if (
                    resolution.auth_method
                    in {"account_login", "external_cli_session"}
                    and resolution.external_session_status != "available"
                ):
                    raise BindingResolutionError("external_session_unavailable")
                return resolution

        return FreshExternalSessionBindingResolver()

    def start(
        self,
        *,
        model_control_port: int | None = None,
        task_api_port: int | None = None,
    ) -> None:
        self._refresh_external_session_auth(True)

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

        try:
            live_enabled = os.environ.get("REVERSE_AGENT_MODEL_CONTROL_LIVE") == "1"
            mc_handler = _model_control_handler_factory(
                self._store,
                live_enabled=live_enabled,
                allowed_origin=self._allowed_origin,
                external_session_refresh=self._refresh_external_session_auth,
                account_auth=self._account_auth,
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

            binding_resolver = self._binding_resolver_factory(self.model_control_url)
            live_github = self._github_adapter
            if live_github is None:
                live_github = LiveGitHubAdapter()
            self._publication_controller = PublicationController(
                store=self._task_store,
                control_store=self._control_store,
                autonomy=self._autonomy_service,
            )
            workspace_root = os.environ.get("REVERSE_AGENT_TASK_WORKSPACE_ROOT", "").strip()
            if not workspace_root:
                workspace_root = os.path.join(
                    os.path.dirname(os.path.abspath(self._task_store.db_path)) or ".",
                    "task_workspaces",
                )
            self._coordinator = UnattendedCoordinator(
                store=self._task_store,
                control_store=self._control_store,
                autonomy=self._autonomy_service,
                router=self._router,
                workspace_root=workspace_root,
                lease_provider=self._lease_provider_factory(),
                binding_resolver=binding_resolver,
                execution_authority_sha=self._execution_authority_sha,
                planning_sha=self._planning_sha,
            )
            task_handler = _task_handler_factory(
                self._task_store,
                self._router,
                allowed_origin=self._allowed_origin,
                lease_provider=self._lease_provider_factory(),
                binding_resolver=binding_resolver,
                github_adapter=live_github,
                execution_authority_sha=self._execution_authority_sha,
                planning_sha=self._planning_sha,
                control_store=self._control_store,
                goal_service=self._goal_service,
                autonomy_service=self._autonomy_service,
                capability_registry=self._capability_registry,
                publication_controller=self._publication_controller,
                coordinator=self._coordinator,
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
                self._started_servers.append(server)
            if os.environ.get("REVERSE_AGENT_AUTONOMOUS") == "1" and self._coordinator:
                self._coordinator.start()
        except BaseException:
            self._cleanup_runtime_resources(close_account_auth=True)
            raise

    def _cleanup_runtime_resources(self, *, close_account_auth: bool) -> None:
        if close_account_auth:
            try:
                self._account_auth.close()
            except Exception:
                pass
        if self._coordinator:
            try:
                self._coordinator.stop()
            except Exception:
                pass

        started_servers = tuple(self._started_servers)
        for server in started_servers:
            try:
                server.shutdown()
            except Exception:
                pass

        for thread in tuple(self._threads):
            try:
                thread.join(timeout=3.0)
            except Exception:
                pass

        created_servers = (
            self._model_server,
            self._task_server,
            self._relay_server_inner,
        )
        seen: set[int] = set()
        for server in created_servers:
            if server is None or id(server) in seen:
                continue
            seen.add(id(server))
            try:
                server.server_close()
            except Exception:
                pass

        self._threads.clear()
        self._started_servers.clear()
        self._model_server = None
        self._task_server = None
        self._relay_server_inner = None
        self._relay_manager.release_all()

    def stop(self) -> None:
        self._cleanup_runtime_resources(close_account_auth=True)


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


def _resolve_store_state_path(task_store: TaskStore) -> str:
    db_path = task_store.db_path
    if not db_path or db_path == ":memory:":
        runtime_dir = os.environ.get(
            "REVERSE_AGENT_TASK_DB_DIR",
            os.path.join(os.getcwd(), ".platform_v1_runtime"),
        )
        os.makedirs(runtime_dir, exist_ok=True)
        return os.path.join(runtime_dir, "model_setup_state.json")
    parent = os.path.dirname(os.path.abspath(db_path)) or "."
    os.makedirs(parent, exist_ok=True)
    return os.path.join(parent, "model_setup_state.json")


def _resolve_trusted_authority_sha() -> str:
    """Resolve trusted execution authority SHA from trusted runtime config.

    HTTP request bodies MUST NOT supply this value. Resolution order:
    1. REVERSE_AGENT_EXECUTION_AUTHORITY_SHA env var (explicit trusted config)
    2. Repository git HEAD SHA from REVERSE_AGENT_REPO_DIR
    3. Empty string if none available (causes fail-closed on durable /execute)

    REVERSE_AGENT_PLANNING_SHA is NOT a valid execution authority source.
    Authority and planning SHA are independent dimensions.
    """
    explicit = os.environ.get("REVERSE_AGENT_EXECUTION_AUTHORITY_SHA", "").strip()
    if explicit:
        return explicit
    repo_dir = os.environ.get("REVERSE_AGENT_REPO_DIR", "").strip()
    if repo_dir:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir, capture_output=True, text=True, check=True,
                timeout=10,
            )
            sha = result.stdout.strip()
            if sha:
                return sha
        except Exception:
            pass
    return ""


def _resolve_trusted_planning_sha() -> str:
    """Resolve trusted planning SHA from trusted runtime config.

    HTTP request bodies MUST NOT supply this value. Resolution order:
    1. REVERSE_AGENT_PLANNING_SHA env var (explicit trusted config)
    2. Repository git HEAD SHA from REVERSE_AGENT_REPO_DIR
    3. Empty string if none available (causes fail-closed on durable /execute)
    """
    explicit = os.environ.get("REVERSE_AGENT_PLANNING_SHA", "").strip()
    if explicit:
        return explicit
    repo_dir = os.environ.get("REVERSE_AGENT_REPO_DIR", "").strip()
    if repo_dir:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir, capture_output=True, text=True, check=True,
                timeout=10,
            )
            sha = result.stdout.strip()
            if sha:
                return sha
        except Exception:
            pass
    return ""


def _wait_for_owned_serving_threads(host: Any, *, poll_interval: float = 0.1) -> None:
    """Wait while at least one serving thread owned by ``host`` is alive.

    ``CombinedTrustedHost.start()`` owns every serving loop.  This helper only
    observes those owned threads; it never starts a second loop.  A provider-free
    test double with no owned threads returns immediately instead of waiting on
    a producer-less event.
    """
    if poll_interval <= 0:
        raise ValueError("poll_interval must be positive")
    while True:
        threads = tuple(getattr(host, "_threads", ()))
        live_threads = [thread for thread in threads if thread.is_alive()]
        if not live_threads:
            return
        for thread in live_threads:
            thread.join(timeout=poll_interval)


def run_combined_trusted_host() -> None:
    auth_sha = _resolve_trusted_authority_sha()
    planning_sha = _resolve_trusted_planning_sha()
    host = CombinedTrustedHost(
        execution_authority_sha=auth_sha,
        planning_sha=planning_sha,
        auth_list_probe=execute_opencode_auth_list_probe,
        account_auth_server_factory=start_opencode_account_auth_server,
    )
    try:
        host.start()
        metadata = {
            "model_control_url": host.model_control_url,
            "task_api_url": host.task_api_url,
            "relay_url": host.relay_url,
            "execution_authority_sha": auth_sha,
            "planning_sha": planning_sha,
        }
        runtime_dir = os.environ.get(
            "REVERSE_AGENT_TASK_DB_DIR",
            os.path.join(os.getcwd(), ".platform_v1_runtime"),
        )
        os.makedirs(runtime_dir, exist_ok=True)
        meta_path = os.path.join(runtime_dir, "trusted_host_meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)

        print("Combined Trusted Host started")
        print(f"  Model Control: {host.model_control_url}")
        print(f"  Task API:      {host.task_api_url}")
        print(f"  Relay:         {host.relay_url}")
        print(f"  Authority SHA: {auth_sha or '(empty - durable execute will fail closed)'}")
        print(f"  Planning SHA:  {planning_sha or '(empty - durable execute will fail closed)'}")

        _wait_for_owned_serving_threads(host)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        host.stop()


if __name__ == "__main__":
    run_combined_trusted_host()
