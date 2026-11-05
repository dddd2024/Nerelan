"""Read-only Magpie usage ingestion (P1 step 1).

Provider-free: every case runs against CSV text, not a live Magpie. One opt-in
integration test touches the real CLI only when ``REVERSE_AGENT_MAGPIE_EXE`` is
set, so ordinary CI never shells out.
"""
from __future__ import annotations

import json
import os

import pytest

from reverse_agent.platform_v1.magpie_usage_ingest import (
    cost_basis_values, cost_facts, ingest, magpie_executable, merge_into_cache,
    parse_usage_csv, read_cache,
)

COLUMNS = ("time", "agent", "requested_model", "provider", "host", "model", "served_model",
           "swapped", "effort", "input_tokens", "output_tokens", "cache_write_tokens",
           "cache_read_tokens", "reasoning_tokens", "cost_usd", "duration_ms", "ttft_ms",
           "status", "error", "session", "kind", "provider_key_id", "provider_key_name",
           "provider_account", "route_id", "request_id", "rejected", "session_account")

HEADER = ",".join(COLUMNS) + "\n"


def _row(**values: str) -> str:
    """Build one CSV row by column name, so a fixture cannot drift out of alignment."""
    return ",".join(str(values.get(name, "")) for name in COLUMNS) + "\n"


SUBSCRIPTION_ROW = _row(
    time="2026-11-04T09:00:00-04:00", agent="claude", requested_model="claude/sonnet",
    provider="anthropic", host="api", model="sonnet", served_model="claude-sonnet-5-5",
    swapped="false", effort="high", input_tokens="1200", output_tokens="300",
    cache_write_tokens="0", cache_read_tokens="4000", reasoning_tokens="50",
    cost_usd="0.0312", duration_ms="2100", ttft_ms="400", status="200", error="",
    session="sess-1", kind="", provider_key_id="key-1", provider_key_name="secret-key-name",
    provider_account="", route_id="route-1", request_id="req-1", rejected="false",
    session_account="vip@example.com")

PAYG_ROW = _row(
    time="2026-11-04T09:05:00-04:00", agent="opencode", requested_model="deepseek/chat",
    provider="deepseek", host="api", model="chat", served_model="deepseek-chat",
    swapped="false", input_tokens="800", output_tokens="120", cost_usd="0.0021",
    duration_ms="900", ttft_ms="120", status="200", session="sess-2",
    provider_key_id="key-2", provider_key_name="other-key", route_id="route-2",
    request_id="req-2", rejected="false")

FAILED_ROW = _row(
    time="2026-11-04T09:06:00-04:00", agent="codex", requested_model="gpt/x",
    provider="openai", host="api", model="x", served_model="gpt-x", swapped="false",
    input_tokens="100", output_tokens="0", cost_usd="0.0040", duration_ms="80",
    ttft_ms="10", status="429", error="rate_limited", session="sess-3",
    provider_key_id="key-3", route_id="route-3", request_id="req-3", rejected="true")

UNPRICED_ROW = _row(
    time="2026-11-04T09:07:00-04:00", agent="codex", requested_model="gpt/y",
    provider="openai", host="api", model="y", served_model="gpt-y", swapped="false",
    input_tokens="10", output_tokens="1", cost_usd="", duration_ms="40", ttft_ms="5",
    status="200", session="sess-4", provider_key_id="key-4", route_id="route-4",
    request_id="req-4", rejected="false")


def _csv(*rows: str) -> str:
    return HEADER + "".join(rows)


def test_parse_normalizes_rows_and_keeps_tokens():
    rows = parse_usage_csv(_csv(SUBSCRIPTION_ROW, PAYG_ROW))
    assert [row["request_id"] for row in rows] == ["req-1", "req-2"]
    first = rows[0]
    assert first["served_model"] == "claude-sonnet-5-5"
    assert first["tokens"] == {"input": 1200, "output": 300, "cache_read": 4000,
                               "cache_write": 0, "reasoning": 50}
    assert first["reported_cost_usd"] == 0.0312
    assert first["billing_class"] == "subscription"
    assert rows[1]["billing_class"] == "payg"


def test_account_identity_is_hashed_and_never_persisted_raw():
    rows = parse_usage_csv(_csv(SUBSCRIPTION_ROW))
    assert rows[0]["account_id"].startswith("acct_")
    assert "vip@example.com" not in json.dumps(rows)
    # The key name from the CSV must not leak either.
    assert "secret-key-name" not in json.dumps(rows)


