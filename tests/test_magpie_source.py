"""Fixture-only Magpie adapter checks: no gateway or vendor is contacted."""

from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from reverse_agent.model_access.magpie import (
    fetch_magpie_snapshot, magpie_enabled, parse_hello, parse_models, parse_quotas,
)
from reverse_agent.model_access.resources import build_resource_view
from reverse_agent.model_access.store import ModelProfileStore


NOW = datetime(2026, 10, 15, 7, 0, tzinfo=timezone.utc)
PRIVATE = ("person@example.test", "private-alias", "private-origin")


def quota():
    return {"provider": "workbuddy", "kind": "subscription", "plan": "Pro",
            "user": PRIVATE[0], "alias": PRIVATE[1], "from": PRIVATE[2],
            "readAt": "2026-10-15T06:59:00Z",
            "windows": [{"name": "hourly", "used": 20, "remaining": 80,
                         "resetsAt": "2026-10-15T08:00:00Z"},
                        {"name": "weekly", "used": 40, "remaining": 60, "unlimited": False}]}


def envelope(*items):
    return {"object": "list", "data": list(items)}


def test_hello():
    assert parse_hello('{"name":"magpie","version":"0.1.1250"}') == "0.1.1250"
    for payload in ({"name": "other", "version": "1"}, {}, "{", None, []):
        assert parse_hello(payload) is None


def test_models():
    models = parse_models(envelope(
        {"id": "workbuddy/glm-5.2", "owned_by": "workbuddy", "display_name": "GLM",
         "reasoning": True, "context_window": 200000, "max_output_tokens": 32000},
        {"id": "workbuddy-ai/model", "owned_by": "workbuddy-ai"}, {"id": "routing"}))
    assert [m["provider"] for m in models] == ["workbuddy", "workbuddy-ai", None]
    assert [m["is_group"] for m in models] == [False, False, True]
    assert models[0]["context_window"] == 200000
    assert models[0]["reasoning"] is True
    assert parse_models("{") == []


def test_subscription_and_privacy():
    result = parse_quotas(envelope(quota()), NOW)
    account = result[0]
    assert account["state"] == "FRESH"
    assert account["provenance"] == "EXTERNAL_MAGPIE"
    assert [w["used_percent"] for w in account["windows"]] == [20, 40]
    assert len(account["account_ref"]) == 12
    assert parse_quotas(json.dumps(envelope(quota())), NOW) == result
    other = quota()
    other["user"] = "another@example.test"
    assert parse_quotas(envelope(other), NOW)[0]["account_ref"] != account["account_ref"]
    assert all(secret not in json.dumps(result) for secret in PRIVATE)


def test_fresh_state_has_none_reason_and_degraded_states_have_reasons():
    """State/reason alignment: exactly FRESH carries reason None; every other
    state persists a real machine-readable reason."""
    fresh = parse_quotas(envelope(quota()), NOW)[0]
    assert fresh["state"] == "FRESH" and fresh["reason"] is None
    undated_raw = quota()
    undated_raw.pop("readAt", None)
    undated_raw.pop("asOf", None)
    undated = parse_quotas(envelope(undated_raw), NOW)[0]
    assert undated["state"] == "UNDATED" and undated["reason"] == "no_read_time"
    stale_raw = quota()
    stale_raw["readAt"] = "2026-10-15T05:00:00Z"
    stale = parse_quotas(envelope(stale_raw), NOW)[0]
    assert stale["state"] == "STALE" and stale["reason"] == "stale_reading"
    for account in (fresh, undated, stale):
        assert (account["state"] == "FRESH") == (account["reason"] is None)


def test_undated_reading_keeps_its_windows():
    raw = quota()
    raw.pop("readAt", None)
    raw.pop("asOf", None)
    account = parse_quotas(envelope(raw), NOW)[0]
    assert (account["state"], account["reason"], account["observed_at"]) == ("UNDATED", "no_read_time", None)
    assert [window["used_percent"] for window in account["windows"]] == [w["used"] for w in raw["windows"]]


