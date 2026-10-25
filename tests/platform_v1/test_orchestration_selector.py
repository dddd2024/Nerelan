"""Provider-free checks for the #1267 orchestration decision core.

Covers the acceptance items: the selector's pin/measure/default ladder and
the accepted-output-normalized cost computation with UNKNOWN preservation.
"""

import math

from reverse_agent.platform_v1.orchestration_selector import (
    cost_per_accepted_change, select_orchestration, update_break_even,
)


_SENTINEL = object()


def run(mode, *, accepted=True, cost=10.0, count=4, tokens=_SENTINEL, wall=60.0, band="trivial"):
    return {"mode": mode, "accepted": accepted, "cost_units": cost, "task_count": count,
            "tokens": {"planner": 100, "executor": 500, "reviewer": 200} if tokens is _SENTINEL else tokens,
            "wall_seconds": wall, "size_band": band}


# --- selector -----------------------------------------------------------------


def test_owner_pin_wins_over_everything():
    decision = select_orchestration(size_estimate={"task_count": 8}, pin="single",
                                    break_even={"cross_over_task_count": 1.0})
    assert decision == {"mode": "single", "reason": "owner_pin",
                        "evidence": {"pin": "single", "break_even_used": None}}
    assert select_orchestration(size_estimate={"task_count": 1}, pin="agent_team")["mode"] == "agent_team"
    # A malformed pin is not a pin: the evidence ladder applies.
    assert select_orchestration(size_estimate={"task_count": 1}, pin="parallel_ultra")["mode"] == "single"


def test_measured_break_even_decides_by_task_count():
    break_even = {"cross_over_task_count": 4.0}
    below = select_orchestration(size_estimate={"task_count": 3}, break_even=break_even)
    above = select_orchestration(size_estimate={"task_count": 6}, break_even=break_even)
    exact = select_orchestration(size_estimate={"task_count": 4}, break_even=break_even)
    assert (below["mode"], above["mode"], exact["mode"]) == ("single", "agent_team", "single")
    assert all(d["reason"] == "measured_break_even" for d in (below, above, exact))
    assert above["evidence"]["break_even_used"] is True


def test_default_until_evidence_exists():
    one_task = select_orchestration(size_estimate={"task_count": 1})
    multi = select_orchestration(size_estimate={"task_count": 3})
    unknown = select_orchestration(size_estimate={})
    assert (one_task["mode"], one_task["reason"]) == ("single", "default_single_task")
    assert (multi["mode"], multi["reason"]) == ("agent_team", "default_multi_task_no_evidence")
    assert unknown["mode"] == "agent_team" and unknown["evidence"]["estimated_task_count"] is None


# --- cost per accepted change ---------------------------------------------------


def test_cost_divides_by_accepted_runs_never_attempts():
    runs = [run("single", cost=10.0), run("single", cost=10.0, accepted=False),
            run("single", cost=10.0)]
    report = cost_per_accepted_change(runs)["single"]
    assert report["runs"] == 3 and report["accepted_runs"] == 2
    assert report["cost_per_accepted"] == 10.0  # (10+10)/2, the failed run excluded
    assert report["cost_known_accepted_runs"] == 2


def test_unknown_usage_is_counted_not_zeroed():
    runs = [run("agent_team", tokens={"planner": 100, "executor": None, "reviewer": 200}),
            run("agent_team", tokens=None),
            run("agent_team", tokens={"planner": 1, "executor": 2, "reviewer": 3})]
    report = cost_per_accepted_change(runs)["agent_team"]
    assert report["unknown_usage_runs"] == 2  # missing dict or a None role is UNKNOWN
    assert report["accepted_runs"] == 3


def test_unknown_cost_blocks_the_average_and_zero_is_known():
    runs = [run("single", cost=None), run("single", cost=0.0)]
    report = cost_per_accepted_change(runs)["single"]
    assert report["cost_per_accepted"] is None
    assert report["cost_known_accepted_runs"] == 1  # only the explicit zero
    boolean = cost_per_accepted_change([run("single", cost=False)])["single"]
    assert boolean["cost_per_accepted"] is None  # a bool is not a cost