def test_bases_never_blend_cash_and_allowance():
    subscription, payg, unpriced = parse_usage_csv(_csv(SUBSCRIPTION_ROW, PAYG_ROW, UNPRICED_ROW))
    assert cost_basis_values(subscription) == {"cash_cost_usd": 0.0, "quota_opportunity_units": 0.0312}
    assert cost_basis_values(payg) == {"cash_cost_usd": 0.0021, "quota_opportunity_units": 0.0}
    assert cost_basis_values(unpriced) == {"cash_cost_usd": None, "quota_opportunity_units": None}


def test_cost_facts_separate_accounts_and_expose_failed_spend():
    facts = cost_facts(parse_usage_csv(_csv(SUBSCRIPTION_ROW, PAYG_ROW, FAILED_ROW)))
    totals = facts["totals"]
    assert totals["requests"] == 3
    assert totals["failed"] == 1
    assert totals["cash_usd"] == 0.0061  # payg 0.0021 + failed payg 0.0040
    assert totals["quota_value_usd"] == 0.0312
    assert totals["spend_total"] == 0.0373
    assert totals["failed_cost_share"] == round(0.0040 / 0.0373, 4)
    assert totals["basis_provenance"] == "magpie_reported_cost"
    # A failed attempt is attached to the account that spent it.
    payg_account = next(entry for entry in facts["accounts"].values()
                        if entry["billing_class"] == "payg" and entry["requests"] == 2)
    assert payg_account["failed"] == 1 and payg_account["cash_usd"] == 0.0061


def test_unpriced_rows_are_counted_as_unknown_not_free():
    facts = cost_facts(parse_usage_csv(_csv(UNPRICED_ROW)))
    assert facts["totals"]["unknown_cost"] == 1
    assert facts["totals"]["spend_total"] == 0.0
    assert facts["totals"]["failed_cost_share"] is None


def test_cache_dedupes_overlapping_windows_and_keeps_newest(tmp_path):
    cache = tmp_path / "usage.jsonl"
    rows = parse_usage_csv(_csv(SUBSCRIPTION_ROW, PAYG_ROW))
    assert merge_into_cache(rows, path=cache) == 2
    assert merge_into_cache(rows, path=cache) == 0  # same window again: no double counting

    newer = parse_usage_csv(_csv(FAILED_ROW))
    assert merge_into_cache(newer, path=cache) == 1
    assert {row["request_id"] for row in read_cache(cache)} == {"req-1", "req-2", "req-3"}

    # The cap keeps the newest rows, not the first ones seen.
    merge_into_cache(parse_usage_csv(_csv(UNPRICED_ROW)), path=cache, limit=2)
    assert {row["request_id"] for row in read_cache(cache)} == {"req-3", "req-4"}


def test_ingest_without_a_configured_executable_degrades_quietly(tmp_path):
    result = ingest(cache_path=tmp_path / "usage.jsonl", env={})
    assert result["available"] is False
    assert result["reason"] == "magpie_executable_not_configured"
    assert result["facts"]["totals"]["requests"] == 0
    assert not (tmp_path / "usage.jsonl").exists()


def test_ingest_parses_cli_output_through_one_bounded_call(monkeypatch, tmp_path):
    fake_exe = tmp_path / "magpie.exe"
    fake_exe.write_bytes(b"stub")
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["shell"] = kwargs.get("shell")

        class Done:
            returncode = 0
            stdout = _csv(SUBSCRIPTION_ROW, PAYG_ROW)

        return Done()

    monkeypatch.setattr("subprocess.run", fake_run)
    result = ingest(cache_path=tmp_path / "usage.jsonl", env={"REVERSE_AGENT_MAGPIE_EXE": str(fake_exe)})

    assert result["available"] is True and result["added"] == 2
    assert seen["command"][:3] == [str(fake_exe), "usage", "--csv"]
    assert seen["shell"] is False  # never a shell: fixed argv, explicit binary
    assert result["facts"]["totals"]["spend_total"] == 0.0333


def test_executable_requires_an_absolute_existing_file():
    assert magpie_executable({"REVERSE_AGENT_MAGPIE_EXE": "magpie.exe"}) is None
    assert magpie_executable({"REVERSE_AGENT_MAGPIE_EXE": "C:/definitely/missing.exe"}) is None
    assert magpie_executable({}) is None


