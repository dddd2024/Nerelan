from __future__ import annotations

from dataclasses import fields
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import threading
from typing import Any

import pytest

from reverse_agent.model_access.contracts import (
    Binding,
    Connection,
    ExecutorDescriptor,
)
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.model_access.service import _handler_factory


def connection_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "connection_id": "sense-api",
        "name": "SenseNova API",
        "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def binding_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "binding_id": "coding-fast",
        "name": "Fast coding",
        "executor_id": "opencode",
        "connection_id": "sense-api",
        "model_id": "sense-coding-fast",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def legacy_profile_payload() -> dict[str, Any]:
    return {
        "id": "legacy-profile",
        "name": "Legacy profile",
        "provider": "litellm-proxy",
        "base_url": "http://localhost:4000/v1",
        "model_id": "legacy-model",
        "executor": "openhands",
        "enabled": True,
        "is_default": True,
    }


def test_connection_executor_and_binding_are_structurally_independent() -> None:
    connection_fields = {field.name for field in fields(Connection)}
    executor_fields = {field.name for field in fields(ExecutorDescriptor)}
    binding_fields = {field.name for field in fields(Binding)}

    assert {"connection_id", "provider", "auth_method"} <= connection_fields
    assert "executor_id" not in connection_fields
    assert {"executor_id", "capabilities"} <= executor_fields
    assert "connection_id" not in executor_fields
    assert binding_fields == {
        "binding_id",
        "name",
        "executor_id",
        "connection_id",
        "model_id",
        "enabled",
    }


def test_executor_registry_exposes_only_proven_operational_executor() -> None:
    store = ModelProfileStore()

    assert store.list_executors_public() == [
        {
            "executor_id": "opencode",
            "name": "OpenCode",
            "operational": True,
            "capabilities": ["model_selection", "workspace_execution"],
        }
    ]


def test_fake_api_key_is_process_local_and_public_connection_is_sanitized() -> None:
    store = ModelProfileStore()
    raw_key = "fake-api-key-not-real"

    public = store.upsert_connection(connection_payload(api_key=raw_key))

    assert public["credential_configured"] is True
    assert public["secret_status"] == "session"
    assert public["external_session_status"] == "not_applicable"
    assert raw_key not in json.dumps(public)
    assert raw_key not in json.dumps(store.list_connections_public())
    assert store.resolve_connection_secret("sense-api") == raw_key


def test_environment_secret_reference_exposes_status_not_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONNECTION_BINDING_FAKE_KEY", "fake-env-secret")
    store = ModelProfileStore()

    public = store.upsert_connection(
        connection_payload(api_key_env="CONNECTION_BINDING_FAKE_KEY")
    )

    serialized = json.dumps(public)
    assert public["credential_configured"] is True
    assert public["secret_status"] == "environment"
    assert "CONNECTION_BINDING_FAKE_KEY" not in serialized
    assert "fake-env-secret" not in serialized
    assert store.resolve_connection_secret("sense-api") == "fake-env-secret"


@pytest.mark.parametrize("auth_method", ["account_login", "external_cli_session"])
def test_external_auth_methods_represent_status_without_accepting_token(
    auth_method: str,
) -> None:
    store = ModelProfileStore()

    public = store.upsert_connection(
        connection_payload(
            connection_id=f"{auth_method}-connection",
            auth_method=auth_method,
        )
    )

    assert public["credential_configured"] is False
    assert public["external_session_status"] == "executor_managed"
    assert public["secret_status"] == "not_applicable"
    with pytest.raises(ValueError, match="external_session_status"):
        store.upsert_connection(
            connection_payload(
                connection_id=f"{auth_method}-derived-status",
                auth_method=auth_method,
                external_session_status="available",
            )
        )
    with pytest.raises(ValueError, match="externalSessionStatus"):
        store.upsert_connection(
            connection_payload(
                connection_id=f"{auth_method}-derived-status-camel",
                auth_method=auth_method,
                externalSessionStatus="available",
            )
        )
    with pytest.raises(ValueError, match="raw session credentials"):
        store.upsert_connection(
            connection_payload(
                connection_id=f"{auth_method}-with-token",
                auth_method=auth_method,
                token="fake-token-not-real",
            )
        )


