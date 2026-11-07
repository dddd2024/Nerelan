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
from contextlib import nullcontext
from typing import Any, Callable, Iterable, Mapping, Optional

from ...model_access.subscription_quota import magpie_route_provider
from .alerts import AlertLedger, epoch_seconds, evaluate_alerts, jsonl_sink
from .config import MultiAccountConfig
from .status import AccountHealth, AccountStatus, MultiAccountStatusMonitor

_logger = logging.getLogger(__name__)

USABLE = (AccountHealth.HEALTHY, AccountHealth.DEGRADED)


# Route provider (as magpie_route_provider names it) -> executor id the pacing policy names.
_PACED_EXECUTOR = {"codex": "codex", "claude-code": "claude_code"}


def pace_state(status: AccountStatus, pace: Optional[Mapping[str, Any]], now: float,
               drain_since: Optional[float] = None) -> Optional[dict[str, Any]]:
    """The weekly pacing line for this account, with the router's rule.

    ``held_until`` is an estimate for a typical task: routing uses each task's
    own need, the display the uncalibrated 3 points. An announced Codex reset
    (``drain_since`` is its announcement time) lifts the hold here too, unless
    this account's week began after it: then its reset happened, as in routing.
    """
    from ..model_router import WEEK_SECONDS, weekly_pace_hold
    executor = _PACED_EXECUTOR.get(magpie_route_provider(status.provider) or "")
    weekly = next((w for w in status.windows if w.window in {"7 days", "weekly", "7d", "week"}
                   and w.used_percent is not None and w.resets_at is not None and not w.reset_passed), None)
    if not pace or not pace.get("enabled") or executor not in pace.get("executors", ()) or weekly is None:
        return None
    candidate = {"executor_id": executor, "cost_class": "subscription",
                 "weekly_headroom": 1 - weekly.used_percent / 100, "weekly_resets_at": weekly.resets_at}
    elapsed = min(1., max(0., (now - (weekly.resets_at - WEEK_SECONDS)) / WEEK_SECONDS))
    draining = (executor == "codex" and drain_since is not None
                and weekly.resets_at - WEEK_SECONDS <= drain_since)
    return {"used": weekly.used_percent / 100,
            # Same reading as the Magpie panel's "配速 +20%": spend minus elapsed share of the week.
            "deviation": weekly.used_percent / 100 - elapsed,
            "line": min(1 - float(pace.get("reserve", .1)), elapsed + float(pace.get("slack", .1))),
            "held_until": None if draining else weekly_pace_hold(candidate, now=now, pace=pace),
            "draining": draining,
            "resets_at": weekly.resets_at}


def account_row(status: AccountStatus, *, cooldown: Optional[Mapping[str, Any]],
                score: Optional[Mapping[str, Any]], now: float,
                pace: Optional[Mapping[str, Any]] = None, drain_since: Optional[float] = None) -> dict[str, Any]:
    active = bool(cooldown) and float(cooldown.get("until") or 0) > now
    return {
        **status.public_view(),
        # False means the account is observed only: no route here claims its
        # provider, so its windows never reach quota admission.
        "admission_evidence": magpie_route_provider(status.provider) is not None,
        "cooldown": dict(cooldown) if active else None,
        "score": dict(score) if score else None,
        "dispatchable": status.health in USABLE and not active,
        "weekly_pace": pace_state(status, pace, now, drain_since),
    }


def window_renews(control_store: Any, window: Any) -> bool:
    """Whether a standing policy will succeed this window when it expires."""
    policy = control_store.standing_window(window.policy_id)
    if not policy or policy.get("status") != "ACTIVE":
        return False
    until, expires = epoch_seconds(policy.get("renew_until")), epoch_seconds(window.expires_at)
    return until is not None and expires is not None and until > expires


def _summary(rows: list[dict[str, Any]], statuses: Iterable[AccountStatus],
             cooldowns: Mapping[str, Any]) -> dict[str, Any]:
    summary = MultiAccountStatusMonitor.health_summary(statuses)
    return {
        **summary,
        "dispatchable_accounts": sum(1 for row in rows if row["dispatchable"]),
        # From the registry: a cooldown can name a ref no observed account has.
        "cooling_accounts": len(cooldowns),
    }


