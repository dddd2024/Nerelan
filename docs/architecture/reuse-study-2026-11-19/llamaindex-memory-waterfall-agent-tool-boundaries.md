<!-- Research only; canonical Issue #1701. Exact upstream SHA and tests-not-run statements below. -->

# LlamaIndex source audit — Waterfall Memory Blocks × Agent tool/handoff trust × Nerelan Context

> **2026-11-19** · SINGLE_UPSTREAM / PINNED_STATIC_SOURCE_REVIEW / RESEARCH_ONLY / NO_TESTS_RUN / NOT_INSTALLED / NOT_IMPLEMENTED / NOT_MERGED / NO R2-R3 AUTHORITY
>
> **Upstream:** [run-llama/llama_index@99d7433f6f71888951379ccca9294e272442c832](https://github.com/run-llama/llama_index/commit/99d7433f6f71888951379ccca9294e272442c832), root [MIT license](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/LICENSE).
>
> **Nerelan inspected:** [main@b48cc9b82893be222e2ccdb307dd4a81bebee935](https://github.com/dddd2024/Nerelan/commit/b48cc9b82893be222e2ccdb307dd4a81bebee935); version-pinned file reads, not live host behavior proof.

## 0. 事前查重与选题防重复

- 搜索 Nerelan GitHub Issues（标题、正文）`LlamaIndex` / `llama-index` / `run-llama/llama_index` / 标题 `Llama`，均未发现独立源码专项；检查研究总索引 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)、11/15 横向研究、此前 Mem0 [#1655](https://github.com/dddd2024/Nerelan/issues/1655)、Graphiti [#1612](https://github.com/dddd2024/Nerelan/issues/1612)、Deep Agents [#1657](https://github.com/dddd2024/Nerelan/issues/1657) 与上轮 Inspect AI [#1697](https://github.com/dddd2024/Nerelan/issues/1697)。
- 排除已单独深审的 Pydantic AI [#1639](https://github.com/dddd2024/Nerelan/issues/1639)、Pi-Harness [#1625](https://github.com/dddd2024/Nerelan/issues/1625)、smolagents [#1643](https://github.com/dddd2024/Nerelan/issues/1643)、Agno [#1616](https://github.com/dddd2024/Nerelan/issues/1616)；`letta-ai/letta` 当前 README 把活跃代码迁到 Letta Code，历史已提过该源码，故**没有**把该 pointer/retired repo 伪作新研究。最终只研究**一个项目：run-llama/llama_index**。
- 区分已有内容：Mem0/Graphiti 关注长期事实提取与检索；本轮**只**审 LlamaIndex core 的短期对话 FIFO → typed Memory Blocks 水位、tool/agent handoff 与 failure ordering；不做 RAG 市场综述或“再次建议新 vector DB”。
- 实施 Owner 维持 **#296 / #642** Context Budget，**#379 / #103** Memory governance，**#1508** multi-agent，**#790 / #253** Plugin/Tool 运行时，**#1546** durability，**#1267 / #1527** quality-cost benchmark，**#299 / #179** Host safety。**不新增重复功能 Issue**。

## 1. 固定源码证据与 Nerelan 逐模块裁决

### A. Memory Block / token budget — **BORROW_PATTERN P1**，不要复制 DB

1. [`memory/memory.py` L103–185](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L103-L185) `BaseMemoryBlock` 提供 `name`、`priority`、`accept_short_term_memory`、`aget`、`aput`、可覆写的 `atruncate`。返回可为 text、ContentBlock 或 ChatMessage。此处是**可组合投影 API**，不是持久化真实性来源；`aput` 给传入消息的 `additional_kwargs` 就地增补 `session_id`，共享可变对象需特别注意。
2. [`memory.py` L188–260](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L188-L260), [L624–668](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L624-L668)：`Memory` 将 ACTIVE chat history 和 Memory Blocks 分别读取/计数，再在 system 或最新 user 消息注入 block。**Nerelan 应建立 Host-owned 类型化上下文投影**：
   - **GoalContract**：当前 Owner 已批准目标、边界、来源和版本，永远通过权威事实读取，不能靠 LLM summary 重建；
   - **WorkingTurn**：最近完整工具调用与结果的短期回合；
   - **TaskHandoff**：从现有 `ContextHandoff` evidence 按 scope+snapshot+source digest 编译；
   - **EvidenceFacts**：从 `ContextSummary`/可见证据按 scope 检索、失效/回收可重建。
   每类独立说明 `max_bytes/tokens`、来源 refs、是否可截断、工具权限影响（默认 **NONE**）、状态 `READY/STALE/PARTIAL/UNKNOWN`，但以 TaskStore 为唯一事实。不要把不可信记忆伪装成宿主 system 指令。
3. [`memory.py` L672–810](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L672-L810)：超过 `token_limit * chat_history_token_ratio` 后按批次逐出最旧消息，尽量使队列从 user 消息开始并保留完整 turn；再调用 `archive_oldest_messages`，随后 `asyncio.gather(block.aput...)`。现有 [上游 turn/tool 测试](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/tests/memory/test_memory_base.py#L229-L306) 涵盖 user→assistant→tool→assistant 的边界（**仅阅读，未执行**）。**复制 invariant**，不复制未做原子提交的 waterfall 实现。
4. **重要 P0 负例：归档与 block 更新不是一个事务。** [`memory.py` L776–807](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L776-L807) 先 archive 再异步并行写 block；[`storage/chat_store/sql.py` L372–405](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/storage/chat_store/sql.py#L372-L405) archive 已单独 commit。若第二步报错或进程断开，旧消息仍在 ARCHIVED，但其派生 block 可能缺/部分成功。上游原始消息尚在 DB 中，不可说数据必然永久丢失；**但 ACTIVE 投影与衍生记忆可不一致，未见此路径中原子化/恢复日志**。Nerelan 借鉴的正确方案为 **canonical evidence → pending materialization → per-block acknowledged projection → retire from active projection**，失败保持重建任务、不得将 PARTIAL 当完整。
5. **P0 负例：`priority=0` 永不截断，不意味着总 budget 一定成立。** [`memory.py` L481–544](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory.py#L481-L544) 明确跳过 priority 0，且保留至少一个完整对话轮次；若 pinned blocks 或单个 turn 超过预算，不能宣称 `aget()` 严格不会越界。Nerelan 应把权威状态 **与模型 token 窗口分离**，超预算返回 `PROJECTION_OVER_BUDGET` 或安全的分层内容引用，而不是静默丢掉 Owner 指令/工具收据。
6. **部署反面证据**：[ `storage/chat_store/sql.py` L31–75](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/storage/chat_store/sql.py#L31-L75) 默认 URI **`sqlite+aiosqlite:///:memory:`**；[`AgentWorkflow` L269–278](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/multi_agent_workflow.py#L269-L278) 和 [`BaseWorkflowAgent` L294–303](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/base_agent.py#L294-L303) 的默认 memory 仍为 `ChatMemoryBuffer.from_defaults` 而非上述可插拔 `Memory`。不要因为文档说 Context 可序列化，就宣称 Agent 整体跨重启具备 durable exactly-once。

### B. VectorMemoryBlock / Scope — **P0 TEST_FIRST, no direct ACL inheritance**

- [`memory_blocks/vector.py` L100–166](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory_blocks/vector.py#L100-L166)：按最近消息查询 embedding，传入 `session_id` 时若已有 filters 含同名 `session_id` 则**保留原 filter 而不强制验证一致**。因此 metadata filter 是调用方配置，不是 Nerelan Owner/Repo/Task 的授权检查。
- [`vector.py` L170–201](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/memory/memory_blocks/vector.py#L170-L201)：对 `message.additional_kwargs.pop("session_id")` **就地删除输入字段**，合并一批消息成单个向量节点，metadata 只有最后观察到的 session_id；与其他 block 并行接收**同一批消息对象**时可能存在可变数据的相互影响。需要深拷贝/不可变记录与 per-source stable ID，而不是把 session_id 字符串当 ACL。这个风险是静态机制推断，未执行并发复现。
- 来源、授权和输出投影由现有 TaskStore/visibility scope 决定；向量/关键词索引永远 derived，跨 scope 检索未证明受权则拒绝。

### C. Agent Handoff / Plugin Tool Router — **BORROW typed events, REJECT as authority**

- [`multi_agent_workflow.py` L73–93](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/multi_agent_workflow.py#L73-L93) `handoff` 按 ctx.store `agents/can_handoff_to` 判断并写 `next_agent`；[L220–266](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/multi_agent_workflow.py#L220-L266) 动态拼装 Agent tools + `tool_retriever` 找到的工具 + handoff tool。**这只是工作流路由，不是 Owner principal/grant/tool-scope 的权限证明**。复制工具列表与来源可解释性；Host 在实际 tool invocation 再验证 trust、scope、request digest、RPC/egress 权限。
- [`workflow_events.py` L24–114](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/workflow_events.py#L24-L114) 有 `AgentInput/Output/ToolCall/ToolCallResult` typed events with `tool_id/name/kwargs/output`；Nerelan 可映射到已有 TaskEvents/收据，而不是新建事件总线。
- [`base_agent.py` L357–392, L615–698](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/llama-index-core/llama_index/core/agent/workflow/base_agent.py#L615-L698) `call_tool` 发事件、直接 `acall`、把一般异常包装为 `ToolOutput(is_error=True)`，然后 `collect_events` 聚合；源码**未在此方法中看到**独立的远端 side-effect reservation/fencing 或 Host 权限。错误输出与未收到结果必须分别记录；不能把“ToolCallResult event 出现”直接当“外部副作用按且只按一次完成”。Nerelan 既有 `durable_external_operations` 是更高优先级约束。
- [Agent state doc](https://github.com/run-llama/llama_index/blob/99d7433f6f71888951379ccca9294e272442c832/docs/src/content/docs/framework/understanding/agent/state.md#L7-L79) 说 Context 默认 run 间 stateless、可显式序列化，也允许 JsonPickleSerializer；序列化可行≠外部调用收据安全，禁止用 pickle 反序列化不可信上传。

## 2. 对 Nerelan 已有模块的“不能重复开发”核查

- [`context_recovery.py` L72–159](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/context_recovery.py#L72-L159)：**已经有** `ContextSummary` 原文摘要来源校验、`ContextHandoff` 绑定 `from_agent/to_agent/scope_digest/input_snapshot_digest`、`recover` 校验 scope；且 handoff 返回 `authority:'NONE'`。**不要**复制 LlamaIndex 的无 Host 授权 handoff 当真实 delegation。
- [`context_optimization.py` L14–103](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/context_optimization.py#L14-L103)：**已经有** `scope_digest`/全文 catalog/source digest、检索 budget、`compact_context` 固定优先级与 `summary_trigger`。本轮增量在 typed block/turn grouping、block materialization receipt 和预算溢出诊断，不是复刻一个 compact/RAG 服务。
- [`run_store.py` L2974–3229](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/run_store.py#L2974-L3229)：已实现外部操作事务 intent + lease fencing + PENDING fail-closed + immutable terminal receipt。不要移植 LlamaIndex Workflow 取代它；Plugin/MCP 的实际调用同理。
- 现有实施归属不变：#296/#642 Context，#379 Memory，#103 cross-agent，#1508 multiagent，#790/#253 plugin/MCP，#1546 durable，#1267 cost/quality，#299 sandbox。

## 3. 最小增量设计与具体落点

| Nerelan 所属层 | 可借鉴 | 不可复制 | 验证 |
|---|---|---|---|
| `context_optimization.py` | `WorkingTurn + GoalContract + EvidenceFacts + Handoff` typed budget, **complete tool-call/result grouping** | 任意 memory system-instruction 注入、priority0 token 无限 | 过预算/断开工具对/异步消息 |
| `context_recovery.py` | derived block `PENDING→READY/FAILED` 的 source digest / content version / retry ledger | archive-before-commit、丢掉原始事实 | 块 2/3 失败后重启重建，原始证据完整 |
| `context_builder.py` | projection only 读 Host 可见来源；per-agent/tool allowlist | 取用户写的 metadata `session_id` 当 ACL | cross-project/session forged filters |
| `tool` / Agent adapters | typed ToolCall/Result/handoff reason 和 block provenance | tool retriever 即授权；工具成功事件等于 exactly-once | 拒绝未授权检索工具，重复副作用 UNKNOWN |
| `model_profiles` / cost | 统计每次 block 检索/摘要/向量写入的额外 tokens/cost | 原样引入新模型依赖造成更高成本 | 不减少受独立验收成功率，观察边际额外费用 |

**Priority**: P0 先验证 no-data-loss/no-ACL-bypass/no-duplicate-effect；P1 则做轻量 typed block API 与 context budget、完整回合；P2 只有真实需求才使用 SQL/vector backing stores。**无充分证据引入 LlamaIndex 依赖或第二记忆服务，默认 COPY-DESIGN 而非 ADOPT**。

## 4. Provider-free 故障注入 / 效益证明计划（未运行）

1. **Crash-between-archive-and-block**: 3 个块，第一成功、第二抛异常、第三未知；原始消息仍保留，`PARTIAL` 不可见为 READY，重启按 source digest 幂等修复，不再额外调用模型。
2. **Parallel mutation**: 一批消息向 VectorMemoryBlock+事实块投影，在 copy/merge 中验证 `session_id` 与消息 hash 不变；并行/重试/相同消息不同 scope 不可跨租户污染。
3. **Mismatched filters**: 数据查询预置 `session_id=other_owner`，当前请求 `session_id=own`，Host 不允许依赖 Vector block 的“已经有 filter”分支，必须返回无权限/空结果。
4. **Complete turns**: FIFO 被触发于 user→assistant tool call→tool result→assistant 中间，输出不能产生孤立 tool result；同时保留未完成的 side-effect UNKNOWN receipt 作为不可裁剪事实。
5. **Pinned block overflow**: 10K tokens 上限，pin 15K + conversation 4K；不静默继续超预算或删除 Owner 批准的契约；以可审计的预算错误/分层引用拒绝。
6. **Tool retriever/Handoff**: retriever 加一条恶意未授权工具，`handoff` 要求越权 Agent；列表可见不等于 execute 许可，Host 再查 grant/epoch/digest，拒绝越权且写 evidence。
7. **Cost/quality A/B**: 相同已冻结任务/Agent×model/budget 下，旧 context 投影 vs typed turns/blocks；统计真实 tokens、model+embedding costs、重试数、TaskStore COMPLETED+独立 Accepted 数，不以“看起来更少的上下文”宣称效率收益。缺失 usage/cash 为 UNKNOWN，不自动填 0。

## 5. 实际证据等级

已完成：查重、固定上游 SHA、读取指定 LlamaIndex Core memory/agent/tool/chat-store 源码与上游相关 test source，读取 Nerelan 现有 Context/Goal/TaskStore 模块与已有 Owner Issues，形成模块级复用决策和可证伪反例。

**未完成**：上游安装、单测执行、Nerelan provider-free/paid benchmark、与 Host 的真实 API 集成、Windows/runtime 验收、CI、独立审查、Merge。读取 upstream pytest 代码 ≠ 执行测试。本 Issue 和 Draft PR 不构成功能实施权限或通过证明。


---

## Publication status
- Canonical single-upstream research: https://github.com/dddd2024/Nerelan/issues/1701
- Research hub: https://github.com/dddd2024/Nerelan/issues/1576
- This is an R1 documentation-only research branch. R2/R3 implementation not authorized, no merge or runtime dependency change.
- STATUS = STATIC_SOURCE_REVIEW / TESTS_NOT_RUN / DOCS_ONLY / NOT_MERGED.
