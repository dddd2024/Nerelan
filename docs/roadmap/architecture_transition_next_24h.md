# reverse-agent 架构迁移下一步 24 小时计划

## 1. 文档定位

本文是 `decision_20260720_architecture_spine_v1` 的规划说明文档。

执行权威仍然是：

```text
project_state/decision_packet.md
```

命令权威仍然是 Agent 在本轮开始时重新生成的：

```text
project_state/gates/command_plan.json
```

本文用于解释为什么这样拆分、24 小时内应交付什么，以及哪些内容必须延后。Agent 不得只根据本文绕过 Decision 执行。

## 2. 当前审计结论

PR #8 已经完成架构迁移前置基础：

- 独立 transition control-plane kernel；
- typed Decision、command-plan、execution-envelope 和 preflight；
- fail-closed 命令授权；
- legacy / transition 模式识别；
- CI、State Gate 和 Decision Preflight 分流；
- 三个远端工作流成功。

但这些只说明旧系统已经具备迁移出口，不代表目标架构已经实现。

当前缺少：

```text
GitHub Work Item 驱动入口
LangGraph Workflow State
checkpoint / resume
R0-R3 风险分类
BMAD planning 输入边界
GitHub truth adapter
Trust Authorization Port
开发工作流与二进制分析工作流分离
```

因此当前阶段定义为：

```text
ARCHITECTURE_MIGRATION_BOOTSTRAP_READY
```

而不是：

```text
NEW_ARCHITECTURE_IMPLEMENTED
```

## 3. 下一轮唯一目标

实现 `Architecture Spine v1`：

```text
BMAD Planning Reference
        ↓
GitHub Work Item
        ↓
LangGraph Workflow Instance
        ↓
Deterministic Risk Classifier
   ┌───────────────┐
   │               │
 R0 / R1         R2 / R3
   │               │
Standard Path   Trust Authorization Port
   └───────┬───────┘
           ↓
Deterministic Acceptance Result
```

这是目标架构的第一个可运行纵向切片，不是完整的自动开发系统。

## 4. 权威划分

| 事实类型 | 主权威 | 本轮要求 |
|---|---|---|
| Product Brief、PRD、Architecture、Story | BMAD planning artifact | 只读输入，不能授权命令 |
| 当前工程工作单元 | GitHub Work Item | 生成 workflow identity |
| workflow 状态、checkpoint、resume | LangGraph | 不复制到旧 closeout 状态链 |
| branch、commit、PR、CI | GitHub | reverse-agent 仅保存带来源 observation |
| R0/R1 普通工程任务 | Work Item + execution envelope | 目标设计中不依赖完整 Decision |
| R2/R3 高风险任务 | reverse-agent Trust Layer | 必须显式授权 |
| 二进制 Evidence、Claim、Counterevidence | reverse-agent Trust Layer | 本轮只保留边界，不实现业务 Schema |
| 最终 merge | 用户和 GitHub protection | Agent 不自动合并 |

## 5. 24 小时工作包

### 工作包 A：架构契约，约 4 小时

建立：

```text
reverse_agent/architecture/
```

定义：

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

验收：

- 可稳定 JSON 序列化；
- 有 schema version；
- 不读取 legacy closeout、seal、report-summary、context 或 state manifest；
- PlanningReference 永远不能成为 command authority；
- GitHubWorkItem 身份不完整时 fail closed。

### 工作包 B：风险分类与授权路由，约 4 小时

第一版只使用确定性规则。

风险等级：

```text
R0：只读研究、规划、代码阅读、审查
R1：限定路径编辑、本地测试、格式化，无网络、无 push、无样本执行
R2：Workflow、依赖、网络、commit/push/Draft PR、权限策略、迁移
R3：未知二进制、debugger/emulator/hook、动态探测、secrets、破坏性操作
```

路由：

```text
R0/R1 → STANDARD_PATH
R2/R3 → TRUST_AUTHORIZATION_REQUIRED
未知、缺失或冲突 → BLOCKED
```

### 工作包 C：LangGraph Shadow Runtime，约 6 小时

引入 LangGraph 作为唯一 Python workflow runtime。

建立：

```text
reverse_agent/workflows/
```

Graph：

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

- Shadow Mode；
- 不执行 shell；
- 不修改源码；
- 不 push；
- 使用内存或测试 checkpointer；
- 相同输入必须可稳定重放；
- checkpoint/resume 必须有测试。