@pytest.mark.skipif(not os.environ.get("REVERSE_AGENT_MAGPIE_EXE"),
                    reason="set REVERSE_AGENT_MAGPIE_EXE to read a live Magpie")
def test_live_magpie_usage_is_readable_and_priced():
    result = ingest(last="2h")
    assert result["available"] is True
    assert result["rows"] >= 0
    assert result["facts"]["totals"]["basis_provenance"] == "magpie_reported_cost"


# --- conservative attribution (P1 step 2) ---------------------------------------

from reverse_agent.platform_v1.magpie_usage_ingest import (  # noqa: E402
    attempts_from_store, correlate_usage, economics_runs,
)
from reverse_agent.platform_v1.orchestration_selector import all_in_economics  # noqa: E402

T0 = "2026-11-04T09:00:00+00:00"


def _req(request_id: str, *, at: str, provider: str, cost: str,
         account: str = "", status: str = "200", rejected: str = "false") -> dict:
    text = _csv(_row(time=at, agent=provider, provider=provider, served_model="m",
                     cost_usd=cost, status=status, rejected=rejected,
                     request_id=request_id, session_account=account, provider_key_id="fixture-key"))
    return parse_usage_csv(text)[0]


def _attempt(task_id: str, *, start: str, end: str, executor: str = "codex",
             accepted: bool = True, mode: str = "single") -> dict:
    from reverse_agent.platform_v1.magpie_usage_ingest import _epoch
    return {"task_id": task_id, "executor_kind": executor, "mode": mode,
            "started_at": _epoch(start), "finished_at": _epoch(end),
            "accepted": accepted, "status": "READY_FOR_REVIEW" if accepted else "FAILED"}


