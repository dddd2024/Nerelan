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


# --- #1260: Magpie subscription windows feed the guard ---


def _magpie_snapshot(*accounts):
    return {"status": "available", "version": "0.1.1250", "models": [], "accounts": list(accounts)}


def _magpie_account(provider, used, resets_at, state="FRESH", name="five_hour"):
    return {"provider": provider, "kind": "subscription", "plan": "Pro", "state": state,
            "reason": None if state == "FRESH" else "stale_reading",
            "observed_at": "2026-10-19T11:00:00Z",
            "windows": [{"name": name, "used_percent": used, "remaining_percent": 100 - used,
                         "resets_at": resets_at, "unlimited": False}]}


def test_magpie_full_window_drives_switch_until_resets_at():
    from reverse_agent.model_access.subscription_quota import magpie_quota_windows
    snapshot = _magpie_snapshot(_magpie_account("codex", 100.0, "2026-10-19T16:00:00Z"))
    quotas = magpie_quota_windows(snapshot, now=1761487200.0)  # 2026-10-19T11:00Z
    verdict = check(_connection(), quotas, None)
    assert (verdict["decision"], verdict["reason"]) == ("switch", "observed_exhausted")
    assert quotas["codex"]["windows"][0]["resets_at"] == "2026-10-19T16:00:00Z"
    assert quotas["codex"]["windows"][0]["reset_passed"] is False


def test_stale_magpie_account_contributes_no_windows():
    from reverse_agent.model_access.subscription_quota import magpie_quota_windows
    snapshot = _magpie_snapshot(_magpie_account("codex", 100.0, "2026-10-19T16:00:00Z", state="STALE"))
    assert magpie_quota_windows(snapshot) == {}


def test_unknown_magpie_provider_is_ignored():
    from reverse_agent.model_access.subscription_quota import magpie_quota_windows
    snapshot = _magpie_snapshot(_magpie_account("workbuddy", 100.0, "2026-10-19T16:00:00Z"))
    assert magpie_quota_windows(snapshot) == {}


def test_host_falls_back_to_local_when_magpie_disabled(monkeypatch):
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "codex-account", "name": "Codex", "provider": "codex",
                             "base_url": "https://chatgpt.com", "auth_method": "external_cli_session",
                             "enabled": True})
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    host._task_store = TaskStore(":memory:")
    local = {"codex": {"state": "UNKNOWN", "windows": []}}
    monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
    assert host._merge_magpie_quotas(local) == local


def test_host_uses_fresh_magpie_windows_over_local(monkeypatch):
    from reverse_agent.model_access import magpie
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    host._task_store = TaskStore(":memory:")
    local = {"codex": {"state": "UNKNOWN", "windows": []}}
    snapshot = _magpie_snapshot(_magpie_account("codex", 100.0, "2026-10-19T16:00:00Z"))
    monkeypatch.setenv("REVERSE_AGENT_MAGPIE", "1")
    monkeypatch.setattr(magpie, "fetch_magpie_snapshot", lambda *a, **k: snapshot)
    merged = host._merge_magpie_quotas(local)
    assert merged["codex"]["provenance"] == "EXTERNAL_MAGPIE"
    assert merged["codex"]["windows"][0]["used_percent"] == 100.0


def test_limit_hit_failure_holds_until_reported_reset(monkeypatch):
    from reverse_agent.platform_v1.run_store import TaskStore
    import time
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "codex-account", "name": "Codex", "provider": "codex",
                             "base_url": "https://chatgpt.com", "auth_method": "external_cli_session",
                             "enabled": True})
    store.upsert_binding({"binding_id": "codex-gpt", "name": "Codex", "connection_id": "codex-account",
                          "executor_id": "codex", "model_id": "gpt-test", "enabled": True})
    tasks = TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._store, host._task_store = store, tasks
    future = int(time.time()) + 3600
    quota = {"codex": {"windows": [{"window": "five_hour", "basis": "official_percent",
                                     "used_percent": 100.0, "resets_at": _iso(future),
                                     "reset_passed": False}]}}
    monkeypatch.setattr(host, "_subscription_quotas", lambda: quota, raising=False)
    failed = tasks.create_task(title="t", repository="o/r", executor_kind="codex", binding_ref="codex-gpt")
    tasks._conn.execute("UPDATE tasks SET status = 'FAILED', failure_classification = ? WHERE id = ?",
                        ("codex_usage_limit", failed.id))
    tasks._conn.commit()
    until = host._limit_hit_until(store.get_connection_public("codex-account"))
    assert until == pytest.approx(future)
    verdict = host._quota_check(store.list_bindings_public()[0])
    assert (verdict["decision"], verdict["reason"]) == ("switch", "limit_hit")


def _iso(epoch):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")