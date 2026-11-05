"""Ambiguous or partial evidence must never become a complete cost claim."""

from reverse_agent.platform_v1.magpie_usage_ingest import (
    correlate_usage, cost_basis_values, economics_runs, parse_usage_csv, read_cache,
)


def attempts(*sessions):
    return [dict(task_id=str(i), executor_kind="codex", mode="single",
                 started_at=1793793500, finished_at=1793793700, accepted=True,
                 agent_session_id=session) for i, session in enumerate(sessions)]


def request(identity, session):
    return dict(request_id=identity, session=session, time="2026-11-04T12:00:00Z",
                agent="codex", reported_cost_usd=3., billing_class="payg")


def test_named_api_account_is_not_assumed_to_be_a_subscription():
    row = parse_usage_csv("request_id,time,provider_account,provider_key_id,cost_usd\n"
                          "api,2026-11-04T12:00:00Z,paid-account,key,3\n")[0]
    assert row["billing_class"] == "payg"
    assert cost_basis_values(row)["cash_cost_usd"] == 3


def test_account_name_without_billing_evidence_stays_unknown():
    row = parse_usage_csv("request_id,time,provider_account,cost_usd\n"
                          "api,2026-11-04T12:00:00Z,account,3\n")[0]
    assert cost_basis_values(row) == dict(cash_cost_usd=None, quota_opportunity_units=None)


def test_duplicate_session_identity_is_ambiguous_instead_of_last_writer_wins():
    result = correlate_usage([request("r", "shared")], attempts("shared", "shared"))
    assert result["summary"]["ambiguous"] == 1
    assert result["summary"]["attributed"] == 0


def test_partial_spend_cannot_be_reported_as_complete():
    result = correlate_usage([request("a", "a"), request("b", "b"), request("c", "")],
                             attempts("a", "b"))
    assert result["summary"]["ambiguous"] == 1
    for run in economics_runs(result):
        assert not run["cost_complete"]
        assert run["cash_cost_usd"] is None


def test_one_matched_row_does_not_prove_the_whole_attempt_was_observed():
    result = correlate_usage([request("a", "a")], attempts("a"))
    assert economics_runs(result)[0]["cash_cost_usd"] is None


def test_correlating_a_generator_has_the_same_evidence_as_a_list():
    rows = [request("a", "a")]
    assert correlate_usage(iter(rows), attempts("a")) == correlate_usage(rows, attempts("a"))


def test_old_cache_classification_is_not_treated_as_verified(tmp_path):
    import json
    path = tmp_path / "old-cache.jsonl"
    raw = json.dumps({**request("old", "old"), "billing_class": "subscription"})
    path.write_text(raw + "\n", encoding="utf-8")
    assert cost_basis_values(read_cache(path)[0])["cash_cost_usd"] is None
    assert path.read_text(encoding="utf-8") == raw + "\n"
