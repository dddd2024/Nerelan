"""Provider-free tests for the zero-LLM deterministic health audit."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from reverse_agent.platform_v1.health_audit import main as audit_main, run_health_audit

NOW = datetime(2026, 11, 26, 10, 0, 0, tzinfo=timezone.utc)
RECENT = "2026-11-25T10:00:00Z"


def _init_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE platform_autonomous_windows (id TEXT PRIMARY KEY, status TEXT);
        CREATE TABLE platform_goals (id TEXT PRIMARY KEY, status TEXT, window_id TEXT, title TEXT);
        CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, created_at TEXT);
        CREATE TABLE platform_goal_task_links (goal_id TEXT, task_id TEXT);
        CREATE TABLE platform_publications (id TEXT PRIMARY KEY, task_id TEXT);
        CREATE TABLE task_usage_observations (
            id TEXT PRIMARY KEY, task_id TEXT, provider_id TEXT, model_id TEXT,
            input_units INTEGER, cache_read_units INTEGER, cache_write_units INTEGER,
            cost_micro_units INTEGER, created_at TEXT
        );
        CREATE TABLE platform_operation_receipts (
            id TEXT PRIMARY KEY, operation_type TEXT, subject_id TEXT, created_at TEXT
        );
        """
    )
    conn.commit()
    return conn


def _by_id(report: dict) -> dict[str, dict]:
    return {item["id"]: item for item in report["invariants"]}


def test_healthy_db_and_missing_optional_inputs_stay_unknown(tmp_path: Path) -> None:
    db = tmp_path / "tasks.sqlite3"
    conn = _init_db(db)
    conn.execute("INSERT INTO platform_autonomous_windows VALUES ('w-act', 'ACTIVE')")
    conn.execute("INSERT INTO platform_goals VALUES ('g1', 'RUNNING', 'w-act', '#100 Active work')")
    conn.execute("INSERT INTO tasks VALUES ('t1', 'READY_FOR_REVIEW', ?)", (RECENT,))
    conn.execute("INSERT INTO platform_goal_task_links VALUES ('g1', 't1')")
    for i in range(20):
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 't1', 'claude-code', 'claude-sonnet', 100, 900, 0, 5000, ?)",
            (f"u-{i}", RECENT),
        )
    conn.execute("INSERT INTO platform_operation_receipts VALUES ('r1', 'policy_evaluation', 't1', ?)", (RECENT,))
    conn.commit()
    conn.close()

    report = run_health_audit(db, now=NOW)
    inv = _by_id(report)
    assert report["overall_status"] == "PARTIAL_UNKNOWN"
    assert inv["failed_fresh_token_share"]["status"] == "OK"
    assert inv["unpriced_usage_obs_ratio"]["status"] == "OK"
    assert inv["low_cache_hit_routes"]["status"] == "OK"
    assert inv["goal_hygiene"]["status"] == "OK"
    assert inv["goal_hygiene"]["metric"]["active_window_running"] == 1
    assert inv["goal_hygiene"]["metric"]["closed_issue_active_goals"] == "UNKNOWN"
    assert inv["probe_error_rate"]["status"] == "UNKNOWN"
    assert inv["supervision_to_worker_cost_ratio"]["status"] == "UNKNOWN"
    assert inv["waiting_receipt_rate"]["status"] == "OK"
    assert inv["stalled_or_repeating_tasks"]["status"] == "OK"