def test_changing_auth_method_requires_explicit_clear_for_configured_secret() -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload(api_key="fake-key-not-real"))

    with pytest.raises(ValueError, match="clear_secret"):
        store.upsert_connection(connection_payload(auth_method="account_login"))

    public = store.upsert_connection(
        connection_payload(auth_method="account_login", clear_secret=True)
    )

    assert public["credential_configured"] is False
    assert public["secret_status"] == "not_applicable"
    assert public["external_session_status"] == "executor_managed"
    assert store.resolve_connection_secret("sense-api") is None


def test_binding_contains_references_and_no_secret_fields() -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload())

    public = store.upsert_binding(binding_payload())

    assert public == binding_payload()
    binding_fields = {field.name.lower() for field in fields(Binding)}
    assert not binding_fields & {"secret", "password", "token", "key", "api_key"}
    with pytest.raises(ValueError, match="credentials"):
        store.upsert_binding(binding_payload(api_key="fake-key-not-real"))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"connection_id": "missing"}, "unknown connection_id"),
        ({"executor_id": "missing"}, "unknown executor_id"),
    ],
)
def test_binding_unknown_references_fail_closed(
    overrides: dict[str, str],
    message: str,
) -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload())

    with pytest.raises(ValueError, match=message):
        store.upsert_binding(binding_payload(**overrides))


def test_referenced_connection_delete_fails_closed_until_binding_deleted() -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    with pytest.raises(ValueError, match="referenced by binding"):
        store.delete_connection("sense-api")

    store.delete_binding("coding-fast")
    store.delete_connection("sense-api")
    assert store.list_connections_public() == []


def test_legacy_model_profile_compatibility_remains_in_same_store() -> None:
    store = ModelProfileStore()
    legacy = store.upsert(legacy_profile_payload())
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    assert store.list_public() == [legacy]
    assert store.get_profile("legacy-profile").executor == "openhands"
    assert store.get_connection_public("sense-api")["provider"] == "openai-compatible"
    assert store.get_binding_public("coding-fast")["executor_id"] == "opencode"


