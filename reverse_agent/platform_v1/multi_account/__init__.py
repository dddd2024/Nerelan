"""Multi-account orchestration brain: perception, scheduling and self-evolution.

This package is the wiring layer the planning spec calls for. It reuses —
rather than rewrites — the mature assets already in the repository:

  - account/quota observation : :func:`model_access.subscription_quota.magpie_account_quotas`
  - reservation / admission    : :mod:`quota_reservation`
  - break-even decision core   : :mod:`orchestration_selector`
  - durable / unattended runtime : :mod:`durable_execution`, :mod:`unattended_coordinator`
  - cost measurement           : :mod:`usage_ledger` (list-price ``cost_units``)

What it *adds* (and only what was missing):
  - a centralized, validated config (:mod:`.config`),
  - a status-perception layer that keeps *every* account instead of one per
    provider (:mod:`.status`, with :func:`pool_account_quotas` as the drop-in
    fix for the ``_merge_magpie_quotas`` defect),
  - an account-aware scheduler with bounded reroute / dead-letter
    (:mod:`.scheduler`),
  - a rolling-window cost ceiling with reservation-based admission
    (:mod:`.budget`),
  - rule-based alerting with dedupe and a bounded history (:mod:`.alerts`),
  - a run watchdog that bounds duration and idle time (:mod:`.watchdog`),
  - a persistence + feedback self-evolution loop (:mod:`.evolution`) plus a
    clamped, audited, rollback-able policy chain (:mod:`.policy`).

Nothing here holds credentials or spins up a second orchestration spine.
"""
from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

from .alerts import Alert, AlertEngine, AlertSeverity, logging_sink
from .budget import CostBudgetGovernor, SpendRecord
from .config import MultiAccountConfig
from .cooldowns import Cooldown, CooldownRegistry
from .dispatch import (
    get_orchestrator, record_account_outcome, record_goal_outcome,
    recommend_orchestration_mode, report_account_success,
    reroute_failed_account, reset_orchestrator, select_dispatch_account,
)
from .evolution import SelfEvolutionLoop, SelfEvolutionStore
from .policy import PolicyLedger
from .routing import resolve_account_routing, routing_view
from .scheduler import AccountAwareScheduler
from .scoring import AccountScore, AccountScoreboard
from .status import (
    AccountHealth, AccountStatus, MultiAccountStatusMonitor, WindowStatus,
    merge_account_quotas, pool_account_quotas,
)
from .watchdog import RunWatchdog

__all__ = [
    "MultiAccountConfig",
    "MultiAccountOrchestrator",
    "MultiAccountStatusMonitor",
    "AccountAwareScheduler",
    "CooldownRegistry",
    "resolve_account_routing",
    "routing_view",
    "Cooldown",
    "AccountScoreboard",
    "AccountScore",
    "SelfEvolutionStore",
    "SelfEvolutionLoop",
    "AccountStatus",
    "WindowStatus",
    "AccountHealth",
    "pool_account_quotas",
    "merge_account_quotas",
    "CostBudgetGovernor",
    "SpendRecord",
    "AlertEngine",
    "Alert",
    "AlertSeverity",
    "logging_sink",
    "RunWatchdog",
    "PolicyLedger",
    "get_orchestrator",
    "reset_orchestrator",
    "recommend_orchestration_mode",
    "record_goal_outcome",
    "record_account_outcome",
    "report_account_success",
    "select_dispatch_account",
    "reroute_failed_account",
]


