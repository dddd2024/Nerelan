# reverse-agent 架构迁移审计与下一步 24 小时计划

## 0. 文档定位

本文针对当前分支 `codex/control-plane-transition-kernel-v1`，给出一次以**整体架构切换**为主线的审计和下一步实现计划。

本轮不再以修复 `current_state.json`、`artifact_index.json`、closeout、final seal、publication truth 或其他历史状态链为主要目标。旧状态系统只承担临时兼容和高风险授权输入，不再继续扩展为项目总控框架。

本轮的核心问题是：

> 如何让项目从“Decision 驱动全部开发与执行”，开始切换为“GitHub Work Item 驱动工程任务、LangGraph 驱动工作流、BMAD 提供规划输入、reverse-agent Trust Layer 只控制高风险动作和二进制分析可信性”。

---

# 1. 当前审计结论

## 1.1 已完成的有效基础

当前分支已经具备以下可保留能力：

1. 独立的 transition control-plane kernel；
2. typed Decision、command-plan、execution-envelope 和 preflight 模型；
3. fail-closed 的命令授权与路径范围校验；
4. legacy / transition 两种模式的确定性识别；
5. CI、State Gate、Decision Preflight 对 transition 模式的条件分流；
6. 测试依赖通过 `.[test]` 安装；
7. 当前头提交的 CI、State Gate、Decision Preflight 均已成功。

这些能力不应被删除，但其长期定位必须收缩为：

```text
R2 / R3 高风险操作的兼容授权内核
```

而不是继续发展成整个软件开发流程的主运行时。

## 1.2 当前仍未完成真正的架构迁移

当前分支虽然完成了“控制平面可迁移”的基础，但尚未进入新架构本体：

```text
尚未形成 GitHub Work Item 驱动入口
尚未引入 LangGraph 作为工作流运行时
尚未建立统一 Workflow State
尚未实现 R0-R3 风险分类
尚未建立 BMAD planning artifact 输入边界
尚未建立 GitHub truth adapter
尚未建立 Trust Layer 的领域 Schema
尚未把 Decision 降级为仅 R2/R3 使用
尚未形成开发工作流和二进制分析工作流的明确分离
```

因此，当前状态只能定义为：

```text
ARCHITECTURE_MIGRATION_BOOTSTRAP_READY
```

不能定义为：

```text
NEW_ARCHITECTURE_IMPLEMENTED
```

## 1.3 当前最大的结构性风险

### 风险 A：继续在旧治理链上追加功能

如果下一轮继续修 report、manifest、closeout、seal、context sync 等状态文件，项目会再次回到“治理治理系统本身”的循环，无法进入 BMAD + GitHub + LangGraph + Trust Layer 的目标结构。

### 风险 B：Transition Kernel 再次膨胀为新总控框架

Transition Kernel 只应回答：

```text
高风险操作是否获得授权？
命令是否在允许范围？
路径和操作是否越权？
```

它不应负责：

```text
产品需求管理
Story 生命周期
多 Agent 编排
checkpoint / resume
普通开发任务状态
GitHub PR 和 CI 事实
二进制 Claim 与 Counterevidence
```

### 风险 C：目标架构只存在于文档，没有可运行纵向切片

当前最重要的下一步不是继续补充架构说明，而是建立一个最小但真实可执行的架构主干，使以下链路第一次跑通：

```text
GitHub Work Item
→ Planning Reference
→ Risk Classification
→ LangGraph Shadow Workflow
→ R0/R1 直接继续
→ R2/R3 请求 Trust Authorization
→ Deterministic Acceptance Result
```

---

# 2. 下一轮唯一主目标

## Architecture Spine v1

在约 24 小时工作量内，建立新架构的第一个可运行纵向切片。

完成后，项目必须第一次具备以下结构：

```text
BMAD Planning Input
        ↓
GitHub Work Item
        ↓
LangGraph Workflow Instance
        ↓
Risk Classifier
   ┌────┴────┐
 R0/R1     R2/R3
   │          │
直接继续   Trust Authorization Adapter
   └────┬─────┘
        ↓
Deterministic Acceptance Gate
```

