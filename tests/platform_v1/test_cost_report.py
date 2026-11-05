"""The old metric and the new metric, side by side, from one dataset.

The point of this suite is that the numbers must be *comparable but not
blended*: the legacy metric sees only accepted runs, the all-in metrics see every
attempt, and the three bases stay apart.
"""
from __future__ import annotations

import json

from reverse_agent.platform_v1.cost_report import build_cost_report
from reverse_agent.platform_v1.magpie_usage_ingest import parse_usage_csv
from reverse_agent.platform_v1.run_store import TaskStore

# Same column order Magpie prints; kept local so this suite stands alone.
COLUMNS = ("time", "agent", "requested_model", "provider", "host", "model", "served_model",
           "swapped", "effort", "input_tokens", "output_tokens", "cache_write_tokens",
           "cache_read_tokens", "reasoning_tokens", "cost_usd", "duration_ms", "ttft_ms",
           "status", "error", "session", "kind", "provider_key_id", "provider_key_name",
           "provider_account", "route_id", "request_id", "rejected", "session_account")


def _row(**values: str) -> str:
    return ",".join(str(values.get(name, "")) for name in COLUMNS)

T_START = "2026-11-04T09:00:00+00:00"
T_END_OK = "2026-11-04T09:10:00+00:00"
T_END_BAD = "2026-11-04T09:20:00+00:00"


def _seed(store, *, title: str, status: str, created: str, updated: str,
          model: str = "claude-sonnet-5-5", tokens=(1000, 500, 100, 2000, 0)):
    task = store.create_task(title=title, executor_kind="codex", binding_ref="b-binding",
                             repository="o/r")
    store._conn.execute("UPDATE tasks SET status=?, created_at=?, updated_at=? WHERE id=?",
                        (status, created, updated, task.id))
    store._conn.execute(
        "INSERT INTO task_usage_observations (id, task_id, window_id, claim_epoch, execution_id, "
        "role, model_id, provider_id, source_kind, source_id, status, input_units, output_units, "
        "reasoning_units, cache_read_units, cache_write_units, payload_digest, created_at) "
        "VALUES (?, ?, '', 0, 'e', 'executor', ?, 'p', 's', ?, 'OBSERVED', ?, ?, ?, ?, ?, '', '')",
        (f"u-{task.id}", task.id, model, f"src-{task.id}", *tokens))
    store._conn.commit()
    return task.id


def _usage_row(request_id: str, at: str, cost: str, *, account: str = "") -> dict:
    text = ",".join(COLUMNS) + "\n" + _row(
        time=at, agent="codex", provider="openai", served_model="claude-sonnet-5-5",
        cost_usd=cost, status="200", rejected="false", request_id=request_id,
        session_account=account, provider_key_id="fixture-key")
    return parse_usage_csv(text)[0]


def test_report_keeps_legacy_and_all_in_side_by_side():
    store = TaskStore(":memory:")
    ok = _seed(store, title="ok", status="READY_FOR_REVIEW", created=T_START, updated=T_END_OK)
    bad = _seed(store, title="bad", status="FAILED", created=T_END_OK, updated=T_END_BAD)

    rows = [
        _usage_row("r-ok", "2026-11-04T09:05:00+00:00", "0.10"),
        _usage_row("r-bad", "2026-11-04T09:15:00+00:00", "0.40"),
    ]
    report = build_cost_report(store, rows, coverage_window=(1793782800, 1793784000))

    assert report["attribution"]["attributed"] == 2
    assert report["attribution"]["overlap"] == "full"  # both attempts sit inside the usage window
    assert report["window"] == {"attempts": 2, "requests": 2}

    cash = report["all_in"]["cash"]["per_mode"]["single"]
    assert cash["accepted_runs"] == 1 and cash["runs"] == 2
    # 0.50 spent across both attempts, 0.40 of it bought nothing accepted.
    assert cash["total_cost"] == 0.5
    assert cash["cost_per_accepted_all_in"] == 0.5
    assert cash["failed_cost_share"] == 0.8

    legacy = report["legacy"]["per_mode"]["single"]
    # The legacy metric sees only the accepted attempt, so it looks cheaper.
    assert legacy["accepted_runs"] == 1
    assert legacy["cost_per_accepted"] is not None
    assert legacy["cost_per_accepted"] < cash["cost_per_accepted_all_in"]
    assert report["all_in"]["cash"]["metric"].endswith("(cash)")
    assert report["all_in"]["quota"]["per_mode"]["single"]["total_cost"] == 0.0
    assert json.dumps(report)  # JSON-safe end to end


def test_report_refuses_to_invent_magpie_numbers_without_usage():
    store = TaskStore(":memory:")
    _seed(store, title="ok", status="READY_FOR_REVIEW", created=T_START, updated=T_END_OK)
    report = build_cost_report(store, [])

    assert report["attribution"]["attributed"] == 0
    for basis in ("cash", "quota"):
        entry = report["all_in"][basis]["per_mode"]["single"]
        assert entry["cost_per_accepted_all_in"] is None
        assert entry["unpriced_runs"] == entry["runs"]
    # The local estimate still works — that is exactly why it stays as fallback.
    assert report["legacy"]["per_mode"]["single"]["cost_per_accepted"] is not None
    assert report["all_in"]["list_price"]["per_mode"]["single"][
        "cost_per_accepted_all_in"] is not None


