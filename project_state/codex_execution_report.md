```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_loop_semantics_mapping_v1",
  "round_id": "round_20260608_cpp2_883e67b9_loop_semantics_mapping_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_loop_semantics_mapping_v1",
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
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json"
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
    "project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json"
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
- [x] 新 artifact 记录 assert_path region 与 5 个 backward branch clusters
- [x] 新 artifact 区分 focus observed sites 与 missing sites
- [x] 新 artifact 把 compare constants 归类为 pending/unknown，而不是 confirmed formula
- [x] 新 artifact 明确 loop_semantics_status=MAPPED_WITH_LIMITATIONS 与 recommended_next_mainline=tool_integration
- [x] artifact_index 登记新 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值
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
| local_reverse_cpp2_883e67b9_structured_evidence_projection | SUCCESS | true |
| local_reverse_cpp2_883e67b9_bounded_loop_evidence_extraction | PARTIAL | true |
| local_reverse_cpp2_883e67b9_bounded_static_extraction | SUCCESS | true |
| local_reverse_cpp2_883e67b9_targeted_static_solving | PARTIAL | true |

所有 source artifacts 均为 current，identity 一致，sample_id=cpp2_883e67b9。

## 3. Existing Interfaces Checked

检查了以下已有接口：

- `reverse_agent/project_state.py` — artifact_index 注册约定、IMPORTANT_ARTIFACTS、LATEST_ARTIFACT_KEYS
- `reverse_agent/local_reverse_solver_profiles.py` — SolverProfileResult、ProfileNormalizedEvidence、SUPPORTED_NORMALIZED_PROFILES
- `reverse_agent/local_reverse_constraint_recovery.py` — 约束恢复接口（未修改）
- `reverse_agent/local_reverse_ida_guided_solver.py` — IDA solver 接口（未修改）
- `reverse_agent/local_reverse_string_solver.py` — 字符串 solver 接口（未修改）

结论：已有接口足以表达 loop_semantics_mapping schema，无需修改 production code。

## 4. New Artifact Summary

生成：`project_state/local_reverse_cpp2_883e67b9_loop_semantics_mapping.json`

Schema 包含：
- identity（sha256、size、identity_verified）
- source_artifacts（4 个 source artifact 的 provenance）
- source_status（各 source artifact 的状态摘要）
- assert_path_region（start_rva=0x5f00, end_rva_exclusive=0x6500, focus_assert_path_rva=0x61c3）
- loop_clusters（5 个 backward branch cluster，含 nearby compares、semantic_hypothesis、expected_focus_site）
- focus_backward_sites（observed=[0x6081, 0x61e8]、missing=[0x5f68, 0x60a4, 0x60b6]）
- compare_constants_classification（10 个常量，全部 semantic_role=unknown/pending）
- evidence_gaps_carried_forward（5 个明确缺口）
- loop_semantics_status = MAPPED_WITH_LIMITATIONS
- formula_recovered = false
- candidate_generated = false
- runtime_validation_attempted = false
- training_status_modified = false
- status_overlay_modified = false
- recommended_next_mainline = tool_integration

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

- 本轮 loop_semantics_mapping 为 MAPPED_WITH_LIMITATIONS，推荐下一轮继续 tool_integration
- 若后续能补全 compare constants 的语义映射、恢复 missing backward sites、明确输入长度，可再决策是否进入 reverse_solving
- 不推进 candidate generation 或 runtime validation，直到 evidence gaps 显著缩小
