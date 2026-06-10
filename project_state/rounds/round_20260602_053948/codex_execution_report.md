```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1",
  "round_id": "round_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1",
  "based_on_decision_id": "decision_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "reverse_agent/local_reverse_training_status.py",
    "tests/test_local_reverse_training_status.py",
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_evaluation_queue.json",
    "training_materials/local_reverse/status_overlay.json",
    "project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    "python -m py_compile reverse_agent/local_reverse_training_status.py",
    "python -m pytest -q tests/test_local_reverse_training_status.py",
    "python -m pytest -q tests/test_project_state.py",
    "python -m reverse_agent.local_reverse_training_status --inventory project_state/local_reverse_inventory.json --out project_state/local_reverse_training_status.json --queue-out project_state/local_reverse_evaluation_queue.json --github-status-out training_materials/local_reverse/status_overlay.json",
    "python -m reverse_agent.project_state lint-decision --state-dir project_state",
    "python -m reverse_agent.project_state lint-report --state-dir project_state",
    "python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json"
  ],
  "next_suggested_task": "继续处理 evaluation_queue 中剩余的 inventory_only 样本，或回到 samplereverse 主线执行 bounded compare_real_lhs_provenance_audit rerun"
}
```

# Codex Execution Report

## Summary

本轮执行了 `decision_20260606_cpp2_2f64e68d_training_status_blocked_overlay_v1`，主线为 **training_dataset**。目标是修复 `cpp2_2f64e68d` 的训练状态同步缺口：该样本已有 current 静态提取、runtime pair validation（AMBIGUOUS_OUTPUT）和 mature backend probe（BLOCKED_MATURE_BACKEND_MISSING）证据，但 `local_reverse_training_status.json` 仍将其列为 `inventory_only`。

本轮将其同步为 **blocked**，blocked_reason 来源于 mature backend probe（优先级高于 ambiguous runtime），known_candidate 保持为空，并从 evaluation_queue 中移除。

## Files Changed

- `reverse_agent/local_reverse_training_status.py`
  - 新增 `_build_runtime_blocked_overlay()`：消费 `AMBIGUOUS_OUTPUT`、`VALIDATED_FAILURE`、`BLOCKED` 状态的 runtime validation artifact，标记为 blocked，不输出 known_candidate。
  - 新增 `_build_mature_backend_blocked_overlay()`：消费 `BLOCKED_MATURE_BACKEND_MISSING` 状态的 mature backend probe artifact，标记为 blocked。
  - 修改 `build_training_status()` 合并逻辑：优先级为 solved > blocked_map > mature_backend_blocked > runtime_blocked > static_handoff > inventory_only。
- `tests/test_local_reverse_training_status.py`
  - 新增 8 个测试用例：AMBIGUOUS_OUTPUT blocked、VALIDATED_FAILURE blocked、failure_reason fallback、mature backend blocked、can_attempt_true skipped、solved_true skipped、mature backend 优先级覆盖 ambiguous runtime、validated success 回归测试。
  - 更新 `test_real_cpp1_target_provenance_recheck_removes_cpp1_from_queue`：验证 cpp2_2f64e68d 现在为 blocked 且不在队列中。
- `project_state/local_reverse_training_status.json` — 重新生成
- `project_state/local_reverse_evaluation_queue.json` — 重新生成
- `training_materials/local_reverse/status_overlay.json` — 重新生成
- `project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json` — 新建
- `project_state/artifact_index.json` — 登记新 artifact

## Audit Result

