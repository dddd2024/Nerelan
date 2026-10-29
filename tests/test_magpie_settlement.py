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
            ("input", "output", "cache_read", "cache_write", "cache_write_1h", "reasoning")}


def snapshot(credits, *, account="acct-1", window="credits", observed_at=T1,
             source="magpie", resets_at="2026-11-01T00:00:00Z"):
    return {"account_ref": account, "source": source, "observed_at": observed_at,
            "window": window, "credits_remaining": credits, "resets_at": resets_at}


def usage_row(rid, session, *, seconds_offset=60, cost=0.5, priced=True, **fields):
    row = {"rid": rid, "session": session, "t": f"2026-10-25T10:{seconds_offset // 60:02d}:00Z",
           "in": fields.get("in", 100), "out": fields.get("out", 200),
           "cache_read": fields.get("cache_read", 0), "cache_write": fields.get("cache_write", 0),
           "cache_write_1h": fields.get("cache_write_1h", 0),
           "reasoning": fields.get("reasoning", 0), "cost": cost, "priced": priced,
           "provider_account": fields.get("provider_account", "acct-1"),
           "served": fields.get("served", "glm-5.3"), "tries": 1}
    for key in ("handed_on", "err"):
        if key in fields:
            row[key] = fields[key]
    return row


def conversion(rate=1.0, *, account="acct-1", window="credits", proven="fixture"):
    """Evidenced credits-per-USD evidence; a fixture is never live billing."""
    return {"credits_per_usd": rate, "evidenced": True, "account_ref": account,
            "window": window, "observed_at": T1, "provenance": proven}


def full_tokens(**overrides):
    """A complete six-bucket token observation set (zeros for absent buckets)."""
    base = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0,
            "cache_write_1h": 0, "reasoning": 0}
    base.update(overrides)
    return base


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
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}],
        credit_conversion=conversion())
    # The conversion fixes the unit but the money input stays ESTIMATED, so the
    # residual is an ESTIMATED accounting fact, never an observed provider debit.
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
    assert record["account_delta_credits"] == 5.75
    assert record["tasks"][0]["estimated_cost_usd"] == 5.0
    # 5.75 credits spent, 5.0 USD attributed at the evidenced 1 credit/USD:
    # the residual is the unattributed credits, never a fabricated subtraction.
    assert record["unattributed_residual_credits"] == 0.75
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["estimated_money"]["completeness"] == "ESTIMATED"
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "ESTIMATED"


def test_zero_delta_with_zero_estimated_money_is_not_observed_credit_consumption():
    before, after = snapshot(100.0, observed_at=T0), snapshot(100.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 0.0, "priced": True}])
    # A zero estimated money total is an estimate, not verified zero task-credit
    # consumption: without an evidenced conversion the residual stays unknown and
    # the interval is a partial accounting fact, never an observed provider debit.
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unknown_credit_conversion"
    assert record["account_delta_credits"] == 0.0
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["estimated_money"]["estimated_usd"] == 0.0
    assert record["unattributed_residual_credits"] is None


# --- different-account parallel deltas -------------------------------------


def test_different_account_parallel_tasks_do_not_cross_attribute():
    before, after = snapshot(50.0, account="acct-1", observed_at=T0), snapshot(48.0, account="acct-1")
    foreign = {"task_id": "t-2", "account_ref": "acct-2", "coverage": "identity_bound",
               "requests": 4, "tokens": full_tokens(input=900), "cost_usd": 9.0, "priced": True}
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 2.0, "priced": True},
                     foreign],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
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
                      "requests": 3, "tokens": full_tokens(input=300), "cost_usd": 4.0, "priced": True},
                     {"task_id": "t-2", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": full_tokens(input=700, reasoning=50),
                      "cost_usd": 3.5, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
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
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}],
        credit_conversion=conversion())
    assert record["unattributed_residual_credits"] == 0.5


