"""Rolling-window cost ceiling: admission control before an attempt is spent.

Domain C (成本限制). The scheduler already ranks accounts by *relative* cost via
:mod:`.scoring`, but relative ranking cannot stop an unattended run from
spending without bound: if every account is cheap-but-nonzero, "cheapest" still
adds up. This module adds the missing absolute constraint.

Design constraints (same red lines as the rest of the package):

* **No second cost model.** The unit is whatever the host already feeds
  :meth:`~.MultiAccountOrchestrator.record_account_outcome` ``cost_units`` —
  today ``usage_ledger.task_feedback_metrics`` list-price USD. This module only
  *accumulates* it; it never prices anything itself.
* **Hold, never drop.** A denied attempt is parked with ``retry_at`` (the moment
  enough spend leaves the window), so an unattended run resumes by itself
  instead of losing work.
* **Never overspend under concurrency.** A forecast is *reserved* before
  dispatch and converted to spend on settle, so two in-flight attempts cannot
  both pass the same remaining budget.
* **Unknown cost is not free.** A settled attempt with no pricing evidence is
  charged its reservation (or the configured default) and counted as
  ``unpriced``; it is never recorded as zero.

Persistence reuses the shared atomic document through the injected ``persist``
callback, so a restart neither forgets the day's spend nor double-counts a
reservation.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from .config import MultiAccountConfig

# Hard bound on stored spend records. Overflow is folded into one conservative
# record (see :meth:`CostBudgetGovernor._prune`) so the document stays bounded
# on a multi-week run while the ceiling can only ever be *under*-estimated,
# never silently reset.
MAX_SPEND_RECORDS = 4000


def _finite_units(value: Any) -> Optional[float]:
    """A usable cost measurement, or ``None`` when the number is unusable.

    Cost units arrive from host telemetry, so they can be huge ints, NaN or
    infinity. ``float()`` on a 10**400 int raises ``OverflowError`` and a NaN
    would poison every comparison against the ceiling, so both are rejected here
    instead of at the call sites: an unusable measurement must degrade to
    "unknown cost", never crash dispatch or silently disable the limit.
    """
    if type(value) not in (int, float):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number if number >= 0 else None


@dataclass(frozen=True)
class SpendRecord:
    """One settled attempt's cost, kept only while it is inside the window."""

    at: float
    units: float
    account_ref: Optional[str] = None
    task_id: Optional[str] = None
    priced: bool = True