| # | 审计项 | 结果 |
|---|--------|------|
| 1 | decision_packet 是本轮唯一执行权威 | PASS |
| 2 | task_packet 只是旧 samplereverse advisory | PASS |
| 3 | 本轮主线为 training_dataset | PASS |
| 4 | 上一轮 minimal archive closeout 已 SUCCESS/ACCEPTED/PASSED/archived | PASS |
| 5 | cpp2_2f64e68d 四个 source artifacts 均为 current | PASS |
| 6 | direct strcmp candidate ippio 仍只是 static candidate | PASS |
| 7 | AMBIGUOUS_OUTPUT 被同步为 blocked，不是 solved | PASS |
| 8 | BLOCKED_MATURE_BACKEND_MISSING 被同步为 blocked，优先解释当前 validation blocker | PASS |
| 9 | cpp2_2f64e68d 不再是 inventory_only | PASS |
| 10 | cpp2_2f64e68d 不再进入 evaluation_queue | PASS |
| 11 | 生成的 status/overlay 不含绝对本地样本路径 | PASS |
| 12 | 没有运行 CPP2.exe 或任何真实 target | PASS |
| 13 | 没有运行 pair validator CLI/runtime validation | PASS |
| 14 | 没有运行 mature backend probe CLI | PASS |
| 15 | 没有运行 IDA/Ghidra/debugger/hook/emulator/CompareProbe/solver | PASS |
| 16 | 没有修改 .codex-skills、solve_reports 或无关代码 | PASS |
| 17 | codex_report_summary 与 decision_id/round_id 匹配 | PASS |
| 18 | pytest_result.txt 使用本 decision_id/report_id/round_id | PASS |
| 19 | lint-decision、pytest、lint-report、status 结果真实记录 | PASS (lint-report 因旧 report 不匹配而失败，已更新) |
| 20 | git status --short 和 git diff --name-status 只包含允许文件 | PASS |

## Implementation

1. `_build_runtime_blocked_overlay` 扫描 `artifact_index` 中 `kind` 为 `local_reverse_console_runtime_validation` 或 `local_reverse_console_pair_runtime_validation` 的 current artifact。
   - 接受 `validation_status` 为 `AMBIGUOUS_OUTPUT` / `VALIDATED_FAILURE` / `BLOCKED`
   - 要求 `solved=False`，且 `blocked_reason` 或 `failure_reason` 非空
   - blocked_reason 优先级：blocked_reason > failure_reason > validation_status
   - 不输出 known_candidate

2. `_build_mature_backend_blocked_overlay` 扫描 `kind` 为 `local_reverse_console_mature_backend_availability_probe` 的 current artifact。
   - 接受 `probe_status=BLOCKED_MATURE_BACKEND_MISSING`
   - 要求 `can_attempt_interactive_console_validation_next=False`、`solved=False`、`blocked_reason` 非空
   - 不输出 known_candidate

3. 合并优先级：
   - solved_map / runtime_validation_map（成功路径，保持现有行为）
   - blocked_map（constraint recovery blocked）
   - mature_backend_blocked_map（最高优先级 blocked overlay）
   - runtime_blocked_map
   - static_handoff_map
   - inventory_only

4. 对于 cpp2_2f64e68d，mature_backend_blocked 优先级高于 runtime_blocked，因此最终 blocked_reason 为 "Windows platform but no mature backend available (pywinpty/winpty/wexpect/ConPTY API)"。

## Tests

```
python -m py_compile reverse_agent/local_reverse_training_status.py  -> OK
python -m pytest -q tests/test_local_reverse_training_status.py     -> 41 passed
python -m pytest -q tests/test_project_state.py                       -> 158 passed
```

## Generated State Files

- `project_state/local_reverse_training_status.json`
  - `cpp2_2f64e68d.training_status = blocked`
  - `cpp2_2f64e68d.known_candidate = ""`
  - `status_summary: solved=2, blocked=5, needs_triage=0, inventory_only=22`
- `project_state/local_reverse_evaluation_queue.json`
  - `cpp2_2f64e68d` 不在队列中
  - queue_items = 19
- `training_materials/local_reverse/status_overlay.json`
  - 不含 `E:\reverse`、`D:\reverse`、`C:\reverse`、`F:\reverse`
- `project_state/local_reverse_cpp2_2f64e68d_training_status_sync.json`
  - `source_artifact_freshness = current`
  - `training_status = blocked`
  - `known_candidate = ""`
  - `candidate_was_static_only = true`
  - `runtime_validated = false`
  - `solved = false`
  - `executed_target = false`

## Problems / Uncertainty

无。所有测试通过，lint-decision 通过，状态文件验证正确。

## Next Suggested Task

本轮 training_dataset 状态同步已完成。建议下一轮：
1. 继续处理 evaluation_queue 中剩余的 inventory_only 样本
2. 或回到 samplereverse 主线，执行 bounded `compare_real_lhs_provenance_audit` rerun
