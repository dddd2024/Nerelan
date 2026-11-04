"""Identity-conflict checks for Magpie usage correlation (synthetic rows only).

Rows pass through the real parse_usage_ledger / parse_usage_request sanitizers
before reaching correlate_task_usage, exactly as the adapter hands them over. No
gateway, model or provider is contacted, and every value is an invented fixture.
"""
import json

import pytest

from reverse_agent.model_access.magpie_usage import (
    correlate_task_usage, parse_usage_ledger, parse_usage_request,
)

T = "2026-10-25T10:00:00Z"
T_EPOCH = 1792922400.0  # parse_time(T)
TASK = "sess-task-1"
OTHER = "sess-other"
ACCOUNT_A = "acct-a@example.test"
ACCOUNT_B = "acct-b@example.test"
TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "cache_write_1h", "reasoning")
ORDERS = pytest.mark.parametrize("order", ["forward", "reverse"])


def wire(rid, session=TASK, account=ACCOUNT_A, **extra):
    """A raw ledger row as the gateway emits it; None models an absent field."""
    base = {"rid": rid, "route_id": 7, "t": T, "agent": "opencode", "provider": "anthropic",
            "providerAccount": account, "model": "claude-fable-5-1", "served": "claude-fable-5-1",
            "session": session, "in": 1000, "out": 200, "cache_read": 3000, "cache_write": 500,
            "cache_write_1h": 0, "reasoning": 40, "cost": 0.0125, "priced": True, "ms": 900}
    base.update(extra)
    return base


def page(*rows):
    """Real page parser: the rows come back sanitized, as the adapter delivers them."""
    return parse_usage_ledger({"rows": list(rows)})["rows"]


def arranged(order, *rows):
    """The same rows in either arrival order, so both permutations are exercised."""
    return page(*(rows if order == "forward" else reversed(rows)))


def local(**overrides):
    base = {"id": "obs-1", "input_units": 1000, "output_units": 200, "reasoning_units": 40,
            "cache_read_units": 3000, "cache_write_units": 500, "cost_micro_units": None}
    base.update(overrides)
    return base


def assert_ambiguous_and_unattributed(report):
    assert report["request_count"] == 0 and report["requests"] == []
    assert report["basis"] == "unknown"
    assert report["identity_conflicts"] == 1 and report["attribution_incomplete"] is True
    assert report["totals"]["requests"] == 0
    assert all(report["totals"][name] is None for name in TOKEN_FIELDS)
    assert report["totals"]["cost_usd"] is None
    # Neither side of the conflict is counted for the task, whichever row came first.
    assert report["accounts"] == {} and report["served_models"] == {}


@ORDERS
def test_conflicting_sessions_under_one_rid_are_ambiguous_for_the_requested_session(order):
    rows = arranged(order, wire("R", session=TASK), wire("R", session=OTHER))
    report = correlate_task_usage([], rows, sessions=[TASK])
    assert_ambiguous_and_unattributed(report)
    assert report["unattributed_rows"] == 2


@ORDERS
def test_conflicting_sessions_under_one_rid_are_ambiguous_for_the_requested_rid(order):
    rows = arranged(order, wire("R", session=TASK), wire("R", session=OTHER))
    report = correlate_task_usage([], rows, rids=["R"])
    assert_ambiguous_and_unattributed(report)
    assert OTHER not in json.dumps(report)


@ORDERS
def test_conflicting_provider_accounts_under_one_session_are_ambiguous(order):
    rows = arranged(order, wire("R", account=ACCOUNT_A), wire("R", account=ACCOUNT_B))
    report = correlate_task_usage([], rows, sessions=[TASK])
    assert_ambiguous_and_unattributed(report)
    dumped = json.dumps(report)
    assert ACCOUNT_A not in dumped and ACCOUNT_B not in dumped


def test_same_identity_duplicates_remain_a_terminal_update():
    rows = page(wire("R", **{"in": 100}), wire("R", **{"in": 900}))
    report = correlate_task_usage([], rows, sessions=[TASK])
    assert report["request_count"] == 1 and report["duplicate_rids_collapsed"] == 1
    assert report["totals"]["input"] == 900
    assert report["identity_conflicts"] == 0 and report["attribution_incomplete"] is False


