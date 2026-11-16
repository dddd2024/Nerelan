# 其他对话中的执行器与框架研究归档（2026-11-16）

> **研究总入口：** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)；[历史专项目录](INDEX.md)。本页专门收录**其他对话已经逐项目讨论、但未有六份正式 Issue+PR 的项目**。  
> **证据等级：** 旧聊天结论由历史上下文恢复；已核对历史 SHA 的 README 或具体源码的项目标为 `SOURCE_REF_VALIDATED`，有的仅 `CHAT_NOTE_ONLY`。**恢复旧讨论不是执行新测试**；下面所有项目均未在本次归档运行、安装、付费请求或改动产品代码。  
> **原始聊天链接限制：** 2026-11-16 的对话标题/片段可恢复，但原聊天的稳定 URL、全部正文、逐轮源码浏览日志不可直接导出。此文标注其范围，不能把它们虚构成原始审查记录/独立 GitHub PR。  
> **横向研究**：[11/15 A–E](../../reuse-study-2026-11-15/README.md)。请先阅读它，避免重复把“横向提过”当全新模块。

## 1. 项目证据台账

| 项目 | 历史会话记录的源码版本 | GitHub 本次核对 | 重点模块 | 归属/边界 |
|---|---|---|---|---|
| **OpenCode** | `anomalyco/opencode@367d24b7`，历史还讨论 v2.3.0 与 v1→v2 | **SOURCE_REF_VALIDATED**：[README](https://github.com/anomalyco/opencode/blob/367d24b7/README.md) | Agent/子代理、插件/MCP、Events/Session、权限、CLI 与 Server 事件差异 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#1530](https://github.com/dddd2024/Nerelan/issues/1530) |
| **Codex CLI/App Server** | `openai/codex@630c0d75` | **SOURCE_REF_VALIDATED**：[README](https://github.com/openai/codex/blob/630c0d75/README.md) | App Server、Python SDK、ExternalMessage、审批、环境继承 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#303](https://github.com/dddd2024/Nerelan/issues/303) |
| **OpenHands Software Agent SDK** | `OpenHands/software-agent-sdk@1d4c0249` | **SOURCE_REF_VALIDATED**：[README](https://github.com/OpenHands/software-agent-sdk/blob/1d4c0249/README.md) | Agent Server 事件、RemoteConversation、DockerWorkspace、风险/评测 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#299](https://github.com/dddd2024/Nerelan/issues/299) |
| **Gemini CLI** | `google-gemini/gemini-cli@4ed06ed0`，v0.68.0 | **SOURCE_REF_VALIDATED**：[README](https://github.com/google-gemini/gemini-cli/blob/4ed06ed0/README.md) | Headless JSONL、ACP、Extensions/MCP、Session/Checkpoint、Plan/YOLO | [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#790](https://github.com/dddd2024/Nerelan/issues/790) |
| **Goose** | `aaif-goose/goose@bf6e1df` / 历史另一轮 `0bf8b624` | **SOURCE_REF_VALIDATED**：[新版 README](https://github.com/aaif-goose/goose/blob/bf6e1df/README.md)；原 `block/goose` 已迁移 | Extension Lease、MCP Tool Schema 快照、Recipe、Session Bound / owns-tool-loop | #790、#253 |
| **Continue** | `continuedev/continue@5522c6f` | **SOURCE_REF_VALIDATED**：[README](https://github.com/continuedev/continue/blob/5522c6f/README.md) | Context Providers、Index、Repo Map、IDE/CLI、权限 | [#296](https://github.com/dddd2024/Nerelan/issues/296)、#1527 |
| **Aider** | `Aider-AI/aider@5dc9490`，v0.86.0 | **SOURCE_REF_VALIDATED**：[README](https://github.com/Aider-AI/aider/blob/5dc9490/README.md) | Tree-sitter/PageRank Repo Map、Architect+Editor、编辑格式、Git/成本 | #296、#1527 |
| **mini-SWE-agent** | `SWE-agent/mini-swe-agent@04d809c`，v2.4.6 | **SOURCE_REF_VALIDATED**：[README](https://github.com/SWE-agent/mini-swe-agent/blob/04d809c/README.md) | 极简 Bash Harness/可控工具循环、执行经济性基线 | #1527、#299 |
| **Qwen Code** | `QwenLM/qwen-code@2366c440`，v0.27.4 | **SOURCE_REF_VALIDATED**：[README](https://github.com/QwenLM/qwen-code/blob/2366c440/README.md) | Python SDK、ACP、Teams/Arena/Goals、MCP/Skills/Hooks | #1527、#789、#790 |
| **Deep Agents** | `langchain-ai/deepagents@eab9304` | **SOURCE_REF_VALIDATED**：[README](https://github.com/langchain-ai/deepagents/blob/eab9304/README.md) | Middleware、Filesystem/Backend、Skills Tool Discovery、Rubric | #253、#296 |
| **Pydantic AI** | `pydantic/pydantic-ai@bc598a1` | **SOURCE_REF_VALIDATED**：[README](https://github.com/pydantic/pydantic-ai/blob/bc598a1/README.md) | Pydantic Evals、WindowsWorkspace、Capabilities、DBOS Durability | [#1267](https://github.com/dddd2024/Nerelan/issues/1267)、#1527、#1546 |
| **FastMCP** | `PrefectHQ/fastmcp@ffc65c7`（历史记录还提 4.1.8 / 4.2.0 alpha） | **SOURCE_REF_VALIDATED**：[README](https://github.com/PrefectHQ/fastmcp/blob/ffc65c7/README.md) | ClientGroup、Tool Search/Provider、OAuth 与 STDIO 安全 | [#790](https://github.com/dddd2024/Nerelan/issues/790) |
| **Orchestrator.inc** | `OrchestratorInc/agent-orchestrator@ad93b42` | **SOURCE_REF_VALIDATED**：[README](https://github.com/OrchestratorInc/agent-orchestrator/blob/ad93b42/README.md) | 多 Harness Adapter、会话事件覆盖、PR Head SHA 幂等、Worktree | #1527、[#1508](https://github.com/dddd2024/Nerelan/issues/1508) |
| **Roo Code** | 历史研究和 Cline 一起谈；独立源码 SHA 未找回 | **CHAT_NOTE_ONLY**：参见 [Cline/Roo 档案](cline-roo.md) | 插件/执行/Hook 的相关比较 | 不应把 Cline 源码事实自动算作 Roo 已核对 |

注：这些短 SHA 是旧对话提到的历史状态，且多数 README 在该 SHA 上已实际读到；**并不意味着所有旧对话提及的模块/函数都已在此次重新逐文件复核**。Qwen 的 `core_tools=[]`、`allowed_tools` 等权限解释属于旧对话观察，随版本可能改变。

## 2. 值得保留的历史研究结论（按模块）

### Agent / 执行器适配（OpenCode、Codex、OpenHands SDK、Gemini CLI、Goose、mini-SWE、Qwen、Orchestrator.inc）

- **OpenCode**：旧对话实际比对 v1→v2 Agent/API/Events、原生子代理、插件/MCP 与工具进度。Nerelan 应优先读原生 Server/SDK Events 避免 CLI 隐藏重试，不应为此复制 Agent Loop。反例：API Version Change，旧 `session.status` 事件/路径可能变化，升级必须做契约测试。
- **Codex**：Python SDK/App Server 与 `ExternalMessage` 适合把结构化的跨 Agent Artifact/Evidence 交给另一执行器，**但默认审批可能宽松且环境变量继承**；原生 CLI 保留，SDK 按权限验证后选择，不能因为编程接口“方便”就默认扩大文件/网络/Secrets 权限。
- **OpenHands SDK**：[RemoteConversation](https://github.com/OpenHands/software-agent-sdk/blob/1d4c0249/openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py) / DockerWorkspace 给出远程容器/事件式执行适配思路；不复制自有 Agent Server/Task Loop，且不能把潜在 Secrets 持久化的会话字段直接交给 Nerelan 使用。
- **Gemini CLI**：Headless Streaming/ACP 有助于构建通用事件桥。[`docs/cli/headless.md`](https://github.com/google-gemini/gemini-cli/blob/4ed06ed0/docs/cli/headless.md)。旧对话提示 Plan Mode 切换和 YOLO 模式、`.gemini/.env` 环境读取可能影响授权；任何危险模式/密钥必须经过 Host 显式否决测试。
- **Goose**：历史先后两次研究 `main@0bf8b624` 与 `main@bf6e1df`；Extension Lease 固定 MCP 服务/工具列表/Schema 与授权快照；禁用 Extension ≠ 自动撤销已进行的授权调用。Recipe 可当 Pack 工作流的非权威输入。[扩展管理源码](https://github.com/aaif-goose/goose/blob/bf6e1df/crates/goose/src/agents/extension_manager/mod.rs)。不移植 Rust Agent Loop。
- **mini-SWE-agent**：极简 Shell/Bash 工具是 Harness 实验的低开销基线；可与 OpenCode/Pi 的任务成功率、模型消耗、工具数量比较，**不能把它的工具执行当安全沙箱**，也不能据它没有 MCP/复杂 Plugin 就说其性能必然好。
- **Qwen Code**：[Python SDK](https://github.com/QwenLM/qwen-code/blob/2366c440/docs/developers/sdk-python.md) 及 ACP/Teams/Goals 适合试做薄 Executor Adapter；历史研究提醒环境会继承父进程、`allowed_tools` 非一定硬白名单、`core_tools=[]` 不必然关闭全部工具。必须用隔离 Fixture 实测，而不是照抄配置期望值。
- **Orchestrator.inc**：[Adapter 注册表](https://github.com/OrchestratorInc/agent-orchestrator/blob/ad93b42/backend/internal/adapters/registry.go) 与 PR/Review 收据提醒多执行器应共享 Task→Agent→Worktree→PR Head 的关联身份；插件多为仓库编译内置的适配器，不能未经审核称为任意第三方插件市场。受控状态仍由 Nerelan TaskStore 决定。

### 上下文、Repo Map 和 Skills（Continue、Aider、Deep Agents）

- **Continue**：历史审过 `core/context/`、`core/indexing/`、`core/config/`、`extensions/cli/src/`。参见 [RepoMapContextProvider.ts](https://github.com/continuedev/continue/blob/5522c6f/core/context/providers/RepoMapContextProvider.ts)。ContextProvider、索引可在 Task 内按问题选择上下文；数据检索结果是**不可信内容**且不是 Host Policy/完整 Evidence。
- **Aider**：[Repo Map 源码](https://github.com/Aider-AI/aider/blob/5dc9490/aider/repomap.py)：Tree-sitter + 引用 PageRank 思路值得拿来做 Nerelan 上下文对照，Architect/Editor 也可作为编码 Agent 模式基线。Aider 的自动 Commit/Lint、默认不一定执行完整 Test、读取工作目录配置和 `.env`，均不能原样迁入受控发布流程。
- **Deep Agents**：[Skills Middleware](https://github.com/langchain-ai/deepagents/blob/eab9304/libs/deepagents/deepagents/middleware/skills.py)：Middleware、逐层暴露工具/技能、Backend 和 Rubric 可借鉴用于 Planner/Context/Verifier 的接口；不要为此换掉 Nerelan LangGraph/TaskStore/审查/多账户路由，更不能信任未验证的 Skill 自描述。

### Tool/MCP/评测/安全（FastMCP、Pydantic AI）

- **FastMCP**：[ClientGroup](https://github.com/PrefectHQ/fastmcp/blob/ffc65c7/fastmcp_slim/fastmcp/client/group.py) 是管理多个独立 MCP Client 连接的成熟候选；对照 #790 做生命周期、重连、来源签名、Tool 发现的成本/授权测试，避免 Nerelan 自建第二 MCP Client 库。`STDIO` 子进程启动路径和 OAuth Redirect/Token 存储必须被 Host 授权。
- **Pydantic AI**：[WindowsWorkspace](https://github.com/pydantic/pydantic-ai/blob/bc598a1/pydantic_ai_slim/pydantic_ai/capabilities/windows_workspace.py) 的安全属性应与 Windows 运行器独立核验：Workspace ≠ Sandbox。Pydantic Evals 值得作为 #1267/#1527 的可复现实验模型（同任务多模型/执行器与稳定评分）；`Usage` 缓存和输入/输出计费桶需映射成 Nerelan/Magpie 的统一独占 Token 分桶。DBOS Durability 是 #1546 的外部参照，不取代其状态与回执设计。

## 3. 证据缺口与最小补证清单

1. **原聊天来源**：旧对话的标题/短片段可检索，但没有可靠的公开 ChatGPT Conversation URL；未提供时不能制造“历史链接”或编造完整逐行阅读日志。
2. **GitHub 过去是否已有专门研究 PR**：当前 GitHub 标题搜索没有找到以上多数项目专属 research PR。早期对话有时口头表示“已关联旧 Issue/PR”，不能把此表当作确认完成的独立专项。具体 Issue/PR 要求检索到实际文件或评论后再升级证据等级。
3. **代码/许可/执行兼容性**：这里只核对 README/少量源码路径与历史 SHA；深入源码审计、Windows 实跑、插件权限/费用/失效注入、Harness×Model 性价比均 **未在本次归档执行**。
4. **横向已覆盖内容无需重复写成“首次发现”**：OpenCode/Codex/OpenHands/Goose/Gemini/Aider/SWE-agent 在 [11/15 执行器报告](../../reuse-study-2026-11-15/C-runtimes.md) 已有概述；Deep Agents 等在其它报告也可检索。
5. 下一轮深调前先读 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)、本历史目录、Pending 专项 PR，再寻找真正未覆盖的源码模块/新版本；**同一个模块只补证据，不重复启动新专项**。

## 4. 统一决策

所有涉及 Agent/Tool/Provider 的复用应优先利用各 Executor 原生 SDK/Server/ACP/MCP，而不是把不同 Agent 的主循环“通用化”为一套新的 Nerelan Agent Loop。Nerelan 的差异化仍是**统一模型订阅与 API 资源、真实额度、任务拆分与 Harness×Model 路由、保留工作与可恢复执行、独立验收和真实总成本**。这份历史档案只有静态/文献证据，不代表任何改动已通过 R1 Gate、R3 权限或生产测试。
