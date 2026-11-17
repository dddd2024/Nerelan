# Nerelan 复用专项：Official MCP Python SDK v2（固定源码）

> Research Issue [#1653](https://github.com/dddd2024/Nerelan/issues/1653) · `STATIC_SOURCE_REVIEW` · 研究不是实施授权。

# Official MCP Python SDK v2 — 源码级复用审计（2026-11-17）

> SINGLE_UPSTREAM / R1 RESEARCH_DOCS_ONLY / STATIC_PINNED_SOURCE / **NOT_INSTALLED / NOT_TESTED / NO_IMPLEMENTATION_AUTHORITY**.
> - 上游：[`modelcontextprotocol/python-sdk@77001c96f9507be0f4d009b83210a384a5e08bda`](https://github.com/modelcontextprotocol/python-sdk/commit/77001c96f9507be0f4d009b83210a384a5e08bda)（`main` 快照，**不以它冒充 v2.2.0 release**）。
> - Nerelan：[main@`5c69e891e3a559a23e7fd4e3115422c057df4438`](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438)，Governance v2.1。
> - 协议与 MCP 生命周期的唯一实现 Owner：[#790](https://github.com/dddd2024/Nerelan/issues/790)。Pack #253、配置 #303、egress #447、沙箱 #299，已有 Inspector 诊断研究 #1650。

## 0. 先查重：为何确实是一个新源码专项
- 已逐项核对 canonical 研究总索引 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 与 **30 条**历史研究评论、GitHub Issue/PR/代码关键词 `modelcontextprotocol/python-sdk` / `MCP Python SDK`，未发现完整 pin-source 的此项目独立研究 Issue/PR。
- #790 **已经**把 `OFFICIAL_MCP_SDK_FIRST + VERSIONED_CAPABILITY_DISCOVERY + AUTHORITY_SEPARATION` 定为平台路线；本轮是执行它的 **MCP-0 源码证据**，不是重新申请一条 MCP 实施路线。
- #1650 [MCP Inspector v2](https://github.com/dddd2024/Nerelan/issues/1650) 是协议诊断测试工具，非可嵌入 Python 客户端；ToolHive #1590 管扩展管理与容器 admission、Goose #1646 管运行中 tool lease；A2A SDK #1603 和 ACP SDK #1585 为不同协议，均不等于官方 MCP Python SDK。

## 1. 固定源码发现 — 按模块裁定

| 模块 / 证据 | 在上游固定源码实际做了什么 | Nerelan 判断 |
|---|---|---|
| **高阶 Client / transport** [client.py:268–375](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/client.py#L268-L375), [Client enter:455–490](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/client.py#L455-L490) | `Client` 可用 URL / stdio 参数 / 自定义传输 / in-process server，`async with` 掌管 session、版本协商和清理 | **DIRECT_REUSE / P1**（#790 将来建 thin host adapter，而不是自写协议）；仅可用在 Host 已批准的目标 |
| **版本探测 / 降级** [client/_probe.py:1–114](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/_probe.py#L1-L114) | 默认 `mode=auto` 先 `server/discover`，MCPError（除明确的现代版本不兼容）大范围退到 `initialize`；网络异常不算协议不兼容；意外的错误可能触发降级握手 | **BORROW_PATTERN + SECURITY GATE / P0**：协商结果必须回报 Nerelan 并与 Owner 要求版本/能力比对；必须支持 `require_modern` 时拒绝降级，不可因 auth/429 就当 legacy |
| **多 Server group** [session_group.py:87–151](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session_group.py#L87-L151), [374–452](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session_group.py#L374-L452) | 聚合工具/资源/提示；同名键直接报 duplicate（而非确定性合并）；`component_name_hook` 可重命名；调用按名称反查 session | **BORROW_PATTERN / P1**：Nerelan 工具身份必须 `connector_id + tool_id + protocol snapshot + account scope`，由 Host 授权，不以 MCP Server 自报名字作为权威；服务断线/连接替换冻结调用快照 |
| **缓存与账号泄露边界** [client/caching.py:92–130](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/caching.py#L92-L130), [210–240](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/caching.py#L210-L240), [318–340](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/caching.py#L318-L340) | 按 `partition` 分隔 private 缓存；`share_public=False` 默认不跨分区；若启用共享则信任服务端的 `public` 标记，明确警告误标会跨租户泄露；失效通知的读取短暂陈旧可能发生 | **DIRECT_CONFIG_REUSE / P0**：每个 Owner account/Connector 绑定独立 Client/Cache 分区；不启用 `share_public`，安全关键工具清单使用 refresh/bypass 并绑定 version/digest |
| **Tool schema** [client/session.py:1052–1183](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session.py#L1052-L1183) | 接收到正常结果时验证 structuredContent schema；编译 validator 缓存，schema 改变会替换；空 registry 阻止从服务器选定远程 `$ref` 被自动下载 | **DIRECT_REUSE + HOST CHECK / P1**：用 SDK 校验类型，不把验证通过当授予权限；外部工具 descriptions/outputs 均为不可信数据；遇到 invalid/unresolved schema 按强验证规则 fail-closed |
| **现代请求 header 镜像** [client/session.py:1067–1071](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session.py#L1067-L1071), [1111–1116](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session.py#L1111-L1116) | 如果已列举工具，服务端 schema 的 `x-mcp-header` 能把指定参数镜像为 `Mcp-Param-*` header | **BORROW_PATTERN / P0 egress**：Host tool policy 必须看最终镜像后的 header 内容，避免只检查 JSON body；敏感数据未经授权不能由 server 诱导进 header |
| **stdio / Windows 回收** [stdio.py:76–82](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/stdio.py#L76-L82), [114–190](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/stdio.py#L114-L190), [291–349](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/stdio.py#L291-L349) | 默认允许继承有限环境变量，`server.env` 可覆盖；子进程读写、flush/terminate/kill 有界；Windows 用 Job Object 结束进程树 | **DIRECT_REUSE / P1**：可复用底层清理，Nerelan 仍决定 `stdio` 是否可执行、cwd/env 白名单、沙箱、操作 ID/超时和子进程授权 |
| **HTTP 同源重定向** [shared/_httpx_utils.py:85–147](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/shared/_httpx_utils.py#L85-L147) | 只按同源限定的 redirect 规则走，保留方法的 307/308 等；是传输级安全限界 | **ALREADY_IN_SDK / P1 VERIFY**：复用，不重写；但接入点、DNS、OAuth metadata、真实 egress 授权仍由 #447/#303 控制 |
| **外部 OAuth 资源限定** [bearer_auth.py:44–88](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/server/auth/middleware/bearer_auth.py#L44-L88) | 只有显式 `resource_server_url` 时才对 AccessToken.resource 比对，非无条件启用的验证；Auth provider/Verifier 需可信 | **DIRECT SDK MECHANISM，BORROW policy / P0**：若将来 Nerelan 暴露 MCP Server 必须配置资源受众，凭据/Owner identity 继续由 Host 提供；勿把 SDK 默认即等价完整权限控制 |
| **输入征询/Agent 控制** [client.py:772–810](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/client.py#L772-L810), [session.py:1052–1109](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session.py#L1052-L1109) | 高阶 Client 可多轮调用应答；手动 `allow_input_required=True` 可拿到 request_state；默认多轮结果/状态可能只在服务端进程本地有效 | **BORROW_PATTERN / P0**：所有 Elicitation/Sampling 必须映射为 Owner 需要输入状态；外部 request_state 只作临时引用，断线后不得当长时持久凭据或权限 |
| **MCP Tasks 扩展** [migration.md:2011–2019](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/docs/migration.md#L2011-L2019) | SDK 2.x 移除了旧实验任务，2026 Tasks 作为新扩展尚未实现；因此不能直接期待 `tasks/get` 等长任务接口可用 | **REJECT AS DURABLE ENGINE**：Nerelan 的 TaskStore/RunStore、外部 task handle 与 reconciliation 仍是权威；参照 #790 已有要求 |
| **授权与许可证** [LICENSE](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/LICENSE), [pyproject.toml](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/pyproject.toml) | MIT；Python >=3.11，当前声明包含 3.13 | **DIRECT_DEPENDENCY candidate only**：#790 选定后按 R2 依赖路径单独 PR，先 Windows Python 3.13 smoke，不在本轮安装 |

## 2. 当前 Nerelan 真实代码对照
- [`capability_registry.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/capability_registry.py) 的 `CapabilityRegistry` 是**只读 metadata**，只枚举 owner-selected `*.json`、拒绝敏感字段，不启动 MCP Server，更没有通用 `ClientSession`。**不能把这个旧能力标成已有 MCP Runtime**。
- [`claude_executor.py:72–95`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/claude_executor.py#L72-L95) 已有受管 MCP config readiness，[`test_claude_managed_mcp_readiness.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/tests/platform_v1/test_claude_managed_mcp_readiness.py) 有 no-provider fail-closed tests。**ALREADY_REUSED**；它不是通用 MCP 工具执行与远程身份验证。
- [#790](https://github.com/dddd2024/Nerelan/issues/790) 已指定官方 SDK-first，并确定 `Nerelan Task/Run = owner; MCP Task handle = external operation reference`。任何协议 Client 成功连接不升级到独立执行授权。
- [#253](https://github.com/dddd2024/Nerelan/issues/253) 的 Pack 包含 MCP capability 与 verifier，但 Pack/Tool metadata 是要求而非 grant。应把多个工具的 identity/version/capability 源映射到既有权威，不建第二个 tool registry/TaskStore。
- [#303](https://github.com/dddd2024/Nerelan/issues/303) 规定项目本地 MCP config 必须先被纯静态发现，未经 Owner 审批不能执行 stdio 命令；协议库只在通过 admission 后调用。
- [#447](https://github.com/dddd2024/Nerelan/issues/447) 管 tool egress/provenance；`x-mcp-header`、OAuth redirect 等需加入 **最终请求**审计，不能只扫描工具描述/JSON。

## 3. 最小 provider-free 验证矩阵（未运行）
1. 未批准 project-local `stdio` command / symlink cwd：0 subprocess/0 network；#303/#299。只有显式 exact config+capability grant 后方能触发 SDK Client。
2. 协议版本混合：modern-only、legacy-only、`server/discover` 401/429 与 `-32022`；必须显示 negotiated era、fallback reason，不以 auth 异常静默表示“正常支持 legacy”；#790。
3. 双服务同名 `run` tool，身份含稳定 `connector_id`、Owner/account scope；重连 tool catalog 变化时旧批准不复用；#790/#253。
4. 两个不同账户收到服务端错误标记 `public` 的私有数据；`share_public=False` 交叉读取为 0，principal 变更后重建 Client、bypass sensitive cache；#790/#447。
5. `x-mcp-header` 将本应只留在 body 的敏感字段镜像到 headers；Host egress 拦截原始/扩展后请求；#447。
6. 伪造 outputSchema 远程 `$ref`、无解的 schema、恶意正则：不得外网 fetch；验证失败标记 INVALID/UNVERIFIABLE；#790/#447。
7. stdio crash、timeout、close/kill Windows 子进程树，队列与 pending 收敛，外部 side-effect UNKNOWN 不二次执行；#790/#299/#1597。
8. OAuth token 颁给另一 resource（audience）或 redirect 到不受信端点，默认无显式 resource_server_url 时也不能通过 Nerelan Host policy；#790/#447。
9. 服务器诱导 InputRequired/Sampling，Owner 未授权时不自动满足；跨进程 request_state 过期时不能假成功；#789/#790。
10. 实际含义：工具诊断通过 ≠ 完成 Nerelan Goal。实装后需对同类任务比较成功率、延迟、返工、账户消耗，验证“全成本每个独立验收成功 Goal”；#1527。

## 4. 实施顺序和不做什么
- **P0 安全门槛（#303/#447/#790）**：先 trust/discovery/admission，再 instantiate Client，保证凭据、HTTP redirect、`x-mcp-header`、缓存分区与授权快照不越界。
- **P1 薄客户端适配（#790）**：连接、版本快照、namespaced tool catalog、错误分类、无副作用 fixture，复用官方 `mcp.Client`；外部 action 收据继续写现有 store。
- **P1 Pack 连接能力（#253）**：把 inspect/compatibility/version 状态纳入 Pack 可用性，不新增任意插件执行 daemon。
- **P2 UX/economics**：用户看到“连接未授权/版本不兼容/需要输入/工具失效/何时重试”，而不是绿灯“已安装成功”；经济性由真实 Goal 验收和成本计算判断。
- **拒绝**：实现自有 JSON-RPC/HTTP/SSE 传输、直接以 `ClientSessionGroup` 名称作宿主授权、默认跨账户缓存、SDK 执行器替代 Nerelan TaskStore、以 2.x 获得 Tasks extension 的虚假承诺。

**验证事实**：已读固定上游源码与 Nerelan current-main/Issues；未安装任何 Python SDK 版本、未运行 pytest/远程 MCP、Windows crash、provider/额度、也未验收任何产品改动；所有测试均为建议。根据 AGENTS.md，依赖更改与真实外部执行不是本研究授权范围，需独立 PR 和相应门禁。

## 5. 细化宿主插件/Agent 接口的完整链路

```text
Pack capability requirement                         (#253, metadata only)
  -> exact workspace config discovery + digest      (#303, ZERO EXECUTION)
  -> Owner-approved connector endpoint + account
  -> Host policy / credentials / egress preflight    (#790/#447)
  -> official mcp.Client mode=auto / required mode
     -> record negotiated protocol + server/transport identity
     -> list_tools, list_resources, list_prompts
     -> build host namespaced projection + capabilities version
  -> Nerelan executor requests a tool:
     -> re-check exact grant, requested tool and final header/body
     -> stage durable operation ID (TaskStore owner)
     -> client.call_tool() via authorized transport
         -> InputRequired / blocked -> Owner attention
         -> success + result receipt -> model-visible data with provenance
         -> call outcome ambiguous -> UNKNOWN, never blind replay
  -> independent Goal verification and cost evidence
```

**不可混淆的四种 identity**：
- `Server implementation.name`：对端自报，**不是**可信 account/connector ID。
- `ConnectorInstance`：Nerelan owner 选择、审批的 endpoint+transport+scope+exact config。
- `ToolOffer`：在这个 connector 的一次版本化 tool catalog 中可观察到的工具，不因为名称相同就获得别的 connector 的 grant。
- `ToolOperation`：Nerelan 某个 Goal/step 中获批准的一次外部副作用，租约/收据/UNKNOWN 是现有 TaskStore 的事实。

## 6. 用户视角要解决的问题

| 产品问题 | 当前该如何表达 | 未来 MCP SDK 复用能解决什么 |
|---|---|---|
| “这个插件怎么突然不能用了？” | `UNAVAILABLE` 与具体失败类型/重新验证条件分离 | 协议/连接/401/429/Tool schema 的可观察诊断；不能拿连通性说明授权 |
| “我的两个账户都安装了同名工具” | tool list 显示清晰 Connector 与账户来源 | ClientSessionGroup 的多连接形态可用，但必须由 host namespacing，不让 server 名称决定帐户 |
| “切换账户后会看见别的账户的资料吗？” | 默认不共享缓存、不复用上一个授权 session | `CacheConfig(partition=..., share_public=False)` + 账号变更后重建 Client |
| “我停了任务，插件的操作会不会继续？” | 明确 CONNECTOR / ToolOperation / Goal 状态分别是什么 | SDK 管客户端连接，但外部任务取消/副作用确认仍需 Nerelan receipts；Tasks 扩展并不现成 |
| “该插件能用哪些能力？” | 与 Pack 的 declared requirements、Host grant 分开显示“已发现协议能力” | 精确 negotiated version + list/discover；欠缺扩展不能默认为支持 |
| “这个本地 MCP 工具安全吗？” | 未审批前不能运行任何 server 代码 | SDK 安全的进程清理只在获授权启动后有价值；它本身不提供沙箱 |

## 7. 细节风险与不变量（避免“SDK 代表一切安全”）

### 7.1 自动回退的版本语义

固定 [`_probe.py:68–113`](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/_probe.py#L68-L113) 中，`mode=auto` 把多数 `MCPError` 转为 legacy `initialize()`；这属于兼容机制，不意味着“所有错误都应降级”。建议为 Nerelan Host 执行 **required capability + negotiated mode** 的双约束；例如 Owner/Pack 声明只接受 modern `server/discover` + 新版 credential semantics 时，即使 SDK 在 auto 上连接到 legacy，也应拒绝提交外部调用。另一个边界是仅有非 `MCPError` 的连接故障会冒泡；不能按“底层尝试过两次”给用户错误的已验证消息。

### 7.2 结果缓存的身份分区

[`CacheConfig`](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/caching.py#L92-L130) 要求自定义共享 store 必须给 `partition`，但 SDK 无从确认这个字符串是否真正按 Owner principal 产生。它只负责按这个标识缓存；**由 Nerelan 计算分区**，禁止从 server 声称的 URL/用户名直接推导。默认 `share_public=False` 应保持。对于权限敏感的能力清单，服务端发出的 `ToolListChangedNotification` 导致 eventual eviction，可能短时间内读到旧清单；审批时必须使用新鲜能力快照，不用仅靠失效通知的 cache。

### 7.3 工具参数可能成为 HTTP header

[`session.py:1067–1116`](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/session.py#L1067-L1116) 根据服务端 tool listing 保存 `x-mcp-header` 映射，将部分工具参数转成 `Mcp-Param-*` header。必须把 header 视为与请求体同样敏感的外发数据，不应绕过 #447 的宿主策略。否则“参数看起来只在 body 中经过过滤”并不证明所有实际发出的 bytes 受到相同授权。

### 7.4 进程回收不等于进程隔离

[`stdio.py:114–190`](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/stdio.py#L114-L190) 会生成进程，`server.env` 合并在有限环境变量之上。尽管 [L291–349](https://github.com/modelcontextprotocol/python-sdk/blob/77001c96f9507be0f4d009b83210a384a5e08bda/src/mcp/client/stdio.py#L291-L349) 的 POSIX process group / Windows Job Object 清理很有参考价值，但插件仍能用被授予的 OS 权限调用文件、网络或其他进程。未经 host policy 和真正隔离验证，不能把 “Job Object 清理” 等价为沙箱。

## 8. 研究方法与证据状态

- 研究时间 2026-11-17，仓库源码来自 GitHub 连接器的固定 commit；同步核对了官方发布说明与 Security Advisories。已发布的 v2.x 包有安全公告历史，如客户端跨域重定向/服务端 session 清理/OAuth resource 范围问题；因此将来依赖选择须重新核对 release 的修复版本，不能只凭某一 commit 宣称“没有漏洞”。
- **实际执行**：仅静态源码和规范/Issue 对照，不需要真实 Owner token，也未启动任何第三方可执行组件。
- **未执行**：SDK 安装、pytest、Windows 本地进程树 kill、真实 OAuth/Provider/MCP server 联调、运行中 Agent×Model 费用基准测试、独立审查。
- **go/no-go**：若不能在 host 侧证明 exact config 授权、分区缓存、跨 server 工具身份绑定、HTTP/header egress 审核和 UNKNOWN 收据，则不能进入自动化 MCP tool execution。能证明这些后优先直接使用 official SDK，而不是重新写协议。

此处的 `DIRECT_REUSE` 仅表示**后续实施的技术建议**，不代表已采用、已集成、已通过 CI 或已合入 main。
