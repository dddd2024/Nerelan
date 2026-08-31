"""Dependency-free trusted-host HTTP service for model profile control."""

from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
import json
import os
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from .contracts import Connection, ModelProfile, ProbeResult
from .store import ModelProfileStore

ProbeTransport = Callable[[str, dict[str, str], float], tuple[int, bytes]]
_MAX_BODY_BYTES = 1_048_576
_PROBE_PAYLOAD_FORBIDDEN_FIELDS = frozenset({
    "api_key", "apiKey",
    "token",
    "base_url", "baseUrl",
    "provider",
    "auth_method", "authMethod",
    "connection_id", "connectionId",
    "name",
    "enabled",
    "model_id", "modelId",
    "api_key_env", "apiKeyEnv",
})


def _default_transport(
    url: str, headers: dict[str, str], timeout: float
) -> tuple[int, bytes]:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - gated opt-in
        return int(response.status), response.read(_MAX_BODY_BYTES)


def _do_probe(
    *,
    url: str,
    headers: dict[str, str],
    live_enabled: bool,
    transport: ProbeTransport | None,
    timeout: float,
) -> ProbeResult:
    """Internal reusable ``/models`` probe primitive.

    Live network access is fail-closed. The returned result never carries any
    credential, Authorization header or upstream request body.
    """
    if not live_enabled:
        return ProbeResult(
            ok=False,
            status="live_probe_disabled",
            message="Live model probes require REVERSE_AGENT_MODEL_CONTROL_LIVE=1",
            latency_ms=None,
        )

    started = perf_counter()
    try:
        status_code, body = (transport or _default_transport)(url, headers, timeout)
        latency_ms = max(0, round((perf_counter() - started) * 1000))
        if not 200 <= status_code < 300:
            return ProbeResult(
                ok=False,
                status="upstream_http_error",
                message=f"Upstream returned HTTP {status_code}",
                latency_ms=latency_ms,
            )
        try:
            json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ProbeResult(
                ok=False,
                status="invalid_upstream_response",
                message="Upstream returned invalid JSON",
                latency_ms=latency_ms,
            )
        return ProbeResult(
            ok=True,
            status="connected",
            message="Connection succeeded",
            latency_ms=latency_ms,
        )
    except HTTPError as error:
        return ProbeResult(
            ok=False,
            status="upstream_http_error",
            message=f"Upstream returned HTTP {error.code}",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )
    except TimeoutError:
        return ProbeResult(
            ok=False,
            status="timeout",
            message="Upstream request timed out",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )
    except URLError:
        return ProbeResult(
            ok=False,
            status="connection_error",
            message="Unable to connect to upstream model endpoint",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )
    except OSError:
        return ProbeResult(
            ok=False,
            status="connection_error",
            message="Unable to connect to upstream model endpoint",
            latency_ms=max(0, round((perf_counter() - started) * 1000)),
        )


def probe_openai_compatible(
    *,
    profile: ModelProfile,
    api_key: str | None,
    live_enabled: bool,
    transport: ProbeTransport | None = None,
    timeout: float = 10.0,
) -> ProbeResult:
    """Probe an OpenAI-compatible ``/models`` endpoint.

    Legacy wrapper — kept for backward compatibility with existing ModelProfile
    probe consumers.  Reuses the shared ``_do_probe`` primitive so Connection
    and ModelProfile probes cannot diverge.
    """
    url = f"{profile.base_url.rstrip('/')}/models"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return _do_probe(
        url=url,
        headers=headers,
        live_enabled=live_enabled,
        transport=transport,
        timeout=timeout,
    )


def probe_saved_connection(
    *,
    store: ModelProfileStore,
    connection_id: str,
    payload: dict[str, Any],
    live_enabled: bool,
    transport: ProbeTransport | None = None,
    timeout: float = 10.0,
) -> ProbeResult:
    """Probe a saved Connection's ``/models`` endpoint.

    Saved-Connection only semantics:
      - The probe body must be empty or ``{}``. Any non-empty payload, including
        credential/config overrides, is rejected (fail closed).
      - The Connection metadata comes from the trusted store, not from the
        request.
      - API-key secrets are resolved server-side via ``resolve_connection_secret``.
      - No credential, environment-variable name or Authorization header is
        ever returned to the client.
      - Disabled connections, missing API-key secrets, and unsupported auth
        methods fail closed without invoking transport.
    """
    # Fail closed: reject any non-empty probe payload / config override.
    if payload:
        conflicting = sorted(k for k in payload if k in _PROBE_PAYLOAD_FORBIDDEN_FIELDS)
        if conflicting:
            raise ValueError(
                "probe payload must not contain configuration overrides"
            )
        raise ValueError("probe payload must be an empty JSON object")

    try:
        connection = Connection.from_mapping(
            store.get_connection_public(connection_id)
        )
    except KeyError:
        return ProbeResult(
            ok=False,
            status="not_found",
            message="Connection not found",
            latency_ms=None,
        )

    if not connection.enabled:
        return ProbeResult(
            ok=False,
            status="disabled",
            message="Connection is disabled",
            latency_ms=None,
        )

    if connection.auth_method == "api_key":
        secret = store.resolve_connection_secret(connection_id)
        if not secret:
            return ProbeResult(
                ok=False,
                status="credential_missing",
                message="API key is not configured",
                latency_ms=None,
            )
        headers = {"Accept": "application/json", "Authorization": f"Bearer {secret}"}
    elif connection.auth_method == "none":
        headers = {"Accept": "application/json"}
    else:
        return ProbeResult(
            ok=False,
            status="unsupported_auth_method",
            message="Probing this authentication method is not yet supported",
            latency_ms=None,
        )

    url = f"{connection.base_url.rstrip('/')}/models"
    return _do_probe(
        url=url,
        headers=headers,
        live_enabled=live_enabled,
        transport=transport,
        timeout=timeout,
    )


