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


def test_insufficient_forecast_holds_agent_team(monkeypatch):
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
    from reverse_agent.platform_v1.run_store import TaskStoreError
    with pytest.raises(TaskStoreError, match="QUOTA_WAIT:predicted_insufficient"):
        host._quota_guarded("coder", "claude_code", "account-model", {})
    assert host._quota_guard_entries()[0]["decision"] == "refuse"


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
    from reverse_agent.model_access import magpie, subscription_quota
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    host = object.__new__(CombinedTrustedHost)
    host._store = store
    host._task_store = TaskStore(":memory:")
    local = {"codex": {"state": "UNKNOWN", "windows": []}}
    snapshot = _magpie_snapshot(_magpie_account("codex", 100.0, "2026-10-19T16:00:00Z"))
    monkeypatch.setattr(subscription_quota.time, "time", lambda: 1792407600.0)
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

@pytest.fixture
def reset_host(monkeypatch):
    from types import SimpleNamespace
    from reverse_agent.platform_v1 import trusted_host, run_store
    now = 1792407600.0
    monkeypatch.setattr(trusted_host.time, "time", lambda: now)
    monkeypatch.setattr(run_store, "_utc_now", lambda: _iso(now))
    tasks = run_store.TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._task_store = tasks
    host._store = SimpleNamespace(list_bindings_public=lambda: [
        {"binding_id": "b", "connection_id": "account"}])
    # Offline stand-in for unavailable quota sources (including Magpie).
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {})
    connection = {"connection_id": "account", "executor_provider_id": "codex"}

    def fail(reset="", age=0, classification="codex_usage_limit", detail=""):
        task = tasks.create_task(title="failure", repository="o/r", executor_kind="codex", binding_ref="b")
        task = tasks.classify_failure(task.id, classification=classification, detail=detail,
                                      failure_reset_at=reset)
        tasks._conn.execute("UPDATE tasks SET failure_at = ?, updated_at = ? WHERE id = ?",
                            (_iso(now - age), _iso(now - age), task.id))
        tasks._conn.commit()
        return task

    yield host, connection, now, fail
    tasks._conn.close()


def test_stated_five_hour_reset_without_magpie(reset_host, monkeypatch):
    host, connection, now, fail = reset_host
    from reverse_agent.model_access import magpie
    monkeypatch.setenv("REVERSE_AGENT_MAGPIE", "1")
    monkeypatch.setattr(magpie, "fetch_magpie_snapshot", lambda *a, **k: {"status": "unavailable"})
    monkeypatch.setattr(host, "_subscription_quotas", lambda: host._merge_magpie_quotas({}))
    task = fail(_iso(now + 5 * 3600))
    persisted = host._task_store.get_task(task.id)
    assert persisted.failure_reset_at == _iso(now + 5 * 3600)
    assert persisted.failure_at == _iso(now)
    assert host._limit_hit_until(connection) == pytest.approx(now + 5 * 3600)


def _local_cli(now, windows, **overrides):
    """Test evidence metadata only: wraps unchanged windows as a fresh attributed local-CLI reading."""
    return {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI", "source": "codex_session_log",
            "observed_at": _iso(now), "windows": windows, **overrides}


_NOT_FRESH_LOCAL_EVIDENCE = {
    "missing_source": lambda now: {"source": None, "provenance": ""},
    "undated": lambda now: {"observed_at": None},
    "stale": lambda now: {"observed_at": _iso(now - 700)},
    "future": lambda now: {"observed_at": _iso(now + 60)},
    "unknown_state": lambda now: {"state": "UNKNOWN"},
    "external_provider": lambda now: {"source": "magpie", "provenance": "EXTERNAL_MAGPIE"},
}


@pytest.mark.parametrize("kind", sorted(_NOT_FRESH_LOCAL_EVIDENCE) + ["foreign_account"])
def test_unfresh_or_unattributed_evidence_does_not_extend_stated_hold(reset_host, monkeypatch, kind):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 3600))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: _unfresh_quotas(
        kind, now, [{"window": "weekly", "used_percent": 100, "resets_at": _iso(now + 5 * 86400)}]))
    assert host._limit_hit_until(connection) == now + 2 * 3600


@pytest.mark.parametrize("kind", sorted(_NOT_FRESH_LOCAL_EVIDENCE) + ["foreign_account"])
def test_unfresh_or_unattributed_evidence_does_not_replace_fixed_fallback(reset_host, monkeypatch, kind):
    host, connection, now, fail = reset_host
    fail("")
    monkeypatch.setattr(host, "_subscription_quotas", lambda: _unfresh_quotas(
        kind, now, [{"resets_at": _iso(now + 7200)}]))
    assert host._limit_hit_until(connection) == now + 3600


def _unfresh_quotas(kind, now, windows):
    if kind == "foreign_account":
        return {"other-key": _local_cli(now, windows, account_ref="other")}
    return {"codex": _local_cli(now, windows, **_NOT_FRESH_LOCAL_EVIDENCE[kind](now))}


