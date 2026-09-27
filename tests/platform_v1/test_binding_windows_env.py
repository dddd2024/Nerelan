"""Windows Binding child environment PATHEXT repair tests (Issue997).

Provider-free: no model, network, credential, or subprocess access. Windows and
non-Windows behavior are exercised deterministically by monkeypatching
``platform.system`` so the suite is reliable on any CI host.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from typing import Any

import pytest

from reverse_agent.platform_v1.binding_resolver import OpenCodeBindingResolution
from reverse_agent.platform_v1.opencode_executor import (
    _DEFAULT_WINDOWS_PATHEXT,
    build_binding_child_env,
    build_binding_config_content,
    build_role_child_env,
    build_role_permission_config,
)


def _resolution() -> OpenCodeBindingResolution:
    return OpenCodeBindingResolution(
        binding_ref="coding-fast",
        connection_id="sense-api",
        executor_id="opencode",
        provider_id="openai-compatible",
        model_id="openai-compatible/sense-coding-fast",
        base_url="https://models.example.test/v1",
        auth_method="external_cli_session",
        external_session_status="available",
    )


class _GuardedParent(Mapping[str, str]):
    """Mapping that forbids secret reads and iteration, mirroring the real guard."""

    forbidden = {
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "FAKE_TOKEN",
        "FAKE_PASSWORD",
        "GH_TOKEN",
    }

    def __init__(self, allowed: dict[str, Any] | None = None) -> None:
        self.read_keys: list[str] = []
        self.allowed = dict(allowed) if allowed else {
            "PATH": "C:\\safe-bin",
            "SystemRoot": "C:\\Windows",
        }

    def get(self, key: str, default=None):
        if key in self.forbidden:
            raise AssertionError(f"forbidden environment read: {key}")
        self.read_keys.append(key)
        return self.allowed.get(key, default)

    def __getitem__(self, key: str) -> str:
        raise AssertionError("environment must be accessed with explicit get")

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("environment iteration is forbidden")

    def __len__(self) -> int:
        raise AssertionError("environment sizing is forbidden")


# ---------------------------------------------------------------------------
# Windows tool execution / discovery
# ---------------------------------------------------------------------------

def test_windows_binding_env_injects_default_pathext_when_absent(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({"PATH": "C:\\safe-bin", "SystemRoot": "C:\\Windows"})
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert child["PATHEXT"] == _DEFAULT_WINDOWS_PATHEXT
    assert ".EXE" in child["PATHEXT"]


def test_windows_binding_env_preserves_parent_pathext(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({
        "PATH": "C:\\safe-bin",
        "SystemRoot": "C:\\Windows",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC",
    })
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert child["PATHEXT"] == ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC"


def test_windows_role_env_under_binding_injects_default_pathext(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({"PATH": "C:\\safe-bin", "SystemRoot": "C:\\Windows"})
    child = build_role_child_env(parent, build_binding_config_content(_resolution()), "coder")

    assert child["PATHEXT"] == _DEFAULT_WINDOWS_PATHEXT
    assert child["OPENCODE_CONFIG_CONTENT"]


def test_default_windows_pathext_covers_executable_extensions() -> None:
    for ext in (".COM", ".EXE", ".BAT", ".CMD"):
        assert ext in _DEFAULT_WINDOWS_PATHEXT


# ---------------------------------------------------------------------------
# Secret exclusion
# ---------------------------------------------------------------------------

def test_binding_env_never_reads_or_echoes_secrets(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({
        "PATH": "C:\\safe-bin",
        "SystemRoot": "C:\\Windows",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
    })
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert not parent.forbidden.intersection(parent.read_keys)
    serialized = json.dumps(child)
    for secret in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FAKE_TOKEN", "GH_TOKEN"):
        assert secret not in serialized

    allowed_keys = {
        "PATH", "SystemRoot", "PATHEXT", "OPENCODE_CONFIG_CONTENT",
        "OPENCODE_DISABLE_AUTOUPDATE", "OPENCODE_DISABLE_MODELS_FETCH",
        "OPENCODE_DISABLE_LSP_DOWNLOAD", "OPENCODE_DISABLE_DEFAULT_PLUGINS",
        "OPENCODE_DISABLE_CLAUDE_CODE",
    }
    assert set(child.keys()) == allowed_keys


# ---------------------------------------------------------------------------
# Role preservation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", ["planner", "reviewer", "coder"])
def test_windows_role_env_preserves_role_permissions(monkeypatch, role) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({"PATH": "C:\\safe-bin", "SystemRoot": "C:\\Windows"})
    child = build_role_child_env(parent, build_binding_config_content(_resolution()), role)

    assert child["PATHEXT"] == _DEFAULT_WINDOWS_PATHEXT
    merged = json.loads(child["OPENCODE_CONFIG_CONTENT"])
    assert "provider" in merged
    assert "permission" in merged
    expected_perm = json.loads(build_role_permission_config(role))
    assert merged["permission"] == expected_perm["permission"]


def test_windows_direct_auth_role_env_does_not_inject_default_pathext(monkeypatch) -> None:
    """Direct authenticated sessions (no binding config) preserve full parent
    inheritance and are NOT subject to the Binding PATHEXT default injection;
    unrelated account-auth behavior stays unchanged."""
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = {"PATH": "C:\\safe-bin", "SystemRoot": "C:\\Windows"}
    child = build_role_child_env(parent, None, "planner")

    assert "PATHEXT" not in child
    assert child["PATH"] == "C:\\safe-bin"
    assert child["OPENCODE_CONFIG_CONTENT"]


# ---------------------------------------------------------------------------
# Missing / nonstring values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [None, 123, "", [], object()])
def test_windows_binding_env_handles_missing_or_nonstring_pathext(monkeypatch, bad) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({
        "PATH": "C:\\safe-bin",
        "SystemRoot": "C:\\Windows",
        "PATHEXT": bad,
    })
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert child["PATHEXT"] == _DEFAULT_WINDOWS_PATHEXT


def test_windows_binding_env_skips_nonstring_path_and_systemroot(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Windows")
    parent = _GuardedParent({"PATH": 123, "SystemRoot": None})
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert "PATH" not in child
    assert "SystemRoot" not in child
    assert child["PATHEXT"] == _DEFAULT_WINDOWS_PATHEXT


# ---------------------------------------------------------------------------
# Non-Windows compatibility
# ---------------------------------------------------------------------------

def test_nonwindows_binding_env_does_not_inject_default_pathext(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Linux")
    parent = _GuardedParent({"PATH": "/usr/bin", "SystemRoot": ""})
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert "PATHEXT" not in child
    assert child["PATH"] == "/usr/bin"
    assert child["OPENCODE_CONFIG_CONTENT"]


def test_nonwindows_role_env_under_binding_does_not_inject_pathext(monkeypatch) -> None:
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Darwin")
    parent = _GuardedParent({"PATH": "/usr/bin", "SystemRoot": ""})
    child = build_role_child_env(parent, build_binding_config_content(_resolution()), "planner")

    assert "PATHEXT" not in child


def test_nonwindows_parent_pathext_copied_without_default_injection(monkeypatch) -> None:
    """The allowlist copies a usable parent PATHEXT regardless of platform
    (inert on non-Windows); the default is never injected on non-Windows."""
    import reverse_agent.platform_v1.opencode_executor as exec_mod

    monkeypatch.setattr(exec_mod.platform, "system", lambda: "Linux")
    parent = _GuardedParent({"PATH": "/usr/bin", "SystemRoot": "", "PATHEXT": ".EXE"})
    child = build_binding_child_env(parent, build_binding_config_content(_resolution()))

    assert child["PATHEXT"] == ".EXE"
    assert child["PATH"] == "/usr/bin"