@ORDERS
def test_handed_on_attempt_with_another_account_is_not_a_conflict(order):
    attempt = wire("R", account=ACCOUNT_B, handed_on=True, **{"in": 99999})
    final = wire("R", account=ACCOUNT_A, **{"in": 1000})
    report = correlate_task_usage([], arranged(order, attempt, final), sessions=[TASK])
    assert report["identity_conflicts"] == 0 and report["attribution_incomplete"] is False
    assert report["excluded_handed_on"] == 1 and report["request_count"] == 1
    assert report["totals"]["input"] == 1000 and report["accounts"] == {ACCOUNT_A: 1}


def test_missing_identity_is_not_a_conflict_and_is_never_fabricated():
    # A rid with no session cannot borrow the task's session from elsewhere.
    alone = correlate_task_usage([], page(wire("N", session=None)), sessions=[TASK])
    assert alone["request_count"] == 0 and alone["identity_conflicts"] == 0
    assert alone["basis"] == "unknown" and alone["totals"]["input"] is None
    # A missing account next to a known one is not a disagreement either.
    report = correlate_task_usage([], page(wire("A", account=None), wire("A", account=ACCOUNT_A)),
                                  sessions=[TASK])
    assert report["identity_conflicts"] == 0 and report["attribution_incomplete"] is False
    assert report["request_count"] == 1 and report["accounts"] == {ACCOUNT_A: 1}


@ORDERS
def test_unrelated_foreign_conflicts_do_not_wipe_the_requested_row(order):
    rows = arranged(order, wire("OK", session=TASK),
                    wire("F", session=OTHER), wire("F", session="sess-third"),
                    wire("G", session="sess-fourth"), wire("G", session="sess-fifth"))
    report = correlate_task_usage([local()], rows, sessions=[TASK])
    assert report["identity_conflicts"] == 2 and report["attribution_incomplete"] is False
    assert report["request_count"] == 1 and [row["rid"] for row in report["requests"]] == ["OK"]
    assert report["totals"]["input"] == 1000 and report["totals"]["cost_usd"] == pytest.approx(0.0125)
    assert report["basis"] == "magpie_measured" and report["unattributed_rows"] == 4
    dumped = json.dumps(report)
    assert OTHER not in dumped and "sess-third" not in dumped and "sess-fifth" not in dumped


@ORDERS
def test_relevant_conflict_keeps_per_request_evidence_but_aggregate_unknown(order):
    rows = arranged(order, wire("OK", session=TASK),
                    wire("BAD", session=TASK), wire("BAD", session=OTHER))
    report = correlate_task_usage([local()], rows, sessions=[TASK])
    assert report["attribution_incomplete"] is True and report["identity_conflicts"] == 1
    assert [row["rid"] for row in report["requests"]] == ["OK"] and report["request_count"] == 1
    assert report["basis"] == "magpie_measured"
    assert all(report["totals"][name] is None for name in TOKEN_FIELDS)
    assert report["totals"]["cost_usd"] is None and report["totals"]["requests"] == 1
    assert report["local_cross_check"]["observations"] == 1
    assert report["unattributed_rows"] == 2


def test_conflict_outside_the_window_is_still_relevant_by_identity():
    rows = page(wire("W", session=TASK), wire("W", session=OTHER))
    report = correlate_task_usage([], rows, sessions=[TASK],
                                  since=T_EPOCH + 60, until=T_EPOCH + 600)
    assert report["attribution_incomplete"] is True and report["identity_conflicts"] == 1
    assert report["request_count"] == 0 and report["totals"]["input"] is None


def test_no_identity_or_evidence_stays_unknown_not_zero():
    report = correlate_task_usage([], [], sessions=[TASK])
    assert report["basis"] == "unknown" and report["request_count"] == 0
    assert report["totals"]["requests"] == 0 and report["attribution_incomplete"] is False
    assert report["totals"]["input"] is None and report["totals"]["cost_usd"] is None
    rows = page(wire(None, session=None), wire("", session=None))
    unidentified = correlate_task_usage([], rows, sessions=[TASK])
    assert unidentified["request_count"] == 0 and unidentified["basis"] == "unknown"
    assert unidentified["totals"]["input"] is None and unidentified["totals"]["cost_usd"] is None


def test_local_only_observations_do_not_become_a_measured_zero():
    report = correlate_task_usage([local()], page(wire("X", session=OTHER)), sessions=[TASK])
    assert report["basis"] == "local_only" and report["request_count"] == 0
    assert report["totals"]["input"] is None and report["totals"]["cost_usd"] is None
    assert report["local_cross_check"] is None


def test_unpriced_or_unknown_bucket_stays_unknown_while_known_tokens_remain():
    report = correlate_task_usage([], page(wire("U", priced=False, cost=None, cache_read=None)),
                                  sessions=[TASK])
    assert report["totals"]["cost_usd"] is None and report["totals"]["cache_read"] is None
    assert report["totals"]["input"] == 1000 and report["totals"]["unpriced_calls"] == 1


