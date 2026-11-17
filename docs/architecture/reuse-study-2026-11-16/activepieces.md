# Activepieces — Nerelan 插件连接器与 Agent 工具发现深度复用审计

> [Research Issue #1668](https://github.com/dddd2024/Nerelan/issues/1668) · R1 docs-only · 2026-11-17 · static source fixed on GitHub · no runtime approval

# Activepieces — pinned code audit of typed Pieces, AI tool discovery, credentials and executor boundaries

RESEARCH_DATE: 2026-11-17
UPSTREAM: activepieces/activepieces@43f1bd074c501e6cb228d1e3621215c7369cfe5c (root version 0.94.0)
NERELAN_MAIN: 6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b
RISK: R1 docs-only / static source reading
STATUS: not implemented / not tested / no runtime authority

## 0. Before-research duplication gate
Reviewed the [canonical hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) with **36 completed archived comments**, searched GitHub Issues, PRs and Nerelan code for `Activepieces` and `activepieces/activepieces`; no prior *standalone pinned-source Activepieces study*. Similar upstream research Dify Plugin Daemon #1571, Composio #1567, Nango #1592, ToolHive #1590, Agent Zero #1659 and NeMo Guardrails #1665 do not duplicate this source audit. One project per turn. Focus: typed connector packages, user/agent affordances, lazy tool search, runtime/credential ownership and licensing.

Pinned source: [Activepieces commit](https://github.com/activepieces/activepieces/commit/43f1bd074c501e6cb228d1e3621215c7369cfe5c) and [Nerelan main@6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b](https://github.com/dddd2024/Nerelan/commit/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b).
LICENSE: [root LICENSE](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/LICENSE) grants MIT-Expat for software outside excluded enterprise locations, but the same text explicitly carves out `packages/ee/` and `packages/server/api/src/app/ee`; [packages/ee/LICENSE](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/ee/LICENSE) requires a separate Enterprise license for production and restricts commercial copying/use. DO NOT classify the Agent/AI runner under `app/ee` as MIT-source or recommend code copying. General TS Piece framework is in `packages/pieces/framework` and MIT-eligible subject to notices/other component licenses.

## 1. Exact code findings and module-by-module disposition

| Upstream unit / evidence | Actually implemented | Verdict for Nerelan |
|---|---|---|
| [Piece metadata / schema](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/pieces/framework/src/lib/piece-metadata.ts#L13-L67) | Version, category, authors, auth, min/max supported release, deprecation, actions/triggers; optional `audience = human/ai/both`, `aiMetadata.description`, `aiMetadata.idempotent`, and `classification = READ/SEARCH/WRITE/DESTRUCTIVE` | **BORROW_PATTERN P0/P1:** add descriptive Pack action/trigger metadata. Risk/idempotency are UNTRUSTED AUTHOR DECLARATIONS; not Host permission, proof of external idempotence or accepted outcome |
| [Piece factory](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/pieces/framework/src/lib/piece.ts#L15-L103), [Action factory](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/pieces/framework/src/lib/action/action.ts#L8-L100) and [Trigger](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/pieces/framework/src/lib/trigger/trigger.ts) | Typed `createPiece`, `createAction`, `createTrigger`, error-handling defaults; Piece can use multiple distinct auth types; execution run/test functions held on runtime object | **BORROW_PATTERN P1:** separate schema-first discovery from executable runtime; not import TypeScript runtime into Nerelan Host; no automatic trigger subscription from metadata |
| [Agent metadata authoring](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/.agents/skills/piece-builder/ai-metadata.md#L1-L135) | Explains concise model-facing 'when to choose', named alternatives, true side effects, retry-safe vs non-idempotent, human/AI visibility. Static Zod schema fields OPTIONAL, guide says new Piece actions MUST supply these | **BORROW_PATTERN P1:** concise tool selection guidance, classify side effects based on `run()`, validate completeness in Nerelan registry; no false claim that schema enforces optional authoring guideline at runtime |
| [Lazy search / degradation](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/tool-search/tool-search.service.ts#L11-L140) and [MCP ap_search_actions](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/mcp/tools/ap-search-actions.ts#L7-L57) | Top5 default, cap20 via MCP, cosine retrieval over tenant/project/audience/modelVersion, overfetch50, `tau` no-match gate then enabled-pieces filter and connected flag, fallback to keyword if no embedder or embed API fails (mode + reason). Separates SEARCH ACTION -> GET PROPS -> RUN ACTION in tool description | **BORROW_PATTERN P0/P1** major value for long-context agent: staged discovery -> limited schema projection -> Host-authorized execution. Retrieval results NEVER imply permissions, authenticated connection availability or safe operation. |
| [Discovery failure semantics](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/tool-search/tool-search.service.ts#L119-L148) | On enabled-pieces resolution failure, code comments explicitly allow undefined -> no enabled filter (**fail-open catalog visibility**); keyword fallback omits some semantic audience/connection/threshold checks, reports mode keyword | **REJECT for Nerelan authorization**. Catalog suggestions may fail-open only if clearly labeled *untrusted search* and restricted to public metadata; final Host enforcement must fail-closed for unknown grants, connection, tenant and source. Prevent cross-project metadata leak before exposing descriptions. |
| [Piece install metadata](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/pieces/piece-install-service.ts#L12-L105) | ARCHIVE/REGISTRY package saved; install triggers `EXECUTE_EXTRACT_PIECE_INFORMATION` job through engine before metadata DB write; optional asynchronous per-tenant tool re-index | **BORROW_PATTERN P1** decouple catalog refresh and slow search embedding; **REJECT treating metadata extraction as passive/safe** without sandbox: engine may load source code to derive metadata. |
| [Runtime installer/cache](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/sandbox/src/lib/cache/pieces/piece-installer.ts#L49-L159), [piece-cache](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/sandbox/src/lib/cache/pieces/piece-cache.ts#L10-L83) | Validates package-name form, locks workspace with `memoryLock`, downloads bundle (3 attempts), calls `bunRunner.install`, rolls back partially failed installs, marks `ready` only after entry file checks. `bunfig.toml`: isolated linker, minimum release age 259200s; exact-version cache key + single-flight in process | **BORROW_PATTERN P1** versioned cache, concurrent fetch coalescing, install rollback, clear readiness states. **REJECT** just trusting package name / `ready` marker / memory process lock as cryptographic integrity, crash proof, or code execution sandbox; Host must enforce source digest/signature, sandbox and Owner grant. |
| [Actual action runner](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/engine/src/lib/handler/piece-executor.ts#L21-L153) | Uses pieceName+pieceVersion+actionName, resolved props with censored input, validation, auth passed into ActionContext, run step and pause/resume via waitpoint; `runWithExponentialBackoff` + per-action retry/continue metadata; ActionContext holds engineToken, server URLs, connection manager, file access, project and run control | **ALREADY_IMPLEMENTED PARTLY** Goal/TaskStore durable execution, Host Adapter, budget/authorization. **REJECT direct runtime**: handing third-party plugin Host-level token/secret/callbacks or retrying non-idempotent actions without external effect identity. |
| [OAuth2 connection UX](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/app-connection/app-connection-service/oauth2/oauth2-util.ts#L28-L65), [OAuth URL](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/app-connection/app-connection-service/oauth2/oauth2-util.ts#L132-L205), [refresh](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/app-connection/app-connection-service/app-connection.handler.ts#L40-L96) | OAuth scopes, S256/PKCE optional, expiry refresh 15 min early, token & secret fields redacted in returned connection representation; custom auth refresh as separate worker job | **BORROW_PATTERN P1** connection availability/status, visible required/granted scopes, expiry and request-purpose. **REJECT** second Magpie account manager or exporting credentials into model context; external SaaS OAuth connectors are distinct from Magpie model-account quotas. |
| [MCP project server](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/mcp/mcp-service.ts#L42-L83) and [permissions](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/mcp/mcp-permissions.ts#L6-L70) | Project/Platform MCP token rotate, disabled-tools, project roles when editionRequiresRbac. **Key detail**: non-RBAC edition returns `ALLOW_ALL`; a `Permission` missing value returns allowed. | **BORROW_PATTERN** project-level tool visibility and user-friendly disabled tool list; **REJECT** `ALLOW_ALL` as Nerelan default. Host Owner grant still mandatory, and `agent` package tools inside `app/ee` carry Enterprise license. |
| [Cloud catalog sync](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/pieces/piece-sync-service.ts#L22-L77) | Hourly OFFICIAL_AUTO registry fetch, batched per piece-version metadata, optional embedding reindex asynchronous; error logged and may leave stale metadata | **BORROW_PATTERN P2** versioned refresh, incremental tool search reindex; **REJECT** automatic upgrade/execution of new untrusted pieces under old owner grant. Source hash changes need new approval; provider-free startup essential. |
| [Large agent tooling](https://github.com/activepieces/activepieces/blob/43f1bd074c501e6cb228d1e3621215c7369cfe5c/packages/server/api/src/app/ee/agent/tools/piece-tool-runner.ts) | Input filler uses model, resolves piece, runs action; redacts auth in returned input and has domain restrictions | **RESEARCH ONLY due to Enterprise license**: conceptual pattern okay, do not copy or import this implementation into Nerelan. No legal conclusion beyond fixed license files. |

## 2. Specific Nerelan main comparison
- [capability_registry.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/capability_registry.py): bounded manifest and no plugin imports. Already has Pack starter; extend catalog metadata only. Owner [#253](https://github.com/dddd2024/Nerelan/issues/253).
- [task_runtime.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/task_runtime.py): ExecutorRouter and local validation; source of executor dispatch. Piece is neither OpenCode nor Codex/Claude execution agent. Owner [#1368](https://github.com/dddd2024/Nerelan/issues/1368).
- [goal_service.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/goal_service.py), [run_store.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/run_store.py): persistent Goal->Spec->Plan->Tasks, SQLite TaskStore, durable event+idempotency and interruption reconciliation. Do not import a second flow engine or promise that one Piece action implies accepted Goal.
- [Magpie adapter](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/model_access/magpie.py): default-off read-only model gateway observation. Do not conflate SaaS connector OAuth2 and Magpie model/account routing.
- Existing Owner Issues: [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack productization; [#790](https://github.com/dddd2024/Nerelan/issues/790) MCP/Connector lifecycle; [#287](https://github.com/dddd2024/Nerelan/issues/287) connection/setup UX; [#303](https://github.com/dddd2024/Nerelan/issues/303) untrusted project config/digest; [#299](https://github.com/dddd2024/Nerelan/issues/299) real OS sandbox; [#447](https://github.com/dddd2024/Nerelan/issues/447) MCP egress/prompt injection; [#379](https://github.com/dddd2024/Nerelan/issues/379) admitted memory/evaluation. **No new runtime owner**.

## 3. Concrete design: how to borrow the good parts without copying its runtime
1. DISCOVER: read-only Pack schema (ID, version/hash, license, authors, action/trigger list, explicit human|agent|both visibility, description, claimed risk and idempotency, required auth/scopes).
2. SEARCH: top-k semantic/keyword candidate summaries, mode=semantic|keyword|unavailable and no-match. Catalog metadata may be untrusted. Search is *not* grant.
3. INSPECT: lazily fetch exact action schema/JSON inputs and connection requirement for the chosen candidate; compare to pinned source/hash.
4. AUTHORIZE: trusted Host Owner grant, action ID, resolved argument VALUES and effects, target service/domain and project, credential grant, quota/budget, idempotency receipts. Unknown => no execute.
5. EXECUTE: official mature MCP/connector adapter in sandbox, never arbitrary Bun lifecycle inside trusted Host; token remains credential broker; TaskStore records request/effect state and independently verified output.
6. RECONCILE: if no receipt, distinguish action's declared idempotent hint from actual provider idempotency key; do not blind retry sends/creates. Waitpoints/trigger delivery use existing durable TaskStore and explicit event identity.
7. VALIDATE: independent evidence of task success + actual total cost and error category, not just API response 200 or a plausible workflow step.

## 4. User-facing flows to test later
- "给 Slack 频道发消息": search small candidate set; get Slack send action schema only after selection; display account scopes and non-idempotent warning; Host grant+confirm outside the tool metadata. Tool unavailable -> inform user rather than fallback to arbitrary HTTP with broad token.
- "查 GitHub 工单，再创建草稿 PR": allow safe read first, require separate write grant; execution receipt proof for PR creation; avoid duplicate PR if worker reconnects.
- "当收到新的 webhook 时继续 Goal": event subscription must be authorized, tied to Project/Goal event IDs and durable receipts; duplicate webhook must not launch duplicate work.
- "新社区 Piece 发布了新版本": visible catalog version can refresh, but existing approved source digest/permissions remain pinned until explicitly re-approved.
- "插件引擎暂时离线": search may downgrade to keyword and tell model, but authorization/cost/credential checks must not downgrade or bypass.

## 5. Proposed negative/regression test matrix — not run
T1 author-declared READ action actually writes => Host blocks as untrusted claim.
T2 action marked idempotent=true creates new record twice => provider receipt/real idempotency beats hint.
T3 semantic unavailable -> keyword fallback label preserved, context prompt not expanded to hundreds of tools.
T4 tenant enabled-piece resolution fails => reject cross-project private catalog disclosure and do not grant execution.
T5 search returns external Piece with no connection => inspect allowed, exec denied until credentials authorized.
T6 action named same across two versions => version/digest and auth/scopes exact, no silent reinterpretation.
T7 registry sync changes bundle under same version => digest mismatch blocks activation.
T8 malicious package name / traversal / symlink / bun lifecycle package => cannot run during read-only discovery; quarantine.
T9 package install process crash after write-before-ready => no false activated status; restart repair.
T10 concurrent installs from separate worker processes => per-process memoryLock not durable owner fence; atomic manifest claims required.
T11 OAuth scope escalation, missing refresh or invalid_grant => no secret leak and no silent broad authorization.
T12 community-edition `ALLOW_ALL` MCP policy => Nerelan Host must still deny unauthorized tools.
T13 malformed Action params/schema and action-specific write target => deterministic deny before external call.
T14 create/send webhook side effect timeout => don't duplicate on retries without provider/external ID.
T15 enterprise agent code import => license gate reject; only documented conceptual learning from restricted files.
T16 vendor API/embedding cost + runtime + retries vs actual accepted-task success; require meaningful benefit.

## 6. Final disposition and verification boundary
**BORROW_PATTERN P0**: staged find->inspect->Host-authorize->execute, risk and retry hints, sparse tool view, explicit fallback. **BORROW_PATTERN P1**: typed connector/action/trigger schema, connection scopes/status, versioned cache and installation recovery. **ALREADY_IMPLEMENTED**: Nerelan TaskStore/Goal/Executor/Owner/Magpie. **REJECT**: Activepieces workflow runtime, direct Node/Bun/npm package installation in trusted Host, enterprise Agent code or any default-open tenant/RBAC policy. **DEFER**: isolated existing connector integration until exact user task, licenses, security, and real total-cost A/B.

Static GitHub source inspection and comparison only. Not installed, cloned, executed, tested, benchmarked, licensed for EE copying, hooked into a real model account, or granted auth. No CI/review or runtime code changed.
## 7. 模块交叉对照：在 Nerelan 现有源码中放在哪里？

### 7.1 Pack 的“静态描述”与“动态执行”必须物理分离

当前主分支 `reverse_agent/platform_v1/capability_registry.py` 的工作是收集受限 JSON 能力描述，不加载外部 Python，不安装第三方扩展。这已经为 Activepieces 式 Piece metadata 提供了切入点。最小改动不是移植 TypeScript 包，而是定义类似下面的 **声明式只读数据**：

```text
PackMetadata:
  source {repository, revision, artifact_digest, manifest_version, license}
  actions:
    - {name, description_for_human, description_for_agent,
       audience, claimed_classification, claimed_idempotent,
       authentication_requirements, input_schema_ref, output_schema_ref}
  triggers:
    - {name, event_type, dedupe_key_contract, callback_scope, auth}
  capabilities {executor_compatibility, sandbox_needs, required_domains, secret_scopes}
```

其中 action 的 `classification` / `idempotent` 字段不能直接变成 runtime permission 或 task-level retry 判定。它们只有在宿主核实真实源码、网络权限和测试后才能被提升为可信能力约束。未核实的第三方元数据属于检索候选信息，不是 Owner grant。

### 7.2 索引是一种“召回层”，不需要成为第二套权限系统

Activepieces `tool-search.service.ts` 把工具目录向量检索与 tenant/project/audience、能力启停和连接可用状态分开：返回的是精简的 `pieceName`、`objectName`、名称、简述、`connected`，不直接把所有工具的 input schema 发给模型。其 MCP 接口 `ap_search_actions` 返回 top-k，再引导模型调用 `ap_get_piece_props`，最后 `ap_run_action`。

对 Nerelan 的价值：目前一个 Goal 可能拥有大量 Pack/Tool，全部展开给上下文会提高 token 和选择错误概率。可先用 Provider-free **名称/关键词检索** + action 分类、scope 过滤，接着按需检索准确 schema；当确有实际采样需求和预期成本收益时，再引入 pgvector/embedding。不要默认安装数据库向量扩展或增加第三方 Embedding 费用。

**上游真实风险提醒：** `resolveEnabledPieceNames` 失败时检索候选可退化成不施加 enabled 过滤，代码明确把这作为 fail-open catalog availability；关键词 fallback 并不完全执行语义检索的 audience/connection/τ 约束。Nerelan 若把目录用于项目私有 Pack，需要在目录可见性上也做租户隔离，不能直接照搬“展示全部检索结果”作为私有元数据的行为。**最重要的是检索成功不意味着工具已授权。**

### 7.3 Agent 选工具的“显式风险 + 重试”用户体验

Activepieces `.agents/skills/piece-builder/ai-metadata.md` 的实践可复制其设计思路：
- `human | ai | both`：减少 Model 看见自己不该选择的内部工具。
- 一句明确模型选择时机的简述，比长篇说明更有用。
- `READ / SEARCH / WRITE / DESTRUCTIVE`：足够简单，适合放在用户确认面板；但外部 HTTP 自定义调用是开放世界操作，不能相信作者给的 READ。
- `idempotent=true|false`：人工整理可帮助重试策略；自动判断必须依赖供应商业务 ID 和实际调用收据。
- 单 Action 的 output schema 有利于 Host 验证结果可解析，但不等于用户任务已经成功。

用户若说“帮我给团队发消息”，界面应该先显示具体渠道、账号、预估副作用和“不能安全盲重试”，而不是只显示工具名字并立即调用。用户若说“看一下新的工单”，可在 Host 的只读范围内执行但仍需符合网络/凭据权限。

### 7.4 连接器凭据必须同 Magpie 的模型账本解耦

Activepieces 同时支持 OAuth2、API Key、Secret、Custom Auth；其 OAuth 代码允许授权 Scope 选择、可选 PKCE、提前 15 分钟 refresh 和返回敏感字段打码。这有助于 Nerelan 未来的 SaaS Connection Center (#287) 设计：
- 告诉用户这个 Connector 需要哪些 scope，目前有哪些已授予；
- 支持多项目不同的连接实例，不要让模型自己猜哪个账号可用；
- 提供失效、过期、撤销的明确状态；无法 refresh 时不要静默升级权限；
- short-lived connection handle 经 Host 绑定具体任务调用，不把 access/refresh token 注入模型上下文。

**账户区分**：Magpie 的模型/API/订阅资源池是另一层；SaaS 的 Gmail/Slack/GitHub OAuth 不是 Magpie ModelBinding。不能为了复用 Activepieces OAuth 模块而引入第二个 LLM 网关，也不能把 Magpie 账户 token 与外部 Connector 凭据混放。

### 7.5 安装器具备成熟细节，但不是不可绕过的信任根

Activepieces 安装路径确实使用包名检查、按 rootWorkspace 的内存锁、bun isolated linker 和 release-age、bundle 下载重试/失败回滚、ready 标记等，这是实际工程细节。

但其 `memoryLock` 不是进程间/跨部署持久化 lease；`ready` + package entry 文件存在只能说明**当前实例可加载文件**，不能证明包内容是预审代码，也不能证明执行安全。通过 `bun install` 安装第三方内容是潜在代码执行边界，不能在 Nerelan Host/Owner/密钥进程里自动发生；在没有仔细验证相关 package scripts 的情况下不能断言已经发生攻击或触发哪些脚本。正确建议：`DISCOVERED -> HASH_CHECKED -> OWNER_APPROVED -> SANDBOX_INSTALLED -> ACTIVE`，外加错误后可恢复状态。

### 7.6 Trigger 与长跑任务恢复的真正关联

Activepieces 将 Trigger 从 Action 中分离，并在 Webhook/renew/onEnable/onDisable 事件里处理订阅。对 Nerelan 来说，未来的“当代码提交到 GitHub 时继续修复任务 / 外部告警到了继续分析”等用户需求应让 Trigger 成为 **Goal 的新事件来源**，而不是第二个任务运行时。

必须保证：
- EventId / external event dedupe key / source signature / Project 和 Goal 的绑定；
- webhook 重复投递不会重复派发一个有副作用的 Task；
- 授权与订阅本身可以独立撤销；
- 事件触发不绕过 Owner 窗口、预算、执行器可用性和独立验收。

### 7.7 许可证和安全边界的原样核查

源文件 `LICENSE` 说明 MIT 限于特定排除目录以外；`packages/ee/LICENSE` 对企业生产和商业复制有单独限制。这意味着本研究中读取的 `packages/server/api/src/app/ee/agent/tools/piece-tool-runner.ts` 只能用于识别架构概念，不能作为“MIT 可以直接抄”代码。复用时以具体文件路径/依赖许可证与法律审查为准，别把整个 monorepo 一律标成 MIT。

独立技术风险：`packages/server/api/src/app/mcp/mcp-permissions.ts` 当 `editionRequiresRbac()` 为 false 时返回 `ALLOW_ALL`，属于 Activepieces 的分版权限决策，**不是** Nerelan 应采用的授权策略。Nerelan 只要存在独立的 Owner grant，任何社区版服务端的未授权默认都不应扩大它。

## 8. Prioritize this against Nerelan's actual long-run product goal

* **P0**：Host Owner grant & exact source digest before any connector invocation, idempotency receipt rather than false-retry; no credential leaks. Already #303/#790/#299.
* **P1**：text-only metadata/tool search + search/inspect/execute split, minimal schema projection, developer-facing/agent-facing description, connection readiness state. Existing #253/#287.
* **P1**：tool/effect classification and no-repeat policy, triggers as durable TaskStore-admitted events with scoped subscriptions, prove restore.
* **P2**：optional embedding index, automatic Piece marketplace refresh, large external connector runtime; only after provider-free and actual accepted-task A/B. Existing #253/#379.
* **REJECT**：copy SaaS-heavy Node/Bun workflow execution, enterprise Agent code, alternate scheduler, new billing/Magpie ownership, default-permissive runtime policy.

Future metrics: number of tools sent to model per task, selection precision for identical task corpus, token/latency/cost, wrongly selected/unavailable tools, over-privilege blocks, stale connector and retries, actual independently accepted task fraction and *all-in real cost per accepted task*. A nice plugin gallery is not sufficient evidence of a better user outcome.

## 9. Audit scope and not-done evidence

This is pinned GitHub code reading of upstream framework (types and factories), action/trigger/schema, API install/sync, tool search, bundle caching/install, OAuth utils, MCP project permissions and a small amount of Enterprise-agent source for **non-reuse** classification. Nerelan main and its Owners were read for overlap. No `bun install`, no TypeScript build, no test suite, no Docker, no network connection to Activepieces/SaaS, no OAuth flow, no package execution, no malware exploit, no live provider/Magpie charge and no accepted-task quality test. Do not claim the static findings prove runtime vulnerabilities or imply specific license entitlements.

**Conclude**: prefer typed Piece/Packs + staged sparse tool discovery + safe user connection experience; leave tool execution authority, scheduler, evidence, cost and secret boundaries where Nerelan already owns them.
