"""Evidence-driven single vs agent_team orchestration choice (#1267).

The Owner requirement: multi-model team mode buys parallelism and model fit at
the price of a planner call, per-task worktrees/validation/handoffs and more
places to fail, so for small goals it can cost more than one model doing the
work. The mode must be chosen by measured evidence, not by default.

This module is the pure decision core; it performs no I/O. The caller records
the returned decision with the goal (the existing goal payloads already carry
``orchestration_mode``); measured runs feed :func:`cost_per_accepted_change`
and :func:`update_break_even`, whose output becomes the next ``break_even``.

The break-even model is linear in the estimated task count ``n``: a single
model costs about ``S·n`` (same per-task price at any size), the team costs
``C + T·n`` (planner plus coordination overhead ``C``, per-task ``T`` — often
cheaper per task through model fit). The team wins for ``n > C/(S−T)``, which
is the measured ``cross_over_task_count``; a team whose marginal per-task cost
is not lower yields cross-over 0 — single at every size. Defaults until
measurements exist follow the issue: ``single`` for an objective that clearly
maps to one task, otherwise ``agent_team``. An Owner pin always wins and is
reported as such. Unknown token or money counts stay UNKNOWN — a run with
unknown usage is counted as such, never silently averaged in as zero.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Iterable, Mapping

_MODES = frozenset({"single", "agent_team"})
_MIN_OBSERVATIONS_PER_MODE = 3


def _positive(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def _known_number(value: Any) -> float | None:
    """A measurement that exists, including an honest zero (but not a bool)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def _mode(value: Any) -> str | None:
    return value if isinstance(value, str) and value in _MODES else None


def _tokens_unknown(tokens: Any) -> bool:
    if not isinstance(tokens, Mapping) or not tokens:
        return True
    return any(value is None for value in tokens.values())


def select_orchestration(
    *,
    size_estimate: Mapping[str, Any],
    break_even: Mapping[str, Any] | None = None,
    pin: Any = None,
) -> dict[str, Any]:
    """Pick the orchestration mode for one goal from evidence.

    ``size_estimate`` carries the planner's ``task_count``. ``break_even`` is
    the measured comparison record from :func:`update_break_even` (may be
    ``None``). ``pin`` is an explicit Owner choice and always wins with reason
    ``owner_pin``. At exactly the cross-over the cheaper-to-trust choice is
    ``single`` (the team has to beat the single model, not tie it).
    """
    pinned = _mode(pin)
    if pinned is not None:
        return {"mode": pinned, "reason": "owner_pin",
                "evidence": {"pin": pinned, "break_even_used": None}}
    estimate = _positive(size_estimate.get("task_count")) if isinstance(size_estimate, Mapping) else None
    cross_over = (_positive(break_even.get("cross_over_task_count"))
                  if isinstance(break_even, Mapping) else None)
    if cross_over is not None and estimate is not None:
        mode = "single" if estimate <= cross_over else "agent_team"
        return {"mode": mode, "reason": "measured_break_even",
                "evidence": {"estimated_task_count": estimate,
                             "cross_over_task_count": cross_over,
                             "break_even_used": True}}
    # A decisive negative measurement: the fitted marginal team cost is not
    # lower, so no size makes the team cheaper — single at every estimate.
    if (isinstance(break_even, Mapping) and break_even.get("sufficient_evidence") is True
            and break_even.get("hint") == "team_per_task_not_cheaper" and estimate is not None):
        return {"mode": "single", "reason": "measured_team_not_cheaper",
                "evidence": {"estimated_task_count": estimate, "break_even_used": True}}
    # Default until evidence exists: one task → one model; more → team mode.
    mode = "single" if estimate is not None and estimate <= 1 else "agent_team"
    reason = "default_single_task" if mode == "single" else "default_multi_task_no_evidence"
    return {"mode": mode, "reason": reason,
            "evidence": {"estimated_task_count": estimate, "break_even_used": False}}


