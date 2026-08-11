"""Task 3C R2 v7 - Production CombinedTrustedHost relay E2E and SSE fail-closed tests.

Proves the real production startup lifecycle:
  CombinedTrustedHost.start()
  -> Model Control binds ephemeral port
  -> Relay binds ephemeral port
  -> Task handler created with live relay_url + actual model_control_url BindingResolver
  -> Task created via host.task_api_url
  -> Task executed via host.task_api_url
  -> OpenCode subprocess launched (real installed CLI)
  -> OpenCode POST /chat/completions -> relay -> fake loopback provider

SSE fail-closed proves:
  downstream headers are NOT committed before upstream status is known.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import tempfile
import threading
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.model_access.credential_relay import (
    CredentialRelayManager,
    CredentialRelayServer,
)
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _secret_scan(text: str) -> list[str]:
    findings: list[str] = []
    for name, pat in [
        ("bearer_token", re.compile(r"(?i)bearer\s+[a-zA-Z0-9+/=]{16,}")),
        ("api_key_value", re.compile(
            r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9+/=]{16,}")),
        ("gh_token", re.compile(r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}")),
    ]:
        if pat.search(text):
            findings.append(name)
    return findings


def _http_json_get(url: str, path: str, timeout: float = 5.0) -> tuple[int, bytes]:
    parsed = url.replace("http://", "").split(":")
    h = parsed[0]
    p = int(parsed[1])
    conn = HTTPConnection(h, p, timeout=timeout)
    conn.request("GET", path)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data


def _http_json_post(url: str, path: str, body: bytes, timeout: float = 120.0) -> tuple[int, bytes]:
    parsed = url.replace("http://", "").split(":")
    h = parsed[0]
    p = int(parsed[1])
    conn = HTTPConnection(h, p, timeout=timeout)
    conn.request("POST", path, body=body,
                 headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data


def _make_e2e_snapshot(base_url: str, *, master_key: str) -> ExecutionSnapshot:
    return ExecutionSnapshot(
        binding_id="sse-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="gpt-4o",
        connection_id="sse-conn",
        connection_enabled=True,
        provider="openai-compatible",
        base_url=base_url,
        auth_method="api_key",
        resolved_api_key=master_key,
        external_session_status="not_applicable",
    )


# ---------------------------------------------------------------------------
# Fake loopback upstream provider
# ---------------------------------------------------------------------------

class _FakeProvider:
    def __init__(self, port: int, *, status: int = 200,
                 body: bytes = b'{"choices":[{"message":{"content":"ok","role":"assistant"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}') -> None:
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.received: list[dict[str, Any]] = []
        self._server: ThreadingHTTPServer | None = None
        self._status = status
        self._body = body

    def start(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else b""
                self.server.requests.append({  # type: ignore[attr-defined]
                    "path": self.path,
                    "method": "POST",
                    "authorization": self.headers.get("Authorization", ""),
                    "body": body.decode("utf-8", errors="replace"),
                })
                self.send_response(self.server.status)  # type: ignore[attr-defined]
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(self.server.body)))  # type: ignore[attr-defined]
                self.end_headers()
                self.wfile.write(self.server.body)  # type: ignore[attr-defined]

            def log_message(self, fmt: str, *args: object) -> None:
                return

        Handler.server = None  # type: ignore[assignment]
        server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        Handler.server = server  # type: ignore[assignment]
        server.requests = []  # type: ignore[attr-defined]
        server.status = self._status  # type: ignore[attr-defined]
        server.body = self._body  # type: ignore[attr-defined]
        self._server = server
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    def received_requests(self) -> list[dict[str, Any]]:
        if self._server:
            return list(self._server.requests)  # type: ignore[attr-defined]
        return []


# ---------------------------------------------------------------------------
# Production E2E
# ---------------------------------------------------------------------------

class TestCombinedTrustedHostInstalledOpenCodeE2E:

    def test_real_task_api_opencode_relay_fake_provider_end_to_end(self) -> None:
        MASTER = "prod-e2e-master-" + os.urandom(16).hex()
        BINDING_ID = "e2e-binding-v7"
        CONN_ID = "e2e-conn-v7"

        fake_port = _free_port()
        fake = _FakeProvider(fake_port)
        fake.start()
        fake_url = fake.url

        try:
            store = ModelProfileStore()
            store.upsert_connection({
                "connection_id": CONN_ID,
                "name": "E2E fake connection",
                "provider": "openai-compatible",
                "base_url": fake_url,
                "auth_method": "api_key",
                "api_key": MASTER,
            })
            store.upsert_binding({
                "binding_id": BINDING_ID,
                "name": "E2E fake binding",
                "executor_id": "opencode",
                "connection_id": CONN_ID,
                "model_id": "gpt-4o",
            })

            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir) / "source-repo"
                repo_path.mkdir()
                subprocess.run(["git", "init", "-q"], cwd=repo_path, timeout=10, check=True)
                subprocess.run(["git", "config", "user.email", "e2e@test.local"],
                               cwd=repo_path, timeout=5, check=True)
                subprocess.run(["git", "config", "user.name", "E2E Test"],
                               cwd=repo_path, timeout=5, check=True)
                (repo_path / "fixture.txt").write_text("fixture\n", encoding="utf-8")
                subprocess.run(["git", "add", "."], cwd=repo_path, timeout=5, check=True)
                subprocess.run(["git", "commit", "-q", "-m", "init"],
                               cwd=repo_path, timeout=10, check=True)

                old_repo = os.environ.get("REVERSE_AGENT_REPO_DIR")
                os.environ["REVERSE_AGENT_REPO_DIR"] = str(repo_path)

                try:
                    host = CombinedTrustedHost(
                        store=store,
                        model_control_port=0,
                        task_api_port=0,
                    )
                    host.start()

                    actual_mc_url = host.model_control_url
                    actual_task_url = host.task_api_url
                    actual_relay_url = host.relay_url

                    assert actual_mc_url and actual_mc_url != "http://127.0.0.1:"
                    assert actual_task_url and actual_task_url != "http://127.0.0.1:"
                    assert actual_relay_url and actual_relay_url != "http://127.0.0.1:"

                    assert actual_mc_url != "http://127.0.0.1:8765", \
                        "BindingResolver must use actual post-bind model_control_url"

                    create_body = json.dumps({
                        "title": "Production relay E2E",
                        "executor_kind": "opencode",
                        "binding_ref": BINDING_ID,
                    }).encode("utf-8")
                    create_status, create_data = _http_json_post(
                        actual_task_url, "/api/tasks", create_body, timeout=30
                    )
                    assert create_status == 201, \
                        f"task create failed {create_status}: {create_data[:300]}"
                    task = json.loads(create_data)
                    task_id = task["id"]

                    lease_count_before = host.relay_manager.lease_count()
                    assert lease_count_before == 0, \
                        f"no active lease before execution expected, got {lease_count_before}"

                    exec_body = json.dumps({
                        "validation_command_id": "git_diff_check",
                    }).encode("utf-8")
                    exec_status, exec_data = _http_json_post(
                        actual_task_url, f"/api/tasks/{task_id}/execute",
                        exec_body, timeout=180,
                    )

                    time.sleep(0.5)
                    received = fake.received_requests()
                    assert len(received) >= 1, \
                        f"fake provider received no requests. exec={exec_status} data={exec_data[:500]}"

                    req = received[-1]
                    assert req["path"] == "/chat/completions", \
                        f"unexpected path: {req['path']}"
                    assert req["method"] == "POST", \
                        f"unexpected method: {req['method']}"

                    body_obj = json.loads(req["body"])
                    assert body_obj.get("model") == "gpt-4o", \
                        f"unexpected model in body: {body_obj.get('model')}"

                    expected_auth = f"Bearer {MASTER}"
                    assert req["authorization"] == expected_auth, \
                        f"auth mismatch: {req['authorization'][:12]}..."

                    auth_hash = hashlib.sha256(
                        req["authorization"].encode()
                    ).hexdigest()
                    expected_hash = hashlib.sha256(
                        expected_auth.encode()
                    ).hexdigest()
                    assert auth_hash == expected_hash

                    lease_id = BINDING_ID
                    assert req["authorization"] != f"Bearer {lease_id}"

                    scan_targets: dict[str, str] = {
                        "task_api_response": exec_data.decode("utf-8", errors="replace"),
                    }

                    mc_bindings_status, mc_bindings_data = _http_json_get(
                        actual_mc_url, "/api/bindings"
                    )
                    assert mc_bindings_status == 200
                    scan_targets["model_control_bindings"] = mc_bindings_data.decode("utf-8", errors="replace")

                    mc_conns_status, mc_conns_data = _http_json_get(
                        actual_mc_url, "/api/connections"
                    )
                    assert mc_conns_status == 200
                    scan_targets["model_control_connections"] = mc_conns_data.decode("utf-8", errors="replace")

                    for label, text in scan_targets.items():
                        assert MASTER not in text, \
                            f"master leaked in {label}"
                        findings = _secret_scan(text)
                        assert not findings, \
                            f"secret pattern leaked in {label}: {findings}"

                    leak_count = sum(
                        len(_secret_scan(t)) for t in scan_targets.values()
                    )
                    assert leak_count == 0, \
                        f"master leak count={leak_count}"

                    time.sleep(0.3)
                    lease_count_after = host.relay_manager.lease_count()
                    assert lease_count_after == 0, \
                        f"lease not released after execution, count={lease_count_after}"

                    task_store_task = store.get_binding_public(BINDING_ID)
                    assert MASTER not in json.dumps(task_store_task)

                    print(f"actual_model_control_url={actual_mc_url}")
                    print(f"actual_task_api_url={actual_task_url}")
                    print(f"actual_relay_url={actual_relay_url}")
                    print(f"auth_hash_equality={auth_hash == expected_hash}")
                    print(f"lease_before={lease_count_before} after={lease_count_after}")
                    print(f"leak_count={leak_count}")

                finally:
                    host.stop()
                    if old_repo is not None:
                        os.environ["REVERSE_AGENT_REPO_DIR"] = old_repo
                    elif "REVERSE_AGENT_REPO_DIR" in os.environ:
                        del os.environ["REVERSE_AGENT_REPO_DIR"]
        finally:
            fake.stop()


# ---------------------------------------------------------------------------
# SSE fail-closed
# ---------------------------------------------------------------------------

class TestRelaySSEFailClosed:

    def _make_manager_and_lease(
        self, upstream_url: str, master: str,
    ) -> tuple[CredentialRelayManager, CredentialRelayServer, str]:
        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_e2e_snapshot(upstream_url, master_key=master)
        relay = CredentialRelayServer(
            manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0
        )
        relay.__enter__()
        lease = manager.create_lease(snap, relay_url=relay.url)
        return manager, relay, lease.lease_id

    def test_upstream_http_error_preserves_status(self) -> None:
        upstream_port = _free_port()
        upstream_url = f"http://127.0.0.1:{upstream_port}"
        error_body = b'{"error":{"type":"auth_error","message":"invalid"}}'
        fake = _FakeProvider(upstream_port, status=401, body=error_body)
        fake.start()

        try:
            manager, relay, lease_id = self._make_manager_and_lease(
                upstream_url, "test-master-for-sse"
            )

            body = json.dumps({
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "hi"}],
            }).encode("utf-8")

            conn = HTTPConnection("127.0.0.1", relay._port, timeout=10)
            conn.request(
                "POST", "/chat/completions",
                body=body,
                headers={
                    "Authorization": f"Bearer {lease_id}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
            )
            resp = conn.getresponse()
            data = resp.read()
            conn.close()

            assert resp.status == 401, \
                f"expected 401 downstream, got {resp.status} body={data[:200]}"
            assert resp.status != 200, \
                "downstream must NOT receive 200 for upstream HTTP error"

        finally:
            relay.__exit__(None, None, None)
            fake.stop()

    def test_preheader_transport_failure_returns_502(self) -> None:
        ghost_port = 1
        ghost_url = f"http://127.0.0.1:{ghost_port}"

        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_e2e_snapshot(ghost_url, master_key="test-master-ghost")
        relay = CredentialRelayServer(
            manager, host="127.0.0.1", port=_free_port(), upstream_timeout=3.0
        )
        relay.__enter__()
        try:
            lease = manager.create_lease(snap, relay_url=relay.url)

            body = json.dumps({"model": "gpt-4o"}).encode("utf-8")

            conn = HTTPConnection("127.0.0.1", relay._port, timeout=10)
            conn.request(
                "POST", "/chat/completions",
                body=body,
                headers={
                    "Authorization": f"Bearer {lease.lease_id}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
            )
            resp = conn.getresponse()
            data = resp.read()
            conn.close()

            assert resp.status == 502, \
                f"expected 502 for transport failure, got {resp.status} body={data[:200]}"
            assert resp.status != 200, \
                "downstream must NOT receive 200 for pre-header transport failure"
        finally:
            relay.__exit__(None, None, None)

    def test_successful_ordered_sse_passthrough(self) -> None:
        upstream_port = _free_port()
        upstream_url = f"http://127.0.0.1:{upstream_port}"
        chunks = [
            b'data: {"choices":[{"delta":{"content":"he"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]
        total_body = b"".join(chunks)

        class SseHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length) if length else None
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(total_body)))
                self.end_headers()
                for chunk in chunks:
                    self.wfile.write(chunk)
                    self.wfile.flush()

            def log_message(self, fmt: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", upstream_port), SseHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        try:
            manager, relay, lease_id = self._make_manager_and_lease(
                upstream_url, "sse-master-ok"
            )

            body = json.dumps({"model": "gpt-4o"}).encode("utf-8")

            conn = HTTPConnection("127.0.0.1", relay._port, timeout=10)
            conn.request(
                "POST", "/chat/completions",
                body=body,
                headers={
                    "Authorization": f"Bearer {lease_id}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
            )
            resp = conn.getresponse()
            collected = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                collected += chunk
            conn.close()

            assert resp.status == 200
            text = collected.decode("utf-8")
            assert "he" in text
            assert "llo" in text
            assert "[DONE]" in text
            assert text.index("he") < text.index("llo") < text.index("[DONE]")
        finally:
            relay.__exit__(None, None, None)
            server.shutdown()
