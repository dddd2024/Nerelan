# Nerelan 开源项目深度调研：统一汇总与复用决策（2026-11-16）

> **统一研究总入口：** [GitHub Issue #1576](https://github.com/dddd2024/Nerelan/issues/1576)（CANONICAL_RESEARCH_HUB）
> **文档性质：** R1 研究/架构导航；不是实施批准、不是审查结果、不是证明某组件已在 Nerelan 运行。
> **依据：** 当前 `main` 已有 2026-11-15 [横向研究](../reuse-study-2026-11-15/README.md)，以及 2026-11-16 六份专项研究 Issue 和 Draft PR。**截至汇总核验，六个专项 PR 均 open/draft/not merged**。本汇总新增时也应保持 Draft 直到 CI 与独立评审通过。
> **口径：** “调研过”≠“代码复用”≠“可重复实验确认”≠“功能已部署”。所有未做的测试必须写为未验证。

## 1. 研究版图：一份横向覆盖，六份源码深拆

### A. 约 30 个成熟项目/组件的横向研究（已位于 main）

这里的“约 30 个”是 2026-11-15 总报告的原有表述；它把一个项目在多领域出现的重叠以及部分商业产品列为对照。**不是约 30 个已完成独立源码深拆的断言**。

| 研究分区 | 参考材料 | 代表性项目及原有判断 |
|---|---|---|
| 多账户/网关 | [A-pooling.md](../reuse-study-2026-11-15/A-pooling.md) | Magpie 为既有基础；one-api/new-api/LiteLLM/Portkey/CLIProxyAPI/sub2api 是错误处理、配额和路由设计参考，不推荐第二网关 |
| 持久执行 | [B-durable.md](../reuse-study-2026-11-15/B-durable.md) | 现有 LangGraph；DBOS 是需实证的候选，Temporal/Restate/Hatchet/Prefect 提供租约、Heartbeat、Recovery 的取舍 |
| 执行器 | [C-runtimes.md](../reuse-study-2026-11-15/C-runtimes.md) | OpenCode/Codex CLI/Claude 等现有或候选执行器；OpenHands/Goose/Gemini CLI/Cline/Roo/Aider/SWE-agent 等作为能力比较 |
| 编排与审查 | [D-orchestration.md](../reuse-study-2026-11-15/D-orchestration.md) | OpenHands resolver、PR-Agent、AutoGen/AG2、CrewAI、MetaGPT、Open SWE；重点是评审回合、剩余缺陷、复核独立性 |
| 成本/观测 | [E-cost-ops.md](../reuse-study-2026-11-15/E-cost-ops.md) | Langfuse、Helicone、OTel GenAI、LiteLLM Spend；按真实请求证据而非估计收费，不新建一个数据平台 |

对这份 11/15 报告的旧实测、版本与代码行数应按**写作日的历史快照**使用；后续是否实施需要查当前 `main`，不能直接把历史缺陷当作现在尚未解决。

### B. 六份源码深拆（均已在 GitHub 留档，均未运行集成实证）

| 项目 | 研究范围 / 版本 | 研究 Issue | 专项报告（**PR 分支，尚未合并**） | Draft PR |
|---|---|---|---|---|
| **Paperclip** | Executor Adapter、队列公平、工作区回传、Plugin、预算；`27866014` | [#1562](https://github.com/dddd2024/Nerelan/issues/1562) | [paperclip.md](https://github.com/dddd2024/Nerelan/blob/agent/paperclip-deep-reuse-20261116/docs/architecture/reuse-study-2026-11-16/paperclip.md) | [#1563](https://github.com/dddd2024/Nerelan/pull/1563) |
| **Mastra** | 模型选择弃权、Model-facing Processor、Workflow Lease、Tool Approval、Eval；`1034a4e4` | [#1564](https://github.com/dddd2024/Nerelan/issues/1564) | [mastra.md](https://github.com/dddd2024/Nerelan/blob/agent/mastra-deep-reuse-20261116/docs/architecture/reuse-study-2026-11-16/mastra.md) | [#1565](https://github.com/dddd2024/Nerelan/pull/1565) |
| **Composio** | Tool/Account Session、MCP vs SDK Hook、工具批量副作用、外部收费；`c59c2db8` | [#1567](https://github.com/dddd2024/Nerelan/issues/1567) | [composio.md](https://github.com/dddd2024/Nerelan/blob/agent/composio-tool-integration-20261116/docs/architecture/reuse-study-2026-11-16/composio.md) | [#1568](https://github.com/dddd2024/Nerelan/pull/1568) |
| **Kubernetes SIG Apps Agent Sandbox** | Sandbox/Claim/WarmPool、Router、K8s 网络隔离、回收；`454d3353` | [#1569](https://github.com/dddd2024/Nerelan/issues/1569) | [agent-sandbox.md](https://github.com/dddd2024/Nerelan/blob/agent/agent-sandbox-source-audit-20261116/docs/architecture/reuse-study-2026-11-16/agent-sandbox.md) | [#1570](https://github.com/dddd2024/Nerelan/pull/1570) |
| **Dify Plugin Daemon** | Manifest、签名/安装、Python 子进程/环境白名单、反向宿主调用；`1fa10988` | [#1571](https://github.com/dddd2024/Nerelan/issues/1571) | [dify-plugin-daemon.md](https://github.com/dddd2024/Nerelan/blob/agent/dify-plugin-daemon-audit-20261116/docs/architecture/reuse-study-2026-11-16/dify-plugin-daemon.md) | [#1572](https://github.com/dddd2024/Nerelan/pull/1572) |
| **Bifrost** | Provider FailureClass、请求级 Key Retry/Trail、Session Affinity/Cost；`31c9e762` | [#1573](https://github.com/dddd2024/Nerelan/issues/1573) | [bifrost.md](https://github.com/dddd2024/Nerelan/blob/agent/bifrost-gateway-audit-20261116/docs/architecture/reuse-study-2026-11-16/bifrost.md) | [#1574](https://github.com/dddd2024/Nerelan/pull/1574) |

**查重原则**：Paperclip/Mastra/Composio 采用连续依赖的堆叠 Draft PR（#1563→#1565→#1568），后面三项从 main 各自开分支。每一份 PR 当前都不是已合并的研究文件。不能以本汇总代替它们自己的 CI/Review。

### C. 已在历史聊天中讨论过、正式深拆证据待核对的项目

Cline/Roo、Pi/pi-mono、Letta Code、Plandex、OpenClaw、Continue、Deep Agents、Pydantic AI、FastMCP、Orchestrator.inc、Hermes Agent、Qwen Code，以及上述横向研究中出现的其他项目。

这些名字应标记为 `TOUCHED_OR_DISCUSSSED / PROVENANCE_PENDING`，**不得**因为本表没有单独报告就重新研究同一模块；先复查旧聊天、GitHub Issues/PR、提交历史与最近上游变更，确定真正新增问题。

### D. 其他对话的**历史研究完整导航**（已归档）

**[历史跨对话研究归档目录](history/INDEX.md)** 已单独补齐研究条目：六份逐项目历史档案（Cline/Roo、Pi、Letta Code、Plandex、OpenClaw、Hermes Agent）与 [13 项其它执行器/框架源码研究](history/other-runtime-frameworks.md)。各项目都有可恢复的旧对话范围、源码提交或本次核验快照、具体模块/路径、借鉴与拒绝、现有实施 Issue、证据等级和待验证反例。

| 历史深入研究 | 逐项目 GitHub 归档 | 历史与源码证据 |
|---|---|---|
| Cline / Roo | [cline-roo.md](history/cline-roo.md) | Cline 新核旧稿缺失 SHA；Roo 独立版本未恢复 |
| Pi / pi-mono | [pi.md](history/pi.md) | 原研究 `22fc026b`；JSONL RPC / `agent_settled` 真实源码已核 |
| Letta Code | [letta-code.md](history/letta-code.md) | 原研究 `eadef1c`；Git Memory/Reflection/Handoff 文件已核 |
| Plandex | [plandex.md](history/plandex.md) | 旧 SHA 丢失，本次用 `e2d77207` 补核，不冒称原版本 |
| OpenClaw | [openclaw.md](history/openclaw.md) | 原研究 `02dc185`；Harness 能力、Manifest Activation 已核 |
| Hermes Agent | [hermes-agent.md](history/hermes-agent.md) | 原研究 `e96221fa`；Kanban/Skills 已核；此前口头“GitHub 已保存”无实际旧 PR 证据 |

13 项其他历史研究：OpenCode、Codex、OpenHands SDK、Gemini CLI、Goose、Continue、Aider、mini-SWE-agent、Qwen Code、Deep Agents、Pydantic AI、FastMCP、Orchestrator.inc。原 `block/goose` 已迁移 `aaif-goose/goose`；Orchestrator.inc 源码身份为 `OrchestratorInc/agent-orchestrator`，历史 SHA 均已验证。

**准确证据等级：** 本目录已经将**可恢复**的旧研究内容归档为文档，但旧聊天完整逐字文本、稳定对话 URL、部分项目的原 SHA 或曾声称存在的独立研究 PR 无法据现有记录证明；已在各文件标注 `PROVENANCE_GAP`。这里的历史归档不是六份新独立源码 PR，也不计为实测或实现。

## 2. 模块级决策：Nerelan 应该“抄什么”

表中“借鉴”是设计证据或未来对照实验；目前没有从本轮六份源码报告获得正式运行效果证明。

| 模块 | 已有权威/基础 | 源码带来的具体新增机制 | 可复用判定 | 最先验证什么 |
|---|---|---|---|---|
| **模型与订阅账户** | Magpie Gateway、Quota、Group、`stays=auto`，[#1342](https://github.com/dddd2024/Nerelan/issues/1342) | Bifrost 区分 `quota` / `rate_limit` / `model_access` / `credential` / `transient`，且跨模型影响范围不同 | **BORROW_PATTERN；部分 ALREADY_REUSED** | 429/402/403/529 真实拒绝日志回放；无暗中 900 秒无效等待（[#1530](https://github.com/dddd2024/Nerelan/issues/1530)） |
| **真实成本/预算与任务归因** | Magpie 请求用量与已有结算实现，[#1531](https://github.com/dddd2024/Nerelan/issues/1531) | Bifrost `attempt_trail`、Paperclip 收据归因，缺失费用保持 UNKNOWN | **BORROW_PATTERN，拒绝第二账本** | Gateway Request vs Key Retry vs Executor Attempt；晚到/重复数据不被双重结算 |
| **Executor Adapter** | `ExecutorRouter`、OpenCode/Codex/Claude 等现有适配器，[#1527](https://github.com/dddd2024/Nerelan/issues/1527) | Paperclip `testEnvironment` 前置能力探测、Runner 事件结构、工作区回传收据 | **BORROW_PATTERN；不引入第二 Agent Loop** | 同任务不同 Executor×Model 的通过率、恢复能力、真实成本 |
| **任务难度与模型选路** | Nerelan 路由策略 + Magpie Account Pool，[#1267](https://github.com/dddd2024/Nerelan/issues/1267) | Mastra 分类置信度不足时弃权；仅分析最新 User Text 是反例 | **BORROW_PATTERN** | 分类调用/模型切换成本是否小于经独立验收的节省 |
| **上下文与记忆** | 现有 Context Builder/Optimization，[#296](https://github.com/dddd2024/Nerelan/issues/296) | Mastra 的临时 Model-facing 工具日志投影、Goal 缓存键与撤回 | **BORROW_PATTERN** | 完整 Evidence 不变的条件下，减少 Token 是否仍能定位关键错误 |
| **Pack 与工具系统** | 只读 `capability_registry.py`、[#253](https://github.com/dddd2024/Nerelan/issues/253)、[#789](https://github.com/dddd2024/Nerelan/issues/789)、[#790](https://github.com/dddd2024/Nerelan/issues/790) | Dify 的校验/安装/Ready 生命周期与反向 LLM/Tool Gate；Composio SDK Modifier 对 Hosted MCP 无效 | **BORROW_PATTERN；后端仍由宿主管** | 任意 SDK/MCP 路径是否可绕过 Owner Policy；第三方模型调用是否可归入 Magpie |
| **Sandbox/不可信执行** | Host-Workspace-Sandbox 原有要求，[#299](https://github.com/dddd2024/Nerelan/issues/299) | Kubernetes Claim UID/Generation/Policy/Cleanup；Router 默认 AllowAll、公网默认 Egress 是反例 | **CONDITIONAL_BACKEND；不强推 K8s** | 真正强隔离门槛、网络、身份与重启/清理证据，Windows local-first 仍可用 |
| **持久执行/审批** | LangGraph、TaskStore；DBOS 实证 [#1546](https://github.com/dddd2024/Nerelan/issues/1546) | Mastra Workflow Lease 不天然 Fencing 全部 Writes；Composio 混合 Batch 在审批前可能部分执行 | **BORROW_NEGATIVE_TESTS；拒绝第三引擎** | Crash/旧 Owner/重复审批/外部副作用重放 |
| **产品体验/可解释性** | [#1561](https://github.com/dddd2024/Nerelan/issues/1561) | Paperclip 的队列/可执行原因；Dify 安装状态；Composio 凭据 Scope；Bifrost 重试理由 | **BORROW_UX** | 用户能否准确得知等待原因、许可账户、花费、处理建议，无需查长日志 |

## 3. 已有与暂不复用：节省研发和维护成本的红线

- **ALREADY_REUSED/OWNER**：Magpie 管多订阅/APIs/账户级路由、额度和请求观察；LangGraph 已存在；OpenCode 是现有主执行器；TaskStore 是持久目标/证据事实；`capability_registry.py` 已是只读 Pack 元数据来源。
- **不新增**：Bifrost/LiteLLM/Composio 的第二模型网关与账户迁移；Paperclip/Mastra/Dify 的完整 Agent/Workflow/Plugin Daemon；第二套消费账本；一套为可选 K8s Sandbox 强制依赖的本地产品安装栈。
- **安全边界**：Plugin Manifest / 包签名 / Python 子进程 ≠ OS Sandbox；MCP 服务端策略 ≠ SDK Hook；Tool Approval Pending ≠ 子操作尚无副作用；模型价目表 ≠ 真实订阅现金开销。
- **产品核心差异**：受授权的账户资源统一使用、任务拆分、合适的 Harness×Model 能力路由、额度不足后保留既有工作、独立验收、**每个成功任务的真实经济性**。六轮研究不证明这些目标已经完成。

## 4. 具体待验证工作按风险优先级汇总

| 顺序 | 课题 | 不需要真实模型的第一轮测试 | 否决门槛 / 终止条件 | 原实施入口 |
|---|---|---|---|---|
| **P0-1** | 网关错误分类和请求级终止 | 真实拒绝文本的离线 Fixture：400 credits、429 rate_limit/insufficient_quota、403 model denied、529 overloaded | 相同耗尽账户持续重试或把服务故障当凭据永久失败 | [#1530](https://github.com/dddd2024/Nerelan/issues/1530), #1342 |
| **P0-2** | 用量归因和未知成本 | Gateway Request、内部 Retry、Attempt、Session 交错的假日志 | 错误归因、重复扣费、缺字段变成零 | [#1531](https://github.com/dddd2024/Nerelan/issues/1531), #1342 |
| **P0-3** | 插件/MCP 授权与副作用 | SDK/Hosted MCP 路径替换、假 LLM 反向调用、审批前子操作已完成 | 任一路径越权或在恢复后重复不可逆动作 | [#790](https://github.com/dddd2024/Nerelan/issues/790), #789, #299 |
| **P1-1** | Harness×Model 真实效率 | 冻结同任务、同验收门槛；先测只读/离线基准设施 | 无明确节省且质量下降，不启动迁移 | [#1527](https://github.com/dddd2024/Nerelan/issues/1527), #1267 |
| **P1-2** | Context 的成本/质量 | 完整证据恒定，对比 Tool History 摘要模型视图 | 误丢关键日志、返工开销超过 Token 节约 | [#296](https://github.com/dddd2024/Nerelan/issues/296) |
| **P1-3** | 远程恢复/安全隔离 | Claim UID/Generation、Sandbox Ready vs Task Done、Policy 修改、假资源清理 | 无授权重接管、未经证实强隔离、资源泄漏 | [#299](https://github.com/dddd2024/Nerelan/issues/299), #1546 |

**时间顺序说明**：这里是模块风险排序，不代表这些问题目前仍未解决或尚未在其他分支开发。正式开工前必须重新读取最新 main、Owner 决策和对应 Issue，不得以 11/15 的历史快照决定实现。

## 5. 研究管理：总入口、专项证据与实现任务三层关系

```text
GitHub Issue #1576              ← 唯一研究总入口：项目/模块/优先级/状态/去重
    ├── 11/15 横向研究 A–E      ← 已在 main 的已有证据，约 30 个项目/组件
    ├── #1562 Paperclip         ← 深拆证据，Draft PR #1563
    ├── #1564 Mastra            ← 深拆证据，Draft PR #1565
    ├── #1567 Composio          ← 深拆证据，Draft PR #1568
    ├── #1569 Agent Sandbox     ← 深拆证据，Draft PR #1570
    ├── #1571 Dify Daemon       ← 深拆证据，Draft PR #1572
    └── #1573 Bifrost           ← 深拆证据，Draft PR #1574

已有实施 Issues（#1342、#1530、#1531、#1527、#1267、#296、#253、#790、#299、#1546 ...）
    ↑ 研究引用它们作为唯一实施 Owner，不因研究创建重复平台模块
```

### 新一轮调研必须先做

1. 查 **#1576**、已有横向研究与当前研究 Draft 分支索引，再搜 GitHub 最近 Issues/PR/代码/提交和历史聊天；把已横向触及和真正的专项源码深拆区分。
2. 每轮只选**一个**项目，定义本次新增源码问题/模块，固定上游 SHA、来源、许可、商业限制。
3. 读取 Nerelan 当前 `main` 的同类代码/Issue；一项项判断 `ALREADY_REUSED / DIRECT_REUSE / BORROW_PATTERN / REJECT`，识别额外依赖、安全风险与用户体验。
4. 写出可证伪实验、成本/风险阈值和拒绝条件；无运行测试就标记 `STATIC_SOURCE_REVIEW`。
5. 维护 **一份专项 Research Issue、一份 docs-only Draft PR 与 #1576 汇总记录**；新研究优先加主 Issue 一条评论/更新清单，而不是再造新的总索引或重复实现 Issue。
6. 每份 PR 从当前 main 建分支、遵守 [AGENTS.md](../../../AGENTS.md)；CI `baseline`、`state-gate` 与独立 exact-head Review 未通过时不得合并；这次汇总不授予任何外部模型调用、R3 或部署授权。

## 6. 尚未关闭的仓库文件/PR 依赖

1. **旧统一查重索引是待合并内容**：[`REUSE_RESEARCH_INDEX.md`（Composio 研究分支）](https://github.com/dddd2024/Nerelan/blob/agent/composio-tool-integration-20261116/docs/architecture/REUSE_RESEARCH_INDEX.md) 通过 #1563 → #1565 → #1568 继承；目前 main 还不存在该文件。
2. #1570/#1572/#1574 是另三个独立从 main 建立的 Draft PR；它们分别在 `COMPETITIVE_LANDSCAPE.md` 增加索引行。合并多个 PR 可能需要同步 base/解决冲突；不能通过汇总报告跳过各 PR 的审查与合并。
3. **本文件是综合决策摘要，不是与 `REUSE_RESEARCH_INDEX.md` 同功能的第二个长期“逐项目查重索引”**。待其正式合入 main 时，按 #1576 的记录补录 #1569/#1571/#1573 与本汇总链接；以后项目查重以 #1576 + 已合并索引 + 最新 Issues/PR 为准。
4. 旧研究 Issue #1562 仍只代表 Paperclip 专项；其评论可导航到 #1576，不能再称其为唯一总入口。

## 7. 汇总结论

**Nerelan 当前不是缺所有基础组件，而是需要将现有 Magpie、Agent Executors、TaskStore、已有恢复/验证机制真正联通并获得实证。** 本轮六个项目的价值最大部分是**较小的、可以用负面测试验证的机制**：错误类别→正确重试与冻结，模型/账户尝试真实归因，失败后安全恢复，工具授权不能跨 SDK/MCP 绕过，插件能力不能越过宿主额度，沙箱身份/权限/清理被证实。

后续如果发现这类能力已由 Magpie/现有库实现，应优先**激活和验证**，而不是因发现了一个优质开源仓库就将其整个引入。任何“节省成本”必须经质量一致的、可复现的 Harness×Model 实验且以独立验收完成的任务为分母证明。
