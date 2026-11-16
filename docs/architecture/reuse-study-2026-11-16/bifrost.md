# Bifrost 源码深拆：Key 故障分类、请求级重试、Session Affinity 和 Magpie 经济性对照（2026-11-16）

> **状态：** `STATIC_SOURCE_REVIEW / RESEARCH_ONLY / NOT_TESTED / NOT_INSTALLED / NO_IMPLEMENTATION_AUTHORITY`  
> **上游：** [maximhq/bifrost](https://github.com/maximhq/bifrost)，冻结 commit [`31c9e762c235`](https://github.com/maximhq/bifrost/commit/31c9e762c235f6905c13793eabad0200633261a5)；仓库 [Apache-2.0](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/LICENSE)，部分高级功能在 Enterprise 计划，不能把宣传项一律当开源实现。  
> **Nerelan 代码基线：** main [`__NSHORT__`](https://github.com/dddd2024/Nerelan/commit/a7b6277772aefef33138921f357c459f259e718b)；研究登记 [#1573](https://github.com/dddd2024/Nerelan/issues/1573)。  
> **范围：** GitHub 源码、测试、文档与 Nerelan 现有代码/Issues 的静态对照。未在本机运行 Bifrost、未接入/操作 Magpie、未读取用户账户、未发模型请求、未独立复现性能收益。

## 0. 前置查重：什么已做过、这轮哪里是增量

- 检查了中央研究索引草稿、11 月 15 日复用研究五分项、[A-pooling.md](../reuse-study-2026-11-15/A-pooling.md)、[Magpie 能力地图](../MAGPIE_CAPABILITY_MAP.md)、11 月 16 日研究 Issue/PR、新的代码/Issues/PR 搜索：没有 Bifrost 专项源码研究/实施 Issue。结论是“在当前 GitHub 入口未发现”，不能据此否定聊天中的非正式提及。
- **不重复**：多 Key 池、权重选择、Quota Wait、Provider Fallback、Gateway Key 硬预算、Session Sticky、用量日志、模型价目表等功能已经由 Magpie 提供且在上面的账户研究中记录。之前也深入比较过 one-api/new-api/LiteLLM 的错误分类与超时。
- **本轮真实源码新增**：Bifrost Provider-specific 错误类别的精细含义、在一次请求内何时换 Key、尝试轨迹、成功后写入的 Provider/Key 会话亲和、归因和预算边界、不可直接套用的商业功能/性能宣称。
- 现有实施唯一负责人仍是 [#1342 Magpie 总复用审计](https://github.com/dddd2024/Nerelan/issues/1342)、[#1530 429 暗中重试](https://github.com/dddd2024/Nerelan/issues/1530)、[#1531 UNKNOWN 占满预留](https://github.com/dddd2024/Nerelan/issues/1531)、[#667 额度 UX](https://github.com/dddd2024/Nerelan/issues/667)、[#1267 单/多模型经济性](https://github.com/dddd2024/Nerelan/issues/1267)、[#1527 Harness×Model](https://github.com/dddd2024/Nerelan/issues/1527)、[#361 复用优先](https://github.com/dddd2024/Nerelan/issues/361)。**不另开同名开发 Issue。**

## 1. 位置：Bifrost 与 Nerelan 的正面比较

| 维度 | Bifrost | Nerelan / Magpie 当前 |
|---|---|---|
| 接入 | Go 网关，OpenAI 等兼容 API 与 Provider Keys、Virtual Keys、路由、MCP | Magpie 统一 API + 多种订阅登录/服务账户 + API 模型；OpenCode/Codex/Claude 等执行器 |
| 多账户 | 同一 Provider 下选择可用 API Key、按权重和故障类别切换 | Magpie group、stays、quotas、provider fallback 已存在，但 Nerelan 未充分启用 |
| 失败 | Provider/type/code/message 组合的 FailureClass；请求内有 Key Attempt Trail | Magpie `err_type/err/tries/status/account/session` 已在日志；Nerelan 有固定 429/hold、Probe 再次请求无效账号的旧问题 |
| Session | 成功服务后的 Provider/Key 绑定到调用者 Session，尽可能利用缓存 | Magpie `stays=auto` 已支持；应做等价试验而不是第二个亲和层 |
| 成本 | 模型价目表+usage+虚拟 Key 预算、可观察请求轨迹 | Magpie 记录请求/额度；Nerelan 区分 PAYG cash、subscription quota opportunity value、list-price estimate、Task acceptance |
| Agent | 兼容 Coding Agents 的 Provider API 网关与 CLI Agent 接入 | Nerelan 更上层：按任务能力和成本选 Executor×Model，长期恢复、独立验收、真实成果质量 |

**结论先行**：Bifrost 是成熟的 API-provider 网关候选，适合当 Magpie 的**功能对照/故障分类实证样本**；不建议双 Gateway 串接、不应擅自迁移多个订阅账户或重建账号 UI。Bifrost README 的微秒延迟/5k RPS 数据来自上游自测，与 Nerelan 本机异质订阅/长时 Agent 的任务价值没有等价关系。

## 2. 模块 A：Provider-specific 失败分类（P1：高度匹配现存事故）

**固定源码**：
- [`core/failureclass.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/failureclass.go)
- [`core/schemas/failureclass.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/schemas/failureclass.go)
- [`core/failureclassrotation_test.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/failureclassrotation_test.go)
- [Retry/fallback 设计与真值表](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/features/retries-and-fallbacks.mdx)

### 核心机制

Bifrost 定义 11 个失败类别，区别于仅按 HTTP 状态码分组：

| `failure_class` | 何种错误 | 该 Key / Provider 的重试语义 |
|---|---|---|
| `credential` | 错 Key/过期凭据/身份拒绝 | 本请求移除该 Key，尝试其他已授权 Key，不宜原 Key 短时重复探测 |
| `quota` | 账户余额耗尽/Spend Cap/Billing Block | 本请求不再尝试该 Key；跨请求应持有至有可信恢复依据 |
| `model_access` | 这个 Key 不允许访问该模型/部署 | 换能访问同模型的 Key；**不能推导该 Key 所有模型不可用** |
| `model_gone` | 模型被停用/退役 | 不能仅靠等待；需经过新的模型可用性证据或受控替代 |
| `region_blocked` | 地区或账户主体受限 | 可能与账户关联，也可能是整个出站地址问题；不应无限换 Key |
| `rate_limit` | RPM/TPM/并发限制或普通 429 | 可换 Key，仍有退避；Account 级共享配额要小心 |
| `transient` | 上游 500/502/503/504/529、网络暂时失败 | 同 Key 退避，不因为服务器过载而把所有 Key 探死 |
| `caller_fault` | 参数错误/请求长度等 | 不换 Key，返回请求问题 |
| `unknown` | 上游格式不认识，如代理 HTML 404 | 不自动宣称临时限流或永久停用；收集证据 |
| `timeout` | 请求或 TTFT 截止 | 不在已失效请求 Deadline 内重试；可能按规则转 fallback |
| `cancelled` | 调用者取消/断开 | 不判定为上游账号失效，也不安排自动同请求重试 |

### 重要的 Provider 例外

- OpenAI `429 insufficient_quota` = `quota`，不是普通可短时恢复 `rate_limit`；
- Anthropic 余额太低可能用 `400` 报告，不能按“400=请求参数错误”处理；
- Bedrock/Gemini 失效账户、模型无权限或地区受限可能共享 `403` 或 `400`，要读取 provider code/type、例外名称与消息；
- Anthropic `529 overloaded_error` 是服务端容量，不是“换另一个订阅就能解决”的 Key 故障；
- Provider 返回模型无权限时不应对该账户其他模型全部封禁，只有 Credential/Quota 明确 CoversAllModels。

**源码注意**：分类器使用结构化 provider type/code 优先，消息短语只是未明确提供结构化字段时的补充，并保持较窄匹配；这不是一个关键词出现就可以封禁全部账号的正则。其规则必须结合 Magpie 的原始字段做离线 Replay，不直接移植整套 Go 实现。

### Nerelan 价值与已有事故

[#1530](https://github.com/dddd2024/Nerelan/issues/1530) 证明工作流曾把重复上游拒绝误判为 900 秒 `executor_stalled`，无法触发正确的额度 Hold 与切换；[#1531](https://github.com/dddd2024/Nerelan/issues/1531) 又把多次拒绝收敛为大量 UNKNOWN 预留。Magpie 已保留 `err_type/err/tries`，不足之处是没有针对上述事实一致应用的统一分类与动作。

**建议：** 先在 Nerelan/Magpie 已有日志读取通道增加一个 **Provider-free taxonomy replay** 测试契约，让“上游拒绝→等待/切换/暂停/刷新”的动作有证据；若确认 Magpie 已能执行相同分类，直接配置并读取它的归因结果，**不用再造一个 Key 决策器**。

## 3. 模块 B：一次请求内的尝试轨迹与重试边界（P1）

**源码/文档**：
- [`failureclassrotation_test.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/failureclassrotation_test.go)
- [`core/schemas/failureclass.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/schemas/failureclass.go)
- [Attempt Trail 结构](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/features/observability/default.mdx)

关键机制：

1. 每个尝试可记录 `attempt / key_id / failure_class / status_code / fail_reason / retry_after_ms / triggered_rotation`；`selected_key_id` 表示真正成功服务的 Key，失败链不能从它反推。
2. **永久 Per-key 拒绝可以在 `max_retries=0` 时继续遍历备用 Key**，因为切换到另一个明确可用 Key 不同于“在同一坏 Key 上无效重试”。但这仍可能额外消耗网络/额度，所以需要全局 Attempt 上界、一次请求总截止和授权的可用候选池。
3. 对 `429` 仍退避；`5xx/529` 不因为想切换账户就无意义地旋转；`caller_fault`、`unknown`、`cancelled` 不让路由器盲目重试。
4. 注入的 Provider request_id / Stream 是否已经收到第一个 token 属于额外生命周期信息；在错误流状态不能自动断言“模型没有产生 Token/费用”。

**对 Nerelan 的证据建议（非已实现 Schema）：**

`GatewayAttempt = {gateway_request_id, executor_session_id, goal_id, task_id, attempt_id, requested_model, served_model, provider_account_ref, provider_error_type, status, retry_after, retry_action, retry_owner, metered_usage_ref, observation_time}`

**不是**“把上游 Bifrost 的 key_id 映射为 Magpie 的账户 ID”；只用 Magpie 自己记录的身份和权限摘要。一次 Executor Attempt 中可能有很多 Gateway Request；一个 Gateway Request 又可能有多个内部尝试。不得按 `tries * input_tokens` 计算用量，不能把内部失败次数当成多个 Task Attempt 收费。

## 4. 模块 C：Session Affinity 不等于任务级选择（P1：优先做等价试验）

**固定源码**：
- [`core/sessionaffinity.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/sessionaffinity.go)
- [Session affinity 文档](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/providers/session-affinity.mdx)

**机制**：
- Session ID 来源可以是明确 Header，或适配 Claude Code / Codex CLI / OpenCode 的原生会话头。Bifrost 以 virtual-key + user + session_id 形成隔离作用域，防止两个用户复用同一 Session 字符串时错误共享路由结果。
- 两级绑定：`Provider+Model` 的先前成功 Route 和该 Provider+Model 下先前成功 Key。**只有真正成功服务请求时写入**；沿绑定失败后移除；调用取消不证明所绑定 Key 有问题。
- 路由规则先决定哪些 Provider/Key 合法，Affinity 只能在**仍被允许**的候选里调整优先级。不会因为缓存价值保留被禁用、无权限、配额耗尽的 Key。
- 基于最后一次成功请求的绑定会影响前缀缓存命中率，尤其 Coding Harness 大量跨轮请求；但系统不能为了保缓存而无视预算、质量或 Owner 的 Account/Model Pin。

**Nerelan 比较**：
- [MAGPIE_CAPABILITY_MAP.md](../MAGPIE_CAPABILITY_MAP.md) 已证实 Magpie 有 `stays=auto` 及 Session 请求日志。因此**第一步是比对 Magpie 的会话作用域/用户身份、回退后绑定更新、Key/Provider 失效时解除绑定**。不需要复制 Bifrost 的亲和存储。
- 上层 Nerelan 负责是否在 Task 子步骤改变模型能力档位；底层 Magpie 负责满足同一个模型意图时选哪一个实际可用的账户。不能跨层二次选 Key。
- 多 Agent 并发中，两个子调用若共享 Session ID，可能竞争更新同一缓存归属；需要用实际 Header/网关日志证实，而不是假设共享 Session 能保证全程一个 Key。

## 5. 模块 D：权重随机与可用模型目录（P2：大部分已由 Magpie 处理）

**源码**：
- [`core/keyselectors/weightedrandom.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/keyselectors/weightedrandom.go)
- [Provider routing/model catalog](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/providers/provider-routing.mdx)
- [Key management](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/features/keys-management.mdx)

Bifrost 先过滤模型 Allowlist 与授权，再按权重抽取 Key。权重算法还处理负数、NaN、∞、浮点极值，以及全部权重为零时均匀选择。此类健壮性可以转化成 Magpie 配置审计/Fixture，但 **Weighted Random 只平衡请求，不判断任务是否能高质量完成**。

其 Model Catalog 同时接入价格表和 Provider List Models API，以便新模型及时出现。**知道模型名称或存在标价，不等于该订阅账号真有权限，更不等于这个 Executor 能透传 Tool/Reasoning 等能力**。Nerelan 的 #1527 模型×Harness 真实运行证据应优先于静态目录，而 Magpie 的已有模型发现/Probing 先作为主通道。

## 6. 模块 E：用量、预算与隐私边界（P1：应保留原账户证据）

**源码/文档**：
- [`core/relay/usage.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/core/relay/usage.go)
- [`framework/logstore/dimensionusage.go`](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/framework/logstore/dimensionusage.go)
- [Observability](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/features/observability/default.mdx)
- [Budget and limits](https://github.com/maximhq/bifrost/blob/31c9e762c235f6905c13793eabad0200633261a5/docs/features/governance/budget-and-limits.mdx)

### 源码发现

- Relay 的 `usageFields` 对 Input/Output/Total/Cost 等字段**单独记录存在性**，而不把缺字段自动视为零。自定义 Relay 只有配置了 Token 的映射路径才去解释 Token，不从非 LLM API 的任意 JSON 键猜用量。这对多种非模型收费服务、Vision/Audio/MCP 工具有参考意义。
- 价格表、Provider 模型报价和 API Response Usage 能产生费用估计或 Provider 报告值，但不能推断用户的订阅现金支出、周额度百分比或订阅年费已被支付。Nerelan 现有代码已把 `PAYG cash`、`subscription allowance` 和 `list-price equivalent` 分开；不要引入一套按 Token/Price 自动算“真实现金”的账本。
- Bifrost 的请求追踪通常可以记录完整 Prompt、工具调用和回答，有利于调试但会产生**额外的私密内容/凭据泄漏面**。没有额外授权不要把 Nerelan 的用户任务、执行日志与账号信息导出至第二套日志平台；Magpie 的最小化 request metadata 已足以支撑绝大多数诊断。
- **OSS 多节点 HA 是明确限制**：上游文档明确说在多个 OSS 节点加 Postgres 时，实例内缓存不会自动跨节点同步；Enterprise 使用不同机制。不能宣传“只要多个副本+共享数据库就能统一硬预算/实时额度”，也不宜因此引入其商业集群依赖。
- Virtual Key/Team/Customer 预算面板是 API 使用者治理，**Nerelan 已有 Magpie gateway-key 短时 Key 与授权预算**；新增第二个预算网关会使 Task 到 Account 的归因更加复杂。

## 7. 用户体验：借鉴哪些信息，而不让用户被 Gateway 参数淹没

用户应看见的是一个任务级归因说明，不是运维内部的 `error_code` 列表：

| 真实情况 | 用户可理解的说明 |
|---|---|
| 账户订阅周额度用完 | “这个账户本周剩余额度不足，已等待重置/转到其他已授权账户” |
| 模型对本账户无权限 | “模型存在，但该账号不能使用；不会反复检测同一组合” |
| 临时请求频率限制 | “服务正限流，下一次重试时间有证据；不会默默耗尽 900 秒” |
| Provider 529 服务拥塞 | “上游暂时拥塞；重试保留原账号以维持缓存，不错误封号” |
| 网络超时 / 不完整 Stream | “请求状态未确认，费用可能待对账”，不标零成本 |
| 账户切换与 Prompt Cache 损失 | “切换可能减少等待但增加本任务消耗”，以实测数据决定 |

Bifrost 在 Agent × Model 层面的直接竞争性不等于 Nerelan 的成果质量闭环：用户真正关心的是 **在已经拥有的订阅/API 资源里，以最少真实成本获得被独立验收的结果**。

## 8. 借鉴/拒绝矩阵（不创建重复开发工作）

| 复用候选 | 处置 | 优先级 | 已有归属 |
|---|---|---|---|
| Provider-specific FailureClass 决策表 | `BORROW_PATTERN_ONLY`，先用 Magpie 真实拒绝日志做离线校验 | **P1** | [#1530](https://github.com/dddd2024/Nerelan/issues/1530), [#1342](https://github.com/dddd2024/Nerelan/issues/1342) |
| Request 内 attempt trail → Gateway Request/Task 关联 | 借鉴证据格式；Magpie 为唯一请求观测 Owner | **P1** | #1342, [#1531](https://github.com/dddd2024/Nerelan/issues/1531) |
| Session Affinity 成功绑定/失败释放 | **先查 Magpie `stays=auto` 等价性**；不做第二次 Key 选择 | **P1** | #1342 / model routing |
| Provider price/model catalog | 与实时权限/实际 model acceptance 分开 | P2 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527), #667 |
| Virtual Key 短期预算、加权 Key/Provider Fallback | **ALREADY_IN_MAGPIE**；复用、配置而非编写 | 现有 | #1342 |
| 自建 Gateway、迁移订阅、Bifrost 商业自适应路由 | **REJECT**；重复系统、无法证明订阅支持优势 | — | #361 |
| 将所有日志内容复制进 Bifrost | **REJECT**；额外敏感数据和重复账本 | — | #1342 / Owner Policy |

## 9. 最小验证计划（本轮未执行）

**F1：Provider Error Fixture Replay（无模型调用）**  
冻结 30+ 条结构化 Provider 拒绝样本：OpenAI 429 `insufficient_quota`、普通 429、Anthropic 400 余额不足、Bedrock 403 模型拒绝、Gemini 400 Key 失效、模型退役、529、代理 HTML 404、取消、TTFT 超时、能解析 reset 时间的中文额度拒绝。输入：status/code/type/message/reset header/body；输出：`failure_class, retry_scope, hold_scope, hold_until_source, action`。**必须区分同账户所有模型与单模型拒绝、账号失效与普通限流，不能因 429 自动继续探测耗尽账号。**

**F2：Magpie request/session Correlation（只读已有 fixture）**  
一个 Executor Attempt → 多个 Magpie Requests → 每个请求可有内部 `tries`；复盘并发、超时、部分完成。检查实际请求数与 Token/Cost 确认来源，**不把“tries”作为多个独立收费任务**；缺归因保持 UNKNOWN、晚到请求允许核对而非覆写原证据。

**F3：Cache-Affinity / Account failover（模拟或 Owner 已授权的现有证据）**  
同一 Session 的多轮请求、重置、账户撤销、无权限模型、Provider 失败、并行子 Agent。比较 Magpie `stays=auto` 真实行为与 Bifrost 期望；严禁重新选择被 Owner/配额禁止的账户；测 `cache_read`、成功率和总任务成本，不能只测时延。

**F4：Cost basis / privacy replay**  
同一用量记录分别标注 PAYG cash、订阅 Quota、List-price equivalent；未知时不能变成零。用户 Prompt/密钥只留在受控宿主，不额外复制为 Gateway tracing 全文。

**F5：更换 Gateway 的绝对否决基准**  
只有 Magpie 经设置与修复后仍无法满足签名/Key/协议/Session/预算的明确证据，且候选支持目前实际使用的全部订阅与执行器、Owner 明确授权迁移、成功任务质量与真实成本实验占优，才进入迁移研究。本文没有提供这些证明，**故 No-Go**。

## 10. 结论与 GitHub 状态

**SELECTIVE_DESIGN_REUSE / DO_NOT_REPLACE_MAGPIE**。本轮与 11 月 15 日账户池横向研究的真正差异：逐源码验证“错误类别→原 Key 重试/换 Key/停止”、请求尝试轨迹以及**仅成功后缓存亲和、失败释放亲和**的机制。值得转化成 Nerelan 现有 Magpie Adapter 的回归样本和用户可解释状态。

本文件为 R1 Docs-only Research。上游代码、许可证与版本已固定；没有本地运行、依赖引入、账号操作、模型调用或 CI/独立审查结果。Draft PR 必须按 [AGENTS.md](../../AGENTS.md) 完成 exact-head 基线检查和独立评审，不能擅自合并。
