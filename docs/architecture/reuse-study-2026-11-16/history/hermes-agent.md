# Hermes Agent：跨对话源码深拆归档（2026-11-16）

**历史记录版本：** `NousResearch/hermes-agent@e96221fa`（历史对话只保留该短 SHA，当前已用此 SHA 读取上游源码确认存在）。[源码提交](https://github.com/NousResearch/hermes-agent/commit/e96221fa)。
**状态：** `HISTORICAL_CHAT_STUDY + SOURCE_SPOTCHECKED / NOT_RUNTIME_TESTED / PREVIOUS_GITHUB_AUDIT_UNVERIFIED`。**此前有助手说“已保存 GitHub 审计”但没有给出真实文件/Issue/PR，本次仓库文件/标题搜索也未定位专属条目，因此不能将它计为过去已经落库的研究。**本页是第一次可核查的本仓库专项档案之一。总入口 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 冻结源码与历史研究恢复

- [`hermes_cli/kanban_ops.py`](https://github.com/NousResearch/hermes-agent/blob/e96221fa/hermes_cli/kanban_ops.py)：命令支持 `dispatch / tail / watch / gc / repair`；派发读取默认分配、全局并发、每 Profile WIP、Spawn 上限，向后台 Kanban State 写事件与 Worker 信息。可以学习“为何没有被调度”的可解释结果，但不取代已有 Nerelan Coordinator。
- [`hermes_cli/kanban_swarm.py`](https://github.com/NousResearch/hermes-agent/blob/e96221fa/hermes_cli/kanban_swarm.py)：在既有 Kanban Task Store 上直接构建规划根→并行 Worker→Verifier→Synthesizer 的小型依赖图；**源码注释明确不另建一个 Scheduler**。共享事实通过已有 Task Comments/Events 保存，而非生成第二本状态账。
- [`hermes_cli/kanban_db.py`](https://github.com/NousResearch/hermes-agent/blob/e96221fa/hermes_cli/kanban_db.py) 与 [`kanban_db_dispatch.py`](https://github.com/NousResearch/hermes-agent/blob/e96221fa/hermes_cli/kanban_db_dispatch.py)：历史对话覆盖 SQLite、Claim/Lease、依赖、后台恢复、独立 Worker；本轮对这些路径做可用性定位，不视作所有竞态已验证。
- [`tools/skills_tool_setup.py`](https://github.com/NousResearch/hermes-agent/blob/e96221fa/tools/skills_tool_setup.py)：Skill Readiness 区分 `available / setup_needed / unsupported`、检查环境变量/需采集的 secrets、远端环境是否适配。这是产品启用前预检模式，不代表 Manifest 许可可越过 Nerelan Host。
- 旧对话还提 `@file`、`@diff` 上下文引用、Handoff/验收文本、Skill 统计/归档/审批/恢复。具体的完成与独立验收契约没有在本轮逐个动态检查，不自动认定安全等价。

## 对 Nerelan 的真实价值

| 借鉴 | 用法和原有归属 | 拒绝 |
|---|---|---|
| Kanban/Dependences 真实待机理由 | **P1** 复用现有 Task DAG、TaskStore、Coordinator 的状态和阻塞原因，[#1508](https://github.com/dddd2024/Nerelan/issues/1508) | 不引入 Hermes Kanban、第二数据库、第二 Scheduler 或 Worker 管理器 |
| Handoff 与证据引用 | **P1** 将 `@file`/`@diff` 式引用映射为不可变 Artifact+Commit SHA，减少跨 Agent 传输全量上下文 | 不能只靠模型自然语言“完成”或没有外部 Evidence 就验收 |
| Skill Readiness/Install | **P1/P2** 安装前明确缺失密钥、依赖、隔离/插件信任要求，允许撤销 | 不把 Skill 目录或安装过程当作宿主授权；不接受自动提升权限 |
| Background Recovery | **P1** 负载上限、Worker 退出、旧 Claim 回收的状态与恢复测试 | 不宣称无需恢复回执的 exactly-once |

**最小负面验证（未执行）**：两名 Worker 争用同任务、撤销后旧 Worker 提交、任务 DAG predecessor 未完成却被执行、Skill 需要的 Secret 意外进入模型输出、Kanban Completed 但独立 Verifier 未通过、临时证据在 Handoff 后变更。

**用户体验**：一眼理解“为什么还没派发/谁在执行/缺什么技能或权限/什么时候可以验收”，同时保持 Nerelan 现有统一 Task/Goal 视图。

**已有实施归属**：[Goal DAG #1508](https://github.com/dddd2024/Nerelan/issues/1508) · [Pack #253](https://github.com/dddd2024/Nerelan/issues/253) · [Hooks #789](https://github.com/dddd2024/Nerelan/issues/789) · [Sandbox #299](https://github.com/dddd2024/Nerelan/issues/299)。