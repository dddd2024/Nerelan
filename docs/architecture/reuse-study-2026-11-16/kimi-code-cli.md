# Kimi Code CLI — 深度源码静态审查（2026-11-16）

**Canonical research Issue:** [#1587](https://github.com/dddd2024/Nerelan/issues/1587) · **Research Hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)

**Evidence / authority:** `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / NOT_IMPLEMENTED / DOCS_ONLY`. This is *not* an R2/R3 implementation grant. No model or plugin code was executed, no new executable was installed, and neither CI nor independent review has been represented as passed.

# Kimi Code CLI 深度源码调研：Agent Harness、动态 Tool、Plugin/Skill 与持久副作用边界

> 2026-11-16 · `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY`  
> **唯一上游项目**：[MoonshotAI/kimi-code](https://github.com/MoonshotAI/kimi-code) [`6819b036cd00f8dcd779e0b70105b93a947340c8`](https://github.com/MoonshotAI/kimi-code/commit/6819b036cd00f8dcd779e0b70105b93a947340c8) (MIT)。本轮不使用旧 `MoonshotAI/kimi-cli` 的历史代码代替现行实现：旧仓库现在标记 Archived/Legacy，README 指向 `kimi-code`。  
> **Nerelan 对照**：[`main@e7ed129d143f5839a4d16dd220adf3afdf88d3ea`](https://github.com/dddd2024/Nerelan/commit/e7ed129d143f5839a4d16dd220adf3afdf88d3ea)。本研究非运行验收，原始实测数据为 **NONE**。

## 0 查重证据（research ≠ product owner）

检查：总研究台账 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 正文、后续 3 条正式专项评论（SWE-ReX #1578、Google ADK #1581、ACP SDK #1585）、历史 19 项归档索引（Cline、Pi、Letta、Plandex、OpenClaw、Hermes 和其他运行时）；GitHub issues 搜索 `"Kimi CLI"`、`"kimi-cli"`、`"MoonshotAI/kimi-cli"`、`"kimi-code"`，以及研究 Issue 列表。没有找到 **现行 `MoonshotAI/kimi-code` 的同模块、同版本独立源码专项**。部分 GitHub Issue 提及 Kimi 模型（如 #1507/#1533），不是 Kimi Code Harness 代码评估；ACP SDK #1585 是协议库，不是本次执行器。邻近已有实施 Owner：[#1527](https://github.com/dddd2024/Nerelan/issues/1527) 多执行器 bake-off、[#296](https://github.com/dddd2024/Nerelan/issues/296) Context、[#253](https://github.com/dddd2024/Nerelan/issues/253) Pack、[#789](https://github.com/dddd2024/Nerelan/issues/789) Hooks、[#790](https://github.com/dddd2024/Nerelan/issues/790) MCP、[#1530](https://github.com/dddd2024/Nerelan/issues/1530) 模型拒绝/额度、[#1531](https://github.com/dddd2024/Nerelan/issues/1531) 请求成本归因、[#1546](https://github.com/dddd2024/Nerelan/issues/1546) 持久恢复、[#299](https://github.com/dddd2024/Nerelan/issues/299) 沙箱、[#1575](https://github.com/dddd2024/Nerelan/issues/1575) 重构。**不创建重复实施 Issue**。

## 1 冻结源码事实与具体借鉴

### A. 新的多执行器候选，不是同名模型

[`core/llm/builtin/provider/endpoints.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/core/src/llm/builtin/provider/endpoints.ts) 暴露 `OPENAI_API_KEY` / `OPENAI_BASE_URL`、Anthropic、Google 等端点配置；[`README.md`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/README.md) 列出并行子 Agent、插件/Skills、MCP、ACP；[`cli/sub/acp.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/apps/kimi-code/src/cli/sub/acp.ts) 明确 `kimi acp` 提供 stdio ACP server，并拒绝与 ACP 客户端环境冲突的 `--environment` 配置。[`acp-server/src/server.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/acp-server/src/server.ts) 具有 new/load/resume/cancel/plan/permission 交互。

**决策：`DIRECT_REUSE_CANDIDATE / P1 TEST_ONLY`**。可以在 #1527 原生 OpenCode/Codex/Claude Code 对照组外增加 Kimi Code *候选*，优先用冻结版本+模拟 Agent/无真实模型 preflight 确认 Windows、headless/ACP、事件/使用量、Magpie OpenAI 协议路径、工作区、信号、资源关闭。**上游存在 OPENAI_BASE_URL 不等于所有 Magpie 模型均能运行，也不证明质量/成本优势**。安装/运行新的第三方可执行文件须独立满足仓库 R3 门槛；本次不安装/不联网调模型。

### B. 按需暴露 Tool Schema — 比全量插件注入更有差异

[`agent/toolSelect/toolSelectService.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/agent/toolSelect/toolSelectService.ts) 管理已登记/可加载/已加载工具，并过滤 `toolPolicy.isToolDenied`、`isToolActive`、过期/未知名字；[`agent/tools/select-tools/selectToolsTool.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/agent/tools/select-tools/selectToolsTool.ts) 仅对确切已公布的工具名称加载 Schema，将动态 Schema 加进模型上下文，并对重复猜测进行终止提示；[上游测试](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/test/agent/toolSelect/toolSelectService.test.ts) 包含 defer、MCP 和拒绝场景。

**决策：`BORROW_PATTERN / P1`**，让 Nerelan 先展示最小工具集、按任务角色和 Owner 授权的白名单再逐步披露 Schema，且保留工具版本/权限/目录新鲜度。当工具更新、被撤销、清单失效时不要相信旧上下文已注入的工具定义。作用假设是**减少 token/context 开销**；必须由 #296/#253/#790 模拟及真实任务对照证明；不引入第二个工具执行/权限引擎。

### C. Plugin/Skill 包装与供应链约束 — 有用但不直接开 Marketplace

[`app/plugin/manifest.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/app/plugin/manifest.ts) 解析 root `kimi.plugin.json` 和 `.kimi-plugin/plugin.json`，对 skills、agents、MCP、hooks、commands、systemPrompt 做验证/诊断；拒绝或提示不支持的运行字段，检查相对路径/realpath 不可越根，约束系统提示最大 32KiB。[测试](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/test/app/plugin/manifest.test.ts) 覆盖 traversal、symlink、大小限制。[Manager](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/app/plugin/manager.ts) 把 GitHub ref 解析到具体 SHA（有条件），ZIP install 可用 `expectedSha256` + expectedPluginId；[packageCache.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/app/plugin/packageCache.ts) 按 SHA-256 校验缓存/下载。[`skillTool.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/features/skill/tools/skillTool.ts) 仅允许 model-invokable inline skill、限制嵌套深度、截断模型可见内容并记录来源/activationID。

**决策：`BORROW_PATTERN / P1`**：Pack 明确 `manifest→provenance→preflight→capability approval→activate`，Skill metadata progressive disclosure，严格路径/大小/来源 ID；用户可读的“不支持该能力”诊断。**拒绝**将安装一个插件或其原始 systemPrompt 等同于已授权执行脚本/外部 MCP；不移植其整个 TS Marketplace/PluginManager 到 Nerelan，也不允许 GitHub HEAD 无固定版本的生产自动安装。

### D. 并行 Agent / 额度退避 — 只取其反馈信号

[`features/swarm/session/agentRunBatch.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/features/swarm/session/agentRunBatch.ts) `AgentRunBatch` 对 provider rate limit 使用重排队、3s 起点的指数 backoff、动态容量 shrink/recovery、取消；[`sessionSwarmService.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/features/swarm/session/sessionSwarmService.ts) 将子 Agent 与 callerAgentId 绑定，拒绝非所属子代理重用。上游为 **进程内批队列**，未证明跨崩溃/外部副作用持久性。

**决策：`ALREADY_REUSED_DIRECTION + BORROW_PATTERN / P2`**：需要“为何队列降速、预计何时恢复、哪个模型/账户触发限额”的可解释状态，归 #1530/#1533/#1527；不要另建与 Owner continuous run / Magpie account-level hold 竞争的第二持久队列。没有真实请求日志前不得把指数重试当作健康切换。

### E. Context/Memory: 只借鉴状态投影与 Skill 注入

[`contextMemory/compactionHandoff.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/agent/contextMemory/compactionHandoff.ts) 明确压缩摘要、头尾用户输入保留、遗漏标注、continuation marker；[`fullCompaction/fullCompactionService.ts`](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/agent/fullCompaction/fullCompactionService.ts) 响应 overflow 降低压缩窗口、限制重复尝试，并记录实际 token usage。与 Nerelan [`context_builder.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/context_builder.py) 和 [`context_optimization.py`](https://github.com/dddd2024/Nerelan/blob/e7ed129d143f5839a4d16dd220adf3afdf88d3ea/reverse_agent/platform_v1/context_optimization.py) 的 *durable truth→只读投影* 目标一致。

**决策：`ALREADY_REUSED + BORROW_PATTERN / P1`**：借鉴用户输入保留预算与显式遗漏/截断原因，保护多 Agent handoff 中的约束；不把外部摘要、systemPrompt 或 Agent 记忆变成权限源。不引入第二套长期 Memory Store。

## 2 必须拒绝 / 需要反例验证的源码风险（静态推断，未实测漏洞）

1. **Session Lock fail-open**：[sessionLockService.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/persistence/backends/node-fs/sessionLockService.ts) 的 `publish()` 在 claim 异常时记录 “session lock unavailable; continuing without lock” 然后返回 token，且环境变量可关闭锁。并非适合 Nerelan 的跨重启唯一 owner/lease fencing。**NO DIRECT REUSE**；模拟两进程抢锁、I/O 失败与 kill/restart，验证 Nerelan 独立任务 claim 始终 fail-closed。
2. **MCP 重连可能重复副作用**：[agent/mcp/tools/mcp.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/agent/mcp/tools/mcp.ts) 的 `retryAfterReconnect` 遇到可恢复 transport failure 可对同一 `callTool` 用现存或新 client 再发送，未看到 operation receipt/idempotency-key 的强制校验。**这是无法证明 exactly-once 的结构性风险，不等于已观察到攻击成功**。Nerelan 应基于 operation ID、服务端收据或 `UNKNOWN/LOST` 等待核销，不得在部分副作用后无脑重试。
3. **ACP replay 不是持久证据**：[acp-server/src/replay.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/acp-server/src/replay.ts) 对压缩后丢失原调用的工具结果直接跳过，避免 UI 孤儿卡片；这个投影策略不能用来推断该工具“没执行”。Nerelan UI 可以不显示没有配对的卡片，但 durable TaskStore/evidence 不能丢失原始结果；与上轮 Google ADK #1581 call-response-pair 保全研究交叉核验。
4. **Hook 没有 Nerelan 授权**：[externalHooks/internal/runHook.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/features/externalHooks/internal/runHook.ts) 和 [matchHooks.ts](https://github.com/MoonshotAI/kimi-code/blob/6819b036cd00f8dcd779e0b70105b93a947340c8/packages/agent-core-v2/src/features/externalHooks/internal/matchHooks.ts) 提供外部命令 spawn、timeout/kill、阻断结果，匹配时并发执行多 hook。不能让插件 hook 的“通过”覆写宿主安全政策；hook 失败或超时如何 fail closed 必须由 Nerelan 风险级别决定。
5. **插件哈希只证明内容一致，不证明安全性或许可合规**。安装包/嵌套内容需严格审查、能力裁剪和沙箱；真实执行需 R3 授权。

## 3 模块优先级、唯一实施归属和可证伪标准

| Nerelan 部分 | 分类 | 建议 | Owner |
|---|---|---|---|
| Agent / Executor | DIRECT_REUSE_CANDIDATE | Kimi Code CLI ACP / non-interactive headless / OpenAI-compatible Magpie preflight，成功后同任务 pair 成本对照 | #1527 |
| Tool / Plugin / Pack | BORROW_PATTERN | 工具清单/Schema 渐进披露；包/Skill 来源、SHA、路径和字节限制；用户可读被拒绝原因 | #253 #789 #790 #296 |
| Memory / Context | ALREADY_REUSED + BORROW_PATTERN | 保留摘要/原始证据分界；显式 omitted events 和用户输入预算 | #296 |
| Swarm/Concurrency | BORROW_PATTERN / P2 | Provider refusal/latency 反馈，仅供现有调度，不转移账户配额职责 | #1530 #1533 #1527 |
| Security/Resume | REJECT specific design | lock failure-open、无收据 MCP retry、ACP 历史投影当成执行真相 | #1546 #299 #790 |
| Cost/Routing | NO DIRECT REUSE | 继续由 Magpie 与 Nerelan 现有 #1267/#1531 归因；只按验收通过与总成本优化 | #1267 #1531 #1342 |
| UX | BORROW_PATTERN | 用户视角显示工具为何不可用、Agent 子任务被限流/等待、被跳过的历史/进度 | #1561 |

**Provider-free experiments (NOT RUN)**：
- E1：使用已授权的固定官方发行包/源，模拟 Kimi Code CLI ACP 和无模型调用，测试 Windows/stdio、头无协议消息、会话中断、超时、工作区只读/写权限，以及 `OPENAI_BASE_URL` 只指向 fake Magpie endpoint。只要模型/ACP/host 权限不兼容，**NO-GO**。
- E2：同一 Agent 主任务、同等工具权限，启用/禁用动态 Schema，固定 3 类长上下文用例，核对 schema tokens、缓存命中、工具选择失败率、验收质量。若 token 节省没有抵消额外选择调用和失败成本，**NO-GO**。
- E3：第三方 ZIP/Plugin manifest 的路径逃逸、symlink、超限提示、版本变化、过时 hash、缺失权限、hook timeout；无 Owner 批准不得获得 host secret、shell 或网络。
- E4：MCP 副作用已发生但首次响应丢失 + session lock I/O 失败 + 两进程 + 崩溃恢复；所有不可确认副作用保持 UNKNOWN/LOST/等待核销，绝不隐式再执行。
- E5：在真实 authorized bake-off 中，将相同 Task/Model 分配到 OpenCode 和 Kimi Code，保持 acceptance/reviewer/仓库基线一致；衡量 pass rate、壁钟耗时、context/cache/token、Magpie 实际请求、用户订阅占用和返工成本，最终以**每个独立验收成功任务的总成本**决策，而非 token 单价。
- E6：多子 Agent 同时触发 429/403/credits，模拟外部恢复时间和 account pool；验证没有错把永久失败当限流、没有重复 spending/side-effect，以及仍符合 continuous-run concurrency。

## 4 最终裁定

`SELECTIVE_BORROW_PATTERN + CONDITIONAL_EXECUTOR_BAKEOFF`，优先级 **P1**（可复用设计）；安全边界 **P0 prerequisite**。最值得 Nerelan 学的是 **动态 Tool Schema 的可解释渐进加载 + 插件来源证据 + 作为独立 Harness 的经济性对照**；拒绝其 session lock fail-open 与 MCP retry 作为持久任务和副作用保障。

本 Issue 仅记录静态源码证据，未下载/运行 Kimi Code、未调用 Magpie/provider、未安装插件、未执行测试、未创建新的 implementation Owner。文档在 R1 Draft PR 走 AGENTS.md 的 exact-head gate + 独立评审之前不得声称已合入 main。

---

## Provenance notes

- Upstream active repository: `MoonshotAI/kimi-code@6819b036cd00f8dcd779e0b70105b93a947340c8`. The old `MoonshotAI/kimi-cli` is archived and was not used as a substitute.
- Nerelan snapshot: `main@e7ed129d143f5839a4d16dd220adf3afdf88d3ea`.
- Source inspection and proposed tests are not runtime evidence; hypotheses require fresh provider-free fixtures before a paid bake-off.
- Use existing implementation owners #1527, #296, #253, #789, #790, #1546, #299. No second agent loop, MCP runtime, gateway, TaskStore or plugin manager is authorized by this audit.
- Canonical research indexing is the #1576 dated comment while pending research-index Draft PRs reconcile; do not add a competing permanent index in this branch.
