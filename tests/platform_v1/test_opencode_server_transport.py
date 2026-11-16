from __future__ import annotations

import base64
from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
from threading import Event, Thread
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from reverse_agent.platform_v1.opencode_server_transport import (
    _DeadlineReader,
    _DeadlineSSEStream,
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
        self.auth_methods: Any = {
            "openai": [
                {"type": "api", "label": "API key"},
                {"type": "oauth", "label": "ChatGPT Plus/Pro"},
            ]
        }
        self.oauth_authorization: Any = {
            "url": "https://auth.example.test/authorize?state=opaque",
            "method": "code",
            "instructions": "Paste the returned code.",
        }
        self.oauth_callback_result: Any = True
        self.oauth_bodies: list[dict[str, Any]] = []


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
            if parsed.path == "/provider/auth":
                assert parse_qs(parsed.query)["directory"] == [state.directory]
                self._json(200, state.auth_methods)
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
            if parsed.path == "/provider/openai/oauth/authorize":
                state.oauth_bodies.append(body)
                self._json(200, state.oauth_authorization)
                return
            if parsed.path == "/provider/openai/oauth/callback":
                state.oauth_bodies.append(body)
                self._json(200, state.oauth_callback_result)
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


def _timed_role(monkeypatch, chunks, *, timeout=100, idle_timeout=5, abort_result=True, usage_observer=None):
    """A fake clock and one-read response exercise the production SSE reader."""
    from types import SimpleNamespace
    import reverse_agent.platform_v1.opencode_server_transport as transport
    clock = [0.0]
    monkeypatch.setattr(transport, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    class Response:
        def __init__(self):
            self.chunks = list(chunks)
            self.timeouts = []
            self.closed = False
            self.fp = SimpleNamespace(raw=SimpleNamespace(_sock=self))
        def settimeout(self, value):
            self.timeouts.append(value)
        def read1(self, limit):
            if not self.chunks:
                clock[0] += self.timeouts[-1]
                raise TimeoutError
            delay, content = self.chunks.pop(0)
            if delay >= self.timeouts[-1]:
                clock[0] += self.timeouts[-1]
                raise TimeoutError
            clock[0] += delay
            if len(content) > limit:
                self.chunks.insert(0, (0, content[limit:]))
            return content[:limit]
        def close(self):
            self.closed = True
    response = Response()
    client = OpenCodeServerClient(base_url="http://127.0.0.1:12345", username="test", password=PASSWORD,
                                  timeout=timeout, idle_timeout=idle_timeout)
    monkeypatch.setattr(client, "health", lambda **kw: "test")
    monkeypatch.setattr(client, "_open_sse", lambda **kw: response)
    monkeypatch.setattr(client, "create_session", lambda **kw: "session-exact")
    monkeypatch.setattr(client, "prompt_async", lambda **kw: None)
    calls = []
    def abort(**kwargs):
        calls.append(kwargs)
        if abort_result is None:
            raise OpenCodeServerTransportError("server_http_request_failed")
        return abort_result
    monkeypatch.setattr(client, "abort", abort)
    def run():
        return client.run_role(directory=".", title="test", prompt="PROMPT_SENTINEL", provider_id="p",
                               model_id="m", agent="", usage_observer=usage_observer or (lambda _: False))
    return run, response, calls, clock


def _event(kind, properties=None):
    return b"data: " + json.dumps({"type": kind, "properties": properties or {}}).encode() + b"\n\n"


@pytest.mark.parametrize("abort_result", [True, False, None])
def test_idle_deadline_ignores_keepalives_and_foreign_session(monkeypatch, abort_result):
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")), (2, b": keepalive\n\n"),
        (2, _event("message.part.delta", {"sessionID": "foreign", "field": "text", "delta": "SECRET"})),
        (2, _event("session.idle", {"sessionID": "session-exact"})),
    ], abort_result=abort_result)
    result = run()
    assert result.failure_classification == "server_stream_stalled" and clock[0] == 5
    assert result.abort_state == ("STREAM_ABORT_CONFIRMED" if abort_result else "STREAM_ABORT_UNKNOWN")
    assert len(calls) == 1 and calls[0]["session_id"] == "session-exact"
    assert stream.closed
    assert "SECRET" not in repr(result) and "PROMPT_SENTINEL" not in repr(result) and PASSWORD not in repr(result)


