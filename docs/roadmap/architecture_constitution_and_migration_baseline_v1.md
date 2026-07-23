# reverse-agent 架构宪章与迁移基线 v1

## 0. 文档状态

```text
REFERENCE_ONLY — IMPLEMENTED_BY_P0_CONSTITUTION
```

本文是长期架构与迁移参考，不是 `Decision`、`Command Plan`、实现授权、合并授权或 PR #9 分支修改授权。P0 的唯一执行权威是 replacement Decision `decision_20260722_architecture_constitution_gate_compatibility_rework_v1`；已接受的权威结论位于 `docs/architecture/**`、`docs/adr/**` 和 `docs/roadmap/long-term-implementation-plan-v2.md`。

对应讨论：GitHub Issue #10 — `Architecture Constitution and Migration Baseline v1`。

本文取代此前将 **Evidence Trust Schema Foundation** 作为立即下一步的安排。Trust Layer 的产品方向保持不变，但在实现 `EvidenceUnit`、`Claim`、`EvidenceRelation` 等对象前，必须先冻结事实源、存储、运行时、Sandbox、Legacy 退出和治理成本边界。

---

# 1. 为什么修改下一步计划

当前仓库仍处在迁移中间态：

1. `main` 仍主要承载旧的 `project_state` 文件型治理体系；
2. PR #9 才包含已验收但尚未合并的 Architecture Spine；
3. 源码、运行状态、命令证据、报告和 stdout/stderr 仍可能进入同一个 Git 工作树；
4. Engineering Control Plane 的“工程执行授权”与 Binary Analysis Trust Domain 的“二进制证据信任”尚未形成正式 bounded context；
5. Legacy Control Plane 与 Transition Control Plane 有兼容边界，但没有明确退出阶段；
6. LangGraph 目前是 non-dispatching shadow runtime，使用内存 checkpointer，不是最终 durable runtime；
7. Evidence、Claim revision、Artifact、Checkpoint 和 Analysis Capsule 的存储归属尚未冻结；
8. debugger、emulator 和未知样本执行所需的 Sandbox/Worker 边界尚未定义；
9. 治理 Artifact 数量没有上限，可能再次形成“为证明治理而继续治理”的循环。

因此，下一轮不能直接编写 Trust Layer 业务代码，而应先完成一次**只修改架构文档和 ADR 的架构宪章轮**。

---

# 2. 当前远端基线

```text
repository: dddd2024/reverse-agent
architecture_pr: #9
pr_state: draft_open_unmerged
accepted_exact_head: 43418818af61d9be3208d2444fd6ce5120f73fab
base_branch: main
```

永久约束：

- PR #9 的已验收 head 不在本计划轮修改；
- 不在原分支继续追加治理修复；
- 不 rebase、squash、force-push；
- 不在没有独立 Integration Decision 的情况下合并或标记 ready；
- 不把 Issue、roadmap 或本文本身当作执行权威。

---

# 3. 下一轮建议 Decision

建议名称：

```text
Architecture Constitution and Migration Baseline v1
```

建议属性：

```yaml
mainline: architecture_planning
risk_tier: R0_or_R1
implementation_allowed: false
runtime_mutation_allowed: false
dependency_change_allowed: false
workflow_change_allowed: false
pr9_branch_mutation_allowed: false
merge_allowed: false
```

如果当前系统尚不支持 `architecture_planning`，可临时使用 `project_governance`，但本轮仍必须保持纯规划性质，不能再次成为“架构规划 + 控制面实现 + 治理修复”的混合轮。

---

# 4. 架构宪章轮目标

一次性冻结以下基础决策：

```text
产品边界
模块边界
Trust Boundary
唯一事实源
数据与 Artifact 存储
工作流运行时归属
Schema 与版本策略
Sandbox/Worker 边界
Legacy Control Plane 退出方式
PR #9 集成方式
长期阶段顺序
治理成本上限
```

推荐产物：

```text
docs/architecture/architecture-spine-v2.md
docs/architecture/trust-model.md
docs/architecture/data-contracts.md
docs/architecture/storage-and-artifact-ownership.md
docs/architecture/sandbox-and-execution-boundary.md
docs/architecture/migration-and-legacy-exit.md
docs/roadmap/long-term-implementation-plan-v2.md
docs/adr/ADR-001-*.md ... docs/adr/ADR-010-*.md
```

---

