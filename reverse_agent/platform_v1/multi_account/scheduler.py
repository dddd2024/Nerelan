"""Account-aware scheduling and bounded fault tolerance.

Domain C (stable execution under quota/account/task failure) and domain D
(unattended, long-running). This module is pure decision logic over
:class:`AccountStatus` objects — it holds no credentials, does not itself
dispatch, and never becomes a second orchestration spine. Real dispatch stays in
:mod:`trusted_host` and the reservation gate in :mod:`quota_reservation`; the
scheduler only decides *which account* and *what to do when it fails*.

Failure modes handled:
  - ``quota_exhausted``  : the chosen account hit a 100% / rejected window.
  - ``account_abnormal`` : account-level error (unauthorized, rate-limit error).
  - ``task_failed``      : the run failed for a task reason (not an account fault).

Each reroute respects ``reroute_max_attempts``; once exceeded the task is sent
to ``dead_letter`` (isolated with evidence) when enabled, otherwise ``hold``.

Two additions make a long unattended run viable:

* every ``hold`` carries ``retry_at`` — the earliest moment capacity can
  plausibly return (a cooldown expiring or a quota window resetting). The
  coordinator sleeps until then instead of polling.
* cooldowns live in :class:`~.cooldowns.CooldownRegistry`, so they escalate on
  repeated failures and survive a restart, instead of resetting to the shortest
  delay after every crash.

Ordering is *health first*: feedback from :mod:`.scoring` can only re-order
accounts inside one health class, never promote a degraded account over a
healthy one.
"""
from __future__ import annotations

import time
from typing import Any, Iterable, Mapping, Optional

from .cooldowns import CooldownRegistry
from .config import MultiAccountConfig
from .scoring import AccountScoreboard
from .status import AccountHealth, AccountStatus


def _materialize(statuses: Iterable[AccountStatus]) -> list[AccountStatus]:
    """One pass over the input: callers may pass a generator or a view."""
    return list(statuses)


def _initial_delay(config: MultiAccountConfig, failure_kind: str) -> float:
    """First cooldown for a failure kind, matching the registry's streak-1 rule."""
    floor = (config.abnormal_account_cooldown_seconds
             if failure_kind == "account_abnormal" else config.reroute_cooldown_seconds)
    return float(min(config.failure_backoff_max_seconds,
                     max(config.failure_backoff_base_seconds, floor)))


def _effective_excluded(excluded: Optional[Mapping[str, float]], *,
                        cooldowns: Optional[CooldownRegistry],
                        now: float) -> dict[str, float]:
    """Merge explicit (per-call) exclusions with the shared cooldown registry."""
    merged = dict(excluded or {})
    if cooldowns is not None:
        for ref, until in cooldowns.active_map(now=now).items():
            merged[ref] = max(until, merged.get(ref, 0.0))
    return merged


def _next_capacity_at(statuses: Iterable[AccountStatus],
                      excluded: Mapping[str, float], *,
                      now: float) -> Optional[float]:
    """Earliest plausible moment an account becomes usable again, or ``None``.

    Considers only *future* cooldown expiries and quota resets; a hold with no
    such signal means "wait for fresh observation", not "poll in a tight loop".
    """
    candidates = [until for until in excluded.values() if until > now]
    for status in statuses:
        for window in status.windows:
            if window.unlimited or window.reset_passed or window.resets_at is None:
                continue
            if window.resets_at > now:
                candidates.append(window.resets_at)
    return min(candidates) if candidates else None


def _bonus(status: AccountStatus, *,
           scores: Optional[AccountScoreboard],
           cost_reference: Optional[float],
           latency_reference: Optional[float]) -> float:
    if scores is None:
        return 0.0
    return scores.bonus(status.account_ref, cost_reference=cost_reference,
                        latency_reference=latency_reference)


def _eligible(statuses: list[AccountStatus], *, config: MultiAccountConfig,
              now: float, small_task: bool,
              excluded: Mapping[str, float]) -> list[AccountStatus]:
    """Accounts the scheduler may use right now, sorted best-first."""
    result: list[AccountStatus] = []
    for s in statuses:
        if s.account_ref in excluded and excluded[s.account_ref] > now:
            continue
        if s.health in (AccountHealth.HEALTHY, AccountHealth.DEGRADED):
            result.append(s)
        elif small_task and s.health is AccountHealth.STALE:
            # A conservative small task may use a stale-but-not-exhausted account.
            result.append(s)
    return result


