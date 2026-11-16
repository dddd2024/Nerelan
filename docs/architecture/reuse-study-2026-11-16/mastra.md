# Mastra 源码深拆：路由弃权、Processor、Workflow 恢复、工具审批和 Evals（2026-11-16）

> **级别**：STATIC_SOURCE_REVIEW · NOT_TESTED · RESEARCH_ONLY · NO_EXECUTION_AUTHORITY  
> **上游仓库**：[mastra-ai/mastra](https://github.com/mastra-ai/mastra)，冻结 [`1034a4e41f6a`](https://github.com/mastra-ai/mastra/commit/1034a4e41f6a486090e2555d5e1efef696f462e3)。  
> **Nerelan 对照**：main [`6602908953f4`](https://github.com/dddd2024/Nerelan/commit/6602908953f400f90d6242d8af1bc60f604f1a97)。  
> **GitHub 研究登记**：[Issue #1564](https://github.com/dddd2024/Nerelan/issues/1564)。  
> **许可证**：[LICENSE.md](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/LICENSE.md)；多数源码 Apache-2.0；`ee/` 路径适用 Mastra Enterprise License，**不能把整个仓库笼统称为 Apache-2.0，更不能移植 `ee/` 功能代码**。  
> **证据类型**：上游代码、上游文档、Nerelan 源码和 Issue 静态核查；没有安装 Mastra、运行测试、访问付费模型、复现性能或执行运行故障。

## 0. 在开始研究前的重复检查

检查了 Nerelan 现有 `docs/architecture/reuse-study-2026-11-15/` 五个领域、`COMPETITIVE_LANDSCAPE.md`、研究索引草稿、当天新增 Issues/PR，以及 GitHub 代码/Issues/PR 对 `Mastra`、`mastra-ai`、`MastraCode` 的检索。没有找到该项目**专项源码深拆**。宽泛词 “Mastra” 命中的 Issue #179 未显示对应专门研究段落。此结论是“在已检查入口未发现”，不是断言任何历史讨论都不存在。

本轮不重复 Pi/Letta 的记忆与 Agent Loop、Plandex 的代码地图、OpenClaw 的 Harness/Plugin 或 Paperclip 的 Adapter/Heartbeat。只研究 **Mastra 特有可观测的路由决策、请求态 Processor、恢复安全边界、验证前审批和评测数据定义**；沿用现有 Issue 作实施归属，不创建第二个路由器、工作流数据库或产品模块。

## 1. 定位：Mastra 不等于 Nerelan

Mastra 是 TypeScript AI 应用框架：Agent、Model、Workflow、Memory、MCP、Processor、Eval 与 Studio。[README](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/README.md)。

| 层 | Mastra | Nerelan | 结果 |
|---|---|---|---|
| 模型供应与路由 | Provider abstraction + ModelSelectionProcessor | Magpie + Connection/Binding + model_router | 两者重叠；**只学习决策弃权和证据口径** |
| Agent Runtime | 自己的 Agent 与工具循环 | OpenCode/Codex/Claude 等执行器 | 不复制新 Agent Loop |
| 任务状态 / Workflow | Mastra Workflow + Snapshot/Journal/Resume | TaskStore + LangGraph，DBOS 待 Spike | 不引入新状态事实源 |
| Context | Input/Output/Error Processors、Memory、ToolCallFilter | Context Packet、Context Recovery | 学可回溯的 model-facing projection |
| Tool/MCP | TS tool schema + `@mastra/mcp` | Pack/MCP 将通过 #253/#790 正式复用 | 不把 TS 组件硬嵌入 Python Host |
| Quality/Evals | Datasets、Scorers、Experiments、Traces | 独立验收 + #1267/#1527 | 借鉴实验数据形状；独立验收仍为权威 |

## 2. 模块 A：ModelSelectionProcessor —— “保留强模型、确信时再降级”

代码：[model-selection.ts](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/processors/processors/model-selection.ts)；[官方 API 说明](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/docs/src/content/en/reference/processors/model-selection-processor.mdx)。

### 代码机制

- `processInput()` 仅从**最后一条用户消息的文本**抽取分类输入；分类器每个请求只调用一次，决策暂存在 `__modelSelection`。
- 决策机制支持 `choices` 或外部 `classifier + select`。`minProbability` 设置后，所需概率缺失或低于阈值都选择 `abstained: below-threshold`；另外还区分 `no-text / error / refused / no-model-for-choice`。
- 默认 Agent 配置一个“有能力兜底”的模型；分类失败时没有切换，保留默认模型。`onDecision` 提供审计，但其失败不得打断模型请求。
- `processInputStep()` 可设 `scope: run`（全次运行）或 `first-step`（仅首次）；在内部模型 fallback 已开始后，不继续强行覆盖模型，避免锁死在已失败的便宜模型。
- 代码注释给出“四轮支持任务的首轮只占输入 token 14%、首轮路由仅拿到可用节省的 9%”的**上游经验值**，没有本轮独立复现，不能迁移成 Nerelan 的性能宣称。
- 重要缺点：仅分析最近的用户消息，忽略系统/既有上下文。对 `“继续完成昨天那个复杂改造”` 之类短 follow-up，复杂性容易被低估。源码文档也提醒 Router 的额外分类调用、跨模型 Prompt Cache 失效、便宜模型需要更多步数可能使净成本上升。

### Nerelan 可以抄什么

- **先通过能力/许可/额度硬门槛，最后优化成本**；路由不确定时不应为了“模型选择了一个答案”而冒险降档。
- 一个独立可记录的 `routing_disposition`：`selected / abstained_no_evidence / abstained_low_confidence / classifier_failed / candidate_incompatible / blocked_quota / forced_pin`，附冻结 Task/Context/Binding 快照身份。
- Model Selection 的**净收益必须包含分类成本、错误路由导致的返工、跨模型缓存损失和实际验收**。不能只比较 token 单价。
- 对 Nerelan 的多账户订阅配额，默认“强模型兜底”不是免费：需要 Owner 已授权的可用账户或安全 `WAIT_FOR_CAPACITY`，绝不自行启动付费 API。

### 不该抄什么

- 不把 Mastra ModelSelectionProcessor 放到 OpenCode 的内部调用中替换 Magpie；模型更换需遵守执行器是否支持热切换及 Binding 冻结边界。
- 不以模型自报概率当作已经校准的成功概率；概率阈值先靠标注任务、接受率和消融实验验证。
- 不强制给所有任务加一次 LLM 分类；对于路径、难度和能力需求明确的 Task，直接规则路由可能更便宜。

**归属**：[Nerelan #1267](https://github.com/dddd2024/Nerelan/issues/1267)、[#1527](https://github.com/dddd2024/Nerelan/issues/1527)、`reverse_agent/platform_v1/model_router.py`。**P1：先实验、不改生产选择器**。

## 3. 模块 B：Processor 管线 —— 传给模型的视图与持久证据分开

代码与说明：
- [ToolCallFilter](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/processors/processors/tool-call-filter.ts)
- [GoalStateProcessor](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/agent/goal/state-processor.ts)
- [Processor 文档](https://mastra.ai/docs/agents/processors)
- [ModelSelectionProcessor](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/processors/processors/model-selection.ts)

### 两个值得实际借鉴的细节

**（1）过滤的是本次模型请求，不是任务历史。**
`ToolCallFilter.processLLMRequest()` 接收模型请求的 Prompt 与步骤记录，按工具名/最近产生工具的步骤筛选工具调用及结果；只返回修改后的 `prompt`，不会修改已存储 Message、Memory 或 UI 展示。可选 `preserveModelOutput` 把被删掉的工具调用/结果转换为较短的文本。它还避免留下 provider 不接受的空 assistant/tool 消息，并默认保留本次运行刚产生的工具调用结果。

**（2）Goal 进度投影不是每一步重复塞进系统 Prompt。**
`GoalStateProcessor.computeStateSignal` 把当前 active objective 做成带稳定 `cacheKey` 的快照；没变化且缓存基底仍在时不重复发；Goal 完成/暂停后需要撤回旧快照，避免 LLM 继续遵循已经失效的目标。其实现刻意不把 `runsUsed` 等每步变化字段放进稳定前缀，以免每轮都破坏缓存。

**Processor 顺序** 在 Mastra 中显式影响行为：输入、输出和错误处理流水线；错误 Handler 优先尝试修复 Provider History / Prefill / Unsupported File，再决定 Retry。`transient` 的提醒可以只进入本次模型请求，不留存在历史里。注意它仍是发给模型的输入，不具备 Nerelan 的宿主授权。

### Nerelan 可复用的具体模式

`Durable Context Packet + Tool/Evidence Records -> policy-filtered transient model projection -> model request`。

- 既有 TaskStore/evidence 原文仍是唯一可审计真实历史；
- 允许对模型可见的冗长工具输出做确定性压缩、引用和“按需取全文”；
- 压缩后的模型视图引用来源 digest 和可见性范围，避免跨 Task 隐藏数据泄漏；
- 目标状态用可靠的 Goal 事件重建；模型级 objective 提醒只做**投影**，不能改动任务权威状态；
- 量化实际 Input Tokens、Cache Read、召回率、验收率，特别测试“被隐藏的工具输出原本包含关键错误”情形。

Nerelan 已有 `context_builder.py` / `context_optimization.py` 的只读、确定性压缩和摘要/检索。这里的新增候选仅是**模型请求时的工具历史投影接口**，而不是新建存储或另一个 Memory 系统。

**归属**：[Nerelan #296](https://github.com/dddd2024/Nerelan/issues/296)。**P1（受控纯函数实验）**。

## 4. 模块 C：Workflow Suspend / Resume 与真实恢复安全边界

代码：
- [Workflow step schema](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/workflows/step.ts)
- [RunStorage](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/workflows/run-storage.ts)
- [Run ownership](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/workflows/run-ownership.ts)
- [Suspend/Resume](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/docs/src/content/en/docs/workflows/suspend-and-resume.mdx)

### 实现要点

- `createStep` 的输入/输出、`resumeSchema`、`suspendSchema` 与 `suspend()/resumeData` 形成类型化的交接边界；快照存储在配置的 Storage Adapter，可恢复被暂停的步骤。
- `createRunStorage` 抽象旧版 V1 Snapshot 和 V2 Journal；`loadForResume` / `isClaimUnused` 检查是否存在被另一个 Resume 改动的情形，不只读“状态为 running”。
- `claimWorkflowRunOwnership` 调用 Storage 的 run-ownership lease 与续租；`repeatAfterSettled` 等待前一次续租完成后再计时，避免慢存储下 `setInterval` 并发续租造成乱序。
- **源码明确标记**：“Writes stay unfenced: the lease only tells the boot-time recovery sweep on other replicas that the run is not orphaned.” 这表示不能把该 Lease 当成 Nerelan 所需的每个外部副作用的 Fencing。不能由此断言 Mastra 全部状态写入都无条件不安全——其 Journal 有另外的 CAS/序列机制；但仅凭 Workflow Resume API **不能证明**崩溃/跨进程后恰好一次执行外部 CLI、Reviewer 或发布操作。

### Nerelan 处置

- **Reject**：用 Mastra Workflow 替换 LangGraph/DBOS 工程路线。Mastra 是 TS Framework，Nerelan 宿主是 Python，整体嵌入会增加跨语言运行、第二套 Workflow 状态和 Recovery 归属。
- **Borrow**：HITL 输入应有可验证的 `suspended_execution_id + tool_call_id + goal_revision + expected_head + expected_authority_digest`；外部完成必须验证精确快照、当前 Owner 授权、重复交付与过期回复。
- **Borrow**：续租完成后再安排下一次续租，丢失 Lease 的旧执行者不能凭历史已批准状态继续进行持久写入或敏感副作用。
- **Go/No-Go**：先执行已有 [DBOS Spike #1546](https://github.com/dddd2024/Nerelan/issues/1546)，按它固定的 crash-after-dispatch / 旧持有者 / 重启回放与代码替代规模指标判断，而不是因为 Mastra 有 Snapshots 就替换。

**优先级：P2，作为既有 #1546、#795 的负面案例/测试输入。**

## 5. 模块 D：工具审批与 Plugin / MCP

源码：
- [Tool approval verdict](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/loop/workflows/agentic-execution/tool-approval-verdict.ts)
- [Tool type and validation](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/tools/tool.ts)
- [MCP integration package](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/mcp/README.md)
- [Connect registry](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/connect/src/registry.ts)

### 工具审批真实边界

`resolveToolApprovalVerdict` 联合全局 `requireToolApproval`、工具 `requireApproval` 与 `needsApprovalFn`：自定义工具函数存在时，以它为权威取代初始值；策略函数抛异常会退回“需要批准”。`runBeforeApprovalChecks` 会先验证 Tool 输入，并执行 `beforeApproval`；用户 Hook 异常通常不取消随后批准关卡，受框架识别的 FGA 授权拒绝另行上抛。

**不能误抄**：把该库级 “是否需要用户批准” 等同于 Nerelan “是否有 Owner 授权”。尤其不能让 Pack 自定义 `needsApprovalFn=false` 覆盖宿主风险分级、路径授权或 Token/现金边界。Nerelan 的 `host policy` 仍须不可被插件弱化。可借鉴“**先验证参数合法性，再请求人审批**”来避免浪费 Owner 注意力。

### Plugin / MCP 边界

Mastra 具备 `@mastra/mcp` Client/Server，与 Connect 的 Provider 工具目录；而 Nerelan 当前的 `capability_registry.py` 是有意只读 Manifest、不运行第三方插件的轻量边界。

**建议**：
- 继续在 [#253](https://github.com/dddd2024/Nerelan/issues/253) 声明 Pack，使用 [#790](https://github.com/dddd2024/Nerelan/issues/790) 规定的官方 MCP SDK 作为主要协议实现；
- 可以借鉴 Tool input/output Schema、版本化 Provider Tool Catalog、失败和诊断的 UI；
- 不导入 Mastra Core 作为第二个权限、工具或 Workflow Runtime；不运行 Mastra 项目本地 Config 里的任意代码作为插件激活；
- 企业源码 `ee/` 不得作为“开源免费可复制”内容。

**归属**：#253/#789/#790/#303。**优先级 P2**。

## 6. 模块 E：数据集、Scorer、评测过程

源码：
- [Experiment type contract](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/core/src/datasets/experiment/types.ts)
- [Evals package](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/packages/evals/README.md)
- [Evals overview](https://github.com/mastra-ai/mastra/blob/1034a4e41f6a486090e2555d5e1efef696f462e3/docs/src/content/en/docs/evals/overview.mdx)

### 真正可学的设计

- 数据集条目含 `id, input, groundTruth, expectedTrajectory, metadata, requestContext, scorerIds` 等，而不只有 Prompt 与一个分数。
- 工具 Mock 能冻结交互；未 Mock 的工具调用策略单独配置，调用参数不符合 Mock 时判定该条失败。
- Workflow 测试条目允许注入 `resumeSteps` / `resumeData`，方便可重复评估需要审批与恢复的工作流。
- Eval 的采样决定基于 Trace ID（无 Trace 时使用 Run ID）确定性产生，可在不同 Scorer 间保持对应性；若 Trace 整体未被采样，后续评分也可能不执行。
- `experiments / scores` 可独立设置写入与否。但**关闭评测持久化不表示关闭目标 Agent 的内存/追踪副作用，更不构成安全沙箱**；源码有明确警告。

### 对 Nerelan 的差异化判定

Nerelan 已有 TaskStore、验证证据、[#1267 单/多模型比较](https://github.com/dddd2024/Nerelan/issues/1267)、[#1527 Harness×Model 评测](https://github.com/dddd2024/Nerelan/issues/1527)。不能因为 Mastra 有 Dataset + Trace 就建第二个 Eval Backend。

真正值得把它作为测试用例的数据定义补充：`frozen_task_id/base_sha/goal_revision/expected_tool_actions/allowed_paths/cached_tokens/upstream_request_ids/independent_validation_digest/outcome`。可将重复执行和恢复中产生的交互轨迹纳入基准，不只在最终代码上打分。

**优先级：P1 实验记录契约候选、P2 产品 UI。**

## 7. 产品视角：用户能感知的不是“多一个模型选择器”

用户每天会打开 Nerelan，可能是为了看到：

1. **为什么没有直接使用便宜模型**：分类证据不足、任务依赖复杂、额度等待、质量风险，给出有证据的拒绝理由，而不是“AI 自己选了”。
2. **少翻日志**：系统把长工具输出压缩成可恢复引用，必要时点开原始证据；不牺牲故障定位和独立验收。
3. **可审查的等待**：任务因 Tool/Owner 决策暂停时，明确“在等谁、等哪一项决定、批准会授权哪些副作用、恢复以后会怎样”。
4. **用已拥有的额度少浪费**：失败或误路由的额外成本被记录，未来选择靠真实完成质量而不是理论单价。

Mastra 已有 Processor、Agent、Eval、MCP 与模型路由，因此这些功能的名称不是 Nerelan 的独家创新点。必须结合账号池可用性、执行器选择、跨尝试的恢复和独立验收体现真实增量。

## 8. 最小实验与反证条件

| 实验 | 冻结控制变量 | 关注指标 | 失败 / 放弃条件 |
|---|---|---|---|
| Router 降档/弃权 | 相同任务/Model Binding/额度基线；已知复杂任务 follow-up | 分类额外用量、路由误降档、最终独立验收率、接受结果成本 | 分类调用 + 返工成本高于节省，或误降档降低质量 |
| 仅模型视图 Tool 过滤 | 相同工作区/Task，完整证据永存 | tokens/cache_reads、错误文件定位、验收率、工具重读 | 关键证据被藏导致重读或误判 |
| HITL 精确 Resume | 冻结 Approval ID、Goal Revision、Tool Call/Attempt，注入重复/迟到/并发回复 | 一次副作用、拒绝旧权限、可恢复性 | 旧回复能触发新副作用或错误授权 |
| Workflow 故障 | Crash-before/after external dispatch 与 Lease 失效 | 重复 CLI/Reviewer 及工作区身份 | 任一“旧 owner/重复副作用”路径无可靠屏障 |
| 实验重放 | Mock 工具、记录拒绝、固定下游数据 | 复现率、Trace 对应、评估结果 | 无法证明被测试的是相同任务/相同产物 |

真实实验应遵守 Owner 已有账户/成本授权与 #1267 唯一基准 Owner，**本轮没有执行这些测试**。

## 9. 决策摘要

| 模块 | 行动 | 级别 |
|---|---|---|
| Router 的“低置信度弃权 + fallback 不覆盖 + 决策说明” | 在现有 Nerelan Router 做受控对照，不复制 TS Processor | **P1** |
| Model-facing 工具历史过滤 + Objective 稳定投影 | 在已有 Context Packet 上做纯函数探索 | **P1** |
| 评测用 Dataset/Trajectory/Mock/Trace Schema | 复用 #1267/#1527，补对照数据定义 | **P1/P2** |
| Tool Approval Input Validation 与精确恢复身份 | 借鉴流程，Owner 授权仍宿主管理 | **P2** |
| Mastra Workflow engine / Memory / Model Gateway | **不迁移**：重复控制面、语言栈差异、恢复权威风险 | REJECT |
| MCP/Connect | 以官方 MCP SDK + 现有 Pack 扩展为主 | P2 |

**结论**：SELECTIVE_DESIGN_REUSE，重点是可审计的低成本路由弃权、对模型请求的只读 Context 视图以及恢复/测试边界，而非装上 Mastra 或替换 Nerelan 的核心引擎。

## 10. 审计限制和下次查重条件

本次为静态查阅；没有运行 Mastra，未复现 ModelSelection 概率校准和 14%/9% 的经验数据，未验证其完整 Workflow 分布式执行，未运行测试。下次如重新研究 Mastra，必须说明与本文件的**新增文件/模块与技术问题**，不可重复输出相同功能列表。若其他 Agent 先在 Issue/PR 中留下了更细结论，应将本报告降级为历史摘要并引用其来源。

文档 PR 在通过 Nerelan exact-head CI 和独立评审前不是正式已合并技术决策；Issue 只用于研究记录，不授权生产实现。
