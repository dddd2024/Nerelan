# Agent Zero — 对照 Nerelan 的插件 / Agent / 并行 / 记忆固定源码审计

> [Research Issue #1659](https://github.com/dddd2024/Nerelan/issues/1659) · 2026-11-17 · Docs-only R1 · No runtime permission

# Agent Zero pinned-source deep audit — plugin packages, executable lifecycle hooks, policy, hierarchical agents, parallel jobs and memory

```
RESEARCH_DATE: 2026-11-17
UPSTREAM: agent0ai/agent-zero@ba9b67df0f54ac78106ae85c552ef5d2458f7c9a
NERELAN_MAIN: 5c69e891e3a559a23e7fd4e3115422c057df4438
RISK_TIER: R1_DOCS_ONLY
STATUS: PINNED_STATIC_SOURCE_REVIEW
EXECUTION_AUTHORITY: NONE
TEST_STATUS: NOT_RUN
LANDING_STATUS: DRAFT_PR_REQUIRED / NO_SELF_MERGE
```

## 0. Confirm no duplicate project study before start

Queried [canonical research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) and its **33 previously archived comments**, targeted Issues and PRs matching `agent0ai/agent-zero` / `agent-zero`, plus repository code search. No previous standalone pinned source Agent Zero audit found. Previous Deep Agents #1657, Mem0 #1655, MCP SDK #1653, Graphiti #1612, AG-UI #1600, Paperclip #1562 and Letta Code historical research concern *different repositories*. Tool/agent feature overlap alone is not duplicate-source research. This issue is an incremental research study, not another plugin, memory or orchestration implementation Owner.

Source: [Agent Zero commit](https://github.com/agent0ai/agent-zero/commit/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a) ([MIT](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/LICENSE)); [Nerelan exact main](https://github.com/dddd2024/Nerelan/commit/5c69e891e3a559a23e7fd4e3115422c057df4438). No installation of Docker, plugin zip, Agent Zero launcher, shell hook or model performed.

## 1. Major source-grounded findings

| Upstream component | Exact code evidence / actual behavior | Nerelan judgment |
|---|---|---|
| **Plugin packaging** | [`helpers/plugins.py:74–106`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/plugins.py#L74-L106) defines plugin.yaml metadata, version, per_project / per_agent config, always_enabled, UI capability, git commit; [`plugins/AGENTS.md:19–33`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/AGENTS.md#L19-L33) describes hooks, tools, prompts, skills, agents, config & UI. | **BORROW_PATTERN / P1**: ergonomic Pack manifest & discoverability, owner #253. Do not import plugin runtime or second registry. |
| **Layered plugin activation** | [`helpers/plugins.py:225–230,492–540`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/plugins.py#L492-L540): `usr/plugins` overlays built-ins; enabled by default unless disabled, `always_enabled` hard on; project/profile overrides. [`helpers/plugins.py:623–730`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/plugins.py#L623-L730) scope-aware config. | **BORROW_PATTERN for UI / REJECT activation defaults**: explicit approval and exact hash/version pin; untrusted project override may narrow grants but never widen Owner scope. |
| **Lifecycle hook registry** | [`helpers/extension.py:57–90,167–214`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/extension.py#L57-L90): decorator emits pre/post hooks, mutable args/result and short-circuit; [`helpers/extension.py:228–240,326–369`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/extension.py#L326-L369): load Python classes dynamically from prioritized extension roots, sorted and filename-shadowed. | **BORROW_PATTERN / P1**: named extension events for *passive* context enrichment and bounded app behavior. **REJECT running arbitrary user/project Python hooks inside trusted Host**; no hook may override Owner policy, TaskStore, billing, result verification. |
| **Installer boundary** | [`plugins/_plugin_installer/helpers/install.py:38–52,92–143,184–222`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_plugin_installer/helpers/install.py#L92-L143): manifest schema + ZIP traversal check or clone, move to `usr/plugins`, **then calls `run_install_hook(plugin_name)`**, which executes a plugin hook; update path [`231–277`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_plugin_installer/helpers/install.py#L231-L277) executes pre_update/install hooks. | **P0 REJECT for Nerelan**: no untrusted hooks during install/upgrade, even when ZIP path is clean and manifest valid; use `DISCOVERED -> SCANNED -> OWNER_APPROVED -> ACTIVATED` with code execution only after separate explicit trust, in bounded runtime. |
| **Scan / validator are not hard gates in audited install paths** | [`plugins/_plugin_scan/api/plugin_scan_run.py:18–44`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_plugin_scan/api/plugin_scan_run.py#L18-L44) sends prompt to Agent and returns Markdown report; [`plugin_validator_run.py:18–49`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_plugin_validator/api/plugin_validator_run.py#L18-L49) similar. **Neither path is called by the install functions examined**; scan response lacks machine-enforced `verdict` field despite docstring claiming it. | **REJECT scan-as-authorization**: optional LLM preflight advisory only, not deterministic artifact quarantine, digest signature, grant or sandbox. We did **not** prove an exploit; this is a static control-flow observation limited to reviewed paths. |
| **Tool policy layered visibility/execution** | [`helpers/tool_policy.py:39–73`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/tool_policy.py#L39-L73): policy inheritance by project/profile; [`206–298`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/tool_policy.py#L206-L298): canonical tool IDs incl MCP and action-specific allow/deny, explicit blocks win, then default; [`324–364`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/tool_policy.py#L324-L364): filter disallowed tool prompts. [`_tool_access/default_config.yaml`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_tool_access/default_config.yaml) defaults `inherit/default=allow/mcp_default=allow`. [`_10_enforce_tool_policy.py:1–9`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_tool_access/extensions/python/tool_execute_before/_10_enforce_tool_policy.py#L1-L9) checks at tool_execute_before as an extension hook. | **BORROW_PATTERN / P0** dual model-visible/tool-time policy and per-action IDs; **REJECT default-allow** or depending only on mutable plugin extension hook for authority. The real Host must check immutable grant *outside plugin code* and sanitize egress/arguments. |
| **Hierarchy and profile customization** | [`helpers/subagents.py:44–90,119–155,345–415`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/subagents.py#L44-L90): built-in → plugin → user → project agent profile merging; [`tools/call_subordinate.py:122–215`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/tools/call_subordinate.py#L122-L215): parent/child context IDs, profile, slot, resume vs reset, in-memory running check and chat save. | **BORROW_PATTERN / P1** reusability of role presets, parent/child links, per-project tailored worker; **REJECT** project profile granting new API account, executor, workspace or budget privileges. Product TaskStore is canonical and model routing owns costs. |
| **Parallel tool jobs** | [`helpers/parallel_tools.py:50–74,118–154,196–255`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/parallel_tools.py#L196-L255): in-memory `ParallelJob` state by context, DeferredTask worker, job IDs; forbid nested parallel and certain session mutations, [`315–395`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/parallel_tools.py#L315-L395) refresh/collect/cancel; [`455–535`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/helpers/parallel_tools.py#L455-L535) direct workers and subordinate context. | **BORROW_PATTERN / P1** protect conflicting tools and expose await/cancel/status UI, **REJECT** volatile context dictionary as durable execution authority. For crash/redeploy, existing Nerelan TaskStore claim/lease/attempt/receipt + reconcile must remain. |
| **Memory consolidation** | [`plugins/_memory/helpers/memory_consolidation.py:18–110`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_memory/helpers/memory_consolidation.py#L18-L110): MERGE/REPLACE/KEEP_SEPARATE/UPDATE/SKIP and 60s timeout; [`434–507`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_memory/helpers/memory_consolidation.py#L434-L507) LLM decides action; [`576–608,611–675`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/plugins/_memory/helpers/memory_consolidation.py#L576-L675) **delete old before inserting new** in merge/replace; LLM metadata wins conflict. | **BORROW_PATTERN for candidate conflicts / P1**, **REJECT authoritative destructive merge**. Preserving evidence & source-bound approved experience (#379) requires immutable originals, atomic or repairable index, supersession instead of pre-delete. |
| **License and runtime shape** | [MIT license](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/LICENSE), [`requirements.txt`](https://github.com/agent0ai/agent-zero/blob/ba9b67df0f54ac78106ae85c552ef5d2458f7c9a/requirements.txt): Docker, Flask, FAISS, LiteLLM, MCP, browser, document parsing, Whisper, many SDKs; README documents Docker-based Linux desktop. | **REJECT whole-stack import**: broad service/runtime and dependency footprint, possible duplicate model gateway with Magpie. No direct integration without isolated SPIKE, security, license and all-in accepted-task-cost evidence. |

## 2. Nerelan actual code and permanent owners

| Nerelan current main | Current implementation (source inspected) | Appropriate reuse boundary |
|---|---|---|
| [`capability_registry.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/capability_registry.py) | Metadata-only capability manifest, bounded JSON, intentionally **not** package manager or dynamic plugin runtime | Extend #253 Pack catalogue with descriptive version/source/trust/activation, not executable hooks |
| [`goal_service.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/goal_service.py) | Persistent Goal→Spec→Plan→Tasks over TaskStore; Owner window, retries, model/executor routing | Parent/child Agent profile selection inside authenticated Goal/Task work, not independent Agent Zero scheduler |
| [`run_store.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/run_store.py) | SQLite append-only task/attempt/event store, stable idempotency keys and replay | No separate in-memory authority for async tool/child run status |
| [`agent_planner.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/agent_planner.py) | Read-only native-CLI planner in detached worktree, bounded JSON plan still subject to GoalService, Owner approval | Project-specific Agent role presets as **input** for routing and planning, not planning approval |
| [`context_recovery.py`](https://github.com/dddd2024/Nerelan/blob/5c69e891e3a559a23e7fd4e3115422c057df4438/reverse_agent/platform_v1/context_recovery.py) | Digest-bound, authority=NONE context recovery; paid summary reservation recorded in existing TaskStore | Recall accepted experience from #379, keep source-trust and freshness; no Agent Zero second memory truth |

Existing owners (not duplicate implementation Issues): [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack and reusable capability packaging; [#303](https://github.com/dddd2024/Nerelan/issues/303) pre-execution workspace/plugin config trust; [#299](https://github.com/dddd2024/Nerelan/issues/299) OS execution sandbox; [#379](https://github.com/dddd2024/Nerelan/issues/379) memory admission; [#260](https://github.com/dddd2024/Nerelan/issues/260) project UX; [#1368](https://github.com/dddd2024/Nerelan/issues/1368) all-executor/native subagent matrix; existing Goal/P0 long-run owners for durable runtime. **No new runtime, central plugin daemon, duplicate store/gateway.**

## 3. Concrete copy/not-copy design

Proposed future **Pack + Agent Profile + Tool Approval** split:

```text
(A) DISCOVER metadata-only:
    plugin.yaml manifest, source commit/signature/digest, requested capabilities,
    tool names/actions, model/provider needs, scripts, hooks, network/fs/secret access
(B) QUARANTINE static review (optional LLM advisory plus deterministic checks):
    no install hook execution, no dynamic import, no project config evaluated as code
(C) OWNER_APPROVE / HOST_GRANT:
    immutable exact version+workspace scope+allowed operations / egress / budget
(D) ACTIVATE under bounded tool adapter:
    Host enforces every tool call, records receipts; changes require new grant
(E) REVOKE / DRAIN:
    disable new calls; reconcile existing receipts and side effects before cleanup
```

Agent Zero's plugin config keys are suitable UI inspiration, but **Nerelan Pack must also ship evaluator fixtures, accepted artifacts, capability health, cost and failure taxonomy** (existing #253). Native executors are independent backend adapters; they should not be forced inside Agent Zero's chat context or Linux workstation.

## 4. Proposed provider-free regression tests (NOT RUN)

- T1 `plugin.yaml` valid and ZIP traversal-safe but Python `hooks.py` malicious: no code import during DISCOVER / SCAN / APPROVE, no subprocess/env read/outbound even if plugin claims trusted.
- T2 plugin scan model claims `safe` but source changes SHA before activation: host must reject digest mismatch; scan output has no authority.
- T3 user or project overlays a builtin plugin or agent profile: cannot raise capabilities; source priority must be auditably visible.
- T4 tool `code_execution:terminal` blocked but tool overall visible: tool action is denied even through alternate route, extension order or direct API.
- T5 default policy missing/corrupted: fail closed, including MCP tools, shell, credentials and network.
- T6 two concurrent child agents mutate one worktree/path: no silent overwrite; host owns claims/workspaces.
- T7 process crash after parallel job launch but before worker receipt: reconcile by durable TaskID/AttemptID and external effect identity, no duplicate provider request or false `completed`.
- T8 duplicate child context IDs, resume/reset and stale profile: rejected if parent/role/scope no longer active.
- T9 memory MERGE deletes old records then new insert fails: evidence remains intact, accepted memories superseded not deleted; negative examples retained.
- T10 model-produced plugin skill instructions / memory update claiming Owner grant: cannot elevate privileges.
- T11 same accepted work suite with/without optional Pack/plugin projection: benchmark accepted task success, tool availability, over-privilege rejects, repeat failures, token+latency+actual spend; compare to existing Nerelan baseline.
- T12 long-running provider-free CI and restarted host: no 3rd party plugin code, no model/provider/network activity on startup.

**Experiments NOT EXECUTED:** no local test suite, test server, Docker/launcher, installed Agent Zero, zip/git plugin import, arbitrary hook, remote scan, memory embedding, API key, provider/model, cost benchmark, security exploit or independent review. This is a static code-path audit, not a vulnerability disclosure or proof of runtime failure.

## 5. Decision

**`BORROW_PATTERN / REJECT_RUNTIME_CLONE`**. Priority:
1. **P0 trust**: separate Pack metadata discovery from dynamic execution, require immutable grants and tool-time checks; keep model scanner advisory. Owner #303/#253.
2. **P1 UX**: plugin catalog and enable/disable/project-level per-agent settings, explicit capability lists and irreversible-actions warnings. Owner #260/#253.
3. **P1 Agent tooling**: subordinate profiles, parent call ID and safe await/cancel for verified durable tasks. Owner #1368 and existing Goal.
4. **P1 memory**: conflict classifications + LLM candidate review, never destructive replacement of accepted source facts. Owner #379.
5. **P2** isolated optional Agent Zero execution adapter **only** if a representative successful-task all-in cost and security review demonstrates benefit over reuse of simpler subcomponents. No need to install entire runtime as a general Nerelan dependency.

Final invariant: the system must remain able to select any real executor, route via Magpie without duplicating account authority, and finish accepted tasks over crashes/restarts under Owner grants. An Agent Zero plugin install or saved chat is not a Nerelan accepted Task receipt.

## 6. 直接从用户角度拆功能包，而不是一个“大 Agent 全家桶”

### 6.1 Pack 列表页应呈现的真实信息

Agent Zero 已有的 UI 基础值得借鉴：名称、描述、版本、作者、Git commit、激活开关、项目/Agent 配置入口、是否有 WebUI/README/license。对 Nerelan，光能展示“支持一个 Tool”还不够，应该最小补充：
- 来源与固定 Revision/Digest、上次检测日期；插件修改需要新的许可。
- **权限差异**：安装前后新增哪些文件访问、网络域、凭据、运行命令和工具 action。
- **状态四分法**：DISCOVERED（仅元数据）、PENDING_REVIEW（等待信任）、APPROVED（有明确授权但尚未激活）、ACTIVE（在某个具体 Project/Agent/Window 下允许被调用）。不能用一个 Enabled 布尔同时表达所有含义。
- **观察面**：最近一次插件方法调用的 Host 收据、上次退出状态、是否存在挂起外部副作用、成本与 quota 归属。不能把它误当成执行已成功。
- 使用者能看懂的审批差异：“此插件要读取仓库并在本地执行 Python；你的当前工作区授权仅允许只读检索，启用会扩大权限，因此需要单独确认”。

这里的功能是 #253/#260 的产品实现提案，并非本轮已实现的 UI。

### 6.2 三种扩展边界

1. **纯数据型 Pack**：JSON manifest、只读技能说明、prompt、可用工具 ID、静态元数据、测试样例。最适合当前 Nerelan，`capability_registry.py` 已有基础。
2. **代理型工具适配**：MCP/外部 API/沙箱进程；Token 和实际账号存留 Host/Magpie，需逐调用授权与可重试收据。适合后续已明确 owner #790/#253。
3. **代码型插件 / 生命周期 Hook**：任何 `hooks.py` / Python class / 用户脚本都应被视为高风险动态代码，需要独立沙箱或可信包审查；绝不导入到处理 Owner 审批、TaskStore 或密钥的进程。上游插件可任意执行 Python 的便利，不能照搬成 Host 默认。

Agent Zero 的 `@extension.extensible` 前后 Hook、按优先级覆盖同名扩展文件、局部项目/Agent 动态源是实现灵活性的来源，同时也是额外的执行攻击面。Nerelan 最佳用法是声明式扩展事件，例如 `before_model_context`、`after_tool_result`、`after_task_evidence`，只接受 Host 决定的数据结构；不能支持自定义 Hook 覆盖 `authorize_tool`、`accept_verdict`、`record_cost` 或 `grant_owner_window`。

### 6.3 主项目层 Agent 体验

Agent Zero 的 `subagents.get_agents_dict()` 通过 builtin/plugin/user/project 层合并 profile，`tools/call_subordinate.py` 通过上下文 ID 和父 Agent 编号确认子会话归属。这适合形成“选择代码修复 Agent、调研 Agent、评审 Agent”的可编辑角色列表。

对 Nerelan 最大价值是独立分清：
```text
AgentProfile      = 模型/执行器适用性偏好 + 工具视图 + 任务模板
AvailableExecutor = 当前本机/远端真实可用 adapter
ModelBinding      = 当前账号额度与性能/费用状态
GoalTask          = 已授权工作、可恢复任务的唯一身份
```

AgentProfile 不应该隐含“即使用主账号额度耗尽，也可以随意启动一个其他订阅 Agent”。模型、账户、软件执行器的实际选择必须由 TaskService/GoalService/Magpie 根据当前信息裁定，不能仅凭项目/用户配置覆盖的 agent.yaml。#1368 负责实测所有实际可用 Agent 的自身子 Agent 接口，避免一刀切假设支持调用。

### 6.4 并行操作的界限

上游 `parallel_tools.py` 的禁止嵌套、禁止在并行里做某些 session reset/output、允许取消后台 job 和列出工作状态，是简单清晰的 UX 设计。缺陷不在 UX，而在它的 `_jobs_for_context()` 把 Job 对象保存在 AgentContext 的 Python dict 里，并把 `DeferredTask` 放进字段。进程退出后，这些对象本身不能成为 Nerelan 的恢复凭证。未来界面可保留这些按钮，但按钮针对现有 TaskStore attempt/receipt 与实际 executor 句柄，**不能对旧 job_id 盲重试**。

### 6.5 记忆与知识质量

Agent Zero 的 MERGE/REPLACE/KEEP_SEPARATE/UPDATE/SKIP 比单纯 append 更丰富，但它并不能为用户承诺可追溯的“事实版本”。MERGE/REPLACE 在删除旧向量记录后写入新记录，任何中间失败都可能导致记忆不可恢复；LLM 生成的 metadata 合并时优先级更高。Nerelan 可以借鉴五种**候选决策**，但权威的旧 run/goal/evidence 不能被 model output 覆盖；#379 的记忆准入和失效链应拥有最终控制。

## 7. 更高价值的产品对比样例

### 场景 A：用户第一次添加“安全扫描 Pack”

Agent Zero 风格会让用户从 Hub 安装，展示插件图片和设置，再启用。Nerelan 应额外让用户在确认前看到：扫描器读取哪些目录、会不会联网、是否安装二进制、是否需要密钥、能否通过当前 sandbox 运行、是否引入持续进程、如何退出/撤销。若当前只有只读授权，系统仍可 DISCOVER，但应保留 PENDING_APPROVAL、不能执行安装 Hook。用户看得到“为什么没启动”和“如何批准”，而不是点后静默失败。

### 场景 B：用户让几个 Agent 同时调研并开发

可以借鉴上游父子 context ID、并行工具排除项、待收集/运行中/失败的易读状态，以及 profile 的受控参数。但每个真实工作应绑定单独 TaskID/AttemptID 和成本预算，避免内存并行 job 在重启后失联。子任务返还一句“完成了”只能成为未经验收的输出，必须经已有 verifier 和 accepted artifact 才是 Goal 前进。

### 场景 C：用户长期运行，自主总结经验

上游会找相似记忆并让 LLM 判断替换/合并、更新。Nerelan 适合在成功任务、审查否决、配额阻塞等真实收据之后提出记忆候选，并用当前仓库版本、实际执行器和观测成本过滤；过期或冲突先降级，不对已有证据做破坏性覆盖。受益标准是再次遇到同类问题时，能否**更少失败、更快恢复、更低真实成本完成独立验收**。

## 8. 为什么本轮优先不做插件系统实施

- 当前 (main@5c69e891) 的 `capability_registry.py` 是有意设计的非执行元数据清单，改成动态导入框架会扩大信任边界，属于新的实施级风险。
- P0 持续运行时的 429、stall、quota、task retry 和真实验收仍直接影响 Nerelan 能不能完成任务，比丰富的插件商店更紧要。
- Agent Zero 全量依赖含 Docker / Flask / LiteLLM / FAISS / MCP / Browser / voice / office parsing，与 Nerelan 薄适配/Magpie/现有宿主大幅交叉，迁移成本和安全面远超单模块拷贝。
- 具体实现应先挑三个极薄可验证片段：**声明式扩展事件、工具 action-level 解释型政策 UI、Agent profile 管理**；任何一个都必须以 Host 安全/TaskStore/成本基准做独立验收。

## 9. 本轮验证边界

全部判断来自固定上游 Commit 与 Nerelan 固定 baseline 的 GitHub 源代码和 Issue 文本。并没有下载和运行 agent-zero 镜像、安装工具、执行它的插件钩子、测试其内存数据库、验证插件扫描器的实际安全性或做任何模型调用；安全结论是静态控制流审计观察，不等同于成功利用或真实事故。

**最终结论：`BORROW_PATTERN` 插件元数据+项目/Agent 配置/工具 action 策略与用户体验；`ALREADY_IMPLEMENTED` Host TaskStore、计划与上下文重建；`REJECT` 默认执行外部插件代码、默认放行、独立并行任务状态/记忆真相、重造网关/全量 Linux 桌面。**
