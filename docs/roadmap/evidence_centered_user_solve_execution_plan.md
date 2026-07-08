# Evidence-Centered User Solve Execution Plan

## 0. 文档定位

本文是 reverse-agent 下一阶段的近期实施计划，用于把较大的平台路线拆成可连续执行的几轮工程任务。

本文不是 `DECISION_PACKET`，不能直接作为 Codex 当前轮任务。当前执行权威仍然是：

```text
project_state/decision_packet.md
```

命令授权权威仍然是：

```text
project_state/gates/command_plan.json
```

本文的作用是：

```text
1. 明确接下来几轮的推进顺序；
2. 避免继续只做过小的 gate 修补；
3. 避免直接跳到 Web、IDA MCP、自动 runner；
4. 把 User Solve、Evidence Replay、Project State Taxonomy、Fast Static Solve、Web Read Model 串成一个可审计的阶段性目标。
```

---

## 1. 阶段总目标

下一阶段总目标命名为：

```text
Evidence-Centered User Solve Foundation
```

一句话目标：

```text
让 reverse-agent 能以用户可理解的方式返回候选结果、验证状态、证据链、时间线和报告，同时继续保持 decision_packet、command-plan、execution_log、final-check、run-closeout 的工程审计闭环。
```

这不是单独做一个网页，也不是单独做一个 solver，而是把以下能力连起来：

```text
Project State 归属清晰
→ User Solve 结果契约稳定
→ Evidence Trace 可追溯
→ Fast Static Solve 能输出候选和证据
→ Web Read Model 能展示结果
→ 后续工具接入有统一 Evidence Provider 边界
```

---

## 2. 当前问题

当前项目已经有较强的治理骨架：

```text
project_state
DECISION_PACKET
command-plan
execution_log
pytest_result
codex_execution_report
report-summary
final-check
run-closeout
round_manifest
negative_results
artifact_index
context packet
workstream registry
```

但下一阶段要解决的问题不是继续堆 gate，而是把内部治理能力转化成用户可见的产品能力。

当前主要断点：

```text
1. project_state 顶层状态与 reverse_solving 样本状态仍然容易混用；
2. User Solve 返回格式没有成为稳定契约；
3. candidate、verified、runtime_validated、failed、blocked 的用户层语义还没有统一；
4. solver 输出与 evidence trace 之间还没有统一绑定；
5. Web 页面如果现在直接做，会缺少稳定 read model；
6. IDA/Ghidra/OllyDbg 如果现在接入，会缺少统一 provider contract 和 evidence schema；
7. roadmap 与 active decision 的边界需要继续保持清晰。
```

---

## 3. 大步推进原则

本计划允许比单次 gate 修复更大，但仍遵守以下规则：

```text
1. 每轮只推进一个 mainline；
2. roadmap 不是执行权威；
3. decision_packet 才是当前任务权威；
4. command-plan 才是命令权威；
5. 不跨主线混做 Web、solver、tool、runner；
6. 不移动或删除 project_state 历史文件；
7. 不执行样本；
8. 不调用 IDA/Ghidra/OllyDbg/MCP；
9. 不引入数据库替代 project_state；
10. 不做自动 push / PR / merge / runner dispatch。
```

---

## 4. 近期实施轮次总览

建议按 6 个较大的实施轮推进：

```text
Round A：Project State Domain Taxonomy Foundation
Round B：User Solve Contract and State Machine
Round C：Evidence Event and Solve Trace Schema
Round D：Fast Static Solve Wrapper
Round E：Web Workbench Read Model
Round F：Tool Provider Contract Readiness
```

这 6 轮合起来完成一个大的阶段性目标：

```text
用户上传逆向样本后，系统至少能返回候选、验证状态、证据来源、分析时间线和报告摘要；同时内部仍保留完整工程审计链。
```

---

## 5. Round A：Project State Domain Taxonomy Foundation

### mainline

```text
project_governance
```

### 目标

先解决状态归属问题，防止后续 User Solve、Evidence Replay、Web 和 Tool Integration 读取错状态。

### 要做

```text
1. 定义 project_state domain taxonomy；
2. 给 state_manifest 增加 role / scope / domain / freshness 语义；
3. 给 artifact_index 增加 scope / domain / mainline / freshness 语义；
4. 给 negative_results 增加 global_policy 与 domain-specific 分类；
5. 新增 domains 目录 skeleton 与 README；
6. 让 context builder 能识别 domain state 与 stale state；
7. final-check 对 legacy missing scope 先 warning，不直接 hard fail。
```

