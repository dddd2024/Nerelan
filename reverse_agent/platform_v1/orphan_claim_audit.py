"""Read-only classification of orphaned coordinator claims.

This is diagnostics, NOT a reconciler. Neither expired leases, failed Tasks nor
missing external-operation records establish that remote side effects stopped.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import time
from urllib.parse import quote


def _unknown(reason: str) -> dict:
    return {
        "state": "UNKNOWN", "reason": reason, "claims": [],
        "dispatch_permitted": False, "reconcile_permitted": False,
        "auto_release_permitted": False,
    }


def inspect_orphan_claims(db: str | Path, *, now_ms: int | None = None) -> dict:
    """Return bounded sanitized observations from one immutable SQLite snapshot."""
    if now_ms is None:
        now_ms = time.time_ns() // 1_000_000
    if type(now_ms) is not int or now_ms < 0:
        return _unknown("invalid_clock")
    path = Path(db).expanduser().resolve()
    if not path.is_file():
        return _unknown("task_store_not_found")
    conn = None
    try:
        conn = sqlite3.connect(
            "file:" + quote(path.as_posix(), safe="/:") + "?mode=ro",
            uri=True, timeout=3,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        # Do not allow an absent table/column to look like an empty queue.
        count = int(conn.execute(
            "SELECT COUNT(*) FROM platform_coordinator_claims WHERE status='ACTIVE'"
        ).fetchone()[0])
        if count > 500:
            return _unknown("claim_count_limit_exceeded")
        rows = conn.execute(
            """SELECT c.task_id, c.window_id, c.epoch, c.expires_at_ms,
                      t.status AS task_status, w.status AS window_status,
                      b.state AS reservation_state,
                      b.observed_token_units, b.observed_cost_micro_units,
                      (SELECT COUNT(*) FROM durable_external_operations e
                       WHERE e.task_id = c.task_id) AS external_operations
               FROM platform_coordinator_claims c
               LEFT JOIN tasks t ON t.id = c.task_id
               LEFT JOIN platform_autonomous_windows w ON w.id = c.window_id
               LEFT JOIN platform_budget_reservations b
                 ON b.task_id = c.task_id AND b.window_id = c.window_id
                 AND b.claim_epoch = c.epoch
               WHERE c.status='ACTIVE' ORDER BY c.task_id"""
        ).fetchall()
        observations = []
        for row in rows:
            if (not row["task_id"] or not row["window_id"]
                    or type(row["epoch"]) is not int
                    or type(row["expires_at_ms"]) is not int
                    or row["task_status"] is None or row["window_status"] is None
                    or row["reservation_state"] != "ACTIVE"):
                reason = "INCONSISTENT_CLAIM_OR_RESERVATION"
            elif row["expires_at_ms"] > now_ms:
                reason = "LEASE_STILL_CURRENT_LIVENESS_UNKNOWN"
            elif row["external_operations"] > 0:
                reason = "EXTERNAL_OPERATION_REQUIRES_RECEIPT"
            elif row["task_status"] == "FAILED":
                reason = "TERMINAL_FAILED_REMOTE_UNVERIFIED"
            elif row["task_status"] == "INTERRUPTED":
                reason = "INTERRUPTED_REQUIRES_RECEIPT"
            else:
                reason = "SIDE_EFFECT_STATUS_UNKNOWN"
            observations.append({
                "task_id": str(row["task_id"]),
                "window_id": str(row["window_id"]),
                "claim_epoch": row["epoch"],
                "task_status": row["task_status"],
                "window_status": row["window_status"],
                "reason": reason,
                "external_operation_count": row["external_operations"],
                "usage_observed": (
                    row["observed_token_units"] is not None
                    and row["observed_cost_micro_units"] is not None
                ),
                "safe_to_release": False,
                "safe_to_dispatch": False,
            })
        return {
            "state": "HOLD_REMOTE_RECONCILIATION" if observations else "NO_ACTIVE_CLAIMS",
            "reason": "remote_terminal_receipt_not_proven" if observations else "claims_absent",
            "claims": observations,
            "dispatch_permitted": False,
            "reconcile_permitted": False,
            "auto_release_permitted": False,
        }
    except (sqlite3.Error, OSError, ValueError, TypeError):
        return _unknown("snapshot_read_failed")
    finally:
        if conn is not None:
            conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only coordinator claim diagnosis")
    parser.add_argument("--db", required=True, help="SQLite TaskStore database")
    args = parser.parse_args()
    report = inspect_orphan_claims(args.db)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 2 if report["state"] == "UNKNOWN" else 0


if __name__ == "__main__":
    raise SystemExit(main())
