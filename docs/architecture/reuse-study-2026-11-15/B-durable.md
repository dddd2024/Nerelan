# B. Durable execution, workflow and task-queue engines

Scope: D4, D5, D6, plus the timeout side of D1 and D8. Checkout read: `reverse_agent/platform_v1/` at e0489d5a.

## What Nerelan does today

- **Two clocks, both hand-written.** `opencode_executor.py` kills a CLI after `DEFAULT_STALL_SECONDS = 900` with no output (#1473). `durable_execution.py` `_HeartbeatContext` renews a sqlite lease row on a thread, with sleep detection (#1321), BUSY retries and fencing epochs. `executor_timeout_seconds()` caps a turn at 600 s, with a maximum of 3600 s.
- **LangGraph is used for very little.** Within one task, `reverse_agent/workflows/team_graph.py` runs planner→coder→reviewer with `SqliteSaver` (`_make_strict_saver`, `thread_id = run_id`) and one checkpoint file per run. The module docstring says the LangGraph checkpoint holds "only the orchestration cursor": TaskStore is the truth. So two durable stores must agree, and much of the 4.5k lines reconciles them (`_resume_single_pre_planner`…`_resume_from_post_reviewer`, `reconcile_external_operation`, `prevent_duplicate_dispatch`).
- **The goal-level loop is not a program. It is a status derived in SQL.** `control_store.runnable_tasks` is a single query over goal status, task status, the window counters `tasks_started < max_tasks` and `retries_used < max_retries`, expired claims joined to ACTIVE reservations, and a `json_each(dependencies_json)` predecessor check. `refresh_goal_status` rebuilds the review→repair chain from `platform_task_escalations` rows (`model_review_repair:` reason prefix, `step` ordering) to decide whether a FAILED review is "awaiting repair". Only then does it pick RUNNING, COMPLETED or BLOCKED. #1542 and #1543 were both patches to this inference. `goal_service._repair_rejected_reviews`, `escalate_failed_tasks`, `_reroute_quota_held` and `unattended_coordinator._sweep_escalations` re-scan the same rows on a timer.
- **The window is a container, not a policy.** `runnable_tasks` filters `g.window_id = ?`. Window caps gate claims, and moving goals needs `rebind_goal_to_window` or `adopt_standing_goals`. This is the mechanism behind D4.
- **One connection.** `TaskStore` opens one `sqlite3.connect(..., check_same_thread=False)` guarded by an `RLock` that `PlatformControlStore` shares (`self._lock = task_store._lock`). Any path that bypasses the lock crashes natively (D6, #1529). No supervisor exists (#1528).

---

## 1. LangGraph (already a dependency)

- **What it is:** a graph/functional agent runtime with checkpointers. MIT licence. Very active: langgraph 1.2.22 and checkpoint 4.3.2 were released 14 Nov 2026, and 1.2.20 (05 Nov) added a "strict resume mode that refuses stale interrupt answers" ([releases](https://github.com/langchain-ai/langgraph/releases)). Nerelan pins **1.0.10** and `langgraph-checkpoint-sqlite==3.1.0` (`pyproject.toml`). Pure Python, in-process, works on Windows, needs no server.
- **New since 1.0.10, all requiring `langgraph>=1.2`** ([timeout and error handling](https://docs.langchain.com/oss/python/langgraph/timeout-and-error-handling)):
  - `add_node(..., timeout=TimeoutPolicy(run_timeout=..., idle_timeout=..., refresh_on="auto"|"heartbeat"))`. `run_timeout` is never refreshed. `idle_timeout` resets on state writes, stream output and callbacks, or only on `runtime.heartbeat()` when `refresh_on="heartbeat"`. It raises `NodeTimeoutError(kind="idle"|"run")`, which is retryable by default. **Async nodes only:** a sync node with a timeout is rejected at compile time, and the docs suggest `asyncio.to_thread` for blocking I/O.
  - `retry_policy=RetryPolicy(...)` per node. A retry re-runs the whole node, so side effects are at-least-once ("use idempotency keys derived from durable state").
  - `error_handler=` runs after retries are exhausted and returns a `Command` to update state and route. The failure context is checkpointed, so the handler sees the same `NodeError` after a resume.
  - **Graceful drain:** pass `RunControl` as `control=` and call `request_drain()`. Drain stops at a superstep boundary, raises `GraphDrained` and writes a resumable checkpoint. Resume with `invoke(None, config)`.
  - Durability modes are `sync`, `async` and `exit` ([Durability](https://reference.langchain.com/python/langgraph/types/Durability)).
- **What it lacks for Nerelan:** no queue, no claim or worker model, no automatic re-start of unfinished threads after a host restart (the host must find them and call `invoke(None, config)`), and no durable multi-hour timer. Background runs, task queues and cron belong to the separately deployed Agent Server ([persistence page](https://docs.langchain.com/oss/python/langgraph/durable-execution) mentions only that the Agent Server sets up the checkpointer). I did not verify the Agent Server's self-host requirements.
- **D1/D8 (timeouts):** `idle_timeout` plus `refresh_on="heartbeat"`, with run_timeout as a separate setting, is exactly the stall/turn split Nerelan wrote by hand. A long test run would call `runtime.heartbeat()` from the output pump, so it is never mistaken for a stall (D8). It does **not** detect a CLI that silently retries a 429 (D1): from outside that is indistinguishable from thinking, and the fix belongs in the gateway or executor parsing.
- **D4:** partial. A `NodeTimeoutError` → `error_handler` → `Command(goto="pick_other_account")` gives a clean place to re-dispatch an interrupted attempt elsewhere. Window stranding is not addressed.
- **D5:** if the goal loop (implement → review → repair, with a round counter in state) were a `StateGraph` with conditional edges, "awaiting repair" would be a position in the graph, not an inference. `get_state().next` would be the status.
- **D6:** no help. `SqliteSaver` takes a caller-supplied connection, and that is the same hazard.
- **Verdict:** **KEEP + upgrade (1.0.10 → 1.2.x)** for the in-task team graph: adopt `TimeoutPolicy`, `RetryPolicy`, `error_handler` and `RunControl` drain (the drain removes the #1515 redeploy class for that graph). Cost: small. The bump needs the strict-serde check `_check_strict_serde_active` re-verified against checkpoint 4.x, and nodes made async. It is **not** a sufficient goal-level engine on its own, because it has no recovery enumerator, queue or durable sleep.

## 2. DBOS Transact (Python)

- **What it is:** a durable-workflow library that runs in-process. State lives in a "system database" (Postgres or **SQLite**). MIT licence, `requires_python >=3.10` ([PyPI](https://pypi.org/pypi/dbos/json)). Active: 3.5.0 (10 Nov 2026) shipped "SQLite system database/datasource reads run outside the write lock", a more scalable scheduler and suspend support. 3.4.0 (28 Oct) shipped serialized SQLite migrations and the `DBOS.reserve_step` API ([releases](https://github.com/dbos-inc/dbos-transact-py/releases)). SQLite is described as a file that cannot be shared by several servers ([database connection](https://docs.dbos.dev/python/tutorials/database-connection)). That limitation does not matter for Nerelan's single host. **Windows:** not mentioned in the docs or the last three releases (not found). It needs no server process.
- **Mechanisms** ([workflows](https://docs.dbos.dev/python/tutorials/workflow-tutorial), [steps](https://docs.dbos.dev/python/tutorials/step-tutorial), [queues](https://docs.dbos.dev/python/tutorials/queue-tutorial), [contexts](https://docs.dbos.dev/python/reference/contexts)):
  - **Recovery:** on launch, DBOS resumes every workflow left `PENDING` from its last completed step. Completed steps are never re-run, and steps run at least once. Workflows that exceed their recovery attempts land in `MAX_RECOVERY_ATTEMPTS_EXCEEDED`. `DBOS.resume_workflow` and `DBOS.fork_workflow(workflow_id, start_step)` restart from a chosen step under a new ID.
  - **Retries:** `@DBOS.step(retries_allowed=True, interval_seconds=1.0, max_attempts=3, backoff_rate=2.0)` gives exponential backoff and raises `DBOSMaxStepRetriesExceeded` to the workflow. `timeout_seconds` covers **async steps only** and raises `DBOSStepTimeoutError` per attempt.
  - **Timeouts:** `SetWorkflowTimeout(s)` measures start to completion, starts at dequeue, is stored durably, and cancels the workflow **and its children** with status `CANCELLED`.
  - **Child workflows:** start them from inside a workflow and await their handles. Cancellation cascades (`cancel_workflow(..., cancel_children=True)`).
  - **Signals and timers:** `DBOS.send`/`recv(topic, timeout_seconds)` and `set_event`/`get_event`. `DBOS.sleep(seconds)` is durable across restarts. `suspend=True` requires DBOS Enterprise.
  - **Queues:** `worker_concurrency`, `global_concurrency`, `limiter={"limit","period"}`, priority, and `deduplication_id`. **Partitioned queues** set `partition_concurrency`/`partition_limiter` per `queue_partition_key`. `listen_queues` restricts which queues a process dequeues from.
  - **Idempotency:** `SetWorkflowID` makes the ID an idempotency key ("executes only once"). `workflow_id_reuse_policy="reject"` makes a reused ID raise `DBOSWorkflowIDInUseError`.
- **D4:** the goal becomes a workflow, not a window member. A window cap becomes a durable wait (`recv("budget_grant", timeout_seconds=...)` or `DBOS.sleep`) instead of a strand. It survives reboot because it is a database row. An interrupted attempt is one step. On failure or timeout the workflow code chooses another account and enqueues the next attempt with `queue_partition_key=<account>`, so one account's rate limit (`partition_limiter`) never blocks the others.
- **D5:** the plan → implement → review → repair loop is ordinary Python: `for round in range(max_rounds): impl = child(implement); verdict = child(review); if ACCEPT: break; ...`. The workflow status (`PENDING`, `SUCCESS`, `ERROR`, `CANCELLED`) and the step log replace `refresh_goal_status`, `runnable_tasks`' dependency subquery and the escalation-chain reconstruction. The #1542/#1543/#1536 class of bug cannot arise from status inference, because nothing infers status.
- **D6:** DBOS owns its system-DB connections through SQLAlchemy, and 3.5.0 moved reads out of the write lock. Nerelan's own TaskStore connection problem remains unless TaskStore also moves to per-thread connections. DBOS gives automatic resume after a crash, but **no supervisor** (not found). A Windows service wrapper is still needed (not studied here).
- **D1/D8:** a run cap exists (step `timeout_seconds`), but **no idle or heartbeat timeout** was found in the docs, so the stall clock stays custom or comes from LangGraph `TimeoutPolicy`.
- **Fit risks:**
  - It adds a second sqlite file beside TaskStore. Nerelan's receipts, budgets and governance must remain in TaskStore, so steps must write there idempotently, keyed on the DBOS workflow and step ID.
  - Agent CLI steps are at-least-once on recovery. That does **not** satisfy Nerelan's external-operation contract by itself: a PENDING journal entry or unknown remote completion must remain parked, never automatically replayed. A workflow id or retained workspace does not deduplicate a remote CLI/reviewer call. Retain TaskStore operation identities, journal checks, lease epochs and fencing until equivalent behavior is proved.
  - Workflow code must be deterministic across replays, with all I/O in steps.
  - It is a new dependency with SQLAlchemy and migrations.
- **Verdict:** **REPLACE (staged, after a spike)**:
  - **Candidates after the spike:** SQL goal-status derivation, dependency scheduling and escalation bookkeeping in `control_store.py`, `unattended_coordinator.py` and `goal_service.py`. The spike must prove crash-before-dispatch, crash-after-remote-call-before-recording, stale lease ownership, cancellation and unknown-completion behavior before replacing corresponding claim, fencing or resume controls. No deletion is justified solely by DBOS workflow recovery.
  - **Keep:** TaskStore external-operation journals, UNKNOWN isolation, lease fencing, account-quota reservations, receipts, landing and governance until equivalent protections pass those tests. Continuous Owner windows follow #1538; delegated/trusted-policy bounds remain unchanged.
  - **Cost:** a 1–2 week spike to put one goal type end to end through DBOS, then a migration of several weeks. No new process and no Postgres. The ops burden is one more sqlite file plus DBOS migrations.

## 3. Temporal (server + Python SDK)

- **What it is:** a durable-execution server plus SDKs. Both are MIT. The Python SDK is very active: 1.36.1 on 14 Nov 2026, and 1.36.0 dropped Python 3.10 so it needs **3.11+** ([releases](https://github.com/temporalio/sdk-python/releases)). Local option: `temporal server start-dev --db-filename <file>` gives persistent, SQLite-backed state (`--sqlite-pragma`). The docs say "the development server is not intended for production use" and give no Windows notes ([CLI server](https://docs.temporal.io/cli/server)). Production self-hosting means a cluster on Postgres, MySQL or Cassandra.
- **Mechanisms** ([activity failures](https://docs.temporal.io/encyclopedia/detecting-activity-failures)):
  - Four activity timeouts: `Schedule-To-Close`, `Start-To-Close` (per attempt, and the docs say to always set it), `Schedule-To-Start` (time waiting in the queue, non-retryable) and `Heartbeat Timeout`.
  - A missed heartbeat fails the attempt. The retry goes back to the task queue, where any worker can pick it up. Heartbeat **details** carry progress, so the next attempt resumes from the saved payload.
  - `RetryPolicy` sets initial interval, backoff coefficient, maximum attempts and non-retryable error types.
  - Child workflows, signals, durable timers and per-worker task queues are built in.
  - The LangGraph integration (`temporalio-langgraph`) maps nodes to activities with `execute_in="activity"`. It is **Public Preview** and uses Temporal's `RetryPolicy` in place of LangGraph's ([integration](https://docs.temporal.io/develop/python/integrations/langgraph)).
- **D4:** best-in-class. Run one task queue per account (or a pool worker): on a heartbeat timeout or a 429-classified failure, the workflow schedules the next attempt on another account's queue. `Schedule-To-Start` shows when a queue is starved.
- **D5:** the same as DBOS. The loop is code, and status is the workflow state.
- **D6:** the server process isolates the state, and workers can crash freely. A supervisor is still needed for the server and the workers.
- **D1/D8:** the cleanest taxonomy, separating queue wait, per-attempt cap, idle heartbeat and total cap. Heartbeats driven by CLI output events give the same stall semantics as today, and test-runner output keeps them alive.
- **Verdict:** **COPY-DESIGN**. Adopting it means a second long-running server on Windows that is not production-supported in dev mode, deterministic-workflow rules and a Python 3.11 floor, which is too heavy for a local-first host. Copy the four-timeout taxonomy, heartbeat-details progress, non-retryable error types, and "retry goes to the queue, not to the same worker".

## 4. Restate

- **What it is:** a durable-execution server written in Rust. The server is under **BSL 1.1** (it becomes Apache-2.0 four years after each release; offering a public Restate platform service is excluded) ([LICENSE](https://github.com/restatedev/restate/blob/main/LICENSE)). Latest v1.8.1, 21 Oct 2026. Pre-built binaries exist "for MacOS and Linux" plus Docker, with **no Windows binary** in the release assets ([repo](https://github.com/restatedev/restate), [releases](https://github.com/restatedev/restate/releases)).
- **D4/D5/D6:** it has similar primitives (durable steps, timers, retries). I did not study the details, because the platform fit fails first.
- **Verdict:** **KEEP (do not adopt)**. Windows would need Docker or WSL, and the licence is not OSI-approved.

## 5. Hatchet

- **What it is:** a Postgres-backed task queue and workflow engine. MIT ([LICENSE](https://github.com/hatchet-dev/hatchet/blob/main/LICENSE)). Very active: Python SDK 1.46.0 and 2.0.0a1 on 13 Nov 2026 ([releases](https://github.com/hatchet-dev/hatchet/releases)). Hatchet Lite "requires Docker" and Postgres (RabbitMQ optional). No SQLite option was found ([Hatchet Lite](https://docs.hatchet.run/self-hosting/hatchet-lite)).
- **Verdict:** **KEEP (do not adopt)**. Docker plus Postgres on the Owner's Windows host is a large ops burden for features that DBOS provides in-process.

## 6. Prefect 3

- **What it is:** a flow and task orchestrator. Apache-2.0. Latest 3.9.3, 13 Nov 2026 ([releases](https://github.com/PrefectHQ/prefect/releases)). The local server runs SQLite by default.
- **Liveness mechanism:** flow-run heartbeats (`PREFECT_FLOWS_HEARTBEAT_FREQUENCY`, default 180 s from 3.6.22) plus a proactive automation that marks a run `CRASHED` when no `prefect.flow-run.*` event follows a heartbeat within the window (540 s suggested). The managed "Unresponsive run detection" is **Cloud-only**. Self-hosted users must script the automation ([zombie flows](https://www.prefect.io/docs/v3/advanced/detect-zombie-flows)). Re-running a crashed run is not described there (not found).
- **Verdict:** **KEEP (do not adopt)**. It needs a server process, and crash detection is an add-on with no documented re-dispatch, so it is weaker than both DBOS and Temporal on D4. It contributes nothing new beyond the heartbeat-plus-automation pattern.

## Others

I did not study Inngest, Huey or the pgqueuer family in depth. Huey and the Postgres queues provide retries but no durable child workflows. No other candidate was found that beats DBOS on "single Windows host, no server, SQLite".

---

## Defect map (this area)

| Defect | Best mechanism | Source |
|---|---|---|
| D1 (timeout side) | Separate idle heartbeat from the per-attempt cap; on timeout, retry with backoff on a *different* account; mark 429 and quota errors non-retryable on that account | Temporal Heartbeat/Start-To-Close + RetryPolicy; LangGraph `TimeoutPolicy` |
| D4 | Goal = durable workflow; window cap = durable wait/signal, not membership; per-account partitioned queue | DBOS `recv`/`sleep`, `partition_limiter`; Temporal task queues |
| D5 | Loop in code; status = workflow state; no SQL inference | DBOS / Temporal workflows; LangGraph StateGraph |
| D6 | Engine-owned connections plus auto-recovery on launch; supervisor still external | DBOS 3.5 SQLite locking; nothing found for a Windows supervisor |
| D8 (timeout side) | `refresh_on="heartbeat"` driven by test-runner output | LangGraph 1.2 |
| #1515 redeploy | `RunControl.request_drain()` → resumable checkpoint; DBOS resumes PENDING on launch | LangGraph 1.2; DBOS recovery |

## Top 3 actions

1. **Spike DBOS Transact (SQLite system DB, in-process) as the goal-level engine**, written as one workflow: plan → child(implement) → child(review) → repair loop with a round limit. Removes **D5** (no status inference), the stranding half of **D4** (window caps become durable waits) and most of the **#1515/D6** recovery code (PENDING workflows resume on launch). Would shrink or replace:
   - `control_store.py`: `runnable_tasks`, `refresh_goal_status`, the claim and rebind functions;
   - `unattended_coordinator.py`: the claim loop, `_sweep_escalations`, `_reroute_held`;
   - `goal_service.py`: the escalation and repair bookkeeping;
   - `durable_execution.py`: the lease, fencing and resume paths.

   Budgets, receipts and landing stay. Cost: about 1–2 weeks of spike, then a staged migration. No server and no Postgres.
2. **Copy Temporal's attempt contract into the executor boundary**, whatever engine runs it:
   - set queue-wait, per-attempt, idle-heartbeat and total timeouts as four explicit settings;
   - add a non-retryable error class (quota/429/402) that forces the next attempt onto another account, with exponential backoff;
   - carry heartbeat details that save progress (worktree head) so an INTERRUPTED attempt resumes on a different account.

   Removes the "INTERRUPTED waits for the same account" half of **D4** and the timeout side of **D1/D8**. Shrinks `_HeartbeatContext`, the stall logic in `opencode_executor.py`, `reroute_held_task` and `_reroute_quota_held`. With DBOS, it maps onto `@DBOS.step` retries plus a partitioned queue per account.
3. **Upgrade LangGraph from 1.0.10 to 1.2.x** and use it for the in-task team graph:
   - `TimeoutPolicy(run_timeout, idle_timeout, refresh_on="heartbeat")`;
   - `RetryPolicy` and `error_handler`;
   - `RunControl.request_drain()` on redeploy.

   Removes the redeploy-strands-running-task class (**#1515**) and the long-test stall false positive (**D8**) for the team graph. Cheap: a dependency bump, async nodes and a re-check of strict serde. If action 1 lands, also drop the dual "LangGraph cursor + TaskStore truth" reconciliation in `durable_execution.py`, because one durable log is enough.
