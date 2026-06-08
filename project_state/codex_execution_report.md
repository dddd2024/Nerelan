```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
  "round_id": "round_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_input_length_evidence_recovery_v1",
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
    "project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -c \"import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json', encoding='utf-8'))\"",
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
    "project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json"
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
- [x] 新 artifact 覆盖 0x64e5、0x6438、0x629f、0x62cb 及 loop_0x647d_0x62bb context
- [x] 新 artifact 给出 per-site length_role_hypothesis / confidence / supports_input_length
- [x] 新 artifact 避免把任何 site 标成 confirmed_input_length
- [x] 新 artifact 保持 known_input_length=null、input_length_confirmed=false
- [x] 新 artifact 明确 input_length_status=UNRESOLVED_WITH_HINTS 与 recommended_next_mainline=tool_integration
- [x] artifact_index 登记新 artifact，freshness=current、source_run 为当前 round、sha256/size_bytes 为真实值
- [x] 没有修改 training_status/status_overlay
- [x] 没有读取 full solve_reports 或 PROJECT_PROGRESS_LOG
- [x] 没有修改 solver production code
- [x] 运行 JSON parse 校验
- [x] 运行 py_compile、pytest、lint-decision、lint-report、status
- [x] 运行 git diff --check、git status --short、git diff --name-status
- [x] git diff 只包含允许文件

## 2. Source Artifacts Audited

| Artifact | Status | Identity Verified |
|----------|--------|-------------------|
| compare_constants_mapping | SUCCESS | true |
| missing_branch_reconciliation | SUCCESS | true |
| loop_semantics_mapping | SUCCESS | true |
| structured_evidence_projection | SUCCESS | true |
| targeted_static_solving | PARTIAL | true |
| bounded_static_extraction | SUCCESS | true |

## 3. New Artifact Summary

生成：`project_state/local_reverse_cpp2_883e67b9_input_length_evidence_recovery.json`

### Length-Related Sites Analysis

| RVA | Value | Length Role | Confidence | Supports Input Length |
|-----|-------|-------------|------------|----------------------|
| 0x64e5 | 0x100 (256) | byte_domain_loop_bound | medium | false |
| 0x6438 | 0xff (255) | sentinel_or_mask | medium | false |
| 0x629f | 0x10c (268) | table_or_buffer_offset | low | false |
| 0x62cb | 0x108 (264) | table_or_buffer_offset | low | false |

### Key Findings

- **0x64e5 + 0x6438**: 配对出现于 loop_0x647d_0x62bb 末端，形成 byte-domain 迭代上界 (0-255, exit when >= 256)，不代表输入长度
- **0x629f + 0x62cb**: 32位值，差为4，可能是 struct field offset 或 table entry，不代表输入长度
- **无直接输入长度证据**: 没有 strlen 模式、没有小常量长度比较、没有可确认的 null-termination check
- **可能的长度机制**: null-terminated string (medium likelihood)、loop-terminates-on-compare-mismatch (medium likelihood)、fixed-length (low likelihood)

### Status

- input_length_status = UNRESOLVED_WITH_HINTS
- known_input_length = null
- input_length_confirmed = false
- recommended_next_mainline = tool_integration

## 4. Tests

| 测试 | 结果 |
|------|------|
| JSON parse validation | ✅ PASS |
| py_compile | ✅ PASS |
| pytest | ✅ 179 passed |
| lint-decision | ✅ OK |
| lint-report | ✅ OK |
| project_state status | ✅ OK |
| git diff --check | ✅ PASS |

## 5. Stop Conditions

无停止条件触发。

## 6. Next Steps

- 本轮 input length evidence recovery 为 UNRESOLVED_WITH_HINTS
- 推荐下一轮：bounded formula-readiness audit，分析 focus comparison loops (0x6081, 0x61e8) 的退出条件
- 或准备 runtime probe 直接观察输入长度行为
- 不推进 candidate generation 或 runtime validation