def _order(eligible: list[AccountStatus], *, scores: Optional[AccountScoreboard]) -> tuple[list[AccountStatus], bool]:
    """Order by health, then by headroom adjusted by measured feedback."""
    cost_reference, latency_reference = scores.references() if scores is not None else (None, None)
    ranked: list[tuple[tuple[Any, ...], AccountStatus]] = []
    bonus_applied = False
    for s in eligible:
        health_rank = {AccountHealth.HEALTHY: 0, AccountHealth.DEGRADED: 1,
                       AccountHealth.STALE: 2}.get(s.health, 3)
        headroom = s.headroom_pct if s.headroom_pct is not None else -1.0
        bonus = _bonus(s, scores=scores, cost_reference=cost_reference,
                       latency_reference=latency_reference)
        bonus_applied = bonus_applied or bool(bonus)
        ranked.append(((health_rank, -(headroom + bonus), len(s.anomaly_flags),
                        s.freshness_age or 1e18), s))
    ranked.sort(key=lambda item: item[0])
    return [s for _, s in ranked], bonus_applied


def select_account(statuses: Iterable[AccountStatus], *,
                   config: MultiAccountConfig, now: float,
                   small_task: bool = False,
                   need: Optional[Mapping[str, Any]] = None,
                   excluded: Optional[Mapping[str, float]] = None,
                   cooldowns: Optional[CooldownRegistry] = None,
                   scores: Optional[AccountScoreboard] = None) -> dict[str, Any]:
    """Pick the best account, or decide to hold / dead-letter when none fit.

    ``need`` is optional and only used to confirm a ``small_task`` truly is
    small (its p80 percentage must sit under ``small_task_percent_ceiling``).
    ``scores`` is optional: with it, measured reliability/cost/latency re-order
    equally-healthy accounts; without it the decision is pure headroom.
    """
    observed = _materialize(statuses)
    effective = _effective_excluded(excluded, cooldowns=cooldowns, now=now)
    candidates = _eligible(observed, config=config, now=now, small_task=small_task,
                           excluded=effective)
    if not candidates:
        if not observed:
            return {"decision": "hold", "account_ref": None, "provider": None,
                    "reason": "no_accounts_observed",
                    "evidence": {"eligible": 0}, "retry_at": None}
        exhausted = any(s.health is AccountHealth.EXHAUSTED for s in observed)
        abnormal = any(s.health is AccountHealth.ABNORMAL for s in observed)
        cooling = [s for s in observed if s.account_ref in effective and effective[s.account_ref] > now]
        if cooling and not exhausted and not abnormal:
            reason = "accounts_cooling_down"
        else:
            reason = "all_accounts_exhausted" if exhausted else (
                "all_accounts_abnormal" if abnormal else "no_eligible_account")
        return {"decision": "hold", "account_ref": None, "provider": None,
                "reason": reason,
                "evidence": {"eligible": 0, "observed": len(observed),
                             "cooling_down": sorted(s.account_ref for s in cooling)},
                "retry_at": _next_capacity_at(observed, effective, now=now)}

    ordered, bonus_applied = _order(candidates, scores=scores)
    best = ordered[0]
    cost_reference, latency_reference = _refs(scores)
    if small_task and need is not None:
        p80 = need.get("p80_percent")
        if not (isinstance(p80, (int, float)) and p80 <= config.small_task_percent_ceiling):
            return {"decision": "hold", "account_ref": None, "provider": None,
                    "reason": "small_task_ceiling_exceeded",
                    "evidence": {"p80_percent": p80,
                                 "ceiling": config.small_task_percent_ceiling},
                    "retry_at": None}
    return {"decision": "use", "account_ref": best.account_ref,
            "provider": best.provider,
            "reason": "best_composite" if bonus_applied else "best_headroom",
            "evidence": {"health": best.health.value,
                         "headroom_pct": best.headroom_pct,
                         "anomaly_flags": best.anomaly_flags,
                         "score_bonus": round(_bonus(
                             best, scores=scores, cost_reference=cost_reference,
                             latency_reference=latency_reference), 2),
                         "alternatives": [s.account_ref for s in ordered[1:4]]},
            "retry_at": None}


def _refs(scores: Optional[AccountScoreboard]) -> tuple[Optional[float], Optional[float]]:
    return scores.references() if scores is not None else (None, None)


