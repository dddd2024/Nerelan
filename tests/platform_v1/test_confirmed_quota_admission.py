"""Provider-free hard quota admission: exhausted != near-limit forecast."""
from __future__ import annotations

import pytest

from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.platform_v1.quota_guard import check, CONFIRMED_EXHAUSTION_REASONS
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost
from reverse_agent.platform_v1.binding_resolver import BindingResolutionError


def _connection():
    return {"executor_provider_id": "codex", "auth_method": "external_cli_session"}


def _window(used=100.0, **kwargs):
    return dict(window="five_hour", basis="official_percent",
                used_percent=used, reset_passed=False, **kwargs)


@pytest.mark.parametrize("used,expected,reason", [
    (100, "switch", "observed_exhausted"),
    (99, "switch", "almost_exhausted"),
    (90, "warn", "nearly_exhausted"),
    (45, "ok", "no_signal"),
])
def test_observed_percentage_distinct_from_near_exhaustion(used, expected, reason):
    verdict = check(_connection(), {"codex": {"windows": [_window(used)]}}, None)
    assert (verdict["decision"], verdict["reason"]) == (expected, reason)
    assert ("observed_exhausted" in CONFIRMED_EXHAUSTION_REASONS)


def test_confirmed_rejected_window_beats_other_nominally_available_window():
    verdict = check(_connection(), {"codex": {"windows": [
        _window(45), _window(32) | {"status": "rejected", "window": "weekly"}]}}, None)
    assert (verdict["decision"], verdict["reason"], verdict["window"]) == (
        "switch", "observed_exhausted", "weekly")


def test_confirmed_account_limit_beats_predicted_task_fit():
    verdict = check(_connection(), {"codex": {"windows": [
        _window(100) | {"remaining_units_range": [100, 120]},
    ]}}, 0.2)
    assert verdict["reason"] == "observed_exhausted"


def test_already_elapsed_window_cannot_stay_a_confirmed_blocker():
    verdict = check(_connection(), {"codex": {"windows": [
        _window(100) | {"reset_passed": True},
    ]}}, 0.1)
    assert verdict["reason"] == "window_reset"


def test_unknown_window_is_not_misrepresented_as_observed_full():
    verdict = check(_connection(), {"codex": {"state": "UNKNOWN", "windows": []}}, None)
    assert (verdict["decision"], verdict["reason"]) == ("ok", "quota_unknown")
    assert verdict["reason"] not in CONFIRMED_EXHAUSTION_REASONS


@pytest.mark.parametrize("reason", ["limit_hit", "limit_reached", "observed_exhausted"])
def test_explicit_binding_route_refuses_provider_confirmed_exhaustion(monkeypatch, reason):
    store = ModelProfileStore()
    store.upsert_connection({
        "connection_id": "codex-account", "name": "Test Codex",
        "provider": "codex", "base_url": "https://chatgpt.com",
        "auth_method": "external_cli_session", "enabled": True,
    })
    store.upsert_binding({
        "binding_id": "named-codex", "name": "Named", "connection_id": "codex-account",
        "executor_id": "codex", "model_id": "gpt-test", "enabled": True,
    })
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    monkeypatch.setattr(host, "_quota_check",
        lambda binding: {"decision": "switch", "reason": reason, "window": "five_hour"})
    resolver = host._binding_resolver_factory("http://127.0.0.1:1")
    with pytest.raises(BindingResolutionError, match="quota_exhausted:" + reason):
        resolver.resolve("named-codex", task_executor="codex")
    assert host._quota_guard_entries()[0]["decision"] == "refuse"


def test_uncertain_insufficient_forecast_does_not_automatically_block_agent_team(monkeypatch):
    store = ModelProfileStore()
    store.upsert_connection({
        "connection_id": "claude-account", "name": "Claude", "provider": "claude-code",
        "base_url": "https://claude.ai", "auth_method": "external_cli_session",
        "enabled": True})
    store.upsert_binding({
        "binding_id": "account-model", "name": "Current", "connection_id": "claude-account",
        "executor_id": "claude_code", "model_id": "opus", "enabled": True})
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    monkeypatch.setattr(host, "_quota_check",
                        lambda _: {"decision": "switch", "reason": "predicted_insufficient"})
    assert host._quota_guarded("coder", "claude_code", "account-model", {}) == (
        "claude_code", "account-model")
    assert host._quota_guard_entries()[0]["decision"] == "warn"