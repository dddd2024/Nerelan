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

## Tiered quota, forecasts and the dispatch guard

The Owner's rule (2026-10-14) is that every subscription window is shown on the best basis
available (`basis` in the API):

| Basis | When | Shown as |
|---|---|---|
| `official_percent` | The CLI states the percent used. Codex always does; Claude does when a notice carries `utilization`. | The percent, with reset time and plan. |
| `official_status` | The CLI only says allowed / warning / rejected (Claude `rate_limit_event`). | Availability (可用 / 接近上限 / 已触顶) plus reset time. Actual limit hits are listed. |
| `estimated` | No official number, but local history shows how much a window holds. | Predicted percent used, with a low–high range and a remaining-units range. The reset time is marked as estimated when it is inferred. |
| `unknown` | Nothing reliable. If usage in the window was measured, that is shown with "上限未知". | UNKNOWN. |

How capacity is learned (`model_access/quota_forecast.py`, `quota_history.py`), in
list-price units, because limits weigh cache and output roughly the way prices do:

- **Codex:** official percent steps against the usage in the same window, taken from
  `token_count` / `turn_context` lines in `$CODEX_HOME/sessions`. Steps under 3 points are
  ignored, and a single sample carries ±1 point of rounding.
- **Claude:** usage in rolling 5-hour blocks, each starting with the first request after the
  previous block ended. A block's usage up to an actual `usage_limit_reached` error gives one
  capacity sample. The samples come from assistant usage lines (deduplicated by message id) and
  API error lines in `~/.claude/projects/*/*.jsonl`. A block that already hit the limit is
  reported as reached until it ends.
- **Range:** the median of the samples, with the interquartile range once there are 4 or
  more. Min and max are kept for reference.