def test_explicit_measured_zero_remains_a_valid_zero():
    zero = {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0, "cache_write_1h": 0,
            "reasoning": 0, "cost": 0.0, "priced": True}
    report = correlate_task_usage([], page(wire("Z", **zero)), sessions=[TASK])
    assert report["basis"] == "magpie_measured" and report["attribution_incomplete"] is False
    assert all(report["totals"][name] == 0 for name in TOKEN_FIELDS)
    assert report["totals"]["cost_usd"] == 0.0 and report["totals"]["priced_calls"] == 1


def test_malformed_direct_numbers_are_not_counted():
    raw = parse_usage_request(wire("M"))
    raw.update({"input": True, "cost_usd": float("nan")})
    report = correlate_task_usage([], [raw], sessions=[TASK])
    assert report["totals"]["input"] is None and report["totals"]["cost_usd"] is None
    assert report["totals"]["priced_calls"] == 0 and report["totals"]["unpriced_calls"] == 1


def test_cap_and_incomplete_flag_are_reported_together():
    rows = [wire("r%d" % i) for i in range(201)] + [wire("BAD", session=TASK), wire("BAD", session=OTHER)]
    report = correlate_task_usage([], page(*rows), sessions=[TASK])
    assert report["request_count"] == 201 and len(report["requests"]) == 200
    assert report["requests_truncated"] is True and report["attribution_incomplete"] is True
    assert report["totals"]["input"] is None


def test_private_values_never_reach_conflict_diagnostics():
    rows = page(wire("F", session=OTHER, account="foreign-a@example.test"),
                wire("F", session="sess-third", account="foreign-b@example.test"))
    report = correlate_task_usage([], rows, sessions=[TASK])
    dumped = json.dumps(report)
    assert report["identity_conflicts"] == 1 and report["attribution_incomplete"] is False
    assert "foreign-" not in dumped and "sess-third" not in dumped and OTHER not in dumped


def test_page_private_value_is_scrubbed_and_never_becomes_a_conflict():
    rows = page(wire("P", session=TASK, account=ACCOUNT_A),
                {**wire("P", session=TASK, account="person@example.test"), "user": "person@example.test"})
    report = correlate_task_usage([], rows, sessions=[TASK])
    assert report["identity_conflicts"] == 0 and report["attribution_incomplete"] is False
    assert "person@example.test" not in json.dumps(report)


def test_one_shot_local_generator_keeps_its_cost_through_a_conflict():
    def generate():
        yield local(cost_micro_units=500)
    rows = page(wire("OK"), wire("BAD", session=TASK), wire("BAD", session=OTHER))
    report = correlate_task_usage(generate(), rows, sessions=[TASK])
    assert report["local_cross_check"]["cost_micro_units"] == 500
    assert report["attribution_incomplete"] is True


@ORDERS
def test_aggregate_cost_overflow_is_unknown_not_infinite(order):
    # Each amount is finite; only their sum overflows, so the task cost is UNKNOWN.
    report = correlate_task_usage([], arranged(order, wire("H1", cost=1e308), wire("H2", cost=1e308)),
                                  sessions=[TASK])
    assert report["request_count"] == 2 and report["totals"]["priced_calls"] == 2
    assert report["totals"]["cost_usd"] is None and report["totals"]["input"] == 2000


@ORDERS
def test_later_finite_row_cannot_resurrect_an_overflowed_cost(order):
    rows = arranged(order, wire("H1", cost=1e308), wire("H2", cost=1e308), wire("H3", cost=0.5))
    report = correlate_task_usage([], rows, sessions=[TASK])
    assert report["request_count"] == 3 and report["totals"]["priced_calls"] == 3
    assert report["totals"]["cost_usd"] is None


def test_explicit_measured_zero_costs_still_sum_to_zero():
    report = correlate_task_usage([], page(wire("Z1", cost=0.0), wire("Z2", cost=0.0)), sessions=[TASK])
    assert report["totals"]["cost_usd"] == 0.0 and report["totals"]["priced_calls"] == 2


def test_ordinary_finite_cost_sum_is_accurate_after_rounding():
    report = correlate_task_usage([], page(wire("S1", cost=0.1), wire("S2", cost=0.2)), sessions=[TASK])
    assert report["totals"]["cost_usd"] == 0.3 and report["totals"]["priced_calls"] == 2
