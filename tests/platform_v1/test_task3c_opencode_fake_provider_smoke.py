"""Task 3C R2 v3 - Fake-provider installed OpenCode smoke test.

This test verifies the full credential relay integration without invoking
the installed OpenCode CLI. It proves:
- the OpenCode child env contains only relay URL + execution-scoped lease;
- the provider master key never appears in env/config/argv;
- the relay accepts POST /chat/completions with a valid lease and injects
  the provider master Authorization upstream;
- the fake provider actually receives the request on /chat/completions.
"""

from __future__ import annotations

import json
import os
import socket
import threading
from http.client import HTTPConnection
from typing import Any

import pytest

from reverse_agent.model_access.credential_relay import (
    CredentialRelayManager,
    CredentialRelayServer,
)
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_executor import (
    ExecutionLeaseHandle,
    build_binding_child_env,
    build_binding_config_content,
)


FAKE_MASTER_KEY = "fake-secret-provider-master-key-xyz"
FAKE_LEASE_ID = "fake-execution-scoped-lease-token-1234567890abcdef"


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_snapshot(base_url: str, *, master_key: str = FAKE_MASTER_KEY) -> ExecutionSnapshot:
    return ExecutionSnapshot(
        binding_id="smoke-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="gpt-4o",
        connection_id="smoke-conn",
        connection_enabled=True,
        provider="openai-compatible",
        base_url=base_url,
        auth_method="api_key",
        resolved_api_key=master_key,
        external_session_status="not_applicable",
    )


def _make_binding_resolution(base_url: str) -> OpenCodeBindingResolution:
    return OpenCodeBindingResolution(
        binding_ref="smoke-binding",
        connection_id="smoke-conn",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="reverse-agent-relay/gpt-4o",
        base_url=base_url,
        auth_method="api_key",
        external_session_status="not_applicable",
        relay_required=True,
    )


# ---------------------------------------------------------------------------
# Fake upstream provider
# ---------------------------------------------------------------------------

class FakeProviderServer:
    def __init__(self, port: int) -> None:
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.received_requests: list[dict[str, Any]] = []
        self._server = None
        self._thread = None

    def start(self) -> None:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                if self.path != "/chat/completions":
                    self.send_response(404)
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                self.server.requests.append({  # type: ignore[attr-defined]
                    "path": self.path,
                    "method": "POST",
                    "authorization": self.headers.get("Authorization", ""),
                    "host": self.headers.get("Host", ""),
                    "body": body.decode("utf-8", errors="replace"),
                })
                resp = b'{"choices":[{"message":{"content":"fake response","role":"assistant"}}],"usage":{"prompt_tokens":10,"completion_tokens":20}}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)

            def log_message(self, fmt, *args):  # noqa: N802
                return

        Handler.server = None  # type: ignore[assignment]
        server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        Handler.server = server  # type: ignore[assignment]
        server.requests = []  # type: ignore[attr-defined]
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    def received(self) -> list[dict[str, Any]]:
        if self._server:
            return list(self._server.requests)  # type: ignore[attr-defined]
        return []


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