### 允许修改方向

```text
reverse_agent/project_state_manifest.py
reverse_agent/project_context.py
reverse_agent/project_gate.py
project_state/roadmap/workstreams.json
project_state/domains/*/README.md
tests/test_project_state_manifest.py
tests/test_project_context.py
tests/test_project_gate.py
docs/roadmap/project_state_domain_taxonomy_supplement.md
```

具体允许文件必须由未来 `DECISION_PACKET` 再精确列出。

### 不做

```text
不移动 current_state.json。
不删除 negative_results 旧记录。
不清理 artifact。
不创建数据库。
不改 solver。
不改 Web。
不接工具。
```

### 验收

```text
1. state_manifest 可以表达状态文件归属；
2. artifact_index 可以表达 artifact 归属；
3. negative_results 可以按 mainline/domain 过滤；
4. context packet 不把 stale reverse_solving 状态包装成 current governance evidence；
5. final-check 对新 metadata 有检查，对旧 metadata 保持兼容 warning。
```

---

## 6. Round B：User Solve Contract and State Machine

### mainline

```text
user_solve_layer
```

如果当前 registry 尚未支持该 mainline，则先使用：

```text
engineering_branch
```

并在 decision 中说明这是 User Solve Layer foundation，不是 Web 或 solver round。

### 目标

定义用户层结果格式和状态机，先稳定“用户看到什么”。

### 要做

```text
1. 定义 UserSolveResult；
2. 定义 UserSolveTask；
3. 定义 CandidateResult；
4. 定义 ValidationStatus；
5. 定义用户层状态机；
6. 定义 failed / blocked 的用户可读 reason；
7. 定义 internal evidence reference，但不暴露内部 governance 文件。
```

### 状态语义

```text
uploaded
fast_analyzing
candidate_found
static_verified
runtime_validation_pending
runtime_validated
failed
blocked
```

关键边界：

```text
candidate_found != verified
static_verified != runtime_validated
runtime_validated 必须有 runtime validation evidence
failed 必须有 reason
blocked 必须有 policy/tool/environment/sample_format reason
```

