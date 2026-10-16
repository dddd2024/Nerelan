"""Fixture-only Magpie route evidence checks: no gateway or network is contacted."""

from datetime import datetime, timedelta, timezone
import json

import pytest

from reverse_agent.model_access.magpie_route import parse_route_evidence

NOW = datetime(2026, 10, 15, 7, 0, tzinfo=timezone.utc)
PRIVATE = ("person@example.test", "private-alias", "private-origin")
SESSION = "session-123"


def entry(**overrides):
    base = {"sessionId": SESSION, "requestedModel": "routing",
            "routedModel": "workbuddy/glm-5.2", "provider": "workbuddy",
            "accountRef": "abc123def456",
            "occurredAt": "2026-10-15T06:59:00Z", "sourceVersion": "0.1.1250"}
    base.update(overrides)
    return base


def envelope(*items):
    return {"object": "list", "data": list(items)}


def verified_record():
    return {"state": "VERIFIED", "reason": None, "session_id": SESSION,
            "requested_model": "routing", "routed_model": "workbuddy/glm-5.2",
            "provider": "workbuddy", "account_ref": "abc123def456",
            "observed_at": "2026-10-15T06:59:00+00:00",
            "provenance": "EXTERNAL_MAGPIE", "source_version": "0.1.1250"}


def assert_unverified(result, reason, state="UNKNOWN"):
    assert result["state"] == state
    assert result["reason"] == reason
    assert result["routed_model"] is None
    assert result["provider"] is None
    assert result["account_ref"] is None


def test_verified_route():
    result = parse_route_evidence(envelope(entry()), SESSION, NOW)
    assert result == verified_record()
    # Same evidence as a JSON string.
    assert parse_route_evidence(json.dumps(envelope(entry())), SESSION, NOW) == result
    # Other sessions in the envelope are ignored.
    other = entry(sessionId="session-other")
    assert parse_route_evidence(envelope(other, entry()), SESSION, NOW) == result


def test_group_name_never_becomes_the_routed_model():
    """The requested group/route name must never be reported as the actual model."""
    result = parse_route_evidence(envelope(entry(requestedModel="routing",
                                                 routedModel="routing")), SESSION, NOW)
    assert_unverified(result, "invalid_route_model")


def test_absent_session():
    assert_unverified(parse_route_evidence(envelope(entry(sessionId="other")), SESSION, NOW),
                      "session_not_found")
    assert_unverified(parse_route_evidence(envelope(), SESSION, NOW), "session_not_found")


def test_invalid_session_id():
    for bad in ("", "   ", None, 123, [], {}):
        assert_unverified(parse_route_evidence(envelope(entry()), bad, NOW), "invalid_session_id")


@pytest.mark.parametrize("payload", ["{", None, [], {}, {"data": []}, {"object": "list", "data": {}}])
def test_invalid_schema(payload):
    assert_unverified(parse_route_evidence(payload, SESSION, NOW), "invalid_schema")


@pytest.mark.parametrize("field", ["routedModel", "provider", "accountRef"])
def test_missing_route_fields(field):
    raw = entry()
    del raw[field]
    assert_unverified(parse_route_evidence(envelope(raw), SESSION, NOW), "missing_route_fields")


def test_missing_route_fields_never_fall_back_to_group():
    raw = entry(routedModel=None, provider=None, accountRef=None)
    result = parse_route_evidence(envelope(raw), SESSION, NOW)
    assert_unverified(result, "missing_route_fields")
    assert result["requested_model"] == "routing"


def test_fallback_ambiguous():
    duplicate = entry(accountRef="999999999999")
    assert_unverified(parse_route_evidence(envelope(entry(), duplicate), SESSION, NOW),
                      "fallback_ambiguous")


@pytest.mark.parametrize("extra", [
    {"unexpectedField": "x"}, {"user": PRIVATE[0]}, {"alias": PRIVATE[1]},
])
def test_untrusted_fields(extra):
    assert_unverified(parse_route_evidence(envelope(entry(**extra)), SESSION, NOW),
                      "untrusted_field")


def test_private_values_anywhere_reject():
    nested = {"object": "list", "data": [entry()],
              "user": PRIVATE[0]}
    assert_unverified(parse_route_evidence(nested, SESSION, NOW), "untrusted_field")


def test_stale_reading():
    old = entry(occurredAt="2026-10-15T06:00:00Z")
    assert_unverified(parse_route_evidence(envelope(old), SESSION, NOW),
                      "stale_reading", state="STALE")
    fresh_edge = entry(occurredAt=(NOW - timedelta(seconds=900)).isoformat())
    assert parse_route_evidence(envelope(fresh_edge), SESSION, NOW)["state"] == "VERIFIED"


@pytest.mark.parametrize("stamp", ["bad", "2026-10-15T06:59:00", None, 123])
def test_invalid_timestamp(stamp):
    assert_unverified(parse_route_evidence(envelope(entry(occurredAt=stamp)), SESSION, NOW),
                      "invalid_timestamp")


def test_invalid_now_and_max_age():
    bad_now = datetime(2026, 10, 15, 7, 0)
    assert_unverified(parse_route_evidence(envelope(entry()), SESSION, bad_now), "invalid_timestamp")
    assert_unverified(parse_route_evidence(envelope(entry()), SESSION, None), "invalid_timestamp")
    for bad_age in (-1, float("nan"), float("inf"), True, "x"):
        assert_unverified(parse_route_evidence(envelope(entry()), SESSION, NOW, bad_age),
                          "invalid_timestamp")


def test_no_private_data_in_any_result():
    payloads = [
        envelope(entry()), "{", envelope(entry(user=PRIVATE[0])),
        envelope(entry(), entry(accountRef="other")),
        envelope(entry(occurredAt="bad")),
    ]
    for payload in payloads:
        result = parse_route_evidence(payload, SESSION, NOW)
        assert all(secret not in json.dumps(result) for secret in PRIVATE)
