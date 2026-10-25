"""Task-level correlation of Magpie usage and route evidence (#1342, #1170).

Provider-free parsers and correlation rules for the Magpie gateway endpoints
the adapter does not read yet: ``GET /v1/magpie/usage/requests`` (per-request
ledger rows), ``GET /v1/magpie/route?session=...`` (a session's latest routing
trace) and the request summary's totals. Field names follow the upstream
source (``internal/usage`` Record/Row, ``internal/gateway/session_route.go``);
records written before a field existed simply lack it, so every field is
optional and missing data stays UNKNOWN. Attribution requires a positive
identity match (session or request id); time-window proximity alone never
attributes a call, and Magpie-measured usage is never summed with the local
task ledger — it replaces it as the measured basis, keeping the local numbers
only as a cross-check (#1170: correlate and deduplicate, never double-count).
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

from .magpie import _decode, _private_strings, _text
from .quota_forecast import parse_time

_MAX_REQUESTS = 200
_STRING_LIMIT = 256
_TOKEN_FIELDS = {
    "input": "in", "output": "out", "cache_read": "cache_read",
    "cache_write": "cache_write", "cache_write_1h": "cache_write_1h",
    "reasoning": "reasoning",
}
_TEXT_FIELDS = (
    ("rid", "rid"), ("session", "session"), ("native_session", "native_session"),
    ("subagent", "subagent"), ("parent_agent", "parent_agent"), ("agent", "agent"),
    ("provider", "provider"), ("provider_account", "providerAccount"),
    ("provider_key_id", "providerKeyId"), ("provider_key_name", "providerKeyName"),
    ("caller_key_id", "callerKeyId"), ("caller_key_name", "callerKeyName"),
    ("model", "model"), ("requested", "req"), ("served", "served"),
    ("upstream", "upstream"), ("source", "source"), ("error", "err"),
    ("error_type", "err_type"), ("session_role", "session_role"),
)


def _count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        # json.loads accepts NaN/Infinity literals; neither is a count.
        if not math.isfinite(value):
            return None
        return int(value) if value >= 0 and value == int(value) else None
    return value if value >= 0 else None


def _flag(value: Any) -> bool:
    return value is True


def parse_usage_request(row: Any, *, page_secrets: frozenset[str] | set[str] = frozenset()) -> dict[str, Any] | None:
    """Sanitize one usage ledger row; unknown shapes return None.

    ``page_secrets`` carries private values collected from the whole ledger
    page, so a value one row marks private never survives in another row of a
    mixed-vintage page (the per-row scan alone cannot see it).
    """
    if not isinstance(row, Mapping):
        return None
    secrets = _private_strings(row) | set(page_secrets)
    record: dict[str, Any] = {}
    for name, source in _TEXT_FIELDS:
        text = _text(row.get(source), secrets)
        record[name] = text[:_STRING_LIMIT] if text else None
    for name, source in _TOKEN_FIELDS.items():
        record[name] = _count(row.get(source))
    moment = _text(row.get("t"), secrets)
    record["t"] = moment[:64] if moment else None
    record["t_epoch"] = parse_time(record["t"]) if record["t"] else None
    record["route_id"] = row.get("route_id") if _count(row.get("route_id")) is not None else None
    cost = row.get("cost")
    try:
        number = float(cost) if not isinstance(cost, bool) else None
    except (TypeError, ValueError, OverflowError):
        number = None  # a huge JSON integer literal overflows float conversion
    record["cost_usd"] = (round(number, 6)
                          if number is not None and math.isfinite(number) and number >= 0 else None)
    record["priced"] = _flag(row.get("priced"))
    for name in ("swapped", "routed", "rejected", "handed_on"):
        record[name] = _flag(row.get(name))
    record["tries"] = _count(row.get("tries"))
    return record


def parse_usage_ledger(payload: Any) -> dict[str, Any]:
    """Parse a /v1/magpie/usage/requests page; bad rows are counted, not kept."""
    data = _decode(payload)
    if not isinstance(data, Mapping):
        return {"rows": [], "total": None, "offset": None, "invalid_rows": 0}
    raw_rows = data.get("rows")
    if raw_rows is not None and not isinstance(raw_rows, list):
        return {"rows": [], "total": None, "offset": None, "invalid_rows": 1}
    # Private values are collected page-wide: any row's user/alias/from must
    # be scrubbed from every other row too, not only its own.
    page_secrets = _private_strings(data)
    rows, invalid = [], 0
    for row in raw_rows or ():
        parsed = parse_usage_request(row, page_secrets=page_secrets)
        if parsed is None:
            invalid += 1
        else:
            rows.append(parsed)
    return {"rows": rows, "total": _count(data.get("total")), "offset": _count(data.get("offset")),
            "invalid_rows": invalid}


def parse_route(payload: Any) -> dict[str, Any] | None:
    """Parse a /v1/magpie/route trace for one session."""
    data = _decode(payload)
    if not isinstance(data, Mapping):
        return None
    secrets = _private_strings(data)

    def clean(value: Any) -> str | None:
        text = _text(value, secrets)
        return text[:_STRING_LIMIT] if text else None

    def attempt(try_row: Any) -> dict[str, str | None] | None:
        if not isinstance(try_row, Mapping):
            return None
        return {"model": clean(try_row.get("model")), "effort": clean(try_row.get("effort")),
                "tier": clean(try_row.get("tier")), "tier_served": clean(try_row.get("tier_served"))}
    raw_tries = data.get("tries")
    tries = ([kept for kept in (attempt(item) for item in raw_tries) if kept is not None]
             if isinstance(raw_tries, list) else [])
    return {"asked": clean(data.get("asked")), "group": clean(data.get("group")),
            "model": clean(data.get("model")), "effort": clean(data.get("effort")),
            "tier": clean(data.get("tier")), "tier_served": clean(data.get("tier_served")),
            "served": clean(data.get("served")), "done": _flag(data.get("done")),
            "status": _count(data.get("status")), "error": clean(data.get("error")),
            "ms": _count(data.get("ms")), "tries": tries[:8]}


def _local_totals(local_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Sum the local ledger observations; any None metric keeps the sum None."""
    keys = (("input_units", "input"), ("output_units", "output"),
            ("cache_read_units", "cache_read"), ("cache_write_units", "cache_write"),
            ("reasoning_units", "reasoning"))
    sums = {name: 0 for _, name in keys}
    for observation in local_rows:
        for field, name in keys:
            value = observation.get(field)
            sums[name] = (sums[name] + value if isinstance(sums[name], int)
                          and isinstance(value, int) and not isinstance(value, bool)
                          and value >= 0 else None)
    cost = 0
    for observation in local_rows:
        value = observation.get("cost_micro_units")
        cost = (cost + value if isinstance(cost, int) and isinstance(value, int)
                and not isinstance(value, bool) and value >= 0 else None)
    return {"token_fields": sums, "cost_micro_units": cost, "observations": len(local_rows)}


