"""Provider-free contract fixtures derived from Magpie session_route.go."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from reverse_agent.model_access.magpie_route import parse_route_evidence

NOW = datetime(2026, 10, 16, 8, 25, tzinfo=timezone.utc)
SESSION = "nerelan-req-123"


def route(**kw):
    data = {
        "id": 12, "time": "2026-10-16T08:24:00Z",
        "asked": "group/development", "group": "development",
        "model": "rb/glm-5.3", "served": "glm-5.3",
        "done": True, "status": 200,
        "tries": [
            {"model": "ra/glm-5.3", "done": True, "status": 429, "fail": "rate limit"},
            {"model": "rb/glm-5.3", "done": True, "status": 200},
        ],
    }
    data.update(kw)
    return data


def response(item=None, *, seq=17, session=SESSION):
    return {"session": session, "seq": seq, "route": route() if item is None else item}


def assert_unknown(result, reason, state="UNKNOWN"):
    assert result["state"] == state
    assert result["reason"] == reason
    assert result["routed_model"] is None
    assert result["provider"] is None
    assert result["account_ref"] is None
    assert result["account_state"] == "UNKNOWN"


def test_exact_upstream_gateway_schema_valid_route_with_fallback():
    obj = response()
    val = parse_route_evidence(obj, SESSION, NOW, after_seq=16)
    assert val["state"] == "VERIFIED_ROUTE"
    assert val["source"] == "MAGPIE_SESSION_ROUTE"
    assert val["seq"] == 17
    assert val["requested_model"] == "group/development"
    assert val["group"] == "development"
    assert val["routed_model"] == "rb/glm-5.3"
    assert val["provider"] == "rb"
    assert val["fallback_count"] == 1
    assert val["account_ref"] is None
    assert val["observed_at"] == "2026-10-16T08:24:00+00:00"
    assert parse_route_evidence(json.dumps(obj), SESSION, NOW, after_seq=16) == val


def test_local_gateway_absent_session_response():
    assert_unknown(parse_route_evidence({"route": None, "seq": 0, "session": SESSION}, SESSION, NOW),
                   "session_has_no_route")


@pytest.mark.parametrize("bad", [None, [], {}, {"object": "list", "data": []}, "nonsense", "[1]"])
def test_reject_synthetic_or_invalid_envelope(bad):
    assert parse_route_evidence(bad, SESSION, NOW)["state"] == "UNKNOWN"


def test_session_exact_match_and_replay_fence():
    assert_unknown(parse_route_evidence(response(session="another"), SESSION, NOW), "session_mismatch")
    assert_unknown(parse_route_evidence(response(seq=17), SESSION, NOW, after_seq=17), "sequence_not_advanced")
    assert_unknown(parse_route_evidence(response(seq=16), SESSION, NOW, after_seq=17), "sequence_not_advanced")
    assert parse_route_evidence(response(seq=18), SESSION, NOW, after_seq=17)["state"] == "VERIFIED_ROUTE"


def test_inflight_candidate_never_becomes_real_route():
    val = parse_route_evidence(response(route(done=False, status=0, served="")), SESSION, NOW)
    assert_unknown(val, "route_in_flight", state="IN_FLIGHT")
    assert val["candidate_model"] == "rb/glm-5.3"
    assert val["requested_model"] == "group/development"


def test_error_even_if_last_model_known():
    for status in (0, 401, 429, 500, 300, True, "200"):
        assert_unknown(parse_route_evidence(response(route(status=status)), SESSION, NOW), "route_failed")


@pytest.mark.parametrize("malformed", [
    [],
    {"done": True, "status": 200, "time": "2026-10-16T08:24:00Z", "model": "p/m"},
    route(tries=[]),
    route(tries="not-a-list"),
])
def test_no_route_or_no_successful_try(malformed):
    reason = "invalid_route" if not isinstance(malformed, dict) else "missing_route_tries"
    assert_unknown(parse_route_evidence(response(malformed), SESSION, NOW), reason)


def test_failed_or_mismatched_last_try_not_attributed():
    for bad in (
        route(tries=[{"model": "rb/glm-5.3", "done": False, "status": 200}]),
        route(tries=[{"model": "rb/glm-5.3", "done": True, "status": 429, "fail": "quota"}]),
        route(tries=[{"model": "ra/glm-5.3", "done": True, "status": 200}]),
        route(model="group/development"),
    ):
        assert_unknown(parse_route_evidence(response(bad), SESSION, NOW), "last_try_not_verified")


def test_served_vendor_model_never_overwrites_verified_member():
    good = route(served="rb/glm-5.3")
    assert parse_route_evidence(response(good), SESSION, NOW)["routed_model"] == "rb/glm-5.3"
    bad = route(served="another-model")
    assert_unknown(parse_route_evidence(response(bad), SESSION, NOW), "served_model_conflict")


def test_stale_future_missing_time_are_not_attributed():
    old = (NOW - timedelta(hours=3)).isoformat()
    assert_unknown(parse_route_evidence(response(route(time=old)), SESSION, NOW),
                   "stale_route", state="STALE")
    future = (NOW + timedelta(minutes=3)).isoformat()
    assert_unknown(parse_route_evidence(response(route(time=future)), SESSION, NOW), "future_route")
    for time in (None, "", "2026-10-16T08:24:00"):
        assert_unknown(parse_route_evidence(response(route(time=time)), SESSION, NOW),
                       "missing_route_timestamp")


def test_reject_bad_clock_and_sequence():
    assert_unknown(parse_route_evidence(response(), SESSION, datetime(2026, 10, 16)), "invalid_clock")
    for age in (float("nan"), float("inf"), True, -1, "15"):
        assert_unknown(parse_route_evidence(response(), SESSION, NOW, age), "invalid_clock")
    for seq in (True, -1, "3"):
        assert_unknown(parse_route_evidence(response(seq=seq), SESSION, NOW), "invalid_sequence")


def test_unsupported_account_identity_never_inferred():
    obj = response(route(account="my.email@example.test", accountRef="secret",
                         authorization="Bearer fake", user="private"))
    result = parse_route_evidence(obj, SESSION, NOW)
    assert result["account_ref"] is None
    text = json.dumps(result)
    for secret in ("my.email@example.test", "secret", "Bearer fake", "private"):
        assert secret not in text


def test_requested_group_cannot_be_misattributed_as_provider_model():
    obj = response(route(model="group/dev",
                         tries=[{"model": "group/dev", "status": 200, "done": True}]))
    result = parse_route_evidence(obj, SESSION, NOW)
    assert_unknown(result, "last_try_not_verified")