def test_overcoverage_reports_a_negative_residual_instead_of_clamping():
    # Attributed estimates above the observed interval delta are an
    # inconsistency signal (mispriced rows, refund, late reading): the residual
    # keeps its sign so the caller can investigate instead of silently zeroing.
    before, after = snapshot(10.0, observed_at=T0), snapshot(9.5)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 1.5, "priced": True}],
        credit_conversion=conversion())
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
                      "requests": 2, "tokens": full_tokens(input=20), "cost_usd": 3.0, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
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
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}],
        credit_conversion=conversion())
    assert record["tasks"][0]["tokens"] == {"input": 100, "output": 200, "cache_read": 500,
                                            "cache_write": 0, "cache_write_1h": 0,
                                            "reasoning": 300}
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
                      "requests": 2, "tokens": full_tokens(input=30), "cost_usd": 3.0, "priced": True}],
        credit_conversion=conversion())
    # The converted residual stays ESTIMATED, so even the fully-evidenced
    # interval is a partial accounting fact; it is nonetheless strictly more
    # complete than the empty-evidence refusal above, and both are durable.
    assert complete["status"] == "PARTIAL"
    assert complete["reason"] == "estimated_credit_reconciliation"
    assert complete["dimensions"]["credit_reconciliation"]["completeness"] == "ESTIMATED"
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
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 1.0, "priced": True}],
        other_reservations=[{"account_ref": "acct-1", "created_at": "2026-10-25T09:00:00Z",
                             "reconciled_at": "2026-10-25T09:59:00Z"}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"


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


# --- review round 1 findings (F1/F2/F3/F5) -------------------------------------


def test_unplaceable_sibling_reservation_fails_closed():
    # F1: a same-account reservation whose start cannot be parsed cannot be
    # proven non-overlapping, so the interval must refuse, not settle.
    before, after = snapshot(100.0, observed_at=T0), snapshot(98.0)
    for bad in ({"account_ref": "acct-1", "created_at": None, "reconciled_at": None},
                {"account_ref": "acct-1", "created_at": "garbage", "reconciled_at": None},
                {"account_ref": "acct-1", "reconciled_at": "2026-10-25T10:30:00Z"}):
        record = reconcile_account_interval(
            before, after,
            task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                          "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}],
            other_reservations=[bad])
        assert record["status"] == "REFUSED" and record["reason"] == "unplaceable_reservation", bad
        assert record["account_delta_credits"] is None


def test_refusal_digest_is_injective_over_task_inputs():
    # F3: two refusals of the same interval with different task sets must not
    # share one inputs_digest.
    before = snapshot(100.0, observed_at=T0)
    after = snapshot(99.0, source="estimated")
    first = reconcile_account_interval(before, after, task_usages=[])
    second = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10}, "cost_usd": 1.0, "priced": True}])
    assert first["inputs_digest"] != second["inputs_digest"]


def test_cache_write_1h_flows_through_the_documented_plumbing():
    # F2: the correlation totals carry six token buckets; dropping one from
    # settlement must not silently shrink a measured task's usage.
    correlated = correlate_task_usage(
        [], ledger([usage_row("r-1h", "s-1h", cost=2.0, cache_write=10)]),
        sessions=("s-1h",))
    # inject a cache_write_1h bucket the wire row carries
    rows = parse_usage_ledger({"rows": [dict(usage_row("r-1h", "s-1h", cost=2.0),
                                              cache_write_1h=77)]})["rows"]
    correlated = correlate_task_usage([], rows, sessions=("s-1h",))
    assert correlated["totals"]["cache_write_1h"] == 77
    before, after = snapshot(50.0, observed_at=T0), snapshot(48.0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"], "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}])
    assert record["tasks"][0]["tokens"]["cache_write_1h"] == 77
    assert record["dimensions"]["task_token_usage"]["tokens"]["cache_write_1h"] == 77


def test_exact_refusal_reasons_for_malformed_shapes():
    # F5: the two previously unasserted refusal reasons.
    record = reconcile_account_interval("not-a-snapshot", snapshot(99.0))
    assert record["status"] == "REFUSED" and record["reason"] == "invalid_snapshot"
    record = reconcile_account_interval(snapshot(100.0, observed_at=T0), snapshot(99.0),
                                        task_usages=[{"task_id": f"t-{i}"} for i in range(65)])
    assert record["status"] == "REFUSED" and record["reason"] == "too_many_tasks"


# --- PR1361 independent review defects 1-4 (Owner1342) -------------------------


