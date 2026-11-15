# Reuse study: what mature projects already solve (2026-11-15)

The Owner asked on 2026-11-15 whether Nerelan can reuse ("抄") open-source agent platforms instead of re-solving their problems. This study compares about 30 projects in five areas against the ten defect classes seen in live runs from 2026-11-13 to 2026-11-15 (D1–D10, listed below). The area reports in this folder hold the evidence, sources and per-project verdicts:

| Area | File | Projects |
|---|---|---|
| A. Account pooling, gateways | [A-pooling.md](A-pooling.md) | Magpie (baseline), one-api, new-api, LiteLLM, Portkey, CLIProxyAPI, sub2api |
| B. Durable execution | [B-durable.md](B-durable.md) | LangGraph, DBOS, Temporal, Restate, Hatchet, Prefect |
| C. Agent runtimes | [C-runtimes.md](C-runtimes.md) | OpenCode, Codex CLI, OpenHands, Goose, Gemini CLI, Cline/Roo, Aider, SWE-agent |
| D. Orchestration, review | [D-orchestration.md](D-orchestration.md) | OpenHands resolver, PR-Agent, AutoGen/AG2, CrewAI, MetaGPT, Open SWE; Devin, Copilot agent, Codex cloud, Jules, CodeRabbit (design only) |
| E. Cost, observability, host | [E-cost-ops.md](E-cost-ops.md) | Langfuse, Helicone, OpenTelemetry GenAI, LiteLLM spend, Windows supervisors |

Area reports were written by research agents with web access on 2026-11-15. Project status was checked live on that date. The supervisor verified these claims against the code:
- `opencode_server_transport.py` exists but `REVERSE_AGENT_OPENCODE_TRANSPORT` defaults to `cli`.
- `magpie_usage_ingest.py` matches only `codex` and `claude_code` executors.
- The OpenCode config written by `build_binding_config_content` sets no `chunkTimeout`, `headerTimeout` or `setCacheKey`.
- The host runs OpenCode 1.19.0.

## Defect classes

