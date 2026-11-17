"""The binding pool a Goal in an Owner window may run on (Owner decision 2026-11-17, #1667).

A window with an expiry keeps the pool the Owner was shown at admission: the
``approved_pool`` of the Goal's admission receipt, unchanged. A continuous window
(#1538) runs until the Owner stops it, so it outlives account and model changes; its
Goals use the *live* pool instead: the bindings enabled now, resolved by the same
rules admission uses (:func:`owner_window.resolve_pool`), minus Owner ``exclude``s.
The admission receipt stays as audit evidence of what was confirmed then.

The trusted host attaches the live pool to the task store as ``live_window_pool``,
the way it attaches ``routing_groups``. Without it (a store with no host), a
continuous window falls back to its admission pool, which can only narrow.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

POOL_SOURCE_LIVE = "live"
POOL_SOURCE_ADMISSION = "admission"


def eligible_pool(task_store: Any, admission_pool: Any, *, continuous: bool) -> tuple[Any, str]:
    """(pool entries, ``live``|``admission``) for a Goal of an Owner window.

    ``admission_pool`` is returned as is for a window with an expiry, so every
    existing check on it behaves exactly as before.
    """
    if continuous:
        provider = getattr(task_store, "live_window_pool", None)
        if callable(provider):
            return list(provider()), POOL_SOURCE_LIVE
    return admission_pool, POOL_SOURCE_ADMISSION


def goal_window_pool(task_store: Any, goal_id: str, window_id: str) -> dict[str, Any] | None:
    """The eligible pool for ``goal_id`` in ``window_id``; None when it is not an Owner window.

    Reads the window and the Goal's admission receipt under the store lock and the
    live pool after releasing it. Raises ``ValueError`` when the receipt is missing,
    ambiguous or malformed: the caller decides whether that refuses or skips.
    """
    import json
    from .control_store import OWNER_WINDOW_MODE, OWNER_WINDOW_RECEIPT
    if not window_id:
        return None
    with task_store._lock:
        window = task_store._conn.execute(
            "SELECT confirmation_mode, expires_at FROM platform_autonomous_windows WHERE id = ?",
            (window_id,)).fetchone()
        if window is None or window["confirmation_mode"] != OWNER_WINDOW_MODE:
            return None
        rows = task_store._conn.execute(
            "SELECT evidence_json FROM platform_operation_receipts WHERE subject_id = ? AND window_id = ? "
            "AND operation_type = ? AND decision = 'allowed' AND confirmation_mode = ?",
            (goal_id, window_id, OWNER_WINDOW_RECEIPT, OWNER_WINDOW_MODE)).fetchall()
    if len(rows) != 1:
        raise ValueError("missing_or_ambiguous_receipt")
    try:
        admission = json.loads(rows[0]["evidence_json"])["approved_pool"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("invalid_receipt") from exc
    if not isinstance(admission, list):
        raise ValueError("invalid_receipt")
    pool, source = eligible_pool(task_store, admission, continuous=window["expires_at"] == "")
    return {"pool": pool, "pool_source": source}


def pool_refs(pool: Sequence[Mapping[str, Any]]) -> set[str]:
    return {str(entry.get("binding_ref", "")) for entry in pool if isinstance(entry, Mapping)}
