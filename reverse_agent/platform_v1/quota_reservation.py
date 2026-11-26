"""Account-scoped observations and task need estimates; no I/O or provider calls.

Callers supply account identities, history, refresh and clock boundaries. Legacy
provider summaries are deliberately not accepted as account evidence.
"""
from __future__ import annotations

import math
import time
from statistics import median
from typing import Any, Callable, Iterable, Mapping

from ..model_access import quota_forecast
from ..model_access import pricing


DEFAULT_PRIOR = {"input": 12000, "cache_read": 12000, "output": 4000, "turn_count": 4}
# Conservative percentage-point need for an account with no measured
# units-per-percent yet (#1281 "conservative prior with a wide band").
UNCALIBRATED_WINDOW_NEED = {"five_hour": {"median": 15.0, "p80": 30.0},
                            "weekly": {"median": 3.0, "p80": 6.0}}
_WINDOW_NAMES = {"five_hour": "five_hour", "5 hours": "five_hour", "5h": "five_hour", "5-hour": "five_hour",
                 "weekly": "weekly", "7 days": "weekly", "7d": "weekly", "week": "weekly"}


# An idle subscription account is re-read by the gateway only every 13 to 56 minutes, so
# the 600 s freshness alone can hold an unused account. An older reading may still admit
# when it leaves room for spend it cannot have seen: percentage points per hour of age.
ADMISSION_FRESHNESS_SECONDS = 600
AGED_MAX_SECONDS = 3600
AGED_POINTS_PER_HOUR = {"five_hour": 40.0, "weekly": 8.0}


def canonical_window(name: Any) -> Any:
    """Observation sources name windows differently ("5 hours", "7 days"); admission needs one name."""
    return _WINDOW_NAMES.get(str(name).strip().lower(), name) if name is not None else name


def _canonical_windows(windows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(w, window=canonical_window(w.get("window", w.get("name")))) for w in windows
            if isinstance(w, Mapping)]


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _padded(used: float, window: str, age: float) -> float:
    return min(100.0, used + AGED_POINTS_PER_HOUR[window] * age / 3600)


def observation(account_ref: str, candidates: Iterable[Mapping[str, Any]], *,
                clock: Callable[[], float] = time.time, freshness: float = 600,
                refresh: Callable[[str], Iterable[Mapping[str, Any]]] | None = None,
                small_task: bool = False) -> dict[str, Any]:
    """Select evidence by source precedence, then recency within that source.

    A stale preferred source yields to a fresh fallback. Refresh runs at most once,
    only when no fresh known observation exists. Small-task permission is explicit.
    """
    if not account_ref or freshness < 0:
        raise ValueError("account identity and nonnegative freshness required")
    now = clock()

    def normalize(items):
        result = []
        for item in items:
            if item.get("account_ref") != account_ref:
                continue
            raw = item.get("observed_at")
            at = float(raw) if _number(raw) else quota_forecast.parse_time(raw)
            source = item.get("source")
            basis = item.get("provenance", "")
            rank = (3 if source in {"magpie", "official"} else
                    2 if basis == "OFFICIAL_VIA_CLI" or source in {"cli", "claude_rate_limit_event"} else
                    1 if basis == "ESTIMATED_FROM_HISTORY" or source == "estimated" else 0)
            known = rank > 0 and bool(item.get("windows")) and item.get("state") != "UNKNOWN"
            aged = rank == 3 and item.get("aged_admission") is True
            limit = max(freshness, AGED_MAX_SECONDS) if aged else freshness
            fresh = known and at is not None and 0 <= now - at <= limit
            windows = _canonical_windows(item.get("windows") or ())
            if aged and fresh:  # the margin grows with the reading's age, also after it was stored
                windows = [dict(w, used_percent=_padded(w["observed_percent"], w["window"], now - at))
                           if w["window"] in AGED_POINTS_PER_HOUR and _number(w.get("observed_percent")) else w
                           for w in windows]
            result.append((fresh, rank if known else 0, at if at is not None else -math.inf,
                           dict(item, observed_at=quota_forecast.iso(at), fresh=bool(fresh), windows=windows)))
        return result

    choices = normalize(candidates)
    if not any(c[0] for c in choices) and refresh is not None:
        choices += normalize(refresh(account_ref))
    selected = max(choices, key=lambda c: c[:3]) if choices else None
    evidence = selected[3] if selected else {"account_ref": account_ref, "state": "UNKNOWN",
                                            "observed_at": None, "windows": [], "fresh": False}
    uncertain = not evidence["fresh"]
    return evidence | {"eligible": not uncertain or small_task, "uncertain": uncertain,
                       "eligibility_reason": "fresh" if not uncertain else
                       "explicit_small_task" if small_task else "refresh_required"}