def test_fresh_local_cli_evidence_helper_is_accepted_for_exhausted_window(reset_host, monkeypatch):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 3600))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": _local_cli(now, [
        {"window": "weekly", "used_percent": 100, "resets_at": _iso(now + 5 * 86400)}])})
    assert host._limit_hit_until(connection) == now + 5 * 86400


@pytest.mark.parametrize("hours", [2, 8])
def test_stated_reset_ignores_quota_windows_without_exhaustion(reset_host, monkeypatch, hours):
    host, connection, now, fail = reset_host
    fail(_iso(now + 5 * 3600))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": {"windows": [
        {"resets_at": _iso(now + 3600)}, {"resets_at": _iso(now + hours * 3600)}]}})
    assert host._limit_hit_until(connection) == now + 5 * 3600


def test_stated_reset_alone_without_windows(reset_host):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 3600))
    assert host._limit_hit_until(connection) == now + 2 * 3600


def test_stated_reset_ignores_non_exhausted_weekly_window(reset_host, monkeypatch):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 3600))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": _local_cli(now, [
        {"window": "five_hour", "used_percent": 100,
         "resets_at": _iso(now + 5 * 3600)},
        {"window": "weekly", "used_percent": 65,
         "resets_at": _iso(now + 5 * 86400)}])})
    assert host._limit_hit_until(connection) == now + 5 * 3600


@pytest.mark.parametrize("exhaustion", [{"used_percent": 100}, {"remaining_percent": 0}])
def test_stated_reset_extended_by_exhausted_weekly_window(reset_host, monkeypatch, exhaustion):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 3600))
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": _local_cli(now, [
        {"window": "weekly", **exhaustion, "resets_at": _iso(now + 5 * 86400)}])})
    assert host._limit_hit_until(connection) == now + 5 * 86400


def test_multiple_failures_and_hold_older_than_one_day(reset_host):
    host, connection, now, fail = reset_host
    fail(_iso(now + 2 * 86400), age=2 * 86400)
    fail(_iso(now + 5 * 3600))
    fail(_iso(now + 6 * 86400), classification="quota_exhausted:limit_hit")
    assert host._limit_hit_until(connection) == now + 2 * 86400


@pytest.mark.parametrize("reset", ["", "bad", "2026-10-19T15:00:00", "past", "over"])
def test_invalid_stated_resets_preserve_fallback(reset_host, monkeypatch, reset):
    host, connection, now, fail = reset_host
    reset = {"past": _iso(now - 1), "over": _iso(now + 7 * 86400 + 1)}.get(reset, reset)
    fail(reset)
    assert host._limit_hit_until(connection) == now + 3600
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": _local_cli(now, [
        {"resets_at": _iso(now + 7200)}])})
    assert host._limit_hit_until(connection) == now + 7200


def test_expired_stated_failure_cannot_renew(reset_host, monkeypatch):
    host, connection, now, fail = reset_host
    fail(_iso(now - 1), age=7200)
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {"codex": _local_cli(now, [
        {"resets_at": _iso(now + 7200)}])})
    assert host._limit_hit_until(connection) is None


def test_seven_day_bound_is_anchored_to_failure(reset_host):
    host, connection, now, fail = reset_host
    fail(_iso(now + 6 * 86400), age=2 * 86400)
    assert host._limit_hit_until(connection) is None


def test_expired_legacy_failure_and_host_refusal_do_not_renew(reset_host):
    host, connection, now, fail = reset_host
    fail(age=2 * 86400)
    fail(_iso(now + 86400), classification="quota_exhausted:limit_hit")
    assert host._limit_hit_until(connection) is None


def test_exact_seven_day_stated_reset_is_accepted(reset_host):
    host, connection, now, fail = reset_host
    fail(_iso(now + 5 * 86400), age=2 * 86400)
    assert host._limit_hit_until(connection) == now + 5 * 86400


def test_october_19_router_avoids_codex_and_preserves_capability():
    from tests.platform_v1.test_model_router import candidate, choose
    pool = [candidate("codex", "gpt-6-sol", "subscription", "codex",
                      short_headroom=.10, task_short_fraction=.05,
                      weekly_headroom=.60, task_weekly_fraction=.02),
            candidate("weak", "flash-lite"), candidate("fit", "opus", "subscription")]
    assert choose(pool, difficulty=5)["binding_ref"] == "fit"


def test_weekly_only_router_capacity_blocks_without_reset_signal():
    from tests.platform_v1.test_model_router import candidate, choose
    pool = [candidate("weekly-full", "gpt-6-sol", "subscription", "codex",
                      short_headroom=.80, task_short_fraction=.01,
                      weekly_headroom=.12, task_weekly_fraction=.03),
            candidate("fit", "opus", "subscription")]
    assert choose(pool, difficulty=5)["binding_ref"] == "fit"


_PLAN_EXHAUSTED = "opencode_nonzero:exit=1:quota_exhausted name=APIError status=429 message=token plan entitlement exhausted"


