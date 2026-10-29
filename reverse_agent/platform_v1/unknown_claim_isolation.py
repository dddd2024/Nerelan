"""Read-only bounded UNKNOWN claim snapshots. A digest selects data, never authority."""
import json
import re
import time
from .control_store import canonical_json, sha256_json
from .run_store import TaskStoreError


def held_task(conn, task_id):
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='platform_coordinator_claims'").fetchone() is None:
        return False
    receipts = conn.execute(
        "SELECT evidence_json FROM platform_operation_receipts "
        "WHERE operation_type='native_goal_admission' AND confirmation_mode='NATIVE_OWNER'"
    ).fetchall()
    for receipt in receipts:
        proof = json.loads(receipt["evidence_json"])
        isolation = proof.get("unknown_claim_isolation")
        if isolation and any(r["claim"]["task_id"] == task_id
                             for r in isolation["snapshot"]["claims"]):
            return True
    return conn.execute(
        "SELECT 1 FROM platform_coordinator_claims c WHERE c.task_id=? "
        "AND c.status='ACTIVE' AND c.expires_at_ms <= ? "
        "AND EXISTS (SELECT 1 FROM platform_autonomous_windows w WHERE w.id=c.window_id "
        "AND julianday(w.expires_at) <= julianday('now')) AND EXISTS (SELECT 1 FROM tasks t WHERE t.id=c.task_id "
        "AND t.status IN ('FAILED', 'INTERRUPTED')) AND NOT EXISTS (SELECT 1 FROM durable_runs r "
        "JOIN durable_external_operations o ON o.run_id=r.run_id WHERE r.task_id=c.task_id)",
        (task_id, int(time.time() * 1000))).fetchone() is not None


def refuse_held(store, task_id):
    with store._lock:
        if held_task(store._conn, task_id):
            raise TaskStoreError("unknown_claim_task_held")


def snapshot(conn):
    claims = conn.execute(
        "SELECT * FROM platform_coordinator_claims WHERE status='ACTIVE' ORDER BY task_id LIMIT 101"
    ).fetchall()
    if not 1 <= len(claims) <= 100:
        raise TaskStoreError("unknown_snapshot_unbounded_or_empty")
    records = []
    now = int(time.time() * 1000)
    for claim in claims:
        task_id = claim["task_id"]
        task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        window = conn.execute("SELECT * FROM platform_autonomous_windows WHERE id=?",
                              (claim["window_id"],)).fetchone()
        runs = conn.execute("SELECT * FROM durable_runs WHERE task_id=? ORDER BY run_id LIMIT 101",
                            (task_id,)).fetchall()
        reservations = conn.execute(
            "SELECT * FROM platform_budget_reservations WHERE task_id=? ORDER BY claim_epoch LIMIT 101",
            (task_id,)).fetchall()
        if (len(runs) > 100 or len(reservations) > 100 or not runs
                or not held_task(conn, task_id) or task is None
                or task["status"] not in {"FAILED", "INTERRUPTED"}
                or claim["expires_at_ms"] > now or window is None
                or conn.execute("SELECT julianday(?) >= julianday('now')",
                                (window["expires_at"],)).fetchone()[0] != 0
                or not reservations or not any(
                    r["state"] == "ACTIVE" and r["claim_epoch"] == claim["epoch"]
                    and r["window_id"] == claim["window_id"] for r in reservations)
                or any(r["lease_expiry_ms"] > now for r in runs)):
            raise TaskStoreError("unknown_snapshot_not_historical")
        records.append({"claim": dict(claim), "task": dict(task), "window": dict(window),
                        "runs": [dict(r) for r in runs],
                        "reservations": [dict(r) for r in reservations]})
    value = {"version": 1, "provider_terminal_state": "UNKNOWN",
            "reservation_accounting": "UNCHANGED; no release, refund or zero-cost inference",
            "automatic_retry": False, "claims": records}
    if len(canonical_json(value)) > 1_000_000:
        raise TaskStoreError("unknown_snapshot_unbounded")
    return value


def selected_snapshot(conn, digest):
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise TaskStoreError("unknown_snapshot_digest_invalid")
    value = snapshot(conn)
    if sha256_json(value) != digest:
        raise TaskStoreError("unknown_snapshot_changed")
    return {"sha256": digest, "snapshot": value}
