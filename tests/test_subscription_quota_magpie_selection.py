"""Deterministic Magpie account selection for provider quota evidence (#1260)."""
from __future__ import annotations

import json

from reverse_agent.model_access.subscription_quota import magpie_quota_windows

NOW = 1792407600.0  # 2026-10-19T11:00:00Z
RESET = "2026-10-19T16:00:00Z"
PAST_RESET = "2026-10-19T10:00:00Z"


def _window(used, *, name="five_hour", reset=RESET):
    return {"name": name, "used_percent": used, "remaining_percent": 100 - used,
            "resets_at": reset, "unlimited": False}


def _account(ref, provider, windows, *, state="FRESH", observed_at="2026-10-19T11:00:00Z"):
    return {"provider": provider, "kind": "subscription", "plan": "Pro", "state": state,
            "reason": None if state == "FRESH" else "stale_reading",
            "account_ref": ref, "observed_at": observed_at, "windows": list(windows)}


def _snapshot(*accounts):
    return {"status": "available", "version": "0.1.1250", "models": [], "accounts": list(accounts)}


def test_reversed_account_order_selects_the_same_conservative_account():
    constrained = _account("aaa111", "codex", [_window(95)])
    roomy = _account("bbb222", "codex", [_window(20)])
    forward = magpie_quota_windows(_snapshot(constrained, roomy), now=NOW)
    reverse = magpie_quota_windows(_snapshot(roomy, constrained), now=NOW)
    assert forward == reverse
    assert forward["codex"]["account_ref"] == "aaa111"
    assert [window["used_percent"] for window in forward["codex"]["windows"]] == [95]


def test_provider_aliases_share_one_selection_across_account_order():
    constrained = _account("aaa111", "openai", [_window(90)])
    roomy = _account("bbb222", "codex", [_window(10)])
    forward = magpie_quota_windows(_snapshot(constrained, roomy), now=NOW)
    reverse = magpie_quota_windows(_snapshot(roomy, constrained), now=NOW)
    assert forward == reverse
    assert forward["codex"]["account_ref"] == "aaa111"


def test_multiple_windows_stay_with_the_one_chosen_account():
    constrained = _account("aaa111", "codex", [_window(20), _window(96, name="weekly")])
    roomy = _account("bbb222", "codex", [_window(40), _window(60, name="weekly")])
    quotas = magpie_quota_windows(_snapshot(roomy, constrained), now=NOW)
    assert quotas["codex"]["account_ref"] == "aaa111"
    assert [(window["window"], window["used_percent"]) for window in quotas["codex"]["windows"]] == [
        ("five_hour", 20), ("weekly", 96)]


def test_equal_headroom_ties_are_ordered_by_sanitized_account_ref():
    first = _account("aaa111", "codex", [_window(75)])
    second = _account("bbb222", "codex", [_window(75)])
    forward = magpie_quota_windows(_snapshot(first, second), now=NOW)
    reverse = magpie_quota_windows(_snapshot(second, first), now=NOW)
    assert forward == reverse
    assert forward["codex"]["account_ref"] == "aaa111"


def test_stale_unknown_invalid_and_expired_accounts_cannot_win():
    stale = _account("stale1", "codex", [_window(100)], state="STALE")
    unknown_provider = _account("other1", "workbuddy", [_window(100)])
    invalid = _account("badwin", "codex", [{"name": "five_hour", "used_percent": 150,
                                            "resets_at": RESET}])
    expired = _account("reset1", "codex", [_window(100, reset=PAST_RESET)])
    usable = _account("good12", "codex", [_window(35)])
    quotas = magpie_quota_windows(
        _snapshot(stale, unknown_provider, invalid, expired, usable), now=NOW)
    assert quotas["codex"]["account_ref"] == "good12"
    assert [window["used_percent"] for window in quotas["codex"]["windows"]] == [35]
    assert "workbuddy" not in quotas


def test_malformed_stated_reset_invalidates_only_that_window():
    account = _account("good12", "codex", [
        {"name": "five_hour", "used_percent": 99, "resets_at": "not-a-time"},
        _window(25),
    ])
    quotas = magpie_quota_windows(_snapshot(account), now=NOW)
    assert quotas["codex"]["account_ref"] == "good12"
    assert [window["used_percent"] for window in quotas["codex"]["windows"]] == [25]


def test_no_usable_fresh_evidence_keeps_the_local_fallback():
    stale = _account("stale1", "codex", [_window(100)], state="STALE")
    expired = _account("reset1", "claude", [_window(100, reset=PAST_RESET)])
    invalid = _account("badwin", "claude", [{"used_percent": "full"}])
    unknown_provider = _account("other1", "workbuddy", [_window(100)])
    assert magpie_quota_windows(
        _snapshot(stale, expired, invalid, unknown_provider), now=NOW) == {}
    assert magpie_quota_windows({"status": "unavailable", "accounts": [stale]}, now=NOW) == {}


def test_selected_evidence_records_only_the_existing_sanitized_account_ref():
    account = _account("abc123def456", "anthropic", [_window(60)])
    account["user"] = "person@example.test"
    quotas = magpie_quota_windows(_snapshot(account), now=NOW)
    evidence = quotas["claude-code"]
    assert evidence["account_ref"] == "abc123def456"
    assert evidence["provenance"] == "EXTERNAL_MAGPIE"
    assert "person@example.test" not in json.dumps(evidence)


def test_unlimited_windows_never_constrain_selection_or_admission():
    unlimited = {**_window(100, name="weekly"), "unlimited": True}
    limited = _account("aaa111", "codex", [_window(30), unlimited])
    quotas = magpie_quota_windows(_snapshot(limited), now=NOW)
    assert [window["window"] for window in quotas["codex"]["windows"]] == ["five_hour"]
    only_unlimited = _account("bbb222", "claude-code", [unlimited])
    assert "claude-code" not in magpie_quota_windows(_snapshot(only_unlimited), now=NOW)