@pytest.fixture()
def connection_service() -> tuple[int, ModelProfileStore]:
    store = ModelProfileStore()
    handler = _handler_factory(
        store,
        live_enabled=False,
        allowed_origin="http://localhost:5173",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield int(server.server_address[1]), store
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def api_request(
    port: int,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"Content-Length": str(len(body))}
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    connection.close()
    return response.status, response_body


def test_connection_and_executor_endpoints_return_sanitized_structures(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, _store = connection_service
    raw_key = "fake-http-key-not-real"

    status, created = api_request(
        port,
        "PUT",
        "/api/connections/sense-api",
        connection_payload(api_key=raw_key),
    )
    assert status == 200
    assert created["connection_id"] == "sense-api"
    assert created["credential_configured"] is True
    assert created["secret_status"] == "session"
    assert raw_key not in json.dumps(created)

    status, listed = api_request(port, "GET", "/api/connections")
    assert status == 200
    assert listed == [created]
    status, fetched = api_request(port, "GET", "/api/connections/sense-api")
    assert status == 200
    assert fetched == created

    status, executors = api_request(port, "GET", "/api/executors")
    assert status == 200
    assert [executor["executor_id"] for executor in executors] == ["opencode"]
    assert "openhands" not in json.dumps(executors).lower()
    assert "codex" not in json.dumps(executors).lower()


def test_binding_endpoints_validate_references_and_never_accept_credentials(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload())

    status, created = api_request(
        port,
        "PUT",
        "/api/bindings/coding-fast",
        binding_payload(),
    )
    assert status == 200
    assert created == binding_payload()
    status, listed = api_request(port, "GET", "/api/bindings")
    assert status == 200
    assert listed == [created]
    status, fetched = api_request(port, "GET", "/api/bindings/coding-fast")
    assert status == 200
    assert fetched == created

    status, error = api_request(
        port,
        "PUT",
        "/api/bindings/unknown-connection",
        binding_payload(binding_id="unknown-connection", connection_id="missing"),
    )
    assert status == 400
    assert "unknown connection_id" in error["error"]
    status, error = api_request(
        port,
        "PUT",
        "/api/bindings/unknown-executor",
        binding_payload(binding_id="unknown-executor", executor_id="missing"),
    )
    assert status == 400
    assert "unknown executor_id" in error["error"]
    status, error = api_request(
        port,
        "PUT",
        "/api/bindings/with-secret",
        binding_payload(binding_id="with-secret", token="fake-token-not-real"),
    )
    assert status == 400
    assert "credentials" in error["error"]
    assert store.list_bindings_public() == [created]


def test_connection_delete_endpoint_fails_closed_while_referenced(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    status, error = api_request(port, "DELETE", "/api/connections/sense-api")
    assert status == 400
    assert "referenced by binding" in error["error"]

    assert api_request(port, "DELETE", "/api/bindings/coding-fast") == (
        200,
        {"deleted": True},
    )
    assert api_request(port, "DELETE", "/api/connections/sense-api") == (
        200,
        {"deleted": True},
    )


def test_legacy_model_profile_http_contract_remains_compatible(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, _store = connection_service

    status, created = api_request(
        port,
        "PUT",
        "/api/model-profiles/legacy-profile",
        legacy_profile_payload(),
    )
    assert status == 200
    assert created["id"] == "legacy-profile"
    status, listed = api_request(port, "GET", "/api/model-profiles")
    assert status == 200
    assert listed == [created]


# ---------------------------------------------------------------------------
# ISSUE183 R2 V1 - Saved Connection probe HTTP contract
# ---------------------------------------------------------------------------

def test_connection_test_endpoint_rejects_non_empty_body(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload(api_key="http-test-key"))

    status, error = api_request(
        port,
        "POST",
        "/api/connections/sense-api/test",
        {"api_key": "injected-api-key"},
    )
    assert status == 400
    assert "configuration overrides" in error["error"]


def test_connection_test_endpoint_rejects_generic_non_empty_body(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload(api_key="http-test-key"))

    status, error = api_request(
        port,
        "POST",
        "/api/connections/sense-api/test",
        {"custom": "value"},
    )
    assert status == 400
    assert "empty JSON object" in error["error"]


def test_connection_test_endpoint_disabled_no_probe_body(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload(api_key="http-test-key", enabled=False))

    status, result = api_request(
        port,
        "POST",
        "/api/connections/sense-api/test",
        None,
    )
    assert status == 200
    assert result["ok"] is False
    assert result["status"] == "disabled"
    assert "http-test-key" not in json.dumps(result)


def test_connection_test_endpoint_missing_secret_no_probe(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload())

    status, result = api_request(
        port,
        "POST",
        "/api/connections/sense-api/test",
        None,
    )
    assert status == 200
    assert result["ok"] is False
    assert result["status"] == "credential_missing"


def test_connection_test_endpoint_live_disabled_fails_closed(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(connection_payload(api_key="http-test-key"))

    status, result = api_request(
        port,
        "POST",
        "/api/connections/sense-api/test",
        None,
    )
    assert status == 200
    assert result["ok"] is False
    assert result["status"] == "live_probe_disabled"
    assert "http-test-key" not in json.dumps(result)


def test_connection_test_endpoint_unsupported_auth_no_probe(
    connection_service: tuple[int, ModelProfileStore],
) -> None:
    port, store = connection_service
    store.upsert_connection(
        connection_payload(
            connection_id="account-login-conn",
            auth_method="account_login",
        )
    )

    status, result = api_request(
        port,
        "POST",
        "/api/connections/account-login-conn/test",
        None,
    )
    assert status == 200
    assert result["ok"] is False
    assert result["status"] == "unsupported_auth_method"


# ===================================================================
# ISSUE210 R2 V1 — Durable sanitized product setup persistence
# ===================================================================

import json as _json_mod
import os as _os_mod
from pathlib import Path as _Path

from reverse_agent.model_access.store import StoreError as _StoreError


def _state_path(tmp_path: _Path, name: str = "state.json") -> str:
    return str(tmp_path / name)


def test_persistence_restores_connection_and_binding_metadata(tmp_path) -> None:
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    fresh = ModelProfileStore(state_path=sp)
    listed = fresh.list_connections_public()
    assert len(listed) == 1
    conn = listed[0]
    assert conn["connection_id"] == "sense-api"
    assert conn["provider"] == "openai-compatible"
    assert conn["base_url"] == "https://models.example.test/v1"
    assert conn["auth_method"] == "api_key"
    assert conn["enabled"] is True

    bindings = fresh.list_bindings_public()
    assert len(bindings) == 1
    b = bindings[0]
    assert b["binding_id"] == "coding-fast"
    assert b["executor_id"] == "opencode"
    assert b["connection_id"] == "sense-api"
    assert b["model_id"] == "sense-coding-fast"
    assert b["enabled"] is True


def test_raw_api_key_never_persisted_and_missing_after_restart(tmp_path) -> None:
    sp = _state_path(tmp_path)
    raw_secret = "RAW-SENTINEL-SECRET-DO-NOT-LEAK"
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload(api_key=raw_secret))

    raw_bytes = _Path(sp).read_bytes()
    assert raw_secret.encode("utf-8") not in raw_bytes
    assert b"RAW-SENTINEL" not in raw_bytes

    fresh = ModelProfileStore(state_path=sp)
    listed = fresh.list_connections_public()
    assert listed[0]["credential_configured"] is False
    assert listed[0]["secret_status"] == "missing"
    assert fresh.resolve_connection_secret("sense-api") is None


def test_api_key_env_only_persists_name_never_value(tmp_path, monkeypatch) -> None:
    sp = _state_path(tmp_path)
    env_name = "TEST_ISSUE210_ENV_KEY"
    env_value = "ENV-SENTINEL-SECRET-VALUE"
    monkeypatch.setenv(env_name, env_value)

    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload(api_key_env=env_name))

    raw_bytes = _Path(sp).read_bytes()
    assert env_name.encode("utf-8") in raw_bytes
    assert env_value.encode("utf-8") not in raw_bytes
    assert b"ENV-SENTINEL" not in raw_bytes

    monkeypatch.setenv(env_name, "FRESH-ENV-VALUE")
    fresh = ModelProfileStore(state_path=sp)
    assert fresh.list_connections_public()[0]["credential_configured"] is True
    assert fresh.list_connections_public()[0]["secret_status"] == "environment"
    assert fresh.resolve_connection_secret("sense-api") == "FRESH-ENV-VALUE"

    monkeypatch.delenv(env_name)
    fresh2 = ModelProfileStore(state_path=sp)
    assert fresh2.list_connections_public()[0]["credential_configured"] is True
    assert fresh2.list_connections_public()[0]["secret_status"] == "missing"
    assert fresh2.resolve_connection_secret("sense-api") is None


def test_binding_metadata_fully_restored_after_restart(tmp_path) -> None:
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload(binding_id="my-binding",
                                          name="My Binding",
                                          model_id="gpt-5",
                                          enabled=False))

    fresh = ModelProfileStore(state_path=sp)
    bindings = fresh.list_bindings_public()
    assert len(bindings) == 1
    b = bindings[0]
    assert b["binding_id"] == "my-binding"
    assert b["name"] == "My Binding"
    assert b["executor_id"] == "opencode"
    assert b["connection_id"] == "sense-api"
    assert b["model_id"] == "gpt-5"
    assert b["enabled"] is False


def test_persistence_fails_closed_on_dangling_binding(tmp_path) -> None:
    doc = {
        "schema_version": 1,
        "connections": [],
        "bindings": [
            {
                "binding_id": "orphan",
                "name": "Orphan",
                "executor_id": "opencode",
                "connection_id": "no-such-conn",
                "model_id": "model-x",
                "enabled": True,
            }
        ],
    }
    sp = _state_path(tmp_path)
    _Path(sp).write_text(_json_mod.dumps(doc), encoding="utf-8")

    with pytest.raises(_StoreError, match="dangling"):
        ModelProfileStore(state_path=sp)


def test_persistence_fails_closed_on_duplicate_ids(tmp_path) -> None:
    doc = {
        "schema_version": 1,
        "connections": [
            {
                "connection_id": "dup",
                "name": "Dup1",
                "provider": "openai-compatible",
                "base_url": "https://a.example.test/v1",
                "auth_method": "none",
                "enabled": True,
            },
            {
                "connection_id": "dup",
                "name": "Dup2",
                "provider": "openai-compatible",
                "base_url": "https://b.example.test/v1",
                "auth_method": "none",
                "enabled": True,
            },
        ],
        "bindings": [],
    }
    sp = _state_path(tmp_path)
    _Path(sp).write_text(_json_mod.dumps(doc), encoding="utf-8")

    with pytest.raises(_StoreError, match="duplicate"):
        ModelProfileStore(state_path=sp)


def test_persistence_fails_closed_on_unknown_schema_version(tmp_path) -> None:
    doc = {
        "schema_version": 999,
        "connections": [],
        "bindings": [],
    }
    sp = _state_path(tmp_path)
    _Path(sp).write_text(_json_mod.dumps(doc), encoding="utf-8")

    with pytest.raises(_StoreError, match="schema_version"):
        ModelProfileStore(state_path=sp)


def test_persistence_fails_closed_on_corrupt_json(tmp_path) -> None:
    sp = _state_path(tmp_path)
    _Path(sp).write_bytes(b"{not valid json at all!!!")

    with pytest.raises(_StoreError):
        ModelProfileStore(state_path=sp)


def test_persistence_fails_closed_on_forbidden_fields_in_file(tmp_path) -> None:
    doc = {
        "schema_version": 1,
        "connections": [
            {
                "connection_id": "sense-api",
                "name": "Leaky",
                "provider": "openai-compatible",
                "base_url": "https://a.example.test/v1",
                "auth_method": "api_key",
                "enabled": True,
                "api_key": "NEVER-PERSIST-THIS",
            }
        ],
        "bindings": [],
    }
    sp = _state_path(tmp_path)
    _Path(sp).write_text(_json_mod.dumps(doc), encoding="utf-8")

    with pytest.raises(_StoreError, match="forbidden"):
        ModelProfileStore(state_path=sp)


def test_atomic_write_interruption_preserves_last_valid_state(tmp_path, monkeypatch) -> None:
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    first_content = _Path(sp).read_bytes()
    assert len(first_content) > 0

    call_count = {"fsync": 0}
    original_fsync = _os_mod.fsync

    def _fsync_interrupt(fd):
        call_count["fsync"] += 1
        raise OSError("simulated disk failure")

    monkeypatch.setattr(_os_mod, "fsync", _fsync_interrupt)

    with pytest.raises(_StoreError, match="persistence"):
        store.upsert_connection(
            connection_payload(connection_id="new-conn", name="New Conn")
        )

    restored = _Path(sp).read_bytes()
    assert restored == first_content

    fresh = ModelProfileStore(state_path=sp)
    listed = fresh.list_connections_public()
    assert len(listed) == 1
    assert listed[0]["connection_id"] == "sense-api"
    assert "new-conn" not in [c["connection_id"] for c in listed]

    monkeypatch.setattr(_os_mod, "fsync", original_fsync)


def test_persistence_failure_rolls_back_memory_mutation(tmp_path, monkeypatch) -> None:
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload())
    store.upsert_binding(binding_payload())

    before_connections = store.list_connections_public()
    before_bindings = store.list_bindings_public()
    assert len(before_connections) == 1
    assert len(before_bindings) == 1

    call_count = {"replace": 0}
    original_replace = _os_mod.replace

    def _replace_interrupt(src, dst):
        call_count["replace"] += 1
        raise OSError("simulated rename failure")

    monkeypatch.setattr(_os_mod, "replace", _replace_interrupt)

    with pytest.raises(_StoreError, match="persistence"):
        store.upsert_connection(
            connection_payload(connection_id="another-conn", name="Another")
        )

    after_connections = store.list_connections_public()
    after_bindings = store.list_bindings_public()
    assert after_connections == before_connections
    assert after_bindings == before_bindings
    assert len(after_connections) == 1
    assert after_connections[0]["connection_id"] == "sense-api"
    assert len(after_bindings) == 1
    assert after_bindings[0]["binding_id"] == "coding-fast"

    monkeypatch.setattr(_os_mod, "replace", original_replace)


def test_process_local_store_still_works_without_state_path(tmp_path) -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload(api_key="local-only-key"))
    store.upsert_binding(binding_payload())

    public = store.list_connections_public()
    assert public[0]["credential_configured"] is True
    assert public[0]["secret_status"] == "session"
    assert store.resolve_connection_secret("sense-api") == "local-only-key"

    bindings = store.list_bindings_public()
    assert len(bindings) == 1

    assert not _Path(str(tmp_path / "state.json")).exists()


