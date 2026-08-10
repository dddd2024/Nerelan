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
            external_session_status="available",
        )
    )

    assert public["external_session_status"] == "available"
    assert public["secret_status"] == "not_applicable"
    with pytest.raises(ValueError, match="raw session credentials"):
        store.upsert_connection(
            connection_payload(
                connection_id=f"{auth_method}-with-token",
                auth_method=auth_method,
                token="fake-token-not-real",
            )
        )


def test_changing_auth_method_resets_incompatible_secret_status() -> None:
    store = ModelProfileStore()
    store.upsert_connection(connection_payload(api_key="fake-key-not-real"))

    public = store.upsert_connection(
        connection_payload(auth_method="account_login")
    )

    assert public["secret_status"] == "not_applicable"
    assert public["external_session_status"] == "missing"
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