# 5. 必须完成的架构决策

## ADR-001：采用模块化单体

单人开发阶段采用：

```text
一个 Python 模块化单体
+ 一个 Web/API 入口
+ 一个结构化 Metadata Store
+ 一个 Content-Addressed Artifact Store
+ 一个独立隔离执行 Worker 边界
```

暂不引入：

```text
微服务
Kubernetes
分布式消息队列
多个主数据库
多个主 Agent Runtime
```

只有隔离执行 Worker 需要独立进程、容器或虚拟机边界。

## ADR-002：开发工作流与二进制分析工作流分离

### 开发 reverse-agent

```text
BMAD Planning Artifact
→ GitHub Work Item
→ Development LangGraph
→ R0-R3 Risk Classification
→ Engineering Authorization
→ Code / Test
→ Draft PR
→ GitHub Actions
→ Human Merge
```

### 使用 reverse-agent 分析样本

```text
Sample Intake
→ Safe Static Evidence
→ EvidenceUnit
→ Claim / Counterevidence
→ ActionProposal
→ Risk and Taint Gate
→ Authorized Provider
→ ValidationExperiment
→ Analysis Capsule
→ User/Auditor View
```

两条工作流必须使用不同 Graph、不同 State Schema、不同 Thread Namespace。PM/Developer Agent 与 Binary Analysis Agent 不得共用一个运行状态。

## ADR-003：分离两个 bounded context

### Engineering Control Plane

```text
GitHubWorkItem
ExecutionEnvelope
EngineeringDecision
CommandPlan
RepositoryMutation
PR/CI Observation
```

### Binary Analysis Trust Domain

```text
AnalysisRun
SampleIdentity
ArtifactRef
EvidenceUnit
Claim
Counterevidence
ValidationExperiment
ActionProposal
ActionReceipt
AnalysisCapsule
```

唯一连接点：

```text
AnalysisActionProposal
→ Engineering/Runtime Authorization
→ ActionReceipt
```

永久禁止：

- CI 成功被解释为 Claim 已验证；
- Command Plan 被解释为分析证据；
- 工具成功退出被解释为分析结论正确；
- 分析 Claim 直接授权 GitHub 操作。

## ADR-004：唯一事实源矩阵

| 事实类型 | 唯一权威 |
|---|---|
| Product Brief、PRD、Architecture、Story | BMAD Artifact |
| 当前工程工作单元 | GitHub Issue / PR |
| Branch、Commit、Review、CI、Merge、Release | GitHub |
| Workflow checkpoint、interrupt、resume | LangGraph Checkpointer |
| R2/R3 工程权限 | Compact Decision |
| 具体高风险命令 | Command Plan |
| 样本身份 | SampleIdentity |
| Evidence、Claim、Validation | Analysis Repository |
| 大型工具输出 | Content-Addressed Artifact Store |
| Trace、成本、延迟、异常 | OpenTelemetry |
| 可迁移最终证明 | Analysis Capsule |
| 用户结果 | Claim/Validation 的投影 |

任何其他文件都只能是带来源和时间的缓存、投影或导出，不得成为平行可变权威。

## ADR-005：存储所有权

Local-first 阶段采用：

```text
SQLite Analysis Repository
+ Local Content-Addressed Artifact Store
+ Persistent LangGraph SQLite Checkpointer
```

三者逻辑上分离：

### Workflow Store

保存：

```text
thread_id
checkpoint
interrupt
resume state
node result
retry metadata
```

### Analysis Repository

保存：

```text
AnalysisRun
SampleIdentity
Evidence metadata
Claim revision
EvidenceRelation
InfluenceRelation
ValidationExperiment
ActionProposal/Receipt
Capsule reference
```

### Artifact Store

保存：

```text
原始二进制
stdout/stderr
反编译导出
截图
工具数据库
验证结果
压缩 Capsule
```

推荐内容寻址布局：

```text
artifacts/sha256/ab/cd/<full_digest>
```

Git 只保存源码、测试、Schema、Policy、架构文档、确定性 Fixture、稳定 Decision 和必要的 Artifact descriptor/digest。正常运行产生的可变证据不继续提交到源码分支。

## ADR-006：Evidence 与 Claim 版本模型

第一批外部契约：

