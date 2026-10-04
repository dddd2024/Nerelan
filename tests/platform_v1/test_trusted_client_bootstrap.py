"""Native Node transport and private launcher boundaries; no actual browser."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading

import pytest

from reverse_agent.platform_v1.trusted_client import TrustedClient, client_environment

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "a" * 64


def test_native_node_transport_suite_is_blocking_and_provider_free():
    node = shutil.which("node")
    assert node, "required native Node capability unavailable"
    result = subprocess.run([node, "--test", "--test-reporter=tap", str(ROOT / "frontend/trusted-client.node-test.mjs")],
                            capture_output=True, timeout=90, cwd=ROOT / "frontend", env=client_environment())
    print(result.stdout.decode("utf-8", errors="replace"))
    assert result.returncode == 0, result.stdout.decode("utf-8", errors="replace") + result.stderr.decode("utf-8", errors="replace")
    assert b"# fail 0" in result.stdout


def test_production_dependency_is_exact_and_existing_lock_is_consistent():
    package = json.loads((ROOT / "frontend/package.json").read_text())
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
    assert package["dependencies"]["playwright-core"] == "1.62.1"
    assert lock["packages"][""]["dependencies"]["playwright-core"] == "1.62.1"
    installed = lock["packages"]["node_modules/playwright-core"]
    assert installed["version"] == "1.62.1" and not installed.get("dev", False)


@pytest.mark.parametrize("key", ["NODE_OPTIONS", "DEBUG", "PWDEBUG", "HTTP_PROXY", "OPENAI_API_KEY", "X_NERELAN_CLIENT_CAPABILITY"])
def test_native_child_environment_excludes_credentials_and_debug_loaders(monkeypatch, key):
    monkeypatch.setenv(key, TOKEN)
    environment = client_environment()
    assert key not in environment and TOKEN not in environment.values()


def test_only_private_stdin_receives_client_capability(monkeypatch):
    captured = {}
    finished = threading.Event()
    class FakeProcess:
        pid = 12345
        def __init__(self):
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO(b'{"state":"ready","pid":12345}\n')
        def poll(self): return 0 if finished.is_set() else None
        def wait(self, timeout=None):
            if timeout is not None: finished.set()
            else: finished.wait(timeout=3)
            return 0
    process = FakeProcess()
    def popen(argv, **kwargs):
        captured.update(argv=argv, options=kwargs)
        return process
    monkeypatch.setattr(subprocess, "Popen", popen)
    client = TrustedClient(node_executable="node", frontend_url="http://127.0.0.1:4173", task_api_url="http://127.0.0.1:8766")
    try:
        client.start(TOKEN)
        packet = json.loads(process.stdin.getvalue())
        assert packet["capability"] == TOKEN
        assert TOKEN not in json.dumps(captured) and TOKEN not in repr(client)
        assert captured["options"]["close_fds"] is True
        assert captured["options"]["stderr"] == subprocess.DEVNULL
    finally:
        client.stop()
        finished.set()
    assert client.pid is None and not client.ready


def test_bootstrap_failure_revokes_delivery_without_sensitive_exception_context(monkeypatch):
    def fail(*args, **kwargs): raise OSError(TOKEN)
    monkeypatch.setattr(subprocess, "Popen", fail)
    client = TrustedClient(node_executable="node", frontend_url="http://127.0.0.1:4173", task_api_url="http://127.0.0.1:8766")
    with pytest.raises(RuntimeError) as error:
        client.start(TOKEN)
    assert str(error.value) == "trusted_client_bootstrap_failed"
    assert error.value.__context__ is None


@pytest.mark.parametrize("url", ["https://127.0.0.1:4173", "http://evil.example:4173", "http://u:p@127.0.0.1:4173", "http://127.0.0.1:4173/?cap=" + TOKEN])
def test_invalid_bootstrap_target_is_rejected_without_echo(url):
    with pytest.raises(ValueError) as error:
        TrustedClient(node_executable="node", frontend_url=url, task_api_url="http://127.0.0.1:8766")
    assert str(error.value) == "trusted_client_configuration_invalid"
