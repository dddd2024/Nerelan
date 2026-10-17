"""CLI-0 accepts no owner tokens, mutation requests, or live model calls."""
from __future__ import annotations

import json
from urllib import request

import pytest

from reverse_agent.platform_v1 import headless_cli


def test_public_health_is_explicitly_not_execution_authority():
    code, body = headless_cli.evaluate(["doctor", "--json"], probe=lambda: b'{"ready":true}')
    assert code == 0
    assert body["status"] == "PUBLIC_HEALTH_OBSERVED"
    assert body["authenticated"] is False
    assert body["dispatch_permitted"] is False
    assert body["control_plane"] == "NOT_CONNECTED"


@pytest.mark.parametrize("payload", [
    b'{"ready":false}', b'{"ready":"true"}', b'[]', b'invalid',
    b'{"ready":true}' + b" " * 4096, b'{"ready":true,"private_key":"x"}' * 1000,
])
def test_bad_health_payload_is_not_auth_or_success(payload):
    code, body = headless_cli.evaluate(["doctor"], probe=lambda: payload)
    assert code == 50
    assert body["status"] == "PUBLIC_HEALTH_UNAVAILABLE"
    assert body["dispatch_permitted"] is False


def test_doctor_uses_only_public_loopback_without_proxy_or_capability(monkeypatch):
    calls = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def geturl(self):
            return headless_cli.HEALTH_URL

        def read(self, n):
            assert n == headless_cli.MAX_HEALTH_BYTES + 1
            return b'{"ready":true}'

    class Opener:
        def open(self, req, *, timeout):
            calls.append((req.full_url, req.get_method(), dict(req.header_items()), timeout))
            return Response()

    def build(*handlers):
        assert len(handlers) == 2
        assert isinstance(handlers[0], request.ProxyHandler)
        assert handlers[0].proxies == {}
        assert isinstance(handlers[1], headless_cli._NoRedirect)
        assert handlers[1].redirect_request(None, None, 302, "redirect", {}, "https://external.invalid") is None
        return Opener()

    monkeypatch.setattr(headless_cli, "build_opener", build)
    code, _ = headless_cli.evaluate(["doctor"])
    assert code == 0
    assert calls == [(headless_cli.HEALTH_URL, "GET", {}, 2)]


@pytest.mark.parametrize("args", [
    ["goal", "create", "--file", "goal.json", "--json"],
    ["goal", "approve", "goal-123"],
    ["goal", "launch", "goal-123", "--window", "window-123"],
    ["task", "list", "--json"], ["run", "stop", "run-123"],
    ["window", "activate", "window-123"], ["run", "resume"],
    ["doctor", "--url", "http://evil.example"],
    ["doctor", "--capability", "private-value"],
    ["doctor", "--json", "extra"], [],
])
def test_unsupported_verbs_fail_closed_before_network(args, monkeypatch):
    def unreachable(*_args, **_kwargs):
        raise AssertionError("unsupported action must not attempt network")

    monkeypatch.setattr(headless_cli, "_public_health", unreachable)
    code, body = headless_cli.evaluate(args)
    assert code == 50
    assert body["status"] == "NOT_SUPPORTED"
    assert "private-value" not in json.dumps(body)
    assert body["dispatch_permitted"] is False


def test_private_status_never_reads_public_health(monkeypatch):
    def unreachable():
        raise AssertionError("status may not substitute public health for auth")
    monkeypatch.setattr(headless_cli, "_public_health", unreachable)
    code, body = headless_cli.evaluate(["status", "--json"])
    assert code == 50
    assert body["status"] == "WAITING"
    assert body["reason"] == "authenticated_control_transport_not_implemented"


def test_main_is_structured_with_nonzero_mutation_exit(capsys):
    result = headless_cli.main(["goal", "launch", "goal-1", "--json"])
    output = json.loads(capsys.readouterr().out)
    assert result == 50
    assert output["status"] == "NOT_SUPPORTED"
    assert "goal-1" not in json.dumps(output)
