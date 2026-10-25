"""Provider-free checks for the opt-in bounded Magpie usage/route readers.

Every transport is an injected fake with the http_safe.urlopen contract, so no
gateway, provider, network, shell or environment secret is ever touched. The
checks pin the fail-closed contract: sanitized rows plus source, version,
coverage and reason, with truncation, missing rows and malformed responses
reported partial rather than zero or complete.
"""

from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from reverse_agent.model_access.magpie import fetch_magpie_snapshot
from reverse_agent.model_access.magpie_usage import (
    MAX_BODY_BYTES, MAX_PAGES, MAX_ROWS, MAX_SESSIONS, MAX_SESSION_LEN, PAGE_LIMIT,
    ROUTE_ENDPOINT, USAGE_ENDPOINT, correlate_task_usage,
    fetch_session_routes, fetch_usage_requests,
)

T = "2026-10-25T10:00:00Z"
PRIVATE = ("person@example.test", "private-alias", "private-origin")
HELLO = {"name": "magpie", "version": "0.1.1250"}
TRACE = {"asked": "route-main", "group": "grp-1", "model": "claude-fable-5-1",
         "tier": "priority", "tier_served": "default", "served": "claude-fable-5-1",
         "done": True, "status": 200, "ms": 900,
         "tries": [{"model": "gpt-6.1-sol", "tier": "priority"}]}


class Response(BytesIO):
    def __init__(self, payload, code=200):
        super().__init__(payload)
        self._code = code

    def getcode(self):
        return self._code


def body(payload, code=200):
    return Response(json.dumps(payload).encode(), code)


def raw(data):
    return Response(data)


def error(code, note="denied"):
    return HTTPError("http://127.0.0.1:3425/probe", code, note, {}, None)


def run(responses):
    """Injectable opener: replays exceptions as-is and records every request."""
    calls = []

    def open_request(request, timeout):
        calls.append(request)
        assert timeout == 2.0
        assert request.get_header("Authorization") == "Bearer magpie-nerelan"
        assert request.get_method() == "GET"
        item = responses[min(len(calls) - 1, len(responses) - 1)]
        if isinstance(item, BaseException):
            raise item
        return item

    return open_request, calls


def urls(calls):
    return [request.full_url for request in calls]


def row(rid="r1", session="sess-task-1", **extra):
    base = {"rid": rid, "route_id": 7, "t": T, "agent": "opencode", "provider": "anthropic",
            "providerAccount": "acct-a@example.test", "providerKeyId": "key-fp-1",
            "model": "claude-fable-5-1", "req": "route-main", "served": "claude-fable-5-1",
            "session": session, "in": 100, "out": 10, "cache_read": 0, "cost": 0.001,
            "priced": True, "ms": 50}
    base.update(extra)
    return base


def ledger(rows, total, offset=0):
    payload = {"rows": list(rows)}
    if total is not None:
        payload["total"] = total
    if offset is not None:
        payload["offset"] = offset
    return payload


def ledger_of(n, start, total, offset=None):
    """A page whose echoed offset matches the offset it was requested at."""
    return ledger([row(rid="r%d" % (start + i)) for i in range(n)], total,
                  offset=start if offset is None else offset)


# --- bounded, partial-coverage semantics ---


def test_single_page_read_is_complete_with_provenance_and_no_body_leak():
    opener, calls = run([body(HELLO),
                         body(ledger([row(debugNote="RAW-BODY-TEXT"), row(rid="r2")], total=2))])
    result = fetch_usage_requests(opener=opener)
    assert result["source"] == "magpie_gateway" and result["endpoint"] == USAGE_ENDPOINT
    assert result["source_version"] == "0.1.1250"
    assert (result["status"], result["reason"], result["complete"]) == ("ok", None, True)
    assert result["row_count"] == 2 and result["scanned"] == 2
    assert result["reported_total"] == 2 and result["invalid_rows"] == 0
    assert result["pages_read"] == 1 and result["reached_cap"] is False
    assert result["row_cap"] == MAX_ROWS and result["page_limit"] == PAGE_LIMIT
    assert [r["rid"] for r in result["rows"]] == ["r1", "r2"]
    assert result["rows"][0]["input"] == 100
    assert result["rows"][0]["provider_account"] == "acct-a@example.test"
    assert urls(calls) == ["http://127.0.0.1:3425/api/hello",
                           "http://127.0.0.1:3425%s?offset=0&limit=%d" % (USAGE_ENDPOINT, PAGE_LIMIT)]
    # The response body is never echoed: an unknown field never reaches the result.
    assert "RAW-BODY-TEXT" not in json.dumps(result)


