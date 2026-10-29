"""Fixture-only Magpie usage/route correlation checks: no gateway is contacted.

Field names follow the upstream source (internal/usage Record/Row and
internal/gateway/session_route.go), so the fixtures mirror what
GET /v1/magpie/usage/requests and GET /v1/magpie/route actually return.
"""

import pytest

from reverse_agent.model_access.magpie_usage import (
    correlate_task_usage, parse_route, parse_usage_ledger, parse_usage_request,
)

T = "2026-10-25T10:00:00Z"
T_EPOCH = 1792922400.0  # parse_time(T)


def row(rid="r1", session="sess-task-1", t=T, **extra):
    base = {"rid": rid, "route_id": 7, "t": t, "agent": "opencode", "provider": "anthropic",
            "providerAccount": "acct-a@example.test", "providerKeyId": "key-fp-1",
            "model": "claude-fable-5-1", "req": "route-main", "served": "claude-fable-5-1",
            "session": session, "in": 1000, "out": 200, "cache_read": 3000, "cache_write": 500,
            "cache_write_1h": 0, "reasoning": 40, "cost": 0.0125, "priced": True, "ms": 900}
    base.update(extra)
    return base


def parsed(**extra):
    return parse_usage_request(row(**extra))


def local(**overrides):
    base = {"id": "obs-1", "input_units": 1000, "output_units": 200, "reasoning_units": 40,
            "cache_read_units": 3000, "cache_write_units": 500, "cost_micro_units": None}
    base.update(overrides)
    return base


def test_parse_usage_request_full_row():
    record = parsed()
    assert record["rid"] == "r1" and record["session"] == "sess-task-1"
    assert record["provider_account"] == "acct-a@example.test"
    assert record["requested"] == "route-main" and record["served"] == "claude-fable-5-1"
    assert record["input"] == 1000 and record["cache_read"] == 3000 and record["reasoning"] == 40
    assert record["cost_usd"] == 0.0125 and record["priced"] is True
    assert record["t_epoch"] == pytest.approx(T_EPOCH)
    assert record["handed_on"] is False and record["rejected"] is False


def test_parse_usage_request_legacy_row_lacks_fields_without_guessing():
    record = parse_usage_request({"t": T, "model": "gpt-6.1-sol", "in": 5, "out": 2})
    assert record["rid"] is None and record["session"] is None
    assert record["cost_usd"] is None and record["priced"] is False
    assert record["cache_read"] is None and record["cache_write"] is None
    assert record["input"] == 5 and record["output"] == 2


def test_parse_usage_request_strips_private_strings_and_rejects_bad_shapes():
    poisoned = row(user="person@example.test", providerAccount="person@example.test")
    record = parse_usage_request(poisoned)
    assert record["provider_account"] is None  # the private value never survives
    assert parse_usage_request("not-a-row") is None
    assert parse_usage_request(None) is None


def test_parse_usage_request_bounds_and_validates_values():
    record = parse_usage_request(row(**{"in": -5, "out": 1.5, "cost": -1, "t": "not-a-time"}))
    assert record["input"] is None and record["output"] is None
    assert record["cost_usd"] is None and record["t_epoch"] is None
    long_value = "x" * 400
    assert len(parse_usage_request(row(agent=long_value))["agent"]) == 256


def test_parse_usage_ledger_page_counts_invalid_rows():
    ledger = parse_usage_ledger({"rows": [row(), row(rid="r2"), "garbage"], "total": 5, "offset": 0})
    assert [r["rid"] for r in ledger["rows"]] == ["r1", "r2"]
    assert ledger["total"] == 5 and ledger["invalid_rows"] == 1
    assert parse_usage_ledger("nope") == {"rows": [], "total": None, "offset": None, "invalid_rows": 0}


def test_parse_route_trace_with_bounded_tries():
    trace = parse_route({"asked": "route-main", "group": "grp-1", "model": "claude-fable-5-1",
                         "tier": "priority", "tier_served": "default", "served": "claude-fable-5-1",
                         "done": True, "status": 200, "ms": 1200,
                         "tries": [{"model": "gpt-6.1-sol", "tier": "priority"},
                                   {"model": "claude-fable-5-1", "tier_served": "default"},
                                   "garbage"]})
    assert trace["asked"] == "route-main" and trace["done"] is True and trace["status"] == 200
    assert [t["model"] for t in trace["tries"]] == ["gpt-6.1-sol", "claude-fable-5-1"]
    assert parse_route([]) is None