@pytest.mark.parametrize("patch,reason,state", [
    ({"readAt": "2026-10-15T06:00:00Z"}, "stale_reading", "STALE"),
    ({"asOf": "2026-10-15T06:00:00Z"}, "stale_reading", "STALE"),
    ({"error": PRIVATE[0]}, "quota_error", "UNKNOWN"),
    ({"readDeferred": True}, "read_deferred", "UNKNOWN"),
    ({"windows": []}, "missing_windows", "UNKNOWN"),
    ({"readAt": "bad"}, "invalid_timestamp", "UNKNOWN"),
    ({"kind": []}, "invalid_schema", "UNKNOWN"),
])
def test_degraded(patch, reason, state):
    raw = quota()
    raw.update(patch)
    result = parse_quotas(envelope(raw), NOW)
    assert result[0]["state"] == state
    assert result[0]["reason"] == reason
    assert result[0]["windows"] == []
    # Stale readings preserve validated windows in cached_windows; all other
    # error/malformed states cache nothing.
    if state == "STALE":
        assert len(result[0]["cached_windows"]) == 2
    else:
        assert result[0]["cached_windows"] == []
    assert all(secret not in json.dumps(result) for secret in PRIVATE)


# --- Stale history preservation (#1170) ---


def test_stale_reading_preserves_validated_windows_in_cached_windows():
    """A stale reading keeps windows=[] for admission but preserves validated
    windows in cached_windows for display, with the same field checks."""
    raw = quota()
    raw["readAt"] = "2026-10-15T05:00:00Z"  # 2 hours old: stale
    account = parse_quotas(envelope(raw), NOW)[0]
    assert account["state"] == "STALE"
    assert account["reason"] == "stale_reading"
    assert account["windows"] == []  # admission semantics: stale = unknown
    # Cached windows preserve the same validated fields as fresh windows.
    assert len(account["cached_windows"]) == 2
    assert [w["name"] for w in account["cached_windows"]] == ["hourly", "weekly"]
    assert account["cached_windows"][0]["used_percent"] == 20
    assert account["cached_windows"][0]["remaining_percent"] == 80
    assert account["cached_windows"][0]["resets_at"] is not None
    assert account["cached_windows"][0]["unlimited"] is False
    # observed_at is still preserved so the UI can label when it was read.
    assert account["observed_at"] is not None


def test_stale_reading_with_invalid_window_discards_cached_windows():
    """A stale reading whose windows fail validation is not cached as trusted."""
    raw = quota()
    raw["readAt"] = "2026-10-15T05:00:00Z"  # stale
    raw["windows"][0]["used"] = -1  # invalid percent
    account = parse_quotas(envelope(raw), NOW)[0]
    assert account["state"] == "UNKNOWN"  # invalid_window overrides stale
    assert account["reason"] == "invalid_window"
    assert account["windows"] == []
    assert account["cached_windows"] == []


def test_stale_reading_with_malformed_window_dict_discards_cached_windows():
    raw = quota()
    raw["readAt"] = "2026-10-15T05:00:00Z"
    raw["windows"][0] = "not-a-dict"
    account = parse_quotas(envelope(raw), NOW)[0]
    assert account["reason"] == "invalid_window"
    assert account["cached_windows"] == []


def test_error_and_read_deferred_accounts_have_no_cached_windows():
    """Error/deferred rows are never cached as trusted history."""
    for patch in [{"error": "boom"}, {"readDeferred": True}]:
        raw = quota()
        raw.update(patch)
        account = parse_quotas(envelope(raw), NOW)[0]
        assert account["cached_windows"] == []


def test_duplicate_accounts_clear_cached_windows_as_well_as_windows():
    """Duplicate account handling clears both windows and cached_windows."""
    raw = quota()
    raw["readAt"] = "2026-10-15T05:00:00Z"  # stale but valid windows
    duplicate = deepcopy(raw)
    duplicate["windows"][0]["used"] = 90
    result = parse_quotas(envelope(raw, duplicate), NOW)
    for account in result:
        assert account["state"] == "UNKNOWN"
        assert account["reason"] == "duplicate_account"
        assert account["windows"] == []
        assert account["cached_windows"] == []


