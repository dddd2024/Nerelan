# Agno：外部编码 Agent、Skills/MCP、审批与持久运行源码审计

**Canonical Research Hub:** [#1576](https://github.com/dddd2024/Nerelan/issues/1576)  
**Dedicated Research Issue:** [#1616](https://github.com/dddd2024/Nerelan/issues/1616)  
**Scope:** Docs-only R1 / static pinned-source inspection / upstream tests inspected but NOT RUN / no implementation authority

> **2026-11-16 / STATIC_SOURCE_REVIEW / R1 DOCS-ONLY / NOT_INSTALLED / NO TESTS RUN / NO MODEL CALL / NOT IMPLEMENTED / NO IMPLEMENTATION AUTHORITY**
>
> **唯一上游：** [agno-agi/agno@3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1](https://github.com/agno-agi/agno/commit/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1)（[Apache-2.0](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/LICENSE)）。Nerelan 对照 [main@0a9997046386bac5ca291410ce428c160f3ea763](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763)。
>
> 证据是两仓在以上 SHA 的代码与**已存在但未执行**的单元测试文件；没有验证版本依赖、运行时性能、安全性和成本。本文“抄”仅意指复用设计/测试思路，**不**授权直接运行上游或拷贝无审查代码。

## 0. 事前查重：PASS

- 先读 [#1576](https://github.com/dddd2024/Nerelan/issues/1576) 单一研究台账、[2026-11-15 五领域横向报告](https://github.com/dddd2024/Nerelan/tree/0a9997046386bac5ca291410ce428c160f3ea763/docs/architecture/reuse-study-2026-11-15)、[历史跨对话目录（Draft PR #1577）](https://github.com/dddd2024/Nerelan/pull/1577)、最新 #1562–#1614 独立专题；GitHub Issues/PR 全仓搜索 `agno` 没有结果。不能因为没有独立 Issue 就断言过去从未口头讨论，本次事实范围为当前可检索记录。
- 有**概念重复**：Pi/Cline/Kimi/Google ADK/Agents SDK 的工具协议、Skills、审批、Agent Session 已研究。但 Agno 的明确增量是 **(1) ExternalAgent 同时适配 Codex/Claude 原生 Harness，(2) Skills 的真实脚本运行边界，(3) 选择性授权 ContextVar 和暂停审批持久化，(4) MCP 多协议/session 生命周期，(5) 运行内复原/重试的安全差距**。
- 只建立一份新研究记录；不新开与 #1527、#253、#790、#296、#1546、#1267、#447 重复的 implementation Issue。

## 1. Nerelan 已有事实与产品方向

- [`AGENTS.md`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/AGENTS.md)：用户目标是 local-first、多执行器/多模型、Magpie 管账户/额度/真实用量，Nerelan 管 Goal/TaskStore、权限、独立评审、exact-head 受控发布；禁止第二 GitHub 状态副本/复制整体 runtime，不得为便利放宽 R2/R3。
- [`policy_adapter.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/policy_adapter.py)：Path A 的 R2/R3、路径和发布操作 fail-closed；[ `goal_service.py` L177–290](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/goal_service.py#L177-L290)：UNKNOWN 外部副作用/活租约阻止重派、区分 host 和模型错误；[ `task_execution.py` L332–410](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/task_execution.py#L332-L410) 已存在 fenced checkpoint 与受信宿主验证。
- [`context_recovery.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/context_recovery.py)：持久 ContextHandoff 和来源/scope snapshot，且 `authority: NONE`；[`magpie_usage_ingest.py`](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/magpie_usage_ingest.py) 区分 cash/quota，不以 SDK 中 `token usage` 推断真实现金账。
- **约束**：OpenCode 是当前执行器之一，**不是** Nerelan 固定核心。Agno 的内置 Codex/Claude 包装层值得对照“统一接入执行器”，而不是更换 Nerelan 为 Agno。

## 2. 实际源码与“抄什么”的分块裁决

| 分块 | 冻结上游文件（实际检查） | 候选可复用设计与不应照抄的点 | 裁决 |
|---|---|---|---|
| **External Agent Harness Adapter** | [`agents/base.py` L127–174](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agents/base.py#L127-L174) 定义 `ExternalRunMetricsEvent`、`ExternalRunResult`、`ExternalContinuation`；[`agents/codex/agent.py` L162–211](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agents/codex/agent.py#L162-L211) 通过 `openai-codex` 官方 Python SDK 适配，SDK 自管 Agent Loop；[`agents/claude/agent.py` L156–202](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agents/claude/agent.py#L156-L202) 适配 `claude-agent-sdk` 原生循环/插件/权限 | **抄薄 Adapter Contract**：能力协商、native session ID、Run/Tool event、cancel/resume、原生 usage/实际模型 ID、权限结果、外部副作用；不把 Agno Agent/Team/Workflow 变第二 Coordinator。需比较实际 Codex/Claude/OpenCode SDK 的持久性差异。 | **P1 BORROW_PATTERN** |
| **Run/Tool 权限传播** | [`run/authorization.py` L24–112,155–266](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/run/authorization.py#L24-L112)：`RunAuthorization` + ContextVar、task-lineage 限制、委派/惰性 generator 携带上下文、可信保存端覆盖 caller-provided claims | 可借鉴**可信宿主生成并绑定的 run authorization**和“暂停/继续不允许自行提升权限”；**关键负例**：`require_permission` 在**没有活动 `RunAuthorization`** 时返回而不抛出。它适用于授权上下文存在的业务路径，绝不能单独成为 Nerelan 全局 Host admission。 | **P0 gate tests; do not copy default** |
| **HITL / 多次审批** | [`approval/decorator.py` L21–69](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/approval/decorator.py#L21-L69) `required` vs `audit`；[`run/approval.py` L48–114,219–279](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/run/approval.py#L219-L279) 创建单次 pause 的审批记录，避免旧审批 cover 下一次调用；[`tests/unit/run/test_approval_multi_pause.py` L151–205](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/tests/unit/run/test_approval_multi_pause.py#L151-L205) 覆盖 `INV-1`/ `INV-2` 两笔调用须分别授权 | 抄 **same run, different tool-call/args, different decision** 的反例。**关键风险**：`create_approval_from_pause` 对 DB 写失败仅 warning 并返回 `None`；[`agent/_run.py` L237–255](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agent/_run.py#L237-L255) 仍将 Run `PAUSED`，但不能推断审批记录已持久化；Nerelan 必须 fail-closed、可见地等待修复，而不能静默丢审批。**不声称 Agno 自动越权执行**。 | **P0 BORROW_TEST + explicit fail rule** |
| **Skills / Pack** | [`skills/agent_skills.py` L16–62,90–185](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/skills/agent_skills.py#L90-L185)：技能元信息先给模型、再提供按需指令/参考/脚本工具；**同名 Skill 后加载覆盖前者，仅 warning**（L34–46） | 可抄 **metadata first, instructions on demand, tool catalog filtered by Pack**；Skills 的 `name+source_digest+trust_scope` 冲突应显式报错，不允许恶意 Skill 以同名覆盖受信 Pack。Nerelan 的 Pack #253 保持唯一 owner。 | **P1 BORROW_PATTERN; REJECT overwrite default** |
| **Skill Script 执行边界** | [`skills/agent_skills.py` L282–395](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/skills/agent_skills.py#L282-L395)：`execute=True` 后直接调用 `run_script`；[`skills/utils.py` L125–175](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/skills/utils.py#L125-L175) 使用本机 `subprocess.run`、Windows 解释器解析，目录穿越路径校验不等于进程隔离 | **P0 REJECT** 将 Agno 默认脚本工具暴露给普通 Agent。只有经 Owner 授权的 Pack/工具、按内容 hash 固定、执行位置 Sandbox、cwd/env/network/io limits、可审计的调用收据才准实际执行；无授权只允许读取文档。 | **P0 REJECT DIRECT EXECUTION** |
| **MCP/Plugin** | [`tools/mcp/mcp.py` L18–40,242–450,615–694,809–1050](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/tools/mcp/mcp.py#L809-L1050)：基于 MCP SDK/fastmcp，支持 legacy/auto protocol、分开连接/stream timeout、run_id 会话 TTL、按页最多 250 页枚举、include/exclude、HITL 名单后注册 `Function` | 借鉴 session lease、协议版本记录、跨页 discovery 后一次性校验、per-run auth headers；**工具列表 allowlist 不是 Host tool authorization**；`close()` 捕获并吞掉多种清理错误（L836–870），不可把清理失败视为资源已释放；远程工具的业务写入仍由 #790 Host Gate 管。 | **P1 BORROW_PATTERN / REJECT plugin as authority** |
| **Agent durability / retry** | [`agent/agent.py` L130–151,309–314](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agent/agent.py#L130-L151) 默认 `checkpoint=` None 最终回退到 `runs`（仅终态写）、`tool-batch` 可选、`tools` 保留未实现；[`agent/_run.py` L426–445,728–751](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agent/_run.py#L728-L751) 默认 `retries=0`，启用后 broad `except Exception` 可重新进 Run | **不要整体借用** Agno Agent Run 来实现 Nerelan 外部操作 exactly once。由 Nerelan durable_external_operations 和 Lease/Fence 继续持有重放决策；每次 retry 须先检查是否已外发/已收费及副作用。可借鉴结构化 Run events，但不抄无外部副作用判定的通用 retry。 | **P0 SAFETY GAP / P1 EVENT CONTRACT** |
| **外部 Harness 沙箱恢复** | [`sandbox/_harness.py` L139–170](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/sandbox/_harness.py#L139-L170)：开跑时确认 Sandbox 类型；测试 fixture 须显式启用；在多 Replica queue 环境拒绝仅在本机的 checkpoint 默认路径；Codex/Claude 外部 Agent 的 SDK 会话要通过适配层保存 | 借鉴 **capability admission**：多 replica 场景，恢复依赖的 Checkpoint 不能只保存在执行节点；本地 Windows 单机和远端 Sandbox 必须分别声明承诺的 resume 能力。沙箱不是权限本身；Nerelan #299 仍掌控真正隔离。 | **P1 BORROW_PATTERN** |
| **错误分类 / 成本与遥测** | [`models/fallback.py` L22–48,121–145](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/models/fallback.py#L121-L145)：细分 429、上下文溢出、其他可重试错误；[`agent/agent.py` L397–400](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agent/agent.py#L397-L400) `telemetry=True` 默认；[`agent/_telemetry.py` L30–57](https://github.com/agno-agi/agno/blob/3cb5054ae5f8b20b50abe9e3e7364ae1ccf8cee1/libs/agno/agno/agent/_telemetry.py#L30-L57) 会尝试发送运行元信息 | 借鉴 **模型错误分类，不借账户路由/计费**；必须 Magpie 确认实际 served model、request usage、quota/cash。实验/插件预设应禁用上游遥测 `telemetry=False` 或 `AGNO_TELEMETRY=false`，还需验证真实无外发；不称已测试。 | **P1 BORROW taxonomy, REJECT egress default** |

## 3. 高价值但最小范围的产品落点

**对用户**：Nerelan 将来可以把 OpenCode、Codex、Claude、任意 SDK Agent 作为等价可替换的 Executor 候选；用户只需选允许执行的项目/操作边界，不需理解不同原生 Agent 的会话恢复和权限 UI；失败后系统能说明是“账号限额/原生会话丢失/审批未持久化/工具重放风险/沙箱恢复不可用”，而不是同一个模型反复撞墙。

**薄协议草案（仅研究）**：`executor_kind / version / model_requested / model_served / native_session_handle / run_id / attempt_epoch / capability{resume,stream,tool_approval,usage,sandbox} / tool_call{namespace,name,args_digest,origin,side_effect_class} / external_operation_id / lifecycle{proposed,paused,pending,unknown,verified,failed} / usage_request_refs / artifact_refs`。元数据不是许可；所有原生批准必须重新映射并通过现有 Host Gate；取消/恢复不可丢旧收据或悄悄重执行副作用。

**不要**将 Agno 的 AgentOS、Workflows、Team Manager、DB、Memory 作为 Nerelan 第二个主控，或者把原生 `allowed_tools` / Skill 元信息 / MCP server `list_tools` 当成安全证明。

## 4. 建议的无 Provider 证伪实验（本轮未执行）

1. **双调用审批**：同一 Run 连续两次 `tool_name` 相同但 `args_digest` 不同，批准第一次不能让第二次执行。DB 审批记录写入/查询故障时状态必须 BLOCKED/REPAIR，不得静默从 UI 消失。
2. **无 Auth Context**：外部 Agent、hook、generator、恢复 Session、MCP 调用携带伪造 metadata 时，所有 effectful 请求均由 Nerelan Host Gate 拒绝或重新绑定，不依赖 SDK `require_permission` 的缺席行为。
3. **脚本伪装**：重名 Skill、换内容的同名脚本、trusted vs untrusted Pack、Windows shebang、子目录符号链接、`execute=True` 和伪超长 timeout；未授予 R3 前零执行、零敏感目录读写。
4. **MCP 生命周期**：非空游标多页工具、半途抛异常后旧 tool registry 仍保持原有状态、失败连接清理、复用不同 Run session ID、重复工具名。任一缺少资源 scope 的工具不得可调用。
5. **长期任务恢复**：模拟模型已调用收费工具但 Agent Run 接到 `Exception` 和重试，必须先查 durable_external_operations；禁止第二次发布/付款/创建 Issue。
6. **多 Harness 能力矩阵**：同一简单任务在 Mock OpenCode/Codex/Claude 模拟器间切换，在无法恢复原生会话时只选“受控新 attempt + 上一 attempt 证据+已完成工作”而不伪造原生继续。
7. **成本/效果**：真实长任务上测试收益：`accepted outcome`、跨执行器续接率、人工干预次数、资源遗留率、重复外部副作用率、总模型 Token/API/订阅额度+工具调用成本。没有收益不引入 Agno 依赖。
8. **零网络**：默认上游 telemetry、MCP header_provider、Fallback 模型等均不得绕过 Magpie 和 Host egress。

## 5. 决策与已有归属

- **P0 测试优先**：单个审批不可复用到另一 tool call、脚本默认禁执行、无 auth context 的 Host Guard、重试未知副作用。由已有 #253（Pack）、#179/#447（权限/外发）、#1546（Durable）、#790（MCP）承接。
- **P1 可复用机制**：Codex/Claude 外部原生 Agent 的薄 Adapter Contract、native session/usage 事件、运行能力协商、Skills 渐进披露、MCP 多页及 TTL/cleanup。由 #1527（Harness×模型质量）、#296（上下文效率）、#790（Connector）、#299（Sandbox）承接。
- **P2 仅在实测后**：完整 Agno 作为可选被动 Executor Harness 的基准候选，而**非核心 AgentOS/Team/Workflow 替换**；由 #1527/#1267 证明质量/成本净值。
- **Reject**：Agno 重复 Agent 状态库、Tool 执行默认授权、Skills 原生进程执行、Skills 同名覆盖、无独立授权的 MCP 服务、默认外发 Telemetry、自动通用 Retry。

### 结论

**Agno 值得抄的是“将原生 Harness 适配进统一运行/权限/事件合同”的细节、Skills 渐进加载和两次 HITL 审批的反例；不值得抄的是它的第二套 Agent 主循环/工作流/数据真相。**

本文只归档研究证据，不授予开发或 R2/R3 操作权限。验证仍需独立 exact-head CI/评审，才可能进一步推进。