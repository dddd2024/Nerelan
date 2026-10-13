"""Claude Code relay mode: an Anthropic-compatible API-key model inside Claude Code (provider-free)."""
from __future__ import annotations

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from types import SimpleNamespace
from typing import Any

import pytest

from reverse_agent.model_access.contracts import ExecutionSnapshot, is_anthropic_relay_connection
from reverse_agent.model_access.credential_relay import CredentialRelayManager, CredentialRelayServer
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.claude_executor import ClaudeCodeExecutor
from reverse_agent.platform_v1.task_runtime import ExecutorRuntimeError

PROVIDER_KEY = "provider-master-key-glm"


def _anthropic_connection(**overrides: Any) -> dict[str, Any]:
    payload = {"connection_id": "zhipu-anthropic", "name": "Zhipu (Anthropic API)", "provider": "anthropic-compatible",
               "executor_provider_id": "anthropic-compatible", "upstream_provider_id": "zhipu",
               "protocol_family": "anthropic", "base_url": "https://open.bigmodel.cn/api/anthropic",
               "auth_method": "api_key", "enabled": True, "api_key": PROVIDER_KEY}
    payload.update(overrides)
    return payload


def _snapshot(base_url: str, **overrides: Any) -> ExecutionSnapshot:
    values = dict(binding_id="glm-in-claude", binding_enabled=True, executor_id="claude_code", raw_model_id="glm-5.2",
                  connection_id="zhipu-anthropic", connection_enabled=True, provider="anthropic-compatible",
                  base_url=base_url, auth_method="api_key", resolved_api_key=PROVIDER_KEY,
                  external_session_status="not_applicable", upstream_provider_id="zhipu",
                  protocol_family="anthropic", executor_provider_id="anthropic-compatible")
    values.update(overrides)
    return ExecutionSnapshot(**values)


# ---- binding rules ---------------------------------------------------------------

def test_claude_code_binds_an_anthropic_api_key_connection_but_not_an_openai_one():
    store = ModelProfileStore()
    store.upsert_connection(_anthropic_connection())
    store.upsert_binding({"binding_id": "glm-in-claude", "name": "GLM in Claude Code", "executor_id": "claude_code",
                          "connection_id": "zhipu-anthropic", "model_id": "glm-5.2", "enabled": True})
    store.upsert_connection({"connection_id": "openai-api", "name": "OpenAI-compatible", "provider": "openai-compatible",
                             "base_url": "https://models.example.test/v1", "auth_method": "api_key", "enabled": True,
                             "api_key": "k"})
    with pytest.raises(ValueError):
        store.upsert_binding({"binding_id": "x", "name": "x", "executor_id": "claude_code",
                              "connection_id": "openai-api", "model_id": "glm-5.2", "enabled": True})
    with pytest.raises(ValueError):  # Codex still runs only on the Owner's ChatGPT login
        store.upsert_binding({"binding_id": "y", "name": "y", "executor_id": "codex",
                              "connection_id": "zhipu-anthropic", "model_id": "glm-5.2", "enabled": True})


def test_relay_predicate_requires_api_key_and_anthropic_wire():
    assert is_anthropic_relay_connection({"auth_method": "api_key", "protocol_family": "anthropic",
                                          "executor_provider_id": "anthropic-compatible"})
    assert not is_anthropic_relay_connection({"auth_method": "api_key", "protocol_family": "openai",
                                              "executor_provider_id": "litellm-proxy"})
    assert not is_anthropic_relay_connection({"auth_method": "external_cli_session", "protocol_family": "anthropic",
                                              "executor_provider_id": "claude-code"})


# ---- relay -----------------------------------------------------------------------

