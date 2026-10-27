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

The residual only reconciles the money estimate with the account delta when a
conversion between the two units is explicitly evidenced for this account and
window *and* carries a usable provenance reference and observation time.
Because the money input stays ESTIMATED, the derived residual stays ESTIMATED
too: the arithmetic fixes the unit but never promotes the estimate's
uncertainty into an observed provider debit. Without that evidence the
residual stays unknown while both observations are retained untouched — one
credit per dollar is never assumed by default. The function is pure: identical
inputs produce an identical record
(the inputs digest covers endpoints, tasks, reservation evidence and
conversion inputs, so persisted records are idempotent), so a later run with
complete late evidence supersedes — never erases — an earlier UNKNOWN record;
releasing historical holds stays the caller's decision.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable, Mapping

from .quota_forecast import parse_time

_PROVIDER_SOURCES = frozenset({"magpie", "official", "cli", "claude_rate_limit_event"})
_MAX_TASKS = 64
_TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "cache_write_1h", "reasoning")


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else None


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _observed_at(snapshot: Mapping[str, Any]) -> Any:
    return parse_time(_text(snapshot.get("observed_at")) or "")


def _as_time(value: Any) -> float | None:
    """Parse an endpoint or reset timestamp from an ISO string or epoch number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return parse_time(_text(value) or "")
    number = float(value)
    return number if math.isfinite(number) else None


def _materialized_reservations(other_reservations: Iterable[Any]) -> list[dict[str, str | None]]:
    """Normalize the reservation evidence the overlap guard decides on.

    Only the fields the guard reads survive, and rows are sorted, so the same
    reservation set always materializes identically whatever order a caller
    supplies it in. The result is part of the inputs digest: two decisions over
    the same endpoints and tasks with different sibling reservations must not
    share one reconciliation identity.
    """
    rows: list[dict[str, str | None]] = []
    for reservation in other_reservations or ():
        if not isinstance(reservation, Mapping):
            continue
        rows.append({"account_ref": _text(reservation.get("account_ref")),
                     "created_at": _text(reservation.get("created_at")),
                     "reconciled_at": _text(reservation.get("reconciled_at"))})
    rows.sort(key=lambda row: (row["account_ref"] or "", row["created_at"] or "",
                               row["reconciled_at"] or ""))
    return rows


def _digest(before: Mapping[str, Any], after: Mapping[str, Any],
            tasks: Iterable[Mapping[str, Any]], unattributed_request_rows: int,
            other_reservations: Iterable[Any] = (),
            credit_conversion: Mapping[str, Any] | None = None) -> str:
    payload = json.dumps({"before": dict(before), "after": dict(after),
                          # Order-independent: the identity covers a task set, not
                          # the sequence a caller happened to hand over.
                          "tasks": sorted((dict(task) for task in tasks),
                                          key=lambda task: json.dumps(task, sort_keys=True,
                                                                      default=str)),
                          "unattributed_request_rows": unattributed_request_rows,
                          "other_reservations": _materialized_reservations(other_reservations),
                          "credit_conversion": (dict(credit_conversion)
                                                if isinstance(credit_conversion, Mapping) else {})},
                         sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _refused(reason: str, before: Mapping[str, Any], after: Mapping[str, Any],
             unattributed_request_rows: int, tasks: Iterable[Mapping[str, Any]] = (),
             other_reservations: Iterable[Any] = (),
             credit_conversion: Mapping[str, Any] | None = None) -> dict[str, Any]:
    task_list = [dict(task) for task in tasks if isinstance(task, Mapping)]
    return {"status": "REFUSED", "reason": reason, "account_ref": after.get("account_ref"),
            "interval": {"start": before.get("observed_at"), "end": after.get("observed_at"),
                         "window": _text(after.get("window"))},
            "account_delta_credits": None, "tasks": [], "unattributed_tasks": [],
            "unattributed_residual_credits": None,
            "dimensions": {"account_balance_credits": None, "task_token_usage": None,
                           "estimated_money": None},
            # The digest covers tasks, reservation evidence and conversion
            # inputs, so two refusals of the same interval with different
            # decision-driving evidence never share one identity.
            "inputs_digest": _digest(before, after, task_list, unattributed_request_rows,
                                     other_reservations, credit_conversion)}


def _conversion_rate(conversion: Mapping[str, Any], account: str | None, window: str | None) -> float | None:
    """Return an evidenced credits-per-USD rate, or None when there is none.

    A conversion counts only when it is explicitly marked evidenced, carries a
    finite positive rate, names this interval's account and window, and retains
    a nonempty provenance reference plus a parseable observation time. Without
    that metadata there is no durable source or moment the rate can be
    attributed to, so it cannot complete a reconciliation. No rate is ever
    invented or defaulted to one credit per dollar.
    """
    if not isinstance(conversion, Mapping) or conversion.get("evidenced") is not True:
        return None
    if conversion.get("account_ref") != account or conversion.get("window") != window:
        return None
    rate = _number(conversion.get("credits_per_usd"))
    if rate is None or rate <= 0:
        return None
    if _text(conversion.get("provenance")) is None:
        return None
    if _observed_at(conversion) is None:
        return None
    return float(rate)


def reconcile_account_interval(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    task_usages: Iterable[Mapping[str, Any]] = (),
    other_reservations: Iterable[Mapping[str, Any]] = (),
    unattributed_request_rows: int = 0,
    credit_conversion: Mapping[str, Any] | None = None,
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
    could claim. ``credit_conversion`` is optional evidence converting an
    estimated money amount into the account's credit unit: ``evidenced`` must
    be True, ``credits_per_usd`` a positive finite number, ``account_ref`` and
    ``window`` this interval's identity, plus a nonempty ``provenance`` and a
    parseable ``observed_at``. Without all of it the conversion cannot complete
    the reconciliation and the residual stays unknown. When it does apply, the
    residual keeps its numeric value (positive unattributed credits or a
    negative over-coverage signal) but stays ESTIMATED with the conversion's
    provenance retained — the arithmetic fixes the unit, it never promotes the
    money estimate into an observed provider debit. A known reset boundary at
    either endpoint or strictly inside the interval, percentage-only readings,
    recharges, overlaps, missing identities and unattributable request rows
    refuse the settlement instead of guessing.
    """
    # Materialize the sibling-reservation evidence exactly once so the overlap
    # guard and every refusal/success digest share the same frozen rows. A
    # generator is single-pass, so a second iteration in the digest would hash
    # empty reservation evidence and make the reconciliation identity depend on
    # the container type (list vs generator) rather than the evidence itself.
    other_reservations = _materialized_reservations(other_reservations)
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return _refused("invalid_snapshot", {}, {}, 0, (), other_reservations, credit_conversion)
    tasks = [dict(task) for task in task_usages if isinstance(task, Mapping)]
    if len(tasks) > _MAX_TASKS:
        return _refused("too_many_tasks", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    start, end = _observed_at(before), _observed_at(after)
    account = _text(after.get("account_ref"))
    if not account or before.get("account_ref") != account:
        return _refused("account_mismatch", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    if (_text(before.get("source")) not in _PROVIDER_SOURCES
            or _text(after.get("source")) not in _PROVIDER_SOURCES):
        return _refused("non_provider_reading", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    window = _text(after.get("window"))
    if _text(before.get("window")) != window or window is None:
        return _refused("window_identity_changed", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    if start is None or end is None or start >= end:
        return _refused("invalid_interval", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    # Item 2: absolute counters only. A rounded percentage delta of zero is not
    # proof of zero use, so a percentage-only interval can never settle a task.
    prior, latest = _number(before.get("credits_remaining")), _number(after.get("credits_remaining"))
    if prior is None or latest is None:
        return _refused("percentage_only_quantized", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    # Item 2: a known reset boundary inside the interval voids the verified
    # exclusive precondition even when both readings carry the same stale reset
    # string — a reset can be followed by use that leaves the ending balance
    # below the starting one, so the credit-increase guard alone never proves
    # reset-free consumption. The same holds when the boundary lies exactly at
    # either endpoint: a reading taken at a known reset cannot establish that
    # its balance precedes that reset (it can include a reset/top-up followed by
    # use, or retain stale reset metadata), so a reset at the after endpoint —
    # and equally at the before endpoint, where a reset immediately after that
    # first reading leaves no ordering metadata proving the first balance was
    # already post-reset — is refused too. There is no baseline guess: the whole
    # closed interval is refused, and only a reset strictly outside it survives.
    # Genuinely unknown reset metadata stays supported: nothing is inferred as a
    # reset, and no reset is refused when it is not evidenced.
    before_reset, after_reset = _as_time(before.get("resets_at")), _as_time(after.get("resets_at"))
    if before_reset != after_reset:
        return _refused("window_reset", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    if before_reset is not None and start <= before_reset <= end:
        return _refused("window_reset", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    if latest > prior:
        # Credits going up is a top-up, expiry refund or correction, not
        # negative consumption: the interval cannot attribute anything.
        return _refused("credit_increase", before, after, unattributed_request_rows, tasks,
                        other_reservations, credit_conversion)
    for reservation in other_reservations:
        if reservation.get("account_ref") != account:
            continue
        created = parse_time(reservation.get("created_at") or "")
        finished = parse_time(reservation.get("reconciled_at") or "")
        # Fail closed like delta_calibration: a same-account reservation whose
        # start cannot be placed cannot be proven non-overlapping, so it voids
        # the verified-exclusive precondition instead of being skipped.
        if created is None:
            return _refused("unplaceable_reservation", before, after, unattributed_request_rows, tasks,
                            other_reservations, credit_conversion)
        if created < end and (finished is None or finished > start):
            return _refused("overlapping_reservation", before, after, unattributed_request_rows, tasks,
                            other_reservations, credit_conversion)

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
    # Item 4: token completeness comes from the six bucket observations
    # themselves. Pricing and session identity never fabricate a token count: a
    # missing bucket stays unknown while every known counter remains usable.
    # An empty identity-bound set is absence of evidence, not an observed empty
    # execution: no identity-bound row means no task token evidence at all, so
    # every bucket stays unknown instead of being observed as a fabricated zero.
    # Explicitly supplied zero observations still count (a nonempty row set with
    # a zero bucket is an observation, never "missing").
    if rows:
        token_sums = {name: (sum(row["tokens"][name] for row in rows)
                             if all(isinstance(row["tokens"][name], (int, float)) for row in rows) else None)
                      for name in _TOKEN_FIELDS}
    else:
        token_sums = {name: None for name in _TOKEN_FIELDS}
    known_tokens = [value for value in token_sums.values() if value is not None]
    token_completeness = ("OBSERVED" if len(known_tokens) == len(_TOKEN_FIELDS)
                          else "PARTIAL" if known_tokens else "UNKNOWN")
    # Item 1: credits and estimated money are distinct dimensions. The residual
    # reconciles them only with an evidenced conversion; otherwise it stays
    # unknown and both independent observations are kept as they are.
    conversion_rate = _conversion_rate(credit_conversion or {}, account, window)
    conversion_reported = None
    if conversion_rate is not None:
        conversion_reported = {"credits_per_usd": conversion_rate,
                               "account_ref": account, "window": window,
                               "observed_at": _text((credit_conversion or {}).get("observed_at")),
                               "provenance": _text((credit_conversion or {}).get("provenance"))}
    if attributed_usd is None:
        residual: float | None = None
        residual_completeness = "UNKNOWN"
    elif conversion_rate is not None:
        # Item 1/4: the unit conversion fixes dimensions only; the money input
        # is still ESTIMATED, so the reconciled residual stays ESTIMATED with
        # the conversion's provenance retained. The numeric value keeps its
        # sign (positive unattributed credits or a negative over-coverage
        # signal) and the account delta/token dimensions stay independently
        # observed. Nothing here turns an estimate into a provider debit.
        residual = round(delta - attributed_usd * conversion_rate, 6)
        residual_completeness = "ESTIMATED"
    else:
        # No evidenced conversion: the residual stays unknown. This holds for an
        # estimated money total of zero too — a zero is an estimate (a positive
        # raw amount can round to it), never verified zero task-credit
        # consumption, so the whole delta is not promoted to an OBSERVED
        # unattributed residual just because the money rounded to 0.0. The
        # supplied zero token counters and the account delta stay observed; only
        # the certainty of the credit residual is unknown, and a later evidenced
        # conversion still completes the unit arithmetic (ESTIMATED).
        residual = None
        residual_completeness = "UNKNOWN"
    complete = (bool(identity_bound) and not aggregate_only and all_priced
                and not unattributed_request_rows
                and token_completeness == "OBSERVED"
                and residual_completeness == "OBSERVED")
    if complete:
        reason = None
    elif aggregate_only:
        reason = "aggregate_only_usage_present"
    elif not identity_bound:
        reason = "no_identity_bound_task"
    elif not all_priced:
        reason = "unpriced_task_requests"
    elif unattributed_request_rows:
        reason = "unattributed_request_rows_present"
    elif token_completeness != "OBSERVED":
        reason = "incomplete_token_fields"
    elif conversion_rate is not None:
        # A valid conversion reconciled the estimate, but the residual is only
        # ESTIMATED (the money input is an estimate), so the interval is a
        # partial accounting fact, never an observed provider debit.
        reason = "estimated_credit_reconciliation"
    else:
        reason = "unknown_credit_conversion"
    return {
        "status": "OBSERVED" if complete else "PARTIAL",
        "reason": reason,
        "account_ref": account,
        "interval": {"start": before.get("observed_at"), "end": after.get("observed_at"),
                     "window": window},
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
                                 "completeness": token_completeness},
            "estimated_money": {"estimated_usd": attributed_usd, "all_priced": all_priced,
                                "completeness": "ESTIMATED" if attributed_usd is not None else "UNKNOWN"},
            "credit_reconciliation": {"residual_credits": residual,
                                      "conversion": conversion_reported,
                                      "completeness": residual_completeness},
        },
        "inputs_digest": _digest(before, after, tasks, unattributed_request_rows,
                                 other_reservations, credit_conversion),
    }