def test_no_conversion_leaves_residual_unknown_and_keeps_dimensions():
    # Defect 1: USD must never be subtracted from provider credits without an
    # evidenced conversion. The residual stays unknown while the account delta,
    # token usage and estimated money all remain available as distinct facts.
    before, after = snapshot(100.0, observed_at=T0), snapshot(94.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 2.5, "priced": True}])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unknown_credit_conversion"
    assert record["unattributed_residual_credits"] is None
    assert record["account_delta_credits"] == 6.0
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 10
    assert record["dimensions"]["task_token_usage"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["estimated_money"]["estimated_usd"] == 2.5
    assert record["dimensions"]["estimated_money"]["completeness"] == "ESTIMATED"
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "UNKNOWN"


def test_one_to_one_is_never_assumed_without_evidence():
    # Defect 1: with credits 100->95 and an attributed USD of 5.0, the invalid
    # default would report a zero residual; without evidenced conversion the
    # residual must stay unknown, never a silent 1 credit per dollar.
    before, after = snapshot(100.0, observed_at=T0), snapshot(95.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 5.0, "priced": True}])
    assert record["unattributed_residual_credits"] is None
    assert record["status"] == "PARTIAL"


def test_evidenced_conversion_reconciles_a_positive_residual():
    # Defect 1 positive path: an evidenced same-unit conversion reconciles the
    # residual, and the evidence is retained with its account/window provenance.
    before, after = snapshot(100.0, observed_at=T0), snapshot(94.25, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": full_tokens(input=20), "cost_usd": 5.0, "priced": True}],
        credit_conversion=conversion())
    # The residual keeps its value but stays ESTIMATED with the provenance
    # retained: the conversion fixes the unit, it never observes a provider debit.
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
    assert record["unattributed_residual_credits"] == 0.75
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "ESTIMATED"
    reported = record["dimensions"]["credit_reconciliation"]["conversion"]
    assert reported["credits_per_usd"] == 1.0 and reported["account_ref"] == "acct-1"
    assert reported["window"] == "credits" and reported["provenance"] == "fixture"


def test_fractional_evidenced_conversion_uses_the_rate():
    before, after = snapshot(100.0, observed_at=T0), snapshot(90.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 2, "tokens": full_tokens(input=20), "cost_usd": 8.0, "priced": True}],
        credit_conversion=conversion(rate=0.5))
    # 10 credits spent, 8.0 USD at 0.5 credits/USD = 4.0 credits attributed.
    assert record["unattributed_residual_credits"] == 6.0


def test_mismatched_conversion_account_or_window_is_not_evidence():
    before, after = snapshot(100.0, observed_at=T0), snapshot(94.0, observed_at=T1)
    for bad in (conversion(account="acct-9"), conversion(window="weekly"),
                conversion(rate=0.0), dict(conversion(), evidenced=False),
                {"credits_per_usd": 1.0, "account_ref": "acct-1", "window": "credits"}):
        record = reconcile_account_interval(
            before, after,
            task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                          "requests": 1, "tokens": full_tokens(input=10),
                          "cost_usd": 2.5, "priced": True}],
            credit_conversion=bad)
        assert record["unattributed_residual_credits"] is None, bad


def test_zero_estimated_money_does_not_promote_the_whole_delta_to_observed():
    # A zero estimated money total is an estimate, not verified zero task-credit
    # consumption, so without an evidenced conversion the residual stays unknown
    # instead of the whole delta being promoted to an OBSERVED unattributed
    # residual. The explicit zero token buckets and the account delta are
    # preserved as observed; only the certainty of the credit residual is unknown.
    before, after = snapshot(100.0, observed_at=T0), snapshot(95.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 0.0, "priced": True}])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unknown_credit_conversion"
    assert record["unattributed_residual_credits"] is None
    assert record["account_delta_credits"] == 5.0
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["task_token_usage"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 10
    assert record["dimensions"]["estimated_money"]["completeness"] == "ESTIMATED"
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "UNKNOWN"


def test_known_reset_inside_interval_refuses_even_when_reset_strings_match():
    # Defect 2: both endpoints carry the same stale resets_at string, but the
    # reset boundary lies between them, so the interval is never verified
    # exclusive regardless of the credit-increase guard.
    before = snapshot(100.0, observed_at=T0, resets_at="2026-10-25T10:30:00Z")
    after = snapshot(94.0, observed_at=T1, resets_at="2026-10-25T10:30:00Z")
    record = reconcile_account_interval(before, after)
    assert record["status"] == "REFUSED" and record["reason"] == "window_reset"


def test_numeric_reset_inside_interval_refuses():
    # Defect 2: an epoch-number reset is parsed the same way as an ISO string.
    from reverse_agent.model_access.quota_forecast import parse_time
    inside = parse_time("2026-10-25T10:30:00Z")
    before = snapshot(100.0, observed_at=T0, resets_at=inside)
    after = snapshot(94.0, observed_at=T1, resets_at=inside)
    assert reconcile_account_interval(before, after)["reason"] == "window_reset"


def test_unknown_reset_metadata_stays_supported():
    # Defect 2: genuinely unknown reset metadata (missing/unparseable at both
    # ends) remains supported and is never inferred as a reset.
    before = snapshot(100.0, observed_at=T0, resets_at=None)
    after = snapshot(94.0, observed_at=T1, resets_at=None)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 5.0, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
    assert record["unattributed_residual_credits"] == 1.0


def test_reset_boundary_outside_the_interval_does_not_refuse():
    # A known reset strictly before the start or after the end does not lie
    # inside the interval, so the exclusive precondition survives.
    for stamp in ("2026-10-25T09:00:00Z", "2026-11-01T00:00:00Z"):
        before = snapshot(100.0, observed_at=T0, resets_at=stamp)
        after = snapshot(94.0, observed_at=T1, resets_at=stamp)
        record = reconcile_account_interval(
            before, after,
            task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                          "requests": 1, "tokens": full_tokens(input=10),
                          "cost_usd": 5.0, "priced": True}],
            credit_conversion=conversion())
        assert record["status"] == "PARTIAL", stamp
        assert record["reason"] == "estimated_credit_reconciliation", stamp