def test_session_progress_refreshes_idle_without_extending_total_deadline(monkeypatch):
    events = [(0, _event("server.connected")),
              (4, _event("message.part.delta", {"sessionID": "session-exact", "field": "text", "delta": "progress"})),
              (4, _event("session.idle", {"sessionID": "session-exact"}))]
    run, stream, calls, clock = _timed_role(monkeypatch, events)
    assert run().success and clock[0] == 8 and calls == [] and stream.closed
    run, stream, calls, clock = _timed_role(monkeypatch, events, timeout=7)
    result = run()
    assert result.failure_classification == "server_role_deadline_exceeded" and clock[0] == 7
    assert len(calls) == 1 and stream.closed


def test_repeated_identical_tool_update_is_not_fresh_progress(monkeypatch):
    tool = {"part": {"id": "tool", "sessionID": "session-exact", "type": "tool", "state": {"status": "running"}}}
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")), (4, _event("message.part.updated", tool)),
        (4, _event("message.part.updated", tool)), (3, b": keepalive\n\n")])
    assert run().failure_classification == "server_stream_stalled" and clock[0] == 9
    assert stream.closed and len(calls) == 1


@pytest.mark.parametrize("kind", ["part", "message"])
def test_replay_beyond_recent_identity_capacity_cannot_extend_idle(monkeypatch, kind):
    def event(index):
        if kind == "part":
            return _event("message.part.updated", {"part": {
                "id": f"tool-{index}", "sessionID": "session-exact", "type": "tool",
                "state": {"status": "running"}}})
        properties = _usage_event()["properties"]
        properties["info"]["id"] = f"message-{index}"
        return _event("message.updated", properties)

    events = [event(index) for index in range(513)]
    chunks = [(0, _event("server.connected"))]
    chunks += [(0.001, data) for data in events] + [(0.05, data) for data in events]
    chunks.append((0.01, _event("session.idle", {"sessionID": "session-exact"})))
    run, stream, calls, clock = _timed_role(monkeypatch, chunks, idle_timeout=0.1)
    result = run()
    assert result.failure_classification == "server_stream_stalled"
    assert clock[0] == pytest.approx(0.613)
    assert stream.closed and len(calls) == 1


def test_new_and_updated_tools_keep_progress_beyond_recent_identity_capacity(monkeypatch):
    def update(index, state):
        return _event("message.part.updated", {"part": {
            "id": f"tool-{index}", "sessionID": "session-exact", "type": "tool",
            "state": {"status": state}}})

    chunks = [(0, _event("server.connected"))]
    chunks += [(0.04, update(index, "running")) for index in range(1024)]
    chunks += [(0.04, update(index, "completed")) for index in range(1024)]
    chunks.append((0.04, _event("session.idle", {"sessionID": "session-exact"})))
    run, stream, calls, _ = _timed_role(monkeypatch, chunks, idle_timeout=0.1)
    assert run().success
    assert stream.closed and calls == []


@pytest.mark.parametrize("stop", [False, True])
def test_saturated_progress_filter_stays_bounded_without_losing_usage(monkeypatch, stop):
    import reverse_agent.platform_v1.opencode_server_transport as transport

    progress = transport._ProgressFilter()
    size = len(progress.bits)
    progress.bits[:] = b"\xff" * size  # worst-case false positives are conservative
    monkeypatch.setattr(transport, "_ProgressFilter", lambda: progress)
    observed = []
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")), (4, _event("message.updated", _usage_event()["properties"])),
        (4, _event("session.idle", {"sessionID": "session-exact"})),
    ], usage_observer=lambda info: observed.append(info) or stop)
    result = run()
    assert result.failure_classification == ("stream_budget_abort_confirmed" if stop else "server_stream_stalled")
    assert clock[0] == (4 if stop else 5)
    assert result.usage_event_count == len(observed) == 1
    assert stream.closed and len(calls) == 1
    assert len(progress.bits) == size == transport.PROGRESS_FILTER_BYTES


