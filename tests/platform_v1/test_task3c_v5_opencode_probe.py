"""Task 3C R2 v5 - OpenCode relay controlled matrix probe.

Proves:
A. config provider ID == CLI model provider prefix
B. config has npm=@ai-sdk/openai-compatible, options.baseURL, options.apiKey=lease, models
C. config does not contain provider master
D. direct fake-provider control (OpenCode -> fake provider, no relay)
E. relay + fake-provider run (OpenCode -> relay -> fake provider)
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from reverse_agent.model_access.credential_relay import (
    CredentialRelayManager,
    CredentialRelayServer,
)
from reverse_agent.model_access.contracts import ExecutionSnapshot
from reverse_agent.platform_v1.opencode_executor import (
    build_binding_child_env,
    build_binding_config_content,
    ExecutionLeaseHandle,
    ExecutorRuntimeError,
    resolve_opencode_cli,
    validate_model_id,
)
from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROVIDER_ID = "reverse-agent-relay"
PROVIDER_NPM = "@ai-sdk/openai-compatible"
PROVIDER_NAME = "Reverse Agent Relay"
PROVIDER_FACING_MODEL = "gpt-4o"
CLI_SELECTOR = "reverse-agent-relay/gpt-4o"
PROMPT = (
    "AUTHORITY CONSTRAINTS\n"
    "You operate ONLY inside the supplied worktree directory.\n"
    "END AUTHORITY CONSTRAINTS\n"
    "USER TASK\n"
    "Answer with exactly one word: ok\n"
    "END USER TASK\n"
)


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _init_git_worktree(worktree: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=worktree, timeout=10, check=True)
    subprocess.run(["git", "config", "user.email", "probe@test.local"], cwd=worktree, timeout=5, check=True)
    subprocess.run(["git", "config", "user.name", "Probe Test"], cwd=worktree, timeout=5, check=True)
    (worktree / "fixture.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "fixture.txt"], cwd=worktree, timeout=5, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init: probe fixture"], cwd=worktree, timeout=10, check=True)


def _make_snapshot(base_url: str, *, master_key: str) -> ExecutionSnapshot:
    return ExecutionSnapshot(
        binding_id="probe-binding",
        binding_enabled=True,
        executor_id="opencode",
        raw_model_id=PROVIDER_FACING_MODEL,
        connection_id="probe-conn",
        connection_enabled=True,
        provider="openai-compatible",
        base_url=base_url,
        auth_method="api_key",
        resolved_api_key=master_key,
        external_session_status="not_applicable",
    )


def _make_binding_resolution(base_url: str) -> OpenCodeBindingResolution:
    return OpenCodeBindingResolution(
        binding_ref="probe-binding",
        connection_id="probe-conn",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/" + PROVIDER_FACING_MODEL,
        base_url=base_url,
        auth_method="api_key",
        external_session_status="not_applicable",
        relay_required=True,
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _secret_scan(text: str) -> list[str]:
    """Return list of actual secret values found (not benign field names)."""
    findings: list[str] = []
    import re
    # Look for actual secret patterns, not field names
    for pattern_name, pattern_re in [
        ("bearer_token", re.compile(r"(?i)bearer\s+[a-zA-Z0-9+/=]{16,}")),
        ("api_key_value", re.compile(r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9+/=]{16,}")),
        ("gh_token", re.compile(r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{20,}")),
        ("sk_leak", re.compile(r"(?<![\w-])sk-[a-zA-Z0-9]{20,}(?![\w-])")),
    ]:
        if pattern_re.search(text):
            findings.append(pattern_name)
    return findings


def _start_fake_provider(
    port: int,
) -> tuple[ThreadingHTTPServer, list[dict[str, Any]]]:
    received: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            if self.path != "/chat/completions":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            received.append({
                "path": self.path,
                "method": "POST",
                "authorization": self.headers.get("Authorization", ""),
                "body": body.decode("utf-8", errors="replace"),
            })
            resp = b'{"choices":[{"message":{"content":"ok","role":"assistant"}}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        def log_message(self, fmt, *args):  # noqa: N802
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, received


# ---------------------------------------------------------------------------
# A. Config provider ID == CLI model provider prefix
# ---------------------------------------------------------------------------

class TestTransientProviderConfig:

    def test_config_provider_id_matches_cli_selector_prefix(self) -> None:
        resolution = _make_binding_resolution("https://models.example.test/v1")
        lease = ExecutionLeaseHandle(
            lease_id="sk-" + secrets.token_urlsafe(24),
            relay_url="http://127.0.0.1:9000",
            model_id=CLI_SELECTOR,
        )
        config_content = build_binding_config_content(resolution, lease=lease)
        config = json.loads(config_content)

        providers = list(config["provider"].keys())
        assert len(providers) == 1
        assert providers[0] == PROVIDER_ID
        assert CLI_SELECTOR.startswith(PROVIDER_ID + "/")

    def test_config_has_required_openai_compatible_fields(self) -> None:
        resolution = _make_binding_resolution("https://models.example.test/v1")
        lease = ExecutionLeaseHandle(
            lease_id="sk-" + secrets.token_urlsafe(24),
            relay_url="http://127.0.0.1:9000",
            model_id=CLI_SELECTOR,
        )
        config_content = build_binding_config_content(resolution, lease=lease)
        config = json.loads(config_content)

        provider = config["provider"][PROVIDER_ID]
        assert provider["npm"] == PROVIDER_NPM
        assert provider["name"] == PROVIDER_NAME
        assert provider["options"]["baseURL"] == lease.relay_url
        assert provider["options"]["apiKey"] == lease.lease_id
        assert PROVIDER_FACING_MODEL in provider["models"]
        assert provider["models"][PROVIDER_FACING_MODEL] == {}

    def test_config_with_lease_has_api_key_and_relay_base_url(self) -> None:
        from reverse_agent.platform_v1.opencode_executor import ExecutionLeaseHandle

        resolution = _make_binding_resolution("https://models.example.test/v1")
        lease = ExecutionLeaseHandle(
            lease_id="sk-" + secrets.token_urlsafe(24),
            relay_url="http://127.0.0.1:9000",
            model_id=CLI_SELECTOR,
        )
        config_content = build_binding_config_content(resolution, lease=lease)
        config = json.loads(config_content)

        provider = config["provider"][PROVIDER_ID]
        assert provider["options"]["baseURL"] == "http://127.0.0.1:9000"
        assert provider["options"]["apiKey"] == lease.lease_id
        assert PROVIDER_FACING_MODEL in provider["models"]

    def test_config_does_not_contain_provider_master(self) -> None:
        FAKE_MASTER = "provider-master-key-xyz-789"
        resolution = _make_binding_resolution("https://models.example.test/v1")
        lease = ExecutionLeaseHandle(
            lease_id="sk-" + secrets.token_urlsafe(24),
            relay_url="http://127.0.0.1:9000",
            model_id=CLI_SELECTOR,
        )
        config_content = build_binding_config_content(resolution, lease=lease)
        assert FAKE_MASTER not in config_content
        assert "master" not in config_content.lower()

    def test_config_api_key_without_lease_fails_closed(self) -> None:
        resolution = _make_binding_resolution("https://models.example.test/v1")
        with pytest.raises(ExecutorRuntimeError) as exc_info:
            build_binding_config_content(resolution)
        assert str(exc_info.value) == "api_key_lease_required"


# ---------------------------------------------------------------------------
# D. Direct fake-provider control (OpenCode -> fake provider, no relay)
# ---------------------------------------------------------------------------

class TestDirectFakeProviderControl:

    def test_opencode_direct_fake_provider(self) -> None:
        opencode_exe, is_cmd = resolve_opencode_cli()
        version_proc = subprocess.run(
            [opencode_exe, "--version"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        version_out = (version_proc.stdout or "").strip()
        assert version_out, "opencode --version produced no output"

        fake_port = _free_port()
        fake_url = "http://127.0.0.1:%d" % fake_port

        fake_srv, received = _start_fake_provider(fake_port)
        try:
            direct_config = json.dumps({
                "provider": {
                    PROVIDER_ID: {
                        "npm": PROVIDER_NPM,
                        "name": PROVIDER_NAME,
                        "options": {
                            "baseURL": fake_url,
                            "apiKey": "sk-" + secrets.token_urlsafe(24),
                        },
                        "models": {PROVIDER_FACING_MODEL: {}},
                    }
                }
            }, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

            child_env = build_binding_child_env(
                parent_env={"PATH": os.environ.get("PATH", ""), "SystemRoot": "C:\\Windows"},
                config_content=direct_config,
            )

            with tempfile.TemporaryDirectory() as tmp:
                worktree = Path(tmp) / "wt"
                worktree.mkdir(parents=True, exist_ok=True)
                _init_git_worktree(worktree)

                prompt_file = Path(tmp) / "prompt.txt"
                prompt_file.write_text(PROMPT, encoding="utf-8")

                argv = [
                    opencode_exe,
                    "run",
                    "--pure",
                    "--model",
                    CLI_SELECTOR,
                    "--dir",
                    str(worktree),
                    "--format",
                    "json",
                    "--auto",
                    "--file",
                    str(prompt_file),
                    "--",
                    "execute bounded task from attached prompt file",
                ]

                proc = subprocess.run(
                    argv,
                    cwd=str(worktree),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                    env=child_env,
                    check=False,
                )

                stdout = proc.stdout or ""
                stderr = proc.stderr or ""

                assert proc.returncode == 0, (
                    "direct OpenCode failed rc=%d stdout=%s stderr=%s"
                    % (proc.returncode, stdout[:200], stderr[:200])
                )

                assert len(received) >= 1, "fake provider received no request from OpenCode"
                req = received[-1]
                assert req["path"] == "/chat/completions"
                assert req["method"] == "POST"
                body_obj = json.loads(req["body"])
                assert body_obj.get("model") == PROVIDER_FACING_MODEL

                stdout_findings = _secret_scan(stdout)
                stderr_findings = _secret_scan(stderr)
                assert not stdout_findings, "stdout secret scan: %s" % stdout_findings
                assert not stderr_findings, "stderr secret scan: %s" % stderr_findings

        finally:
            fake_srv.shutdown()


# ---------------------------------------------------------------------------
# E. Relay + fake-provider run (OpenCode -> relay -> fake provider)
# ---------------------------------------------------------------------------

class TestRelayFakeProviderRun:

    def test_opencode_relay_fake_provider(self) -> None:
        opencode_exe, is_cmd = resolve_opencode_cli()

        fake_port = _free_port()
        fake_url = "http://127.0.0.1:%d" % fake_port
        master_key = "relay-probe-master-key-" + secrets.token_hex(16)

        fake_srv, fake_received = _start_fake_provider(fake_port)
        try:
            manager = CredentialRelayManager(default_expiry_seconds=120.0)
            snap = _make_snapshot(fake_url, master_key=master_key)

            relay = CredentialRelayServer(
                manager, host="127.0.0.1", port=_free_port(), upstream_timeout=30.0
            )
            with relay:
                time.sleep(0.3)
                lease = manager.create_lease(snap, relay_url=relay.url)
                assert manager.has_active_lease(lease.lease_id)

                relay_config = json.dumps({
                    "provider": {
                        PROVIDER_ID: {
                            "npm": PROVIDER_NPM,
                            "name": PROVIDER_NAME,
                            "options": {
                                "baseURL": relay.url,
                                "apiKey": lease.lease_id,
                            },
                            "models": {PROVIDER_FACING_MODEL: {}},
                        }
                    }
                }, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
                assert master_key not in relay_config

                child_env = build_binding_child_env(
                    parent_env={"PATH": os.environ.get("PATH", ""), "SystemRoot": "C:\\Windows"},
                    config_content=relay_config,
                )

                with tempfile.TemporaryDirectory() as tmp:
                    worktree = Path(tmp) / "wt"
                    worktree.mkdir(parents=True, exist_ok=True)
                    _init_git_worktree(worktree)

                    prompt_file = Path(tmp) / "prompt.txt"
                    prompt_file.write_text(PROMPT, encoding="utf-8")

                    argv = [
                        opencode_exe,
                        "run",
                        "--pure",
                        "--model",
                        CLI_SELECTOR,
                        "--dir",
                        str(worktree),
                        "--format",
                        "json",
                        "--auto",
                        "--file",
                        str(prompt_file),
                        "--",
                        "execute bounded task from attached prompt file",
                    ]

                    proc = subprocess.run(
                        argv,
                        cwd=str(worktree),
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=60,
                        env=child_env,
                        check=False,
                    )

                    stdout = proc.stdout or ""
                    stderr = proc.stderr or ""

                    assert proc.returncode == 0, (
                        "relay OpenCode failed rc=%d stdout=%s stderr=%s"
                        % (proc.returncode, stdout[:200], stderr[:200])
                    )

                    assert len(fake_received) >= 1, "fake provider received no request through relay"
                    req = fake_received[-1]
                    assert req["path"] == "/chat/completions"
                    assert req["method"] == "POST"
                    assert req["authorization"] == "Bearer " + master_key

                    body_obj = json.loads(req["body"])
                    assert body_obj.get("model") == PROVIDER_FACING_MODEL

                    manager.release_lease(lease.lease_id)
                    assert not manager.has_active_lease(lease.lease_id)

        finally:
            fake_srv.shutdown()
