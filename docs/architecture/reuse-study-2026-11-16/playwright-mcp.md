# Playwright MCP — core tool-level trust audit (2026-11-16)

**Research Issue:** [#1598](https://github.com/dddd2024/Nerelan/issues/1598) · **Canonical hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

**Source-only / R1 / no execution authority:** No package installed, no browser started, no model calls, no tests executed, no source copied. This report is not an acceptance result and does not authorize modifying security policies, connecting real personal browser sessions or taking credentialed actions. Direct Playwright SDK adoption is a hypothesis pending dependency and runtime approval.

# Playwright MCP: deep source audit of structured browser tools, default unsafe code, WebMCP and Nerelan guardrails

**2026-11-16 | RESEARCH_ONLY | STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / NO_IMPLEMENTATION_AUTHORITY / DOCS_ONLY**

**One project with two source locations:** [microsoft/playwright-mcp release/packaging repository](https://github.com/microsoft/playwright-mcp/commit/78eca85361efb545a4c0f59b6140aef0721c5412) fixed at 78eca85361efb545a4c0f59b6140aef0721c5412 (Nov 11, 2026), and [microsoft/playwright monorepo core implementation](https://github.com/microsoft/playwright/commit/b4d016aadc5cbd2b898a284307975fe73e05483d) fixed at b4d016aadc5cbd2b898a284307975fe73e05483d (Nov 14, 2026). Both Apache-2.0. The former's package.json pins playwright-core version **1.66.0-alpha-2026-11-09**, so the later core source is a separately pinned source snapshot and **not proven bit-identical** to the distributed npm alpha. This is a required pre-install version-verification gate.

**Nerelan comparison:** [main 57637b338b896f00f966c60a5c67f3e0e9848c4e](https://github.com/dddd2024/Nerelan/commit/57637b338b896f00f966c60a5c67f3e0e9848c4e).

## 0. Pre-study dedup and ownership

Checked [research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576), the initial six studies, seven subsequent pinned study issues (#1578, #1581, #1585, #1587, #1590, #1592, #1594), 19 archived historical studies, and live GitHub Issue searches for "playwright-mcp" and "microsoft/playwright-mcp". The browser execution product direction is already explicitly owned by [#802](https://github.com/dddd2024/Nerelan/issues/802). The preceding [Browser Use 1.0 #1594](https://github.com/dddd2024/Nerelan/issues/1594) concerned a **different** Python-REPL-based browser Agent. No independent pinned Playwright MCP source-level deep dive was found. This record adds implementation evidence only. No duplicate browser implementation Issue, MCP owner or Agent loop.

Existing owners: #802 Browser Use (primary); #790 MCP runtime and tool ingress; #179 host authority; #299 OS isolation; #447 egress; #798 context privacy; #253 Pack; #296 context economy; #1531 usage/cost; #803 post-action review. Keep AGENTS.md's explicit prohibition on browser-side shell/filesystem/credential authority.

## 1. Source provenance matters: wrapper != core

The release repository's [src/README.md](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/src/README.md), [AGENTS.md](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/AGENTS.md) and [index.js](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/index.js) state that the published package reexports a bundled Playwright-core implementation. The real MCP server and tool handlers are in Microsoft Playwright monorepo packages/playwright-core/src/tools/mcp and packages/playwright-core/src/tools/backend. Static source check covered both. Never infer runtime safety from packaging README alone or import assumptions from another Playwright version.

## 2. Verified mechanisms and selective reuse

### A. Structured semantic browser operations — P1 BORROW_PATTERN / conditional direct SDK reuse

[Core snapshot.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/snapshot.ts) implements accessibility snapshots and semantic target references for click, select, drag and related actions; [form.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/form.ts) implements structured form filling. [BrowserBackend](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/browserBackend.ts) validates known built-in tool input through Zod and exposes tool result/error representation. [Packaged tests](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/tests/capabilities.spec.ts) pin tool inventories and navigation snapshot shape.

Borrow narrow observe -> resolve semantic target -> HOST side-effect class/authorization -> act -> reobserve -> postcondition evidence. A click is potentially a create/send/delete operation and semantic targeting does not itself grant permission. Deterministic Playwright SDK with Nerelan-owned narrow functions may be safer and lower-maintenance than exposing this entire MCP server to an untrusted model.

### B. P0 hard gate: browser_run_code_unsafe included in DEFAULT core tools, RCE-equivalent

[Core runCode.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/runCode.ts) defines browser_run_code_unsafe with capability **core**, an arbitrary JavaScript function (or filename), vm.createContext / vm.runInContext and an explicit upstream description: "Unsafe: executes arbitrary JavaScript in the Playwright server process and is RCE-equivalent". Node vm context is NOT a security sandbox. [Core tools.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/tools.ts) includes **all** capabilities whose names start with core by default, with optional --caps only ADDING other capabilities; [packaged capabilities.spec.ts](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/tests/capabilities.spec.ts) expects this tool in its default list. Official [code execution docs](https://playwright.dev/mcp/tools/code-execution) independently warn.

**Decision P0 NO-GO for unfiltered Playwright MCP.** Exact allowlist filtering MUST be enforced on actual tools/call before the backend, *not only* hidden from the model's tools/list. Block guessed or stale names. If no fail-closed host gate exists, do not install/use as a privileged Nerelan agent tool. Keep high-risk server in isolated OS environment even when ingress policy is enforced. Client filtering alone must be verified to apply to every route, including MCP SDK access and reconnect.

### C. Other core tool risks, WebMCP and user-provided data

[Core evaluate.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/evaluate.ts) exposes browser_evaluate as core, running JS in PAGE context (different threat model than server-process RCE); [network.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/network.ts) exposes network request headers and bodies through core tools; [files.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/files.ts) exposes browser_file_upload and browser_drop paths as core. All require host-scoped permissions, secret/context redaction and upload roots, not mere schema validation.

[Core webmcp.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/webmcp.ts) collects tools from page main and embedded frames, with tool schemas/descriptions/results explicitly marked as **page-provided, untrusted**. [Config declaration](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/mcp/config.d.ts) says experimental WebMCP is enabled by default. BrowserBackend falls back to page-supplied tool handlers for unmatched built-in names. Page-provided tool hints are not authorization or verified read-only status. **Default deny** WebMCP in pilot, and if enabled later, bind frame origin + current page + tool name + args + operation ID and rerun final host authority.

### D. Network, local files, HTTP endpoint and profile isolation are not sufficient security

[Core config.d.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/mcp/config.d.ts) documents **network.allowedOrigins defaults to allow all**, secrets and redactUrlParams are convenience *not a security feature*, and allowUnrestrictedFileAccess is a guardrail that deliberate actors can work around. [Core context.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/backend/context.ts) implements browserContext.route for allowed/blocked origin policies, workspaceFile/checkFile and allows special code-origin trust bypass for file paths. Browser-level interception != OS network egress firewall, especially with server-process arbitrary JS. Restrict destination and upload files at a trusted Nerelan broker.

[Core HTTP transport](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/utils/mcp/http.ts) has HTTP Host checks to resist DNS rebinding and supports SSE/streamable sessions. Host validation is NOT user authentication: do not bind broad public interfaces without an independent authenticated gateway/allowlisted caller. [Core program.ts](https://github.com/microsoft/playwright/blob/b4d016aadc5cbd2b898a284307975fe73e05483d/packages/playwright-core/src/tools/mcp/program.ts) supports sharedBrowserContext versus per-client isolated context in a shared browser. Never equate working-directory-derived browser profile names with Owner identity, or mix authenticated user sessions across Task/Agent identities.

### E. Cost/UX: don't assume MCP is always cheapest

[Upstream README](https://github.com/microsoft/playwright-mcp/blob/78eca85361efb545a4c0f59b6140aef0721c5412/README.md) explicitly suggests CLI+SKILLS may use fewer tokens than MCP for coding agents (smaller tool schemas and snapshots), whereas MCP is useful for iterative stateful browser exploration. This is a vendor description, not a controlled Nerelan cost study. Borrow small/bounded accessibility slices and use direct SDK/CLI for deterministic acceptance. Measure real Magpie requests, cache hits, wall-clock, retries, browser start and teardown, and **successful independently accepted task total cost**. Do not build a second AgentLoop, TaskStore, scheduler, usage system or credential store.

## 3. Nerelan source mapping and implementation ownership

Nerelan [task_runtime.py](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/platform_v1/task_runtime.py) has an executor-neutral contract; [task_execution.py](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/platform_v1/task_execution.py) owns TaskStore evidence and executor result acceptance; [capability_registry.py](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/reverse_agent/platform_v1/capability_registry.py) is only metadata, NOT execution authorization. Existing frontend Playwright E2E tests prove known product journeys, not generic Browser Use. Magpie remains model account/usage settlement.

| Nerelan module | Classification | Concrete adoption boundary | Owner |
|---|---|---|---|
| Browser semantic tools | P1 BORROW_PATTERN / DIRECT_SDK_CANDIDATE | a11y refs, Zod argument schema, re-observe and postcondition | #802 |
| Unfiltered Playwright MCP | P0 NO-GO | default server-process RCE-equivalent core tool | #790 #179 #299 |
| Dynamic page WebMCP | P0 DEFAULT_DENY | page-authored tool metadata never grants host capabilities | #802 #447 |
| Network, upload, credentials | P0 NEGATIVE_TEST | explicit origins + OS broker, approved artifacts, no headers/bodies leak | #447 #798 #299 |
| Session/profile/MCP transport | P1 BORROW_PATTERN | isolated browser context and explicit host identity; no shared cross-user session | #802 #790 |
| Context and economic tests | P1 EVAL_CANDIDATE | SDK vs restricted MCP vs CLI+SKILLS on same accepted tasks | #296 #1531 |
| Durable evidence/permission | KEEP NERELAN | TaskStore/approval/postcondition, no second run truth | #179 #1546 |

## 4. Falsifiable tests — NONE EXECUTED

**T1 Default exposure/deny (P0):** provider-free fake MCP site, verify packaged exact version default list exposes browser_run_code_unsafe plus browser_evaluate, browser_file_upload, network-request tools; then assert Nerelan's host filter denies both listing and real tools/call for unsafe, guessed, cached, direct-SDK, reconnect paths, with backend invocation count ZERO.

**T2 Untrusted WebMCP (P0):** hostile iframe registers misleading read-only/consequential tool and duplicate tool names; verify disabled default and explicit final authority if enabled. Frame-specific provenance never mints Owner approval.

**T3 Origins and server egress (P0):** test blocked page subresources/private IP and DNS change, browser allowedOrigins default-open behavior and server-process JS outgoing request; assert network/isolation broker blocks unauthorised targets even outside context.route.

**T4 Upload/private content (P0):** Symlink and out-of-workspace file upload, read of dummy Bearer header from browser_network_request, storageState and screenshot exposure, redaction at model/evidence boundary. Zero unauthorised file bytes.

**T5 Non-idempotent form (P0):** simulated Submit completes remotely, response lost and MCP reconnects; Nerelan readback must settle effect or park BROWSER_SIDE_EFFECT_STATE_AMBIGUOUS, never click again without evidence.

**T6 Quality/cost head-to-head (P1):** matched fixture tasks, fixed browser capabilities and acceptance for direct Playwright SDK, restricted Playwright MCP and Playwright CLI+SKILLS; measure tool schema/AX tree tokens, cache, total provider requests, startup latency, failure/rework and total verified-task dollars. No generic presumption CLI or MCP is cheaper.

**T7 Exact-binary provenance (P1):** inspect npm release tarball's playwright-core alpha mapping before any R2 install/R3 binary execution; fail closed on mismatch between fixed source-based review and actual package.

## 5. Decision and evidence limitations

**SELECTIVE_DIRECT_PLAYWRIGHT_SDK_REUSE + P0 NO_GO_DEFAULT_UNFILTERED_MCP + CONDITIONAL_FILTERED_MCP_PILOT.** The differentiator versus Browser Use #1594 is that even a "semantic-first" MCP backend can expose an unsafe default code tool and page-supplied dynamic tool surface. Best initial route is narrow host-owned Playwright SDK actions with semantic snapshots; a full MCP server is optional and requires enforced per-call allowlist, network/OS isolation, no raw personal browser profile, and independent postcondition verification.

No npm package installed, no server or browser launched, no screenshot/website visited, no test run, no provider call, no exploit reproduced, no cost benchmark, no CI/independent verdict/merge. This is R1 documentation only and does not grant R2/R3 permissions.

---

## Provenance, review and integration caveats

- The **single product** is Microsoft Playwright MCP, whose code is divided between the published package wrapper and the Playwright monorepo. Record both snapshots; do **not** claim the Nov 14 monorepo code is identical to the packaging repo's pinned Nov 09 npm alpha without inspecting that artifact.
- Nerelan main compared at `57637b338b896f00f966c60a5c67f3e0e9848c4e`.
- This report is a research addition to permanent browser owner [#802](https://github.com/dddd2024/Nerelan/issues/802); #790 remains MCP gate, #299 OS sandbox, #447 egress and #179 host authority. No second AgentLoop/TaskStore/tool-policy authority.
- Only a **Draft docs PR** is in scope; leave in Draft until exact-head baseline/state-gate and independent review meet AGENTS.md requirements. Do not assert independent review, CI, merges or runtime benchmark were completed.
- Canonical index is the dated comment in [#1576](https://github.com/dddd2024/Nerelan/issues/1576); do not add duplicate index file while earlier stacked research index work is unresolved.