def test_dribbled_partial_sse_line_cannot_extend_idle_deadline(monkeypatch):
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")), (2, b"data: {"), (2, b'"type":'), (2, b'"session.idle"}')])
    assert run().failure_classification == "server_stream_stalled" and clock[0] == 5
    assert stream.closed and len(calls) == 1


def test_alternating_identical_part_updates_do_not_refresh_idle(monkeypatch):
    tool_a = {
        "part": {
            "id": "tool-a",
            "sessionID": "session-exact",
            "type": "tool",
            "state": {"status": "running"},
        }
    }
    tool_b = {
        "part": {
            "id": "tool-b",
            "sessionID": "session-exact",
            "type": "tool",
            "state": {"status": "running"},
        }
    }
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")),
        (4, _event("message.part.updated", tool_a)),
        (4, _event("message.part.updated", tool_b)),
        (4, _event("message.part.updated", tool_a)),
        (4, _event("message.part.updated", tool_b)),
        (4, _event("session.idle", {"sessionID": "session-exact"})),
    ])
    result = run()
    assert result.failure_classification == "server_stream_stalled"
    assert clock[0] == 13
    assert result.abort_state == "STREAM_ABORT_CONFIRMED"
    assert stream.closed and len(calls) == 1


def test_replayed_completed_message_does_not_refresh_idle(monkeypatch):
    properties = _usage_event()["properties"]
    run, stream, calls, clock = _timed_role(monkeypatch, [
        (0, _event("server.connected")),
        (4, _event("message.updated", properties)),
        (1, _event("message.updated", properties)),
        (4, b": keepalive\n\n"),
    ])
    result = run()
    assert result.failure_classification == "server_stream_stalled"
    assert clock[0] == 9
    assert result.usage_event_count == 1
    assert stream.closed and len(calls) == 1


def test_absolute_deadline_holds_below_real_chunked_framing() -> None:
    client_sock, peer_sock = socket.socketpair()
    stop = Event()

    def dribble() -> None:
        try:
            peer_sock.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/event-stream\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n"
            )
            # HTTPResponse parses the chunk-size/extension line through a
            # buffered readline; dribbling bytes keeps that readline alive.
            for _ in range(200):
                if stop.is_set():
                    break
                peer_sock.sendall(b"a")
                time.sleep(0.02)
        except OSError:
            pass
        finally:
            peer_sock.close()

    responder = Thread(target=dribble, daemon=True)
    responder.start()
    response = http.client.HTTPResponse(client_sock, method="GET")
    try:
        response.begin()
        stream = _DeadlineSSEStream(response)
        stream.deadline = time.monotonic() + 0.1
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            stream.readline(1024)
        assert time.monotonic() - started < 0.5
    finally:
        stop.set()
        try:
            response.close()
        finally:
            client_sock.close()
        responder.join(timeout=2.0)


def test_dribbled_chunk_extension_times_out_near_absolute_deadline() -> None:
    """#1548/#1549 counterexample: one chunk-extension byte every 0.03 s.

    Before the fix a per-read relative timeout let this peer hold a 0.1 s
    absolute deadline open for about 0.366 s.  Each underlying read is now
    armed with the remaining absolute budget, so the read stops near 0.1 s.
    """

    client_sock, peer_sock = socket.socketpair()
    stop = Event()

    def dribble() -> None:
        try:
            peer_sock.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/event-stream\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n"
                b"40;ext="
            )
            for _ in range(100):
                if stop.is_set():
                    break
                peer_sock.sendall(b"x")
                time.sleep(0.03)
        except OSError:
            pass
        finally:
            peer_sock.close()

    responder = Thread(target=dribble, daemon=True)
    responder.start()
    response = http.client.HTTPResponse(client_sock, method="GET")
    try:
        response.begin()
        stream = _DeadlineSSEStream(response)
        started = time.monotonic()
        stream.deadline = started + 0.1
        with pytest.raises(TimeoutError):
            stream.readline(1024)
        elapsed = time.monotonic() - started
        assert 0.09 <= elapsed < 0.25, elapsed
    finally:
        stop.set()
        try:
            response.close()
        finally:
            client_sock.close()
        responder.join(timeout=2.0)


