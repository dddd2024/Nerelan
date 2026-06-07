```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260607_local_reverse_training_status_summary_sync_v1",
  "round_id": "round_20260607_local_reverse_training_status_summary_sync_v1",
  "based_on_decision_id": "decision_20260607_local_reverse_training_status_summary_sync_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/local_reverse_training_status.json",
    "project_state/local_reverse_training_status_summary_sync.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -m py_compile reverse_agent/project_state.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_project_state.py",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_training_status_summary_sync.json"
  ]
}
```

# Codex Execution Report

## Summary

本轮 **SUCCESS**。这是 `training_dataset` 主线的 aggregate summary sync，不是新样本求解。

本轮只修复 `project_state/local_reverse_training_status.json` 顶部汇总与样本列表/overlay/post-solve sync 之间的不一致：

```text
before top-level status_summary: solved=2, blocked=5, needs_triage=0, inventory_only=22
after top-level status_summary:  solved=3, blocked=4, needs_triage=0, inventory_only=22
computed samples[] summary:      sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22
```

没有运行任何样本，没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe。`cpp2_32f1713e` 保持为 next queue hint，没有作为当前执行任务。

## Evidence

- 当前 `decision_packet.md` 是本轮唯一执行权威，`decision_id=decision_20260607_local_reverse_training_status_summary_sync_v1`，`mainline=training_dataset`。
- Accepted validation artifact 存在，`validation_status=VALIDATED_SUCCESS`，`runtime_validated=true`，`known_candidate=10013`，`timeout_after_oracle_signal_captured=true`。
- `project_state/local_reverse_post_solve_state_sync.json` 确认 `executed_sample=false`、`ran_static_tools=false`、`ran_runtime_tools=false`、`updated_sample_id=cpp2_2f64e68d`、`known_candidate=10013`，并给出 `status_summary_after={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}`。
- `training_materials/local_reverse/status_overlay.json` 顶部 summary 为 `solved=3 / blocked=4 / needs_triage=0 / inventory_only=22`，且 `cpp2_2f64e68d` 为 `solved / 10013`。
- `project_state/local_reverse_training_status.json.samples[]` 重新计算结果为 `sample_count=29 / solved=3 / blocked=4 / needs_triage=0 / inventory_only=22`。
- `samples[]` 编辑前后哈希一致：`7ae94de85eba2d3ab091cf7a18b9c56326c1bffdecf8a1185287a5e5e98d4a1c`。

## Changes

- 更新 `project_state/local_reverse_training_status.json`：
  - `generated_at=2026-06-07T10:25:00Z`
  - `status_summary.solved=3`
  - `status_summary.blocked=4`
  - `status_summary.needs_triage=0`
  - `status_summary.inventory_only=22`
  - `status_summary.solved_count=3`
  - `status_summary.blocked_count=4`
  - `status_summary.inventory_only_count=22`
  - 添加低 token provenance：`summary_sync_round_id`、`summary_sync_decision_id`、`summary_source_status_overlay`、`summary_source_post_solve_sync`
- 生成 `project_state/local_reverse_training_status_summary_sync.json`：
  - `executed_sample=false`
  - `ran_static_tools=false`
  - `ran_runtime_tools=false`
  - `updated_sample_statuses=false`
  - `updated_known_candidates=false`
  - `before_summary={sample_count=29, solved=2, blocked=5, needs_triage=0, inventory_only=22}`
  - `after_summary={sample_count=29, solved=3, blocked=4, needs_triage=0, inventory_only=22}`
  - `recent_solved_sample_id=cpp2_2f64e68d`
  - `known_candidate=10013`
  - `next_queue_hint_sample_id=cpp2_32f1713e`
- 更新 `project_state/artifact_index.json`：
  - `latest_artifacts.local_reverse_training_status_summary_sync`
  - `latest_artifacts_v2.local_reverse_training_status_summary_sync`
  - compatibility `artifact_refs.local_reverse_training_status_summary_sync`
  - 真实 artifact metadata：`sha256=0170214ecc4c579ee95337b7cabb069366eea547798e5a016be501a20b380216`，`size_bytes=1271`

`negative_results.json` 未更新，因为本轮只同步训练状态汇总，不产生新的 reverse-solving negative result。

## Required Audit

