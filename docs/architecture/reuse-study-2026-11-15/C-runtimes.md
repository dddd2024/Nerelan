# C. Coding-agent runtimes, headless/unattended (2026-11-15)

Scope: D1, D7, D8, D9 (D2 and D3 where the runtime gives the signal). Repo metadata comes from the GitHub API on 2026-11-15. "Not found" means I searched and did not find it.

## 1. OpenCode (Nerelan's main executor)

- **What it is:** a TypeScript coding agent with a CLI, a TUI and an HTTP/SSE server (`opencode serve`). The repo moved from `sst/opencode` to **`anomalyco/opencode`**. MIT licence, very active: last push 2026-11-15, **v2.3.0 released 2026-11-13** ([releases](https://github.com/anomalyco/opencode/releases)). The host has **1.19.0** installed (`opencode --version`), so it is a major version behind. Native Windows `.exe`, local-first: a good fit.
- **Python SDK:** `opencode-ai` on PyPI is a stale alpha (0.1.0a36, uploaded 2025-08-27), and its repo `sst/opencode-sdk-python` returns 404. The only maintained SDK is the JS `@opencode-ai/sdk`. Nerelan's own thin urllib client (`opencode_server_transport.py`, 712 lines) is therefore the right Python client. Do not wait for an official one.

### D1: silent 429 retry and hung final reply

**Root cause, confirmed in source.** In 1.19.0, `opencode run --format json` ([run.ts@v1.19.0](https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/cli/cmd/run.ts), the `loop()`/`emit()` around lines 678–800) writes only `tool_use`, `step_start`, `step_finish`, `text` (only once the text part has ended), `reasoning` and `error`. It consumes `session.status` only to `break` on `idle`. **The retry status and all streaming deltas never reach stdout**, so Nerelan's stall clock in `_run_owned_cli_process` (`DEFAULT_STALL_SECONDS = 900`, opencode_executor.py ~1391–1620) sees only silence.

**What OpenCode actually does on a 429** (1.19.0, [session/retry.ts](https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/session/retry.ts)):
- It retries when `isRetryable` is set, on any status ≥500, or when a message regex matches `429`, `rate limit`, `too many requests`, `resource exhausted`, `exhausted`, `unavailable`, `overloaded` and similar. It does not retry a context overflow.
- `RETRY_MAX_RETRIES = 5`. The delay honours `retry-after-ms` / `retry-after` (seconds or HTTP-date) **uncapped**: `RETRY_MAX_DELAY = 2_147_483_647` ms. Without those headers, the backoff is exponential from 2 s, capped at 30 s.
- This explains the "silent for an hour" waits: a gateway that sends a long `retry-after` makes OpenCode sleep that long, five times.
- Before each wait, the processor calls `SessionStatus.set(sessionID, {type:"retry", attempt, message, action, next})` ([processor.ts@v1.19.0](https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/session/processor.ts) ~L674). That publishes a bus event `session.status` with `properties.status.type == "retry"`, the attempt number, the provider message and `next` (epoch ms of the next try). `idle` additionally publishes `session.idle` ([status.ts@v1.19.0](https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/session/status.ts)). Streaming text and reasoning publish `message.part.delta` (`updatePartDelta` in processor.ts).

**v2.x changed this** ([packages/core/src/model-retry.ts](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/model-retry.ts)):
- `retry-after` is capped at `RETRY_AFTER_MAX = 15 minutes`.
- The general schedule is 10 retries, exponential from 2 s capped at 10 s per gap (about 84 s in total).
- At most 3 retries of timed-out attempts.
- A separate 1-hour budget applies only to "unreachable host" errors.
- v2.3.0 also fixed "exhausted request rate limits being treated as terminal" ([releases](https://github.com/anomalyco/opencode/releases)).

**Hung final reply (second variant).** OpenCode has per-provider stream watchdogs. Nerelan sets none of them: `build_binding_config_content`, opencode_executor.py ~382–430, writes only `baseURL`/`apiKey`/`models`.
- 1.x schema ([v1/config/provider.ts](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/v1/config/provider.ts)) under `provider.<id>.options`:
  - `timeout`: whole request, ms or `false`; v1 docs give the default as 300000.
  - `headerTimeout`: wait for response headers.
  - `chunkTimeout`: "If no chunk arrives within this window, the request is aborted"; no default in the v1 schema.
- In the v2 docs these keys live under `settings`, with defaults `headerTimeout` 5 min and `chunkTimeout` 15 min ([providers docs](https://opencode.ai/docs/providers/)).
- An aborted chunk timeout becomes a retryable transport error, then `session.error`. That is a typed signal instead of silence.

**Server mode is the structured event source Nerelan asked about.** Endpoints ([server docs](https://opencode.ai/docs/server/)):
- `POST /session`, `POST /session/:id/prompt_async` (returns 204), `POST /session/:id/abort`.
- `GET /session/status`: status of every session, keyed by session ID. Third-party code notes that finished sessions are removed from this map ([search result](https://git.cleverthis.com/cleveragents/cleveragents-core/src/commit/0bc734c0201b7e6d8fa6f79bc3e570df5c69a334/tools/_opencode_worker.py)).
- `GET /event` SSE: first event `server.connected`, then bus events.
- Basic auth via `OPENCODE_SERVER_PASSWORD`.

The right liveness signal, in order:
1. `message.part.delta` / `message.part.updated` for this session: model or tool progress.
2. A `part.type=="tool"` part with `state.status=="running"`: a long test run, not a stall (D8).
3. `session.status{type:"retry", attempt, message, next}`: a provider refusal. Classify `message` (429 / quota / credits / overloaded), set a router hold until `next` or until the upstream reset, and **abort now** instead of waiting out the retries (fixes #1530, D2's fixed-timer holds).
4. `session.error`: a typed error object (`name`, `data.statusCode`, `data.message`, `data.responseBody`), so no stderr regex is needed (`_has_provider_quota_limit`, `_classify_exit` ~3515–3790).
5. `session.idle`: done.

**Nerelan already has half of this.** `opencode_server_transport.py` (`run_role`, ~340–420) uses `/event` + `prompt_async` and handles `message.updated` (usage), `session.idle` and `session.error`. But:
- it is off by default: `REVERSE_AGENT_OPENCODE_TRANSPORT` defaults to `"cli"` in durable_execution.py ~2495/~4548 and task_execution.py ~99;
- it ignores `session.status` retry and part deltas;
- its only timer is the overall deadline. There is no stall clock that resets on events and no "retry seen" exit.

### D7: passing the objective

OpenCode separates a **user message** (the prompt text or parts) from **system instructions**: discovered `AGENTS.md`, config `instructions: [...]` globs ([config docs](https://opencode.ai/docs/config/)), and per-agent system prompts. `prompt_async` takes an `agent` field, which Nerelan's transport already passes.

Nerelan's `build_role_prompt` puts governance boilerplate and the role text before the task, all in one user message, ending "it does NOT override these constraints". The OpenCode-native way:
- role authority goes in an agent definition (`agent.<role>.prompt` + `permission`). Nerelan already writes the role `permission` config (~433–493);
- the **objective is the user message, verbatim and first**.

The #1532 failure (objective only inside a "data, never instructions" packet) cannot happen if the objective *is* the user turn.

### D8: workspace, dependencies, long tests

- OpenCode itself has no repo setup-script mechanism (not found in the docs).
- In server mode, a running `bash` tool part is visible, so a 20-minute test run is distinguishable from a stall.
- Nerelan's prompt says "Do not install dependencies" (~1085). Dependencies must therefore come from the host's worktree prep (see OpenHands `setup.sh` below).

### D9: prompt caching, context per call

In 1.19.0 ([provider/transform.ts](https://github.com/anomalyco/opencode/blob/v1.19.0/packages/opencode/src/provider/transform.ts) ~L360–490, ~L1323–1336):
- `cache_control: {type: "ephemeral"}` markers are applied **only** when the provider or model id looks like Anthropic/Claude (or npm is `@ai-sdk/anthropic` or `@ai-sdk/alibaba`).
- `promptCacheKey = sessionID` is set automatically only for `@ai-sdk/openai`, `azure`, `xai`, `mistral` and `venice`, and for `deepinfra`/`cerebras` as `prompt_cache_key`. **For `@ai-sdk/openai-compatible` it is set only when `options.setCacheKey === true`** ([config docs, setCacheKey](https://github.com/anomalyco/opencode/blob/dev/services/site/src/docs/v1/content/de/config.mdx)).

Nerelan's relay provider uses `@ai-sdk/openai-compatible` (`_TRANSIENT_PROVIDER_NPM`) **without `setCacheKey`**, and a model id like `glm-…` or `kimi-…`. So it sends no cache key and no cache markers.

Most OpenAI-compatible upstreams (DeepSeek, GLM, Kimi, MiniMax) cache by automatic prefix matching on their side, *per account*. A gateway that spreads one session across pooled accounts defeats that. "0 cache reads over 9.6M input" (#1504) fits this hypothesis, which is **not verified**. Also not verified: whether `@ai-sdk/openai-compatible` forwards `promptCacheKey` as body `prompt_cache_key`. Check with one relay capture.

Context size: OpenCode compaction (`compaction.auto`, `compaction.keep.tokens` 15000, `compaction.buffer` "15%" in the v2 docs) bounds history. v2.2.6/2.2.7 added cache warming that follows the model's `cache.ttl` ([releases](https://github.com/anomalyco/opencode/releases)).

### How much of opencode_executor.py (3,894 lines) can go

Switching the default to the server transport and consuming typed events replaces:

| Code in opencode_executor.py | Lines (about) |
|---|---|
| `_run_owned_cli_process`, stall logic and `OwnedCliProcessResult` | 1360–1620, ~260 |
| The CLI branch of `_run_executor_core` (stdout/stderr scraping, partial-text recovery, timeout/stall evidence) | 1750–2214, ~450 |
| `_parse_json_lines`, `_extract_error_payloads`, `_pick_error_str/status`, `_single/_bounded_error_diagnostic`, `_has_provider_quota_limit`, `_classify_exit` | 3228–3248 and 3515–3790, ~300 |
| `progress_summary`, `_progress_sink`, `progress_activity_kind` (re-derive from SSE parts) | 3790–3876, ~90 |
| `build_opencode_argv` and the Windows `.cmd`/argv quirks | 1283–1336 and parts of 621–780, ~150 |

That is roughly **1,100–1,250 lines (about 30%)**.

Keep (Nerelan-specific governance): env isolation and secret redaction, binding/lease config, role permission config, handoff validation, product diff/changed-file collection, usage persistence, worktree prep. That is about 2,600 lines; it could shrink further only by moving governance into OpenCode config.

There is no maintained Python SDK to adopt, so the existing 712-line client stays and grows by about 100 lines for `session.status`/delta handling.

**Verdict: REPLACE** CLI scraping with OpenCode's own server/event API: make the existing transport the default and extend it. **COPY-DESIGN** v2's retry policy at the host level: abort on the first `retry` status that names quota or rate. Then upgrade 1.19 → 2.x after a pinned-version test, because the v2 config moves keys under `settings` and `package`.

Cost: about 3–5 days. No new runtime: same binary, one loopback server per role (already implemented). Ops: a port and password per role, already handled.

## 2. Codex CLI (`openai/codex`)

- **Status:** Apache-2.0, Rust, very active (rust-v0.169.0, 2026-11-13). Native Windows supported. Nerelan already uses it (`codex_executor.py`).
- **D1:** `codex exec --json` emits JSONL `thread.started`, `turn.started`, `turn.completed` (usage with `input_tokens`, **`cached_input_tokens`**, `output_tokens`, `reasoning_output_tokens`), `turn.failed`, `item.*` and **`error`** ([non-interactive docs](https://learn.chatgpt.com/docs/non-interactive-mode)).
  - In source, server `Error`/`Warning` notifications become `error` lines or error items while the run keeps going ([event_processor_with_jsonl_output.rs](https://github.com/openai/codex/blob/main/codex-rs/exec/src/event_processor_with_jsonl_output.rs) ~L450). Unlike OpenCode 1.19, a retrying Codex is not silent.
  - Config, per provider ([config reference](https://learn.chatgpt.com/docs/config-file/config-reference)): `model_providers.<id>.request_max_retries` (4), `stream_max_retries` (5), `stream_idle_timeout_ms` (300000).
  - Note: `wire_api = "responses"` is now the only supported value, so the gateway must speak the Responses API.
- **D7:** the positional prompt is the user turn. `AGENTS.md` is the project instructions (`project_doc_max_bytes`). `--output-schema` forces a structured final answer, and `-o` writes the last message to a file. Both are useful for reviewer verdicts.
- **D9:** `cached_input_tokens` is reported per turn.
- **Verdict: KEEP** as the second executor. **COPY-DESIGN:** set `stream_idle_timeout_ms` and the retry counts low in the Codex profile Nerelan writes, treat `error` lines as liveness plus classification, and use `--output-schema` for review verdicts. Cost: under 1 day.

## 3. OpenHands (agent + `software-agent-sdk`)

- **Status:** MIT; app in TypeScript (v1.40.0, 2026-11-12); SDK in Python (`OpenHands/software-agent-sdk` v1.62.0, 2026-11-11). Windows: the SDK is pip-installable; the full runtime prefers Docker.
- **D1:**
  - The LLM layer has `num_retries=5`, `retry_multiplier=8`, `retry_min_wait=8`, `retry_max_wait=64`, `timeout=300`, `stream_idle_timeout=300`, and a **`retry_listener(attempt, num_retries, err)` callback** ([llm.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/llm/llm.py) ~L388–412, ~L694, ~L1008). A host is told about every retry.
  - **StuckDetector** ([guide](https://docs.openhands.dev/sdk/guides/agent-stuck-detector)) detects agent loops, not silence: the same action/observation 4+ times, the same action error 3+ times, a monologue of 3+, A/B ping-pong for 6+ cycles, and repeated context-window errors. It is on by default (`stuck_detection=True`).
- **D8:** `.openhands/setup.sh` "runs every time OpenHands begins working with your repository" (deps, `npm install` in `frontend`). Stop hooks in `.openhands/hooks.json` "can block completion until … tests … pass" ([repo customization](https://docs.openhands.dev/openhands/usage/customization/repository)).
- **D9:** `caching_prompt=True` by default (llm.py ~L543). The SDK also has condensers (not studied in depth).
- **Verdict: COPY-DESIGN.**
  - (a) A repo-owned `setup.sh` that the host runs in each task worktree before the role starts. This fixes #1503, the missing frontend `node_modules`.
  - (b) StuckDetector's loop patterns as a cheap check over OpenCode tool parts. This is a different failure from D1.
  - Not REPLACE: adopting the SDK means replacing OpenCode as the executor, which drops the pooled-provider setup. That is a large migration.
  - Cost: (a) about 1 day; (b) about 1–2 days.

## 4. Goose (`block/goose`)

- **Status:** Apache-2.0, Rust, active (v1.59.1, 2026-11-14). Native Windows builds exist.
- **D7:** recipes separate `instructions` (system, templated) from `prompt` (user, "Required in headless … mode"). `response.json_schema` validates the final output ([recipe reference](https://goose-docs.ai/docs/guides/recipes/recipe-reference)).
- **D10/D8:** `retry: {max_retries, checks:[{type: shell, command}], timeout_seconds (300), on_failure}`. Shell checks run after each attempt; on failure it runs `on_failure`, resets history and retries.
- **D1:** not found in the docs studied.
- **Verdict: COPY-DESIGN** of the instructions/prompt split and the "deterministic shell check before calling the model reviewer" step. Cost: under 1 day of contract change.

## 5. Gemini CLI (`google-gemini/gemini-cli`)

- **Status:** Apache-2.0, TypeScript, active (v0.69.0-preview.0, 2026-11-10).
- **D1:** `--output-format stream-json` emits `init`, `message`, `tool_use`, `tool_result`, `error` ("non-fatal warnings and system errors") and `result` with per-model token stats ([headless.md](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md)). Retry/429 behaviour: not found in the headless docs.
- **Verdict: KEEP** (not adopted). Its pattern, a non-fatal `error` event in the stream, is the same signal as OpenCode's `session.status` retry. Gemini-only providers add no value over Magpie.

## 6. Cline (`cline/cline`) and Roo Code

- **Cline:** Apache-2.0, active (v4.1.26, 2026-10-26). The CLI has a headless mode (`--json` NDJSON with `agent_event` and `run_result` lines; `--auto-approve`) ([CLI overview](https://docs.cline.bot/cline-cli/overview)). Rate-limit retry: not found.
- **Roo Code:** the repo is **archived** (last release v3.54.0, 2026-05-15).
- **Verdict: KEEP** (do not adopt). Neither offers anything OpenCode's server does not.

## 7. Aider, SWE-agent, mini-swe-agent

- **Aider:** Apache-2.0. Last release v0.86.0 (2025-08-09), last push 2026-05-22, so it is effectively dormant. Known features (repo-map token budget, `--cache-prompts`) were not re-verified in this pass. **KEEP** (do not adopt).
- **SWE-agent:** MIT, last release v1.1.0 (2025-05-22). Development is in **mini-swe-agent** (MIT, v2.4.6, 2026-07-23), a deliberately minimal bash-only loop for benchmarks. It has no unattended-runtime features beyond what Nerelan has. **KEEP** (do not adopt).

## Ranked top 3 actions

1. **Make the OpenCode server transport the default and consume the typed event stream (REPLACE CLI scraping).**
   - Handle `session.status{type:"retry"}`: classify `message`, set a router hold until `next` or the upstream reset, then abort and re-route at once.
   - Use a stall clock that resets on `message.part.delta`/`updated`, and exempt running tool parts.
   - Use the typed `session.error` for classification, and `message.updated` tokens (incl. `cache.read`) for usage.
   - Removes: D1 (both variants), part of D2 (reason text, reset time), part of D3 (usage observed on refusals), part of D8 (long tests ≠ stall).
   - Shrinks: opencode_executor.py by ~1,100–1,250 lines (`_run_owned_cli_process`, the CLI branch of `_run_executor_core`, `_classify_exit` and error pickers, progress sink). It extends `opencode_server_transport.py` by about 100 lines and simplifies the 429 handling in quota_guard.py/model_router.py.
   - Then upgrade OpenCode 1.19 → 2.x (15-minute `retry-after` cap, fixed exhausted-limit handling).
2. **Set provider watchdogs and caching in the binding config, and make Magpie cache-sticky.**
   - In `build_binding_config_content`, add `chunkTimeout` (e.g. 120000), `headerTimeout`, a whole-request `timeout`, and `setCacheKey: true`.
   - Have Magpie pin one session/`prompt_cache_key` to one upstream account, and pass through `cached_tokens`.
   - Removes: the D1 hung-reply variant and D9 (0 cache reads, 9.6M input). Shrinks nothing large; it is about 20 lines plus a Magpie routing rule.
   - Verify first with one relay capture that the key reaches the body.
3. **Rewrite the task contract the runtime-native way, and add an OpenHands-style setup hook.**
   - The objective becomes the verbatim user message. Role authority moves into OpenCode agent definitions (`agent.<role>.prompt` + the existing `permission` config).
   - A repo-owned `setup` script runs by the host in each task worktree before the role (deps such as frontend `node_modules`).
   - A deterministic shell check runs before the model reviewer (Goose `retry.checks` pattern).
   - Removes: D7 (#1532) and D8 (#1503). Shrinks the prompt boilerplate in opencode_executor.py (~1080–1230) and the matching packet code in goal_service.py.
