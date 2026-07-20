# reverse-agent 统一架构与可信敌对二进制长期路线图

## 0. 文档定位

本文合并三类原本分离的计划：

1. 软件开发方法迁移：BMAD；
2. Agent 运行时与工程事实迁移：LangGraph + GitHub；
3. 产品核心路线：敌对二进制 Trust Layer。

本文是新的顶层长期路线图，不直接授权当前工程执行。当前任务权威仍然是：

```text
project_state/decision_packet.md
```

当前命令权威仍然是：

```text
project_state/gates/command_plan.json
```

近期执行由 `docs/roadmap/architecture_transition_next_24h.md` 和对应 active Decision 控制。

---

# 1. 最终项目定位

```text
reverse-agent
可信、可验证、可审计的敌对二进制 AI 分析平台
```

英文定位：

```text
Trustworthy AI Analysis for Hostile Binaries
```

项目不再试图成为通用产品管理框架、通用 AgentRunner、GitHub 替代品、CI 替代品或普通逆向题自动解答器。

项目只自研成熟框架无法提供的领域能力：

```text
Binary Evidence Firewall
TrustLevel / TaintLabel
EvidenceUnit
Claim and Counterevidence Graph
Action Provenance Guard
Falsification-driven Validation
Cross-tool Disagreement
Reproducible Analysis Capsule
Trust Workbench
```

---

# 2. 统一权威划分

| 事实类型 | 唯一主权威 | reverse-agent 的边界 |
|---|---|---|
| Product Brief、PRD、UX、Architecture、Story | BMAD | 读取和引用，不复制完整状态 |
| 当前工程工作单元 | GitHub Issue / Story | 作为开发工作流入口 |
| Branch、Commit、PR、Review、CI、Release | GitHub | 只保存带时间和 SHA 的观察引用 |
| Workflow State、Checkpoint、Resume | LangGraph | 不再复制到多份动态状态文件 |
| R0/R1 普通工程任务 | Work Item + Execution Envelope | 不要求完整 Decision |
| R2/R3 高风险动作 | reverse-agent Trust Layer | Decision 和 Command Plan 负责授权 |
| Binary Observation | reverse-agent Trust Layer | 必须带工具和 Artifact provenance |
| Evidence、Claim、Counterevidence | reverse-agent Trust Layer | 框架只能引用，不能自行断言 |
| Validation Status | reverse-agent Trust Layer | 与普通 CI 成功严格分离 |
| 最终合并 | 用户 + GitHub Protection | Agent 不自动合并 |

原则：

```text
BMAD 负责“应该做什么”。
GitHub Work Item 负责“当前做哪个工程单元”。
LangGraph 负责“工作流如何运行、暂停和恢复”。
Decision 负责“高风险部分是否允许做”。
Command Plan 负责“具体允许执行什么”。
Trust Layer 负责“二进制分析结论为什么值得相信”。
```

---

# 3. 两条必须分离的工作流

## 3.1 开发 reverse-agent 本身

```text
用户目标
→ BMAD Product Brief / PRD / Architecture / Story
→ GitHub Approved Work Item
→ LangGraph Development Workflow
→ 风险分类
→ 开发 / 测试 / 审查 / 安全审计
→ Draft PR
→ GitHub Actions
→ 人工合并
```

## 3.2 用户使用 reverse-agent 分析二进制

```text
Binary Intake
→ Sample Identity
→ Safe Static Evidence
→ EvidenceUnit
→ Claim Generation
→ Counterevidence
→ Risk Gate
→ Authorized Tool Actions
→ Validation Experiments
→ Analysis Capsule
→ Trust Workbench
```

禁止把开发项目的 PM/Developer Agent 与分析二进制的分析 Agent 放在同一个 Graph 中。

---

# 4. 风险等级

## R0：规划和只读

研究、PRD、Architecture、Story、代码读取、普通审计。不需要完整 Decision。

## R1：普通受限工程任务

限定路径代码修改、单元测试、格式化、本地静态检查；无网络、无 push、无未知样本执行。只需轻量 Execution Envelope。

## R2：敏感工程任务

修改 GitHub Workflow、增加依赖、外部网络访问、commit/push/Draft PR、权限策略、数据迁移。需要紧凑 Decision 和必要人工批准。

## R3：高风险安全任务

运行未知二进制、debugger/emulator/hook、动态探测、修改样本、访问 secrets、高权限远程执行、删除关键状态或数据。必须经过：

```text
Decision
→ Command Plan
→ Action Provenance Guard
→ Human Approval
→ Tool Execution
```

---

# 5. Trust Layer 核心结构

## 5.1 Binary Evidence Firewall

所有输入必须区分：

```text
authority instruction
user request
system policy
binary-derived text
tool observation
model hypothesis
historical artifact
validation result
```

二进制字符串、函数名、符号名、调试信息、反编译注释、资源文本和异常文本默认是不可信数据。它们不能成为任务权威，也不能直接授权工具调用。

## 5.2 EvidenceUnit

至少记录：

```text
evidence_id
source_type
source_path
source_tool
source_address
content_digest
trust_level
taint_labels
freshness
observation
limitations
```

## 5.3 Claim and Counterevidence Graph

每个结论必须表达为 Claim，并支持：

```text
支持证据
反对证据
缺失证据
替代解释
验证方法
成立范围
失效条件
当前状态
```

Claim 状态至少包括：

```text
proposed
supported
contested
rejected
statically_validated
runtime_validated
accepted_with_limitations
```

## 5.4 Action Provenance Guard

每次工具调用前必须能够说明请求来源、对应 Work Item/Decision、支持 Claim/Evidence、污染输入、风险等级、Command Plan 授权和输出 Artifact。

