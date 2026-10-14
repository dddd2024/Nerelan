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

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
import collections
import json
import os
import subprocess
import threading
import time
from typing import Any, Mapping

from ..model_access.contracts import NATIVE_CLI_PROVIDERS, ExecutionSnapshot
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
from .run_store import TaskStore, TaskStoreError
from .task_runtime import ExecutorRouter
from .task_service import _handler_factory as _task_handler_factory
from .task_service import validate_bind_host
from .task_service import _configured_autonomy
from .task_service import _default_task_db_path, _ensure_db_path, adopt_legacy_task_store
from .durable_execution import DurableExecutionService
from .autonomy import AutonomyService
from .capability_registry import CapabilityRegistry
from .control_store import PlatformControlStore
from .goal_service import GoalService
from .publication_controller import PublicationController
from .unattended_coordinator import UnattendedCoordinator
from .local_client_session import LocalClientSession


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
        codex_readiness_probe: Callable[[], str] | None = None,
        claude_code_readiness_probe: Callable[[], str] | None = None,
        vault: Any = _PLATFORM_VAULT,
        local_client_session: LocalClientSession | None = None,
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
        if codex_readiness_probe is not None:
            self._store.set_codex_readiness(codex_readiness_probe())
        if claude_code_readiness_probe is not None:
            self._store.set_native_readiness("claude_code", claude_code_readiness_probe())
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
        self._autonomy_service = _configured_autonomy(
            self._task_store, self._control_store, self._capability_registry
        )
        self._goal_service = GoalService(
            store=self._task_store,
            control_store=self._control_store,
            roster_resolver=self._resolve_agent_role,
        )
        self._publication_controller: PublicationController | None = None
        self._coordinator: UnattendedCoordinator | None = None

        self._model_control_host = validate_bind_host(model_control_host)
        self._model_control_port = model_control_port
        self._task_api_host = validate_bind_host(task_api_host)
        self._task_api_port = task_api_port
        self._allowed_origin = allowed_origin

        self._model_server: ThreadingHTTPServer | None = None
        self._task_server: ThreadingHTTPServer | None = None
        self._relay_server: CredentialRelayServer | None = None
        self._relay_server_inner: ThreadingHTTPServer | None = None
        self._threads: list[threading.Thread] = []
        self._started_servers: list[ThreadingHTTPServer] = []
        # Private lifecycle identity foundation. HTTP admission is unchanged
        # until the separately governed guard and native bootstrap are wired.
        self._local_client_session = local_client_session or LocalClientSession()
        self._trusted_client = None

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
        return connection["executor_provider_id"] not in NATIVE_CLI_PROVIDERS and connection["auth_method"] in {
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
            anthropic = snapshot.protocol_family == "anthropic" and snapshot.executor_id == "claude_code"
            expected_model = (snapshot.raw_model_id if anthropic
                              else _normalize_model_id(snapshot.provider, snapshot.raw_model_id))
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
                _deadline_callback=lambda seconds: manager.bind_execution_deadline(
                    lease_id, seconds
                ),
            )

        return _provider

    def _agent_planner(self) -> Any:
        from .agent_planner import AgentPlanner
        from .repository_workspace import resolve_repository_workspace
        return AgentPlanner(
            goal_service=self._goal_service,
            roster_resolver=self._resolve_agent_role,
            binding_model=lambda binding_ref: self._store.get_binding_public(binding_ref)["model_id"],
            repo_dir_for=lambda repository: str(resolve_repository_workspace(repository).repo_dir),
        )

    def _context_recovery(self) -> Any:
        from pathlib import Path
        from .context_recovery import ContextRecoveryService
        from .context_builder import _git_head
        from .repository_workspace import resolve_repository_workspace

        def workspace(task_id: str) -> tuple[str, str]:
            task = self._task_store.get_task(task_id, event_limit=0)
            observation = self._task_store.get_latest_durable_run_observation(task_id)
            if observation is not None:
                run = self._task_store._get_durable_run(observation.run_id)
                if run.execution_id != task.execution_id:
                    raise TaskStoreError('context_execution_stale')
                path = run.worktree_path
                if not path:
                    raise TaskStoreError('context_workspace_unavailable')
            else:
                path = str(resolve_repository_workspace(task.repository).repo_dir)
            return str(path), _git_head(Path(path))

        def binding() -> tuple[str, str]:
            executor, ref = self._resolve_agent_role('planner')
            public = self._store.get_binding_public(ref)
            connection = self._store.get_connection_public(public['connection_id'])
            if (not public['enabled'] or public['executor_id'] != executor
                    or connection['auth_method'] != 'external_cli_session'):
                raise TaskStoreError('context_summary_requires_native_account_binding')
            return executor, public['model_id']

        return ContextRecoveryService(store=self._task_store, workspace_for=workspace,
                                      summary_binding=binding)

    def _agent_policy(self) -> Any:
        from .policy_configurator import PolicyConfigurator, binding_health

        def bindings() -> list[dict[str, Any]]:
            connections = {item["connection_id"]: item for item in self._store.list_connections_public()}
            result = []
            for item in self._store.list_bindings_public():
                connection = connections.get(item["connection_id"], {})
                native = connection.get("auth_method") == "external_cli_session" and item["executor_id"] != "opencode"
                result.append({**item, "connection_name": connection.get("name", ""),
                               "cost_class": "subscription account" if native else f'api ({connection.get("name", "")})'})
            return result

        def interpreter() -> tuple[str, str, str]:
            # Prefer the configured planner; otherwise the first enabled, ready native account binding.
            try:
                executor_kind, binding_id = self._resolve_agent_role("planner")
                if executor_kind in {"claude_code", "codex"}:
                    return executor_kind, binding_id, self._store.get_binding_public(binding_id)["model_id"]
            except TaskStoreError:
                pass
            ready = {item["executor_id"] for item in self._store.list_executors_public() if item.get("operational")}
            for item in sorted(self._store.list_bindings_public(), key=lambda b: b["executor_id"] != "claude_code"):
                if item["enabled"] and item["executor_id"] in {"claude_code", "codex"} and item["executor_id"] in ready:
                    return item["executor_id"], item["binding_id"], item["model_id"]
            raise TaskStoreError("agent_policy_requires_native_interpreter")

        return PolicyConfigurator(bindings=bindings, health=lambda: binding_health(self._task_store),
                                  interpreter=interpreter, apply_roster=self._store.put_agent_roster)

    def _resolve_agent_role(self, role: str) -> tuple[str, str]:
        """Role -> (executor_kind, binding_ref) from the in-process agent roster."""
        roster = self._store.get_agent_roster_public()
        entry = roster["roles"].get(role)
        if not entry or not entry["available"]:
            raise TaskStoreError(f"agent_role_unfilled:{role}")
        executor_id, binding_id = self._prefer_measured_pairing(role, entry["executor_id"], entry["binding_id"])
        return self._quota_guarded(role, executor_id, binding_id, roster["roles"],
                                   standins=roster.get("standins", {}).get(role, ()))

    def _quota_check(self, binding: Mapping[str, Any]) -> dict[str, Any] | None:
        from .quota_guard import check, typical_need
        from .usage_ledger import task_token_records
        try:
            connection = self._store.get_connection_public(binding["connection_id"])
            until = self._limit_hit_until(connection)
            if until is not None:
                # The account itself refused a recent run: exhausted until it resets, whatever the estimate says.
                return {"decision": "switch", "reason": "limit_hit", "window": None,
                        "until": datetime.fromtimestamp(until, timezone.utc).isoformat().replace("+00:00", "Z")}
            records = _cached(self, "_task_records_cache", lambda: task_token_records(self._task_store))
            need, source = typical_need(records, binding, self._store.list_bindings_public())
            verdict = check(connection, self._subscription_quotas(), need)
            return verdict | {"need_source": source} if verdict else None
        except Exception:  # noqa: BLE001 - a quota estimate must never block dispatch by itself
            return {"decision": "error", "reason": "quota_check_failed"}

    def _limit_hit_until(self, connection: Mapping[str, Any]) -> float | None:
        """When a run on this connection last failed for quota, and the account has not reset since."""
        from .quota_guard import LIMIT_HIT, limit_hit_until
        bindings = [b["binding_id"] for b in self._store.list_bindings_public()
                    if b["connection_id"] == connection.get("connection_id")]
        if not bindings:
            return None
        since = datetime.fromtimestamp(time.time() - 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = self._task_store._conn.execute(
            "SELECT failure_classification, updated_at FROM tasks WHERE status IN ('FAILED', 'BLOCKED') "
            "AND updated_at >= ? AND binding_ref IN ({}) ORDER BY updated_at DESC".format(",".join("?" * len(bindings))),
            (since, *bindings)).fetchall()
        hit = next((row["updated_at"] for row in rows if LIMIT_HIT.search(row["failure_classification"] or "")), None)
        if hit is None:
            return None
        hit_at = datetime.fromisoformat(hit.replace("Z", "+00:00")).timestamp()
        quota = self._subscription_quotas().get(connection.get("executor_provider_id") or "")
        until = limit_hit_until(hit_at, quota)
        return until if until > time.time() else None

    def _runnable_bindings(self) -> set[str]:
        """Bindings that could dispatch now: enabled, credential usable, executor ready (resolver rules)."""
        from ..model_access.resources import build_resource_view
        view = build_resource_view(self._store, dict)
        return {row["binding_id"] for item in view["resources"] if item["credential"]["configured"]
                for row in item["bindings"] if row["usable"]}

    def _record_quota_decision(self, entry: dict[str, Any]) -> None:
        log = getattr(self, "_quota_guard_log", None)
        if log is None:
            log = self._quota_guard_log = collections.deque(maxlen=20)
        key = (entry.get("binding_id"), entry.get("decision"), entry.get("reason"))
        last = log[0] if log else None
        if last and (last.get("binding_id"), last.get("decision"), last.get("reason")) == key \
                and time.monotonic() - last.get("_logged", 0) < 120:
            return  # the same verdict from role resolution and from the run itself
        log.appendleft({"at": _utc_now(), "_logged": time.monotonic(), **entry})

    def _quota_guarded(self, role: str, executor_id: str, binding_id: str,
                       roster: Mapping[str, Mapping[str, Any]], standins: Sequence[str] = ()) -> tuple[str, str]:
        """Move a role off an account whose quota cannot take the next task, before dispatch."""
        from .quota_guard import alternatives
        bindings = self._store.list_bindings_public()
        chosen = next((b for b in bindings if b["binding_id"] == binding_id), None)
        decision = self._quota_check(chosen) if chosen else None
        if not decision or decision["decision"] in {"ok", "error"}:
            return executor_id, binding_id  # no shortfall known: never move on a failed estimate
        entry = {"role": role, "binding_id": binding_id, "decision": decision["decision"],
                 "reason": decision["reason"], "window": decision.get("window"), "switched_to": None}
        if decision["decision"] == "switch":
            usable = {item["executor_id"] for item in self._store.list_executors_public() if item.get("operational")}
            usable &= self.ROLE_EXECUTORS.get(role, usable)
            runnable = self._runnable_bindings()
            for candidate in alternatives(role, chosen, bindings=bindings, roster=roster, usable_executors=usable,
                                          standins=standins):
                if candidate["binding_id"] not in runnable:
                    continue  # a stand-in that cannot run is worse than a warned run
                verdict = self._quota_check(candidate)
                # API keys have no window (None); a failed check is not "fits".
                if verdict is None or verdict["decision"] in {"ok", "warn"}:
                    self._record_quota_decision(entry | {"switched_to": candidate["binding_id"]})
                    return candidate["executor_id"], candidate["binding_id"]
            entry["decision"], entry["reason"] = "warn", f"{decision['reason']}:no_alternative"
        self._record_quota_decision(entry)
        return executor_id, binding_id

    def _quota_guard_entries(self) -> list[dict[str, Any]]:
        return [{k: v for k, v in entry.items() if not k.startswith("_")}
                for entry in getattr(self, "_quota_guard_log", ())]

    # Roles whose work only some executors can do; a measured swap never leaves this set.
    ROLE_EXECUTORS = {"planner": frozenset({"claude_code", "codex"})}

    def _usage_profiles(self) -> dict[str, dict[str, Any]]:
        """What each Binding was observed doing, for the unified resource view."""
        from .model_profiles import cached_agent_profiles
        return cached_agent_profiles(self._task_store)

    def _token_usage(self) -> dict[str, Any]:
        """Per-binding token counters normalized across OpenCode, Codex and Claude Code."""
        from .usage_ledger import binding_token_totals, task_token_records
        return _cached(self, "_token_usage_cache", lambda: binding_token_totals(task_token_records(self._task_store)))

    def _subscription_quotas(self) -> dict[str, Any]:
        """Account windows as the official CLIs last reported them, keyed by native provider."""
        if os.environ.get("REVERSE_AGENT_SUBSCRIPTION_QUOTA") == "0":
            return {}
        from ..model_access.subscription_quota import claude_quota, codex_quota
        from .usage_ledger import latest_rate_limits

        def read() -> dict[str, Any]:
            bindings = self._store.list_bindings_public()
            connections = {item["connection_id"]: item for item in self._store.list_connections_public()}
            # Only runs on the Claude account itself; a relay run's notices are not about the subscription.
            account = [b["binding_id"] for b in bindings if b["executor_id"] == "claude_code"
                       and connections.get(b["connection_id"], {}).get("auth_method") == "external_cli_session"]
            # Official numbers first; the local CLI logs fill in what they do not say.
            return {"codex": codex_quota(),
                    "claude-code": claude_quota(latest_rate_limits(self._task_store, account))}
        return _cached(self, "_subscription_quota_cache", read)

    def _prefer_measured_pairing(self, role: str, executor_id: str, binding_id: str) -> tuple[str, str]:
        """Same model, another executor: let real outcomes pick the pairing that works better."""
        from .model_profiles import best_pairing, cached_agent_profiles
        bindings = {item["binding_id"]: item for item in self._store.list_bindings_public()}
        chosen = bindings.get(binding_id)
        if chosen is None:
            return executor_id, binding_id
        ready = {item["executor_id"] for item in self._store.list_executors_public() if item.get("operational")}
        ready &= self.ROLE_EXECUTORS.get(role, ready)
        siblings = [item["binding_id"] for item in bindings.values()
                    if item["binding_id"] != binding_id and item.get("enabled")
                    and item["connection_id"] == chosen["connection_id"] and item["model_id"] == chosen["model_id"]
                    and item["executor_id"] in ready]
        if not siblings:
            return executor_id, binding_id
        picked = best_pairing(cached_agent_profiles(self._task_store), binding_id, siblings)
        return bindings[picked]["executor_id"], picked

    def _binding_resolver_factory(self, base_url: str) -> Any:
        from .binding_resolver import BindingResolutionError, BindingResolver

        host = self
        delegate = BindingResolver(base_url=base_url)

        class FreshExternalSessionBindingResolver:
            def resolve(self, binding_ref: str, *, task_executor: str) -> Any:
                snapshot = host._store.resolve_execution_snapshot(binding_ref)
                binding = next((b for b in host._store.list_bindings_public() if b["binding_id"] == binding_ref), None)
                verdict = host._quota_check(binding) if binding else None
                if verdict and verdict.get("reason") == "limit_hit":
                    # Refuse before launch: the account already answered with its limit. The plan task
                    # is then rerouted to a stand-in, or blocked, instead of failing again at the API.
                    host._record_quota_decision({"role": None, "binding_id": binding_ref, "decision": "refuse",
                                                 "reason": "limit_hit", "window": None, "switched_to": None})
                    raise BindingResolutionError("quota_exhausted:limit_hit")
                if verdict and verdict["decision"] in {"warn", "switch"}:
                    # A binding the task named itself is kept; the shortfall is recorded before the run.
                    host._record_quota_decision({"role": None, "binding_id": binding_ref, "decision": "warn",
                                                 "reason": verdict["reason"], "window": verdict.get("window"),
                                                 "switched_to": None})
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
        if self._started_servers:
            raise RuntimeError("trusted_host_already_started")
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
                usage_profiles=self._usage_profiles,
                token_usage=self._token_usage,
                subscription_quotas=self._subscription_quotas,
                quota_guard_log=self._quota_guard_entries,
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
                goal_escalator=self._goal_service.escalate_failed_tasks,
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
                agent_planner=self._agent_planner(),
                context_recovery=self._context_recovery(),
                agent_policy=self._agent_policy(),
                autonomy_service=self._autonomy_service,
                capability_registry=self._capability_registry,
                publication_controller=self._publication_controller,
                coordinator=self._coordinator,
                local_client_session=self._local_client_session,
            )
            self._task_server = ThreadingHTTPServer(
                (self._task_api_host, tap), task_handler
            )
            self._task_server.daemon_threads = True
            actual_task_port = self._task_server.server_address[1]
            self.task_api_url = f"http://{self._task_api_host}:{actual_task_port}"

            self._local_client_session.rotate()

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
        self._local_client_session.revoke()
        if self._trusted_client is not None:
            try:
                self._trusted_client.stop()
            except Exception:
                pass
            finally:
                self._trusted_client = None
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