def correlate_task_usage(
    local_observations: Iterable[Mapping[str, Any]],
    magpie_rows: Iterable[Mapping[str, Any]],
    *,
    sessions: Iterable[str] = (),
    rids: Iterable[str] = (),
    since: float | None = None,
    until: float | None = None,
) -> dict[str, Any]:
    """Attribute Magpie request rows to one task by positive identity only.

    A row is attributed when its session is one of ``sessions`` or its rid is
    one of ``rids``, and its timestamp falls inside the optional window.
    Rows for a rid already seen collapse to the last one; ``handed_on`` tries
    are excluded from requests and totals and only counted. When at least one
    row is attributed, Magpie becomes the measured basis and the local ledger
    numbers move to ``local_cross_check`` — the same calls must never be
    summed from both sides. Unattributed rows are counted, never guessed.
    """
    wanted_sessions = {value for value in sessions if isinstance(value, str) and value}
    wanted_rids = {value for value in rids if isinstance(value, str) and value}
    # Materialize once: a one-shot generator must not silently lose the cost
    # pass of _local_totals.
    local_rows = list(local_observations)
    by_rid: dict[str, Mapping[str, Any]] = {}
    loose: list[Mapping[str, Any]] = []
    unattributed = handed_on = duplicates = 0
    attributed: list[Mapping[str, Any]] = []
    for row in magpie_rows:
        if not isinstance(row, Mapping):
            unattributed += 1
            continue
        rid = row.get("rid")
        if row.get("handed_on") is True:
            handed_on += 1
            continue
        if isinstance(rid, str) and rid:
            if rid in by_rid:
                duplicates += 1
            by_rid[rid] = row
        else:
            loose.append(row)
    for row in (list(by_rid.values()) + loose):
        session = row.get("session")
        rid = row.get("rid")
        moment = row.get("t_epoch")
        matched = ((wanted_sessions and isinstance(session, str) and session in wanted_sessions)
                   or (wanted_rids and isinstance(rid, str) and rid in wanted_rids))
        if not matched:
            unattributed += 1
            continue
        if moment is None or (since is not None and moment < since) or (until is not None and moment > until):
            unattributed += 1
            continue
        attributed.append(row)
    totals = {name: 0 for name in _TOKEN_FIELDS}
    cost: float | None = 0.0
    unpriced = priced = 0
    accounts: dict[str, int] = {}
    served: dict[str, int] = {}
    for row in attributed:
        for name in _TOKEN_FIELDS:
            value = row.get(name)
            totals[name] = (totals[name] + value if isinstance(totals[name], int)
                            and isinstance(value, int) and value >= 0 else None)
        if row.get("priced") is True and isinstance(row.get("cost_usd"), (int, float)):
            if cost is not None:
                cost = round(cost + float(row["cost_usd"]), 6)
            priced += 1
        else:
            unpriced += 1
            cost = None
        account = row.get("provider_account") or "unknown"
        accounts[account] = accounts.get(account, 0) + 1
        model = row.get("served") or row.get("model") or "unknown"
        served[model] = served.get(model, 0) + 1
    local = _local_totals(local_rows)
    basis = "magpie_measured" if attributed else ("local_only" if local["observations"] else "unknown")
    truncated = len(attributed) > _MAX_REQUESTS
    return {
        "basis": basis,
        "requests": [dict(row) for row in attributed[:_MAX_REQUESTS]],
        "request_count": len(attributed),
        "totals": {**totals, "requests": len(attributed), "cost_usd": cost,
                   "priced_calls": priced, "unpriced_calls": unpriced},
        "local_cross_check": local if attributed else None,
        "accounts": accounts, "served_models": served,
        "sessions": sorted(wanted_sessions), "unattributed_rows": unattributed,
        "excluded_handed_on": handed_on, "duplicate_rids_collapsed": duplicates,
        "requests_truncated": truncated,
    }