### 允许新增方向

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
docs/user_solve_contract.md
```

### 不做

```text
不上传样本。
不执行样本。
不实现 Web。
不调用 solver。
不调用工具。
不生成真实 candidate。
```

### 验收

```text
1. UserSolveResult JSON 稳定；
2. 非法状态转换被拒绝；
3. verified 类状态没有 evidence 时被拒绝；
4. candidate_found 可以 validation_status=pending；
5. 用户层 payload 不暴露 decision_packet / command-plan / negative_results 原文。
```

---

## 7. Round C：Evidence Event and Solve Trace Schema

### mainline

```text
evidence_replay
```

如果当前 mainline registry 尚未支持，则使用：

```text
engineering_branch
```

并明确这是 Evidence Replay schema foundation。

### 目标

让每个候选、验证、失败都能追溯来源。

### 要做

```text
1. 定义 EvidenceEvent；
2. 定义 SolveTrace；
3. 定义 CandidateEvidenceRef；
4. 定义 ValidationEvidence；
5. 定义 ReplayTimeline；
6. 定义 ReportEvidenceSummary；
7. 提供 trace -> timeline 的 deterministic 转换。
```

### 事件类型

```text
upload
hash
extract_strings
type_detect
solver_attempt
candidate_generated
validation_attempt
validation_result
fallback_step
report_generated
error
blocked
```

### 允许新增方向

```text
reverse_agent/evidence/events.py
reverse_agent/evidence/trace.py
reverse_agent/evidence/replay_model.py
reverse_agent/evidence/report_summary.py
tests/test_evidence_events.py
tests/test_solve_trace.py
tests/test_replay_model.py
docs/evidence_trace_schema.md
```

### 不做

```text
不实现前端页面。
不执行样本。
不调用外部工具。
不把 trace 写进 bulky solve_reports。
不把 missing evidence 伪装成 passed。
```

### 验收

```text
1. 每个 candidate 可引用 evidence event；
2. 每个 validation result 可引用 validation event；
3. failed/blocked 有明确 event；
4. replay timeline 可由 SolveTrace 确定性生成；
5. report summary 可引用 evidence 摘要而不复制大型 artifact。
```

---

## 8. Round D：Fast Static Solve Wrapper

### mainline

```text
reverse_solving
```

### 目标

在不执行样本、不调试、不调用外部逆向工具的前提下，封装一个用户层可用的安全静态快解入口。

### 支持的第一批能力

```text
1. 明文字符串比较识别；
2. Base64 静态识别；
3. 单字节 XOR 简单候选；
4. 简单 repeated-key XOR 候选；
5. 简单位移候选；
6. hash 字符串识别；
7. RC4 特征提示；
8. 查表结构提示。
```

### 要做

```text
1. 封装 FastStaticSolveWrapper；
2. 输入样本 metadata 或 extracted strings；
3. 输出 UserSolveResult；
4. 为每次尝试生成 SolveTrace；
5. candidate 绑定 CandidateEvidenceRef；
6. 不支持题型返回 failed/blocked。
```

### 允许新增方向

```text
reverse_agent/user_solve_fast.py
reverse_agent/static_extract.py
reverse_agent/static_candidate.py
reverse_agent/static_solve_trace.py
tests/test_user_solve_fast.py
tests/test_static_candidate.py
tests/test_static_solve_trace.py
```

### 不做

```text
不运行 exe。
不动态调试。
不调用 IDA/Ghidra/OllyDbg。
不调用 MCP。
不扩大 beam/topN 靠猜。
不把 static_verified 说成 runtime_validated。
```

### 验收

```text
1. 无候选时返回 failed/no_candidate；
2. 有候选时返回 candidate_found；
3. 静态检查通过时只标 static_verified；
4. 每个候选都有 evidence ref；
5. 每次尝试都有 SolveTrace；
6. unsupported 类型不会伪造成功。
```

---

## 9. Round E：Web Workbench Read Model

### mainline

```text
web_workbench
```

如果当前 mainline registry 尚未支持，则使用：

```text
engineering_branch
```

并明确不实现完整 Web runtime。

### 目标

先做 Web 后端读取模型，避免前端直接读取混乱内部状态。

### 要做

```text
1. TaskListItem；
2. TaskDetailView；
3. CandidateView；
4. ValidationView；
5. EvidenceTimelineView；
6. ReportView；
7. CapabilityMatrixView；
8. UserSolveResult -> TaskDetailView；
9. SolveTrace -> EvidenceTimelineView。
```

### 允许新增方向

```text
reverse_agent/web_read_models.py
reverse_agent/user_solve_views.py
reverse_agent/evidence_timeline_view.py
tests/test_web_read_models.py
tests/test_user_solve_views.py
docs/web_workbench_read_model.md
```

### 不做

```text
不做完整前端。
不做上传页面。
不做 runner dispatcher。
不做执行按钮。
不做自动 PR。
不绕过 command-plan。
```

### 验收

```text
1. UserSolveResult 能转换成用户任务详情；
2. SolveTrace 能转换成时间线；
3. candidate 与 validation 状态可区分；
4. blocked/failed reason 可展示；
5. read model 不暴露内部 gate 原始文件。
```

---

## 10. Round F：Tool Provider Contract Readiness

### mainline

```text
tool_integration
```

### 目标

为后续 IDA/Ghidra/OllyDbg/MCP 接入准备 contract，但不调用工具。

### 要做

```text
1. ToolProfile；
2. ToolCapability；
3. ToolProviderContract；
4. ProviderEvidenceOutput；
5. tool unavailable / blocked 状态；
6. timeout / risk_level / authorized_by_command_plan 字段。
```

### 允许新增方向

```text
reverse_agent/tool_profiles.py
reverse_agent/tool_capabilities.py
reverse_agent/tool_provider_contract.py
tests/test_tool_profiles.py
tests/test_tool_capabilities.py
tests/test_tool_provider_contract.py
docs/tool_provider_contract.md
```

### 不做

```text
不调用 IDA。
不调用 Ghidra。
不调用 OllyDbg。
不调用 x64dbg。
不调用 radare2。
不调用 MCP。
不执行外部二进制。
不把工具输出当最终事实。
```

### 验收

```text
1. 工具可用性可被建模；
2. 工具缺失返回 blocked/tool_unavailable；
3. provider output 必须转换为 evidence schema；
4. provider contract 支持 timeout/risk_level/allowed_operations；
5. 后续 command-plan 能精确授权工具调用。
```

---

## 11. 推荐第一份正式 DECISION_PACKET

下一份正式 `DECISION_PACKET` 建议选择：

```text
Round A：Project State Domain Taxonomy Foundation
```

原因：

```text
1. 这是后续 User Solve / Evidence Replay / Web / Tool Integration 的状态基础；
2. 当前审计限制项中 state_manifest freshness 正好属于这个问题；
3. 不会直接触碰样本执行、Web、外部工具等高风险能力；
4. 可以用 tests/final-check 验收；
5. 完成后上下文包和 workstream registry 更稳定。
```

推荐正式 decision_id：

```text
decision_20260708_state_domain_taxonomy_foundation_v1
```

推荐 round_id：

```text
round_20260708_state_domain_taxonomy_foundation_v1
```

推荐 mainline：

```text
project_governance
```

推荐 skill profile：

```text
reverse-agent-iteration@v2
```

---

## 12. 第一份 DECISION_PACKET 的边界建议

### Goal

```text
Add compatibility-first scoped state metadata and domain taxonomy foundations so that project_state can distinguish global governance state, reverse_solving sample state, current gate evidence, historical artifacts, and future user_solve/evidence/web/tool domains.
```

### Implementation Scope

只允许：

```text
1. 增加 metadata schema；
2. 增加 domain skeleton README；
3. 增加 state_manifest/artifact_index/negative_results scoped validation；
4. 增加 final-check warnings；
5. 增加 context packet domain awareness；
6. 增加测试。
```

不允许：

```text
1. 移动 current_state.json；
2. 删除 old negative_results；
3. 修改 solver；
4. 修改 Web；
5. 调用工具；
6. 运行样本；
7. cleanup apply；
8. 修改 .codex-skills；
9. push/commit/PR/merge/rebase。
```

### Tests

建议测试：

```text
python -m pytest tests/test_project_state_manifest.py tests/test_project_context.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate preflight
python -m reverse_agent.project_gate command-plan
python -m reverse_agent.project_gate final-check
python -m reverse_agent.project_gate run-closeout
```

具体命令仍以未来生成的 command-plan 为准。

---

## 13. 阶段完成后的项目形态

当 Round A-F 完成后，项目应具备如下能力：

```text
1. project_state 状态归属清晰；
2. User Solve 有稳定结果契约；
3. candidate / verified / runtime_validated / failed / blocked 被明确区分；
4. 每个候选都能追溯 evidence event；
5. 每次求解可生成 solve trace；
6. Web 可以读取稳定 read model；
7. 工具接入有 provider contract；
8. 仍然保持 command-plan、execution_log、pytest_result、final-check、run-closeout 审计闭环。
```

这时再进入下一阶段：

```text
Minimal Web Workbench
→ IDA/Ghidra evidence provider
→ controlled runner integration
→ CI/Auditor/Planner automation
```

---

## 14. 明确不要提前做的事

在 Round A-F 完成前，不建议做：

```text
1. 漂亮 Web 页面；
2. 自动上传样本页面；
3. IDA MCP；
4. Ghidra headless；
5. OllyDbg 脚本；
6. 数据库；
7. 自动 runner；
8. GitHub Actions 自动执行；
9. 漏洞挖掘 / crash triage；
10. 复杂多用户权限；
11. 自主 planner/auditor API；
12. 自动 push / PR / merge。
```

这些都可以做，但必须在 User Solve、Evidence Trace、State Domain、Web Read Model 稳定后再进入 roadmap accepted 或 active round。

---

## 15. 最终结论

下一阶段不应该继续做过小的状态修补，也不应该直接跳进 Web 或工具接入。

更合适的大步计划是：

```text
Project State Domain Taxonomy
→ User Solve Contract
→ Evidence Trace Schema
→ Fast Static Solve Wrapper
→ Web Read Model
→ Tool Provider Contract
```

这条路线的结果是：

```text
reverse-agent 从“内部可审计 solver 工程”推进到“用户可见、证据可追溯、后续可扩展 Web 和工具接入的平台基础”。
```

所有后续执行仍必须遵守：

```text
decision_packet 是当前任务权威；
command-plan 是命令权威；
execution_log 是执行事实；
artifact_index 是证据索引；
final-check 是硬门禁；
run-closeout 是收尾门禁；
audit 是最终裁决。
```
