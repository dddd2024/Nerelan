# Letta Code：跨对话研究归档（2026-11-16）

**原研究版本：** [`letta-ai/letta-code@eadef1c`](https://github.com/letta-ai/letta-code/commit/eadef1c)；历史对话记录版本 `0.34.63`。
**状态：** `HISTORICAL_CHAT_STUDY + SOURCE_SPOTCHECKED / NOT_RUNTIME_TESTED`。旧对话没有可核查的独立研究 Issue/PR；本文是重新入库，不代表插件代码运行或新功能实施。主入口 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 能与上游源码对应的历史结论

1. [`memory-operation.ts`](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/memory-operation.ts)：Git-backed Memory Checkout 的部分**由 Harness 负责的写者**通过文件锁串行化；锁仅在持有者进程死亡后允许回收，暂停但还活着的进程仍保有锁。源码明确说 **Primary Agent 自己的编辑不在这把锁下**，工作树仍可有 Git 冲突。故不能宣称 Memory 写入具有全局事务保障。
2. [`memory-worktree.ts`](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/memory-worktree.ts)：Reflection 可在独立 Git Worktree 产生变更并尝试合并；失败/冲突与“无改动”必须分开保存。代码中的 Git 操作有超时，失败回滚需另按当前调用链验证。
3. [`memory-handoff.ts`](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/subagents/memory-handoff.ts)：新 Worker 默认收到 Assignment，父上下文按需导出而非把整个历史直接注入；`withMemoryHandoff` 在 finally 中清理只为这名子 Worker 创建的 Transcript 快照。
4. [`memory-worker.ts`](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/subagents/memory-worker.ts) 与 [`reflection-runs.ts`](https://github.com/letta-ai/letta-code/blob/eadef1c/src/agent/reflection-runs.ts)：旧对话研究 Dreaming/Reflection 与 Repair、锁/合并结果、工作进度；本轮只核查这些真实路径，没有逐个运行分支。
5. 历史对话还研究了 `MEMORY.md` 根目录短注入、更多记忆文件按需读取、Core/External/Conversation 分层、Skills/Mods/MCP 与 Subagent 记忆范围；详细权限/版本语义只保留为“历史提及”，非本次全面核验。旧对话指出 `.af` AgentFile 路径已移除及 Windows 自动 Reflection 受限制，需在未来实际适配前重新检查版本。

## Nerelan 可抄、不抄

| 模块 | 借鉴 | 拒绝 |
|---|---|---|
| 长期记忆 | **P1** 以版本化文件记录“结论/证据路径/适用范围/来源”；将根索引摘要与按需子文件分层 | 不把未经审查的模型记忆自动变为事实、Policy 或 Owner 授权 |
| Reflection | **P1/P2** 独立 Worktree + 差异/冲突/失败回执，候选记忆经审查才能进入公共上下文 | 不在 Trusted Host 后台默默合并 Agent 写的 Memory；不能宣称完全无冲突 |
| Agent 间交接 | **P1** 精简 Assignment + 不可变证据引用、临时 Transcript 作用域清理 | 不把所有父会话上下文/隐私自动广播给所有子执行器 |
| Plugin / Skills | **P2** 借鉴绑定 Agent 的 Skill/Mods 生命周期与只读能力发现 | 不接管 Nerelan Pack、Executor、权限与成本结算 |

## 测试与产品意义

应验证：两个 Memory Writer 竞争、进程暂停与死亡、Worktree 合并冲突、旧版本反思写覆盖新事实、跨任务注入未经批准指令、Windows 路径行为、记忆命中质量与成本。**没有执行**。

用户最终需要的是可解释的“某条经验是谁、在哪次任务中得到、何时被验证、如何撤回”，而非模型自动声称永久记得一切。

**已有归属**：[Context #296](https://github.com/dddd2024/Nerelan/issues/296) · [Pack #253](https://github.com/dddd2024/Nerelan/issues/253) · [Workspace trust #303](https://github.com/dddd2024/Nerelan/issues/303)。