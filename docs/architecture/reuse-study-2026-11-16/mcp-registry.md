# 官方 MCP Registry 深度源码审计：Nerelan 插件发现、版本与信任隔离

> [研究 Issue #1674](https://github.com/dddd2024/Nerelan/issues/1674) · 2026-11-17 · R1 docs-only · single pinned upstream · no runtime authority

# Official MCP Registry pinned-source audit — plugin discovery, publishing provenance, version/lifecycle and activation trust

DATE: 2026-11-17
SOURCE: modelcontextprotocol/registry@115f85225c9fac5281d8a2dc8551cf49b004d2f9 (main, preview; API v0.1 freeze stated in README, not GA)
NERELAN_MAIN: 6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b
SCOPE: R1 DOCS_ONLY; research-only GitHub evidence
EXECUTION_AUTHORITY: NONE
TEST_STATUS: NOT_RUN

## 0. Mandatory duplicate gate (before studying source)

Read [research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576): **39 comments** before this round. Exact GitHub Issues/PR/code searches for `modelcontextprotocol/registry` and `MCP Registry` yielded no independent fixed-source Registry study. Earlier source-specific MCP Python SDK v2 #1653, Inspector #1650, ToolHive #1590, Goose #1646 and Pack #253 concern protocol validation/transport/real runtime or other upstreams; this is a distinct official metadata registry. One project only.

[Upstream fixed commit](https://github.com/modelcontextprotocol/registry/commit/115f85225c9fac5281d8a2dc8551cf49b004d2f9) / [Nerelan fixed main](https://github.com/dddd2024/Nerelan/commit/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b).

## 1. License and maturity gate

- [LICENSE](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/LICENSE): **licensing transition** MIT to Apache-2.0; new and consent-relicensed code Apache-2.0, historical non-consenting contributors remain MIT; non-spec docs CC-BY-4.0. Do not describe entire repo uniformly as Apache-2.0 and do not copy docs verbatim into code without applicable notice/rights review. Go module declares `go 1.26.0` ([go.mod](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/go.mod)); no need to introduce Go service into Nerelan.
- [README](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/README.md) and [publisher quickstart](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/docs/modelcontextprotocol-io/quickstart.mdx): official registry is **preview**. README says API v0.1 freeze since 2025-10-24 but preview may reset/change; source uses v0/v0.1 route variants. Do not infer GA stability or production readiness from API freeze.
- [Ecosystem vision](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/docs/design/ecosystem-vision.md#L5-L56): Registry is a **meta-registry**; it indexes server names, packages/remotes, versions/metadata but does NOT store or execute package binaries. Consumers/subregistries may enrich/cureate. **DO NOT** classify listing as runtime/permission verification.

## 2. Exact modules and Nerelan disposition

| Unit | Source-confirmed behavior | Decision |
|---|---|---|
| [server.json response](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/pkg/api/v0/types.go#L10-L51) | `ServerJSON` contains schema URL, reverse-DNS server name, description/title, repository metadata, version, website/icons, packages, remotes, publisher-provided metadata; separate registry `_meta` contains status, statusChangedAt, publishedAt, updatedAt, isLatest. | **BORROW_PATTERN P0**: public discoverable catalog separated from local Host-admitted Pack manifest and trusted credentials. Do not mix publisher metadata with registry-maintained facts or Owner approval. |
| [model Package/Transport/Input](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/pkg/model/types.go#L11-L113) | npm/pypi/nuget/cargo/oci/mcpb package identifiers; URL/stdio/streamable HTTP; arguments/env/headers are templates, `isSecret`, file path and choices. Required `fileSha256` for MCPB, optional for other packages; repository provides forge stable `id` to mitigate name-resurrection impersonation. Icon SVG can contain executable JS. | **BORROW_PATTERN P0/P1**: typed read-only manifest with exact source identity, digest and secret requirements. **REJECT** raw runtime arguments or remote header contents from registry as executable Host config; `isSecret` declaration does not guarantee redaction; no automatic SVG loading. |
| [Schema and semantic preflight](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/validators/validators.go#L54-L112) | Validates JSON Schema version and semantic fields; exact version, not range/latest; repository, URL, icons and package/transport args validated. [schema.go](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/validators/schema.go) maps invalid JSON to actionable diagnostics. | **BORROW_PATTERN P0**: pure parsing and fully reported validation errors before Pack inclusion or install, pin protocol schema version; reject unknown/unsupported transport without falling back to execution. |
| [Namespace & package ownership](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/docs/reference/server-json/official-registry-requirements.md#L8-L45) | Official registry asks publishers to prove domain/GitHub namespace and matching ownership metadata in public package registries; restricts base registries. [publish handler](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/api/handlers/v0/publish.go#L37-L77) validates bearer JWT, scoped publish permission, schema; [validators.go L690–725](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/validators/validators.go#L690-L725) runs registry package ownership *conditionally* when EnableRegistryValidation is true. | **BORROW_PATTERN P0**: namespace/forge owner provenance and package ownership are distinct attestations; in Nerelan cache provenance and validation capability, **never** treat registry publication as signed binary, full dependency audit, app-store endorsement, or permission for user’s files/secrets. |
| [Version lifecycle](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/pkg/api/v0/types.go#L10-L16), [service](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/service/registry_service.go#L305-L399) | active/deprecated/deleted separate from isLatest; recalculates latest after status changes, may retain a deleted latest for administrative includeDeleted views; new version inserted with advisory per-name lock and version collision check. | **BORROW_PATTERN P0**: lifecycle states and exact registry version+content digest; deleted/deprecated must not be auto-install candidate; already-activated package requires local revocation policy and Host judgement, not unexamined auto-uninstall. |
| [Listing + incremental sync](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/api/handlers/v0/servers.go#L45-L78) | `updated_since` automatically requires includeDeleted=true; forbids client explicitly setting false; list limit max100, cursor and version filters; by default entries include all versions even when search. `version=latest` only picks latest; still inspect status. | **BORROW_PATTERN P0/P1**: incremental catalog mirror with tombstones, cursor checkpoint, explicit as-of timestamp, per-source grace. **REJECT** naive first-result/latest-only or sync losing tombstones. |
| [Publisher metadata](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/docs/reference/server-json/official-registry-requirements.md#L46-L104) | Only `io.modelcontextprotocol.registry/publisher-provided` custom data preserved, 4KB limit, other keys dropped; registry `_meta` is a separate response-level object. | **BORROW_PATTERN P1**: namespace extensions, bounded payload and independent, trusted local annotations; do not import arbitrary publisher-provided policy into Nerelan grant field. |
| [HTTP challenge SSRF boundary](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/api/handlers/v0/auth/http.go#L32-L98) | domain well-known fetch blocks redirects and private/loopback/linklocal/multicast/unspecified/cgnat/blocked IPv6 addresses at dial, pins resolved IP against DNS rebinding, 10s per attempt and 15s overall, max two attempts and response byte cap. | **BORROW_PATTERN P1** safe opt-in remote verification client pattern. It guards that **specific auth fetcher**, not all remote MCP servers, user package downloads, or arbitrary SSRF pathways. |
| [Publish concurrency](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/internal/service/registry_service.go#L205-L346) | External package/ownership checks performed **before** database transaction; acquire per-server advisory lock in transaction, reject same server version duplicate, publish phases timed. `UpdateServer` docs note some network checks remain inside transaction due to read/skip-status race. | **BORROW_PATTERN P1** for registry catalog ingestion: bound remote checks separate from TaskStore DB lock, per source/digest atomic version admission, distinct failed phases. **REJECT** new PostgreSQL registry server just to reuse this. |
| [Publisher tool](https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/cmd/publisher/commands/publish.go) | CLI publishes versioned metadata with token and validation; not a generic tool permission broker. | **DEFER** if Nerelan ever publishes its own Pack catalog. No user need to publish now. |

## 3. Actual Nerelan architecture comparison (main@6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b)
- [capability_registry.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/capability_registry.py): deliberately small, bounded **metadata-only** JSON Pack registry, no arbitrary plugin loading. Already implemented important read-only safety; #253 Pack owner.
- [run_store.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/run_store.py): SQLite authoritative Task/Attempt/Event/Receipts, idempotency, no need for registry DB.
- [goal_service.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/goal_service.py): Owner-scoped durable tasks and recovery, **not** registry ingestion.
- [task_runtime.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/task_runtime.py): executor routing and disposable-workspace validation; no permission to execute discovered MCP commands.
- [#790](https://github.com/dddd2024/Nerelan/issues/790) existing MCP/Connector runtime owner and official SDK-first; [#303](https://github.com/dddd2024/Nerelan/issues/303) exact source/digest workspace trust; [#299](https://github.com/dddd2024/Nerelan/issues/299) sandbox; [#447](https://github.com/dddd2024/Nerelan/issues/447) MCP/tool content/egress; [#287](https://github.com/dddd2024/Nerelan/issues/287) setup/connection; [#361](https://github.com/dddd2024/Nerelan/issues/361) mature component reuse. No duplicate implementation owner created.

## 4. Recommended Nerelan user-oriented flow

DISCOVER public metadata -> inspect source repo/forge immutable ID and named package -> check registry status/version/package ownership attestation/format -> pin package digest and trusted vendor scopes -> Owner grants workspace/secret/network/side effects -> sandbox installs/launches using existing MCP adapter -> TaskStore durable receipts and independent verifier -> refresh registry metadata and **never** silently widen permissions on upstream metadata change.

Users should be able to answer:
1) Who publishes this MCP server and what exactly was proven?
2) Which package version and actual file digest will run?
3) Are there warnings: deprecated/deleted, hash missing, endpoint changed, provider unknown, dangerous args?
4) Does this server need a local process, network, secrets, worktree paths or user OAuth account?
5) Which Agent/Task would be allowed, what can it do, and how do I revoke it?

Make the default implementation **read-only, local metadata cache** with explicit install/activate requests. No model calls, no broad credential scanning, no automatic official-registry sync service needed in this R1 study.

## 5. Provider-free negative / acceptance tests (PROPOSED ONLY)
T01 unsigned/missing package digest in non-MCPB: display but no auto-activation.
T02 isLatest=true but deprecated/deleted: not activatable by default, warning visible.
T03 incremental sync remove tombstone / timestamp skew: previously indexed deleted server remains marked deleted, never revived automatically.
T04 registry returns multiple versions in name-sort order: do not interpret first as latest.
T05 version `^1.2.0` or `latest` in publish metadata: validation rejects.
T06 source GitHub repository re-created with same name but different immutable repository ID: source identity changes; require new approval.
T07 package name/owner attestation valid but malicious code requests network exfil: Host sandbox and explicit grants still block.
T08 remote template header contains secret placeholder: render outside model context with trusted credential broker, never log.
T09 manifest prompt injection in description/icon metadata: treated as untrusted display text, never Owner instruction.
T10 SVG URL with external script: sanitize/proxy/reject; no browser script execution in main UI.
T11 tampered SHA256 package file: refuse install; no fallback to latest.
T12 HTTP verification DNS resolves to internal IP or redirects: reject; bounded timeout.
T13 validation endpoint 500/timeout: `PROVENANCE_UNKNOWN`, no implicit secure flag.
T14 mixed Auth method and client package metadata: do not treat namespace auth as package provenance or binary integrity.
T15 concurrent duplicate version publication/ingestion: one canonical version revision and no half-activated plugin.
T16 publisher changes remote URL/package args under same version: local pin/digest/grant invalidation before use.
T17 registry cache unavailable: previously approved local pinned plugin remains under existing trust policy; new installation blocked/unknown.
T18 compare cold-start, metadata/context size, security false-allow and user setup error vs direct manual MCP JSON, no real models unless separately scoped.

## 6. Final decision
**BORROW_PATTERN P0**: public registry vs local activation trust, typed server.json, exact pinned version/digest, publisher+package provenance, lifecycle status/tombstones, no untrusted metadata to Owner policy.
**BORROW_PATTERN P1**: incremental sync, remote key retrieval SSRF/timeouts, publish lock validation ordering, source forge stable ID, bounded extension/GUI.
**ALREADY_IMPLEMENTED**: Nerelan Pack metadata-only registry, Owner grant/GoalService/TaskStore, official MCP runtime ownership.
**REJECT**: whole Go registry/Postgres deployment as default component; direct auto-install from listing; public package owner = safe binary; IS_LATEST = ACTIVE; first search result latest; in-place approval across digest/config change; registry content as trusted tool instructions.
**DEFER**: optional read-only public registry client and manual catalog UX until #790/#253 fixtures, security/sandbox and real user benefit data.

Static GitHub inspection only; never installed or ran Go binary, no publisher auth, no external registry API calls or npm/binary fetching, no model/paid credentials, no local tests, no CI, no independent review, no runtime changes and no merge.
## 7. 更深入的源代码复用裁定：一个 Registry 不等于一个执行器

### 7.1 按“公开目录 / 本机信任 / 真实执行”三层拆分

官方项目的设计文档将 MCP Registry 定义成 meta-registry：发布者提供包和远端服务位置，实际制品驻留 npm、PyPI、OCI 等其他包服务；官方 Registry 本身只存元数据。对 Nerelan 推荐三个状态归属：

1. 公开目录（PublicCatalogRecord）：服务器名、描述、注册来源、包和远端配置、仓库信息、公开生命周期、来源获取时间。这一层只能帮助用户或 Agent 选择“可能有用”的工具。
2. 本机信任（LocalPackAdmission）：Owner 选中的发布者命名空间、仓库不可变 ID、实际包内容 SHA256、插件声明和工作区目标，经过版本检查、签名/来源验证及明确的权限批准。本机信任不能通过刷新远端目录自动升级。
3. 真实执行（TaskStore + Executor/MCP Adapter）：唯一绑定 Task/Attempt/Grant 的进程或远程工具实例，凭据由 Host 保管，对外调用由 Host 决策，结果必须有可审计收据。

如果把上面三者合并成一个“已在官方注册表出现所以允许启动”的开关，任何发生发布者账号劫持、包内容替换、远端端点换域或供应链依赖污染的情形都可能绕过 Nerelan 的授权模型。

### 7.2 版本、状态和文件摘要是三个互相独立的轴

上游 `pkg/api/v0/types.go` 的 RegistryExtensions 将 `status`（active/deprecated/deleted）和 `isLatest` 分离。上游 `registry_service.go` 还能在状态变化后重新计算 latest，并保留一个已删除版本作为管理查询的可寻址入口。技术含义：
- `latest` 表示排序结果，不表示未弃用；
- `active` 表示公开注册表当前生命周期，不表示包文件内容安全或 Owner 允许；
- `fileSha256` 只在 MCPB 类制品必填，对其他类型可选，不能把任意 server.json 当作已签名二进制；
- 即使服务器版本号固定，远端 URL、启动参数或关联包描述如果更新，Nerelan 也不应静默放宽现有授权；
- 取消某个公开版本或退役，不应自动销毁用户本地可重复验证的旧任务证据，但要阻止新自动激活和不加提示的恢复运行。

**推荐宿主准入键**：registry_source + server_name + registry_record_digest + version + package_identifier + resolved_artifact_digest + stable_repository_id + owner_grant_epoch。可将公网注册源声明与本地实际包文件的 SHA 作为两个不同字段，不相互冒充。

### 7.3 确切的增量同步合同：丢失 tombstone 就可能复活已撤下的工具

`internal/api/handlers/v0/servers.go` 对 `updated_since` 自动设置 includeDeleted；当调用者显式 `include_deleted=false` 时返回 400。这个条件不是 UI 特性，而是目录一致性的核心：如果一个服务器在某次镜像后被删除，而后续增量只拉活跃项，本地记录就会永久留在“可用”状态。Registry 还明确说明默认 list 返回同名服务器的多版本，排序不是最新优先；`version=latest` 是过滤而不是必须依赖数组首条。

对 Nerelan 的轻量镜像建议：
- 仅 Owner 启用的公开源；不必先跑常驻同步进程，按需刷新即可；
- 保存上次成功游标和更新水位，按同一过滤条件分页，处理不完整拉取或失败重试；
- 将 deleted/deprecated 作为独立事件输入 Catalog，而不是直接删除本地 TaskStore 历史；
- 刷新完成必须保留本机批准的 artifact_digest，若冲突显示 `UPDATE_NEEDS_REAPPROVAL`；
- 离线时可显示已缓存只读元数据，但不向未授权的新目标自动发安装请求。

### 7.4 “已证明发布者是谁” 与 “已证明包由谁控制” 是两次不同验证

上游发布路由 `internal/api/handlers/v0/publish.go` 在服务器 JWT 权限中检查发布目标命名空间，还先进行 JSON Schema/semantic 检查。包所有权在 `validators.ValidatePublishRequest` 中可以通过 `EnableRegistryValidation` 开关执行对 npm/PyPI/OCI/MCPB 等包管理服务的核查。正式官方 Registry 要求另有严格包源白名单。

不能据此过度承诺：
- 通过 DNS/GitHub 命名空间认证意味着发布者控制相关身份，并不是项目的源码安全审计；
- 通过包元数据核查意味着某些发布权关联成立，不代表依赖树无漏洞，也不代表发布者账号永远可信；
- 一个包被白名单 Registry 托管不等于其文件 digest 当前可信，更不等于用户授权该包启动命令；
- Registry 级校验开关、部署差异及后台同步失效都必须单独显示，不得将未执行验证显示为 `VERIFIED`。

用户界面可以将来自不同层次的证据分别表述为“发布命名空间已验证 / 包所有权已验证 / 下载内容完整性已验证 / 本机 Owner 已授权”，且每一层都有验证时间和失败原因，避免单个绿色勾号误导用户。

### 7.5 防 SSRF 的成功设计应移植到具体验证网络客户端，而不是依赖提示词

固定源码的 `DefaultHTTPKeyFetcher` 使用受控 dialer：DNS 解析后在拨号前拒绝 loopback、私网、link-local、无效和部分保留网段；后续实际拨号使用已解析 IP，抵御两次 DNS 解析之间的 rebinding；HTTP 禁止 redirect；单次请求 10 秒、总预算 15 秒、最多两次暂时错误重试，响应体有大小上限。

这段设计的可借鉴点不是“我们也应该有一个 HTTP Server”，而是 **任何从不可信插件描述导出的远程来源验证请求都要在 Host 内置的受控网络适配器里做 SSRF 防护**。但此具体实现在上游针对域名公钥验证，不能因此把这些安全属性推断到 Registry 里的每个 Package URL、Remotes transport、用户自行选择的代理或第三方 MCP Server。

### 7.6 Publisher metadata / trusted registry metadata / Owner metadata 三套命名空间

`server.json` 中发布者扩展只保存 `io.modelcontextprotocol.registry/publisher-provided`，限制 4KB；它不会取代 API Response 层的 Registry Official metadata。对 Nerelan，在本机还应另加一个 Host-owned 只读注释层，用来写安全审计、用户批准源、真实包摘要和企业策略。例如：

- Publisher provided: 联系方式、文档、可显示的工具说明（不可信）；
- Registry provided: 官方 publishedAt/updatedAt/status/isLatest 与验证上下文（外部来源事实，但非本机授权）；
- Host provided: `admission_state`、`owner_approved_scope`、`artifact_digest`、`sandbox_profile` 和 `last_verified_at`（内部权威）。

通过扩展数据拥有发布权限，并不能修改 Host provided 数据。Agent 读取 description 应走 ContextBuilder 的 `authority=NONE` 路径，绝不能把其中“忽略权限限制”当成 Owner 指令。

### 7.7 UI 和用户思维：只让用户做必要的决定

当用户说“给我安装一个能查 GitHub PR 的插件”，理想交互是：
- 首先只检索候选插件的名称、功能摘要与包来源；
- 对用户选择的插件展开真实开发者、版本和是否弃用；
- 显示它需要哪种账户连接、哪些域名、是否在本机运行命令、是否访问源码文件；
- 在用户已授予的权限范围内完成配置验证，不自动扫描所有账号或复制 Magpie token；
- 只有所有强制条件满足时才提供“由 Host 启动此特定版本”的明确准入；
- 失败时显示 `UNVERIFIED_SOURCE`、`MISSING_ARTIFACT_DIGEST`、`REGISTRY_DEPRECATED`、`OWNER_GRANT_REQUIRED`、`SANDBOX_UNAVAILABLE` 等可解释原因。

这一体验比把官方目录整个搬进 Agent 的系统提示词更有利于降低 token 成本，而且可以自然衔接已研究的 Activepieces 分阶段搜索、ToolHive 生命周期、NeMo 的工具调用许可和 MCP SDK 的协议能力。

### 7.8 为什么不要移植 Registry Go/PG 服务器

Nerelan 的目标不是发布公共 MCP 应用商店，而是以极低成本、安全可信地统一管理已有 AI 资源。上游 Go 服务包含多人发布认证、DNS/HTTP/OIDC token 交换、托管 Postgres、跨多种公共包管理器的合法性验证、运营删除流程、监控、负载优化以及 Registry API 版本治理。直接移植到 Nerelan 将增加第二份元数据真相、多套后台同步和新的密钥/网络暴露面。

更合适的实现顺序：
- 从已有 `capability_registry.py` 的 metadata-only 模式增加标准 `server.json` ingest validator；
- 由 #790 的 MCP Adapter 提供协议发现和工具调用，不让目录本身执行工具；
- 由 #303 做精确来源和签名/digest 批准，#299 提供真正的隔离；
- 由 #287/ #253 负责显示选项、用户 Scope 和 Pack 封装；
- 使用 #447 做 Tool Result 信任/出站过滤；
- TaskStore 继续记录真正发起的尝试、授权、执行和证据。

## 8. 18 项测试的最小衡量方式（皆未执行）

所有 T01–T18 先在无外网、无模型的静态 JSON fixture 中运行。每个测试必须记录 expected catalog state、expected Host admission state、expected error category。升级到真实公共 Registry API 或下载第三方 Package 必须另有运行权限和安全审查，本轮不包含。

正确性指标建议：
- **Identity correctness**：同名服务器不同 Forge immutable ID、同版本不同制品摘要必须保持为不同状态；
- **Revocation freshness**：删除/弃用事件最终能更新本地目录，目录刷新失败不得暗中恢复旧项；
- **Permission correctness**：发现/验证来源/本地激活三个动作互不自动授权；
- **Reliability**：Registry 暂时不可用时不会卡死已批准的长期 Goal，也不会出现新的自动安装；
- **Costs**：静态目录同步和安装验证无需默认 LLM 花费，新增网络、下载、隔离耗时要可见；
- **User outcome**：用户找到并成功配置所需连接器的比例、首次配置耗时、错装/越权调用数，与手工 MCP JSON 流程比较。

只有以上安全与可用性测试达标，才值得考虑定时增量同步和更多目录 UI。不能只看目录里收录的 MCP Server 数量作为产品成功指标。

## 9. 可靠性缺口与过度借鉴风险

上游源码自身注明：CreateServer 将包所有权等外部网络核验放在 DB transaction 之前，避免占住 pgxpool 连接造成新发布请求阻塞；而 UpdateServer 部分验证因依赖当前删除状态而仍在事务中进行，这是一项明确的已知权衡。对 Nerelan，应遵守“外部慢网络调用在 TaskStore 写事务外执行，并在提交前重新检查授权/版本”，而不是生搬这套 Postgres advisory lock。

同样，Registry 约束自身服务域名验证时的 HTTP 安全，并不替任何下游消费者保证运行插件的 OS 级权限、包生命周期脚本、安全版本或秘密处理。它不是插件沙箱，不是认证插件的应用商店质量认证，也不是任务完成的验证器。

## 10. 研究完成条件 / 未完成条件

已固定阅读上游 README、LICENSE、go.mod、模型结构、发布指南、registry requirements、generic server.json、versioning、ecosystem vision、发布 API、server list 与增量同步、schema/semantic/package validators、DNS/HTTP/OIDC auth、registry_service publish 和更新事务；已对照 Nerelan 目标 main 的 AGENTS.md、capability_registry.py、task_runtime.py、run_store.py、goal_service.py、COMPETITIVE_LANDSCAPE.md 以及已有 owners。

**未执行**：Go build/test、真实 Registry API 请求、发布者登录、包下载与 hash 验证、第三方 MCP Server 启动、Nerelan Runtime/TaskStore 变更、模型调用、Magpie 结算测试、CI、独立复核和合并。源码审阅不证明防 SSRF 实现没有其他漏洞，也不证明本地任何插件已满足安全验收。

**最终：BORROW_PATTERN（公开目录与本机信任分层、精确来源/包身份、状态/同步）、ALREADY_IMPLEMENTED（TaskStore/Host/Pack metadata）、REJECT_RUNTIME_CLONE（Go+Postgres registry 与自动安装）、DEFER（受控公共目录适配器）。**
