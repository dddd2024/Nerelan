"""Provider-free checks for the account-interval credit-delta settlement.

The Owner contract (issue #1342, comment 6379371024 items 1-6) fixes the
regression targets exercised here: isolated task deltas, different-account
parallel deltas, interleaved shared-account requests, retries and duplicates
across sources, missing IDs, delayed readings, account reset/top-up/expiry,
percentage quantization, independently priced cache/reasoning, and late
completion evidence with idempotent reconciliation. No gateway, network,
shell or environment is touched; every input is a literal snapshot.
"""

import json

from reverse_agent.model_access.magpie_usage import (
    correlate_task_usage, parse_usage_ledger,
)
from reverse_agent.model_access.magpie_settlement import reconcile_account_interval

T0 = "2026-10-25T10:00:00Z"
T1 = "2026-10-25T11:00:00Z"


def ledger(raw_rows):
    """Run raw wire rows through the real page parser, as the adapter does."""
    return parse_usage_ledger({"rows": raw_rows})["rows"]


def token_totals(correlated):
    return {k: correlated["totals"][k] for k in
            ("input", "output", "cache_read", "cache_write", "reasoning")}


def snapshot(credits, *, account="acct-1", window="credits", observed_at=T1,
             source="magpie", resets_at="2026-11-01T00:00:00Z"):
    return {"account_ref": account, "source": source, "observed_at": observed_at,
            "window": window, "credits_remaining": credits, "resets_at": resets_at}


def usage_row(rid, session, *, seconds_offset=60, cost=0.5, priced=True, **fields):
    row = {"rid": rid, "session": session, "t": f"2026-10-25T10:{seconds_offset // 60:02d}:00Z",
           "in": fields.get("in", 100), "out": fields.get("out", 200),
           "cache_read": fields.get("cache_read", 0), "cache_write": fields.get("cache_write", 0),
           "reasoning": fields.get("reasoning", 0), "cost": cost, "priced": priced,
           "provider_account": fields.get("provider_account", "acct-1"),
           "served": fields.get("served", "glm-5.3"), "tries": 1}
    for key in ("handed_on", "err"):
        if key in fields:
            row[key] = fields[key]
    return row


# --- isolated task delta ---------------------------------------------------


def test_isolated_task_delta_reconciles_with_unattributed_residual():
    before, after = snapshot(100.0, observed_at=T0), snapshot(94.25, observed_at=T1)
    correlated = correlate_task_usage([], ledger([usage_row("r-1", "s-1", cost=2.5),
                                                  usage_row("r-2", "s-1", cost=2.5)]),
                                      sessions=("s-1",))
    assert correlated["totals"]["requests"] == 2
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["totals"]["requests"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}])
    assert record["status"] == "OBSERVED"
    assert record["account_delta_credits"] == 5.75
    assert record["tasks"][0]["estimated_cost_usd"] == 5.0
    # 5.75 spent, 5.0 covered by identified requests: the residual stays itself.
    assert record["unattributed_residual_credits"] == 0.75
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["estimated_money"]["completeness"] == "ESTIMATED"


def test_zero_delta_with_zero_requests_is_observed_without_inference():
    before, after = snapshot(100.0, observed_at=T0), snapshot(100.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 0.0, "priced": True}])
    assert record["status"] == "OBSERVED"
    assert record["account_delta_credits"] == 0.0
    assert record["unattributed_residual_credits"] == 0.0


# --- different-account parallel deltas -------------------------------------


def test_different_account_parallel_tasks_do_not_cross_attribute():
    before, after = snapshot(50.0, account="acct-1", observed_at=T0), snapshot(48.0, account="acct-1")
    foreign = {"task_id": "t-2", "account_ref": "acct-2", "coverage": "identity_bound",
               "requests": 4, "tokens": {"input": 900}, "cost_usd": 9.0, "priced": True}
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 2.0, "priced": True},
                     foreign])
    assert record["status"] == "OBSERVED"
    assert record["account_delta_credits"] == 2.0
    assert [task["task_id"] for task in record["tasks"]] == ["t-1"]
    assert record["other_account_tasks"] == 1
    assert record["unattributed_residual_credits"] == 0.0


# --- shared-account tasks and aggregates ------------------------------------


