```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "round_id": "round_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_structured_evidence_projection_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "tool_integration",
  "sample_id": "cpp2_883e67b9",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/artifact_index.json",
    "project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json"
  ]
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] decision_packet 是唯一执行权威
- [x] mainline 为 tool_integration
- [x] task_packet 仅为 advisory
- [x] 确认本轮不是 reverse_solving，不生成/验证 candidate
- [x] 确认没有运行样本、runtime validation、debugger、hook、emulator、probe、winpty
- [x] 确认没有调用 IDA/Ghidra 或重新读取样本二进制
- [x] 检查了已有 StructuredEvidence / solver profile / project_state / artifact_index 接口
- [x] 复用了已有接口/格式，未新建重复框架
- [x] 读取并只使用 current 的 cpp2_883e67b9 source artifacts
- [x] 新 artifact 记录 source artifacts/source_run/freshness
- [x] 新 artifact 记录 identity_verified 与 sha256/size 事实
- [x] 新 artifact 区分可结构化证据和证据缺口
- [x] 新 artifact 明确 solver_profile_readiness 与 recommended_next_mainline
- [x] artifact_index 登记新 artifact，freshness=current、source_run 为当前 round
- [x] 没有修改 training_status/status_overlay
- [x] 没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG
- [x] 没有修改 solver production code
- [x] 运行 py_compile
- [x] 运行相关 pytest
- [x] 运行 lint-decision、lint-report、project_state status
- [x] 运行 git diff --check、git status --short、git diff --name-status
- [x] git diff 只包含允许文件

## 2. Source Artifacts Audited

读取并审计了以下 current artifacts：

| Artifact | Status | Identity Verified |
|----------|--------|-------------------|
| local_reverse_cpp2_883e67b9_bounded_static_triage_readiness | READY | true |
| local_reverse_cpp2_883e67b9_bounded_static_extraction | SUCCESS | true |
| local_reverse_cpp2_883e67b9_targeted_static_solving | PARTIAL | true |
| local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction | PARTIAL | true |

所有 source artifacts 均为 current，identity 一致，sample_id=cpp2_883e67b9。

## 3. Existing Interfaces Checked

检查了以下已有接口：

- `reverse_agent/project_state.py` — artifact_index 注册约定、IMPORTANT_ARTIFACTS、LATEST_ARTIFACT_KEYS
- `reverse_agent/local_reverse_solver_profiles.py` — SolverProfileResult、ProfileNormalizedEvidence、SUPPORTED_NORMALIZED_PROFILES
- `reverse_agent/local_reverse_constraint_recovery.py` — 约束恢复接口（未修改）
- `reverse_agent/local_reverse_ida_guided_solver.py` — IDA solver 接口（未修改）
- `reverse_agent/local_reverse_string_solver.py` — 字符串 solver 接口（未修改）

结论：已有接口足以表达 projection schema，无需修改 production code。

## 4. New Artifact Summary

生成：`project_state/local_reverse_cpp2_883e67b9_structured_evidence_projection.json`

Schema 包含：
- identity（sha256、size、identity_verified）
- source_artifacts（4 个 source artifact 的 provenance）
- source_status（各 source artifact 的状态摘要）
- structured_evidence（pe_mapping、string_anchors、bounded_regions、branch_summary、compare_constants）
- evidence_gaps（7 个明确缺口，含 severity 和 blocks 字段）
- solver_profile_readiness = READY_WITH_LIMITATIONS
- recommended_next_mainline = tool_integration
- candidate_generated = false
- runtime_validation_attempted = false
- training_status_modified = false
- status_overlay_modified = false

## 5. Tests

### py_compile
```
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py
```
结果：PASS（无语法错误）

### pytest
```
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
```
结果：见 pytest_result.txt

### lint-decision
```
.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state
```
结果：PASS

### lint-report
```
.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state
```
结果：PASS

### project_state status
```
.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state
```
结果：PASS

### git checks
```
git diff --check -> PASS
git status --short -> (recorded)
git diff --name-status -> (recorded)
```

## 6. Stop Conditions

无停止条件触发。所有 required source artifacts 存在且为 current，identity 匹配，无需运行样本或调用 IDA/Ghidra/debugger/runtime。

## 7. Next Steps

- 本轮 projection 为 READY_WITH_LIMITATIONS，推荐下一轮继续 tool_integration
- 若后续能补全 compare constants 的语义映射并恢复完整公式，可再决策是否进入 reverse_solving
- 不推进 candidate generation 或 runtime validation，直到 evidence gaps 显著缩小
