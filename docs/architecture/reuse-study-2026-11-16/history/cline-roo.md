# Cline / Roo：跨对话研究归档（2026-11-16）

**历史范围**：Cline Plugin / Hooks / MCP / Agent 执行状态与恢复；Roo 被作为相关分叉与比较对象讨论。**没有找到 Roo 独立冻结版本和本轮可验证的 Roo 专项源码证据**，本页不把 Cline 机制自动归属 Roo。  
**历史上游 Cline SHA：** 未保留。**本次归档补核源码**：[`cline/cline@0eeb32315ee28e5cd80c879ba16bc96eecf17dfe`](https://github.com/cline/cline/commit/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe)（**不能冒充历史源码版本**）。  
**状态：** `HISTORICAL_CHAT_STUDY / ARCHIVE_TIME_SOURCE_SPOTCHECK / NO_RUNTIME_VALIDATION`。已有 [11/15 横向执行器报告](../../reuse-study-2026-11-15/C-runtimes.md)，但未核实 Cline/Roo 专项 PR/Issue。归档于 [研究 Hub #1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 核查路径与模块

- [`plugin-config-loader.ts`](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/sdk/packages/core/src/extensions/plugin/plugin-config-loader.ts)：区分插件配置搜索路径、发现/禁用、显式指定，以及加载诊断。插件发现 ≠ 立即授予执行权限。
- [`settings/types.ts`](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/sdk/packages/core/src/settings/types.ts)：将 Skill/Workflow/Rules/Plugin/Tool/MCP 划分来源、可用性、启停与插件贡献，`CorePluginContributions` 将 capabilities/tools/skills/hooks/commands/mcpServers/providers 分开描述。借鉴可解释能力元数据，但不复制完整插件控制面。
- [`plugin-sandbox.ts`](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/sdk/packages/core/src/extensions/plugin/plugin-sandbox.ts)：默认 `subprocess` 进程或 `worker` 线程两种 Runtime Transport；Sandbox 是源码名词，**不能从此推断满足 Nerelan 对不可信代码强隔离的要求**。
- [`hook-factory.ts`](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/apps/vscode/src/core/hooks/hook-factory.ts) / [`hooks.proto`](https://github.com/cline/cline/blob/0eeb32315ee28e5cd80c879ba16bc96eecf17dfe/apps/vscode/proto/cline/hooks.proto)：已有多 Hooks/Task 事件协议；历史对话还研究了 Abort/Snapshot/Restore、Agent 生命周期和 SSE。但本轮未逐一核验这些逻辑的所有终态/运行时行为。

## 对 Nerelan 的明确结论

| 领域 | 借鉴 | 不应照搬 |
|---|---|---|
| Agent adapter | **P1** 事件通知、当前 Tool/Task 状态、Abort/恢复能力描述，可作为多 Executor Adapter 的运行契约 | 不再造 Cline 自己的任务调度/历史状态真相，不以插件 Loader 代替 Nerelan 执行器 |
| Pack/Hook | **P1** Manifest 展示功能来源、可用性和启停诊断；Hook 拦截点和错误可观察 | 不让项目级设置直接提高 Host Owner 权限 |
| 不可信插件 | **P0** 验证子进程环境、工具权限和真实安全隔离；不跨 Cline/Roo 混同 | 不把 Worker Thread/Subprocess 自动认作强沙箱 |
| 用户体验 | “为什么当前这个工具/插件不可用”“哪些 Hook 会参与任务”可以在任务视图明确解释 | 不暴露一套互相矛盾的二级设置页 |

**最小测试（未执行）**：插件显式禁用却从另一搜索路径被发现；Plugin Runtime 被强杀；Task Abort 后后续 Hook/Tool 仍回调；Repository 注入未经批准的 MCP/Hook；插件的能力声明与实际运行时不一致。

**现有实施 Owner**：[Pack #253](https://github.com/dddd2024/Nerelan/issues/253)、[Hooks #789](https://github.com/dddd2024/Nerelan/issues/789)、[MCP #790](https://github.com/dddd2024/Nerelan/issues/790)、[Workspace trust #303](https://github.com/dddd2024/Nerelan/issues/303)、[Harness×Model #1527](https://github.com/dddd2024/Nerelan/issues/1527)。