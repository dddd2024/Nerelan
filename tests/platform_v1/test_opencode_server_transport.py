from __future__ import annotations

import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Event, Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from reverse_agent.platform_v1.opencode_server_transport import (
    OpenCodeServerClient,
    OpenCodeServerTransportError,
    ServerTransportResult,
    run_managed_server_role,
)


PASSWORD = "test-only-password"
AUTH = "Basic " + base64.b64encode(
    f"reverse-agent:{PASSWORD}".encode("utf-8")
).decode("ascii")


class _State:
    def __init__(self, directory: str, *, abort_result: bool = True) -> None:
        self.directory = directory
        self.abort_result = abort_result
        self.prompted = Event()
        self.calls: list[tuple[str, str]] = []
        self.prompt_body: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []


def _handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def _auth(self) -> bool:
            assert self.headers.get("Authorization") == AUTH
            return True

        def _json(self, status: int, payload: Any) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            self._auth()
            parsed = urlsplit(self.path)
            state.calls.append(("GET", parsed.path))
            if parsed.path == "/global/health":
                self._json(200, {"healthy": True, "version": "test-1"})
                return
            if parsed.path == "/event":
                assert parse_qs(parsed.query)["directory"] == [state.directory]
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(
                    b'data: {"type":"server.connected","properties":{}}\n\n'
                )
                self.wfile.flush()
                assert state.prompted.wait(2.0)
                for event in state.events:
                    raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
                    self.wfile.write(b"data: " + raw + b"\n\n")
                    self.wfile.flush()
                self.close_connection = True
                return
            self._json(404, {"error": "not-found"})

        def do_POST(self) -> None:  # noqa: N802
            self._auth()
            parsed = urlsplit(self.path)
            state.calls.append(("POST", parsed.path))
            query = parse_qs(parsed.query)
            if parsed.path != "/instance/dispose":
                assert query["directory"] == [state.directory]
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length)) if length else None
            if parsed.path == "/session":
                self._json(
                    200,
                    {
                        "id": "session-exact",
                        "directory": state.directory,
                        "title": body["title"],
                    },
                )
                return
            if parsed.path == "/session/session-exact/prompt_async":
                state.prompt_body = body
                state.prompted.set()
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if parsed.path == "/session/session-exact/abort":
                self._json(200, state.abort_result)
                return
            if parsed.path == "/instance/dispose":
                self._json(200, True)
                return
            self._json(404, {"error": "not-found"})

    return Handler


@contextmanager
def _fake_server(state: _State):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def _usage_event(session_id: str = "session-exact") -> dict[str, Any]:
    return {
        "type": "message.updated",
        "properties": {
            "info": {
                "id": "message-one",
                "sessionID": session_id,
                "role": "assistant",
                "time": {"completed": 123},
                "cost": 0.125,
                "tokens": {
                    "input": 2,
                    "output": 3,
                    "reasoning": 4,
                    "cache": {"read": 5, "write": 6, "secret": "CACHE_SENTINEL"},
                },
                "password": "TOP_LEVEL_SENTINEL",
                "response": "must never cross the usage callback",
            }
        },
    }


def _client(base_url: str) -> OpenCodeServerClient:
    return OpenCodeServerClient(
        base_url=base_url,
        username="reverse-agent",
        password=PASSWORD,
        timeout=3.0,
    )


def test_server_client_runs_exact_session_and_projects_usage(tmp_path) -> None:
    state = _State(str(tmp_path.resolve()))
    state.events = [
        _usage_event("foreign-session"),
        _usage_event(),
        {"type": "session.idle", "properties": {"sessionID": "foreign-session"}},
        {"type": "session.idle", "properties": {"sessionID": "session-exact"}},
    ]
    observed: list[dict[str, Any]] = []
    with _fake_server(state) as base_url:
        result = _client(base_url).run_role(
            directory=state.directory,
            title="bounded",
            prompt="PROMPT_SENTINEL",
            provider_id="provider",
            model_id="model",
            agent="",
            usage_observer=lambda value: observed.append(dict(value)) or False,
        )

    assert result.success is True
    assert result.abort_state == "NOT_REQUESTED"
    assert result.usage_event_count == 1
    assert result.session_digest.startswith("session-")
    assert len(observed) == 1
    serialized = json.dumps(observed)
    assert "TOP_LEVEL_SENTINEL" not in serialized
    assert "CACHE_SENTINEL" not in serialized
    assert "response" not in serialized
    assert observed[0]["tokens"]["reasoning"] == 4
    assert state.prompt_body["parts"] == [
        {"type": "text", "text": "PROMPT_SENTINEL"}
    ]
    assert state.prompt_body["model"] == {
        "providerID": "provider",
        "modelID": "model",
    }