def test_all_eight_invariants_alert_and_preserve_stranded_publications(tmp_path: Path) -> None:
    db = tmp_path / "tasks.sqlite3"
    conn = _init_db(db)
    conn.executemany("INSERT INTO platform_autonomous_windows VALUES (?, ?)", [
        ("w-act", "ACTIVE"),
        ("w-stop", "STOPPED"),
    ])
    conn.executemany("INSERT INTO platform_goals VALUES (?, ?, ?, ?)", [
        ("g-act", "RUNNING", "w-act", "#200 Live goal"),
        ("g-strand-pub", "RUNNING", "w-stop", "#201 Stranded with PR"),
        ("g-dup-1", "BLOCKED", "w-stop", "#202 Duplicate"),
        ("g-dup-2", "PLANNED", "w-act", "#202 Duplicate"),
    ])
    for i in range(4):
        tid = f"tf-{i}"
        conn.execute("INSERT INTO tasks VALUES (?, 'FAILED', ?)", (tid, RECENT))
        conn.execute("INSERT INTO platform_goal_task_links VALUES ('g-act', ?)", (tid,))
    conn.execute("INSERT INTO tasks VALUES ('t-pub', 'READY_FOR_REVIEW', ?)", (RECENT,))
    conn.execute("INSERT INTO platform_goal_task_links VALUES ('g-strand-pub', 't-pub')")
    conn.execute("INSERT INTO platform_publications VALUES ('pub-1', 't-pub')")

    # 20 failed uncached unpriced rows -> triggers failed_fresh_token_share, unpriced_usage_obs_ratio, low_cache_hit_routes
    for i in range(20):
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 'tf-0', 'trae-cn', 'glm-5.3-max', 1000, 0, 0, 0, ?)",
            (f"uf-{i}", RECENT),
        )
    # 500 receipts in 24h for one waiting task -> 20.83/h > 20
    for i in range(500):
        conn.execute("INSERT INTO platform_operation_receipts VALUES (?, 'policy_evaluation', 'tf-0', ?)", (f"rc-{i}", RECENT))
    conn.commit()
    conn.close()

    magpie_csv = tmp_path / "magpie.csv"
    magpie_csv.write_text(
        "\n".join([
            "agent,status,error_type,rejected,cost_usd",
            "Python-urllib,402,402,0,0.0",
            "Python-urllib,200,,0,0.0",
            "antigravity,200,,0,50.0",
            "opencode,200,,0,5.0",
        ]),
        encoding="utf-8",
    )

    report = run_health_audit(
        db,
        now=NOW,
        magpie_csv_path=magpie_csv,
        closed_issue_numbers=[200],
    )
    inv = _by_id(report)
    assert report["overall_status"] == "ALERT"
    assert inv["failed_fresh_token_share"]["status"] == "ALERT"
    assert inv["unpriced_usage_obs_ratio"]["status"] == "ALERT"
    assert inv["probe_error_rate"]["status"] == "ALERT"
    assert inv["probe_error_rate"]["metric"] == 0.5
    assert inv["low_cache_hit_routes"]["status"] == "ALERT"
    assert inv["goal_hygiene"]["status"] == "ALERT"
    assert inv["goal_hygiene"]["metric"] == {
        "active_window_running": 1,
        "stranded_running_inactive_windows": 1,
        "stranded_with_publications": 1,
        "duplicate_issue_groups": 0,
        "blocked_duplicate_issue_groups": 0,
        "closed_issue_active_goals": 1,
    }
    assert inv["supervision_to_worker_cost_ratio"]["status"] == "ALERT"
    assert inv["supervision_to_worker_cost_ratio"]["metric"] == 10.0
    assert inv["waiting_receipt_rate"]["status"] == "ALERT"
    assert inv["stalled_or_repeating_tasks"]["status"] == "ALERT"