_CACHE_SECONDS = 60.0


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _cached(owner: Any, attribute: str, compute: Any) -> Any:
    """Recompute an expensive read at most once a minute per host."""
    now = time.monotonic()
    cached = getattr(owner, attribute, None)
    if cached is None or now - cached[0] > _CACHE_SECONDS:
        cached = (now, compute())
        setattr(owner, attribute, cached)
    return cached[1]


def _make_task_store(db_path: str | None) -> TaskStore:
    resolved = db_path or _default_task_db_path()
    explicit = bool(db_path) or any(
        os.environ.get(name) for name in ("REVERSE_AGENT_TASK_DB_PATH", "REVERSE_AGENT_TASK_DB_DIR")
    )
    if not explicit:
        # Only the launcher may name the pre-#1117 checkout store; adoption is
        # a one-time copy into the absent host-owned store and fails closed.
        adopt_legacy_task_store(resolved, os.environ.get("REVERSE_AGENT_LEGACY_TASK_DB_PATH", ""))
    return TaskStore(db_path=_ensure_db_path(resolved))


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
                cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
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
                cwd=repo_dir, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
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
    from .codex_executor import probe_codex_readiness
    from .claude_executor import probe_claude_code_readiness
    auth_sha = _resolve_trusted_authority_sha()
    planning_sha = _resolve_trusted_planning_sha()
    host = CombinedTrustedHost(
        execution_authority_sha=auth_sha,
        planning_sha=planning_sha,
        model_control_host=os.environ.get("REVERSE_AGENT_MODEL_CONTROL_HOST", "127.0.0.1"),
        model_control_port=int(os.environ.get("REVERSE_AGENT_MODEL_CONTROL_PORT", "8765")),
        task_api_host=os.environ.get("REVERSE_AGENT_TASK_SERVICE_HOST", "127.0.0.1"),
        task_api_port=int(os.environ.get("REVERSE_AGENT_TASK_SERVICE_PORT", "8766")),
        allowed_origin=os.environ.get("REVERSE_AGENT_TASK_SERVICE_ORIGIN", "http://127.0.0.1:4173"),
        auth_list_probe=execute_opencode_auth_list_probe,
        account_auth_server_factory=start_opencode_account_auth_server,
        codex_readiness_probe=probe_codex_readiness if os.environ.get("REVERSE_AGENT_CODEX_ENABLED") == "1" else None,
        claude_code_readiness_probe=(probe_claude_code_readiness
                                     if os.environ.get("REVERSE_AGENT_CLAUDE_CODE_ENABLED") == "1" else None),
    )
    try:
        host.start()
        if os.environ.get("REVERSE_AGENT_TRUSTED_CLIENT_UI") == "1":
            from .trusted_client import TrustedClient
            host._trusted_client = TrustedClient(
                node_executable=os.environ.get("REVERSE_AGENT_TRUSTED_CLIENT_NODE", ""),
                frontend_url=os.environ.get("REVERSE_AGENT_TASK_SERVICE_ORIGIN", "http://127.0.0.1:4173"),
                task_api_url=host.task_api_url,
            )
            host._local_client_session.deliver(host._trusted_client.start)
        metadata = {
            "model_control_url": host.model_control_url,
            "task_api_url": host.task_api_url,
            "relay_url": host.relay_url,
            "execution_authority_sha": auth_sha,
            "planning_sha": planning_sha,
            "client_ui_enabled": os.environ.get("REVERSE_AGENT_TRUSTED_CLIENT_UI") == "1",
            "client_process_pid": host._trusted_client.pid if getattr(host, "_trusted_client", None) else None,
            "client_ui_ready": False,
            "client_process_start_filetime": None,
            "client_process_executable": None,
        }
        runtime_dir = os.environ.get(
            "REVERSE_AGENT_TASK_DB_DIR",
            os.path.join(os.getcwd(), ".platform_v1_runtime"),
        )
        os.makedirs(runtime_dir, exist_ok=True)
        meta_path = os.path.join(runtime_dir, "trusted_host_meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2)
        client = getattr(host, "_trusted_client", None)
        if client is not None:
            metadata_lock = threading.Lock()
            def publish_client_status() -> None:
                with metadata_lock:
                    metadata["client_ui_ready"] = client.ready
                    metadata["client_process_pid"] = client.pid
                    metadata["client_process_start_filetime"] = client.start_filetime
                    metadata["client_process_executable"] = client.executable
                    try:
                        temporary = meta_path + ".client-status.tmp"
                        with open(temporary, "w", encoding="utf-8") as fh:
                            json.dump(metadata, fh, indent=2)
                        os.replace(temporary, meta_path)
                    except OSError:
                        pass
            client.observe_status(publish_client_status)

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