def test_shared_account_identity_bound_tasks_sum_and_residual_stays():
    before, after = snapshot(100.0, observed_at=T0), snapshot(90.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 3, "tokens": {"input": 300}, "cost_usd": 4.0, "priced": True},
                     {"task_id": "t-2", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": {"input": 700, "reasoning": 50},
                      "cost_usd": 3.5, "priced": True}])
    assert record["status"] == "OBSERVED"
    assert record["unattributed_residual_credits"] == 2.5
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 1000


def test_aggregate_only_usage_stays_account_level_and_never_allocates():
    before, after = snapshot(100.0, observed_at=T0), snapshot(95.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "aggregate_only",
                      "requests": 3, "tokens": {"input": 300}, "cost_usd": 5.0, "priced": True}])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "aggregate_only_usage_present"
    assert record["tasks"] == []
    assert record["unattributed_tasks"] == ["t-1"]
    assert record["unattributed_residual_credits"] is None


# --- missing IDs, retries and duplicates across sources ----------------------


def test_unattributed_request_rows_keep_the_settlement_partial():
    before, after = snapshot(100.0, observed_at=T0), snapshot(98.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}],
        unattributed_request_rows=1)
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unattributed_request_rows_present"


def test_duplicate_rids_collapse_before_the_sum_reaches_settlement():
    # One request observed twice (log + gateway replay of the same rid) must be
    # billed once: correlate collapses, settlement sees one priced request.
    rows = ledger([usage_row("r-dup", "s-dup", cost=1.5), usage_row("r-dup", "s-dup", cost=1.5)])
    correlated = correlate_task_usage([], rows, sessions=("s-dup",))
    assert correlated["duplicate_rids_collapsed"] == 1
    assert correlated["totals"]["cost_usd"] == 1.5
    before, after = snapshot(10.0, observed_at=T0), snapshot(8.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}])
    assert record["unattributed_residual_credits"] == 0.5


def test_overcoverage_reports_a_negative_residual_instead_of_clamping():
    # Attributed estimates above the observed interval delta are an
    # inconsistency signal (mispriced rows, refund, late reading): the residual
    # keeps its sign so the caller can investigate instead of silently zeroing.
    before, after = snapshot(10.0, observed_at=T0), snapshot(9.5)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.5, "priced": True}])
    assert record["unattributed_residual_credits"] == -1.0


def test_missing_rid_with_bound_session_still_attributes_by_session():
    rows = ledger([usage_row("r-keep", "s-keep", cost=1.0),
                   {"rid": None, "session": "s-keep", "t": T0, "cost": 2.0, "priced": True},
                   usage_row("r-hand", "s-keep", cost=3.0, handed_on=True),
                   {"rid": None, "session": "s-other", "t": T0, "cost": 7.0, "priced": True}])
    correlated = correlate_task_usage([], rows, sessions=("s-keep",))
    # A row without a rid is not anonymous: the bound session attributes it.
    # Only a row with no claimed identity at all stays unattributed, and a
    # handed-on try is counted, never billed to the task.
    assert correlated["request_count"] == 2
    assert correlated["excluded_handed_on"] == 1
    assert correlated["unattributed_rows"] == 1


# --- delayed readings --------------------------------------------------------


def test_delayed_after_reading_still_settles_when_ordered():
    before, after = snapshot(100.0, observed_at=T0), snapshot(97.0, observed_at="2026-10-25T12:30:00Z")
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": {"input": 20}, "cost_usd": 3.0, "priced": True}])
    assert record["status"] == "OBSERVED"
    assert record["unattributed_residual_credits"] == 0.0


def test_inverted_or_unreadable_times_refuse():
    assert reconcile_account_interval(snapshot(100.0, observed_at=T1), snapshot(99.0, observed_at=T0))["reason"] == "invalid_interval"
    assert reconcile_account_interval(snapshot(100.0, observed_at=None), snapshot(99.0))["reason"] == "invalid_interval"


# --- account reset / top-up / expiry -----------------------------------------


def test_window_reset_refuses_the_settlement():
    before = snapshot(100.0, observed_at=T0, resets_at="2026-10-26T00:00:00Z")
    after = snapshot(20.0, resets_at="2026-10-25T10:30:00Z")
    assert reconcile_account_interval(before, after)["reason"] == "window_reset"


def test_credit_increase_is_a_topup_not_negative_use():
    assert reconcile_account_interval(snapshot(90.0, observed_at=T0), snapshot(95.0))["reason"] == "credit_increase"


# --- percentage quantization -------------------------------------------------


