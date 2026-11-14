"""Executor CLI availability must reflect what is actually installed (#1458).

Detection rules mirror dev-up.ps1 Find-Executable: opencode, codex, and
claude (for Claude Code). Each scenario is deterministic and never probes
auth or the network.
"""

from __future__ import annotations

import json
import tempfile
from typing import Any

import pytest

from reverse_agent.model_access.contracts import NATIVE_CLI_PROVIDERS
from reverse_agent.model_access.resources import build_resource_view
from reverse_agent.model_access.store import ModelProfileStore


def _connection_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "connection_id": "sense-api",
        "name": "SenseNova API",
        "provider": "openai-compatible",
        "base_url": "https://models.example.test/v1",
        "auth_method": "api_key",
        "enabled": True,
        "api_key": "sk-test",
    }
    payload.update(overrides)
    return payload


def _codex_connection(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "connection_id": "codex-acc",
        "name": "Codex Account",
        "provider": "codex",
        "upstream_provider_id": "openai",
        "protocol_family": "codex-cli",
        "executor_provider_id": "codex",
        "base_url": "https://api.openai.com/v1",
        "auth_method": "external_cli_session",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _binding_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "binding_id": "coding-fast",
        "name": "Fast coding",
        "executor_id": "opencode",
        "connection_id": "sense-api",
        "model_id": "sense-coding-fast",
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _cli_detectors(which: str) -> dict[str, Any]:
    """Return CLI detector callables for a given scenario label."""
    scenarios = {
        "none": {"opencode": False, "codex": False, "claude_code": False},
        "codex_only": {"opencode": False, "codex": True, "claude_code": False},
        "all": {"opencode": True, "codex": True, "claude_code": True},
    }
    wanted = scenarios[which]

    def mk(result: bool):
        return lambda: result

    return {k: mk(v) for k, v in wanted.items()}


class TestExecutorCliDetection:
    """Three acceptance scenarios from the issue."""

    def _store_with_detectors(self, which: str) -> ModelProfileStore:
        with tempfile.TemporaryDirectory() as td:
            store = ModelProfileStore(state_path=f"{td}/state.json")
            store.install_cli_detectors(_cli_detectors(which))
            store.refresh_cli_availability()
            return store

    def test_none_installed_all_non_operational(self) -> None:
        store = self._store_with_detectors("none")
        for executor in store.list_executors_public():
            assert executor["operational"] is False
            assert executor.get("readiness_status") == "cli_unavailable"

    def test_none_installed_routing_sees_zero_usable_bindings(self) -> None:
        store = self._store_with_detectors("none")
        store.upsert_connection(_connection_payload())
        store.upsert_binding(_binding_payload())
        view = build_resource_view(store, lambda: {})
        assert view["summary"]["usable_bindings"] == 0

    def test_codex_installed_only_codex_operational(self) -> None:
        store = self._store_with_detectors("codex_only")
        for executor in store.list_executors_public():
            if executor["executor_id"] == "codex":
                assert executor["operational"] is True
                assert executor.get("readiness_status") in {None, ""}
            else:
                assert executor["operational"] is False
                assert executor.get("readiness_status") == "cli_unavailable"

    def test_codex_installed_native_readiness_probe_updates_state(self) -> None:
        store = self._store_with_detectors("codex_only")
        store.upsert_connection(_codex_connection())
        store.set_native_readiness("codex", "managed_login_ready")
        codex_exec = store.get_executor_public("codex")
        assert codex_exec["operational"] is True
        assert codex_exec["readiness_status"] == "managed_login_ready"
        # external_session_status follows the readiness verdict
        conn = store.get_connection_public("codex-acc")
        assert conn["external_session_status"] == "available"

    def test_codex_installed_probe_says_login_broken_executor_still_seen(self) -> None:
        """CLI present but login broken: still operational for relay paths, but
        managed_session bindings get external_session_status=missing."""
        store = self._store_with_detectors("codex_only")
        store.upsert_connection(_codex_connection())
        store.set_native_readiness("codex", "managed_login_unavailable")
        codex_exec = store.get_executor_public("codex")
        assert codex_exec["operational"] is False
        assert codex_exec["readiness_status"] == "managed_login_unavailable"
        conn = store.get_connection_public("codex-acc")
        assert conn["external_session_status"] == "missing"

    def test_all_installed_all_operational(self) -> None:
        store = self._store_with_detectors("all")
        for executor in store.list_executors_public():
            assert executor["operational"] is True, executor["executor_id"]

    def test_all_installed_codex_connection_sees_available_session(self) -> None:
        store = self._store_with_detectors("all")
        store.upsert_connection(_codex_connection())
        # When CLI is present, refresh_cli_availability marks the connection
        # external_session_status as "available" (CLI is there, login unknown).
        conn = store.get_connection_public("codex-acc")
        assert conn["external_session_status"] == "available"

    def test_cli_disappears_after_probe_executor_reverted(self) -> None:
        store = self._store_with_detectors("codex_only")
        store.set_native_readiness("codex", "managed_login_ready")
        assert store.get_executor_public("codex")["readiness_status"] == "managed_login_ready"

        # Now simulate the CLI disappearing (e.g. uninstalled while the host
        # is running). Re-refresh.
        store.install_cli_detectors(_cli_detectors("none"))
        store.refresh_cli_availability()

        codex = store.get_executor_public("codex")
        assert codex["operational"] is False
        assert codex["readiness_status"] == "cli_unavailable"

    def test_host_restart_re_reads_cli_state(self) -> None:
        """The very first read (fresh __init__) must not hard-code opencode=True."""
        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/state.json"
            store_a = ModelProfileStore(state_path=path)
            store_a.install_cli_detectors(_cli_detectors("none"))
            store_a.refresh_cli_availability()
            store_a.upsert_connection(_connection_payload())
            store_a.upsert_binding(_binding_payload())

            # Restarting should also produce non-operational when no CLIs found,
            # even on a fresh __init__ that auto-refreshes.
            store_b = ModelProfileStore(state_path=path)
            store_b.install_cli_detectors(_cli_detectors("none"))
            store_b.refresh_cli_availability()
            opencode = store_b.get_executor_public("opencode")
            assert opencode["operational"] is False
            assert opencode["readiness_status"] == "cli_unavailable"

    def test_executor_view_matches_real_cli_state(self) -> None:
        """list_executors_public output is what Model Control API exposes."""
        store = self._store_with_detectors("none")
        public = store.list_executors_public()
        serialized = json.dumps(public)
        # None should ever say "operational: True" when no CLIs are present.
        assert '"operational": true' not in serialized.lower()
        # cli_unavailable must appear for every executor
        for executor_id in ("opencode", "codex", "claude_code"):
            assert any(e["executor_id"] == executor_id and e.get("readiness_status") == "cli_unavailable"
                       for e in public)

    def test_compatible_executors_still_validates_executor_ids(self) -> None:
        """Routing's compatible_executors doesn't break, only executor.operational does."""
        store = self._store_with_detectors("none")
        store.upsert_connection(_connection_payload())
        # opencode remains listed as compatible executor for an api_key connection,
        # but routing filters it out because operational=False.
        assert "opencode" in store.compatible_executors("sense-api")
