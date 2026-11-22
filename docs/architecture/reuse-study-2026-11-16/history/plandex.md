# Plandex：跨对话研究归档（2026-11-16）

**历史来源：** 其他对话已做 Plan/Branch/Changes/Tree-sitter/回滚的源码级研究，但**原研究上游 SHA 未保留**。
**本次补核上游：** [`plandex-ai/plandex@e2d772072efadbe41d2946d97d79be55532dbab5`](https://github.com/plandex-ai/plandex/commit/e2d772072efadbe41d2946d97d79be55532dbab5)，**这是归档时的独立源码快照，不得冒称旧对话冻结版本**。
**状态：** `HISTORICAL_CHAT_STUDY / ARCHIVE_TIME_SOURCE_SPOTCHECK / NOT_RUNTIME_TESTED`。没有核实到本项目原有的独立研究 PR/Issue，参见研究 Hub [#1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 已复核的上游源码

- [`app/cli/lib/apply.go`](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/app/cli/lib/apply.go)：Plan 的 Changes 被显式 `Apply` 而不是一生成就写入用户工作区。存在 `AutoConfirm`、`AutoCommit`、`NoCommit`、`NoExec` 参数；**这些自动模式不能未经 Owner 权限直接移植**。
- [`app/cli/lib/rewind.go`](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/app/cli/lib/rewind.go)：按 Plan Apply 历史识别应撤销的文件、真实已应用路径和已有修改冲突；不是无条件 `git reset`。
- [`app/server/syntax/file_map/map.go`](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/app/server/syntax/file_map/map.go)：Tree-sitter/解析器构造函数、类、配置等的结构性 File Map；不支持文件可返回 `no_map`，不应把未解析视作“空文件无代码”。
- [`docs/docs/core-concepts/version-control.md`](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/docs/docs/core-concepts/version-control.md) 与 [`reviewing-changes.md`](https://github.com/plandex-ai/plandex/blob/e2d772072efadbe41d2946d97d79be55532dbab5/docs/docs/core-concepts/reviewing-changes.md)：Plan Versions、待应用修改与审查流程的产品语义；历史对话另谈到 `architect_context.go`、`build_validate_and_fix.go` 等文件，但当前已复核的是上面列出的路径，其他文件不借用“已复核”的标记。

## 具体复用判断

| 模块 | 对 Nerelan 的价值 | 现有任务和边界 |
|---|---|---|
| Versioned Plan | 记录任务计划的版本、依赖、修改意图及撤销到何版本 | [#803](https://github.com/dddd2024/Nerelan/issues/803) 变更检查点；不能与 TaskStore 的持久 Goal 产生双真相 |
| Pending Changes | 先产出 Patch/Artifact 再经过 Policy/Validation 批准应用 | [#653](https://github.com/dddd2024/Nerelan/issues/653) 选择性修改后的复验；不要自动提交/执行 |
| Repo / Symbol Map | 使用 Tree-sitter 结构地图为模型挑选上下文，降低重复扫描与 Token | [#296](https://github.com/dddd2024/Nerelan/issues/296)；需要对比缺符号/生成代码/跨语言文件的覆盖质量 |
| Build Repair | 修复应基于具体失败并保留原始失败证据 | 与现有 Verifier/Review Loop 对照；不复制 Plandex 整个 Agent Loop/自治等级 |

## 最小验证及用户体验

Provider-free 测试：Patch 已生成但未批准时不能写工作区；同时发生用户本地编辑时不得盲目 `rewind`；同文件不同 Plan 版本不可误合并；不支持的源码语言需明确退回普通文件摘要；测结构地图是否在相同验收门槛下减少 Token/返工。**本次未执行**。

用户侧值得借鉴的是明确的“已规划 / 有待确认修改 / 已应用 / 可撤销”，而不是在复杂任务中让 Agent 私自应用并声称成功。

**不采用**：Plandex 整个平台、计划 DB、完整 Agent Runtime、自动提交策略或第二个持久工作流引擎。