def test_digest_covers_other_reservations_and_conversion():
    # Defect 3: decision-driving reservation and conversion evidence both
    # participate in the inputs identity, so opposite verdicts never collide.
    before = snapshot(100.0, observed_at=T0)
    after = snapshot(94.0, observed_at=T1)
    tasks = [{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
              "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 2.5, "priced": True}]
    no_sibling = reconcile_account_interval(before, after, task_usages=tasks,
                                            credit_conversion=conversion())
    sibling = reconcile_account_interval(before, after, task_usages=tasks,
                                         credit_conversion=conversion(),
                                         other_reservations=[{"account_ref": "acct-1",
                                                              "created_at": "2026-10-25T10:30:00Z",
                                                              "reconciled_at": None}])
    assert no_sibling["status"] != sibling["status"]
    assert no_sibling["inputs_digest"] != sibling["inputs_digest"]
    with_conversion = reconcile_account_interval(before, after, task_usages=tasks,
                                                 credit_conversion=conversion())
    without_conversion = reconcile_account_interval(before, after, task_usages=tasks)
    assert with_conversion["inputs_digest"] != without_conversion["inputs_digest"]


def test_reservation_order_does_not_change_the_digest():
    # Materialized reservations are sorted, so the identity is order-independent.
    before = snapshot(100.0, observed_at=T0)
    after = snapshot(94.0, observed_at=T1)
    tasks = [{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
              "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 2.5, "priced": True}]
    a = {"account_ref": "acct-1", "created_at": "2026-10-25T09:00:00Z", "reconciled_at": None}
    b = {"account_ref": "acct-1", "created_at": "2026-10-25T11:30:00Z", "reconciled_at": None}
    first = reconcile_account_interval(before, after, task_usages=tasks, other_reservations=[a, b])
    second = reconcile_account_interval(before, after, task_usages=tasks, other_reservations=[b, a])
    assert first["inputs_digest"] == second["inputs_digest"]


def test_reservation_container_type_does_not_change_decision_or_digest():
    # The concrete defect: other_reservations is advertised as Iterable, but the
    # overlap guard consumes a generator before the digest re-iterates it, so a
    # single overlapping reservation delivered as a list versus a generator
    # returned the same REFUSED verdict yet a different inputs_digest. The
    # reconciliation identity must depend on the evidence, never on the
    # container type that happens to carry it.
    before = snapshot(100.0, observed_at=T0)
    after = snapshot(98.0, observed_at=T1)
    tasks = [{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
              "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 1.0, "priced": True}]
    cases = {
        "overlapping_reservation": [{"account_ref": "acct-1", "created_at": "2026-10-25T10:30:00Z",
                                     "reconciled_at": None}],
        "unplaceable_reservation": [{"account_ref": "acct-1", "created_at": None,
                                     "reconciled_at": None}],
        "success": [{"account_ref": "acct-1", "created_at": "2026-10-25T09:00:00Z",
                     "reconciled_at": "2026-10-25T09:59:00Z"}],
    }
    seen = {}
    for expected, rows in cases.items():
        as_list = reconcile_account_interval(before, after, task_usages=tasks,
                                             other_reservations=list(rows),
                                             credit_conversion=conversion())
        as_gen = reconcile_account_interval(before, after, task_usages=tasks,
                                            other_reservations=(row for row in rows),
                                            credit_conversion=conversion())
        if expected == "success":
            # The converted residual is ESTIMATED, so this is a partial fact.
            assert as_list["status"] == "PARTIAL" and as_gen["status"] == "PARTIAL", expected
        else:
            assert as_list["reason"] == expected and as_gen["reason"] == expected, expected
        # Same evidence, different container type: identical decision identity.
        assert as_list["inputs_digest"] == as_gen["inputs_digest"]
        assert as_list["inputs_digest"] not in seen, expected
        seen[as_list["inputs_digest"]] = expected
    # Opposite decisions never collide on identity: the two refusals and the
    # successful settlement are three distinct inputs digests.
    assert len(seen) == 3


def test_missing_token_bucket_keeps_completeness_partial_and_keeps_known_counts():
    # Defect 4: token completeness comes from the six buckets themselves. A
    # missing cache_write_1h keeps the dimension partial, never fabricates a
    # zero, and the known input/output counters stay usable.
    before, after = snapshot(50.0, observed_at=T0), snapshot(48.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {"input": 10, "output": 5, "cache_read": 0,
                                                "cache_write": 0, "reasoning": 0},
                      "cost_usd": 1.0, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "incomplete_token_fields"
    assert record["dimensions"]["task_token_usage"]["completeness"] == "PARTIAL"
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 10
    assert record["dimensions"]["task_token_usage"]["tokens"]["output"] == 5
    assert record["dimensions"]["task_token_usage"]["tokens"]["cache_write_1h"] is None
    assert record["unattributed_residual_credits"] is not None


def test_all_token_buckets_observed_gives_complete_token_dimension():
    before, after = snapshot(50.0, observed_at=T0), snapshot(48.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 1.0, "priced": True}],
        credit_conversion=conversion())
    assert record["dimensions"]["task_token_usage"]["completeness"] == "OBSERVED"
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"


def test_no_token_observation_is_unknown_not_zero():
    before, after = snapshot(50.0, observed_at=T0), snapshot(48.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": {}, "cost_usd": 1.0, "priced": True}],
        credit_conversion=conversion())
    assert record["dimensions"]["task_token_usage"]["completeness"] == "UNKNOWN"
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "incomplete_token_fields"


# --- corrected-review probes (the four new REJECT findings and their controls) --


def corrected_inputs():
    """The corrected-review probe fixture: 100 -> 94, one priced task, a valid conversion."""
    before = snapshot(100.0, observed_at=T0, resets_at=None)
    after = snapshot(94.0, observed_at=T1, resets_at=None)
    task = {"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
            "requests": 1, "tokens": full_tokens(input=10), "cost_usd": 2.5, "priced": True}
    return before, after, task


def test_reset_at_after_endpoint_must_not_settle():
    # Finding 1: a known reset at the after-reading endpoint cannot establish
    # that the ending balance precedes the reset (it may include reset/top-up
    # followed by use, or retain stale metadata), so the interval must refuse.
    before, after, task = corrected_inputs()
    before["resets_at"] = after["resets_at"] = T1
    record = reconcile_account_interval(before, after, task_usages=[task],
                                        credit_conversion=conversion())
    assert record["status"] == "REFUSED", json.dumps(record)
    assert record["reason"] == "window_reset"


def test_empty_identity_evidence_does_not_observe_six_zero_tokens():
    # Finding 3: no identity-bound rows is absence of task-token evidence, so
    # the six totals are UNKNOWN (None), never fabricated observed zeros.
    before, after, _task = corrected_inputs()
    record = reconcile_account_interval(before, after, task_usages=[],
                                        unattributed_request_rows=2)
    tokens = record["dimensions"]["task_token_usage"]
    assert tokens["completeness"] == "UNKNOWN", json.dumps(record)
    assert all(value is None for value in tokens["tokens"].values())


def test_estimated_money_does_not_become_an_observed_credit_residual():
    # Finding 2: the unit conversion fixes dimensions but the money input is
    # still ESTIMATED, so the derived residual stays ESTIMATED with the
    # conversion provenance, never promoted into an OBSERVED provider debit.
    before, after, task = corrected_inputs()
    record = reconcile_account_interval(before, after, task_usages=[task],
                                        credit_conversion=conversion(rate=2.0))
    assert record["dimensions"]["estimated_money"]["completeness"] == "ESTIMATED"
    reconciliation = record["dimensions"]["credit_reconciliation"]
    assert reconciliation["completeness"] == "ESTIMATED", json.dumps(record)
    assert reconciliation["conversion"]["provenance"] == "fixture"
    # 6.0 credits spent, 2.5 USD at the evidenced 2 credits/USD = 5.0 credits.
    assert record["unattributed_residual_credits"] == 1.0
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"


def test_conversion_without_provenance_cannot_complete_reconciliation():
    # Finding 4: a conversion needs a nonempty provenance AND a parseable
    # observed_at; without both the residual cannot be reconciled, whatever the
    # caller asserts. A caller assertion flag is never real billing proof.
    before, after, task = corrected_inputs()
    for bad in (dict(conversion(), provenance=None), dict(conversion(), observed_at=None),
                dict(conversion(), observed_at="garbage")):
        record = reconcile_account_interval(before, after, task_usages=[task],
                                            credit_conversion=bad)
        assert record["unattributed_residual_credits"] is None, bad
        assert record["dimensions"]["credit_reconciliation"]["completeness"] == "UNKNOWN"
        assert record["reason"] == "unknown_credit_conversion"


def test_conversion_with_provenance_and_time_retains_the_estimated_residual():
    # Positive control: a complete conversion (provenance + parseable time) does
    # complete the unit arithmetic and retains the numeric signed residual, but
    # the result stays an ESTIMATED accounting fact, never an observed debit.
    before, after, task = corrected_inputs()
    record = reconcile_account_interval(before, after, task_usages=[task],
                                        credit_conversion=conversion(rate=2.0))
    assert record["unattributed_residual_credits"] == 1.0
    reported = record["dimensions"]["credit_reconciliation"]["conversion"]
    assert reported["observed_at"] == T1 and reported["provenance"] == "fixture"


def test_control_no_conversion_unknown_and_known_tokens_preserved():
    # Positive control: without a conversion the residual stays unknown while
    # the observed token dimension survives intact and account-level.
    before, after, task = corrected_inputs()
    record = reconcile_account_interval(before, after, task_usages=[task])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unknown_credit_conversion"
    assert record["unattributed_residual_credits"] is None
    assert record["dimensions"]["task_token_usage"]["completeness"] == "OBSERVED"
    assert record["account_delta_credits"] == 6.0


def test_control_generators_late_evidence_and_original_record_retention():
    # Positive control: list/generator reservation evidence settles identically,
    # the earlier partial record is not mutated, and new evidence changes the
    # reconciliation identity (materialize-once and digest coverage).
    before, after, task = corrected_inputs()
    partial = reconcile_account_interval(before, after, task_usages=[],
                                         unattributed_request_rows=2)
    original = json.dumps(partial, sort_keys=True)
    rows = [{"account_ref": "acct-1", "created_at": "2026-10-25T09:00:00Z",
             "reconciled_at": "2026-10-25T09:30:00Z"}]
    listed = reconcile_account_interval(before, after, task_usages=[task],
                                        credit_conversion=conversion(),
                                        other_reservations=rows)
    streamed = reconcile_account_interval(before, after, task_usages=(item for item in [task]),
                                          credit_conversion=conversion(),
                                          other_reservations=(row for row in rows))
    assert listed == streamed
    assert json.dumps(partial, sort_keys=True) == original
    assert partial["inputs_digest"] != listed["inputs_digest"]
    assert partial["status"] == "PARTIAL"


def test_control_actual_parser_missing_token_fields_stay_unknown():
    # Positive control: real parser -> correlator -> settlement propagation of a
    # missing bucket keeps the token dimension PARTIAL/None, never fabricated.
    before, after, task = corrected_inputs()
    # The wire row carries no cache_write_1h bucket, so the correlated totals
    # leave it unknown and settlement keeps it PARTIAL/None, never fabricating 0.
    rows = ledger([{"rid": "r-1", "session": "s-1", "t": T0,
                    "in": 10, "out": 0, "cost": 2.5, "priced": True}])
    correlated = correlate_task_usage([], rows, sessions=["s-1"])
    task.update(tokens=token_totals(correlated),
                cost_usd=correlated["totals"]["cost_usd"],
                requests=correlated["request_count"])
    record = reconcile_account_interval(before, after, task_usages=[task],
                                        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["dimensions"]["task_token_usage"]["completeness"] == "PARTIAL"
    assert record["tasks"][0]["tokens"]["cache_write_1h"] is None


# --- PR1361 evidence-final defects 1-2 and their controls (Owner1342) ----------


def test_known_reset_at_start_endpoint_refuses_without_order_proof():
    # A known reset exactly at the before-reading endpoint is just as ambiguous
    # as one at the after endpoint: no ordering metadata proves the first
    # balance was already post-reset, so a reset plus subsequent use can leave
    # the ending balance below the starting one without the interval being the
    # true consumption. The whole closed interval refuses; no baseline guess.
    before = snapshot(100.0, observed_at=T0, resets_at=T0)
    after = snapshot(94.0, observed_at=T1, resets_at=T0)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10),
                      "cost_usd": 2.5, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "REFUSED"
    assert record["reason"] == "window_reset"
    assert record["account_delta_credits"] is None


def test_positive_raw_cost_rounded_to_zero_keeps_residual_unknown():
    # Real parser -> correlator -> settlement: a positive raw amount (4e-7)
    # rounds to cost_usd 0.0 after the six-decimal rounding, but that is an
    # estimate, not verified zero task-credit consumption. Without a conversion
    # the credit residual stays UNKNOWN, never promoted to an OBSERVED whole
    # delta, while the supplied zero token buckets stay observed.
    before = snapshot(100.0, observed_at=T0)
    after = snapshot(94.0, observed_at=T1)
    rows = ledger([{"rid": "r-0", "session": "s-0", "t": T0, "cost": 0.0000004,
                    "priced": True, "in": 10, "out": 1, "cache_read": 0,
                    "cache_write": 0, "cache_write_1h": 0, "reasoning": 0}])
    correlated = correlate_task_usage([], rows, sessions=("s-0",))
    assert correlated["totals"]["cost_usd"] == 0.0
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}])
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "unknown_credit_conversion"
    assert record["unattributed_residual_credits"] is None
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "UNKNOWN"
    assert record["dimensions"]["task_token_usage"]["completeness"] == "OBSERVED"
    assert record["dimensions"]["task_token_usage"]["tokens"]["input"] == 10
    assert record["dimensions"]["account_balance_credits"]["completeness"] == "OBSERVED"


def test_zero_estimated_money_with_conversion_keeps_numeric_estimated_residual():
    # Positive control: with an evidenced conversion even a zero estimated money
    # total completes the unit arithmetic and keeps the numeric residual
    # ESTIMATED (the whole delta is unattributed), never an observed promotion.
    before, after = snapshot(100.0, observed_at=T0), snapshot(95.0, observed_at=T1)
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": 1, "tokens": full_tokens(input=10),
                      "cost_usd": 0.0, "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
    assert record["unattributed_residual_credits"] == 5.0
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "ESTIMATED"


def test_positive_raw_cost_not_rounded_to_zero_still_yields_estimated_residual():
    # Positive control: a positive raw amount that does not round to zero still
    # reconciles an ESTIMATED numeric residual with an evidenced conversion.
    before, after = snapshot(100.0, observed_at=T0), snapshot(94.0, observed_at=T1)
    rows = ledger([{"rid": "r-1", "session": "s-1", "t": T0, "cost": 0.4,
                    "priced": True, "in": 10, "out": 1, "cache_read": 0,
                    "cache_write": 0, "cache_write_1h": 0, "reasoning": 0}])
    correlated = correlate_task_usage([], rows, sessions=("s-1",))
    assert correlated["totals"]["cost_usd"] == 0.4
    record = reconcile_account_interval(
        before, after,
        task_usages=[{"task_id": "t-1", "account_ref": "acct-1", "coverage": "identity_bound",
                      "requests": correlated["request_count"],
                      "tokens": token_totals(correlated),
                      "cost_usd": correlated["totals"]["cost_usd"], "priced": True}],
        credit_conversion=conversion())
    assert record["status"] == "PARTIAL"
    assert record["reason"] == "estimated_credit_reconciliation"
    # 6.0 credits spent, 0.4 USD at the evidenced 1 credit/USD.
    assert record["unattributed_residual_credits"] == 5.6
    assert record["dimensions"]["credit_reconciliation"]["completeness"] == "ESTIMATED"
