"""No-auth, provider-free tests for daily check-in grant lifecycle."""
from datetime import datetime, timedelta, timezone

import pytest
from reverse_agent.model_access.reward_claims import (
    check_claim_eligibility, check_reward_receipt,
)

DAY = datetime(2026, 10, 16, 2, tzinfo=timezone.utc)


def assess(**overrides):
    opts = dict(program="traework", opaque_account_ref="internal_a019",
                now=DAY, provider_timezone="Asia/Shanghai",
                last_verified_at=None, reset_policy="PROVIDER_DAY",
                claim_method="FIRST_PARTY_UI", automation_allowed=True,
                user_opted_in=True, active_campaign=True)
    opts.update(overrides)
    return check_claim_eligibility(**opts)


def test_valid_allowed_app_checkin_is_only_eligible_not_claimed():
    r = assess()
    assert r["state"] == "ELIGIBLE"
    assert not r["claim_performed"]
    assert r["needs_actual_reward_receipt"]


def test_provider_day_prevents_claiming_twice():
    assert assess(last_verified_at=DAY-timedelta(hours=1))["state"] == "ALREADY_CLAIMED"


def test_claim_before_and_after_provider_midnight():
    yesterday = datetime(2026,10,15,15,59,tzinfo=timezone.utc)
    now = datetime(2026,10,15,16,1,tzinfo=timezone.utc)
    assert assess(now=now,last_verified_at=yesterday)["state"] == "ELIGIBLE"


def test_account_period_idempotency():
    a = assess()
    b = assess()
    c = assess(opaque_account_ref="another_acc_2")
    assert a["idempotency_digest"] == b["idempotency_digest"]
    assert a["idempotency_digest"] != c["idempotency_digest"]


def test_unsupported_third_party_unpublished_endpoint_is_not_auto_eligible():
    assert assess(claim_method="UNDOCUMENTED_API")["state"] == "HUMAN_REQUIRED"


def test_unconfirmed_provider_permission_requires_human():
    assert assess(automation_allowed=None)["state"] == "HUMAN_REQUIRED"


def test_2fa_and_captcha_require_human():
    assert assess(requires_human_challenge=True)["state"] == "HUMAN_REQUIRED"


def test_missing_optin_requires_human():
    assert assess(user_opted_in=False)["state"] == "HUMAN_REQUIRED"


def test_inactive_or_unknown_campaign_never_mints_credits():
    assert assess(active_campaign=None)["state"] == "UNKNOWN"
    assert assess(active_campaign=False)["state"] == "UNKNOWN"


def test_rolling_window_respects_24_hours():
    last = DAY - timedelta(hours=23)
    assert assess(reset_policy="ROLLING_24H",last_verified_at=last)["state"] == "ALREADY_CLAIMED"
    assert assess(reset_policy="ROLLING_24H",last_verified_at=DAY-timedelta(hours=25))["state"] == "ELIGIBLE"


def test_daylight_saving_timezone_supported():
    ny = datetime(2026,11,1,7,tzinfo=timezone.utc)
    last = datetime(2026,10,31,7,tzinfo=timezone.utc)
    assert assess(now=ny,last_verified_at=last,provider_timezone="America/New_York")["state"] == "ELIGIBLE"


@pytest.mark.parametrize("changes", [
    {"program": ""}, {"opaque_account_ref": "email@example.com"},
    {"now": DAY.replace(tzinfo=None)}, {"provider_timezone": "Unknown/Unknown"},
    {"reset_policy": "UNKNOWN"}, {"last_verified_at": DAY+timedelta(days=1)},
])
def test_invalid_fields_fail_closed(changes):
    assert assess(**changes)["state"] == "UNKNOWN"


def test_clicked_not_equal_reward_granted():
    assert check_reward_receipt(claim_attempted=True,provider_receipt_verified=False,credited_units=200)["state"] == "CLAIMED_UNVERIFIED"


def test_success_provenance_requires_positive_integer_credit():
    assert check_reward_receipt(claim_attempted=True,provider_receipt_verified=True,credited_units=150)["state"] == "VERIFIED_GRANTED"
    assert check_reward_receipt(claim_attempted=True,provider_receipt_verified=True,credited_units=0)["state"] == "CLAIMED_UNVERIFIED"
    assert check_reward_receipt(claim_attempted=True,provider_receipt_verified=True,credited_units=True)["state"] == "CLAIMED_UNVERIFIED"


def test_secret_logging_rejected_even_if_receipt_successful():
    assert check_reward_receipt(claim_attempted=True,provider_receipt_verified=True,credited_units=200,credential_or_session_logged=True)["state"] == "REJECTED"