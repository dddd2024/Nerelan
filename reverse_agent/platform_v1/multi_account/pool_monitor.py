"""One read model of the account pool, refreshed off the dispatch path.

Perception, cooldowns, scores and the routing policy already exist; this module
joins them into the single view operators and the web client read, and runs the
alert rules on it. It has its own thread on purpose: an alert about a stuck
coordinator cannot depend on the coordinator's tick.

It is strictly read-only. A snapshot read here is diagnostic and never reaches
``platform_quota_observations``, which stays hard-admission evidence, and it
never calls a model or writes account state.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Optional

from ...model_access.subscription_quota import magpie_route_provider
from .alerts import AlertLedger, evaluate_alerts, jsonl_sink
from .config import MultiAccountConfig
from .status import AccountHealth, AccountStatus, MultiAccountStatusMonitor

_logger = logging.getLogger(__name__)

USABLE = (AccountHealth.HEALTHY, AccountHealth.DEGRADED)


def account_row(status: AccountStatus, *, cooldown: Optional[Mapping[str, Any]],
                score: Optional[Mapping[str, Any]], now: float) -> dict[str, Any]:
    active = bool(cooldown) and float(cooldown.get("until") or 0) > now
    return {
        **status.public_view(),
        # False means the account is observed only: no route here claims its
        # provider, so its windows never reach quota admission.
        "admission_evidence": magpie_route_provider(status.provider) is not None,
        "cooldown": dict(cooldown) if active else None,
        "score": dict(score) if score else None,
        "dispatchable": status.health in USABLE and not active,
    }


def _summary(rows: list[dict[str, Any]], statuses: Iterable[AccountStatus]) -> dict[str, Any]:
    summary = MultiAccountStatusMonitor.health_summary(statuses)
    return {
        **summary,
        "dispatchable_accounts": sum(1 for row in rows if row["dispatchable"]),
        "cooling_accounts": sum(1 for row in rows if row["cooldown"]),
    }


class PoolMonitor:
    """Latest pool view plus alert state; every source is injected."""

    def __init__(self, *, config: MultiAccountConfig,
                 fetch_snapshot: Callable[[], Optional[Mapping[str, Any]]],
                 stored_statuses: Callable[[], list[AccountStatus]],
                 runtime_status: Callable[[], Mapping[str, Any]],
                 brain: Callable[[], Any],
                 persist_alerts: bool = False,
                 clock: Callable[[], float] = time.time) -> None:
        self._config = config
        self._fetch_snapshot = fetch_snapshot
        self._stored_statuses = stored_statuses
        self._runtime_status = runtime_status
        self._brain = brain
        self._clock = clock
        sink = None
        if persist_alerts:
            sink = jsonl_sink(config.alert_log_path, max_bytes=config.alert_log_max_bytes,
                              backups=config.alert_log_backups)
        self._ledger = AlertLedger(sink)
        self._lock = threading.Lock()
        self._view: Optional[dict[str, Any]] = None
        self._view_at = 0.0
        self._progress: Optional[tuple[int, float]] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _perceive(self) -> tuple[str, list[AccountStatus]]:
        try:
            snapshot = self._fetch_snapshot()
        except Exception:  # noqa: BLE001 - transport text may carry private detail
            return "unavailable", []
        if snapshot is None:
            statuses = self._stored_statuses()
            return ("observations" if statuses else "none"), statuses
        if snapshot.get("status") != "available":
            return "unavailable", []
        return "magpie", MultiAccountStatusMonitor(self._config, clock=self._clock).diagnose(snapshot)

    def _feedback(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Cooldowns, scores, routing and policy; absent when the brain is unavailable."""
        try:
            brain = self._brain()
            now = self._clock()
            cooldowns = {ref: brain.cooldowns.get(ref).to_state() for ref in brain.cooldowns.active_map(now=now)}
            return cooldowns, brain.account_scores(), brain.routing(), brain.account_policy_view()
        except Exception:  # noqa: BLE001 - feedback is optional; perception still reports
            return {}, {}, {}, {}

    def _stalled_seconds(self, coordinator: Mapping[str, Any], now: float) -> Optional[float]:
        """Seconds without a finished tick while the coordinator claims to run."""
        ticks = coordinator.get("ticks")
        if coordinator.get("lifecycle") != "RUNNING" or not isinstance(ticks, int):
            self._progress = None
            return None
        if self._progress is None or self._progress[0] != ticks:
            self._progress = (ticks, now)
        return now - self._progress[1]

    def refresh(self) -> dict[str, Any]:
        """Run one observation. Never raises: a monitor must outlive its sources."""
        now = self._clock()
        source, statuses = self._perceive()
        cooldowns, scores, routing, policy = self._feedback()
        rows = [account_row(status, cooldown=cooldowns.get(status.account_ref),
                            score=scores.get(status.account_ref), now=now)
                for status in statuses]
        rows.sort(key=lambda row: (not row["dispatchable"], -(row["headroom_pct"] or 0), row["account_ref"]))
        pool = {"source": source, "accounts": rows}
        try:
            runtime = dict(self._runtime_status())
        except Exception:  # noqa: BLE001
            runtime = {}
        with self._lock:
            stalled = self._stalled_seconds(runtime.get("coordinator") or {}, now)
            self._ledger.observe(evaluate_alerts(pool, runtime, self._config, now=now,
                                                 stalled_seconds=stalled), now=now)
            view = {
                "observed_at": now,
                "source": source,
                "summary": _summary(rows, statuses),
                "accounts": rows,
                "routing": routing,
                "policy": policy,
                "budget": runtime.get("budget") or None,
                "alerts": {"active": self._ledger.active(), "recent": self._ledger.recent()},
                "monitoring": self._thread is not None,
            }
            self._view, self._view_at = view, now
        return view

    def view(self) -> dict[str, Any]:
        """Cached view; refreshed here only when no monitor thread keeps it fresh."""
        with self._lock:
            cached, age = self._view, self._clock() - self._view_at
        if cached is not None and age < self._config.alert_interval_seconds:
            return cached
        if cached is not None and self._thread is not None:
            return cached
        return self.refresh()

    def _run(self) -> None:
        # Wait first: the host is still starting its coordinator at thread start.
        while not self._stop.wait(self._config.alert_interval_seconds):
            try:
                self.refresh()
            except Exception:  # noqa: BLE001
                _logger.exception("multi_account_pool_refresh_failed")

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="multi-account-pool-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=5)
        self._ledger.close()
