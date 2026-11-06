"""Multi-account orchestration brain: perception, scheduling and self-evolution.

This package is the wiring layer the planning spec calls for. It reuses —
rather than rewrites — the mature assets already in the repository:

  - account/quota observation : :func:`model_access.subscription_quota.magpie_account_quotas`
  - reservation / admission    : :mod:`quota_reservation`
  - break-even decision core   : :mod:`orchestration_selector`
  - durable / unattended runtime : :mod:`durable_execution`, :mod:`unattended_coordinator`

What it *adds* (and only what was missing):
  - a centralized, validated config (:mod:`.config`),
  - a status-perception layer that keeps *every* account instead of one per
    provider (:mod:`.status`, with :func:`pool_account_quotas` as the drop-in
    fix for the ``_merge_magpie_quotas`` defect),
  - an account-aware scheduler with bounded reroute / dead-letter
    (:mod:`.scheduler`),
  - a persistence + feedback self-evolution loop (:mod:`.evolution`).

Nothing here holds credentials or spins up a second orchestration spine.
"""
from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .config import MultiAccountConfig
from .cooldowns import Cooldown, CooldownRegistry
from .dispatch import (
    get_orchestrator, record_account_outcome, record_goal_outcome,
    recommend_orchestration_mode, report_account_success,
    reroute_failed_account, reset_orchestrator, select_dispatch_account,
)
from .evolution import SelfEvolutionLoop, SelfEvolutionStore
from .routing import resolve_account_routing, routing_view
from .scheduler import AccountAwareScheduler
from .scoring import AccountScore, AccountScoreboard
from .status import (
    AccountHealth, AccountStatus, MultiAccountStatusMonitor, WindowStatus,
    merge_account_quotas, pool_account_quotas,
)

__all__ = [
    "MultiAccountConfig",
    "MultiAccountOrchestrator",
    "MultiAccountStatusMonitor",
    "AccountAwareScheduler",
    "CooldownRegistry",
    "resolve_account_routing",
    "routing_view",
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
    """Facade combining perception + scheduling + self-evolution.

    Construction is cheap and side-effect free apart from one optional local
    read: when a ``store_path`` is given, cooldowns and account scores are
    restored from it so a restart does not re-dispatch onto a quarantined
    account. The ledger is created lazily on first write.
    """

    def __init__(self, config: Optional[MultiAccountConfig] = None, *,
                 fetch_quotas: Optional[Any] = None,
                 clock: Any = time.time,
                 store_path: Optional[Path] = None) -> None:
        self.config = config or MultiAccountConfig.from_env()
        self.store = SelfEvolutionStore(self.config, path=store_path)
        persist = bool(self.config.persist_account_state)
        self._account_feedback_store = self.store if persist else SelfEvolutionStore(self.config)
        self._feedback_lock = threading.RLock()
        self.cooldowns = CooldownRegistry(
            self.config, clock=clock,
            state=self.store.section("cooldowns") if persist else None,
            persist=(lambda snapshot: self.store.patch("cooldowns", snapshot)) if persist else None)
        self.scores = AccountScoreboard(
            self.config, clock=clock,
            state=self.store.section("accounts") if persist else None,
            persist=(lambda snapshot: self.store.patch("accounts", snapshot)) if persist else None)
        self.monitor = MultiAccountStatusMonitor(
            self.config, fetch_quotas=fetch_quotas, clock=clock)
        self.scheduler = AccountAwareScheduler(
            self.config, clock=clock, cooldowns=self.cooldowns,
            scores=self.scores if self.config.enable_account_scoring else None)
        self.evolution = SelfEvolutionLoop(self.store, self.config, scoreboard=self.scores)
        # Who selects accounts. Resolved once, from configuration only, so a
        # flaky health probe can never silently change routing ownership.
        self.routing_owner = resolve_account_routing(self.config.account_routing)
        self._clock = clock

    def routing(self) -> dict:
        """Operator view: requested owner, effective owner, and why."""
        return routing_view(self.config.account_routing)

    # --- perception (domain B) -------------------------------------------------
    def perceive(self, snapshot: Optional[Mapping[str, Any]] = None,
                 *, now: Optional[float] = None) -> list[AccountStatus]:
        return self.monitor.perceive(snapshot, now=now)

    def health_summary(self, statuses: Iterable[AccountStatus]) -> dict[str, Any]:
        return MultiAccountStatusMonitor.health_summary(statuses)

    # --- scheduling / fault tolerance (C, D) -----------------------------------
    def select(self, statuses: Iterable[AccountStatus], *,
               small_task: bool = False,
               need: Optional[Mapping[str, Any]] = None,
               reset_task: bool = False) -> dict[str, Any]:
        if reset_task:
            self.scheduler.reset_for_task()
        return self.scheduler.select(statuses, small_task=small_task, need=need)

    def on_failure(self, statuses: Iterable[AccountStatus], *,
                   failed_ref: str, failure_kind: str, attempt: int,
                   small_task: bool = False) -> dict[str, Any]:
        return self.scheduler.on_failure(
            statuses, failed_ref=failed_ref, failure_kind=failure_kind,
            attempt=attempt, small_task=small_task)

    def on_success(self, account_ref: str) -> None:
        """A run finished on this account: drop its cooldown and failure streak."""
        self.scheduler.on_success(account_ref)

    def next_retry_in(self, *, now: Optional[float] = None) -> Optional[float]:
        """Seconds until the earliest account cooldown expires, or ``None``.

        This is the unattended coordinator's idle-wait hint: with every account
        cooling down there is nothing to dispatch, so waiting until the soonest
        expiry is cheaper and quieter than polling every second.
        """
        now = self._clock() if now is None else now
        until = self.cooldowns.next_retry_at(now=now)
        return None if until is None else max(0.0, until - now)

    # --- self-evolution (E) ----------------------------------------------------
    def record_outcome(self, outcome: Mapping[str, Any], *,
                       now: Optional[float] = None) -> dict[str, Any]:
        return self.evolution.record_outcome(outcome, now=now)

    def record_account_outcome(self, account_ref: str, *, ok: bool,
                               cost_units: Optional[float] = None,
                               wall_seconds: Optional[float] = None,
                               failure_kind: Optional[str] = None,
                               outcome_id: Optional[str] = None,
                               now: Optional[float] = None) -> Optional[dict[str, Any]]:
        """One finished attempt feeds *both* loops.

        Scheduling: a failure cools the account down (quarantine for
        account-level errors), a success clears its quiet time. Ranking: the
        reliability/cost/latency EWMA in :mod:`.scoring`.
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
            return result["view"]

    def account_scores(self) -> dict[str, dict[str, Any]]:
        return self.evolution.account_scores()

    def recommend_mode(self, size_estimate: Mapping[str, Any], *,
                       pin: Any = None) -> dict[str, Any]:
        return self.evolution.recommend_mode(size_estimate, pin=pin)

    def calibration_feedback(self, before: Any, after: Any,
                            settlements: Iterable[Mapping[str, Any]]) -> Optional[dict[str, Any]]:
        return self.evolution.calibration_feedback(before, after, settlements)

    # --- reused primitive (domain A drop-in fix) -------------------------------
    @staticmethod
    def pool_account_quotas(snapshot: Mapping[str, Any], *,
                           now: Optional[float] = None) -> dict[str, dict[str, Any]]:
        return pool_account_quotas(snapshot, now=now)