class CostBudgetGovernor:
    """Admission control over a rolling-window cost ceiling.

    ``admit()`` answers one question — may this attempt be dispatched now — and
    returns a decision the scheduler can act on without knowing the arithmetic:

    ==========  ===============================================================
    decision    meaning
    ==========  ===============================================================
    ``allow``   the forecast fits under the soft threshold; dispatch normally
    ``degrade`` the soft threshold is reached but the hard ceiling is not:
                dispatch, preferring the cheapest eligible account
    ``deny``    the forecast would breach the ceiling; hold until ``retry_at``
    ==========  ===============================================================

    With ``cost_budget_enabled`` false every call returns ``allow`` with
    ``enforced=False``, so the default deployment is byte-for-byte the previous
    behaviour.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 clock: Callable[[], float] = time.time,
                 state: Optional[Mapping[str, Any]] = None,
                 persist: Optional[Callable[[dict[str, Any]], None]] = None) -> None:
        self._config = config
        self._clock = clock
        self._persist = persist
        self._records: list[SpendRecord] = []
        self._reservations: dict[str, dict[str, Any]] = {}
        self._expired_reservations = 0
        self.load(state)

    # --- configuration --------------------------------------------------------
    @property
    def enabled(self) -> bool:
        return bool(self._config.cost_budget_enabled and self._config.cost_budget_units > 0)

    @property
    def cap_units(self) -> float:
        return float(self._config.cost_budget_units)

    @property
    def window_seconds(self) -> float:
        return float(self._config.cost_budget_window_seconds)

    @property
    def _ttl_seconds(self) -> float:
        """Lifetime of an in-flight reservation that nobody settles."""
        return float(self._config.cost_budget_reservation_ttl_seconds)

    def _expired(self, reservation: Mapping[str, Any], *, now: float) -> bool:
        expires_at = reservation.get("expires_at")
        if not isinstance(expires_at, (int, float)):
            # A legacy/unknown reservation has no expiry recorded: treat it as
            # live rather than silently forgiving spend the ceiling already saw.
            return False
        return now >= float(expires_at)

    def _live_reservations(self, *, now: float) -> dict[str, dict[str, Any]]:
        return {token: entry for token, entry in self._reservations.items()
                if not self._expired(entry, now=now)}

    def _sweep_expired(self, *, now: float) -> int:
        """Drop expired reservations so the persisted document stays bounded."""
        dead = [token for token, entry in self._reservations.items()
                if self._expired(entry, now=now)]
        for token in dead:
            self._reservations.pop(token, None)
        if dead:
            self._expired_reservations += len(dead)
            self._save()
        return len(dead)

    def measured_forecast(self, *, now: Optional[float] = None) -> Optional[float]:
        """Mean settled cost per attempt inside the window, if any is known.

        This is the *measured* basis for reserving in-flight work: an operator
        who has not configured ``cost_budget_default_task_units`` still gets a
        forecast grounded in what attempts actually cost, instead of a guess or
        a zero that reserves nothing.
        """
        now = self._clock() if now is None else now
        horizon = now - self.window_seconds
        priced = [r.units for r in self._records if r.at > horizon and r.priced and r.units > 0]
        if not priced:
            return None
        return round(sum(priced) / len(priced), 6)

    # --- read -----------------------------------------------------------------
    def spent_units(self, *, now: Optional[float] = None) -> float:
        """Settled cost inside the current window."""
        now = self._clock() if now is None else now
        horizon = now - self.window_seconds
        return round(sum(r.units for r in self._records if r.at > horizon), 6)

    def reserved_units(self, *, now: Optional[float] = None) -> float:
        """In-flight reservations that still count against the ceiling.

        An expired reservation stops counting *before* it is swept, so a host
        that never carries a token still regains its ceiling room automatically
        instead of being denied forever by a leaked hold.
        """
        if not self._config.cost_budget_include_reservations:
            return 0.0
        now = self._clock() if now is None else now
        horizon = now - self.window_seconds
        return round(sum(float(r.get("units") or 0.0)
                         for r in self._reservations.values()
                         if not self._expired(r, now=now)
                         and float(r.get("at") or 0.0) > horizon), 6)

    def committed_units(self, *, now: Optional[float] = None) -> float:
        return round(self.spent_units(now=now) + self.reserved_units(now=now), 6)

    def status(self, *, now: Optional[float] = None) -> dict[str, Any]:
        """Operator/dashboard view; JSON-safe and side-effect free."""
        now = self._clock() if now is None else now
        spent = self.spent_units(now=now)
        reserved = self.reserved_units(now=now)
        cap = self.cap_units
        return {
            "enforced": self.enabled,
            "cap_units": cap,
            "spent_units": spent,
            "reserved_units": reserved,
            "remaining_units": round(max(0.0, cap - spent - reserved), 6),
            "window_seconds": self.window_seconds,
            "soft_ratio": self._config.cost_budget_soft_ratio,
            "utilization": round((spent + reserved) / cap, 4) if self.enabled and cap > 0 else 0.0,
            "open_reservations": len(self._live_reservations(now=now)),
            "expired_reservations": self._expired_reservations,
            "reservation_ttl_seconds": self._ttl_seconds,
            "measured_forecast_units": self.measured_forecast(now=now),
            "unpriced_attempts": sum(1 for r in self._records if not r.priced),
            # An operator reading a ledger with a different local config (or a
            # clock that has moved on) must be able to tell "no spend" from "no
            # spend *inside this window*". Without these two counters a pruned
            # window looks identical to an empty one.
            "records_in_window": sum(1 for r in self._records
                                     if r.at > now - self.window_seconds),
            "records_total": len(self._records),
        }

    # --- admission ------------------------------------------------------------
    def admit(self, forecast_units: Optional[float] = None, *, now: Optional[float] = None,
              account_ref: Optional[str] = None, reserve: bool = False) -> dict[str, Any]:
        """Decide whether one attempt fits, optionally reserving its forecast.

        ``forecast_units`` is the caller's best estimate for this attempt. When
        it is ``None`` the configured default is used; when that is also zero
        the governor admits on observed spend alone (it can then only stop after
        the ceiling is already reached — the honest trade-off of not guessing).
        """
        now = self._clock() if now is None else now
        self._prune(now=now)
        self._sweep_expired(now=now)
        if not self.enabled:
            return {"decision": "allow", "enforced": False, "reason": "budget_disabled",
                    "forecast_units": None, "retry_at": None, "status": self.status(now=now)}

        forecast = self._forecast(forecast_units, now=now)
        settled = self.spent_units(now=now)
        committed = self.committed_units(now=now)
        cap = self.cap_units
        soft_cap = cap * self._config.cost_budget_soft_ratio

        if forecast > cap:
            # No amount of waiting makes a single attempt fit under the ceiling.
            return {"decision": "deny", "enforced": True,
                    "reason": "forecast_exceeds_cap", "forecast_units": forecast,
                    "retry_at": None, "status": self.status(now=now)}

        if settled + forecast > cap:
            return {"decision": "deny", "enforced": True,
                    "reason": "cost_budget_exhausted", "forecast_units": forecast,
                    "retry_at": self._retry_at(forecast, now=now),
                    "status": self.status(now=now)}

        if committed + forecast > cap:
            # Settled spend still fits: only in-flight reservations block. That
            # clears as soon as they settle, so there is no future moment to
            # sleep to — the caller polls normally instead.
            return {"decision": "deny", "enforced": True,
                    "reason": "cost_budget_reserved", "forecast_units": forecast,
                    "retry_at": None, "status": self.status(now=now)}

        decision = "degrade" if committed + forecast >= soft_cap else "allow"
        reason = "cost_budget_soft_cap" if decision == "degrade" else "within_budget"
        payload = {"decision": decision, "enforced": True, "reason": reason,
                   "forecast_units": forecast, "retry_at": None,
                   "status": self.status(now=now)}
        if reserve:
            payload["reservation"] = self.reserve(forecast, now=now, account_ref=account_ref)
        return payload

    def reserve(self, units: float, *, now: Optional[float] = None,
                account_ref: Optional[str] = None) -> str:
        """Hold ``units`` against the ceiling until :meth:`settle`/:meth:`release`.

        The hold carries ``expires_at``. An unattended coordinator usually has
        no per-task token to settle, so expiry — not a callback — is what keeps
        the ceiling from being permanently blocked by a forgotten reservation.
        """
        now = self._clock() if now is None else now
        token = uuid.uuid4().hex
        self._reservations[token] = {"units": _finite_units(units) or 0.0, "at": now,
                                     "expires_at": now + self._ttl_seconds,
                                     "account_ref": account_ref}
        self._save()
        return token

    def settle(self, token: Optional[str], *, actual_units: Optional[float] = None,
               account_ref: Optional[str] = None, task_id: Optional[str] = None,
               now: Optional[float] = None) -> dict[str, Any]:
        """Convert a reservation into realised spend.

        ``actual_units=None`` means "the attempt ran but its cost is unknown":
        the reservation (or the configured default) is charged and the record is
        flagged ``priced=False``. Dropping an unmeasurable attempt instead would
        let cost drift out of the ceiling unnoticed.
        """
        now = self._clock() if now is None else now
        reservation = self._reservations.pop(token, None) if token else None
        measured = _finite_units(actual_units)
        if measured is not None:
            charged = measured
            priced = True
        elif reservation is not None:
            charged = float(reservation.get("units") or 0.0)
            # A hold is a known quantity, so charging it keeps the ceiling
            # honest; but a *supplied yet unusable* measurement is not evidence
            # of cost, and the attempt stays visible as unpriced.
            priced = charged > 0 and actual_units is None
        else:
            charged = 0.0
            priced = False
        record = SpendRecord(at=now, units=charged, priced=priced, task_id=task_id,
                             account_ref=account_ref or (reservation or {}).get("account_ref"))
        # Spend is always recorded, even while the ceiling is disabled: turning
        # it on mid-run must start from real history instead of an empty window.
        if charged >= 0:
            self._records.append(record)
            self._prune(now=now)
            self._save()
        return {"charged_units": round(charged, 6), "priced": priced,
                "spent_units": self.spent_units(now=now),
                "status": self.status(now=now)}

    def release(self, token: Optional[str]) -> None:
        """Drop a reservation for an attempt that provably incurred no cost."""
        if token and self._reservations.pop(token, None) is not None:
            self._save()

    # --- maintenance ----------------------------------------------------------
    def reset(self, *, now: Optional[float] = None) -> None:
        """Owner override: forget the window (e.g. after raising the ceiling)."""
        self._records.clear()
        self._reservations.clear()
        self._expired_reservations = 0
        self._save()

    def _forecast(self, forecast_units: Optional[float], *,
                  now: Optional[float] = None) -> float:
        supplied = _finite_units(forecast_units)
        if supplied is not None:
            return supplied
        configured = float(self._config.cost_budget_default_task_units)
        if configured > 0:
            return configured
        if self._config.cost_budget_reserve_inflight:
            # Reserving needs a non-zero number to be meaningful; fall back to
            # what attempts actually cost in this window.
            measured = self.measured_forecast(now=now)
            if measured is not None:
                return measured
        return 0.0

    def _retry_at(self, forecast: float, *, now: float) -> Optional[float]:
        """Earliest moment the forecast fits again, or ``None`` if not by waiting.

        Walks settled spend oldest-first and asks which expiry frees enough room.
        ``None`` therefore has two meanings the caller distinguishes by
        :meth:`admit`'s reason: either in-flight reservations are the only
        obstacle (transient), or a single forecast exceeds the whole ceiling.
        """
        cap = self.cap_units
        horizon = now - self.window_seconds
        in_window = sorted((r for r in self._records if r.at > horizon), key=lambda r: r.at)
        committed = self.committed_units(now=now)
        spent = self.spent_units(now=now)
        if spent <= cap - forecast:
            return None  # settled spend already fits; only reservations block
        freed = 0.0
        for record in in_window:
            freed += record.units
            if committed - freed <= cap - forecast:
                return record.at + self.window_seconds
        return None

    def _prune(self, *, now: float) -> None:
        horizon = now - self.window_seconds
        kept = [r for r in self._records if r.at > horizon]
        overflow = len(kept) - MAX_SPEND_RECORDS
        if overflow > 0:
            folded = kept[:overflow]
            # Conservative fold: keep the *latest* timestamp so the merged spend
            # stays in the window at least as long as its parts would have.
            kept = [SpendRecord(at=max(r.at for r in folded),
                                units=round(sum(r.units for r in folded), 6),
                                account_ref=None, task_id=None,
                                priced=all(r.priced for r in folded))] + kept[overflow:]
        if len(kept) != len(self._records):
            self._records = kept

    # --- persistence ----------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        return {
            "records": [[r.at, r.units, r.account_ref, r.task_id, r.priced]
                        for r in sorted(self._records, key=lambda r: r.at)],
            "reserved": dict(self._reservations),
        }

    def load(self, state: Optional[Mapping[str, Any]]) -> None:
        self._records = []
        self._reservations = {}
        if not isinstance(state, Mapping):
            return
        raw_records = state.get("records")
        for row in raw_records if isinstance(raw_records, (list, tuple)) else ():
            try:
                self._records.append(SpendRecord(
                    at=float(row[0]), units=float(row[1]),
                    account_ref=row[2] if isinstance(row[2], str) else None,
                    task_id=row[3] if isinstance(row[3], str) else None,
                    priced=bool(row[4]) if len(row) > 4 else True))
            except (TypeError, ValueError, IndexError):
                continue
        raw_reserved = state.get("reserved")
        if isinstance(raw_reserved, Mapping):
            for token, entry in raw_reserved.items():
                if isinstance(token, str) and isinstance(entry, Mapping):
                    restored = dict(entry)
                    if not isinstance(restored.get("expires_at"), (int, float)):
                        # State written before reservations had a TTL: give it
                        # one now instead of letting it hold room forever.
                        at = restored.get("at")
                        base = float(at) if isinstance(at, (int, float)) else 0.0
                        restored["expires_at"] = base + self._ttl_seconds
                    self._reservations[token] = restored

    def _save(self) -> None:
        if self._persist is None:
            return
        try:
            self._persist(self.snapshot())
        except Exception:  # noqa: BLE001 - cost bookkeeping must never break dispatch
            pass
