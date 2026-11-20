# NVIDIA NeMo Guardrails 0.25.0-rc1 — Nerelan Agent/Tool/Plugin 可信执行边界深审

> [研究 Issue #1665](https://github.com/dddd2024/Nerelan/issues/1665) · 2026-11-17 · R1 纯文档 · 固定来源静态审计 · no runtime approval

# NeMo Guardrails 0.25.0-rc1 — pinned-source agent Hooks, policy defaults, tool-call/result guards and fail-open gaps

Status: PINNED_STATIC_SOURCE_REVIEW; risk R1 DOCS_ONLY; execution authority NONE; test/model-run status NOT RUN. Date 2026-11-17.

## 0. Mandatory duplicate review BEFORE choosing
Read canonical hub [#1576](https://github.com/dddd2024/Nerelan/issues/1576) and 35 prior project research comments. Exact-source Issues/PR/code searches for "NeMo Guardrails" and "NVIDIA-NeMo/Guardrails" found no standalone pinned audit. Other topics' references to guardrails (OpenAI Agents SDK #1609, Agent Zero #1659, MCP Python SDK #1653 etc.) are different codebases. This study is one upstream only. Note upstream name redirects from NVIDIA/NeMo-Guardrails to [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails). No additional implementation owner created.

Fixed [upstream develop@7162b55e8a4496af3480f02e19dd992bd656b20e](https://github.com/NVIDIA-NeMo/Guardrails/commit/7162b55e8a4496af3480f02e19dd992bd656b20e), Python project nemoguardrails 0.25.0-rc1, Apache-2.0 declared in pyproject, Python >=3.11,<3.14. Exact [Nerelan main@6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b](https://github.com/dddd2024/Nerelan/commit/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b). Upstream DEVELOP prerelease, not a confirmed production released version; v0.25 explicitly deprecates direct LLMRails/Colang 2.x.

## 1. Source-verified findings and decisions
1. **Hooks Server / adapter boundary.** [server/hooks/app.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/app.py#L268-L365) offers /v1/hooks/claude-code, /codex, /nemo-relay. [schemas.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/schemas.py#L32-L69) accepts tool_name/input/use_id; [adapters.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/adapters.py#L77-L129) renders native PreToolUse deny vs no decision when allowed. **BORROW_PATTERN P1**: typed per-executor event/outcome adapter with no new Agent runtime; **REJECT** assuming all executors support the same hook/version/tool coverage.
2. **Three-state result.** [checking.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/checking.py#L77-L169) separates allow, deny, error; invalid schema/check failures remain error not consent. [results-and-errors](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/docs/run-rails/using-hooks-server/results-and-errors.mdx#L109-L124) says agents own failure handling. Claude Code default hook failure can let tool run unless onFailure=block; Codex timeout and other errors can let tool run unless command exits 2 **before** its own timeout. Versions in upstream docs: Claude Code >=2.1.295 for onFailure=block; Codex >=0.124.0 (hook coverage/trust evolves). **P0**: Host must make final decision outside optional hook.
3. **Config preflight.** [app.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/app.py#L81-L162) refuses configs that cannot deny, attempts to use unsupported engine, contain dead per-tool rails, global tool rails incorrectly applied to hooks, and ignored main-model tool declarations. [app.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/app.py#L214-L224) refuses allowlist with implicit default allow_unlisted_tools. **BORROW_PATTERN P0** policy-compile/self-test before activation, fail-closed for inactive/unsupported/misaligned configured guards.
4. **Pure tool policy.** [tool_policy.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/tool_policy.py#L41-L92) immutable mapping with allow/deny tool names and **argument names**, blocked before LLM rails. Important actual default allow_unlisted=true; listing allowed_tools without explicitly setting allow_unlisted=false is not an allowlist. Bare allowed tool means any arguments. **BORROW_PATTERN P0** deterministic gate, **REJECT default open** and do not mistake argument-name allowlist for path or network authorization.
5. **Per-tool tool-call rails.** [app.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/app.py#L337-L365) applies deterministic policy before conditional model-free or model-based check_async. The server passes only called tool's name and a **synthetic schema**, not the real executor tool schema; [checking.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/server/hooks/checking.py#L59-L74). **BORROW_PATTERN P1** optional extra risk check, not authoritative schema/path preflight. Per-tool rail may cost model calls/latency, accounting through Magpie only when actually routed/settled.
6. **Tool schema / output safety.** [tool_schema.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/guardrails/tool_schema.py#L356-L440) validates JSON Schema and missing tool, refuses invalid schema. [rails_manager.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/guardrails/rails_manager.py#L713-L795) matches tool_result to prior call, blocks unlinkable results when per-tool result rail applies. **BORROW_PATTERN P1**: tool_id/receipt relationship, untrusted outputs/prompt injection; **DO NOT CLAIM** Hooks Server does tool-result checks: its API only checks PreToolUse.
7. **Critical bypass/failure semantics.** [Codex integration docs](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/docs/run-rails/using-hooks-server/codex.mdx#L61-L129): new/changed hooks may be untrusted/skipped, provider-hosted tools, write_stdin and some paths bypass PreToolUse. [Claude docs](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/docs/run-rails/using-hooks-server/claude-code.mdx), [results](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/docs/run-rails/using-hooks-server/results-and-errors.mdx) document an allow has no permission decision, a server error is non2xx. **REJECT hooks as OS permission sandbox or task authorization**; plugin/config source must be trusted and pinned.
8. **Engine compatibility.** [guardrails.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/guardrails/guardrails.py#L110-L169) generally falls back to LLMRails if IORails unsupported but refuses fallback when per-tool rails would be silently dropped; Hooks Server requires IORails. v0.25 [deprecation.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/nemoguardrails/deprecation.py#L25-L48) deprecates direct LLMRails. **BORROW_PATTERN P1** refuse silently degraded security feature, no whole Colang engine.
9. **Testing, security, resource overhead.** Sources [tests/server/test_hooks_server.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/tests/server/test_hooks_server.py) and [tests/server/test_hooks_tool_policy.py](https://github.com/NVIDIA-NeMo/Guardrails/blob/7162b55e8a4496af3480f02e19dd992bd656b20e/tests/server/test_hooks_tool_policy.py) cover event mismatch, unsupported 422, fail/queue 503, allowlist, secrets-not-in-errors. **Source test inspection only**. External Judge LLM rails add paid calls; regex examples acknowledge easy bypass. **REJECT always-on model gate or extra runtime/process by default**. Small deterministic Host guard and passive checks first.

## 2. Actual Nerelan counterpart (exact main)
- [reverse_agent/platform_v1/opencode_executor.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/opencode_executor.py) thin OpenCode process in approved worktree, defensive output/parsing, execution budget and short-lived binding; executor-specific, not a universal hook manager.
- [reverse_agent/platform_v1/task_runtime.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/task_runtime.py) ExecutorRouter + LocalValidationRunner; support multiple adapters without changing Task API.
- [reverse_agent/platform_v1/run_store.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/run_store.py) TaskStore SQLite + append-only events and durable operation fences; primary authority.
- [reverse_agent/platform_v1/goal_service.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/goal_service.py) Owner-started Goal/Task orchestration, quota/retry/recovery and accepted work.
- [reverse_agent/platform_v1/capability_registry.py](https://github.com/dddd2024/Nerelan/blob/6cb20fc8502fa7ccc1d6a629b0a7a3c8aecf987b/reverse_agent/platform_v1/capability_registry.py) bounded metadata-only Pack registry. No dynamic code here.
- Existing canonical owners (do not duplicate): [#303](https://github.com/dddd2024/Nerelan/issues/303) untrusted project config and exact digest; [#299](https://github.com/dddd2024/Nerelan/issues/299) actual OS sandbox; [#447](https://github.com/dddd2024/Nerelan/issues/447) MCP and tool output egress; [#790](https://github.com/dddd2024/Nerelan/issues/790) MCP lifecycle; [#253](https://github.com/dddd2024/Nerelan/issues/253) Pack, [#1368](https://github.com/dddd2024/Nerelan/issues/1368) real executor capability matrix; [#179](https://github.com/dddd2024/Nerelan/issues/179) host policy/security.

## 3. Nerelan recommended product split
Trusted Host policy from Owner -> strict deterministic tool/action/scope/arguments check -> optional advisory per-tool safety classifier -> executor-native hook policy (where supported) -> OS/process network/fs secret sandbox -> evidence-based independent verifier.
* It is wrong to make "Guardrails said allow" equivalent to Host permission, or run untrusted Python rail modules in trusted control process.
* Treat assistant tool results as untrusted; attach exact tool call ID to sanitization decision, never allow result payload to grant rights.
* Per-executor support must be probed **live**: OpenCode/Codex/Claude have different versions, tool inventories, pre-execution hooks, event path coverage; a managed Codex hook is still not OS isolation.
* For optional LLM rails, record whether check ran, class, latency and real model charge; offline/cheap deterministic rule first, no extra guard cost by default if no benefit.
* Transparent UX: show "denied by Host", "denied by optional rail", "guard checker unavailable", "unsupported tool path" distinctly.

## 4. Provider-free negative tests to implement under owners, NOT EXECUTED
T01 deny unknown/MCP tool when no owner grant; T02 policy has allowlist but no explicit deny-unlisted => reject configuration; T03 allowlisted Bash with secret file path despite allowed argument name => Host must still deny by resolved path; T04 model/tool prompt injection asks to disable guard => no widening; T05 hooks server off/500/503/hangs => Host fail-closed while controller continues recovering; T06 Codex ignored/untrusted hook or timeout must not grant; T07 Codex write_stdin / hosted tools bypass pretool hook => Host/sandbox bounds still hold; T08 Claude onFailure absent => no Host tool execution; T09 per-tool rail named for denied tool => config preflight rejects dead rule; T10 unsupported engine/flow => no silent fallback; T11 tool_result unmatched/ambiguous call ID => reject result trust; T12 policy grant/revocation change between check and exec => bind per-attempt owner epoch/hash; T13 prompt/tool-input never leaked into logs, secrets redacted; T14 regex bypass patterns not relied on as protection; T15 multi-agent profiles with same named tool have separate scope; T16 baseline vs optional guard latency/model fees and independently accepted work per total cost.

## 5. Verdict
**BORROW_PATTERN** (fast config validator, tool-action schema gate, 3-state adapters, result provenance); **ALREADY_IMPLEMENTED** (Owner policy, TaskStore, executors, Pack metadata); **REJECT WHOLE RUNTIME** (new guardrails daemon as sole authority, default-open policy, model-based gate on every tool call); **DEFER OPTIONAL SDK** until isolated deterministic baseline and real security/latency/cost A/B.
No tests/CI, installed package, remote Hook service, executor plugin, paid model, credentials, approval, deployment or merge performed; do not interpret source reads as proof of effective safety.

## 6. 建议 Nerelan 直接参考的最小 API 设计（静态提案，不是实现）

### 6.1 一次工具请求的统一身份

与 NeMo 的 `ToolInvocation(name, arguments, call_id)` 比较，Nerelan 的统一入口应至少包括：
```text
ToolAttempt = {
  goal_id, task_id, attempt_id, owner_grant_epoch,
  workspace_id, workspace_source_digest,
  executor_kind, executor_version, agent_profile_id,
  tool_surface_id, action_id, tool_call_id,
  canonical_arguments_digest, resolved_paths_and_domains,
  budget_lease_id, capability_snapshot_hash,
}
```
这些字段中的身份和权限只能来自受信 Host，**不能**把用户/Agent 控制的请求体里的 `session_id`、`cwd`、`tool_name` 自报当成可靠身份。NeMo hook 的 `tool_name` 以原样匹配，而且服务对 Claude/Codex 附加字段不使用、不同执行器需要独立服务器配置，说明它更像一个工具事件格式转换器，**不是**跨 Agent Host 签名/审计授权。

可读的判定结果也建议保留三态：
```text
ALLOW_ADVISORY  -> Optional rail found no issue; owner grant still required
DENY_POLICY     -> deterministic Host/rail policy denies; no call
ERROR_UNKNOWN   -> missing hook, unavailable rail, invalid schema, queue overflow;
                   privileged call must NOT silently proceed
```
`DENY_POLICY` 与 `ERROR_UNKNOWN` 有不同用户含义：前者是策略明确阻止，后者是安全检查不确定。不要把错误显示成“请求违规”，也不应把错误作为授权例外。

### 6.2 明确两条信任链

**授权链**（必须在真实执行侧强制）：
```text
Owner grant snapshot
  -> Host validates workspace + budget + executor capability
  -> Host checks exact tool/action, target path/network/effects
  -> optional NeMo-style rule or judge (advisory, may only narrow)
  -> executor call / sandbox action
  -> persisted TaskStore receipt and verifier evidence
```

**内容链**（无法通过 pre-tool hook 代替）：
```text
External tool returns HTML / MCP content / file text
  -> associate with original ToolCall ID/attempt
  -> untrusted source type and provenance
  -> optional per-tool-result rail (safety/injection/exfil)
  -> scoped context packet (authority NONE)
  -> planner/reviewer, NEVER new permission
```

NeMo 源码 `rails_manager.py:713–795` 在已有 per-tool-result 规则时拒绝无法唯一关联到先前调用的结果；这对异步 MCP、浏览器多 Tab、外部 API 非顺序返回很重要。但 NeMo Hooks Server 不接收 post-tool result 的路由，所以仅接入 `/v1/hooks/codex` / Claude Code 不是完整的内容信任保护。

### 6.3 为什么值得借鉴它的 config preflight

NeMo `check_hooks_config()` 的核心想法是“宁可拒绝启动，也不要让一个看似启用的安全规则毫无作用”。具体看到了五种静态检查：
1. 强制 IORails 实现，不允许默默回落到不能跑逐工具规则的 LLMRails。
2. 没有可拒绝调用的 policy/rail，则拒绝配置。
3. 只配 `allowed_tools` 却忘了把默认的 `allow_unlisted_tools` 显式改为 false，则拒绝。
4. 给已经被工具策略全部禁用的工具配无效的 per-tool rail，则拒绝。
5. 在 Hooks Server 指定无实际效果的 `main` model/工具声明或全局工具规则，则拒绝。

Nerelan 可以将其用于**Pack / Executor Profile 启用前**的 deterministic validation：未发现执行器有效 hook、无执行时 enforcement、未知 MCP 工具、未确认网络/文件副作用、一致性检查失败，就显示“只读取配置，不能激活”，而不是继续派发。

### 6.4 NeMo tool policy 的准确局限

NeMo 的 `blocked_tools` 和 `allowed_tools` 可以按工具名、参数**名称**裁定，`blocked` 优先，`allow_unlisted_tools` 在 `ToolPolicy` 类上的默认值明确为 true。它无法通过仅列举 `file_path` 参数名称来验证“该路径是否在已授予 worktree 内”，因为 **值** 和路径解析在这个 policy 内并未被强制约束。即使 per-tool-regex 识别了 `.env` 片段，符号链接、相对路径、PowerShell、参数组合、压缩与编码仍是另一层问题。安全边界必须用 Host 解析和 OS sandbox 支撑。

NeMo `tool_schema.py` 的 schema validation 是另一个组件，具有检测 JSON Schema 错误、未声明工具、参数结构错误等确定性能力。Hooks Server 在没有完整工具列表时会合成一个简化工具 schema 供 IORails 运行，不能据此说它验证了执行器/插件原生全部 JSON Schema 或副作用权限。

### 6.5 Hooks 客户端错误路径与业务可用性

<escape>-</escape> Claude Code 的 `onFailure: block` 和 Codex 的 `curl ... --max-time N || exit 2` 是**客户端配置**，并非服务端返回 500 就一定阻止调用。Codex 内置钩子自己的超时发生时甚至可能放行，故 curl 超时必须更早触发。上游 docs 还写明 Codex 项目 hook 需由用户信任，未获信任时可被跳过，部分 hosted/streamed 工具也不触发对应事件。这是部署约束，不能只验证 API 200/deny 就宣称“全面拦截”。

对 Nerelan，减少本地钩子不可用导致长跑卡死的合理方式不是“临时全部放行”，而是：
- Host 维持自己的允许/拒绝/预算与可用工具清单，不依赖附加检查服务；
- 对仅附加低风险内容检查的功能设置清晰超时和恢复类别；
- 对 Owner 必须检查的高风险工具，`CHECK_UNAVAILABLE` 保持未执行、可重试/升级，而不是转成永久任务失败；
- 记一次 TaskStore 事件就够，防重复外部副作用；
- 不在警告/拒绝文本泄漏工具参数中的秘密值。

### 6.6 用户实际能看到的产品价值

用户启用一个新的 MCP Pack 时，不需要懂 Claude/Codex hook 内部细节，界面应显示：
- **这次允许的是谁**：Goal/Task、具体项目、执行器、模型绑定、有效授权窗口。
- **调用什么**：官方 MCP 工具名、工具版本、参数目的、预期访问网络/文件/密钥范围。
- **为什么允许或阻止**：Host Owner grant / workspace policy / optional content rail / executor-native permissions / sandbox。
- **遇到检查失败怎么办**：`CHECK_UNAVAILABLE`、`UNSUPPORTED_HOOK`、`STALE_GRANT`、`INSUFFICIENT_BUDGET` 明确提示，自动重试应限于可证明安全的情况。
- **跟踪是否真的完成**：只有 Host 的执行收据与独立结果验证才能证明成功，NeMo `allow` 不是成功、也不是 Host 许可。

若用户在 Codex 和 Claude Code 间切换，同一 **Owner 业务策略** 应被投影成两个不同 hook 事件/配置；不应维护两套独立可变的授权账本。未安装的 OpenCode hook 接口不能推定存在，必须按 #1368 实际安装版本与真正覆盖的工具逐一验收。

## 7. 低成本实施路线与验收门槛

**A. P0 static profile test / no provider**（#303/#1368/#253）：把工具/功能列表转换成受限 manifest，在真正启动任何 Agent 前验证：未知工具默认不允许、高权限动作需要完整 grant、可执行 hook 缺失不能静默启用、无效 schema 拒绝、项目 config 不可扩大 Owner 权限。复用现有 registry 和 Host policy。

**B. P0 Host runtime control / no second daemon**（#179/#299）：即使 upstream hook 服务死掉/被删除/超时，文件网络密钥边界仍由 Host 和 sandbox 拦住。对 Codex 的 `PreToolUse` 例外如 `write_stdin` 也应有 Host/OS 权限保障。

**C. P1 agent-native compatibility matrix**（#1368）：仅在隔离测试里通过真实安装版 Claude Code/Codex/OpenCode 发出测试工具事件，验证配置来源信任/拒绝状态/跨平台路径/不被 hook 覆盖的入口；明确标记 `NOT_SUPPORTED` 而不是虚假支持。

**D. P1 output content provenance**（#447/#790）：基于原有工具 ID、调用收据、来源系统/消息类型完成 Tool Result 审查；先 deterministic 规则与消毒，再引入可选 LLM 辅助；不可把 HTML、MCP 描述、日志注入当作 Owner 指令。

**E. P2 optional tool content rail A/B**（#379/#1342）：选择有代表性的受控复杂样本做 paired benchmark，指标至少包括应挡拒绝率、误挡正常工具率、p95 工具延迟、额外模型调用与 Magpie 结算、每个独立验收完成任务的完整成本。只有有可证收益才引入 NeMo SDK/独立服务。模型调用应只发生在明确预算内；生产默认无此负担。

## 8. 静态审查证据与没有做的事情

1. 已读取 upstream `server/hooks/app.py`、`tool_policy.py`、`checking.py`、`adapters.py`、`schemas.py`、`guardrails/rails_manager.py`、`tool_schema.py`、`iorails.py`、`guardrails.py`、LangChain middleware、相关 docs、tests 的函数与部分实现。测试目录存在多种用例只是**源码核对**，未运行测试。
2. 已读取 Nerelan 精确 main 的 `AGENTS.md`、`opencode_executor.py`、`task_runtime.py`、`run_store.py`、`goal_service.py`、`capability_registry.py`、`context_builder.py`，以及 #303/#299/#447/#790/#253/#1368/#179 现有 Owner 文档。没有修改这些代码。
3. 没有安装 nemoguardrails、没有启动 8100 hooks server、没有实际启动 Claude Code/Codex、没有获取模型或 API key、没有沙箱验证、没有运行 GitHub CI、没有用真实私有工作区执行危险命令。**不能**以这份研究证明某个生产版本钩子可完整阻断。
4. 本轮无新实施 Owner，仅研究 Issue、docs 报告、研究索引和 Draft PR；不能自动合并、升级真实策略或绕过独立评审。

**结论：从 NeMo 直接学“统一钩子事件 / 确定性裁定 / 错误不可混同许可 / 动态 rail 可选 / 工具输出关联”的模式，始终让 Nerelan Host 保有最终权限、成本和恢复控制。**