def test_median_wall_time_requires_all_accepted_timed():
    ok = cost_per_accepted_change([run("single", wall=30.0), run("single", wall=90.0)])["single"]
    assert ok["median_wall_seconds_per_accepted"] == 60.0
    missing = cost_per_accepted_change([run("single", wall=30.0), run("single", wall=None)])["single"]
    assert missing["median_wall_seconds_per_accepted"] is None


def test_no_accepted_runs_reports_no_average():
    report = cost_per_accepted_change([run("single", accepted=False)])["single"]
    assert report["accepted_runs"] == 0
    assert report["cost_per_accepted"] is None and report["median_wall_seconds_per_accepted"] is None


# --- break-even -----------------------------------------------------------------


def team_runs(costs_counts):
    return [run("agent_team", cost=c, count=n) for c, n in costs_counts]


def single_runs(costs_counts):
    return [run("single", cost=c, count=n) for c, n in costs_counts]


def test_break_even_from_linear_model():
    # single: 10 per task (n = 2, 4, 8); team: 20 + 5n → cross-over at 20/(10-5) = 4.
    runs = single_runs([(20.0, 2), (40.0, 4), (80.0, 8)]) + team_runs([(30.0, 2), (40.0, 4), (60.0, 8)])
    record = update_break_even(runs)
    assert record["sufficient_evidence"] is True
    assert record["unit_cost_per_task"] == {"single": 10.0, "agent_team": 5.0}
    assert record["team_overhead"] == 20.0
    assert record["cross_over_task_count"] == 4.0


def test_break_even_needs_three_usable_runs_per_mode():
    runs = single_runs([(20.0, 2), (40.0, 4)]) + team_runs([(30.0, 2), (40.0, 4)])
    sparse = update_break_even(runs)
    assert sparse["sufficient_evidence"] is False and sparse["hint"] == "insufficient_evidence"
    # Unknown cost or task count rows are not usable and do not pad the count.
    padded = update_break_even(runs + [run("single", cost=None, count=8), run("agent_team", cost=50.0, count=0)])
    assert padded["usable_runs"] == {"single": 2, "agent_team": 2}


def test_break_even_carries_previous_when_sparse():
    runs = single_runs([(20.0, 2), (40.0, 4)]) + team_runs([(30.0, 2), (40.0, 4)])
    record = update_break_even(runs, previous={"cross_over_task_count": 3.5})
    assert record["cross_over_task_count"] == 3.5
    assert record["carried_from_previous"] is True and record["sufficient_evidence"] is False
    # No previous measurement: no cross-over to report.
    assert update_break_even(runs)["cross_over_task_count"] is None


def test_team_per_task_not_cheaper_reports_hint_and_no_cross_over():
    runs = single_runs([(10.0, 2), (20.0, 4), (40.0, 8)]) + team_runs([(30.0, 2), (60.0, 4), (120.0, 8)])
    record = update_break_even(runs)
    assert record["sufficient_evidence"] is False
    assert record["hint"] == "team_per_task_not_cheaper"
    assert record["cross_over_task_count"] is None


def test_zero_overhead_team_wins_from_first_split():
    runs = single_runs([(20.0, 2), (40.0, 4), (80.0, 8)]) + team_runs([(10.0, 2), (20.0, 4), (40.0, 8)])
    record = update_break_even(runs)
    assert record["sufficient_evidence"] is True and record["cross_over_task_count"] == 1.0


def test_selector_round_trip_with_measured_break_even():
    runs = single_runs([(20.0, 2), (40.0, 4), (80.0, 8)]) + team_runs([(30.0, 2), (40.0, 4), (60.0, 8)])
    break_even = update_break_even(runs)
    assert select_orchestration(size_estimate={"task_count": 3}, break_even=break_even)["mode"] == "single"
    assert select_orchestration(size_estimate={"task_count": 7}, break_even=break_even)["mode"] == "agent_team"


def test_records_are_json_safe_and_finite():
    import json
    runs = single_runs([(20.0, 2), (40.0, 4), (80.0, 8)]) + team_runs([(30.0, 2), (40.0, 4), (60.0, 8)])
    for payload in (select_orchestration(size_estimate={"task_count": 2}),
                    cost_per_accepted_change(runs), update_break_even(runs)):
        json.dumps(payload, allow_nan=False)
    assert all(math.isfinite(v) for v in
               update_break_even(runs)["unit_cost_per_task"].values())