def aged_evidence(selected: Mapping[str, Any] | None, *, now: float) -> dict[str, Any] | None:
    """A provider reading past the admission freshness, charged for the spend it cannot show.

    Usage only grows before a stated reset, so the reading is a lower bound; each window is
    raised by AGED_POINTS_PER_HOUR. Needs a provider reading of both windows, no older than
    AGED_MAX_SECONDS and with no reset passed. The result is for admission only: calibration
    ignores it, and ``observed_at`` stays the real reading time so spend settled since then
    is still counted on top.
    """
    if not selected or selected.get("source") not in {"magpie", "official"} or selected.get("aged_admission"):
        return None
    at = quota_forecast.parse_time(selected.get("observed_at"))
    if at is None or not ADMISSION_FRESHNESS_SECONDS < now - at <= AGED_MAX_SECONDS:
        return None
    windows = []
    for window in _canonical_windows(selected.get("windows") or ()):
        used, points = window.get("used_percent"), AGED_POINTS_PER_HOUR.get(window["window"])
        if points is None:
            continue
        reset_raw = window.get("resets_at")
        reset = float(reset_raw) if _number(reset_raw) else quota_forecast.parse_time(reset_raw)
        if not _number(used) or (reset_raw is not None and reset is None) or (reset is not None and reset <= now):
            return None
        windows.append(dict(window, observed_percent=used, used_percent=_padded(used, window["window"], now - at)))
    if sorted(w["window"] for w in windows) != sorted(AGED_POINTS_PER_HOUR):
        return None
    return dict(selected, windows=windows, aged_admission=True, reading_age_seconds=round(now - at))


def task_need(records: Iterable[Mapping[str, Any]], *, binding: str, kind: str,
              difficulty: str, model: str, clock: Callable[[], float] = time.time,
              prior: Mapping[str, float] = DEFAULT_PRIOR, min_samples: int = 5,
              cold_gap: float = 3600, cold_input: float = 12000) -> dict[str, Any]:
    """Linear-interpolated p80 and median; sparse history is floored by priors.

    Cold starts move cached input into uncached input and add context-loading cost.
    Missing timestamps conservatively count as cold. History never crosses bindings.
    """
    if min_samples < 1 or cold_gap < 0 or cold_input < 0:
        raise ValueError("invalid estimation policy")
    now = clock()
    rows = [r for r in records if r.get("binding_ref") == binding and r.get("kind") == kind
            and r.get("difficulty") == difficulty and (r.get("ok") or r.get("measured")) and r.get("tokens")]
    times = [at for r in rows if (at := quota_forecast.parse_time(r.get("observed_at"))) is not None
             and at <= now]
    cold = not times or now - max(times) >= cold_gap
    estimates = {}
    for counter in DEFAULT_PRIOR:
        values = sorted(float(v) for r in rows
                        if _number(v := (r.get("turn_count") if counter == "turn_count"
                                         else r["tokens"].get(counter))))
        floor = prior[counter]
        estimates[counter] = {
            "median": max(median(values), floor) if values and len(values) < min_samples else
                      median(values) if values else floor,
            "p80": max(quota_forecast._quantile(values, .8), floor * 1.5) if values and len(values) < min_samples else
                   quota_forecast._quantile(values, .8) if values else floor * 1.5,
            "samples": len(values),
        }
    if cold:
        for q in ("median", "p80"):
            estimates["input"][q] += estimates["cache_read"][q] + cold_input
            estimates["cache_read"][q] = 0
    units = {q: pricing.equivalent_cost(model, {k: v[q] for k, v in estimates.items()
                                               if k != "turn_count"}).get("usd")
             for q in ("median", "p80")}
    return {"binding": binding, "kind": kind, "difficulty": difficulty, "model": model,
            "estimated_at": quota_forecast.iso(now),
            "policy": {"prior": dict(prior), "min_samples": min_samples, "cold_gap": cold_gap, "cold_input": cold_input},
            "history": [{key: r.get(key) for key in ("task_id", "claim_epoch", "binding_ref", "kind", "difficulty",
                         "ok", "measured", "tokens", "turn_count", "observed_at")} for r in rows], "tokens": estimates,
            "units": units, "cold_start": cold, "samples": len(rows),
            "uncertain": any(v["samples"] < min_samples for v in estimates.values())}


