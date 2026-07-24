# Architecture Spine 证据完整性与运行时闭环计划 v1

## 0. 文档定位

本文记录对提交 `976122bdaeb98c05f04bcb54affec54d130a8e45` 的独立审计结论，并定义 Architecture Spine v1 的最后一轮定向修复。

本文是路线和验收文档，不直接授权命令执行。执行权威仍然只能来自：

```text
project_state/decision_packet.md
```

本轮继续使用：

```text
repository: dddd2024/reverse-agent
branch: codex/architecture-spine-v1
Draft PR: #9
base: main
```

不创建新分支，不创建第二个 PR，不合并 PR #9。

---

# 1. 审计结论

当前结论：

```text
REWORK_REQUIRED
```

上一轮已经完成了大部分代码结构：

- structured `allowed_commands`；
- command plan 生成；
- execution reconciliation 数据类型；
- capability policy 数据类型；
- path risk floor 计算函数；
- report truth 数据类型；
- focused tests；
- exact-head CI、State Gate、Decision Preflight 均成功。

这些成果保留，不推倒重来。

但是当前还不能接受，原因不是“测试没有绿”，而是机器门禁对实际完成情况仍然存在错误证明。

---

# 2. 审计发现

## F1 — Required command coverage 没有进入 reconciliation

严重度：`BLOCKING`

当前 `reconcile_executions()` 只验证“已经提供的 envelope 是否能在 plan 中找到”，没有验证 command plan 中所有 `required=true` 的命令是否真的出现。

因此，即使 execution log 只有三条 bootstrap gate 命令，也能得到：

```text
POST_EXECUTION_RECONCILED
```

当前 committed execution log 确实只包含：

```text
transition-command-plan
transition-lint
transition-preflight
```

它没有记录实现、focused tests、integration tests、full diagnostic、diff check 或 publication。

修复原则：

```text
matched submitted records != required plan coverage
```

post-execution reconciliation 必须同时证明：

1. 每条观察记录均合法；
2. 所有 required local commands 已完成；
3. 所有 required CI commands 已由对应 exact-head workflow 证明；
4. diagnostic-only 命令允许失败，但必须保留真实结果；
5. optional 命令可以缺失，但不能被报告为已执行。

---

## F2 — Envelope 可通过省略 operations 绕过能力门禁

严重度：`BLOCKING`

当前 execution-log loader 允许以下字段为空：

```text
operations
mutated_paths
started_at
observed_at
```

当前 `reconcile_command()` 仅在 plan 和 envelope 都包含 operations 时才检查 operation under-reporting。

结果是：

- plan 声明 `network_access`；
- envelope 不写 operations；
- reconciliation 不一定报错；
- network/capability policy 又只读取 envelope operations；
- 能力门禁可能被空字段绕过。

修复原则：

1. plan entry 有 operations 时，execution envelope 必须至少完整覆盖 plan operations；
2. plan entry 的 `network_access=true` 必须由 plan 驱动检查，不依赖 envelope 自报；
3. `execution_surface` 必须显式记录，不能仅由 phase 猜测；
4. executed record 的 exit code、时间、head SHA 和 working tree identity 必须存在；
5. 缺失关键字段必须 BLOCKED，而不是用空元组兼容；
6. bootstrap 身份不能由 envelope 中的布尔值自行声明。

---

## F3 — Bootstrap provenance 仍然由调用方自报

严重度：`HIGH`

当前 normal allowed command 与 bootstrap command 在 plan 构建时按 command + surface 去重，并优先保留 normal entry。execution log 随后通过：

```text
bootstrap_exception: true
```

或 `bootstrap_*` phase 自行声明它属于 bootstrap。

这不能证明命令当时确实处于 bootstrap window。

修复原则：

- plan entry 必须有稳定 `command_id`；
- bootstrap authority 必须有独立 `authority_origin`；
- bootstrap window 必须有明确开始/失效状态；
- execution record 只能引用已存在的 command ID；
- bootstrap 状态由 authority state 推导，不能由日志作者决定；
- bootstrap 到期后，任何新的 bootstrap record 都必须阻塞。

---

## F4 — Path risk 已实现函数，但没有接入实际 LangGraph 节点

严重度：`BLOCKING`

`classify_risk()` 已支持：

```text
max(operation_risk, path_risk, capability_flag_risk)
```

但当前 `classify_risk_node()` 仍然只调用：

```text
classify_risk(envelope)
```

没有传入 path risk floor，也没有传入 capability risk。

因此直接测试 classifier 能通过，但真实 workflow 中修改：

