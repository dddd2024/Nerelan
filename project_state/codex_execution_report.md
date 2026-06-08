```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_compare_constants_mapping_v1",
  "round_id": "round_20260608_cpp2_883e67b9_compare_constants_mapping_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_compare_constants_mapping_v1",
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
    "project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json"
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
    "project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json"
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
- [x] 新 artifact 记录 10 个 compare constants 与 per-constant semantic_role_hypothesis
- [x] 新 artifact 避免把任何 constant 标成 confirmed_formula_constant 或 candidate source
- [x] 新 artifact 保持 known_compare_constant_count=0
- [x] 新 artifact 明确 constants_mapping_status=MAPPED_WITH_LIMITATIONS 与 recommended_next_mainline=tool_integration
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
| local_reverse_cpp2_883e67b9_missing_branch_reconciliation | SUCCESS | true |
| local_reverse_cpp2_883e67b9_loop_semantics_mapping | SUCCESS | true |
| local_reverse_cpp2_883e67b9_structured_evidence_projection | SUCCESS | true |
| local_reverse_cpp2_883e67b9_targeted_static_solving | PARTIAL | true |
| local_reverse_cpp2_883e67b9_bounded_static_extraction | SUCCESS | true |

所有 source artifacts 均为 current，identity 一致，sample_id=cpp2_883e67b9。

## 3. Existing Interfaces Checked

检查了以下已有接口：

- `reverse_agent/project_state.py` — artifact_index 注册约定
- `reverse_agent/local_reverse_solver_profiles.py` — SolverProfileResult、ProfileNormalizedEvidence
- `reverse_agent/local_reverse_constraint_recovery.py` — 约束恢复接口（未修改）
- `reverse_agent/local_reverse_ida_guided_solver.py` — IDA solver 接口（未修改）
- `reverse_agent/local_reverse_string_solver.py` — 字符串 solver 接口（未修改）

结论：已有接口足以表达 compare_constants_mapping schema，无需修改 production code。

## 4. New Artifact Summary

生成：`project_state/local_reverse_cpp2_883e67b9_compare_constants_mapping.json`

### Compare Constants Semantic Mapping

| RVA | Type | Value | Semantic Role | Confidence | Formula Role |
|-----|------|-------|---------------|------------|-------------|
| 0x5f38 | cmp_al_imm8 | 0xc2 (194) | unknown | low | none |
| 0x6077 | cmp_imm8 | 0x1 (1) | control_state_flag | medium | pending |
| 0x60f7 | cmp_al_imm8 | 0x8d (141) | algorithm_constant_candidate | low | pending |
| 0x6124 | cmp_al_imm8 | 0x85 (133) | algorithm_constant_candidate | low | pending |
| 0x618f | cmp_imm32 | 0x1102 (4354) | table_or_address_constant | low | none |
| 0x61de | cmp_imm8 | 0x1 (1) | control_state_flag | medium | pending |
| 0x629f | cmp_imm32 | 0x10c (268) | table_or_address_constant | low | none |
| 0x62cb | cmp_imm32 | 0x108 (264) | table_or_address_constant | low | none |
| 0x6438 | cmp_imm8 | 0xff (255) | sentinel_or_mask | medium | pending |
| 0x64e5 | cmp_imm32 | 0x100 (256) | loop_index_or_bound | medium | pending |

### Key Observations

- **control_state_flag** (0x6077, 0x61de): 两个 `cmp eax, 1` 分别位于两个 focus comparison loop 附近，形成重复的控制流模式
- **algorithm_constant_candidate** (0x60f7, 0x6124): 两个 `cmp al` 位于 focus loop 0x6081 内，可能是逐字符比较常量
- **sentinel_or_mask** (0x6438): `cmp 0xff` 是经典的 EOF/掩码值
- **loop_index_or_bound** (0x64e5): `cmp 0x100` 是字节迭代的经典循环上界
- **table_or_address_constant** (0x618f, 0x629f, 0x62cb): 32位大值，可能是地址偏移或表索引

### Status

- known_compare_constant_count = 0（无 current source artifact 支持升级）
- constants_mapping_status = MAPPED_WITH_LIMITATIONS
- formula_recovered = false
- candidate_generated = false
- recommended_next_mainline = tool_integration（优先 input length evidence recovery）

## 5. Tests

### py_compile
```
.venv\Scripts\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py
```
结果：PASS

### pytest
```
.venv\Scripts\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py
```
结果：见 pytest_result.txt

### lint-decision / lint-report / status
结果：PASS

### git checks
结果：PASS

## 6. Stop Conditions

无停止条件触发。

## 7. Next Steps

- 本轮 compare constants mapping 为 MAPPED_WITH_LIMITATIONS，推荐下一轮继续 tool_integration
- 优先方向：input length evidence recovery，利用 0x64e5 (cmp 0x100) 和 0x6438 (cmp 0xff) 作为循环上界/输入长度线索
- 不推进 candidate generation 或 runtime validation，直到 evidence gaps 显著缩小
