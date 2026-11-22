# Paperclip 源码级复用审计（2026-11-16）

> **Status:** SOURCE_REVIEW_ONLY / NOT_IMPLEMENTED / NOT_TESTED  
> **Upstream:** [paperclipai/paperclip](https://github.com/paperclipai/paperclip), commit [`278660149ca6`](https://github.com/paperclipai/paperclip/commit/278660149ca69f0b993195e21c34c5815ec70689)，MIT。  
> **Nerelan baseline:** [`09203bc2762c`](https://github.com/dddd2024/Nerelan/commit/09203bc2762c8c0fd2ca095dd2827e273555d7ec)。  
> **GitHub study tracker:** [#1562](https://github.com/dddd2024/Nerelan/issues/1562)。  
> **Authority:** 研究文档，仅供决策与评审；不授权安装第三方可执行代码、修改生产运行时、创建账户密钥或扩大权限。

## 0. 先查重（为什么此次不是重复研究）

1. `docs/architecture/COMPETITIVE_LANDSCAPE.md` 的 2026-11-08 竞品地图已经收录 Paperclip：目标/角色、任务、审批、预算、统一 UI，并明确不整体替换 Nerelan 的 TaskStore/Coordinator。
2. `docs/radar.md` 将 Paperclip 列为需观察的竞争项目。
3. 复查 `docs/architecture/reuse-study-2026-11-15/README.md`、五个分领域研究和 Nerelan Issues；该批次比较过同类 Agent Runtime、编排与成本工具，但**未定位到 Paperclip 专属、逐源码文件的独立研究记录**。
4. 本次仅深拆过去未充分覆盖的 **Adapter 合同、跨运行工作区、Heartbeat 队列公平性、用量结算与插件加载**。已经存在的功能方向合并到现有 Issue，不另立实施任务。
5. 本次检查采用仓库文件搜索与 Issue 搜索；“未定位到”不等于历史上绝对无人提过。先前聊天中研究过但未落 GitHub 的项目必须标为“待补录”，不能据文件缺失误判为新项目。

## 1. 总体结论

Paperclip 是 Node.js + React 的多 Agent 工作管理平台，不是单一编码 Agent。它支持 OpenCode、Codex、Claude、Pi、Hermes 等多种 Agent，并以任务、组织、审批、Heartbeat 运行、成本和工作区为产品中心。[README](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/README.md)

**结论：SELECTIVE_DESIGN_REUSE，而非集成整个平台。**

- 与 Nerelan 重叠：多执行器、任务队列、预算、授权、隔离工作区、持续执行与恢复。直接接入其控制面会重复任务真相和权限模型。
- 需要提炼的具体小模块：Adapter 环境诊断与结构化结果、远程同步回执、用户可见队列公平性、用量收据及迟到/歧义证据处理、动态插件的能力/信任边界。
- 不能据“它有 Harness 和 Budget”断言 Nerelan 的差异化；要用“质量约束下按任务选择 Agent×模型×现有账户资源，且实际成本可复核”的基准测试证明价值。

## 2. 模块 A：Agent Adapter（P1：薄适配契约）

**源码与文档**
- [Adapter authoring contract](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/docs/adapters/creating-an-adapter.md)
- [Adapter registry](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/adapters/registry.ts)
- [External plugin loader](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/adapters/plugin-loader.ts)
- [Runtime selection](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/heartbeat/runtime-selection.ts)

**源码事实**
- Adapter 接收 `AdapterExecutionContext`（run、agent、session、配置、任务上下文、`onLog`、`onMeta`、`onSpawn`），返回 `AdapterExecutionResult`（退出码、signal、timeout、usage、sessionParams、provider、model、costUsd、clearSession 等）。
- 每个 Adapter 有 `testEnvironment`，返回 `pass/warn/fail`、结构化检查与修复建议；运行时可续接原生 Session。
- 内置 Adapter 包把执行、结果解析、环境诊断、UI 展示分开；外部包需显式导出 `createServerAdapter()`，可提供独立 UI parser。
- `server/src/adapters/registry.ts` 有大量内置类型导入，不能把其维护成本当作“纯插件无需修改”的证明；外部 Adapter Loader 解决第三方增量扩展。

**对照 Nerelan**
- 已有 `reverse_agent/platform_v1/task_runtime.py` 的 `Executor` 协议、`ExecutorResult`、`ExecutorRouter`；`#1527` 要求 Headless、用量与故障分类等。
- 应补：**只读环境预检与兼容性事实**（CLI/版本、模型请求是否忠实、鉴权归属、事件流、Session 恢复、工具权限执法、错误类别），形成运行前可解释的选择拒绝原因。
- 不应补：第二套 Agent Loop、第二套 Credential Store、Paperclip 组织/角色数据库。

**最小建议契约（提案，不是现有 Schema）**
`probe(executor, binding, work_env) -> {supported, reason_codes, capabilities, evidence_digest}`。
Probe 结果不授予权限，也不代替每次运行的现行授权检查。`#1527` 是实施归属。

## 3. 模块 B：Heartbeat、唤醒与队列公平性（P1/P2）

**源码**
- [Run-dispatch ordering](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/heartbeat/queued-run-dispatch-order.ts)
- [Visible queue ordering](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/heartbeat/queued-run-line.ts)
- [Run completion](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/heartbeat/run-completion.ts)
- [Heartbeat internals](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/doc/heartbeat-internals.md)

**源码事实**
- 调度按 `person`、`work`、`recovery`、`recovery_backlog` 分类；人工请求优先；单独保留恢复类调度份额以避免饿死，另有老任务年龄晋升规则。
- 代码常量：`QUEUED_RUN_AGING_MS = 1h`，`OLDEST_DISPATCH_SHARE = 4`，`RECOVERY_DISPATCH_SHARE = 4`；具体保障以就绪条件与开始历史为前提，**不是“所有任务四次内执行”**。
- `queued-run-line.ts` 的注释强调，UI 中排队位置与调度实际使用同一个事实构造器，避免面板展示一套顺序、系统执行另一套。
- Heartbeat 内部文档区分运行终态、agent 状态落库与后续 orphan 恢复；不是“进程退出即全部资源收尾”。

**对照 Nerelan**
- 已有 `unattended_coordinator.py`、TaskStore 原子认领、Continuous Window、`#1508` critical-path / DAG 调度。
- 真正可借鉴：针对持续窗口设计**饥饿防护与统一可见队列语义**；批量恢复不能抢占用户当前等待的重要任务，也不能永远被新任务压住。
- 不应引入第二套 Heartbeat scheduler / Run DB，也不应照抄四次份额阈值；需要依据 Nerelan 的并发限制、账户占用与 DAG 依赖验证参数。

**试验**：模拟人工、自动、恢复三类待运行任务并持续注入新任务；检查有界排队、Critical Path、每账户并发、队列解释一致性；不调用真实模型。

## 4. 模块 C：Remote Workspace“无远端 Git 依赖”规则（P1：安全恢复边界）

**源码**
- [Adapter no-remote-git contract](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/packages/adapters/AUTHORING.md)
- [SSH helper](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/packages/adapter-utils/src/ssh.ts)

**源码事实**
- Paperclip 要求 local execution-workspace `cwd` 是跨运行的持久化交接点，Adapter 不能靠 `git push` / 后续 `fetch` 把运行状态传递到下次 Heartbeat。
- SSH 适配器通过 `prepareWorkspaceForSshExecution` 发出工作副本，`restoreWorkspaceFromSshExecution` 回传变更；即使没有远端 Git origin 仍需工作。
- **回传失败是运行级错误**：标记 `workspace_finalize=failed`，阻止依赖该工作区已更新的后续任务；明确要求不能吞掉错误。
- 相关测试和静态 CI 检查见该文档链接的 `ssh-fixture.test.ts` 和 `check-no-git-push.mjs`。

**对照 Nerelan**
- Nerelan 使用隔离 Git worktree 和 `remote_jobs.py`/远程作业回执；不能默认为所有外部 Executor 已有无损回传。
- 提案：扩展执行器或环境适配契约，明确 `workspace_export_digest`、`remote_result_digest`、`sync_back_status`、`local_head_after_sync`；远端返回“成功”不等于本地工作区已经完成安全合入。
- 冻结下游任务准入直到成功核对可验证的回传或 Git 产物身份；保留冲突与失败证据。不要接管现有 Git 合入与发布门禁。

**试验**：对本地+模拟远端复制进行三轮，强杀在回传前、回传中与回传后，验证无重复写入、失败不会解锁下游。

## 5. 模块 D：用量收据、预算与账单歧义（P1：复用原则，不重建账本）

**源码**
- [Run cost accounting](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/run-cost-accounting.ts)
- [Budget evaluation work](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/budget-evaluation-work.ts)
- [Billing reconciliation](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/billing-reconciliation.ts)
- [Provider-limit wait](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/heartbeat/provider-limit-wait.ts)

**源码事实**
- `run-cost-accounting.ts` 显式处理运行用量收据、重放、迟到证据、原生进程与最终化结果，不仅从最终输出一次性估算。
- `queueBudgetEvaluation` 预期只由**已提交的真实风险敞口变化**触发，先持久化待评估工作、再由专属队列处理。
- 对账遇到无法唯一归属的账单条目不盲目二次扣减，而留待 reconciliation。
- `provider-limit-wait.ts` 对已知额度重置预先延迟普通唤醒，但允许人工、恢复、会话或路由池路径继续尝试；**无重置时间时 fallback 一小时不能作为可靠额度事实复制**。

**对照 Nerelan**
- `reverse_agent/model_access/magpie_usage.py` 已要求正向 request/session 身份、去重、未证实的数量为 UNKNOWN；与 Paperclip 的谨慎结算设计一致。
- 账户池及上游实际错误归属继续由 Magpie、Nerelan 已有 #1342/#1531 和预算控制承担；只借鉴“请求证据到账与预算执行进度分开、晚到可核对、歧义不算零或双重扣费”的证明结构。
- 保留 provider 估价、订阅额度消耗与实际现金支出三种不同口径；不得混成单一伪精确美元指标。

**试验**：构造迟到、重复、跨 Attempt 模糊匹配与真实零用量记录，验证不会重复结算，不会用“无记录”推断无成本。

## 6. 模块 E：插件加载与 UI Parser（P2；有信任风险）

**源码**
- [Plugin loader](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/adapters/plugin-loader.ts)
- [Adapter code policy](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/server/src/services/adapter-code-policy.ts)
- [Creating an adapter](https://github.com/paperclipai/paperclip/blob/278660149ca69f0b993195e21c34c5815ec70689/docs/adapters/creating-an-adapter.md)

**源码事实**
- 外部 Adapter 包可以独立安装，入口导出 `createServerAdapter`；注册表负责实例与 Adapter Type 的检查。
- UI Parser 可以作为 `./ui-parser` 单独导出，并有 `paperclip.adapterUiParser` 版本契约（主版本当前为 1）；Loader 检查解析路径不能跳出包目录。
- Loader 仍会动态加载第三方 JS；Cloud 管理模式禁止随意安装外部 Adapter，并不等同“插件沙箱”。

**对照 Nerelan**
- `capability_registry.py` 目前故意只处理只读 JSON Manifest，不执行外部代码；这是要保留的边界。
- 针对 #253 Pack 与 #789 Hook / #303 Repo Trust，可借鉴**能力发现、组件版本兼容、单独的事件解析展示层**；真正执行插件代码必须经过独立授权和隔离，不应把项目本地配置当作可信插件。
- UI Parser 的可插拔机制对统一展示不同 Executor 的运行日志有帮助，但建议宿主提供受控格式化器或安全纯数据变换，而不是直接在浏览器中运行任意插件脚本。

## 7. 用户价值与差异化反证

Paperclip 已具备“bring your own agent + 任务/组织板 + 心跳唤醒 + 预算 + 审批 + 多适配器”，**不能再把这些功能名本身包装成 Nerelan 特有的竞争力**。

对 Nerelan 较有用的体验应是：在同一任务卡上能看清 `为何等待`、`哪个 Agent/模型可用`、`额度原因`、`远端修改是否回传`、`独立验证结果`、`真实资源消耗是否已结算`。这些事实应来自 Nerelan 原有权威状态，而非插件的自报。

差异化应基于对比实验：多账户资源条件下，以相同冻结任务、独立验收质量约束对比 **每成功交付任务的总资源消耗、恢复损耗与人工接管次数**，不能预先声称 Paperclip 不具备相近能力。

## 8. 决策矩阵

| 模块 | 处置 | 优先度 | Nerelan 归属 |
|---|---|---|---|
| Adapter 环境诊断 + Session/事件能力描述 | 薄契约 + 测试，不移植整套 Adapter | P1 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527) |
| 跨运行工作区同步完成回执 | 只补回执/失败门禁，先看现有远端组件是否覆盖 | P1 | 现有 remote jobs / workspace recovery |
| 队列老任务与人工优先公平性 | 先仿真证伪，不改生产调度器 | P1 | [#1508](https://github.com/dddd2024/Nerelan/issues/1508) |
| 用量收据和模糊归因 | 已有 Magpie 口径；补测试而非新账本 | P1 | [#1342](https://github.com/dddd2024/Nerelan/issues/1342), #1531 |
| 第三方 Adapter 及 UI Parser | 借鉴声明/版本约束；不运行第三方代码 | P2 | [#253](https://github.com/dddd2024/Nerelan/issues/253), #789, #303 |
| Heartbeat / 组织图 / 预算控制面整体移植 | REJECT | — | TaskStore / Coordinator / Magpie 继续唯一权威 |

## 9. 验证计划 / 未完成

尚未克隆/运行 Paperclip；未运行其测试、未验证当前 Windows 机器的兼容性，也未执行上述四项试验。以上为上游源码和 Nerelan 代码的**静态对照结论**，不能作为性能、经济性或可靠性的实验事实。未来实现须首先核查同一功能是否已落在 Nerelan main，遵守 R1/R2/R3 治理规则；若只是重复实现，应关闭提案并引用已有组件。

**复评触发**：Nerelan 出现新的远程执行器/Plugin UI/持续队列饥饿问题，或 Paperclip 发布明确可独立嵌入的组件与稳定 API，才重新评估。
