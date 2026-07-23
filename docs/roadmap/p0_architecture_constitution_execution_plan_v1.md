# reverse-agent P0 架构宪章具体执行计划 v1

## 0. 文档状态

```text
REFERENCE_ONLY — SUPERSEDED_EXECUTION_DETAILS
```

本文保留为 P0 原始执行参考。实际执行权威已由 replacement Decision `decision_20260722_architecture_constitution_gate_compatibility_rework_v1` 接管：自动 Profile 为 `fast`，不运行 `run-closeout` 或 `close-round`，存储文档与 ADR-007 使用新的 workflow/ownership 文件名。本文中与 replacement Decision 冲突的旧 profile、closeout 和文件名指令均已被替代。

本文不是：

```text
Decision
Command Plan
实现授权
PR #9 合并授权
未知二进制执行授权
发布授权
```

即使用户已经提出“开始执行”，仓库当前仍由 `project_state/decision_packet.md` 驱动。因此，真正开始修改架构正文前，第一笔实施提交必须建立新的 P0 Decision；随后必须生成与该 Decision 对应的 Command Plan。

关联材料：

```text
GitHub Issue #10
GitHub PR #11
docs/roadmap/architecture_constitution_and_migration_baseline_v1.md
docs/roadmap/architecture_constitution_implementation_plan_v1.md
GitHub PR #9 — Architecture Spine v1
```

---

# 1. 本轮目标

本轮只执行：

```text
P0：Architecture Constitution and Migration Baseline
```

本轮必须冻结：

1. 产品边界；
2. 模块边界；
3. Engineering Control Plane 与 Binary Analysis Trust Domain 的边界；
4. Development Workflow 与 Binary Analysis Workflow 的分离规则；
5. 唯一事实源矩阵；
6. 数据、Artifact、Checkpoint 和 Telemetry 的存储归属；
7. Evidence、Claim、Validation、Action 和 Capsule 的版本规则；
8. LangGraph 的职责边界；
9. Sandbox S0-S3 的安全边界；
10. PR #9 的精确集成规则；
11. Legacy Control Plane 的退出路径；
12. R0-R3 治理成本上限；
13. P1-P16 的长期实施顺序。

本轮不实现任何 Trust Layer 业务功能。

---

# 2. 当前远端基线

执行前必须重新观察远端。计划编写时的基线为：

```text
repository: dddd2024/reverse-agent
working_branch: agent/architecture-constitution-plan-v1
planning_pr: #11
planning_pr_state: draft_open_unmerged
planning_pr_head_before_this_file: 351570f016caadf28bf025541ce44a6865fd6d5e
architecture_pr: #9
architecture_pr_state: draft_open_unmerged
architecture_pr_accepted_head: 43418818af61d9be3208d2444fd6ce5120f73fab
base_branch: main
```

实际执行时必须重新读取：

```text
origin/main
origin/agent/architecture-constitution-plan-v1
origin/codex/architecture-spine-v1
PR #9 metadata and checks
PR #11 metadata and head
```

如果任一关键 head 已变化，停止沿用旧结论，重新比较后再继续。

---

# 3. 执行位置

## 3.1 工作分支

继续使用：

```text
agent/architecture-constitution-plan-v1
```

不要再创建第三个重复规划分支。

## 3.2 Pull Request

继续使用：

```text
PR #11
```

PR #11 在 P0 完成前保持 Draft。

## 3.3 PR #9 边界

PR #9 必须保持：

```text
Draft
open
unmerged
head == 43418818af61d9be3208d2444fd6ce5120f73fab
```

本轮不得：

```text
修改 PR #9 分支
rebase PR #9
squash PR #9
force-push PR #9
mark ready
merge PR #9
tag
release
```

PR #9 的集成属于后续独立 P1 Decision。

---

# 4. 新 Decision

## 4.1 建议标识

```text
decision_id:
decision_20260722_architecture_constitution_and_migration_baseline_v1

round_id:
round_20260722_architecture_constitution_and_migration_baseline_v1
```

执行时如果日期或命名规则需要调整，可以使用新的唯一标识，但不得复用历史 Decision ID。