def test_cached_windows_privacy_filtered_same_as_windows():
    """Cached windows apply the same privacy filtering (secret stripping) as fresh windows."""
    raw = quota()
    raw["readAt"] = "2026-10-15T05:00:00Z"  # stale
    raw["windows"][0]["name"] = PRIVATE[1]  # private alias as window name
    account = parse_quotas(envelope(raw), NOW)[0]
    # Private name → name filtered to None → invalid_window, nothing cached.
    assert account["reason"] == "invalid_window"
    assert account["cached_windows"] == []
    assert all(secret not in json.dumps(account) for secret in PRIVATE)


def test_undated_and_fresh_accounts_have_empty_cached_windows():
    """Only stale readings populate cached_windows; fresh/undated keep windows in windows[]."""
    # Fresh
    fresh = parse_quotas(envelope(quota()), NOW)[0]
    assert fresh["state"] == "FRESH"
    assert len(fresh["windows"]) == 2
    assert fresh["cached_windows"] == []
    # Undated
    undated_raw = quota()
    undated_raw.pop("readAt", None)
    undated_raw.pop("asOf", None)
    undated = parse_quotas(envelope(undated_raw), NOW)[0]
    assert undated["state"] == "UNDATED"
    assert len(undated["windows"]) == 2
    assert undated["cached_windows"] == []


@pytest.mark.parametrize("value", [-1, 101, "20", None, True, float("nan"), float("inf"), {}, []])
@pytest.mark.parametrize("field", ["used", "remaining"])
def test_invalid_percent(value, field):
    raw = quota()
    raw["windows"][0][field] = value
    result = parse_quotas(envelope(raw), NOW)[0]
    assert result["state"] == "UNKNOWN"
    assert result["windows"] == []


@pytest.mark.parametrize("payload", ["{", None, [], {}, {"data": []}, envelope(None)])
def test_malformed(payload):
    result = parse_quotas(payload, NOW)
    assert result[0]["state"] == "UNKNOWN"


def test_duplicate_accounts():
    raw = quota()
    duplicate = deepcopy(raw)
    duplicate["windows"][0]["used"] = 90
    result = parse_quotas(envelope(raw, duplicate), NOW)
    assert all(a["state"] == "UNKNOWN" and a["reason"] == "duplicate_account" and not a["windows"] for a in result)


class Response(BytesIO):
    def getcode(self):
        return 200


def fixture_opener(payloads, calls):
    def open_request(request, timeout):
        calls.append(request)
        assert timeout == 2.0
        assert request.get_header("Authorization") == "Bearer magpie-nerelan"
        assert request.get_method() == "GET"
        return Response(json.dumps(payloads[len(calls) - 1]).encode())
    return open_request


def test_fetch():
    calls = []
    raw = quota()
    raw["readAt"] = datetime.now(timezone.utc).isoformat()
    result = fetch_magpie_snapshot(opener=fixture_opener([
        {"name": "magpie", "version": "0.1.1250"}, envelope({"id": "workbuddy/glm-5.2"}), envelope(raw)], calls))
    assert result["status"] == "available"
    assert result["accounts"][0]["source_version"] == "0.1.1250"
    assert result["accounts"][0]["state"] == "FRESH"
    assert [r.full_url for r in calls] == ["http://127.0.0.1:3425/api/hello", "http://127.0.0.1:3425/v1/models", "http://127.0.0.1:3425/v1/magpie/quotas?kept=1"]
    assert all(secret not in json.dumps(result) for secret in PRIVATE)


def test_not_magpie_stops():
    calls = []
    result = fetch_magpie_snapshot(opener=fixture_opener([{"name": "other"}], calls))
    assert result["status"] == "not_magpie"
    assert len(calls) == 1


@pytest.mark.parametrize("url", ["http://example.test", "http://127.0.0.2", "http://localhost.evil", "http://user:pass@localhost", "file:///tmp", "http://localhost:bad", "http://localhost/path"])
def test_refused_without_request(url):
    def forbidden(*args, **kwargs):
        pytest.fail("opener must not be called")
    assert fetch_magpie_snapshot(url, opener=forbidden)["status"] == "refused"


