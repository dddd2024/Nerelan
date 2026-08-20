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

    password = secrets.token_urlsafe(32)
    env = dict(child_env)
    env["OPENCODE_SERVER_USERNAME"] = SERVER_USERNAME
    env["OPENCODE_SERVER_PASSWORD"] = password
    port = _reserve_loopback_port()
    server_args = [
        "serve", "--hostname", "127.0.0.1", "--port", str(port)
    ]
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
    try:
        deadline = time.monotonic() + min(float(timeout), 10.0)
        while True:
            if process.poll() is not None:
                raise OpenCodeServerTransportError("server_process_exited_before_health")
            try:
                client.health(timeout=min(0.25, max(0.1, deadline - time.monotonic())))
                break
            except OpenCodeServerTransportError:
                if time.monotonic() >= deadline:
                    raise OpenCodeServerTransportError("server_health_timeout")
                time.sleep(0.05)
        return client.run_role(
            directory=cwd,
            title=title,
            prompt=prompt,
            provider_id=provider_id,
            model_id=model_id,
            agent=agent,
            usage_observer=usage_observer,
        )
    finally:
        client.dispose(directory=cwd)
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