def cost_per_accepted_change(runs: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Accepted-output-normalized cost and time per orchestration mode.

    Each ``runs`` row is one goal execution: ``mode``, the outcome (``accepted``
    — passed functional checks *and* independent review), per-role usage
    (``tokens`` by planner/executor/reviewer, ``None`` where the vendor did not
    expose it), ``cost_units`` (list-price equivalent, ``None`` if unknown),
    ``wall_seconds`` and ``executor_turns``. Cost is divided by accepted runs,
    never by attempted runs; a run with unknown usage is counted in
    ``unknown_usage_runs`` instead of entering any average as zero.
    """
    rows = [dict(row) for row in runs if isinstance(row, Mapping) and _mode(row.get("mode"))]
    result: dict[str, Any] = {}
    for mode in sorted(_MODES):
        mine = [row for row in rows if row["mode"] == mode]
        accepted = [row for row in mine if row.get("accepted") is True]
        known_cost = [row for row in accepted if _known_number(row.get("cost_units")) is not None]
        entry: dict[str, Any] = {
            "runs": len(mine), "accepted_runs": len(accepted),
            "unknown_usage_runs": sum(1 for row in mine if _tokens_unknown(row.get("tokens"))),
        }
        # An average over only the runs that happened to report cost is
        # selection-biased: any accepted run with UNKNOWN cost keeps the whole
        # average UNKNOWN instead of entering as zero.
        entry["cost_per_accepted"] = (
            round(sum(float(row["cost_units"]) for row in known_cost) / len(accepted), 6)
            if accepted and len(known_cost) == len(accepted) else None)
        entry["cost_known_accepted_runs"] = len(known_cost)
        timed = [_positive(row.get("wall_seconds")) for row in accepted]
        entry["median_wall_seconds_per_accepted"] = (
            round(statistics.median(timed), 3) if accepted and all(v is not None for v in timed) else None)
        result[mode] = entry
    return result


def update_break_even(runs: Iterable[Mapping[str, Any]], *, previous: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Recompute the measured single/team cross-over from accepted runs.

    Uses the linear model from the module docstring: ``S`` = median
    cost-per-task of accepted single runs (no overhead term); the team's
    ``cost = C + T·n`` is fitted by least squares over its accepted runs
    (median ratios would absorb the overhead into ``T`` and hide it);
    ``cross_over_task_count = C/(S−T)``. Per the issue's evidence bar — at
    least 3 tasks per size band in both modes before the default may move —
    every ``size_band`` represented in the data must hold
    ``_MIN_OBSERVATIONS_PER_MODE`` usable accepted runs per mode, otherwise the
    previous break-even is kept and flagged ``insufficient_evidence``. When
    the team's marginal per-task cost is not lower, no size makes it cheaper:
    the record is decisive (``sufficient_evidence`` with hint
    ``team_per_task_not_cheaper``) and the selector maps every estimate to
    single from it, instead of silently falling back to the default.
    """
    rows = [dict(row) for row in runs
            if isinstance(row, Mapping) and _mode(row.get("mode")) and row.get("accepted") is True]
    usable: dict[str, dict[str, list[tuple[float, float]]]] = {}
    for row in rows:
        cost, count = _known_number(row.get("cost_units")), _positive(row.get("task_count"))
        if cost is None or count is None:
            continue
        band = row.get("size_band") if isinstance(row.get("size_band"), str) and row.get("size_band") else "unbanded"
        usable.setdefault(band, {"single": [], "agent_team": []})[row["mode"]].append((cost, count))
    band_counts = {band: {mode: len(values) for mode, values in sides.items()}
                   for band, sides in sorted(usable.items())}
    record: dict[str, Any] = {
        "usable_runs": {mode: sum(counts[mode] for counts in band_counts.values())
                        for mode in sorted(_MODES)},
        "usable_runs_per_band": band_counts,
        "cross_over_task_count": None,
        "sufficient_evidence": False,
        "carried_from_previous": False,
        "hint": None,
    }
    enough = (bool(band_counts) and all(
        min(counts["single"], counts["agent_team"]) >= _MIN_OBSERVATIONS_PER_MODE
        for counts in band_counts.values()))
    if not enough:
        record["hint"] = "insufficient_evidence"
        if isinstance(previous, Mapping) and _known_number(previous.get("cross_over_task_count")) is not None:
            record["cross_over_task_count"] = previous["cross_over_task_count"]
            record["carried_from_previous"] = True
        return record
    pooled_single = [(cost, count) for sides in usable.values() for cost, count in sides["single"]]
    pooled_team = [(cost, count) for sides in usable.values() for cost, count in sides["agent_team"]]
    single_per_task = statistics.median(cost / count for cost, count in pooled_single)
    # Team cost follows the linear model C + T·n; the median of cost/n is NOT
    # the marginal cost when overhead is present (it drifts down with n), so
    # fit slope T and intercept C by least squares instead.
    team_n = [float(count) for _, count in pooled_team]
    team_c = [float(cost) for cost, _ in pooled_team]
    if len(set(team_n)) < 2:
        record["hint"] = "degenerate_team_sizes"
        return record
    n_mean, c_mean = statistics.mean(team_n), statistics.mean(team_c)
    denom = sum((n - n_mean) ** 2 for n in team_n)
    if denom <= 0:
        record["hint"] = "degenerate_team_sizes"
        return record
    team_per_task = sum((n - n_mean) * (c - c_mean) for n, c in zip(team_n, team_c)) / denom
    overhead = c_mean - team_per_task * n_mean
    record["unit_cost_per_task"] = {"single": round(single_per_task, 6),
                                    "agent_team": round(team_per_task, 6)}
    if team_per_task >= single_per_task:
        # The team's marginal per-task cost is not lower: no size makes it
        # cheaper. There is no cross-over quantity to report; the decisive
        # measurement lives in the hint the selector reads explicitly.
        record["sufficient_evidence"] = True
        record["hint"] = "team_per_task_not_cheaper"
        return record
    if overhead <= 0:
        # No measurable coordination overhead: the team wins from the first
        # split, i.e. every goal above a single task.
        record["cross_over_task_count"] = 1.0
        record["sufficient_evidence"] = True
        return record
    record["team_overhead"] = round(overhead, 6)
    record["cross_over_task_count"] = round(overhead / (single_per_task - team_per_task), 3)
    record["sufficient_evidence"] = True
    return record