def window_need(need: Mapping[str, Any], account_ref: str,
                calibrations: Mapping[str, Mapping[str, float]]) -> dict[str, Any]:
    """Convert measured price units per percentage point, independently per account/window."""
    account = calibrations.get(account_ref, {})
    account = {canonical_window(name): rate for name, rate in account.items()}
    windows, prior = {}, []
    for window in ("five_hour", "weekly"):
        rate = account.get(window)
        if _number(rate) and rate > 0:
            windows[window] = {q: units / rate if _number(units) else None for q, units in need["units"].items()}
        else:
            # Uncalibrated account: a wide conservative prior instead of an unknown need,
            # so a fresh observation can still admit work (never an indefinite hold).
            windows[window] = dict(UNCALIBRATED_WINDOW_NEED[window])
            prior.append(window)
    return {"account_ref": account_ref, "windows": windows, "estimate": dict(need), "calibration": dict(account),
            "prior_windows": prior,
            "uncertain": need["uncertain"] or bool(prior) or any(v is None for w in windows.values() for v in w.values())}


def release_weekly_reserve(need, evidence, *, release_hours, now):
    """Mark the weekly need when the Owner's reserve is released for this very window."""
    for window in _canonical_windows(evidence.get("windows", ())):
        raw = window.get("resets_at")
        reset = float(raw) if _number(raw) else quota_forecast.parse_time(raw)
        weekly = (need.get("windows") or {}).get("weekly")
        if (window["window"] == "weekly" and isinstance(weekly, Mapping) and reset is not None
                and 0 < reset - now <= release_hours * 3600):
            return {**need, "windows": {**need["windows"], "weekly": {**weekly, "reserve_released_until": reset}}}
    return need


def cap_need_to_window(need, buffer=10):
    """A single task's need capped at what one window can hold (``100 - buffer``).

    An estimate beyond a whole window can never fit, so admission would wait
    forever: Codex reviews estimated at 324% of the 5-hour window stayed QUEUED
    through resets at 0% used (2026-11-26). Capped once, where the need is
    stored, admission, reservations and in-flight checks all see the same value;
    the original is kept as ``uncapped_p80``. Summed goal forecasts are never
    capped, and a buffer of 100 (no capacity) leaves the need unchanged.
    """
    limit = 100 - buffer if _number(buffer) else None
    if limit is None or limit <= 0 or not isinstance(need, dict):
        return need
    capped = dict(need)
    windows = {}
    for name, window in (need.get("windows") or {}).items():
        window = dict(window) if isinstance(window, dict) else window
        if isinstance(window, dict) and _number(window.get("p80")) and window["p80"] > limit:
            window["uncapped_p80"] = window["p80"]
            window["p80"] = limit
            if _number(window.get("median")) and window["median"] > limit:
                window["median"] = limit
        windows[name] = window
    capped["windows"] = windows
    return capped


