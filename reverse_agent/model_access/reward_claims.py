"""Provider-free check-in entitlement eligibility and receipt state.

This module never logs in, reads credentials, calls an undocumented endpoint,
or actually claims a daily reward. The service must explicitly allow the
selected automation surface, and a user must independently opt in.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from zoneinfo import ZoneInfo
from typing import Any


_ALLOWED_METHODS = frozenset({"OFFICIAL_API", "FIRST_PARTY_UI"})


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone_aware_required")
    return value.astimezone(timezone.utc)


def check_claim_eligibility(
    *,
    program: str,
    opaque_account_ref: str,
    now: datetime,
    provider_timezone: str,
    last_verified_at: datetime | None = None,
    reset_policy: str = "PROVIDER_DAY",
    claim_method: str | None = None,
    automation_allowed: bool | None = None,
    user_opted_in: bool = False,
    requires_human_challenge: bool = False,
    active_campaign: bool | None = None,
) -> dict[str, Any]:
    """Assess one legitimate claim; UNKNOWN is safer than a fake reward.

    The returned idempotency digest is *not* an authentication token.
    Callers must still enforce account scope and a durable atomic claim lock.
    """
    base = {
        "state": "UNKNOWN", "reason": None, "period_key": None,
        "idempotency_digest": None, "needs_actual_reward_receipt": True,
        "claim_performed": False,
    }

    def result(state: str, reason: str, **extra: Any) -> dict[str, Any]:
        return base | {"state": state, "reason": reason} | extra

    if not isinstance(program, str) or not program.strip():
        return result("UNKNOWN", "invalid_program")
    if not isinstance(opaque_account_ref, str) or not (
        8 <= len(opaque_account_ref) <= 128 and
        all(c.isalnum() or c in "_-" for c in opaque_account_ref)
    ):
        return result("UNKNOWN", "opaque_account_ref_required")
    try:
        current = _utc(now)
        tz = ZoneInfo(provider_timezone)
        last = _utc(last_verified_at) if last_verified_at is not None else None
    except (TypeError, ValueError, KeyError, OverflowError):
        return result("UNKNOWN", "invalid_timestamp_or_timezone")

    if last is not None and last > current:
        return result("UNKNOWN", "future_claim_evidence")
    if reset_policy == "PROVIDER_DAY":
        period = current.astimezone(tz).date().isoformat()
        already_claimed = (
            last is not None and last.astimezone(tz).date().isoformat() == period
        )
    elif reset_policy == "ROLLING_24H":
        anchor = last.isoformat() if last is not None else "unclaimed"
        period = f"rolling:{anchor}"
        already_claimed = last is not None and current - last < timedelta(hours=24)
    else:
        return result("UNKNOWN", "unsupported_reset_policy")

    # The opaque reference must be an internal pseudonym, never an email,
    # bearer token or identifiable account name.
    key = sha256(f"{program}:{opaque_account_ref}:{period}".encode()).hexdigest()
    metadata = {"period_key": period, "idempotency_digest": key}

    if already_claimed:
        return result("ALREADY_CLAIMED", "verified_for_current_period", **metadata)
    if active_campaign is not True:
        return result("UNKNOWN", "campaign_unverified_or_inactive", **metadata)
    if not user_opted_in:
        return result("HUMAN_REQUIRED", "account_opt_in_required", **metadata)
    if requires_human_challenge:
        return result("HUMAN_REQUIRED", "challenge_must_be_human", **metadata)
    if claim_method not in _ALLOWED_METHODS or automation_allowed is not True:
        return result("HUMAN_REQUIRED", "unsupported_or_unconfirmed_automation", **metadata)
    return result("ELIGIBLE", "requires_bounded_idempotent_claim", **metadata)


def check_reward_receipt(
    *,
    claim_attempted: bool,
    provider_receipt_verified: bool,
    credited_units: int | None,
    credential_or_session_logged: bool = False,
) -> dict[str, Any]:
    """Do not add credits to the ledger until confirmed by provider evidence."""
    if credential_or_session_logged:
        return {"state": "REJECTED", "credited_units": None, "reason": "secret_exposure"}
    if not claim_attempted:
        return {"state": "NOT_ATTEMPTED", "credited_units": None}
    if not provider_receipt_verified:
        return {"state": "CLAIMED_UNVERIFIED", "credited_units": None}
    if type(credited_units) is not int or credited_units <= 0:
        return {"state": "CLAIMED_UNVERIFIED", "credited_units": None}
    return {"state": "VERIFIED_GRANTED", "credited_units": credited_units}