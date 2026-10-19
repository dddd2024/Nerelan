"""Provider-free recognition tests: never claim rewards or account quota."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from reverse_agent.model_access.reward_discovery import (
    RewardAccount, RewardProgram, discover_reward_needs,
)

NOW = datetime(2026, 10, 19, 12, tzinfo=timezone.utc)
ACCOUNT = RewardAccount("service", "ownerref_01123", eligible=True)
KEY = ("service", "ownerref_01123", "daily")


def p(**override):
    props = {
        "provider_id": "service", "program_id": "daily",
        "kind": "DAILY_CHECK_IN", "source_kind": "OFFICIAL_API",
        "evidence_url": "https://service.example/rewards",
        "evidence_verified": True, "verified_at": NOW-timedelta(days=1),
        "expires_at": NOW+timedelta(days=2), "active": True,
        "provider_timezone": "Asia/Shanghai",
        "claim_method": "OFFICIAL_API", "automation_allowed": True,
    }
    props.update(override)
    return RewardProgram(**props)


def result(program=None, account=ACCOUNT, **kwargs):
    return discover_reward_needs([account], [program or p()], now=NOW, **kwargs)[0]


def test_no_catalog_is_unknown_not_no_checkin():
    r = discover_reward_needs([ACCOUNT], [], now=NOW)[0]
    assert r["state"] == "UNKNOWN" and r["action"] == "DISCOVER_ONLY"


def test_discovered_daily_requires_optin_before_auto_eligibility():
    assert result()["state"] == "OPT_IN_REQUIRED"
    r = result(opted_in={KEY})
    assert r["state"] == "AUTO_ELIGIBLE"
    assert r["claim_performed"] is False


def test_actual_provider_receipt_prevents_duplicate_claim():
    r = result(opted_in={KEY}, verified_claims={KEY: NOW-timedelta(minutes=10)})
    assert r["state"] == "ALREADY_CLAIMED" and r["action"] == "NONE"


@pytest.mark.parametrize("kind", ["PASSIVE_QUOTA_RESET", "NO_REWARD_PROGRAM"])
def test_passive_reset_and_no_reward_are_not_signin(kind):
    assert result(p(kind=kind))["state"] == "NOT_REQUIRED"


def test_banked_grant_must_be_redeemed_manually():
    r = result(p(kind="BANKED_MANUAL_REDEEM"), opted_in={KEY})
    assert r["state"] == "MANUAL_REQUIRED"
    assert r["action"] == "MANUAL"


def test_one_time_campaign_unknown_until_supported_period():
    r = result(p(kind="CAMPAIGN_CLAIM", reset_policy="ONE_TIME"), opted_in={KEY})
    assert r["state"] == "UNKNOWN" and r["action"] == "DISCOVER_ONLY"


@pytest.mark.parametrize("changes", [
    {"requires_human_challenge": True},
    {"automation_allowed": None},
    {"claim_method": "UNDOCUMENTED_API"},
])
def test_provider_does_not_allow_automated_claim(changes):
    for optin in ((), {KEY}):
        r = result(p(**changes), opted_in=optin)
        assert r["state"] == "MANUAL_REQUIRED"


def test_inactive_unknown_and_not_eligible():
    assert result(p(active=False))["state"] == "NOT_REQUIRED"
    assert result(p(active=None))["state"] == "UNKNOWN"
    assert result(account=replace(ACCOUNT, eligible=False))["state"] == "NOT_ELIGIBLE"
    assert result(account=replace(ACCOUNT, eligible=None))["state"] == "UNKNOWN"


@pytest.mark.parametrize("changes", [
    {"evidence_verified": False}, {"source_kind": "PUBLIC_MIRROR"},
    {"evidence_url": "http://service.example/rewards"},
    {"evidence_url": "https://john:secret@service.example/rewards"},
    {"verified_at": NOW-timedelta(days=31)},
    {"verified_at": NOW+timedelta(hours=1)},
    {"expires_at": NOW-timedelta(minutes=1)},
])
def test_missing_or_stale_original_evidence_does_not_claim(changes):
    r = result(p(**changes), opted_in={KEY})
    assert r["state"] == "UNKNOWN", changes
    assert r["claim_performed"] is False


def test_contradictory_program_descriptors_fail_closed():
    r = discover_reward_needs([ACCOUNT], [p(), p(kind="NO_REWARD_PROGRAM")], now=NOW)
    assert len(r) == 1 and r[0]["state"] == "UNKNOWN"


def test_several_accounts_are_separate_and_duplicates_deduped():
    other = replace(ACCOUNT, opaque_account_ref="ownerref_09999")
    r = discover_reward_needs(
        [ACCOUNT, other, ACCOUNT],
        [p(), p(program_id="passive", kind="PASSIVE_QUOTA_RESET")],
        now=NOW, opted_in={KEY})
    assert len(r) == 4
    assert [z["state"] for z in r if z["program_id"] == "daily"] == [
        "AUTO_ELIGIBLE", "OPT_IN_REQUIRED"]


def test_invalid_identity_is_not_echoed():
    bad = replace(ACCOUNT, opaque_account_ref="myemail@example.org")
    assert discover_reward_needs([bad], [p()], now=NOW) == []


def test_malformed_unhashable_program_id_is_ignored_not_a_crash():
    bad = p(program_id=["unhashable"])
    r = discover_reward_needs([ACCOUNT], [bad], now=NOW)
    assert len(r) == 1 and r[0]["state"] == "UNKNOWN"


def test_explicit_no_claim_or_credit_grant_fields():
    r = result(opted_in={KEY})
    assert "api_key" not in r and "credited_units" not in r
    assert r["claim_performed"] is False
