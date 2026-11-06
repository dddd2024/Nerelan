"""Account-level self-evolution: bounded EWMA feedback that re-orders equal accounts.

The existing self-evolution loop (:mod:`.evolution`) learns at *mode* level —
single agent vs team. That leaves the per-account question unanswerable: two
accounts with the same headroom are not equally good, because one of them may
have failed the last four tasks on it, or cost twice as much per accepted task.

This module keeps a small smoothed profile per account — success ratio, mean
cost units, mean wall time, failure-kind counts — and exposes it as a small
*bonus* in headroom-equivalent points. It is deliberately not a learning
framework:

* bounded (one record per account, capped count, prunable),
* explainable (a weighted sum of three named terms, visible in the decision
  evidence),
* rollback-able (clear the state document and the ranking is purely headroom),
* non-decisive (the scheduler applies it only *inside* one health class, so it
  can never promote an unhealthy account over a healthy one).

Smoothing is a plain EWMA with ``score_ewma_alpha``; a sample is discounted
until the account has a few observations, so one lucky run cannot dominate.

The pool-wide aggregate (:meth:`AccountScoreboard.failure_profile`) is the only
input the self-evolution policy chain (:mod:`.policy`) steers on. It sums
*counts* rather than averaging ratios, so one account with three attempts cannot
outweigh another with three hundred.
"""
from __future__ import annotations

import math
import sys
import time
from typing import Any, Callable, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from .config import MultiAccountConfig

# How many observations an account needs before its score counts in full.
CONFIDENCE_ATTEMPTS = 3
# Accounts idle for longer than this are pruned on write, keeping the document bounded.
PRUNE_HORIZON_SECONDS = 30 * 24 * 3600
MAX_TRACKED_ACCOUNTS = 200
# Cumulative totals are exact until they approach the float ceiling; beyond that
# they saturate. Two accounts reporting 1e308 per attempt would otherwise sum to
# inf, and an inf in the persisted document makes the whole feedback snapshot
# unusable (json and every downstream comparison reject it). Saturation happens
# only at values where "exact" has no meaning left, and keeps the document finite.
_MAX_TOTAL = sys.float_info.max / 4.0


def _accumulate(total: float, value: float) -> float:
    combined = total + value
    return combined if combined < _MAX_TOTAL else _MAX_TOTAL