@pytest.fixture
def upstream():
    seen: list[dict[str, Any]] = []

    class Upstream(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append({"path": self.path, "x-api-key": self.headers.get("x-api-key"),
                         "authorization": self.headers.get("Authorization"),
                         "version": self.headers.get("anthropic-version"), "body": body})
            if body.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(b"event: message_stop\ndata: {}\n\n")
                return
            data = b'{"type":"message","content":[{"type":"text","text":"ok"}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", seen
    server.shutdown()


def _post(relay, path, lease_id, body, headers=None):
    conn = HTTPConnection("127.0.0.1", relay._port, timeout=5)
    conn.request("POST", path, body=json.dumps(body).encode(),
                 headers={"Authorization": f"Bearer {lease_id}", "Content-Type": "application/json",
                          "anthropic-version": "2023-06-01", **(headers or {})})
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, data


@pytest.mark.parametrize("stream", [False, True])
def test_messages_are_forwarded_with_the_provider_key_only_upstream(upstream, stream):
    url, seen = upstream
    manager = CredentialRelayManager(default_expiry_seconds=30.0)
    with CredentialRelayServer(manager, host="127.0.0.1", port=0, upstream_timeout=5.0) as relay:
        lease = manager.create_lease(_snapshot(url), relay_url=relay.url)
        status, data = _post(relay, "/v1/messages", lease.lease_id,
                             {"model": "glm-5.2", "stream": stream, "messages": [{"role": "user", "content": "hi"}]})
    assert status == 200 and (b"message_stop" in data if stream else b'"ok"' in data)
    [request] = seen
    assert request["path"] == "/v1/messages" and request["x-api-key"] == PROVIDER_KEY
    assert request["authorization"] is None  # the client capability is never forwarded
    assert request["version"] == "2023-06-01"
    assert PROVIDER_KEY not in data.decode()


def test_an_anthropic_lease_cannot_call_chat_and_a_chat_lease_cannot_call_messages(upstream):
    url, seen = upstream
    manager = CredentialRelayManager(default_expiry_seconds=30.0)
    with CredentialRelayServer(manager, host="127.0.0.1", port=0, upstream_timeout=5.0) as relay:
        anthropic = manager.create_lease(_snapshot(url), relay_url=relay.url)
        chat = manager.create_lease(_snapshot(url, executor_id="opencode", protocol_family="openai",
                                              provider="openai-compatible", executor_provider_id="openai-compatible"),
                                    relay_url=relay.url)
        assert _post(relay, "/chat/completions", anthropic.lease_id, {"model": "glm-5.2", "messages": []})[0] == 401
        assert _post(relay, "/v1/messages", chat.lease_id, {"model": "glm-5.2", "messages": []})[0] == 401
        assert _post(relay, "/v1/messages", anthropic.lease_id, {"model": "other-model", "messages": []})[0] == 401
    assert seen == []


# ---- executor --------------------------------------------------------------------

def _resolution(relay_required=True, auth_method="api_key"):
    return SimpleNamespace(binding_ref="glm-in-claude", connection_id="zhipu-anthropic", executor_id="claude_code",
                           provider_id="anthropic-compatible", model_id="glm-5.2",
                           base_url="https://open.bigmodel.cn/api/anthropic", auth_method=auth_method,
                           external_session_status="not_applicable", relay_required=relay_required)


def test_relay_mode_requires_a_lease_provider():
    with pytest.raises(ExecutorRuntimeError, match="claude_code_relay_requires_lease_provider"):
        ClaudeCodeExecutor(binding_resolution=_resolution(), repo_dir=".", base_ref="a" * 40)


def test_relay_mode_child_sees_only_the_relay_and_a_capability(monkeypatch):
    released = []
    lease = SimpleNamespace(lease_id="sk-capability", relay_url="http://127.0.0.1:9999", model_id="glm-5.2",
                            bind_execution_deadline=lambda seconds: None, release=lambda: released.append(True))
    executor = ClaudeCodeExecutor(binding_resolution=_resolution(), repo_dir=".", base_ref="a" * 40,
                                  lease_provider=lambda resolution: lease,
                                  parent_env={"PATH": "x", "ANTHROPIC_API_KEY": "owner-api-key",
                                              "ANTHROPIC_BASE_URL": "https://evil.example"})
    captured = {}

    def fake_execute(self, prepared, store, *, role_context, event_callback=None):
        captured.update(self._child_env())
        return "done"

    from reverse_agent.platform_v1.codex_executor import CodexExecutor
    monkeypatch.setattr(CodexExecutor, "execute_role_prepared", fake_execute)
    assert executor.execute_role_prepared(None, None, role_context=None) == "done"
    assert captured["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:9999"
    assert captured["ANTHROPIC_AUTH_TOKEN"] == "sk-capability"
    assert "ANTHROPIC_API_KEY" not in captured and PROVIDER_KEY not in json.dumps(captured)
    assert released == [True] and executor._child_env().get("ANTHROPIC_BASE_URL") is None


def test_login_mode_still_strips_every_anthropic_variable():
    executor = ClaudeCodeExecutor(model_id="sonnet", repo_dir=".", base_ref="a" * 40,
                                  parent_env={"PATH": "x", "ANTHROPIC_API_KEY": "k", "ANTHROPIC_BASE_URL": "u"})
    assert not executor.relay_mode
    assert not any(key.startswith("ANTHROPIC") for key in executor._child_env())
