# Nango — external account selection and OAuth lifecycle, pinned source deep dive

**Research:** [Issue #1592](https://github.com/dddd2024/Nerelan/issues/1592) · **Canonical index:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Date:** 2026-11-16.

**Evidence level:** `STATIC_SOURCE_REVIEW / NOT_TESTED / NOT_INSTALLED / NO_IMPLEMENTATION_AUTHORITY`. This is R1 documentation only. No Nango source copied, no ELv2 code imported, no network integration, credentials, Model API calls, CI or independent review are claimed.

# Nango deep source audit — connector/account selection, OAuth refresh, Agent Session scopes and ELv2 no-go

> **2026-11-16** · **STATUS:** `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / NOT_IMPLEMENTED / DOCS_ONLY`  
> **Single upstream:** [NangoHQ/nango](https://github.com/NangoHQ/nango) @ [`6cbf922512e5bffe1beec7ee1a100225b53b41d8`](https://github.com/NangoHQ/nango/commit/6cbf922512e5bffe1beec7ee1a100225b53b41d8). **Root license: Elastic License 2.0 (ELv2), NOT Apache-2.0/MIT.** GitHub's `NOASSERTION` SPDX detection and [actual LICENSE](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/LICENSE) checked.  
> **Nerelan compared:** [`main@57637b338b896f00f966c60a5c67f3e0e9848c4e`](https://github.com/dddd2024/Nerelan/commit/57637b338b896f00f966c60a5c67f3e0e9848c4e).

## 0. Duplication gate

Read [canonical study hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) original six static source studies, all follow-up dated entries #1578 SWE-ReX, #1581 Google ADK, #1585 ACP Python SDK, #1587 Kimi Code, #1590 ToolHive, older 19-item provenance, and GitHub repo issue searches `Nango` and `NangoHQ/nango` (both zero). The 11/15 cross-category comparison already includes model-gateway providers; it does **not** substitute for Nango's SaaS OAuth/connector lifecycle. Adjacent studies #1567 Composio (hosted tool/connection session) and #1590 ToolHive (MCP proxy/runtime) share some *concepts* but do not review Nango's specific credential refresh, connection ambiguity, connect-session and OAuth redirect code. No existing project-specific Nango audit found. This Issue is a **new source-evidence report**, NOT an implementation owner.

Owners already exist: [#790](https://github.com/dddd2024/Nerelan/issues/790) MCP/connector runtime (primary), [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack, [#287](https://github.com/dddd2024/Nerelan/issues/287) configuration/Connection UX, [#179](https://github.com/dddd2024/Nerelan/issues/179) host authority, [#303](https://github.com/dddd2024/Nerelan/issues/303) repo-controlled MCP config trust, [#447](https://github.com/dddd2024/Nerelan/issues/447) egress/secret scanning, [#299](https://github.com/dddd2024/Nerelan/issues/299) sandbox; [#1342](https://github.com/dddd2024/Nerelan/issues/1342) / #1531 for *separate* Magpie model-account usage. Do not create another connector or account-system implementation issue.

## 1. Key findings, pinned to actual code

### A. Account selector ambiguity: **P0 BORROW_PATTERN**, no arbitrary account choice

[`agentSessionConnections.service.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/services/agentSessionConnections.service.ts) `resolveTenantConnections` and `pickConnectionPerIntegration`:
- Looks up connections under **environment** and tag selectors; pin a precise (integration_id, connection_id) if needed.
- Explicitly reports `unknown_pinned_connection`, `pinned_connection_not_matched` and `ambiguous_connections`, with bounded candidate sample. A provider with 2 matching accounts does **not** silently select one. Uses `Map` to prevent `__proto__` key loss.
- **Proposed Nerelan**: map `User/Owner identity × connector_id × external account identity × Task/Run scope`. A task's GitHub/Google/etc account must be pinned or intentionally selected by a trusted host; report `MULTIPLE_MATCHES`, `NOT_CONNECTED`, `OUT_OF_SCOPE`, `REVOKED` separately. Do not infer resource access merely from same provider or login. This is different from **model-account** pooling/cheapest-healthy switching in Magpie: swapping external write principals during a long task can be unsafe.

### B. Session token lifecycle with hashed storage: **P1 BORROW_PATTERN**, not Owner authority

[`agentSession.service.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/services/agentSession.service.ts) `runCreation` builds one resolved-connection map + compiled toolset, then inserts session **and mints token in one DB transaction** (failed token mint rolls back). `createAgentSessionToken` stores only hash, binds accountId/environmentId/entityUuid and TTL, returns raw token once. `endAgentSession` sets ended_at/reason and removes corresponding keys **in transaction**. Default expiry constant is **15 days** and explicit `createConnection` meta-tool is **disabled by default**.
- **Borrow**: snapshot and validate the selected connection IDs and compiled tool-capabilities at admission; mint a short-lived host-issued connector call capability; revoke/expire on disconnect, policy revision, task completion or Owner Stop. Evidence should include only ids/digests, not credentials.
- **Reject** default 15-day token for a high-privilege unattended Agent/Run. Nango code itself says unified authorization grants are still planned: an Agent Session bearer token, even hashed at rest, is not an Owner approval or proof of tool rights. Execute-time host policy and freshness/side-effect guard required.

### C. Toolset policy and actual tool execution: **P0/P1 BORROW_PATTERN**, wildcard risk

[`agentSessionToolset.service.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/services/agentSessionToolset.service.ts): `toolset=undefined` means all **connected integrations**, `toolset='*'` means all environment integrations even disconnected; explicit allow/deny/pinned names validated and invalid names fail compilation. Particularly good: **typos in deny names cause failure**, not silent allow. Discovered MCP tools can be added mid-session filtered by stored policy.
[`execute/execute.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/controllers/agent/mcp/execute/execute.ts): checks the requested integration is in `session.compiledToolset`, finds permitted named tool, resolves session's connection, re-checks that deployed action is still enabled, emits provenance/operation telemetry and returns distinct error classes; `RETRY_MAX=0` on its legacy action path prevents automatic duplicate retries there, but does **not** establish exactly-once for all tool paths.
- **Borrow**: strict known tool names including deny-list typo validation, `pinned vs searchable`, mid-session capability revision tracking, and execution-time recheck. **Reject broad defaults**: Nerelan should default to no third-party write tools unless Owner/policy explicitly allows. Do not treat allowed tool discovery as a grant to call it.

### D. OAuth refresh and failure states: **P1 BORROW_PATTERN**, locks are NOT durable fencing

[`credentials/refresh.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/shared/lib/services/connections/credentials/refresh.ts):
- Separate credential types that can refresh, credential types that can only be verified, and unknown/opaque credentials. Distinguishes `refresh_exhausted` / `connection_refresh_backoff` / success / failure and records counters/timestamps. Manual `instantRefresh` bypasses cooldown but not account/session authority.
- `inFlightRefreshes` deduplicates concurrent refresh calls **within one process**, keyed by environment+provider+connection; a Redis TTL tryAcquire coordinates elsewhere. **Upstream code explicitly says this is not a robust distributed lock**, unsafe across multi-Redis or Redis crash. It also obtains current credentials after acquiring/waiting on lock to avoid refreshing tokens already refreshed by another worker.
[`crons/refreshConnections.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/crons/refreshConnections.ts) periodically checks stale connections under a bounded cron lock.
- **Borrow** for *external connector OAuth health*, not for Magpie subscription limits: `CONNECTED / REFRESHING / EXPIRED / REAUTH_REQUIRED / BACKOFF / UNAVAILABLE` with explicit reasons and user-facing re-link instructions. Preserve host-managed secrets and operation retry policy.
- **Reject** copying Redis TTL lock into Nerelan durable Goal/Task exactly-once side effects; cannot assume one refreshed OAuth token means previous tool side effect never happened.

### E. Token egress/SSRF defense: **P0 BORROW_PATTERN**, close gap at redirect

[`outbound-policy.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/shared/lib/services/proxy/outbound-policy.ts) resolves different outbound policies for proxy, OAuth and MCP OAuth. The OAuth Axios path uses a safe HTTP agent/pinned lookup, validates every redirect URL, caps hops and strips all non-benign headers **at each redirect, including same-origin redirects**; the fetch path has a separate manual redirect policy because DNS pinning alone doesn't cap hops.
[`agent/mcp/proxy/proxy.ts`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/packages/server/lib/controllers/agent/mcp/proxy/proxy.ts) verifies integration is in the session, finds its selected connection, refuses caller-provided reserved auth headers, and only then sends the authenticated request.
- **Borrow**: independent host-owned HTTPS/OAuth redirect allowlist+DNS rebinding checks, credential stripping before every 30x, strict audience/endpoint binding; actual execution route still requires tool scope and final host permission. **Do not** copy Nango's HTTP client, OAuth server, private token storage or untrusted custom host override.

### F. License and scope: **hard NO-GO for code copy or default hosted reuse**

[`LICENSE`](https://github.com/NangoHQ/nango/blob/6cbf922512e5bffe1beec7ee1a100225b53b41d8/LICENSE) is **ELv2**. It restricts offering a substantial set of the software's features to third parties as a hosted/managed service and includes notices and key-protection conditions. This makes the binary/source-copy route materially different from Apache/MIT projects previously studied. **Decision:** no source file copying/vendor, derivative code, Nango runtime bundle, or shared multi-tenant hosted connector service based on it without specific legal review. High-level design-pattern observation is not the same as licensed code reuse. Even self-host or a service integration warrants a separate R2/R3 licensing/dependency/security/product decision. This is an engineering gate, **not** legal advice.

### G. Keep existing Nerelan code and role boundaries

Nerelan [`model_access/os_vault.py`](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/model_access/os_vault.py) already implements host-only, fail-closed Windows Credential Manager (and fake vault), connection-authority-bound secret reference, no plaintext fallback. [`model_access/credential_relay.py`](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/model_access/credential_relay.py) already binds **model provider** short-lived leases to execution snapshots with model/endpoint/time checks and no secret disclosure. [`platform_v1/capability_registry.py`](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/platform_v1/capability_registry.py) is explicitly a non-executing metadata/Pack registry, not a service-account OAuth client. Existing #790 should define any external connector auth adapter and #287 its reconnect/ambiguity UX.
- **Already built / keep** the vault and model relay (model usage separate).
- **Missing direction / not an established bug**: user-controlled external SaaS connection selection, refresh/revocation and source-specific API scope for heterogeneous Agent tool calls; not proven absent in every runtime without integration tests. 
- **Do not** take Nango's sync/records engine, 1000 integrations, job service, multi-tenant PostgreSQL+Redis stack or billing dashboard as a dependency. They do not solve Nerelan's primary quality-adjusted cost benchmark and would create more code/maintenance.

## 2. Reuse matrix

| Module | Decision | What to borrow / keep | Owner |
|---|---|---|---|
| Agent × external account selection | **P0 BORROW_PATTERN** | fail ambiguous, require exact pin or explicit host selection; stable account per stateful task | #790 #287 |
| External OAuth auth/refresh/reauth | **P1 BORROW_PATTERN** | classify refreshable/test-only/expired/exhausted/backoff; distinct retry/reenable states | #790 |
| Short-lived session & tool scope | **P0/P1 BORROW_PATTERN** | hash-only stored token, atomic mint/revoke, allowlist validation, tool recheck | #790 #179 #253 |
| OAuth outbound/SSRF | **P0 BORROW_PATTERN** | redirect hop validation, strip credentials, host-bound endpoints and no arbitrary override | #447 #790 |
| Model account pooling & usage | **KEEP EXISTING** | Magpie's model/subscription inventory and true request spend, not Nango's SaaS OAuth | #1342 #1531 |
| Memory/Agent Loop/Durable TaskStore | **NO_DIRECT_REUSE** | existing Nerelan context, approvals, receipt and resume | #296 #1546 |
| Nango code, service or SDK bundle | **NO-GO P0 license** | ELv2 needs independent legal/dependency decision; no code copying | R2/R3 governance |

## 3. Minimal falsifiable tests — **NOT RUN**

1. **Ambiguous accounts, P0:** same GitHub provider, two accounts under same tags, Agent requests write; no silent choice/no write. Named pinned account absent/out-of-scope/revoked gets explicit block and safe re-selection. Repeat across concurrent Tasks with different scopes.
2. **Session lifecycle, P0:** simulate atomic session/toolset/token creation failure; after task stop/approval revocation/expiry, old capability cannot call; no long-lived implicit `allow all`; no raw credential appears in TaskStore/event/context/browser.
3. **Toolset deny mutation, P0:** typo in deny rule, stale tool catalog, newly discovered MCP tool, disabled action, tool already running at revoke. Final effective request must pass host authority even if model-facing catalog is stale.
4. **Refresh concurrency, P1:** 20 workers, two processes, Redis lock expiry/multi-Redis/connection refreshed in another worker, token revocation and manual refresh; cannot double issue invalid rotating refresh tokens or quietly mark healthy; hold as REAUTH/UNKNOWN with reason if inconclusive. This test concerns connector token refresh, not durable task lease correctness.
5. **SSRF/redirect, P0:** redirect from approved OAuth endpoint to private-IP/loopback, DNS rebinding, same-origin 302 with Authorization/Cookie/Proxy-Authorization/custom API key headers, cross-origin, endless hops; zero credential leakage and explicit bounded error.
6. **Economics/UX, P1:** mock GitHub/Google connector; compare official SDK + thin Nerelan adapter vs a hypothetical Nango integration for auth freshness, connect errors, operator touches, latency, untrusted dependencies, and maintenance cost. Do not claim cost or quality improvement from code reading. License gate blocks runtime Nango evaluation unless separately authorized.

## 4. Final verdict

**`SELECTIVE_BORROW_PATTERN / DIRECT_CODE_REUSE_NO_GO_ELV2`**. Highest-value incremental Nerelan features are **ambiguous external-account fail-closed selection** and **reliable OAuth refresh/reconnect classification**, followed by **redirect-time credential protection and ephemeral session/tool-scope guards**. These should feed existing #790/#287/#447 contracts, not a separate Nango-derived runtime. No external integration execution, no credentials access, no tests, no CI, no independent review and no merge are asserted. Research Issue + R1 docs-only Draft PR + hub update, under existing AGENTS.md governance.

---

## Research provenance and governance

1. Upstream fixed at `NangoHQ/nango@6cbf922512e5bffe1beec7ee1a100225b53b41d8`. The root LICENSE text is Elastic License 2.0; distinguish it from its license detector's `NOASSERTION` output.
2. Current Nerelan main fixed at `57637b338b896f00f966c60a5c67f3e0e9848c4e`.
3. No implementation task or direct code reuse authorized. All experiments are proposals and remain unrun.
4. This report must remain a Draft PR until AGENTS.md exact-head gate and independent review; do not mark merged or ready because the static audit exists.
5. Existing research hub [#1576](https://github.com/dddd2024/Nerelan/issues/1576) owns the canonical per-round item; avoid a competing index while the stacked historical research-index PRs are pending.
