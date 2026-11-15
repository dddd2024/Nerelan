# E. Cost, usage attribution, observability and host self-protection

Study date 2026-11-15. Checkout `F:/nerelan/.claude/worktrees/handover-docs-continue-9ae221` at `e0489d5a`, read-only. Defects covered: **D3**, **D6**, **D9**, with a small part of D1.

## 0. What Nerelan does today (the baseline being judged)

- **Ledger** (`reverse_agent/platform_v1/usage_ledger.py`, 379 lines). It normalizes OpenCode, Codex and Claude Code usage into five exclusive counters: `input`, `cache_read`, `cache_write`, `output` and `reasoning`. The window is charged in "cost-equivalent units" using **fixed** weights `COST_EQUIVALENT_WEIGHTS = {input 1.0, cache_read 0.1, cache_write 1.25, output 1.0}` (lines 34-40). `task_token_records` reads only the `OK_STATUSES` and `FAILED` tasks (lines 26 and 129-130). Interrupted, blocked and retired attempts never appear in per-attempt cost.
- **Settlement** (`control_store.py`, about lines 2590-2730). If an attempt has no usage observation (`not observations` and not a fixture), the result is `usage_unknown = True`. In an Owner window the window is then charged `max(reserved_token_units, partial)` (the `owner_charge` branch, Owner decision 2026-11-08). Claim retirement and goal rebind also set reservations to `UNKNOWN` (lines 1275 and 1403). This is exactly **D3**. A 429-refused attempt that consumed zero tokens is charged its full reservation, because nothing proves it was zero.
- **Quota estimates** (`quota_reservation.py`, 403 lines). It admits work against provider quota windows, settles, and runs delta calibration. Its output is an estimate, and the docstring says so (line 218 onward).
- **Magpie ingest** (`magpie_usage_ingest.py`, 599 lines). It reads Magpie's per-request CSV. Attribution to attempts uses a time window plus the agent name, "only when exactly one attempt matches" (lines 359-372). `AGENTS_BY_EXECUTOR` lists only `codex` and `claude_code`, so **OpenCode, the main executor, is never attributed**. The capability map also cites a `magpie_settlement.py`, but that file is **not found** in this checkout.
- **Pricing** (`reverse_agent/model_access/pricing.py`). This is already reuse: a vendored models.dev snapshot (MIT) with `cache_read` and `cache_write` prices per model. It is used only for "equivalent cost", **not** for the window charge.
- **SQLite** (`run_store.py`, lines 240-330 and 452-460). One connection is opened with `check_same_thread=False` and WAL. Every call goes through `_LockedConnection` and `_LockedCursor`, serialized by one `RLock` (the #1528/#1529 fix).
- **Host start** (`scripts/windows/Install-HostAutostart.ps1`). A Startup-folder shortcut runs `Start-NerelanAtLogon.ps1`. The script header says explicitly "No scheduled task, service, registry". There is **no restart and no crash capture** (D6, #1528). `faulthandler` is not used anywhere in `reverse_agent/`.
- **Magpie map** (`docs/architecture/MAGPIE_CAPABILITY_MAP.md` §2.3-2.4). Magpie already offers `/v1/magpie/usage/requests`, which gives per request the model asked, sent and served, tokens, `cost_usd`, account, tries and status. It also offers `magpie sessions` (cost per agent session), an `otel` export and `noStats` (marked N/A), and **gateway keys** with per-key `--tokens`/`--cost` limits and `gateway-key issue --ttl`. Map actions 2 and 4 already point at #1531 and #1342.

---

## 1. Langfuse

**What it is.** LLM tracing, cost and eval platform. TypeScript server, with Python/JS SDKs that are OpenTelemetry-based.
- **Licence:** MIT, except the `ee/` directories, which have their own licence ([LICENSE](https://github.com/langfuse/langfuse/blob/main/LICENSE)).
- **Maintenance:** very active. v4.80.0 shipped 13 Nov, v4.79.0 12 Nov and v4.78.0 10 Nov ([releases](https://github.com/langfuse/langfuse/releases)). Langfuse Cloud becomes v4-only on 2026-11-16, and self-hosted v3 gets security patches until January 2027 ([v4 changelog](https://langfuse.com/changelog/2026-08-17-langfuse-v4)).
- **Windows/local fit: poor.** Self-hosting needs Langfuse Web plus Worker, PostgreSQL, ClickHouse, Redis/Valkey and S3/blob storage ([self-hosting](https://langfuse.com/self-hosting)). On this host that means Docker Desktop with four stateful services. Langfuse Cloud would ship prompts and code off-host, which conflicts with local-first.

**D3 (charging by evidence).** Langfuse distinguishes **ingested** cost (`cost_details` you send) from **inferred** cost (usage × model price). "Ingested costs take priority over inferred ones", and it "no longer estimates usage from text": no usage means no cost ([token & cost tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking)). That is the right principle for D3: missing evidence gives *no number*, never a guess. It does not settle budgets, though, so it cannot replace the window charge.

**D9 (cache and per-attempt cost).**
- `usage_details` uses **mutually exclusive buckets**: "each token must be counted in exactly one key". `input` excludes `input_*` keys such as `cache_read_input_tokens`.
- **Model definitions** match on a `match_pattern` regex and carry a price per usage type. **Pricing tiers** have conditions, such as `input > 200000`, or `service_tier` matching `fast`.
- Usage arriving as OTel `gen_ai.usage.*` is normalized by subtracting cache reads and writes from `input` ([same page](https://langfuse.com/docs/observability/features/token-and-cost-tracking)).
- Nerelan's five counters already follow the exclusive-bucket rule.

**Verdict: COPY-DESIGN (now). Optional REPLACE of the viewer only (later).**
- Copy two rules into the window charge: (a) ingested cost beats inferred cost, and (b) per-model, per-bucket prices instead of global weights.
- Do not run Langfuse as a dependency: the ops burden (four services) is too high for the gain.
- If the Owner later wants trace UIs, point Magpie's existing `otel` export at a Langfuse instance. That needs zero Nerelan code.
- Cost: about 0.5 day for the design copy. A self-hosted instance would add a permanent Docker stack.

## 2. Helicone

**What it is.** Proxy-based LLM observability: an AI gateway plus logging, in TypeScript/Rust.
- **Licence:** Apache-2.0 ([repo](https://github.com/Helicone/helicone)).
- **Status:** Mintlify acquired it on 2026-03-03, and the product is in **maintenance mode**: security updates, bug fixes and new models, with no stated new features ([Helicone post](https://www.helicone.ai/blog/joining-mintlify), [Mintlify post](https://mintlify.com/blog/mintlify-acquires-helicone)).
- **Self-host:** Docker compose (`helicone-compose.sh`).

**D3/D9 mechanism.** Attribution travels on **request headers**: `Helicone-Property-<Name>`, `Helicone-User-Id` and `Helicone-Session-Id` ([custom properties](https://docs.helicone.ai/features/advanced-usage/custom-properties)). Cost is then aggregated per property or session. This is the "join key travels with the request" design that Nerelan lacks today, where the ingest guesses by time window.

**Verdict: KEEP (do not adopt).** It sits in maintenance mode, and Magpie already occupies the proxy position. Adding a second proxy would double the hop and the failure surface. The header-as-join-key idea is covered better by a per-attempt Magpie gateway key (§6). Cost: none.

## 3. OpenTelemetry GenAI semantic conventions and OpenLLMetry

**What they are.**
- **OTel GenAI semconv** defines span and metric attributes for LLM calls. Every attribute is still at **Development** status. The attribute registry now redirects to the dedicated GenAI conventions repo, and the schema links reference v1.41.0 ([registry](https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/)).
- Key attributes: `gen_ai.usage.input_tokens` ("should include all input token types", so cached tokens are **included**), `gen_ai.usage.output_tokens` (includes reasoning), `gen_ai.usage.cache_read.input_tokens`, `gen_ai.usage.cache_creation.input_tokens`, `gen_ai.conversation.id` and `gen_ai.agent.id`. **No cost attribute is defined.**
- **OpenLLMetry** (Traceloop) instruments SDKs in Python. Licence Apache-2.0 ([repo](https://github.com/traceloop/openllmetry)). The latest release found is 0.62.x, with 0.62.0 dated 2026-06-28 ([newreleases](https://newreleases.io/project/github/traceloop/openllmetry/release/0.62.0)). ServiceNow acquired Traceloop on 2026-03-02, and Traceloop says OpenLLMetry stays open source (per the search summary; the primary post was not fetched).

**D9.** The cache attributes give a standard vocabulary. The trap is that OTel's `input_tokens` is *inclusive* of cache, while Nerelan's `input` and Anthropic's `input_tokens` are *exclusive* ([Anthropic caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)). Any export must therefore emit `input + cache_read + cache_write` as `gen_ai.usage.input_tokens`.

**Verdict.**
- **KEEP (not adopted): OpenLLMetry.** Nerelan makes no SDK model calls itself, because executors are external CLIs. There is nothing to instrument in-process.
- **COPY-DESIGN: semconv names.** Use them only if Nerelan ever exports per-attempt usage, and name the ledger's export fields after them.
- The cheaper path to OTel is Magpie's own `otel` export, which sits where the requests actually flow.
- Cost: about 0 now; about 0.5 day for an exporter if one is ever wanted.

## 4. LiteLLM (attribution angle only)

**What it is.** Python gateway and SDK.
- **Licence:** MIT for the core, with an enterprise directory separate (not re-verified this session).
- **Maintenance:** very active. v1.109.0 stable notes were updated 2026-11-11 ([release notes](https://docs.litellm.ai/release_notes/v1.109.0/v1-109-0.md)).

**D3/D9 mechanisms** ([spend tracking](https://docs.litellm.ai/docs/proxy/cost_tracking)):
- **Virtual keys** carry `user_id`, `team_id`, `max_budget`, `budget_duration` and `budget_reset_at`.
- Every request writes a `LiteLLM_SpendLogs` row with `spend`, tokens, the hashed key, `request_tags` (from `metadata.tags` or the `x-litellm-tags` header), `end_user` and `spend_logs_metadata` (`x-litellm-spend-logs-metadata`).
- The response header `x-litellm-response-cost` returns the cost per request.
- The docs warn that the body `user` field is self-declared, so they recommend **issuing keys bound to the identity** for trustworthy attribution. That is the same design as a Magpie per-attempt key.
- Zero-priced requests with usage are logged with `spend = 0` and counted by `litellm_zero_cost_requests_total`. The page does **not** say how failed requests are charged ("not found").
- **Cache pricing:** `cache_read_input_token_cost` and `cache_creation_input_token_cost` per model. The worked example splits 112k prompt tokens into 12k fresh plus 100k cache-read plus 800 output, which costs $0.185 ([custom pricing](https://docs.litellm.ai/docs/proxy/custom_pricing), [model cost map](https://docs.litellm.ai/docs/proxy/model_cost_map)).

**Verdict: COPY-DESIGN.** The pattern to copy is "a key per accountable unit, a spend log per request, a budget on the key". Magpie already has the key and the request log (§6), so no LiteLLM runtime is needed. Its price map is not needed either: `pricing.py` already vendors models.dev with `cache_read` and `cache_write`. Cost: none beyond §6.

## 5. Cache pricing and how to measure a cache hit (D9)

Current facts:
- **Anthropic:** 5-minute cache write is 1.25×, 1-hour write is 2×, and a cache read is 0.1× of base input. The read rate is **0.05× for Opus 5.5 / Sonnet 5.5** and 0.025× for Fable/Mythos 5.x. `input_tokens` is exclusive: total = `cache_read + cache_creation + input` ([prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).
- **OpenAI:** caching is automatic above 1,024 visible input tokens. A cache read costs 0.1× for GPT-5.6+ (0.05× for GPT-6.1 Sol/Terra) and is model-dependent before that. `prompt_cache_key` helps route requests to the same cache. `cached_tokens` is reported inside the input details and is *inclusive* in input ([OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)).

**Consequence for Nerelan.**
- `COST_EQUIVALENT_WEIGHTS["cache_read"] = 0.1` is wrong by 2-4× for current Claude models, and wrong in different ways per vendor. The per-model ratio is already in `pricing_snapshot.json`.
- The cache-hit metric should be `cache_read / (input + cache_read + cache_write)` per attempt and per binding. All three counters already exist in `binding_token_totals`. It just isn't reported.
- The #1504 run had 9.6M input and 0 cache reads. A per-binding hit rate of 0 is the signal that a route has no caching, or that rotation is breaking prefix affinity. Magpie's `stays=auto` exists to keep that affinity (map §1.1).

**Verdict: COPY-DESIGN**, in the Langfuse style: derive each counter's weight per model from the vendored price snapshot (`price[bucket] / price["input"]`), falling back to today's constants. Add hit rate and cost per attempt to the window report. Cost: about 1 day, inside `usage_ledger.py` and the report code. No new runtime.

## 6. Magpie (already a dependency): per-request cost and gateway keys

Facts are from the map, inventoried 2026-11-14 on 0.1.4074, and were not re-verified live: `magpie` is not on PATH in this shell.
- **Per request:** `/v1/magpie/usage/requests` gives status, tries, served model, account, tokens and `cost_usd`.
- **Per session:** `magpie sessions` gives cost per OpenCode/Codex/Claude Code session.
- **Gateway keys:** per-key token and cost limits, `--ttl`, and model/account allowlists.

**D3.**
- A refused (429) or stalled attempt *does* leave request rows at the gateway, with a status and tokens that are often 0. If each attempt runs under its **own short-lived gateway key**, settlement becomes exact: sum the rows for that key. Zero rows with a gateway-side refusal status is evidence of zero spend. Only "no rows and no key data" stays UNKNOWN.
- The key also makes the token budget a **hard gateway cap** instead of a post-hoc reservation.
- OpenCode's per-task config already puts a per-attempt lease into `apiKey` (`opencode_executor.py` lines 405-418). A Magpie key would ride the same slot.

**D9.** Magpie's per-request rows give served model and cache tokens for OpenCode attempts, which the ingest currently cannot attribute at all.

**D1 (side benefit).** Request rows with `tries` and a refusal status show *why* an attempt was silent.

**Not verified.** Whether `/v1/magpie/usage/requests` exposes the gateway-key id per row, and whether it reports cache-read tokens for OpenAI-compatible routes, were **not found** in the map. Both must be checked before building.

**Verdict.**
- **REPLACE:** the attribution heuristic in `magpie_usage_ingest.py` (the about 240 lines of time-window matching from line 359 on), and the D3 fallback charge path in `control_store.py` (`owner_charge`) for Magpie-routed attempts.
- **KEEP:** the window and goal budget *policy*, the reservation as an admission bound, and `quota_reservation.py` forecasts. Magpie has no notion of a task or window (map §3).
- **KEEP:** `pricing.py` equivalent cost beside Magpie's `cost_usd`, as the map already decided.
- Cost: about 2-3 days. No new runtime.

## 7. Host self-protection: supervision, crash capture, SQLite (D6)

### 7.1 Supervisors

**NSSM 2.24**
- **Status:** last release dated 2014-08-31. The 2.25 builds are pre-releases. The official bug page lists 2.24 defects on newer Windows, such as needing `AppNoConsole` and a thread-handle leak on restart ([bugs](https://nssm.cc/bugs)).
- **Mechanism:** the `AppExit` registry values choose per exit code among `Restart` (default), `Ignore` and `Exit`. `AppThrottle` defaults to 1500 ms; `AppRestartDelay` sets the restart delay ([changelog](https://git.nssm.cc/nssm/nssm/src/be6863ff7b79067b0bf6716bfcb022c99cfeec86)).
- **Verdict:** COPY-DESIGN of the semantics only. The tool is stale.

**WinSW**
- **Licence and status:** MIT. v2.12.0 is the stable release; v3.0.0-alpha.11 is a pre-release ([releases](https://github.com/winsw/winsw/releases)). It is a single .NET exe plus an XML file with `onfailure` restart actions and log roll.
- **Fit problem:** a Windows **service** runs outside the logged-on user's session. Nerelan's executors use the user's CLI logins (OpenCode, Codex, Claude Code), and Magpie runs as a user app. Running the service as that user needs the account password stored in the service configuration, which is a credential operation (R3).
- **Verdict: not now.**

**Task Scheduler**
- `RestartOnFailure` retries a task that fails "for any reason" ([schema](https://learn.microsoft.com/en-us/windows/win32/TaskSchd/taskschedulerschema-restartonfailure-settingstype-element)).
- Community reports say a started program's **non-zero exit is still logged as success**, so the restart never fires ([serverfault mirror](https://kiwix.lema.org/serverfault.com_en_all_2023-11/questions/936459/powershell-script-won-t-restart-on-failure)).
- **Verdict:** not reliable as the only watchdog.

**Recommended: COPY-DESIGN.**
- Turn `Start-NerelanAtLogon.ps1` into a small supervision loop in the user session. It already starts at logon with the user's logins.
- Loop behavior: restart on any non-zero exit with NSSM-style throttling (exponential backoff, and give up after N crashes in M minutes with a toast or receipt). Write an exit-record line (time, exit code, last faulthandler file) that the host reads on boot, and log a `host_restart` receipt.
- Recovery after a restart is already the job of durable execution and claim retirement. D4 and D5 cover those gaps.
- Cost: about 1 day of PowerShell. No new runtime and no Owner-level system change.

### 7.2 Crash capture

**faulthandler**
- `faulthandler.enable(file=..., all_threads=True)` dumps every thread's Python traceback on SIGSEGV, SIGABRT and similar. Since 3.6 it also installs a handler for **Windows exceptions**.
- `dump_traceback_later(timeout, repeat=True)` is a built-in hang watchdog.
- The `file` must stay open, so use a dedicated log file, not a rotated one.
- `-X faulthandler` or `PYTHONFAULTHANDLER` enables it at startup.
- `register()` (dump on demand) is **not available on Windows** ([docs](https://docs.python.org/3/library/faulthandler.html)).
- **Verdict: REPLACE/adopt (stdlib).** Use `-X faulthandler` plus an explicit file in host startup. Cost: about 1 hour.

**WER LocalDumps**
- Setting `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe` with `DumpType=2` and `DumpFolder` produces full minidumps of native crashes, such as the `_json.scanstring_unicode` crash of #1528 ([WER settings](https://learn.microsoft.com/en-us/windows/win32/wer/wer-settings), [collecting user-mode dumps](https://learn.microsoft.com/windows/win32/wer/collecting-user-mode-dumps)).
- This is an HKLM system setting, so the **Owner** must apply it.
- **Verdict: adopt, Owner-applied.** Cost: one registry entry.

### 7.3 SQLite threading

- Python docs: with `check_same_thread=False` "write operations may need to be serialized by the user". DB-API `threadsafety` is 3 (serialized) only when SQLite is compiled serialized ([sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)).
- Even in serialized mode, the Python-level `Connection`/`Cursor` objects and transaction state are shared. A `BEGIN IMMEDIATE ... COMMIT` on a shared connection is only atomic if one thread holds the lock across it.
- The established patterns are (a) one connection per thread (`threading.local`) with WAL and `busy_timeout`, or (b) a single serialized proxy.
- Nerelan chose (b) (`_LockedConnection`, #1529). It is correct as long as multi-statement transactions hold `store._lock` throughout, as `rebind_goal_to_window` does.
- **Verdict: KEEP (b).** Add a test that greps for `BEGIN` outside `with self._lock`. Consider per-thread **read-only** connections later if lock contention appears; WAL allows concurrent readers. Cost: about 0.5 day.

---

## Top 3 actions for Nerelan (area E)

1. **Per-attempt Magpie gateway key, with settlement from Magpie request rows.** Removes **D3** (refused or stalled attempts settle at their real, often zero, spend instead of the full reservation as UNKNOWN). Gives exact per-attempt cost for OpenCode for **D9**. Adds refusal evidence for **D1**, and makes the token budget a hard gateway cap.
   - **Shrinks/replaces:** the time-window attribution in `magpie_usage_ingest.py` (lines 359 onward); the `owner_charge` and `usage_unknown` fallback in `control_store.py` settlement (about lines 2590-2730) for Magpie-routed attempts; the UNKNOWN marking on retire/rebind (lines 1275 and 1403) once rows prove zero.
   - **Prerequisite:** check that request rows carry the key id and cache tokens.
   - Design copied from LiteLLM virtual keys and spend logs, and Helicone session headers.
2. **Host supervision and crash capture.** The logon script becomes a supervision loop with restart, throttle, a crash-loop cap and a `host_restart` receipt; startup adds `-X faulthandler` with a dedicated file and `dump_traceback_later` as a hang watchdog; the Owner sets WER LocalDumps for `python.exe`. Keep the serialized SQLite proxy and add a lint test for unlocked transactions.
   - Removes **D6** (#1528 no restart, crash invisible).
   - **Touches:** `scripts/windows/Start-NerelanAtLogon.ps1`, `Install-HostAutostart.ps1` and the host entrypoint. **Keeps:** `run_store._LockedConnection`.
   - No new runtime. NSSM, WinSW and Task Scheduler are rejected for the reasons in §7.1.
3. **Per-model cache-aware charge, and cache-hit and cost-per-attempt reporting.** Replace the fixed `COST_EQUIVALENT_WEIGHTS` with ratios derived from the already vendored models.dev snapshot (Langfuse model-definition design; ingested Magpie `cost_usd` wins over inferred). Report `cache_read / total_input` and cost per attempt and per binding in the window report, including interrupted and retired attempts that `task_token_records` skips today.
   - Removes the measurement half of **D9** (a zero cache hit becomes visible per route) and makes the budget fair across vendors (0.05× vs 0.1× reads).
   - **Shrinks:** `usage_ledger.py` weight constants. **Extends:** `pricing.py` and the window report.
   - Langfuse and OTel export stay optional, through Magpie's `otel` setting, with no Nerelan code.
