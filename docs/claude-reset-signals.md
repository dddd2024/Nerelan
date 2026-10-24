# Claude reset announcements — Nerelan opt-in observer (#1255)

The Claude subscription reset source is the third-party public tracker [Claude Resets](https://clauderesets.com/) with the documented JSON API [GET /api/v1/status](https://clauderesets.com/api/docs). It curates original @ClaudeDevs/Anthropic-related announcements; it is not an official Anthropic API.

## Operating contract

Set `REVERSE_AGENT_CLAUDE_RESET_WATCH=1` in the host environment to start a read-only polling worker. Default: **off**. It polls at most once each hour (minimum interval 30 minutes), and stops with the host. It does not call inference models, log into X, read credentials, buy usage, redeem grants or dispatch Agent tasks.

Read-only endpoint: `GET http://127.0.0.1:<model-control-port>/api/reset-announcements`.

Event receipts persist atomically to `<TaskStore DB directory>/claude_reset_observations.json`, not to the production task SQLite tables. They are bounded to 64 distinct event identities. Event ID plus revision makes repeat polling and host restarts idempotent; retraction and revision update the original receipt. A stale/unreachable source yields UNKNOWN but does not erase previous receipts. `new_events` are observations, **not permissions**.

| Public event | Advisory action | Meaning |
| --- | --- | --- |
| Confirmed recent applied reset with known scope | `REFRESH_QUOTA` | Ask for separate, read-only account quota check; never auto-dispatch |
| Announced but not completed reset | `PLAN_ONLY` | Preparation or bounded later review only |
| Banked reset still within expiry | `CLAIM_MANUALLY` | Eligible users check Claude Settings → Usage; never auto-redeem |
| Retracted/cancelled event | `INVALIDATE_HINT` | Revoke previous expectation |
| Stale/error/unknown scope | `UNKNOWN` or no event | No capacity claim |

Subscriptions and Claude Code share usage limits; separately billed Claude API credits are unrelated. Existing `reverse_agent/model_access/subscription_quota.py` provides account-specific official CLI observations via `claude_quota()`. When an unseen confirmed applied reset is observed, the host invalidates its cached Claude subscription quota presentation and reads the existing official CLI telemetry **once per event**; this is a local, read-only log check and may still return UNKNOWN or stale numbers. The observer does **not** modify the quota guard, Magpie, account state, budgets or #1244 routing. `REFRESH_QUOTA` is not a verified 5-hour/weekly refill and never authorizes a model call.

## Verification

Provider-free blocking suite: `python -m pytest tests/platform_v1/test_claude_reset_signals.py -q`. It covers applied vs banked, expiry, plan/window scopes, corrections/retractions, stale/error behavior, whole-request DNS timeout, original provenance, idempotence after host restart and real trusted-host model API endpoint on isolated TaskStore. No paid inference or production data modifications.

The tracker explicitly provides **no reliable global reset forecasts**. The September 4 applied announcement is old and inactionable on October 19; the September 22 banked offer is potentially valid until October 22 for individually eligible accounts. Historical cadence is not a usable reset schedule.