| | Defect (live evidence) |
|---|---|
| D1 | Upstream 429 retried silently inside OpenCode → "stall" after 900 s. Also: open request, no reply, no gateway error (#1530) |
| D2 | Credit/billing errors misread; fixed-timer holds; refusals without a reason (#1525, #1521) |
| D3 | Failed attempts charged the full reservation as UNKNOWN; silent window exhaustion (#1531) |
| D4 | Window caps strand goals; goals cannot move; an INTERRUPTED attempt waits for the same rate-limited account |
| D5 | Hand-written SQL status derivation bugs (#1536, #1542, #1543, #1515) |
| D6 | Native host crash; no watchdog or restart (#1529, #1528) |
| D7 | Objective only in a "data" packet → executor no-op (#1532) |
| D8 | Workspaces lack dependencies; long tests look like stalls (#1503) |
| D9 | Cheapest-first lock-in; no prompt caching (0 cache reads on 9.6M input) (#1504, #1533) |
| D10 | Review → repair loop churn and dead end at the round limit |

## Conclusion

**Do not replace Nerelan with another platform, and do not swap the gateway.** No project pools the subscription and free accounts Magpie pools. None has a cross-model review whose independence is proved from the models actually used, or a governed exact-head landing. Those stay Nerelan's own (area D).

**Most of this week's failures come from reimplementing generic mechanisms by hand**, where mature components or designs exist:
- liveness detection by scraping CLI output;
- charging by estimate;
- goal state derived in SQL;
- account holds on fixed timers.

The plan below removes those, in this order.

### P0: stop the silent stalls and blind charging (D1, D2, D3)

1. **OpenCode server transport by default, consuming its retry events** (area C).
   - **Why:** OpenCode's server event stream reports `session.status {type:"retry", attempt, message, next}` and typed `session.error`. `run --format json` prints neither, and OpenCode 1.19 waits the full `retry-after` up to five times with no cap.
   - **What:** extend `opencode_server_transport.py` to act on retry events by holding the account at `next` and ending the attempt early, then make it the default.
   - **Effect:** removes D1 and shrinks `opencode_executor.py` by roughly 1.1k lines.
   - **Issue:** extends #443.
2. **Per-attempt Magpie gateway key plus settlement and refusal detection from Magpie request rows** (areas A, E).
   - **Why:** every Magpie row carries the session, status, error text, account, time to first token and cost. A refused request shows up within about 0.3 s.
   - **What:** charge each attempt by its rows (fixes D3), end a refused attempt in seconds (backs up item 1) and get exact per-attempt cost (D9 measurement). A key with a token cap makes the per-attempt runaway guard a hard gateway limit, which fits the Owner decision of 2026-11-15 (#1538).
   - **Before building:** check that rows carry the key id and cache tokens.
   - **Issue:** #1531.
3. **One table-driven upstream error classifier**, copying the designs of new-api, one-api and LiteLLM (area A).
   - **What:** classify rate limit, quota exhausted, credits/402, auth, model gone and overload. Holds use the upstream reset time. Credits and auth stay disabled until a probe succeeds, so `pool_verifier` stops re-probing dead 402/403 bindings.
   - **Effect:** replaces the regexes in `quota_guard.py` and `model_availability.py`.
   - **Issue:** #1525.
4. **OpenCode provider config: `timeout`, `headerTimeout`, `chunkTimeout`, and `setCacheKey: true`** for OpenAI-compatible routes. Magpie should also keep one session on one upstream account.
   - **Why:** this removes the hung-final-reply D1 variant and enables prompt caching (D9).
   - **Cost:** small, inside `build_binding_config_content`.
   - **Issue:** #1504 (later parts) and #1530.

### P1: attempts that recover and goals that finish (D4, D7, D8, D10, D6)

5. **Attempt contract copied from Temporal** (area B).
   - **What:** four explicit timeouts (queue wait, per attempt, idle heartbeat, total). Quota, 429 and 402 are non-retryable *on that account*. Progress (the worktree head) is kept, so an interrupted attempt resumes on another account.
   - **Effect:** removes the D4 "waits for the same account" case seen live on 2026-11-15 and the timeout side of D1/D8.
   - **Issue:** extends #120.
6. **Objective in the instruction channel, plus a repo setup hook** (areas C, D).
   - **What:** the Owner objective and an `expected_output` go in the user turn; only third-party content stays "data". A repo-owned setup script runs in each task worktree, as with OpenHands `.openhands/setup.sh`. A deterministic check runs before the model reviewer.
   - **Issues:** #1532, #1503, #793.
7. **Review loop tuning** (area D).
   - **What:**
     - reject only on high or critical findings; low and medium become notes;
     - cap the number of findings;
     - the refreshed review judges the previous findings against the repair's changes, with the same reviewer model where possible;
     - at the round limit, open a Draft PR with the open findings instead of leaving the goal BLOCKED.
   - **Copies:** PR-Agent, CodeRabbit incremental review, Codex P0/P1 policy, OpenHands/Copilot handoff.
   - **Issue:** new.
8. **Host supervision loop and crash capture** (area E).
   - **What:** the logon script restarts the host on a non-zero exit with backoff and a crash-loop stop, and logs a `host_restart` receipt. Start with `-X faulthandler` writing to a file, with `dump_traceback_later` as a hang watchdog. WER LocalDumps for `python.exe` is an Owner-only system setting.
   - **Rejected:** NSSM (stale), WinSW as a service (outside the login session) and Task Scheduler restart (ignores exit codes).
   - **Issue:** #1528.

### P2: shrink the custom engine (D5, D9, D4 window coupling)

9. **Spike DBOS Transact as the goal-level engine** (area B).
   - **What it is:** MIT licence, in-process, a SQLite system database, no server.
   - **What:** model plan → implement → review → repair, with its round limit, as workflows. Unfinished workflows resume on launch.
   - **Effect:** replaces SQL status derivation (`refresh_goal_status`, `runnable_tasks`), the claim and rebind logic, coordinator sweeps and most of the `durable_execution` lease and resume code. Those are the source of D5, the redeploy strand (#1515) and window stranding.
   - **Gaps:** no idle timeout (item 5 covers it) and no supervisor (item 8). Windows is undocumented, so the spike must prove Windows and the existing SQLite store first.
   - **Issue:** new, as a spike with explicit go/no-go criteria.
10. **Route by Magpie groups instead of single accounts** (area A).
    - **What:** enable `account_routing=magpie` after the verification already required by the Owner decision of 2026-11-14. Map tiers to `auto/<model>` or Nerelan-owned groups. Set `groupFirstToken`, `refusalRetries` and `retryAfterCap`.
    - **Effect:** shrinks account holds in `model_router.py` and `quota_guard.py` and the `pool_verifier.py` sweep. Removes D9 lock-in.
    - **Gap:** Magpie has no mid-stream idle timeout; items 1 and 4 cover it.
    - **Issue:** #1533, #1170.
11. **Per-model cache pricing in the cost-equivalent unit** (area E).
    - **What:** the 0.1 cache-read weight from #1504 Part 1 becomes per-model ratios from the vendored models.dev snapshot. Magpie-reported `cost_usd` wins over computed values. Reports include interrupted and retired attempts.
    - **Issue:** #1504.
12. **Dependency upgrades:** LangGraph 1.0.10 → 1.2.x (`TimeoutPolicy` idle timeouts, `RunControl.request_drain()` on redeploy) for the in-task team graph; OpenCode 1.19 → 2.x (caps `retry-after` at 15 min; config keys move under `settings`). Both are R2 dependency changes. Only take them if item 9 does not supersede LangGraph's role.

## What stays Nerelan's own

- the multi-account pool and evidence-based routing policy (on top of Magpie);
- the cross-model review with independence proved from the models actually used;
- exact-head evidence and governed landing;
- the goal and plan model;
- Owner controls (start/stop, continuous run, #1538).

Langfuse (needs Postgres, ClickHouse, Redis and S3), Temporal (a second server), Restate (no Windows binary, BSL), Hatchet (Docker and Postgres) and Prefect (a server) are rejected as dependencies. Their designs are copied where noted.

## Open facts to verify before building

- Do Magpie request rows carry the gateway key id and cache-token counts? (items 2, 11)
- Does OpenCode's `setCacheKey` reach the upstream request body through Magpie? (item 4; one relay capture)
- Magpie `tries` was set on only 1 of 500 rows. Is its in-request failover evidence reliable? (item 10)
- DBOS on Windows with the existing SQLite file. (item 9)