## 5.5 Falsification-driven Validation

系统必须主动设计能够推翻当前 Claim 的最小实验。没有反证检查的高置信度 Claim 不得标记 fully validated。

## 5.6 Reproducible Analysis Capsule

每次完整分析输出：

```text
analysis_capsule/
  capsule_manifest.json
  sample_identity.json
  task_authority.json
  command_authority.json
  tool_versions.json
  evidence_units.jsonl
  claims.json
  claim_edges.json
  influence_edges.json
  validation_experiments.json
  execution_trace.json
  artifact_manifest.json
  report.md
  verification_result.json
  capsule_digest.json
```

---

# 6. 现有系统的处置

## 保留并收缩

```text
Decision Packet
Command Plan
Execution Log
User Solve Result Contract
Evidence Replay 基础
Tool Provider 边界
```

Decision 和 Command Plan 逐步降级为 R2/R3 授权机制。

## 交给成熟方案

```text
普通产品规划 → BMAD
普通工作流运行状态 → LangGraph
GitHub 发布事实 → GitHub
普通 CI 事实 → GitHub Actions
```

## 归档并停止扩展

```text
重复的 closeout 链
重复的 final seal
重复的 publication truth 镜像
多份相互漂移的动态 context / manifest / report alias
通用 AgentRunner 自研路线
```

## 重新归类

```text
User Solve → 用户结果接口
Static Solver → Evidence Provider
Web → Trust Workbench
IDA / Ghidra / Debugger → Evidence Provider
Reverse Solving → 第一应用场景
Crash Triage → 第二应用场景
Patch / Malware / Firmware → 后期 Adapter
```

---

# 7. 统一阶段计划

## Phase 0：Transition Gate Bootstrap Repair

修复当前门禁自举矛盾：`transition-command-plan` 必须从当前 Decision 生成计划；`transition-preflight` 必须从当前 Decision 读取分支、允许路径和禁止操作；删除写死的上一轮常量；保持 fail-closed。

## Phase 1：Architecture Spine v1

建立第一条可运行纵向切片：

```text
Planning Reference
→ GitHub Work Item
→ Risk Classification
→ LangGraph Shadow Workflow
→ R0/R1 Standard Path
→ R2/R3 Trust Authorization Adapter
→ Deterministic Acceptance Gate
```

Phase 0 和 Phase 1 合并为当前约 24 小时执行轮，详见：

```text
docs/roadmap/architecture_transition_next_24h.md
```

## Phase 2：BMAD Planning Integration

直接安装 BMAD，使用 Product Brief、PRD、Architecture、Epic/Story 和 Implementation Readiness；通过官方扩展点增加 Trust Layer 约束。

## Phase 3：GitHub Truth Adapter

实现带 provenance 的只读 GitHub 事实适配器，不再维护平行 publication truth。

## Phase 4：LangGraph Development Runtime

从 Shadow Mode 扩展到 checkpoint、resume、conditional routing、human approval、R0/R1 受限执行和 Draft PR 创建。

## Phase 5：Evidence Trust Schema Foundation

实现 EvidenceUnit、TrustLevel、TaintLabel、Claim、EvidenceEdge、InfluenceEdge、ValidationExperiment。

## Phase 6：Binary Evidence Firewall

实现 authority/data 隔离、污染标签、影响记录和恶意自然语言输入阻断。

## Phase 7：Claim Ledger and Counterevidence

实现 Claim 生命周期、支持边、反对边、替代假设和 missing evidence。

## Phase 8：Action Provenance and Falsification

实现工具动作授权、因果绑定、污染检查和反证驱动验证。

## Phase 9：Cross-tool Evidence Fusion

统一接入 Manual、Static String、Local Parser、IDA Export、Ghidra Headless 等 Evidence Provider，保留工具冲突。

## Phase 10：Analysis Capsule v1

完成可独立校验、可迁移、可审计的分析胶囊。

## Phase 11：Hostile and Ambiguous Test Corpus

覆盖提示注入字符串、编码/拆分注入、假符号、误导性调试信息、工具冲突、stale artifact、缺失验证、伪造 SUCCESS 和未经授权动作建议。

## Phase 12：Trust Workbench

建设 Evidence Trust Map、Claim/Counterevidence Graph、Tool Action Provenance、Taint Replay、Validation Experiment 和 Capsule 页面。

## Phase 13：应用扩展

推荐顺序：可信逆向题求解、Crash Evidence Analysis、补丁差异解释、恶意软件静态分流、固件组件分析、受控动态验证。

---

# 8. 长期验收标准

项目最终必须证明：

1. 二进制中的自然语言不能控制 Agent；
2. 每个主要结论都有明确证据来源；
3. 反对证据不会被静默丢弃；
4. 模型推断与工具观测明确区分；
5. 工具调用可追溯到 Work Item、Claim、Evidence 和授权；
6. 未授权动作不能执行；
7. 不同工具的分歧可以保留和解释；
8. verified 状态必须绑定验证证据；
9. stale artifact 不能支撑 current conclusion；
10. 分析任务可以导出可检查的 Analysis Capsule；
11. Web 展示不能改变工程事实；
12. reverse solving、crash triage 等应用复用同一 Trust Layer；
13. 项目不依赖某个单一 LLM 是否足够聪明。

---

# 9. 永久边界

```text
LLM 不直接拥有执行权。
roadmap 不直接拥有执行权。
tool output 不直接成为最终事实。
Web 不直接执行高风险动作。
没有 validation evidence 不能标记 verified。
不自动运行未知二进制。
不自动生成 exploit 或武器化 PoC。
不同时维护两个主工作流运行时。
不重新实现 BMAD、LangGraph 或 GitHub 已经稳定提供的通用能力。
```