def test_executor_reported_plan_exhaustion_holds_longer_than_a_rate_limit(reset_host):
    """#1497: a used-up plan stays held for hours; a plain 429 an hour."""
    host, connection, now, fail = reset_host
    fail(age=2 * 3600, classification="api_error_429",
         detail="opencode_nonzero:exit=1:api_error_429 name=APIError status=429 message=too many requests")
    assert host._limit_hit_until(connection) is None
    fail(age=2 * 3600, classification="quota_exhausted", detail=_PLAN_EXHAUSTED)
    assert host._limit_hit_until(connection) == now + 3 * 3600


def test_stated_reset_still_beats_the_plan_exhaustion_fallback(reset_host):
    host, connection, now, fail = reset_host
    fail(_iso(now + 600), classification="quota_exhausted", detail=_PLAN_EXHAUSTED)
    assert host._limit_hit_until(connection) == now + 600


@pytest.mark.parametrize("detail", ["quota_exhausted:limit_hit", "quota_exhausted:limit_hit:no_alternative", ""])
def test_host_quota_refusals_are_not_account_evidence(reset_host, detail):
    host, connection, now, fail = reset_host
    fail(classification="quota_exhausted", detail=detail)
    assert host._limit_hit_until(connection) is None


def test_plan_exhausted_binding_is_not_selected_again_in_the_window(monkeypatch):
    """The next dispatch after a plan-exhaustion failure switches away while the hold lasts."""
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    store.upsert_connection({"connection_id": "glm-plan", "name": "GLM", "provider": "openai_compatible",
                             "base_url": "https://example.invalid/v1", "auth_method": "api_key",
                             "enabled": True})
    store.upsert_binding({"binding_id": "coding-glm", "name": "GLM", "connection_id": "glm-plan",
                          "executor_id": "opencode", "model_id": "glm-test", "enabled": True})
    tasks = TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._store, host._task_store = store, tasks
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {}, raising=False)
    failed = tasks.create_task(title="t", repository="o/r", executor_kind="opencode", binding_ref="coding-glm")
    tasks.classify_failure(failed.id, classification="quota_exhausted", detail=_PLAN_EXHAUSTED)
    verdict = host._quota_check(store.list_bindings_public()[0])
    assert (verdict["decision"], verdict["reason"]) == ("switch", "limit_hit")


def _gateway_host(monkeypatch, *, account_ref=None):
    """One gateway connection (as Magpie) fronting two upstreams, plus a second model of the first."""
    from reverse_agent.platform_v1.run_store import TaskStore
    store = ModelProfileStore()
    connection = {"connection_id": "gateway", "name": "Gateway", "provider": "openai_compatible",
                  "base_url": "http://127.0.0.1:3425/v1", "auth_method": "none", "enabled": True}
    if account_ref:
        connection["account_ref"] = account_ref
    store.upsert_connection(connection)
    for binding_id, model in (("trae-glm", "trae-cn/glm-5.2"), ("trae-deepseek", "trae-cn/deepseek-v4.1-flash"),
                              ("copilot-sonnet", "copilot/claude-sonnet-5.5")):
        store.upsert_binding({"binding_id": binding_id, "name": binding_id, "connection_id": "gateway",
                              "executor_id": "opencode", "model_id": model, "enabled": True})
    tasks = TaskStore(":memory:")
    host = object.__new__(CombinedTrustedHost)
    host._store, host._task_store = store, tasks
    monkeypatch.setattr(host, "_subscription_quotas", lambda: {}, raising=False)
    failed = tasks.create_task(title="t", repository="o/r", executor_kind="opencode", binding_ref="trae-deepseek")
    tasks.classify_failure(failed.id, classification="api_error_429",
                           detail="opencode_nonzero:exit=1:api_error_429 name=APIError status=429 message=rpm exhausted")
    bindings = {b["binding_id"]: b for b in store.list_bindings_public()}
    return host, store.get_connection_public("gateway"), bindings


def test_a_gateway_refusal_holds_only_that_upstream(monkeypatch):
    """2026-11-14: one upstream's 429 held every model behind Magpie for an hour."""
    host, connection, bindings = _gateway_host(monkeypatch)
    assert host._limit_hit_until(connection, bindings["trae-glm"]) is not None  # same upstream account
    assert host._limit_hit_until(connection, bindings["copilot-sonnet"]) is None  # another upstream
    verdict = host._quota_check(bindings["copilot-sonnet"])
    assert verdict is None or verdict.get("reason") != "limit_hit"
    assert host._quota_check(bindings["trae-glm"])["reason"] == "limit_hit"


def test_a_recorded_account_still_holds_every_model_it_serves(monkeypatch):
    host, connection, bindings = _gateway_host(monkeypatch, account_ref="one-account")
    assert host._limit_hit_until(connection, bindings["copilot-sonnet"]) is not None


def test_without_a_binding_the_whole_connection_is_held_as_before(monkeypatch):
    host, connection, _ = _gateway_host(monkeypatch)
    assert host._limit_hit_until(connection) is not None
