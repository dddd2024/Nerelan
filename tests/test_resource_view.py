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
    assert view["summary"] == {"connections": 2, "usable_bindings": 2, "quota_known": 0}


def test_quota_stays_unknown_and_is_never_derived_from_local_usage():
    view = build_resource_view(_store(), lambda: {"sense-glm-5.2": {"attempts": 50, "ok": 50,
                                                                    "observed_tokens": 10**6}})
    for item in view["resources"]:
        assert item["quota"] == {"state": "UNKNOWN", "provenance": "UNAVAILABLE",
                                 "reason": "no_official_quota_source"}


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