本轮不追求完整多 Agent 自动开发，也不接入未知二进制执行。目标是建立正确的架构权威关系和可测试运行主干。

---

# 3. 权威关系

本轮必须把以下权威关系固化为代码和测试，而不是只写在文档中。

| 事实类型 | 唯一主权威 | 本轮边界 |
|---|---|---|
| Product Brief / PRD / Architecture / Story | BMAD planning artifacts | 只作为规划输入，不授权命令 |
| 当前工程工作单元 | GitHub Issue / Work Item | 驱动 workflow instance |
| 工作流状态、checkpoint、resume | LangGraph | 不复制到旧 `project_state` 状态链 |
| Branch、commit、PR、CI | GitHub | reverse-agent 只能保存带来源的 observation |
| R0/R1 普通工程执行 | Work Item + execution envelope | 不要求完整 Decision |
| R2/R3 高风险授权 | reverse-agent Trust Layer | 可复用 transition kernel |
| 二进制 Evidence、Claim、Counterevidence | reverse-agent Trust Layer | 不由 BMAD、GitHub 或 LangGraph断言 |
| 最终合并 | 用户 / GitHub protection | Agent 不自动合并 |

---

# 4. 24 小时实施范围

## 4.1 Work Package A：架构契约和统一状态（约 4 小时）

新增建议：

```text
reverse_agent/architecture/
  __init__.py
  contracts.py
  authority.py
  risk.py
```

核心模型：

```text
PlanningReference
GitHubWorkItem
WorkflowIdentity
RiskTier
ExecutionEnvelope
AuthorizationRequirement
ArchitectureDecision
AcceptanceResult
```

要求：

1. `GitHubWorkItem` 成为普通开发任务的入口对象；
2. `PlanningReference` 只保存 BMAD artifact 路径、摘要和 digest；
3. `RiskTier` 固定为 R0、R1、R2、R3；
4. `AuthorizationRequirement` 明确 R0/R1 不依赖完整 Decision，R2/R3 必须经过 Trust Layer；
5. 所有模型可稳定序列化；
6. 不读取 legacy closeout、seal、report-summary 或 state manifest 来决定工作流是否可以启动。

## 4.2 Work Package B：风险分类与授权路由（约 4 小时）

新增建议：

```text
reverse_agent/architecture/risk_classifier.py
reverse_agent/architecture/authorization_router.py
```

第一版使用确定性规则，不调用 LLM。

建议规则：

### R0

```text
只读研究
PRD / Architecture / Story 生成
代码读取
普通审计
```

### R1

```text
限定路径代码修改
单元测试
格式化
本地静态检查
无网络、无 push、无样本执行
```

### R2

```text
修改 GitHub Workflow
增加或升级依赖
外部网络访问
创建 commit / push / Draft PR
修改权限策略
数据迁移
```

### R3

```text
运行未知二进制
调试器 / 模拟器 / hook
动态探测
样本修改
访问 secrets
高权限远程执行
删除关键状态或数据
```

验收：

```text
R0/R1 → STANDARD_PATH
R2/R3 → TRUST_AUTHORIZATION_REQUIRED
未知或字段缺失 → BLOCKED
```

## 4.3 Work Package C：LangGraph Shadow Runtime（约 6 小时）

修改 `pyproject.toml`，直接引入 LangGraph 作为唯一 Python 工作流运行时。

新增建议：

```text
reverse_agent/workflows/
  __init__.py
  development_graph.py
  state.py
  nodes/
    load_work_item.py
    load_planning_context.py
    classify_risk.py
    request_authorization.py
    acceptance_gate.py
```

第一版 Graph：

```text
START
→ load_work_item
→ load_planning_context
→ classify_risk
→ conditional route
   ├─ R0/R1 → acceptance_gate
   └─ R2/R3 → request_authorization → acceptance_gate
→ END
```

限制：

