"""Account-level self-evolution: bounded EWMA feedback that re-orders equal accounts.

The existing self-evolution loop (:mod:`.evolution`) learns at *mode* level —
single agent vs team. That leaves the per-account question unanswerable: two
accounts with the same headroom are not equally good, because one of them may
have failed the last four tasks on it, or cost twice as much per accepted task.

This module keeps only three smoothed numbers per account — success ratio, mean
cost units, mean wall time — and exposes them as a small *bonus* in
headroom-equivalent points. It is deliberately not a learning framework:

* bounded (one record per account, capped count, prunable),
* explainable (a weighted sum of three named terms, visible in the decision
  evidence),
* rollback-able (clear the state document and the ranking is purely headroom),
* non-decisive (the scheduler applies it only *inside* one health class, so it
  can never promote an unhealthy account over a healthy one).

Smoothing is a plain EWMA with ``score_ewma_alpha``; a sample is discounted
until the account has a few observations, so one lucky run cannot dominate.
"""
from __future__ import annotations

import math
import time
from typing import Any, Callable, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from .config import MultiAccountConfig

# How many observations an account needs before its score counts in full.
CONFIDENCE_ATTEMPTS = 3
# Accounts idle for longer than this are pruned on write, keeping the document bounded.
PRUNE_HORIZON_SECONDS = 30 * 24 * 3600
MAX_TRACKED_ACCOUNTS = 200


class AccountScore(BaseModel):
    """Measured, smoothed behaviour of one account."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    account_ref: str
    attempts: int = Field(0, ge=0, strict=True)
    successes: int = Field(0, ge=0, strict=True)
    reliability: float = Field(0.5, ge=0, le=1)
    mean_cost_units: Optional[float] = Field(None, ge=0)
    mean_wall_seconds: Optional[float] = Field(None, ge=0)
    consecutive_failures: int = Field(0, ge=0, strict=True)
    last_failure_kind: Optional[str] = None
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
        alpha = self._config.score_ewma_alpha
        score = self._scores.get(account_ref) or AccountScore(
            account_ref=account_ref, first_seen_at=now)
        score.attempts += 1
        if ok:
            score.successes += 1
            score.consecutive_failures = 0
        else:
            score.consecutive_failures += 1
            score.last_failure_kind = failure_kind or "unknown"
        score.reliability = _ewma(score.reliability, 1.0 if ok else 0.0, alpha)
        cost = _measurement(cost_units)
        wall = _measurement(wall_seconds)
        if cost is not None:
            score.mean_cost_units = _ewma(score.mean_cost_units, cost, alpha)
        if wall is not None:
            score.mean_wall_seconds = _ewma(score.mean_wall_seconds, wall, alpha)
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
              latency_reference: Optional[float] = None) -> float:
        """Headroom-equivalent points this account earns (or loses) from feedback."""
        score = self._scores.get(account_ref)
        if score is None or not score.attempts:
            return 0.0
        config = self._config
        points = config.reliability_weight * (score.reliability - 0.5) * 2.0
        if cost_reference and score.mean_cost_units is not None:
            points -= config.cost_weight * min(1.0, score.mean_cost_units / cost_reference)
        if latency_reference and score.mean_wall_seconds is not None:
            points -= config.latency_weight * min(1.0, score.mean_wall_seconds / latency_reference)
        confidence = min(1.0, score.attempts / CONFIDENCE_ATTEMPTS)
        return points * confidence

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
    return (ordered[middle - 1] + ordered[middle]) / 2.0
