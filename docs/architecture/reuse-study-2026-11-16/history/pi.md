# Pi / pi-mono：跨对话研究归档（2026-11-16）

**原研究定位：** Pi 是候选 Agent Executor/Harness，而不是 Nerelan 的第二个任务协调器或账本。
**历史对话研究版本：** `earendil-works/pi@22fc026b`（仓库原名 `badlogic/pi-mono` 曾有迁移/重定向）；本次在该 Git SHA 上复核了以下源码/文档路径。
**研究状态：** `HISTORICAL_CHAT_STUDY + SOURCE_SPOTCHECKED / NOT_RUNTIME_TESTED`。原聊天的可公开固定消息链接和完整对话原文不可从当前 GitHub 项目获取；不声称历史已有独立 Issue/PR。研究总入口 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 复核过的源码/协议

- [RPC 规范](https://github.com/earendil-works/pi/blob/22fc026b/packages/coding-agent/docs/rpc.md)：Pi 作为受控 JSONL 子进程，`prompt` 的成功响应仅代表输入被接收/排队/处理，不代表整轮完成；低层 `agent_end` 后仍可能恢复/压缩/继续，客户端需等待 `agent_settled`。协议同时明确帧边界、流背压、命令 ID 关联及事件与命令响应不同源。
- [RPC 类型](https://github.com/earendil-works/pi/blob/22fc026b/packages/coding-agent/src/modes/rpc/rpc-types.ts)：`prompt`、`steer`、`follow_up`、`abort`、`compact`、`fork`、`get_tree`、`set_model`、`get_state` 等控制语义；`streamingBehavior` 不应被误当成额外的 Goal 授权。
- [Agent Session](https://github.com/earendil-works/pi/blob/22fc026b/packages/coding-agent/src/core/agent-session.ts) 和 [Session Manager](https://github.com/earendil-works/pi/blob/22fc026b/packages/coding-agent/src/core/session-manager.ts)：多叉会话树、压缩及分支/恢复需由 Executor Adapter 解释，不能自动转为 Nerelan TaskStore 真相。
- 历史对话另研究 Agent Loop、扩展/Skills、MCP、原生工具披露、QuickJS Code Mode 与 pi-durable。以上模块的**全部具体版本与函数证据未逐一复核**，不可将本段解释为这次全部重跑测试。

## Nerelan 对照及复用决策

| 模块 | 借鉴内容 | 保留的边界 |
|---|---|---|
| 执行器接入 | **P1** 用 Pi RPC/SDK 作为可选 `ExecutorRouter` 适配器；将 `prompt accepted`、`agent_settled`、abort 与事件明确映射到 Task Attempt 生命周期 | 不复制 Pi Agent Loop 作为新 Coordinator；Nerelan 保留 TaskStore/审批/发布 |
| 实时操作 | **P1** 将 `steer/follow_up` 作为 Host-owned、带授权/操作 ID 的显式控制命令 | 用户中途干预不得绕过 Window/Owner 许可 |
| 长会话 | **P1/P2** Session Tree/Compaction 作为 Executor 原生能力；记录 session_id、分支 head、checkpoint provenance | 压缩摘要不是审计证据或已验收事实 |
| 插件/工具 | **P2** 优先使用 Pi 原生工具/MCP/Extensions；按需展示而不是在 Nerelan 复制一套插件内核 | 扩展/Code Mode 非沙箱，工具回路必须经 Host Policy 与预算 |
| Durable | **P2** 参考 replay-safe/unsafe 工具分界 | 外部文件、CLI、GitHub、模型副作用不能凭日志保证 exactly-once |

## 用户价值与最小验证

用户希望一键选择 Pi 执行复杂任务，仍能看见“Pi 接受了命令/正在压缩/真正结束/需要授权”的区分，而不是收到一个假的 Completed。

**待验证**：Provider-free 子进程 Fake RPC：`prompt` 快速应答但迟迟无 `agent_settled`；`agent_end` 后触发自动压缩；`steer` 与 `abort` 竞态；RPC 背压/挂起；Session 换分支与重启；插件请求未授权 Tool；能力不可用时是否明确拒绝。未执行这些测试。

**实施归属**：[Harness×Model #1527](https://github.com/dddd2024/Nerelan/issues/1527) · [MCP #790](https://github.com/dddd2024/Nerelan/issues/790) · [Context #296](https://github.com/dddd2024/Nerelan/issues/296)；本历史档案不创建新 Pi Executor Issue，也不授权执行。