```text
.github/workflows/**
pyproject.toml
project_state/decision_packet.md
project_state/gates/**
```

仍可能只按照调用方声明的 operation 分类。

修复原则：

1. workflow state 必须携带 immutable policy snapshot；
2. classify node 必须从 snapshot 读取 path risk floor 和 capability risk；
3. R2/R3 路由测试必须通过完整 graph，而不是只测试纯函数；
4. policy 缺失时 fail closed；
5. 调用方不能直接传入更低的 path/capability policy 覆盖 Decision。

---

## F5 — Preflight 中的 path/reference 检查对 allowed paths 基本失效

严重度：`HIGH`

当前 preflight 先计算：

```text
outside_scope
```

然后只对 `outside_scope` 执行 reference-path 和 path-risk 检查。

这意味着合法 scope 内的敏感路径不会接受 path-risk enforcement；同时如果某个路径同时属于 reference 和 allowed，reference read-only 也不会阻塞。

修复原则：

- scope authorization 与 risk classification 是两件事；
- 路径在 allowed scope 内，只代表“可以考虑修改”，不代表风险为低；
- reference path 与 mutable path 禁止重叠；
- generated gate artifacts 应使用独立 `generated_artifact_paths`，不能同时放入 reference paths；
- path risk 必须检查全部 observed/mutated paths；
- path risk 的结果用于路由或授权，不应简单把所有 R2/R3 路径当成越界。

---

## F6 — Report truth 仍是未接线模块

严重度：`BLOCKING`