class AccountScore(BaseModel):
    """Measured, smoothed behaviour of one account."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    account_ref: str
    attempts: int = Field(0, ge=0, strict=True)
    successes: int = Field(0, ge=0, strict=True)
    reliability: float = Field(0.5, ge=0, le=1)
    mean_cost_units: Optional[float] = Field(None, ge=0)
    mean_wall_seconds: Optional[float] = Field(None, ge=0)
    cost_samples: int = Field(0, ge=0, strict=True)
    latency_samples: int = Field(0, ge=0, strict=True)
    consecutive_failures: int = Field(0, ge=0, strict=True)
    last_failure_kind: Optional[str] = None
    # Cumulative totals. The pool trend needs a true per-attempt average, which
    # a median of per-account means cannot give: that median moves whenever a
    # newly-active account joins, even if nothing actually got more expensive.
    cost_total: float = Field(0.0, ge=0)
    wall_total: float = Field(0.0, ge=0)
    # Why this account failed, counted — the input the policy loop steers on.
    # Counts (not ratios) so a pool-wide profile can be summed unambiguously.
    failure_kinds: dict[str, int] = Field(default_factory=dict)
    first_seen_at: Optional[float] = None
    updated_at: Optional[float] = None

    def to_state(self) -> dict[str, Any]:
        return self.model_dump()

    def public_view(self) -> dict[str, Any]:
        """Dashboard-facing shape (no internal streaks)."""
        return {
            "account_ref": self.account_ref,
            "attempts": self.attempts,
            "successes": self.successes,
            "reliability": round(self.reliability, 4),
            "mean_cost_units": self.mean_cost_units,
            "mean_wall_seconds": self.mean_wall_seconds,
            "cost_samples": self.cost_samples,
            "latency_samples": self.latency_samples,
            "last_failure_kind": self.last_failure_kind,
            "failure_kinds": dict(self.failure_kinds),
            "updated_at": self.updated_at,
        }


def _ewma(previous: Optional[float], sample: float, alpha: float) -> float:
    return sample if previous is None else (1.0 - alpha) * previous + alpha * sample


def _measurement(value: Any) -> Optional[float]:
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) and number >= 0 else None


class AccountScoreboard:
    """Per-account EWMA store with an optional persistence callback."""

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._persist = persist
        self._scores: dict[str, AccountScore] = {}
        self.load(state)

    # --- feedback -------------------------------------------------------------
    def observe(self, account_ref: str, *, ok: bool,
                cost_units: Optional[float] = None,
                wall_seconds: Optional[float] = None,
                failure_kind: Optional[str] = None,
                now: Optional[float] = None) -> AccountScore:
        """Fold one run outcome into the account's smoothed profile."""
        now = self._clock() if now is None else now
        if type(ok) is not bool:
            raise ValueError("ok must be a boolean")
        if _measurement(now) is None:
            raise ValueError("feedback time must be finite and non-negative")
        self.prune(now=now)
        alpha = self._config.score_ewma_alpha
        score = self._scores.get(account_ref) or AccountScore(
            account_ref=account_ref, first_seen_at=now)
        score.attempts += 1
        if ok:
            score.successes += 1
            score.consecutive_failures = 0
        else:
            score.consecutive_failures += 1
            kind = failure_kind or "unknown"
            score.last_failure_kind = kind
            score.failure_kinds[kind] = score.failure_kinds.get(kind, 0) + 1
        score.reliability = _ewma(score.reliability, 1.0 if ok else 0.0, alpha)
        cost = _measurement(cost_units)
        wall = _measurement(wall_seconds)
        if cost is not None:
            score.mean_cost_units = _ewma(score.mean_cost_units, cost, alpha)
            score.cost_total = _accumulate(score.cost_total, cost)
            score.cost_samples += 1
        if wall is not None:
            score.mean_wall_seconds = _ewma(score.mean_wall_seconds, wall, alpha)
            score.wall_total = _accumulate(score.wall_total, wall)
            score.latency_samples += 1
        score.updated_at = now
        self._scores[account_ref] = score
        self.prune(now=now)
        self._save()
        return score

    # --- read -----------------------------------------------------------------
    def get(self, account_ref: str) -> Optional[AccountScore]:
        return self._scores.get(account_ref)

    def scores(self) -> dict[str, AccountScore]:
        return dict(self._scores)

    def has_evidence(self, account_ref: str) -> bool:
        score = self._scores.get(account_ref)
        return bool(score and score.attempts)

    def failure_profile(self) -> dict[str, Any]:
        """Pool-wide outcome profile: the single input the policy loop steers on.

        ``cost_units`` and ``wall_seconds`` are true per-attempt averages, so the
        trend stays comparable while the set of active accounts changes.
        """
        attempts = sum(s.attempts for s in self._scores.values())
        successes = sum(s.successes for s in self._scores.values())
        kinds: dict[str, int] = {}
        for score in self._scores.values():
            for kind, count in score.failure_kinds.items():
                kinds[kind] = kinds.get(kind, 0) + int(count)
        cost_total = sum(s.cost_total for s in self._scores.values())
        cost_samples = sum(s.cost_samples for s in self._scores.values())
        wall_total = sum(s.wall_total for s in self._scores.values())
        wall_samples = sum(s.latency_samples for s in self._scores.values())
        return {
            "attempts": attempts,
            "successes": successes,
            "success_rate": round(successes / attempts, 4) if attempts else None,
            "failure_kinds": kinds,
            "cost_units": round(cost_total / cost_samples, 6) if cost_samples else None,
            "wall_seconds": round(wall_total / wall_samples, 3) if wall_samples else None,
            "accounts": len(self._scores),
        }

    def references(self) -> tuple[Optional[float], Optional[float]]:
        """Median cost and wall time across accounts, used to normalize the penalties.

        Normalizing against the observed median keeps the weights unit-free: an
        account is penalized for being expensive *relative to its peers*, so no
        absolute currency or token scale has to be configured.
        """
        costs = [s.mean_cost_units for s in self._scores.values() if s.mean_cost_units is not None]
        walls = [s.mean_wall_seconds for s in self._scores.values() if s.mean_wall_seconds is not None]
        return _median(costs), _median(walls)

    def bonus(self, account_ref: str, *,
              cost_reference: Optional[float] = None,
              latency_reference: Optional[float] = None,
              cap: Optional[float] = None) -> float:
        """Headroom-equivalent points this account earns (or loses) from feedback.

        ``cap`` bounds ``|bonus|``; the policy loop uses it to make sure learned
        preference can never dominate the headroom signal it is only meant to
        refine (``cap=0`` therefore means "rank by headroom alone").
        """
        score = self._scores.get(account_ref)
        if score is None or not score.attempts:
            return 0.0
        config = self._config
        points = config.reliability_weight * (score.reliability - 0.5) * 2.0
        if cost_reference is not None and score.mean_cost_units is not None:
            ratio = (min(1.0, score.mean_cost_units / cost_reference) if cost_reference > 0
                     else float(score.mean_cost_units > 0))
            points -= config.cost_weight * ratio
        if latency_reference is not None and score.mean_wall_seconds is not None:
            ratio = (min(1.0, score.mean_wall_seconds / latency_reference) if latency_reference > 0
                     else float(score.mean_wall_seconds > 0))
            points -= config.latency_weight * ratio
        confidence = min(1.0, score.attempts / CONFIDENCE_ATTEMPTS)
        points *= confidence
        if cap is not None:
            points = min(float(cap), max(-float(cap), points))
        return points

    # --- maintenance ----------------------------------------------------------
    def prune(self, *, now: Optional[float] = None) -> int:
        now = self._clock() if now is None else now
        stale = [ref for ref, s in self._scores.items()
                 if s.updated_at is not None and now - s.updated_at > PRUNE_HORIZON_SECONDS]
        for ref in stale:
            del self._scores[ref]
        overflow = len(self._scores) - MAX_TRACKED_ACCOUNTS
        if overflow > 0:
            oldest = sorted(self._scores.values(),
                            key=lambda s: (s.updated_at or 0.0, s.attempts))[:overflow]
            for score in oldest:
                self._scores.pop(score.account_ref, None)
            stale.extend(score.account_ref for score in oldest)
        return len(stale)

    def reset(self) -> None:
        self._scores.clear()
        self._save()

    # --- persistence ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {ref: score.to_state() for ref, score in sorted(self._scores.items())}

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        self._scores = {}
        if not isinstance(state, Mapping):
            return
        for ref, raw in state.items():
            if not isinstance(ref, str) or not isinstance(raw, Mapping):
                continue
            try:
                self._scores[ref] = AccountScore(**{**dict(raw), "account_ref": ref})
            except Exception:  # noqa: BLE001 - a corrupt entry must not block startup
                continue

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - feedback must never break dispatch
            pass


def _median(values: list[float]) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    low, high = ordered[middle - 1], ordered[middle]
    # Avoid overflow when both finite non-negative measurements are large.
    return low / 2.0 + high / 2.0 if low < 0 < high else low + (high - low) / 2.0