def test_pagination_walks_offset_pages_until_the_ledger_total_is_read():
    opener, calls = run([body(HELLO), body(ledger_of(PAGE_LIMIT, 0, 120)),
                         body(ledger_of(PAGE_LIMIT, PAGE_LIMIT, 120)),
                         body(ledger_of(20, 2 * PAGE_LIMIT, 120))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"], result["complete"]) == ("ok", None, True)
    assert result["pages_read"] == 3
    assert result["scanned"] == 120 == result["row_count"]
    assert [r["rid"] for r in result["rows"][:2]] == ["r0", "r1"]
    assert result["rows"][-1]["rid"] == "r119"
    assert urls(calls)[1:] == ["http://127.0.0.1:3425%s?offset=%d&limit=%d"
                               % (USAGE_ENDPOINT, page * PAGE_LIMIT, PAGE_LIMIT)
                               for page in range(3)]
    # No filters, no summary totals and no quota reads: only offset and limit.
    for url in urls(calls):
        assert "summary" not in url and "period" not in url and "quotas" not in url
    for url in urls(calls)[1:]:
        assert "?" in url
        assert all(part.split("=")[0] in ("offset", "limit")
                   for part in url.split("?", 1)[1].split("&"))


def test_reaching_the_page_and_row_caps_is_partial_never_complete():
    opener, calls = run([body(HELLO)] + [body(ledger_of(PAGE_LIMIT, page * PAGE_LIMIT, 5000))
                                         for page in range(MAX_PAGES)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("ok", None)
    assert result["complete"] is False and result["reached_cap"] is True
    assert result["pages_read"] == MAX_PAGES
    assert result["row_count"] == MAX_ROWS == result["scanned"]
    assert result["reported_total"] == 5000
    assert len(calls) == MAX_PAGES + 1  # one hello plus one page per attempt


def test_a_short_ledger_read_is_partial_not_zero():
    opener, calls = run([body(HELLO), body(ledger([row(), row(rid="r2")], total=500)),
                         body(ledger([], total=500, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"], result["complete"]) == ("ok", None, False)
    assert result["reported_total"] == 500 and result["scanned"] == 2
    assert result["row_count"] == 2 and [r["rid"] for r in result["rows"]] == ["r1", "r2"]
    assert result["reached_cap"] is False
    assert len(calls) == 3


def test_an_unverifiable_total_keeps_coverage_unknown():
    opener, _ = run([body(HELLO), body(ledger([row()], None)),
                     body(ledger([], None, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("ok", None)
    assert result["reported_total"] is None and result["complete"] is False
    assert result["row_count"] == 1 and result["scanned"] == 1


def test_an_empty_ledger_is_the_only_complete_zero():
    opener, _ = run([body(HELLO), body(ledger([], total=0))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["complete"]) == ("ok", True)
    assert result["rows"] == [] and result["row_count"] == 0
    assert result["scanned"] == 0 and result["reported_total"] == 0


def test_unparseable_rows_make_the_scan_incomplete_when_counts_match():
    opener, _ = run([body(HELLO), body(ledger([row(), "garbage"], total=2)),
                     body(ledger([], total=2, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    assert result["complete"] is False and result["invalid_rows"] == 1
    assert result["row_count"] == 1 and result["scanned"] == 2


# --- hello handshake ---


def test_hello_is_verified_first_and_a_non_magpie_gateway_stops():
    opener, calls = run([body({"name": "other", "version": "1"}), body(ledger([], total=0))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("not_magpie", "invalid_hello")
    assert result["source_version"] is None and result["rows"] == []
    assert result["complete"] is False
    assert urls(calls) == ["http://127.0.0.1:3425/api/hello"]


def test_a_versionless_hello_stops_before_any_evidence_request():
    opener, calls = run([body({"name": "magpie"}), body(ledger([row()], total=1))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("not_magpie", "invalid_hello")
    assert len(calls) == 1


def test_a_handshake_failure_reports_a_reason_without_a_body():
    opener, calls = run([error(403, PRIVATE[0]), body(ledger([row()], total=1))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("refused", "forbidden")
    assert PRIVATE[0] not in json.dumps(result)
    assert len(calls) == 1


# --- fail-closed refusals ---


@pytest.mark.parametrize("url", [
    "http://example.test", "http://127.0.0.2", "http://localhost.evil",
    "http://user:pass@localhost:3425", "http://localhost:bad", "http://localhost/path",
    "ftp://localhost", "not a url", "http://localhost:3425?x=1", "",
])
def test_only_loopback_origins_are_read(url):
    def forbidden(*args, **kwargs):
        pytest.fail("opener must not be called")
    for call in (lambda: fetch_usage_requests(url, opener=forbidden),
                 lambda: fetch_session_routes(["sess-task-1"], url, opener=forbidden)):
        result = call()
        assert result["status"] == "refused" and result["reason"] == "invalid_url"
        assert result["complete"] is False and result["source_version"] is None


def test_redirect_is_refused_without_exposing_the_location():
    opener, _ = run([body(HELLO), error(302, PRIVATE[0])])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("refused", "redirect_refused")
    assert PRIVATE[0] not in json.dumps(result)
    assert result["rows"] == [] and result["complete"] is False


@pytest.mark.parametrize("code,reason,status", [
    (301, "redirect_refused", "refused"), (302, "redirect_refused", "refused"),
    (307, "redirect_refused", "refused"),
    (403, "forbidden", "refused"), (429, "rate_limited", "refused"),
    (404, "not_found", "unavailable"),
    (500, "http_error", "unavailable"), (502, "http_error", "unavailable"),
])
def test_http_failures_fail_closed_without_body_text(code, reason, status):
    opener, _ = run([body(HELLO), error(code, PRIVATE[0])])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == (status, reason)
    assert result["rows"] == [] and result["reported_total"] is None
    assert result["complete"] is False
    assert PRIVATE[0] not in json.dumps(result)


def test_a_non_two_xx_status_code_fails_closed():
    opener, _ = run([body(HELLO), body({"rows": [], "total": 0}, code=503)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "http_error")
    assert result["rows"] == [] and result["complete"] is False


def test_transport_and_timeout_failures_never_echo_exception_text():
    for failure, reason in ((OSError(PRIVATE[0]), "request_failed"),
                            (TimeoutError(PRIVATE[1]), "request_timeout")):
        opener, _ = run([body(HELLO), failure])
        result = fetch_usage_requests(opener=opener)
        assert (result["status"], result["reason"]) == ("unavailable", reason)
        assert all(secret not in json.dumps(result) for secret in PRIVATE)


def test_an_oversized_body_fails_closed_at_the_byte_bound():
    opener, _ = run([body(HELLO), raw(b"x" * (MAX_BODY_BYTES + 1))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "body_too_large")
    assert result["rows"] == [] and result["complete"] is False


def test_a_body_at_the_byte_bound_is_read_and_then_validated():
    opener, _ = run([body(HELLO), raw(b"x" * MAX_BODY_BYTES)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_schema")


# --- schema and pagination validation ---


@pytest.mark.parametrize("payload", [{"rows": "nope"}, {"rows": 7}, "not-a-page", 5, [], None, "{"])
def test_mismatched_ledger_schema_fails_closed(payload):
    opener, _ = run([body(HELLO), body(payload)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_schema")
    assert result["rows"] == [] and result["complete"] is False


@pytest.mark.parametrize("page", [
    {"rows": [], "total": 0, "offset": PAGE_LIMIT},
    {"rows": [], "offset": 999},
    {"rows": [], "offset": "page-1"},
    {"rows": [], "offset": -1},
])
def test_an_offset_mismatch_fails_closed(page):
    opener, _ = run([body(HELLO), body(page)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_pagination")
    assert result["rows"] == [] and result["complete"] is False


@pytest.mark.parametrize("patch", [{"total": "many"}, {"total": -5}, {"total": True},
                                   {"total": float("nan")}, {"total": float("inf")}])
def test_invalid_pagination_fields_fail_closed(patch):
    page = ledger([row()], total=1)
    page.update(patch)
    opener, _ = run([body(HELLO), body(page)])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_pagination")
    assert result["rows"] == [] and result["reported_total"] is None


def test_a_shrinking_total_fails_closed():
    opener, _ = run([body(HELLO), body(ledger([row()], total=100)),
                     body(ledger([row(rid="r2")], total=50, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_pagination")


def test_an_inconsistent_total_across_pages_fails_closed():
    opener, _ = run([body(HELLO), body(ledger([row()], total=100)),
                     body(ledger([row(rid="r2")], None, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_pagination")


# --- privacy ---


def test_private_values_never_reach_the_usage_result():
    opener, _ = run([body(HELLO),
                     body(ledger([row(alias=PRIVATE[1], providerAccount=PRIVATE[1]),
                                  row(rid="r2", providerAccount=PRIVATE[1])], total=2)),
                     body(ledger([], total=2, offset=PAGE_LIMIT))])
    result = fetch_usage_requests(opener=opener)
    dumped = json.dumps(result)
    for secret in PRIVATE:
        assert secret not in dumped
    assert result["rows"][0]["provider_account"] is None
    assert result["rows"][0]["rid"] == "r1" and result["row_count"] == 2


# --- route traces ---


def test_session_ids_are_url_encoded_not_concatenated():
    opener, calls = run([body(HELLO), body(TRACE), body(TRACE)])
    result = fetch_session_routes(["sess task/1", "sess+2"], opener=opener)
    assert (result["status"], result["reason"], result["complete"]) == ("ok", None, True)
    assert result["source"] == "magpie_gateway" and result["endpoint"] == ROUTE_ENDPOINT
    assert result["source_version"] == "0.1.1250"
    assert result["requested"] == 2 and result["returned"] == 2 and result["missing"] == 0
    assert result["session_cap"] == MAX_SESSIONS
    assert [t["session"] for t in result["traces"]] == ["sess task/1", "sess+2"]
    assert result["traces"][0]["trace"]["served"] == "claude-fable-5-1"
    assert result["traces"][0]["trace"]["done"] is True
    assert urls(calls) == ["http://127.0.0.1:3425/api/hello",
                           "http://127.0.0.1:3425/v1/magpie/route?session=sess%20task%2F1",
                           "http://127.0.0.1:3425/v1/magpie/route?session=sess%2B2"]
    # Encoded ids cannot add a second query field or terminate the query.
    for url in urls(calls)[1:]:
        assert len(url.split("?", 1)[1].split("&")) == 1
        assert url.split("?", 1)[1].startswith("session=")


def test_unencodable_sessions_fail_closed_before_any_request():
    def forbidden(*args, **kwargs):
        pytest.fail("opener must not be called")
    bad = ("", None, 5, "x" * (MAX_SESSION_LEN + 1), "sess\n1", "sess&x", "sess#x",
           "sess?x", "sess=x", "sess%20x", " sess", "sess ", ["sess"])
    for value in bad:
        result = fetch_session_routes([value], opener=forbidden)
        assert (result["status"], result["reason"]) == ("refused", "invalid_session"), value
        assert result["traces"] == [] and result["complete"] is False


def test_too_many_sessions_fail_closed_before_any_request():
    def forbidden(*args, **kwargs):
        pytest.fail("opener must not be called")
    result = fetch_session_routes(["s%d" % i for i in range(MAX_SESSIONS + 3)], opener=forbidden)
    assert (result["status"], result["reason"]) == ("refused", "too_many_sessions")
    assert result["requested"] == MAX_SESSIONS + 1  # bounded, not the whole input
    assert result["complete"] is False
    result = fetch_session_routes([], opener=forbidden)
    assert (result["status"], result["reason"]) == ("refused", "invalid_session")


@pytest.mark.parametrize("payload", [{}, [], {"rows": []}, "not-a-trace", None])
def test_an_unrecognized_route_payload_fails_closed(payload):
    opener, _ = run([body(HELLO), body(payload)])
    result = fetch_session_routes(["sess-task-1"], opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_schema")
    assert result["traces"] == [] and result["complete"] is False


def test_one_missing_session_keeps_the_others_and_reports_incomplete_coverage():
    opener, calls = run([body(HELLO), body(TRACE), error(404, PRIVATE[0])])
    result = fetch_session_routes(["sess-1", "sess-2"], opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "not_found")
    assert result["requested"] == 2 and result["returned"] == 1 and result["missing"] == 1
    assert result["complete"] is False
    assert result["traces"][0]["session"] == "sess-1"
    assert PRIVATE[0] not in json.dumps(result)
    assert len(calls) == 3


def test_route_traces_are_privacy_filtered_and_bounded():
    poisoned = dict(TRACE)
    poisoned["user"] = PRIVATE[1]
    poisoned["asked"] = PRIVATE[1]
    poisoned["tries"] = [{"model": "m%d" % i} for i in range(20)]
    opener, _ = run([body(HELLO), body(poisoned)])
    result = fetch_session_routes(["sess-task-1"], opener=opener)
    dumped = json.dumps(result)
    for secret in PRIVATE:
        assert secret not in dumped
    assert result["traces"][0]["trace"]["asked"] is None
    assert len(result["traces"][0]["trace"]["tries"]) == 8
    assert result["complete"] is True


# --- integration with the accepted parsers and the unchanged default path ---


def test_adapter_rows_feed_the_existing_correlator_directly():
    opener, _ = run([body(HELLO),
                     body(ledger([row(), row(rid="r2", **{"in": 5, "out": 1, "cost": 0.0001})], total=2))])
    fetched = fetch_usage_requests(opener=opener)
    report = correlate_task_usage([], fetched["rows"], sessions=["sess-task-1"])
    assert report["basis"] == "magpie_measured"
    assert report["request_count"] == 2
    assert report["totals"]["input"] == 105 and report["totals"]["output"] == 11
    assert report["totals"]["cost_usd"] == pytest.approx(0.0011)


def test_no_summary_or_period_endpoint_is_read_for_task_consumption():
    opener, calls = run([body(HELLO)] + [body(ledger_of(PAGE_LIMIT, page * PAGE_LIMIT, 4000))
                                         for page in range(MAX_PAGES)])
    result = fetch_usage_requests(opener=opener)
    for url in urls(calls):
        assert "summary" not in url and "period=" not in url and "day=" not in url
    # reported_total is a row count of the ledger, never tokens or a period total.
    assert result["reported_total"] == 4000 and result["row_count"] == MAX_ROWS
    assert result["complete"] is False and result["reached_cap"] is True


def test_the_default_snapshot_still_asks_only_for_hello_models_and_quotas():
    opener, calls = run([body(HELLO), body({"object": "list", "data": []}),
                         body({"object": "list", "data": []})])
    result = fetch_magpie_snapshot(opener=opener)
    assert result["status"] == "available"
    assert urls(calls) == ["http://127.0.0.1:3425/api/hello", "http://127.0.0.1:3425/v1/models",
                           "http://127.0.0.1:3425/v1/magpie/quotas?kept=1"]
    assert not any(USAGE_ENDPOINT in url or ROUTE_ENDPOINT in url for url in urls(calls))


# --- boundary regressions ---


def test_duplicate_rids_prevent_complete_coverage():
    first = ledger([row(rid="same") for _ in range(PAGE_LIMIT)], total=PAGE_LIMIT + 1, offset=0)
    second = ledger([row(rid="same")], total=PAGE_LIMIT + 1, offset=PAGE_LIMIT)
    opener, _ = run([body(HELLO), body(first), body(second)])
    result = fetch_usage_requests(opener=opener)
    assert result["complete"] is False
    assert result["row_count"] == PAGE_LIMIT + 1
    assert result["reported_total"] == PAGE_LIMIT + 1
    assert result["invalid_rows"] == 0


def test_missing_rid_prevents_complete_coverage():
    opener, _ = run([body(HELLO), body(ledger([{"in": 1}], total=1))])
    result = fetch_usage_requests(opener=opener)
    assert result["complete"] is False
    assert result["row_count"] == 1


def test_page_over_limit_is_refused():
    opener, _ = run([body(HELLO),
                     body(ledger([row(rid="r%d" % i) for i in range(PAGE_LIMIT + 1)],
                                 total=PAGE_LIMIT + 1, offset=0))])
    result = fetch_usage_requests(opener=opener)
    assert (result["status"], result["reason"]) == ("unavailable", "invalid_schema")
    assert result["complete"] is False and result["rows"] == []


def test_growing_total_prevents_complete():
    first = ledger_of(PAGE_LIMIT, 0, PAGE_LIMIT + 1)
    second = ledger([row(rid="r%d" % (PAGE_LIMIT + i)) for i in range(2)],
                    total=PAGE_LIMIT + 2, offset=PAGE_LIMIT)
    opener, _ = run([body(HELLO), body(first), body(second)])
    result = fetch_usage_requests(opener=opener)
    assert result["complete"] is False
    assert result["reported_total"] == PAGE_LIMIT + 2
    assert result["status"] == "ok"


def test_cross_page_private_scrub():
    secret = "synthetic-private-model"
    first = ledger([row(rid="r%d" % i, **{"model": secret}) for i in range(PAGE_LIMIT)],
                   total=PAGE_LIMIT + 1, offset=0)
    second = ledger([row(rid="r%d" % PAGE_LIMIT, **{"alias": secret})],
                    total=PAGE_LIMIT + 1, offset=PAGE_LIMIT)
    opener, _ = run([body(HELLO), body(first), body(second)])
    result = fetch_usage_requests(opener=opener)
    dumped = json.dumps(result)
    assert secret not in dumped
    assert result["complete"] is True


def test_private_session_not_echoed_in_route_result():
    secret = "synthetic-private-alias"
    payload = {"model": "m", "served": "m", "alias": secret}
    opener, _ = run([body(HELLO), body(payload)])
    result = fetch_session_routes([secret], opener=opener)
    assert secret not in json.dumps(result)


def test_cross_trace_private_scrub():
    secret = "synthetic-private-alias"
    first = {"model": "m", "served": "m"}
    second = {"model": "m", "served": "m", "alias": secret}
    opener, _ = run([body(HELLO), body(first), body(second)])
    result = fetch_session_routes([secret, "opaque-second"], opener=opener)
    assert secret not in json.dumps(result)
    assert "opaque-second" in json.dumps(result)


def test_invalid_object_session_is_json_safe():
    result = fetch_session_routes([object()])
    dumped = json.dumps(result)
    assert len(dumped) < 4000
    assert result["status"] == "refused"


def test_malformed_route_model_not_complete():
    opener, _ = run([body(HELLO), body({"model": []})])
    result = fetch_session_routes(["opaque-session"], opener=opener)
    assert result["complete"] is False
    assert result["status"] == "unavailable"