```text
AnalysisRun
SampleIdentity
ArtifactRef
EvidenceUnit
Claim
ClaimRevision
EvidenceRelation
InfluenceRelation
ValidationExperiment
ActionProposal
ActionAuthorization
ActionReceipt
CapsuleManifest
TrustPolicySnapshot
```

永久规则：

1. `Trust`、`Confidence`、`Validation` 必须分离；
2. EvidenceUnit、ActionReceipt、Validation result、sealed manifest 创建后不可原地覆盖；
3. Claim 演化必须创建 revision；
4. binary-derived content 默认 `untrusted/tainted`；
5. `verified` 必须绑定明确 validation evidence；
6. stale evidence 不能支撑 current accepted Claim；
7. supporting 与 contradicting evidence 可以同时存在；
8. 外部交换标准使用版本化 JSON Schema；
9. Python dataclass/Pydantic 只是实现，不是唯一规范。

Schema 变更分类：

```text
PATCH: 新增兼容可选字段
MINOR: 新对象或兼容状态
MAJOR: 破坏已有消费者
```

只有 MAJOR 变化才必须启动完整迁移 Decision。

## ADR-007：LangGraph 是唯一工作流运行时

当前 PR #9 保持 shadow/non-dispatching，不立即扩展真实执行。

未来 durable runtime 必须支持：

```text
persistent checkpoint
interrupt/resume
idempotent node
bounded retry
human approval
separate namespaces
provider dispatch through ports
```

不再自研第二套主 AgentRunner。旧 Runner 只能作为 compatibility adapter 或逐步归档对象。

## ADR-008：Sandbox 与 Worker 边界

执行等级：

```text
S0: hash、file type、header、strings、local parser 等纯读取
S1: Ghidra/IDA export、disassembler、CFG 等不运行目标程序的静态工具
S2: emulator、debugger、hook、runtime probe 的隔离执行
S3: 未知样本在可销毁环境中的动态执行
```

S2/S3 必须具备：

```text
ActionProposal
risk classification
authorization
必要时 Human Approval
默认断网
只读输入
资源限制
超时
独立输出目录
进程树清理
环境销毁
ActionReceipt
```

Worker 不得获得：

```text
GitHub Token
Git 凭据
用户主目录访问
项目源码写权限
其他 Analysis Run 访问
长期 secrets
```

## ADR-009：运行遥测不等于分析证据

OpenTelemetry 负责：

```text
trace
log
metric
cost
latency
retry
exception
```

这些内容默认是 operational telemetry，不自动成为 EvidenceUnit 或 Claim validation。只有显式 adapter 和 provenance 转换后，才可进入 Analysis Repository。

## ADR-010：Legacy Control Plane 退出

生命周期：

```text
ACTIVE_COMPATIBILITY
→ READ_ONLY_COMPATIBILITY
→ ARCHIVED
→ REMOVED_FROM_RUNTIME
```

退出条件至少包括：

1. 新控制面完成多个有代表性的 R1/R2 任务；
2. GitHub 发布事实不再复制到 legacy publication mirror；
3. 新运行证据不再写入 `project_state/gates/evidence`；
4. Legacy Decision 可读取，但不能启动新一代工作流；
5. 所有新 Work Item 进入新控制路径；
6. 记录 rollback window 与最终移除条件；
7. 旧 closeout/final seal/report mirror 不再扩展新字段或新 Gate。

---

# 6. PR #9 集成计划

架构宪章轮不执行合并。

后续独立 Integration Decision 按以下顺序进行：

1. 确认 PR #9 仍是 accepted exact head：`43418818af61d9be3208d2444fd6ce5120f73fab`；
2. 重新观察 exact-head required checks；
3. 比较当前 `main` 与 PR base，识别冲突；
4. 不 rebase、squash 或修改 accepted head；
5. 使用保留 accepted commit ancestry 的集成方式；
6. 合并后将 Architecture Spine 标记为 `FROZEN_BASELINE`；
7. 只有已证明的 security/correctness defect 才能重开，不因功能扩展重开治理修复轮。

---

# 7. Repository Hygiene 与运行证据迁移

PR #9 集成后的第一个实现轮，应停止运行 Artifact 污染源码 Diff。

## 保留在 Git

```text
源码
测试
Schema
Policy
架构文档
ADR
确定性 Fixture
稳定 Decision
必要的 Artifact descriptor/digest
```

## 移出普通源码提交

```text
stdout/stderr
execution trace body
可变 gate result
原始工具导出
大型二进制证据
截图
workflow checkpoint
普通测试日志
Analysis Capsule payload
```