def test_cross_module_usage_status_null_vs_zero_and_active_only_duplicates(tmp_path: Path) -> None:
    db = tmp_path / "tasks.sqlite3"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE platform_autonomous_windows (id TEXT PRIMARY KEY, status TEXT);
        CREATE TABLE platform_goals (id TEXT PRIMARY KEY, status TEXT, window_id TEXT, title TEXT);
        CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT, created_at TEXT);
        CREATE TABLE platform_goal_task_links (goal_id TEXT, task_id TEXT);
        CREATE TABLE platform_publications (id TEXT PRIMARY KEY, task_id TEXT);
        CREATE TABLE task_usage_observations (
            id TEXT PRIMARY KEY, task_id TEXT, provider_id TEXT, model_id TEXT,
            status TEXT, input_units INTEGER, cache_read_units INTEGER, cache_write_units INTEGER,
            cost_micro_units INTEGER, created_at TEXT
        );
        CREATE TABLE platform_operation_receipts (
            id TEXT PRIMARY KEY, operation_type TEXT, subject_id TEXT, created_at TEXT
        );
        """
    )
    conn.execute("INSERT INTO platform_autonomous_windows VALUES ('w-act', 'ACTIVE')")
    conn.executemany("INSERT INTO platform_goals VALUES (?, ?, ?, ?)", [
        ("gb-1", "BLOCKED", "w-act", "#300 Historical blocked 1"),
        ("gb-2", "BLOCKED", "w-act", "#300 Historical blocked 2"),
        ("ga-1", "RUNNING", "w-act", "#301 Single active"),
    ])
    conn.executemany("INSERT INTO tasks VALUES (?, ?, ?)", [
        ("t-fix", "READY_FOR_REVIEW_FIXTURE", RECENT),
        ("t-fail", "FAILED", RECENT),
    ])
    # 20 UNKNOWN rows should NOT inflate low_cache_hit_routes obs count or denominator
    for i in range(25):
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 't-fix', 'unknown-prov', 'm-unk', 'UNKNOWN', NULL, NULL, NULL, NULL, ?)",
            (f"unk-{i}", RECENT),
        )
    # 10 PARTIAL rows with NULL cost + 10 OBSERVED rows with cost=0 + 10 OBSERVED rows with positive cost
    for i in range(10):
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 't-fix', 'claude-code', 'claude-sonnet', 'PARTIAL', 100, 900, 0, NULL, ?)",
            (f"part-{i}", RECENT),
        )
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 't-fix', 'opencode', 'free-m', 'OBSERVED', 100, 900, 0, 0, ?)",
            (f"zero-{i}", RECENT),
        )
        conn.execute(
            "INSERT INTO task_usage_observations VALUES (?, 't-fix', 'opencode', 'paid-m', 'OBSERVED', 100, 900, 0, 1200, ?)",
            (f"pos-{i}", RECENT),
        )
    conn.execute(
        "INSERT INTO task_usage_observations VALUES ('fail-1', 't-fail', 'opencode', 'paid-m', 'OBSERVED', 500, 0, 0, 500, ?)",
        (RECENT,),
    )
    conn.commit()
    conn.close()

    report = run_health_audit(db, now=NOW)
    inv = _by_id(report)
    unpriced = inv["unpriced_usage_obs_ratio"]
    assert unpriced["metric"] == round(20 / 31, 4)
    assert "null_cost_rows=10" in unpriced["detail"]
    assert "zero_cost_rows=10" in unpriced["detail"]
    assert "positive_cost_rows=11" in unpriced["detail"]
    assert "unknown_status_rows=25" in unpriced["detail"]
    assert inv["low_cache_hit_routes"]["status"] == "OK"
    assert inv["failed_fresh_token_share"]["metric"] == round(500 / 3500, 4)
    assert inv["goal_hygiene"]["status"] == "OK"
    assert inv["goal_hygiene"]["metric"]["duplicate_issue_groups"] == 0
    assert inv["goal_hygiene"]["metric"]["blocked_duplicate_issue_groups"] == 1


def test_magpie_csv_handles_unpriced_boolean_rejected_and_lookback_window(tmp_path: Path) -> None:
    db = tmp_path / "tasks.sqlite3"
    conn = _init_db(db)
    conn.close()

    csv_path = tmp_path / "magpie.csv"
    csv_path.write_text(
        "\n".join([
            "time,agent,status,error,rejected,cost_usd",
            # Out of 7-day window -> must be excluded from both invariants
            "2026-11-01T10:00:00Z,Python-urllib,500,old_outage,true,0.0",
            "2026-11-01T10:00:00Z,antigravity,200,,false,99.0",
            # In window: probe failed with status=0 + error + rejected="true"
            "2026-11-25T10:00:00-04:00,Python-urllib,0,connection_reset,true,0.0",
            "2026-11-25T10:01:00-04:00,Python-urllib,200,,false,0.0",
            # In window: missing supervision cost_usd must leave ratio UNKNOWN (not $0.0)
            "2026-11-25T10:02:00-04:00,codex,200,,false,",
            "2026-11-25T10:03:00-04:00,opencode,200,,false,5.0",
        ]),
        encoding="utf-8",
    )

    report = run_health_audit(db, now=NOW, lookback_days=7, magpie_csv_path=csv_path)
    inv = _by_id(report)
    assert inv["probe_error_rate"]["status"] == "ALERT"
    assert inv["probe_error_rate"]["metric"] == 0.5
    assert inv["supervision_to_worker_cost_ratio"]["status"] == "UNKNOWN"
    assert inv["supervision_to_worker_cost_ratio"]["metric"] is None
    assert "unpriced_sup_rows=1" in inv["supervision_to_worker_cost_ratio"]["detail"]


def test_cli_json_smoke(tmp_path: Path, capsys) -> None:
    db = tmp_path / "tasks.sqlite3"
    conn = _init_db(db)
    conn.close()
    rc = audit_main(["--db", str(db), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["schema_version"] == 1
    assert len(out["invariants"]) == 8
