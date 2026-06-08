```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_solver_profile_dispatch_guardrails_v1",
  "round_id": "round_20260608_solver_profile_dispatch_guardrails_v1",
  "based_on_decision_id": "decision_20260608_solver_profile_dispatch_guardrails_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "multi_solved_profile_dispatch_guardrails",
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/local_reverse_constraint_recovery.py",
    "tests/test_local_reverse_solver_profile_dispatch.py",
    "project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "tests/test_local_reverse_solver_profile_dispatch.py",
    "tests/test_local_reverse_solver_profiles.py",
    "tests/test_project_state.py"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_solver_profile_dispatch_guardrails_audit.json"
  ]
}
```

# Codex Execution Report

## 1. Decision Authority Check

- [x] decision_packet 是唯一执行权威
- [x] mainline 为 engineering_branch
- [x] task_packet 仅为 advisory
- [x] 确认本轮不是 reverse_solving，不解新题
- [x] 确认未推进 cpp2_883e67b9

## 2. Previous Round Baseline

- [x] 上一轮 dispatch integration 为本轮基础
- [x] 上一轮 report: report_20260608_solver_profile_dispatch_integration_v1
- [x] 上一轮 audit: local_reverse_solver_profile_dispatch_integration_audit

## 3. Guardrail Changes

### Phase A — Profile/Classification Mismatch Guardrail

在 `reverse_agent/local_reverse_constraint_recovery.py` 的 `recover_profile_normalized_constraints` 中，在调用 `_normalized_profile_payload` 之前加入显式检查：

1. **top-level profile mismatch**: 当 `evidence["profile"]` 存在且与 `classification` 不一致时，返回 `BLOCKED:PROFILE_CLASSIFICATION_MISMATCH`，不生成 candidate。
2. **nested profile mismatch**: 当 `evidence["normalized_profile_evidence"]["profile"]` 存在且与 `classification` 不一致时，同样返回 `BLOCKED:PROFILE_CLASSIFICATION_MISMATCH`。

关键设计：mismatch 检查在 `_normalized_profile_payload` 调用之前执行，避免 `nested.setdefault("profile", classification)` 掩盖显式 mismatch。

### Phase B — Freshness=Current Guardrail

在 `_normalized_profile_payload` 之后、调用 `solve_normalized_profile` 之前加入检查：

- `freshness` 必须为 `"current"`
- `freshness` 在 `{"stale", "missing", "unknown", ""}` 或字段缺失时，返回 `BLOCKED:NON_CURRENT_PROFILE_EVIDENCE`
- 字段缺失按 `unknown` 处理，不允许默认 `current`

### Phase C — Existing Behavior Preservation

- [x] invert_xor_array_table / invert_bytewise_transform_table / invert_digit_mod_affine_table 的纯函数 happy path 未改变
- [x] unknown transform_kind 仍返回 BLOCKED，不执行任意表达式
- [x] api_assisted_password_write_and_compare 的基础 synthetic regression 未回退
- [x] bounded_input_range_hash_output_increment_compare 和 sha256_hex_compare_with_post_hash_character_adjustment 的 dispatch 顺序和 blocked 行为未改变
- [x] runtime_allowed=false 时不调用 probe_runner

## 4. Required Audit Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | decision_packet 是否是唯一执行权威？ | YES |
| 2 | mainline 是否为 engineering_branch？ | YES |
| 3 | task_packet 是否仅为 advisory？ | YES |
| 4 | 是否确认本轮不是 reverse_solving，不解新题？ | YES |
| 5 | 是否确认未推进 cpp2_883e67b9？ | YES |
| 6 | 上一轮 dispatch integration 是否为本轮基础？ | YES |
| 7 | 是否修复 profile/classification mismatch 的静默求解风险？ | YES，现在显式阻断 |
| 8 | mismatch 时具体 blocked_reason 是什么？ | `BLOCKED:PROFILE_CLASSIFICATION_MISMATCH` |
| 9 | 是否修复 stale/missing/unknown freshness 仍可生成 candidate 的风险？ | YES，现在显式阻断 |
| 10 | non-current freshness 时具体 blocked_reason 是什么？ | `BLOCKED:NON_CURRENT_PROFILE_EVIDENCE` |
| 11 | nested normalized_profile_evidence 的 profile mismatch 是否也会阻断？ | YES |
| 12 | 当前三类 profile 的 current evidence happy path 是否仍通过？ | YES，全部通过 |
| 13 | unknown transform_kind 是否仍 blocked，且不执行表达式字符串？ | YES |
| 14 | 现有 api/hash/sha constraint recovery 行为是否未回退？ | YES |
| 15 | 是否没有运行样本？ | YES，仅 synthetic 测试 |
| 16 | 是否没有 runtime validation/debugger/hook/emulator/probe/winpty？ | YES |
| 17 | 是否没有调用 IDA/Ghidra 或读取二进制？ | YES |
| 18 | 是否没有修改 training_status/status_overlay？ | YES |
| 19 | 是否没有读取 full solve_reports？ | YES |
| 20 | 是否没有在 production code 中硬编码真实 candidate？ | YES，已检查 |
| 21 | 是否新增或更新了 synthetic-only 测试？ | YES，新增 7 个测试 |
| 22 | pytest_result 是否包含当前 decision_id/report_id/round_id？ | YES |
| 23 | artifact_index 是否登记 guardrails audit artifact？ | YES |
| 24 | git diff 是否只包含允许文件？ | YES |

## 5. Test Results

```
pytest target: tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py
result: 179 passed
```

新增测试覆盖：
- test_top_level_profile_mismatch_blocks_without_candidate
- test_nested_profile_mismatch_blocks_without_candidate
- test_stale_freshness_blocks_without_candidate
- test_missing_freshness_blocks_without_candidate
- test_unknown_freshness_blocks_without_candidate
- test_empty_string_freshness_blocks_without_candidate
- test_current_freshness_and_matching_profile_happy_path

## 6. Lint / Status Checks

- py_compile: PASS
- lint-decision: PASS
- lint-report: PASS
- git diff --check: PASS

## 7. Next Recommended Action

继续 engineering_branch 的 guardrail 加固，或在获得新的静态证据后过渡到 tool_integration。