## 4.2 Mainline

使用：

```text
engineering_branch
```

暂不使用：

```text
architecture_planning
```

原因：当前仓库尚未证明 `architecture_planning` 是已注册、已被 Gate 接受的 mainline。不得为了完成 P0 先修改 mainline 注册系统。

## 4.3 风险等级

概念风险等级：

```text
R1
```

由于轻量 Execution Envelope 尚未正式落地，当前仍使用现有完整 Decision 驱动机制。

## 4.4 建议 Decision 元数据

```json
{
  "schema_version": 1,
  "decision_id": "decision_20260722_architecture_constitution_and_migration_baseline_v1",
  "round_id": "round_20260722_architecture_constitution_and_migration_baseline_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

## 4.5 建议核心约束

```json
{
  "workstream_id": "architecture-constitution-and-migration-baseline-v1",
  "risk_tier": "R1",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "implementation_allowed": "documentation_only",
  "runtime_mutation_allowed": false,
  "dependency_change_allowed": false,
  "workflow_change_allowed": false,
  "source_code_change_allowed": false,
  "test_code_change_allowed": false,
  "pr9_branch_mutation_allowed": false,
  "pr9_merge_allowed": false,
  "network_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "tool_provider_execution_allowed": false,
  "database_creation_allowed": false,
  "langgraph_upgrade_allowed": false,
  "bmad_install_allowed": false,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "tag_mutation_allowed": false,
  "release_allowed": false
}
```

---

# 5. 允许范围

## 5.1 允许新增或修改的架构文件

```text
docs/architecture/architecture-spine-v2.md
docs/architecture/trust-model.md
docs/architecture/data-contracts.md
docs/architecture/storage-and-artifact-ownership.md
docs/architecture/sandbox-and-execution-boundary.md
docs/architecture/migration-and-legacy-exit.md
docs/architecture/governance-cost-model.md
```

## 5.2 允许新增或修改的 ADR

```text
docs/adr/ADR-001-modular-monolith.md
docs/adr/ADR-002-separate-development-and-analysis-workflows.md
docs/adr/ADR-003-separate-trust-bounded-contexts.md
docs/adr/ADR-004-unique-source-of-truth.md
docs/adr/ADR-005-storage-ownership.md
docs/adr/ADR-006-evidence-and-claim-versioning.md
docs/adr/ADR-007-langgraph-workflow-ownership.md
docs/adr/ADR-008-sandbox-worker-boundary.md
docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md
docs/adr/ADR-010-legacy-control-plane-exit.md
```

## 5.3 允许新增或修改的路线文件

```text
docs/roadmap/architecture_constitution_and_migration_baseline_v1.md
docs/roadmap/architecture_constitution_implementation_plan_v1.md
docs/roadmap/p0_architecture_constitution_execution_plan_v1.md
docs/roadmap/long-term-implementation-plan-v2.md
```

已有三份计划文件原则上只允许：

```text
修正内部矛盾
补充交叉引用
记录最终接受状态
修正已验证的远端事实
```

不得把 Roadmap 当作动态运行状态或执行授权。

## 5.4 允许产生的当前轮治理文件

仅在现有工具实际要求时允许：

```text
project_state/decision_packet.md
project_state/gates/command_plan.json
project_state/gates/gate_profile_plan.json
project_state/gates/preflight_result.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260722_architecture_constitution_and_migration_baseline_v1/**
```

不得为了保持旧系统“看起来完整”而批量刷新整个 `project_state`。

---

# 6. 禁止范围

## 6.1 禁止修改路径

```text
reverse_agent/**
tests/**
frontend/**
.github/workflows/**
.codex-skills/**
pyproject.toml
requirements*.txt
package*.json
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/roadmap/workstreams.json
project_state/domains/**
project_state/jobs/**
project_state/user_sessions/**
project_state/archives/**
project_state/deletions/**
project_state/blob_store/**
project_state/*.db
project_state/index.sqlite
```

## 6.2 禁止行为

```text
修改或合并 PR #9
rebase
squash
force-push
直接 push main
修改依赖
升级 LangGraph
安装或配置 BMAD
实现 EvidenceUnit
实现 Claim
实现 Analysis Repository
实现 CAS
实现 Sandbox
实现 Provider
实现 Action Provenance
实现 Web
实现新的 AgentRunner
执行未知二进制
调用 IDA/Ghidra/debugger/emulator
修改 GitHub Actions
创建生产数据库
打 tag
发布版本
```

## 6.3 禁止范围扩张

本轮发现任何源码问题时：

1. 记录为后续 Work Item；
2. 不在 P0 顺手修复；
3. 不修改允许路径来绕过 Gate；
4. 不为文档轮增加新 Gate 代码；
5. 不把 P1、P2 或 P3 内容提前塞进本轮。

---

# 7. 执行顺序

# P0-A：远端和本地基线观察

在 Windows PowerShell 中执行：

```powershell
Set-Location F:\reverse-agent
Get-Location
git status --short
git branch --show-current
git rev-parse HEAD
git remote -v
git fetch origin
git rev-parse origin/main
git rev-parse origin/agent/architecture-constitution-plan-v1
git rev-parse origin/codex/architecture-spine-v1
```

同时读取 GitHub：

```text
PR #9 state, head, checks, comments
PR #11 state, head, changed files
Issue #10 state and latest comments
```

必须确认：

```text
当前工作目录正确
当前分支正确
没有无法隔离的无关改动
PR #11 head 可解释
PR #9 accepted head 未变化
main 没有需要先处理的未知规划冲突
```

如果工作树存在无关改动：

```text
禁止 git add -A
禁止覆盖
禁止自动 stash 后继续
```

必须只处理明确属于 P0 的文件。

---

# P0-B：建立 Decision

第一笔新实施提交只包含：

```text
project_state/decision_packet.md
```

不得在同一提交中加入架构正文、ADR 或路线图正文。

建议提交信息：

```text
Authorize architecture constitution documentation round
```

Decision 必须明确：

```text
只允许文档
Decision 提交先于实施
激活后 Decision 内容不可变
Command Plan 必须先于正文修改
PR #9 不可修改和合并
源码、测试、依赖、Workflow 不可修改
无二进制执行授权
无发布授权
```

Decision 提交完成后，记录其 commit SHA，后续报告必须引用该 SHA。

---

# P0-C：生成执行授权

在修改架构正文之前，使用仓库实际支持的命令生成 Command Plan。

优先尝试：

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state
```

执行前先检查帮助：

```powershell
python -m reverse_agent.project_gate --help
```

如果当前版本命令名称或参数不同：

1. 不修改 `reverse_agent/project_gate.py`；
2. 使用现有等价命令；
3. 记录实际命令；
4. 不为 P0 新增 Gate；
5. Command Plan 必须包含所有会修改文件、测试、报告和发布的命令。

如果 Command Plan 无法覆盖允许的文档路径，则停止本轮，不得无授权修改。

---

# P0-D：建立统一文档骨架

先创建七份架构文档骨架：

```text
architecture-spine-v2.md
trust-model.md
data-contracts.md
storage-and-artifact-ownership.md
sandbox-and-execution-boundary.md
migration-and-legacy-exit.md
governance-cost-model.md
```

每份文档统一包含：

```text
Status
Purpose
Authority
Scope
Non-goals
Context
Decisions
Invariants
Interfaces
Failure modes
Security implications
Migration impact
Acceptance criteria
Related ADRs
```

骨架阶段必须先检查：

```text
每个主题只有一个权威正文
其他文档只交叉引用
不存在同一事实被两个文档同时定义
不存在 Architecture、Roadmap 和 ADR 互相覆盖职责
```

---

# P0-E：冻结总体架构

在 `architecture-spine-v2.md` 中冻结 Python 模块化单体：

```text
reverse_agent/
  engineering/
  analysis/
    domain/
    application/
    ports/
    adapters/
  workflows/
    development/
    binary_analysis/
  infrastructure/
    persistence/
    artifacts/
    sandbox/
    telemetry/
  interfaces/
    api/
    web/
```

本阶段只冻结目标边界，不要求立即重排现有仓库目录。

固定依赖方向：

```text
interfaces
    ↓
application / workflows
    ↓
domain
    ↑
ports
    ↑
infrastructure adapters
```

永久禁止：

```text
domain -> LangGraph
domain -> GitHub
domain -> FastAPI
domain -> SQLite driver
domain -> IDA/Ghidra
domain -> OpenTelemetry
domain -> Web UI
```

Domain 只允许依赖标准库、纯领域值对象和稳定协议。

初期部署形态固定为：

```text
one Python application
one Web/API surface
one structured metadata database
one content-addressed artifact store
one isolated execution worker boundary
```

暂不引入：

```text
microservices
Kubernetes
distributed queue
multiple primary databases
event bus as primary truth
```

---

# P0-F：冻结两条独立 Workflow

## Development Workflow

```text
BMAD artifact
→ GitHub Work Item
→ risk classification
→ engineering authorization
→ implementation
→ tests
→ Draft PR
→ CI
→ review
→ human merge
```

## Binary Analysis Workflow

```text
Sample intake
→ safe evidence collection
→ EvidenceUnit
→ Claim / Counterevidence
→ ActionProposal
→ risk and taint gate
→ authorized provider
→ ValidationExperiment
→ Analysis Capsule
→ user/auditor projection
```

必须明确：

```text
不同 Graph
不同 State Schema
不同 Checkpoint namespace
不同风险模型
不同授权对象
不同最终状态
不同失败语义
```

不得建立一个同时处理开发和二进制分析的通用 Graph。

不得把：

```text
CI PASS
PR APPROVED
Decision ACCEPTED
Tool exit code 0
```

解释为二进制 Claim 已验证。

---

# P0-G：冻结两个 bounded context

## Engineering Control Plane

```text
Work Item
Execution Envelope
Engineering Decision
Command Plan
Repository Mutation
PR/CI Observation
Review
Merge
Release
```

## Binary Analysis Trust Domain

```text
AnalysisRun
SampleIdentity
ArtifactRef
EvidenceUnit
Claim
Counterevidence
ValidationExperiment
ActionProposal
ActionAuthorization
ActionReceipt
AnalysisCapsule
```

两者唯一允许的桥接是：

```text
ActionProposal
→ Engineering authorization boundary
→ ActionAuthorization
→ isolated provider execution
→ ActionReceipt
```

工程接受不得解释为分析结论有效。

分析证据不得直接授予仓库写权限。

---

# P0-H：冻结唯一事实源矩阵

| 事实类型 | 唯一权威 |
|---|---|
| Brief、PRD、Architecture、Story | BMAD Artifact |
| 当前工程任务 | GitHub Issue / PR |
| branch、commit、CI、review、merge、release | GitHub |
| Workflow 运行状态 | LangGraph Checkpointer |
| R2/R3 工程授权 | Decision |
| 高风险具体命令 | Command Plan |
| Sample 身份 | SampleIdentity |
| Evidence、Claim、Validation | Analysis Repository |
| 大型输出 | CAS Artifact Store |
| traces、metrics、logs | OpenTelemetry |
| 最终可携带证明 | Analysis Capsule |
| 用户结果 | Claim/Validation 投影视图 |

每一种动态事实只允许一个可变权威。

其他位置只能保存：

```text
reference
URI
digest
immutable snapshot
read-only projection
cache
```

不得自称同等权威。

尤其禁止：

```text
GitHub merge truth 被重复复制成另一份可修改 publication truth
LangGraph checkpoint 被重复复制为 current_state authority
Analysis Claim 被报告文本重新定义
Telemetry 自动晋升为 Evidence
```

---

# P0-I：冻结数据契约

本轮只定义对象和规则，不创建实现代码或正式 JSON Schema 文件。

第一批契约：

```text
AnalysisRun
SampleIdentity
ArtifactRef
EvidenceUnit
TrustLevel
TaintLabel
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

```text
Trust != Confidence != Validation
```

并规定：

1. `EvidenceUnit` 创建后不可覆盖；
2. `ActionReceipt` 创建后不可覆盖；
3. Validation 结果创建后不可覆盖；
4. Sealed CapsuleManifest 不可覆盖；
5. Claim 通过 revision 演化；
6. binary-derived 数据默认 `tainted/untrusted`；
7. `verified` 必须引用 validation evidence；
8. stale evidence 不得支撑 current accepted Claim；
9. Evidence 必须具有 producer、provenance、sample binding 和 observation time；
10. Claim 必须明确支持证据和反证；
11. JSON Schema 是外部交换标准；
12. Python Model 是实现，不是唯一规范。

本轮不得创建：

```text
reverse_agent/analysis/domain/**
reverse_agent/analysis/schemas/**
SQLite migration
repository implementation
```

这些属于 P3。

---

# P0-J：冻结存储架构

本地优先阶段采用：

```text
SQLite Analysis Repository
Local content-addressed Artifact Store
LangGraph SQLite Checkpointer
```

逻辑上必须分成：

```text
Workflow Store
Analysis Repository
Artifact Store
Telemetry Backend
```

即使初期都运行在本地，也不得混成一个状态目录或一个事实模型。

## Git 中保留

```text
source
tests
JSON Schema
Policy
ADR
architecture docs
deterministic fixtures
stable Decisions
ArtifactRef
digest
small immutable summaries
```

## Git 外保存

```text
stdout/stderr
raw trace bodies
decompiler exports
binaries
screenshots
memory dumps
debugger sessions
normal test logs
workflow checkpoints
Capsule payloads
large execution evidence
```

Git 中的 ArtifactRef 至少包含：

```text
uri
digest
size
media_type
producer
created_at
retention_class
verification_status
```

---

# P0-K：冻结 LangGraph 所有权

LangGraph 是未来唯一 Workflow Runtime。

当前 PR #9 的 shadow/non-dispatching 行为仍作为过渡基础；P0 不升级或扩展 LangGraph。

未来要求：

```text
persistent checkpoint
interrupt/resume
idempotent nodes
bounded retry
human approval
separate workflow namespaces
provider dispatch through ports
explicit terminal states
```

禁止：

```text
第二个 primary AgentRunner
Development 和 Binary Analysis 共用一个 Graph
把 GitHub 当 checkpoint store
把 project_state 文件镜像当 durable runtime
```

LangGraph durable runtime 属于 P11，不得提前实施。

---

# P0-L：冻结 Sandbox 边界

定义：

```text
S0：hash、headers、strings、纯解析
S1：不执行目标的静态工具
S2：隔离 emulator/debugger/scripted probe
S3：一次性环境中的未知样本执行
```

## S0

```text
只读输入
无目标执行
无网络
普通进程隔离即可
```

## S1

```text
静态工具可运行
目标文件不作为本机可执行程序启动
输出写入隔离 run directory
```

## S2

```text
模拟器、调试器或脚本化探针
显式 ActionProposal
风险分类
授权
资源限制
文件系统隔离
受控网络策略
ActionReceipt
```

## S3

```text
未知样本真实执行
一次性 disposable worker
默认无网络
严格 CPU/内存/时间限制
运行后销毁
完整输出隔离
人工批准
```

S2/S3 Worker 不得获得：

```text
GitHub Token
用户主目录
仓库写权限
宿主机 Secret
其他 Analysis Run 数据
长期网络凭据
SSH key
cloud credentials
```

S2/S3 必须具备：

```text
ActionProposal
risk classification
Decision or high-risk authorization
Command Plan
human approval
timeout
CPU/memory limits
network policy
output isolation
cleanup
ActionReceipt
```

Sandbox Executor 属于 P8，不得在 P0 实现。

---

# P0-M：冻结 Telemetry 与 Evidence 边界

OpenTelemetry 负责：

```text
trace
metric
log
latency
cost
retry
exception
node duration
provider health
```

这些默认不是：

```text
EvidenceUnit
Claim support
Validation result
ActionReceipt
```

如果某条运行信息需要晋升为分析证据，必须经过显式 Evidence Adapter，记录：

```text
source telemetry identifier
promotion rule
producer
sample binding
normalization
trust and taint classification
immutable EvidenceUnit identifier
```

禁止“因为 trace 显示工具成功，所以 Claim 正确”。

---

# P0-N：冻结 Legacy 退出路线

Lifecycle 固定为：

```text
ACTIVE_COMPATIBILITY
→ READ_ONLY_COMPATIBILITY
→ ARCHIVED
→ REMOVED_FROM_RUNTIME
```

## ACTIVE_COMPATIBILITY

```text
旧控制面仍可启动旧工作
新控制面尚未完成代表性任务
```

## READ_ONLY_COMPATIBILITY

```text
历史文件可读取
旧 Decision 可审计
新工作不得写入旧 runtime evidence 位置
旧入口不得启动新一代 Workflow
```

## ARCHIVED

```text
旧数据进入只读归档
不参与运行时判断
只用于审计和迁移验证
```

## REMOVED_FROM_RUNTIME

```text
运行时不读取旧控制面
仅保留迁移工具或离线归档读取能力
```

迁移原则：

1. 不一次删除全部历史文件；
2. 新工作流先停止写旧位置；
3. Legacy 文件继续只读；
4. 新控制面完成代表性 R1/R2 任务后才能降级；
5. GitHub 事实不再复制到 publication mirror；
6. runtime evidence 不再进入普通源码提交；
7. rollback window 结束后才允许从 runtime 移除；
8. 删除必须由独立高风险 Decision 授权。

---

# P0-O：冻结治理成本模型

## R0：规划和只读

需要：

```text
Work Item 或讨论记录
```

不需要：

```text
Decision
Command Plan
seal
closeout chain
```

## R1：受限普通工程

需要：

```text
Work Item
Execution Envelope
PR
CI
```

在 Execution Envelope 尚未实现前，可暂时使用简化 Decision，但不得永久维持 full-profile 治理。

## R2：敏感工程

需要紧凑 Decision：

```text
scope
risk
allowed operations
forbidden operations
acceptance checks
expiry
approval
```

典型操作：

```text
merge
workflow change
dependency change
data migration
networked publication
release
```

## R3：高风险二进制或安全执行

需要：

```text
Decision
Command Plan
human approval
Sandbox
Action Provenance
execution evidence
validation
Capsule when applicable
```

每个 Gate 必须回答：

```text
specific failure prevented
single authority read
blocking decision emitted
whether duplicate truth is created
retirement condition
```

无法回答的 Gate 不得加入。

---

# P0-P：编写十份 ADR

统一格式：

```text
Title
Status
Context
Decision
Alternatives considered
Consequences
Security implications
Migration implications
Revisit conditions
```

ADR 列表：

```text
ADR-001 Modular Monolith
ADR-002 Separate Development and Analysis Workflows
ADR-003 Separate Trust Bounded Contexts
ADR-004 Unique Source of Truth
ADR-005 Storage Ownership
ADR-006 Evidence and Claim Versioning
ADR-007 LangGraph Runtime Ownership
ADR-008 Sandbox Worker Boundary
ADR-009 Telemetry Is Not Analysis Evidence
ADR-010 Legacy Control Plane Exit
```

初始状态：

```text
PROPOSED
```

通过本轮审查后统一变为：

```text
ACCEPTED
```

不得使用模糊状态：

```text
mostly accepted
temporarily final
accepted pending redesign
final draft
```

---

# P0-Q：整理长期路线

新增：

```text
docs/roadmap/long-term-implementation-plan-v2.md
```

固定顺序：

```text
P0  Architecture Constitution
P1  PR #9 exact integration and freeze
P2  Repository hygiene and Legacy containment
P3  Analysis Trust Domain kernel
P4  Safe Static Evidence Pipeline
P5  Binary Evidence Firewall
P6  Claim / Counterevidence Ledger
P7  Provider Contract and Action Provenance
P8  Sandbox Executor
P9  Falsification-driven Validation
P10 Analysis Capsule
P11 Durable Binary Analysis LangGraph Runtime
P12 BMAD and GitHub adapters
P13 Trust Workbench
P14 Trusted reverse-solving application
P15 Crash/Patch/Malware/Firmware adapters
P16 Production hardening
```

每阶段必须写清：

```text
entry criteria
risk tier
allowed scope
forbidden scope
deliverables
tests
acceptance criteria
rollback conditions
next-phase unlock
```

不得用固定天数替代验收条件。

---

# 8. 提交拆分

建议提交边界如下。

## Commit 1：Decision

```text
Authorize architecture constitution documentation round
```

只包含：

```text
project_state/decision_packet.md
```

## Commit 2：架构与信任边界

```text
Define architecture and trust boundaries
```

包含：

```text
docs/architecture/architecture-spine-v2.md
docs/architecture/trust-model.md
docs/architecture/governance-cost-model.md
docs/adr/ADR-001-modular-monolith.md
docs/adr/ADR-002-separate-development-and-analysis-workflows.md
docs/adr/ADR-003-separate-trust-bounded-contexts.md
docs/adr/ADR-004-unique-source-of-truth.md
```

## Commit 3：数据与存储

```text
Define data contracts and storage ownership
```

包含：

```text
docs/architecture/data-contracts.md
docs/architecture/storage-and-artifact-ownership.md
docs/adr/ADR-005-storage-ownership.md
docs/adr/ADR-006-evidence-and-claim-versioning.md
docs/adr/ADR-007-langgraph-workflow-ownership.md
docs/adr/ADR-009-telemetry-is-not-analysis-evidence.md
```

## Commit 4：Sandbox 与迁移

```text
Define sandbox and legacy migration boundaries
```

包含：

```text
docs/architecture/sandbox-and-execution-boundary.md
docs/architecture/migration-and-legacy-exit.md
docs/adr/ADR-008-sandbox-worker-boundary.md
docs/adr/ADR-010-legacy-control-plane-exit.md
```

## Commit 5：长期路线

```text
Finalize architecture implementation roadmap
```

包含：

```text
docs/roadmap/long-term-implementation-plan-v2.md
必要的计划交叉引用修正
```

## Commit 6：Closeout

```text
Close architecture constitution round
```

只包含本轮实际需要的报告和 Gate 结果。

不得每写一段就提交，也不得把 Decision 与实施正文放在同一个提交。

---

# 9. 验证计划

## 9.1 Git 差异检查

```powershell
git status --short
git diff --check
git diff --name-only
git diff --stat
```

实际变更必须只位于允许范围。

## 9.2 Decision 和 Gate 检查

按照当前仓库真实命令运行：

```text
decision lint or equivalent
gate profile
command plan
preflight
execution log
report summary
final check
run closeout
close round
```

不得假装不存在的命令已经执行。

不得在 Command Plan 生成之前修改架构正文。

## 9.3 测试

本轮不改源码，最低运行现有控制面测试：

```powershell
python -m pytest `
  tests/test_project_gate.py `
  tests/test_project_reports.py `
  tests/test_project_state.py `
  -q
```

如果当前分支实际测试名称不同，选择与 Decision、报告和 project_state 解析直接相关的现有测试。

不得为了让测试通过而修改源码。

全仓测试可以作为 diagnostic，但不得因为预先存在、与本轮无关的失败而扩大范围；必须明确区分 required test 与 diagnostic test。

## 9.4 文档一致性检查

至少验证：

```text
ADR 编号唯一
链接路径存在
不存在两个唯一权威
Development 和 Binary Analysis Workflow 未混合
Engineering Decision 不等于 Claim Validation
Telemetry 不等于 Evidence
CI PASS 不等于 Claim verified
Tool exit 0 不等于 Evidence correct
PR #9 head 在文档中一致
P0-P16 编号一致
所有架构文档的 Authority 字段不冲突
所有 ADR 与架构正文一致
```

## 9.5 禁止内容扫描

检查文档没有出现错误授权：

```text
自动合并 PR #9
直接运行未知二进制
立即安装 BMAD
立即升级 LangGraph
立即建立微服务
立即引入 Kubernetes
立即创建生产数据库
把普通 trace 当作分析证据
让 Workflow checkpoint 取代 GitHub merge truth
让 Roadmap 直接触发执行
```

---

# 10. P0 验收标准

只有同时满足以下条件才接受：

1. 每类动态事实只有一个权威来源；
2. Development Workflow 与 Binary Analysis Workflow 完全分离；
3. Engineering Control Plane 与 Analysis Trust Domain 完全分离；
4. Domain 依赖方向明确且可测试；
5. Evidence、Claim、Validation、Action 和 Capsule 边界明确；
6. Metadata、Artifact、Checkpoint 和 Telemetry 存储归属明确；
7. Evidence 与 Claim 的不可变和 revision 规则明确；
8. Sandbox S0-S3 权限边界明确；
9. PR #9 的 exact-head、非修改和集成方式明确；
10. Legacy 有可执行的退出阶段；
11. R0-R3 治理成本有明确上限；
12. P1-P16 顺序不需要重新讨论基础选型；
13. 没有业务代码、依赖、Workflow 或运行时变更；
14. 所有 required tests 和文档一致性检查通过；
15. Git diff 只包含允许文件；
16. Decision commit 早于所有正文实施 commit；
17. Command Plan 早于所有正文修改；
18. PR #9 accepted head 未变化；
19. PR #11 仍为 Draft；
20. 报告没有把规划文件解释为执行授权。

终态：

```text
ARCHITECTURE_CONSTITUTION_ACCEPTED
```

---

# 11. 立即停止条件

出现下列任意情况必须停止本轮：

```text
PR #9 accepted head 变化
PR #11 出现无法解释的未知提交
Decision lint 或 preflight 阻塞
Command Plan 无法覆盖允许文档路径
必须修改源代码才能完成文档轮
必须修改 Workflow 才能继续
必须升级依赖才能继续
发现两个无法统一的事实权威
文档要求提前实现数据库或 Sandbox
架构结论依赖尚未验证的关键技术假设
工作树包含无法隔离的无关改动
测试失败只能通过源码修改解决
需要执行未知二进制才能完成文档
```

停止后只能：

```text
保留已生成证据
报告阻塞原因
建立新的 Work Item 或 Decision
```

不得扩大范围“顺手修复”。

---

# 12. P0 完成后的下一步

P0 接受后，不得直接进入 EvidenceUnit。

下一步建立单独 Decision：

```text
P1：PR #9 Exact-head Integration and Architecture Spine Freeze
```

P1 才能授权：

```text
重新观察 PR #9 checks
比较最新 main
验证 exact accepted head
保留 accepted ancestry
合并 PR #9
在 main 上运行集成检查
记录 FROZEN_BASELINE
```

P1 不得与 P2 Repository Hygiene 混在同一轮。

P2 不得与 P3 Trust Domain Kernel 混在同一轮。

固定后续顺序：

```text
P0 Architecture Constitution
→ P1 PR #9 Integration
→ P2 Repository Hygiene and Legacy Containment
→ P3 Analysis Trust Domain Kernel
```

---

# 13. 交给 Codex 的执行摘要

```text
1. 在 F:\reverse-agent 检查本地和远端基线。
2. 保持 PR #9 Draft、未合并且 exact head 不变。
3. 继续使用 agent/architecture-constitution-plan-v1 和 PR #11。
4. 第一笔实施提交只创建新的 P0 Decision。
5. Decision 提交后生成 Command Plan 和 preflight。
6. 仅修改 docs/architecture/**、docs/adr/**、允许的 docs/roadmap/** 和必要当前轮 project_state 文件。
7. 编写七份架构文档、十份 ADR 和 long-term-implementation-plan-v2。
8. 不修改源码、测试、依赖、Workflow、PR #9、BMAD、LangGraph、数据库、Sandbox、Web 或工具接入。
9. 运行控制面 required tests、文档一致性检查和 Git diff 检查。
10. 生成报告和 closeout；只有满足全部验收标准才能标记 ARCHITECTURE_CONSTITUTION_ACCEPTED。
11. 不合并 PR #11，不开始 P1，不开始 Trust Layer 代码。
```