def test_requests_inside_one_attempt_are_attributed_with_separate_bases():
    rows = [_req("r1", at="2026-11-04T09:05:00+00:00", provider="codex", cost="0.0100"),
            _req("r2", at="2026-11-04T09:06:00+00:00", provider="codex", cost="0.0300",
                 account="me@example.com")]
    correlated = correlate_usage(rows, [_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00")])
    window = correlated["attempts"]["t1"]
    assert window["requests"] == 2
    assert window["cash_cost_usd"] == 0.01
    assert window["quota_opportunity_units"] == 0.03
    assert window["spend_total"] == 0.04
    assert correlated["summary"]["attributed"] == 2


def test_agent_and_time_mismatches_are_reported_not_forced():
    rows = [_req("r1", at="2026-11-04T09:05:00+00:00", provider="claude", cost="0.01"),
            _req("r2", at="2026-11-04T12:00:00+00:00", provider="codex", cost="0.01")]
    correlated = correlate_usage(rows, [_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00")])
    assert correlated["attempts"]["t1"]["requests"] == 0
    reasons = {item["reason"] for item in correlated["unattributed"]}
    assert reasons == {"no_matching_attempt"}
    assert correlated["summary"]["unattributed"] == 2


def test_overlapping_attempts_of_the_same_agent_are_ambiguous_not_split():
    rows = [_req("r1", at="2026-11-04T09:05:00+00:00", provider="codex", cost="0.02")]
    attempts = [_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00"),
                _attempt("t2", start="2026-11-04T09:04:00+00:00", end="2026-11-04T09:09:00+00:00")]
    correlated = correlate_usage(rows, attempts)
    assert correlated["ambiguous"] == [{"request_id": "r1", "candidates": ["t1", "t2"]}]
    # Neither attempt may claim the spend, and the ambiguity is measurable.
    assert correlated["attempts"]["t1"]["requests"] == 0
    assert correlated["summary"]["ambiguity_rate"] == 1.0


def test_overlapping_attempts_of_different_agents_stay_unambiguous():
    rows = [_req("r1", at="2026-11-04T09:05:00+00:00", provider="codex", cost="0.02"),
            _req("r2", at="2026-11-04T09:05:30+00:00", provider="claude", cost="0.05",
                 account="me@example.com")]
    attempts = [_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00"),
                _attempt("t2", start=T0, end="2026-11-04T09:10:00+00:00", executor="claude_code")]
    correlated = correlate_usage(rows, attempts)
    assert correlated["attempts"]["t1"]["cash_cost_usd"] == 0.02
    assert correlated["attempts"]["t2"]["quota_opportunity_units"] == 0.05
    assert correlated["ambiguous"] == []


def test_slack_absorbs_clock_skew_but_not_a_wrong_day():
    rows = [_req("r1", at="2026-11-04T08:58:30+00:00", provider="codex", cost="0.01")]
    attempt = _attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00")
    assert correlate_usage(rows, [attempt])["attempts"]["t1"]["requests"] == 1
    assert correlate_usage(rows, [attempt], slack_seconds=0)["attempts"]["t1"]["requests"] == 0


def test_attempts_from_store_uses_the_ledger_success_definition():
    from reverse_agent.platform_v1.run_store import TaskStore

    store = TaskStore(":memory:")
    ok = store.create_task(title="ok", executor_kind="codex", binding_ref="b", repository="o/r")
    bad = store.create_task(title="bad", executor_kind="codex", binding_ref="b", repository="o/r")
    store._conn.execute("UPDATE tasks SET status='READY_FOR_REVIEW', created_at=?, updated_at=? WHERE id=?",
                        (T0, "2026-11-04T09:10:00+00:00", ok.id))
    store._conn.execute("UPDATE tasks SET status='FAILED', created_at=?, updated_at=? WHERE id=?",
                        (T0, "2026-11-04T09:12:00+00:00", bad.id))
    store._conn.commit()

    attempts = {item["task_id"]: item for item in attempts_from_store(store)}
    assert attempts[ok.id]["accepted"] is True
    assert attempts[bad.id]["accepted"] is False
    assert attempts[bad.id]["finished_at"] - attempts[bad.id]["started_at"] == 720.0


def test_economics_runs_feed_the_all_in_metric_end_to_end():
    rows = [
        _req("r1", at="2026-11-04T09:05:00+00:00", provider="codex", cost="0.10"),
        _req("r2", at="2026-11-04T09:06:00+00:00", provider="codex", cost="0.10"),
        _req("r3", at="2026-11-04T09:25:00+00:00", provider="codex", cost="0.20"),
        _req("r4", at="2026-11-04T09:45:00+00:00", provider="codex", cost="0.25"),
    ]
    attempts = [_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00", accepted=False),
                _attempt("t2", start="2026-11-04T09:20:00+00:00",
                         end="2026-11-04T09:30:00+00:00", accepted=True),
                _attempt("t3", start="2026-11-04T09:40:00+00:00",
                         end="2026-11-04T09:50:00+00:00", accepted=True)]
    # This fixture owns every request in the declared interval. Live exports
    # need a separate completeness receipt before they may declare coverage.
    runs = economics_runs(correlate_usage(rows, attempts, coverage_window=(
        attempts[0]["started_at"], attempts[-1]["finished_at"])))

    economy = all_in_economics(runs, basis="cash")["single"]
    assert economy["runs"] == 3 and economy["accepted_runs"] == 2
    # 0.20 wasted on the failed attempt is inside the numerator: 0.65 / 2.
    assert economy["total_cost"] == 0.65
    assert economy["cost_per_accepted_all_in"] == 0.325
    assert economy["failed_cost_share"] == round(0.20 / 0.65, 4)
    assert all(run["cost_complete"] for run in runs)


def test_unmatched_attempt_is_unknown_not_free():
    """55 attempts with zero matched requests must not report "$0 per change"."""
    runs = economics_runs(correlate_usage([], [_attempt("t1", start=T0,
                                                       end="2026-11-04T09:10:00+00:00")]))
    assert runs[0]["cost_complete"] is False
    assert runs[0]["cash_cost_usd"] is None
    economy = all_in_economics(runs, basis="cash")["single"]
    assert economy["unpriced_runs"] == 1
    assert economy["cost_per_accepted_all_in"] is None

    # A labelled lower bound is allowed for dashboards, never for a decision.
    lenient = economics_runs(correlate_usage([], [_attempt("t1", start=T0,
                                                           end="2026-11-04T09:10:00+00:00")]),
                             strict=False)
    assert lenient[0]["cash_cost_usd"] == 0.0
    assert lenient[0]["cost_complete"] is False


def test_disjoint_periods_are_reported_as_no_overlap_not_as_a_match_failure():
    rows = [_req("r1", at="2026-11-04T09:05:00+00:00", provider="codex", cost="0.01")]
    old = _attempt("t-old", start="2026-10-18T15:00:00+00:00", end="2026-10-18T15:10:00+00:00")
    summary = correlate_usage(rows, [old])["summary"]
    assert summary["attributed"] == 0
    assert summary["overlap"] == "none"
    assert summary["overlap_attempts"] == 0
    assert summary["usage_window"] is not None


# --- exact join key (P1 step 3) --------------------------------------------------

def _req_with_session(request_id: str, *, at: str, session: str, cost: str,
                      agent: str = "codex", account: str = "") -> dict:
    text = _csv(_row(time=at, agent=agent, provider="openai", served_model="m",
                     cost_usd=cost, status="200", rejected="false", request_id=request_id,
                     session=session, session_account=account, provider_key_id="fixture-key"))
    return parse_usage_csv(text)[0]


def test_exact_session_id_beats_two_competing_time_windows():
    rows = [_req_with_session("r1", at="2026-11-04T09:05:00+00:00", session="sess-B", cost="0.30")]
    attempts = [
        {**_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00"), "agent_session_id": "sess-A"},
        {**_attempt("t2", start=T0, end="2026-11-04T09:10:00+00:00"), "agent_session_id": "sess-B"},
    ]
    correlated = correlate_usage(rows, attempts)
    # Both windows contain the request, but the id settles it: no ambiguity.
    assert correlated["ambiguous"] == []
    assert correlated["attempts"]["t2"]["requests"] == 1
    assert correlated["attempts"]["t1"]["requests"] == 0
    assert correlated["summary"]["exact_attempts"] == 2


def test_exact_session_id_ignores_the_clock():
    rows = [_req_with_session("r1", at="2026-11-05T23:00:00+00:00", session="sess-A", cost="0.10")]
    attempt = {**_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00"),
               "agent_session_id": "sess-A"}
    assert correlate_usage(rows, [attempt])["attempts"]["t1"]["cash_cost_usd"] == 0.1
    # Without the id the same request is outside every window.
    assert correlate_usage(rows, [{**attempt, "agent_session_id": None}])[
        "attempts"]["t1"]["requests"] == 0


def test_unknown_session_falls_back_to_the_window():
    rows = [_req_with_session("r1", at="2026-11-04T09:05:00+00:00", session="sess-unknown", cost="0.10")]
    attempt = {**_attempt("t1", start=T0, end="2026-11-04T09:10:00+00:00"),
               "agent_session_id": "sess-A"}
    correlated = correlate_usage(rows, [attempt])
    assert correlated["attempts"]["t1"]["requests"] == 1  # time window still applies


def test_attempts_from_store_reads_the_session_id_from_the_completion_event():
    import json

    from reverse_agent.platform_v1.run_store import TaskStore

    store = TaskStore(":memory:")
    task = store.create_task(title="t", executor_kind="codex", binding_ref="b", repository="o/r")
    # seq is AUTOINCREMENT: insertion order is the event order.
    for index, session in enumerate(("old-session", "final-session"), start=1):
        store._conn.execute(
            "INSERT INTO task_events (id, task_id, type, timestamp, title, description, raw_log, metadata) "
            "VALUES (?, ?, 'EXECUTOR_COMPLETED', ?, '', '', '', ?)",
            (f"ev-{index}", task.id, T0, json.dumps({"agent_session_id": session})))
    store._conn.execute("UPDATE tasks SET status='READY_FOR_REVIEW', created_at=?, updated_at=? WHERE id=?",
                        (T0, "2026-11-04T09:10:00+00:00", task.id))
    store._conn.commit()

    attempts = {item["task_id"]: item for item in attempts_from_store(store)}
    assert attempts[task.id]["agent_session_id"] == "final-session"  # latest wins


def test_attempt_without_a_session_event_stays_attributable_by_time():
    from reverse_agent.platform_v1.run_store import TaskStore

    store = TaskStore(":memory:")
    task = store.create_task(title="t", executor_kind="codex", binding_ref="b", repository="o/r")
    store._conn.execute("UPDATE tasks SET status='FAILED', created_at=?, updated_at=? WHERE id=?",
                        (T0, "2026-11-04T09:10:00+00:00", task.id))
    store._conn.commit()
    attempts = {item["task_id"]: item for item in attempts_from_store(store)}
    assert attempts[task.id]["agent_session_id"] is None


def test_no_usage_rows_reports_no_overlap_not_partial():
    """An empty dataset must not be described as "partially overlapping"."""
    old = _attempt("t-old", start="2026-10-18T15:00:00+00:00", end="2026-10-18T15:10:00+00:00")
    summary = correlate_usage([], [old])["summary"]
    assert summary["overlap"] == "none"
    assert summary["overlap_attempts"] == 0
    assert summary["usage_window"] is None
