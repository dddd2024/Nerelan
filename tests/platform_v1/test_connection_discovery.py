"""One Connection, every model: discovery and bulk binding (provider-free)."""
from __future__ import annotations

import json
from typing import Any

import pytest

from reverse_agent.model_access.service import discover_connection_models
from reverse_agent.model_access.store import ModelProfileStore


def _connection(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "connection_id": "sense-api", "name": "SenseNova API", "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1", "auth_method": "api_key", "enabled": True,
        "api_key": "connection-master-key",
    }
    payload.update(overrides)
    return payload


def _listing(*ids: str) -> bytes:
    return json.dumps({"data": [{"id": model_id} for model_id in ids]}).encode()


def test_discovery_lists_models_server_side_and_marks_bound_ones():
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    store.upsert_binding({"binding_id": "glm", "name": "GLM", "executor_id": "opencode",
                          "connection_id": "sense-api", "model_id": "glm-5.2", "enabled": True})
    calls = []

    def transport(url, headers, timeout):
        calls.append((url, headers))
        return 200, _listing("glm-5.2", "kimi-k3", "bad id with spaces", "glm-5.2")

    result = discover_connection_models(store=store, connection_id="sense-api", live_enabled=True,
                                        transport=transport)
    assert result["status"] == "discovered"
    assert result["models"] == ["glm-5.2", "kimi-k3"]
    assert result["bound"] == {"glm-5.2": [{"binding_id": "glm", "executor_id": "opencode"}]}
    assert calls == [("https://models.example.test/v1/models",
                      {"Accept": "application/json", "Authorization": "Bearer connection-master-key"})]
    assert "connection-master-key" not in json.dumps(result)


@pytest.mark.parametrize("live,body,status", [
    (False, _listing("x"), "live_probe_disabled"),
    (True, b"not json", "invalid_upstream_response"),
    (True, b'{"object":"list"}', "invalid_upstream_response"),
])
def test_discovery_fails_closed(live, body, status):
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    result = discover_connection_models(store=store, connection_id="sense-api", live_enabled=live,
                                        transport=lambda url, headers, timeout: (200, body))
    assert (result["ok"], result["status"], result["models"]) == (False, status, [])


def test_unknown_or_disabled_connection():
    store = ModelProfileStore()
    assert discover_connection_models(store=store, connection_id="nope", live_enabled=True)["status"] == "not_found"
    store.upsert_connection(_connection(enabled=False))
    assert discover_connection_models(store=store, connection_id="sense-api", live_enabled=True)["status"] == "disabled"


def test_bind_all_creates_once_and_reuses_existing():
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    first = store.bind_connection_models("sense-api", ["glm-5.2", "kimi-k3", "glm-5.2"], "opencode")
    assert first["reused"] == [] and len(first["created"]) == 2
    bindings = {b["binding_id"]: b for b in store.list_bindings_public()}
    assert {bindings[b]["model_id"] for b in first["created"]} == {"glm-5.2", "kimi-k3"}
    assert all(bindings[b]["enabled"] and bindings[b]["executor_id"] == "opencode" for b in first["created"])
    again = store.bind_connection_models("sense-api", ["kimi-k3", "deepseek-v4"], "opencode")
    assert again["reused"] == [b for b in first["created"] if bindings[b]["model_id"] == "kimi-k3"]
    assert len(again["created"]) == 1


@pytest.mark.parametrize("model_ids,executor,error", [
    ([], "opencode", "bind_models_model_ids_invalid"),
    ("glm", "opencode", "bind_models_model_ids_invalid"),
    (["glm"], "", "bind_models_executor_required"),
])
def test_bind_all_validates_input(model_ids, executor, error):
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    with pytest.raises(ValueError, match=error):
        store.bind_connection_models("sense-api", model_ids, executor)


def test_bind_all_keeps_native_connection_rules():
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    with pytest.raises(ValueError):
        store.bind_connection_models("sense-api", ["sonnet"], "claude_code")  # API key cannot feed a native CLI


def test_anthropic_connections_list_models_under_v1():
    store = ModelProfileStore()
    store.upsert_connection(_connection(connection_id="sense-anthropic", provider="anthropic-compatible",
                                        base_url="https://token.sensenova.cn"))
    calls = []

    def transport(url, headers, timeout):
        calls.append(url)
        return 200, _listing("glm-5.2")

    result = discover_connection_models(store=store, connection_id="sense-anthropic", live_enabled=True,
                                        transport=transport)
    assert calls == ["https://token.sensenova.cn/v1/models"] and result["models"] == ["glm-5.2"]


def test_one_key_binds_every_compatible_executor_automatically():
    store = ModelProfileStore()
    store.upsert_connection(_connection(connection_id="sense", provider="litellm-proxy",
                                        base_url="https://token.sensenova.cn/v1"))
    connection = store.get_connection_public("sense")
    assert connection["protocol_family"] == "openai"
    assert connection["anthropic_base_url"] == "https://token.sensenova.cn"  # known host: filled in automatically
    assert store.compatible_executors("sense") == ["opencode", "claude_code"]
    result = store.bind_connection_models("sense", ["glm-5.2"], "auto")
    assert result["executors"] == ["opencode", "claude_code"]
    assert sorted(result["created"]) == ["sense-glm-5.2", "sense-glm-5.2-claude_code"]
    snapshot = store.resolve_execution_snapshot("sense-glm-5.2-claude_code")
    assert (snapshot.base_url, snapshot.protocol_family) == ("https://token.sensenova.cn", "anthropic")
    opencode = store.resolve_execution_snapshot("sense-glm-5.2")
    assert (opencode.base_url, opencode.protocol_family) == ("https://token.sensenova.cn/v1", "openai")


def test_unknown_hosts_get_no_implicit_anthropic_endpoint_but_accept_an_explicit_one():
    store = ModelProfileStore()
    store.upsert_connection(_connection())
    assert store.get_connection_public("sense-api")["anthropic_base_url"] is None
    assert store.compatible_executors("sense-api") == ["opencode"]
    store.upsert_connection(_connection(anthropic_base_url="https://models.example.test/anthropic"))
    assert store.compatible_executors("sense-api") == ["opencode", "claude_code"]