虽然新增了 `report_truth.py` 和单元测试，但当前仓库中的：

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
```

仍属于上一轮 Decision：

```text
decision_20260720_transition_bootstrap_and_architecture_spine_v1
```

当前报告没有覆盖本轮实现，没有真实 changed-file inventory，也没有记录当前 head 的本地与远端事实。

修复原则：

1. report truth 必须接入一个真实 project-gate 命令；
2. report 和 pytest result 必须从机器产物生成；
3. 当前 Decision/round/head identity 必须一致；
4. changed files 必须从 activation base 到 implementation head 的 Git diff 生成；
5. 报告不能从计划 scope 推测实际 changed files；
6. 当前轮没有测试证据时不能沿用上一轮测试结果。

---

## F7 — committed execution log 不具备完整证据属性

严重度：`HIGH`

当前日志使用固定生成时间：

```text
2026-07-21T00:00:00Z
```

且没有逐命令：

```text
command_id
execution_surface
operations
mutated_paths
started_at
observed_at
head_before
head_after
stdout_digest
stderr_digest
```

其 `source=observed_codex_tool_transcript` 也没有 transcript digest 或外部来源标识。

修复原则：

- 不再把手工整理的本地日志当成唯一 acceptance evidence；
- Git commit/diff 和 exact-head GitHub Actions 是可重复验证命令的主要权威；
- local execution log 只承担 provenance，并必须满足严格 schema；
- narrative commit message 不属于机器验收证据。

---

# 3. 目标架构：三层证据权威

为了停止继续增加治理税，本轮不再追求“一个 JSON 证明所有事情”，而是明确三层权威。

## 3.1 Repository truth

权威内容：

```text
Decision identity
command plan
Git commit ancestry
actual Git diff
changed paths
local generated artifacts
```

来源：Git object database 和 committed files。

## 3.2 CI truth

权威内容：

```text
required test commands
State Gate
Decision Preflight
exact-head workflow conclusion
workflow/run identity
```

来源：GitHub Actions。

能够在 CI 重跑的测试，不再仅依赖本地 execution log 声明。

## 3.3 Local provenance

内容：

```text
agent/tool commands
local exit codes
local timestamps
local stdout/stderr digests
local head/worktree identity
```

来源：严格 schema 的 execution records。

local provenance 可以支持调查，但不能覆盖 Git 或 CI 的相反事实。

---

# 4. Phase A — Evidence schema 与 bootstrap 关闭

## 4.1 Command identity

每个 command-plan entry 增加稳定字段：

```text
command_id
command
phase
required
required_evidence_source
expected_exit_codes
execution_surface
operations
network_access
authority_origin
```

允许的 `required_evidence_source`：

```text
local_provenance
exact_head_ci
repository_truth
```

允许的 `authority_origin`：

```text
normal_plan
bootstrap_exception
```

## 4.2 Execution record schema

每条 observed execution 至少包含：

```text
command_id
command
execution_surface
operations
mutated_paths
exit_code
started_at
observed_at
head_before
head_after
stdout_digest
stderr_digest
authority_origin
```

关键字段缺失必须 BLOCKED。

## 4.3 Bootstrap 生命周期

引入明确状态：

```text
BOOTSTRAP_OPEN
BOOTSTRAP_EXPIRED
```

bootstrap 只允许完成 evidence schema、pre/post gate split 和 plan regeneration。

当新 plan 生成且 pre-execution gate 通过后，bootstrap 自动失效。后续日志不能自行声明 bootstrap。

---

# 5. Phase B — Pre-execution 与 Post-execution 分离

当前 `transition-preflight` 同时承担 plan 校验和执行后对账，语义混乱。

拆分为：

```text
transition-preflight --mode pre
transition-reconcile --mode post
```

## 5.1 Pre mode

只验证：

- Decision/round；
- branch/base/ancestry；
- plan identity 和 schema；
- allowed/forbidden/reference/generated path contract；
- capability policy；
- bootstrap state；
- 不读取历史 execution log 作为完成证据。

结果只能是：

```text
PRE_EXECUTION_AUTHORIZED
BLOCKED
```

## 5.2 Post mode

验证：

- current execution-record identity；
- required local command coverage；
- required exact-head CI evidence；
- command/surface/operation/network/exit-code 对账；
- optional/diagnostic truth；
- changed-file inventory；
- report identity。

结果只能是：

```text
POST_EXECUTION_RECONCILED
BLOCKED
```

禁止只有三条 bootstrap 命令就得到完整 post reconciliation。

---

# 6. Phase C — Operation 与 Capability 防省略

必须按 plan 驱动，而不是 envelope 自报驱动：

```text
required_operations = plan.operations
observed_operations = execution.operations
```

规则：

1. `required_operations - observed_operations` 非空时阻塞；
2. plan `network_access=true` 时无论 envelope 如何写，都执行 network policy；
3. plan `network_access=false` 但实际 operation 含 network 时阻塞；
4. capability flag 的 operation 不允许通过空 operations 隐藏；
5. `execution_surface` 必须来自记录字段，禁止通过 phase 推断；
6. unknown operation 继续 fail closed；
7. command text、command_id 和 surface 三者必须一致。

---

# 7. Phase D — Runtime risk wiring

## 7.1 Policy snapshot

在 workflow 初始化时生成 immutable `RiskPolicySnapshot`：

```text
decision_id
round_id
path_risk_floor
capability_risk_rules
policy_digest
```

## 7.2 Graph 接线

`classify_risk_node()` 必须显式调用：

```text
classify_risk(
    envelope,
    path_risk_floor=policy.path_risk_floor,
    capability_flag_risk=resolved_capability_risk,
)
```

policy 缺失、identity 不匹配或 digest 变化时 BLOCKED。

## 7.3 End-to-end tests

必须通过完整 graph 测试：

- 普通源码编辑 → R1 standard path；
- workflow path + `source_edit` → 至少 R2 Trust Authorization；
- dependency path + `source_edit` → 至少 R2；
- Decision/gate path → 至少 R2；
- secret/binary/debugger path → R3；
- missing policy snapshot → BLOCKED；
- caller 提供更低 risk hint → 不降低结果。

---

# 8. Phase E — Path contract 修正

Decision contract 使用四组互斥路径：

```text
reference_paths
generated_artifact_paths
allowed_mutated_paths
forbidden_mutated_paths
```

规则：

- reference paths 永远只读；
- generated artifacts 仅允许由对应 generator 更新；
- allowed mutated paths 是实现 scope；
- forbidden paths 永远阻塞；
- 四组中禁止产生语义冲突；
- path risk 对所有 observed paths 计算，包括 allowed paths；
- allowed 不等于 low risk；
- R2/R3 allowed path 必须进入对应授权路线，而不是被 preflight 直接忽略。

---

# 9. Phase F — Report truth 真正落地

新增或完善：

```text
python -m reverse_agent.project_gate transition-report --state-dir project_state
```

该命令生成：

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/changed_file_inventory.json
project_state/gates/reconciliation_result.json
project_state/gates/remote_observation_payload.json
```

## 9.1 Local report

repo 内报告只记录：

```text
LOCAL_VALIDATED
LOCAL_PARTIAL
LOCAL_FAILED
REMOTE_NOT_OBSERVED
REMOTE_PENDING
```

它必须基于 current Decision、current round 和 implementation head。

## 9.2 Remote observation

避免以下循环：

```text
提交报告
→ CI 完成
→ 再提交报告记录 CI
→ HEAD 改变
→ CI 又需要重新观察
```

因此 `REMOTE_PASSED/FAILED` 不再通过新的 repository commit 回写。