def test_percentage_only_readings_can_never_settle():
    before = {"account_ref": "acct-1", "source": "magpie", "observed_at": T0, "window": "credits",
              "used_percent": 40.0, "remaining_percent": 60.0, "resets_at": None}
    after = {"account_ref": "acct-1", "source": "magpie", "observed_at": T1, "window": "credits",
             "used_percent": 40.0, "remaining_percent": 60.0, "resets_at": None}
    record = reconcile_account_interval(before, after)
    assert record["status"] == "REFUSED"
    assert record["reason"] == "percentage_only_quantized"
    assert record["account_delta_credits"] is None


# --- independently priced cache/reasoning -------------------------------------


def test_cache_and_reasoning_tokens_stay_in_their_own_dimension():
    correlated = correlate_task_usage([], ledger([usage_row("r-c", "s-c", cost=2.0, cache_read=500,
                                                            reasoning=300)]),
                                      sessions=("s-c",))
    assert correlated["totals"]["cache_read"] == 500
    assert correlated["totals"]["reasoning"] == 300
    before, after = snapshot(50.0, observed_at=T0), snapshot(48.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}])
    assert record["tasks"][0]["tokens"] == {"input": 100, "output": 200, "cache_read": 500,
                                            "cache_write": 0, "reasoning": 300}
    assert record["account_delta_credits"] == 2.0
    assert record["unattributed_residual_credits"] == 0.0


def test_unpriced_call_keeps_money_none_and_status_partial():
    correlated = correlate_task_usage([], ledger([usage_row("r-u", "s-u", cost=None, priced=False)]),
                                      sessions=("s-u",))
    assert correlated["totals"]["cost_usd"] is None
    before, after = snapshot(50.0, observed_at=T0), snapshot(49.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": False}])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unpriced_task_requests"
    assert record["unattributed_residual_credits"] is None
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 100


# --- late completion evidence and idempotent reconciliation -------------------


def test_identical_inputs_reconcile_identically_idempotent():
    before, after = snapshot(100.0, observed_at=T0), snapshot(98.0)
    tasks = [{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
              "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}]
    first = reconcile_account_interval(before, after, task_usages=tasks)
    second = reconcile_account_interval(dict(before), dict(after),
                                         task_usages=[dict(task) for task in tasks])
    assert first == second
    assert first["inputs_digest"] == second["inputs_digest"]


def test_late_complete_evidence_supersedes_partial_without_erasing_it():
    before, after = snapshot(100.0, observed_at=T0), snapshot(97.0)
    partial = reconcile_account_interval(before, after, task_usages=[],
                                         unattributed_request_rows=2)
    assert partial["status"] == "PARTIAL"
    complete = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": {"input": 30}, "cost_usd": 3.0, "priced": True}])
    assert complete["status"] == "OBSERVED"
    assert complete["inputs_digest"] != partial["inputs_digest"]
    # The earlier partial record is a distinct durable fact; nothing above
    # mutates it (pure function), and the caller persists both.


# --- exclusive-interval guard -------------------------------------------------


def test_overlapping_reservation_refuses_the_interval():
    before, after = snapshot(100.0, observed_at=T0), snapshot(98.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}],
        other_reservations=[{"account_ref": "acct-1", "created_at": "2026-10-25T10:30:00Z",
                             "reconciled_at": None}])
    assert record["reason"] == "overlapping_reservation"


def test_finished_reservation_outside_interval_does_not_refuse():
    before, after = snapshot(100.0, observed_at=T0), snapshot(98.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}],
        other_reservations=[{"account_ref": "acct-1", "created_at": "2026-10-25T09:00:00Z",
                             "reconciled_at": "2026-10-25T09:59:00Z"}])
    assert record["status"] == "OBSERVED"


def test_non_provider_or_mismatched_endpoints_refuse():
    assert reconcile_account_interval(snapshot(100.0, observed_at=T0),
                                      snapshot(99.0, source="estimated"))["reason"] == "non_provider_reading"
    assert reconcile_account_interval(snapshot(100.0, observed_at=T0, account="acct-1"),
                                      snapshot(99.0, account="acct-9"))["reason"] == "account_mismatch"
    assert reconcile_account_interval(snapshot(100.0, observed_at=T0, window="credits"),
                                      snapshot(99.0, window="weekly"))["reason"] == "window_identity_changed"


def test_record_is_json_safe():
    record = reconcile_account_interval(snapshot(100.0, observed_at=T0), snapshot(99.0))
    json.dumps(record, allow_nan=False)