def next_after_failure(statuses: Iterable[AccountStatus], *,
                       config: MultiAccountConfig, failed_ref: str,
                       failure_kind: str, attempt: int, now: float,
                       small_task: bool = False,
                       excluded: Optional[Mapping[str, float]] = None,
                       cooldowns: Optional[CooldownRegistry] = None,
                       scores: Optional[AccountScoreboard] = None) -> dict[str, Any]:
    """Decide what to do after ``failed_ref`` failed on this attempt.

    Returns one of:
      - ``reroute``    : move to ``next_account_ref`` (attempt+1).
      - ``dead_letter``: terminal — isolate with evidence (only if enabled).
      - ``hold``       : wait for capacity to return; ``retry_at`` says until when.

    ``attempt`` is the 1-based count of accounts already tried. When a
    ``cooldowns`` registry is supplied the failure is recorded there (escalating
    and restart-safe); otherwise a first-failure delay is applied locally.
    """
    observed = _materialize(statuses)
    effective = dict(excluded or {})
    if cooldowns is not None:
        recorded = cooldowns.record_failure(failed_ref, failure_kind, now=now)
        effective[failed_ref] = recorded.until
    else:
        effective[failed_ref] = now + _initial_delay(config, failure_kind)

    if attempt >= config.reroute_max_attempts:
        terminal = {
            "next_account_ref": None,
            "excluded": sorted(effective),
            "excluded_state": effective,
            "evidence": {"attempt": attempt, "max": config.reroute_max_attempts,
                         "failure_kind": failure_kind},
            "retry_at": _next_capacity_at(observed, effective, now=now),
        }
        if config.dead_letter_enabled:
            return {"decision": "dead_letter",
                    "reason": f"max_reroutes_exceeded:{failure_kind}", **terminal}
        return {"decision": "hold", "reason": "max_reroutes_exceeded_hold", **terminal}

    decision = select_account(observed, config=config, now=now, small_task=small_task,
                              excluded=effective, cooldowns=cooldowns, scores=scores)
    if decision["decision"] == "use":
        return {"decision": "reroute", "next_account_ref": decision["account_ref"],
                "provider": decision["provider"], "reason": "rerouted_to_next_best",
                "excluded": sorted(effective), "excluded_state": effective,
                "evidence": decision["evidence"],
                "retry_at": None}
    return {"decision": "hold", "next_account_ref": None,
            "reason": decision["reason"], "excluded": sorted(effective),
            "excluded_state": effective,
            "evidence": decision["evidence"],
            "retry_at": decision.get("retry_at")}


class AccountAwareScheduler:
    """Stateful wrapper: shared account cooldowns plus per-task quiet time.

    ``cooldowns`` is normally the process-wide registry, so a quarantine is
    honoured by every task and survives restarts. ``reset_for_task()`` clears
    only transient quiet time — an account-level quarantine is not a task
    property and must not be lifted by starting the next task.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Any = time.time,
                 cooldowns: Optional[CooldownRegistry] = None,
                 scores: Optional[AccountScoreboard] = None) -> None:
        self._config = config
        self._clock = clock
        self._cooldowns = cooldowns if cooldowns is not None else CooldownRegistry(
            config, clock=clock)
        self._scores = scores
        self._excluded: dict[str, float] = {}

    @property
    def cooldowns(self) -> CooldownRegistry:
        return self._cooldowns

    def reset_for_task(self) -> None:
        self._excluded = {}
        self._cooldowns.clear_transient()

    def clear_quarantine(self) -> None:
        """Owner-level escape hatch: trust every account again right now."""
        self._excluded = {}
        self._cooldowns.clear_all()

    def select(self, statuses: Iterable[AccountStatus], *,
               small_task: bool = False,
               need: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        return select_account(statuses, config=self._config, now=self._clock(),
                              small_task=small_task, need=need,
                              excluded=self._excluded, cooldowns=self._cooldowns,
                              scores=self._scores)

    def on_failure(self, statuses: Iterable[AccountStatus], *,
                   failed_ref: str, failure_kind: str,
                   attempt: int, small_task: bool = False) -> dict[str, Any]:
        result = next_after_failure(statuses, config=self._config,
                                    failed_ref=failed_ref, failure_kind=failure_kind,
                                    attempt=attempt, now=self._clock(),
                                    small_task=small_task, excluded=self._excluded,
                                    cooldowns=self._cooldowns, scores=self._scores)
        # Persist the exclusion the helper computed so the next select() honours it.
        self._excluded.update(result.get("excluded_state", {}))
        return result

    def on_success(self, account_ref: str) -> None:
        """Feedback: a working account loses its quiet time and streak."""
        self._cooldowns.record_success(account_ref)
        self._excluded.pop(account_ref, None)