def test_report_states_its_caveats_and_provenance():
    store = TaskStore(":memory:")
    report = build_cost_report(store, [])
    caveats = " ".join(report["caveats"])
    assert "list_price is an estimate" in caveats
    assert "subscription run bills 0" in caveats
    assert "carries null, never 0" in caveats
    assert "time-window" in caveats


# --- comparison snapshots (the experiment harness) ------------------------------

from reverse_agent.platform_v1.cost_report import (  # noqa: E402
    SNAPSHOT_VERSION, compare_snapshots, snapshot, snapshot_document,
)


def _report_for(store, rows):
    return build_cost_report(store, rows, coverage_window=(1793782800, 1793784000))


def test_snapshot_roundtrips_and_compare_writes_nothing(tmp_path):
    store = TaskStore(":memory:")
    _seed(store, title="ok", status="READY_FOR_REVIEW", created=T_START, updated=T_END_OK)
    report = _report_for(store, [_usage_row("r-ok", "2026-11-04T09:05:00+00:00", "0.10")])

    path = tmp_path / "baseline.json"
    document = snapshot(report, label="local-routing", path=path)
    assert document["version"] == SNAPSHOT_VERSION
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["label"] == "local-routing"
    assert on_disk["all_in"]["cash"]["metric"]

    # Comparing must not overwrite the baseline it reads.
    before = path.read_text(encoding="utf-8")
    comparison = compare_snapshots(on_disk, snapshot_document(report, label="candidate"))
    assert path.read_text(encoding="utf-8") == before
    assert comparison["baseline"] == "local-routing"
    assert comparison["candidate"] == "candidate"
    assert any(row["basis"] == "cash" for row in comparison["rows"])
    assert "regression" in comparison["note"]


def test_compare_reports_the_direction_and_keeps_accepted_runs_in_view(tmp_path):
    store = TaskStore(":memory:")
    _seed(store, title="ok", status="READY_FOR_REVIEW", created=T_START, updated=T_END_OK)
    cheap = snapshot_document(_report_for(store, [
        _usage_row("r1", "2026-11-04T09:05:00+00:00", "0.10")]), label="cheap")
    pricey = snapshot_document(_report_for(store, [
        _usage_row("r1", "2026-11-04T09:05:00+00:00", "0.30")]), label="pricey")

    comparison = compare_snapshots(cheap, pricey)
    cash = next(row for row in comparison["rows"] if row["basis"] == "cash"
                and row["section"] == "all_in" and row["mode"] == "single")
    assert cash["before"] == 0.1 and cash["after"] == 0.3
    assert cash["delta"] == 0.2 and cash["relative"] == 2.0
    assert cash["before_accepted"] == 1 and cash["after_accepted"] == 1

    reversed_direction = compare_snapshots(pricey, cheap)
    cash_back = next(row for row in reversed_direction["rows"] if row["basis"] == "cash"
                     and row["section"] == "all_in" and row["mode"] == "single")
    assert all(row["before"] is not None or row["after"] is not None
               for row in reversed_direction["rows"])
    assert cash_back["delta"] == -0.2


def test_compare_refuses_incomparable_versions():
    import pytest as _pytest

    with _pytest.raises(ValueError):
        compare_snapshots({"version": SNAPSHOT_VERSION + 1, "all_in": {}},
                          {"version": SNAPSHOT_VERSION, "all_in": {}})


# --- doctor: can the experiment run at all? -------------------------------------

from reverse_agent.platform_v1.cost_report import doctor_report  # noqa: E402


def _doctor(**overrides):
    base = dict(exe_configured=True, magpie_status="available",
                rows=[{"request_id": "r1"}],
                attempts=[{"task_id": "t1", "agent_session_id": "sess-1"}],
                correlated={"summary": {"overlap": "full", "overlap_attempts": 1,
                                        "attributed": 1, "ambiguity_rate": 0.0,
                                        "coverage_complete": True}})
    base.update(overrides)
    return doctor_report(**base)


def test_doctor_is_ready_when_every_input_exists():
    report = _doctor()
    assert report["ready"] is True and report["blockers"] == []
    assert report["next"].startswith("run the comparison")
    assert all(check["ok"] for check in report["checks"].values())


def test_doctor_names_every_missing_input_instead_of_failing_vaguely():
    report = _doctor(exe_configured=False, magpie_status=None, rows=[],
                     attempts=[{"task_id": "t1", "agent_session_id": None}],
                     correlated={"summary": {"overlap": "none", "overlap_attempts": 0,
                                             "attributed": 0, "ambiguity_rate": None}})
    assert report["ready"] is False
    assert set(report["blockers"]) == {
        "magpie_cli_configured", "magpie_reachable", "usage_rows",
        "tasks_with_session_id", "windows_overlap", "complete_cost_evidence"}
    assert "no request was attributed to a task" in report["warnings"]
    assert "re-run --doctor" in report["next"]


def test_doctor_warns_when_attribution_is_mostly_a_time_guess():
    report = _doctor(correlated={"summary": {"overlap": "partial", "overlap_attempts": 3,
                                             "attributed": 4, "ambiguity_rate": 0.5}})
    assert report["ready"] is False  # partial evidence cannot authorize cost decisions
    assert any("ambiguity_rate=0.5" in warning for warning in report["warnings"])


def test_doctor_reports_the_new_run_requirement_in_plain_language():
    report = _doctor(attempts=[{"task_id": "t1", "agent_session_id": None}] * 3)
    detail = report["checks"]["tasks_with_session_id"]["detail"]
    assert detail.startswith("0/3")
    assert "only runs after the join-key change" in detail