def admission(evidence, need, outstanding=(), *, now=None, freshness=600,
              buffer=10, small_task=False):
    """Check percentage-point p80 against both windows. Never infer reset usage.

    Completed usage is covered only by an observation taken after completion;
    active or unknown reservations remain outstanding regardless of observation age.
    """
    now = time.time() if now is None else now
    if not _number(buffer) or buffer > 100:
        raise ValueError("invalid safety buffer")
    account = evidence.get("account_ref")
    selected = observation(account, [evidence], clock=lambda: now,
                           freshness=freshness, small_task=small_task)
    waits = []
    exhausted_waits = []
    windows = {w["window"]: w for w in _canonical_windows(selected.get("windows", ()))}
    observed = quota_forecast.parse_time(selected.get("observed_at"))
    provider_reported = (selected.get("source") in {"magpie", "official", "cli", "claude_rate_limit_event"}
                         or selected.get("provenance") == "OFFICIAL_VIA_CLI")
    uncertain = not selected["fresh"]
    for name in ("five_hour", "weekly"):
        window = windows.get(name, {})
        p80 = (need.get("windows", {}).get(name) or {}).get("p80")
        used = window.get("used_percent")
        reset_raw = window.get("resets_at")
        reset = float(reset_raw) if _number(reset_raw) else quota_forecast.parse_time(reset_raw)
        known = selected["fresh"] and _number(used) and _number(p80) and not (reset is not None and reset <= now)
        if not known:
            uncertain = True
            # Explicitly bounded small work still cannot override known exhaustion.
            if small_task and _number(p80) and 0 < p80 <= 1 and not (_number(used) and used >= 100 and (reset is None or reset > now)):
                continue
            # Stale (unexhausted) evidence must not lock admission until a distant window reset.
            is_exhausted = _number(used) and used >= 100
            wait_until = (reset if reset is not None and reset > now else None) if is_exhausted else None
            waits.append((name, wait_until))
            if is_exhausted:
                exhausted_waits.append(wait_until)
            continue
        reserved = 0
        for row in outstanding:
            if row.get("account_ref") != account:
                continue
            if row.get("state") == "UNKNOWN" or row.get("quota_state") == "UNKNOWN":
                uncertain = True
            completed = quota_forecast.parse_time(row.get("reconciled_at"))
            finished = row.get("state") != "ACTIVE" and completed is not None and observed is not None and completed < observed
            if finished and (provider_reported or (row.get("state") != "UNKNOWN" and row.get("quota_state") != "UNKNOWN")):
                # A provider-reported percentage taken after completion already
                # counts that task's spend, measured or not; holding its estimate
                # as well would double-book and eventually stall the account.
                continue
            amount = row.get("actual_windows", {}).get(name) if row.get("state") not in {"ACTIVE", "UNKNOWN"} else None
            details = row.get("actual_observations", [])
            if amount is not None and details and observed is not None and all(
                    quota_forecast.parse_time(o.get("observed_at")) is not None and
                    _number(o.get("windows", {}).get(name)) for o in details):
                amount = sum(o["windows"][name] for o in details
                             if quota_forecast.parse_time(o["observed_at"]) >= observed)
            if amount is None:
                amount = row.get("quota_windows", {}).get(name, 0)
            if not _number(amount):
                uncertain = True
                waits.append((name, reset if reset is not None and reset > now else None))
                continue
            reserved += amount
        released = need["windows"][name].get("reserve_released_until")
        # Only for the window it was released for: a renewed week keeps its reserve.
        margin = (0 if name == "weekly" and _number(released) and reset is not None
                  and now < released and abs(reset - released) <= 900 else buffer)
        # A spent window always waits, however small the need.
        if p80 + reserved > 100 - used - margin or margin == 0 and used >= 100:
            wait_until = reset if reset is not None and reset > now else None
            waits.append((name, wait_until))
            if used >= 100:
                exhausted_waits.append(wait_until)
    if waits and all(r is not None for _, r in waits):
        until = quota_forecast.iso(max(r for _, r in waits))
    elif exhausted_waits and all(r is not None for r in exhausted_waits):
        until = quota_forecast.iso(max(exhausted_waits))
    else:
        until = None
    return {"decision": "quota_wait" if waits else "ok", "reason": "quota_capacity" if waits else "quota_fit",
            "state": "UNKNOWN" if uncertain else "OBSERVED", "blocking_windows": [w for w, _ in waits],
            "until": until,
            "uncertain": uncertain or any(r is None for _, r in waits)}


def settlement(observations, estimate, *, usage_unknown):
    """Reproducible measured counters; conversion uses the admission's frozen rates.

    A price-derived percentage is still an estimate, never provider attribution.
    Unknown percentage spend therefore remains held across provider refreshes.
    """
    fields = {"input": "input_units", "cache_read": "cache_read_units", "cache_write": "cache_write_units",
              "output": "output_units", "reasoning": "reasoning_units"}
    counters = {name: (sum(o[field] for o in observations) if observations and
                all(o.get(field) is not None and o["status"] in {"OBSERVED", "PARTIAL"} for o in observations) else None)
                for name, field in fields.items()}
    if counters["output"] is not None:
        # Native summaries already include reasoning in output.
        extra = [o for o in observations if o.get("source_kind") != "native_summary"]
        counters["output"] = counters["output"] + sum(o["reasoning_units"] for o in extra) if all(
            o.get("reasoning_units") is not None for o in extra) else None
    turns = len(observations) if observations and all(o.get("source_kind") in {"assistant_message", "step_finish"}
                 and o["status"] == "OBSERVED" for o in observations) else None
    cost = sum(o["cost_micro_units"] for o in observations) / 1_000_000 if observations and all(
        o["status"] == "OBSERVED" and o.get("cost_micro_units") is not None for o in observations) else None
    actual = {name: cost / rate if cost is not None and _number(rate) and rate > 0 else None
              for name, rate in estimate.get("calibration", {}).items()}
    details = [{"id": o["id"], "observed_at": o.get("created_at"),
                "windows": {name: o["cost_micro_units"] / 1_000_000 / rate
                            if o.get("cost_micro_units") is not None and _number(rate) and rate > 0 else None
                            for name, rate in estimate.get("calibration", {}).items()}}
               for o in observations]
    # List-price equivalent of the measured tokens: the same units as the need
    # estimate, used only for delta calibration (never reported as spend).
    model = (estimate.get("estimate") or {}).get("model")
    priced = {name: counters[name] for name in ("input", "cache_read", "output")}
    price_units = None
    # Price measured tokens even when cost or percentage attribution stays
    # unknown (native CLI turn totals settle as PARTIAL/UNKNOWN). The figure
    # only feeds delta calibration, where undercounted tokens can only lower
    # the learned rate and therefore overestimate, never underestimate, the
    # next task's need (#1323).
    if model and all(v is not None for v in priced.values()):
        price_units = pricing.equivalent_cost(model, priced).get("usd")
    return {"state": "UNKNOWN" if usage_unknown or not actual or any(v is None for v in actual.values()) else "ESTIMATED",
            "tokens": counters, "turn_count": turns, "cost_units": cost, "price_units": price_units,
            "actual_windows": actual,
            "observation_ids": [o["id"] for o in observations], "actual_observations": details, "estimate": estimate}