class MultiAccountOrchestrator:
    """Facade combining perception + scheduling + cost/alert/watchdog + evolution.

    Construction is cheap and side-effect free apart from one optional local
    read: when a ``store_path`` is given, cooldowns, scores, spend, alerts, the
    policy chain and the run clock are restored from it so a restart does not
    re-dispatch onto a quarantined account, forget the day's spend, or restart
    the run budget from zero.

    The five capabilities are composed here rather than in the call sites so a
    host only has to touch one object:

    =============  ==========================================================
    capability     entry point
    =============  ==========================================================
    状态感知        :meth:`observe` / :meth:`perceive`
    调度与容错      :meth:`select` / :meth:`on_failure` / :meth:`on_success`
    成本限制        :meth:`admit` / :meth:`settle`
    告警            :meth:`drain_alerts` / :meth:`alert_history`
    运行时长        :meth:`start_run` / :meth:`run_verdict` / :meth:`heartbeat`
    自进化          :meth:`record_account_outcome` / :meth:`evolve` /
                   :meth:`rollback_policy` / :meth:`policy_audit`
    =============  ==========================================================
    """

    def __init__(self, config: Optional[MultiAccountConfig] = None, *,
                 fetch_quotas: Optional[Any] = None,
                 clock: Any = time.time,
                 store_path: Optional[Path] = None,
                 alert_sink: Optional[Callable[[Alert], None]] = None) -> None:
        self.config = config or MultiAccountConfig.from_env()
        self.store = SelfEvolutionStore(self.config, path=store_path)
        persist = bool(self.config.persist_account_state)
        # Atomic account feedback: one lock, one write transaction, replay-safe by
        # ``outcome_id`` (main's guarantee). Budget settlement, the run heartbeat
        # and the policy step ride the same critical section below so a replayed
        # outcome cannot be counted twice anywhere.
        self._account_feedback_store = self.store if persist else SelfEvolutionStore(self.config)
        self._feedback_lock = threading.RLock()

        def _section(name: str) -> Optional[dict[str, Any]]:
            return self.store.section(name) if persist else None

        def _persister(name: str) -> Optional[Callable[[dict[str, Any]], None]]:
            return (lambda snapshot: self.store.patch(name, snapshot)) if persist else None

        self.cooldowns = CooldownRegistry(
            self.config, clock=clock, state=_section("cooldowns"),
            persist=_persister("cooldowns"))
        self.scores = AccountScoreboard(
            self.config, clock=clock, state=_section("accounts"),
            persist=_persister("accounts"))
        self.budget = CostBudgetGovernor(
            self.config, clock=clock, state=_section("budget"),
            persist=_persister("budget"))
        self.alerts = AlertEngine(
            self.config, clock=clock, sink=alert_sink, state=_section("alerts"),
            persist=_persister("alerts"))
        self.watchdog = RunWatchdog(
            self.config, clock=clock, state=_section("watchdog"),
            persist=_persister("watchdog"))
        self.policy = PolicyLedger(
            self.config, clock=clock, state=_section("policy"),
            persist=_persister("policy"))
        self.monitor = MultiAccountStatusMonitor(
            self.config, fetch_quotas=fetch_quotas, clock=clock)
        self.scheduler = AccountAwareScheduler(
            self.config, clock=clock, cooldowns=self.cooldowns,
            scores=self.scores if self.config.enable_account_scoring else None,
            budget=self.budget if self.config.cost_budget_enabled else None,
            policy=self.policy if self.config.policy_enabled else None)
        self.evolution = SelfEvolutionLoop(self.store, self.config, scoreboard=self.scores)
        # Who selects accounts. Resolved once, from configuration only, so a
        # flaky health probe can never silently change routing ownership.
        self.routing_owner = resolve_account_routing(self.config.account_routing)
        self._clock = clock
        self._attempts_since_policy = 0
        self._last_policy_decision: Optional[dict[str, Any]] = None
        # Latest perception, kept so an idle wait can answer "when does this
        # pool refill" without re-observing every loop.
        self._last_statuses: list[AccountStatus] = []

    def routing(self) -> dict:
        """Operator view: requested owner, effective owner, and why."""
        return routing_view(self.config.account_routing)

    # --- perception (domain B) -------------------------------------------------
    def perceive(self, snapshot: Optional[Mapping[str, Any]] = None,
                 *, now: Optional[float] = None) -> list[AccountStatus]:
        statuses = self.monitor.perceive(snapshot, now=now)
        self._last_statuses = list(statuses)
        return statuses

    def health_summary(self, statuses: Iterable[AccountStatus]) -> dict[str, Any]:
        return MultiAccountStatusMonitor.health_summary(statuses)

    def observe(self, snapshot: Optional[Mapping[str, Any]] = None, *,
                now: Optional[float] = None, events: Iterable[Mapping[str, Any]] = (),
                ) -> dict[str, Any]:
        """One perception cycle: statuses + health summary + newly raised alerts.

        This is the "持续感知" entry point: a host calls it on a timer, forwards
        whatever :meth:`drain_alerts` returns to its sink, and gets a consistent
        picture of account health, quota headroom and cost utilization in one
        object. Every sub-view is JSON-safe (``raw`` evidence stays host-side).
        """
        now = self._clock() if now is None else now
        statuses = self.perceive(snapshot, now=now)
        summary = MultiAccountStatusMonitor.health_summary(statuses)
        host_events = list(events)
        if self.monitor.last_error:
            # A broken telemetry source is not an empty pool: say so, otherwise
            # the operator sees "no accounts" and looks in the wrong place.
            host_events.append({
                "code": "perception_failed", "severity": "error", "subject": "pool",
                "message": f"额度观测失败，调度保持等待：{self.monitor.last_error}",
                "evidence": {"error": self.monitor.last_error}})
        raised = self.alerts.evaluate(
            statuses, budget=self.budget.status(now=now),
            cooldowns=self.cooldowns.active_streaks(now=now),
            account_scores=self.evolution.account_scores(),
            events=host_events, run_state=self.run_verdict(now=now), now=now)
        return {
            "accounts": [status.public_view() for status in statuses],
            "summary": summary,
            "budget": self.budget.status(now=now),
            "alerts": [alert.to_dict() for alert in raised],
            "run": self.run_verdict(now=now),
            "routing": self.routing(),
            "policy": self.policy.current(),
            "perception_error": self.monitor.last_error,
        }

    # --- scheduling / fault tolerance (C, D) -----------------------------------
    def select(self, statuses: Iterable[AccountStatus], *,
               small_task: bool = False,
               need: Optional[Mapping[str, Any]] = None,
               reset_task: bool = False) -> dict[str, Any]:
        observed = list(statuses)
        self._last_statuses = observed
        if reset_task:
            self.scheduler.reset_for_task()
        return self.scheduler.select(observed, small_task=small_task, need=need)

    def on_failure(self, statuses: Iterable[AccountStatus], *,
                   failed_ref: str, failure_kind: str, attempt: int,
                   small_task: bool = False) -> dict[str, Any]:
        decision = self.scheduler.on_failure(
            statuses, failed_ref=failed_ref, failure_kind=failure_kind,
            attempt=attempt, small_task=small_task)
        if decision.get("decision") == "dead_letter":
            # A terminal task is an operator fact, not just a scheduler state:
            # raise it once so the run does not fail silently.
            self.alerts.evaluate(events=[{
                "code": "task_dead_letter", "severity": "error",
                "subject": str(failed_ref), "message": "任务重路由次数用尽，已隔离留证",
                "evidence": decision.get("evidence") or {}}])
        return decision

    def on_success(self, account_ref: str) -> None:
        """A run finished on this account: drop its cooldown and failure streak."""
        self.scheduler.on_success(account_ref)

    def next_retry_in(self, *, now: Optional[float] = None) -> Optional[float]:
        """Seconds until capacity plausibly returns, or ``None``.

        This is the unattended coordinator's idle-wait hint. Three signals are
        merged, because they are the three ways a pool comes back:

        * an account's cooldown expiring after a failure,
        * an exhausted account's quota window resetting,
        * a cost ceiling rolling a spend record out of its window.

        If any account is currently usable the answer is ``None``: sleeping is
        for an empty pool only, and a stale "wait 40 minutes" hint must never
        make a working pool idle. A bounded run also caps the hint at its own
        remaining budget, so the loop re-evaluates before its deadline instead
        of oversleeping past it.
        """
        now = self._clock() if now is None else now
        if any(self._is_usable(status, now=now) for status in self._last_statuses):
            return None
        waits: list[float] = []
        cooldown_until = self.cooldowns.next_retry_at(now=now)
        if cooldown_until is not None:
            waits.append(max(0.0, cooldown_until - now))
        resets = [status.next_reset_at() for status in self._last_statuses]
        resets = [reset for reset in resets if reset is not None and reset > now]
        if resets:
            waits.append(min(resets) - now)
        budget_retry = self._budget_retry_at(now=now)
        if budget_retry is not None:
            waits.append(max(0.0, budget_retry - now))
        if not waits:
            return None
        hint = min(waits)
        remaining = self.watchdog.remaining_seconds(now=now)
        if remaining is not None:
            hint = min(hint, remaining)
        return max(0.0, hint)

    def _is_usable(self, status: AccountStatus, *, now: float) -> bool:
        """Whether this account could take at least a small task right now.

        A healthy account that is cooling down after a failure is *not* usable:
        that cooldown is precisely what the idle hint is supposed to wait out,
        and ignoring it would make the hint answer "no wait" while the pool is
        still blocked.
        """
        if self.cooldowns.is_cooling(status.account_ref, now=now):
            return False
        if status.health is AccountHealth.HEALTHY:
            return True
        if status.health is not AccountHealth.DEGRADED:
            return False
        headroom = status.headroom_pct
        # A DEGRADED account near its ceiling can still run a small task; that
        # is exactly what ``small_task_percent_ceiling`` encodes.
        return headroom is None or headroom > self.config.small_task_percent_ceiling

    def _budget_retry_at(self, *, now: float) -> Optional[float]:
        """When the cost ceiling could admit again, if it is the binding limit."""
        if not self.budget.enabled:
            return None
        decision = self.budget.admit(0.0, now=now)
        if decision.get("decision") != "deny":
            return None
        retry_at = decision.get("retry_at")
        return float(retry_at) if isinstance(retry_at, (int, float)) else None

    # --- cost ceiling (domain C: 成本限制) --------------------------------------
    def admit(self, forecast_units: Optional[float] = None, *,
              now: Optional[float] = None, account_ref: Optional[str] = None,
              reserve: bool = True) -> dict[str, Any]:
        """Ask the cost governor whether one attempt fits, reserving its forecast.

        The returned ``reservation`` token must be handed to :meth:`settle` when
        the attempt ends (success *or* failure) so the ceiling converges on real
        spend. A host that does not reserve still gets the admission verdict,
        but concurrent dispatch can then overshoot the ceiling.
        """
        return self.budget.admit(forecast_units, now=now, account_ref=account_ref,
                                 reserve=reserve)

    def settle(self, token: Optional[str], *, cost_units: Optional[float] = None,
               account_ref: Optional[str] = None, task_id: Optional[str] = None,
               now: Optional[float] = None) -> dict[str, Any]:
        """Convert a reservation into realised spend (unknown cost is not free)."""
        return self.budget.settle(token, actual_units=cost_units, account_ref=account_ref,
                                  task_id=task_id, now=now)

    def budget_status(self, *, now: Optional[float] = None) -> dict[str, Any]:
        return self.budget.status(now=now)

    # --- alerting (domain D: 告警) ---------------------------------------------
    def drain_alerts(self) -> list[Alert]:
        """Alerts raised since the last drain — the host's delivery point."""
        return self.alerts.drain()

    def alert_history(self) -> list[dict[str, Any]]:
        return self.alerts.history()

    def raise_alert(self, code: str, *, severity: str = "warning", subject: str = "host",
                    message: str = "", evidence: Optional[Mapping[str, Any]] = None,
                    now: Optional[float] = None) -> list[Alert]:
        """Host-supplied fact (e.g. a failed feedback callback) into the stream."""
        return self.alerts.evaluate(events=[{
            "code": code, "severity": severity, "subject": subject,
            "message": message or code, "evidence": dict(evidence or {})}], now=now)

    # --- run duration (domain D: 运行时长) --------------------------------------
    def start_run(self, *, now: Optional[float] = None) -> dict[str, Any]:
        return self.watchdog.start(now=now)

    def heartbeat(self, *, now: Optional[float] = None) -> None:
        self.watchdog.heartbeat(now=now)

    def run_verdict(self, *, now: Optional[float] = None) -> dict[str, Any]:
        """``continue`` / ``conclude`` / ``stop`` for the current run."""
        return self.watchdog.check(now=now)

    def run_status(self, *, now: Optional[float] = None) -> dict[str, Any]:
        return self.watchdog.status(now=now)

    # --- self-evolution (E) ----------------------------------------------------
    def record_outcome(self, outcome: Mapping[str, Any], *,
                       now: Optional[float] = None) -> dict[str, Any]:
        return self.evolution.record_outcome(outcome, now=now)

    def record_account_outcome(self, account_ref: str, *, ok: bool,
                               cost_units: Optional[float] = None,
                               wall_seconds: Optional[float] = None,
                               failure_kind: Optional[str] = None,
                               outcome_id: Optional[str] = None,
                               budget_token: Optional[str] = None,
                               task_id: Optional[str] = None,
                               now: Optional[float] = None) -> Optional[dict[str, Any]]:
        """One finished attempt feeds *every* loop.

        Scheduling: a failure cools the account down (quarantine for
        account-level errors), a success clears its quiet time. Ranking: the
        reliability/cost/latency EWMA in :mod:`.scoring`. Cost: the reservation
        is settled against real spend. Duration: the watchdog records progress.
        Evolution: once ``policy_min_samples`` new attempts have accumulated the
        policy chain may take one bounded step.

        ``outcome_id`` keeps the whole transition replay-safe: the same terminal
        receipt cannot double-train the ranking, double-count a policy sample or
        release a budget reservation twice. A replayed receipt returns the
        originally stored view verbatim.
        """
        with self._feedback_lock:
            if not self.config.persist_account_state:
                self._account_feedback_store.patch("accounts", self.scores.snapshot())
                self._account_feedback_store.patch("cooldowns", self.cooldowns.snapshot())
            result = self._account_feedback_store.record_account_feedback(
                account_ref, ok=ok, cost_units=cost_units, wall_seconds=wall_seconds,
                failure_kind=failure_kind, outcome_id=outcome_id,
                now=self._clock() if now is None else now)
            self.cooldowns.load(result["cooldowns"])
            self.scores.load(result["accounts"])
            if result.get("replayed"):
                # The receipt is already accounted for; do not settle, heartbeat
                # for progress or advance the policy sample counter again.
                return result["view"]
            if budget_token is not None or cost_units is not None:
                self.settle(budget_token, cost_units=cost_units, account_ref=account_ref,
                            task_id=task_id, now=now)
            self.watchdog.heartbeat(now=now)
            self._attempts_since_policy += 1
            decision = None
            if self._attempts_since_policy >= self.config.policy_min_samples:
                self._attempts_since_policy = 0
                decision = self.evolve(now=now)
            view = result["view"]
            if decision is not None and view is not None:
                return {**view, "policy": decision}
            return view

    def evolve(self, *, now: Optional[float] = None) -> dict[str, Any]:
        """Evaluate the policy rules on the pool-wide failure profile.

        Called automatically every ``policy_min_samples`` attempts; exposed so an
        operator (or a test) can force one evaluation.
        """
        decision = self.policy.observe(self.scores.failure_profile(), now=now)
        if decision.get("changed"):
            self.alerts.evaluate(events=[{
                "code": "policy_changed", "severity": "info", "subject": "policy",
                "message": f"调度权重已调整：{decision.get('reason')}（v{decision.get('version')}）",
                "evidence": {"changed_keys": decision.get("changed_keys"),
                             "reason": decision.get("reason")}}], now=now)
        self._last_policy_decision = decision
        return decision

    def last_policy_decision(self) -> Optional[dict[str, Any]]:
        return self._last_policy_decision

    def account_scores(self) -> dict[str, dict[str, Any]]:
        return self.evolution.account_scores()

    def failure_profile(self) -> dict[str, Any]:
        return self.scores.failure_profile()

    def recommend_mode(self, size_estimate: Mapping[str, Any], *,
                       pin: Any = None) -> dict[str, Any]:
        return self.evolution.recommend_mode(size_estimate, pin=pin)

    def calibration_feedback(self, before: Any, after: Any,
                            settlements: Iterable[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
        return self.evolution.calibration_feedback(before, after, settlements)

    # --- policy audit / rollback (domain E: 可审计、可回滚) ---------------------
    def policy_view(self) -> dict[str, Any]:
        return self.policy.current()

    def policy_audit(self) -> list[dict[str, Any]]:
        return self.policy.audit()

    def rollback_policy(self, version: int = 0, *,
                        now: Optional[float] = None,
                        reason: str = "operator_rollback") -> dict[str, Any]:
        """Restore an earlier policy version (``0`` = configured baseline)."""
        result = self.policy.rollback(version, now=now, reason=reason)
        if result.get("changed"):
            self.alerts.evaluate(events=[{
                "code": "policy_rolled_back", "severity": "warning", "subject": "policy",
                "message": f"调度策略回滚至 v{version}（{reason}）",
                "evidence": {"effective": result.get("effective")}}], now=now)
        return result

    # --- reused primitive (domain A drop-in fix) -------------------------------
    @staticmethod
    def pool_account_quotas(snapshot: Mapping[str, Any], *,
                           now: Optional[float] = None) -> dict[str, dict[str, Any]]:
        return pool_account_quotas(snapshot, now=now)
