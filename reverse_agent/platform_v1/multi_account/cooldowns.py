"""Two-tier account cooldown registry: task-level quiet time and account quarantine.

Why a registry instead of the previous single ``_excluded`` dict on the
scheduler: the one dict mixed two different lifetimes.

* **transient** — "this task just failed on this account, do not retry it right
  away" (``quota_exhausted`` / ``task_failed``). It may be cleared when a new
  task starts.
* **quarantine** — "this account itself is unhealthy" (``account_abnormal``:
  unauthorized, provider-side rate-limit error). It belongs to the account, not
  to the task, so it must survive a new task *and* a process restart. Losing it
  on restart is what makes an unattended run hammer a dead account after every
  crash.

Consecutive failures of the same account escalate the delay exponentially up to
``failure_backoff_max_seconds``, so a flapping account backs off instead of
being retried every ``reroute_cooldown_seconds`` forever. A success clears the
streak. Idle entries are pruned after ``cooldown_memory_seconds`` so the state
document stays bounded on a long unattended run.

The registry holds no credentials and performs no dispatch; it is pure bookkeeping
with an injected clock and an optional persistence callback.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from .config import MultiAccountConfig

TRANSIENT = "transient"
QUARANTINE = "quarantine"

# Account-level failures quarantine the account; quota/task failures only quiet it.
QUARANTINE_KINDS = frozenset({"account_abnormal"})


@dataclass(frozen=True)
class Cooldown:
    """One account's current quiet window and the streak that produced it."""

    account_ref: str
    until: float
    kind: str
    streak: int
    tier: str

    def active_at(self, now: float) -> bool:
        return self.until > now

    def to_state(self) -> dict[str, Any]:
        return {"until": self.until, "kind": self.kind, "streak": self.streak, "tier": self.tier}


class CooldownRegistry:
    """Bookkeeping for which accounts may be dispatched right now, and until when.

    ``state`` is the persisted mapping ``{account_ref: {...}}`` loaded at startup;
    ``persist`` is called after every mutation so a crash cannot lose a
    quarantine. Both are optional: without them the registry is in-memory only.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._persist = persist
        self._entries: dict[str, Cooldown] = {}
        self.load(state)

    # --- introspection --------------------------------------------------------
    def get(self, account_ref: str) -> Optional[Cooldown]:
        return self._entries.get(account_ref)

    def until(self, account_ref: str) -> float:
        entry = self._entries.get(account_ref)
        return entry.until if entry else 0.0

    def is_cooling(self, account_ref: str, *, now: Optional[float] = None) -> bool:
        now = self._clock() if now is None else now
        entry = self._entries.get(account_ref)
        return bool(entry and entry.active_at(now))

    def active_map(self, *, now: Optional[float] = None) -> dict[str, float]:
        """``{account_ref: until}`` for accounts that are cooling right now."""
        now = self._clock() if now is None else now
        return {ref: entry.until for ref, entry in self._entries.items() if entry.active_at(now)}

    def next_retry_at(self, *, now: Optional[float] = None) -> Optional[float]:
        active = self.active_map(now=now)
        return min(active.values()) if active else None

    def blocked_accounts(self, *, now: Optional[float] = None) -> list[str]:
        return sorted(self.active_map(now=now))

    # --- mutation -------------------------------------------------------------
    def record_failure(self, account_ref: str, kind: str, *,
                       now: Optional[float] = None) -> Cooldown:
        """Escalate this account's cooldown and return the new window."""
        now = self._clock() if now is None else now
        previous = self._entries.get(account_ref)
        # Escalate while failures keep coming, even when a short cooldown already
        # expired in between (that is exactly the flapping case), but forget the
        # streak once the account has been quiet for the whole memory window.
        recent = previous is not None and (now - previous.until) <= self._config.cooldown_memory_seconds
        streak = previous.streak + 1 if recent and previous is not None else 1
        tier = QUARANTINE if kind in QUARANTINE_KINDS else TRANSIENT
        delay = self._delay_for(kind, streak)
        entry = Cooldown(account_ref=account_ref, until=now + delay, kind=kind,
                         streak=streak, tier=tier)
        self._entries[account_ref] = entry
        self._save()
        return entry

    def record_success(self, account_ref: str, *, now: Optional[float] = None) -> None:
        """A successful run proves the account works: drop its streak and quiet time."""
        entry = self._entries.get(account_ref)
        if entry is None:
            return
        # A quarantine is never lifted by an ordinary success (we do not dispatch
        # to a quarantined account, so such a success could only be a stale
        # in-flight run); its wall-clock expiry remains the only exit.
        if entry.tier == QUARANTINE:
            return
        del self._entries[account_ref]
        self._save()

    def clear(self, account_ref: str) -> None:
        if self._entries.pop(account_ref, None) is not None:
            self._save()

    def clear_transient(self) -> None:
        """Start a new task: forget quiet times but keep account quarantines."""
        kept = {ref: e for ref, e in self._entries.items() if e.tier == QUARANTINE}
        if len(kept) != len(self._entries):
            self._entries = kept
            self._save()

    def clear_all(self) -> None:
        if self._entries:
            self._entries.clear()
            self._save()

    def prune(self, *, now: Optional[float] = None) -> int:
        """Drop entries that are long expired; keeps the state document bounded."""
        now = self._clock() if now is None else now
        horizon = self._config.cooldown_memory_seconds
        stale = [ref for ref, e in self._entries.items() if now - e.until > horizon]
        for ref in stale:
            del self._entries[ref]
        if stale:
            self._save()
        return len(stale)

    def _delay_for(self, kind: str, streak: int) -> float:
        """Exponential backoff with a per-kind floor, capped by config."""
        config = self._config
        grown = config.failure_backoff_base_seconds * (config.failure_backoff_multiplier ** (streak - 1))
        floor = (config.abnormal_account_cooldown_seconds if kind in QUARANTINE_KINDS
                 else config.reroute_cooldown_seconds)
        return float(min(config.failure_backoff_max_seconds, max(grown, floor)))

    # --- persistence ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {ref: entry.to_state() for ref, entry in sorted(self._entries.items())}

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        self._entries = {}
        if not isinstance(state, Mapping):
            return
        for ref, raw in state.items():
            if not isinstance(ref, str) or not isinstance(raw, Mapping):
                continue
            until = raw.get("until")
            if not isinstance(until, (int, float)):
                continue
            streak = raw.get("streak")
            tier = raw.get("tier")
            self._entries[ref] = Cooldown(
                account_ref=ref, until=float(until),
                kind=str(raw.get("kind") or "unknown"),
                streak=int(streak) if isinstance(streak, int) and streak > 0 else 1,
                tier=tier if tier in (TRANSIENT, QUARANTINE) else TRANSIENT)

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - bookkeeping must never break dispatch
            pass
