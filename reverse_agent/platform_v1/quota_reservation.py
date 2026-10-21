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


def canonical_window(name: Any) -> Any:
    """Observation sources name windows differently ("5 hours", "7 days"); admission needs one name."""
    return _WINDOW_NAMES.get(str(name).strip().lower(), name) if name is not None else name


def _canonical_windows(windows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(w, window=canonical_window(w.get("window", w.get("name")))) for w in windows
            if isinstance(w, Mapping)]


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


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
            fresh = known and at is not None and 0 <= now - at <= freshness
            result.append((fresh, rank if known else 0, at if at is not None else -math.inf,
                           dict(item, observed_at=quota_forecast.iso(at), fresh=bool(fresh),
                                windows=_canonical_windows(item.get("windows") or ()))))
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
    windows = {w["window"]: w for w in _canonical_windows(evidence.get("windows", ()))}
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
            waits.append((name, reset if reset is not None and reset > now else None))
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
        if p80 + reserved > 100 - used - buffer:
            waits.append((name, reset if reset is not None and reset > now else None))
    return {"decision": "quota_wait" if waits else "ok", "reason": "quota_capacity" if waits else "quota_fit",
            "state": "UNKNOWN" if uncertain else "OBSERVED", "blocking_windows": [w for w, _ in waits],
            "until": quota_forecast.iso(max(r for _, r in waits)) if waits and all(r is not None for _, r in waits) else None,
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
    return {"state": "UNKNOWN" if usage_unknown or not actual or any(v is None for v in actual.values()) else "ESTIMATED",
            "tokens": counters, "turn_count": turns, "cost_units": cost, "actual_windows": actual,
            "observation_ids": [o["id"] for o in observations], "actual_observations": details, "estimate": estimate}


def attributable_calibration(before, after, settlements):
    """Learn only from an explicitly exhaustive set of account observation IDs.

    Provider-wide deltas without attribution, resets, overlaps and missing costs
    cannot train an account/window conversion rate.
    """
    start = quota_forecast.parse_time(before.get("observed_at"))
    end = quota_forecast.parse_time(after.get("observed_at"))
    ids = after.get("attributed_observation_ids")
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
