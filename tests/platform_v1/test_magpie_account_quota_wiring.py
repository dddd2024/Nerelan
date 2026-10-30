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
from reverse_agent.platform_v1 import quota_reservation as reservation
from reverse_agent.platform_v1 import trusted_host, usage_ledger
from reverse_agent.platform_v1.quota_guard import check
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
    assert check(connection, merged, None)["decision"] != "ok"  # A's 95% window still drives the guard


def test_resume_observations_only_attribute_account_keyed_magpie_evidence(monkeypatch):
    h = _host(monkeypatch, _snapshot(*_two(), _account("synthetic-a", 10.0, provider="claude")), local=_local_codex())
    merged = h.host._subscription_quotas()
    observations = trusted_host._account_observations(merged)
    # A is duplicated across providers (conflicting identity); only B is attributable.
    assert sorted(q["account_ref"] for q in observations) == ["synthetic-b"]
    evidence = reservation.observation("synthetic-a", observations)
    assert evidence["state"] == "UNKNOWN" and not evidence["eligible"]