运行证据进入：

```text
Local Run Store
GitHub Actions Artifact
Content-Addressed Artifact Store
```

Git 中最多保留：

```text
artifact URI
SHA-256
producer
observed_at
retention policy
verification status
```

---

# 8. 治理税上限

继续保留 R0-R3，但每一级的 Artifact 数量和 Gate 数量必须受限。

## R0：规划与只读

需要：

```text
Work Item 或讨论记录
```

不需要：

```text
Decision
Command Plan
Seal
Closeout
```

## R1：限定范围普通工程修改

需要：

```text
GitHub Work Item
Lightweight Execution Envelope
PR
CI
```

不需要完整 Decision 和多层终态封存。

## R2：敏感工程操作

例如依赖、Workflow、网络、push、迁移和权限策略。

需要 compact Decision：

```text
work_package_id
approved_scope
risk_profile
allowed_operations
forbidden_operations
acceptance_checks
expiry
approver
```

## R3：高风险安全执行

需要：

```text
Decision
Command Plan
Human Approval
Sandbox
Action Provenance
Execution Evidence
Validation
Analysis Capsule（适用时）
```

每个 Gate 必须说明：

```text
阻止的具体失败
读取的唯一权威
输出的阻塞结论
是否复制动态事实
何时可以退役
```

不能回答上述问题的 Gate 不得加入。

---

# 9. 本轮明确禁止

架构宪章轮不得：

- 实现 EvidenceUnit、Claim、数据库或 CAS；
- 安装或配置 BMAD；
- 升级 LangGraph；
- 将 shadow graph 扩展成真实执行；
- 修改 GitHub Workflow；
- 修改 PR #9 分支；
- merge、rebase、squash、force-push、tag、release 或 mark ready；
- 接入 IDA、Ghidra、debugger、emulator 或模型 API；
- 执行未知二进制；
- 修改 Web/UI；
- 创建生产数据库或 Artifact Store；
- 一次性重写所有 legacy state；
- 再开启 Architecture Spine 细节修复循环。

---

# 10. 架构宪章轮验收标准

只有同时满足以下条件才可接受：

1. 每一种可变事实都有一个唯一权威；
2. Engineering Trust 与 Binary Analysis Trust 已形成两个 bounded context；
3. 模块依赖方向明确且可通过测试或 lint 约束；
4. Metadata、Artifact、Checkpoint、Telemetry、Capsule 的存储归属明确；
5. Evidence 不可变与 Claim revision 规则明确；
6. Sandbox tiers、凭据边界和文件系统边界明确；
7. PR #9 的 non-mutation 与集成方式明确；
8. Legacy Control Plane 有退出阶段、退出条件和回滚窗口；
9. R0-R3 治理成本不再统一；
10. 下一轮可以直接生成 Integration Decision，而不重新讨论基础选型；
11. 本轮没有业务代码、依赖、Workflow、数据库或运行时修改。

---

# 11. 修订后的长期实施顺序

```text
Phase 0  Architecture Constitution and Migration Baseline
Phase 1  PR #9 exact-head integration and Architecture Spine freeze
Phase 2  Repository Hygiene and Legacy Control Plane containment
Phase 3  Analysis Trust Domain kernel and versioned schemas
Phase 4  Safe Static Evidence Pipeline
Phase 5  Binary Evidence Firewall and Claim/Counterevidence Ledger
Phase 6  Tool Provider Contract and Action Provenance
Phase 7  Sandbox Executor and Controlled Dynamic Validation
Phase 8  Falsification-driven Validation and Analysis Capsule
Phase 9  Durable LangGraph Runtime
Phase 10 BMAD and live GitHub planning/truth integration
Phase 11 Trust Workbench
Phase 12 Application adapters: reverse solving, crash evidence, patch diff, malware, firmware
Phase 13 Production hardening after measured need
```

---

# 12. 近期执行边界

```text
当前只提交本计划文档和后续架构 ADR。
不从本文直接开始实现。
```

有效顺序必须是：

```text
提交并接受 documentation-only Architecture Decision
→ 完成架构宪章轮
→ 提交独立 PR #9 Integration Decision
→ 集成并冻结 Architecture Spine
→ 完成 Repository/Legacy Hygiene
→ 才开始 Analysis Trust Domain Schema 实现
```
