# Unified AI resource management (P0-3)

Product priority: #1151 P0-3. Owners: #287 (setup), #667 (usage and quota), #1009 (guided setup).
Status at this commit: **decision matrix fixed; read-only resource view implemented.** The
view was checked once against the Owner's real configuration (8 connections, 7 usable
bindings, no secret in the output) on an isolated host. That host also ran one live relay
task (SenseNova key → Claude Code, `glm-5.2`; see #1154). No quota source is wired yet.

## What "one place for every resource" means here

```text
Connection (API key | subscription CLI account | no-auth endpoint)
  -> credential state (who owns it: Nerelan vault or the official CLI login)
  -> executors it can drive, and whether each is ready now
  -> Bindings: model x executor pairings
  -> what Nerelan observed them do (attempts, success, time, tokens)
  -> provider quota/balance: only when an official source says so, else UNKNOWN
```

`GET /api/resources` on the model-control service returns exactly this, sanitized. It is a
read model over the existing store and TaskStore. It is not a second registry, and it calls
no provider.

## Replace or reuse: decision matrix

Candidates were checked on 2026-10-14 against their upstream repositories.

| Candidate | What it is | License, platform | Stable integration surface | Fit for Nerelan |
|---|---|---|---|---|
| **CC Switch** (`farion1231/cc-switch`) | Tauri desktop app that switches the API provider used by Claude Code, Codex, OpenCode, Gemini CLI and others. It does this by rewriting each tool's own config file. It also manages MCP, skills and prompts. | MIT; Windows/macOS/Linux; very active | GUI only. Its provider list sits in its own app store, and nothing there is a documented API or CLI contract. | Conflicts with Nerelan's model. Nerelan never rewrites `~/.claude/settings.json` or `~/.codex/config.toml`. Each child process gets a loopback relay and a short-lived lease, so the provider key never reaches the CLI. If both tools managed the same executor config, they would fight over it, which #1151 forbids. |
| **OpenUsage** (`janekbaraniewski/openusage`, the one named in #667) | Terminal dashboard plus headless reports (`daily/weekly/monthly/session/blocks --json`). It reads local usage of Claude Code, Codex, Cursor, Copilot, OpenCode and others, plus provider APIs (OpenAI, Anthropic, OpenRouter). | MIT; Go; Windows amd64 release binary (v0.26.1, 2026-10-11) | The `--json` report output of the CLI. Its Go `internal/...` packages are not a public API. | Covers what Nerelan cannot see itself: quota windows and spend of **subscription** accounts (Claude/Codex 5-hour blocks) and provider usage APIs. |
| **Magpie** (`yetone/magpie`) | Local gateway on `127.0.0.1:3425`. It translates between OpenAI Chat, OpenAI Responses, Anthropic Messages and Gemini. It rewrites ~60 agents' config files to point at itself. It uses signed-in Claude/Codex/Copilot accounts as providers by reading their credential files and refreshing their tokens, and fails over between accounts and models in routing groups. | MIT; Go; Windows CLI and app; very active but pre-1.0 (v0.1.1231 on 2026-10-14, first commit 2026-09-23) | `magpie quota --json`, plus `GET /v1/magpie/quotas` (`?kept=1` answers from cache and never asks a vendor) and `GET /v1/magpie/usage` on loopback. The gateway itself is OpenAI- and Anthropic-compatible. | Gives the subscription windows Nerelan cannot see (Claude/Codex 5-hour and 7-day use, resets, credits) through a local HTTP read instead of a vendor call. Its gateway also works as an ordinary Connection base URL. However, it owns subscription credentials directly, which goes against #1151 ("keep the official CLI login"). It rewrites `~/.claude/settings.json` too, and its loopback accepts any token, so any local process can spend every pooled account. |
| **LiteLLM** (`BerriAI/litellm`) | OpenAI-format gateway for 100+ providers with keys, budgets, spend logs and fallbacks. | Mostly MIT, plus an enterprise directory; Python | HTTP proxy with an OpenAI-compatible API. | Already supported as a Connection type (`litellm-proxy`, see `docs/model-access.md`). It suits Owners who already run one. Making it mandatory would add a second key store and router. |
| **Nerelan model control (existing)** | Connections, OS vault, provider identity, model discovery, Bindings, Claude/Codex readiness probes, credential relay with leases, agent profiles, `provider_usage` contracts | In-repo | `/api/connections`, `/api/bindings`, `/api/executors`, `/api/agent-roster`, now `/api/resources` | Holds the authority that matters: which key may reach which host, and task/budget truth. |

### Decisions

| Capability | Decision | Reason |
|---|---|---|
| Connection, credential vault, authority-change checks | **KEEP** | This is the security boundary (#1146, #1154). No candidate replaces it without exposing keys to a CLI's config file. |
| Credential relay plus lease for executor children | **KEEP** | Unique to Nerelan. CC Switch's file rewriting is the opposite model. |
| Model discovery, model x executor Bindings, auto-pairing | **KEEP** | Landed in #1144 and #1150, and covered by tests. |
| Subscription account login (Codex / Claude Code) | **KEEP, official CLI owns it** | #1151: accounts keep the official CLI's persistent login. Nerelan only probes readiness. |
| Locally observed usage per model x executor (agent profiles) | **KEEP, now exposed** | Real per-task evidence. `/api/resources` surfaces it with `LOCAL_METERING` provenance. |
| Provider and subscription quota/balance | **REUSE, read-only and opt-in, next slice: Magpie `GET /v1/magpie/quotas?kept=1` first, OpenUsage `--json` second** | Both are #667 option C (an external process's JSON, no `internal/` imports). Magpie's endpoint is a loopback HTTP read that never triggers a vendor call, and it already models 5-hour and 7-day windows, resets and credits per account. OpenUsage covers Owners who don't run Magpie. Until then quota is `UNKNOWN`/`UNAVAILABLE`, never derived from local usage. |
| Magpie gateway as an upstream | **KEEP generic path; no new code** | Point an `openai-compatible` or Anthropic-compatible Connection at `http://127.0.0.1:3425`. Nerelan still sees one Connection, and Magpie handles failover behind it. Whether to route subscription accounts through it is the Owner's call, because it bypasses the official-CLI-login rule. |
| Magpie / CC Switch config rewriting and subscription bridging | **Do not adopt; guard against it** | See the coexistence risk below. |
| `provider_usage` contracts and parsers | **ADAPT** | The normalized snapshot/provenance model (`OFFICIAL_*`, `LOCAL_METERING`, `UNAVAILABLE`) becomes the shape the OpenUsage adapter fills. |
| LiteLLM gateway | **KEEP as optional Connection type** | Fits Owners who already run a proxy. Not required, and not embedded. |
| CC Switch | **Do not integrate as a runtime.** Possible later: a read-only, Owner-triggered import of its provider list into Connections. | It has no stable interface and would mean dual control of executor config files. Re-evaluate if it publishes an export format. |
| Legacy `ModelProfile` (`/api/model-profiles`, `model-profile-editor.tsx`) | **RETIRE candidate** (separate PR) | Superseded by Connection + Binding. The editor is no longer mounted on any page. Removal needs its own migration check for `REVERSE_AGENT_MODEL_PROFILES_JSON` users. |

## Coexistence risk: tools that rewrite executor config

Magpie and CC Switch switch Claude Code's model by writing `~/.claude/settings.json`
(its `env` block: base URL, token, model). Nerelan's Claude Code child strips the parent
environment (`claude_child_env`), but its argv does not pin `--setting-sources`. So a
user-level `settings.json` written by one of those tools may still redirect a Nerelan
**account** run to another gateway, or to another account or model. That would happen without
Nerelan's binding, lease or budget knowing. This is unverified against the current Claude
Code CLI and is tracked as a follow-up. Until it is resolved, the resource view's readiness
describes Nerelan's intent, not proof of which upstream served a turn.

## Interface: `GET /api/resources`

```json
{
  "resources": [{
    "connection_id": "sense", "name": "SenseNova", "enabled": true,
    "upstream_provider_id": "...", "protocol_family": "openai",
    "credential": {"kind": "api_key", "configured": true, "status": "vault"},
    "credential_owner": "nerelan",
    "executors": [{"executor_id": "opencode", "ready": true, "readiness_status": null},
                  {"executor_id": "claude_code", "ready": true, "readiness_status": "managed_login_unavailable"}],
    "bindings": [{"binding_id": "sense-glm-5.2-claude_code", "model_id": "glm-5.2",
                  "executor_id": "claude_code", "enabled": true, "usable": true,
                  "observed": {"attempts": 3, "ok": 3, "success_rate": 1.0, "median_ok_seconds": 44,
                               "observed_tokens": 9000, "provenance": "LOCAL_METERING", "...": "..."}}],
    "observed_usage": {"attempts": 3, "ok": 3, "failed": 0, "observed_tokens": 9000,
                       "provenance": "LOCAL_METERING", "window_tasks": 500},
    "quota": {"state": "UNKNOWN", "provenance": "UNAVAILABLE", "reason": "no_official_quota_source"}
  }],
  "summary": {"connections": 1, "usable_bindings": 1, "quota_known": 0}
}
```

Invariants (tested):

- No secret, env-var name or vault reference appears in the response.
- `quota` is never filled from local usage. Unknown stays `UNKNOWN`.
- `usable` uses the binding resolver's rules: the connection is enabled, a CLI-session
  connection has an available session, and the executor is operational, or it is the
  Claude Code relay without a claude.ai login.
- `credential_owner` is `nerelan` for API keys, the official CLI for Codex/Claude accounts,
  `external_cli` for another CLI's own sign-in (for example OpenCode), and `none` for no-auth
  endpoints.
- If the observed-usage source fails, the view still lists every resource with
  `observed_usage.status: "unavailable"` and zero totals; it does not fail the request.

## Tokens, equivalent cost and subscription quota

**One token ledger** (`reverse_agent/platform_v1/usage_ledger.py`). Every finished,
model-backed task becomes the same counters: `input` (non-cached), `cache_read`,
`cache_write`, `output` (billable, reasoning included) and `reasoning` (for reference).
The three executors report differently:

| Executor | Source | Differences handled |
|---|---|---|
| OpenCode | `task_usage_observations` rows | Reasoning is reported *beside* output, not inside it: real history has reasoning > output in 540 of 1,312 rows. It is folded into billable output. |
| Codex | `EXECUTOR_COMPLETED.token_usage` | `input_tokens` *includes* `cached_input_tokens`, so non-cached input = input − cached. |
| Claude Code | `EXECUTOR_COMPLETED.token_usage` | Cache reads and writes are separate from input. The stream parser now also keeps `cache_creation_input_tokens`, the concrete model behind an alias such as `sonnet` (`modelUsage`), and the CLI's own `total_cost_usd`. |

**Equivalent cost** (`reverse_agent/model_access/pricing.py`) is what the tokens would
cost at the **model maker's own** pay-as-you-go list price. For example, GLM-5.2 is
priced at Zhipu's price even when it ran on SenseNova's free gateway.
- Prices come from a vendored, dated models.dev snapshot (`pricing_snapshot.json`). It is
  refreshed offline with `python -m reverse_agent.model_access.pricing refresh <api.json>`.
- Every figure is `ESTIMATED_LIST_PRICE` with its source and date. It is not an invoice.
- An unresolved alias, an unknown vendor or an unlisted model stays `UNKNOWN`, and a mix
  of priced and unpriced runs is `PARTIAL`.
- Two cases are flagged in `notes` rather than silently assumed: a cache price that is not
  listed (billed at the input price) and long-context tiers (not applied).
- Claude Code's own `total_cost_usd` is shown beside the estimate as a cross-check.

**Subscription quota** (`reverse_agent/model_access/subscription_quota.py`) uses
first-party sources only:
- **Codex:** the account's 5-hour and weekly windows (percent used, reset time, plan,
  credits) from the newest `token_count` event in `$CODEX_HOME/sessions`. Only lines
  containing that event are decoded.
- **Claude Code:** `rate_limit_event` notices captured from Nerelan's own runs on the Claude
  *account*. Relay runs are excluded, because their notices are not about the subscription.
- **Freshness:** a window whose reset time has passed is shown as "reset passed, current use
  unknown", never as 0%.
- **Opting out:** set `REVERSE_AGENT_SUBSCRIPTION_QUOTA=0`.

All three appear in `/api/resources` per binding, per connection and in total. They also
appear in Settings → 资源与用量. If a source fails, only its figures are dropped.

Checked on the Owner's real history (a read-only copy):
- 62 finished model-backed tasks, 45 of them with tokens.
- About $16.67 at list price, almost all GLM-5.2 cache reads on `coding-glm`.
- Codex Plus windows at 49% (5-hour) and 40% (weekly), matching the CLI.
- Older Claude `sonnet` runs stay unpriced, because they predate model capture.

## Remaining P0-3 work

1. Quota beyond official percentages, following the Owner's rule (2026-10-14):
   - Official percent → show it.
   - Status only → show availability and record actual limit hits.
   - History but no number → predict with an error range.
   - Nothing reliable → `UNKNOWN`.
   - If the predicted quota is too low for the next task, switch model or warn before
     dispatch.
2. Optional third-party quota sources (Magpie `GET /v1/magpie/quotas?kept=1`, OpenUsage
   `--json`) for subscriptions the official CLIs do not report. These are opt-in and
   labelled with the tool as their source.
3. Executor isolation: verify whether `claude -p` applies `~/.claude/settings.json` `env`
   under Nerelan's argv. If it does, pin the settings sources for account and relay runs and
   add a regression test.
4. Retire legacy `ModelProfile` after a migration check.
