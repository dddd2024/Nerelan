# AG-UI 1.0 — 多执行器事件一致性与只读前端投影源码专项

**研究 Issue**：[ #1600 ](https://github.com/dddd2024/Nerelan/issues/1600) · **总索引**：[ #1576 ](https://github.com/dddd2024/Nerelan/issues/1576) · 日期：2026-11-16

**证据等级：STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**。没有安装 AG-UI、执行其测试、访问模型或改动运行时。上游源码固定在 ag-ui-protocol/ag-ui@344d21fcc1bc276a1168546ae7c8ccaba96a3545（MIT）。

**Nerelan 对照版本**：初始源码检查 main@57637b338b896f00f966c60a5c67f3e0e9848c4e。生成研究分支前重新读取 main，已前进至 **0509cd6135b9bdcd7e08c94838b5df6dd04b54b3**，本分支从该 SHA 创建。对两个 SHA 的 GitHub compare 显示 10 commits、19 个文件改动，其中 frontend/src/lib/platform-client.ts、frontend/src/hooks/use-platform.ts、reverse_agent/platform_v1/task_service.py 有变更（主要是服务错误响应与查询/分页等），而 frontend/src/components/goal-thread.tsx、frontend/src/lib/goal-thread.ts、frontend/src/components/activity-stream.tsx 仍存在且内容路线不变。新基线还保留 TaskStore -> server read model -> React polling and assistant-ui projection；不能声称无变化的绝对快照。

---

# AG-UI 1.0 源码专项：多 Agent 用户事件协议、流校验、状态投影与宿主权限边界

> 2026-11-16 · STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY
> 单一上游项目：[ag-ui-protocol/ag-ui@344d21fcc1bc276a1168546ae7c8ccaba96a3545](https://github.com/ag-ui-protocol/ag-ui/commit/344d21fcc1bc276a1168546ae7c8ccaba96a3545)（MIT）。对照 [Nerelan main@57637b338b896f00f966c60a5c67f3e0e9848c4e](https://github.com/dddd2024/Nerelan/commit/57637b338b896f00f966c60a5c67f3e0e9848c4e)。源码静态审阅，未运行 SDK / E2E，未开模型调用。

## 0. 选题前查重与独有增量

先检查研究 Hub [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 的原六项及后续八项（#1578 SWE-ReX、#1581 ADK Python、#1585 ACP Python SDK、#1587 Kimi Code、#1590 ToolHive、#1592 Nango、#1594 Browser Use、#1598 Playwright MCP），历史 19 个项目归档、GitHub Issues 检索“AG-UI”、“ag-ui-protocol/ag-ui”与“CopilotKit”（均未出现独立源码专项）、当前 main UI/TaskService 代码；没有发现此项目已做完整的源码专项。本轮是第 15 个独立静态源码专项，非第 15 个已合并或验收的项目。

**独有问题**：ACP #1585 处理 IDE ↔ Agent 协议，MCP #1590/#1598 处理 Agent ↔ Tool；本轮 AG-UI 专门处理 **Agent ↔ 用户界面** 的消息、工具调用显示、子 Agent 归属、运行生命周期、复联与消息正确性。Nerelan 现有 [#280](https://github.com/dddd2024/Nerelan/issues/280) 执行观测、[#448](https://github.com/dddd2024/Nerelan/issues/448) 前端布局、[#375](https://github.com/dddd2024/Nerelan/issues/375) 浏览器端事件投影、[#806](https://github.com/dddd2024/Nerelan/issues/806) Headless API、[#795](https://github.com/dddd2024/Nerelan/issues/795) 运行中 Steering、[#281](https://github.com/dddd2024/Nerelan/issues/281) 状态收敛、[#296](https://github.com/dddd2024/Nerelan/issues/296) 上下文，均已有 Owner，本研究不创建重复实施 Issue，也不替换 TaskStore。

## 1. 固定源码与差异分析

### A. 事件协议 1.0 与最小可移植的前端投影（P1 BORROW_PATTERN）

[README](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/README.md) 和 [Python 事件导出](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/python/ag_ui/core/events.py) 明确 AG-UI 1.0 基于冻结 JSON Schema/类型，包含运行、消息、工具、共享状态、reasoning、activity、subagents、raw/custom 等事件族。客户端只负责在 threadId/runId 下展示事件；MCP 工具调用权、Agent 执行权、Owner 权限不属于该协议。
对照 Nerelan [goal-thread.tsx](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/frontend/src/components/goal-thread.tsx)、[goal-thread.ts](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/frontend/src/lib/goal-thread.ts)、[activity-stream.tsx](https://github.com/dddd2024/Nerelan/blob/57637b338b896f00f966c60a5c67f3e0e9848c4e/frontend/src/components/activity-stream.tsx) 已把 Task/Run 只读 Timeline 投影给 assistant-ui，并已有三档活动密度和可折叠动作。因此不要复制 AG-UI 组件或重建会话数据库；优先研究把不同执行器的 EventEnvelope 投影为统一 UI 的小型纯函数/协议适配器。

### B. 严格事件流验证 + 并发归属（P1 BORROW_TEST_FIXTURES，高优先）

[verify.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/verify/verify.ts) 为 message、toolCall、activity、reasoning 分开保存 opener/owner 映射；子 Agent 归属不得借其他类型的相同 ID 或在关闭后从父 Agent 偷接。STEP 活跃状态按（subagent owner，stepName）区分；run 起止和文本/工具流有严格开闭纪律。
[Conformance 流 golden fixtures](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/spec/1.0/conformance/streams/) 明确：首次事件没有 RUN_STARTED 为 fatal、结束后普通事件 fatal、工具 START/ARGS/END 分片按次序合并、工具子 Agent opener/continuation 不一致为 fatal、状态 patch 无法应用时保留旧状态并报警（不是半应用）。[前端并发 reducer 测试](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/apply/__tests__/default.concurrent.test.ts) 并发消息/工具 ID 在反序结束时仍独立。
**建议 Nerelan：**为 OpenCode、Codex、Claude Code 和后续执行器建立同一组 provider-free EventEnvelope 负例：跨 attempt ID 串流、不同 subagent 复用 tool ID、重复结束、丢失 opener、断线重放、旧 event version。后端输出必须带 TaskId/AttemptId/AgentRunId、事件序号/来源摘要；浏览器仅消费裁剪后的可信投影，绝不能因事件自报 DONE 就将 TaskStore 状态改为已验收。

### C. 校验先于修复：无法理解就降级/隔离（P1 BORROW_PATTERN）

[agent.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/agent/agent.ts) 将线上的兼容性转换、enforceEvents、chunk expansion、verifyEvents、apply 顺序固定，强调 **enforce-before-expand**，避免不合法分片经过转换后被悄悄“修好”。[enforce.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/enforce/enforce.ts) 未识别事件或属性按策略丢弃/警告，已识别但不合法的字段使 run 报错。[limits.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/enforce/limits.ts) 每事件默认上限 1,000,000 entries，并允许 Infinity：这是上游默认值，不是 Nerelan 安全推荐值。
[SSE parser](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/transform/sse.ts) 限制未完成 SSE buffer 10 MiB（注意只对残留缓冲尾而非每个已经完整的事件逐一生效）；[run-error restart test](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/agent/__tests__/agent-run-error-restart.test.ts) 证明 RUN_ERROR 并不必然结束整条流：后续 RUN_STARTED 可开始新 run。**Nerelan 必须将此视为前端事件会话语义，而非允许已失败的 TaskStore Attempt 静默复活**。
建议默认采用更小、分字段/分消息/分 run 的本地主机预算和有限输出，按需存 Raw 事件摘要而非全量敏感内容；超过限额在 UI 明确显示“内容已截断/已拒绝”，不能丢事件却继续显示正常完成。

### D. 并发 Tool/Message 拼装和快照授权（P1 BORROW_PATTERN）

[default reducer](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/apply/default.ts) 对 Tool START/ARGS/END 分片及 parentMessageId 关联处理错误 ID/角色，MESSAGES_SNAPSHOT 合并后调用 keepToolResultsWithCalls，避免工具结果脱离对应工具调用。[activity-history.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/activity-history.ts) 用类型作用域声明哪些 activity 是 authoritative，避免“后端快照缺失某一客户端活动”被误删，或反向永远保留已经删除的活动。[compact.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/compact/compact.ts) 将连续 token 和 STATE_DELTA 归并为投影，且文档承认会改变部分事件顺序。
建议 Nerelan：TaskStore 和 evidence 为唯一真实执行来源；UI 可以重排、压缩和补快照，但不能改变执行顺序证据、工具是否真实执行、真实用量、Owner 审批或不可确认副作用。历史回放应从可信 TaskStore 读模组重新生成 UI snapshot，不用浏览器持久记忆取代服务器。

### E. 最重要的拒绝项：前端 FilterToolCalls 不构成安全门禁（P0 REJECT_AS_AUTHORITY）

[filter-tool-calls.ts](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/sdks/typescript/packages/client/src/middleware/filter-tool-calls.ts) 的逻辑是从 Observable 流中过滤 TOOL_CALL_START、ARGS、END、RESULT 并按 run 清空 blockedToolCallIds。它只改变 **哪些工具事件被订阅者看到**；不会阻止后端执行该工具。反而可能隐藏了已执行的高风险工具调用、削弱审计可见性。
**绝不能**以 `allowedToolCalls/disallowedToolCalls` 作为 Nerelan 执行器/MCP/Frontend Tool 的 Owner 权限证明。必须在 host 实际 tools/call side-effect seam 检查 ToolName×Task×Attempt×Actor×AuthorizationSnapshot；已授权/拒绝/UNKNOWN 的不可篡改审计在 TaskStore，而不是来自 UI 事件。客户端 RunAgentInput 里自带 tools/state/messages 也不代表能访问任何宿主工具或密钥。

### F. 主动 UI、Steering 和产品价值（P2 CONDITIONALLY REUSE）

[README](https://github.com/ag-ui-protocol/ag-ui/blob/344d21fcc1bc276a1168546ae7c8ccaba96a3545/README.md) 提到 HITL interrupt、前端工具、共享状态和子代理。对 Nerelan 的用户价值应是“我为什么要介入、什么证据证明任务完成、继续会花多少钱”，而非单纯 token-by-token 动画。AG-UI 和 A2UI/MCP Apps/通用聊天外壳可共存，但不能把它们都全量引入。
**实际推荐的最小范围**：保留现有 assistant-ui/Goal-Thread；作为内部候选定义只读 AG-UI-compatible EventProjection（version, runId, taskId, attemptId, stable event key, owner, eventType, sourceHash, payloadSummary），源于 TaskStore Timeline；支持限量回放/丢包后刷新和简洁/标准/详细视图；不提供任何前端 Agent 自身替代执行器控制环。

## 2. Nerelan 模块复用矩阵

| 模块 | 决策 | 具体内容 | 现有归属 |
|---|---|---|---|
| 通用 Agent UI event adapter | P1 BORROW_PATTERN | Run/Step/Text/Tool/Activity/Subagent 通用事件映射，跨执行器身份分离 | #280 #375 #806 |
| SSE/JSON 验证与 conformance fixtures | P1 HIGH_VALUE | schema-first, enforce-before-expand，stream budget，错误/乱序/并发回放 | #280 #281 #806 |
| 只读 Activity/Context Projection | ALREADY_DIRECTION + P1 | 折叠信息、同 ID 重放、跨端重连、只读状态快照 | #280 #448 #296 |
| UI Tool/Plugin 过滤 | P0 REJECT_AS_AUTHORITY | FilterToolCalls 只隐藏事件，宿主仍必须拒绝未授权 tool call | #790 #179 #253 |
| HITL/Steering | P2 BORROW_PATTERN | interrupt outcome 与用户动作是请求，必须宿主重新确认并保存批准证据 | #795 #179 |
| Agent Loop/Session Memory | REJECT_DUPLICATION | 保留 Nerelan TaskStore/多执行器路由/持久性事实 | #1546 #1527 |
| 模型成本/预算 | KEEP_NERELAN | Magpie 实际请求记录和已验收任务总成本 | #1342 #1531 #1267 |

## 3. 最小可证伪 provider-free 实验（全部未执行）

**T1 双执行器同义流**：OpenCode、Codex、Claude 的 fake progress 同映射至 Run/Step/Tool/Message；不同执行器输出相同可接受的用户呈现，不泄露 raw headers/secrets。
**T2 失序与恶意输入**：CONFORMANCE first-event, duplicate START, wrong role, tool result without call, after-finished, wrong subagent owner, invalid JSON Patch, unknown fields/older protocol。所有不合法终态应明确 ERROR/TRUNCATED/UNKNOWN，绝不变成 SUCCESS。
**T3 重放/断线重连**：断线重连后从 TaskStore 投影重建；跨 attempt 同 ID 不混合；重发同一 chunk 不重复附加；UI 只丢弃重复渲染，不删除原始证据。
**T4 ToolHide 负例**：前端 FilterToolCalls 隐藏某危险工具的事件，但试图直接调用该工具仍必须在 host side-effect gate 被拒；如果后端确已执行，只读审计不得隐藏这条证据。
**T5 多 Agent/HITL**：两个 Agent 使用相同 message/tool id、步骤名、reasoning span；一 Agent 等待人工批准，另一 Agent 仍更新。批准须绑定权限和 Task revision，过期拒绝。
**T6 流量/隐私预算**：小单条事件和大量并发分片、超大 SSE 完整帧/缓存尾、JSON 深嵌套/数组、工具 stdout/敏感凭据；对 host 事件/每消息/每 run 输出限额、脱敏、快速拒绝与 UI 提示进行真实测量。
**T7 成本-价值对照**：同一接受标准，比较现有只读 Task timeline 与 AG-UI compatible projection；衡量用户找到需要干预的时间、误判率、CPU/memory/SSE 开销、开发维护复杂度。若没有显著可见价值，不引入第二套 JS Agent state runtime。

## 4. 最终裁定

**SELECTIVE_BORROW_PATTERN / P1_CONFORMANCE_FIXTURES / NO_GO_FOR_CLIENT_AUTHORITY / P2_OPTIONAL_AG_UI_COMPAT_ADAPTER**。最值得做的是“可信事件规范 + 统一多 Agent 视图 + 断线可恢复的 UI 投影”；最应拒绝的是把 AG-UI SDK 的内存消息状态、Client tools、FilterToolCalls 和 UI 中断当作 TaskStore 真相或 Owner 权限。当前代码已完成基础体验，不做全量重写。

本 Issue 为静态源码研究与测试计划：**未安装、未运行测试、未调用模型、未创建 AG-UI runtime、未进行 CI、未独立评审、未合并**。后续文档以 R1 Draft PR 提交，禁止抢占既有实施 Owner 或将研究自动升级为 R2/R3 安装授权。

---

## 本轮追加：新 main 的现状对齐（避免研究时基线漂移）

- [frontend/src/hooks/use-platform.ts](https://github.com/dddd2024/Nerelan/blob/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3/frontend/src/hooks/use-platform.ts) 中已有 Goal/Status 的 React Query polling、运行时更高频刷新、重连与 retry 分级。这不是 AG-UI SSE stream；**建议先以 polling 的 TaskStore snapshot 为真相，AG-UI compatible event envelope 只作可选更细粒度 UI 渐进增强**，不可引入两套互相矛盾的运行状态。
- [frontend/src/components/goal-thread.tsx](https://github.com/dddd2024/Nerelan/blob/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3/frontend/src/components/goal-thread.tsx) 已使用 assistant-ui 并支持停止/重试交互，不能以 AG-UI 的 frontend-tools/HITL 协议代替实际 API 权限。
- [reverse_agent/platform_v1/task_service.py](https://github.com/dddd2024/Nerelan/blob/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3/reverse_agent/platform_v1/task_service.py) 仍声明 Task/Run truth 在服务端 TaskStore；最新版本强化错误结构与读取端路径。AG-UI 事件仅能是从服务端已裁剪、已脱敏的 read model 发出的快照/增量。
- [frontend/src/lib/goal-thread.ts](https://github.com/dddd2024/Nerelan/blob/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3/frontend/src/lib/goal-thread.ts) 把 Executor progress 转为 assistant-ui ToolCall parts 是展示性映射，不能将 ToolCall part.id 当成真实工具副作用收据。

## 最小范围（不扩实施权限）

本 PR 仅新增此研究报告，不修改 package.json、Python/TS 运行时、TaskStore、前端组件、工作流、测试或安全政策。未来优先把上游 **spec/1.0/conformance/streams** 的 provider-free 场景作为测试思想映射到现有 #280/#375/#806 读取层，并保留同一 Task/Attempt/Agent ID/证据 ID 的映射；全量 AG-UI SDK/Client Agent Runtime 不是本研究授权的默认方案。

**Go/No-go**：若只读事件适配器无法在断线、乱序、并行、跨版本和权限撤销时与 TaskStore 投影一致，则停留在当前已存在的 polling/assistant-ui 实现，不引入 AG-UI 依赖。此文件须依 AGENTS.md 作为 R1 Docs-only Draft，经 exact-head CI、独立评审后才能考虑合入；本研究没有宣称这些步骤已经完成。