DELTA_SAMPLES = 5  # recent per-window samples whose median is the calibrated rate


def delta_calibration(task_id, before, after, settlements):
    """Conservative units-per-percent from one isolated task's provider-reported delta (#1313 B).

    ``before`` is the task's own admission observation and ``after`` a later fresh
    provider-reported one. The account delta may include usage outside Nerelan, so
    the rate is a lower bound (need is overestimated, never underestimated); one
    extra percentage point absorbs integer rounding. Any other reservation on the
    account overlapping the interval, a reset, a missing count or no increase
    yields nothing.
    """
    start = quota_forecast.parse_time(before.get("observed_at"))
    end = quota_forecast.parse_time(after.get("observed_at"))
    account = after.get("account_ref")
    if before.get("aged_admission") or after.get("aged_admission"):
        return {}  # an aged reading's percentages are padded, not measured
    provider = {"official", "magpie", "cli", "claude_rate_limit_event"}
    # Both ends must be provider readings: an estimated start could overstate usage
    # and shrink the delta, which would make the rate optimistic.
    if (before.get("account_ref") != account or start is None or end is None or start >= end
            or any(o.get("source") not in provider or o.get("state") == "UNKNOWN" for o in (before, after))):
        return {}
    own = [r for r in settlements if r.get("task_id") == task_id and r.get("account_ref") == account]
    if len(own) != 1:
        return {}
    row = own[0]
    created = quota_forecast.parse_time(row.get("created_at"))
    finished = quota_forecast.parse_time(row.get("reconciled_at"))
    units = (row.get("settlement") or {}).get("price_units")
    if (row.get("state") == "ACTIVE" or created is None or finished is None or not start <= created < finished < end
            or not _number(units) or units <= 0):
        return {}
    for other in settlements:
        if other is row or other.get("account_ref") != account:
            continue
        o_start = quota_forecast.parse_time(other.get("created_at"))
        o_end = quota_forecast.parse_time(other.get("reconciled_at"))
        if o_start is None or (o_start < end and (o_end is None or o_end > start)):
            return {}  # another task spent on this account inside the interval
    old = {w["window"]: w for w in _canonical_windows(before.get("windows", ()))}
    result = {}
    for window in _canonical_windows(after.get("windows", ())):
        name = window["window"]
        previous = old.get(name, {})
        used, prior_used = window.get("used_percent"), previous.get("used_percent")
        reset_raw = window.get("resets_at")
        reset = float(reset_raw) if _number(reset_raw) else quota_forecast.parse_time(reset_raw)
        if (name in {"five_hour", "weekly"} and reset is not None and reset > end
                and window.get("resets_at") == previous.get("resets_at")
                and _number(used) and _number(prior_used) and used > prior_used):
            result[name] = units / (used - prior_used + 1)
    return result