class PoolMonitor:
    """Latest pool view plus alert state; every source is injected."""

    def __init__(self, *, config: MultiAccountConfig,
                 fetch_snapshot: Callable[[], Optional[Mapping[str, Any]]],
                 stored_statuses: Callable[[], list[AccountStatus]],
                 runtime_status: Callable[[], Mapping[str, Any]],
                 brain: Callable[[], Any],
                 persist_alerts: bool = False,
                 weekly_pace: Callable[[], Optional[Mapping[str, Any]]] = lambda: None,
                 reset_signal: Callable[[], Optional[Mapping[str, Any]]] = lambda: None,
                 clock: Callable[[], float] = time.time) -> None:
        self._config = config
        self._reset_signal = reset_signal
        self._weekly_pace = weekly_pace
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
        self._last_refresh: Optional[float] = None
        self._last_statuses: list[AccountStatus] = []
        self._last_statuses_at: Optional[float] = None
        self._last_cooldowns: dict[str, Any] = {}
        self._last_ledger: tuple[dict[str, Any], ...] = ({}, {}, {})
        self._last_runtime: dict[str, Any] = {}
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

    def _cooldowns(self, now: float) -> tuple[dict[str, Any], bool]:
        """Active cooldowns from the in-memory registry, independent of the ledger.

        A failed read falls back to the last good one, but expiry still applies:
        a remembered quarantine must end when its time is up.
        """
        try:
            brain = self._brain()
            with getattr(brain, "_feedback_lock", nullcontext()):
                self._last_cooldowns = {ref: brain.cooldowns.get(ref).to_state()
                                        for ref in brain.cooldowns.active_map(now=now)}
            return self._last_cooldowns, True
        except Exception:  # noqa: BLE001 - feedback is optional; perception still reports
            return {ref: item for ref, item in self._last_cooldowns.items()
                    if float(item.get("until") or 0) > now}, False

    def _ledger_reads(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]:
        """Scores, routing and policy; the last good read if the ledger is unreadable."""
        try:
            brain = self._brain()
            self._last_ledger = (brain.account_scores(), brain.routing(), brain.account_policy_view())
            fresh = True
        except Exception:  # noqa: BLE001
            fresh = False
        scores, routing, policy = self._last_ledger
        return scores, routing, policy, fresh

    def _codex_reset(self) -> Optional[dict[str, Any]]:
        """The reset signal routing uses, reduced to what an operator needs."""
        try:
            signal = self._reset_signal() or {}
        except Exception:  # noqa: BLE001
            return None
        if signal.get("state") not in {"PLAN_ONLY", "REFRESH_QUOTA"}:
            return None
        return {key: signal.get(key) for key in
                ("state", "expected_reset_at", "source_url", "assumed", "announced_at")}

    def _aged_statuses(self, now: float) -> list[AccountStatus]:
        """Last known rows; past the freshness budget they stop claiming health."""
        age = now - self._last_statuses_at if self._last_statuses_at is not None else 0.0
        if age <= self._config.observation_freshness_seconds:
            return self._last_statuses
        return [status.model_copy(update={"health": AccountHealth.STALE, "freshness_age": age})
                for status in self._last_statuses]

    def _stalled_seconds(self, coordinator: Mapping[str, Any], now: float) -> Optional[float]:
        """Seconds without a finished tick while the coordinator claims to run."""
        ticks = coordinator.get("ticks")
        # A long gap between observations means the host slept: nobody was
        # running, so that time says nothing about the coordinator.
        slept = (self._last_refresh is not None
                 and now - self._last_refresh > self._config.alert_interval_seconds * 3)
        self._last_refresh = now
        if coordinator.get("lifecycle") != "RUNNING" or not isinstance(ticks, int):
            self._progress = None
            return None
        if slept or self._progress is None or self._progress[0] != ticks:
            self._progress = (ticks, now)
        return now - self._progress[1]

    def refresh(self) -> dict[str, Any]:
        """Run one observation. Never raises: a monitor must outlive its sources."""
        now = self._clock()
        source, statuses = self._perceive()
        # One failed read is not news about the accounts: keep the last known
        # rows, so their alerts neither resolve nor re-raise on a transport blip.
        if source == "unavailable":
            statuses = self._aged_statuses(now)
        else:
            self._last_statuses, self._last_statuses_at = statuses, now
        cooldowns, cooldowns_fresh = self._cooldowns(now)
        scores, routing, policy, ledger_fresh = self._ledger_reads()
        try:
            pace = self._weekly_pace()
        except Exception:  # noqa: BLE001 - a bad Owner file must not blank the view
            pace = None
        codex_reset = self._codex_reset()
        drain_since = None
        if (codex_reset and codex_reset.get("state") == "PLAN_ONLY"
                and (epoch_seconds(codex_reset.get("expected_reset_at")) or 0) > now):
            # Without an announcement time routing cannot tell a renewed week either.
            drain_since = epoch_seconds(codex_reset.get("announced_at")) or now
        rows = [account_row(status, cooldown=cooldowns.get(status.account_ref), pace=pace, drain_since=drain_since,
                            score=scores.get(status.account_ref), now=now)
                for status in statuses]
        rows.sort(key=lambda row: (not row["dispatchable"], -(row["headroom_pct"] or 0), row["account_ref"]))
        pool = {"source": source, "accounts": rows, "cooldowns": cooldowns,
                "feedback_fresh": cooldowns_fresh and ledger_fresh}
        try:
            runtime = dict(self._runtime_status())
            self._last_runtime = runtime
        except Exception:  # noqa: BLE001
            runtime = {**self._last_runtime, "stale": True}
        with self._lock:
            stalled = self._stalled_seconds(runtime.get("coordinator") or {}, now)
            self._ledger.observe(evaluate_alerts(pool, runtime, self._config, now=now,
                                                 stalled_seconds=stalled), now=now)
            view = {
                "observed_at": now,
                "source": source,
                "summary": _summary(rows, statuses, cooldowns),
                "accounts": rows,
                "routing": routing,
                "policy": policy,
                "budget": runtime.get("budget") or None,
                "codex_reset": codex_reset,
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
