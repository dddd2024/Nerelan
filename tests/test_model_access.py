from __future__ import annotations

import json
import socket
import threading
from http.client import HTTPConnection
from typing import Any, Callable

import pytest

from reverse_agent.model_access.contracts import ModelProfile, ProbeResult
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.model_access.service import (
    _handler_factory,
    probe_openai_compatible,
    validate_bind_host,
)


def profile_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": "coding-default",
        "name": "Default coding model",
        "provider": "litellm-proxy",
        "base_url": "http://localhost:4000/v1",
        "model_id": "coding-default",
        "executor": "openhands",
        "enabled": True,
        "is_default": True,
    }
    payload.update(overrides)
    return payload


def test_profile_validation_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        ModelProfile.from_mapping(
            profile_payload(base_url="https://user:pass@example.com/v1")
        )


def test_store_masks_api_keys_and_keeps_one_default() -> None:
    store = ModelProfileStore()
    first = store.upsert(profile_payload(api_key="secret-alpha"))
    second = store.upsert(
        profile_payload(
            id="review",
            name="Review model",
            model_id="review-strong",
            api_key="secret-beta",
            is_default=True,
        )
    )

    public = store.list_public()
    serialized = json.dumps(public)
    assert "secret-alpha" not in serialized
    assert "secret-beta" not in serialized
    assert first["secret_status"] == "session"
    assert second["secret_status"] == "session"
    assert [item["id"] for item in public if item["is_default"]] == ["review"]


def test_deleting_default_promotes_an_enabled_profile() -> None:
    store = ModelProfileStore()
    store.upsert(profile_payload())
    store.upsert(
        profile_payload(
            id="review",
            name="Review model",
            model_id="review-strong",
            is_default=False,
        )
    )

    store.delete("coding-default")

    assert store.list_public() == [
        {
            "id": "review",
            "name": "Review model",
            "provider": "litellm-proxy",
            "base_url": "http://localhost:4000/v1",
            "model_id": "review-strong",
            "executor": "openhands",
            "enabled": True,
            "is_default": True,
            "secret_status": "missing",
        }
    ]


def test_environment_secret_is_resolved_without_exposure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_ACCESS_TEST_KEY", "environment-secret")
    store = ModelProfileStore()
    profile = store.upsert(
        profile_payload(api_key_env="MODEL_ACCESS_TEST_KEY", api_key=None)
    )

    assert profile["secret_status"] == "environment"
    assert store.resolve_secret("coding-default") == "environment-secret"
    assert "environment-secret" not in json.dumps(store.list_public())


def test_probe_is_blocked_without_explicit_live_opt_in() -> None:
    profile = ModelProfile.from_mapping(profile_payload())

    result = probe_openai_compatible(
        profile=profile,
        api_key="secret",
        live_enabled=False,
    )

    assert result == ProbeResult(
        ok=False,
        status="live_probe_disabled",
        message="Live model probes require REVERSE_AGENT_MODEL_CONTROL_LIVE=1",
        latency_ms=None,
    )


