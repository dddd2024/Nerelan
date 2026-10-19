# Codex global reset signals (read-only adapter; #1246)

Public reset announcements are **not account authorization**.

## Source and ownership

- Direct anonymous X page retrieval for `@thsottiaux` returned HTTP 403 on 2026-10-19; do not scrape X behind login or ask for user cookies.
- Optional third-party mirror: https://codex-reset.com/api/feed (source posts link to original X).
- Read-only prototype: `reverse_agent/model_access/codex_reset_signals.py`, functions `fetch_feed` and `parse_feed`. No host polling, background task, persisted event store, frontend or dispatcher wiring has been shipped in this slice.
- The provider may become unavailable or change its API. Only a valid, fresh `version:1` feed is accepted. Results are an untrusted observation. The provider's forecast is experimental and intentionally **not consumed** by this module.

## Output and rules

Each valid recent original post is returned as a `ResetEvent` with a stable `event_id`, `published_at`, `source_url`, limited `excerpt` and advisory `action`.

| Event kind | Meaning | Advisory action |
| --- | --- | --- |
| `RESET_ANNOUNCEMENT` | Explicit prospective public reset report | `PLAN_ONLY` |
| `POSSIBLE_HINT` | Third-party tease classifier; no guarantee | `PLAN_ONLY` |
| `RESET_REPORTED_COMPLETE` | Public author claims completed reset, not account evidence | `REFRESH_QUOTA` |
| `BANKED_ANNOUNCEMENT` | Grant into account bank may need redemption | `PLAN_ONLY` |

The interpreter does **not** accept arbitrary discussion of a reset as a completion claim. If the feed is stale, malformed or unreachable it returns `STALE`/`UNKNOWN`, not an available quota.

The downstream #1193/#1244 implementation must persist deduped events, perform an authorized local vendor quota refresh after `REFRESH_QUOTA`, and independently verify BOTH subscription windows and current Owner authority before dispatch. A third-party quote, a reset forecast, or a banked announcement must not clear a known provider limit, start a paid task, change the selected account, or extend a window.

## Verification

Provider-free test: `python -m pytest tests/test_codex_reset_signals.py -q` (fake HTTP, no X login, no paid inference). On a current X mirror feed, `fetch_feed()` is only a read-only reachability check, not a declaration of account availability.
