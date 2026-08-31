"""Bounded OpenCode Server transport for Platform V1.

The transport deliberately implements only the small official API surface the
executor needs: health, session creation, the project SSE stream, asynchronous
prompt submission, session abort, and instance disposal.  It never persists
raw events or content and it accepts only an executor-created loopback server.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


MAX_JSON_BYTES = 1_048_576
MAX_SSE_EVENT_BYTES = 262_144
SERVER_USERNAME = "reverse-agent"
_VERSION_RE = re.compile(r"^[A-Za-z0-9._+-]{1,64}$")
_PROVIDER_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")


class OpenCodeServerTransportError(RuntimeError):
    """A sanitized, closed-classification server transport failure."""


@dataclass(frozen=True)
class ServerTransportResult:
    success: bool
    failure_classification: str = ""
    abort_state: str = "NOT_REQUESTED"
    server_version: str = ""
    session_digest: str = ""
    usage_event_count: int = 0


@dataclass(frozen=True)
class ProviderAuthMethod:
    """Sanitized provider-advertised authentication method."""

    index: int
    type: str
    label: str


@dataclass(frozen=True)
class ProviderAuthAuthorization:
    """Transient browser continuation returned by OpenCode."""

    url: str
    method: str
    instructions: str


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise OpenCodeServerTransportError("server_redirect_forbidden")


def _safe_digest(value: str, prefix: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_child_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise OpenCodeServerTransportError(f"invalid_server_{name}")
    return value


def _validate_loopback_base_url(base_url: str) -> str:
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError as exc:
        raise OpenCodeServerTransportError("invalid_server_url") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise OpenCodeServerTransportError("server_endpoint_not_loopback")
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"http://{host}:{port}"


def _usage_projection(info: Mapping[str, Any]) -> dict[str, Any]:
    """Project one assistant message onto the closed numeric usage shape."""

    time_value = info.get("time")
    tokens_value = info.get("tokens")
    tokens = tokens_value if isinstance(tokens_value, Mapping) else {}
    cache_value = tokens.get("cache")
    cache = cache_value if isinstance(cache_value, Mapping) else {}
    return {
        "id": _validate_child_id(info.get("id"), "message_id"),
        "sessionID": _validate_child_id(info.get("sessionID"), "session_id"),
        "role": "assistant",
        "time": {
            "completed": (
                time_value.get("completed")
                if isinstance(time_value, Mapping)
                else None
            )
        },
        "cost": info.get("cost"),
        "tokens": {
            "input": tokens.get("input"),
            "output": tokens.get("output"),
            "reasoning": tokens.get("reasoning"),
            "cache": {
                "read": cache.get("read"),
                "write": cache.get("write"),
            },
        },
    }


class OpenCodeServerClient:
    """Minimal authenticated client for one executor-owned server process."""

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        timeout: float,
    ) -> None:
        self.base_url = _validate_loopback_base_url(base_url)
        if not username or not password:
            raise OpenCodeServerTransportError("server_basic_auth_required")
        self.timeout = max(0.1, float(timeout))
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        self._authorization = f"Basic {token}"
        self._opener = build_opener(_NoRedirect())

    def health(self, *, timeout: float | None = None) -> str:
        payload = self._json_request("GET", "/global/health", timeout=timeout)
        if not isinstance(payload, Mapping) or payload.get("healthy") is not True:
            raise OpenCodeServerTransportError("server_health_invalid")
        version = payload.get("version")
        if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
            raise OpenCodeServerTransportError("server_version_invalid")
        return version

    def create_session(self, *, directory: str, title: str) -> str:
        payload = self._json_request(
            "POST",
            "/session",
            query={"directory": directory},
            body={"title": title[:128]},
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("session_create_invalid")
        session_id = _validate_child_id(payload.get("id"), "session_id")
        returned_directory = payload.get("directory")
        if not isinstance(returned_directory, str):
            raise OpenCodeServerTransportError("session_directory_missing")
        if Path(returned_directory).resolve() != Path(directory).resolve():
            raise OpenCodeServerTransportError("session_directory_mismatch")
        return session_id

    def prompt_async(
        self,
        *,
        directory: str,
        session_id: str,
        prompt: str,
        provider_id: str,
        model_id: str,
        agent: str,
    ) -> None:
        body: dict[str, Any] = {
            "parts": [{"type": "text", "text": prompt}],
        }
        if agent:
            body["agent"] = agent
        if provider_id and model_id:
            body["model"] = {"providerID": provider_id, "modelID": model_id}
        self._empty_request(
            "POST",
            f"/session/{quote(session_id, safe='')}/prompt_async",
            query={"directory": directory},
            body=body,
            expected_status=204,
        )

    def abort(self, *, directory: str, session_id: str) -> bool:
        payload = self._json_request(
            "POST",
            f"/session/{quote(session_id, safe='')}/abort",
            query={"directory": directory},
        )
        return payload is True

    def dispose(self, *, directory: str) -> bool:
        try:
            payload = self._json_request(
                "POST", "/instance/dispose", query={"directory": directory}
            )
        except OpenCodeServerTransportError:
            return False
        return payload is True

    def provider_auth_methods(
        self, *, directory: str, provider_id: str
    ) -> tuple[ProviderAuthMethod, ...]:
        """Return only bounded methods advertised for one exact provider."""

        provider = _validate_provider_id(provider_id)
        payload = self._json_request(
            "GET", "/provider/auth", query={"directory": directory}
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("provider_auth_methods_invalid")
        raw_methods = payload.get(provider)
        if not isinstance(raw_methods, list):
            raise OpenCodeServerTransportError("provider_auth_method_missing")
        methods: list[ProviderAuthMethod] = []
        for index, raw in enumerate(raw_methods):
            if not isinstance(raw, Mapping):
                raise OpenCodeServerTransportError("provider_auth_method_invalid")
            method_type = raw.get("type")
            label = raw.get("label")
            if method_type not in {"oauth", "api"}:
                raise OpenCodeServerTransportError("provider_auth_type_invalid")
            if (
                not isinstance(label, str)
                or not label.strip()
                or len(label) > 200
                or any(ord(char) < 32 for char in label)
            ):
                raise OpenCodeServerTransportError("provider_auth_label_invalid")
            methods.append(
                ProviderAuthMethod(index=index, type=method_type, label=label.strip())
            )
        return tuple(methods)

    def provider_oauth_authorize(
        self, *, directory: str, provider_id: str, method_index: int
    ) -> ProviderAuthAuthorization:
        provider = _validate_provider_id(provider_id)
        index = _validate_method_index(method_index)
        payload = self._json_request(
            "POST",
            f"/provider/{quote(provider, safe='')}/oauth/authorize",
            query={"directory": directory},
            body={"method": index},
        )
        if not isinstance(payload, Mapping):
            raise OpenCodeServerTransportError("provider_oauth_authorization_invalid")
        url = payload.get("url")
        callback_method = payload.get("method")
        instructions = payload.get("instructions")
        try:
            parsed = urlsplit(url) if isinstance(url, str) else None
        except ValueError as exc:
            raise OpenCodeServerTransportError(
                "provider_oauth_authorization_url_invalid"
            ) from exc
        if (
            parsed is None
            or parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or len(url) > 8192
        ):
            raise OpenCodeServerTransportError(
                "provider_oauth_authorization_url_invalid"
            )
        if callback_method not in {"auto", "code"}:
            raise OpenCodeServerTransportError("provider_oauth_callback_method_invalid")
        if not isinstance(instructions, str) or len(instructions) > 2000:
            raise OpenCodeServerTransportError("provider_oauth_instructions_invalid")
        return ProviderAuthAuthorization(
            url=url,
            method=callback_method,
            instructions=instructions,
        )

    def provider_oauth_callback(
        self,
        *,
        directory: str,
        provider_id: str,
        method_index: int,
        code: str | None = None,
    ) -> bool:
        provider = _validate_provider_id(provider_id)
        index = _validate_method_index(method_index)
        body: dict[str, Any] = {"method": index}
        if code is not None:
            if not isinstance(code, str) or not code or len(code) > 4096:
                raise OpenCodeServerTransportError("provider_oauth_code_invalid")
            body["code"] = code
        payload = self._json_request(
            "POST",
            f"/provider/{quote(provider, safe='')}/oauth/callback",
            query={"directory": directory},
            body=body,
        )
        if not isinstance(payload, bool):
            raise OpenCodeServerTransportError("provider_oauth_callback_invalid")
        return payload

    def run_role(
        self,
        *,
        directory: str,
        title: str,
        prompt: str,
        provider_id: str,
        model_id: str,
        agent: str,
        usage_observer: Callable[[Mapping[str, Any]], bool],
    ) -> ServerTransportResult:
        """Run one exact-session role and return only sanitized control facts."""

        deadline = time.monotonic() + self.timeout
        version = self.health(timeout=self._remaining(deadline))
        stream = self._open_sse(directory=directory, timeout=self._remaining(deadline))
        session_id = ""
        usage_count = 0
        try:
            first = self._read_sse_event(stream, deadline)
            if first.get("type") != "server.connected":
                raise OpenCodeServerTransportError("server_connected_event_missing")
            session_id = self.create_session(directory=directory, title=title)
            self.prompt_async(
                directory=directory,
                session_id=session_id,
                prompt=prompt,
                provider_id=provider_id,
                model_id=model_id,
                agent=agent,
            )
            while True:
                event = self._read_sse_event(stream, deadline)
                event_type = event.get("type")
                properties = event.get("properties")
                if not isinstance(properties, Mapping):
                    continue
                if event_type == "message.updated":
                    info = properties.get("info")
                    if not isinstance(info, Mapping):
                        continue
                    if info.get("sessionID") != session_id or info.get("role") != "assistant":
                        continue
                    completed = info.get("time")
                    if not isinstance(completed, Mapping) or not completed.get("completed"):
                        continue
                    projected = _usage_projection(info)
                    usage_count += 1
                    if usage_observer(projected):
                        try:
                            confirmed = self.abort(
                                directory=directory, session_id=session_id
                            )
                        except OpenCodeServerTransportError:
                            confirmed = False
                        return ServerTransportResult(
                            success=False,
                            failure_classification=(
                                "stream_budget_abort_confirmed"
                                if confirmed
                                else "stream_budget_abort_unknown"
                            ),
                            abort_state=(
                                "STREAM_ABORT_CONFIRMED"
                                if confirmed
                                else "STREAM_ABORT_UNKNOWN"
                            ),
                            server_version=version,
                            session_digest=_safe_digest(session_id, "session-"),
                            usage_event_count=usage_count,
                        )
                    continue
                bound_session = properties.get("sessionID")
                if event_type == "session.idle" and bound_session == session_id:
                    return ServerTransportResult(
                        success=True,
                        server_version=version,
                        session_digest=_safe_digest(session_id, "session-"),
                        usage_event_count=usage_count,
                    )
                if event_type == "session.error" and bound_session == session_id:
                    return ServerTransportResult(
                        success=False,
                        failure_classification="server_session_error",
                        server_version=version,
                        session_digest=_safe_digest(session_id, "session-"),
                        usage_event_count=usage_count,
                    )
        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _open_sse(self, *, directory: str, timeout: float):
        request = self._request(
            "GET", "/event", query={"directory": directory}, accept="text/event-stream"
        )
        try:
            response = self._opener.open(request, timeout=timeout)
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_event_connect_failed") from exc
        content_type = response.headers.get_content_type()
        if content_type != "text/event-stream":
            response.close()
            raise OpenCodeServerTransportError("server_event_content_type_invalid")
        return response

    def _read_sse_event(self, stream: Any, deadline: float) -> Mapping[str, Any]:
        data_lines: list[bytes] = []
        total = 0
        while True:
            if self._remaining(deadline) <= 0:
                raise OpenCodeServerTransportError("server_event_timeout")
            try:
                line = stream.readline(MAX_SSE_EVENT_BYTES + 1)
            except (TimeoutError, OSError) as exc:
                raise OpenCodeServerTransportError("server_event_timeout") from exc
            if not line:
                raise OpenCodeServerTransportError("server_event_disconnected")
            total += len(line)
            if total > MAX_SSE_EVENT_BYTES:
                raise OpenCodeServerTransportError("server_event_too_large")
            if line in {b"\n", b"\r\n"}:
                if not data_lines:
                    total = 0
                    continue
                raw = b"\n".join(data_lines)
                try:
                    event = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise OpenCodeServerTransportError("server_event_malformed") from exc
                if not isinstance(event, Mapping):
                    raise OpenCodeServerTransportError("server_event_shape_invalid")
                return event
            if line.startswith(b"data:"):
                value = line[5:]
                if value.startswith(b" "):
                    value = value[1:]
                data_lines.append(value.rstrip(b"\r\n"))

    def _json_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        request = self._request(method, path, query=query, body=body, accept="application/json")
        try:
            response = self._opener.open(request, timeout=timeout or self.timeout)
            with response:
                if response.headers.get_content_type() != "application/json":
                    raise OpenCodeServerTransportError("server_json_content_type_invalid")
                raw = response.read(MAX_JSON_BYTES + 1)
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_http_request_failed") from exc
        if len(raw) > MAX_JSON_BYTES:
            raise OpenCodeServerTransportError("server_json_too_large")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OpenCodeServerTransportError("server_json_malformed") from exc

    def _empty_request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str],
        body: Mapping[str, Any],
        expected_status: int,
    ) -> None:
        request = self._request(method, path, query=query, body=body, accept="application/json")
        try:
            response = self._opener.open(request, timeout=self.timeout)
            with response:
                if response.status != expected_status:
                    raise OpenCodeServerTransportError("server_http_status_invalid")
                if response.read(1):
                    raise OpenCodeServerTransportError("server_empty_response_expected")
        except OpenCodeServerTransportError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise OpenCodeServerTransportError("server_http_request_failed") from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = None,
        body: Mapping[str, Any] | None = None,
        accept: str,
    ) -> Request:
        if not path.startswith("/") or "//" in path or "?" in path or "#" in path:
            raise OpenCodeServerTransportError("server_request_path_invalid")
        url = self.base_url + path
        if query:
            url += "?" + urlencode(query)
        data = None
        headers = {"Accept": accept, "Authorization": self._authorization}
        if body is not None:
            data = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            if len(data) > MAX_JSON_BYTES:
                raise OpenCodeServerTransportError("server_request_too_large")
            headers["Content-Type"] = "application/json"
        return Request(url, data=data, headers=headers, method=method)

    @staticmethod
    def _remaining(deadline: float) -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise OpenCodeServerTransportError("server_event_timeout")
        return remaining


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _validate_provider_id(value: Any) -> str:
    if not isinstance(value, str) or not _PROVIDER_ID_RE.fullmatch(value):
        raise OpenCodeServerTransportError("provider_id_invalid")
    return value


def _validate_method_index(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise OpenCodeServerTransportError("provider_auth_method_index_invalid")
    return value


@dataclass
class ManagedOpenCodeServer:
    """One authenticated loopback OpenCode child with deterministic cleanup."""

    process: Any
    client: OpenCodeServerClient
    directory: str
    _closed: bool = False

    def provider_auth_methods(
        self, *, provider_id: str
    ) -> tuple[ProviderAuthMethod, ...]:
        return self.client.provider_auth_methods(
            directory=self.directory, provider_id=provider_id
        )

    def provider_oauth_authorize(
        self, *, provider_id: str, method_index: int
    ) -> ProviderAuthAuthorization:
        return self.client.provider_oauth_authorize(
            directory=self.directory,
            provider_id=provider_id,
            method_index=method_index,
        )

    def provider_oauth_callback(
        self, *, provider_id: str, method_index: int, code: str | None = None
    ) -> bool:
        return self.client.provider_oauth_callback(
            directory=self.directory,
            provider_id=provider_id,
            method_index=method_index,
            code=code,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.client.dispose(directory=self.directory)
        try:
            self.process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2.0)


def start_managed_server(
    *,
    cli_path: str,
    is_cmd: bool,
    cwd: str,
    child_env: Mapping[str, str],
    timeout: float,
) -> ManagedOpenCodeServer:
    """Start one authenticated loopback server and return after health passes."""

    password = secrets.token_urlsafe(32)
    env = dict(child_env)
    env["OPENCODE_SERVER_USERNAME"] = SERVER_USERNAME
    env["OPENCODE_SERVER_PASSWORD"] = password
    port = _reserve_loopback_port()
    server_args = ["serve", "--hostname", "127.0.0.1", "--port", str(port)]
    if is_cmd:
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        argv = [comspec, "/d", "/s", "/c", cli_path, *server_args]
    else:
        argv = [cli_path, *server_args]
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except (FileNotFoundError, OSError) as exc:
        raise OpenCodeServerTransportError("server_process_start_failed") from exc
    client = OpenCodeServerClient(
        base_url=f"http://127.0.0.1:{port}",
        username=SERVER_USERNAME,
        password=password,
        timeout=timeout,
    )
    managed = ManagedOpenCodeServer(process=process, client=client, directory=cwd)
    try:
        deadline = time.monotonic() + min(float(timeout), 10.0)
        while True:
            if process.poll() is not None:
                raise OpenCodeServerTransportError("server_process_exited_before_health")
            try:
                client.health(timeout=min(0.25, max(0.1, deadline - time.monotonic())))
                return managed
            except OpenCodeServerTransportError:
                if time.monotonic() >= deadline:
                    raise OpenCodeServerTransportError("server_health_timeout")
                time.sleep(0.05)
    except Exception:
        managed.close()
        raise


def run_managed_server_role(
    *,
    cli_path: str,
    is_cmd: bool,
    cwd: str,
    child_env: Mapping[str, str],
    timeout: float,
    title: str,
    prompt: str,
    provider_id: str,
    model_id: str,
    agent: str,
    usage_observer: Callable[[Mapping[str, Any]], bool],
) -> ServerTransportResult:
    """Start, use, and stop exactly one authenticated loopback server child."""

    managed = start_managed_server(
        cli_path=cli_path,
        is_cmd=is_cmd,
        cwd=cwd,
        child_env=child_env,
        timeout=timeout,
    )
    try:
        return managed.client.run_role(
            directory=cwd,
            title=title,
            prompt=prompt,
            provider_id=provider_id,
            model_id=model_id,
            agent=agent,
            usage_observer=usage_observer,
        )
    finally:
        managed.close()