- **Scope:** usage elsewhere (other devices, the web, Nerelan's `--ephemeral` Codex runs) is
  invisible here. The estimates say `usage_scope: this_machine` and lean optimistic.

**Official Claude readings** come from two places:

- **The Nerelan status line** (`model_access/claude_statusline.py`). Installed with
  `python -m reverse_agent.model_access.claude_statusline install`, on the Owner's request
  (2026-10-14).
  - Claude Code hands it the official `rate_limits` (`five_hour`, `seven_day`:
    `used_percentage`, `resets_at`): the same figures as the app's "Plan usage limits".
  - It appends only those numbers to `%LOCALAPPDATA%\Nerelan\claude_rate_limits.jsonl`. It
    never reads the login token and never fails the status line.
  - It runs only where Claude Code renders a status line: terminal sessions, and possibly
    not the desktop app.
- **Nerelan's own Claude account runs:** `rate_limit_event.utilization`.

With official readings:

- A reading at most 10 minutes old is shown as is.
- An older reading is carried forward: its percent, plus the local usage since, divided by a
  capacity calibrated from earlier readings. Calibration takes the usage in that window
  instance divided by its official percent.
- The weekly window rolls the official reset forward on its fixed 7-day schedule.

Without official readings, the 5-hour capacity falls back to actual limit hits:

- One sample per window, and samples under 60% of the median are dropped as probable weekly
  hits.
- The optimistic end is widened 1.5×, because a backtest against the Owner's official 88%
  (06:50 UTC, 2026-10-14) showed the hit-based capacity was about a third too low in a
  cache-read-heavy window. Limits do not weigh token kinds exactly like list prices.
- 5-hour windows open at the top of the hour of their first request, matching the reset time
  the CLI reports.
- Only events up to `now` are counted.

**Dispatch guard** (`platform_v1/quota_guard.py`, host `_quota_guarded`). Before an
agent-team role dispatches on a subscription binding, the account's windows are compared with
the binding's typical task size. That size is taken from the binding's own successful tasks
when it has them, then its connection's, then all tasks; the decision records which was used.

- **`switch`:** the limit is reached, an official percent is ≥ 98, an estimate's optimistic
  end is ≥ 98, or even the optimistic remaining amount cannot fit the task. The role moves to
  the same model on another account, or to a stronger coding role's agent. It never moves to
  a weaker one, and the planner and reviewer only move to the same model. If no alternative
  passes its own check, the run goes ahead with a recorded warning.
- **`warn`:** the pessimistic remaining amount does not fit, an official percent is ≥ 90, an
  estimate's midpoint is ≥ 90, or the CLI says the account is near its limit.
- **Explicitly chosen bindings** are never moved; their shortfall is recorded as a warning.

Decisions appear in `/api/resources` (`summary.quota_guard`) and in Settings.

On the Owner's real data (2026-10-14):
- Codex official 72% / 43%.
- Claude estimated at about 99% (range 72–100%) from 9 limit hits in three days.
- The guard dry run gave Claude bindings `warn` (possibly insufficient) and Codex `ok`.

## Remaining P0-3 work

1. Optional third-party quota sources (Magpie `GET /v1/magpie/quotas?kept=1`, OpenUsage
   `--json`) for subscriptions the official CLIs do not report. These are opt-in and
   labelled with the tool as their source.
2. Executor isolation: verify whether `claude -p` applies `~/.claude/settings.json` `env`
   under Nerelan's argv. If it does, pin the settings sources for account and relay runs and
   add a regression test.
3. Retire legacy `ModelProfile` after a migration check.

## Magpie source (opt-in)

Nerelan can read a local [Magpie](https://github.com/yetone/magpie) gateway (v0.1.1250)
read-only so the resources page shows subscriptions served through it — the first target is
the WorkBuddy subscription (provider ids `workbuddy` and `workbuddy-ai`). This is
**default-off** and touches the network only when explicitly enabled.

### Enabling

In Settings, enable **Start Magpie with Nerelan**, choose an existing absolute `.exe`
path, and set its loopback URL (default `http://127.0.0.1:3425`). These Owner settings
are persisted as `magpie: {enabled, executable, base_url}` in the model setup state;
they default to disabled. Changes apply on the next host check, within 60 seconds.

The trusted host probes `/v1/models` with a two-second timeout. If it is down and the
configured executable is not already running, the host starts it detached with no
arguments and waits up to 30 seconds for health. Failure leaves Nerelan available
and Magpie bindings unusable. A watcher checks every 60 seconds and allows at most
three restart attempts per rolling hour, in addition to the initial launch.
Nerelan never stops Magpie or reads or changes its config or login files.

Settings and `/api/platform/status` show `MAGPIE_DISABLED`, `ALREADY_RUNNING`,
`STARTED`, `START_FAILED` with a reason, or `UNREACHABLE`, plus the last probe time
and served model count. A running executable with an unresponsive port is reported
as `UNREACHABLE` and is never duplicated.

Enabling the setting also enables read-only resource observation. The existing
`REVERSE_AGENT_MAGPIE=1` / `REVERSE_AGENT_MAGPIE_URL` options remain available for
observation only; they do not authorize launching an executable. When neither is
enabled, no gateway is contacted and `GET /api/resources` has no `external_sources` key.

### What is read

Three loopback GET requests, in order, with `Authorization: Bearer magpie-nerelan` so Magpie
counts the calls as Nerelan:

1. `GET /api/hello` — confirms the gateway is Magpie (`{"name":"magpie","version":"0.1.1250"}`).
2. `GET /v1/models` — lists models Magpie exposes, including routing groups.
3. `GET /v1/magpie/quotas?kept=1` — **cached only**: Magpie answers from its own cache and
   never asks a vendor. A key held to a budget returns 403 `gateway_key_held`; the snapshot
   reports that account as unavailable.

The result appears under `external_sources.magpie` in `GET /api/resources`:

```json
{"external_sources": {"magpie": {
  "status": "available", "version": "0.1.1250",
  "models": [{"model_id": "workbuddy/glm-5.2", "provider": "workbuddy", "...": "..."}],
  "accounts": [{"provider": "workbuddy", "kind": "subscription", "account_ref": "a1b2c3d4e5f6",
                "windows": [{"name": "hourly", "used_percent": 20, "remaining_percent": 80, "...": "..."}],
                "state": "FRESH", "provenance": "EXTERNAL_MAGPIE"}]}}}
```

### Privacy

Account identity is reduced to a short `account_ref` hash (first 12 hex chars of SHA-256 over
`[provider, user]`). No `user` string, email, phone-derived login, alias or origin is placed
in the response. Transport errors that may embed personal data are caught and replaced with a
generic reason. The snapshot never contains secrets.

### Fallback

If the gateway is not Magpie, refuses, redirects, times out, or returns malformed data, the
snapshot is `{"status": "unavailable"}` (or `refused` / `not_magpie`). Legacy resources
(connections, bindings, quotas, tokens, cost, summary) are **unaffected** — external accounts
are listed separately and are never added into a Nerelan connection's quota, tokens or cost, so
nothing is double counted. When Magpie is disabled the response is byte-identical to before.

### Using WorkBuddy models through Magpie

Magpie's gateway is OpenAI-compatible. To use WorkBuddy models through it:

1. In Settings (or via `PUT /api/connections`), add an **openai-compatible** Connection with
   `base_url` `http://127.0.0.1:3425/v1` and key `magpie-nerelan`.
2. Discover models (`POST /api/connections/<id>/models`); you will see ids like
   `workbuddy/glm-5.2` and routing-group names without a slash.
3. Bind e.g. `workbuddy/glm-5.2` to OpenCode (or another executor).

> **Owner responsibility (R3):** Magpie reads WorkBuddy's login token itself and manages its
> own credential refresh. Installing Magpie and signing in to WorkBuddy is the Owner's own
> action — Nerelan never touches that token. The loopback gateway accepts **any** bearer key;
> that is a convenience for attribution, **not** access control. Any local process that knows
> the address can spend every pooled account. Secure the host accordingly.

## One-time move of legacy API connections into Magpie (#1170)

Owner decision 2026-10-21: the API-key Connections configured before Magpie are moved into
Magpie **once**, and every **new** API provider or account is added in Magpie, not in Nerelan.
Nerelan keeps consuming Magpie through its single `magpie` openai-compatible Connection and keeps
its task-level routing, guards and evidence. There is no importer, sync or second provider
editor in Nerelan. Official CLI sessions (`external_cli_session`: OpenCode, Codex/ChatGPT,
Claude) keep their native login and are not moved. `claude/*` and `codex/*` models in Magpie
share the Owner's subscription quota, so they are bound only on the Owner's explicit say-so.

| Legacy Connection | Upstream base URL | Add in Magpie as | Magpie model ids |
| --- | --- | --- | --- |
| `openrouter` | `https://openrouter.ai/api/v1` | preset **OpenRouter** | `openrouter/<model>` |
| `groq` | `https://api.groq.com/openai/v1` | preset **Groq** | `groq/<model>` |
| `mistral` | `https://api.mistral.ai/v1` | preset **Mistral** | `mistral/<model>` |
| `deepseek-flash` | `https://token.sensenova.cn/v1` | custom vendor `sensenova`, same base URL | `sensenova/<model>` |
| `agnes` | `https://apihub.agnes-ai.com/v1` | custom vendor `agnes`, same base URL | `agnes/<model>` |

Steps:

1. **Back up locally** `model_setup_state.json` and `~/.config/magpie/providers.json`. Never
   publish either. Leave the OS-vault keys of the legacy Connections in place.
2. **The Owner adds each provider in Magpie's Providers UI** with its key. Keys are never pasted
   into issues, logs or shell arguments (so not `magpie provider add <id> <key>` either), and
   Nerelan never reads or copies them.
3. **Check** what Magpie now lists, read-only (GET `/api/hello`, `/v1/models`,
   `/v1/magpie/quotas?kept=1`; no inference, no config write):

   ```text
   python -m reverse_agent.model_access.magpie_migration --state <path>/model_setup_state.json
   ```

   Each `api_key` Connection is reported `IMPORTED` (Magpie lists models under its provider id),
   `NOT_IMPORTED`, or `UNKNOWN` (Magpie unavailable, or no provider mapping — pass
   `--provider <connection_id>=<magpie_provider>` if a custom vendor got another name). Each of
   its Bindings gets the proposed `magpie_model_id`, whether Magpie lists it, and any existing
   Binding on the `magpie` Connection with that model. `IMPORTED` is not `TESTED`: a provider is
   `TESTED` only after a bounded live request the Owner authorizes, and `summary.complete` stays
   `false` in this report by design.
4. **Rebind** each still-wanted Binding: add a Binding on the `magpie` Connection with the
   proposed model id and the same executor, run one small live Task, and check the run's actual
   model and Magpie's usage for it. Then disable the legacy Binding. **Rollback** is re-enabling
   the legacy Binding; keep the legacy Connection until a live Task on the Magpie Binding has
   passed.
5. When every wanted Binding runs through Magpie, the one-time migration is complete. Only then
   remove legacy Connections the Owner no longer wants, and the duplicated legacy setup UI once
   nothing depends on it.
