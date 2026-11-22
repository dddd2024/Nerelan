# Google ADK (Python) — source audit for Nerelan, 2026-11-16

**Research**: [Issue #1581](https://github.com/dddd2024/Nerelan/issues/1581) · **Canonical Hub**: [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

**Scope**: docs-only upstream static analysis. Evidence grade `STATIC_SOURCE_REVIEW`; no integration, benchmark, model calls, dependency installs, CI or independent review are asserted. This report is not an authorization for runtime changes.

# Google ADK Python 深度源码研究：Tool-call integrity / compaction / scoped session / plugin gate

> **Date** 2026-11-16 · **Status** STATIC_SOURCE_REVIEW / NO_RUNTIME_TEST / NO_DEPENDENCY / NO_IMPLEMENTATION_AUTHORITY  
> **Upstream** [google/adk-python](https://github.com/google/adk-python) @ [`c6586f19ab8a2bb8b53e70041633b10858d9902e`](https://github.com/google/adk-python/commit/c6586f19ab8a2bb8b53e70041633b10858d9902e), Apache-2.0 (LICENSE verified).  
> **Nerelan main** [`853a787143ef738e421b8efc637a7b8905629e0b`](https://github.com/dddd2024/Nerelan/commit/853a787143ef738e421b8efc637a7b8905629e0b). Note main had materially changed after prior SWE-ReX review: compare against this *new* baseline, not stale `a7b62777`.

## 0. Prior-work and duplication gate

Checked [canonical hub #1576](https://github.com/dddd2024/Nerelan/issues/1576), archived six prior deep studies, 19 cross-conversation entries (including Cline, Pi, Letta Code, Hermes Agent, OpenCode, Pydantic AI), latest [SWE-ReX #1578](https://github.com/dddd2024/Nerelan/issues/1578), current GitHub Issue search for `ADK`, `google-adk`, `google/adk-python`, `Agent Development Kit`, and source keyword search `google.adk`; no existing project-specific ADK Python source audit found. Adjacent implementation directions **already exist**, and MUST NOT be duplicated: [#789](https://github.com/dddd2024/Nerelan/issues/789) hook/interceptors, [#790](https://github.com/dddd2024/Nerelan/issues/790) MCP lifecycle, [#296](https://github.com/dddd2024/Nerelan/issues/296) context, [#303](https://github.com/dddd2024/Nerelan/issues/303) untrusted repo config, [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack, [#1546](https://github.com/dddd2024/Nerelan/issues/1546) DBOS durable engine, [#1527](https://github.com/dddd2024/Nerelan/issues/1527) multi-executor bake-off, [#1575](https://github.com/dddd2024/Nerelan/issues/1575) refactor. This is a new **source-evidence increment**, not a new Agent runtime rollout.

## 1. Source-pinned findings

### A. Stored tool-call tamper integrity — highest-value P0 hypothesis

[`plugins/_tool_call_integrity_plugin.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/plugins/_tool_call_integrity_plugin.py), [tests](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/tests/unittests/plugins/test_tool_call_integrity_plugin.py).
- An **optional** `ToolCallIntegrityPlugin` HMAC-SHA256-stamps the canonicalized stored FunctionCall with context; verifies stamps when runs resume and immediately before tool execution; checks tool name/arguments; supports key rotation and explicitly rejects copied/restored history as executable calls. A compatibility `allow_unstamped_calls` mode allows unstamped calls through with warning, **not appropriate for Nerelan security-critical admission**.
- This targets stored-call mutation between an approval/credential wait and eventual execution, including when the session store is writable by a lower-trust actor. It does **not** prove authority, exactly-once side effects, timely approval, policy freshness, or sandboxing.
- **Borrow pattern**, not necessarily this plugin: immutable trusted `operation_id + task_id + call_id + tool identity/version + canonical args digest + approval identity + snapshot/policy revision` binding; exact call verification **at side-effect boundary** against Nerelan's own authority and durable event; stale/changed/missing -> refuse with evidence. Do not store the HMAC key in agent-reachable workspace.

### B. Model-facing compaction must preserve tool-call/response referential integrity

[`flows/llm_flows/context/_compaction.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/flows/llm_flows/context/_compaction.py) `_recover_compacted_function_calls`: reintroduces missing original calls when a response survives summarization, keeps parallel siblings' responses and preserves thought signatures; resolves duplicated call IDs by source order rather than global ID alone. Tests cover compaction request and tool-result interactions [test_compaction.py](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/tests/unittests/flows/llm_flows/context/test_compaction.py).
- Nerelan currently has [`context_builder.py`](https://github.com/dddd2024/Nerelan/blob/853a787143ef738e421b8efc637a7b8905629e0b/reverse_agent/platform_v1/context_builder.py) and [`context_optimization.py`](https://github.com/dddd2024/Nerelan/blob/853a787143ef738e421b8efc637a7b8905629e0b/reverse_agent/platform_v1/context_optimization.py) which deterministically bound authoritative-source projection and summarize history; [`context_recovery.py`](https://github.com/dddd2024/Nerelan/blob/853a787143ef738e421b8efc637a7b8905629e0b/reverse_agent/platform_v1/context_recovery.py) gives scope-digest and authority-free handoff. **ALREADY_REUSED concept**: bounded/no-authority context; **BORROW_PATTERN missing explicit proof**: referenced tool-call/response pair invariants under compression and resumed long-running tools; cannot infer a production defect without a failing fixture.
- Proposed transformation: read-only model-facing *projection* retains relevant unmatched call IDs, pending approvals, responder pair and provenance while raw TaskStore events stay unchanged; if cannot reconstruct, make model-facing context UNKNOWN/blocked rather than silently invent calls.

### C. Event branch / per-worker visibility, but not owner authorization

[`events/event.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/events/event.py): `branch` and internal `isolation_scope` restrict subagent conversation visibility; `isolation_scope` expressly labelled internal/unstable; [`sessions/base_session_service.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/sessions/base_session_service.py) splits invocation-local `temp:` state from persisted deltas.
- **BORROW_PATTERN**: per-role/per-task visible-event projection, ephemeral vs persistable state classification. **REJECT direct use of undocumented field**, or trusting agent-controlled scope tags. Nerelan task and lease/policy/approval remain host-owned.

### D. Event append with stale writer guard; not DBOS replacement

[`sessions/sqlite_session_service.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/sessions/sqlite_session_service.py) `append_event` uses SQLite `BEGIN IMMEDIATE`, compares stored update time to supplied session timestamp before commit and rolls back on failure; [tests](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/tests/unittests/sessions/test_session_service.py) include stale writer, lock wait and rollback.
- **BORROW_PATTERN**: adversarial stale session/duplicate event fixtures and atomic append+state checks. **REJECT** importing second SessionService/TaskStore or assuming timestamp-based optimistic lock is a lease fencing token for external side effects. Existing Nerelan durable owner #1546 controls crash semantics.

### E. Plugins / MCP toolsets: useful division, one dangerous shortcut

[`plugins/base_plugin.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/plugins/base_plugin.py) and [`plugins/plugin_manager.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/plugins/plugin_manager.py): before/after run/agent/model/tool, event, and error callbacks; name uniqueness and bounded plugin close. Normal callback dispatcher **stops on first non-None result**, potentially skipping later checks. Error notification callbacks instead visit all plugins best-effort. [Plugin tests](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/tests/unittests/plugins/test_plugin_manager.py) explicitly test short-circuit.
[`tools/base_toolset.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/tools/base_toolset.py): context-filtered tool retrieval and per-invocation cache; documented risk that replacement tools returned on discovery error may bypass `tool_filter`. [`tools/_confirmation_utils.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/tools/_confirmation_utils.py) tool-local confirmation is a request mechanism, not trusted host authority.
- **BORROW_PATTERN**: distinguish ordered observational/advisory handlers, unskippable host-policy gate, final pre-side-effect integrity check, and best-effort notifications; tool catalog identity/cache invalidation + error states.
- **REJECT** treating ADK's ordinary callback short-circuit, toolset filtering, tool-local confirmation, or plugin installation as authorization. Both SDK and hosted MCP paths must pass one Nerelan host gate; no second plugin manager.

### F. Prompt/tool-description untrusted fencing

[`flows/llm_flows/context/_fencing.py`](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/src/google/adk/flows/llm_flows/context/_fencing.py) wraps external tool/schema descriptions and other-agent messages with untrusted markers; recursively scrubs injected delimiters; [tests](https://github.com/google/adk-python/blob/c6586f19ab8a2bb8b53e70041633b10858d9902e/tests/unittests/flows/llm_flows/context/test_fencing.py) include marker injection and schema fields. The code itself states Unicode lookalike normalization is out of scope.
- **BORROW_PATTERN**: model-facing tool-description provenance/fencing as *defense-in-depth*, not a security boundary. Model compliance with delimiters cannot replace server authorization, egress and secret policies (#303/#447/#789).

## 2. Nerelan-specific adoption matrix

| Owner / module | Decision | What to borrow | What **not** to borrow |
|---|---|---|---|
| #789 Hooks / #179 Policy | **P0 BORROW_PATTERN** | immutable call identity+pre-execution gate; normal vs notification callbacks; cannot skip policy when plugin returns early | unrestricted ADK plugin runtime or short-circuit as auth |
| #296 Context / Memory | **P1 BORROW_PATTERN** | compaction survivor pairing: pending call/results + parallel siblings, branch-visible context, temp/persistent separation | second session store, lossy truth editing, private ADK scope fields |
| #790 MCP / #253 Pack | **P1 BORROW_PATTERN** | per-invocation tool catalog cache/provenance; discovery failure must not bypass filtering; tool descriptions untrusted | new MCP SDK, plugin installer, account pool |
| #1546 Durable / #1191 Recovery | **ALREADY_REUSED + P0 TEST** | atomic append vs stale session, crash/resume tamper fixture | ADK timestamp stale check as exactly-once guarantee |
| #1527 Multi-executor | **NO DIRECT RUNTIME REUSE** | external harness event adapter idea if paired benchmarks show value | replacing OpenCode/Codex/Claude executors with Google-only ADK loop |
| #1267 / #1342 / #1531 Cost | **NO INCREMENT** | trace call IDs as possible evidence tags | duplicate Magpie ledger / budget |
| #1561 Product UX | **P2 BORROW_PATTERN** | explain “waiting for approval / stale call / compressed tool history / tool unavailable” without exposing raw protocol logs | exposing internal framework events as authority |

## 3. Minimum falsifiable, provider-free tests (NOT RUN)

1. **Security P0:** create an approved pending call with digest/signature -> mutate args/name/call_id/tool version/policy revision before resume; ensure host re-authorization and identity validation rejects **before** any side effect. Replay identical approved call after crash: no duplicate side effect; if external receipt unknown, park as UNKNOWN. Rotate key and test old/new retention.
2. **Plugin P0:** callbacks A (early return), B (security deny), C (audit): A must **never** suppress independent host gate B, and notification C is recorded best-effort. Repeat via simulated SDK and MCP paths, including discovery fallback tool that bypasses normal tool-filter.
3. **Compaction P1:** 100+ events, pending tool call compacted away, response arrives after resume, 2 concurrent siblings, reused call IDs, restricted subagent branches; compare baseline vs dependency-preserving projection for valid call-response pairs and admission of out-of-scope events; verify immutable raw evidence.
4. **Context economy P1:** fixed tasks, identical acceptance and model/harness; measure projection overhead, cached input tokens, untrusted tool description overhead, acceptance success and full cost (including recovery/review). No-go if context bloat / latency / mispairing worsens.
5. **Stale writer P0:** two simultaneous session writers on frozen state with network response loss; session commit must preserve conflict evidence and never authorize external side effect solely from timestamp or session write success.

## 4. Decision and boundary

**SELECTIVE_DESIGN_REUSE.** Priority (a) P0 stored tool call integrity + independent host gate test, (b) P1 compaction call/response reconciliation, (c) P1 scope/context tool catalog, (d) P2 operator-facing explanations. These are **hypotheses**, not measured Nerelan benefits.

No copy, no dependency, no model calls, no plugin installation, no remote production, no changes to existing Owner authority, no CI/review claim. Draft R1 docs-only PR, then exact-head CI and independent review per [AGENTS.md](https://github.com/dddd2024/Nerelan/blob/853a787143ef738e421b8efc637a7b8905629e0b/AGENTS.md). New implementation work belongs to existing Issues; do not open another executor/plugin/context TaskStore owner.

---

## Research provenance / merge hygiene

The upstream code references above are pinned to `c6586f19ab8a2bb8b53e70041633b10858d9902e` and Nerelan source references to `853a787143ef738e421b8efc637a7b8905629e0b`. Future implementation must recheck current upstream/main and run separate provider-free fixtures. Since the canonical research index is still under open stacked PRs, the Research Hub issue #1576 is the canonical new-entry tracker until gated merge/reconciliation. Do not introduce another permanent research index in this branch.
