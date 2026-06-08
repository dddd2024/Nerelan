```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1",
  "round_id": "round_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1",
  "based_on_decision_id": "decision_20260608_cpp2_883e67b9_target_array_audit_report_rework_v1",
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
    "project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json",
    "reverse_agent/ida_scripts/xref_boundary_audit.py",
    "reverse_agent/ida_scripts/decompile_sub_401120.py",
    "reverse_agent/ida_scripts/decompile_sub_401014.py"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -c \"import json; json.load(open('project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json', encoding='utf-8'))\"",
    ".venv\\Scripts\\python -m py_compile reverse_agent/project_state.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_ida_guided_solver.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_project_state.py tests/test_local_reverse_solver_profiles.py tests/test_local_reverse_solver_profile_dispatch.py",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_cpp2_883e67b9_target_array_xref_boundary_audit.json"
  ]
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] decision_packet 是唯一执行权威
- [x] mainline 为 tool_integration
- [x] task_packet 仅为 advisory
- [x] 确认本轮不是 reverse_solving，不生成/验证 candidate
- [x] 确认没有运行样本交互逻辑、runtime validation、debugger、hook、emulator、probe、winpty
- [x] 检查并复用了已有 IDA/IDAPython 接口
- [x] 新建了专用 xref_boundary_audit.py 脚本（复用 IDA 接口框架），未重复造轮子
- [x] IDA 静态接口执行了 3 次，范围限定在 focus functions/data symbols
- [x] 读取并只使用 current 的 cpp2_883e67b9 source artifacts（9 个）
- [x] 新 artifact 记录 source artifacts/source_run/freshness
- [x] 新 artifact 包含 target_symbols、byte_429A34_boundary_candidates、selected_target_array_boundary、xrefs、transform_chain_hypothesis、formula_evidence_summary
- [x] 新 artifact 没有把 byte_429A34 边界标为 confirmed（除非有 XREF 证据支持）
- [x] 新 artifact 保持 candidate_generated=false、runtime_validation_attempted=false
- [x] 新 artifact 保持 reverse_solving_ready=true（公式证据完整，边界已解决）
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
| ida_ghidra_focus_loop_extraction | ACCEPTED_WITH_LIMITATIONS | true |
| formula_readiness_audit | SUCCESS | true |
| input_length_evidence_recovery | SUCCESS | true |
| compare_constants_mapping | SUCCESS | true |
| structured_evidence_projection | SUCCESS | true |
| loop_semantics_mapping | SUCCESS | true |
| missing_branch_reconciliation | SUCCESS | true |
| bounded_static_extraction | SUCCESS | true |
| targeted_static_solving | PARTIAL | true |

## 3. Tool Execution Summary

| # | Script | Purpose | Exit Code |
|---|--------|---------|-----------|
| 1 | xref_boundary_audit.py | XREF + data window extraction | 0 |
| 2 | decompile_sub_401120.py | Key init function + call chain | 0 |
| 3 | decompile_sub_401014.py | sub_401014 thunk + key init data | 0 |

## 4. Key Discovery: XOR Key Initialization

**Prior ambiguity**: `byte_429A34[i] ^ 0x66` produced `U.wTkAGwDvwAN[P` (0x7F at position 1)

**Root cause**: `sub_401120` (called via `sub_401014` from `_main_0`) modifies `byte_429A30` before comparison:
```c
memcpy(byte_42CCAC, 0x40004E, 0x2B);  // Copy DOS stub text
for (i = 0; i < 43; ++i) {
    byte_429A30 ^= byte_42CCAC[4 * i];  // XOR accumulate
}
```

**Key transform**: Initial `0x66` → Runtime `0x78` (XOR with DOS stub text bytes at stride 4)

**Complete call chain**:
```
_main_0 → sub_401005 → sub_401090 (input + length check)
         → sub_401014 → sub_401120 (key init: 0x66 → 0x78)
         → sub_40100A → sub_4011E0 (XOR compare with key 0x78)
```

## 5. Target Array Boundary Candidates

| Candidate | XOR 0x66 | XOR 0x78 | Printable | Status |
|-----------|----------|----------|-----------|--------|
| 0x429A32 | ffU.wTkAGwDvwAN (14/15) | — | — | Rejected (not XREF confirmed) |
| **0x429A34** | **U.wTkAGwDvwAN[P (14/15)** | **15/15 printable ASCII** | **15/15** | **Selected (XREF confirmed)** |
| 0x429A36 | wTkAGwDvwAN[Pff (15/15) | — | — | Rejected (not XREF confirmed) |

## 6. Formula Evidence Summary

| Parameter | Value |
|-----------|-------|
| Input length | 15 |
| XOR key (static) | 0x66 |
| XOR key (runtime) | 0x78 |
| Target array VA | 0x429A34 |
| Target array bytes | 33 19 11 32 0D 27 21 11 22 10 11 27 28 3D 36 |
| Formula | input[i] ^ 0x78 == byte_429A34[i] |
| Inverse | input[i] = byte_429A34[i] ^ 0x78 |
| **Decoded output** | **REDACTED (15/15 printable ASCII)** |

## 7. XREF Audit

| Symbol | XREF Count | Key Sites |
|--------|-----------|-----------|
| byte_429A34 | 1 | sub_4011E0: movsx edx, byte_429A34[ecx] |
| byte_429A30 | 3 | sub_401120: read+write (key init), sub_4011E0: xor (compare) |
| byte_429A31 | 2 | sub_401090: length check, sub_4011E0: loop bound |
| Str | 5 | sub_401090: scanf+strlen, sub_4011E0: read+write+read |

## 8. Readiness Update

| Metric | Prior | Current |
|--------|-------|---------|
| formula_boundary_resolved | false | **true** |
| target_array_boundary_confidence | none | **high** |
| solver_profile_normalization_ready | false | **true** |
| reverse_solving_ready | false | **true** |
| recommended_next_mainline | tool_integration | **reverse_solving** |

## 9. Tests

| 测试 | 结果 |
|------|------|
| JSON parse validation | PASS |
| py_compile | PASS |
| pytest | PASS |
| lint-decision | OK |
| lint-report | OK |
| project_state status | OK |
| git diff --check | PASS |

## 10. Stop Conditions

无停止条件触发。

## 11. Next Steps

- 本轮 target_array_xref_boundary_audit 确认 `SUCCESS_BOUNDARY_RESOLVED`
- 公式证据完整：input_length=15, xor_key=0x78 (runtime), target_array=byte_429A34[0..14]
- 所有先前方轮的歧义已解决（XOR key 初始化函数 sub_401120 发现）
- 推荐下一轮切换到 `reverse_solving` 主线，生成 candidate 并进行 runtime validation
