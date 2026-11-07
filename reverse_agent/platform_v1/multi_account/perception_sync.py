"""Turn a live Magpie snapshot into quota observation rows.

Quota observations are persisted only as a side effect of task admission, so
until the first dispatch the store is empty and multi-account perception sees
no accounts even when Magpie reports them. This module converts a
:func:`reverse_agent.model_access.magpie.fetch_magpie_snapshot` result into the
``(account_ref, observed_at, evidence)`` rows the control store can persist.

Only the keys in :data:`EVIDENCE_KEYS` are kept. Personal data is removed
upstream; the allow-list is a second line of defence so that a field such as
``user`` or ``email`` cannot reach the store through this path.

Nothing here raises on malformed input: a bad snapshot yields no rows, and a
failed write is counted and reported by exception type only, so no message or
traceback (which may carry paths) enters the summary.
"""
from __future__ import annotations

import copy
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

EVIDENCE_KEYS = ("provider", "kind", "plan", "account_ref", "windows",
                 "cached_windows", "state", "reason", "observed_at",
                 "provenance", "source_version")

_UNKNOWN_STATE = "UNKNOWN"


def _iso_utc(epoch: float) -> str:
    """Format an epoch second as ISO-8601 UTC with a trailing ``Z``."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_for(account: Any, now: float | None) -> dict[str, Any] | None:
    """Build one observation row, or ``None`` when the entry has no usable account_ref."""
    if not isinstance(account, Mapping):
        return None
    account_ref = account.get("account_ref")
    if not isinstance(account_ref, str) or not account_ref:
        return None

    evidence = {key: copy.deepcopy(account[key]) for key in EVIDENCE_KEYS if key in account}

    observed_at = account.get("observed_at")
    if not isinstance(observed_at, str) or not observed_at:
        observed_at = _iso_utc(time.time() if now is None else now)

    state = account.get("state")
    if not isinstance(state, str):
        state = _UNKNOWN_STATE

    reason = account.get("reason")
    return {
        "account_ref": account_ref,
        "observed_at": observed_at,
        "evidence": evidence,
        "state": state,
        "reason": reason if isinstance(reason, str) else None,
    }


def _collect(snapshot: Mapping[str, Any], now: float | None) -> tuple[list[dict[str, Any]], int]:
    """Return ``(rows sorted by account_ref, skipped count)`` for a snapshot."""
    if not isinstance(snapshot, Mapping):
        return [], 0
    accounts = snapshot.get("accounts")
    if not isinstance(accounts, list):
        return [], 0

    rows: list[dict[str, Any]] = []
    skipped = 0
    for account in accounts:
        row = _row_for(account, now)
        if row is None:
            skipped += 1
        else:
            rows.append(row)
    rows.sort(key=lambda row: row["account_ref"])
    return rows, skipped


def observations_from_snapshot(snapshot: Mapping[str, Any], *, now: float | None = None,
                               max_age_seconds: float = 900.0) -> list[dict[str, Any]]:
    """Return one observation row per account with a usable ``account_ref``.

    Rows are sorted by ``account_ref``. ``observed_at`` falls back to ISO-8601 UTC
    derived from ``now`` (default ``time.time()``) when the account has none.
    ``max_age_seconds`` is accepted for the caller's summary only and never drops rows.
    """
    rows, _ = _collect(snapshot, now)
    return rows


def _order_key(stamp: str) -> tuple[int, float, str]:
    """Order timestamps chronologically; unparseable strings sort after parseable ones."""
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return (1, 0.0, stamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (0, parsed.timestamp(), stamp)


def _extreme(stamps: list[str], pick: Callable[..., str]) -> str | None:
    """Return the min or max of ``stamps`` by chronological order, or ``None`` when empty."""
    if not stamps:
        return None
    return pick(stamps, key=_order_key)


def sync_snapshot(snapshot: Mapping[str, Any], *,
                  write: Callable[[str, str, str], None],
                  now: float | None = None,
                  max_age_seconds: float = 900.0) -> dict[str, Any]:
    """Write every observation row of a snapshot through ``write`` and summarise the result.

    ``write`` receives ``(account_ref, observed_at, evidence_json)``. A write that
    raises is counted in ``failed`` and the loop continues; only the exception's
    type name is recorded. ``skipped`` counts entries without a usable account_ref.
    """
    rows, skipped = _collect(snapshot, now)

    written = 0
    failed = 0
    failures: list[str] = []
    states: dict[str, int] = {}
    for row in rows:
        states[row["state"]] = states.get(row["state"], 0) + 1
        try:
            write(row["account_ref"], row["observed_at"],
                  json.dumps(row["evidence"], sort_keys=True, ensure_ascii=False))
        except Exception as exc:
            failed += 1
            failures.append(type(exc).__name__)
        else:
            written += 1

    stamps = [row["observed_at"] for row in rows]
    return {
        "written": written,
        "failed": failed,
        "skipped": skipped,
        "states": dict(sorted(states.items())),
        "oldest_observed_at": _extreme(stamps, min),
        "newest_observed_at": _extreme(stamps, max),
        "failures": failures,
    }