def _chunked_socketpair(
    *, split_chunk_header: bool = False, chunk_extension: bool = False
) -> tuple[socket.socket, socket.socket, Thread]:
    """Open a real socketpair that serves one complete chunked SSE body."""

    client_sock, peer_sock = socket.socketpair()
    body = b'data: {"type":"server.connected","properties":{}}\n\n'

    def serve() -> None:
        try:
            peer_sock.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/event-stream\r\n"
                b"Transfer-Encoding: chunked\r\n\r\n"
            )
            size = b"%x" % len(body)
            if chunk_extension:
                size += b";chunk-ext=1"
            if split_chunk_header:
                # Deliver the chunk-size line across two reads so the
                # framing line is only complete after a second read.
                peer_sock.sendall(size[:1])
                time.sleep(0.05)
                peer_sock.sendall(size[1:] + b"\r\n")
            else:
                peer_sock.sendall(size + b"\r\n")
            peer_sock.sendall(body + b"\r\n")
            peer_sock.sendall(b"0\r\n\r\n")
        except OSError:
            pass
        finally:
            peer_sock.close()

    thread = Thread(target=serve, daemon=True)
    thread.start()
    return client_sock, peer_sock, thread


def _read_chunked_line(client_sock: socket.socket, peer_sock: socket.socket) -> bytes:
    response = http.client.HTTPResponse(client_sock, method="GET")
    try:
        response.begin()
        stream = _DeadlineSSEStream(response)
        stream.deadline = time.monotonic() + 5.0
        return stream.readline(1024)
    finally:
        response.close()
        client_sock.close()


def test_healthy_chunked_response_is_not_reported_as_incomplete_read() -> None:
    """A complete chunked session must not fail as IncompleteRead(0 bytes)."""

    client_sock, peer_sock, thread = _chunked_socketpair()
    try:
        line = _read_chunked_line(client_sock, peer_sock)
    finally:
        peer_sock.close()
        thread.join(timeout=2.0)

    assert line.startswith(b'data: {"type":"server.connected"')


def test_chunk_size_line_split_across_reads_is_reassembled() -> None:
    """A chunk-size line delivered in two reads must still frame the body."""

    client_sock, peer_sock, thread = _chunked_socketpair(split_chunk_header=True)
    try:
        line = _read_chunked_line(client_sock, peer_sock)
    finally:
        peer_sock.close()
        thread.join(timeout=2.0)

    assert line.startswith(b'data: {"type":"server.connected"')


def test_chunk_extension_line_does_not_break_framing() -> None:
    """A chunk-extension line must be stripped, not treated as payload."""

    client_sock, peer_sock, thread = _chunked_socketpair(chunk_extension=True)
    try:
        line = _read_chunked_line(client_sock, peer_sock)
    finally:
        peer_sock.close()
        thread.join(timeout=2.0)

    assert line.startswith(b'data: {"type":"server.connected"')