def test_redirect_and_transport_privacy():
    def redirect(request, timeout):
        raise HTTPError(request.full_url, 302, PRIVATE[0], {"Location": "http://example.test"}, None)
    result = fetch_magpie_snapshot(opener=redirect)
    assert result["status"] == "refused"
    assert PRIVATE[0] not in json.dumps(result)

    def failed(request, timeout):
        raise OSError(PRIVATE[0])
    assert fetch_magpie_snapshot(opener=failed)["reason"] == "request_failed"


@pytest.mark.parametrize("value", [None, "", "0", "true", "yes", " 1", "1", 1, True])
def test_enabled(value):
    assert magpie_enabled({"REVERSE_AGENT_MAGPIE": value}) is (value == "1")


# --- Wiring into build_resource_view (fake store, no network) ---


def _resource_store() -> ModelProfileStore:
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "sense", "name": "SenseNova", "provider": "litellm-proxy",
                             "base_url": "https://token.sensenova.cn/v1", "auth_method": "api_key",
                             "enabled": True, "api_key": "wiring-secret"})
    store.bind_connection_models("sense", ["glm-5.2"], "auto")
    return store


def _by_id(view):
    return {item["connection_id"]: item for item in view["resources"]}


def _magpie_snapshot():
    return {"status": "available", "version": "0.1.1250",
            "models": [{"model_id": "workbuddy/glm-5.2", "provider": "workbuddy",
                        "display_name": "GLM", "reasoning": True,
                        "context_window": 200000, "max_output_tokens": 32000, "is_group": False}],
            "accounts": [{"provider": "workbuddy", "kind": "subscription", "plan": "Pro",
                          "account_ref": "abc123def456", "windows": [{"name": "hourly", "used_percent": 20,
                          "remaining_percent": 80, "resets_at": "2026-10-15T08:00:00Z", "unlimited": False}],
                          "cached_windows": [],
                          "state": "FRESH", "reason": None, "observed_at": "2026-10-15T06:59:00Z",
                          "provenance": "EXTERNAL_MAGPIE", "source_version": "0.1.1250"}],
            "reason": None}


def test_disabled_env_has_no_external_sources():
    """external=None leaves the view identical to the pre-Magpie shape."""
    store = _resource_store()
    without = build_resource_view(store, dict)
    with_external_none = build_resource_view(store, dict, external=None)
    assert "external_sources" not in without
    assert "external_sources" not in with_external_none
    # Identical payloads.
    assert json.dumps(without, sort_keys=True) == json.dumps(with_external_none, sort_keys=True)


def test_external_snapshot_appears_under_magpie_and_leaves_resources_unchanged():
    store = _resource_store()
    baseline = build_resource_view(store, dict)
    view = build_resource_view(store, dict, external=_magpie_snapshot)

    assert view["external_sources"]["magpie"]["status"] == "available"
    assert view["external_sources"]["magpie"]["accounts"][0]["provider"] == "workbuddy"

    # No resource's quota, token_usage, equivalent_cost or the summary changed.
    assert _by_id(view)["sense"]["quota"] == _by_id(baseline)["sense"]["quota"]
    assert _by_id(view)["sense"]["token_usage"] == _by_id(baseline)["sense"]["token_usage"]
    assert _by_id(view)["sense"]["equivalent_cost"] == _by_id(baseline)["sense"]["equivalent_cost"]
    assert view["summary"] == baseline["summary"]


def test_raising_external_yields_unavailable_while_resources_render():
    def boom():
        raise RuntimeError("gateway down")
    store = _resource_store()
    view = build_resource_view(store, dict, external=boom)
    assert view["external_sources"]["magpie"] == {"status": "unavailable"}
    assert view["summary"]["connections"] == 1
    assert _by_id(view)["sense"]["bindings"][0]["model_id"] == "glm-5.2"


def test_non_mapping_external_yields_unavailable():
    store = _resource_store()
    view = build_resource_view(store, dict, external=lambda: ["not", "a", "mapping"])
    assert view["external_sources"]["magpie"] == {"status": "unavailable"}
    assert len(view["resources"]) == 1