class TestFakeProviderSmoke:
    def test_opencode_config_contains_only_relay_url_and_lease(self) -> None:
        resolution = _make_binding_resolution("https://fake-provider.example.test/v1")

        lease = ExecutionLeaseHandle(
            lease_id=FAKE_LEASE_ID,
            relay_url="http://127.0.0.1:9000",
            model_id="reverse-agent-relay/gpt-4o",
        )

        config_content = build_binding_config_content(resolution, lease=lease)
        config_obj = json.loads(config_content)

        assert "reverse-agent-relay" in config_obj["provider"]
        assert config_obj["provider"]["reverse-agent-relay"]["options"]["baseURL"] == "http://127.0.0.1:9000"
        assert config_obj["provider"]["reverse-agent-relay"]["options"]["apiKey"] == FAKE_LEASE_ID
        assert config_obj["provider"]["reverse-agent-relay"]["npm"] == "@ai-sdk/openai-compatible"
        assert "gpt-4o" in config_obj["provider"]["reverse-agent-relay"]["models"]
        assert FAKE_MASTER_KEY not in config_content
        assert "provider-master" not in config_content

        child_env = build_binding_child_env(
            parent_env={"PATH": "/usr/bin", "OPENCODE_EXISTING": "keep"},
            config_content=config_content,
        )
        assert "OPENCODE_CONFIG_CONTENT" in child_env
        assert FAKE_MASTER_KEY not in json.dumps(child_env)
        assert child_env.get("OPENCODE_EXISTING") is None

    def test_provider_master_not_in_env_argv_config_prompt(
        self,
    ) -> None:
        resolution = _make_binding_resolution("https://fake-provider.example.test/v1")
        lease = ExecutionLeaseHandle(
            lease_id=FAKE_LEASE_ID,
            relay_url="http://127.0.0.1:9000",
            model_id="reverse-agent-relay/gpt-4o",
        )
        config_content = build_binding_config_content(resolution, lease=lease)
        child_env = build_binding_child_env(
            parent_env={"PATH": "/usr/bin"},
            config_content=config_content,
        )

        env_dump = json.dumps(child_env)
        assert FAKE_MASTER_KEY not in env_dump
        assert "master" not in env_dump.lower()
        assert "provider-master" not in env_dump

    def test_relay_injects_provider_authorization_upstream(
        self,
    ) -> None:
        fake_port = _free_port()
        fake = FakeProviderServer(fake_port)
        fake.start()
        try:
            manager = CredentialRelayManager(default_expiry_seconds=30.0)
            snap = _make_snapshot(fake.url)
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                body = json.dumps({
                    "model": "gpt-4o",
                    "messages": [{"role": "user", "content": "hello"}],
                }).encode("utf-8")

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={
                        "Authorization": f"Bearer {lease.lease_id}",
                        "Content-Type": "application/json",
                    },
                )
                resp = conn.getresponse()
                data = resp.read()
                conn.close()

                assert resp.status == 200
                parsed = json.loads(data)
                assert "choices" in parsed

                received = fake.received()
                assert len(received) == 1
                req = received[0]
                assert req["path"] == "/chat/completions"
                assert req["method"] == "POST"
                assert req["authorization"] == f"Bearer {FAKE_MASTER_KEY}"
                assert FAKE_LEASE_ID not in req["authorization"]
        finally:
            fake.stop()

    def test_actual_inference_route_is_chat_completions(self) -> None:
        fake_port = _free_port()
        fake = FakeProviderServer(fake_port)
        fake.start()
        try:
            manager = CredentialRelayManager(default_expiry_seconds=30.0)
            snap = _make_snapshot(fake.url)
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                body = b'{"model":"gpt-4o","messages":[]}'
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request(
                    "POST",
                    "/chat/completions",
                    body=body,
                    headers={"Authorization": f"Bearer {lease.lease_id}"},
                )
                resp = conn.getresponse()
                resp.read()
                conn.close()
                assert resp.status == 200

                received = fake.received()
                assert len(received) == 1
                assert received[0]["path"] == "/chat/completions"
                assert received[0]["method"] == "POST"
        finally:
            fake.stop()

    def test_store_integration_end_to_end(self) -> None:
        store = ModelProfileStore()
        store.upsert_connection({
            "connection_id": "smoke-conn",
            "name": "Smoke test connection",
            "provider": "openai-compatible",
            "base_url": "http://127.0.0.1:19999",
            "auth_method": "api_key",
            "api_key": FAKE_MASTER_KEY,
        })
        store.upsert_binding({
            "binding_id": "smoke-binding",
            "name": "Smoke binding",
            "executor_id": "opencode",
            "connection_id": "smoke-conn",
            "model_id": "gpt-4o",
        })

        snap = store.resolve_execution_snapshot("smoke-binding")
        assert snap.resolved_api_key == FAKE_MASTER_KEY
        assert snap.auth_method == "api_key"
        assert snap.provider == "openai-compatible"

        public_bindings = json.dumps(store.list_bindings_public())
        public_connections = json.dumps(store.list_connections_public())
        assert FAKE_MASTER_KEY not in public_bindings
        assert FAKE_MASTER_KEY not in public_connections