### 工作包 D：Trust Authorization Adapter，约 3 小时

建立：

```text
reverse_agent/trust/authorization.py
```

将 PR #8 的 transition kernel 包装成窄接口：

```text
AuthorizationRequest
→ TrustAuthorizationPort
→ AUTHORIZED / APPROVAL_REQUIRED / BLOCKED
```

边界：

- 不修改 `reverse_agent/control_plane/**`；
- 不导入完整 legacy closeout 生命周期；
- 不读取 final-check、seal、report-summary、context 或 state manifest；
- 不让 Decision 成为目标架构中 R0/R1 的必需输入。

### 工作包 E：BMAD 与 GitHub adapter，约 3 小时

建立：

```text
reverse_agent/adapters/bmad_planning.py
reverse_agent/adapters/github_work_item.py
reverse_agent/adapters/github_truth.py
```

本轮只处理 fixture 和结构化输入，不做完整远程自动化。

BMAD adapter：

- 读取 Product Brief、PRD、Architecture、Story 的路径、摘要和 digest；
- 不安装 BMAD；
- 不生成命令权限。

GitHub adapter：

- 读取 repository、item number、acceptance criteria、requested operations、requested paths；
- 身份缺失即阻塞；
- branch、commit、PR、check 必须带 source 和 observed-at；
- observation 只是缓存，不是真相源。

### 工作包 F：测试、CI 与架构文档，约 4 小时

新增测试：

```text
tests/test_architecture_contracts.py
tests/test_risk_classifier.py
tests/test_development_graph.py
tests/test_trust_authorization_adapter.py
tests/test_planning_and_github_adapters.py
```

更新 CI，使新架构测试在 clean runner 中执行。

增加：

```text
docs/architecture/architecture-spine-v1.md
```

## 6. 必须验证的场景

1. 只读审查被分类为 R0。
2. 指定路径本地修改和测试被分类为 R1。
3. 修改 Workflow 或依赖被分类为 R2。
4. 运行未知二进制被分类为 R3。
5. 未知操作或字段冲突被阻塞。
6. R0/R1 不调用 Trust Authorization Port。
7. R2/R3 必须调用 Trust Authorization Port。
8. `BLOCKED` 不能进入 accepted。
9. `APPROVAL_REQUIRED` 不能被包装为 executable。
10. transition kernel adapter 保持 fail closed。
11. Graph 节点不执行 shell，不修改仓库。
12. 同一 fixture 的最终状态可重放。
13. checkpoint/resume 得到相同终态。
14. BMAD planning reference 不能授权命令。
15. GitHub observation 不能覆盖 GitHub 真相。
16. PR #8 已有 transition-kernel 测试保持通过。

## 7. 明确不做

本轮不做：

```text
旧 closeout / final seal / publication truth 修复
旧 project_state 扩展
BMAD 正式安装和完整流程迁入
Microsoft Agent Framework 双运行时
自由多 Agent 自动写代码
真实 runner dispatch
模型 API 调用
未知二进制执行
IDA / Ghidra / debugger 接入
Binary Evidence Firewall
Claim / Counterevidence Graph
User Solve 迁移
Web Workbench 迁移
数据库、队列、scheduler
自动 merge 或 release
```

## 8. 完成标准

Architecture Spine v1 完成时必须满足：

- Decision commit 早于全部实现提交；
- 新 command plan 在实现前重新生成；
- 分支从 PR #8 最终有效头派生；
- LangGraph 是唯一 primary runtime；
- Shadow Graph 端到端可运行；
- R0/R1 和 R2/R3 路由正确；
- 未知输入 fail closed；
- Trust adapter 复用但不修改 transition kernel；
- checkpoint/resume 测试通过；
- 新增 focused tests 通过；
- 旧 transition tests 通过；
- full pytest 或真实已知限制被完整记录；
- `git diff --check` 通过；
- Draft PR exact-head CI、State Gate、Decision Preflight 成功；
- PR 保持 Draft、Open、Unmerged。

## 9. 本轮之后

本轮完成后，再选择一个独立 workstream：

```text
Trust Layer Schema Foundation
或
GitHub Truth Live Adapter
或
BMAD Planning Integration
```

不得在本轮自动开始 Binary Evidence Firewall、Claim Ledger、User Solve、Web 或外部逆向工具集成。