# ===================================================================
# ISSUE216 OPENCODE_CREDENTIAL_REUSE_ADAPTER_V3 REGRESSIONS
# ===================================================================

def test_external_session_becomes_available_from_sanitized_auth_metadata() -> None:
    store = ModelProfileStore()
    store.upsert_connection(
        connection_payload(
            connection_id="external-cli-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("external-cli-conn")["external_session_status"] == "executor_managed"
    refreshed = store.refresh_external_session_status({"sensetime": "api"})
    assert refreshed == 1
    assert store.get_connection_public("external-cli-conn")["external_session_status"] == "available"


def test_external_session_missing_when_provider_not_in_auth_metadata() -> None:
    store = ModelProfileStore()
    store.upsert_connection(
        connection_payload(
            connection_id="external-cli-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("external-cli-conn")["external_session_status"] == "executor_managed"
    store.refresh_external_session_status({"other-provider": "api"})
    assert store.get_connection_public("external-cli-conn")["external_session_status"] == "missing"


def test_executor_managed_external_session_survives_authority_unchanged_upsert(tmp_path) -> None:
    """Authority-unchanged external auth upsert preserves existing runtime status."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    refresh = store.refresh_external_session_status({"sensetime": "api"})
    assert refresh == 1
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "available"

    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "available"


def test_available_external_session_survives_authority_unchanged_upsert(tmp_path) -> None:
    """After refresh sets external-session status to 'available', a name-only
    upsert with no authority-bearing change must preserve 'available'."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    store.refresh_external_session_status({"sensetime": "api"})
    before = store.get_connection_public("persisted-external-conn")["external_session_status"]
    assert before == "available"

    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
            name="Renamed Connection",
        ),
    )
    after = store.get_connection_public("persisted-external-conn")["external_session_status"]
    assert after == "available"


def test_missing_external_session_survives_authority_unchanged_upsert(tmp_path) -> None:
    """After refresh sets external-session status to 'missing', a name-only
    upsert with no authority-bearing change must preserve 'missing'."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    store.refresh_external_session_status({"other-provider": "api"})
    before = store.get_connection_public("persisted-external-conn")["external_session_status"]
    assert before == "missing"

    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
            name="Renamed Connection",
        ),
    )
    after = store.get_connection_public("persisted-external-conn")["external_session_status"]
    assert after == "missing"


def test_executor_managed_external_session_resets_when_authority_changes(tmp_path) -> None:
    """Authority-bearing field change resets external-session status to executor_managed."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    store.refresh_external_session_status({"sensetime": "api"})
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "available"

    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime-v2",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"
    assert store.get_connection_public("persisted-external-conn")["provider"] == "sensetime-v2"


def test_executor_managed_external_session_resets_from_api_key_to_external(tmp_path) -> None:
    """Switching an existing api_key connection to external auth requires explicit clear."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="sense-api",
            auth_method="api_key",
            api_key="fake-key-not-real",
        ),
    )
    assert store.get_connection_public("sense-api")["external_session_status"] == "not_applicable"

    with pytest.raises(ValueError, match="clear_secret"):
        store.upsert_connection(
            connection_payload(
                connection_id="sense-api",
                auth_method="external_cli_session",
                provider="sensetime",
            ),
        )

    store.upsert_connection(
        connection_payload(
            connection_id="sense-api",
            auth_method="external_cli_session",
            provider="sensetime",
            clear_secret=True,
        ),
    )
    assert store.get_connection_public("sense-api")["credential_configured"] is False
    assert store.get_connection_public("sense-api")["external_session_status"] == "executor_managed"
    assert store.get_connection_public("sense-api")["secret_status"] == "not_applicable"
    assert store.resolve_connection_secret("sense-api") is None


def test_executor_managed_external_session_resets_from_external_to_api_key(tmp_path) -> None:
    """Switching an external connection back to api_key stays not_applicable."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="api_key",
            api_key="fake-key-not-real",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["credential_configured"] is True
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "not_applicable"
    assert store.get_connection_public("persisted-external-conn")["secret_status"] == "session"


def test_executor_managed_external_session_reload_from_sanitized_persisted_state(tmp_path) -> None:
    """Reloaded external-session Connection starts executor_managed; persisted JSON
    must never contain the runtime status or the executor_managed sentinel."""
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(
        connection_payload(
            connection_id="persisted-external-conn",
            auth_method="external_cli_session",
            provider="sensetime",
        ),
    )
    assert store.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    raw_bytes = _Path(sp).read_bytes()
    assert b"external_session_status" not in raw_bytes
    assert b"externalSessionStatus" not in raw_bytes
    assert b"executor_managed" not in raw_bytes

    fresh = ModelProfileStore(state_path=sp)
    listed = fresh.list_connections_public()
    assert listed[0]["external_session_status"] == "executor_managed"

    fresh.refresh_external_session_status({"sensetime": "api"})
    assert fresh.get_connection_public("persisted-external-conn")["external_session_status"] == "available"

    fresh_second = ModelProfileStore(state_path=sp)
    assert fresh_second.get_connection_public("persisted-external-conn")["external_session_status"] == "executor_managed"

    fresh_second.refresh_external_session_status({})
    assert fresh_second.get_connection_public("persisted-external-conn")["external_session_status"] == "missing"


def test_refresh_external_session_status_does_not_mutate_api_key_status(tmp_path) -> None:
    sp = _state_path(tmp_path)
    store = ModelProfileStore(state_path=sp)
    store.upsert_connection(connection_payload(api_key="fresh-in-memory-key"))

    store.refresh_external_session_status({"sensetime": "api"})
    conn = store.get_connection_public("sense-api")
    assert conn["credential_configured"] is True
    assert conn["external_session_status"] == "not_applicable"
    assert conn["secret_status"] == "session"
    assert store.resolve_connection_secret("sense-api") == "fresh-in-memory-key"

    raw_bytes = _Path(sp).read_bytes()
    assert b"external_session_status" not in raw_bytes
