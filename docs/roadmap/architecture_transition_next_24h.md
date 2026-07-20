# reverse-agent 门禁自举与 Architecture Spine v1 合并执行计划

## 0. 文档定位

本文是以下 active Decision 的实施说明：

```text
decision_20260720_transition_bootstrap_and_architecture_spine_v1
```

执行权威：

```text
project_state/decision_packet.md
```

命令权威：

```text
Phase A 完成后由当前 Decision 重新生成的
project_state/gates/command_plan.json
```

统一长期路线图位于：

```text
docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md
```

本文将原来分离的两个近期计划合并为一个约 24 小时工程轮：

1. 修复 transition gate 无法启动新 Decision 的自举矛盾；
2. 门禁通过后实施 Architecture Spine v1。

Agent 不得只根据本文绕过 Decision，也不得跳过 Phase A 直接进入 Architecture Spine。

---

# 1. 当前阻塞审计

当前 transition kernel 已经完成 legacy/transition 分流、fail-closed 校验和 CI 接入，但存在两个自举缺陷：

```text
transition-command-plan
= 只读取并复制旧 command_plan.json
= 不会根据 active Decision 生成新计划

transition-preflight
= 写死 codex/control-plane-transition-kernel-v1
= 写死上一轮 allowed paths
= 无法接受新分支和新架构范围
```

因此新的 Architecture Spine Decision 虽然已经上传，但会被旧计划身份和旧分支范围阻塞。

这不是 Architecture Spine 业务实现问题，而是迁移门禁本身尚未成为可复用、数据驱动的控制面。

---

# 2. 合并后的唯一目标

在约 24 小时内完成：

```text
Phase A：Transition Gate Bootstrap Repair
  ↓
当前 Decision 生成当前 Command Plan
  ↓
transition-lint PASSED
  ↓
transition-preflight PASSED
  ↓
Phase B：Architecture Spine v1
```

工作量目标：

```text
Phase A：4–6 小时
Phase B：18–20 小时
总量：约 24 小时
```

范围不足时优先保证 Phase A 完整和 Phase B 的可运行最小纵向切片，不扩张到 BMAD 安装、真实 Agent 执行或 Trust Schema 全量建设。

---

# 3. Phase A：Transition Gate Bootstrap Repair

## 3.1 目标

使 transition kernel 从“为上一轮写死的门禁”变成“可由任意合法 active Decision 驱动的门禁”。

## 3.2 必须实现

### A. 当前 Decision 生成 Command Plan

`transition-command-plan` 必须：

1. 读取 active `decision_packet.md`；
2. 提取 decision/round identity；
3. 提取 allowed paths、forbidden paths、forbidden operations；
4. 生成而不是复制 `command_plan.json`；
5. 输出稳定、可验证的计划摘要；
6. 重复生成结果应一致；
7. 不允许手工编辑冒充生成结果。

### B. 当前 Decision 驱动 lint

`transition-lint` 必须检查：

```text
active Decision identity
current Command Plan identity
Decision status
skill profile
plan schema
plan digest / generation provenance
```

不得再因为继承了上一轮 plan 而永久 BLOCKED。

### C. 当前 Decision 驱动 preflight

`transition-preflight` 必须从 Decision 读取：

```text
required_branch
allowed source/test/doc/state paths
forbidden paths
forbidden operations
legal mainline
```

必须删除或降级以下硬编码事实：

```text
codex/control-plane-transition-kernel-v1
上一轮 TRANSITION_ALLOWED_PATHS
上一轮 TRANSITION_FORBIDDEN_PATHS
```

字段缺失、类型错误、路径规则冲突或 Decision 不明确时必须 fail closed。

### D. 兼容性

```text
legacy mode 行为不变
PR #8 已有 transition Decision 仍可被解析
旧 plan 不能覆盖新 Decision
```

## 3.3 明确授权的自举边界

因为旧门禁无法为新 Decision 生成计划，本轮 Decision 明确授权 Agent 在新 command plan 生成前，只修改以下范围：

```text
reverse_agent/project_gate.py
reverse_agent/control_plane/legacy_adapter.py
reverse_agent/control_plane/models.py
reverse_agent/control_plane/command_authority.py
tests/test_project_gate.py
tests/test_control_plane_transition.py
project_state/gates/command_plan.json
project_state/gates/transition_command_plan_preview.json
project_state/gates/transition_preflight_result.json
```

允许命令仅限 Decision 中的 bootstrap command list。

该例外在以下条件同时满足后立即失效：

```text
当前 command plan identity 正确
transition-lint = PASSED
transition-preflight = PASSED
```

## 3.4 Phase A 验收

1. 新 Decision 能生成新 plan；
2. 换一个 Decision/branch fixture 后计划和 preflight 随之改变；
3. 无需修改 Python 常量；
4. 当前分支 `codex/architecture-spine-v1` 通过；
5. old branch 不再是硬要求；
6. malformed Decision 被 BLOCKED；
7. focused tests 和 `git diff --check` 通过。

Phase A 未通过时必须停止。

---

# 4. Phase B：Architecture Spine v1

## 4.1 目标纵向切片

```text
Planning Reference
→ GitHub Work Item
→ Workflow Identity
→ R0–R3 Risk Classifier
→ LangGraph Shadow Workflow
   ├─ R0/R1 → STANDARD_PATH
   └─ R2/R3 → TRUST_AUTHORIZATION_REQUIRED
→ Deterministic Acceptance Gate
```

这一阶段只建立正确的架构主干，不实现完整多 Agent 自动开发，也不运行未知二进制。

## 4.2 Work Package B1：架构契约

建议目录：

```text
reverse_agent/architecture/
  __init__.py
  contracts.py
  authority.py
  risk.py
```

至少实现：