@pytest.mark.parametrize(
    ("abort_result", "expected"),
    [(True, "STREAM_ABORT_CONFIRMED"), (False, "STREAM_ABORT_UNKNOWN")],
)
def test_threshold_requests_exactly_one_honest_abort(
    tmp_path, abort_result: bool, expected: str
) -> None:
    state = _State(str(tmp_path.resolve()), abort_result=abort_result)
    state.events = [_usage_event()]
    with _fake_server(state) as base_url:
        result = _client(base_url).run_role(
            directory=state.directory,
            title="bounded",
            prompt="bounded prompt",
            provider_id="provider",
            model_id="model",
            agent="",
            usage_observer=lambda _: True,
        )

    assert result.success is False
    assert result.abort_state == expected
    assert result.failure_classification == (
        "stream_budget_abort_confirmed"
        if abort_result
        else "stream_budget_abort_unknown"
    )
    assert state.calls.count(("POST", "/session/session-exact/abort")) == 1
    assert state.calls.count(("POST", "/session/session-exact/prompt_async")) == 1


def test_disconnect_before_idle_fails_closed(tmp_path) -> None:
    state = _State(str(tmp_path.resolve()))
    state.events = [_usage_event("foreign-session")]
    with _fake_server(state) as base_url:
        with pytest.raises(
            OpenCodeServerTransportError, match="server_event_disconnected"
        ):
            _client(base_url).run_role(
                directory=state.directory,
                title="bounded",
                prompt="bounded prompt",
                provider_id="provider",
                model_id="model",
                agent="",
                usage_observer=lambda _: False,
            )


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:4096",
        "http://example.com:4096",
        "http://user:pass@127.0.0.1:4096",
        "http://127.0.0.1:4096/path",
        "http://127.0.0.1:4096?secret=value",
    ],
)
def test_server_client_rejects_every_noncanonical_endpoint(url: str) -> None:
    with pytest.raises(OpenCodeServerTransportError):
        OpenCodeServerClient(
            base_url=url,
            username="reverse-agent",
            password=PASSWORD,
            timeout=1.0,
        )


def test_managed_process_uses_transient_auth_without_result_exposure(
    tmp_path, monkeypatch
) -> None:
    import reverse_agent.platform_v1.opencode_server_transport as transport

    captured: dict[str, Any] = {}

    class Process:
        def poll(self):
            return None

        def wait(self, timeout):
            return 0

        def terminate(self):
            raise AssertionError("healthy fake child should dispose cleanly")

        def kill(self):
            raise AssertionError("healthy fake child should not be killed")

    def fake_popen(argv, **kwargs):
        captured["argv"] = argv
        captured["env"] = kwargs["env"]
        return Process()

    class Client:
        def __init__(self, **kwargs):
            captured["client_password"] = kwargs["password"]

        def health(self, **kwargs):
            return "test-1"

        def run_role(self, **kwargs):
            return ServerTransportResult(success=True, server_version="test-1")

        def dispose(self, **kwargs):
            return True

    monkeypatch.setattr(transport, "_reserve_loopback_port", lambda: 45678)
    monkeypatch.setattr(transport.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(transport, "OpenCodeServerClient", Client)
    result = run_managed_server_role(
        cli_path="C:/tools/opencode.exe",
        is_cmd=False,
        cwd=str(tmp_path),
        child_env={"PATH": "C:/tools"},
        timeout=2.0,
        title="bounded",
        prompt="PROMPT_SENTINEL",
        provider_id="provider",
        model_id="model",
        agent="",
        usage_observer=lambda _: False,
    )

    password = captured["env"]["OPENCODE_SERVER_PASSWORD"]
    assert password == captured["client_password"]
    assert len(password) >= 32
    assert password not in repr(result)
    assert password not in json.dumps(captured["argv"])
    assert captured["argv"] == [
        "C:/tools/opencode.exe",
        "serve",
        "--hostname",
        "127.0.0.1",
        "--port",
        "45678",
    ]
