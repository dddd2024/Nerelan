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
from pathlib import Path
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
from .remote_jobs import configured_broker


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
        reset_signal_reader: Callable[[], Mapping[str, Any]] | None = None,
        availability_probe: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        vault: Any = _PLATFORM_VAULT,
        local_client_session: LocalClientSession | None = None,
    ) -> None:
        if auth_refresh_ttl_seconds < 0:
            raise ValueError("auth_refresh_ttl_seconds must be non-negative")
        self._reset_signal_reader = reset_signal_reader
        self._availability_probe = availability_probe
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
            task_resolver=self._resolve_task_model,
        )
        self._publication_controller: PublicationController | None = None
        self._coordinator: UnattendedCoordinator | None = None
        self._claude_reset_watcher: Any | None = None

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
        self._remote_job_broker = None

        from .native_goal_admission import NativeGoalAdmission
        self._native_goal_admission = NativeGoalAdmission(self)

        self.model_control_url = ""
        self.task_api_url = ""
        self.relay_url = ""

    def _native_owner_admit_goal(self, goal_id: str, *, unknown_claims_sha256=None):
        """Trusted native bootstrap only; never register on a transport/router.

        The host process must run as the interactive Owner at construction.
        This method displays native consent and atomically enqueues existing
        persisted work. It neither dispatches nor changes API authentication,
        account selection, or executor sandbox policy.
        """
        return self._native_goal_admission.admit(goal_id, unknown_claims_sha256=unknown_claims_sha256)

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
            if snapshot.native_endpoint != getattr(resolution, "native_endpoint", "/chat/completions"):
                raise RuntimeError("native_endpoint_drift_before_lease")
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

    def _resolve_task_model(self, task: Any, *, goal: Any = None, failed_binding: str = "",
                            author_binding: str = "", failed_tier: int | None = None,
                            refused_models: Sequence[str] = ()) -> dict[str, Any]:
        """Route across the entire runnable catalog, including discovered connections."""
        import random
        from .model_router import capability, select_model
        from .routing_inputs import read_overrides, binding_cost_class
        from .routing_capabilities import read_capability_table
        try:
            owner = read_overrides(getattr(self._store, "_state_path", None))
            capability_table = read_capability_table(getattr(self._store, "_state_path", None))
        except ValueError as exc:
            raise TaskStoreError(str(exc)) from exc
        signal = self._routing_refresh_quota_for_signal()
        self._routing_bind_discovered()
        bindings = self._store.list_bindings_public()
        by_id = {b["binding_id"]: b for b in bindings}
        connections = {c["connection_id"]: c for c in self._store.list_connections_public()}
        runnable = self._runnable_bindings()
        profiles = self._usage_profiles()
        role = task.agent_role or (
            "reviewer" if task.kind == "review" else "simple" if task.difficulty <= 2 else
            "coder" if task.difficulty == 3 else "complex")
        if (role == "reviewer" or task.kind == "review") and task.artifact_input and author_binding not in by_id:
            raise TaskStoreError("review_author_binding_required")
        candidates = []
        metadata = self._routing_model_metadata()
        allow_paid = self._routing_paid_allowed(goal, owner)
        for binding in bindings:
            connection = connections.get(binding["connection_id"], {})
            native = connection.get("auth_method") == "external_cli_session"
            cost_class = binding_cost_class(binding, connection, owner)
            quota = self._quota_check(binding)
            provider = connection.get("executor_provider_id", "")
            try:
                windows = self._subscription_quotas().get(provider, {}).get("windows", ()) if native else ()
            except Exception:  # noqa: BLE001 - unknown headroom is not evidence of exhaustion
                windows = ()
            weekly_window = next((w for w in windows if w.get("window") in {"weekly", "7d", "week"}), {})
            short_window = next((w for w in windows if w.get("window") in {"5h", "five_hour", "five_hours"}), {})
            need = (quota or {}).get("need_units")
            def fraction(window: Mapping[str, Any]) -> float | None:
                capacity = (window.get("capacity_units") or {}).get("low")
                return need / capacity if type(need) in (int, float) and type(capacity) in (int, float) and capacity > 0 else None
            try:
                raw_reset = short_window.get("resets_at")
                short_reset = float(raw_reset) if type(raw_reset) in (int, float) else datetime.fromisoformat(raw_reset.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError, AttributeError, OverflowError):
                short_reset = None
            remaining = [1 - w["used_percent"] / 100 for w in windows
                         if type(w.get("used_percent")) in (int, float) and not w.get("reset_passed")]
            candidate = {**binding, "runnable": binding["binding_id"] in runnable, "quota": quota,
                               "metadata": metadata.get(binding["model_id"], {}),
                               "weekly_headroom": next((1 - w["used_percent"] / 100 for w in windows
                                   if w.get("window") in {"weekly", "7d", "week"} and type(w.get("used_percent")) in (int, float)), None),
                               "quota_headroom": min(remaining, default=None),
                               "task_weekly_fraction": fraction(weekly_window), "task_short_fraction": fraction(short_window),
                               "short_headroom": 1 - short_window["used_percent"] / 100 if type(short_window.get("used_percent")) in (int, float) else None,
                               "short_resets_at": short_reset,
                               "cost_class": cost_class}
            # Evaluate the same pure hard filters before spending a probe. A
            # catalog entry excluded by scope, quota or calibration costs no call.
            try:
                select_model([{**candidate, "availability": {"state": "AVAILABLE"}}],
                    difficulty=task.difficulty, kind=task.kind, role=role, profiles=profiles,
                    capability_table=capability_table, allow_paid=allow_paid,
                    context_need=getattr(task, "context_need", 0) + self._routing_context_tokens(task, goal),
                    needs=getattr(task, "needs", ()), overrides=owner.get("bindings", {}),
                    refused_models=refused_models, author_model=by_id.get(author_binding, {}).get("model_id", ""),
                    reset_signal=signal, reset_buffer=owner.get("reset_buffer", .03))
                can_probe = True
            except ValueError:
                can_probe = False
            candidate["availability"] = self._routing_availability(binding, connection, allow_paid=allow_paid,
                cost_class=cost_class, probe_allowed=can_probe and self._routing_probe_window_allowed(goal))
            candidates.append(candidate)
        # Legacy labels only identify optional pins; unpinned tasks use the full pool.
        entry = self._store.get_agent_roster_public()["roles"].get(role, {})
        pin = getattr(goal, "binding_ref", "") or (entry.get("binding_id", "") if entry.get("pin") else "")
        failed = by_id.get(failed_binding, {})
        tier = failed_tier if failed_tier is not None else (
            capability(failed.get("model_id", ""), profiles.get(failed_binding, {}),
                       task.kind, task.difficulty)[0] if failed_binding else 0)
        try:
            decision = select_model(candidates, difficulty=task.difficulty, kind=task.kind, role=role,
                                profiles=profiles, pin=pin, capability_table=capability_table, allow_paid=allow_paid,
                                context_need=getattr(task, "context_need", 0) + self._routing_context_tokens(task, goal),
                                needs=getattr(task, "needs", ()), overrides=owner.get("bindings", {}),
                                reset_signal=signal, reset_buffer=owner.get("reset_buffer", .03),
                                refused_models=refused_models, refusal_tier=tier if refused_models else 0,
                                author_model=by_id.get(author_binding, {}).get("model_id", ""),
                                failed_model=failed.get("model_id", ""), failed_tier=tier,
                                exploration_draw=random.random())
            decision["context_packet_reservation"] = 16384 + 256
            return decision
        except ValueError as exc:
            error = TaskStoreError(str(exc))
            error.decision = getattr(exc, "decision", {"reason": str(exc)})
            raise error from exc

    def _routing_paid_allowed(self, goal: Any, owner: Mapping[str, Any] | None = None) -> bool:
        # Owner configuration names a specific active window; a generic setting
        # or a caller-supplied task flag cannot enable paid spend.
        if not goal or not getattr(goal, "window_id", ""):
            return False
        try:
            window = self._control_store.get_window(goal.window_id)
            if window.status != "ACTIVE":
                return False
            binding = self._control_store.window_policy_binding(goal.window_id)
            return (binding.get("authority", {}).get("allow_paid_api") is True
                    or goal.window_id in (owner or {}).get("paid_api_windows", []))
        except (AttributeError, KeyError, TaskStoreError):
            return False

    def _routing_bind_discovered(self) -> None:
        """Use sanitized, host-observed listings from every connection.

        Listing is not availability. This hook never discovers keys or performs
        inference. Existing bindings (including disabled ones) are preserved.
        """
        catalogs = getattr(self._store, "_routing_catalogs", {}) | getattr(self, "_routing_connection_catalogs", {})
        for connection in self._store.list_connections_public():
            snapshot = catalogs.get(connection["connection_id"], {})
            if not connection.get("enabled") or snapshot.get("status") != "discovered":
                continue
            models = snapshot.get("models", [])
            if models:
                self._store.bind_connection_models(connection["connection_id"], models, "auto")

    def _routing_probe_window_allowed(self, goal: Any) -> bool:
        if getattr(self, "_availability_probe", None) is not None:
            return True  # Explicit trusted callback, also the provider-free fake seam.
        if not goal or not getattr(goal, "window_id", ""):
            return False
        try:
            window = self._control_store.get_window(goal.window_id)
            authority = self._control_store.window_policy_binding(goal.window_id).get("authority", {})
            return (window.status == "ACTIVE"
                    and authority.get("model_call_limit") != 0 and authority.get("provider_call_limit") != 0
                    and datetime.fromisoformat(window.expires_at.replace("Z", "+00:00")).timestamp() > time.time())
        except (AttributeError, KeyError, TypeError, ValueError, TaskStoreError):
            return False

    def _routing_availability(self, binding: Mapping[str, Any], connection: Mapping[str, Any], *,
                              allow_paid: bool, cost_class: str, probe_allowed: bool = True) -> dict[str, Any]:
        from .model_availability import AvailabilityCache, observation, availability_error
        cache = getattr(self, "_availability_cache", None)
        if cache is None:
            path = getattr(self._store, "_state_path", None)
            cache = self._availability_cache = AvailabilityCache(
                Path(path).with_name("model_availability.json") if path else None)
        recent = None
        store = getattr(self, "_task_store", None)
        if store is not None:
            rows = store._conn.execute(
                "SELECT status, failure_classification, failure_detail, updated_at FROM tasks "
                "WHERE binding_ref=? ORDER BY updated_at DESC LIMIT 20", (binding["binding_id"],)).fetchall()
            for row in reversed(rows):
                try:
                    at = datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")).timestamp()
                except (ValueError, TypeError):
                    continue
                entry = cache.entries.get(cache.key(binding, connection), {})
                if at <= entry.get("observed_at", 0):
                    continue
                classification = row["failure_classification"] or ""
                if row["status"] in {"COMPLETED", "READY_FOR_REVIEW"} or classification in {"MODEL_REFUSED", "deterministic_validation_failure"}:
                    cache.remember(binding, connection, observation(now=at, success=True))
                elif classification == "MODEL_UNAVAILABLE":
                    cache.remember(binding, connection, observation(now=at, error=row["failure_detail"]))
                elif row["status"] == "FAILED" and any(marker in classification.lower() for marker in
                        ("timeout", "network_provider", "api_error_429", "api_error_5", "rate_limit")):
                    cache.remember(binding, connection, observation(now=at, error="transient"))
        probe = getattr(self, "_availability_probe", None)
        live = (os.environ.get("REVERSE_AGENT_MODEL_CONTROL_LIVE") == "1"
                and os.environ.get("REVERSE_AGENT_ROUTING_PROBES") == "1")
        return cache.check(binding, connection, recent_success=recent,
                           probe=probe or self._probe_routing_binding,
                           allow_probe=probe_allowed and (probe is not None or live) and (cost_class != "paid_api" or allow_paid))

    def _probe_routing_binding(self, binding: Mapping[str, Any]) -> Mapping[str, Any]:
        """One tiny request through the host relay's confined transport."""
        from ..model_access.credential_relay import forward_keyless_probe
        from ..model_access.http_safe import urlopen
        from urllib.request import Request
        from urllib.error import HTTPError
        from .model_availability import availability_error
        snapshot = self._store.resolve_execution_snapshot(binding["binding_id"])
        anthropic = snapshot.protocol_family == "anthropic" and binding["executor_id"] == "claude_code"
        endpoint = "/v1/messages" if anthropic else snapshot.native_endpoint
        body = {"model": snapshot.raw_model_id, "messages": [{"role": "user", "content": "Reply OK"}], "max_tokens": 4}
        if endpoint == "/responses":
            body = {"model": snapshot.raw_model_id, "input": "Reply OK", "max_output_tokens": 4}
        if snapshot.auth_method == "none":
            status, response, _ = forward_keyless_probe(snapshot, body=json.dumps(body).encode(), timeout=10)
            if not 200 <= status < 300:
                return {"ok": False, "error": availability_error(response.decode("utf-8", errors="replace")) or "transient"}
            payload = json.loads(response)
            return {"ok": isinstance(payload, dict) and bool(payload.get("choices") or payload.get("content") or payload.get("output"))}
        lease = self._relay_manager.create_lease(snapshot, relay_url=self.relay_url)
        try:
            request = Request(lease.relay_url.rstrip("/") + endpoint, data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + lease.lease_id, "Content-Type": "application/json"})
            try:
                with urlopen(request, timeout=10) as response:
                    payload = json.loads(response.read(65536))
                    return {"ok": isinstance(payload, dict) and bool(payload.get("choices") or payload.get("content") or payload.get("output"))}
            except HTTPError as exc:
                reason = availability_error(exc.read(65536).decode("utf-8", errors="replace"))
                return {"ok": False, "error": reason or "transient"}
        finally:
            self._relay_manager.release_lease(lease.lease_id)

    def _routing_refresh_quota_for_signal(self) -> Mapping[str, Any]:
        """Refresh at selection and again at the real dispatch boundary."""
        from .routing_inputs import reset_decision
        signal = self._routing_reset_signal()
        if reset_decision(signal, now=time.time())["refresh_quota"]:
            previous_quota = self.__dict__.pop("_subscription_quota_cache", None)
            try:
                self._subscription_quotas()
            except Exception:
                if previous_quota is not None:
                    self._subscription_quota_cache = previous_quota
                return {"state": "UNKNOWN", "refresh_failed": True}
        return signal

    def _routing_reset_signal(self) -> Mapping[str, Any]:
        """Injected validated observation; missing reader/fetch failure is UNKNOWN."""
        reader = getattr(self, "_reset_signal_reader", None)
        try:
            value = reader() if reader else None
            return value if isinstance(value, Mapping) else {"state": "UNKNOWN"}
        except Exception:  # noqa: BLE001 - forecasts are optional, never capacity
            return {"state": "UNKNOWN"}

    def _routing_model_metadata(self) -> dict[str, Any]:
        """Consume an already-observed Magpie snapshot, never fetch during routing."""
        snapshot = getattr(self, "_routing_magpie_snapshot", {})
        result = {m["model_id"]: m for m in snapshot.get("models", ()) if isinstance(m, Mapping) and m.get("model_id")}
        for catalog in getattr(self._store, "_routing_catalogs", {}).values():
            result.update(catalog.get("metadata", {}))
        return result

    def _routing_context_tokens(self, task: Any, goal: Any) -> int:
        """Reserve packet byte budget before materialization (one byte/token).

        Actual packets are measured at dispatch; this conservative upper bound
        prevents selecting a window that cannot hold the later packet.
        """
        prompt = " ".join(str(getattr(value, field, "") or "") for value, field in
                          ((task, "instruction"), (task, "title"), (goal, "title")))
        return 16384 + 256 + 512 + len(prompt.encode("utf-8"))

    def _resolve_agent_role(self, role: str) -> tuple[str, str]:
        """Legacy role resolution; planning also uses the task-aware candidate pool."""
        if role == "planner":
            from .goal_service import PlannedTask
            decision = self._resolve_task_model(PlannedTask("planner", "Plan", "Plan", agent_role="planner",
                                                           difficulty=4, kind="research_design"))
            return decision["executor_kind"], decision["binding_ref"]
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
        from .quota_guard import ACCOUNT_LIMIT, limit_hit_until
        bindings = [b["binding_id"] for b in self._store.list_bindings_public()
                    if b["connection_id"] == connection.get("connection_id")]
        if not bindings:
            return None
        since = datetime.fromtimestamp(time.time() - 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = self._task_store._conn.execute(
            "SELECT failure_classification, updated_at FROM tasks WHERE status IN ('FAILED', 'BLOCKED') "
            "AND updated_at >= ? AND binding_ref IN ({}) ORDER BY updated_at DESC".format(",".join("?" * len(bindings))),
            (since, *bindings)).fetchall()
        # Our own refusals are not new answers from the account and must never extend the hold.
        hit = next((row["updated_at"] for row in rows if ACCOUNT_LIMIT.search(row["failure_classification"] or "")), None)
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
        from .quota_guard import CONFIRMED_EXHAUSTION_REASONS, alternatives
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
            if decision["reason"] in CONFIRMED_EXHAUSTION_REASONS:
                entry["decision"], entry["reason"] = "refuse", f"{decision['reason']}:no_alternative"
                self._record_quota_decision(entry)
                # Do not advertise an exhausted role as an executable route.
                raise TaskStoreError(f"quota_exhausted:{decision['reason']}:no_alternative")
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

    def _claude_reset_quota_recheck(self) -> None:
        # Read-only official CLI telemetry; never change entitlement/limits.
        # Invalidate any minute-old presentation cache after public notice.
        self._subscription_quota_cache = None
        self._subscription_quotas()

    def _claude_reset_status(self) -> dict[str, Any]:
        watcher = self._claude_reset_watcher
        if watcher is None:
            return {"provider": "claude-code", "enabled": False, "status": "UNKNOWN", "reason": "monitor_disabled"}
        return {"enabled": True, **watcher.snapshot()}

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
                host._routing_refresh_quota_for_signal()
                snapshot = host._store.resolve_execution_snapshot(binding_ref)
                binding = next((b for b in host._store.list_bindings_public() if b["binding_id"] == binding_ref), None)
                verdict = host._quota_check(binding) if binding else None
                from .quota_guard import CONFIRMED_EXHAUSTION_REASONS
                if verdict and verdict.get("decision") == "switch" and verdict.get("reason") in CONFIRMED_EXHAUSTION_REASONS:
                    # Explicit/single-Goal binding routes have the same hard
                    # quota boundary as an agent-team role: no model call.
                    host._record_quota_decision({"role": None, "binding_id": binding_ref, "decision": "refuse",
                                                 "reason": verdict["reason"], "window": verdict.get("window"),
                                                 "switched_to": None})
                    raise BindingResolutionError(f"quota_exhausted:{verdict['reason']}")
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
        coordinator_paused: bool = False,
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
            if not coordinator_paused:
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
                claude_reset_status=self._claude_reset_status,
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
            if not coordinator_paused and os.environ.get("REVERSE_AGENT_AUTONOMOUS") == "1" and self._coordinator:
                self._coordinator.start()
            self._remote_job_broker = configured_broker()
            if self._remote_job_broker is not None:
                self._remote_job_broker.start()
            # Optional, independent public-announcement observer. This never
            # changes a quota guard decision or starts any model execution.
            if os.environ.get("REVERSE_AGENT_CLAUDE_RESET_WATCH") == "1":
                db_path = self._task_store.db_path
                if db_path and db_path != ":memory:":
                    from ..model_access.claude_reset_signals import ClaudeResetWatcher
                    self._claude_reset_watcher = ClaudeResetWatcher(
                        os.path.dirname(os.path.abspath(db_path)) or ".",
                        on_quota_refresh=self._claude_reset_quota_recheck,
                    )
                    self._claude_reset_watcher.start()
        except BaseException:
            self._cleanup_runtime_resources(close_account_auth=True)
            raise

    def _cleanup_runtime_resources(self, *, close_account_auth: bool) -> None:
        if self._remote_job_broker is not None:
            self._remote_job_broker.stop()
            self._remote_job_broker = None
        watcher = self._claude_reset_watcher
        self._claude_reset_watcher = None
        if watcher is not None:
            try:
                watcher.stop()
            except Exception:
                pass
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


def run_combined_trusted_host(*, native_goal_id: str | None = None,
                              unknown_claims_sha256: str | None = None) -> None:
    """Run the official lifecycle; native_goal_entry validates explicit CLI requests.

    Admission follows successful port ownership and failures use normal cleanup.
    No consent material is printed or added to host metadata.
    """
    import re
    if ((native_goal_id is not None and
         re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,255}", native_goal_id) is None)
            or (unknown_claims_sha256 is not None and
                (native_goal_id is None or re.fullmatch(r"[0-9a-f]{64}", unknown_claims_sha256) is None))):
        raise ValueError("invalid_native_admission_arguments")
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
        if native_goal_id is None:
            host.start()
        else:
            host.start(coordinator_paused=True)
            host._native_owner_admit_goal(native_goal_id, **(
                {"unknown_claims_sha256": unknown_claims_sha256}
                if unknown_claims_sha256 is not None else {}))
            if os.environ.get("REVERSE_AGENT_AUTONOMOUS") == "1" and host._coordinator:
                host._coordinator.start()
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
