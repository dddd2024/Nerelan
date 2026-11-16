# Composio 源码级复用研究：外部应用账户、MCP、工具执行与预算安全（2026-11-16）

> **状态：** STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / NO_IMPLEMENTATION_AUTHORITY  
> **上游：** [ComposioHQ/composio](https://github.com/ComposioHQ/composio)，commit [`c59c2db88a5c`](https://github.com/ComposioHQ/composio/commit/c59c2db88a5c67d8034280f1b5639c9f5cf783cc)。上游 SDK 仓库 [MIT](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/LICENSE)。  
> **Nerelan 对照：** main [`a7b6277772ae`](https://github.com/dddd2024/Nerelan/commit/a7b6277772aefef33138921f357c459f259e718b)。  
> **研究索引：** [#1567](https://github.com/dddd2024/Nerelan/issues/1567)。不触及任何已有账户的凭据、Composio API、运行权限或部署。  
> **注意：** MIT SDK 并不能证明 Composio 托管后端、认证服务和整个数据面都可同条件本地自部署；默认云服务引入第三方凭据与数据托管边界，必须单独评审。

## 0. 查重在选择项目前完成

- 检查了 Nerelan 11 月 15 日复用报告、`COMPETITIVE_LANDSCAPE.md`、已创建但尚未合并的 `REUSE_RESEARCH_INDEX.md`（Mastra 研究分支）、11 月 16 日 Issues/PR、新近提交和 GitHub 文件搜索。
- `Composio`/`composiohq` 检索没有找到对应专项文档或已有实现 Issue；这意味着“在检查范围内无专项结果”，并不绝对否定以前的非正式聊天讨论。
- 本轮与已研究的 Cline、Pi、Letta Code、Plandex、OpenClaw、Paperclip、Mastra 不同：不研究另一套 Coding Agent，而是将第三方**应用工具**作为可选 Pack/MCP 能力纳入 Nerelan，检验账户归属、工具授权、请求侧拦截、MCP 漏口、审批原子性和外部工具费用。

## 1. 定位与防止概念混淆

Composio 提供**应用工具目录、工具账户授权、托管/本地工具调用、会话级策略和托管 MCP**。典型对象：

| 名称 | 具体作用 | Nerelan 对应概念 |
|---|---|---|
| `user_id` | 工具连接所代理的稳定用户身份 | 宿主用户/Owner 身份，不是模型账号 |
| `AuthConfig` | 某一工具包的授权方式和 OAuth 参数 | 外部应用认证配置，不是 Magpie Provider/Model |
| `ConnectedAccount` | 已完成关联的具体 GitHub/Gmail/Slack 账号 | 工具账户连接；不能与模型订阅池混为一谈 |
| `Session` | 对某用户可使用的工具范围、账户优先级、费用设置、Sandbox 和 MCP 端点 | Task/Attempt 的**非权威工具访问上下文** |
| Toolkit/Tool | GitHub、Gmail 等应用能力和动作 | Pack 的可选能力，受宿主风险/权限二次门控 |
| `instant` | 有条件使用 Composio 自有账户调用并收取工具费 | **第三方工具费用**，不属于 Magpie 模型 token 账 |

**范围定性：** Nerelan 的本体仍是 TaskStore + ExecutorRouter + Magpie + 受控审查。Composio 不是 Agent 控制面、不是模型订阅账号池，也不能替代 Nerelan 的 Magpie 接入。

### 上游关键入口

- [Python SDK](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/sdk.py)
- [Tool Router session](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router_session.py)
- [Tool Router creation](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router.py)
- [ConnectedAccount](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/connected_accounts.py)
- [AuthConfigs](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/auth_configs.py)
- [Session 配置](https://docs.composio.dev/docs/configuring-sessions)

## 2. 模块 A：账户归属不是模型资源池（P1：避免混用）

**已确认的事实**

- Composio 的 `ConnectedAccount` 与 `AuthConfig` 是不同对象：账号通过用户授权连接，而 AuthConfig 表示方式、范围和客户端信息；OAuth 链接完成后账号属于项目+用户，可供后续符合权限的会话复用。
- Session 的 `connectedAccounts` 明确指定特定工具包的账户时，该覆盖不会暗中选择其他账号作为替代。没有 Pin 时工具账号可能按“最近成功连接”等后端策略选择，故不能把“当前 Session 有 GitHub 能力”误当成“必然操作了 Owner 选择的那个仓库或企业账号”。
- [ConnectionRequest.wait_for_connection](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/connected_accounts.py) 将 ACTIVE 与 FAILED/EXPIRED/REVOKED 区分；INACTIVE 没有被视为不可恢复的终态；轮询尊重 Retry-After（但客户端内部重试可能使外层 timeout 不精确）。

**Nerelan 具体可抄的协议形状：**

`ToolConnection = (owner_identity, provider_app, auth_config_ref, connected_account_ref, scopes, state, last_verified, provider)`

`ToolSessionGrant = (task_id, attempt_id, connection_ref, allowed_tools, approved_actions, policy_digest, expiry, generation)`

这里仅是**研究建议 Schema**，不是 Nerelan 已实现接口。密钥仍由受信任的 Credential/Connector 层持有；ToolSessionGrant 只存引用，不存明文 token。

**必须拒绝的路径：** 借此把 Claude/Codex/OpenAI 等 LLM 账户从 Magpie 搬到 Composio；或者授权单个 Gmail 工具包后默认允许使用该用户的所有 Gmail 账户。

**现有归属：** [#287 Configuration](https://github.com/dddd2024/Nerelan/issues/287)、[#790 MCP](https://github.com/dddd2024/Nerelan/issues/790)、[#253 Pack](https://github.com/dddd2024/Nerelan/issues/253)。无需新建账号管理器。

## 3. 模块 B：Session 策略容易出现“遗漏即放开”（P0 研究风险）

**上游证据**：[Session config](https://docs.composio.dev/docs/configuring-sessions)、[Python TypeDefs](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router.py)。

- 不传 `toolkits` 时，Composio Session 默认可发现整个目录；传 `{"enable": []}` 表示禁止所有应用工具包；传 `{"disable": []}` 仍是无限制。删除/清空一个 Session 策略可能扩大权限。早期 SDK 版本的空白名单行为不同；版本敏感，不能绕过升级测试。
- 默认 Session 启用**远程 Sandbox**，可以展示 `COMPOSIO_REMOTE_WORKBENCH` 和 `COMPOSIO_REMOTE_BASH_TOOL`。没有需要远程执行的场景，必须明确 `sandbox.enable=false`；仅用应用工具不等于需要打开远端 Shell。
- `manage_connections`、`search`、`execute_multi` 等 Meta Tools 具备能力扩展性；工具包 allowlist 不必然关闭所有 Meta Tools。要单独审核其效果，而不是通过 app toolkit 名称推断。
- MCP Tools 的 `readOnlyHint` / `destructiveHint` 只是分类标签，不能成为 Nerelan 的操作授权来源。
- Session `config_version` 可用于乐观并发更新，但一份 SDK 会话配置不等于 Nerelan 一次 Attempt 的不可更改授权快照。

**Nerelan 可学：** 对所有可选第三方工具采用 *default-deny exact allowlist*，拒绝未明确的 App、Tool、Action、Account。每个运行/工具执行有固定的授权摘要，且敏感调用前再次检查当前撤销状态。

**No-go:** 在一个执行器里直接挂一个未经宿主逐项约束的“所有 Composio 工具”会话，或者允许某个 Repo/MCP 配置自行打开远程 Shell。

## 4. 模块 C：MCP 与 SDK 是两条不同的执行路线（P0 研究风险）

**文档证据**：[Using sessions via MCP](https://docs.composio.dev/docs/sessions-via-mcp)，源码 [Modifiers](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/_modifiers.py)、[Tools](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tools.py)。

SDK 方式 `session.tools(modifiers=...)` 将 Schema/Before/After 修饰器挂在 Python 本地包装工具上。Hosted MCP 方式由执行器直连 Composio 后端 MCP URL：**不经过 Python/TS 客户端的本地工具执行代码，所以本地 beforeExecute/afterExecute/modifySchema 不运行**；本地自定义工具也不会自动出现在 Hosted MCP 中。

此事实**不代表 Composio 服务端 Session Toolkit 限制失效**，而是提醒宿主不能把 *local SDK modifier* 当成全协议的权限或审计边界。

### 对 Nerelan 的正确限制

如果 Nerelan 想让任何执行器通过工具调用执行外部副作用，必须确保某种**可信的请求入口**可以对每个请求进行：
1. 识别 Task/Attempt 与有效 Owner 授权；
2. 校验 Tool、Tool Args、ConnectedAccount、成本与敏感操作；
3. 持久化意图与幂等/收据身份；
4. 允许或拒绝；在权限允许时将调用交给被授权的 MCP/SDK；
5. 收到结果后核对回执与费用。

当某个外部 Agent 直接向 Hosted MCP 发送请求，而宿主无逐请求中介能力时，**不能假称上述拦截已经实现**：应改用受控本地代理/受限且有短生命周期的远端 Session，或对此类敏感工具路径直接拒绝。

### MCP Headers 的额外警示

`session.mcp.headers` 可以包含项目 API Key，某些用户身份模式下甚至会携带更广范围的 User API Key；SDK 做 Origin 检查，并对不匹配端点拒绝凭据附着。执行器仍要安全处理跳转、日志和 Header 转发，不得输出到 Task Evidence 或给模型看到。

Composio 允许 MCP 客户端不支持 elicitation 时选择 `no_elicitation_support_fallback = allow | deny`；Nerelan 的敏感动作必须使用 `deny`，不能为了“工具能用”绕过批准。

**现有归属：** #790/#447/#303；直接 MCP 连接是否可治理，是首批必须验证的协议测试。

## 5. 模块 D：混合本地/远端批量执行的审批非原子性（P0 测试入口）

**源码**：[`_route_multi_execute` in ToolRouterSession](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router_session.py)。

真实代码行为：
1. `COMPOSIO_MULTI_EXECUTE_TOOL` 的工具调用分为 local 和 remote 两组；
2. 用 `ThreadPoolExecutor(max_workers=min(5, tasks))` 对本地调用并发处理，并同时发远端批量执行；
3. 先收集本地结果，再等待远端；
4. 远端如抛 `ToolInputRequiredError`，源码注释明确说**本地调用可能已经完成，其结果会被丢弃**，然后传播审批异常；
5. 再执行同一批请求时，如果没有按每个子操作记账/去重，可能重放已经发生的本地副作用。

**这不是 Composio“所有审批都不安全”的结论**，而是一个具体的“跨本地与远端工具批次不能被视作原子事务”的源码反例。尚未动态复现。

### Nerelan 必须避免

- 对混合有副作用动作的 Batch，在**全部准入检查通过前**就运行其中一部分；
- 把 `NEEDS_APPROVAL` 状态自动视作“本批所有工具都未执行”；
- 只按 Batch ID 记录成功而不保留子操作 `tool_call_id`；
- 被打断后全批重试而不检查已完成子操作的副作用/收据。

### 可复用方式

分离 `prepare -> authorize_all -> execute_allowed -> settle_per_operation`；若无法原子化，则使用有界、显式的部分完成记录与补偿/人工裁决，避免假装事务。

**最小测试：** 一个本地 Dummy Tool 对临时计数器做加一，远端 Dummy Tool 抛 `ToolInputRequiredError`；同批请求重试一次，验收要求本地计数器不能被隐式加两次，且 UI 提示部分执行/未知状态。测试用假客户端与 Provider-free Fixture，不使用任何真实账户。

## 6. 模块 E：渐进式工具发现与 Prompt Context 成本

**上游**：[Session tool wrapping](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router_session.py)、[Tools schema](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tools.py)、[Session configuration](https://docs.composio.dev/docs/configuring-sessions)。

- 默认通过 `COMPOSIO_SEARCH_TOOLS` 等 Meta Tools 在运行时选择工具，而不是将目录里所有工具的 Schema 一次性发给模型。
- 对明确的专业工作流，可用 `preload.tools` 或 `direct_tools` 预加载已知的少量工具；文档建议通常少于 20 个，避免 Prompt 体积急剧增加。
- 但动态发现会付出额外的 Tool Search 调用、延迟与潜在错误；“更多工具不写入 Prompt”不等于总体成本必然更低。
- Local Custom Tool 在 SDK 进程内执行，Hosted MCP 不会自动暴露；跨执行器如果使用不同集成协议，工具可用性也可能不同。

**Nerelan 复用建议：** Pack 宣告可用 Tool Catalog；每个 Task 先声明候选功能，宿主投影出仅这个 Task 可见的 `tool schema shortlist`；可选“搜索后再加载”的递进模式，比较每成功任务的模型 token、Tool Search 次数、权限拒绝与验收率。

**归属：** #253/#296/#790。保持现有 `capability_registry.py` 的只读 Manifest 安全边界，避免新增通用插件管理服务。

## 7. 模块 F：Instant Tool 费用独立于 Magpie（P0：防止账本与预算误判）

**上游**：[Instant Tools](https://docs.composio.dev/docs/instant-tools)、[Python Session config](https://github.com/ComposioHQ/composio/blob/c59c2db88a5c67d8034280f1b5639c9f5cf783cc/python/composio/core/models/tool_router_session.py)。

- Composio Instant（过去称 Premium）可使用 Composio 的工具账户并向组织余额收取**工具调用费用**；该能力是项目层开启的实验功能，**默认项目不开启**。但是一旦项目开启，Session 未显式关闭 Instant 就可能使用并产生收费。
- **Session API 没有精确的每会话 USD Hard Cap 参数**。调用后返回的费用不能代替事前预算上界。预付余额检查为异步，也不保证精确硬上限。
- 成功/失败或超时调用可能有迟到账单，缺少费用回执不代表零费用。
- 这与 Nerelan 的 Magpie 模型 token 账单不同；不能直接混进 Magpie request log，也不能以固定模型费率替代。

**Nerelan 初始策略：** 对可选 Composio Connector，`instant=false`，`sandbox=false`，且默认不给 Agent 自动授权更改这些设置。若未来 Owner 明确允许付费 Tool，则必须独立预留上限、限制并发占用、按真实工具请求身份对账、区分 UNKNOWN/zero，并考虑执行器模型费与工具费的合计。这属于现有预算授权机制的增量而非第二套账本。

## 8. 用户视角与实现边界

用户真正需要的不是“插件商店里有上千个工具”：

- 连接某个 Gmail/GitHub 账号后，清楚看到**哪些 Task/Pack 能使用，具体会使用哪个账号**，不允许暗中换账户；
- 将一个 Pack 暂时授予“读取 Issue”和“创建 Draft”权限，而不是“拥有整个 GitHub”；
- 接近敏感动作时明确显示是**哪一个工具调用、哪些参数、哪个执行器、哪个账号、是否额外收费**；
- 发生登录失效、审批等待、外部服务超时与部分成功时，Agent 不会把完成的操作再执行一次；
- 从同一个任务视图看到工具开销是否已核对、账号仍需连接还是已被撤销。

目前 Nerelan 的 `capability_registry.py` 提供 Manifest 元数据，`#790` 提供 MCP 生命周期方向，`#253` 提供 Pack 产品单位；这些要继续保持 Host-owned，不能让 Composio Cloud 成为 Nerelan 任务授权、成本总账或执行状态的权威。

## 9. 复用决策和现有 Issue 映射

| 子模块 | 结论 | 优先度 | 归属 |
|---|---|---|---|
| User/AuthConfig/ConnectedAccount/Session 分离 | 借鉴身份/范围模型；可选适配器独立评估 | P1 | [#790](https://github.com/dddd2024/Nerelan/issues/790) / [#287](https://github.com/dddd2024/Nerelan/issues/287) |
| SDK vs Hosted MCP 拦截差异 | **必须纳入反绕过测试** | P0 (research risk) | [#790](https://github.com/dddd2024/Nerelan/issues/790) / [#447](https://github.com/dddd2024/Nerelan/issues/447) |
| 混合批执行“先有副作用再审批” | **必须纳入故障恢复/幂等测试** | P0 (research risk) | Existing task execution & tool policy |
| Toolkit 白名单、固定账号、禁止默认 Sandbox | 借鉴安全默认值，不直接照搬开放默认 | P1 | [#303](https://github.com/dddd2024/Nerelan/issues/303) / #790 |
| 搜索工具 vs 少量工具预加载 | Prompt/工具成本对照，不重复造 Toolkit 目录 | P2 | [#296](https://github.com/dddd2024/Nerelan/issues/296) / [#253](https://github.com/dddd2024/Nerelan/issues/253) |
| Instant 外部工具费用 | 初期关闭；如启用须独立预算证据和事前授权 | P1 | Existing budget + #790 |
| Composio Cloud/Auth/Tool backend 接管主平台 | **拒绝**；本地优先、密钥保管与 TaskStore 不迁移 | REJECT | [#361](https://github.com/dddd2024/Nerelan/issues/361) |

### “直接复用”是否可能

可以考虑**自愿安装、明确授权**的 Python SDK 或 Hosted MCP Session，用于用户确有需求的单个外部应用工具包。但这要求实际做凭据托管/网络边界/远端结果数据外流/Tool Policy 一致性评审。**它不是纯本地零成本插件，也不能宣称完整自托管。**

## 10. 待做试验（本次未执行）

1. **权限漏口矩阵：** SDK Direct、Hosted MCP、native Agent MCP 连接三条路径分别测试 Toolkit allowlist、Tool allowlist、Hook、MCP Elicitation 不支持时 deny、Session 设置被清空后的访问。Pass：任何敏感动作不能绕过 Nerelan 授权，且不可审计路线拒绝。
2. **混合调用重复副作用：** local=写入可见计数器，remote=审批中断，之后 retry；Pass：计数器一次，账簿记录子调用结果和不确定状态；未能保证时禁止这种 Batch。
3. **连接选择：** 同一用户两组独立的模拟工具账户，无 Pin/有 Pin、失效、撤销、跨 Task Session；Pass：绝不对未经 Task 授权的另一账户 fallback。
4. **工具目录上下文消融：** 直接列完整工具、少量已知工具、动态 Search；Pass：在成功验收率和权限一致条件下，整体成本/耗时真实降低，不能只看提示词短了。
5. **工具成本与迟到收据：** Instant disabled fixture、已授权的模拟费用、迟到/缺失/重复收据；Pass：无未授权收费、无重复结算、未知仍 UNKNOWN。

## 11. 对比其他研究与下次再审计门槛

- OpenClaw/Paperclip：强调执行器、会话与插件 Loader；本次补的是**外部应用账户归属与托管 MCP 的真实执法边界**。
- Mastra：有 Tool Approval 的局部策略覆盖问题；本次补的是**SDK/MCP 不同路径和混合 Batch 产生不可回滚副作用**。
- Nerelan 差异化并不是“连接 1000+ Apps”，而是将工具使用纳入任务级实际授权、资源经济性和独立验收；此主张必须实测成立。

如再研究 Composio，需要指出当前报告之外的新源码模块与未解决假设，否则判定为重复，直接引用本研究。不复制上游源码；没有安装、执行、付费调用、凭据访问或实证评测。

**研究 Issue**：[#1567](https://github.com/dddd2024/Nerelan/issues/1567)。**合并准入**：遵守 Nerelan [AGENTS.md](../../AGENTS.md) 的 R1 文档 PR + exact-head CI + 独立评审；研究讨论不能替代 Owner 的真实权限决策。
