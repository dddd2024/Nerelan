"""Account and quota *status perception* for the multi-account orchestration brain.

This is domain B (perceive account/quota state) and the corrected half of
domain A (multi-account pooling). The legacy :func:`magpie_quota_windows` keeps
*one* account per provider and :meth:`trusted_host._merge_magpie_quotas`
overwrites by provider key, which silently drops the second of two real
accounts (e.g. ``WorkBuddy`` vs ``WorkBuddy AI``). :func:`pool_account_quotas`
reuses the account-preserving projection :func:`magpie_account_quotas` and
enriches it with the route provider, then keeps *every* account — it is the
drop-in fix for the merge defect.

The module performs no I/O of its own: the source of observations is injected
(``fetch_quotas``), defaulting to :func:`pool_account_quotas`, so it is fully
testable with fakes and never blocks dispatch on a failed observation.
"""
from __future__ import annotations

import enum
from typing import Any, Callable, Iterable, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from .config import MultiAccountConfig


class AccountHealth(str, enum.Enum):
    """Coarse health used by the scheduler to admit, reroute or quarantine."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"      # high utilization but still usable
    EXHAUSTED = "EXHAUSTED"    # a window hit 100% / provider rejected
    ABNORMAL = "ABNORMAL"      # account-level error (unauthorized, rate-limit error)
    STALE = "STALE"            # last observation older than freshness budget
    UNKNOWN = "UNKNOWN"        # no usable observation at all


class WindowStatus(BaseModel):
    """One quota window for one account, normalized for the perception layer.

    Upstream evidence is wider than this model on purpose: Magpie windows carry
    ``basis="official_percent"`` and the local CLI projection carries
    ``availability``/``anchor``. Those known keys are typed below and any future
    key lands in :attr:`extra` instead of raising, because a single unexpected
    field must never take the whole perception pool down (see
    :meth:`MultiAccountStatusMonitor._normalize_window`).
    """

    model_config = ConfigDict(extra="forbid")

    window: str
    used_percent: Optional[float] = None
    resets_at: Optional[float] = None          # epoch seconds
    reset_passed: bool = False
    status: Optional[str] = None               # provider rate-limit status if any
    source: Optional[str] = None
    basis: Optional[str] = None                # official_percent / official_status / ...
    availability: Optional[str] = None         # provider availability classification
    unlimited: bool = False                    # an unlimited window never constrains admission
    extra: dict[str, Any] = Field(default_factory=dict)  # unknown upstream keys, preserved


class AccountStatus(BaseModel):
    """Perceived state of a single quota account, ready for scheduling + UI."""

    model_config = ConfigDict(extra="forbid")

    account_ref: str
    provider: Optional[str] = None             # route key (codex/claude-code/...)
    health: AccountHealth
    observed_at: Optional[float] = None        # epoch seconds
    freshness_age: Optional[float] = None      # now - observed_at
    headroom_pct: Optional[float] = None       # min over active windows of 100-used
    anomaly_flags: list[str] = Field(default_factory=list)
    windows: list[WindowStatus] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    def public_view(self) -> dict[str, Any]:
        """JSON-safe view for ``/api/resources`` and the web client.

        ``raw`` stays host-side: it is unredacted upstream evidence and has no
        business crossing the loopback API boundary.
        """
        return {
            "account_ref": self.account_ref,
            "provider": self.provider,
            "health": self.health.value,
            "observed_at": self.observed_at,
            "freshness_age": self.freshness_age,
            "headroom_pct": self.headroom_pct,
            "anomaly_flags": list(self.anomaly_flags),
            "windows": [w.model_dump(exclude={"extra"}) for w in self.windows],
            "next_reset_at": min(
                (w.resets_at for w in self.windows
                 if w.resets_at is not None and not w.reset_passed and not w.unlimited),
                default=None),
        }


def _parse_iso(value: Any) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        from ...model_access.subscription_quota import parse_iso_time
        return parse_iso_time(value)
    except Exception:  # noqa: BLE001 - perception must never raise on a bad stamp
        return None


def pool_account_quotas(snapshot: Mapping[str, Any], *,
                        now: Optional[float] = None) -> dict[str, dict[str, Any]]:
    """Account-preserving Magpie projection enriched with the route provider.

    Reuses :func:`magpie_account_quotas` (which already keeps one entry per
    ``account_ref``) and adds the ``provider`` route key each account maps to,
    so the scheduler can pair an account with the right executor/binding. Unlike
    :func:`magpie_quota_windows` this never collapses multiple accounts of the
    same provider into one.

    Returns ``{account_ref: evidence}``. Safe to call with an empty/unavailable
    snapshot — it returns ``{}`` rather than raising.
    """
    try:
        from ...model_access.subscription_quota import (
            magpie_account_quotas, magpie_route_provider,
        )
    except Exception:  # noqa: BLE001 - a missing dependency must not break perception
        return {}
    projected = magpie_account_quotas(snapshot, now=now)
    provider_by_ref: dict[str, Optional[str]] = {}
    accounts = snapshot.get("accounts") if isinstance(snapshot, Mapping) else None
    for account in accounts if isinstance(accounts, (list, tuple)) else ():
        if not isinstance(account, Mapping):
            continue
        ref = account.get("account_ref")
        if isinstance(ref, str) and ref:
            provider_by_ref[ref] = magpie_route_provider(account.get("provider"))
    enriched: dict[str, dict[str, Any]] = {}
    for ref, evidence in projected.items():
        evidence = dict(evidence)
        evidence.setdefault("provider", provider_by_ref.get(ref))
        enriched[ref] = evidence
    return enriched


def merge_account_quotas(local: Mapping[str, Any], snapshot: Mapping[str, Any], *,
                        now: Optional[float] = None) -> dict[str, Any]:
    """Additive merge used by the dispatch quota view.

    Keeps the legacy provider-keyed entries (still consumed by provider lookups
    in :mod:`trusted_host`) **and** preserves every observed account under its
    own ``account_ref`` key. Previously only one account per provider survived
    (``magpie_quota_windows`` collapses to one per provider and the loop
    overwrote by provider key), silently dropping a second real account such as
    ``WorkBuddy AI`` next to ``WorkBuddy``. This is the drop-in fix for that
    defect and is strictly additive: it never removes a key, so existing
    callers are unaffected.
    """
    merged = dict(local)
    try:
        from ...model_access.subscription_quota import magpie_quota_windows
        for key, quota in magpie_quota_windows(snapshot, now=now).items():
            merged[key] = quota
    except Exception:  # noqa: BLE001 - perception must never break dispatch
        pass
    for ref, quota in pool_account_quotas(snapshot, now=now).items():
        merged.setdefault(ref, quota)
    return merged


class MultiAccountStatusMonitor:
    """Turns raw account/quota observations into structured :class:`AccountStatus`.

    The observation source is injected so tests and alternative telemetry (local
    CLI, vendor APIs) can be swapped without touching the derivation logic.
    """

    def __init__(self, config: MultiAccountConfig, *,
                 fetch_quotas: Optional[Callable[[Optional[Mapping[str, Any]]], Mapping[str, Any]]] = None,
                 clock: Callable[[], float] = __import__("time").time) -> None:
        self._config = config
        self._fetch = fetch_quotas if fetch_quotas is not None else pool_account_quotas
        self._clock = clock

    def perceive(self, snapshot: Optional[Mapping[str, Any]] = None, *,
                 now: Optional[float] = None) -> list[AccountStatus]:
        now = self._clock() if now is None else now
        raw = self._fetch(snapshot) or {}
        statuses: list[AccountStatus] = []
        for ref, evidence in raw.items():
            if not isinstance(evidence, Mapping):
                continue
            try:
                statuses.append(self._build_status(str(ref), evidence, now))
            except Exception:  # noqa: BLE001 - one malformed account must not empty the pool
                statuses.append(AccountStatus(
                    account_ref=str(ref), provider=None, health=AccountHealth.UNKNOWN,
                    observed_at=None, freshness_age=None, headroom_pct=None,
                    anomaly_flags=["perception_error"], windows=[], raw={}))
        return statuses

    def _build_status(self, account_ref: str, evidence: Mapping[str, Any], now: float) -> AccountStatus:
        windows = [self._normalize_window(w) for w in evidence.get("windows", [])
                   if isinstance(w, Mapping)]
        observed_at = _parse_iso(evidence.get("observed_at"))
        freshness_age = (now - observed_at) if observed_at is not None else None
        flags: list[str] = []

        if observed_at is None:
            health = AccountHealth.UNKNOWN
            flags.append("no_observation")
        elif freshness_age is not None and freshness_age > self._config.observation_freshness_seconds:
            health = AccountHealth.STALE
            flags.append("stale")
        else:
            # Worst-case across active windows: EXHAUSTED > ABNORMAL > DEGRADED > HEALTHY.
            # A provider "rejected" status is *confirmed* exhaustion, so it ranks
            # as EXHAUSTED, not merely abnormal.
            rank = {AccountHealth.HEALTHY: 3, AccountHealth.DEGRADED: 2,
                    AccountHealth.ABNORMAL: 1, AccountHealth.EXHAUSTED: 0}
            health = AccountHealth.HEALTHY
            for w in windows:
                if w.unlimited or w.reset_passed:
                    continue  # an unlimited window, or one already reset, never constrains
                if w.status == "rejected" or (w.used_percent is not None and w.used_percent >= 100):
                    w_health = AccountHealth.EXHAUSTED
                    flags.append(f"exhausted:{w.window}")
                elif w.status in {"error", "unauthorized"}:
                    w_health = AccountHealth.ABNORMAL
                    flags.append(f"abnormal:{w.window}")
                elif (w.used_percent is not None
                      and w.used_percent >= self._config.high_utilization_threshold):
                    w_health = AccountHealth.DEGRADED
                    flags.append(f"high_utilization:{w.window}")
                else:
                    w_health = AccountHealth.HEALTHY
                if rank[w_health] < rank[health]:
                    health = w_health
                if w.status in ("rejected", "error", "unauthorized"):
                    flags.append(f"rate_limited:{w.window}")
                if (w.resets_at is not None and not w.reset_passed
                        and 0 <= (w.resets_at - now) <= self._config.reset_soon_threshold_seconds):
                    flags.append(f"reset_soon:{w.window}")
                if w.used_percent is None and w.status is None:
                    flags.append(f"unknown_window:{w.window}")

        headroom: Optional[float] = None
        active = [w for w in windows
                  if not w.reset_passed and not w.unlimited and w.used_percent is not None]
        if active:
            headroom = min(100.0 - w.used_percent for w in active)  # type: ignore[arg-type]

        return AccountStatus(
            account_ref=account_ref,
            provider=evidence.get("provider"),
            health=health,
            observed_at=observed_at,
            freshness_age=freshness_age,
            headroom_pct=headroom,
            anomaly_flags=sorted(set(flags)),
            windows=windows,
            raw=dict(evidence),
        )

    @staticmethod
    def _normalize_window(window: Mapping[str, Any]) -> WindowStatus:
        """Coerce an upstream window (ISO ``resets_at``) into the typed model.

        Unknown keys are preserved in ``extra`` rather than rejected: a provider
        adding a field to its evidence must not blind the whole account pool.
        """
        data = dict(window)
        resets_at = data.get("resets_at")
        if isinstance(resets_at, str):
            data["resets_at"] = _parse_iso(resets_at)
        allowed = set(WindowStatus.model_fields)
        unknown = {key: data.pop(key) for key in list(data) if key not in allowed}
        if isinstance(data.get("extra"), Mapping):
            unknown = {**unknown, **data["extra"]}
        # Magpie names the window ``name``; accept it and never duplicate it in rest.
        name = unknown.pop("name", None) or window.get("name")
        if not data.get("window"):
            data["window"] = name if isinstance(name, str) and name else "window"
        data["extra"] = unknown
        return WindowStatus(**data)
        return WindowStatus(**data)

    def diagnose(self, snapshot: Mapping[str, Any], *,
                 now: Optional[float] = None) -> list[AccountStatus]:
        """Every Magpie account, for operators; never admission evidence.

        :func:`pool_account_quotas` keeps only accounts a route here claims, which
        is right for admission and hides the rest of the pool. This projection
        keeps them all so that nobody reads "2 accounts" off an 11-account pool.
        The STALE/UNKNOWN verdict from Magpie stands: those windows are not re-judged.
        """
        now = self._clock() if now is None else now
        statuses: list[AccountStatus] = []
        unidentified = 0
        for account in snapshot.get("accounts") or ():
            if not isinstance(account, Mapping):
                continue
            provider = account.get("provider")
            ref = account.get("account_ref")
            if not ref:
                unidentified += 1
                ref = f"{provider or 'unknown'}:unidentified:{unidentified}"
            try:
                windows = []
                for window in account.get("windows") or ():
                    if isinstance(window, Mapping):
                        resets_at = _parse_iso(window.get("resets_at"))
                        windows.append({**window, "window": window.get("name"), "resets_at": resets_at,
                                        "reset_passed": resets_at is not None and resets_at <= now})
                status = self._build_status(str(ref), {
                    "provider": provider, "windows": windows,
                    "observed_at": account.get("observed_at")}, now)
            except Exception:  # noqa: BLE001 - one malformed account must not empty the pool
                status = AccountStatus(account_ref=str(ref), provider=str(provider or "") or None,
                                       health=AccountHealth.UNKNOWN, anomaly_flags=["perception_error"])
            state = account.get("state")
            if state in {"STALE", "UNKNOWN"}:
                reason = account.get("reason")
                status = status.model_copy(update={
                    "health": AccountHealth[state],
                    "anomaly_flags": sorted({*status.anomaly_flags, *([str(reason)] if reason else [])}),
                })
            statuses.append(status.model_copy(update={"raw": {}}))
        return statuses

    @staticmethod
    def health_summary(statuses: Iterable[AccountStatus]) -> dict[str, Any]:
        """Aggregate view for dashboards and the unattended coordinator.

        The input is materialized once: a caller passing a generator must not get
        ``total_accounts == 0`` after the counting loop consumed it.
        """
        observed = list(statuses)
        counts: dict[str, int] = {h.value: 0 for h in AccountHealth}
        eligible = 0
        best_headroom: Optional[float] = None
        earliest_reset: Optional[float] = None
        for s in observed:
            counts[s.health.value] += 1
            if s.health in (AccountHealth.HEALTHY, AccountHealth.DEGRADED):
                eligible += 1
                if s.headroom_pct is not None:
                    best_headroom = s.headroom_pct if best_headroom is None else max(best_headroom, s.headroom_pct)
            for window in s.windows:
                if window.reset_passed or window.unlimited or window.resets_at is None:
                    continue
                earliest_reset = (window.resets_at if earliest_reset is None
                                  else min(earliest_reset, window.resets_at))
        return {
            "total_accounts": len(observed),
            "eligible_accounts": eligible,
            "by_health": counts,
            "best_headroom_pct": best_headroom,
            "earliest_capacity_at": earliest_reset,
            "stale_accounts": counts[AccountHealth.STALE.value] + counts[AccountHealth.UNKNOWN.value],
        }