1. Shadow Mode，不修改源码、不运行 shell、不 push；
2. 使用内存或测试 checkpointer；
3. 所有节点必须是普通 Python 函数；
4. transition kernel 只通过 adapter 被调用；
5. Graph state 是运行时事实源，不把节点状态回写成大量 legacy gate artifact；
6. workflow 可以用相同输入稳定重放。

## 4.4 Work Package D：Trust Authorization Adapter（约 3 小时）

新增建议：

```text
reverse_agent/trust/
  __init__.py
  authorization.py
```

目标：把当前 transition kernel 包装为新架构中的 R2/R3 授权端口。

接口建议：

```python
class TrustAuthorizationPort(Protocol):
    def authorize(self, request: AuthorizationRequest) -> AuthorizationResult:
        ...
```

第一版 adapter 可复用：

```text
TransitionDecision
TransitionCommandPlan
ExecutionEnvelope
validate_transition
```

但必须满足：

1. 新 workflow 不直接依赖 `project_gate.py` 的全部 legacy CLI；
2. adapter 只返回 `AUTHORIZED`、`BLOCKED` 或 `APPROVAL_REQUIRED`；
3. 不读取 final-check、closeout、seal、report-summary；
4. 不把 Decision 作为 R0/R1 的必需输入；
5. 将 transition kernel 明确定位为 compatibility adapter，而不是 runtime。

## 4.5 Work Package E：BMAD 和 GitHub 适配边界（约 3 小时）

新增建议：

```text
reverse_agent/adapters/
  __init__.py
  bmad_planning.py
  github_work_item.py
  github_truth.py
```

本轮只实现结构和 fixture，不进行完整远程自动化。

### BMAD adapter

输入：

```text
Product Brief path
PRD path
Architecture path
Story path
artifact digest
```

输出：

```text
PlanningReference
```

禁止：

```text
BMAD artifact 直接生成命令授权
BMAD artifact 覆盖 GitHub Work Item 状态
```

### GitHub adapter

输入 fixture：

```text
repository
issue_number
head_sha
base_branch
labels
acceptance_criteria
```

输出：

```text
GitHubWorkItem
GitHubTruthObservation
```

GitHub observation 必须带：

```text
source
observed_at
repository
head_sha
```

## 4.6 Work Package F：测试、示例和架构验收（约 4 小时）

新增建议：

```text
tests/test_architecture_contracts.py
tests/test_risk_classifier.py
tests/test_authorization_router.py
tests/test_development_graph.py
tests/test_trust_authorization_adapter.py
tests/fixtures/architecture/
```

必须覆盖：

1. R0 只读任务不要求 Decision；
2. R1 限定代码修改不要求完整 Decision；
3. R2 workflow 修改必须进入授权节点；
4. R3 未知二进制执行必须进入授权节点；
5. 未知风险类型 fail-closed；
6. BMAD artifact 不能授权命令；
7. GitHub observation 不能被本地缓存覆盖；
8. transition adapter 不读取 legacy closeout 状态；
9. Shadow Graph 可完整运行并返回确定性结果；
10. checkpoint 后可以恢复；
11. 相同输入得到相同路由结果；
12. 旧 transition kernel 单元测试继续通过。

---

# 5. 建议时间分配

| 时间 | 工作 |
|---|---|
| 0–2 小时 | 固化模块边界、删除歧义、确定接口 |
| 2–6 小时 | Architecture contracts、risk tier、serialization |
| 6–10 小时 | Risk classifier 和 authorization router |
| 10–16 小时 | LangGraph Shadow Runtime 与 checkpoint |
| 16–19 小时 | Trust Authorization Adapter |
| 19–21 小时 | BMAD / GitHub adapter fixture |
| 21–23 小时 | 集成测试和回归测试 |
| 23–24 小时 | 文档、示例输出、Draft PR 说明更新 |

若实现出现超时，优先级顺序为：

```text
Architecture contracts
> Risk routing
> LangGraph Shadow Graph
> Trust adapter
> BMAD/GitHub fixture
> 文档美化
```

---

# 6. 明确不做

本轮禁止把工作量重新消耗在以下内容：

