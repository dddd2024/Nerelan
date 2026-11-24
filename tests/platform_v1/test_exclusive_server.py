"""A Nerelan host owns its ports: a second host cannot bind them (2026-11-09)."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler
import inspect
import os

import pytest

from reverse_agent.model_access import credential_relay, service
from reverse_agent.model_access.exclusive_server import ExclusiveThreadingHTTPServer
from reverse_agent.platform_v1 import trusted_host


def test_a_second_server_cannot_bind_a_listening_port():
    first = ExclusiveThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    try:
        with pytest.raises(OSError):
            ExclusiveThreadingHTTPServer(("127.0.0.1", first.server_address[1]), BaseHTTPRequestHandler)
    finally:
        first.server_close()


@pytest.mark.skipif(os.name != "nt", reason="the duplicate bind only happens with Windows SO_REUSEADDR")
def test_the_plain_server_would_have_allowed_it_on_windows():
    from http.server import ThreadingHTTPServer
    first = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    try:
        second = ThreadingHTTPServer(("127.0.0.1", first.server_address[1]), BaseHTTPRequestHandler)
        second.server_close()
    finally:
        first.server_close()


def test_a_freed_port_can_be_bound_again():
    first = ExclusiveThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
    port = first.server_address[1]
    first.server_close()
    again = ExclusiveThreadingHTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler)
    again.server_close()


def test_every_host_listener_uses_the_exclusive_server():
    for module in (trusted_host, service, credential_relay):
        source = inspect.getsource(module)
        assert "= ThreadingHTTPServer(" not in source, module.__name__
        assert "ExclusiveThreadingHTTPServer(" in source, module.__name__