def test_peek_with_partial_pending_reads_forward_and_arms_deadline() -> None:
    """peek() must not spin on the bytes it already holds."""

    class FakeStream:
        def __init__(self) -> None:
            self.calls = 0

        def read1(self, size: int) -> bytes:
            self.calls += 1
            if self.calls > 2:
                raise TimeoutError("no more data")
            return b"ab"

    class FakeSocket:
        def __init__(self) -> None:
            self.timeouts: list[float] = []

        def settimeout(self, value: float) -> None:
            self.timeouts.append(value)

    stream = FakeStream()
    sock = FakeSocket()
    reader = _DeadlineReader(stream, sock, lambda: time.monotonic() + 5.0)
    reader.pending.extend(b"xy")

    with pytest.raises(TimeoutError):
        reader.peek(4096)

    # The held bytes survive, the underlying stream was actually read and
    # the loop terminated instead of re-inserting the same bytes forever.
    assert bytes(reader.pending[:2]) == b"xy"
    assert stream.calls > 1
    # Every read below the deadline armed the socket with the remaining
    # absolute budget instead of extending it.
    assert sock.timeouts
    assert all(0 < value <= 5.0 for value in sock.timeouts)


def test_peek_raises_when_the_absolute_deadline_has_passed() -> None:
    class EmptyStream:
        def read1(self, size: int) -> bytes:
            raise AssertionError("an expired deadline must not reach the socket")

    reader = _DeadlineReader(EmptyStream(), None, lambda: time.monotonic() - 1.0)
    reader.pending.extend(b"partial")

    with pytest.raises(TimeoutError):
        reader.peek(4096)


def test_peek_returns_pending_bytes_when_the_stream_is_exhausted() -> None:
    class EmptyStream:
        def read1(self, size: int) -> bytes:
            return b""

    reader = _DeadlineReader(EmptyStream(), None, lambda: time.monotonic() + 5.0)
    reader.pending.extend(b"partial")

    assert reader.peek(4096) == b"partial"
    assert bytes(reader.pending) == b"partial"


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


def test_provider_oauth_surface_is_bounded_and_sanitized(tmp_path) -> None:
    state = _State(str(tmp_path.resolve()))
    with _fake_server(state) as base_url:
        client = _client(base_url)
        methods = client.provider_auth_methods(
            directory=state.directory, provider_id="openai"
        )
        authorization = client.provider_oauth_authorize(
            directory=state.directory,
            provider_id="openai",
            method_index=methods[1].index,
        )
        completed = client.provider_oauth_callback(
            directory=state.directory,
            provider_id="openai",
            method_index=methods[1].index,
            code="TRANSIENT_CODE_SENTINEL",
        )

    assert [(method.index, method.type, method.label) for method in methods] == [
        (0, "api", "API key"),
        (1, "oauth", "ChatGPT Plus/Pro"),
    ]
    assert authorization.url.startswith("https://auth.example.test/")
    assert authorization.method == "code"
    assert completed is True
    assert state.oauth_bodies == [
        {"method": 1},
        {"method": 1, "code": "TRANSIENT_CODE_SENTINEL"},
    ]


@pytest.mark.parametrize(
    ("provider_id", "method_index"),
    [("../openai", 0), ("openai/other", 0), ("openai", -1), ("openai", True)],
)
def test_provider_oauth_rejects_unadvertised_path_inputs(
    tmp_path, provider_id: str, method_index: Any
) -> None:
    state = _State(str(tmp_path.resolve()))
    with _fake_server(state) as base_url:
        with pytest.raises(OpenCodeServerTransportError):
            _client(base_url).provider_oauth_authorize(
                directory=state.directory,
                provider_id=provider_id,
                method_index=method_index,
            )


@pytest.mark.parametrize(
    "authorization",
    [
        {"url": "http://auth.example.test", "method": "auto", "instructions": ""},
        {"url": "https://user:pass@auth.example.test", "method": "auto", "instructions": ""},
        {"url": "https://auth.example.test/#token", "method": "auto", "instructions": ""},
        {"url": "https://auth.example.test/", "method": "other", "instructions": ""},
    ],
)
def test_provider_oauth_rejects_invalid_authorization_response(
    tmp_path, authorization: dict[str, Any]
) -> None:
    state = _State(str(tmp_path.resolve()))
    state.oauth_authorization = authorization
    with _fake_server(state) as base_url:
        with pytest.raises(OpenCodeServerTransportError):
            _client(base_url).provider_oauth_authorize(
                directory=state.directory,
                provider_id="openai",
                method_index=1,
            )


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