```text
不修复旧 current_state / artifact_index 的业务内容
不新增 legacy closeout round
不新增 final seal / publication truth 轮次
不重建第二套 checkpoint
不扩展 project_gate.py 成通用 Agent runtime
不实现完整 BMAD 安装和全量模板迁入
不实现多模型自动开发
不调用真实远程 GitHub 写操作
不自动创建或合并 PR
不运行未知二进制
不接 IDA / Ghidra / debugger
不修改 User Solve 和 Web
不实现完整 EvidenceUnit / Claim Graph
不删除旧系统
```

旧状态文件仅在以下情况允许最小修改：

```text
保证当前分支测试和 CI 不被破坏
记录本轮执行事实
提供 transition adapter 的兼容输入
```

不得把它们作为本轮主要交付物。

---

# 7. 交付物

本轮完成后至少应产生：

```text
reverse_agent/architecture/*
reverse_agent/workflows/development_graph.py
reverse_agent/workflows/state.py
reverse_agent/trust/authorization.py
reverse_agent/adapters/bmad_planning.py
reverse_agent/adapters/github_work_item.py
reverse_agent/adapters/github_truth.py
对应单元与集成测试
一个可运行的 Shadow Graph 示例
更新后的架构边界文档
```

示例命令建议：

```text
python -m reverse_agent.workflows.development_graph \
  --fixture tests/fixtures/architecture/r1_work_item.json
```

输出示例：

```json
{
  "workflow_status": "COMPLETED",
  "work_item_id": "GH-ARCH-001",
  "risk_tier": "R1",
  "route": "STANDARD_PATH",
  "authorization_required": false,
  "execution_enabled": false
}
```

R3 示例：

```json
{
  "workflow_status": "BLOCKED",
  "work_item_id": "GH-ARCH-002",
  "risk_tier": "R3",
  "route": "TRUST_AUTHORIZATION_REQUIRED",
  "authorization_status": "APPROVAL_REQUIRED",
  "execution_enabled": false
}
```

---

# 8. 验收标准

本轮只有同时满足以下条件才算完成：

1. 普通工程任务入口已从 Decision 抽象为 `GitHubWorkItem`；
2. BMAD planning artifact 只能提供上下文，不能授权命令；
3. LangGraph 成为新 workflow 的唯一 runtime；
4. R0/R1 与 R2/R3 路径在代码中真实分离；
5. 当前 transition kernel 被包装成 Trust Authorization Adapter；
6. Decision 不再是 R0/R1 的强制前置条件；
7. GitHub branch / PR / CI 事实模型包含来源和 head SHA；
8. Shadow Graph 可以运行、checkpoint、恢复和确定性重放；
9. 没有新增 legacy closeout / seal 修复轮次；
10. 所有新增测试通过；
11. 当前 transition kernel 和相关回归测试继续通过；
12. CI、State Gate、Decision Preflight 保持成功。

---

# 9. 本轮结束后的下一步

Architecture Spine v1 完成后，再进入以下顺序：

```text
1. GitHub Truth Adapter 接入真实只读 API
2. BMAD Planning Adapter 接入真实产物目录
3. LangGraph R0/R1 受限执行
4. Trust Layer Schema Foundation
5. 开发工作流的 Test / Review / Security Audit 节点
6. Draft PR 创建节点
7. 二进制分析工作流
8. EvidenceUnit / Claim / Counterevidence
9. Trust Workbench
```

下一轮不应立即接入完整自动开发或未知二进制执行。必须先证明新架构的权威划分、状态归属和风险路由是稳定的。

---

# 10. 最终审计结论

当前分支的 transition kernel 和 workflow cutover 已经完成其迁移引导作用。它们应被保留，但不再继续扩展为项目总架构。

下一步正确方向不是继续修状态文件，而是实现：

```text
GitHub Work Item 驱动
+ LangGraph 工作流运行
+ BMAD 规划输入
+ reverse-agent Trust Layer 高风险授权
```

24 小时内最有价值的交付不是更多治理 artifact，而是一个真实可运行、可测试、可恢复的 Architecture Spine v1。