def test_correlate_attributes_by_session_and_never_sums_both_sides():
    report = correlate_task_usage([local()], [parsed(), parsed(rid="r2", **{"in": 10, "out": 5,
                                   "cache_read": 0, "cache_write": 0, "reasoning": 0, "cost": 0.002})],
                                  sessions=["sess-task-1"])
    assert report["basis"] == "magpie_measured"
    assert report["request_count"] == 2
    # Totals come from Magpie alone; the local ledger is only a cross-check.
    assert report["totals"]["input"] == 1010 and report["totals"]["cost_usd"] == pytest.approx(0.0145)
    assert report["local_cross_check"]["observations"] == 1
    assert report["local_cross_check"]["token_fields"]["input"] == 1000
    assert report["accounts"] == {"acct-a@example.test": 2}
    assert report["served_models"] == {"claude-fable-5-1": 2}
    assert report["unattributed_rows"] == 0


def test_correlate_collapses_duplicate_rids_and_excludes_handed_on_tries():
    rows = [parsed(**{"in": 100}), parsed(**{"in": 900}),  # same rid: the terminal row wins
            parsed(rid="h1", handed_on=True, **{"in": 99999})]
    report = correlate_task_usage([], rows, sessions=["sess-task-1"])
    assert report["request_count"] == 1
    assert report["duplicate_rids_collapsed"] == 1 and report["excluded_handed_on"] == 1
    assert report["totals"]["input"] == 900 and "cost_usd" in report["totals"]


def test_correlate_without_identity_match_stays_local_only():
    report = correlate_task_usage([local()], [parsed(session="someone-else")],
                                  sessions=["sess-task-1"])
    assert report["basis"] == "local_only" and report["requests"] == []
    assert report["unattributed_rows"] == 1
    assert report["local_cross_check"] is None  # local IS the basis here


def test_correlate_enforces_the_time_window_on_attributed_rows():
    report = correlate_task_usage([], [parsed()], sessions=["sess-task-1"],
                                  since=T_EPOCH + 60, until=T_EPOCH + 600)
    assert report["request_count"] == 0 and report["unattributed_rows"] == 1
    inside = correlate_task_usage([], [parsed()], sessions=["sess-task-1"],
                                  since=T_EPOCH - 60, until=T_EPOCH + 600)
    assert inside["request_count"] == 1


def test_correlate_unpriced_call_keeps_cost_unknown():
    report = correlate_task_usage(
        [], [parsed(), parsed(rid="r2", priced=False, cost=None)], sessions=["sess-task-1"])
    assert report["totals"]["cost_usd"] is None
    assert report["totals"]["priced_calls"] == 1 and report["totals"]["unpriced_calls"] == 1


def test_correlate_unknown_when_neither_side_has_data():
    report = correlate_task_usage([], [], sessions=["sess-task-1"])
    assert report["basis"] == "unknown" and report["request_count"] == 0


def test_correlate_missing_token_keeps_the_total_unknown():
    report = correlate_task_usage([], [parsed(**{"cache_read": None})], sessions=["sess-task-1"])
    assert report["totals"]["cache_read"] is None and report["totals"]["input"] == 1000


def test_correlate_attributes_by_request_id_when_no_session_is_known():
    report = correlate_task_usage([], [parsed(rid="req-9", session="")], rids=["req-9"])
    assert report["request_count"] == 1 and report["basis"] == "magpie_measured"


def test_page_wide_private_values_never_survive_in_other_rows():
    import json as _json
    page = {"rows": [row(rid="a", user="person@example.test"),
                     row(rid="b", providerAccount="person@example.test")]}
    ledger = parse_usage_ledger(page)
    dumped = _json.dumps(ledger)
    assert "person@example.test" not in dumped
    assert ledger["rows"][0]["rid"] == "a" and ledger["rows"][1]["rid"] == "b"


def test_non_finite_and_huge_numbers_fail_closed():
    record = parse_usage_request(row(**{"in": float("nan"), "out": float("inf"),
                                        "cost": 10 ** 400}))
    assert record["input"] is None and record["output"] is None
    assert record["cost_usd"] is None


def test_non_iterable_rows_and_tries_do_not_crash_the_parsers():
    bad_page = parse_usage_ledger({"rows": 5})
    assert bad_page["rows"] == [] and bad_page["invalid_rows"] == 1
    trace = parse_route({"asked": "route-main", "tries": 5})
    assert trace is not None and trace["tries"] == []


def test_one_shot_generator_local_observations_keep_their_cost():
    def generate():
        yield local(cost_micro_units=500)
    report = correlate_task_usage(generate(), [parsed()], sessions=["sess-task-1"])
    assert report["local_cross_check"]["cost_micro_units"] == 500
    assert report["local_cross_check"]["observations"] == 1


def test_attributed_requests_are_capped_with_a_flag():
    rows = [parsed(rid="r%d" % i) for i in range(205)]
    report = correlate_task_usage([], rows, sessions=["sess-task-1"])
    assert report["request_count"] == 205
    assert len(report["requests"]) == 200 and report["requests_truncated"] is True
