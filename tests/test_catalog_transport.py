"""Real isolated Python/owned-loopback fixtures, never real provider access."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

import pytest

from reverse_agent.model_access import catalog_transport as transport_module
from reverse_agent.model_access.catalog_transport import CatalogTransportError, catalog_transport
from reverse_agent.model_access.catalog_worker import MAX_BODY_BYTES


@contextmanager
def endpoint(respond):
    records = []
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            records.append((self.path, self.headers.get("Authorization")))
            try:
                respond(self, stop)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/models", records
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def reply(handler, body=b'{"data":[{"id":"synthetic-model"}]}', status=200):
    handler.send_response(status)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def capture_workers(monkeypatch):
    original = transport_module._popen
    children = []
    options = []

    def launch(argv, **kwargs):
        options.append((list(argv), dict(kwargs)))
        child = original(argv, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(transport_module, "_popen", launch)
    return children, options


def test_real_child_sends_one_get_and_keeps_synthetic_secret_in_private_pipe(monkeypatch, capsys):
    children, options = capture_workers(monkeypatch)
    secret = "synthetic-pipe-only-secret"
    monkeypatch.setenv("HTTPS_PROXY", "http://untrusted-proxy.invalid:1")
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted-proxy.invalid:1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-env-not-authority")
    body = b'{"data":[{"id":"synthetic-model"}]}'
    with endpoint(lambda h, _: reply(h, body)) as (url, records):
        assert catalog_transport(url, {"Accept": "application/json", "Authorization": f"Bearer {secret}"}, 3) == (200, body)
        assert records == [("/models", f"Bearer {secret}")]
    assert len(children) == 1 and children[0].poll() == 0
    argv, kwargs = options[0]
    assert argv[:3] == [sys.executable, "-I", "-B"]
    assert secret not in repr(argv) + repr(kwargs)
    assert "HTTP_PROXY" not in kwargs["env"] and "OPENAI_API_KEY" not in kwargs["env"]
    assert kwargs["stderr"] == subprocess.DEVNULL and kwargs["shell"] is False
    assert children[0].stdin.closed and children[0].stdout.closed
    output = capsys.readouterr()
    assert secret not in output.out + output.err


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_is_not_followed_even_with_synthetic_authorization(status):
    with endpoint(lambda h, _: reply(h)) as (sink, sink_records):
        def redirect(handler, _):
            handler.send_response(status)
            handler.send_header("Location", sink)
            handler.send_header("Content-Length", "0")
            handler.end_headers()

        with endpoint(redirect) as (url, records):
            assert catalog_transport(url, {"Authorization": "Bearer synthetic-redirect-secret"}, 3) == (status, b"")
            assert len(records) == 1
            assert sink_records == []


def test_http_error_body_is_not_projected():
    with endpoint(lambda h, _: reply(h, b"synthetic-server-secret", 401)) as (url, records):
        assert catalog_transport(url, {}, 3) == (401, b"")
        assert len(records) == 1


@pytest.mark.parametrize("extra", [0, 1])
def test_cap_plus_one_distinguishes_exact_body_limit(extra):
    body = b"a" * (MAX_BODY_BYTES + extra)
    with endpoint(lambda h, _: reply(h, body)) as (url, records):
        if extra:
            with pytest.raises(CatalogTransportError) as caught:
                catalog_transport(url, {}, 3)
            assert caught.value.status == "response_too_large"
            assert str(caught.value) == "response_too_large"
        else:
            assert catalog_transport(url, {}, 3) == (200, body)
        assert len(records) == 1


def test_total_deadline_includes_slow_body_and_reaps_owned_child(monkeypatch):
    children, _ = capture_workers(monkeypatch)

    def slow_body(handler, stop):
        handler.send_response(200)
        handler.send_header("Content-Length", "30")
        handler.end_headers()
        if not stop.wait(3):
            handler.wfile.write(b"a" * 30)

    with endpoint(slow_body) as (url, records):
        started = time.monotonic()
        with pytest.raises(CatalogTransportError) as caught:
            catalog_transport(url, {"Authorization": "Bearer synthetic-timeout-secret"}, 0.8)
        elapsed = time.monotonic() - started
        assert caught.value.status == "timeout"
        assert elapsed < 1.2
        assert len(records) == 1
        assert len(children) == 1 and children[0].poll() is not None
        assert children[0].stdin.closed and children[0].stdout.closed
        assert "synthetic-timeout-secret" not in repr(caught.value)


def test_slow_dns_cannot_send_a_late_credential_request(monkeypatch):
    children, _ = capture_workers(monkeypatch)
    worker_path = Path(transport_module.__file__).with_name("catalog_worker.py")
    # Same production worker and urllib request; only DNS delay is controlled
    # inside the real isolated child. No simulated provider response is used.
    script = (
        "import socket,time,runpy\n"
        "original=socket.getaddrinfo\n"
        "def delayed(*args,**kwargs):\n"
        " time.sleep(1.3)\n"
        " return original(*args,**kwargs)\n"
        "socket.getaddrinfo=delayed\n"
        f"runpy.run_path({str(worker_path)!r},run_name='__main__')\n"
    )
    monkeypatch.setattr(transport_module, "_worker_command", lambda: [sys.executable, "-I", "-B", "-c", script])
    with endpoint(lambda h, _: reply(h)) as (url, records):
        started = time.monotonic()
        with pytest.raises(CatalogTransportError) as caught:
            catalog_transport(url, {"Authorization": "Bearer synthetic-delayed-secret"}, 0.8)
        assert caught.value.status == "timeout"
        assert time.monotonic() - started < 1.2
        assert len(children) == 1 and children[0].poll() is not None
        time.sleep(1.4)
        assert records == []


def test_worker_cap_rejects_third_request_without_spawn_and_reuses_released_slots(monkeypatch):
    children, _ = capture_workers(monkeypatch)
    release = threading.Event()
    two_requests = threading.Event()
    requested = []
    results = []

    def blocked_body(handler, stop):
        requested.append(True)
        if len(requested) == 2:
            two_requests.set()
        handler.send_response(200)
        body = b'{"data":[]}'
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        while not release.wait(0.05):
            if stop.is_set():
                return
        handler.wfile.write(body)

    with endpoint(blocked_body) as (url, records):
        def call():
            try:
                results.append(catalog_transport(url, {}, 3))
            except CatalogTransportError as error:
                results.append(error.status)

        callers = [threading.Thread(target=call) for _ in range(2)]
        for caller in callers:
            caller.start()
        try:
            assert two_requests.wait(2), "Both real children must reach the owned loopback server"
            assert len(children) == 2 and all(child.poll() is None for child in children)
            started = time.monotonic()
            with pytest.raises(CatalogTransportError) as caught:
                catalog_transport(url, {}, 3)
            assert caught.value.status == "busy"
            assert time.monotonic() - started < 0.2
            assert len(children) == 2 and len(records) == 2
        finally:
            release.set()
            for caller in callers:
                caller.join(timeout=4)
        assert all(not caller.is_alive() for caller in callers)
        assert results == [(200, b'{"data":[]}'), (200, b'{"data":[]}')]
        assert all(child.poll() == 0 and child.stdin.closed and child.stdout.closed for child in children)
        assert catalog_transport(url, {}, 3) == (200, b'{"data":[]}')
        assert len(children) == 3 and len(records) == 3


@pytest.mark.parametrize("url", [
    "http://example.invalid/models", "ftp://127.0.0.1/models", "https://user:secret@host.invalid/models",
    "https://@host.invalid/models", "https://host.invalid/models?key=synthetic", "https://host.invalid/models?",
    "https://host.invalid/models#fragment", "https://host.invalid/models#", "https://host.invalid:0/models",
    "https://host.invalid:99999/models", "http://127.0.0.1\\@host.invalid/models",
    "https://host.invalid/models\n", "https://host.invalid/completions", "//host.invalid/models",
])
def test_unsafe_request_is_rejected_before_any_child_or_network(monkeypatch, url):
    monkeypatch.setattr(transport_module, "_popen", lambda *_a, **_kw: pytest.fail("must not start worker"))
    with pytest.raises(CatalogTransportError) as caught:
        catalog_transport(url, {}, 1)
    assert caught.value.status == "invalid_request"
    assert "synthetic" not in str(caught.value) and "host.invalid" not in str(caught.value)


@pytest.mark.parametrize("timeout", [True, False, 0, -1, 10.1, float("inf"), float("nan"), "1", None])
def test_invalid_timeout_never_dispatches(monkeypatch, timeout):
    monkeypatch.setattr(transport_module, "_popen", lambda *_a, **_kw: pytest.fail("must not start worker"))
    with pytest.raises(CatalogTransportError) as caught:
        catalog_transport("http://127.0.0.1:1/models", {}, timeout)
    assert caught.value.status == "invalid_request"


@pytest.mark.parametrize("headers", [
    {"Host": "untrusted.invalid"}, {"Authorization": "Bearer synthetic\r\nX-Injected: yes"},
    {"authorization": "one", "Authorization": "two"}, {"Authorization": "a" * 16_385},
    {"Accept": ""}, {"Accept": 1}, {"Cookie": "synthetic"},
])
def test_unsafe_headers_never_dispatch(monkeypatch, headers):
    monkeypatch.setattr(transport_module, "_popen", lambda *_a, **_kw: pytest.fail("must not start worker"))
    with pytest.raises(CatalogTransportError) as caught:
        catalog_transport("http://127.0.0.1:1/models", headers, 1)
    assert caught.value.status == "invalid_request"


def test_connection_failure_is_finite_and_does_not_echo_url_or_secret():
    # A real accepted connection closes before sending an HTTP response. This
    # avoids platform-specific connection-refusal retry timing in the OS.
    def disconnect(handler, _):
        handler.connection.shutdown(socket.SHUT_RDWR)
        handler.connection.close()

    with endpoint(disconnect) as (url, records):
        with pytest.raises(CatalogTransportError) as caught:
            catalog_transport(url, {"Authorization": "Bearer synthetic-connect-secret"}, 2)
        assert len(records) == 1
    assert caught.value.status == "connection_error"
    assert str(caught.value) == "connection_error"
    assert url not in repr(caught.value) and "synthetic-connect-secret" not in repr(caught.value)
