"""Task-level correlation of Magpie usage and route evidence (#1342, #1170).

Provider-free parsers, correlation rules and bounded opt-in readers for the
Magpie gateway endpoints: ``GET /v1/magpie/usage/requests`` (per-request ledger
rows) and ``GET /v1/magpie/route?session=...`` (a session's latest routing
trace). Field names follow the upstream source (``internal/usage`` Record/Row,
``internal/gateway/session_route.go``); records written before a field existed
simply lack it, so every field is optional and missing data stays UNKNOWN.
Attribution requires a positive identity match (session or request id); time-window
proximity alone never attributes a call, and Magpie-measured usage is never summed
with the local task ledger — it replaces it as the measured basis, keeping the local
numbers only as a cross-check (#1170: correlate and deduplicate, never double-count).
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request

from . import http_safe
from .magpie import MAGPIE_AUTH, _decode, _private_strings, _text, parse_hello, validate_loopback_origin
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


# Opt-in bounded reads (#1342, #1170)
#
# Nothing in normal startup calls these: fetch_magpie_snapshot still asks only for
# hello, models and quotas. Both readers reuse the accepted parsers above, go through
# http_safe so a redirect carrying the identification header is refused, send the
# fixed MAGPIE_AUTH value (never an upstream credential) and answer with sanitized
# rows plus source, version, coverage and reason. Every refusal and every exception
# collapses to a machine-readable reason, so no URL, response body or exception text
# ever reaches a result. A capped, short or unverifiable scan is reported partial --
# never zero and never complete.


SOURCE = "magpie_gateway"
HELLO_ENDPOINT = "/api/hello"
USAGE_ENDPOINT = "/v1/magpie/usage/requests"
ROUTE_ENDPOINT = "/v1/magpie/route"

MAX_BODY_BYTES = 512 * 1024
PAGE_LIMIT = 50        # upstream caps limit at 500; smaller pages stay bounded
MAX_PAGES = 10
MAX_ROWS = PAGE_LIMIT * MAX_PAGES
MAX_SESSIONS = 10
MAX_SESSION_LEN = 128

_ROUTE_FIELDS = ("asked", "group", "model", "effort", "tier", "tier_served", "served",
                 "done", "status", "error", "ms", "tries")
_ENCODED_QUERY_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._~%-")


def _bounded_session(value: Any) -> Any:
    """Return a JSON-safe bounded representation of a session id."""
    if not isinstance(value, str):
        return None
    return value[:MAX_SESSION_LEN]


def _scrub_strings(value: Any, secrets: set[str]) -> Any:
    """Recursively replace strings containing any secret with None."""
    if isinstance(value, str):
        return _text(value, secrets)
    if isinstance(value, dict):
        return {k: _scrub_strings(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_strings(v, secrets) for v in value]
    return value


class _FetchRefused(Exception):
    """Fail-closed outcome carrying only a status and a machine-readable reason."""

    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


def _usage_result(status: str, reason: str | None, source_version: str | None = None,
                  rows: Iterable[Mapping[str, Any]] = (), scanned: int = 0, invalid_rows: int = 0,
                  reported_total: int | None = None, pages_read: int = 0, reached_cap: bool = False,
                  complete: bool = False,
                  secrets: frozenset[str] | set[str] = frozenset()) -> dict[str, Any]:
    kept = [dict(row) for row in rows]
    return {"source": SOURCE, "endpoint": USAGE_ENDPOINT, "source_version": _text(source_version, secrets),
            "status": status, "reason": reason, "rows": kept, "row_count": len(kept),
            "scanned": scanned, "invalid_rows": invalid_rows, "reported_total": reported_total,
            "pages_read": pages_read, "page_limit": PAGE_LIMIT, "row_cap": MAX_ROWS,
            "reached_cap": reached_cap, "complete": complete}


def _route_result(status: str, reason: str | None, source_version: str | None,
                  sessions: list[Any], traces: list[dict[str, Any]], complete: bool,
                  secrets: frozenset[str] | set[str] = frozenset()) -> dict[str, Any]:
    safe_sessions = [_text(_bounded_session(session), secrets) for session in sessions]
    return {"source": SOURCE, "endpoint": ROUTE_ENDPOINT,
            "source_version": _text(source_version, secrets),
            "status": status, "reason": reason, "sessions": safe_sessions, "traces": traces,
            "requested": len(sessions), "returned": len(traces),
            "missing": len(sessions) - len(traces), "session_cap": MAX_SESSIONS,
            "complete": complete}


def _read_page(open_request: Any, origin: str, path: str, timeout: float) -> Any:
    """One bounded GET: the body is capped and every failure becomes a reason."""
    request = Request(origin + path, headers={"Authorization": MAGPIE_AUTH}, method="GET")
    try:
        with open_request(request, timeout=timeout) as response:
            status = response.getcode()
            if status is None or not 200 <= status < 300:
                raise _FetchRefused("unavailable", "http_error")
            body = response.read(MAX_BODY_BYTES + 1)
    except _FetchRefused:
        raise
    except HTTPError as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        if 300 <= code < 400:
            raise _FetchRefused("refused", "redirect_refused") from None
        if code == 403:
            raise _FetchRefused("refused", "forbidden") from None
        if code == 429:
            raise _FetchRefused("refused", "rate_limited") from None
        if code == 404:
            raise _FetchRefused("unavailable", "not_found") from None
        raise _FetchRefused("unavailable", "http_error") from None
    except TimeoutError:
        raise _FetchRefused("unavailable", "request_timeout") from None
    except Exception:
        raise _FetchRefused("unavailable", "request_failed") from None
    if len(body) > MAX_BODY_BYTES:
        raise _FetchRefused("unavailable", "body_too_large")
    return _decode(body)


def _validated_session(value: Any) -> str | None:
    """URL-encode one session id, or None when it is not a plain bounded id.

    The value is validated before encoding and the encoding re-checked, so a session
    id can never add a query field, terminate the query or smuggle control bytes into
    the request line.
    """
    if not isinstance(value, str) or not value or len(value) > MAX_SESSION_LEN:
        return None
    if value.strip() != value or any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in value):
        return None
    if any(ch in value for ch in ("&", "#", "?", "=", "%")):
        return None
    encoded = quote(value, safe="")
    if (not encoded or len(encoded) > MAX_SESSION_LEN * 4
            or any(ch not in _ENCODED_QUERY_CHARS for ch in encoded)):
        return None
    return encoded


def fetch_usage_requests(base_url: str = "http://127.0.0.1:3425", opener: Any = None,
                         timeout: float = 2.0) -> dict[str, Any]:
    """Opt-in bounded read of the per-request ledger; no startup path calls this.

    Pages are read in order through the documented offset/limit parameters up to
    MAX_ROWS sanitized rows. ``complete`` is True only when the ledger's own row
    count was fully read with no cap, no unparseable row, no duplicate or missing
    request identity and no changing reported total, so a capped, short or
    unverifiable scan is partial rather than zero or complete. ``reported_total`` is
    a row count, never tokens or cost: no summary endpoint is read.
    """
    if not validate_loopback_origin(base_url):
        return _usage_result("refused", "invalid_url")
    origin = base_url.rstrip("/")
    open_request = opener or http_safe.urlopen
    try:
        version = parse_hello(_read_page(open_request, origin, HELLO_ENDPOINT, timeout))
        if version is None:
            return _usage_result("not_magpie", "invalid_hello")
        rows: list[dict[str, Any]] = []
        scanned = invalid_rows = pages_read = 0
        reported_total: int | None = None
        total_key: bool | None = None
        reached_cap = False
        total_changed = False
        duplicate_rid = False
        missing_rid = False
        page_secrets: set[str] = set()
        raw_rids: list[str | None] = []
        offset = 0
        while pages_read < MAX_PAGES:
            page = _read_page(open_request, origin,
                              "%s?offset=%d&limit=%d" % (USAGE_ENDPOINT, offset, PAGE_LIMIT), timeout)
            # Private values are collected before the structural checks refuse a page,
            # so a malformed page still scrubs the evidence already read.
            page_secrets |= _private_strings(page)
            if not isinstance(page, Mapping) or not isinstance(page.get("rows"), list):
                raise _FetchRefused("unavailable", "invalid_schema")
            if len(page["rows"]) > PAGE_LIMIT:
                raise _FetchRefused("unavailable", "invalid_schema")
            pages_read += 1
            has_total = "total" in page
            total = _count(page["total"]) if has_total else None
            if has_total and total is None:
                raise _FetchRefused("unavailable", "invalid_pagination")
            if total_key is None:
                total_key, reported_total = has_total, total
            elif (has_total != total_key
                  or (has_total and reported_total is not None and total < reported_total)):
                raise _FetchRefused("unavailable", "invalid_pagination")
            elif has_total and reported_total is not None and total > reported_total:
                total_changed = True
                reported_total = total
            if "offset" in page and _count(page["offset"]) != offset:
                raise _FetchRefused("unavailable", "invalid_pagination")
            ledger = parse_usage_ledger(page)
            raw_rows = page["rows"]
            scanned += len(raw_rows)
            invalid_rows += ledger["invalid_rows"]
            for raw_row in raw_rows:
                rid = raw_row.get("rid") if isinstance(raw_row, Mapping) else None
                raw_rids.append(rid if isinstance(rid, str) and rid else None)
            if len(rows) + len(ledger["rows"]) > MAX_ROWS:
                rows.extend(ledger["rows"][: MAX_ROWS - len(rows)])
                reached_cap = True
                break
            rows.extend(ledger["rows"])
            if not raw_rows or (reported_total is not None and scanned >= reported_total):
                break
            offset += PAGE_LIMIT
        seen_rids: set[str] = set()
        for rid in raw_rids:
            if not rid:
                missing_rid = True
            elif rid in seen_rids:
                duplicate_rid = True
            else:
                seen_rids.add(rid)
        for i, row in enumerate(rows):
            rows[i] = _scrub_strings(row, page_secrets)
        if pages_read >= MAX_PAGES:
            reached_cap = True
        return _usage_result("ok", None, source_version=version, rows=rows, scanned=scanned,
                              invalid_rows=invalid_rows, reported_total=reported_total,
                              pages_read=pages_read, reached_cap=reached_cap, secrets=page_secrets,
                              complete=(reported_total is not None and not reached_cap
                                        and scanned == reported_total and invalid_rows == 0
                                        and not duplicate_rid and not missing_rid and not total_changed))
    except _FetchRefused as exc:
        return _usage_result(exc.status, exc.reason)
    except Exception:
        return _usage_result("unavailable", "request_failed")


def fetch_session_routes(sessions: Iterable[Any], base_url: str = "http://127.0.0.1:3425",
                         opener: Any = None, timeout: float = 2.0) -> dict[str, Any]:
    """Opt-in bounded read of one route trace per validated session id.

    Session ids are validated then URL-encoded: never concatenated into a query
    string or a shell. Each trace comes back through parse_route, so an unrelated or
    empty payload fails closed instead of reading as an empty trace. Coverage is
    complete only when every requested session returned a parsed trace with actual
    route evidence. Private values are collected across all payloads, then every
    returned session and trace string is scrubbed against the union.
    """
    provided: list[Any] = []
    for session in sessions:
        provided.append(session)
        if len(provided) > MAX_SESSIONS:
            break
    if not provided:
        return _route_result("refused", "invalid_session", None, provided, [], False)
    if len(provided) > MAX_SESSIONS:
        return _route_result("refused", "too_many_sessions", None, provided, [], False)
    encoded = [_validated_session(session) for session in provided]
    if any(value is None for value in encoded):
        return _route_result("refused", "invalid_session", None, provided, [], False)
    if not validate_loopback_origin(base_url):
        return _route_result("refused", "invalid_url", None, provided, [], False)
    origin = base_url.rstrip("/")
    open_request = opener or http_safe.urlopen
    version: str | None = None
    traces: list[dict[str, Any]] = []
    page_secrets: set[str] = set()
    try:
        version = parse_hello(_read_page(open_request, origin, HELLO_ENDPOINT, timeout))
        if version is None:
            return _route_result("not_magpie", "invalid_hello", None, provided, traces, False)
        for session, query in zip(provided, encoded):
            page = _read_page(open_request, origin,
                              "%s?session=%s" % (ROUTE_ENDPOINT, query), timeout)
            # Private values are collected before the structural checks refuse a page,
            # so a malformed page still scrubs the traces already read.
            page_secrets |= _private_strings(page)
            if not isinstance(page, Mapping) or not any(key in page for key in _ROUTE_FIELDS):
                raise _FetchRefused("unavailable", "invalid_schema")
            trace = parse_route(page)
            if trace is None or trace.get("model") is None:
                raise _FetchRefused("unavailable", "invalid_schema")
            traces.append({"session": session, "trace": trace})
        for i, entry in enumerate(traces):
            traces[i] = {"session": _text(entry["session"], page_secrets),
                         "trace": _scrub_strings(entry["trace"], page_secrets)}
        return _route_result("ok", None, version, provided, traces, True, page_secrets)
    except _FetchRefused as exc:
        for i, entry in enumerate(traces):
            traces[i] = {"session": _text(entry["session"], page_secrets),
                         "trace": _scrub_strings(entry["trace"], page_secrets)}
        return _route_result(exc.status, exc.reason, version, provided, traces, False, page_secrets)
    except Exception:
        for i, entry in enumerate(traces):
            traces[i] = {"session": _text(entry["session"], page_secrets),
                         "trace": _scrub_strings(entry["trace"], page_secrets)}
        return _route_result("unavailable", "request_failed", version, provided, traces, False, page_secrets)
