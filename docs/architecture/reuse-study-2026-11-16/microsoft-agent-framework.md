# Microsoft Agent Framework — workflow recovery, MCP ownership and context integrity

**Research date:** 2026-11-16
**Status:** `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY`
**Canonical research Issue:** [#1608](https://github.com/dddd2024/Nerelan/issues/1608)
**Research hub and anti-duplication owner:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

## Scope and exact source versions

- **Single upstream:** [Microsoft Agent Framework `10801303c1bdf08811ba2c1066b55722b86b3fc2`](https://github.com/microsoft/agent-framework/commit/10801303c1bdf08811ba2c1066b55722b86b3fc2). Root [MIT license](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/LICENSE); this research copies no source or dependencies. Provider/cloud services and transitive artifacts have not been licensed individually.
- **Nerelan comparison:** [main `0a9997046386bac5ca291410ce428c160f3ea763`](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763).
- **Deduplication:** checked #1576, its archived cross-chat studies and 2026-11-15 five-area reuse study, and GitHub issue/PR searches for `microsoft/agent-framework` and `Microsoft Agent Framework`. MAF has no prior dedicated source audit seen. This study examines specific gaps not already owned by Mastra #1564, Google ADK #1581, A2A #1603, AG-UI #1600, ToolHive #1590 and Dify #1571.
- **Method:** source/ADR inspection only. No package installation, model calls, live-host experiments, performance or cost measurements.

## Executive architecture verdict

**Do not add MAF as a second Agent/Workflow framework.** Nerelan already uses LangGraph [team graph](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/workflows/team_graph.py) with parallel `Send`, reducer and verifier; the [LangGraph architecture boundary](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md) reserves TaskStore as durable task truth. [`task_runtime.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/task_runtime.py) routes actual executor kinds and validates commands; `goal_service.py` orchestrates product Goals. Replacing the workflow stack would create a second authority/status path and distract from present 429/stall/timeout/settlement defects.

**Borrow five bounded designs instead:** (1) pair emitted output with an exact durable checkpoint ID; (2) handle cancellation of pending file writes without mistaking a cancelled await for a cancelled write; (3) explicit MCP Client/session ownership per authorization scope; (4) fail-loud tool middleware without claiming side-effect rollback; (5) compact model-facing history by tool and approval groups. Implementations remain owned by existing Nerelan Issues.

## Source deep dive

### 1. Agent graph and durable workflow boundaries

[Python `WorkflowBuilder`](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_workflows/_workflow_builder.py) builds typed executor edges and takes `start_executor`, `max_iterations`, and optional `checkpoint_storage`. [`AgentExecutorCheckpointState`](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_workflows/_agent_executor.py) serializes conversation, agent session and pending request/response state to the workflow checkpoint. These are **workflow mechanics**, not Nerelan Goal/Task/Owner authorization semantics.

[`WorkflowCheckpoint`](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_workflows/_checkpoint.py) captures graph signature, `previous_checkpoint_id` lineage, superstep/iteration, pending external requests and state. `CheckpointStorage` explicitly separates `save`, `load`, `list`, `get_latest`, `delete`. Its `get_latest` selection resolves same-timestamp ties using lineage: even a reliable latest within the storage does **not** mean it matches the latest response already persisted to clients.

[ADR 0041](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/docs/decisions/0041-foundry-hosting-resilient-long-running-agents.md) (status **proposed**) documents the stronger recovery rule: pair the *acknowledged response snapshot* and persisted AgentSession with the exact workflow checkpoint. If a newer superstep checkpoint exists but its response was never snapshotted, restart from the older acknowledged checkpoint, not the newest. This avoids lost/duplicated visible outputs; **external side effects can still repeat after that boundary**, so Nerelan needs durable operation receipts/fencing and idempotency. ADR 0041 is evidence of a design, not evidence that all .NET hosting behavior is released and verified.

**Nerelan mapping:** [#1546 DBOS spike](https://github.com/dddd2024/Nerelan/issues/1546), existing TaskStore/GoalService, [#120 checkpoint/resume](https://github.com/dddd2024/Nerelan/issues/120); reject a new MAF engine. In a recovery protocol, bind (Goal ID, Task ID, Attempt ID, checkpoint ID, workspace head, owner generation, published response cursor) and reconcile external receipts before retrying an action. Precise schema is a candidate, not a current feature claim.

### 2. Checkpoint persistence itself can stall or corrupt

The [`FileCheckpointStorage` implementation](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_workflows/_checkpoint.py) uses a process-wide per-destination queue of `concurrent.futures.Future` tickets. Code comments explain why `asyncio.wrap_future` cancellation propagation and cancelled `to_thread` awaits could release ownership **before** a worker-thread file write has actually ended, causing a later `os.replace` to be overwritten. The current design queues and releases writes through thread-safe completion signals.

**Limit:** it explicitly does **not** serialize writes across distinct host processes/replicas. It stores JSON structure plus a pickle-encoded state section; deserialization defaults to constrained allowlisted types with optional explicit registrations. Do not treat a third-party checkpoint file as safe untrusted input, and do not substitute file replacement for cross-process CAS/fencing.

**Nerelan mapping:** property/fault-injection tests for multi-writer / cancellation / recovery in #1546, not adoption of the MAF file backend.

### 3. MCP/plugin connection and identity

[ADR 0050](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/docs/decisions/0050-python-mcp-v2-client-lifecycle.md) is **approved**. It assigns ownership to three modes: framework-created high-level MCP `Client`, borrowed caller-owned high-level `Client`, and a deprecated borrowed low-level `ClientSession`. High-level behavior (protocol negotiation, tool/resource/prompt calls, caching and multi-round-trip requests) must not be bypassed through the low-level session. The framework's responsibilities include cleanup even on cancel/failed connect, request-scoped header identity and reconnect, bounded discovery and sanitized result conversion. Caller-owned client/session resources remain caller-owned.

[ADR 0047](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/docs/decisions/0047-python-mcp-runtime-context.md) (status **proposed**) offers an approval trust model: host runtime context must be separate from model-supplied tool args; delayed tool approval binds request ID plus an HMAC over evaluated HTTP headers; if credentials rotate, re-approve. It explicitly keeps raw credentials out of approval payloads.

[ADR 0053](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/docs/decisions/0053-python-invocation-owned-mcp-sessions.md) (status **proposed**) advocates **invocation-owned** protocol sessions instead of one global client cache keyed only by connection configuration. The ADR acknowledges an extra connection/catalog discovery cost and loss of implicit remote session continuity. It is a design input, **not an already proven current implementation**.

**Nerelan mapping:** [#790 MCP runtime](https://github.com/dddd2024/Nerelan/issues/790), [#789 hooks/interception](https://github.com/dddd2024/Nerelan/issues/789), [#303 repository config trust](https://github.com/dddd2024/Nerelan/issues/303), [#253 Pack productization](https://github.com/dddd2024/Nerelan/issues/253). Define per-Task/per-account security scope, explicit connection owner, credential rebind, cancellation and cleanup, and host-side approval checks at the actual tool call. Do not create a second daemon or silently trust project-local MCP config.

### 4. Middleware is not a transaction boundary

[`_middleware.py`](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_middleware.py) exposes `MiddlewareFailure` as an explicit fail-closed escape from the normal function-tool failure-to-result behavior. The module describes aborting the batch and cancelling sibling asynchronous work. Critically, already-running **synchronous tool threads may still commit external side effects**; their results being discarded does not roll back the mutation. Persisted service conversations may also issue a settlement response for dangling tool calls.

**Nerelan mapping:** [#789](https://github.com/dddd2024/Nerelan/issues/789), [#790](https://github.com/dddd2024/Nerelan/issues/790), [#299 sandbox](https://github.com/dddd2024/Nerelan/issues/299). Separate (a) policy decision, (b) dispatch admission, (c) started side effect, (d) observed completion/UNKNOWN, (e) compensation. Hosted tools, other SDK paths or external effects cannot be proven protected by Python function middleware alone.

### 5. Memory/context compaction without history corruption

[`_compaction.py`](https://github.com/microsoft/agent-framework/blob/10801303c1bdf08811ba2c1066b55722b86b3fc2/python/packages/core/agent_framework/_compaction.py) explicitly groups tool-call/result occurrences and approval request/response pairs, including ambiguity checks. That is safer than blindly keeping the latest N messages.

**Nerelan mapping:** [#296 context management](https://github.com/dddd2024/Nerelan/issues/296) and [#1267 cost/quality routing](https://github.com/dddd2024/Nerelan/issues/1267). Keep TaskStore evidence immutable. Apply reduction only to model-facing projection, preserving call/result IDs, approval identity, recent immutable objective/constraints and verified artifact pointers. Compare cached prompt token savings against summary cost, cache invalidation, reviewer cost and rework.

## Decision matrix

| Area | Decision | Why | Existing implementation owner |
|---|---|---|---|
| Agent/graph executor routing | **ALREADY_REUSED** | LangGraph `Send` fanout and `ExecutorRouter` already exist | #1508 / #1527 |
| Entire MAF runtime, Foundry hosting, another DevUI | **REJECT** | Would duplicate workflow/task truth and dev-product surface | #1546 / #260 |
| Response/checkpoint exact alignment + cancellation-write tests | **BORROW_PATTERN** | Durable output/side-effect evidence must survive crash without logical time travel | #1546 / #120 |
| MCP client ownership and auth scope | **BORROW_PATTERN** | Avoid cross-task/account credential/session leakage; check actual cost of extra connection | #790 / #789 / #303 |
| Fail-closed tool middleware with side-effect receipts | **BORROW_PATTERN** | Interrupt is not undo; task success must not hide partial mutation | #789 / #299 |
| Group-aware context compaction | **BORROW_PATTERN** | Avoid tool/approval orphaning; verify total cost and acceptance | #296 / #1267 |
| Drop-in MAF Python Agent dependency | **REJECT** for current platform | No demonstrated cost/quality win; extra framework and status graph | #1546 / #1527 |
| Direct code/library reuse | **NONE PROPOSED** | Existing frameworks already own these mechanics; patterns need hosted invariants | #361 |

## Falsifiable minimal experiments — **not executed in this research**

| Test ID | Fixture | Pass criterion | No-go condition |
|---|---|---|---|
| MAF-N1 crash between checkpoint/response/receipt | Fake Goal → superstep → tool output → external receipt; kill at each durable write boundary | Resume at matching response checkpoint, reconcile receipts, preserve exact Task outcome and workspace | Duplicate external mutation, skipped committed output, fabricated succeeded status |
| MAF-N2 MCP identity during approval | Two Tasks and accounts using same MCP URL, distinct header identity; rotate credentials while approval is pending | No cross-account session, no stale approval, no host Gate bypass; failure/UNKNOWN accounted | A call executes with unapproved principal or stale headers |
| MAF-N3 middleware mixed batch | Concurrent async denied function and already-started sync mutator | Denial fails loudly; sync mutation appears in receipt; retries idempotent | Lost side effect/duplicate mutation despite a cancelled batch |
| MAF-N4 checkpoint writer concurrency | Cancel queued file save while thread write continues, then concurrent save; second process same checkpoint ID | Single-process save queue does not stall; explicitly fail/do-not-reuse file method for multi-process | Save stuck or a claim of cross-process exactly-once |
| MAF-N5 compaction acceptance and cost | Same fixed work item, original history vs grouped model projection, identical deterministic and independent checks | All calls/approvals paired; non-worse acceptance at lower **total** measured cost | Lost pairing, lower acceptance, or net cost rise |

## Priorities and governance

1. **P0 current product fires remain #1530/#1531/#1342** (silent stall, 429, quota and attempt-level settlement): do not pause real repair for MAF framework research.
2. **P1 resume receipts/identity (#1546/#120)** and **P1 MCP scope/approval (#790/#789)** before opening a larger plugin ecosystem.
3. **P1/P2 compaction (#296)** only after provider-free pairing tests and measured Executor×Model cost/quality comparison.
4. This is **docs-only R1 research**. No implementation Issue created, no dependency, secrets, R3 operations or model calls authorized; any future code change requires its existing owner, regression/fault tests, exact-head CI and independent review. The linked Draft PR is not an integration pass or an adopted behavior.
