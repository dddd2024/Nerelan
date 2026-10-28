# Reward discovery: services requiring check-in (#1270)

## Current implementation state

The model_access/reward_discovery.py module is provider-free and side-effect-free. It consumes already authorized account pseudonyms and externally verified program descriptors. It DOES NOT access live provider pages, log into accounts, submit check-ins, redeem offers, query external APIs or schedule tasks. Existing reward_claims.py handles eligibility and receipt verification.

Do not interpret AUTO_ELIGIBLE as CLAIMED, credits received or authorization to call a model. Claim execution requires an approved provider adapter, a durable per-account-per-period lock and verified reward receipt before any ledger update.

## Evidence and outputs

Every program descriptor must be independently verified from a first-party source or Owner verification, with a non-sensitive URL, timestamps, active campaign status, service timezone and claim reset policy, and automation permissions. The trusted loader, not arbitrary downloaded metadata, must set evidence_verified. Missing/stale/conflicting evidence yields UNKNOWN.

| Program and evidence | State | Action |
| --- | --- | --- |
| Verified daily check-in without user opt-in | OPT_IN_REQUIRED | Request opt-in |
| Verified daily check-in and approved opt-in | AUTO_ELIGIBLE | Eligible ONLY, not attempted |
| Provider-verified receipt for current period | ALREADY_CLAIMED | None |
| One-time campaign with unsupported cadence | UNKNOWN | Investigate |
| Banked grant, such as Claude manual reset | MANUAL_REQUIRED | Claim through first-party UI |
| Provider quota resets automatically | NOT_REQUIRED | Never produce a fake check-in |
| Verified service has no reward program | NOT_REQUIRED | None |
| Missing/expired/conflicting source | UNKNOWN | More evidence needed |
| Captcha, 2FA or no permission for automation | MANUAL_REQUIRED | Human action required |

## Remaining deliverables

D1: Connect the classifier to actual authenticated Connection/Magpie account discovery and verified service-specific program metadata. Surface source/freshness and account states in the resource UI. No unverified program may be labeled executable.

D2: For at least one service with a documented, permissible method, perform user-opted-in check-in via approved API or first-party UI, then reconcile real provider receipt. This is NOT implemented.

D3: Configure bounded provider-local intervals with durable idempotency, retry/backoff and restarts. Automatic quota resets and banked manual grants are separate flows.

Tests (no real provider calls): python -m pytest tests/platform_v1/test_reward_discovery.py tests/test_reward_claims.py -q.
