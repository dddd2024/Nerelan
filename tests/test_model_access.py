from __future__ import annotations

import json
import socket
import threading
from http.client import HTTPConnection
from typing import Any
from urllib.parse import urljoin

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
