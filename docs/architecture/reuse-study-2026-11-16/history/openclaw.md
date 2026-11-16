# OpenClaw：跨对话源码深拆归档（2026-11-16）

**原研究上游：** [`openclaw/openclaw@02dc185`](https://github.com/openclaw/openclaw/commit/02dc185)，本次在该历史提交验证了源码/文档存在。  
**状态：** `HISTORICAL_CHAT_STUDY + SOURCE_SPOTCHECKED / NOT_RUNTIME_TESTED`。旧对话静态源码研究，没有找到同名独立 GitHub 研究 Issue/PR，不能用别的实施 Issue 证明已做专项归档。研究总入口 [#1576](https://github.com/dddd2024/Nerelan/issues/1576)。

## 可核实的结构

1. [`Agent Harness Registration`](https://github.com/openclaw/openclaw/blob/02dc185/docs/plugins/sdk-agent-harness/registration.md)：`AgentHarnessV2` 用 `supports(ctx)` 识别当前 Provider/Model、RuntimePolicy、请求覆写等真实兼容性，并返回 `supported/reason/priority`；`runAttempt` 执行一轮原生 Agent。示例区分 Hosted Workspace 标记与真正的身份、认证、数据同步权限。不能仅凭 UI 标签就宣称可安全远端执行。
2. [`extensions/copilot/harness.ts`](https://github.com/openclaw/openclaw/blob/02dc185/extensions/copilot/harness.ts)：`CopilotSessionBinding` 保存 `sdkSessionId / compatKey / authMode / authProfileVersion / journalVersion`，当 Provider、Model、CWD 或 Auth 不兼容时开新原生 Session，而不是无条件恢复旧 Session。
3. [`src/plugins/activation-planner.ts`](https://github.com/openclaw/openclaw/blob/02dc185/src/plugins/activation-planner.ts)：`resolveManifestActivationPluginIds` 能仅凭 Manifest、Plugin Owner Trust、用途 Trigger（Command/Provider/Harness/Channel/Route/Capability）决定应激活的插件 ID，**不需要导入运行时代码来完成最初的发现**。
4. [`docs/plugins/architecture-internals/load-pipeline.md`](https://github.com/openclaw/openclaw/blob/02dc185/docs/plugins/architecture-internals/load-pipeline.md)：配置/发现/激活的阶段区别，以及可信来源和运行时注册边界。历史对话进一步讨论 `discovery / setup-only / setup-runtime / tool-discovery / full` 的概念，需保持与实际版本相匹配。
5. 本次**没运行**任何 Plugin，也未证明 OpenClaw 第三方插件在所有路径上强制 OS 级隔离。插件运行在 Gateway 进程内或经其逻辑运行不等于 Hostile Code Sandbox。

## 可复用机制与拒绝

| 机制 | Nerelan 可复用 | 不允许假设 |
|---|---|---|
| Harness capability preflight | **P1** 逐 Executor 检查 Provider/Model/API/认证/TLS/Headless/CWD/Session/Tool Events，返回不兼容原因；绑定到 `ExecutorRouter` | 兼容不等于 Host 授权，不能因预检成功发付费请求 |
| Session Compatibility Key | **P1** 恢复任务前验证实际模型、账号、工作区、协议版本与 Tool Policy；条件变化时失败关闭 | 名称相同就能安全 Resume |
| Manifest-first plugin loading | **P1** 只读取声明做工具查找/启用审批/按需加载，不在 Discovery 阶段执行项目代码 | 安装/发现就授权执行不可信插件 |
| Plugin Runtime Generation | **P1/P2** 绑定 Attempt 的插件配置/工具范围/策略版本，避免运行中热更新改变已批准的工具面 | 工具 Manifest 是可信的授权来源；运行时代际不能越权扩容 |
| Gateway、Cron、Channels | **REJECT DEFAULT** 不复制 OpenClaw 的整套聊天网关、调度器、会话真相和 In-Process 插件体系 | 不为统一工具入口再建一个主 Platform |

**测试（未执行）**：Provider/Model 切换后的 Session 不兼容、未经批准 Plugin 在 Manifest 阶段意外加载、Plugin 热更新时的已发 Tool Call、不同执行器是否报告一致的错误原因、插件卸载后原 Attempt 是否仍持有效授权。

**归属**：[Harness×Model #1527](https://github.com/dddd2024/Nerelan/issues/1527) · [Pack #253](https://github.com/dddd2024/Nerelan/issues/253) · [MCP #790](https://github.com/dddd2024/Nerelan/issues/790) · [Workspace trust #303](https://github.com/dddd2024/Nerelan/issues/303)。