远端最终事实记录在 PR #9 的审计评论中，至少包含：

```text
observed_head_sha
CI run id + conclusion
State Gate run id + conclusion
Decision Preflight run id + conclusion
observed_at
auditor outcome
```

repo 内 `remote_observation_payload.json` 只生成待发布 payload，不声称已经观察。

最终 acceptance 由以下组合决定：

```text
committed LOCAL_VALIDATED report
+
exact-head GitHub Actions success
+
PR audit comment bound to same head SHA
```

这样可以结束 exact-head 报告的无限提交循环。

---

# 10. 测试计划

## 10.1 Reconciliation negative tests

1. 只提供一条 required command 时 BLOCKED；
2. 只有 bootstrap commands 时不能 post reconcile；
3. required CI evidence 缺失时 BLOCKED；
4. optional command 缺失允许通过；
5. diagnostic command exit 1 如实记录；
6. command ID 不匹配时 BLOCKED；
7. stale Decision/round/head record BLOCKED；
8. execution surface 缺失或错误 BLOCKED；
9. operations 为空但 plan 非空时 BLOCKED；
10. network operation 被省略时 BLOCKED；
11. bootstrap flag 伪造时 BLOCKED；
12. bootstrap expired 后新 bootstrap record BLOCKED。

## 10.2 Path and risk tests

1. reference/generated/allowed/forbidden 冲突 BLOCKED；
2. generated artifact 只能由指定 generator 修改；
3. allowed workflow path 仍为 R2；
4. allowed secret path 仍为 R3 或禁止；
5. graph end-to-end 路由正确；
6. policy snapshot 缺失 BLOCKED；
7. path risk 不因 operation 低报下降。

## 10.3 Report truth tests

1. report identity 必须是 current Decision；
2. pytest result 不允许沿用上一轮；
3. changed files 精确等于 activation-base diff；
4. local report 不伪造 REMOTE_PASSED；
5. remote payload head 与当前 implementation head 一致；
6. PR audit comment observation head 不一致时不接受；
7. stale workflow run 不支持新 head。

---

# 11. 建议实施顺序

```text
1. 提交本计划
2. 提交新的 active Decision
3. 在 bootstrap scope 内实现 command_id、strict execution schema、pre/post split
4. 生成新 Decision command plan
5. 运行 pre-execution gate
6. bootstrap 自动失效
7. 修复 required command coverage 和 capability 防省略
8. 修复 path contract
9. 将 risk policy 接入完整 LangGraph
10. 将 report_truth 接入 transition-report
11. 生成 current-round local report、pytest result 和 inventory
12. 运行 focused tests
13. 运行 control-plane/graph integration tests
14. 运行 full repository diagnostic
15. git diff --check
16. 运行 post-execution reconciliation
17. push 当前分支
18. 等待 exact-head CI、State Gate、Decision Preflight
19. 在 PR #9 发布绑定当前 head 的独立审计评论
20. 停止
```

---

# 12. 验收条件

只有以下条件全部满足，才能将 Architecture Spine v1 判定为：

```text
ACCEPTED
```

1. command plan 有稳定 command IDs；
2. required local command coverage 完整；
3. required CI evidence 绑定 exact head；
4. execution records 缺关键字段时 fail closed；
5. operation/network/capability 不能通过省略绕过；
6. bootstrap authority 不由调用方自报；
7. bootstrap 已明确失效；
8. pre-execution 与 post-execution 状态分离；
9. path risk 真正接入 LangGraph node；
10. graph end-to-end R0-R3 tests 通过；
11. reference/generated/allowed/forbidden path 语义分离；
12. risk 对全部 observed paths 生效；
13. report truth 已接入实际 generator；
14. report、pytest、inventory 均属于当前 Decision；
15. local report 不伪造 remote pass；
16. exact-head 三项 GitHub checks 成功；
17. PR 审计评论与同一 head SHA 绑定；
18. PR #9 保持 Draft，直到独立审计给出 ACCEPTED。

任一 blocking 条件未满足，结果仍为：

```text
REWORK_REQUIRED
```

---

# 13. 本轮之后

本轮通过后，不再创建新的 Architecture Spine 治理修复轮。

下一步只能是：

```text
1. 将 PR #9 标记为 ready for review 并准备合并；
2. 合并后开始 Evidence Trust Schema Foundation。
```

不得继续扩展旧 closeout、final-seal、state-manifest 或新的平行治理系统。普通工程事实由 Git/GitHub/LangGraph 承担；只有 R2/R3 操作进入精简的 Trust Authorization。