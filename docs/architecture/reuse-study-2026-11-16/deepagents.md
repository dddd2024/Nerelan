# Nerelan 单项目固定源码调研：Deep Agents 0.7.39

> [Research Issue #1657](https://github.com/dddd2024/Nerelan/issues/1657) · R1 doc-only · pinned static source · no install/tests/implementation authorization

# Deep Agents 0.7.39 — Agent harness / subagents / skills / filesystem / summarization deep source audit

**Status**: 2026-11-17 · SINGLE_UPSTREAM · PINNED_SOURCE_STATIC_REVIEW · R1_DOCS_ONLY · **NO_INSTALL / NO_TEST / NO_PROVIDER / NO_IMPLEMENTATION_AUTHORITY**

Upstream [`langchain-ai/deepagents@9a02909f69896ee6bf4cb1e7a41d612ace9c7589`](https://github.com/langchain-ai/deepagents/commit/9a02909f69896ee6bf4cb1e7a41d612ace9c7589), Python library `deepagents 0.7.39`, MIT ([license](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/LICENSE), [pyproject](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/pyproject.toml)). Nerelan [`main@5c69e891e3a559a23e7fd4e3115422c057df4438`](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438), Governance v2.1.

## 0. Preflight dedup — this is not LangGraph or Agents SDK again
- Examined [research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) and **32 archived project-specific comments** before beginning; GitHub Issues/PR and code search for `deepagents`, `langchain-ai/deepagents`, `Deep Agents` returned **no standalone pinned-source Deep Agents audit**.
- LangGraph is an existing framework **already reused** in Nerelan. Microsoft Agent Framework #1608, OpenAI Agents SDK #1609, smolagents #1643, Pydantic AI #1639, Agno #1616, Mem0 #1655 concern other codebases/ownership. This study maps only Deep Agents' **middleware composition, subagent, Skills, files, summarization** to actual Nerelan seams.
- This issue is a research artifact; the canonical owners remain Goal/TaskStore [#120](https://github.com/dddd2024/Nerelan/issues/120) and current architecture, context [#296](https://github.com/dddd2024/Nerelan/issues/296)/[#642](https://github.com/dddd2024/Nerelan/issues/642), Pack [#253](https://github.com/dddd2024/Nerelan/issues/253), untrusted workspace config [#303](https://github.com/dddd2024/Nerelan/issues/303), sandbox [#299](https://github.com/dddd2024/Nerelan/issues/299), independent evidence [#379](https://github.com/dddd2024/Nerelan/issues/379), model-agent bakeoff [#1527](https://github.com/dddd2024/Nerelan/issues/1527). **Do not duplicate any implementation owner.**

## 1. Precise pinned-source findings by module

| Module / pinned code | Actual behavior | Judgment for Nerelan |
|---|---|---|
| **Harness assembly** [`graph.py:225–295`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/graph.py#L225-L295), [`296–316`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/graph.py#L296-L316), [`920–1045`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/graph.py#L920-L1045) | `create_deep_agent` assembles filesystem, subagent, context summarize, Skills, memory, HITL, refusal and profile-specific middleware, then calls LangChain `create_agent` and returns LangGraph graph. Named override-in-place and required middleware guard. Default graph recursion_limit=9999 (not a product budget). | **BORROW_PATTERN / P1**: thin per-executor harness profile and composable user-configured capability projection. **REJECT** replacing GoalService/TaskStore or treating graph recursion as cost cap. |
| **Subagent context boundary** [`subagents.py:121–205`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/subagents.py#L121-L205), [`900–1030`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/subagents.py#L900-L1030) | ordinary `task` agent gets a new description-only `HumanMessage` plus limited inherited state; `mode=fork` inherits prior parent context (experimental); child checkpoint namespace & tracing metadata include `tool_call_id`, and result becomes parent update. Parent config flows by RunnableConfig. | **BORROW_PATTERN / P1**: child tool-call ID -> Nerelan Task/Run/Goal/accepted artifact link, explicit context visibility/allowed paths. No direct LLM-created subagent shall gain owner authority or unlimited budgets; avoid speculative fork state inheritance. |
| **Remote async subagents** [`async_subagents.py:192–236`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/async_subagents.py#L192-L236), [`860–930`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/async_subagents.py#L860-L930), [`1084–1110`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/async_subagents.py#L1084-L1110) | remote LangGraph server thread/run identity, persisted task projection, `check_async_task` gets fresh observable status; waiting for human distinct from terminal; parent wake notifications and follow-up queue semantics. | **BORROW_PATTERN / P1** for observation/reconcile and user status. **REJECT** treating remote thread as canonical Nerelan TaskStore or assuming remote adapter works with OpenCode/Codex/Claude CLI without explicit translation and auth. |
| **Filesystem permission** [`filesystem.py:375–471`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/filesystem.py#L375-L471) | permission `allow|deny|interrupt`, ordered first-match, both requested and symlink-resolved path checked for deny; if no matching rule, return **allow**. Interactive interrupt is mapped to LangChain HITL by [`_fs_interrupt.py`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/_fs_interrupt.py). | **BORROW_PATTERN / P0** for user-visible approval surfaces, not an Owner policy enforcement replacement. Require Host exact cwd/path/operation grant and filesystem/sandbox control; default allow is incompatible with untrusted worktrees without separate outer gate. |
| **Parallel tool mutation guard** [`filesystem.py:204–230`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/filesystem.py#L204-L230) | rejects later file mutation for same normalized path in a single model response; no guarantee about concurrent workers, worktrees, symlinks/remote task concurrency. | **BORROW_PATTERN / P1**: same-path in-turn duplicate prevention as a guard, not replacement for Nerelan worktree ownership/dirty checks. |
| **Shell backend** [`local_shell.py:256–265,535–549,659–667`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/backends/local_shell.py#L535-L549) | explicit LocalShellBackend is **not default**, but executes `Popen(..., shell=True)` with host user privileges; `virtual_mode` path constraints do NOT constrain shell. | **REJECT direct untrusted execution**: no command/hard sandbox safety merely from middleware; preserve #299 host sandbox, #303 config trust and #447 network/secret admission. |
| **Skills progressive disclosure** [`skills.py:914–1010`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/skills.py#L914-L1010), [`1320–1391`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/skills.py#L1320-L1391), [`_skill_tools.py:265–300`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/_skill_tools.py#L265-L300) | loads `SKILL.md` metadata progressively, surfaces body on demand; recognizes tool calls reading skill path; dynamically discloses tool definitions and can resolve gated tools at runtime. Tool visibility depends on observed skill read, not a host authorization predicate. | **BORROW_PATTERN / P1** Pack/Skill tool schema narrowing; approval must be independently verified at Host tool-call boundary with capability IDs; project-local SKILL file cannot self-grant new external capabilities. |
| **Skills precedence** [`skills.py:1–15`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/skills.py#L1-L15), [`skills.py:443–560`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/skills.py#L443-L560) | multiple sources loaded in order; later duplicate skill name **overrides previous**. `allowed-tools` metadata is parsed and used as recommendation/disclosure info, **not proof of Owner's grant**. | **P0 trust warning**: exactly version/digest bind each source and enforce `DISCOVERED_UNTRUSTED` before activation (#303); refuse silently shadowing trusted skill with workspace-controlled one. |
| **Memory prompt injection** [`memory.py:104–123,346–399`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/memory.py#L104-L123) | memory file text (e.g. AGENTS.md) directly inserted into system prompt and recommends modifying remembered files; own upstream [THREAT_MODEL T1](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/THREAT_MODEL.md#L249-L255) identifies poisoned file injection. | **REJECT trust inheritance**: existing Nerelan [`context_builder.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_builder.py) explicitly `authority=NONE`; only Owner/GitHub/TaskStore are authoritative. |
| **Context compression + offload** [`summarization.py:1–59,141–180`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/summarization.py#L1-L59), [`_message_eviction.py:115–131,260–296`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/_message_eviction.py#L115-L131) | thresholded LLM summary and artifact offload to `/conversation_history/{session_id}.md`; previews show head/tail, path allows selective reread. Summary event has cutoff and file path, not authoritative current Task truth. | **BORROW_PATTERN / P1** for tool-result offload and inspectable omission under controlled backend; protect provenance, digest & access; preserve Nerelan `context_recovery` paid-call reservation and snapshots. |
| **Tools exclusion runtime gate** [`_tool_exclusion.py:34–101`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/deepagents/middleware/_tool_exclusion.py#L34-L101) | tools listed in excluded profile filtered from model request **and rejected again at tool invocation**; required middleware cannot be excluded accidentally by profile. | **DIRECT_PATTERN / P0** two-stage scope filtering and tool-time checks, layered under Nerelan Host, useful for safe capabilities and tools limiting. |
| **Dependency and license** [`pyproject.toml`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/libs/deepagents/pyproject.toml), [`LICENSE`](https://github.com/langchain-ai/deepagents/blob/9a02909f69896ee6bf4cb1e7a41d612ace9c7589/LICENSE) | MIT, Python >=3.11; `deepagents==0.7.39` depends on langchain >=1.5, langchain-core >=1.8, several model SDKs and LangSmith; Nerelan pins `langgraph==1.0.10`, `checkpoint-sqlite==3.1.0` without `langchain` direct dep. | **DEFER SDK INSTALL**: dependency graph, provider-free startup, trace destination and version conflicts must be validated in separate authorized spike. No assumption direct in-process compatibility. |

## 2. Nerelan code map: what is real today, what is missing

1. [`goal_service.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/goal_service.py): durable Goal -> Spec -> Plan -> Tasks, controls launch in Owner window, task identity, routing and retries over existing TaskStore. **ALREADY_IMPLEMENTED**. Deep Agents agent graph cannot replace this without second state authority.
2. [`agent_planner.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/agent_planner.py): independent CLI planner produces bounded JSON plan but only creates PLANNED goal for Owner review. **ALREADY_IMPLEMENTED**; Deep Agents `task(description)` alone does not offer governed Goal approval.
3. [`context_builder.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_builder.py), [`context_recovery.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_recovery.py), [`context_optimization.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_optimization.py): source/scope digest, no-auth summaries, byte-budget projections, durable reservation before paid summarization. **ALREADY_IMPLEMENTED**; adding a second chat summary source would be regression.
4. [`capability_registry.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/capability_registry.py): bounded read-only Pack metadata, not plugin loading/runtime. **MISSING** optional dynamic skill-to-capability **projection** but #253 owns it; approval must remain Host side.
5. [`LANGGRAPH_ORCHESTRATION_BOUNDARY.md`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md): LangGraph workflow nodes/edges/checkpoints are execution aids only; TaskStore is authoritative product truth. **ALREADY GOVERNED**; inner Deep Agents checkpointer is not a replacement.
6. [`pyproject.toml`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/pyproject.toml): `requires-python >=3.13`; `langgraph==1.0.10`, `langgraph-checkpoint-sqlite==3.1.0`; **no direct Deep Agents or LangChain pin**, integration untested.

## 3. User-facing value and proposed architecture

Proposed *future* non-authoritative adapter shape:

```text
Owner-authorized Goal/Task + approved scope
  -> Nerelan capability & executor routing (model quality, quota, true cost)
  -> immutable subagent launch receipt (task_id / parent / worktree / model / limits)
  -> optional DeepAgents-style middleware adapter
       - approved tool catalog projection
       - optional scoped Skills metadata progressively revealed
       - host-guarded file read/write, no raw shell
       - bounded tool-result offload to protected artifacts
       - context read-only packet with digest
  -> parent observes child checkpoint / tool result as untrusted data
  -> Nerelan canonical TaskStore side-effect status / independent check
  -> completion or NEEDS_INPUT / UNKNOWN / RETRY_WAIT / FAIL
```

**End user impact**: clear why worker was delegated, what it may access, whether it waits for approval, where offloaded details are retrievable, and exact accepted result/cost. Without these, a powerful agent harness can appear more autonomous but is not measurably more reliable.

## 4. Minimal test matrix (not run)

- S1 middleware override: untrusted user middleware tries to drop filesystem permissions, trusted tool exclusion must still reject at **actual tool call**.
- S2 Skills shadowing: system skill `deploy` overridden by repo-local `deploy`; discovered but not activated until exact digest/Host approval.
- S3 skill includes `shell` tool without Host capability; read/disclose alone cannot grant it and tool-time guard refuses.
- S4 unrestricted `LocalShellBackend` (without actual sandbox) must be blocked entirely on untrusted repo, even if `FilesystemPermission` says deny `/secrets/**`.
- S5 concurrently two file writes to same real canonical path (aliases/symlink) across children; must respect per-worktree ownership and not rely solely on in-turn guard.
- S6 subagent `fork` with parent hidden data, token/secret/Owner approval; fresh scoped packet must not leak parent-only state.
- S7 crash between remote child run start and Nerelan receipt; recovery reconciles exact `thread_id/run_id` before re-dispatch, no duplicate side effects.
- S8 remote child waiting human should not be counted as terminal; owner prompt is untrusted external request that needs separate approval.
- S9 summary provider 429 after reservation/offload failure; existing receipt survives restart, no accidental duplicate paid calls; offloaded raw evidence remains inspectable.
- S10 malicious `AGENTS.md` or skill body with priority-claim instructions: model-visible content never changes Owner grants or mainline policy.
- S11 provider-free startup/CI with model unset or no key: zero model traffic, zero automatic LangSmith external trace; no unexpected dependency/version failure.
- S12 compare production-like tasks across current Nerelan baseline, targeted middleware-pattern changes, and optional SDK harness (if later authorized), using independently accepted completion rate, quota failure recovery, per-model usage and **real full cost per accepted task**, not agent demo.

## 5. Decisions and boundaries
- **BORROW_PATTERN — highest value**: late tool-time exclusion, skill progressive disclosure, subagent call-id/checkpoint lineage, threshold offload with source refs, visible waiting states and explicit HITL.
- **ALREADY_IMPLEMENTED**: LangGraph, Goal/Task/Run authority, context reconstruction/handoff, bounded summaries, native executor adaptation, scoped Pack metadata.
- **REJECT for Nerelan default**: Deep Agents as top-level coordinator/TaskStore; untrusted LocalShellBackend; implicit Skills/AGENTS authority; default first-match allow treated as security enforcement; `recursion_limit=9999` as budget; arbitrary parent context for fork; unreviewed remote subagent endpoint or LangSmith deployment.
- **OPTIONAL_LATER SDK SPIKE**: only after existing route/429/stall reliability P0 is functional and a controlled import/compatibility test shows no regressions; separate authorized implementation PR with exact dependency bounds and authorization/eval.

This is **STATIC_RESEARCH_ONLY**. No Deep Agents package installed, no tests/executions/Windows sandbox, no provider/model calls, no actual benchmark or evidence of runtime compatibility. No dependency or source edits; no independent review or merge.

## 6. 深一层：按 Agent/插件/文件/记忆接口拆成真实可复用的“薄模式”

### 6.1 Agent profile 与 executor adapter 不是同一个东西

在上游，`create_deep_agent(model, tools, middleware, subagents, skills, memory, permissions, backend, interrupt_on, checkpointer, store)` 是“单个可执行 Agent 图的装配工厂”。它可以决定单个图如何调用工具、何时总结、把哪些技能放进提示词。

在 Nerelan：
- **上层**：GoalService 按 Owner window / Goal / run / task 做调度，记录失败和质量约束，能在多个执行器与账号之间切换。
- **中层**：OpenCode / Codex / Claude Code 作为不同“可执行节点”，各自需要准确的 tool/model/config 能力探测；部分 CLI 已内置自己的 subagent 概念。
- **下层**：适合加工具披露、辅助输出截断、自动建议 ContextSummary、Task->Child tool-call lineage 的 facade。

因此“换上 Deep Agents 便让 Nerelan 有好多 Agent”不是可接受的计划；必须将每个 Agent 的 **执行所有权** 与模型/工具 **上下文工具选择** 拆开。

### 6.2 Skills 加载 / 动态工具披露有两个门

```text
A. Discover (safe read of bounded skill manifest)
    -> Owner-approved source/version/digest + allowed capability ID
    -> render metadata; body only as untrusted read-only context
B. Model requested skill include
    -> expose only previously host-approved tool schema
    -> tool-call boundary re-check host scope/credential/egress/step ownership
    -> invoke approved adapter and record exact operation receipt
```

上游 `_skill_tools.py:265–300` 通过技能文件读取痕迹推断披露节点，`skills.py:1320–1391` 通过 tool resolver 挂上执行 Tool。这个“什么时候展示工具”的技术契约可借鉴；**Host tool allow decision 不是这个文件的职责**。如果把一个不可信 `SKILL.md` 的 `include-tools` 当作 Grant，就会发生 source-to-authority escalation。

研究中还应该区分两种 security：
1. `_tool_exclusion.py` 对 **excluded tool** 做 model-time 和 tool-time 双层拦截，是一个真实运行时门槛；
2. `skills.py` 的动态发现、披露本身，**不能**证明这次工具调用已经获得 Owner grant。

### 6.3 子 Agent 运行权威 / 多模型成本

同步 `task` 的 `lc_subagent_tool_call_id` 与 checkpoint namespace 可以使下游日志从父工具调用关联回去，但是它不是不可变任务主键或授权凭证。若用户未来让 OpenCode/Codex/Claude/Deep Agents 混用，应绑定：
```text
Nerelan TaskID/AttemptID + ParentGoal/Step
  + ParentToolCallID (observed)
  + ChildExecutor/Model/Binding
  + Worktree + exact input artifact / context digest
  + Owner grant/budget/quota reservation
  + Child checkpointer/run identity (observed, non-authoritative)
  + result artifact & independent verification
```

另一个值得明确的差异是 **Deep Agents 高阶 async subagent 主要依赖部署的 LangGraph server**，Nerelan 要做多执行器统一管理，必须保留自己的 adapter/TaskStore。不能直接将异步线程的 `success` 映射成 Goal accepted，也不能拿 cloud session 状态作为本地 stop/retry 的全部事实。

### 6.4 成本机制与产品体验

上游通过 Skills metadata-first、根据模型支持动态工具加入、Prompt cache 感知的顺序、Token 阈值触发 Summary，以及 ToolResult 大正文写文件后显示 head+tail，可明显**减少暴露给模型的内容**。但更多的 summarization calls、异步 Agent fork / remote instances、受保护 offload 存储也有成本。

实际产品比较应同时记录：
- 用户目标完成率（独立 verifier）、失败恢复次数、重复委派次数、人工审批次数。
- 全部 subagent 的输入/输出/缓存 tokens 和真实 Magpie 观测费用；模型降级后质量影响。
- Raw artifact 是否仍可追溯、工具结果是否被非权威摘要误替代。
- “用 middleware 才完成”的新任务数，而不只是“提示词变短了多少”。

## 7. 关键的 4 个实现陷阱

**陷阱 A：Skills 文件覆盖 / prompt injection**。多个源中后加载的同名 Skill 会覆盖早加载版本；即便是看起来无害的项目本地技能，若其文字有权指令注入，模型可能产生不受控动作。Nerelan 的 #303 必须把 exact workspace config/skill 来源当成“需要审批的数据”，而不是已经可信的系统指令。

**陷阱 B：权限表默认放行**。上游 `_check_fs_permission` 在没有匹配规则时返回 `allow`，这对通用开发者 SDK 是可理解的；对 Nerelan 的未授权仓库或外部 Agent 则不能直接作为唯一控制门。上游 LocalShellBackend 的 `shell=True` 还会绕过文件工具路径粒度。拒绝把这个组件在默认安装时暴露给任何未信任的 Code Agent。

**陷阱 C：复制整个 forked parent context**。Fork 方式的子 Agent 继承父子上下文和若干状态字段（会排除部分私有字段，但不是 Nerelan 的 visibility proof）。它是开发者的“便利模式”，不能替代 TaskStore 生成的专用 scope/context packet。跨账号/用户/项目必须由 Host 自己过滤。

**陷阱 D：长文本摘要被当成事实**。上游保留 `SummarizationEvent` 的 cutoff、文件路径并将旧消息 offload；但“能找回历史文本”不等于“当下 HEAD/Goal/Review 仍正确”。Nerelan 现有 `scope_digest` 和 `snapshot_digest` 已能应对来源漂移，这一能力不能被不绑定来源的摘要覆盖。

## 8. 快速迁移选择：下次真实试验从哪里开始

**P0（不等待新依赖）**：对现有可用执行器按 host policy 加上“tool catalog projection / tool-time gate / source digest”观察，先 provider-free 断言工具命名冲突、Skill 未授权、沙箱无法绕过；防止 P0 429/stall 修复被研究挤掉。

**P1（只借鉴，不拉包）**：把执行器输出的大型 ToolResult 先存受保护原件，向模型仅暴露有行号的 head/tail 与 source ref；通过现有 `context_recovery` 读取并保护引用，不增第二数据源。对同一工作流进行 A/B 质量与成本验收。

**P1（只借鉴，先修快照）**：给正在规划的 Pack/Agent profiles 设计 `DISCOVERED -> APPROVED -> ACTIVATED` 以及 tool-time 二次检查，不用 `allowed-tools` 前置文本冒充权限。

**P2（单独授权兼容性试验）**：可在隔离 Python 3.13 环境测试 `deepagents==0.7.39` 与现有 `langgraph==1.0.10`、`langgraph-checkpoint-sqlite==3.1.0` 依赖求解；以纯 in-memory mocked model/backend 检查 SDK 版本和 provider-free/no outbound 特性。**当前没有做这一步**。

**实施顺序原则**：只有独立验收成功任务的质量/总成本/长跑恢复变好，才引入更多运行时代码。未满足时继续复用现有 LangGraph 和薄适配器。

## 9. 核查与风险状态

本报告已完成 **源代码级静态审计**，包括固定上游源码和 `THREAT_MODEL.md`（该 threat-model 是上游项目提供的研究资料，不作为动态攻击成功证据）；与 Nerelan main 固定源码与既有 Issue 核对。未安装/执行 Deep Agents、没有运行 pytest、无提供商调用/Windows 实验/远程 LangGraph 实验/依赖求解/性能基准，也未获得独立审核。GitHub PR 的最终 diff 与 exact-head 状态将在创建后回读。

**本轮精确结论：`BORROW_PATTERN / DEFER_SDK`。研究 Issue 不代表已经批准向宿主注入新工具，也没有权限改变产品级架构、依赖或开始真实消耗。**
