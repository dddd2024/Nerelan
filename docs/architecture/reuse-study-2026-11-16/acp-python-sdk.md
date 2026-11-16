# ACP Python SDK — pinned deep source audit (Nerelan)

**Source study:** [#1585](https://github.com/dddd2024/Nerelan/issues/1585) · **Canonical research hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Date:** 2026-11-16

**Evidence status:** STATIC_SOURCE_REVIEW / NOT_TESTED / NOT_INSTALLED / NO_IMPLEMENTATION_AUTHORITY. This is a documentation-only protocol and architectural audit. No live ACP client, vendor model, R2 dependency change, R3 binary execution, validation, or independent review was performed. Protocol examples are not Nerelan acceptance results.

# ACP Python SDK 源码级专项：同一个协议，两种集成角色；稳定 SDK 与 Nerelan 权限/持久性的分界

> **Research-only / DOCS_ONLY** · 2026-11-16 · `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_RUN / NO_IMPLEMENTATION_AUTHORITY`  
> **One upstream repository:** [agentclientprotocol/python-sdk](https://github.com/agentclientprotocol/python-sdk), [pinned `4fed584775d6a650cd669b63617049e5352297fe`](https://github.com/agentclientprotocol/python-sdk/commit/4fed584775d6a650cd669b63617049e5352297fe) (2026-11-16), Apache-2.0 ([LICENSE](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/LICENSE)).  
> **Current Nerelan main comparison:** [`e7ed129d143f5839a4d16dd220adf3afdf88d3ea`](https://github.com/dddd2024/Nerelan/commit/e7ed129d143f5839a4d16dd220adf3afdf88d3ea). **Not** the previous #1581 baseline.

## 0. 查重结果：有规划，但无官方 SDK 源码级专项

Read canonical [#1576](https://github.com/dddd2024/Nerelan/issues/1576) including its chronological research comments: six original deep reports + #1578 SWE-ReX + #1581 Google ADK; historical 19-project archive; current Issue search for `"Agent Client Protocol"`, `"ACP" "executor"`, and `"Research / Reuse"`; [#816 ACP-first IDE owner](https://github.com/dddd2024/Nerelan/issues/816), [#96 historical OpenHands+Codex ACP plan](https://github.com/dddd2024/Nerelan/issues/96), [#806 headless API](https://github.com/dddd2024/Nerelan/issues/806), [#1527 executor/multi-harness](https://github.com/dddd2024/Nerelan/issues/1527), [#803 change review](https://github.com/dddd2024/Nerelan/issues/803), [#795 steering](https://github.com/dddd2024/Nerelan/issues/795), [#384 local client auth](https://github.com/dddd2024/Nerelan/issues/384), [#790 MCP](https://github.com/dddd2024/Nerelan/issues/790). ACP itself **already exists as product direction and early historical prototype idea**. No separately indexed source audit of the official Python SDK was found. This report is a source-evidence increment to existing #816/#1527, not a competing feature owner or an attempt to resurrect #96.

## 1. Critical architecture split: ACP dual role, MCP unrelated

**Role A — Nerelan as ACP Client**, internally talking to an ACP-capable external coding Agent. Owned by #1527. Thin adapter -> ACP session/notifications -> trusted Nerelan `ExecutorResult` and evidence, linked via **one separate** `Task/Attempt ID <-> ACP connection/session ID` mapping. ACP has no Magpie account pooling, independent task acceptance, Owner authority, or economic ranking.

**Role B — Nerelan as ACP Agent**, exporting the existing Goal/Run through an editor client (e.g. Zed/JetBrains). Owned by #816 with #806/#384/#803/#795. The IDE sends `session/prompt`, displays progress/changes and answers allowed permission requests; **Nerelan** owns durable Run, workspace identity, permission/authorization, review and publication.

**Do not collapse the roles:** client callbacks for `fs/read_text_file`, `fs/write_text_file`, terminal are *operations requested from the editor by the agent*; they do not grant agent-side filesystem or shell authority. These operations must be routed through approved workspace/host checks or denied. MCP is the separate tool-provider protocol (#790), not an ACP substitute.

## 2. Source-confirmed mechanisms (exact pinned paths)

### A. Official typed SDK directly reusable *only under dependency/admission gate*

- [`src/acp/client/connection.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/client/connection.py): `ClientSideConnection` has `initialize`, `new_session`, `load_session`, `list_sessions`, `set_session_mode`, `set_config_option`, `authenticate`, `prompt`, `fork_session`, `resume_session`, `close_session`, `cancel`. `prompt` waits for outstanding matching session-update callbacks to settle (v1 semantics).
- [`src/acp/agent/connection.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/agent/connection.py): `AgentSideConnection` emits `session_update`, makes `request_permission`, and requests file read/write, terminal create/output/wait/kill, and MCP forwarding **from the Client**. 
- [`src/acp/interfaces.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/interfaces.py), generated [`schema.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/schema.py): typed client/agent method contracts and schema-v1.23.0 reference; [golden tests](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/tests/test_golden.py) cover plan/message/tool updates, tool output including diff/terminal, permissions and file requests.
- **Decision**: `DIRECT_REUSE_CANDIDATE` official Python SDK as a thin protocol library once R2 dependency/compatibility gate approved; **not** vendored upstream code, not replacing current runtime. The protocol is **not** a turnkey ACP Agent implementation of Nerelan.

### B. Structured streaming and UI projection

- [`contrib/tool_calls.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/contrib/tool_calls.py): `ToolCallTracker` produces start/progress notifications with stable tool call IDs; [`contrib/session_state.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/contrib/session_state.py): experimental `SessionAccumulator` merges plan, mode, available commands, tool progress and message chunks. It defaults to resetting on session ID change; a strict mode throws `SessionNotificationMismatchError`. [tests](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/tests/contrib/test_contrib_session_state.py).
- **BORROW_PATTERN**: map typed stream to UI: action explanation, current plan, tool status, diff/terminal metadata; keep the authority-free *projection* separate from task truth; use `auto_reset_on_session_change=False` or equivalent strict task/session binding. Reject live UI state as a durable TaskStore substitute; don't ingest arbitrary agent thought, terminal text, or diff instructions as trusted actions.

### C. PermissionBroker `allow_always` is not Nerelan authorization

- [`contrib/permissions.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/contrib/permissions.py): `PermissionBroker` is a helper for building a client request with options: `allow_once`, `allow_always` ("Approve for session"), `reject_once`; returns the client's selected outcome. [tests](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/tests/contrib/test_contrib_permissions.py) and [real-user flow](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/tests/real_user/test_permission_flow.py).
- **P0 BORROW_PATTERN / REJECT as authority**: `request_permission` is UI consent **only**. Even if client responds `allow_always`, call must pass Nerelan pre-side-effect host policy with fresh scope/approval revision, path and command checks, lease/cost constraints, and R2/R3 governance; no client/grant token can mint Owner authority. For dangerous terminal/file requests, deny absent suitable host capability. Do not give editor full host shell or arbitrary writable paths.

### D. Cancellation, connection identity and resume are not exactly-once

- [`src/acp/connection.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/connection.py): JSON-RPC request IDs are in-memory per connection; await cancellation sends best-effort `$/cancel_request`, incoming cancellation cancels handler task; `session/cancel` is separate. On disconnect outstanding requests are rejected. These are **transport semantics**, not a guarantee that started tool/process effects are reversed. 
- `session/load` / `resume` / `fork` are agent capabilities, not a guarantee of retaining an authoritative Nerelan Goal across crashes. Existing `TaskStore`/`Run`/`Attempt` identities and receipts remain authoritative.
- **BORROW_PATTERN**: add transport generation, session ID mapping, cancel-ack vs actual process termination, stale-update and duplicated-stream fixtures. UI reconnect must reconcile from Nerelan durable truth, not rely on ACP session accumulator alone.

### E. Windows stdio stable pilot vs remote/v2 experimental protocol

- [`src/acp/stdio.py`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/stdio.py) implements Windows async stdio using a thread feeder and specialized stdout writer; [`spawn_agent_process`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/src/acp/stdio.py) and `spawn_client_process` provide distinct role helpers.
- [`docs/web-transport.md`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/docs/web-transport.md) marks Streamable HTTP/WebSocket transport **experimental**, HTTP requires HTTP/2, and reconnect/retry is caller responsibility. Do not expose public network listeners as a shortcut to IDE integration.
- [`docs/experimental-v2.md`](https://github.com/agentclientprotocol/python-sdk/blob/4fed584775d6a650cd669b63617049e5352297fe/docs/experimental-v2.md) marks protocol v2 alpha **experimental** (`schema-v2.0.0-alpha.5`). v2 asynchronous accepted `session/prompt` `message_id`, notices and patch tri-state differ materially from v1; there is **no transparent v1/v2 conversion**. Explicit capability/version gating, fail closed for unsupported features.
- **DIRECT_REUSE_CANDIDATE**: locally authenticated v1/stdin-out adapter after dependency authorization, not v2 or public remote by default. Spawn an external CLI only after separate R3 execution approval or preauthorized bounded grant.

### F. No second TaskStore, no second Gateway, no editor-side authority

- Nerelan currently [`task_runtime.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/task_runtime.py) routes executors; [`task_execution.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/task_execution.py) normalizes `ExecutorResult` and persists evidence; [`codex_protocol.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/codex_protocol.py) and [`claude_protocol.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/claude_protocol.py) sanitize native event streams and cap bytes/events; [`local_client_session.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/local_client_session.py) has host-memory client identity **but possession does not confer action authority**; [`task_service.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/task_service.py) remains loopback-only and TaskStore-owned. Existing #816 already owns IDE surface.
- **ALREADY_REUSED / KEEP** all of these. A native ACP adapter should be measurable against existing native executors for functionality, quality, latency, cost and security; **no claim** ACP reduces model token cost merely by standardizing transport.

## 3. Module decisions + unique Owner

| Nerelan module | Decision | Reuse / boundary | Implementation Owner |
|---|---|---|---|
| IDE/editor gateway | `P1 DIRECT_REUSE_CANDIDATE` | Python ACP SDK typed v1, Nerelan as Agent; explicitly version- and capability-gate | #816, #806 |
| External Agent harness adapter | `P1 DIRECT_REUSE_CANDIDATE` | Nerelan as Client; no automatic replacement of native executor | #1527 |
| UI agent turn / tool event | `P1 BORROW_PATTERN` | typed ToolCallTracker, plan/mode/progress and strict session binding | #816, #1561 |
| Permission / terminal / FS / MCP | `P0 SECURITY_REJECT_AS_AUTHORITY` | client asks/answers only; host policy, approval and bounds always authoritative | #384, #303, #299, #790 |
| Resume and crash recovery | `ALREADY_REUSED + P0 TEST` | ACP session transport ID != Goal/Run or side-effect receipt | #120, #1546 |
| Memory / context | `NO_DIRECT_REUSE` | explicit editor content as untrusted bounded context; not full chat memory replication | #296 |
| Accounts, model router, cost | `REJECT_REPLACEMENT` | Magpie remains model pool and request/usage authority | #1342, #1267 |
| v2/web experimental | `DEFER` | do not pin production to changing experimental contracts | #816 |

## 4. Provider-free falsifiable tests (NOT RUN)

**T1 Role/handshake matrix**: fake editor connects to fake Nerelan ACP Agent; separately Nerelan Client connects to mock ACP Agent; assert negotiated v1 methods, session binding, unsupported capabilities rejected explicitly, no accidental cross-role invocation; unique IDs/generation.
**T2 Permission & terminal escape**: malicious fake ACP client selects `allow_always`, asks to write outside worktree/hidden protected file and create privileged terminal. Assert zero host-side effects without original Owner policy, fresh path check and bounded capability. Reject same operations on missed client auth; no credential leaks.
**T3 Streaming/duplicate/failure**: 2 concurrent sessions with overlapping tool_call_ids, interrupted/reordered stream, stale session updates and disconnect; strict projection must not merge sessions or invent done status. Task truth comes from durable store and readback.
**T4 Cancellation/crash**: transport cancel and dropped terminal response after command starts; process may still run. Assert TaskStore remains `RUNNING/UNKNOWN/LOST` until real process/receipt reconciled; never double execute by retrying ACP notification.
**T5 Windows compatibility and economicity**: separate R2/R3 authorization before official SDK install or external agent spawn. Start provider-free echo in trusted local temp/workspace, stress stdio shutdown, bad bytes and limits; compare existing native bridge vs ACP for tool fidelity, time to first update, p95 latency, resource usage, acceptance and total request-equivalent cost. **NO-GO** if fidelity, authorization, Windows cleanup or recovery evidence regress.

## 5. Product user story and verdict

End user can continue a governed Nerelan Goal from IDE or Nerelan desktop without a second identity, see the same plan/tool status, give *bounded* permission, review exact changed files and return to running task. **Do not confuse a smooth ACP demo with durable/verified Goal completion.**

**Verdict: SELECTIVE_DIRECT_SDK_REUSE_CANDIDATE / P1**, conditional on first provider-free compatibility and R2 dependency approval; security/privacy gates are **P0 prerequisites**. No SDK install, live agent, remote server, provider requests, code copy or new implementation Issue today. Only Issue + R1 docs-only Draft PR + #1576 canonical hub entry. No CI or independent review claimed.

---

## Provenance and merge management

- ACP Python SDK source frozen: `4fed584775d6a650cd669b63617049e5352297fe` (Apache-2.0).
- Nerelan main compared: `e7ed129d143f5839a4d16dd220adf3afdf88d3ea`.
- Older ACP plans are [#816](https://github.com/dddd2024/Nerelan/issues/816) and [#96](https://github.com/dddd2024/Nerelan/issues/96), not treated as new source execution authority.
- No permanent second research index created in this PR while [#1576](https://github.com/dddd2024/Nerelan/issues/1576) and its stacked documentation/index PRs are being reconciled. Log this ninth static study in the canonical hub's dated entry and sync to the accepted index only through a future gated update.
