"""Account-interval credit-delta settlement for task consumption (#1342).

Implements the Owner accounting contract (issue #1342, comment 6379371024,
items 1-6) as a provider-free read model over absolute observations. The
dimensions stay separate end to end: an account's observed remaining credit is
a balance, a task's deduplicated request tokens are usage, and a Magpie
``cost`` figure is an estimated equivalent amount of money — none of them is
an observed provider debit by itself, and none is ever backfilled from the
others.

Settlement of a task's credit consumption from an interval is allowed only
when the interval is *verified exclusive*: both endpoints are fresh absolute
credit readings of the same account and window identity, the window neither
reset nor recharged (a credit increase is a top-up or refund, not negative
use), no other reservation overlapped the account inside the interval, and the
readings are not percentage-only — a zero rounded difference is not proof of
zero use. Shared-account tasks are attributed only through positive identity
(task/execution bound to session/request ids from
:mod:`reverse_agent.model_access.magpie_usage`); proximity in time never
attributes. Whatever the identity-bound sums do not cover stays an
unattributed residual — it is never forced into a task, split by task count,
or inferred from token counts, and a shared aggregate stays account-level.

The reconciliation subtracts the identity-bound tasks' estimated request cost
from the absolute credit delta; the residual is reported, never allocated. The
function is pure: identical inputs produce an identical record (the inputs
digest makes persisted records idempotent), so a later run with complete late
evidence supersedes — never erases — an earlier UNKNOWN record; releasing
historical holds stays the caller's decision.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable, Mapping

from .quota_forecast import parse_time

_PROVIDER_SOURCES = frozenset({"magpie", "official", "cli", "claude_rate_limit_event"})
_MAX_TASKS = 64
_TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _observed_at(snapshot: Mapping[str, Any]) -> Any:
    return parse_time(_text(snapshot.get("observed_at")) or "")


def _digest(before: Mapping[str, Any], after: Mapping[str, Any],
            tasks: Iterable[Mapping[str, Any]], unattributed_request_rows: int) -> str:
    payload = json.dumps({"before": dict(before), "after": dict(after),
                          "tasks": [dict(task) for task in tasks],
                          "unattributed_request_rows": unattributed_request_rows},
                         sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _refused(reason: str, before: Mapping[str, Any], after: Mapping[str, Any],
             unattributed_request_rows: int) -> dict[str, Any]:
    return {"status": "REFUSED", "reason": reason, "account_ref": after.get("account_ref"),
            "interval": {"start": before.get("observed_at"), "end": after.get("observed_at"),
                         "window": _text(after.get("window"))},
            "account_delta_credits": None, "tasks": [], "unattributed_tasks": [],
            "unattributed_residual_credits": None,
            "dimensions": {"account_balance_credits": None, "task_token_usage": None,
                           "estimated_money": None},
            "inputs_digest": _digest(before, after, (), unattributed_request_rows)}


def reconcile_account_interval(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    task_usages: Iterable[Mapping[str, Any]] = (),
    other_reservations: Iterable[Mapping[str, Any]] = (),
    unattributed_request_rows: int = 0,
) -> dict[str, Any]:
    """Settle one account interval against identity-bound per-task sums.

    ``before``/``after`` are account credit snapshots: ``account_ref``,
    ``source`` (a provider reading), ``observed_at``, the ``window`` name,
    ``credits_remaining`` as an absolute number and the ``resets_at`` the
    window carried. ``task_usages`` rows come from ``correlate_task_usage``:
    ``task_id``, ``account_ref``, ``coverage`` (``identity_bound`` or
    ``aggregate_only``), deduplicated ``requests``, ``tokens`` totals and the
    estimated ``cost_usd`` with its ``priced`` flag. ``other_reservations``
    are the account's settlement rows, used only to detect overlap;
    ``unattributed_request_rows`` is the correlation's count of rows no task
    could claim. Percentage-only readings, resets, recharges, overlaps,
    missing identities and unattributable request rows refuse the settlement
    instead of guessing.
    """
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return _refused("invalid_snapshot", {}, {}, 0)
    tasks = [dict(task) for task in task_usages if isinstance(task, Mapping)]
    if len(tasks) > _MAX_TASKS:
        return _refused("too_many_tasks", before, after, unattributed_request_rows)
    start, end = _observed_at(before), _observed_at(after)
    account = _text(after.get("account_ref"))
    if not account or before.get("account_ref") != account:
        return _refused("account_mismatch", before, after, unattributed_request_rows)
    if (_text(before.get("source")) not in _PROVIDER_SOURCES
            or _text(after.get("source")) not in _PROVIDER_SOURCES):
        return _refused("non_provider_reading", before, after, unattributed_request_rows)
    if _text(before.get("window")) != _text(after.get("window")) or _text(after.get("window")) is None:
        return _refused("window_identity_changed", before, after, unattributed_request_rows)
    if start is None or end is None or start >= end:
        return _refused("invalid_interval", before, after, unattributed_request_rows)
    # Item 2: absolute counters only. A rounded percentage delta of zero is not
    # proof of zero use, so a percentage-only interval can never settle a task.
    prior, latest = _number(before.get("credits_remaining")), _number(after.get("credits_remaining"))
    if prior is None or latest is None:
        return _refused("percentage_only_quantized", before, after, unattributed_request_rows)
    if before.get("resets_at") != after.get("resets_at"):
        return _refused("window_reset", before, after, unattributed_request_rows)
    if latest > prior:
        # Credits going up is a top-up, expiry refund or correction, not
        # negative consumption: the interval cannot attribute anything.
        return _refused("credit_increase", before, after, unattributed_request_rows)
    for reservation in other_reservations:
        if not isinstance(reservation, Mapping) or reservation.get("account_ref") != account:
            continue
        created = parse_time(_text(reservation.get("created_at")) or "")
        finished = parse_time(_text(reservation.get("reconciled_at")) or "")
        if created is not None and created < end and (finished is None or finished > start):
            return _refused("overlapping_reservation", before, after, unattributed_request_rows)

    delta = round(prior - latest, 6)
    mine = [task for task in tasks if task.get("account_ref") == account]
    foreign = len(tasks) - len(mine)
    identity_bound = [task for task in mine if task.get("coverage") == "identity_bound"]
    aggregate_only = [task for task in mine if task.get("coverage") != "identity_bound"]
    attributed_usd: float | None = 0.0 if identity_bound else None
    all_priced = True
    rows = []
    for task in identity_bound:
        tokens = task.get("tokens") if isinstance(task.get("tokens"), Mapping) else {}
        cost = _number(task.get("cost_usd"))
        if task.get("priced") is True and cost is not None:
            attributed_usd = None if attributed_usd is None else round(attributed_usd + cost, 6)
        else:
            all_priced = False
            attributed_usd = None
        rows.append({"task_id": _text(task.get("task_id")), "coverage": "identity_bound",
                     "requests": _number(task.get("requests")),
                     "tokens": {name: _number(tokens.get(name)) for name in _TOKEN_FIELDS},
                     "estimated_cost_usd": cost if task.get("priced") is True else None})
    complete = (bool(identity_bound) and not aggregate_only and all_priced
                and not unattributed_request_rows)
    residual = (None if attributed_usd is None else round(delta - attributed_usd, 6))
    token_sums = {name: (sum(row["tokens"][name] for row in rows)
                         if all(isinstance(row["tokens"][name], (int, float)) for row in rows) else None)
                  for name in _TOKEN_FIELDS}
    return {
        "status": "OBSERVED" if complete else "PARTIAL",
        "reason": (None if complete else
                   ("aggregate_only_usage_present" if aggregate_only else
                    ("no_identity_bound_task" if not identity_bound else
                     ("unpriced_task_requests" if not all_priced else
                      "unattributed_request_rows_present")))),
        "account_ref": account,
        "interval": {"start": before.get("observed_at"), "end": after.get("observed_at"),
                     "window": _text(after.get("window"))},
        "account_delta_credits": delta,
        "tasks": rows,
        "unattributed_tasks": [_text(task.get("task_id")) for task in aggregate_only],
        "other_account_tasks": foreign,
        "unattributed_residual_credits": residual,
        # Item 5: a shared aggregate stays account-level observed usage; no
        # allocation is inferred here under any weighting rule.
        "dimensions": {
            "account_balance_credits": {
                "credits_remaining_before": prior, "credits_remaining_after": latest,
                "source": _text(after.get("source")), "completeness": "OBSERVED"},
            "task_token_usage": {"tokens": token_sums,
                                 "completeness": "OBSERVED" if complete else "PARTIAL"},
            "estimated_money": {"estimated_usd": attributed_usd, "all_priced": all_priced,
                                "completeness": "ESTIMATED"},
        },
        "inputs_digest": _digest(before, after, tasks, unattributed_request_rows),
    }
