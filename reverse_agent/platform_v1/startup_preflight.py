"""Read-only, fail-closed reboot preflight for Nerelan's durable task host.

A newly booted process must never infer permission to resume an external model
or GPU job from a queued Task, an old RUNNING Goal, or an expired SQLite lease.
This reporter is not a Windows service installer and never dispatches work.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
from urllib.parse import quote


@dataclass(frozen=True)
class WindowState:
    id: str
    status: str
    starts_at: str
    expires_at: str


@dataclass(frozen=True)
class ClaimState:
    task_id: str
    window_id: str
    status: str


_ALLOWED_WINDOWS = frozenset({"ACTIVE", "COMPLETED", "EXPIRED", "STOPPED", "BLOCKED"})
_ALLOWED_CLAIMS = frozenset({"ACTIVE", "COMPLETE", "COMPLETED", "FAILED", "EXPIRED", "RELEASED", "INTERRUPTED", "CANCELLED"})
_ALLOWED_TASKS = frozenset({
    "QUEUED", "BLOCKED", "CANCELLED", "FAILED", "INTERRUPTED",
    "READY_FOR_REVIEW", "READY_FOR_REVIEW_FIXTURE", "PREPARING_WORKSPACE",
    "RUNNING", "RUNNING_FIXTURE", "VALIDATING",
})


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("bad_timestamp")
    value = value.replace("Z", "+00:00")
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("naive_timestamp")
    return instant.astimezone(timezone.utc)


def assess_boot_readiness(
    *, windows: list[WindowState], claims: list[ClaimState],
    task_counts: dict[str, int], now: datetime,
) -> dict[str, Any]:
    """Never grant execution authority: report only safe next verification step."""
    report = dict(
        state="UNKNOWN", reason="unverified_snapshot", dispatch_permitted=False,
        auto_extend_window=False, startup_install_permitted=False,
        active_window_id=None, active_claims=0, interrupted_tasks=0,
        queued_tasks=0, required_next_action="INSPECT",
    )
    try:
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("time_not_aware")
        current = now.astimezone(timezone.utc)
        if any(not isinstance(w, WindowState) or not w.id or w.status not in _ALLOWED_WINDOWS
               for w in windows):
            raise ValueError("unknown_window_state")
        if len({w.id for w in windows}) != len(windows):
            raise ValueError("duplicate_window_ids")
        if any(not isinstance(c, ClaimState) or not c.task_id or not c.window_id
               or c.status not in _ALLOWED_CLAIMS for c in claims):
            raise ValueError("unknown_claim_state")
        if any(k not in _ALLOWED_TASKS or type(v) is not int or v < 0
               for k, v in task_counts.items()):
            raise ValueError("unknown_task_state")
        for w in windows:
            start, end = _parse_time(w.starts_at), _parse_time(w.expires_at)
            if start >= end:
                raise ValueError("bad_window_boundary")
        active_claims = [c for c in claims if c.status == "ACTIVE"]
        active = [w for w in windows if w.status == "ACTIVE"]
        report.update(active_claims=len(active_claims),
                      interrupted_tasks=task_counts.get("INTERRUPTED", 0),
                      queued_tasks=task_counts.get("QUEUED", 0))
        if len(active) > 1:
            return report | dict(reason="multiple_active_windows",
                                 required_next_action="INSPECT_WINDOW_CONFLICT")
        if len(active) == 0:
            if active_claims:
                return report | dict(
                    state="HOLD_ORPHANED_CLAIMS", reason="claim_without_active_window",
                    required_next_action="RECONCILE_REMOTE_RECEIPTS")
            return report | dict(
                state="HOST_IDLE_NO_WINDOW", reason="no_authorized_active_window",
                required_next_action="WAIT_FOR_OWNER_WINDOW")
        w = active[0]
        report["active_window_id"] = w.id
        if not (_parse_time(w.starts_at) <= current < _parse_time(w.expires_at)):
            return report | dict(
                state="HOLD_WINDOW_TIME_MISMATCH", reason="active_status_outside_time",
                required_next_action="VERIFY_WINDOW_LIFECYCLE")
        if any(c.window_id != w.id for c in active_claims):
            return report | dict(
                state="HOLD_ORPHANED_CLAIMS", reason="claim_for_other_window",
                required_next_action="RECONCILE_REMOTE_RECEIPTS")
        if active_claims:
            return report | dict(
                state="HOLD_REMOTE_RECONCILIATION", reason="outstanding_claims_may_have_side_effects",
                required_next_action="VERIFY_REMOTE_JOB_IDENTITIES")
        if report["interrupted_tasks"] > 0:
            return report | dict(
                state="HOLD_INTERRUPTED_TASKS", reason="interrupted_tasks_need_receipt_verification",
                required_next_action="RECONCILE_DURABLE_RUNS")
        return report | dict(
            state="READY_FOR_HOST_RECONCILIATION", reason="window_current_no_claims",
            required_next_action="RUN_EXISTING_FENCED_RECONCILER")
    except (ValueError, TypeError, OverflowError):
        return report | dict(reason="invalid_or_incomplete_snapshot")


def inspect_task_store(db: str | Path, *, now: datetime | None = None) -> dict[str, Any]:
    """Read only the minimal SQLite metadata. No UPDATE/INSERT nor model calls."""
    path = Path(db).expanduser().resolve()
    if not path.is_file():
        return dict(state="UNKNOWN", reason="task_store_not_found",
                    dispatch_permitted=False, auto_extend_window=False,
                    startup_install_permitted=False)
    connection = None
    try:
        # SQLite ro mode is mandatory. Do not invoke active_window(), which
        # mutates expired window rows as a side effect.
        uri = "file:" + quote(path.as_posix(), safe="/:") + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=3)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        windows = [
            WindowState(*row) for row in connection.execute(
                "SELECT id,status,starts_at,expires_at FROM platform_autonomous_windows")]
        claims = [
            ClaimState(*row) for row in connection.execute(
                "SELECT task_id,window_id,status FROM platform_coordinator_claims")]
        counts = dict(connection.execute("SELECT status,count(*) FROM tasks GROUP BY status"))
        return assess_boot_readiness(
            windows=windows, claims=claims, task_counts=counts,
            now=now or datetime.now(timezone.utc))
    except (sqlite3.Error, OSError, ValueError):
        return dict(state="UNKNOWN", reason="snapshot_read_failed",
                    dispatch_permitted=False, auto_extend_window=False,
                    startup_install_permitted=False)
    finally:
        if connection is not None:
            connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Nerelan reboot/admission preflight")
    parser.add_argument("--db", required=True, help="Existing TaskStore SQLite file")
    args = parser.parse_args()
    result = inspect_task_store(args.db)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 2 if result["state"] == "UNKNOWN" else 0


if __name__ == "__main__":
    raise SystemExit(main())