def test_probe_uses_injected_transport_and_never_returns_secret() -> None:
    calls: list[tuple[str, dict[str, str], float]] = []

    def transport(
        url: str, headers: dict[str, str], timeout: float
    ) -> tuple[int, bytes]:
        calls.append((url, headers, timeout))
        return 200, b'{"data":[{"id":"coding-default"}]}'

    result = probe_openai_compatible(
        profile=ModelProfile.from_mapping(profile_payload()),
        api_key="probe-secret",
        live_enabled=True,
        transport=transport,
    )

    assert result.ok is True
    assert result.status == "connected"
    assert "probe-secret" not in result.message
    assert calls == [
        (
            "http://localhost:4000/v1/models",
            {
                "Accept": "application/json",
                "Authorization": "Bearer probe-secret",
            },
            10.0,
        )
    ]


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_control_service_accepts_only_loopback_hosts(host: str) -> None:
    assert validate_bind_host(host) == host


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.20", "model-host.local"])
def test_control_service_rejects_non_loopback_hosts(host: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        validate_bind_host(host)


# ---------------------------------------------------------------------------
# MA-ORIGIN-001: HTTP boundary Origin-gate tests
# ---------------------------------------------------------------------------

_ALLOWED_ORIGIN = "http://localhost:5173"
_FOREIGN_ORIGIN = "https://evil.example.com"


@pytest.fixture()
def model_service_port(monkeypatch: pytest.MonkeyPatch) -> int:
    """Bind to a free loopback port and return it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_HOST", "127.0.0.1")
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_PORT", str(port))
    monkeypatch.setenv("REVERSE_AGENT_MODEL_CONTROL_ORIGIN", _ALLOWED_ORIGIN)
    monkeypatch.delenv("REVERSE_AGENT_MODEL_CONTROL_LIVE", raising=False)
    return port


@pytest.fixture()
def model_service_server(model_service_port: int) -> None:
    """Start the model-control service in a background daemon thread."""
    from http.server import ThreadingHTTPServer  # noqa: PLC0415
    from reverse_agent.model_access.service import store_from_environment  # noqa: PLC0415

    store = ModelProfileStore()
    store.upsert(profile_payload())
    handler_cls = _handler_factory(
        store,
        live_enabled=False,
        allowed_origin=_ALLOWED_ORIGIN,
    )
    server = ThreadingHTTPServer(("127.0.0.1", model_service_port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield
    server.shutdown()


def _request(
    model_service_port: int,
    method: str,
    path: str,
    origin: str | None = None,
    body: bytes | None = None,
) -> HTTPConnection:
    conn = HTTPConnection("127.0.0.1", model_service_port, timeout=3)
    headers: dict[str, str] = {}
    if origin is not None:
        headers["Origin"] = origin
    if body is not None:
        headers["Content-Length"] = str(len(body))
    conn.request(method, path, body=body, headers=headers)
    return conn


def _get_response(
    model_service_port: int,
    method: str = "GET",
    path: str = "/api/model-profiles",
    origin: str | None = None,
    body: bytes | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    conn = _request(model_service_port, method, path, origin=origin, body=body)
    resp = conn.getresponse()
    data = resp.read()
    headers = {k.lower(): v for k, v in resp.getheaders()}
    conn.close()
    return resp.status, data, headers


class TestOriginGateHttpBoundary:
    """Verify the server-side Origin gate at the HTTP boundary."""

    def test_allowed_origin_returns_acao(self, model_service_port: int, model_service_server: None) -> None:  # noqa: ANN401
        status, data, headers = _get_response(
            model_service_port,
            method="GET",
            origin=_ALLOWED_ORIGIN,
        )
        assert status == 200
        assert "access-control-allow-origin" in headers
        assert headers["access-control-allow-origin"] == _ALLOWED_ORIGIN
        profiles = json.loads(data)
        assert len(profiles) == 1

    def test_no_origin_allowed_as_trusted_cli(
        self, model_service_port: int, model_service_server: None  # noqa: ANN401
    ) -> None:
        status, data, headers = _get_response(
            model_service_port,
            method="GET",
            origin=None,
        )
        assert status == 200
        assert "access-control-allow-origin" not in headers
        profiles = json.loads(data)
        assert len(profiles) == 1

    def test_foreign_origin_get_rejected_403(
        self, model_service_port: int, model_service_server: None  # noqa: ANN401
    ) -> None:
        status, data, headers = _get_response(
            model_service_port,
            method="GET",
            origin=_FOREIGN_ORIGIN,
        )
        assert status == 403
        body = data.decode("utf-8")
        assert json.loads(body) == {"error": "forbidden"}
        assert "secret" not in body

    def test_foreign_origin_state_change_rejected_and_store_unchanged(
        self, model_service_port: int, model_service_server: None  # noqa: ANN401
    ) -> None:
        payload = json.dumps(
            profile_payload(
                id="injected",
                name="Injected",
                model_id="injected-model",
                api_key="secret-403-try",
            )
        ).encode("utf-8")
        status, data, headers = _get_response(
            model_service_port,
            method="PUT",
            path="/api/model-profiles/injected",
            origin=_FOREIGN_ORIGIN,
            body=payload,
        )
        assert status == 403

        # Post-state verification: use no-Origin GET (trusted CLI) to query the store.
        # The injected profile must not exist, and the original profile must be intact.
        verify_status, verify_data, verify_headers = _get_response(
            model_service_port,
            method="GET",
            path="/api/model-profiles",
            origin=None,
        )
        assert verify_status == 200
        profiles = json.loads(verify_data)
        ids = {p["id"] for p in profiles}
        assert "injected" not in ids, (
            "store must not contain the foreign-origin injected profile"
        )
        assert "coding-default" in ids, (
            "original profile must be unchanged after foreign-origin rejection"
        )

    def test_foreign_origin_options_rejected_403(
        self, model_service_port: int, model_service_server: None  # noqa: ANN401
    ) -> None:
        status, data, headers = _get_response(
            model_service_port,
            method="OPTIONS",
            path="/api/model-profiles",
            origin=_FOREIGN_ORIGIN,
        )
        assert status == 403
        assert "access-control-allow-origin" not in headers
        assert "access-control-allow-methods" not in headers

    def test_foreign_origin_error_body_no_secret(
        self, model_service_port: int, model_service_server: None  # noqa: ANN401
    ) -> None:
        """403 response must not echo back any submitted secret or request body."""
        test_secret = "REVERSE-AGENT-TEST-KEY-12345"
        payload = json.dumps(
            profile_payload(
                id="leak-test",
                model_id="leak-model",
                api_key=test_secret,
            )
        ).encode("utf-8")
        status, data, headers = _get_response(
            model_service_port,
            method="POST",
            path="/api/model-profiles/leak-test/default",
            origin=_FOREIGN_ORIGIN,
            body=payload,
        )
        assert status == 403
        response_text = data.decode("utf-8")
        assert test_secret not in response_text


# ---------------------------------------------------------------------------
# TASK 3C R2 V3 - Segment A: Connection secret-rotation invariant
# ---------------------------------------------------------------------------

def _connection_payload(**overrides) -> dict[str, Any]:
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


def _binding_payload(**overrides) -> dict[str, Any]:
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


class TestConnectionSecretRotationInvariant:
    def test_authority_field_change_without_replacement_fail_closed(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="old-master-key"))

        # Changing provider without replacement secret must fail closed
        with pytest.raises(ValueError, match="replacement api_key"):
            store.upsert_connection(
                _connection_payload(
                    provider="different-provider",
                    api_key=None,
                )
            )

        old_secret = store.resolve_connection_secret("sense-api")
        assert old_secret == "old-master-key", "old secret must still be intact (not mutated)"

    def test_authority_field_change_with_replacement_secret_ok(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="old-master-key"))

        result = store.upsert_connection(
            _connection_payload(
                provider="openai-compatible",
                base_url="https://new-provider.example.test/v1",
                api_key="new-master-key",
            )
        )
        assert result["secret_status"] == "session"
        assert store.resolve_connection_secret("sense-api") == "new-master-key"

    def test_authority_field_change_with_clear_secret_ok(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="old-master-key"))

        result = store.upsert_connection(
            _connection_payload(
                base_url="https://new-provider.example.test/v1",
                clear_secret=True,
            )
        )
        assert result["secret_status"] == "missing"
        assert store.resolve_connection_secret("sense-api") is None

    def test_name_and_enabled_change_retains_secret(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="secret-abc"))

        result = store.upsert_connection(
            _connection_payload(
                name="Renamed",
                enabled=False,
            )
        )
        assert result["name"] == "Renamed"
        assert result["enabled"] is False
        assert store.resolve_connection_secret("sense-api") == "secret-abc"

    def test_new_connection_without_secret_allowed(self) -> None:
        store = ModelProfileStore()
        result = store.upsert_connection(_connection_payload())
        assert result["secret_status"] == "missing"
        assert store.resolve_connection_secret("sense-api") is None

    def test_auth_method_change_requires_replacement(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(auth_method="none"))

        with pytest.raises(ValueError, match="replacement api_key"):
            store.upsert_connection(
                _connection_payload(auth_method="api_key")
            )


# ---------------------------------------------------------------------------
# TASK 3C R2 V3 - Segment B: Atomic private execution snapshot
# ---------------------------------------------------------------------------

class TestExecutionSnapshot:
    def test_snapshot_reads_all_fields_atomically(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="snapshot-key"))
        store.upsert_binding(_binding_payload())

        snap = store.resolve_execution_snapshot("coding-fast")

        assert snap.binding_id == "coding-fast"
        assert snap.binding_enabled is True
        assert snap.executor_id == "opencode"
        assert snap.raw_model_id == "sense-coding-fast"
        assert snap.connection_id == "sense-api"
        assert snap.connection_enabled is True
        assert snap.provider == "openai-compatible"
        assert snap.base_url == "https://models.example.test/v1"
        assert snap.auth_method == "api_key"
        assert snap.resolved_api_key == "snapshot-key"
        assert snap.external_session_status == "not_applicable"

    def test_snapshot_not_exposed_through_public_api(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="private-secret"))
        store.upsert_binding(_binding_payload())

        serialized_bindings = store.list_bindings_public()
        serialized_connections = store.list_connections_public()
        all_public = json.dumps(serialized_bindings) + json.dumps(serialized_connections)

        assert "private-secret" not in all_public
        for item in serialized_bindings:
            assert "resolved_api_key" not in item
            assert "api_key" not in item
            assert "secret" not in str(item).lower()

    def test_snapshot_missing_secret_returns_none(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload())
        store.upsert_binding(_binding_payload())

        snap = store.resolve_execution_snapshot("coding-fast")
        assert snap.resolved_api_key is None

    def test_snapshot_missing_binding_raises(self) -> None:
        store = ModelProfileStore()
        with pytest.raises(KeyError, match="binding not found"):
            store.resolve_execution_snapshot("missing-binding")

    def test_snapshot_env_secret_resolves(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TASK3C_MODEL_KEY", "env-key-value")
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key_env="TASK3C_MODEL_KEY"))
        store.upsert_binding(_binding_payload())

        snap = store.resolve_execution_snapshot("coding-fast")
        assert snap.resolved_api_key == "env-key-value"


# ---------------------------------------------------------------------------
# ISSUE183 R2 V1 - Saved Connection probe contract
# ---------------------------------------------------------------------------

from reverse_agent.model_access.service import probe_saved_connection


class TestConnectionProbeService:
    """Saved-Connection probe: server-side secret, no body echo, fail-closed."""

    def test_stored_secret_used_and_never_serialized(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="connection-master-key"))

        calls: list[tuple[str, dict[str, str], float]] = []

        def transport(
            url: str, headers: dict[str, str], timeout: float
        ) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"data":[{"id":"probe-model"}]}'

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=True,
            transport=transport,
        )

        assert result.ok is True
        assert result.status == "connected"
        assert calls == [
            (
                "https://models.example.test/v1/models",
                {
                    "Accept": "application/json",
                    "Authorization": "Bearer connection-master-key",
                },
                10.0,
            )
        ]
        serialized = json.dumps(result.to_dict())
        assert "connection-master-key" not in serialized
        assert "Bearer" not in serialized
        assert "Authorization" not in serialized

    def test_non_empty_payload_rejected_fail_closed(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="ignored"))

        with pytest.raises(ValueError, match="configuration overrides"):
            probe_saved_connection(
                store=store,
                connection_id="sense-api",
                payload={"api_key": "injected-key"},
                live_enabled=True,
            )

    def test_non_empty_generic_payload_rejected(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="ignored"))

        with pytest.raises(ValueError, match="empty JSON object"):
            probe_saved_connection(
                store=store,
                connection_id="sense-api",
                payload={"custom_field": "value"},
                live_enabled=True,
            )

    def test_disabled_connection_no_transport(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="key", enabled=False))

        calls: list[tuple[str, dict[str, str], float]] = []

        def transport(
            url: str, headers: dict[str, str], timeout: float
        ) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"data":[]}'

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=True,
            transport=transport,
        )

        assert result.ok is False
        assert result.status == "disabled"
        assert calls == []

    def test_missing_api_key_secret_no_transport(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload())  # no secret

        calls: list[tuple[str, dict[str, str], float]] = []

        def transport(
            url: str, headers: dict[str, str], timeout: float
        ) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"data":[]}'

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=True,
            transport=transport,
        )

        assert result.ok is False
        assert result.status == "credential_missing"
        assert calls == []

    @pytest.mark.parametrize(
        "auth_method", ["account_login", "external_cli_session"]
    )
    def test_unsupported_auth_method_no_transport(self, auth_method: str) -> None:
        store = ModelProfileStore()
        store.upsert_connection(
            _connection_payload(
                connection_id=f"{auth_method}-conn",
                auth_method=auth_method,
            )
        )

        calls: list[tuple[str, dict[str, str], float]] = []

        def transport(
            url: str, headers: dict[str, str], timeout: float
        ) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"data":[]}'

        result = probe_saved_connection(
            store=store,
            connection_id=f"{auth_method}-conn",
            payload={},
            live_enabled=True,
            transport=transport,
        )

        assert result.ok is False
        assert result.status == "unsupported_auth_method"
        assert calls == []

    def test_none_auth_method_probes_without_authorization(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(
            _connection_payload(
                connection_id="no-auth-conn",
                auth_method="none",
            )
        )

        calls: list[tuple[str, dict[str, str], float]] = []

        def transport(
            url: str, headers: dict[str, str], timeout: float
        ) -> tuple[int, bytes]:
            calls.append((url, headers, timeout))
            return 200, b'{"data":[{"id":"m"}]}'

        result = probe_saved_connection(
            store=store,
            connection_id="no-auth-conn",
            payload={},
            live_enabled=True,
            transport=transport,
        )

        assert result.ok is True
        assert result.status == "connected"
        assert calls == [
            (
                "https://models.example.test/v1/models",
                {"Accept": "application/json"},
                10.0,
            )
        ]
        assert "Authorization" not in calls[0][1]

    def test_live_opt_in_disabled_still_fail_closed(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection(_connection_payload(api_key="key"))

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=False,
        )

        assert result.ok is False
        assert result.status == "live_probe_disabled"
        assert "key" not in json.dumps(result.to_dict())

    def test_not_found_connection_returned(self) -> None:
        store = ModelProfileStore()

        result = probe_saved_connection(
            store=store,
            connection_id="missing-conn",
            payload={},
            live_enabled=True,
        )

        assert result.ok is False
        assert result.status == "not_found"


# ---------------------------------------------------------------------------
# ISSUE444 R3 - provider-owned OpenAI OAuth lifecycle
# ---------------------------------------------------------------------------

from types import SimpleNamespace as _SimpleNamespace

from reverse_agent.model_access.account_auth import AccountAuthManager


class _FakeAccountAuthServer:
    def __init__(self, *, callback_method: str = "code") -> None:
        self.callback_method = callback_method
        self.closed = False
        self.calls: list[tuple[Any, ...]] = []

    def provider_auth_methods(self, *, provider_id: str):
        self.calls.append(("methods", provider_id))
        return (
            _SimpleNamespace(index=0, type="api", label="API key"),
            _SimpleNamespace(index=2, type="oauth", label="ChatGPT Plus/Pro"),
        )

    def provider_oauth_authorize(self, *, provider_id: str, method_index: int):
        self.calls.append(("authorize", provider_id, method_index))
        return _SimpleNamespace(
            url="https://auth.example.test/authorize?state=opaque",
            method=self.callback_method,
            instructions="Continue in browser.",
        )

    def provider_oauth_callback(
        self, *, provider_id: str, method_index: int, code: str | None = None
    ) -> bool:
        self.calls.append(("callback", provider_id, method_index, code))
        return True

    def close(self) -> None:
        self.closed = True


class _FakeAccountAuthTimer:
    def __init__(self, seconds: float, callback: Callable[[], None]) -> None:
        self.seconds = seconds
        self.callback = callback
        self.daemon = False
        self.started = False
        self.canceled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.canceled = True

    def fire(self) -> None:
        self.callback()


class _FakeAccountAuthTimerFactory:
    def __init__(self) -> None:
        self.timers: list[_FakeAccountAuthTimer] = []

    def __call__(
        self, seconds: float, callback: Callable[[], None]
    ) -> _FakeAccountAuthTimer:
        timer = _FakeAccountAuthTimer(seconds, callback)
        self.timers.append(timer)
        return timer


def _account_login_store() -> ModelProfileStore:
    store = ModelProfileStore()
    store.upsert_connection(
        _connection_payload(
            connection_id="openai-account",
            provider="openai",
            base_url="https://api.openai.com/v1",
            auth_method="account_login",
        )
    )
    return store


def test_account_auth_delegates_to_advertised_oauth_and_refreshes_status() -> None:
    store = _account_login_store()
    server = _FakeAccountAuthServer()

    def refresh(force: bool, connection_id: str | None) -> None:
        assert force is True
        assert connection_id == "openai-account"
        store.refresh_external_session_status({"openai": "oauth"})

    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: server,
        refresh=refresh,
    )
    started = manager.start("openai-account")
    completed = manager.callback("openai-account", "TRANSIENT_CODE_SENTINEL")

    assert started == {
        "status": "awaiting_browser",
        "provider": "openai",
        "authorization_url": "https://auth.example.test/authorize?state=opaque",
        "callback_method": "code",
        "instructions": "Continue in browser.",
        "expires_in_seconds": 300,
    }
    assert completed == {
        "status": "authenticated",
        "provider": "openai",
        "external_session_status": "available",
    }
    assert server.calls == [
        ("methods", "openai"),
        ("authorize", "openai", 2),
        ("callback", "openai", 2, "TRANSIENT_CODE_SENTINEL"),
    ]
    assert server.closed is True
    assert "TRANSIENT_CODE_SENTINEL" not in json.dumps(started)
    assert "TRANSIENT_CODE_SENTINEL" not in json.dumps(completed)


def test_account_auth_auto_callback_rejects_supplied_code() -> None:
    store = _account_login_store()
    server = _FakeAccountAuthServer(callback_method="auto")
    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: server,
        refresh=lambda *_: None,
    )
    manager.start("openai-account")

    with pytest.raises(ValueError, match="not accepted"):
        manager.callback("openai-account", "UNEXPECTED_CODE")
    assert server.closed is False
    result = manager.callback("openai-account")
    assert result["status"] == "verification_pending"
    assert server.closed is True


def test_account_auth_timeout_proactively_closes_child_without_polling() -> None:
    store = _account_login_store()
    server = _FakeAccountAuthServer()
    timers = _FakeAccountAuthTimerFactory()
    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: server,
        refresh=lambda *_: None,
        timeout_seconds=5,
        timer_factory=timers,
    )
    manager.start("openai-account")

    assert len(timers.timers) == 1
    timer = timers.timers[0]
    assert timer.seconds == 5
    assert timer.started is True
    assert timer.daemon is True
    assert server.closed is False

    timer.fire()

    assert server.closed is True
    assert timer.canceled is True
    status = manager.status("openai-account")
    assert status["status"] == "expired"
    assert status["external_session_status"] == "executor_managed"


def test_account_auth_completed_flow_cancels_proactive_expiry_timer() -> None:
    store = _account_login_store()
    server = _FakeAccountAuthServer()
    timers = _FakeAccountAuthTimerFactory()
    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: server,
        refresh=lambda *_: None,
        timer_factory=timers,
    )
    manager.start("openai-account")
    manager.callback("openai-account", "TRANSIENT_CODE")

    assert timers.timers[0].canceled is True
    timers.timers[0].fire()
    assert manager.status("openai-account")["status"] == "idle"


def test_account_auth_cancel_and_logout_are_explicit_provider_boundaries() -> None:
    store = _account_login_store()
    server = _FakeAccountAuthServer()
    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: server,
        refresh=lambda *_: None,
    )
    manager.start("openai-account")
    canceled = manager.cancel("openai-account")
    logout = manager.logout("openai-account")

    assert canceled["status"] == "canceled"
    assert server.closed is True
    assert logout["status"] == "provider_logout_required"
    assert "OpenCode" in logout["instructions"]
    assert logout["external_session_status"] == "executor_managed"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"provider": "anthropic"}, "OpenAI only"),
        ({"auth_method": "external_cli_session"}, "does not use account_login"),
        ({"enabled": False}, "disabled"),
    ],
)
def test_account_auth_rejects_out_of_scope_connections(
    overrides: dict[str, Any], message: str
) -> None:
    store = ModelProfileStore()
    payload = _connection_payload(
        connection_id="other-account",
        provider="openai",
        auth_method="account_login",
    )
    payload.update(overrides)
    store.upsert_connection(payload)
    manager = AccountAuthManager(
        store=store,
        server_factory=lambda: _FakeAccountAuthServer(),
        refresh=lambda *_: None,
    )
    with pytest.raises(ValueError, match=message):
        manager.start("other-account")


# ---------------------------------------------------------------------------
# ISSUE441 R1 - Durable OS-backed API-key persistence (CRED-1 ~ CRED-4)
# ---------------------------------------------------------------------------

from pathlib import Path as _Path
import reverse_agent.model_access.store as _store_module

from reverse_agent.model_access.os_vault import (
    FakeVault,
    VaultItemMissingError,
    VaultSizeError,
    VaultUnavailableError,
    _decode_secret_blob,
    connection_vault_ref,
)


class _FakeCtypesBlobReader:
    def __init__(self, payload: bytes = b"secret") -> None:
        self.payload = payload
        self.calls: list[tuple[Any, int]] = []

    def string_at(self, pointer: Any, size: int) -> bytes:
        self.calls.append((pointer, size))
        return self.payload[:size]


def test_native_vault_read_rejects_oversized_blob_before_copy() -> None:
    ctypes_api = _FakeCtypesBlobReader()

    with pytest.raises(VaultSizeError, match="oversized"):
        _decode_secret_blob(ctypes_api, object(), 2561, "safe-ref")

    assert ctypes_api.calls == []


def test_native_vault_read_copies_and_decodes_only_bounded_blob() -> None:
    ctypes_api = _FakeCtypesBlobReader(b"bounded-secret")
    pointer = object()

    assert _decode_secret_blob(
        ctypes_api, pointer, len(b"bounded-secret"), "safe-ref"
    ) == "bounded-secret"
    assert ctypes_api.calls == [(pointer, len(b"bounded-secret"))]

_VAULT_SECRET = "vault-backed-master-key-sentinel"


class TestVaultReferenceBinding:
    """The vault item reference is bound to the Connection authority."""

    def test_reference_is_deterministic_and_namespaced(self) -> None:
        ref = connection_vault_ref(
            "sense-api", "openai-compatible", "https://models.example.test/v1", "api_key"
        )
        assert ref.startswith("nerelan:conn:v1:sense-api:")
        assert ref == connection_vault_ref(
            "sense-api", "openai-compatible", "https://models.example.test/v1", "api_key"
        )
        suffix = ref.rsplit(":", 1)[1]
        assert len(suffix) == 16 and all(c in "0123456789abcdef" for c in suffix)

    def test_any_authority_change_moves_the_reference(self) -> None:
        base = connection_vault_ref(
            "sense-api", "openai-compatible", "https://models.example.test/v1", "api_key"
        )
        assert connection_vault_ref(
            "sense-api", "litellm-proxy", "https://models.example.test/v1", "api_key"
        ) != base
        assert connection_vault_ref(
            "sense-api", "openai-compatible", "https://other.example.test/v1", "api_key"
        ) != base
        assert connection_vault_ref(
            "sense-api", "openai-compatible", "https://models.example.test/v1", "none"
        ) != base
        assert connection_vault_ref(
            "other-api", "openai-compatible", "https://models.example.test/v1", "api_key"
        ) != base

    def test_two_connections_with_same_authority_never_share_a_reference(self) -> None:
        first = connection_vault_ref(
            "conn-a", "openai-compatible", "https://models.example.test/v1", "api_key"
        )
        second = connection_vault_ref(
            "conn-b", "openai-compatible", "https://models.example.test/v1", "api_key"
        )
        assert first != second


class TestVaultBackedSaveAndRestart:
    """Save through the vault, then restart over the same sanitized state."""

    def _vault_store(self, tmp_path, vault):
        return ModelProfileStore(
            state_path=str(tmp_path / "model_setup_state.json"), vault=vault
        )

    def test_save_reports_stored_and_persists_ref_never_secret(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._vault_store(tmp_path, vault)

        public = store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        assert public["credential_configured"] is True
        assert public["secret_status"] == "stored"
        assert "api_key" not in public
        assert _VAULT_SECRET not in json.dumps(public)

        raw = _Path(str(tmp_path / "model_setup_state.json")).read_bytes()
        assert _VAULT_SECRET.encode("utf-8") not in raw
        assert b"nerelan:conn:v1:sense-api:" in raw
        assert vault.item_refs() == (
            connection_vault_ref(
                "sense-api",
                "openai-compatible",
                "https://models.example.test/v1",
                "api_key",
            ),
        )

    def test_restart_resolves_secret_again_without_re_entry(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._vault_store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        fresh = self._vault_store(tmp_path, vault)
        listed = fresh.list_connections_public()
        assert listed[0]["credential_configured"] is True
        assert listed[0]["secret_status"] == "stored"
        assert fresh.resolve_connection_secret("sense-api") == _VAULT_SECRET

    def test_public_reads_show_status_only_never_the_secret(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._vault_store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        serialized = json.dumps(
            store.list_connections_public()
            + [store.get_connection_public("sense-api")]
        )
        assert _VAULT_SECRET not in serialized
        assert "credential_ref" not in serialized
        assert "resolved_api_key" not in serialized

    def test_execution_snapshot_resolves_through_the_vault(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._vault_store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        store.upsert_binding(_binding_payload())

        snap = store.resolve_execution_snapshot("coding-fast")
        assert snap.resolved_api_key == _VAULT_SECRET

    def test_oversized_secret_fails_closed(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._vault_store(tmp_path, vault)

        with pytest.raises(VaultSizeError):
            store.upsert_connection(
                _connection_payload(api_key="x" * 2561)
            )
        assert vault.item_refs() == ()
        assert store.list_connections_public() == []


class TestVaultFailClosedStates:
    """Locked or missing vault items produce explicit typed states."""

    def _prepared(self, tmp_path):
        vault = FakeVault()
        store = ModelProfileStore(
            state_path=str(tmp_path / "model_setup_state.json"), vault=vault
        )
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        return vault, store

    def test_locked_vault_on_public_read_reports_store_locked(self, tmp_path) -> None:
        vault, store = self._prepared(tmp_path)
        vault.locked = True

        listed = store.list_connections_public()
        assert listed[0]["credential_configured"] is True
        assert listed[0]["secret_status"] == "store_locked"

    def test_externally_missing_item_maps_to_replacement_required(self, tmp_path) -> None:
        vault, store = self._prepared(tmp_path)
        ref = vault.item_refs()[0]
        vault._items.pop(ref)  # simulate external removal from the OS store

        listed = store.list_connections_public()
        assert listed[0]["credential_configured"] is True
        assert listed[0]["secret_status"] == "replacement_required"
        assert store.resolve_connection_secret("sense-api") is None

    def test_locked_vault_fails_execution_resolution_closed(self, tmp_path) -> None:
        vault, store = self._prepared(tmp_path)
        store.upsert_binding(_binding_payload())
        vault.locked = True

        with pytest.raises(VaultUnavailableError):
            store.resolve_connection_secret("sense-api")
        with pytest.raises(VaultUnavailableError):
            store.resolve_execution_snapshot("coding-fast")

    def test_locked_vault_probe_returns_typed_state(self, tmp_path) -> None:
        vault, store = self._prepared(tmp_path)
        vault.locked = True

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=True,
        )
        assert result.ok is False
        assert result.status == "credential_store_locked"
        assert _VAULT_SECRET not in json.dumps(result.to_dict())

    def test_missing_vault_item_probe_reports_credential_missing(self, tmp_path) -> None:
        vault, store = self._prepared(tmp_path)
        vault._items.pop(vault.item_refs()[0])

        result = probe_saved_connection(
            store=store,
            connection_id="sense-api",
            payload={},
            live_enabled=True,
        )
        assert result.ok is False
        assert result.status == "credential_missing"


class TestVaultSaveAtomicityAndAuthority:
    """Failed saves preserve prior state; authority changes never reuse items."""

    def _store(self, tmp_path, vault):
        return ModelProfileStore(
            state_path=str(tmp_path / "model_setup_state.json"), vault=vault
        )

    def test_locked_vault_save_fails_closed_and_preserves_previous_state(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        vault.locked = True
        with pytest.raises(VaultUnavailableError):
            store.upsert_connection(
                _connection_payload(api_key="replacement-secret")
            )
        vault.locked = False

        listed = store.list_connections_public()
        assert listed[0]["secret_status"] == "stored"
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET
        raw = _Path(str(tmp_path / "model_setup_state.json")).read_bytes()
        assert b"replacement-secret" not in raw

    def test_failed_replacement_preserves_prior_valid_item(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        original_ref = vault.item_refs()[0]

        def fail_store(ref: str) -> None:
            raise VaultUnavailableError("write failed mid-replacement")

        vault._store_hook = fail_store
        with pytest.raises(VaultUnavailableError):
            store.upsert_connection(
                _connection_payload(api_key="replacement-secret")
            )
        vault._store_hook = None

        assert vault.item_refs() == (original_ref,)
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET

    @pytest.mark.parametrize(
        "replacement",
        [
            {"api_key": "replacement-secret"},
            {"provider": "litellm-proxy", "api_key": "replacement-secret"},
            {"clear_secret": True},
        ],
    )
    def test_persistence_failure_restores_prior_committed_vault_relation(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
        replacement: dict[str, Any],
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        state_path = _Path(str(tmp_path / "model_setup_state.json"))
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        committed_state = state_path.read_bytes()
        committed_refs = vault.item_refs()

        def fail_persist(_data: bytes, _target: _Path) -> None:
            raise OSError("simulated sanitized-state persistence failure")

        monkeypatch.setattr(_store_module, "_write_atomic", fail_persist)
        with pytest.raises(_store_module.StoreError, match="persistence failed"):
            store.upsert_connection(_connection_payload(**replacement))

        assert state_path.read_bytes() == committed_state
        assert vault.item_refs() == committed_refs
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET
        assert "replacement-secret" not in vault._items.values()

    def test_delete_persistence_failure_preserves_connection_and_vault_item(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        state_path = _Path(str(tmp_path / "model_setup_state.json"))
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        committed_state = state_path.read_bytes()
        committed_refs = vault.item_refs()

        def fail_persist(_data: bytes, _target: _Path) -> None:
            raise OSError("simulated sanitized-state persistence failure")

        monkeypatch.setattr(_store_module, "_write_atomic", fail_persist)
        with pytest.raises(_store_module.StoreError, match="persistence failed"):
            store.delete_connection("sense-api")

        assert state_path.read_bytes() == committed_state
        assert vault.item_refs() == committed_refs
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET

    def test_obsolete_item_delete_failure_rolls_back_new_state_and_item(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        state_path = _Path(str(tmp_path / "model_setup_state.json"))
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        old_ref = vault.item_refs()[0]
        committed_state = state_path.read_bytes()

        def fail_old_delete(ref: str) -> None:
            if ref == old_ref:
                raise VaultUnavailableError("simulated obsolete-item delete failure")

        vault._delete_hook = fail_old_delete
        with pytest.raises(VaultUnavailableError, match="obsolete-item"):
            store.upsert_connection(
                _connection_payload(
                    provider="litellm-proxy",
                    api_key="replacement-secret",
                )
            )
        vault._delete_hook = None

        assert state_path.read_bytes() == committed_state
        assert vault.item_refs() == (old_ref,)
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET

    def test_authority_change_with_new_key_writes_new_ref_and_removes_old(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        old_ref = vault.item_refs()[0]

        store.upsert_connection(
            _connection_payload(
                provider="litellm-proxy", api_key="rotated-secret"
            )
        )

        new_ref = vault.item_refs()[0]
        assert new_ref != old_ref
        assert vault.item_refs() == (new_ref,)
        assert vault._items[new_ref] == "rotated-secret"
        assert store.resolve_connection_secret("sense-api") == "rotated-secret"

    def test_authority_change_without_replacement_fail_closed(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        with pytest.raises(ValueError, match="authority-bearing"):
            store.upsert_connection(_connection_payload(provider="litellm-proxy"))

        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET

    def test_one_connection_never_resolves_another_connections_item(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        store.upsert_connection(
            _connection_payload(
                connection_id="other-api",
                name="Other API",
                api_key="other-connection-secret",
            )
        )

        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET
        assert store.resolve_connection_secret("other-api") == "other-connection-secret"
        assert len(vault.item_refs()) == 2


class TestVaultRemovalAndIndependentPaths:
    """Explicit removal removes only the owning item; other paths unchanged."""

    def _store(self, tmp_path, vault):
        return ModelProfileStore(
            state_path=str(tmp_path / "model_setup_state.json"), vault=vault
        )

    def test_clear_secret_removes_only_the_owning_item(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))
        store.upsert_connection(
            _connection_payload(
                connection_id="other-api",
                name="Other API",
                api_key="other-connection-secret",
            )
        )

        cleared = store.upsert_connection(
            _connection_payload(clear_secret=True)
        )

        assert cleared["credential_configured"] is False
        assert cleared["secret_status"] == "missing"
        remaining = vault.item_refs()
        assert len(remaining) == 1
        assert vault._items[remaining[0]] == "other-connection-secret"
        raw = _Path(str(tmp_path / "model_setup_state.json")).read_bytes()
        assert b"nerelan:conn:v1:sense-api:" not in raw

    def test_delete_connection_removes_the_nerelan_owned_item(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        store.delete_connection("sense-api")

        assert vault.item_refs() == ()
        fresh = self._store(tmp_path, vault)
        assert fresh.list_connections_public() == []

    def test_environment_backed_path_stays_independent_with_vault_present(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VAULT_TEST_ENV_KEY", "env-path-secret")
        vault = FakeVault()
        store = self._store(tmp_path, vault)

        public = store.upsert_connection(
            _connection_payload(api_key_env="VAULT_TEST_ENV_KEY")
        )

        assert public["secret_status"] == "environment"
        assert vault.item_refs() == ()
        assert store.resolve_connection_secret("sense-api") == "env-path-secret"

    def test_env_replacement_of_vault_secret_removes_the_item(self, tmp_path) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        store.upsert_connection(
            _connection_payload(api_key_env="VAULT_TEST_ENV_KEY_2")
        )

        assert vault.item_refs() == ()
        listed = store.list_connections_public()
        assert listed[0]["secret_status"] == "missing"  # env var not set

    def test_without_vault_process_local_behavior_is_unchanged(self, tmp_path) -> None:
        store = self._store(tmp_path, None)

        public = store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        assert public["secret_status"] == "session"
        assert store.resolve_connection_secret("sense-api") == _VAULT_SECRET
        raw = _Path(str(tmp_path / "model_setup_state.json")).read_bytes()
        assert _VAULT_SECRET.encode("utf-8") not in raw
        assert b"nerelan:conn:v1" not in raw

    def test_restarted_connection_without_vault_reports_store_locked(
        self, tmp_path
    ) -> None:
        state = str(tmp_path / "model_setup_state.json")
        vault = FakeVault()
        ModelProfileStore(state_path=state, vault=vault).upsert_connection(
            _connection_payload(api_key=_VAULT_SECRET)
        )

        fresh = ModelProfileStore(state_path=state)

        listed = fresh.list_connections_public()
        assert listed[0]["credential_configured"] is True
        assert listed[0]["secret_status"] == "store_locked"
        assert fresh.resolve_connection_secret("sense-api") is None

    def test_account_login_path_rejects_raw_credentials_with_vault(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)

        with pytest.raises(ValueError, match="raw session credentials"):
            store.upsert_connection(
                _connection_payload(auth_method="account_login", token="x")
            )
        assert vault.item_refs() == ()

    def test_vault_secret_discarded_on_auth_method_change_requires_clear(
        self, tmp_path
    ) -> None:
        vault = FakeVault()
        store = self._store(tmp_path, vault)
        store.upsert_connection(_connection_payload(api_key=_VAULT_SECRET))

        with pytest.raises(ValueError, match="clear_secret"):
            store.upsert_connection(_connection_payload(auth_method="none"))

        switched = store.upsert_connection(
            _connection_payload(auth_method="none", clear_secret=True)
        )
        assert switched["secret_status"] == "not_applicable"
        assert vault.item_refs() == ()
