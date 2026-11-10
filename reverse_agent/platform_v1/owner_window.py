"""Owner-confirmed autonomous window over exact Goals (Owner decision 2026-11-07).

    python -m reverse_agent.platform_v1.owner_window --goal G1 --goal G2 --hours 24 \
        --max-tasks 10 --max-concurrent 1 --max-retries 2 --capability execute_task

Starts the host, prints the exact scope, and activates only after the Owner types
the one-time code it shows in this terminal. Then it keeps running as the host.

Why it exists: the native single-Task path admits one Codex Task for 30 minutes. This admits several Goals for
hours under the same discipline: persisted truth is read before the prompt and again
inside the activation transaction, the window, approvals, launches and one receipt
per Goal commit together or not at all, and the store enforces hard ceilings.

The receipt records the binding pool the Owner was shown. Only these Goals can run
in the window (launch, rebind and claim refuse others) and a Task may only run on a
binding from that pool (checked before every executor launch).

What the typed code proves: someone at this terminal read the scope and typed it.
It does not authenticate the OS user as the repository Owner, and any process that
can drive this terminal could type it.

Other surfaces run the same admission: the confirmation card's Start (Owner decision
2026-11-09) and, when the Owner turns it on, a supervisor request served by the
running host with preset bounds only (Owner decision 2026-11-10, see
:mod:`supervisor_requests`).
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import getpass
from pathlib import Path
import json
import re
import secrets
import sys
import threading
import time
from typing import Any
from urllib.parse import unquote, urlsplit

from .binding_resolver import BindingResolver
from .control_store import (
    OWNER_WINDOW_CAPABILITIES,
    OWNER_WINDOW_MAX_GOALS,
    OWNER_WINDOW_MAX_MINUTES,
    OWNER_WINDOW_MODE,
    OWNER_WINDOW_RECEIPT,
    canonical_json,
    sha256_json,
)
from .functional_validation import repository_base
from .repository_workspace import resolve_repository_workspace
from .run_store import TaskStoreError

CONFIRM_SECONDS = 300
MAX_SCOPE_CHARS = 40_000
_GOAL_ID = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]{0,255}")
_EXECUTORS = {"opencode", "codex", "claude_code"}
_MODES = {"single", "sequential_team", "agent_team"}
_MECHANISMS = {
    "terminal": "owner typed a one-time code at the host terminal",
    "ui": "owner pressed Start on the Nerelan confirmation card",
    "supervisor": "supervisor request file under the Owner's standing delegation; preset bounds only",
}


def _utc(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _store_transport(store: Any) -> Callable[[str, float, int], tuple[int, Any]]:
    """A ``BindingResolver`` transport answering from the persisted public views.

    Mirrors the model-control GET routes for bindings, connections and executors,
    minus their external-session refresh. A session whose persisted status is not
    usable is therefore not offered, which only ever narrows the pool.
    """
    getters = {"bindings": store.get_binding_public, "connections": store.get_connection_public,
               "executors": store.get_executor_public}

    def transport(url: str, _timeout: float, _limit: int) -> tuple[int, Any]:
        segments = [unquote(part) for part in urlsplit(url).path.strip("/").split("/")]
        if len(segments) != 3 or segments[0] != "api" or segments[1] not in getters:
            return 404, {"error": "route not found"}
        try:
            return 200, getters[segments[1]](segments[2])
        except KeyError:
            return 404, {"error": "not found"}

    return transport


class OwnerWindowAdmission:
    """One typed Owner confirmation -> one atomic window over exactly these Goals."""

    def __init__(self, host: Any) -> None:
        self._host = host
        self._instance = secrets.token_hex(16)
        self._lock = threading.Lock()

    # --- what the Owner is shown ---------------------------------------------

    def _pool(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        """Bindings a Task may run on, resolved exactly as dispatch resolves them."""
        host = self._host
        from .routing_inputs import binding_cost_class, read_overrides, weekly_pace_config
        owner = read_overrides(getattr(host._store, "_state_path", None))
        pace = weekly_pace_config(owner)
        # Same validation and normalization as dispatch, but read from the store in
        # this process: no HTTP to our own server (its handler needs the store lock we
        # hold), no session refresh, no quota or login probe inside the transaction.
        resolver = BindingResolver(transport=_store_transport(host._store))
        connections = {c["connection_id"]: c for c in host._store.list_connections_public()}
        pool, shown, skipped = [], [], []
        for binding in sorted(host._store.list_bindings_public(), key=lambda b: b["binding_id"]):
            if not binding.get("enabled"):
                continue
            connection = connections.get(binding.get("connection_id"), {})
            cost = binding_cost_class(binding, connection, owner)
            if cost == "paid_api":
                skipped.append(f"{binding['binding_id']} (paid API)")
                continue
            try:
                resolution = resolver.resolve(binding["binding_id"], task_executor=binding["executor_id"])
            except Exception as exc:  # noqa: BLE001 - an unusable binding is simply not offered
                skipped.append(f"{binding['binding_id']} ({type(exc).__name__})")
                continue
            entry = {"binding_ref": resolution.binding_ref, "model_id": resolution.model_id,
                     "connection_id": resolution.connection_id, "executor_id": resolution.executor_id,
                     "provider_id": resolution.provider_id, "auth_method": resolution.auth_method,
                     "base_url": resolution.base_url}
            pool.append(entry)
            shown.append({"binding": entry["binding_ref"], "executor": entry["executor_id"],
                          "model": entry["model_id"], "cost": cost,
                          "weekly_paced": bool(pace.get("enabled") and entry["executor_id"] in pace.get("executors", ()))})
        return pool, shown, skipped

    def _scope(self, goal_ids: Sequence[str], envelope: dict[str, Any]) -> dict[str, Any]:
        """Persisted truth for the prompt and for the in-transaction recheck."""
        host = self._host
        control = host._control_store
        if control._conn.execute(
                "SELECT 1 FROM platform_coordinator_claims WHERE status = 'ACTIVE' LIMIT 1").fetchone():
            raise TaskStoreError("owner_window_old_active_claims_hold")
        goals = [control.get_goal(goal_id) for goal_id in goal_ids]
        repositories = {goal.repository for goal in goals}
        if len(repositories) != 1:
            raise TaskStoreError("owner_window_requires_one_repository")
        task_count = 0
        for goal in goals:
            if (goal.status != "PLANNED" or goal.window_id or not goal.artifact_digest
                    or goal.executor_kind not in _EXECUTORS or goal.orchestration_mode not in _MODES
                    or not goal.tasks or control.list_goal_tasks(goal.id)):
                raise TaskStoreError(f"owner_window_goal_not_admissible:{goal.id}")
            for task in goal.tasks:
                if task.get("capability", "execute_task") not in envelope["capabilities"]:
                    raise TaskStoreError(f"owner_window_capability_missing:{goal.id}")
            task_count += len(goal.tasks)
        if task_count > envelope["max_tasks"]:
            raise TaskStoreError("owner_window_max_tasks_below_planned_tasks")
        repository = repositories.pop()
        workspace = resolve_repository_workspace(repository)
        if workspace.repository != repository:
            raise TaskStoreError("owner_window_repository_changed")
        pool, shown, skipped = self._pool()
        pinned = {goal.binding_ref for goal in goals if goal.binding_ref}
        if not pinned <= {entry["binding_ref"] for entry in pool}:
            raise TaskStoreError("owner_window_pinned_binding_outside_pool")
        return {"goals": [asdict(goal) for goal in goals], "repository": repository,
                "workspace": str(workspace.repo_dir), "base_sha": repository_base(repository),
                "envelope": envelope, "approved_pool": pool, "pool_display": shown,
                "pool_skipped": skipped, "paid_api": "excluded",
                "host_instance": self._instance, "os_user": getpass.getuser()}

    @staticmethod
    def render(scope: dict[str, Any], code: str, preview: Sequence[str] = ()) -> str:
        """Everything the Owner approves, in full. Too much to show is refused, never cut."""
        env = scope["envelope"]
        lines = ["Nerelan: activate an autonomous window over exactly these Goals", "",
                 f"Repository:     {scope['repository']}",
                 f"Workspace:      {scope['workspace']}  (base {scope['base_sha'][:12]})",
                 f"Window:         {env['starts_at']} -> {env['expires_at']}",
                 f"Limits:         {env['max_tasks']} tasks, {env['max_concurrent_tasks']} at a time, "
                 f"{env['max_retries']} retries",
                 f"Capabilities:   {', '.join(env['capabilities'])}",
                 f"Budget caps:    tokens {env['max_token_units'] or 'none'}, "
                 f"cost {env['max_cost_micro_units'] or 'none'}",
                 f"Paid API:       {scope['paid_api']}", "", f"Goals ({len(scope['goals'])}):"]
        for goal in scope["goals"]:
            lines += [f"- {goal['id']} rev {goal['revision']}  {goal['executor_kind']}/{goal['orchestration_mode']}"
                      f"{'  pinned ' + goal['binding_ref'] if goal['binding_ref'] else '  routed'}",
                      f"  digest {goal['artifact_digest']}",
                      f"  {goal['title']}", "  objective:"]
            lines += ["    " + line for line in goal["objective"].splitlines() or [""]]
            lines += [f"  task {task.get('id')}: {task.get('title')}" for task in goal["tasks"]]
        lines += ["", "Bindings a Task may run on:"]
        lines += [f"- {row['binding']}: {row['executor']} {row['model']} ({row['cost']}"
                  f"{', weekly paced' if row['weekly_paced'] else ''})" for row in scope["pool_display"]]
        if scope["pool_skipped"]:
            lines += ["Not offered: " + ", ".join(scope["pool_skipped"])]
        if preview:
            lines += ["", "Expected model per task (routing may still change it within the pool above):", *preview]
        lines += ["", f"Scope digest: {sha256_json(scope)}",
                  f"Type {code} to activate. Anything else cancels."]
        text = "\n".join(lines)
        if len(text) > MAX_SCOPE_CHARS:
            raise TaskStoreError("owner_window_scope_too_large")
        return text

    def _route_preview(self, scope: dict[str, Any]) -> list[str]:
        """The binding each task is expected to launch on; refuses a scope where any has none.

        Uses the same routing as launch (``GoalService._route_tasks``), with availability
        probes off, so reviews are routed with their authors' identity. Routing creates
        nothing, but like launch it may refresh quota and bind newly discovered models.
        A routed ``single``/``sequential_team`` Goal gets no binding at launch, so an Owner
        window cannot run it.
        """
        goals = self._host._goal_service
        pool = {entry["binding_ref"]: entry for entry in scope["approved_pool"]}
        lines, problems = [], []
        for snapshot in scope["goals"]:
            if not snapshot["binding_ref"] and (snapshot["orchestration_mode"] != "agent_team"
                                                or goals.task_resolver is None):
                problems.append(f"{snapshot['id']}:routed_{snapshot['orchestration_mode']}_goal_gets_no_binding"
                                f"_use_agent_team_or_pin_a_binding")
                continue
            goal = self._host._control_store.get_goal(snapshot["id"])
            planned = tuple(goals._normalize_task(raw, seq=seq) for seq, raw in enumerate(snapshot["tasks"]))
            try:
                routes, decisions = goals._route_tasks(goal, planned, window_id="", probe_availability=False)
            except TaskStoreError as exc:
                problems.append(f"{snapshot['id']}:{exc}")
                continue
            for seq, item in enumerate(planned):
                binding = routes[seq][1]
                decision = decisions.get(seq) or {}
                if not binding:
                    problems.append(f"{snapshot['id']}:{item.id}:{decision.get('reason') or 'no_binding'}")
                    continue
                if binding not in pool:
                    problems.append(f"{snapshot['id']}:{item.id}:{binding}_outside_pool")
                    continue
                model = decision.get("model_id") or pool[binding].get("model_id", "?")
                why = decision.get("reason", "routed") if decisions.get(seq) is not None else "pinned"
                lines.append(f"- {snapshot['id']} {item.id}: {binding} ({model}, {why})")
        if problems:
            raise TaskStoreError("owner_window_task_unroutable:" + "; ".join(problems)[:2000])
        return lines

    # --- activation -------------------------------------------------------------

    def _prepare(self, goal_ids: Sequence[str], *, hours: float, max_tasks: int, max_concurrent: int,
                 max_retries: int, capabilities: Sequence[str], max_token_units: int = 0,
                 max_cost_micro_units: int = 0) -> tuple[tuple[str, ...], dict[str, Any]]:
        """Validate the request and fix the envelope; binds discovered models first."""
        host = self._host
        goal_ids = tuple(goal_ids)
        if (not 1 <= len(goal_ids) <= OWNER_WINDOW_MAX_GOALS or len(set(goal_ids)) != len(goal_ids)
                or any(not isinstance(g, str) or not _GOAL_ID.fullmatch(g) for g in goal_ids)):
            raise TaskStoreError("owner_window_goals_invalid")
        if not 0 < hours * 60 <= OWNER_WINDOW_MAX_MINUTES:
            raise TaskStoreError("owner_window_duration_invalid")
        # Same ranges as the command line, so a preflight never reports ok for a request
        # that activation would refuse.
        if not 1 <= max_tasks <= 100 or not 1 <= max_concurrent <= 8 or not 0 <= max_retries <= 5:
            raise TaskStoreError("owner_window_limits_invalid")
        if max_token_units < 0 or max_cost_micro_units < 0:
            raise TaskStoreError("owner_window_budget_invalid")
        capabilities = tuple(dict.fromkeys(capabilities))
        if "execute_task" not in capabilities or not set(capabilities) <= OWNER_WINDOW_CAPABILITIES:
            raise TaskStoreError("owner_window_capabilities_invalid")
        # Discovered models bind now, so routing inside the transaction cannot
        # pick a binding the Owner was never shown.
        host._routing_bind_discovered()
        # The model-control routes refresh OpenCode login sessions on read; the pool
        # reads the store directly under the lock, so refresh once here, before it.
        host._refresh_external_session_auth(False, None)
        now = datetime.now(timezone.utc)
        # Times are fixed before the prompt; reading time spends the window.
        envelope = {"window_id": "owner-" + secrets.token_hex(16),
                    "policy_id": "owner-" + secrets.token_hex(16), "policy_revision": 1,
                    "owner_identity": f"os-user:{getpass.getuser()}",
                    "starts_at": _utc(now), "expires_at": _utc(now + timedelta(hours=hours)),
                    "repositories": [], "capabilities": list(capabilities),
                    "max_tasks": max_tasks, "max_concurrent_tasks": max_concurrent,
                    "max_retries": max_retries, "max_token_units": max_token_units,
                    "max_cost_micro_units": max_cost_micro_units,
                    # Without a reservation every use of a capped window was an overrun
                    # (2026-11-09). Reserve an even share of each cap per task.
                    "per_task_token_reservation": max_token_units // max(max_tasks, 1),
                    "per_task_cost_reservation": max_cost_micro_units // max(max_tasks, 1),
                    "provider_quota_state": "UNKNOWN", "enforcement_class": "HARD_ADMISSION_ENFORCED"}
        return goal_ids, envelope

    @staticmethod
    def card_digest(scope: Mapping[str, Any]) -> str:
        """What the confirmation card shows, without per-request identities and times.

        Goals at their revisions and artifact digests, repository and base, every
        bound, the model pool. A request activates only if this is unchanged since
        the card was drawn (Owner decision 2026-11-09: the card's Start is the
        confirmation).
        """
        raw = scope["envelope"]
        envelope = {key: value for key, value in raw.items()
                    if key not in {"window_id", "policy_id", "starts_at", "expires_at", "owner_identity"}}
        # The window's length is a bound the card shows; its clock times are per request.
        envelope["duration_seconds"] = round((
            datetime.fromisoformat(raw["expires_at"].replace("Z", "+00:00"))
            - datetime.fromisoformat(raw["starts_at"].replace("Z", "+00:00"))).total_seconds())
        return sha256_json({**{key: value for key, value in scope.items()
                               if key not in {"envelope", "host_instance", "os_user"}}, "envelope": envelope})

    def _state_dir(self) -> Path | None:
        state_path = getattr(self._host._store, "_state_path", None)
        return Path(state_path).parent if state_path else None

    def _settings(self) -> dict[str, Any]:
        """The Owner's owner_window_settings.json beside the task store; absent means defaults."""
        state_dir = self._state_dir()
        if state_dir is None:
            return {}
        try:
            data = json.loads((state_dir / "owner_window_settings.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as exc:
            raise TaskStoreError("owner_window_settings_invalid") from exc
        if (not isinstance(data, dict) or data.get("confirmation", "ui") not in {"ui", "terminal"}
                or not isinstance(data.get("supervisor_activation", False), bool)):
            raise TaskStoreError("owner_window_settings_invalid")
        return data

    def confirmation_mode(self) -> str:
        """``ui`` (default) or ``terminal``, from the Owner's owner_window_settings.json."""
        return self._settings().get("confirmation", "ui")

    def supervisor_enabled(self) -> bool:
        """Off unless the Owner's settings say ``"supervisor_activation": true``."""
        return self._settings().get("supervisor_activation", False) is True

    def _digest_confirm(self, card_digest: Any) -> Callable[..., bool]:
        if not isinstance(card_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", card_digest):
            raise TaskStoreError("owner_window_card_digest_invalid")

        def confirm(_text: str, _code: str, *, scope: Mapping[str, Any]) -> bool:
            if self.card_digest(scope) != card_digest:
                raise TaskStoreError("owner_window_scope_changed")
            return True
        return confirm

    def supervisor_request(self, goal_ids: Any, preset: Any) -> dict[str, Any]:
        """The window request a preset gives for these Goals; a supervisor cannot ask for another."""
        from .quick_start import presets, window_request
        options = presets(self._state_dir())
        if not isinstance(preset, str) or preset not in options:
            raise TaskStoreError("owner_window_preset_invalid")
        if (not isinstance(goal_ids, (list, tuple)) or not goal_ids
                or not all(isinstance(goal_id, str) and _GOAL_ID.fullmatch(goal_id) for goal_id in goal_ids)):
            raise TaskStoreError("owner_window_request_invalid")
        host = self._host
        with host._task_store._lock, host._store._lock:
            tasks = sum(len(host._control_store.get_goal(goal_id).tasks) for goal_id in goal_ids)
        request = window_request(options[preset], list(goal_ids), tasks=tasks)
        del request["goal_ids"]
        return request

    def admit_from_supervisor(self, goal_ids: Any, *, preset: Any, card_digest: Any,
                              requested_by: Any = "") -> Any:
        """Activation a supervising agent asks the running host for (Owner decision 2026-11-10).

        Off unless the Owner's settings turn it on, and never in strict ``terminal``
        mode. The bounds are a preset's, computed here; the request names only the
        preset, the Goals and the digest of the preflight it read. Everything else is
        the card path: scope reread, one atomic commit, one receipt per Goal, and the
        receipt says a supervisor asked.
        """
        if self.confirmation_mode() != "ui" or not self.supervisor_enabled():
            raise TaskStoreError("owner_window_supervisor_activation_disabled")
        confirm = self._digest_confirm(card_digest)
        request = self.supervisor_request(goal_ids, preset)
        return self.admit(list(goal_ids), **request, confirm=confirm, surface="supervisor",
                          requested_by=str(requested_by or "")[:200])

    def admit_from_card(self, goal_ids: Sequence[str], *, card_digest: str, **request: Any) -> Any:
        """Activation from the confirmation card's Start (Owner decision 2026-11-09).

        The local client session authenticates the caller; the Start click is the
        Owner's confirmation. The card's digest must match the scope read now, and
        everything else is the terminal path: persisted truth reread inside the
        transaction, one atomic commit, one receipt per Goal. With the Owner's
        strict mode (``terminal``) the card cannot activate.
        """
        if self.confirmation_mode() != "ui":
            raise TaskStoreError("owner_window_terminal_confirmation_required")
        return self.admit(goal_ids, **request, confirm=self._digest_confirm(card_digest), surface="ui")

    def preflight(self, goal_ids: Sequence[str], **request: Any) -> dict[str, Any]:
        """Everything that would refuse activation or block the window, reported, not raised.

        Changes nothing beyond what admission does first anyway (binding discovered
        models, refreshing login sessions, routing). Authorizes nothing: no window,
        no approval, no receipt.
        """
        checks: list[dict[str, Any]] = []

        def add(check: str, reason: str = "", detail: str = "") -> None:
            checks.append({"check": check, "ok": not reason, "reason": reason, "detail": detail})

        result: dict[str, Any] = {"ok": False, "checks": checks, "preview": [], "scope": None}
        try:
            goal_ids, envelope = self._prepare(goal_ids, **request)
        except TaskStoreError as exc:
            add("request", str(exc))
            return result
        host = self._host
        control = host._control_store
        scope = None
        with host._task_store._lock, host._store._lock:
            held = control._conn.execute(
                "SELECT COUNT(*) FROM platform_coordinator_claims WHERE status = 'ACTIVE'").fetchone()[0]
            add("leftover_claims", "owner_window_old_active_claims_hold" if held else "",
                f"{held} active coordinator claims; reconcile or isolate them first" if held else "none")
            if held:
                add("goals", "skipped_while_claims_hold")
            else:
                try:
                    envelope["repositories"] = [control.get_goal(goal_ids[0]).repository]
                    scope = json.loads(canonical_json(self._scope(goal_ids, envelope)))
                except TaskStoreError as exc:
                    add("goals", str(exc))
        if scope is not None:
            tasks = sum(len(goal["tasks"]) for goal in scope["goals"])
            add("goals", "", f"{len(scope['goals'])} goals, {tasks} tasks in {scope['repository']}")
            add("model_pool", "" if scope["approved_pool"] else "owner_window_pool_empty",
                f"{len(scope['approved_pool'])} bindings offered, {len(scope['pool_skipped'])} not offered")
            try:
                result["preview"] = self._route_preview(scope)
                add("routing", "", f"{len(result['preview'])} tasks placed")
            except TaskStoreError as exc:
                add("routing", str(exc))
            env = scope["envelope"]
            result["scope"] = {
                "repository": scope["repository"], "base_sha": scope["base_sha"],
                "goals": [{"id": goal["id"], "objective": goal["objective"], "mode": goal["orchestration_mode"],
                           "tasks": [{"id": task.get("id"), "title": task.get("title")} for task in goal["tasks"]]}
                          for goal in scope["goals"]],
                "pool": scope["pool_display"], "pool_skipped": scope["pool_skipped"],
                "envelope": {key: env[key] for key in (
                    "starts_at", "expires_at", "capabilities", "max_tasks", "max_concurrent_tasks",
                    "max_retries", "max_token_units", "max_cost_micro_units")},
                "paid_api": scope["paid_api"]}
            result["card_digest"] = self.card_digest(scope)
            result["confirmation"] = self.confirmation_mode()
        result["ok"] = all(check["ok"] for check in checks)
        return result

    def admit(self, goal_ids: Sequence[str], *, hours: float, max_tasks: int, max_concurrent: int,
              max_retries: int, capabilities: Sequence[str], confirm: Callable[..., bool],
              max_token_units: int = 0, max_cost_micro_units: int = 0, surface: str = "terminal",
              requested_by: str = "") -> Any:
        if surface not in _MECHANISMS:
            raise TaskStoreError("owner_window_surface_invalid")
        if not self._lock.acquire(blocking=False):
            raise TaskStoreError("owner_window_admission_in_progress")
        try:
            host = self._host
            goal_ids, envelope = self._prepare(
                goal_ids, hours=hours, max_tasks=max_tasks, max_concurrent=max_concurrent,
                max_retries=max_retries, capabilities=capabilities, max_token_units=max_token_units,
                max_cost_micro_units=max_cost_micro_units)
            deadline = time.monotonic() + CONFIRM_SECONDS
            with host._task_store._lock, host._store._lock:
                goal = host._control_store.get_goal(goal_ids[0])
                envelope["repositories"] = [goal.repository]
                before = canonical_json(self._scope(goal_ids, envelope))
            # Outside the locks: routing may refresh quota. A task that would launch with no
            # binding is refused at dispatch, so it is refused here, before the Owner is asked.
            preview = self._route_preview(json.loads(before))
            code = secrets.token_hex(3).upper()
            confirmed = (confirm("", code, scope=json.loads(before)) if surface != "terminal"
                         else confirm(self.render(json.loads(before), code, preview), code))
            if confirmed is not True:
                raise TaskStoreError("owner_window_confirmation_refused")
            if time.monotonic() >= deadline:
                raise TaskStoreError("owner_window_confirmation_expired")
            approved = json.loads(before)

            def validate() -> None:
                if canonical_json(self._scope(goal_ids, envelope)) != before:
                    raise TaskStoreError("owner_window_scope_changed")
                if time.monotonic() >= deadline:
                    raise TaskStoreError("owner_window_confirmation_expired")

            def sql_admit(window_id: str) -> None:
                validate()  # BEGIN IMMEDIATE is held: reread persisted truth.
                control = host._control_store
                marked = control._conn.execute(
                    "UPDATE platform_autonomous_windows SET confirmation_mode = ? WHERE id = ?",
                    (OWNER_WINDOW_MODE, window_id))
                if marked.rowcount != 1:
                    raise TaskStoreError("owner_window_missing")
                provenance_base = {"host_instance_id": self._instance, "os_user": approved["os_user"],
                                   "scope_digest": sha256_json(approved), "goals": list(goal_ids),
                                   "envelope": envelope, "approved_pool": approved["approved_pool"],
                                   "workspace": approved["workspace"], "base_sha": approved["base_sha"],
                                   "mechanism": _MECHANISMS[surface]}
                if surface == "supervisor":
                    provenance_base["requested_by"] = requested_by
                for goal_snapshot in approved["goals"]:
                    provenance = {**provenance_base, "goal_id": goal_snapshot["id"],
                                  "goal_revision": goal_snapshot["revision"],
                                  "artifact_digest": goal_snapshot["artifact_digest"]}
                    receipt = control.append_receipt(
                        window_id=window_id, operation_type=OWNER_WINDOW_RECEIPT, capability="execute_task",
                        repository=approved["repository"], subject_id=goal_snapshot["id"], decision="allowed",
                        reason="owner_window_exact_scope", input_payload={"goal_id": goal_snapshot["id"]},
                        result=sha256_json(provenance))
                    stored = control._conn.execute(
                        "UPDATE platform_operation_receipts SET evidence_json = ?, confirmation_mode = ? "
                        "WHERE id = ? AND window_id = ? AND operation_type = ?",
                        (canonical_json(provenance), OWNER_WINDOW_MODE, receipt.id, window_id, OWNER_WINDOW_RECEIPT))
                    if stored.rowcount != 1:
                        raise TaskStoreError("owner_window_receipt_missing")
                    host._goal_service.approve(goal_snapshot["id"], expected_revision=goal_snapshot["revision"],
                                               policy_ref=envelope["policy_id"])
                    host._goal_service._launch(goal_snapshot["id"], expected_revision=goal_snapshot["revision"],
                                               window_id=window_id, probe_availability=False,
                                               _owner_window_admission=True)
                    # Routing inside the transaction can still come back empty (quota moved since
                    # the preview); an unbound task would fail at dispatch and block the window.
                    for link in control.list_goal_tasks(goal_snapshot["id"]):
                        if not host._task_store.get_task(link["task_id"]).binding_ref:
                            raise TaskStoreError(
                                f"owner_window_task_unbound:{goal_snapshot['id']}:{link['plan_task_id']}")
                if time.monotonic() >= deadline:
                    raise TaskStoreError("owner_window_confirmation_expired")

            with host._task_store._lock, host._store._lock:
                validate()
                return host._control_store.activate_window(
                    envelope, confirmation="ACTIVATE", _host_sql_admit=sql_admit,
                    _host_expected_goal_ids=goal_ids)
        finally:
            self._lock.release()


# --- command line ---------------------------------------------------------------

def terminal_confirm(text: str, code: str, *, stdin: Any = None, stdout: Any = None) -> bool:
    """Show the scope and read the code from an interactive terminal only."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    if not stdin.isatty():
        stdout.write("Refused: the code must be typed at an interactive terminal.\n")
        return False
    stdout.write(text + "\n> ")
    stdout.flush()
    answer = stdin.readline().strip()
    return secrets.compare_digest(answer.upper(), code)


def parse(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    parser.add_argument("--goal", action="append", required=True, metavar="GOAL_ID")
    parser.add_argument("--hours", type=float, required=True)
    parser.add_argument("--max-tasks", type=int, required=True)
    parser.add_argument("--max-concurrent", type=int, default=1)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--capability", action="append", required=True,
                        choices=sorted(OWNER_WINDOW_CAPABILITIES))
    parser.add_argument("--max-token-units", type=int, default=0)
    parser.add_argument("--max-cost-micro-units", type=int, default=0)
    args = parser.parse_args(argv)
    if (len(args.goal) > OWNER_WINDOW_MAX_GOALS or len(set(args.goal)) != len(args.goal)
            or any(not _GOAL_ID.fullmatch(g) for g in args.goal)):
        parser.error("--goal values must be distinct Goal IDs")
    if not 0 < args.hours * 60 <= OWNER_WINDOW_MAX_MINUTES:
        parser.error("--hours must be above 0 and at most 168")
    if not 1 <= args.max_tasks <= 100 or not 1 <= args.max_concurrent <= 8 or not 0 <= args.max_retries <= 5:
        parser.error("limits out of range")
    if "execute_task" not in args.capability:
        parser.error("--capability execute_task is required")
    if args.max_token_units < 0 or args.max_cost_micro_units < 0:
        parser.error("budget caps must not be negative")
    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse(argv)  # before importing or starting the host
    from .trusted_host import run_combined_trusted_host
    run_combined_trusted_host(owner_window={
        "goal_ids": tuple(args.goal), "hours": args.hours, "max_tasks": args.max_tasks,
        "max_concurrent": args.max_concurrent, "max_retries": args.max_retries,
        "capabilities": tuple(args.capability), "max_token_units": args.max_token_units,
        "max_cost_micro_units": args.max_cost_micro_units, "confirm": terminal_confirm})


if __name__ == "__main__":
    main()
