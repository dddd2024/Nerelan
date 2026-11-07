# Codex global reset signals — read-only adapter (#1246)

**Public reset announcements are not individual account quota evidence.** This module has no scheduler, dispatch, tokens, cookies, or model API access.

## Source and limits

- Anonymous direct X for Tibo (@thsottiaux) returned HTTP 403. The optional untrusted public mirror is https://codex-reset.com/api/feed; it can also return HTTP 403 or become unavailable, which correctly yields UNKNOWN.
- The adapter is `reverse_agent/model_access/codex_reset_signals.py` with `fetch_feed` (bounded unauthenticated GET, rejects redirects) and `parse_feed` (no network). It does not persist events, poll automatically or override routing.
- Accept only a fresh `version:1` feed with `source:"x-api"` (this label is a claim by the mirror, not verified X credentials), valid UTC timestamps, valid original `x.com/thsottiaux/status/<id>` URLs, and X Snowflake timestamp agreement (5 minute bound). Old/replayed IDs, bad parent links, unhashable IDs, stale provider data and invalid JSON are ignored or classified UNKNOWN.
- Feed size is capped at 256 KiB; an outer 5-second deadline includes DNS and connect. A single daemon worker prevents repeated requests from accumulating blocked resolver threads. A slow or uninspectable TLS response yields UNKNOWN rather than blocking the host.
- Experimental forecast probabilities are intentionally **not** consumed as quota estimates.

## Interpretations

| Event kind | Description | Advisory action |
| --- | --- | --- |
| `POSSIBLE_HINT` | Third-party tease classification | `PLAN_ONLY` |
| `RESET_ANNOUNCEMENT` | Announcement or validated reply context | `PLAN_ONLY` |
| `BANKED_ANNOUNCEMENT` | Banked grant, may need claim | `PLAN_ONLY` |
| `RESET_SCOPE_UNVERIFIED` | Mirror claims completion but post lacks global Codex scope or is personal/banked | `PLAN_ONLY` |
| `RESET_REPORTED_COMPLETE` | Explicit post claims finished global Codex reset | `REFRESH_QUOTA` |

The event ID is stable (`tibo-x:<original ID>`), even after mirror reclassification, so a later scheduler can persist/dedupe it. Mirror text is untrusted evidence, not an instruction.

The #1193/#1244 scheduler must check account-specific 5-hour **and** weekly quota, timestamp freshness, execution authority, current task budgets and model eligibility before *any* Codex dispatch. An announced reset must **never** change CONFIRMED_EXHAUSTED to available or launch a paid probe. Banked grants must be claimed and individually verified. The adapter's `REFRESH_QUOTA` is a request for a read-only vendor telemetry refresh, not a claim of verified available capacity.

## Verification

- Blocking platform suite: `python -m pytest tests/platform_v1/test_codex_reset_signals.py -q` (provider-free, fake responses). The entire `tests/platform_v1` directory runs in the required GitHub baseline gate.
- A manual live `fetch_feed()` probe is read-only and optional; third-party reachability fluctuates. Do not assume background monitoring is deployed based on a successful probe.