class _ModelControlHandler(BaseHTTPRequestHandler):
    store = ModelProfileStore()
    live_enabled = False
    allowed_origin = "http://localhost:5173"
    external_session_refresh: Callable[[bool, str | None], None] = staticmethod(
        lambda _force, _connection_id: None
    )

    server_version = "reverse-agent-model-control/1"

    def log_message(self, format: str, *args: object) -> None:
        # Do not log request bodies, headers or secrets. The method/route/status
        # are already observable by the caller and need no default stderr log.
        return

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._check_origin():
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._check_origin():
            return
        try:
            segments = self._segments()
            if segments == ["api", "model-profiles"]:
                self._send_json(HTTPStatus.OK, self.store.list_public())
                return
            if segments == ["api", "connections"]:
                self.external_session_refresh(False, None)
                self._send_json(HTTPStatus.OK, self.store.list_connections_public())
                return
            if len(segments) == 3 and segments[:2] == ["api", "connections"]:
                self.external_session_refresh(False, segments[2])
                self._send_json(
                    HTTPStatus.OK,
                    self.store.get_connection_public(segments[2]),
                )
                return
            if segments == ["api", "executors"]:
                self._send_json(HTTPStatus.OK, self.store.list_executors_public())
                return
            if len(segments) == 3 and segments[:2] == ["api", "executors"]:
                self._send_json(
                    HTTPStatus.OK,
                    self.store.get_executor_public(segments[2]),
                )
                return
            if segments == ["api", "bindings"]:
                self._send_json(HTTPStatus.OK, self.store.list_bindings_public())
                return
            if len(segments) == 3 and segments[:2] == ["api", "bindings"]:
                self._send_json(
                    HTTPStatus.OK,
                    self.store.get_binding_public(segments[2]),
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except Exception as error:  # handler boundary
            self._send_exception(error)

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._check_origin():
            return
        try:
            segments = self._segments()
            if len(segments) == 3 and segments[:2] == ["api", "model-profiles"]:
                payload = self._read_json()
                payload["id"] = segments[2]
                self._send_json(HTTPStatus.OK, self.store.upsert(payload))
                return
            if len(segments) == 3 and segments[:2] == ["api", "connections"]:
                payload = self._read_json()
                payload["connection_id"] = segments[2]
                try:
                    previous = self.store.get_connection_public(segments[2])
                except KeyError:
                    previous = None
                self.store.upsert_connection(payload)
                current = self.store.get_connection_public(segments[2])
                if _external_session_truth_changed(previous, current):
                    self.external_session_refresh(True, segments[2])
                self._send_json(
                    HTTPStatus.OK,
                    self.store.get_connection_public(segments[2]),
                )
                return
            if len(segments) == 3 and segments[:2] == ["api", "bindings"]:
                payload = self._read_json()
                payload["binding_id"] = segments[2]
                self._send_json(
                    HTTPStatus.OK,
                    self.store.upsert_binding(payload),
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except Exception as error:  # handler boundary
            self._send_exception(error)

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._check_origin():
            return
        try:
            segments = self._segments()
            if len(segments) == 3 and segments[:2] == ["api", "model-profiles"]:
                self.store.delete(segments[2])
                self._send_json(HTTPStatus.OK, {"deleted": True})
                return
            if len(segments) == 3 and segments[:2] == ["api", "connections"]:
                self.store.delete_connection(segments[2])
                self._send_json(HTTPStatus.OK, {"deleted": True})
                return
            if len(segments) == 3 and segments[:2] == ["api", "bindings"]:
                self.store.delete_binding(segments[2])
                self._send_json(HTTPStatus.OK, {"deleted": True})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except Exception as error:  # handler boundary
            self._send_exception(error)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if not self._check_origin():
            return
        try:
            segments = self._segments()
            if (
                len(segments) == 4
                and segments[:2] == ["api", "model-profiles"]
                and segments[3] == "default"
            ):
                self._send_json(
                    HTTPStatus.OK,
                    self.store.set_default(segments[2]),
                )
                return
            if (
                len(segments) == 4
                and segments[:2] == ["api", "model-profiles"]
                and segments[3] == "test"
            ):
                payload = self._read_json(optional=True)
                secret = _optional_request_secret(payload) or self.store.resolve_secret(
                    segments[2]
                )
                result = probe_openai_compatible(
                    profile=self.store.get_profile(segments[2]),
                    api_key=secret,
                    live_enabled=self.live_enabled,
                )
                self._send_json(HTTPStatus.OK, result.to_dict())
                return
            if (
                len(segments) == 4
                and segments[:2] == ["api", "connections"]
                and segments[3] == "test"
            ):
                payload = self._read_json(optional=True)
                result = probe_saved_connection(
                    store=self.store,
                    connection_id=segments[2],
                    payload=payload,
                    live_enabled=self.live_enabled,
                )
                self._send_json(HTTPStatus.OK, result.to_dict())
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except Exception as error:  # handler boundary
            self._send_exception(error)

    def _segments(self) -> list[str]:
        path = urlsplit(self.path).path
        return [unquote(part) for part in path.split("/") if part]

    def _read_json(self, *, optional: bool = False) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            if optional:
                return {}
            raise ValueError("request body is required")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ValueError("invalid Content-Length") from error
        if length < 0 or length > _MAX_BODY_BYTES:
            raise ValueError("request body exceeds limit")
        if length == 0 and optional:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("request JSON must be an object")
        return payload

    def _send_exception(self, error: Exception) -> None:
        if isinstance(error, KeyError):
            message = str(error.args[0]) if error.args else "not found"
            self._send_json(HTTPStatus.NOT_FOUND, {"error": message})
        elif isinstance(error, ValueError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        else:
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal model control error"},
            )

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_forbidden(self) -> None:
        """Send opaque 403 response — no secrets, no body echo, no stack trace."""
        body = b'{"error":"forbidden"}'
        self.send_response(HTTPStatus.FORBIDDEN)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _check_origin(self) -> bool:
        """Server-side Origin gate.

        Origin absent      -> allow (trusted loopback CLI / non-browser)
        Origin == allowed -> allow (normal CORS)
        Origin != allowed -> 403 (fail closed before any handler logic)
        """
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        if origin == self.allowed_origin:
            return True
        self._send_forbidden()
        return False

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin == self.allowed_origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")


def _optional_request_secret(payload: dict[str, Any]) -> str | None:
    value = payload.get("api_key", payload.get("apiKey"))
    if value in {None, ""}:
        return None
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError("api_key must be a string no longer than 4096 characters")
    return value


def _external_session_truth_changed(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> bool:
    if current.get("auth_method") not in {
        "account_login",
        "external_cli_session",
    }:
        return False
    if previous is None:
        return True
    return any(
        previous.get(field) != current.get(field)
        for field in ("provider", "base_url", "auth_method", "enabled")
    )


def _handler_factory(
    store: ModelProfileStore,
    *,
    live_enabled: bool,
    allowed_origin: str,
    external_session_refresh: Callable[[bool, str | None], None] | None = None,
) -> type[_ModelControlHandler]:
    class ConfiguredHandler(_ModelControlHandler):
        pass

    ConfiguredHandler.store = store
    ConfiguredHandler.live_enabled = live_enabled
    ConfiguredHandler.allowed_origin = allowed_origin
    ConfiguredHandler.external_session_refresh = staticmethod(
        external_session_refresh or (lambda _force, _connection_id: None)
    )
    return ConfiguredHandler


def store_from_environment() -> ModelProfileStore:
    store = ModelProfileStore()
    raw = os.environ.get("REVERSE_AGENT_MODEL_PROFILES_JSON", "").strip()
    if not raw:
        return store
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("REVERSE_AGENT_MODEL_PROFILES_JSON must be a JSON array")
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("each model profile must be a JSON object")
        store.upsert(item)
    return store


def validate_bind_host(host: str) -> str:
    """Fail closed unless the control service binds to a loopback interface."""

    normalized = host.strip()
    if normalized == "localhost":
        return normalized
    try:
        address = ip_address(normalized)
    except ValueError as error:
        raise ValueError(
            "model control service host must be a loopback address or localhost"
        ) from error
    if not address.is_loopback:
        raise ValueError(
            "model control service host must be a loopback address or localhost"
        )
    return normalized


def run_model_control_service(
    *,
    host: str | None = None,
    port: int | None = None,
    store: ModelProfileStore | None = None,
) -> None:
    bind_host = validate_bind_host(
        host
        or os.environ.get(
            "REVERSE_AGENT_MODEL_CONTROL_HOST",
            "127.0.0.1",
        )
    )
    bind_port = port or int(os.environ.get("REVERSE_AGENT_MODEL_CONTROL_PORT", "8765"))
    allowed_origin = os.environ.get(
        "REVERSE_AGENT_MODEL_CONTROL_ORIGIN", "http://localhost:5173"
    )
    live_enabled = os.environ.get("REVERSE_AGENT_MODEL_CONTROL_LIVE") == "1"
    server = ThreadingHTTPServer(
        (bind_host, bind_port),
        _handler_factory(
            store or store_from_environment(),
            live_enabled=live_enabled,
            allowed_origin=allowed_origin,
        ),
    )
    server.serve_forever()


if __name__ == "__main__":
    run_model_control_service()
