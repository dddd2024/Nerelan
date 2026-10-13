"""A request carrying a provider key is never replayed to a redirect target."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from reverse_agent.model_access import credential_relay, service
from reverse_agent.model_access.http_safe import urlopen


def _serve(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def redirect_to_collector():
    seen = []

    class Collector(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"data": []}')

        do_POST = do_GET

        def log_message(self, *args):
            pass

    collector = _serve(Collector)

    class Redirector(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{collector.server_port}/stolen")
            self.end_headers()

        do_POST = do_GET

        def log_message(self, *args):
            pass

    redirector = _serve(Redirector)
    yield f"http://127.0.0.1:{redirector.server_port}/v1/models", seen
    redirector.shutdown()
    collector.shutdown()


@pytest.mark.parametrize("method,body", [("GET", None), ("POST", b"{}")])
def test_redirects_are_refused_and_the_key_is_not_forwarded(redirect_to_collector, method, body):
    url, seen = redirect_to_collector
    request = Request(url, data=body, method=method, headers={"Authorization": "Bearer provider-secret"})
    with pytest.raises(HTTPError) as caught:
        urlopen(request, timeout=5)
    assert caught.value.code == 302
    assert seen == []  # the redirect target never received the request


def test_model_listing_and_relay_use_the_safe_opener():
    assert service.urlopen is urlopen
    assert credential_relay.urlopen is urlopen
