<!-- RESEARCH_ONLY: no source copied from AGPL upstream, no dependency change. -->
> 研究 Issue [#1625](https://github.com/dddd2024/Nerelan/issues/1625) · [总索引 #1576](https://github.com/dddd2024/Nerelan/issues/1576) · 实施继续归属已存在的 #1508/#1527/#253/#789/#790/#296/#280/#1267/#1531/#1546。

# Pi-Harness 固定版本源码深度调研：Agent 控制层、Plugin、DAG、Replay/Eval 与 Nerelan 对照

> **日期：2026-11-17** · **状态：RESEARCH_ONLY / STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_BENCHMARKED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**  
> **唯一上游：** [wangmiaozero/pi-harness@79adc4318f59b1b2b5b3e38831432cd0ddebb3f0](https://github.com/wangmiaozero/pi-harness/commit/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0)；**Nerelan 对照：** [main@c96732520f3bd5329fc254bc95a91c05768d3ef8](https://github.com/dddd2024/Nerelan/commit/c96732520f3bd5329fc254bc95a91c05768d3ef8)。上游根 `LICENSE` 为 **AGPL-3.0-only**，本次**不复制源码、无直接依赖**，仅分析设计；对 AGPL 衍生/链接/分发的实际适用性需另行评估，不假定与 Nerelan 许可证直接兼容。

## 0. 查重：不是再次调研 Pi/pi-mono

- 检查了研究索引 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)、18 条既有总索引评论、已知源码专项、GitHub `pi-harness`/`wangmiaozero` Issues 与 PR 搜索，未找到独立 Pi-Harness pinned-SHA 研究专项或 Draft PR。
- 现有 [`COMPETITIVE_LANDSCAPE.md:48-58`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/docs/architecture/COMPETITIVE_LANDSCAPE.md#L48-L58) 只将 Pi-Harness 列为**待分诊雷达候选**；不能把一个产品名称候选算成源码深审。
- [Pi/pi-mono 历史研究](https://github.com/dddd2024/Nerelan/issues/1576) 针对 Pi 原生 Agent SDK/RPC/session，不等于 Pi-Harness 的外围管理、Plugin SDK、Recovery 与 Evaluator。本轮不重复 Pi loop 内核的历史研究。
- 不增加新实施 Owner：已有 [#1508](https://github.com/dddd2024/Nerelan/issues/1508) 多 Agent DAG、[#1527](https://github.com/dddd2024/Nerelan/issues/1527) executor×model、[#253](https://github.com/dddd2024/Nerelan/issues/253)/[#789](https://github.com/dddd2024/Nerelan/issues/789)/[#790](https://github.com/dddd2024/Nerelan/issues/790) Pack/Tool/MCP、[#296](https://github.com/dddd2024/Nerelan/issues/296) context、[#280](https://github.com/dddd2024/Nerelan/issues/280) 事件、[#1267](https://github.com/dddd2024/Nerelan/issues/1267) 经济性、[#1531](https://github.com/dddd2024/Nerelan/issues/1531) 成本归因、[#1546](https://github.com/dddd2024/Nerelan/issues/1546) 长任务恢复。

## 1. 可核验的上游设计与隐藏边界

| 模块 | 固定源码证据 | 结论 |
|---|---|---|
| **Agent runtime seam** | [`orchestrator-service.ts:1-75`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L1-L75)、[`agent-runtime-service.ts`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/agent/agent-runtime-service.ts)、[`pi-rpc-runtime.ts`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/agent/pi-rpc-runtime.ts) | `OrchestratorHost` 作为可注入宿主接口承载 Session/Prompt/Event/Artifact，但真正执行 Pi 原生 session，**不是 OpenCode/Codex/Claude 通用 Harness 运行时**。Nerelan 可借鉴 Host contract，不应放弃多执行器。 |
| **DAG schedule** | [`task-scheduler.ts:1-108`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/task-scheduler.ts#L1-L108)、[`orchestration-store.ts:1-115`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestration-store.ts#L1-L115) | 纯确定性依赖解析 + manual/sequential/dependency 策略、priority、agent/run 双并发上限、一 agent 一次一 run。持久模型是单个版本化 JSON Store，**不是跨进程 TaskStore/CAS/lease authority**。 |
| **Restart Recovery 的边界** | [`orchestrator-service.ts:569-625`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L569-L625)、[`orchestrator-service.test.ts:916-934`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.test.ts#L916-L934) | 重启后将 running/verifying/review task 置为 pending，编排置 paused，手动 resume 后可再次派发。同一 task 外部副作用是否已发生不由这个函数证明；**适用于人机交互，不符合 Nerelan 无人值守自动安全续跑**。不能照抄。 |
| **Context/handoff** | [`task-context-builder.ts:1-80`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/task-context-builder.ts#L1-L80)、[`handoff-service.ts:28-65`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/handoff-service.ts#L28-L65) | 明确取父任务/依赖结果、最多 8 件 artifact、限制文本预览、记录 handoff 的 from/to/task/artifact ID，避免把所有历史塞进 Prompt。**预览/ID 不自动等于内容哈希和冻结可复现证据**，Nerelan 应保留原证据与受限 model-facing projection 分层。 |
| **Review gate** | [`orchestrator-service.ts:1211-1265`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L1211-L1265)、[`task-context-builder.ts:200-215`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/task-context-builder.ts#L200-L215)、[`orchestrator-service.ts:1362-1411`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L1362-L1411) | reviewer 可通过文本 `[REVIEW: APPROVED]` 标记，parse 使用正则；显式 `reviewAgentId` 路径中未见强制与 producer 不同，亦无 Nerelan exact-head hash / independent context proof。只能当 UI/工作流示例，**不能当 Nerelan 独立发布许可**。 |
| **插件安装与授权** | [`plugin-registry.ts:24-71`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/plugins/plugin-registry.ts#L24-L71)、[`#L100-L167`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/plugins/plugin-registry.ts#L100-L167)、[`plugin-host.ts:278-336`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/plugins/plugin-host.ts#L278-L336) | Manifest schema/version、无符号链接读取、哈希绑定安装内容、先安装但默认 disabled、原生批准、批准后再次校验 digest，再启动 worker。可借鉴 **manifest→install receipt→grant→activate** 状态机，但必须自设计避免 TOCTOU，并放在 Nerelan 权限源下。 |
| **插件 worker 与副作用边界** | [`process-host.ts:25-137`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/plugins/process-host.ts#L25-L137)、[`plugin-host.ts:355-444`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/plugins/plugin-host.ts#L355-L444)、[`docs/plugins/security.md:3-42`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/docs/plugins/security.md#L3-L42) | 最多 8 active / 每插件 64 queued events / 2 pending RPC / 2s per-call / 256KiB reply / depth 12；事件满时**丢弃**，所以插件投影绝不能作为可靠审计日志。单独 Node utility process 不是 OS Sandbox；已批准的 Node 代码仍有文件/网络/进程权限。 |
| **Trace Replay vs actual rerun** | [`replay-service.ts:27-66`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/replay/replay-service.ts#L27-L66) | `buildReplay` 是 recorded trace 或 session JSONL fallback 的**可视化重放**，不是模型无副作用确定性重执行；恢复、分析与真实重新运行必须分开命名。 |
| **Evaluation** | [`evaluation-service.ts:100-150`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/evaluation/evaluation-service.ts#L100-L150)、[`#L214-L265`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/evaluation/evaluation-service.ts#L214-L265) | 基于运行时 entries 提取已执行 test/lint/typecheck/build 的证据，再组合 fast/standard/strict 评估 stage；**不是自动在受控新环境重新执行全部测试**，不能直接替代 Nerelan 的独立检查和评审。 |
| **Budget / UNKNOWN** | [`run-registry.ts:615-653`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/runs/run-registry.ts#L615-L653)、[`orchestrator-service.ts:1510-1549`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L1510-L1549)、[`#L1614-L1626`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/src/main/harness/orchestrator/orchestrator-service.ts#L1614-L1626) | 单 Run 的成本判断 `usage.estimatedCost ?? 0`；编排的 `estimatedCost=null` 不触发 maxCost 条件。**未知不能证明零**，Nerelan 应继续使用 Magpie Request-level 证据并对 UNKNOWN 单独决策，不能复制这个 fail-open 行为。 |
| **License** | [`LICENSE`](https://github.com/wangmiaozero/pi-harness/blob/79adc4318f59b1b2b5b3e38831432cd0ddebb3f0/LICENSE) | AGPL-3.0-only：不建议从中直接移植源代码/内部 SDK；可独立实现机制、做非代码的产品参考或在明确许可分析后决策依赖。 |

## 2. Nerelan main 已有与新增价值（用户视角 + 开发视角）

| Nerelan 模块/事实 | 四分类 | 此轮可以“抄”的最小设计 / 不应该做的事 | 唯一 owner |
|---|---|---|---|
| 已有 [`ExecutorRouter`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/task_runtime.py#L511-L555) + [`team_graph.py`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/workflows/team_graph.py#L1-L98)；不仅 Pi / OpenCode | **ALREADY_REUSED / BORROW_PATTERN** | 可选调度策略和能力/占用快照的可解释出队视图；不要换成 Pi-only 主 Agent loop，也不要创建新 scheduler authority | #1508 / #1527 |
| [`control_store.runnable_tasks`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/control_store.py#L1104-L1175) + [`unattended_coordinator.reconcile`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/unattended_coordinator.py#L199-L224) 已有 SQLite 租约/claim | **ALREADY_REUSED / REJECT 替代** | 参考用户可见的 dependency-ready/blocked 原因；不使用 JSON store 的 paused/manual restart 取代持续运行、DBOS spike 或 Host lease | #1508 / #1546 |
| [`run_read_model.py`](https://github.com/dddd2024/Nerelan/blob/c96732520f3bd5329fc254bc95a91c05768d3ef8/reverse_agent/platform_v1/run_read_model.py#L628-L660) 是运行投影 | **BORROW_PATTERN** | Run → Trace → Artifact → Eval → Dependency 的 UI 链路，含异常解释与 replay；但展示层不是审计真相，必须由 TaskStore/原生证据重建 | #280 / #260 |
| Pack、MCP、Hooks 已由 #253/#789/#790 规划 | **BORROW_PATTERN** | 分离不可执行的**声明式团队模板**和需要原生信任批准的**可执行扩展**；Manifest + grant + digest + actor/session scope + 只读事件投影。绝不照搬 Node process 为沙箱，不准 plugin exporter/evaluator 控制发布 | #253 / #789 / #790 / #299 |
| 上下文/跨 Agent 结果交接 | **BORROW_PATTERN** | 采用显式 dependency result + artifact references + bounded preview；加 Nerelan 原始证据 hash/权限/时效与 ContextBuilder 分层，避免上下文膨胀和隐式串会话 | #296 / #1508 |
| 成本/预算与路由由 Magpie + Nerelan 分工 | **REJECT 上游预算权威** | 不把估算费用 NULL 当零，不建第二账户管理或 Token 账本；增加 UNKNOWN 的 UI 说明并按真实 Task 结果测成本 | #1531 / #1342 / #1267 |
| 审评与发布 | **REJECT 上游 verdict authority** | 可借 reviewer UI 与状态流，但必须保留 frozen exact-head diff、不同审查上下文/模型家族、CI、Host evidence marker 和 publish gate | #791 / #1508 |

**推荐顺序：** P1 上下文交接 receipts + plugin manifest/grant 状态（先 provider-free 反例），P1 run lineage/traces UI 与可解释等待，P2 多调度策略。P0 连续运行中 stalls、429、超时、未知用量仍优先。本轮没有证据证明 Pi-Harness 比 Nerelan 更稳定/便宜。

## 3. 可证伪的最小验证（本研究不执行；交由已有 implementation owner）

1. **Plugin-1 / 文件替换、授信与权限** (#253/#789/#790/#303)：构造同 ID manifest/entry 更新、审批过程中替换内容、symlink/hardlink、非预期 MCP 工具路径；digest/身份/权限变更后阻断执行。未获得强 sandbox 则强隔离要求 fail closed。
2. **Plugin-2 / Event loss** (#280)：输出 1000 条事件、subscriber 停顿、重启/取消/越权 filter，展示投影可以丢，但 TaskStore 原始 run/permission/usage/audit receipts 不丢；前端不得声称事件无缺失。
3. **DAG / Recovery crash matrix** (#1508/#1546)：Agent 已写文件但 settle 未存、review 已输出但 claim 丢失、旧线程重入，验证 epoch/effect key 去重 + UNKNOWN/PARK；不能像上游一律 pending 然后重发 prompt。
4. **Context/Artifact handoff** (#296/#1508)：父任务 12 个 artifact，含过期/修改/高敏信息；子任务仅收到已授权 preview+hash/id，独立读取冻结内容，禁止跨 Task 原始密钥泄漏；测 tokens+验收率而非只测长度。
5. **Review forgery** (#791/#1508)：Review 文本含伪造 `[REVIEW: APPROVED]`、和作者同一 context，或在 head 更新后重放；只有 Nerelan frozen head + trusted verdict 才授权发布。
6. **Cost UNKNOWN / Agent×Model economics** (#1531/#1267/#1527)：在 mock gateway 缺报价、成本迟到、0 成本与 UNKNOWN 混合，限制预算不得将 UNKNOWN 计零；固定实际任务同验收 compare 单/多 Agent 与 reviewer/返工成本，若净成本增或成功率降则 NO-GO。

## 4. 最终判断与执行边界

**SELECTIVE_DESIGN_REUSE / NOT_A_RUNTIME_REPLACEMENT.** 最大价值是模块边界与 UI 信息架构：`Host Adapter + deterministic scheduler + bounded handoff + advisory plugin + replay/read model`。**不能照抄** AGPL 程序、Pi-only runtime、JSON Store 恢复、插件 Node 伪沙箱、文本 review verdict 或 UNKNOWN cost=0。尤其 Nerelan 长期目标是无人工反复确认地把真实任务安全完成：上游以人为中心的 paused recovery 与受控自动恢复目标不同。

本研究所有结论为 **pinned static source findings**，没有安装第三方二进制，没有 Windows/Electron 实跑、没有供应商 API、没有经济性对照、没有 CI/独立评审通过。研究创建的文档 Draft PR 会与本 Issue、#1576 双向登记；唯一实施 owner 保留既有 Issues。


## 5. 代码与许可复核要点

- 本研究仅链接 Pi-Harness 固定源码位置，未复制其 AGPL 源码或组件入 Nerelan；无需新 runtime/plugin manager。实际许可相容性不是此静态报告的法律意见。
- 实施指标应为独立验收成功任务 / 全成本 / 失败恢复正确性，而非单看功能数量。每项潜在复用以 Nerelan 的已有 Issue 为实施 owner，先以 Provider-free fixture 证明缺口，随后再真实对照。
- 研究稿保留为 docs-only Draft PR；在 exact-head CI 和独立评审前不得认定 main 已采用。
