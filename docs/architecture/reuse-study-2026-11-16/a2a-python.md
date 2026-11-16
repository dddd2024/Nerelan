# A2A Python SDK 1.0 — 远端 Agent 任务委派和安全边界源码专项

**研究 Issue**：[ #1603 ](https://github.com/dddd2024/Nerelan/issues/1603) · **总台账**：[ #1576 ](https://github.com/dddd2024/Nerelan/issues/1576) · 2026-11-16

**证据：STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**。

**唯一上游**：[a2aproject/a2a-python@c16cab1ca22a5fac8288c1351610dfc85a4e072c](https://github.com/a2aproject/a2a-python/commit/c16cab1ca22a5fac8288c1351610dfc85a4e072c)（Apache-2.0），**Nerelan current main**：[0509cd6135b9bdcd7e08c94838b5df6dd04b54b3](https://github.com/dddd2024/Nerelan/commit/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3)。研究只读取固定源码/测试，没执行上游 Python、HTTP、模型或任何真实服务。

---

# A2A Python SDK 1.0 深度源码审查：远程 Agent 信任 / 跨副本任务 / 取消与 Push 回调

> 2026-11-16 · STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY
> 唯一上游：[a2aproject/a2a-python@c16cab1ca22a5fac8288c1351610dfc85a4e072c](https://github.com/a2aproject/a2a-python/commit/c16cab1ca22a5fac8288c1351610dfc85a4e072c)（Apache-2.0）。Nerelan 对照：[main@0509cd6135b9bdcd7e08c94838b5df6dd04b54b3](https://github.com/dddd2024/Nerelan/commit/0509cd6135b9bdcd7e08c94838b5df6dd04b54b3)。未运行上游代码/模型/安全测试。

## 0. 事前查重和独有价值

查阅研究 Hub #1576（六个原专项与之后九个：#1578 #1581 #1585 #1587 #1590 #1592 #1594 #1598 #1600）、19 个历史归档、横向研究及 GitHub Issue 关键词 A2A、a2a-python、Agent2Agent。发现已有协议提及，但没有 a2aproject/a2a-python 固定 SHA 的独立源码审计。注意仓库中如 #1010 的内部 A2a 只是工作编号，不是此 SDK。当前为第十六个独立静态源码专项，不代表十六个合并/实测的项目。

与 ACP #1585（IDE↔Agent）、AG-UI #1600（Agent↔UI）、MCP #1590/#1598（Agent↔Tool）不同，A2A 是**跨系统远程 Agent↔Agent 的发现与任务委派**，不能自动将 Nerelan 本地 OpenCode/Codex/Claude CLI 变成分布式远端 Agent。

已有实施归属：#806 Headless API/SDK（主要归属）、#1527 多 Harness、#179 Host Policy、#447 egress/SSRF、#1546 durable engine、#299 sandbox、#253/#789 Pack 与 hooks、#1267 任务成本/质量基准；不创建重复 implementation Issue，不替换 TaskStore/Coordinator/Magpie。

## 1. 源码级机制 / 风险

### A. Agent Card 发现与多协议协商：P1 BORROW_PATTERN，P2 条件性 SDK

[client/card_resolver.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/client/card_resolver.py) 能获取公开/指定路径 Agent Card，并转换旧版字段；签名验证参数 signature_verifier 是**可选**的，默认 None；解析格式不等于可信身份。获取后还会向 INFO 日志输出 Agent Card JSON，部署时需限制来源、长度和敏感字段。
[client/client_factory.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/client/client_factory.py) 可以在 JSON-RPC、HTTP+JSON、gRPC 协议绑定间选择版本/优先级，并含 0.3/1.0 兼容。find_best_interface 有高于 1.0 的候选规则，但 Nerelan 必须基于**实际已验证版本**决定是否连接，而不是自动相信宣称更高版本的未验证 Agent Card。
建议定义只读 RemoteAgentDescriptor（来源、验证结果、协议能力、endpoint/audience、费用、使用边界、支持的任务/模型/数据安全级别），验证签名/源/域、做权限检查和有限能力测试。只有真实跨系统远端 Agent 需求得到验证，才考虑复用官方 Python SDK；本地 Harness 不要强制转换为 A2A。

### B. CAS 任务状态、追加事件与 Artifact：P1 BORROW_PATTERN

[server/cluster/database_task_store.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/cluster/database_task_store.py) 用 owner/task/version 做 CAS，并将 Task/Version 和可选 Event 写入同一事务；冲突抛 ConcurrentTaskModificationError；临时数据库争用才有有界重试。终态 task 的 cancel 会被拒绝。[database_event_stream.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/cluster/database_event_stream.py) 以版本游标和 seq 读取追加事件，owner_resolver 若未配置则订阅查询没有 owner 过滤，故多租户集成必须在 Host 做身份和 owner 限制。
[tasks/task_manager.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/tasks/task_manager.py) 校验 task_id/context_id，复制后更新任务，Artifact 先创建再 append，防止未创建 ID 的片段被当作有效 artifact；[task_updater.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/tasks/task_updater.py) 有 submitted/working/input-required/auth-required/completed/failed/canceled 等状态。
对 Nerelan 只创建远端映射：Nerelan Task/Attempt -> remote card digest/version/contextId/taskId/last event seq/artifact digest/UNKNOWN。远端 completed 是远端自报结果而不是本地独立功能验收、合并权限或真实成本结算。现有 run_store.py/task_execution.py/task_runtime.py 的 TaskStore、受信验证与中立 Executor 合同必须保留。

### C. 多副本主动任务 + 旧权限漏洞的修复测试：P0 NEGATIVE_FIXTURE

[DefaultRequestHandlerV2](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/request_handlers/default_request_handler_v2.py) 明确告警：queue_manager 参数接受但**忽略**，活动任务由内存 ActiveTaskRegistry 管；multi-replica streaming 需要另外的共享事件流/转发路由，不能认为配置共享 QueueManager 就有全局事件能力。interrupted_task_timeout 默认 None，不自动释放闲置等待输入的 ActiveTask。
[active_task_registry.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/agent_execution/active_task_registry.py) 源码注释记录曾经 cache-hit task_id 查找绕过 owner（#1159/CWE-639），当前逻辑为命中路径额外通过 owner-scoped TaskStore 读取，否则以 NotFound 掩盖。**此为已修复历史边界，不宣称当前仍存在漏洞**。[test_cancel_multireplica.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/tests/server/cluster/test_cancel_multireplica.py) 覆盖跨副本取消、重复取消、非 owner 取消与取消后的等待任务不能再恢复。
对应 Nerelan provider-free 测试：多 Agent 抢同一任务、不同 owner 使用同 TaskId、取消与完成竞争，另一个实例崩溃后 replay；不能重复外部 side effect，也不能让旧请求恢复已经取消/终止的任务。

### D. Push Notification 默认 URL 不校验：P0 NO-GO

[utils/push_url_validator.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/utils/push_url_validator.py) 提供 HTTP(S) scheme 和 DNS/IP 目标筛选，拒绝非公网地址、loopback、link-local、100.64.0.0/10、IPv4-mapped IPv6，并对解析失败 fail-closed。但 [BasePushNotificationSender](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/tasks/base_push_notification_sender.py) 构造器与 DefaultRequestHandlerV2 的 push_url_validator 默认均是**None，不做库层校验**。
Sender 从 PushConfig 取得 URL 后可 best-effort POST，并带 X-A2A-Notification-Token / Authorization。即使显式启用校验，它在 DNS 查询和真实网络连接之间仍可能存在 TOCTOU；需要对重定向/代理/目标证书/实际连接 IP 另做验证。不能因为预校验通过就宣称不存在 SSRF，也不能让远端 Agent 决定把回调发送到 Nerelan 的本机服务。
建议初期禁用任意 Push URL，优先受信的主动 polling/受控订阅；如有真实异步通知需求，必须绑定特定可信 HTTPS callback、网络 egress 策略、按操作授权、签名/短期 token 与重试/去重证据。

### E. 认证/插件 Hook ≠ Owner 授权：P0 HOST_GATE

[client/auth/interceptor.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/client/auth/interceptor.py) 根据 Agent Card securityRequirements，将 Bearer/OAuth/API-key 加到发送参数，但 Card 是远端**自报**，不能因此把 Magpie provider、宿主 Owner 或外部 SaaS 长期凭据发送到未受信端点。
[server/owner_resolver.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/owner_resolver.py) 默认从服务端 authenticated context.user.user_name 取 owner；[plugin_agent_executor.py](https://github.com/a2aproject/a2a-python/blob/c16cab1ca22a5fac8288c1351610dfc85a4e072c/src/a2a/server/agent_execution/plugin_agent_executor.py) 执行 before/after/event hooks 但 Hook 不是安全审查或授权的替代。

## 2. 模块复用矩阵

| 模块 | 裁定 | 复用边界 | 既有 Owner |
|---|---|---|---|
| 远程 Agent 卡片/协议 | P1 BORROW_PATTERN，P2 CONDITIONAL_SDK | 1.0/0.3 multi transport，验证卡片信任再派发 | #806 #1527 |
| 远程委派任务恢复 | P1 BORROW_PATTERN | CAS/事件序号/跨副本取消、read-back/reconciliation | #806 #1546 |
| 客户身份与认证 | P0 HOST_GATE | 仅对可信 endpoint/audience/scope 注入短期密钥 | #179 #447 |
| 外部通知/回调 | P0 NO-GO_DEFAULT | URL 默认不校验；禁止任意外部 Push 与私网访问 | #447 #806 |
| 插件 Hook | P2 BORROW_PATTERN | 保留 provenance/errors，不引第二套 Plugin Manager | #253 #789 |
| Agent Loop / TaskStore / 审查 | KEEP_EXISTING | 远端完成不代表本地通过功能验收或 Owner 批准 | #1546 #1527 #803 |
| 模型账户与成本 | KEEP_MAGPIE | 不以 A2A remote endpoint 替换 Magpie 模型账号池 | #1342 #1267 |

## 3. 拟议 provider-free 实验（NOT RUN）

**D1 发现/协议**：伪造签名/修改 Card、非法版本/不同 transport、伪造远端 endpoint、卡片变更 redirect；不泄露任何实际账户凭据。
**D2 多副本身份/取消**：alice/bob 同 Task ID，跨副本 cancel/complete race、被取消任务的后续消息不能复活；跨用户任务订阅不得泄露事件。
**D3 Durable ID/收据**：事件丢失/重复、Artifact chunk append before create、写入成功但响应丢失、重新连接和跨进程切换；无重复 side effect，UNKNOWN 或独立远端 readback。
**D4 Callback SSRF**：未启用 validator 的默认行为负面 fixture，以及私网 IP、DNS rebind、302、认证头、代理；Nerelan callback 出站必须 Host 网络层拒绝。
**D5 Auth 持续性**：Card 更新 authentication schemes / URL 变化，撤销后旧 token 不可注入，Agent 不能传递 Magpie 账户凭据。
**D6 资源与错误**：JSON-RPC/HTTP+JSON/gRPC、SSE 提前断开、timeout、重复取消、插件异常对执行回滚/清理的影响；没有无界重试或子进程泄漏。
**D7 价值验证**：真实任务 acceptance 相同，远端 A2A Agent 与现有 Executor 的完成质量、模型/远端费率、时延、人工干预和总代价对照；没有改善不引入依赖。

## 4. 最终结论

**SELECTIVE_BORROW_PATTERN / P2_CONDITIONAL_OFFICIAL_CLIENT_SDK / P0_NO_GO_UNTRUSTED_CARD_AND_CALLBACK**。最值得借鉴远程任务身份、卡片信任、跨副本 cancel/CAS 及 callback 默认不安全的负例。现阶段不建议把现有本地 Harness 强制转成 A2A。只有远端异构 Agent 的独立价值经成本与验收证明，才评估官方 SDK 直接复用。

全篇仅静态源码审阅，未安装依赖、未运行测试、未打网络请求或模型、未申请 R2/R3/新实施 Owner。应将此 Issue 连到 R1 docs-only Draft PR 与 canonical hub #1576。

---

## 本轮治理与分支说明

该文件在 main@0509cd6135b9bdcd7e08c94838b5df6dd04b54b3 创建的独立 R1 branch；不是第二个 AgentLoop/TaskStore/Connector 实施方案或代码授权。已有 #806 是远程/Headless SDK 的产品 Owner，#1527 是各种 Harness 测评 Owner，#179/#447 负责身份/网络安全，#1546 负责 durable state。所有 D1–D7 是**尚未执行**的 provider-free 测试建议，不是实证结果。

研究索引继续写入 #1576 的 dated append-only comment，避免与已有多个 Draft 研究索引 PR 冲突。文档合并需要遵守 AGENTS.md exact-head baseline/state-gate + independent verdict；不宣称已经完成 CI 或评审。