"""Subscription quota beyond the official percentage (P0-3, Owner rule of 2026-10-14).

Each window is reported on the best basis available, in this order:

1. ``official_percent`` - the CLI states the percent used: shown as is.
2. ``official_status`` - the CLI only says allowed / warning / rejected and when it resets:
   shown as availability, and every actual limit hit is listed.
3. ``estimated`` - no official number, but history shows how much a window holds: the
   current use is predicted with an explicit low-high range.
4. ``unknown`` - nothing reliable.

Usage is measured in "units" = list-price equivalent USD (see ``pricing``), because
subscription limits weigh cache reads, writes and output differently, much as prices do.
The estimates only see usage recorded on this machine; if the account is also used
elsewhere, capacity is overestimated, which the result says.

Pure functions only: callers pass in events read elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from .pricing import equivalent_cost

FIVE_HOURS = 5 * 3600
MIN_PERCENT_STEP = 3.0  # smaller official steps are mostly rounding noise


@dataclass(frozen=True)
class UsageEvent:
    at: float           # epoch seconds
    units: float        # list-price equivalent USD


@dataclass(frozen=True)
class PercentSample:
    at: float
    window: str         # "five_hour", "weekly", ...
    resets_at: int      # identifies one window instance
    used_percent: float
    units: float        # usage reported with this sample (since the previous one)


def parse_time(value: Any) -> float | None:
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def iso(epoch: float | None) -> str | None:
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def usage_units(model: str, tokens: Mapping[str, Any]) -> float | None:
    """List-price USD of normalized counters, or None when the model has no list price."""
    cost = equivalent_cost(model, tokens)
    return cost["usd"] if cost.get("usd") is not None else None


def _quantile(values: Sequence[float], q: float) -> float:
    position = (len(values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def capacity_range(samples: Sequence[float], *, single_spread: tuple[float, float] | None = None) -> dict[str, Any] | None:
    """Window capacity in units: median with a low-high range.

    With four or more samples the range is the interquartile spread, so one window with
    unseen usage (another device, an unlogged run) does not swamp it; min and max stay
    visible beside it. Fewer samples use their full spread.
    """
    values = sorted(value for value in samples if value > 0)
    if not values:
        return None
    if len(values) == 1 and single_spread:
        low, high = single_spread
        return {"low": round(low, 4), "mid": round(values[0], 4), "high": round(high, 4), "samples": 1}
    robust = len(values) >= 4
    return {"low": round(_quantile(values, 0.25) if robust else values[0], 4), "mid": round(median(values), 4),
            "high": round(_quantile(values, 0.75) if robust else values[-1], 4), "samples": len(values),
            "min": round(values[0], 4), "max": round(values[-1], 4)}


def capacity_from_percent(samples: Iterable[PercentSample]) -> dict[str, dict[str, Any]]:
    """Per window kind: units per 100%, from official percent steps against measured usage."""
    groups: dict[tuple[str, int], list[PercentSample]] = {}
    for sample in samples:
        groups.setdefault((sample.window, sample.resets_at), []).append(sample)
    per_window: dict[str, list[float]] = {}
    spreads: dict[str, tuple[float, float]] = {}
    for (window, _), items in groups.items():
        items.sort(key=lambda s: s.at)
        step = items[-1].used_percent - items[0].used_percent
        units = sum(s.units for s in items[1:])  # the first sample's use is already in its percent
        if step < MIN_PERCENT_STEP or units <= 0:
            continue
        per_window.setdefault(window, []).append(units * 100 / step)
        # Official percents are whole numbers: each end may be off by up to one point.
        spreads[window] = (units * 100 / (step + 1), units * 100 / max(step - 1, 0.5))
    return {window: capacity_range(values, single_spread=spreads.get(window))
            for window, values in per_window.items()}


def rolling_blocks(events: Sequence[UsageEvent], *, length: int = FIVE_HOURS,
                   align: int = 3600) -> list[dict[str, Any]]:
    """Group usage into windows opened by the first request after the previous one ended.

    A Claude window starts at the top of the hour of that request (first message at 04:07
    -> window 04:00-09:00, matching the reset time the CLI reports).
    """
    blocks: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda e: e.at):
        if not blocks or event.at >= blocks[-1]["end"]:
            start = event.at - event.at % align if align else event.at
            blocks.append({"start": start, "end": start + length, "units": 0.0})
        blocks[-1]["units"] += event.units
    return blocks


def usage_between(events: Sequence[UsageEvent], start: float, end: float) -> float:
    return sum(e.units for e in events if start <= e.at <= end)


def calibrate(samples: Sequence[Mapping[str, Any]], events: Sequence[UsageEvent],
              *, length: int) -> dict[str, Any] | None:
    """Window capacity from official percents: local usage in the window / percent used.

    Each window instance (one reset time) contributes its latest reading, which has the
    most usage behind it. Readings under 10% are too coarse to divide by.
    """
    latest: dict[int, Mapping[str, Any]] = {}
    for sample in samples:
        reset = sample.get("resets_at")
        if type(reset) is int and sample.get("used_percent", 0) >= 10:
            key = round(reset / 60)  # two sources may report the same reset a second apart
            if key not in latest or sample["at"] > latest[key]["at"]:
                latest[key] = sample
    values, spread = [], None
    for sample in latest.values():
        used_units = usage_between(events, sample["resets_at"] - length, sample["at"])
        if used_units <= 0:
            continue
        pct = sample["used_percent"]
        values.append(used_units * 100 / pct)
        spread = (used_units * 100 / (pct + 1), used_units * 100 / max(pct - 1, 1))
    return capacity_range(values, single_spread=spread if len(values) == 1 else None)


def capacity_from_hits(events: Sequence[UsageEvent], hits: Sequence[float],
                       *, length: int = FIVE_HOURS) -> dict[str, Any] | None:
    """Units a window held when the CLI reported the limit was reached.

    One sample per window (its first hit: retries after it add nothing). A hit in a window
    holding far less than the others is most likely the weekly limit, not this one, so with
    three or more samples those below 60% of the median are left out.
    """
    blocks = rolling_blocks(events, length=length)
    first_hit: dict[float, float] = {}
    for hit in sorted(set(hits)):
        block = next((b for b in blocks if b["start"] <= hit < b["end"]), None)
        if block is not None and block["start"] not in first_hit:
            first_hit[block["start"]] = hit
    samples = [used for start, hit in first_hit.items() if (used := usage_between(events, start, hit)) > 0]
    if len(samples) >= 3:
        middle = median(samples)
        samples = [value for value in samples if value >= 0.6 * middle]
    return capacity_range(samples)


def estimated_window(window: str, *, used_units: float, capacity: Mapping[str, Any],
                     resets_at: float | None, now: float) -> dict[str, Any]:
    """Predicted percent used with the range the capacity spread allows."""
    low = used_units / capacity["high"] * 100
    high = used_units / capacity["low"] * 100
    mid = used_units / capacity["mid"] * 100
    clamp = lambda value: round(min(max(value, 0.0), 100.0), 1)  # noqa: E731
    return {"window": window, "basis": "estimated", "used_percent": clamp(mid),
            "used_percent_range": [clamp(low), clamp(high)], "used_units": round(used_units, 4),
            "capacity_units": dict(capacity), "resets_at": iso(resets_at), "reset_passed": False,
            "status": None, "remaining_units_range": [round(max(capacity["low"] - used_units, 0.0), 4),
                                                       round(max(capacity["high"] - used_units, 0.0), 4)]}


def availability(status: str | None) -> str | None:
    return {"allowed": "available", "allowed_warning": "near_limit", "rejected": "limit_reached"}.get(status or "")


def guard(window: Mapping[str, Any], need_units: float | None) -> dict[str, Any]:
    """Can the next task fit in this window? ``switch`` / ``warn`` / ``ok`` with the reason."""
    if window.get("reset_passed"):
        return {"decision": "ok", "reason": "window_reset"}
    status = window.get("status")
    if status == "rejected" or window.get("availability") == "limit_reached":
        return {"decision": "switch", "reason": "limit_reached"}
    remaining = window.get("remaining_units_range")
    if need_units is not None and remaining:
        if remaining[1] < need_units:
            return {"decision": "switch", "reason": "predicted_insufficient"}
        if remaining[0] < need_units:
            return {"decision": "warn", "reason": "possibly_insufficient"}
    used = window.get("used_percent")
    if window.get("basis") == "official_percent" and isinstance(used, (int, float)):
        if used >= 98:
            return {"decision": "switch", "reason": "almost_exhausted"}
        if used >= 90:
            return {"decision": "warn", "reason": "nearly_exhausted"}
    if window.get("basis") == "estimated" and isinstance(used, (int, float)):
        # An estimate moves a role only when even its optimistic end is exhausted.
        low = (window.get("used_percent_range") or [used, used])[0]
        if low >= 98:
            return {"decision": "switch", "reason": "almost_exhausted"}
        if used >= 90:
            return {"decision": "warn", "reason": "nearly_exhausted"}
    if status == "allowed_warning":
        return {"decision": "warn", "reason": "near_limit"}
    if remaining and need_units is None:
        return {"decision": "ok", "reason": "no_task_estimate"}
    return {"decision": "ok", "reason": "fits" if remaining else "no_signal"}


def worst(decisions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rank = {"switch": 2, "warn": 1, "ok": 0}
    return dict(max(decisions, key=lambda d: rank[d["decision"]], default={"decision": "ok", "reason": "no_signal"}))
