# 竞品与复用地图

记录与 Nerelan 功能重叠的开源项目、我们复用或借鉴了什么、为什么不整体替换，以及什么情况下要重新评估。
[竞品雷达](../radar.md) 每周把新发现交给分诊任务，由它更新本文件。

初版来自 Owner 2026-11-08 的竞品调研；仓库名与 star 数在同日通过 GitHub 核对，其余能力描述来自各项目
公开文档，未在本地实测。

## 定位

Nerelan 要坚持的差异化：在授权范围内，综合任务能力、账户额度、执行成本和失败状态，长期运行真实开发
任务，并以可审计证据证明结果正确的本地优先平台。功能名称上的重叠不说明谁更强；差距在生产级实测证据。

## 项目

| 项目 | 仓库 | 重叠 | 处置 | 我们用了什么 | 为什么不整体替换 | 何时重新评估 | 上次检查 |
|---|---|---|---|---|---|---|---|
| Paperclip | `paperclipai/paperclip` | 高：目标拆解、角色层级、任务委派、审批、预算暂停 | 对标产品体验 | 无代码复用；作为任务、状态、预算统一展示的对照 | 引入它的调度器会形成两套任务真相和审批语义，与 TaskStore、Coordinator、授权快照冲突 | 它支持外部调度器接管任务状态，或提供可嵌入的组织/预算视图组件时 | 2026-11-08 |
| Orca | `stablyai/orca` | 高：编码 Agent 工作台、Git worktree、Codex/Claude 多账户切换 | 借鉴 UI，独立试用 | 无 | 它的账户切换是人工选择；Nerelan 需要按任务、额度和能力自动选择并判断能否安全启动。与 Magpie 同时管理账户会造成归因不一致 | 它支持按任务自动选账户，或开放账户状态接口时 | 2026-11-08 |
| Magpie | 本机 `F:\magpie` | 高：同服务账户切换、额度等待、请求重试 | 已复用，作为账户层 owner | 账户池、额度窗口、模型网关（`fetch_magpie_snapshot`） | 已是复用对象；Nerelan 只保留任务级能力匹配、周配速和授权边界 | 路由归属验收（见下）完成后，决定本地哪些路径降为 fallback | 2026-11-08 |
| OpenBot | `CopilotKit/OpenBot` | 中高：隔离浏览器与文件环境、工具调用前后的权限网关、AG-UI | 研究可插拔执行层 | 无 | Beta 阶段，需要自带服务、数据库和执行环境；整套移植会让它接管任务状态 | 核心任务闭环通过后，评估把隔离浏览器作为可选工具，由宿主做权限决策 | 2026-11-08 |
| Rulesync | `dyoshikawa/rulesync` | 中：统一生成各 Agent 的配置 | 小规模验证后复用 | 无 | 不能让它成为第二套治理真相；`AGENTS.md` 仍是权威 | 需要为多个执行器维护同一套非权威指令时 | 2026-11-08 |
| Agent-Native | `BuilderIO/agent-native` | 中：Agent 与 UI 共用操作接口 | 借鉴 Action 设计 | 无 | 是应用框架，不是调度或治理层 | 前端操作需要同时暴露给 Agent 时 | 2026-11-08 |
| OpenHands | `OpenHands/OpenHands` | 中：Agent 工作台 | 已复用前端框架 | 侧栏与工作台框架，见 `frontend/OPENHANDS_REUSE_MAP.md` | 只复用 UI，不复用其运行时 | 其前端组件大版本变化时 | 2026-11-08 |
| LangGraph | `langchain-ai/langgraph` | 低：图式工作流 | 已复用 | 团队图与开发图 | 已是依赖 | 大版本或检查点格式变化时 | 2026-11-08 |
| OpenCode | `anomalyco/opencode` | 低：执行器 | 已复用 | 执行适配器 | 已是依赖 | 子进程管理或用量上报接口变化时（关联 #1336） | 2026-11-08 |
| Sogen | `momo5502/sogen` | 低：二进制仿真与动态逆向 | 后续扩展候选 | 无 | 逆向不在默认产品范围 | 逆向扩展立项时 | 2026-11-08 |

## 职责划分

| 能力 | 归属 | 理由 |
|---|---|---|
| 同服务账户切换、请求级重试、额度等待 | Magpie 为主，本地保留 fallback | 已有成熟实现；先做等价性测试，再降级本地路径 |
| 用量与成本数据 | 复用上游用量证据 | 避免两套不一致的账本 |
| 任务级能力匹配、周额度配速 | Nerelan | Magpie 不知道任务质量要求和未来任务需求 |
| 权限、预算、执行租约、独立验收、受控发布 | Nerelan | 核心信任边界 |
| 通用多 Agent UI 框架 | 暂停大规模重构 | 现有 OpenHands 复用足够 |

"停止重复建设"必须先通过等价性测试，再把重复路径降级或移除；不能只因为上游文档写着支持就删掉本地容错。

## 待验证事项

- **Magpie 路由归属**：账户耗尽、切换、失效与恢复下，只有一个账户级决策 owner。
- **真实任务恢复**：断网、强杀、重启、额度阻塞下，租约、预算和副作用不重复。见
  [真实任务长跑方案](REAL_TASK_LONG_RUN_PLAN.md)。
- **成本与质量**：同一任务集比较单 Agent、多 Agent 和不同选路，以每个独立验收成功任务的完整成本为指标。

## 雷达首次发现（2026-11-08 预览，未分诊）

| 仓库 | 来源查询 | 说明（仓库自述） |
|---|---|---|
| `savannahfeder/agentbox` | coding agent worktree | 桌面端并行运行多个 Claude Code / Codex，每个在独立 worktree |
| `cosscom/shipyard` | coding agent worktree | 在开发机上运行编码 Agent：worktree、终端、编排、桌面应用 |
| `wangmiaozero/pi-harness` | multi-agent coding orchestration | Pi Coding Agent 的运维超集：可观测性、治理、故障恢复、评测、多 Agent 编排 |
| `boadij/pi-herdsman` | multi-agent coding orchestration | 异步子 Agent 与并行编码 Agent 编排 |
| `y5ez3g/facadecode` | multi-agent coding orchestration | VS Code 中的多 Agent 编排，跨窗口和机器运行 Claude Code、Codex |

这些尚未分诊；`pi-harness` 自述的"治理、故障恢复、评测"与 Nerelan 定位最接近，建议优先查看。
