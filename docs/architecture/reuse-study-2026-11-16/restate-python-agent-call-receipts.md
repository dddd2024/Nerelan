<!-- Single-project research snapshot; canonical tracking Issue #1694. No integration authority. -->

# Restate Python SDK — Agent tool-call receipt / transcript commit / restart semantics

> **2026-11-19 · SINGLE_PROJECT / R1 RESEARCH_ONLY / PINNED_STATIC_SOURCE_REVIEW · NOT_INSTALLED · TESTS_NOT_RUN · NOT_IMPLEMENTED · NO R2/R3 AUTHORITY**
>
> **Upstream:** [restatedev/sdk-python@fc7eb19744dea54d4de890070666e1a439514502](https://github.com/restatedev/sdk-python/tree/fc7eb19744dea54d4de890070666e1a439514502), **MIT SDK**. This is **not** a recommendation to adopt Restate Server; the server's BSL-1.1 and Windows/Docker overhead were already screened out in `B-durable.md`.
>
> **Nerelan baseline read:** [main@b48cc9b82893be222e2ccdb307dd4a81bebee935](https://github.com/dddd2024/Nerelan/tree/b48cc9b82893be222e2ccdb307dd4a81bebee935). Version references are file/search snapshots, not runtime or production deployment proof.

## 0. 查重与增量边界

- 查过研究总索引 **#1576** 及后续研究评论、[2026-11-15 持久性横向报告](https://github.com/dddd2024/Nerelan/blob/main/docs/architecture/reuse-study-2026-11-15/B-durable.md)、相关 GitHub Issues；Restate 在横向报告中被 **KEEP / do not adopt**，但无独立 Restate Python SDK Agent 工具收据专项。
- 已有 **DBOS #1623** / **Inngest #1648** 深审；这次不重复选引擎、不重复讨论通用 checkpoint/retry。**新问题**：工具/模型调用已经返回但 Agent transcript 尚未持久化时，重启后的同一逻辑调用该怎样可解释地接续？
- 实施 Owner 沿用 **#1546** durable spike、**#1191** cross-restart dogfood、**#296** context、**#790/#789** connector/hooks、**#1527** agent×model benchmark、**#1575** continuous-run defects；不创建新的实施 Issue。

## 1. 固定源码事实（具体路径）

1. **双阶段证据而非单一“成功”标志。** [`python/restate/agents/_calls.py` L11-L37](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/agents/_calls.py#L11-L37) 的注释明确区分一次 Restate call 已返回和 framework transcript 已保存结果。`_store` L92-L99 在调用前持久化工具调用；`call_of` L144-L189 以 call-id 优先关联早期调用，跨 attempt 也可按 tool + JSON-encoded input 复用原 id；`answered` L126-L135 标记已返回，`settle` L193-L207 **只有 transcript 存了结果才删除 pending call**。
2. **实测边界在上游测试中，而非 Nerelan 实测。** [`tests/agents_tools.py` L203-L271](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/tests/agents_tools.py#L203-L271) 注入“调用返回但结果未入 transcript”的失败，再用新 tool call id 重试，断言两次调用使用原始 idempotency key `req.id:t1`，最后 transcript 存储后 call row 清除。[ `tests/agents_conversation.py` L615-L689 ](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/tests/agents_conversation.py#L615-L689) 区分 `RETURNED_UNRECORDED` 与根本没返回，并只关闭匹配旧 invocation 的 turn。
3. **Agent session 与 context 分离。** [`_conversation.py` L10-L77](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/agents/_conversation.py#L10-L77) 分成 `restate_agent_turns`（prompt/answer/carry）、`restate_agent_items`（message/tool result/compaction）和可选 snapshots；turn 只能有一个 unanswered，`seq` 稳增供 UI cursor。可借鉴投影层，但不是 Nerelan 可直接使用的 SQLite schema。
4. **基础 journal/重试。** [`server_context.py` L895-L941](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/server_context.py#L895-L941) 把 `TerminalError` 记录为终态、`RetryableError`/一般异常作为 transient proposal；[L1008-L1038](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/server_context.py#L1008-L1038) `sys_run` 非 replay 时才执行 closure。[`context.py` L37-L69](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/context.py#L37-L69) exposes bounded run retry options.
5. **重要兼容/负例。** [`sessions/_driver.py` L11-L27, L65-L79](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/sessions/_driver.py#L11-L79) 的 explicit recovery session **每个 attempt 从头执行 handler、并不 replay journal**，且会给 Restate 发送 heartbeat 以允许长 LLM/tool wait。这个 heartbeat 证明 SDK/Handler 存活，不证明模型或账号正在产生真实输出；不能把它当 Nerelan stall liveness evidence。
6. **批准与副作用分离。** [`_tools.py` L708-L736](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/agents/_tools.py#L708-L736) 对 `wait_for` 传 `rejoin=False`，且 `approval` wait 不是 tool 执行成功；工具使用 [L305-L326](https://github.com/restatedev/sdk-python/blob/fc7eb19744dea54d4de890070666e1a439514502/python/restate/agents/_tools.py#L305-L326) `call_of` 和 `answered`。批准证据必须绑定宿主身份/范围/版本与具体 request digest。

## 2. Nerelan 当前已有的约束（不能当新功能重复造轮子）

- [`run_store.py` L2974-L3229](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/run_store.py#L2974-L3229): 已有 `durable_external_operations`, `_record_external_operation` 在调用前事务登记、`require_new` 与 lease-owner/epoch fence、同 key 不同 digest 冲突、PENDING 失去确定结果则拒绝二次 dispatch、终态收据不可变。**ALREADY_REUSED**：intent-first + fail-closed/fencing，不需要引入 Restate 或建第二张账。
- [`model_review.py` L35-L148](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/model_review.py#L35-L148): reviewer RPC 有 intent + saved response/settlement；无回复时可作为 cost-only abandoned case 分类，不可宣称零花费。
- [`run_store.py` L137-L174](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/run_store.py#L137-L174) 的 `pre_dispatch_interruption` 检查 worktree/checkpoint/external-op/lease/claim，[`unattended_coordinator.py` L158-L234](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/unattended_coordinator.py#L158-L234) 在启动时做 fail-closed reconciliation；[orphan_claim_audit.py L162-L202](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/orphan_claim_audit.py#L162-L202) 只出诊断，不放行外部操作。2026-11-17 的恢复测试在 `tests/platform_v1/test_host_interruption_recovery.py`；不是上游验证。

## 3. 分模块复用裁决

| Nerelan 模块 | 源码机制 | 裁决 | 适配工作及风险 |
|---|---|---|---|
| **Agent tool turn / resume** | `_calls.call_of` → `answered` → `settle` | **BORROW_PATTERN / P1** | 在**现有 TaskStore**为 tool intent、remote receipt、transcript commit 建明确三阶段关联；避免“外部调用成功但会话没记录”被当成没执行。明确 trace-id、logical step-id、call-id 和 attempt-id；不得单凭 tool+args 自动重关联有副作用操作 |
| **Context / Memory** | `_conversation` turns/items/snapshot，单调 seq | **BORROW_PATTERN / P1** | 将不可修改原始消息/工具结果、给模型的紧凑投影、UI 游标分离；保留 Nerelan 自身 context owner，不引入 Restate session DB |
| **Plugin / MCP / HITL** | `_tools._once`, `wait_for(approval=True)` | **BORROW_PATTERN / P0 contract** | 宿主授权对应具体 principal+scope+digest+effect_id；审批等待 ≠ 工具返回；多条 tool path 一致执行权限/egress gate |
| **Durable goal / coordinator** | `server_context.sys_run`, explicit recovery | **REJECT DIRECT / P0 no-go** | 不引入 Restate Server、第二 Durable State、第二 Scheduler；Server + SDK 不是安全/Exactly-once 外部副作用替代品 |
| **Cost and liveness** | SDK heartbeat and retry | **BORROW caveat / P1** | 把 Agent heartbeat、模型实际输出、服务端 ack、tool receipt 和 billing evidence 分字段；重试实际成本+UNKNOWN，不把 session alive 当 model alive |

## 4. 明确的 No-go / 尚不能证明

- **不能承诺外部 exactly-once**：远端副作用在“远端已完成，本地收据未持久化”窗口仍可能 UNKNOWN，除非对方提供基于稳定 request key 的幂等/状态回读。Restate journaled `ctx.run` 不是任意 CLI、GitHub 发布、MCP、收费 LLM 请求的跨系统事务。
- **不能直接照搬 input-only rejoin**：`_calls.py` 依据同 tool+JSON input 在跨 attempt 复用 id。对两次有意相同的删除/发送/采购操作可能误合并；Nerelan 的安全身份必须再包含 logical action slot、Owner grant、资源身份与 digest，跨 epoch 严格核查。
- **不复制 SDK heartbeat 作为 Model 进度指标**；可能持续心跳但模型 900s 无输出；应继续沿用现有 stall/quotas 及不同 binding 的恢复策略。
- **Restate SDK 为 MIT，Restate Server 另有 BSL 1.1 和 Windows 本地部署阻力**；许可证与部署问题不因 SDK 模块可读而消失。无安装、性能数据、测试执行或实际成本对照。

## 5. Provider-free 最小验证（尚未运行）

1. **Crash A:** tool intent 已落库，尚未 remote dispatch；检查能否依据本地证据确证“未派发”，否则 UNKNOWN（不重复调用）。
2. **Crash B:** remote 模拟返回、receipt 已落库，transcript 尚未写；同 logical step 恢复应复用 receipt 或标记 `RETURNED_UNRECORDED`，不能再调 tool；人工可见缺失记录。
3. **Crash C:** remote 返回但 receipt 未落库；不能假定未执行。无上游幂等回读就 BLOCKED/UNKNOWN；有 readback 必须匹配 key+digest+principal 后 reconcile。
4. **Identity:** 同 call_id 不同 digest、同 tool+args 但两个独立 action slots、Owner approval 改变、stale lease epoch、批量工具部分成功；均不能错误重放/误合并。
5. **Model economics:** LLM response 丢失/重复，分别记录 executor attempt、gateway request、真实 usage receipt / UNKNOWN，纳入 #1527/#1504 对比，不能用“没落 transcript”掩盖花费。
6. **Process:** 强制杀 host / 睡眠重启，coordinator reconcile 后验证内部未决链的可观察状态、取消与是否仍 runnable；不以定时 sweep 存在作为最终验收。

**成功标准**：provider-free crash fixture 全通过、禁止危险二次副作用、无已有安全门禁降级，并减少“既有成功调用但无会话记录”造成的人工修复。**停止条件**：新三阶段投影增加锁/事务竞态、允许 input-only replay 或出现两个并列权威账本。Owner 可在既有实现 Issue 下决定实验，不由本研究授权实现。

**Research only; issue/PR 不是完成度或集成成功证明。**

---

## 6. Filing / integration status

- Canonical research Issue: https://github.com/dddd2024/Nerelan/issues/1694
- Canonical hub: https://github.com/dddd2024/Nerelan/issues/1576
- This markdown is a **static review report only**. It does not grant adoption of an engine, dependency changes, execution of untrusted binaries, or a decision to merge its own draft PR.
- Changes to production functionality, especially external-operation replay and approval, require the existing owner's issue and provider-free fixtures before adoption.
