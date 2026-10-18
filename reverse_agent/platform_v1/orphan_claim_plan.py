"""R0 orphan-claim evidence planning; deliberately has no release operation.

Local terminal Task state and dispatch bookkeeping are not remote receipts.
TERMINAL_VERIFIED is reserved for a future authoritative receipt verifier; no
current durable representation can establish that classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .control_store import PlatformControlStore


@dataclass(frozen=True)
class OrphanClaimPlan:
    task_id: str
    run_id: str
    classification: Literal["UNKNOWN", "TERMINAL_VERIFIED"]
    reason: str
    # Observed binding only, never a capability or a token for a later write.
    owner: str | None
    epoch: int | None
    window_id: str | None
    policy_binding: tuple[str, int, str] | None
    reservation_binding: tuple[str, int, str, int, int] | None
    budget_state: Literal["UNKNOWN"] = "UNKNOWN"
    release_allowed: Literal[False] = False


def plan_orphan_claim(
    control: PlatformControlStore, *, task_id: str, run_id: str, now_ms: int
) -> OrphanClaimPlan:
    """Observe one explicitly selected task/run in one SQLite read snapshot.

    No startup reconciliation, receipt ingestion, provider calls, writes, or
    authorization opening. Even a fully matching SUCCESS dispatch row remains
    UNKNOWN: its result_state is caller supplied and proves no remote outcome.
    The caller-supplied clock affects diagnostic eligibility only.
    """
    if not task_id or not run_id or type(now_ms) is not int or now_ms < 0:
        raise ValueError("explicit_task_run_and_nonnegative_clock_required")
    with control._lock:
        row = control._conn.execute(
            "SELECT t.status AS task_status, c.owner, c.epoch, c.window_id, "
            "c.status AS claim_status, c.expires_at_ms, "
            "w.policy_id, w.policy_revision, w.policy_digest, w.expires_at, "
            "r.task_id AS reserved_task, r.claim_epoch, r.window_id AS reserved_window, "
            "r.state AS reservation_state, r.reserved_token_units, r.reserved_cost_micro_units, "
            "d.run_id, d.lease_owner, d.lease_epoch, d.lease_expiry_ms, "
            "CASE WHEN julianday(w.expires_at) <= julianday(? / 1000.0, 'unixepoch') "
            "THEN 1 ELSE 0 END AS window_expired "
            "FROM tasks t LEFT JOIN platform_coordinator_claims c ON c.task_id=t.id "
            "LEFT JOIN platform_autonomous_windows w ON w.id=c.window_id "
            "LEFT JOIN platform_budget_reservations r ON r.task_id=c.task_id "
            "AND r.claim_epoch=c.epoch AND r.window_id=c.window_id "
            "LEFT JOIN durable_runs d ON d.task_id=t.id AND d.run_id=? WHERE t.id=?",
            (now_ms, run_id, task_id),
        ).fetchone()
    reason = "authoritative_terminal_receipt_format_unavailable"
    if row is None:
        reason = "task_missing"
    elif row["claim_status"] != "ACTIVE" or row["reservation_state"] != "ACTIVE":
        reason = "active_claim_reservation_pair_missing"
    elif not row["policy_digest"] or row["policy_revision"] is None:
        reason = "original_policy_binding_missing"
    elif row["task_status"] not in {"FAILED", "INTERRUPTED"}:
        reason = "task_not_terminal_candidate"
    elif row["expires_at_ms"] > now_ms or not row["window_expired"]:
        reason = "original_claim_or_window_not_expired"
    elif row["run_id"] is None:
        reason = "task_run_binding_missing"
    elif row["lease_expiry_ms"] > now_ms:
        reason = "run_lease_not_expired"
    # Run lease owner/epoch and coordinator owner/epoch are separate fences;
    # equality would not establish a trusted association between them.
    policy = None if row is None or row["policy_id"] is None else (
        row["policy_id"], row["policy_revision"], row["policy_digest"]
    )
    reservation = None if row is None or row["reserved_task"] is None else (
        row["reserved_task"], row["claim_epoch"], row["reserved_window"],
        row["reserved_token_units"], row["reserved_cost_micro_units"],
    )
    return OrphanClaimPlan(
        task_id, run_id, "UNKNOWN", reason,
        row["owner"] if row else None, row["epoch"] if row else None,
        row["window_id"] if row else None, policy, reservation,
    )