```text
PlanningReference
GitHubWorkItem
WorkflowIdentity
RiskTier
ExecutionEnvelope
AuthorizationRequirement
AuthorizationRequest
AuthorizationResult
AcceptanceResult
DevelopmentWorkflowState
```

约束：

1. Planning Reference 只提供上下文；
2. GitHub Work Item 是普通工程任务入口；
3. R0/R1 不强制完整 Decision；
4. R2/R3 必须进入 Trust Authorization；
5. 未知字段或缺失 identity 必须拒绝；
6. 所有模型稳定序列化。

## 4.3 Work Package B2：确定性风险分类

建议目录：

```text
reverse_agent/architecture/risk_classifier.py
reverse_agent/architecture/authorization_router.py
```

第一版不调用 LLM。

分类：

```text
R0：规划、研究、只读
R1：限定代码修改、测试、无网络/无 push
R2：Workflow、依赖、网络、commit/push/Draft PR、权限策略
R3：未知二进制、debugger、hook、secrets、破坏性或高权限动作
```

路由：

```text
R0/R1 → STANDARD_PATH
R2/R3 → TRUST_AUTHORIZATION_REQUIRED
unknown/conflict → BLOCKED 或取更高风险
```

## 4.4 Work Package B3：LangGraph Shadow Runtime

建议目录：

```text
reverse_agent/workflows/
  __init__.py
  state.py
  development_graph.py
  nodes/
    load_work_item.py
    load_planning_context.py
    classify_risk.py
    request_authorization.py
    acceptance_gate.py
```

Graph：

```text
START
→ load_work_item
→ load_planning_context
→ classify_risk
→ conditional route
   ├─ standard_path
   └─ request_authorization
→ acceptance_gate
→ END
```

限制：

1. Shadow Mode；
2. 不修改业务源码；
3. 不执行 shell 工具动作；
4. 不访问网络；
5. 不调用模型；
6. 使用内存或测试 checkpointer；
7. 相同输入可稳定重放；
8. LangGraph 是唯一 Python 主运行时。

## 4.5 Work Package B4：Trust Authorization Adapter

建议目录：

```text
reverse_agent/trust/
  __init__.py
  authorization.py
```

接口：

```python
class TrustAuthorizationPort(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        ...
```

输出仅允许：

```text
AUTHORIZED
APPROVAL_REQUIRED
BLOCKED
```

不得读取 legacy closeout、final seal、report-summary、publication truth。不得要求 R0/R1 提供完整 Decision。

## 4.6 Work Package B5：BMAD 与 GitHub 边界

建议目录：

```text
reverse_agent/adapters/
  __init__.py
  bmad_planning.py
  github_work_item.py
  github_truth.py
```

本轮只实现 fixture 和解析边界：

```text
BMAD artifact path / digest / summary
GitHub repository / issue / title / acceptance criteria
GitHub branch / head SHA / PR / CI observation
```

不安装 BMAD，不远程调用 GitHub，不创建真实 Issue/PR。

---

# 5. 测试计划

## Phase A 测试

```text
active Decision 生成新 plan
Decision identity 改变时 plan 改变
branch 来自 Decision
allowed paths 来自 Decision
缺失字段 fail closed
手工篡改 plan 被拒绝
legacy mode 保持兼容
```

## Phase B 测试

```text
模型稳定序列化
planning input 不能授权命令
GitHub observation 带 repository/SHA provenance
R0/R1/R2/R3 分类
冲突时取更高风险
unknown 被阻止
R0/R1 走 standard path
R2/R3 调 Trust Port
blocked authorization 进入 blocked acceptance
checkpoint replay 结果一致
Graph 无副作用调用
```

建议测试文件：

```text
tests/test_project_gate.py
tests/test_control_plane_transition.py
tests/test_architecture_contracts.py
tests/test_risk_classifier.py
tests/test_development_graph.py
tests/test_trust_authorization_adapter.py
tests/test_planning_and_github_adapters.py
```

---

# 6. 执行顺序

```text
1. 确认 codex/architecture-spine-v1
2. 读取 active Decision
3. 只实施 Phase A
4. 跑 bootstrap focused tests
5. 生成当前 command_plan.json
6. transition-lint
7. transition-preflight
8. 三者通过后自举例外失效
9. 实施 Phase B
10. 跑 Phase B focused tests
11. 跑控制平面回归测试
12. git diff --check
13. 在时间允许时跑完整 pytest
14. 更新执行报告
15. push 到当前分支
16. 最多创建一个 Draft PR
17. 停止，等待审计
```

---

# 7. 禁止事项

```text
不跳过 Phase A
不手工伪造 command plan
不保留旧分支硬编码作为 fallback
不修 legacy closeout / seal / publication truth
不安装 BMAD
不引入第二个工作流运行时
不修改 User Solve、frontend、solver、harness
不运行未知二进制、IDA、Ghidra、debugger
不调用模型 API
不访问 secrets
不直接 push main
不 merge、rebase、force-push、tag、release
不自动开始 Trust Schema Foundation
```

---

# 8. 完成标准

全部满足才算完成：

1. transition gate 由 active Decision 数据驱动；
2. 当前 Decision 生成当前 command plan；
3. 当前 lint 和 preflight 通过；
4. Architecture Spine typed contracts 完成；
5. R0–R3 分类确定且 fail-closed；
6. LangGraph Shadow Workflow 可运行、可 checkpoint、可重放；
7. R2/R3 经过 Trust Authorization Adapter；
8. R0/R1 不依赖 legacy closeout；
9. focused tests 和 diff check 通过；
10. 未执行或超时测试被如实记录；
11. 只推送到 `codex/architecture-spine-v1`；
12. 不发生 merge；
13. 完成后停止，等待下一次独立审计。
