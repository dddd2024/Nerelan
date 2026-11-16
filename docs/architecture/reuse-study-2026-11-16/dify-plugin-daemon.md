# Dify Plugin Daemon 源码级复用审计：Pack 生命周期、运行子进程与反向调用（2026-11-16）

> **级别：** `STATIC_SOURCE_REVIEW / RESEARCH_ONLY / NOT_INSTALLED / NOT_TESTED / NO_IMPLEMENTATION_AUTHORITY`  
> **上游：** [langgenius/dify-plugin-daemon](https://github.com/langgenius/dify-plugin-daemon)，commit [`1fa10988ce3f`](https://github.com/langgenius/dify-plugin-daemon/commit/1fa10988ce3fb69af48538d3a6d405fcd4769afc)；此 **daemon 仓库** 为 [Apache-2.0](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/LICENSE)，不能由此推断 Dify 主仓库全部同许可证。  
> **Nerelan：** main [`a7b6277772ae`](https://github.com/dddd2024/Nerelan/commit/a7b6277772aefef33138921f357c459f259e718b)；研究 Issue [#1571](https://github.com/dddd2024/Nerelan/issues/1571)。  
> **方法与限制：** 检查上游 Go 源码、README、许可证、示例设置和 Nerelan 真实实现与既有 Issues。没有安装或运行守护进程、下载安装依赖、调用模型、查看用户凭据、进行容器隔离测试或实证 Benchmark。所列代码机制是静态阅读结果，非 Nerelan 已实现功能。

## 0. 选择之前的重复检查（必须保留）

1. 查询现存研究索引草稿（Composio 分支）、2026-11-15 reuse-study、竞品地图、2026-11-16 全部最新研究 Issues/PR，以及 GitHub 文件/Issue/PR 中的 `Dify`、`dify-plugin-daemon`、`langgenius`、`plugin daemon`。
2. Dify 在旧文档有少量泛指，但未发现 **langgenius/dify-plugin-daemon 的独立源码级专项记录或实施 Issue**。这是“在所查 GitHub 入口未发现”，不是绝对否认历史聊天。
3. 已有研究：OpenClaw 的插件 Manifest/Loader，Composio 的 SaaS 工具账户/MCP，Agent Sandbox 的执行环境真实隔离，Mastra 的工具授权和 Eval。**本轮增量**限定为：完整的 `.difypkg` 生命周期、签名/版本/校验和、Python 子进程、标准流协议、插件反向调用宿主、后台安装任务与卸载/故障边界。
4. 实施范围已经由 [#253 Pack Productization](https://github.com/dddd2024/Nerelan/issues/253)、[#789 Agent Hooks](https://github.com/dddd2024/Nerelan/issues/789)、[#790 MCP Runtime](https://github.com/dddd2024/Nerelan/issues/790)、[#303 Workspace Trust](https://github.com/dddd2024/Nerelan/issues/303)、[#299 Sandbox](https://github.com/dddd2024/Nerelan/issues/299) 和 [#361 Reuse Gate](https://github.com/dddd2024/Nerelan/issues/361) 管理，不新建同名实施路线。
5. 中央 `REUSE_RESEARCH_INDEX.md` 暂时只存在于 #1563 → #1565 → #1568 的待审 Draft PR 链；本轮按 `AGENTS.md` **从当前 main 独立建分支、Draft PR target main**，在现有竞品与复用地图建立可检索入口，等待索引正式合入后再补记，不创建平行“第二研究索引”。

## 1. 要理解的架构边界

本项目是 Dify 的 **Plugin Daemon**，不是整个 Dify 产品或通用 Coding Agent。它作为服务接收主应用请求、保存插件安装包、维护声明/租户安装、管理 Plugin Runtime，并将请求转交到 Local/Debug/Serverless 执行路径。

[README](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/README.md) 自述：
- `Local`：Go Daemon 启动 Python 子进程，通过 stdin/stdout 交互；
- `Debug`：开发者本地插件通过 TCP 全双工连接；
- `Serverless`：Daemon 将调用路由至远程服务函数；
- 其安装数据库、Redis、存储和 Python/uv 依赖均是该系统的基础运维成本。

**Nerelan 不需要重新造一个 Dify：** 现有 `reverse_agent/platform_v1/capability_registry.py` 刻意只读 JSON Manifest，不执行外部程序。`TaskStore`、`ExecutorRouter`、Owner Policy、Magpie 仍是唯一权威。把 Plugin Daemon 接入只应作为未来**经过 Owner 授权的可选 Pack Runtime** 候选，而不是升级现有 Pack 所必须安装的基础设施。

## 2. 模块 A：Plugin Manifest 与 Pack 的关系（P1：仅借鉴 Schema）

源码：[`pkg/entities/plugin_entities/plugin_declaration.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/pkg/entities/plugin_entities/plugin_declaration.go)。

上游结构：
- Plugin 类别：`tool`、`model`、`extension`、`agent-strategy`、`datasource`、`trigger`；
- `Meta`：插件版本、架构列表、`Runner(language/version/entrypoint)`、最低 Dify 版本；
- `Resource`：内存要求及 Permission 声明，含模型类型（LLM、embedding、rerank 等）、Tool、App、Storage、Node、Endpoint 等；
- `PluginExtensions`：插件暴露的具体工具、模型、Agent Strategy、数据源、触发器文件路径。

**细节值得借鉴：** Schema 不止描述“插件叫什么”，还提供运行条件、反向能力需求和可列出的工具/扩展。用户安装前可看到“需要哪些能力、是否可运行”。

**不应直接映射：** Dify 的 `agent-strategy` 是其 Agent 层策略扩展，不是 Nerelan 的 OpenCode/Codex/Pi 等完整 Executor；Dify 的 `model` 插件也不是 Magpie 的模型账号池。Nerelan `Pack = Skills + Tools/MCP + Knowledge + Agent Profiles + Workflow + Verifier + Eval + Policies`，比 Dify 单个 Plugin 的 Schema 更广，不该缩成单个 Dify 插件定义。

**提案最小增量（非现有实现）：**

`PackRuntimeRequirement = {pack_digest, declared_tools, required_host_capabilities, min_adapter_version, supported_arches, isolation_class, permissions_requested, runtime_type, memory_limit}`

只用于可解释的预检/允许列表，不触发任意运行命令；由 Host 按真正可用能力和当前授权判断。

## 3. 模块 B：包签名、安装步骤与“安装不等于激活”（P1）

源码：
- [`plugin_decoder.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/service/plugin_decoder.go)
- [`decoder/verifier.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/pkg/plugin_packager/decoder/verifier.go)
- [`plugin_manager/packages.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/plugin_manager/packages.go)
- [`service/install_plugin.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/service/install_plugin.go)
- [`tasks/install_plugin.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/tasks/install_plugin.go)

**源码事实：**
1. 上传 `.difypkg` 后先受包大小限制、解析 Plugin Unique Identifier 和 Manifest；`PreparePackage` 验证 Manifest/资源与包身份。
2. `ForceVerifyingSignature || verifySignature` 才会在相应路径强制拒绝未被验证的包。上游的 `.env.example` 设置 `FORCE_VERIFYING_SIGNATURE=true`，但这是**可配置门槛**；不能因工具有“签名功能”就断言所有实际部署无条件拒绝非签名包。第三方公钥也可纳入校验信任根。
3. `PreparedPackage` 将内存中的包、Asset、校验状态与 `PersistPackage` 区分；保存失败有补偿回滚，但不同存储/数据库间仍不是天然全局事务。
4. `models.Plugin` 的 `PluginUniqueIdentifier` 包含版本和校验和，并被数据库唯一约束保障幂等；安装过程区分已存在运行时与尚未安装的租户登记。
5. `InstallMultiplePluginsToTenant` 创建后台任务；与 HTTP 断开解耦，设置安装超时。`ProcessInstallJob` 依据 Info/Error/Done 写入用户可见状态，运行时安装成功之后才写租户安装记录。

**Nerelan 可以抄的生命周期语义：**

`DISCOVERED -> PACKAGE_VERIFIED -> HOST_APPROVED -> INSTALLED -> ACTIVATING -> READY -> DRAINING -> REMOVED`。

每阶段存冻结 `content_digest + policy_digest + run_context + previous_version_ref`；失败和取消不能静默吞掉已完成阶段。**但不必为此再建 Redis/SQL 安装作业服务**：复用当前 TaskStore 或受控变更记录，只有真实插件执行功能批准时才新增必要状态。

**关键反证：** “有可信签名”只证明某把信任公钥签署了包内容，不证明插件不会执行危险系统调用。签名/版本一致性、Owner 授权、OS 沙箱是三个不同检查。

## 4. 模块 C：Local Plugin Runtime 与信任边界（P0 安全评估）

源码：
- [`local_runtime/subprocess.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/subprocess.go)
- [`local_runtime/instance.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/instance.go)
- [`local_runtime/setup_python_environment.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/setup_python_environment.go)

具体实现：
- Python 插件以 `exec.Command(venvPython, "-m", entrypoint)` 启动，工作目录是插件的独立路径，stdin/stdout/stderr 均为管道。
- `BuildPluginCommandEnv` 从明确白名单取进程环境（PATH/HOME/locale/TMP/SSL/HTTP_PROXY 等）并附加运行标志；不直接继承 Daemon 的 `DB_PASSWORD`、`SERVER_KEY` 等，显著降低宿主 secret 意外传给插件的概率。
- Python 依赖由 uv/Python 环境初始化，存在包安装供应链、时间与磁盘开销。`requirements`/`uv.lock` 的处理与镜像配置都会影响复现性；不能把“相同 Manifest”自动视作“相同依赖环境”。
- `PluginInstance` 以首个 heartbeat 作为开始就绪的信号，并在标准输出管道终止后执行 kill/reap，防止普通僵尸子进程累积。`PluginInstance.Stop()` 本身发出 IO 关闭，不等于远端第三方 API 副作用撤销。

**风险界限**：子进程与虚拟环境≠OS 安全隔离。源码这里没有证明 AppArmor/seccomp、Windows ACL、容器 user namespace、网络拒绝、主机敏感路径或 PID/CPU/磁盘强限制。`HTTP_PROXY/NO_PROXY` 等变量仍可进入插件，网络能力必须另外治理。运行不可信插件属 Nerelan R3，必须经 [#299](https://github.com/dddd2024/Nerelan/issues/299) 的成熟 Sandbox 后端及 Owner 授权；**绝不为了实现插件而将 Nerelan Trusted Host 直接运行成通用任意 Python 插件宿主**。

## 5. 模块 D：标准流 Session、多实例与失败传播（P1/P2）

源码：
- [`local_runtime/io.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/io.go)
- [`local_runtime/control.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/control.go)
- [`local_runtime/load_balancing.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/local_runtime/load_balancing.go)
- [`core/io_tunnel/generic.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/io_tunnel/generic.go)
- [`session_manager/session.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/session_manager/session.go)

真实机制：
- `sessionId -> instance` 映射绑定本次 stdio 调用，监听插件的 Streaming/End/Error 消息；避免一个实例内并发流互相串话。
- `pickLowestLoadInstance()` 实际注释明确是**round robin**，跳过已知停止的实例；名字暗示的“最低负载最优”并未实现，不能直接拿这个函数证明效率。
- `Write` 遇 dead pipe 会停止/淘汰实例、移除 Session 映射并唤醒调度；Runtime 周期检查并补充缺少的实例。
- `Session` 包含 TenantID/UserID/PluginUniqueIdentifier/InvokeFrom/Action，Redis TTL 默认为 30 分钟，供短暂会话关联；它**不是** Nerelan 多小时/多天 Task 的持久可靠真相。
- 流错误和挂起、HTTP 调用重试并不证明外部有副作用动作“恰好一次”。尤其模型/工具插件发出的请求可能已被后端接受，却因 pipe 断开没有回执。

**Nerelan 应借鉴：** 使用 `plugin_instance_id` + `activation_generation` + `session_id` + `tool_invocation_id` + `attempt_id` 形成可追溯链，保留各次 Plugin 响应与完成/未知状态；若插件实例重启，只有受信任的 Host 判断外部操作可否安全重试。不要给第三方插件一套新的 TaskStore。

## 6. 模块 E：最需要防范的“插件反向调用宿主”（P0/P1）

源码：
- [`backwards_invocation/task.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/io_tunnel/backwards_invocation/task.go)
- [`io_tunnel/generic.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/io_tunnel/generic.go)
- [`plugin_declaration.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/pkg/entities/plugin_entities/plugin_declaration.go)
- [`dify_invocation/invcation.go`](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/internal/core/dify_invocation/invcation.go)

Dify 插件不仅接收调用，还可以向 Daemon 发 `INVOKE` 消息，请 Dify 主应用提供：
- LLM、结构化输出、Embedding、Rerank、TTS/STT；
- Tool、App、Node、Storage/File 等服务。

上游 `InvokeDify` 先拒绝被禁止的调用来源，再用 Manifest Permission 做调用类型许可检查，随后异步 Dispatch；具体类型通过 `permissionMapping` 映射。例如 `AllowInvokeLLM()` 校验 `model.enabled && model.llm`。

**一个需要二次核查的源码细节：** `INVOKE_TYPE_UPLOAD_FILE` 在该文件中的映射返回 `true`，而其它 Storage 能力可能需要声明权限。不能单凭这一段断言有安全漏洞，因为其它路径可能有边界检查；但足以证明“仅看 Manifest 权限字段不等于所有下游操作都已经被限制”。

对于 Nerelan，反向能力应统一走现有 Host：
- 请求包含 `task_id / attempt_id / pack_digest / operation / budget_reservation / call_id`；
- **Host** 检查用户实际授权、是否受当前 Window/Token/现金门槛覆盖、是否有可用绑定；
- LLM 请求只能进入受管的 Nerelan/Magpie 模型路由，不能让插件自建代理键或直接读取所有用户账号；
- 第三方工具请求受现有 MCP/Connector Policy 和相同的授权、收据、幂等性门禁；
- 使用 Magpie 请求级身份及真实用量记录做结算，迟到/缺失为 UNKNOWN，不因插件报告“成功”而推断成本为零；
- 拒绝插件自行提高权限，不能用自报 Manifest Permission 覆盖宿主政策。

这里是比“插件能安装”更值得前置的安全与经济性验证，也是 Nerelan 与一般 Plugin Daemon 必须保持的架构差异。

## 7. 部署、运行经济性与复用可行性

[上游 README](https://github.com/langgenius/dify-plugin-daemon/blob/1fa10988ce3fb69af48538d3a6d405fcd4769afc/README.md) 明确：
- Daemon 社区版当前支持 Linux/macOS，Windows 适配未完善；
- 依赖 Go 服务、Python >=3.11、uv、数据库、Redis、包存储、运行目录；
- Local Runtime 与 Serverless/Debug 协议、升级、依赖编译和成本不同；
- 社区版 Kubernetes 多副本横向扩展存在明确限制。

这和 Nerelan 当前 **Windows 本地优先 + 现有 Executor/Magpie 资源**不匹配。若在未来成熟的 Linux Worker/Devbox 上有真正的“运行不可信 Python Pack”需求，才可在 Sandbox 具备足够隔离且符合 Owner 授权时，以独立服务的方式考虑 Adapter。不能为了插件目录或更好看的商店 UI 引入整个服务。

**即使能运行，成本还包括**：安装环境 CPU/磁盘/网络、常驻实例、定期 heartbeat、日志与 Stream、升级失败、重启与恢复、模型反向请求、审批/人工介入、独立验收。最终只能以被验收 Task 的资源/恢复总成本衡量收益。

## 8. Developer × 用户价值矩阵

| 用户实际需要 | 最小可行产品行为 | 避免的重复建设 |
|---|---|---|
| “这个 Pack 到底能干什么？” | 发现 Tool/Agent Profile/Workflow/Verifier 要求，显示真实环境可用性 | 不另建 SDK Marketplace |
| “它会用我哪个模型/账号？” | 展示经批准的 Binding、额度与应用连接；不能私自 fallback | 不复制 Magpie 账号池 |
| “安装成功是否真的能工作？” | `Package Valid/Enabled/Runtime Ready` 三段状态，显示缺失依赖 | 不另建 Dify 安装控制面 |
| “它为什么不能调用工具？” | 宿主的权限拒绝原因、调用 ID、原始审批目标 | 不让第三方 Hook 覆盖 Host |
| “插件崩了，任务会不会重复？” | 完整调用收据，UNKNOWN/部分完成与重试可见 | 不替换 TaskStore |
| “插件会偷看我的凭据吗？” | 显示真实隔离级别；未知隔离时不激活代码插件 | 不声称虚拟环境即安全 |

## 9. 与已有 Nerelan 工作的复用优先级

| 范围 | 具体结论 | 优先度 | 对应 Issue |
|---|---|---|---|
| Manifest 能力与运行前可解释诊断 | `BORROW_PATTERN_ONLY`：补条件/权限/版本，不让 Metadata 触发任意执行 | **P1** | [#253](https://github.com/dddd2024/Nerelan/issues/253), #303 |
| Package 身份/签名/阶段/回滚与 Activation Generation | `BORROW_PATTERN_ONLY`：先读状态，隔离版本；不引入另一数据库 | **P1** | #253, [#789](https://github.com/dddd2024/Nerelan/issues/789) |
| Plugin → Host 反向 LLM/Tool 调用 | `REQUIRE_HOST_GATE`：不可绕过的模型额度、权限与结果归因 | **P0** | #789, [#790](https://github.com/dddd2024/Nerelan/issues/790), Magpie |
| Python 子进程启动/心跳/数据流 | `BORROW_PROTOCOL`：保证跨 Agent/Plugin Session 与调用关联，错误保持 UNKNOWN | P2 | #790, #253 |
| 真实沙箱 | `REQUIRE_EXTERNAL_MATURE_RUNTIME`：Python 进程不是安全沙箱 | **P0** | [#299](https://github.com/dddd2024/Nerelan/issues/299) |
| 移植 Dify Daemon + DB + Redis + Debug TCP + Serverless | `REJECT_DEFAULT`：对当前单机/Windows 过重 | REJECT | [#361](https://github.com/dddd2024/Nerelan/issues/361) |
| 让 Dify 管理全部模型/账号/主工作流 | `REJECT`：Magpie、TaskStore 是权威 | REJECT | #253, #790 |

## 10. 最小可证伪实验（本轮未执行）

1. **签名/包身份（provider-free）：** 相同版本不同校验和、错误签名、超大解压后包、重复安装、半途失败；验收：没有明确批准的代码不得激活，失败可回滚且不会把“已上传”变成“已运行”。
2. **环境白名单（假子进程）：** 在宿主设置 `DB_PASSWORD`、`SERVER_KEY`、`GH_TOKEN`、模型提供商模拟密钥；Pass：插件看不到这些变量。验证仅白名单也不能阻止插件读取磁盘等，强沙箱缺失必须阻止不可信插件启用。
3. **反向权限 + Magpie 账单（fake Host）：** 无 LLM 权限、低额度、Owner 暂停、错误 Binding、重复 request_id；Pass：拒绝未授权调用，不产生遗漏或重复扣费，缺收据为 UNKNOWN。
4. **崩溃/重启（fake Runtime）：** 插件收到 Tool 调用、发出外部副作用后 pipe 断开，重启并再次请求；Pass：状态保留“可能已发生”，不无条件重放，需确认收据。
5. **版本升级与在途调用：** v1/v2 Manifest 工具集合和权限不同；Pass：在途任务按准入的 activation generation 结束或被显式撤销，不能混用新旧权限。
6. **成本/UX 基准：** 只有 Pack Metadata vs 外部运行时；测加载开销、Task 成功率、模型 token、插件进程资源、安装/恢复失败、用户需要的批准次数。失败条件是额外运维/配置成本超过有效收益。

这些都是建议的 Provider-free Fixture/设计审查；**本轮没有运行任何一项测试**。若要执行未受信任的第三方代码，须遵守 Nerelan R3 Owner 授权，不得从本 Issue 推导执行权限。

## 11. 结论

**SELECTIVE_DESIGN_REUSE**：Dify Plugin Daemon 证明成熟 Plugin 生态需要可校验包、明确启用状态、版本化执行契约、后台安装错误处理及流式调用关联；但它同时表明“进程+签名”不等于真实沙箱，插件反向调用工具和模型会暴露新的权限及资源账单边界。

Nerelan **保留自己的 Pack Manifest、Host Policy、TaskStore、Magpie 账号池和独立验收**。优先把源码观察转为现有 #253/#789/#790/#299 的回归测试与可解释用户状态，不移植整套 Daemon。

**正式研究状态**：上游静态代码已阅读、冻结来源；本 Draft PR 在 exact-head CI 与独立评审之前不可合并。研究记录本身不允许安装、实际调用或发布。
