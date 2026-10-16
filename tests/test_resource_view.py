from __future__ import annotations

import json

from reverse_agent.model_access.resources import build_resource_view
from reverse_agent.model_access.store import ModelProfileStore

SECRET = "resource-view-secret-key"


def _store() -> ModelProfileStore:
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "sense", "name": "SenseNova", "provider": "litellm-proxy",
                             "base_url": "https://token.sensenova.cn/v1", "auth_method": "api_key",
                             "enabled": True, "api_key": SECRET})
    store.bind_connection_models("sense", ["glm-5.2"], "auto")
    store.upsert_connection({"connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
                             "base_url": "https://claude.ai", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_binding({"binding_id": "claude-sonnet", "name": "Sonnet", "connection_id": "claude-account",
                          "executor_id": "claude_code", "model_id": "sonnet", "enabled": True})
    return store


def _by_id(view):
    return {item["connection_id"]: item for item in view["resources"]}


def test_one_view_joins_credentials_executors_bindings_and_observed_usage():
    store = _store()
    store.set_native_readiness("claude_code", "managed_login_unavailable")  # CLI present, no claude.ai login
    profiles = {"sense-glm-5.2-claude_code": {"attempts": 3, "ok": 3, "failed": 0, "success_rate": 1.0,
                                              "median_ok_seconds": 44, "median_ok_tokens": 3000,
                                              "observed_tokens": 9000, "failure_kinds": {"x": 1}}}
    view = build_resource_view(store, lambda: profiles)
    sense, claude = _by_id(view)["sense"], _by_id(view)["claude-account"]

    assert sense["credential"] == {"kind": "api_key", "configured": True, "status": "session"}
    assert sense["credential_owner"] == "nerelan"
    assert {e["executor_id"]: e["ready"] for e in sense["executors"]} == {"opencode": True, "claude_code": True}
    rows = {row["binding_id"]: row for row in sense["bindings"]}
    assert rows["sense-glm-5.2-claude_code"]["usable"] is True  # relay needs no account login
    assert rows["sense-glm-5.2-claude_code"]["observed"]["observed_tokens"] == 9000
    assert rows["sense-glm-5.2-claude_code"]["observed"]["provenance"] == "LOCAL_METERING"
    assert "failure_kinds" not in rows["sense-glm-5.2-claude_code"]["observed"]
    assert rows["sense-glm-5.2"]["observed"] is None
    assert sense["observed_usage"]["attempts"] == 3 and sense["observed_usage"]["observed_tokens"] == 9000

    assert claude["credential"] == {"kind": "subscription", "configured": False, "status": "missing"}
    assert claude["credential_owner"] == "claude-code-cli"
    assert claude["bindings"][0]["usable"] is False  # an account binding does need the login
    assert {k: view["summary"][k] for k in ("connections", "usable_bindings", "quota_known")} == {
        "connections": 2, "usable_bindings": 2, "quota_known": 0}


def test_credential_owner_names_who_holds_the_sign_in():
    store = _store()
    store.upsert_connection({"connection_id": "opencode-session", "name": "OpenCode", "provider": "opencode",
                             "base_url": "https://opencode.ai/zen/v1", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_connection({"connection_id": "local", "name": "Local", "provider": "openai-compatible",
                             "base_url": "http://127.0.0.1:11434/v1", "auth_method": "none", "enabled": True})
    owners = {cid: item["credential_owner"] for cid, item in _by_id(build_resource_view(store, dict)).items()}
    assert owners == {"sense": "nerelan", "claude-account": "claude-code-cli",
                      "opencode-session": "external_cli", "local": "none"}


def test_cli_session_without_a_session_is_not_usable_like_the_resolver_says():
    store = _store()
    store.upsert_connection({"connection_id": "opencode-session", "name": "OpenCode", "provider": "openai",
                             "base_url": "https://opencode.ai/zen/v1", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_binding({"binding_id": "oc-glm", "name": "GLM", "connection_id": "opencode-session",
                          "executor_id": "opencode", "model_id": "glm-5.2", "enabled": True})
    store.refresh_external_session_status({})  # OpenCode reports no signed-in provider
    item = _by_id(build_resource_view(store, dict))["opencode-session"]
    assert item["credential"]["configured"] is False
    assert not any(e["ready"] for e in item["executors"])
    assert item["bindings"][0]["usable"] is False


def test_a_failing_or_malformed_profile_source_only_drops_the_usage_figures():
    def broken():
        raise RuntimeError("task store unavailable")
    view = build_resource_view(_store(), broken)
    sense = _by_id(view)["sense"]
    assert sense["observed_usage"]["status"] == "unavailable" and sense["observed_usage"]["attempts"] == 0
    assert view["summary"]["connections"] == 2
    odd = _by_id(build_resource_view(_store(), lambda: {"sense-glm-5.2": {"attempts": "lots", "ok": -1}}))
    assert odd["sense"]["observed_usage"]["attempts"] == 0 and odd["sense"]["observed_usage"]["status"] == "available"


def test_quota_stays_unknown_and_is_never_derived_from_local_usage():
    view = build_resource_view(_store(), lambda: {"sense-glm-5.2": {"attempts": 50, "ok": 50,
                                                                    "observed_tokens": 10**6}})
    for item in view["resources"]:
        assert (item["quota"]["state"], item["quota"]["provenance"], item["quota"]["windows"]) == (
            "UNKNOWN", "UNAVAILABLE", [])
    assert _by_id(view)["sense"]["quota"]["reason"] == "api_key_has_no_subscription_window"


def test_disabled_connection_or_binding_is_not_usable():
    store = _store()
    store.upsert_binding({"binding_id": "sense-glm-5.2", "name": "GLM", "connection_id": "sense",
                          "executor_id": "opencode", "model_id": "glm-5.2", "enabled": False})
    rows = {row["binding_id"]: row for row in _by_id(build_resource_view(store, dict))["sense"]["bindings"]}
    assert rows["sense-glm-5.2"]["usable"] is False
    store.upsert_connection({"connection_id": "sense", "name": "SenseNova", "provider": "litellm-proxy",
                             "base_url": "https://token.sensenova.cn/v1", "auth_method": "api_key",
                             "enabled": False})
    sense = _by_id(build_resource_view(store, dict))["sense"]
    assert not any(e["ready"] for e in sense["executors"])
    assert not any(row["usable"] for row in sense["bindings"])


def test_view_never_contains_secrets_or_env_references(monkeypatch):
    monkeypatch.setenv("RESOURCE_VIEW_KEY_ENV", SECRET)
    store = _store()
    store.upsert_connection({"connection_id": "env-conn", "name": "Env", "provider": "openai-compatible",
                             "base_url": "https://models.example.test/v1", "auth_method": "api_key",
                             "enabled": True, "api_key_env": "RESOURCE_VIEW_KEY_ENV"})
    text = json.dumps(build_resource_view(store, dict))
    assert SECRET not in text and "RESOURCE_VIEW_KEY_ENV" not in text
    assert _by_id(json.loads(text))["env-conn"]["credential"]["status"] == "environment"


def test_http_route_serves_the_view_with_injected_profiles():
    import threading
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer

    from reverse_agent.model_access.service import _handler_factory

    store = _store()
    handler = _handler_factory(store, live_enabled=False, allowed_origin="http://localhost:5173",
                               usage_profiles=lambda: {"sense-glm-5.2": {"attempts": 2, "ok": 1, "failed": 1,
                                                                         "observed_tokens": 400}})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
        connection.request("GET", "/api/resources")
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    assert response.status == 200 and SECRET not in body
    sense = _by_id(json.loads(body))["sense"]
    assert sense["observed_usage"]["attempts"] == 2 and sense["observed_usage"]["observed_tokens"] == 400


def _ledger(**bindings):
    entry = lambda models, **extra: {"input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "reasoning": 0,
                                     "tasks": 1, "tasks_with_tokens": 1, "cache_write_unknown_tasks": 0,
                                     "models": models, "cli_reported_cost_usd": None, **extra}
    return {binding: entry(models, **{k: sum(m.get(k, 0) for m in models.values()) for k in ("input", "output")})
            for binding, models in bindings.items()}


def test_tokens_and_list_price_cost_per_binding_connection_and_total():
    tokens = _ledger(**{
        # The binding's own model when the run named none; glm-5.2 is priced at Zhipu's list price.
        "sense-glm-5.2": {"": {"input": 1_000_000, "output": 100_000}},
        # An unpriceable model leaves the connection PARTIAL rather than inventing a price.
        "sense-glm-5.2-claude_code": {"mystery-model-9": {"input": 10, "output": 10}},
        # Claude Code named the concrete model behind the "sonnet" alias.
        "claude-sonnet": {"claude-sonnet-5-5": {"input": 1_000_000, "output": 1_000_000}},
    })
    view = build_resource_view(_store(), dict, tokens=lambda: tokens)
    sense, claude = _by_id(view)["sense"], _by_id(view)["claude-account"]
    rows = {row["binding_id"]: row for row in sense["bindings"]}
    assert rows["sense-glm-5.2"]["tokens"]["input"] == 1_000_000
    glm = rows["sense-glm-5.2"]["equivalent_cost"]
    assert glm["state"] == "ESTIMATED" and glm["provenance"] == "ESTIMATED_LIST_PRICE"
    assert glm["usd"] == 1.84 and glm["price_source"] == "https://models.dev/api.json"
    assert rows["sense-glm-5.2-claude_code"]["equivalent_cost"]["state"] == "UNKNOWN"
    assert sense["equivalent_cost"]["state"] == "PARTIAL" and sense["equivalent_cost"]["usd"] == glm["usd"]
    assert "vendor_unknown" in sense["equivalent_cost"]["unpriced"]
    assert claude["bindings"][0]["equivalent_cost"]["usd"] == 12.0
    assert sense["token_usage"]["input"] == 1_000_010
    assert view["summary"]["tokens"]["output"] == 100_010 + 1_000_000
    assert view["summary"]["equivalent_cost"]["state"] == "PARTIAL"


def test_an_unresolved_claude_alias_is_not_priced():
    tokens = _ledger(**{"claude-sonnet": {"": {"input": 1000, "output": 1000}}})  # model "sonnet"
    cost = _by_id(build_resource_view(_store(), dict, tokens=lambda: tokens))["claude-account"]["bindings"][0]
    assert cost["equivalent_cost"]["state"] == "UNKNOWN" and cost["equivalent_cost"]["usd"] is None
    assert cost["equivalent_cost"]["unpriced"] == ["model_unresolved"]


def test_subscription_quota_is_shown_only_on_its_own_account():
    snapshot = {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI", "source": "claude_rate_limit_event",
                "observed_at": "2026-10-14T05:00:00Z",
                "windows": [{"window": "five_hour", "used_percent": 40.0, "resets_at": "2026-10-14T09:00:00Z",
                             "window_minutes": None, "status": "allowed", "reset_passed": False}]}
    view = build_resource_view(_store(), dict, quotas=lambda: {"claude-code": snapshot})
    assert _by_id(view)["claude-account"]["quota"] == snapshot
    assert _by_id(view)["sense"]["quota"]["state"] == "UNKNOWN"  # the API key shares no subscription window
    assert view["summary"]["quota_known"] == 1


def test_failing_token_or_quota_sources_leave_the_view_intact():
    def broken():
        raise OSError("unreadable")
    view = build_resource_view(_store(), dict, tokens=broken, quotas=broken)
    assert view["summary"]["connections"] == 2 and view["summary"]["equivalent_cost"] is None
    assert all(item["quota"]["state"] == "UNKNOWN" for item in view["resources"])


# --- M2 resource view mode tests (#1170) ---

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


def test_legacy_default_is_byte_identical_to_pre_m2_view():
    store = _store()
    legacy_default = build_resource_view(store, dict)
    legacy_explicit = build_resource_view(store, dict, mode="legacy")
    assert "external_sources" not in legacy_default
    assert "view_mode" not in legacy_default
    assert "correlation" not in legacy_default
    assert "magpie_view" not in legacy_default
    assert json.dumps(legacy_default, sort_keys=True) == json.dumps(legacy_explicit, sort_keys=True)


def test_legacy_with_external_snapshot_preserves_resources_unchanged():
    store = _store()
    baseline = build_resource_view(store, dict)
    view = build_resource_view(store, dict, external=_magpie_snapshot)
    assert view["external_sources"]["magpie"]["status"] == "available"
    assert _by_id(view)["sense"]["quota"] == _by_id(baseline)["sense"]["quota"]
    assert _by_id(view)["sense"]["token_usage"] == _by_id(baseline)["sense"]["token_usage"]
    assert view["summary"] == baseline["summary"]
    assert "correlation" not in view and "magpie_view" not in view


def test_hybrid_with_external_includes_correlation_and_leaves_resources_unchanged():
    store = _store()
    baseline = build_resource_view(store, dict)
    view = build_resource_view(store, dict, external=_magpie_snapshot, mode="hybrid")
    assert view["view_mode"] == "hybrid"
    assert view["external_sources"]["magpie"]["status"] == "available"
    assert view["correlation"]["status"] == "available"
    # No resource's quota, token_usage, equivalent_cost or summary changed.
    assert _by_id(view)["sense"]["quota"] == _by_id(baseline)["sense"]["quota"]
    assert _by_id(view)["sense"]["token_usage"] == _by_id(baseline)["sense"]["token_usage"]
    assert _by_id(view)["sense"]["equivalent_cost"] == _by_id(baseline)["sense"]["equivalent_cost"]
    assert view["summary"] == baseline["summary"]
    assert "magpie_view" not in view


def test_hybrid_without_external_shows_disabled_state():
    store = _store()
    view = build_resource_view(store, dict, external=None, mode="hybrid")
    assert view["view_mode"] == "hybrid"
    assert view["external_sources"]["magpie"] == {"status": "disabled", "reason": "magpie_not_enabled"}
    assert view["correlation"]["status"] == "no_external_data"
    assert view["summary"]["connections"] == 2


def test_magpie_primary_leads_with_external_and_keeps_legacy_fallback():
    store = _store()
    view = build_resource_view(store, dict, external=_magpie_snapshot, mode="magpie_primary")
    assert view["view_mode"] == "magpie_primary"
    assert view["magpie_view"]["status"] == "available"
    assert view["magpie_view"]["reason"] is None
    assert view["magpie_view"]["models"][0]["model_id"] == "workbuddy/glm-5.2"
    assert view["magpie_view"]["legacy_fallback"]["connections"] == 2
    # Resources are still present as fallback.
    assert len(view["resources"]) == 2


def test_magpie_primary_without_external_shows_unavailable_with_reason():
    store = _store()
    view = build_resource_view(store, dict, external=None, mode="magpie_primary")
    assert view["magpie_view"]["status"] == "disabled"
    assert view["magpie_view"]["reason"] == "magpie_not_enabled"
    assert view["magpie_view"]["legacy_fallback"]["connections"] == 2


def test_magpie_primary_with_raising_external_shows_unavailable():
    def boom():
        raise RuntimeError("gateway down")
    store = _store()
    view = build_resource_view(store, dict, external=boom, mode="magpie_primary")
    assert view["magpie_view"]["status"] == "unavailable"
    assert view["magpie_view"]["legacy_fallback"]["connections"] == 2
    assert len(view["resources"]) == 2


def test_correlation_accounts_are_always_uncorrelated_without_stable_identity():
    store = _store()
    view = build_resource_view(store, dict, external=_magpie_snapshot, mode="hybrid")
    accounts = view["correlation"]["accounts"]
    assert len(accounts) == 1
    assert accounts[0]["status"] == "uncorrelated"
    assert accounts[0]["reason"] in ("provider_match_ambiguous", "no_stable_account_identifier_on_legacy_side")


def test_correlation_models_exact_match_is_candidate_only_not_verified_identity():
    store = _store()
    view = build_resource_view(store, dict, external=_magpie_snapshot, mode="hybrid")
    models = view["correlation"]["models"]
    # glm-5.2 is bound on the sense connection: exact model_id match.
    matched = [m for m in models if m["external_model_id"] == "workbuddy/glm-5.2"]
    assert matched and matched[0]["status"] == "correlated"
    assert matched[0]["matched_binding_ids"] == ["sense-glm-5.2"]
    # But the account correlation is never trusted as the same account/provider.
    assert all(a["status"] == "uncorrelated" for a in view["correlation"]["accounts"])


def test_external_non_mapping_yields_unavailable_in_non_legacy_mode():
    store = _store()
    view = build_resource_view(store, dict, external=lambda: ["not", "a", "mapping"], mode="hybrid")
    assert view["external_sources"]["magpie"] == {"status": "unavailable"}
    assert view["correlation"]["status"] == "no_external_data"


def test_invalid_mode_raises_value_error():
    import pytest
    with pytest.raises(ValueError, match="unsupported resource view mode"):
        build_resource_view(_store(), dict, mode="bogus")


def test_invalid_mode_http_route_returns_400():
    import threading
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer

    from reverse_agent.model_access.service import _handler_factory

    handler = _handler_factory(_store(), live_enabled=False, allowed_origin="http://localhost:5173")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
        connection.request("GET", "/api/resources?mode=bogus")
        response = connection.getresponse()
        body = response.read().decode("utf-8")
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    assert response.status == 400
    assert "unsupported resource view mode" in body


def test_connection_binding_equality_preserved_across_mode_switch_and_rollback():
    store = _store()
    profiles = {"sense-glm-5.2-claude_code": {"attempts": 3, "ok": 3, "failed": 0, "success_rate": 1.0,
                                              "median_ok_seconds": 44, "median_ok_tokens": 3000,
                                              "observed_tokens": 9000, "failure_kinds": {"x": 1}}}
    legacy = build_resource_view(store, lambda: profiles, mode="legacy")
    hybrid = build_resource_view(store, lambda: profiles, external=_magpie_snapshot, mode="hybrid")
    primary = build_resource_view(store, lambda: profiles, external=_magpie_snapshot, mode="magpie_primary")
    rolled_back = build_resource_view(store, lambda: profiles, mode="legacy")

    # Connection-level fields are identical across all modes.
    for cid in ("sense", "claude-account"):
        for view in (hybrid, primary, rolled_back):
            assert _by_id(view)[cid]["credential"] == _by_id(legacy)[cid]["credential"]
            assert _by_id(view)[cid]["credential_owner"] == _by_id(legacy)[cid]["credential_owner"]
            assert _by_id(view)[cid]["enabled"] == _by_id(legacy)[cid]["enabled"]
            assert _by_id(view)[cid]["equivalent_cost"] == _by_id(legacy)[cid]["equivalent_cost"]
            assert _by_id(view)[cid]["token_usage"] == _by_id(legacy)[cid]["token_usage"]
            assert _by_id(view)[cid]["quota"] == _by_id(legacy)[cid]["quota"]

    # Binding-level fields are identical across all modes.
    for view in (hybrid, primary, rolled_back):
        sense_bindings = {b["binding_id"]: b for b in _by_id(view)["sense"]["bindings"]}
        legacy_sense = {b["binding_id"]: b for b in _by_id(legacy)["sense"]["bindings"]}
        for bid in legacy_sense:
            for key in ("model_id", "executor_id", "enabled", "usable", "observed", "tokens", "equivalent_cost"):
                assert sense_bindings[bid][key] == legacy_sense[bid][key]

    # Summary is identical across all modes.
    assert hybrid["summary"] == legacy["summary"]
    assert primary["summary"] == legacy["summary"]
    assert rolled_back["summary"] == legacy["summary"]