1. 当前 decision_packet 是本轮唯一执行权威：PASS
2. 本轮主线为 training_dataset：PASS
3. 本轮只是 aggregate summary sync，不是新样本求解：PASS
4. 本轮没有运行任何样本：PASS
5. 本轮没有运行 IDA/Ghidra/debugger/hook/emulator/solver/bruteforce/runtime probe：PASS
6. accepted validation artifact 存在且 validation_status=VALIDATED_SUCCESS：PASS
7. cpp2_2f64e68d known_candidate=10013 且只作用于该样本：PASS
8. status_overlay summary 为 solved=3 blocked=4 inventory_only=22：PASS
9. local_reverse_training_status 样本列表中 cpp2_2f64e68d 已是 solved/10013：PASS
10. local_reverse_training_status 顶部 status_summary 已更新为 solved=3 blocked=4 needs_triage=0 inventory_only=22：PASS
11. legacy 兼容字段 solved_count=3 blocked_count=4 inventory_only_count=22：PASS
12. 未改变任何 samples[] 条目的 training_status/known_candidate/blocked_reason/classification：PASS
13. 已生成 project_state/local_reverse_training_status_summary_sync.json：PASS
14. 已更新 artifact_index 的 latest_artifacts 和 latest_artifacts_v2：PASS
15. negative_results 未更新理由已说明：PASS
16. task_packet.task 未变成 cpp2_32f1713e 执行任务：PASS
17. cpp2_32f1713e 仍只是 next_queue_hint，没有执行：PASS
18. 已补跑 py_compile reverse_agent/project_state.py：PASS
19. pytest_result.txt 使用本 decision_id/report_id/round_id：PASS
20. final lint-report 为写入本轮 report 后的最终成功记录：PASS
21. git diff --check、git status --short、git diff --name-status 均有真实输出记录：PASS
22. 没有提交 .venv、site-packages、wheel、DLL、EXE、sample binary、solve_reports 或 .codex-skills：PASS

## Commands and Results

1. `.venv\Scripts\python -m py_compile reverse_agent/project_state.py`
   - exit_code: 0
   - output: no output

2. `.venv\Scripts\python -m pytest -q tests/test_project_state.py`
   - exit_code: 0
   - output:

```text
........................................................................ [ 45%]
........................................................................ [ 91%]
..............                                                           [100%]
158 passed in 22.59s
```

3. `.venv\Scripts\python -m reverse_agent.project_state lint-decision --state-dir project_state`
   - exit_code: 0
   - output:

```text
lint-decision: OK
decision_id: decision_20260607_local_reverse_training_status_summary_sync_v1
decision_status: APPROVED
mainline: training_dataset
skill_profiles: ['reverse-agent-iteration@v2']
based_on_state_build_id: state_20260602_053948_4e3984041cd7
based_on_state_digest: 4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
current_state_build_id: state_20260602_053948_4e3984041cd7
current_state_digest: 4e3984041cd78e5a412e28a53fa3441957ea87f43f62a9688c3e80ca4413678c
execution_scope: decision_packet_controls_current_round
active_decision_packet: project_state/decision_packet.md
```

4. `git diff --check`
   - exit_code: 0
   - output:

```text
warning: in the working copy of 'project_state/artifact_index.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/codex_execution_report.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/local_reverse_training_status.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/pytest_result.txt', LF will be replaced by CRLF the next time Git touches it
```

5. content assertions
   - exit_code: 0
   - output:

```text
content assertions: PASS
samples_hash: 7ae94de85eba2d3ab091cf7a18b9c56326c1bffdecf8a1185287a5e5e98d4a1c
summary: {'sample_count': 29, 'solved': 3, 'blocked': 4, 'needs_triage': 0, 'inventory_only': 22}
```

6. `.venv\Scripts\python -m reverse_agent.project_state lint-report --state-dir project_state`
   - exit_code: 0
   - output:

```text
lint-report: OK
warning: report round not archived yet
report_id: report_20260607_local_reverse_training_status_summary_sync_v1
report_status: SUCCESS
acceptance_recommendation: ACCEPTED
based_on_decision_id: decision_20260607_local_reverse_training_status_summary_sync_v1
decision_report_id_match: True
report_decision_round_id_match: True
pytest_result_matches_report: True
pytest_result_tests_cover_report: True
```

7. `.venv\Scripts\python -m reverse_agent.project_state status --state-dir project_state`
   - exit_code: 0
   - output:

```text
decision_id: decision_20260607_local_reverse_training_status_summary_sync_v1
report_id: report_20260607_local_reverse_training_status_summary_sync_v1
pytest_result_decision_id: decision_20260607_local_reverse_training_status_summary_sync_v1
decision_report_id_match: True
decision_state_digest_match: True
decision_consumed_by_report: True
decision_execution_state: CONSUMED_BY_SUCCESS_REPORT
decision_ready_for_execution: False
report_decision_round_id_match: True
pytest_result_matches_report: True
```

8. `git status --short`
   - exit_code: 0
   - output:

```text
 M project_state/artifact_index.json
 M project_state/codex_execution_report.md
 M project_state/local_reverse_training_status.json
 M project_state/pytest_result.txt
?? project_state/local_reverse_training_status_summary_sync.json
```

9. `git diff --name-status`
   - exit_code: 0
   - output:

```text
M	project_state/artifact_index.json
M	project_state/codex_execution_report.md
M	project_state/local_reverse_training_status.json
M	project_state/pytest_result.txt
warning: in the working copy of 'project_state/artifact_index.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/codex_execution_report.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/local_reverse_training_status.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'project_state/pytest_result.txt', LF will be replaced by CRLF the next time Git touches it
```
