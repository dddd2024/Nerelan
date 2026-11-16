# Magpie capability map (living reference)

```text
MAGPIE VERSION:   0.1.4074 (app, gateway 127.0.0.1:3425), inventoried 2026-11-14
SUPERSEDES:       MAGPIE_CAPABILITY_AUDIT_2026-11-04.md for scope (that audit covered
                  M1–M5 only — accounts, quota wait, namespaces, usage/cost — on 0.12.6)
METHOD:           read-only: `magpie --help` and every subcommand's help, `magpie agents|
                  groups|settings list|tools|status`, GET on the gateway index `/` and its
                  read endpoints, a walk of every app page (no setting changed), and a
                  search of Nerelan's code for each endpoint/command
INDEX ISSUE:      #1342 (cross-feature gap matrix)
```

**Rule.** Before designing a feature or filing an Issue about models, accounts, quota,
usage, routing, agent configuration or agent tooling, check this map *and* closed Issues.
When Magpie bumps its version, diff `magpie --help` and the gateway index against this
file and update it.

## 1. Headline findings

1. **Magpie routing groups cover most of what Nerelan's router does per account.**
   Groups route by `smart | order | rotate | usage | pace | weight | free | fast | cheap |
   drain | expiring`, keep a conversation on an account while its cache is worth keeping
   (`stays=auto`), fail over *inside one request* when an account is out of quota or down,
   and can classify turn difficulty (`effort=auto`). Magpie already builds an
   `auto/<model>` group for every model that several providers serve (`auto/glm-5.2` =
   SenseTime + ZCode + WorkBuddy + Trae CN; `auto/minimax-m3.1-flash` = OpenRouter +
   WorkBuddy + WorkBuddy AI + MiniMax Code). Nerelan never selects a group; it picks
   concrete accounts and so re-implements holds, fallback and spreading — and today
   (2026-11-14) failed at exactly those (#1530, #1533).
2. **Several needed capabilities already exist in Nerelan but are switched off or
   ineffective**, so the work is activation, not construction:
   - `account_routing=auto|magpie` (Owner decision 2026-11-04, `multi_account/routing.py`)
     hands account selection to Magpie — never enabled: `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING`
     is unset on the run host.
   - Expiring credits / time-limited allowances (#1471, `1e272186`) — deployed, but cannot
     reach bindings the unproven-model gate never lets in.
   - `pool_verifier.py` (Owner decision 2026-11-11) verifies unproven bindings — reachability
     only (`Reply OK`), one per minute, so ~3 h to cover 169 bindings; MiniMax was never reached.
3. **Stalls have a gateway-side answer.** `groupFirstToken` / `groupPatience` (time to first
   token before failing over), `refusalRetries`, `retryAfterCap` bound what OpenCode
   experienced as 15-minute silent retries (#1530).
4. **Free credits are left on the table.** Daily check-ins: `workbuddyCheckin on`,
   `traeCheckin off`, `minimaxCheckin off` (MiniMax Code shows +400/day).
5. **Per-request and per-session cost already exists** (`/v1/magpie/usage/requests`,
   `magpie sessions` — the app shows each Nerelan task's OpenCode session with tokens,
   cache and cost). Nerelan charges failed attempts their full reservation as UNKNOWN (#1531).
6. **Gateway keys can hard-enforce budgets**: per-key `--tokens/--cost` limits, model and
   account allowlists, concurrency, and short-lived keys (`gateway-key issue --ttl`). A
   per-task or per-window key would make Nerelan's token budget enforced at the gateway
   rather than reconciled afterwards.
7. **Agent tooling has grown** (library: shared instructions, memory MCP, MCP router, skills
   router, hooks, sub-agents, RTK, billion-context; MCP tools: web search/fetch, vision,
   image/video, browser, hub). None of it is used by Nerelan executors today.

## 2. Feature map

Decision legend: **REUSE** (use Magpie, retire or never build the Nerelan copy) ·
**WRAP** (Nerelan calls Magpie and adds task-level policy/evidence) · **KEEP** (Nerelan's
own, differentiating) · **EVAL** (worth a trial) · **N/A** (not relevant to Nerelan).

### 2.1 Accounts and quota

| Magpie | Nerelan today | Decision |
|---|---|---|
| `quota [--json]`, `/v1/magpie/quotas` — every subscription, plan and key balance, incl. `limit`, `runsOutAt` | `model_access/magpie.py` reads it; `subscription_quota.py` and `quota_history.py` also parse Codex/Claude CLI logs | **WRAP** Magpie; keep CLI-log parsing only as fallback when Magpie is off |
| `quota history`, `/v1/magpie/quotas/history` (45 days) | `quota_history.py`, `quota_forecast.py` (own estimates) | **REUSE** history from Magpie; keep forecast logic on top of it |
| `quota wait <provider\|account>` | `magpie_wait.py` (bounded adapter) | **WRAP** (done) |
| `accounts switch <agent> next`, accounts discovery/import/alias/refresh | own account selection, cooldowns (`multi_account/*`) | **REUSE** via `account_routing=magpie` once switching is verified (flag never set) |
| Daily check-ins (`accounts checkin`, settings `workbuddyCheckin`/`traeCheckin`/`minimaxCheckin`/`qoderCheckin`) | `reward_claims.py`, `reward_discovery.py` (eligibility only, never claims) | **REUSE**; retire Nerelan's check-in modules; enabling trae/minimax check-ins is an Owner setting in Magpie |
| Subscription warm-up (`codexWarmup`, `claudeWarmup`) | none | **EVAL** (starts 5 h windows early; interacts with Owner pacing rule) |
| `statusline`, `/v1/magpie/statusline` | `claude_statusline.py` (records Claude windows) | **REUSE** for display; keep only if Magpie's misses the `rate_limits` fields Nerelan needs |
| Alerts: `usageAlert`, `balanceAlert`, `resetReminder` | multi-account alerts (toast) | **WRAP**: one alert surface; avoid duplicate toasts |

### 2.2 Routing

| Magpie | Nerelan today | Decision |
|---|---|---|
| Routing groups, 11 strategies, `stays`, nested groups, patterns (`openrouter/*:free`), per-account members (`model#account`) | `model_router.py` chooses concrete bindings; `proven_pool` lock-in; cost-class first | **REUSE** for *which account/provider serves a model*; **KEEP** Nerelan for *which capability tier a task step needs* and task-level budget. Bind Nerelan's tiers to Magpie groups. |
| `auto/<model>` groups found automatically | not used (no `group/` model id anywhere) | **REUSE**: the natural binding target for multi-provider models |
| Group templates (hard→strongest, cheapest-first, never-stuck, plan-first, fastest, spread-evenly) | own policies | **EVAL** "never stuck" + "spread evenly" as defaults for free pools |
| `provider fallback <id> <provider/model>…` | escalation by retry (costs a window retry and a new task) | **REUSE** for account/provider failure; keep Nerelan escalation for *model capability* failure |
| `effort=auto` classifier, group rules by length/image/effort/agent | difficulty from the planner | **EVAL** (could replace part of difficulty→model mapping) |
| `groupFirstToken`, `groupPatience`, `refusalRetries`, `retryAfterCap`, `noLoopGuard` | 900 s stall detector after the fact | **REUSE**: set these so refusals fail over in seconds (#1530) |
| `/v1/magpie/route?session=`, `/v1/magpie/trace` | `magpie_usage.py` parses route | **WRAP** (done for route); trace unused — **EVAL** for failure evidence |

### 2.3 Usage and cost

| Magpie | Nerelan today | Decision |
|---|---|---|
| `usage`, `/v1/magpie/usage`, `/v1/magpie/usage/requests` (per request: model asked/sent/served, tokens, `cost_usd`, account, tries, status) | `usage_ledger.py`, `magpie_usage_ingest.py`, `magpie_settlement.py` | **WRAP**: settle every attempt from Magpie's requests by session/task — including refused and stalled attempts (#1531) |
| `sessions` (cost per Claude Code/Codex/OpenCode/Pi session, per day, top models and folders) | none per session | **WRAP**: task cost = its executor session's cost |
| `cost_usd` per request | `pricing.py` (list-price *equivalent* cost) | **KEEP** equivalent cost for comparison; show Magpie's actual cost beside it |
| `otel` export, `noStats` | none | **N/A** for now |

### 2.4 Gateway

| Magpie | Nerelan today | Decision |
|---|---|---|
| OpenAI chat/responses, Anthropic messages, Gemini, images, video, audio, embeddings, rerank, `/v1/decisions`, `/v1/systemone` | executors talk to the gateway through OpenCode | KEEP as is |
| Gateway keys: per-key token/cost limits by day/week/month or N hours, model/account allowlists, concurrency cap, MCP allowlist, read-only, admin | window budget enforced by reservations and reconciliation | **EVAL (high value)**: a short-lived key per task or per window (`gateway-key issue --ttl --tokens --models`) makes the budget a hard gateway limit and attributes usage exactly |
| OIDC exchange for CI, mTLS, https, LAN | none | N/A (Nerelan is local-first; CI makes no model calls) |

### 2.5 Agent configuration

| Magpie | Nerelan today | Decision |
|---|---|---|
| `magpie <agent> <model|field>`, profiles `save/use`, `visible`, `models <agent>` | Nerelan writes per-task OpenCode config and runs Codex/Claude Code CLIs | **KEEP** per-task isolation; do not let a global agent profile change a running task |
| 40+ agents detected; 15 more installable from the Agent page (Kilo Code, Aider, Goose, Antigravity CLI, …) | three executors (OpenCode, Codex, Claude Code) | **EVAL** — candidate list for the agent × model bake-off (#1527) |

### 2.6 Library (written into every agent)

| Magpie | Nerelan today | Decision |
|---|---|---|
| Shared instructions | per-task prompt envelope | **KEEP** task prompts; do not mix global instructions into governed tasks without review |
| Memory (MCP `/mcp/magpie/memory`, shared across agents) | durable context packet per task; supervisor memory | **EVAL** — must not leak across tasks/goals; Nerelan context stays authoritative |
| MCP servers + MCP router; skills + skills router; hooks; env vars; sub-agents; Claude plugins; project skills | none for executors | **EVAL** per item; sub-agents relate to #1508 multi-agent design |
| RTK (shell output compression for agents) | none | **EVAL (cost)** — directly reduces executor tokens (#1504) |
| billion-context (summarises long agent conversations) | `context_builder.py` compaction levels for the task packet | **EVAL (cost)** for executor sessions; does not replace the task packet |

### 2.7 Tools (MCP)

| Magpie | Nerelan today | Decision |
|---|---|---|
| web search / fetch, vision, image & video generation, browser, tool hub, MiniMax tools | none | **EVAL** when a task kind needs them; never default-on for governed code tasks |

### 2.8 Privacy, operations, plugins

| Magpie | Nerelan today | Decision |
|---|---|---|
| Desensitization (`redact*`: secrets, personal info, custom words — masked before leaving, restored on return) | secret redaction in evidence only | **EVAL** — protects prompts going to free third-party models |
| backup/restore, sync (WebDAV/S3/GitHub), daemon, update channel, healthcheck, profiling | `magpie_launch.py` (start + health) | KEEP launch; the rest is Magpie's own operations |
| Provider plugins (Raccoon, MiniMax Code, OpenCode Zen Free, Qoder, Trae, WorkBuddy, ZCode) | consumed as bindings | REUSE (Qoder and Trae Global installed but not signed in) |

## 3. What stays Nerelan's own (differentiation)

Goals and plans, Owner windows and authority, admission and budgets *per task*, isolated
workspaces, durable execution and recovery, deterministic functional validation, independent
review, the landing gate and evidence chain, supervisor control. Magpie has no notion of a
task, a repository change, acceptance, or review; it is the model/account substrate.

## 4. Actions (each goes to its existing owner Issue)

1. Account/provider selection to Magpie: verify switching, then enable
   `account_routing=magpie`; bind Nerelan tiers to `auto/<model>` or Nerelan-owned groups;
   set `groupFirstToken`/`groupPatience`/`retryAfterCap`. → #1170, #1530, #1533
2. Settle every attempt from Magpie requests/sessions, refused and stalled ones included. → #1531, #1342
3. Enable Trae and MiniMax daily check-ins (Owner setting in Magpie); retire
   `reward_claims.py`/`reward_discovery.py`. → #1342
4. Trial a per-task short-lived gateway key with a token cap. → #1342
5. Trial RTK and billion-context on OpenCode executor sessions for token cost. → #1504
6. Add the 15 installable agents to the bake-off candidate list. → #1527
7. Retire or demote duplicates once the Magpie path is live: `quota_history.py`,
   `subscription_quota.py` (fallback only), `claude_statusline.py`, `reward_*`. → #1170
