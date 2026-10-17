"""All fixtures are local SQLite copies. Never inspect or modify production TaskStore."""
import hashlib
from pathlib import Path
import sqlite3

import pytest

from reverse_agent.platform_v1.orphan_claim_audit import inspect_orphan_claims

NOW = 10_000_000


def fixture_db(tmp_path, *, task_status="FAILED", claim_expires=1,
               external=False, reservation=True):
    path = tmp_path / "synthetic-tasks.sqlite3"
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE platform_coordinator_claims(
          task_id TEXT, window_id TEXT, epoch INTEGER, expires_at_ms INTEGER, status TEXT);
        CREATE TABLE tasks(id TEXT, status TEXT);
        CREATE TABLE platform_autonomous_windows(id TEXT, status TEXT);
        CREATE TABLE platform_budget_reservations(
          task_id TEXT, window_id TEXT, claim_epoch INTEGER, state TEXT,
          observed_token_units INTEGER, observed_cost_micro_units INTEGER);
        CREATE TABLE durable_external_operations(task_id TEXT);
    """)
    db.execute("INSERT INTO tasks VALUES(?,?)", ("task-example", task_status))
    db.execute("INSERT INTO platform_autonomous_windows VALUES(?,?)",
               ("window-expired", "EXPIRED"))
    db.execute("INSERT INTO platform_coordinator_claims VALUES(?,?,?,?,?)",
               ("task-example", "window-expired", 1, claim_expires, "ACTIVE"))
    if reservation:
        db.execute("INSERT INTO platform_budget_reservations VALUES(?,?,?,?,?,?)",
                   ("task-example", "window-expired", 1, "ACTIVE", None, None))
    if external:
        db.execute("INSERT INTO durable_external_operations VALUES(?)", ("task-example",))
    db.commit()
    db.close()
    return path


@pytest.mark.parametrize("task_status,external,expires,reservation,reason", [
    ("FAILED", False, 1, True, "TERMINAL_FAILED_REMOTE_UNVERIFIED"),
    ("INTERRUPTED", False, 1, True, "INTERRUPTED_REQUIRES_RECEIPT"),
    ("FAILED", True, 1, True, "EXTERNAL_OPERATION_REQUIRES_RECEIPT"),
    ("FAILED", False, NOW + 1, True, "LEASE_STILL_CURRENT_LIVENESS_UNKNOWN"),
    ("FAILED", False, 1, False, "INCONSISTENT_CLAIM_OR_RESERVATION"),
])
def test_orphan_claims_are_classified_but_never_auto_released(
    tmp_path, task_status, external, expires, reservation, reason
):
    path = fixture_db(tmp_path, task_status=task_status, external=external,
                      claim_expires=expires, reservation=reservation)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = inspect_orphan_claims(path, now_ms=NOW)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert before == after
    assert result["state"] == "HOLD_REMOTE_RECONCILIATION"
    assert result["dispatch_permitted"] is False
    assert result["reconcile_permitted"] is False
    assert result["auto_release_permitted"] is False
    assert len(result["claims"]) == 1
    claim = result["claims"][0]
    assert claim["reason"] == reason
    assert not claim["safe_to_release"] and not claim["safe_to_dispatch"]
    assert claim["usage_observed"] is False
    assert "owner" not in claim and "credential" not in claim


def test_empty_claims_are_not_authorization(tmp_path):
    path = fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE platform_coordinator_claims SET status = 'FAILED'")
    result = inspect_orphan_claims(path, now_ms=NOW)
    assert result["state"] == "NO_ACTIVE_CLAIMS"
    assert result["claims"] == []
    assert result["dispatch_permitted"] is False


def test_missing_db_schema_and_invalid_clock_fail_closed(tmp_path):
    assert inspect_orphan_claims(tmp_path / "absent.sqlite3")["state"] == "UNKNOWN"
    path = tmp_path / "empty.sqlite3"
    sqlite3.connect(path).close()
    assert inspect_orphan_claims(path)["reason"] == "snapshot_read_failed"
    assert inspect_orphan_claims(path, now_ms=-1)["reason"] == "invalid_clock"


def test_large_claim_queue_is_bounded_and_not_treated_as_clear(tmp_path):
    path = fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        db.executemany("INSERT INTO platform_coordinator_claims VALUES(?,?,?,?,?)",
                       [(f"other-{i}", "window-expired", 1, 1, "ACTIVE") for i in range(500)])
    result = inspect_orphan_claims(path, now_ms=NOW)
    assert result["state"] == "UNKNOWN"
    assert result["reason"] == "claim_count_limit_exceeded"
    assert result["dispatch_permitted"] is False


def test_malformed_path_fails_closed_without_disclosing_path():
    result = inspect_orphan_claims("private-path\x00.sqlite3", now_ms=NOW)
    assert result["state"] == "UNKNOWN"
    assert result["claims"] == []
    assert result["dispatch_permitted"] is False
    assert "private-path" not in str(result)


@pytest.mark.parametrize("operation", ["expanduser", "resolve", "is_file"])
@pytest.mark.parametrize("error", [OSError, ValueError, RuntimeError])
def test_path_errors_fail_closed(tmp_path, monkeypatch, operation, error):
    def fail(*args, **kwargs):
        raise error("private-filesystem-details")

    monkeypatch.setattr(Path, operation, fail)
    result = inspect_orphan_claims(tmp_path / "private.sqlite3", now_ms=NOW)
    assert result == {
        "state": "UNKNOWN", "reason": "snapshot_read_failed", "claims": [],
        "dispatch_permitted": False, "reconcile_permitted": False,
        "auto_release_permitted": False,
    }


def test_large_unindexed_journal_is_scanned_once_for_shared_tasks(tmp_path, monkeypatch):
    path = fixture_db(tmp_path)
    with sqlite3.connect(path) as db:
        db.executemany("INSERT INTO platform_coordinator_claims VALUES(?,?,?,?,?)",
                       [("task-example", "window-expired", epoch, 1, "ACTIVE")
                        for epoch in range(2, 500)])
        db.execute("INSERT INTO tasks VALUES('no-operation', 'FAILED')")
        db.execute("INSERT INTO platform_coordinator_claims VALUES(?,?,?,?,?)",
                   ("no-operation", "window-expired", 1, 1, "ACTIVE"))
        db.executemany("INSERT INTO platform_budget_reservations VALUES(?,?,?,?,?,?)",
                       [("task-example", "window-expired", epoch, "ACTIVE", None, None)
                        for epoch in range(2, 500)]
                       + [("no-operation", "window-expired", 1, "ACTIVE", None, None)])
        db.executemany("INSERT INTO durable_external_operations VALUES(?)",
                       (("unrelated-task",) for _ in range(100_000)))
        db.executemany("INSERT INTO durable_external_operations VALUES(?)",
                       [("task-example",)] * 3)

    # Bound SQLite VM work, not elapsed time: 500 full journal scans exceed
    # this budget by orders of magnitude. No task_id index exists in this fixture.
    connect = sqlite3.connect
    progress_calls = 0

    def progress():
        nonlocal progress_calls
        progress_calls += 1
        return int(progress_calls > 2_000)

    def bounded_connect(*args, **kwargs):
        conn = connect(*args, **kwargs)
        conn.set_progress_handler(progress, 1_000)
        return conn

    monkeypatch.setattr(sqlite3, "connect", bounded_connect)
    result = inspect_orphan_claims(path, now_ms=NOW)
    assert result["state"] == "HOLD_REMOTE_RECONCILIATION"
    assert len(result["claims"]) == 500
    assert result["dispatch_permitted"] is False
    for claim in result["claims"]:
        if claim["task_id"] == "task-example":
            assert claim["external_operation_count"] == 3
            assert claim["reason"] == "EXTERNAL_OPERATION_REQUIRES_RECEIPT"
        else:
            assert claim["external_operation_count"] == 0
            assert claim["reason"] == "TERMINAL_FAILED_REMOTE_UNVERIFIED"
        assert claim["safe_to_release"] is False
        assert claim["safe_to_dispatch"] is False
