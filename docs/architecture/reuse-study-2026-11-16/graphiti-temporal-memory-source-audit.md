# Graphiti 时态记忆与并发摄取源码研究（Nerelan 对照）

**Research Issue:** [#1612](https://github.com/dddd2024/Nerelan/issues/1612) · **Canonical hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **Status:** STATIC_SOURCE_REVIEW / DOCS_ONLY / NOT_TESTED / NOT_IMPLEMENTED

> **2026-11-16 · RESEARCH_ONLY / STATIC_SOURCE_REVIEW / NOT_INSTALLED / NO_RUNTIME_OR_COST_TEST / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**
>
> **唯一上游：** [getzep/graphiti@869c1b279e01a2767a464581e1cb657ce0e39271](https://github.com/getzep/graphiti/commit/869c1b279e01a2767a464581e1cb657ce0e39271)，[Apache-2.0](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/LICENSE)；对照 Nerelan [main@0a9997046386bac5ca291410ce428c160f3ea763](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763)。
>
> 本报告基于固定 SHA 的 Python 源码、上游测试文件、Nerelan 实际模块与既有 Issue；**未安装 Graphiti、未调用模型、未运行上游/Nerelan 测试，不代表安全、性能、经济性已经验证。**

## 0. 必须事前完成的查重

- 查核 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 唯一总研究台账与其 11/15 A–E 横向报告、[历史研究目录（Draft PR #1577）](https://github.com/dddd2024/Nerelan/blob/agent/reuse-research-hub-20261116/docs/architecture/reuse-study-2026-11-16/history/INDEX.md)，以及 11/16 已创建的源码专项至 OpenAI Agents SDK #1609。
- GitHub 全仓 Issue 与 PR 搜索 `Graphiti`、`Zep` 和源代码搜索 `graphiti` 未找到独立专项或集成；与 Letta Code 的 Git/Reflection Memory、Mastra 的 Context Projection、Google ADK 的 Session/Compaction 属于**相邻主题但不是 Graphiti 时态知识库的同一源码审计**。查无记录不意味着没有零散讨论。
- 本轮不研究其他项目，不新增与 #296、#642、#1546、#790、#1267、#1342 重复的实施 Owner。

## 1. Nerelan 已有的东西——不要重复造

- [`reverse_agent/platform_v1/context_recovery.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/context_recovery.py)：现有 TaskStore 内 ContextSummary/ContextHandoff 来源、Scope 和 snapshot digest 校验；handoff 不能授权执行；summary 显式执行且防止重复收费。这是**值得保留的基础**。
- [`context_optimization.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/context_optimization.py)：provider-free Context Catalog/lexical retrieval、受可见范围与字节预算限制、source digest、可重现投影，已有与本研究目标重叠的设计。
- [#296](https://github.com/dddd2024/Nerelan/issues/296) 是现有上下文效率/生命周期 Roadmap；[#642](https://github.com/dddd2024/Nerelan/issues/642) 是短 Prompt 与 GitHub 权威来源；[#1546](https://github.com/dddd2024/Nerelan/issues/1546) 是 Goal 持久引擎 Spike；[#1267](https://github.com/dddd2024/Nerelan/issues/1267) 是质量/真实成本基准唯一 Owner；[#790](https://github.com/dddd2024/Nerelan/issues/790) 是 MCP/Connector 运行时唯一 Owner。
- 目前没有在上述**已检查的** Context 模块见到 Graphiti 式跨 Goal 时间化实体/关系检索；不是断言全仓不存在任何其他记忆功能。

## 2. 源码机制与具体复用决策

| Graphiti 模块（固定 SHA） | 真实代码机制 | Nerelan 对应／可抄什么 | 结论 |
|---|---|---|---|
| [`nodes.py` EpisodicNode 245–282](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/nodes.py#L245-L282)、[`edges.py` EntityEdge 228–254](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/edges.py#L228-L254) | 原始 Episode 有 `content/source/valid_at/created_at`；事实 Edge 有 `episodes[]/valid_at/invalid_at/expired_at`；边为衍生事实，不取代原始证据 | **只读 Memory Projection**：在已授权 TaskStore/GitHub 证据上建立 `fact→source_ref/source_digest`；分别记录发生时间、观察时间、失效证据、scope；过期事实不能作为当前执行依据 | **BORROW_PATTERN P1** |
| [`ingestion/change_set.py` 30–125](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/ingestion/change_set.py#L30-L125) | 一次摄取整理为 ChangeSet，包含 `unit_id/seq/snapshot_seq`、新建实体、EndEdge、PatchNode、源 Episode、候选冲突/去重记录 | 对 Memory Projection 的新增/失效先形成**可审阅增量**（derived, non-authoritative），在来源变更后重建；不能直接写入 Work Item 真实状态 | **BORROW_PATTERN P1** |
| [`ingestion/state_store.py` 105–199](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/ingestion/state_store.py#L105-L199)、[`sqlite_state_store.py` 238–300,343–430](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/ingestion/sqlite_state_store.py#L343-L430) | 原子 Admission、`unit_id` 重放检测、组内序号、Lease、Heartbeat、`fence`、序号提交及旧 payload 恢复；`BEGIN IMMEDIATE` | 同仓已有 TaskStore/租约/Checkpoint，**不复制第二套 Scheduler/SQLite 状态库**；如未来允许批量记忆写入，参考“分析可并行、提交有序、过期 Fence 不得更新”的 invariant | **ALREADY_REUSED / BORROW_PATTERN** |
| [`ingestion/delta.py` 107–175,249–350](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/ingestion/delta.py#L249-L350)、[`tests/ingestion/test_commit_repair.py`](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/tests/ingestion/test_commit_repair.py) | 为近期已提交/部分 apply_failed 改动计算局部 Delta，检测节点/边重复、索引滞后及矛盾；有 recovery 测试覆盖，但本次未运行 | 上游测试模式可转为**无 Provider**反例：两 Agent 先后发现相同事实、旧索引、过期事件、崩溃重启后重复写入 | **BORROW_PATTERN P1** |
| [`utils/maintenance/temporal_edge_utils.py` 39–71](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/utils/maintenance/temporal_edge_utils.py#L39-L71) | 区分未来计划/承诺时间与已发生事实的有效时间；防止“周五前完成”被误做成失效边界 | 长期 Goal/科研任务中，“计划明天修复”**不是**“明天已修复”；区分 `PLANNED/OBSERVED/ACCEPTED/REVOKED`；只有受信验收和真实事实源决定完成 | **BORROW_PATTERN P1** |
| [`search/search_config_recipes.py` 33–154](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/search/search_config_recipes.py#L33-L154)、[`search/search.py` 98–161](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/search/search.py#L98-L161) | BM25 + cosine + optional BFS、RRF/MMR/CrossEncoder; 需要查询嵌入时会调用 Embedder；`group_ids=[]` / `['']` 转成 `None`，**不代表不可见** | 第一步继续已有词法检索/来源型 Context Pack；只有证据证明跨 Goal 检索必要且准确性净改善，才对局部只读 index 测试向量/图检索；Host 不许把空组当权限过滤 | **BORROW_PATTERN conditional P2** |
| [`search/search_filters.py` 38–75](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/search/search_filters.py#L38-L75) | `valid_at/invalid_at/created_at/expired_at` 筛选是可选字段；**默认 SearchFilters 不代表只返回仍有效的事实** | 构造投影时必须同时验证 scope、source digest、事件状态及当前 GitHub/TaskStore truth；不能将一般搜索结果提升为当前事实/执行授权 | **REJECT default-as-authority** |
| [`mcp_server/README.md` 8–20](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/mcp_server/README.md#L8-L20)、[`mcp_server/src/graphiti_mcp_server.py` 402–780](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/mcp_server/src/graphiti_mcp_server.py#L402-L780) | 上游警告：MCP Server 是 reference，**无 authentication/authorization/prompt-injection protection**；其公开工具包含 add/search/delete/clear，`group_id` 可被请求指定 | **不要**直接启用其可写 MCP；Graphiti 的 group_id 是数据分组，非 Nerelan 授权。任何只读记忆能力必须经现有 #790/#303/#447 Host Gate | **REJECT DIRECT MCP** |
| [`telemetry/telemetry.py` 15–114](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/telemetry/telemetry.py#L15-L114) | `GRAPHITI_TELEMETRY_ENABLED` 缺失时默认 true，若 `posthog` 可导入会向 `us.i.posthog.com` 发匿名安装事件 | Local-first 默认禁止未批准 egress；研究实验也应 explicit `GRAPHITI_TELEMETRY_ENABLED=false` 并检查实际网络。**本次没有执行此操作或测试网络** | **REJECT defaults** |
| [`llm_client/openai_base_client.py` 43–220](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/llm_client/openai_base_client.py#L43-L220)、[`llm_client/token_tracker.py` 22–100](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/graphiti_core/llm_client/token_tracker.py#L22-L100) | Episode 提取/去重可发 LLM、Embedding 调用；TokenUsageTracker 按 prompt 分类计数；本身**不是** Magpie 真实现金与订阅额度账本 | 任何模型/Embedder 请求都必须经 Magpie、受预算约束并保留 Request/Goal 关联。无实际收益实验不能默认让每个 Agent Turn 自动记忆抽取 | **REJECT auto-on / BORROW cost instrumentation** |
| [`pyproject.toml` 1–54](https://github.com/getzep/graphiti/blob/869c1b279e01a2767a464581e1cb657ce0e39271/pyproject.toml#L1-L54) | 核心图数据库驱动 Neo4j，选配 FalkorDB/FalkorDBLite 等，伴随模型和检索依赖；不是单文件免费 Session Store | 当前 Windows local-first/已有 SQLite TaskStore 场景，应先轻量 provider-free memory fixture；不因“图记忆”直接引入运行依赖/服务 | **REJECT FULL ADOPTION** |

## 3. 与 Nerelan 真正目标的判断

**用户价值机会**（未验证）：当 Goal 跨天、跨 Agent、跨项目时，用户不应重复介绍“项目现在使用哪个模型/环境、上次为何暂停、之前哪个方案被否决”；系统能从真实来源提供**可追溯、带失效状态**的记忆卡，且已变更的 GitHub/TaskStore 权威事实自动使旧卡失效。对长期复杂任务有用；对短小任务，抽取/嵌入/维护增加时延和成本，很可能适得其反。

**最小候选合同**（仅设计，不授权实现）：`memory_fact_id, owner_scope, repository, goal_id, source_ref, source_digest, observed_at, asserted_valid_at, invalidated_at, extraction_version, derivation_state, confidence_or_unknown, non_authoritative=true`。读取前校验受信源和当前可见范围，原文/工具日志不直接变成 Owner 命令，模型摘要不能更改 Work Item / Secret / policy。

**产品呈现**：仅当检索到高度相关的记忆时显示“来自哪个 Issue/Run/Commit、何时观察、是否过期、为什么有帮助”；宁可显示“需要重新核对”，不展示无来源的貌似确定陈述。

## 4. 无模型调用的最小证伪实验（尚未执行）

1. **时态错配**：记录“下周更新 executor”的计划，未来日到来前后不得变成“executor 已更新”；以真实 main/PR 合并收据为准。
2. **来源撤销/快照变化**：source digest、Git head、Work Item revision 或 scope 变化后，旧衍生记忆应失效/显式标记，不覆盖当前 Context。
3. **授权隔离**：多个 Goal/Repository/Owner 的 `group_id`，空组筛选、越权指定组、连接失败等都不能扩大可见范围。
4. **冲突与恢复**：两个 Worker 同时提出相同/矛盾事实，重复 ingest、旧 fence、apply 中断及重新回放不能造出两个看似当前的事实或提升无收据的写入。
5. **无外发**：模拟 LLM/Embedding/Telemetry/MCP 接口，未授权时零网络与零付费模型请求；明确任何第三方 MCP 不能更改正式记忆授权。
6. **成本/质量**：用固定短/中/长的真实 Goal（#1267 baseline）比较：当前来源型词法 Context、只读时间化记忆、图/混合检索三臂。记录可证实旧事实召回率、失效事实误用、跨 Goal 检索权限差错、质量验收、LLM+Embedding+缓存/重试/Reviewer 总消耗与 **每个 accepted outcome 的成本**，而非“检索分数更高”。

**Go 门槛：** 新记忆能显著减少忘记/重复探索/失效误用，且无授权、来源、外发回归，同时计入所有模型+检索成本后净值为正。否则只复用时态事实和失效测试模式，保留现有 Context Store。

## 5. 当前推荐排序与归属

- **P1 BORROW_PATTERN**：带 provenance 与时间区间的非权威 Memory Projection + stale/contradiction tests → 已有 #296/#642（实际实施须另经正常审批）。
- **P1 BORROW_PATTERN**：并发 ChangeSet、有序提交及 crash fixtures → 现有 TaskStore/Goal Runtime #1546，不建第二状态引擎。
- **P2 CONDITIONAL**：Graphiti 式 hybrid search 或完整 Graphiti 作为可选只读 memory backend，先在 #1267 证明质量/成本/权限收益。
- **P0 REJECT**：参考 MCP Server、默认 Telemetry、空组绕过、记忆作权限来源、自动 LLM/Embedding 消耗 → #790/#303/#447/#1342。

**本 Issue 仅存档单项目源码研究，不代表主张部署 Graphiti、修改生产状态、创建新 Agent/Memory 产品模块、外部 API 或新依赖。** 后续研发继续走 Nerelan `AGENTS.md` CI、exact-head 独立评审和合并门槛。