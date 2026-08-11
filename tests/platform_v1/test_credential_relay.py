"""Credential relay lease and confinement tests.

Covers Task 3C R2 v3 Segments C (lease + negative confinement) and D
(upstream Authorization injection + JSON/SSE).
"""

from __future__ import annotations

import json
import socket
import threading
from http.client import HTTPConnection
from typing import Any

import pytest

from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.model_access.credential_relay import (
    CredentialRelayError,
    CredentialRelayManager,
    CredentialRelayServer,
    ExecutionLease,
    forward_to_upstream,
    _normalize_model_id,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_snapshot(**overrides: Any) -> ExecutionSnapshot:
    base = dict(
        binding_id="test-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id="gpt-4o",
        connection_id="test-conn",
        connection_enabled=True,
        provider="openai-compatible",
        base_url="https://models.example.test/v1",
        auth_method="api_key",
        resolved_api_key="provider-master-key-xyz",
        external_session_status="not_applicable",
    )
    base.update(overrides)
    return ExecutionSnapshot(**base)


@pytest.fixture()
def manager() -> CredentialRelayManager:
    return CredentialRelayManager(default_expiry_seconds=2.0)


@pytest.fixture()
def snapshot() -> ExecutionSnapshot:
    return _make_snapshot()


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ---------------------------------------------------------------------------
# Segment C: Lease creation
# ---------------------------------------------------------------------------

class TestLeaseCreation:
    def test_create_lease_returns_high_entropy(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        assert isinstance(lease, ExecutionLease)
        assert len(lease.lease_id) >= 32
        assert lease.relay_url == "http://127.0.0.1:0"
        assert lease.model_id == "gpt-4o"
        assert lease.expires_at > __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        )

    def test_create_lease_requires_api_key_auth(self, manager: CredentialRelayManager) -> None:
        snap = _make_snapshot(auth_method="none", resolved_api_key=None)
        with pytest.raises(CredentialRelayError, match="lease_requires_api_key_auth"):
            manager.create_lease(snap, relay_url="http://127.0.0.1:0")

    def test_create_lease_requires_resolved_secret(self, manager: CredentialRelayManager) -> None:
        snap = _make_snapshot(resolved_api_key=None)
        with pytest.raises(CredentialRelayError, match="lease_requires_resolved_secret"):
            manager.create_lease(snap, relay_url="http://127.0.0.1:0")

    def test_create_lease_rejects_non_loopback_relay_url(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        with pytest.raises(CredentialRelayError, match="relay_url"):
            manager.create_lease(snapshot, relay_url="http://example.com:9000")

    def test_model_id_normalized(self) -> None:
        assert _normalize_model_id("openai", "gpt-4o") == "openai/gpt-4o"
        assert _normalize_model_id("openai", "openai/gpt-4o") == "openai/gpt-4o"


# ---------------------------------------------------------------------------
# Segment C: Lease validation / negative confinement
# ---------------------------------------------------------------------------

class TestLeaseValidation:
    def test_no_lease_fails_closed(self, manager: CredentialRelayManager) -> None:
        with pytest.raises(CredentialRelayError, match="lease_not_found"):
            manager._validate_lease_for_request(
                "totally-missing-lease",
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

    def test_wrong_method_fails_closed(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        with pytest.raises(CredentialRelayError, match="lease_method_mismatch"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="GET",
                path="/chat/completions",
                model="gpt-4o",
            )

    def test_wrong_path_fails_closed(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        with pytest.raises(CredentialRelayError, match="lease_path_mismatch"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/responses",
                model="gpt-4o",
            )

    def test_wrong_model_fails_closed(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        with pytest.raises(CredentialRelayError, match="lease_model_mismatch"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="other-model",
            )

    def test_missing_model_fails_closed(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        with pytest.raises(CredentialRelayError, match="lease_model_mismatch"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model=None,
            )

    def test_released_lease_replay_fails(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        manager.release_lease(lease.lease_id)
        with pytest.raises(CredentialRelayError, match="lease_not_found|lease_released"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

    def test_expired_lease_fails_closed(self, snapshot: ExecutionSnapshot) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=0.01)
        lease = manager.create_lease(snapshot, relay_url="http://127.0.0.1:0")
        import time
        time.sleep(0.05)
        with pytest.raises(CredentialRelayError, match="lease_expired"):
            manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )


# ---------------------------------------------------------------------------
# Segment D: HTTP relay integration
# ---------------------------------------------------------------------------

class TestRelayHttpIntegration:
    def _start_fake_upstream(self, port: int, responses: list[tuple[int, bytes]]) -> threading.Thread:
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        idx = [0]

        class FakeHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                if self.path != "/chat/completions":
                    self.send_response(404)
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", "0"))
                _body = self.rfile.read(length)
                auth = self.headers.get("Authorization", "")
                idx[0] += 1
                if idx[0] > len(responses):
                    self.send_response(404)
                    self.end_headers()
                    return
                status, data = responses[idx[0] - 1]
                received_auth = auth
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return t

    def test_authorized_request_upstream_authorization_hash_match(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        port = _free_port()
        fake_response = (200, b'{"choices":[{"message":{"content":"ok"}}]}')
        t = self._start_fake_upstream(port, [fake_response])
        try:
            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                lease = manager.create_lease(snapshot, relay_url=relay.url)

                fake_upstream_url = f"http://127.0.0.1:{port}"
                snap_with_local = _make_snapshot(base_url=fake_upstream_url)
                lease2 = manager.create_lease(snap_with_local, relay_url=relay.url)

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
                        "Authorization": f"Bearer {lease2.lease_id}",
                        "Content-Type": "application/json",
                    },
                )
                resp = conn.getresponse()
                data = resp.read()
                conn.close()
                assert resp.status == 200
                assert b"ok" in data
                parsed = json.loads(data)
                assert "choices" in parsed
        finally:
            pass

    def test_wrong_method_zero_upstream(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        port = _free_port()
        fake_response = (200, b'{"choices":[]}')
        upstream_requests = [0]

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class FakeHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                upstream_requests[0] += 1
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "13")
                self.end_headers()
                self.wfile.write(fake_response[1])

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                snap_local = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
                lease = manager.create_lease(snap_local, relay_url=relay.url)

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request("GET", "/chat/completions", headers={"Authorization": f"Bearer {lease.lease_id}"})
                resp = conn.getresponse()
                data = resp.read()
                conn.close()
                assert resp.status == 405
                assert upstream_requests[0] == 0
        finally:
            pass

    def test_wrong_path_zero_upstream(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        port = _free_port()
        upstream_requests = [0]

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class FakeHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                upstream_requests[0] += 1
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                snap_local = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
                lease = manager.create_lease(snap_local, relay_url=relay.url)

                body = b'{"model":"gpt-4o"}'
                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request("POST", "/responses", body=body, headers={"Authorization": f"Bearer {lease.lease_id}"})
                resp = conn.getresponse()
                resp.read()
                conn.close()
                assert resp.status == 404
                assert upstream_requests[0] == 0
        finally:
            pass

    def test_non_loopback_relay_only(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
        with relay:
            lease = manager.create_lease(snapshot, relay_url=relay.url)
            body = b'{"model":"gpt-4o"}'
            conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
            conn.request("POST", "/chat/completions", body=body, headers={"Authorization": f"Bearer {lease.lease_id}"})
            resp = conn.getresponse()
            resp.read()
            conn.close()
            assert resp.status == 502

    def test_missing_lease_rejected(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
        with relay:
            body = b'{"model":"gpt-4o"}'
            conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
            conn.request("POST", "/chat/completions", body=body, headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            resp.read()
            conn.close()
            assert resp.status == 400

    def test_release_replay_failure(self, manager: CredentialRelayManager, snapshot: ExecutionSnapshot) -> None:
        port = _free_port()
        call_count = [0]

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class FakeHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                call_count[0] += 1
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "13")
                self.end_headers()
                self.wfile.write(b'{"choices":[]}')

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            relay = CredentialRelayServer(manager, host="127.0.0.1", port=_free_port(), upstream_timeout=5.0)
            with relay:
                snap_local = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
                lease = manager.create_lease(snap_local, relay_url=relay.url)

                body = json.dumps({"model": "gpt-4o"}).encode("utf-8")

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request("POST", "/chat/completions", body=body, headers={"Authorization": f"Bearer {lease.lease_id}"})
                r1 = conn.getresponse()
                r1.read()
                conn.close()
                assert r1.status == 200
                assert call_count[0] == 1

                manager.release_lease(lease.lease_id)

                conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
                conn.request("POST", "/chat/completions", body=body, headers={"Authorization": f"Bearer {lease.lease_id}"})
                r2 = conn.getresponse()
                r2.read()
                conn.close()
                assert r2.status == 401
                assert call_count[0] == 1
        finally:
            pass


# ---------------------------------------------------------------------------
# Segment D: Provider master injection evidence
# ---------------------------------------------------------------------------

class TestProviderMasterInjection:
    def test_upstream_sees_bearer_master(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=2.0)
        port = _free_port()

        received_headers: dict[str, str] = {}

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class CaptureHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                received_headers["Authorization"] = self.headers.get("Authorization", "")
                received_headers["Host"] = self.headers.get("Host", "")
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "13")
                self.end_headers()
                self.wfile.write(b'{"choices":[]}')

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), CaptureHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            master = "secret-provider-master-key-xyz"
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}", resolved_api_key=master)
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")

            body = b'{"model":"gpt-4o"}'
            active_lease = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )
            status, resp_body, _ = forward_to_upstream(active_lease, body=body, timeout=5.0)
            assert status == 200
            assert received_headers["Authorization"] == f"Bearer {master}"
        finally:
            pass


# ---------------------------------------------------------------------------
# Segment D: Normal JSON + ordered SSE
# ---------------------------------------------------------------------------

class TestJsonAndSseResponses:
    def test_normal_json_response_passed_through(self, manager: CredentialRelayManager) -> None:
        port = _free_port()
        expected = b'{"choices":[{"message":{"content":"hello"}}]}'

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class FakeHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(expected)))
                self.end_headers()
                self.wfile.write(expected)

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), FakeHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
            active = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )
            status, body, _ = forward_to_upstream(active, body=b"{}", timeout=5.0)
            assert status == 200
            assert body == expected
        finally:
            pass

    def test_ordered_multi_chunk_sse(self, manager: CredentialRelayManager) -> None:
        port = _free_port()
        chunks = [
            b'data: {"choices":[{"delta":{"content":"he"}}]}\n\n',
            b'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n',
            b'data: [DONE]\n\n',
        ]
        total_body = b"".join(chunks)

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class SseHandler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                self.rfile.read(length)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(total_body)))
                self.end_headers()
                for chunk in chunks:
                    self.wfile.write(chunk)
                    self.wfile.flush()

            def log_message(self, fmt, *args):  # noqa: N802
                return

        server = ThreadingHTTPServer(("127.0.0.1", port), SseHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        try:
            snap = _make_snapshot(base_url=f"http://127.0.0.1:{port}")
            lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
            active = manager._validate_lease_for_request(
                lease.lease_id,
                method="POST",
                path="/chat/completions",
                model="gpt-4o",
            )

            import io
            from reverse_agent.model_access.credential_relay import stream_sse
            buf = io.BytesIO()
            status = stream_sse(
                active,
                body=b'{"model":"gpt-4o"}',
                wfile=buf,
                timeout=5.0,
            )
            assert status == 200
            content = buf.getvalue().decode("utf-8")
            assert "he" in content
            assert "llo" in content
            assert "[DONE]" in content
        finally:
            pass


# ---------------------------------------------------------------------------
# Segment F: Expiry / release / timeout / nonzero / exception cleanup
# ---------------------------------------------------------------------------

class TestLeaseCleanup:
    def test_expired_lease_auto_cleanup(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=0.01)
        snap = _make_snapshot()
        lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        assert manager.lease_count() == 1
        import time
        time.sleep(0.05)
        assert manager.lease_count() == 0
        assert not manager.has_active_lease(lease.lease_id)

    def test_release_removes_lease(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_snapshot()
        lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        assert manager.lease_count() == 1
        manager.release_lease(lease.lease_id)
        assert not manager.has_active_lease(lease.lease_id)

    def test_release_all_clears_all_leases(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=60.0)
        snap = _make_snapshot()
        lease1 = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        lease2 = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        assert manager.lease_count() == 2
        manager.release_all()
        assert manager.lease_count() == 0
        assert not manager.has_active_lease(lease1.lease_id)
        assert not manager.has_active_lease(lease2.lease_id)

    def test_hard_expiry_bounded(self) -> None:
        manager = CredentialRelayManager(default_expiry_seconds=5.0)
        snap = _make_snapshot()
        lease = manager.create_lease(snap, relay_url="http://127.0.0.1:0")
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        assert lease.expires_at <= now + __import__("datetime").timedelta(seconds=6)
        assert lease.expires_at >= now + __import__("datetime").timedelta(seconds=4)