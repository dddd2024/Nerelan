"""Magpie account identities survive host merge and quota admission (provider-free).

Every scenario runs the real ``_subscription_quotas`` -> ``_merge_magpie_quotas``
-> ``_prepare_task_quota`` path. Only the Magpie fetch, the local CLI log readers
and the control store's ``prepare_quota_admission`` capture are replaced.
"""
from __future__ import annotations

from datetime import datetime, timezone
import time
from types import SimpleNamespace

import pytest

from reverse_agent.model_access import magpie, subscription_quota
from reverse_agent.model_access.resources import _quota
from reverse_agent.platform_v1 import model_router, run_store
from reverse_agent.platform_v1 import quota_reservation as reservation
from reverse_agent.platform_v1 import trusted_host, usage_ledger
from reverse_agent.platform_v1.goal_service import PlannedTask
from reverse_agent.platform_v1.quota_guard import check
from reverse_agent.platform_v1.run_store import TaskStoreError
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost


NATIVE = "synthetic-native-login"


def _iso(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _account(ref, used, weekly=30.0, *, provider="codex", state="FRESH", age=60):
    # Shape produced by magpie.parse_quotas for a FRESH reading.
    now = time.time()
    account = {"provider": provider, "kind": "subscription", "state": state, "observed_at": _iso(now - age),
               "provenance": "EXTERNAL_MAGPIE", "windows": [
                   {"name": "5 hours", "used_percent": used, "remaining_percent": 100 - used,
                    "resets_at": _iso(now + 3600), "unlimited": False},
                   {"name": "7 days", "used_percent": weekly, "remaining_percent": 100 - weekly,
                    "resets_at": _iso(now + 86400), "unlimited": False}]}
    if ref is not None:
        account["account_ref"] = ref
    return account


def _snapshot(*accounts):
    return {"status": "available", "version": "test", "models": [], "accounts": list(accounts)}


def _local_codex(used=40.0, age=60):
    # Shape produced by subscription_quota.codex_quota from this machine's session log.
    now = time.time()
    return {"state": "OBSERVED", "provenance": "OFFICIAL_VIA_CLI", "source": "codex_session_log",
            "observed_at": _iso(now - age), "usage_scope": "this_machine", "windows": [
                {"window": "five_hour", "basis": "official_percent", "used_percent": used,
                 "resets_at": _iso(now + 3600), "reset_passed": False},
                {"window": "weekly", "basis": "official_percent", "used_percent": 10.0,
                 "resets_at": _iso(now + 86400), "reset_passed": False}]}


def _host(monkeypatch, snapshot, *, account_ref=None, provider="codex", local=None, enabled=True):
    host = CombinedTrustedHost.__new__(CombinedTrustedHost)
    connection = {"connection_id": NATIVE, "executor_provider_id": provider,
                  "auth_method": "external_cli_session", "account_ref": account_ref}
    calls = []
    host._store = SimpleNamespace(
        list_bindings_public=lambda: [{"binding_id": "bind", "connection_id": NATIVE,
                                       "executor_id": "codex", "model_id": "gpt-6.1-sol"}],
        list_connections_public=lambda: [connection],
        get_connection_public=lambda _id: connection)
    host._task_store = SimpleNamespace()
    host._control_store = SimpleNamespace(quota_calibration=lambda account: {},
                                          prepare_quota_admission=lambda **kw: calls.append(kw))
    monkeypatch.delenv("REVERSE_AGENT_SUBSCRIPTION_QUOTA", raising=False)
    if enabled:
        monkeypatch.setenv("REVERSE_AGENT_MAGPIE", "1")
    else:
        monkeypatch.delenv("REVERSE_AGENT_MAGPIE", raising=False)
    fetches = []

    def fetch(*args, **kwargs):
        fetches.append(args)
        if isinstance(snapshot, Exception):
            raise snapshot
        return snapshot
    monkeypatch.setattr(magpie, "fetch_magpie_snapshot", fetch)
    monkeypatch.setattr(subscription_quota, "codex_quota",
                        lambda *a, **k: local if local is not None else subscription_quota.unknown("no_recent_codex_rate_limits"))
    monkeypatch.setattr(subscription_quota, "claude_quota", lambda *a, **k: subscription_quota.unknown("no_rate_limits_reported"))
    monkeypatch.setattr(usage_ledger, "latest_rate_limits", lambda *a, **k: None)
    monkeypatch.setattr(usage_ledger, "estimation_records", lambda store: [])
    return SimpleNamespace(host=host, calls=calls, fetches=fetches, connection=connection)


def _prepare(h):
    h.host._prepare_task_quota(SimpleNamespace(id="t", binding_ref="bind", executor_kind="codex",
                                               kind="code", difficulty=3))
    [call] = h.calls
    return call


def _assert_unknown(call, account):
    evidence = call["evidence"]
    assert call["account_ref"] == account and evidence["account_ref"] == account
    assert evidence["state"] == "UNKNOWN" and evidence["windows"] == []
    assert (evidence["eligible"], evidence["uncertain"], evidence["fresh"]) == (False, True, False)
    assert evidence["eligibility_reason"] == "refresh_required"
    assert evidence.get("source") != "magpie"
    assert reservation.admission(evidence, call["need"])["decision"] == "quota_wait"


def _two(order=1):
    # Built per test: observation freshness is measured against the real clock.
    return (_account("synthetic-a", 95.0), _account("synthetic-b", 20.0))[::order]


@pytest.mark.parametrize("order", [1, -1])
def test_merge_keeps_both_accounts_and_the_legacy_summary_in_either_order(monkeypatch, order):
    accounts = _two(order)
    h = _host(monkeypatch, _snapshot(*accounts))
    merged = h.host._subscription_quotas()
    assert merged["codex"]["account_ref"] == "synthetic-a"  # most constrained account, as before
    assert {k: v["account_ref"] for k, v in merged.items() if k.startswith("magpie-account:")} == {
        "magpie-account:synthetic-a": "synthetic-a", "magpie-account:synthetic-b": "synthetic-b"}
    # No cross-account or cross-window aggregation.
    assert [w["used_percent"] for w in merged["magpie-account:synthetic-a"]["windows"]] == [95.0, 30.0]
    assert [w["used_percent"] for w in merged["magpie-account:synthetic-b"]["windows"]] == [20.0, 30.0]
    reversed_host = _host(monkeypatch, _snapshot(*accounts[::-1]))
    assert reversed_host.host._subscription_quotas() == merged


@pytest.mark.parametrize("order", [1, -1])
def test_explicitly_bound_account_sees_only_its_own_magpie_evidence(monkeypatch, order):
    call = _prepare(_host(monkeypatch, _snapshot(*_two(order)), account_ref="synthetic-b"))
    evidence = call["evidence"]
    assert call["account_ref"] == "synthetic-b" and call["binding_ref"] == "bind"
    assert call["need"]["account_ref"] == "synthetic-b"
    assert (evidence["account_ref"], evidence["source"], evidence["fresh"]) == ("synthetic-b", "magpie", True)
    assert [(w["window"], w["used_percent"]) for w in evidence["windows"]] == [("five_hour", 20.0), ("weekly", 30.0)]
    assert reservation.admission(evidence, call["need"])["decision"] == "ok"
    assert call["resume_route"] is None


def test_bound_matching_constrained_account_keeps_its_own_limit(monkeypatch):
    call = _prepare(_host(monkeypatch, _snapshot(*_two(-1)), account_ref="synthetic-a"))
    assert call["evidence"]["account_ref"] == "synthetic-a" and call["evidence"]["fresh"]
    assert [w["used_percent"] for w in call["evidence"]["windows"]] == [95.0, 30.0]
    verdict = reservation.admission(call["evidence"], call["need"])
    assert verdict["decision"] == "quota_wait" and verdict["blocking_windows"] == ["five_hour"]


def test_bound_nonmatching_account_gets_typed_uncertainty(monkeypatch):
    h = _host(monkeypatch, _snapshot(*_two()), account_ref="synthetic-c", local=_local_codex())
    _assert_unknown(_prepare(h), "synthetic-c")
    assert len(h.fetches) >= 1


@pytest.mark.parametrize("order", [1, -1])
def test_unbound_native_login_never_adopts_a_foreign_magpie_summary(monkeypatch, order):
    # The diagnostic on 96cbe519: A's summary was relabeled OBSERVED/source=magpie for the native login.
    _assert_unknown(_prepare(_host(monkeypatch, _snapshot(*_two(order)))), NATIVE)


def test_unbound_native_login_keeps_its_local_cli_fallback_when_magpie_wins_the_summary(monkeypatch):
    local = _local_codex(used=40.0)
    h = _host(monkeypatch, _snapshot(*_two()), local=local)
    merged = h.host._subscription_quotas()
    assert merged["codex"]["source"] == "magpie"  # legacy presentation unchanged
    assert merged["local-cli:codex"] == local      # source distinction retained
    call = _prepare(h)
    evidence = call["evidence"]
    assert (call["account_ref"], evidence["account_ref"]) == (NATIVE, NATIVE)
    assert (evidence["source"], evidence["provenance"], evidence["fresh"]) == ("codex_session_log", "OFFICIAL_VIA_CLI", True)
    assert [w["used_percent"] for w in evidence["windows"]] == [40.0, 10.0]
    assert reservation.admission(evidence, call["need"])["decision"] == "ok"


def test_unbound_native_login_keeps_local_cli_contract_without_magpie(monkeypatch):
    local = _local_codex()
    h = _host(monkeypatch, _snapshot(*_two()), local=local, enabled=False)
    assert "local-cli:codex" not in h.host._subscription_quotas()
    call = _prepare(h)
    assert h.fetches == []
    assert (call["evidence"]["account_ref"], call["evidence"]["source"], call["evidence"]["fresh"]) == (
        NATIVE, "codex_session_log", True)


def test_stale_local_cli_fallback_stays_non_eligible(monkeypatch):
    call = _prepare(_host(monkeypatch, _snapshot(*_two()), local=_local_codex(age=3600)))
    evidence = call["evidence"]
    assert evidence["source"] == "codex_session_log" and evidence["account_ref"] == NATIVE
    assert (evidence["fresh"], evidence["eligible"], evidence["uncertain"]) == (False, False, True)
    assert reservation.admission(evidence, call["need"])["decision"] == "quota_wait"


@pytest.mark.parametrize("snapshot", [
    _snapshot(_account("synthetic-a", 10.0, state="STALE"), _account("synthetic-b", 10.0, state="UNKNOWN")),
    {"status": "unavailable", "accounts": [], "reason": "request_failed"},
    OSError("gateway down"),
])
def test_stale_or_unavailable_gateway_contributes_no_account_evidence(monkeypatch, snapshot):
    h = _host(monkeypatch, snapshot, account_ref="synthetic-a")
    assert not any(k.startswith("magpie-account:") for k in h.host._subscription_quotas())
    _assert_unknown(_prepare(h), "synthetic-a")
    # The unbound native login still falls back to its genuine local observation.
    unbound = _host(monkeypatch, snapshot, local=_local_codex())
    assert _prepare(unbound)["evidence"]["source"] == "codex_session_log"


@pytest.mark.parametrize("order", [1, -1])
def test_duplicate_conflicting_identity_is_never_account_evidence(monkeypatch, order):
    accounts = (_account("synthetic-a", 10.0), _account("synthetic-a", 90.0))[::order]
    h = _host(monkeypatch, _snapshot(*accounts), account_ref="synthetic-a")
    merged = h.host._subscription_quotas()
    assert "magpie-account:synthetic-a" not in merged
    assert merged["codex"]["account_ref"] == "synthetic-a"  # legacy summary is presentation only
    assert trusted_host._account_observations(merged) == []
    _assert_unknown(_prepare(h), "synthetic-a")


def test_unidentified_magpie_account_is_neither_adopted_nor_attributed(monkeypatch):
    h = _host(monkeypatch, _snapshot(_account(None, 10.0)))
    merged = h.host._subscription_quotas()
    assert merged["codex"]["source"] == "magpie" and "account_ref" not in merged["codex"]
    assert not any(k.startswith("magpie-account:") for k in merged)
    _assert_unknown(_prepare(h), NATIVE)


def test_namespace_collisions_do_not_overwrite_provider_or_relabel_identity(monkeypatch):
    accounts = (_account("codex", 50.0), _account("claude-code", 60.0, provider="anthropic"),
                _account("local-cli:codex", 70.0), _account(NATIVE, 5.0))
    h = _host(monkeypatch, _snapshot(*accounts), local=_local_codex(used=45.0))
    merged = h.host._subscription_quotas()
    # Provider keys keep the legacy summary, never an account named after a provider.
    assert merged["codex"]["provenance"] == "EXTERNAL_MAGPIE" and merged["codex"]["account_ref"] == "local-cli:codex"
    assert merged["claude-code"]["account_ref"] == "claude-code"
    assert merged["local-cli:codex"]["source"] == "codex_session_log"
    assert merged["magpie-account:local-cli:codex"]["account_ref"] == "local-cli:codex"
    assert merged["magpie-account:codex"]["windows"][0]["used_percent"] == 50.0
    # A Magpie account whose ref equals the connection id is still not the native login.
    call = _prepare(h)
    assert call["evidence"]["source"] == "codex_session_log"
    assert [w["used_percent"] for w in call["evidence"]["windows"]] == [45.0, 10.0]
    bound = _prepare(_host(monkeypatch, _snapshot(*accounts), account_ref="codex"))
    assert bound["evidence"]["account_ref"] == "codex" and bound["evidence"]["source"] == "magpie"
    assert [w["used_percent"] for w in bound["evidence"]["windows"]] == [50.0, 30.0]


def test_provider_aliases_keep_each_account_under_its_own_identity(monkeypatch):
    accounts = (_account("synthetic-openai", 15.0, provider="openai"),
                _account("synthetic-chatgpt", 25.0, provider="chatgpt"),
                _account("synthetic-claude", 35.0, provider="claude"),
                _account("synthetic-other", 5.0, provider="workbuddy"))
    h = _host(monkeypatch, _snapshot(*accounts), account_ref="synthetic-claude", provider="claude-code")
    merged = h.host._subscription_quotas()
    assert sorted(k for k in merged if k.startswith("magpie-account:")) == [
        "magpie-account:synthetic-chatgpt", "magpie-account:synthetic-claude", "magpie-account:synthetic-openai"]
    assert merged["codex"]["account_ref"] == "synthetic-chatgpt"
    call = _prepare(h)
    assert call["evidence"]["account_ref"] == "synthetic-claude"
    assert [w["used_percent"] for w in call["evidence"]["windows"]] == [35.0, 30.0]


def test_legacy_provider_guard_and_presentation_ignore_reserved_keys(monkeypatch):
    h = _host(monkeypatch, _snapshot(*_two()), local=_local_codex())
    merged = h.host._subscription_quotas()
    legacy = {k: v for k, v in merged.items() if ":" not in k}
    connection = {"executor_provider_id": "codex", "auth_method": "external_cli_session"}
    for need in (None, 0.2):
        assert check(connection, merged, need) == check(connection, legacy, need)
    assert _quota(connection, ("openai", "codex-cli", "codex"), merged) == dict(merged["codex"])
    # The legacy summary still describes A's 95% window; host consumers no longer read it (below).
    assert check(connection, merged, None)["decision"] != "ok"


def test_resume_observations_only_attribute_account_keyed_magpie_evidence(monkeypatch):
    h = _host(monkeypatch, _snapshot(*_two(), _account("synthetic-a", 10.0, provider="claude")), local=_local_codex())
    merged = h.host._subscription_quotas()
    observations = trusted_host._account_observations(merged)
    # A is duplicated across providers (conflicting identity); only B is attributable.
    assert sorted(q["account_ref"] for q in observations) == ["synthetic-b"]
    evidence = reservation.observation("synthetic-a", observations)
    assert evidence["state"] == "UNKNOWN" and not evidence["eligible"]


# Guard, hold, ranking and resume consumers. Account refs are synthetic metadata:
# nothing here proves persistence or which account a native CLI actually uses.

def _accounts_host(monkeypatch, snapshot, accounts, *, local=None, enabled=True):
    """Real ``_quota_check``/``_limit_hit_until``/routing over several native connections."""
    h = _host(monkeypatch, snapshot, local=local, enabled=enabled)
    connections = {conn: {"connection_id": conn, "executor_provider_id": "codex",
                          "auth_method": "external_cli_session", "account_ref": ref}
                   for conn, ref in accounts.items()}
    bindings = [{"binding_id": "bind-" + conn, "connection_id": conn, "executor_id": "codex",
                 "model_id": "gpt-6.1-sol", "enabled": True} for conn in connections]
    h.host._store = SimpleNamespace(list_bindings_public=lambda: bindings,
                                    list_connections_public=lambda: list(connections.values()),
                                    get_connection_public=lambda conn: connections[conn],
                                    list_executors_public=lambda: [],
                                    get_agent_roster_public=lambda: {"roles": {}})
    h.host._task_store = run_store.TaskStore(":memory:")
    monkeypatch.setattr(h.host, "_runnable_bindings", lambda: {b["binding_id"] for b in bindings})
    h.connections, h.bindings, h.base = connections, {b["binding_id"]: b for b in bindings}, int(time.time())
    return h


def _fail(h, binding, *, reset_in=None, age=0, classification="codex_usage_limit"):
    tasks = h.host._task_store
    task = tasks.create_task(title="failure", repository="o/r", executor_kind="codex", binding_ref=binding)
    reset = _iso(h.base + reset_in) if reset_in is not None else ""
    tasks.classify_failure(task.id, classification=classification, failure_reset_at=reset)
    tasks._conn.execute("UPDATE tasks SET failure_at = ?, updated_at = ? WHERE id = ?",
                        (_iso(h.base - age), _iso(h.base - age), task.id))
    tasks._conn.commit()
    return task


def _history(h):
    return [tuple(r) for r in h.host._task_store._conn.execute(
        "SELECT id, status, failure_classification, failure_reset_at, failure_at, updated_at FROM tasks ORDER BY id")]


def _decision(verdict):
    return verdict["decision"], verdict["reason"]


def _route(monkeypatch, h, task=None, **kwargs):
    """Run the ordinary task-aware router and return the candidate input it built."""
    for name, value in (("_routing_refresh_quota_for_signal", lambda: {"state": "UNKNOWN"}),
                        ("_routing_bind_discovered", lambda: None), ("_usage_profiles", lambda: {}),
                        ("_routing_model_metadata", lambda: {}), ("_routing_paid_allowed", lambda *a: False),
                        ("_routing_availability_history", lambda: {}),
                        ("_routing_probe_window_allowed", lambda goal: False),
                        ("_routing_availability", lambda *a, **k: {"state": "AVAILABLE", "reason": "fixture"})):
        monkeypatch.setattr(h.host, name, value)
    seen = []

    def select(candidates, **_):
        seen.append({c["binding_id"]: c for c in candidates})
        return {"binding_ref": candidates[0]["binding_id"]}
    monkeypatch.setattr(model_router, "select_model", select)
    CombinedTrustedHost._resolve_task_model(h.host, task or PlannedTask("T1", "t", "i", difficulty=3), **kwargs)
    return seen[-1]


@pytest.mark.parametrize("order", [1, -1])
def test_foreign_exhausted_summary_neither_switches_nor_extends_a_bound_account(monkeypatch, order):
    # The frozen-8af19684 probe: A=100%, B=20%; B was switched and its 600s hold became A's 3600s.
    accounts = (_account("synthetic-a", 100.0), _account("synthetic-b", 20.0))[::order]
    h = _accounts_host(monkeypatch, _snapshot(*accounts), {"conn-a": "synthetic-a", "conn-b": "synthetic-b"})
    merged = h.host._subscription_quotas()
    assert merged["codex"]["account_ref"] == "synthetic-a"
    # The legacy summary itself is unchanged presentation: it still describes A.
    assert _decision(check(h.connections["conn-b"], merged, None)) == ("switch", "observed_exhausted")
    assert _decision(h.host._quota_check(h.bindings["bind-conn-b"])) == ("ok", "no_signal")
    assert h.host._quota_guarded("coder", "codex", "bind-conn-b", {}) == ("codex", "bind-conn-b")
    assert h.host._quota_guard_entries() == []
    # Matching confirmed exhaustion still refuses through the real guard.
    assert _decision(h.host._quota_check(h.bindings["bind-conn-a"])) == ("switch", "observed_exhausted")
    with pytest.raises(TaskStoreError, match="quota_exhausted:observed_exhausted:no_alternative"):
        h.host._quota_guarded("coder", "codex", "bind-conn-a", {})
    _fail(h, "bind-conn-b", reset_in=600)
    history = _history(h)
    assert h.host._limit_hit_until(h.connections["conn-b"]) == h.base + 600
    verdict = h.host._quota_check(h.bindings["bind-conn-b"])
    assert _decision(verdict) == ("switch", "limit_hit") and verdict["until"] == _iso(h.base + 600)
    assert h.host._limit_hit_until(h.connections["conn-a"]) is None  # B's failure is not A's hold
    assert _history(h) == history and h.calls == []


def test_bound_account_with_its_own_exhaustion_still_refuses_and_holds_to_its_reset(monkeypatch):
    h = _accounts_host(monkeypatch, _snapshot(_account("synthetic-a", 20.0), _account("synthetic-b", 100.0)),
                       {"conn-a": "synthetic-a", "conn-b": "synthetic-b"})
    assert h.host._subscription_quotas()["codex"]["account_ref"] == "synthetic-b"
    assert _decision(h.host._quota_check(h.bindings["bind-conn-b"])) == ("switch", "observed_exhausted")
    with pytest.raises(TaskStoreError, match="quota_exhausted:observed_exhausted:no_alternative"):
        h.host._quota_guarded("coder", "codex", "bind-conn-b", {})
    assert _decision(h.host._quota_check(h.bindings["bind-conn-a"])) == ("ok", "no_signal")
    _fail(h, "bind-conn-b", reset_in=600)
    # B's own exhausted five-hour window extends B's stated hold, as before.
    assert h.host._limit_hit_until(h.connections["conn-b"]) == pytest.approx(h.base + 3600, abs=5)
    assert h.host._limit_hit_until(h.connections["conn-a"]) is None


def test_same_account_aliases_share_holds_and_reservation_identity(monkeypatch):
    h = _accounts_host(monkeypatch, _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 20.0)),
                       {"conn-b1": "synthetic-b", "conn-b2": "synthetic-b", "conn-a": "synthetic-a"})
    for binding in ("bind-conn-b1", "bind-conn-b2"):
        assert _decision(h.host._quota_check(h.bindings[binding])) == ("ok", "no_signal")
    _fail(h, "bind-conn-b1", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-b1"]) == h.base + 600
    assert h.host._limit_hit_until(h.connections["conn-b2"]) == h.base + 600
    assert h.host._limit_hit_until(h.connections["conn-a"]) is None
    for binding in ("bind-conn-b1", "bind-conn-b2"):
        h.host._prepare_task_quota(SimpleNamespace(id="t-" + binding, binding_ref=binding, executor_kind="codex",
                                                   kind="code", difficulty=3))
    assert [(c["binding_ref"], c["account_ref"], c["evidence"]["account_ref"]) for c in h.calls] == [
        ("bind-conn-b1", "synthetic-b", "synthetic-b"), ("bind-conn-b2", "synthetic-b", "synthetic-b")]
    assert [[w["used_percent"] for w in c["evidence"]["windows"]] for c in h.calls] == [[20.0, 30.0]] * 2


def _malformed(ref):
    account = _account(ref, 100.0)
    account["windows"] = [{"name": "5 hours", "used_percent": "100", "resets_at": "not-a-time"}]
    return account


@pytest.mark.parametrize("snapshot", [
    {"status": "unavailable", "accounts": [], "reason": "request_failed"},
    OSError("gateway down"),
    _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 100.0, state="STALE")),
    _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 100.0, state="UNKNOWN")),
    _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 10.0), _account("synthetic-b", 100.0)),
    _snapshot(_account("synthetic-a", 100.0), _malformed("synthetic-b")),
], ids=["unavailable", "fetch_error", "stale", "unknown", "conflicting", "malformed"])
def test_missing_or_untrusted_own_evidence_stays_unknown_and_never_borrows_a_summary(monkeypatch, snapshot):
    h = _accounts_host(monkeypatch, snapshot, {"conn-b": "synthetic-b"})
    assert "magpie-account:synthetic-b" not in h.host._subscription_quotas()
    assert _decision(h.host._quota_check(h.bindings["bind-conn-b"])) == ("ok", "quota_unknown")
    _fail(h, "bind-conn-b", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-b"]) == h.base + 600
    # Unknown account evidence never produces a refusal or a fresh admission.
    h.host._prepare_task_quota(SimpleNamespace(id="t", binding_ref="bind-conn-b", executor_kind="codex",
                                               kind="code", difficulty=3))
    _assert_unknown(h.calls[-1], "synthetic-b")


def test_quota_source_failure_is_reported_not_silenced(monkeypatch):
    h = _accounts_host(monkeypatch, _snapshot(_account("synthetic-b", 20.0)), {"conn-b": "synthetic-b"})

    def unavailable():
        raise OSError("fixture quota source down")
    monkeypatch.setattr(h.host, "_subscription_quotas", unavailable)
    assert h.host._quota_check(h.bindings["bind-conn-b"]) == {"decision": "error", "reason": "quota_check_failed"}
    _fail(h, "bind-conn-b", reset_in=600)
    with pytest.raises(OSError, match="fixture quota source down"):
        h.host._limit_hit_until(h.connections["conn-b"])


def test_unbound_native_login_uses_only_its_genuine_local_cli_source(monkeypatch):
    # A Magpie account whose ref equals the connection id is still not the machine's login.
    snapshot = _snapshot(_account("synthetic-a", 100.0), _account("conn-c", 100.0))
    h = _accounts_host(monkeypatch, snapshot, {"conn-c": None}, local=_local_codex(used=40.0))
    assert h.host._subscription_quotas()["codex"]["source"] == "magpie"
    assert _decision(h.host._quota_check(h.bindings["bind-conn-c"])) == ("ok", "no_signal")
    _fail(h, "bind-conn-c", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-c"]) == h.base + 600
    # The genuine local observation of exhaustion still refuses and extends the hold.
    exhausted = _accounts_host(monkeypatch, _snapshot(_account("synthetic-a", 20.0)), {"conn-c": None},
                               local=_local_codex(used=100.0))
    assert _decision(exhausted.host._quota_check(exhausted.bindings["bind-conn-c"])) == ("switch", "observed_exhausted")
    _fail(exhausted, "bind-conn-c", reset_in=600)
    assert exhausted.host._limit_hit_until(exhausted.connections["conn-c"]) == pytest.approx(exhausted.base + 3600, abs=5)


def _resets(account, *seconds):
    # Move each window's reset so a borrowed foreign reset would be distinguishable.
    for window, offset in zip(account["windows"], seconds):
        window["resets_at"] = _iso(time.time() + offset)
    return account


@pytest.mark.parametrize("enabled", [True, False])
def test_unbound_native_login_without_local_source_ignores_foreign_magpie(monkeypatch, enabled):
    snapshot = _snapshot(_resets(_account("synthetic-a", 100.0), 1800), _resets(_account("conn-c", 100.0), 2400))
    h = _accounts_host(monkeypatch, snapshot, {"conn-c": None}, enabled=enabled)
    assert _decision(h.host._quota_check(h.bindings["bind-conn-c"])) == ("ok", "quota_unknown")
    _fail(h, "bind-conn-c", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-c"]) == h.base + 600
    # Without a stated reset the fixed hold applies, not a foreign window reset.
    fallback = _accounts_host(monkeypatch, snapshot, {"conn-c": None}, enabled=enabled)
    _fail(fallback, "bind-conn-c")
    assert fallback.host._limit_hit_until(fallback.connections["conn-c"]) == fallback.base + 3600


def test_expired_hold_and_seven_day_bound_are_unchanged_by_account_scoping(monkeypatch):
    snapshot = _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 100.0, weekly=100.0))
    h = _accounts_host(monkeypatch, snapshot, {"conn-b": "synthetic-b"})
    _fail(h, "bind-conn-b", reset_in=-1, age=7200)
    _fail(h, "bind-conn-b", reset_in=6 * 86400, age=2 * 86400)
    history = _history(h)
    # Even B's own exhausted windows cannot revive an expired or over-bound stated hold.
    assert h.host._limit_hit_until(h.connections["conn-b"]) is None
    # A's exhausted weekly window resets after B's bounded stated reset; it must not extend B.
    foreign = _resets(_account("synthetic-a", 100.0, weekly=100.0), 3600, 6 * 86400)
    exact = _accounts_host(monkeypatch, _snapshot(foreign, _account("synthetic-b", 20.0)), {"conn-b": "synthetic-b"})
    _fail(exact, "bind-conn-b", reset_in=5 * 86400, age=2 * 86400)
    assert exact.host._limit_hit_until(exact.connections["conn-b"]) == exact.base + 5 * 86400
    assert _history(h) == history and h.calls == [] and exact.calls == []


def test_ordinary_routing_candidates_take_headroom_and_guard_from_their_own_account(monkeypatch):
    snapshot = _snapshot(_account("synthetic-a", 100.0, weekly=50.0), _account("synthetic-b", 20.0),
                         _account("conn-c", 100.0))
    h = _accounts_host(monkeypatch, snapshot, {"conn-a": "synthetic-a", "conn-b": "synthetic-b", "conn-c": None},
                       local=_local_codex(used=40.0))
    candidates = _route(monkeypatch, h)
    view = {b: (_decision(c["quota"]), c["short_headroom"], c["weekly_headroom"], c["quota_headroom"])
            for b, c in candidates.items()}
    assert view == {
        "bind-conn-a": (("switch", "observed_exhausted"), 0.0, 0.5, 0.0),
        "bind-conn-b": (("ok", "no_signal"), pytest.approx(0.8), pytest.approx(0.7), pytest.approx(0.7)),
        "bind-conn-c": (("ok", "no_signal"), pytest.approx(0.6), pytest.approx(0.9), pytest.approx(0.6))}
    assert candidates["bind-conn-b"]["short_resets_at"] == pytest.approx(h.base + 3600, abs=5)
    # Missing own evidence is unknown headroom, never another account's.
    bare = _accounts_host(monkeypatch, snapshot, {"conn-c": None, "conn-d": "synthetic-d"})
    for candidate in _route(monkeypatch, bare).values():
        assert _decision(candidate["quota"]) == ("ok", "quota_unknown")
        assert (candidate["short_headroom"], candidate["weekly_headroom"], candidate["quota_headroom"]) == (None,) * 3


def test_quota_wait_resume_forecasts_each_connection_from_its_own_account(monkeypatch):
    snapshot = _snapshot(_account("synthetic-a", 100.0), _account("synthetic-b", 20.0), _account("conn-c", 100.0))
    h = _accounts_host(monkeypatch, snapshot, {"conn-a": "synthetic-a", "conn-b": "synthetic-b", "conn-c": None},
                       local=_local_codex(used=40.0))
    link = {"goal_id": "g", "plan_task_id": "T1", "goal_revision": 1}
    h.host._task_store = SimpleNamespace(_conn=SimpleNamespace(
        execute=lambda sql, params: SimpleNamespace(fetchone=lambda: link)))
    h.host._control_store.get_goal = lambda goal_id: SimpleNamespace(
        id="g", revision=1, status="RUNNING", orchestration_mode="agent_team", binding_ref="",
        tasks=[{"id": "T1", "title": "Finish", "instruction": "Finish", "difficulty": 3}])
    routes = []
    monkeypatch.setattr(h.host, "_resolve_task_model", lambda planned, **kw: routes.append(kw) or {
        "binding_ref": "bind-conn-c", "executor_kind": "codex", "underpowered": False})
    h.host._prepare_task_quota(SimpleNamespace(id="t", status="QUOTA_WAIT", binding_ref="bind-conn-c",
                                               executor_kind="codex", kind="code", difficulty=3))
    [route] = routes
    evidence = route["quota_evidence"]
    assert route["forecast"] is True and set(evidence) == {"synthetic-a", "synthetic-b", "conn-c"}
    assert {a: (e["account_ref"], e["source"], [w["used_percent"] for w in e["windows"]])
            for a, e in evidence.items()} == {
        "synthetic-a": ("synthetic-a", "magpie", [100.0, 30.0]),
        "synthetic-b": ("synthetic-b", "magpie", [20.0, 30.0]),
        "conn-c": ("conn-c", "codex_session_log", [40.0, 10.0])}
    [call] = h.calls
    assert (call["account_ref"], call["evidence"]["source"], call["resume_route"]) == ("conn-c", "codex_session_log", None)

    # The forecast router consumes that evidence without any further quota read.
    def forbidden(*args, **kwargs):
        pytest.fail("forecast read quota state")
    monkeypatch.setattr(h.host, "_subscription_quotas", forbidden)
    monkeypatch.setattr(h.host, "_quota_check", forbidden)
    candidates = _route(monkeypatch, h, forecast=True, quota_evidence=evidence)
    assert {b: c["short_headroom"] for b, c in candidates.items()} == {
        "bind-conn-a": 0.0, "bind-conn-b": pytest.approx(0.8), "bind-conn-c": pytest.approx(0.6)}
    assert all(c["quota"] is None for c in candidates.values())


# Freshness: capacity consumers use the admission contract (600s), not the
# Magpie parser's wider FRESH bound (900s). Clocks are controlled.

def _clock(monkeypatch):
    clock = [float(int(time.time()))]
    monkeypatch.setattr(time, "time", lambda: clock[0])
    return clock


def _magpie_reading(user, used, *, now, age, reset_in=3600):
    """One account read ``age`` seconds ago, through the real Magpie parser."""
    raw = {"provider": "codex", "kind": "subscription", "user": user, "readAt": _iso(now - age),
           "windows": [{"name": "5 hours", "used": used, "remaining": 100 - used, "resetsAt": _iso(now + reset_in)},
                       {"name": "7 days", "used": 30, "remaining": 70, "resetsAt": _iso(now + 86400)}]}
    [account] = magpie.parse_quotas({"object": "list", "data": [raw]}, datetime.fromtimestamp(now, timezone.utc))
    return account


def _headroom(candidate):
    return (candidate["short_headroom"], candidate["weekly_headroom"], candidate["quota_headroom"],
            candidate["short_resets_at"])


def test_parser_fresh_reading_past_admission_freshness_is_unknown_capacity(monkeypatch):
    # The external pair: B=100% read 700s ago with a future reset; A is a fresh 20% reading.
    now = _clock(monkeypatch)[0]
    a = _magpie_reading("synthetic-a", 20.0, now=now, age=60)
    b = _magpie_reading("synthetic-b", 100.0, now=now, age=700)
    assert (a["state"], b["state"]) == ("FRESH", "FRESH")  # the parser permits up to 900s
    h = _accounts_host(monkeypatch, _snapshot(a, b), {"conn-a": a["account_ref"], "conn-b": b["account_ref"]})
    ref = b["account_ref"]
    # The diagnostic observation keeps B's windows and its own timestamp; it is not fresh.
    candidates = h.host._account_quota_candidates(h.connections["conn-b"], h.host._subscription_quotas())
    diagnostic = reservation.observation(ref, candidates, clock=time.time)
    assert (diagnostic["fresh"], diagnostic["eligible"], diagnostic["uncertain"]) == (False, False, True)
    assert [w["used_percent"] for w in diagnostic["windows"]] == [100.0, 30]
    usable = h.host._account_quota(h.connections["conn-b"])
    assert usable["windows"] == [] and usable["observed_at"] == diagnostic["observed_at"] == _iso(now - 700)
    assert (usable["fresh"], usable["eligible"], usable["eligibility_reason"]) == (False, False, "refresh_required")
    # Guard: unknown capacity, not confirmed exhaustion and not proof of eligibility.
    assert _decision(h.host._quota_check(h.bindings["bind-conn-b"])) == ("ok", "quota_unknown")
    assert h.host._quota_guarded("coder", "codex", "bind-conn-b", {}) == ("codex", "bind-conn-b")
    assert h.host._quota_guard_entries() == []
    # Positive control: A's fresh reading remains usable capacity.
    assert _decision(h.host._quota_check(h.bindings["bind-conn-a"])) == ("ok", "no_signal")
    routed = _route(monkeypatch, h)
    assert _headroom(routed["bind-conn-b"]) == (None,) * 4
    assert _headroom(routed["bind-conn-a"]) == (pytest.approx(0.8), pytest.approx(0.7), pytest.approx(0.7), now + 3600)
    # Hold: the stated 600s stays 600s; B's stale exhausted window never extends it.
    _fail(h, "bind-conn-b", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-b"]) == now + 600
    verdict = h.host._quota_check(h.bindings["bind-conn-b"])
    assert _decision(verdict) == ("switch", "limit_hit") and verdict["until"] == _iso(now + 600)
    assert h.host._limit_hit_until(h.connections["conn-a"]) is None
    # Admission preparation still reads the original diagnostic and stays fail-closed.
    h.host._prepare_task_quota(SimpleNamespace(id="t", binding_ref="bind-conn-b", executor_kind="codex",
                                               kind="code", difficulty=3))
    [call] = h.calls
    evidence = call["evidence"]
    assert (call["account_ref"], evidence["account_ref"], evidence["source"]) == (ref, ref, "magpie")
    assert [w["used_percent"] for w in evidence["windows"]] == [100.0, 30]
    assert (evidence["fresh"], evidence["eligible"], evidence["uncertain"]) == (False, False, True)
    assert evidence["eligibility_reason"] == "refresh_required"
    assert reservation.admission(evidence, call["need"])["decision"] == "quota_wait"


def test_admission_freshness_boundary_governs_guard_hold_and_headroom(monkeypatch):
    clock = _clock(monkeypatch)
    now = clock[0]
    a = _magpie_reading("synthetic-a", 20.0, now=now, age=0)
    b = _magpie_reading("synthetic-b", 100.0, now=now, age=600, reset_in=1800)
    h = _accounts_host(monkeypatch, _snapshot(a, b), {"conn-a": a["account_ref"], "conn-b": b["account_ref"]})
    merged = h.host._subscription_quotas()
    # Forecast evidence as persisted at ``now``; it ages with the clock like live evidence.
    evidence = {ref: reservation.observation(ref, trusted_host._account_observations(merged, ref), clock=time.time)
                for ref in (a["account_ref"], b["account_ref"])}
    assert all(e["fresh"] for e in evidence.values())
    _fail(h, "bind-conn-b", reset_in=600)
    # Exactly 600s old: B's own fresh exhausted window refuses and extends its stated hold.
    assert h.host._limit_hit_until(h.connections["conn-b"]) == now + 1800
    blocked = _route(monkeypatch, h)["bind-conn-b"]
    assert _decision(blocked["quota"]) == ("switch", "limit_hit") and blocked["short_headroom"] == 0.0
    forecast = _route(monkeypatch, h, forecast=True, quota_evidence=evidence)
    assert _headroom(forecast["bind-conn-b"]) == (0.0, pytest.approx(0.7), 0.0, now + 1800)
    # 601s old: the same reading no longer counts as capacity anywhere.
    clock[0] = now + 1
    assert h.host._limit_hit_until(h.connections["conn-b"]) == now + 600
    for candidates in (_route(monkeypatch, h), _route(monkeypatch, h, forecast=True, quota_evidence=evidence)):
        assert _headroom(candidates["bind-conn-b"]) == (None,) * 4
        assert candidates["bind-conn-a"]["short_headroom"] == pytest.approx(0.8)  # fresh control
    # Without a failure the guard sees unknown capacity after the boundary, exhaustion at it.
    unfailed = _accounts_host(monkeypatch, _snapshot(a, b), {"conn-b": b["account_ref"]})
    assert _decision(unfailed.host._quota_check(unfailed.bindings["bind-conn-b"])) == ("ok", "quota_unknown")
    clock[0] = now
    assert _decision(unfailed.host._quota_check(unfailed.bindings["bind-conn-b"])) == ("switch", "observed_exhausted")
    with pytest.raises(TaskStoreError, match="quota_exhausted:observed_exhausted:no_alternative"):
        unfailed.host._quota_guarded("coder", "codex", "bind-conn-b", {})


@pytest.mark.parametrize("observed", ["stale", "future", "undated"])
def test_untrusted_local_cli_exhaustion_neither_refuses_nor_extends_a_hold(monkeypatch, observed):
    now = _clock(monkeypatch)[0]
    local = _local_codex(used=100.0, age={"stale": 700, "future": -120, "undated": 0}[observed])
    if observed == "undated":
        local["observed_at"] = None
    h = _accounts_host(monkeypatch, _snapshot(), {"conn-c": None}, local=local)
    assert _decision(h.host._quota_check(h.bindings["bind-conn-c"])) == ("ok", "quota_unknown")
    assert _headroom(_route(monkeypatch, h)["bind-conn-c"]) == (None,) * 4
    _fail(h, "bind-conn-c", reset_in=600)
    assert h.host._limit_hit_until(h.connections["conn-c"]) == now + 600
    # Control: the same reading taken now is fresh confirmed exhaustion with its own reset hold.
    fresh = _accounts_host(monkeypatch, _snapshot(), {"conn-c": None}, local=_local_codex(used=100.0))
    assert _decision(fresh.host._quota_check(fresh.bindings["bind-conn-c"])) == ("switch", "observed_exhausted")
    assert _headroom(_route(monkeypatch, fresh)["bind-conn-c"])[0] == 0.0
    _fail(fresh, "bind-conn-c", reset_in=600)
    assert fresh.host._limit_hit_until(fresh.connections["conn-c"]) == now + 3600
