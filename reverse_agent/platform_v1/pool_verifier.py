"""Verify unproven models in the background while an Owner window is active.

Routing ranks a verified model ahead of every unverified one, whatever it
costs. Without verification the first model that ever worked takes all the
work (run host, 2026-11-10: one credit-billed model got 42M of 46.8M tokens
while 180 other bindings stayed "unverified").

Owner decision 2026-11-11: inside an active window the host verifies unproven
candidates by default. Each check is the existing `Reply OK` request (4 output
tokens) through the existing probe path, at most one per minute, cheapest and
strongest first. Results go to the existing availability cache, so later
selections, escalations and windows use them. It never runs without an active
window that permits model calls, never touches native Owner accounts, and
never probes a paid API unless the window allows paid use.

Each binding is tried at most once per day by this thread, whatever the
answer: a binding that keeps answering 429 must not be asked again every few
minutes, nor hold up the bindings behind it.

Off switches: `"availability_probes": false` in model_routing_overrides.json,
or `REVERSE_AGENT_ROUTING_PROBES=0`.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from types import SimpleNamespace
from typing import Any

LOG = logging.getLogger(__name__)
POLL_SECONDS = 60.0
RETRY_SECONDS = 86400.0
_COST_RANK = {"free": 0, "subscription": 1, "paid_api": 2}


class PoolVerifier:
    def __init__(self, host: Any, *, poll_seconds: float = POLL_SECONDS) -> None:
        self._host = host
        self._poll_seconds = poll_seconds
        self._stop: threading.Event | None = None
        self._thread: threading.Thread | None = None
        # When this thread last tried each binding; a failed or inconclusive try is not repeated.
        self._tried: dict[str, float] = {}

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop = stop = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(stop,), name="routing-pool-verify", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        stop, self._stop = self._stop, None
        thread, self._thread = self._thread, None
        if stop is not None:
            stop.set()
        if thread is not None:
            thread.join(timeout=5)

    def _run(self, stop: threading.Event) -> None:
        # The first check comes one interval after start: startup makes no model call.
        while not stop.wait(self._poll_seconds):
            try:
                self.verify_once()
            except Exception:  # noqa: BLE001 - verification is advisory and must not stop the host
                LOG.exception("routing pool verification failed")

    def verify_once(self, *, now: float | None = None) -> str | None:
        """Verify at most one unproven binding; returns its id, or None if nothing was checked."""
        from .model_availability import native_owner_account
        from .model_router import capability
        from .routing_inputs import binding_cost_class, read_overrides

        host = self._host
        now = time.time() if now is None else now
        if os.environ.get("REVERSE_AGENT_ROUTING_PROBES") == "0":
            return None
        try:
            owner = read_overrides(getattr(host._store, "_state_path", None))
        except ValueError:
            return None  # a broken settings file never widens what the host does
        if owner.get("availability_probes", True) is False:
            return None
        window = host._control_store.active_window()
        if window is None:
            return None
        goal = SimpleNamespace(window_id=window.id)
        if not host._routing_probe_window_allowed(goal):
            return None
        allow_paid = host._routing_paid_allowed(goal, owner)
        connections = {c["connection_id"]: c for c in host._store.list_connections_public()}
        runnable = host._runnable_bindings()
        profiles = host._usage_profiles()
        history = host._routing_availability_history()
        pending = []
        for binding in host._store.list_bindings_public():
            binding_id = binding["binding_id"]
            connection = connections.get(binding["connection_id"])
            if (connection is None or not binding.get("enabled", True) or not connection.get("enabled", True)
                    or binding_id not in runnable or native_owner_account(binding, connection)
                    or now - self._tried.get(binding_id, float("-inf")) < RETRY_SECONDS
                    or (owner.get("bindings", {}).get(binding_id) or {}).get("exclude") is True):
                continue
            cost_class = binding_cost_class(binding, connection, owner)
            if cost_class == "paid_api" and not allow_paid:
                continue
            known = host._routing_availability(binding, connection, allow_paid=allow_paid, cost_class=cost_class,
                                               probe_allowed=False, history=history.get(binding_id, ()), runnable=True)
            if known.get("state") != "UNKNOWN":
                continue
            tier = capability(binding["model_id"], profiles.get(binding_id, {}), "code", 3)[0]
            pending.append((_COST_RANK.get(cost_class, 2), -tier, binding_id, binding, connection))
        if not pending:
            return None
        _, _, binding_id, binding, connection = min(pending, key=lambda item: item[:3])
        cache = host._availability_cache
        if now < cache.next_probe:
            return None  # the one-per-minute limit shared with selection-time probes
        probe = getattr(host, "_availability_probe", None) or host._probe_routing_binding
        self._tried[binding_id] = now
        result = cache.check(binding, connection, probe=probe, allow_probe=True, now=now)
        LOG.info("routing pool verification: %s is %s (%s)", binding_id, result.get("state"), result.get("reason"))
        return binding_id