def attributable_calibration(before, after, settlements):
    """Learn only from an explicitly exhaustive set of account observation IDs.

    Provider-wide deltas without attribution, resets, overlaps and missing costs
    cannot train an account/window conversion rate.
    """
    start = quota_forecast.parse_time(before.get("observed_at"))
    end = quota_forecast.parse_time(after.get("observed_at"))
    ids = after.get("attributed_observation_ids")
    if before.get("aged_admission") or after.get("aged_admission"):
        return {}
    if (before.get("account_ref") != after.get("account_ref") or not ids or
            len(ids) != len(set(ids)) or start is None or end is None or start >= end):
        return {}
    if after.get("source") not in {"official", "magpie", "cli", "claude_rate_limit_event"}:
        return {}
    if any(r.get("account_ref") == after.get("account_ref") and r.get("state") == "ACTIVE" and
           (at := quota_forecast.parse_time(r.get("created_at"))) is not None and at < end for r in settlements):
        return {}
    eligible = [r for r in settlements if r.get("account_ref") == after.get("account_ref")
                and (at := quota_forecast.parse_time(r.get("reconciled_at"))) is not None and start < at < end]
    facts = [r["settlement"] for r in eligible]
    observed_ids = [i for fact in facts for i in fact.get("observation_ids", [])]
    if not facts or sorted(observed_ids) != sorted(ids) or any(f.get("cost_units") is None for f in facts):
        return {}
    # An execution crossing the observation boundary is not attributable to the interval.
    if any((at := quota_forecast.parse_time(r.get("created_at"))) is None or at <= start for r in eligible):
        return {}
    cost = sum(f["cost_units"] for f in facts)
    old = {w.get("window", w.get("name")): w for w in before.get("windows", [])}
    result = {}
    for window in after.get("windows", []):
        name = window.get("window", window.get("name"))
        previous = old.get(name, {})
        used, prior_used = window.get("used_percent"), previous.get("used_percent")
        raw_reset = window.get("resets_at")
        reset = float(raw_reset) if _number(raw_reset) else quota_forecast.parse_time(raw_reset)
        if (name in {"five_hour", "weekly"} and reset is not None and reset > end and
                window.get("resets_at") == previous.get("resets_at") and
                _number(used) and _number(prior_used) and used > prior_used and cost > 0):
            result[name] = cost / (used - prior_used)
    return result


def goal_fit(tasks, evidence, outstanding=(), *, now=None, buffer=10, alternatives=()):
    """Read-only cumulative forecast of already routed, account-bound task needs.

    Alternatives must already have passed the dispatch router's eligibility filters.
    No resets are simulated and no capacity is reserved by this calculation.
    """
    now = time.time() if now is None else now
    totals = {}
    estimates = []
    for task in tasks:
        account = task.get("account_ref")
        need = task.get("need", {})
        estimates.append(dict(task))
        if not account:
            continue
        total = totals.setdefault(account, {"windows": {n: {"p80": 0} for n in ("five_hour", "weekly")}})
        for name, value in total["windows"].items():
            amount = need.get("windows", {}).get(name, {}).get("p80")
            value["p80"] = value["p80"] + amount if _number(value["p80"]) and _number(amount) else None
    accounts = {}
    for account, total in totals.items():
        observation = evidence.get(account, {"account_ref": account, "state": "UNKNOWN", "windows": []})
        verdict = admission(observation, total, outstanding, now=now, buffer=buffer)
        accounts[account] = {**verdict, "need": total, "observation": observation, "resets": {
            w.get("window", w.get("name")): w.get("resets_at") for w in observation.get("windows", ())}}
    unknown = any(not t.get("account_ref") for t in tasks) or any(v["state"] == "UNKNOWN" for v in accounts.values())
    blocked = any(v["decision"] != "ok" for v in accounts.values())
    status = "UNKNOWN" if unknown else "needs_a_reset" if blocked else "fits_now"
    if not unknown and any(_number(v["p80"]) and v["p80"] > 100 - buffer
                           for total in totals.values() for v in total["windows"].values()):
        status = "needs_another_model"
    alternative_fit = None
    if blocked and not unknown:
        for alternative in alternatives:
            replacement = [alternative if t["task_id"] == alternative["task_id"] else t for t in tasks]
            trial = goal_fit(replacement, evidence, outstanding, now=now, buffer=buffer)
            if trial["status"] == "fits_now":
                status = "needs_another_model"
                alternative_fit = trial
                break
    return {"status": status, "accounts": accounts, "tasks": estimates, "alternative": alternative_fit,
            "uncertain": unknown or any(v["uncertain"] for v in accounts.values())
                         or any(t.get("need", {}).get("uncertain", True) for t in tasks),
            "safety_buffer_percent": buffer, "forecast_only": True,
            "availability_guaranteed": False, "estimated_at": quota_forecast.iso(now)}
