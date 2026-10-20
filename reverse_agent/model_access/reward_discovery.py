"""Evidence-based check-in discovery for already configured services.

Only an authorized upstream catalog may mark evidence_verified=True. This
module never requests credentials, calls providers, schedules or claims credits.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping, Sequence
from urllib.parse import urlsplit

from .reward_claims import check_claim_eligibility

KINDS = frozenset({"DAILY_CHECK_IN", "CAMPAIGN_CLAIM", "BANKED_MANUAL_REDEEM",
                   "PASSIVE_QUOTA_RESET", "NO_REWARD_PROGRAM"})
SOURCE_KINDS = frozenset({"OFFICIAL_API", "FIRST_PARTY_UI", "OWNER_VERIFIED"})
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_ACCOUNT = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")


@dataclass(frozen=True)
class RewardAccount:
    provider_id: str
    opaque_account_ref: str
    eligible: bool | None = None


@dataclass(frozen=True)
class RewardProgram:
    provider_id: str
    program_id: str
    kind: str
    source_kind: str
    evidence_url: str
    evidence_verified: bool
    verified_at: datetime
    expires_at: datetime
    active: bool | None
    provider_timezone: str = "UTC"
    reset_policy: str = "PROVIDER_DAY"
    claim_method: str | None = None
    automation_allowed: bool | None = None
    requires_human_challenge: bool = False


def _utc(dt: datetime) -> datetime:
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("aware UTC time required")
    return dt.astimezone(timezone.utc)


def _valid(p: RewardProgram, now: datetime) -> bool:
    try:
        url = urlsplit(p.evidence_url)
        t, expiry = _utc(p.verified_at), _utc(p.expires_at)
        return (
            isinstance(p.kind, str) and p.kind in KINDS
            and isinstance(p.source_kind, str) and p.source_kind in SOURCE_KINDS
            and (p.claim_method is None or isinstance(p.claim_method, str))
            and type(p.requires_human_challenge) is bool
            and p.evidence_verified is True
            and bool(_ID.fullmatch(p.provider_id)) and bool(_ID.fullmatch(p.program_id))
            and url.scheme == "https" and bool(url.hostname)
            and url.username is None and url.password is None and url.port in (None, 443)
            and t <= now < expiry and now-t <= timedelta(days=30)
        )
    except (ValueError, TypeError, AttributeError, OverflowError):
        return False


def discover_reward_needs(
    accounts: Sequence[RewardAccount],
    programs: Sequence[RewardProgram],
    *, now: datetime,
    opted_in: Collection[tuple[str, str, str]] = (),
    verified_claims: Mapping[tuple[str, str, str], datetime] | None = None,
) -> list[dict[str, object]]:
    """Return advisory account/program states, never an executed check-in.

    Missing or conflicting program evidence is UNKNOWN, not NOT_REQUIRED.
    Requires actual first-party evidence and account-level opt-in to qualify.
    """
    now = _utc(now)
    program_map: dict[str, dict[str, list[RewardProgram]]] = {}
    for p in programs:
        if (isinstance(p, RewardProgram)
                and isinstance(p.provider_id, str) and _ID.fullmatch(p.provider_id)
                and isinstance(p.program_id, str) and _ID.fullmatch(p.program_id)):
            program_map.setdefault(p.provider_id, {}).setdefault(p.program_id, []).append(p)
    # Validate identities before hashing, and compare every duplicate account
    # record so a caller cannot select eligibility simply by input ordering.
    account_map: dict[tuple[str, str], RewardAccount] = {}
    account_conflicts: set[tuple[str, str]] = set()
    for account in accounts:
        if not isinstance(account, RewardAccount):
            continue
        if (not isinstance(account.provider_id, str)
                or not _ID.fullmatch(account.provider_id)
                or not isinstance(account.opaque_account_ref, str)
                or not _ACCOUNT.fullmatch(account.opaque_account_ref)):
            continue  # avoid echoing account PII/tokens as opaque refs
        key = (account.provider_id, account.opaque_account_ref)
        # bool compares equal to int(1); untrusted account-level evidence must
        # be normalized before dedupe, otherwise input order selects authority.
        verified_eligibility = (account.eligible if
                                account.eligible is None or type(account.eligible) is bool
                                else None)
        canonical = RewardAccount(account.provider_id, account.opaque_account_ref,
                                  eligible=verified_eligibility)
        existing = account_map.setdefault(key, canonical)
        if existing.eligible != canonical.eligible:
            account_conflicts.add(key)

    results = []
    for key, account in account_map.items():
        matching = program_map.get(account.provider_id, {})
        # NO_REWARD_PROGRAM is a provider-wide claim. A different program ID
        # must never bypass that contradiction to become AUTO_ELIGIBLE.
        has_no_reward = any(
            p.kind == "NO_REWARD_PROGRAM" and p.active is True and _valid(p, now)
            for versions in matching.values() for p in versions
        )
        has_other = any(
            p.kind != "NO_REWARD_PROGRAM" and p.active is True and _valid(p, now)
            for versions in matching.values() for p in versions
        )
        provider_conflict = has_no_reward and has_other
        if not matching:
            matching = {"": []}
        for program_id, candidates in sorted(matching.items()):
            p = candidates[0] if candidates else None
            kind = p.kind if p else "UNKNOWN"
            state, reason, action = "UNKNOWN", "unverified_reward_program", "DISCOVER_ONLY"
            if key in account_conflicts or provider_conflict:
                reason = ("conflicting_account_eligibility" if key in account_conflicts
                          else "provider_wide_no_reward_conflict")
            elif p and len(candidates) == 1 and _valid(p, now):
                if p.active is False:
                    state, reason, action = "NOT_REQUIRED", "inactive", "NONE"
                elif p.active is not True:
                    reason = "campaign_status_unknown"
                elif kind in {"PASSIVE_QUOTA_RESET", "NO_REWARD_PROGRAM"}:
                    state, reason, action = "NOT_REQUIRED", "no_check_in_needed", "NONE"
                elif account.eligible is False:
                    state, reason, action = "NOT_ELIGIBLE", "account_not_eligible", "NONE"
                elif account.eligible is not True:
                    reason = "account_eligibility_unknown"
                elif kind == "BANKED_MANUAL_REDEEM":
                    state, reason, action = "MANUAL_REQUIRED", "redeem_in_first_party_ui", "MANUAL"
                elif kind in {"DAILY_CHECK_IN", "CAMPAIGN_CLAIM"}:
                    claim_key = (*key, program_id)
                    try:
                        eligibility = check_claim_eligibility(
                            program=program_id, opaque_account_ref=account.opaque_account_ref,
                            now=now, provider_timezone=p.provider_timezone,
                            last_verified_at=(verified_claims or {}).get(claim_key),
                            reset_policy=p.reset_policy, claim_method=p.claim_method,
                            automation_allowed=p.automation_allowed,
                            user_opted_in=claim_key in opted_in,
                            requires_human_challenge=p.requires_human_challenge,
                            active_campaign=p.active,
                        )
                    except (OverflowError, ValueError, TypeError):
                        # Provider-local day conversion of boundary receipt
                        # timestamps can overflow even after valid UTC input.
                        eligibility = {"state": "UNKNOWN",
                                       "reason": "invalid_receipt_timezone"}
                    reason = eligibility["reason"]
                    state, action = {
                        "ELIGIBLE": ("AUTO_ELIGIBLE", "AUTO_ELIGIBLE"),
                        "ALREADY_CLAIMED": ("ALREADY_CLAIMED", "NONE"),
                        "HUMAN_REQUIRED": ("MANUAL_REQUIRED", "MANUAL"),
                    }.get(eligibility["state"], ("UNKNOWN", "DISCOVER_ONLY"))
                    if reason == "account_opt_in_required":
                        # Surface an unavoidable human challenge before an opt-in
                        # toggle; opt-in cannot make this provider automatable.
                        if (p.requires_human_challenge
                                or p.automation_allowed is not True
                                or p.claim_method not in {"OFFICIAL_API", "FIRST_PARTY_UI"}):
                            state, action = "MANUAL_REQUIRED", "MANUAL"
                            reason = "non_automatable_provider_method"
                        else:
                            state, action = "OPT_IN_REQUIRED", "OPT_IN"
            results.append({
                "provider_id": account.provider_id,
                "opaque_account_ref": account.opaque_account_ref,
                "program_id": program_id or None, "kind": kind,
                "state": state, "reason": reason, "action": action,
                "evidence_url": p.evidence_url if p and state != "UNKNOWN" else None,
                "claim_performed": False,
            })
    return results
