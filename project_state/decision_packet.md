```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_affine_blocked_archive_consistency_v1",
  "round_id": "round_20260611_rework_affine_blocked_archive_consistency_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "training_dataset",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

只修复上一轮 `BLOCKED` 报告的归档一致性问题，不再修改 triage 逻辑，不再推进样本分析。

必须完成：

1. 保持 `STATIC_TOOL_NO_OUTPUT` 的 `BLOCKED` 结论。
2. 修正 live `codex_execution_report.md` 的 `files_changed` 和 `generated_artifacts`，覆盖实际 Git diff 和 round archive 文件。
3. 重新归档当前 round，确保 archived `codex_execution_report.md` 与 live report 内容一致。
4. 重新运行 post-archive lint/status/doctor，并完整记录到 `pytest_result.txt`。
5. final git status 必须与 report summary 可解释一致。

## 2. Current Evidence

- `affine_8cfebe03` 已经是 `needs_triage`，有 `STATIC_TOOL_NO_OUTPUT` evidence。
- `artifact_index.json` 已登记 `local_reverse_affine_8cfebe03_static_triage` 为 current tool-blocked evidence。
- live report 为 `BLOCKED`，但 archived report 是中间态，只含 6 条 tests_ran。
- actual diff 新增了 current round archive 文件，但 live report 未列入 `files_changed/generated_artifacts`。
- 本轮不需要继续修 static triage 逻辑。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、runtime probe、debugger、hook、emulator、sidecar。
- 不修改 `.codex-skills/`。
- 不读取完整 `solve_reports/`。
- 不继续改 `local_reverse_training_status.py`，除非 post-check 证明现有文件损坏。
- 不改 `local_reverse_affine_8cfebe03_static_triage.json`。
- 不把 BLOCKED 改成 SUCCESS。
- 不生成 candidate、known_candidate 或 solved 状态。

## 4. Files To Inspect

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1/round_manifest.json`
- `project_state/local_reverse_training_status.json`
- `project_state/artifact_index.json`

## 5. Required Audit

Codex must:

1. Confirm active decision is this packet.
2. Confirm previous `affine_8cfebe03` status remains `needs_triage`, not solved.
3. Confirm current artifact remains tool-blocked evidence.
4. Update report summary so `files_changed` includes all actual modified/added files, including round archive files.
5. Update `generated_artifacts` so it includes live generated metadata and all archive files created by archive-round.
6. Re-run archive after final report/pytest_result are written.
7. Confirm archived report matches live report.
8. Run post-archive lint/status/doctor.
9. Record exact command outputs in formal `pytest_result_summary`.

## 6. Implementation Scope

Allowed:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_rework_affine_blocked_archive_consistency_v1/*`

Allowed only if archive tool requires it:

- `project_state/rounds/round_20260611_rework_affine_static_triage_blocked_report_and_overlay_gate_v1/*`

Disallowed:

- `reverse_agent/local_reverse_training_status.py`
- `tests/test_local_reverse_training_status.py`
- `project_state/artifact_index.json`
- `project_state/local_reverse_training_status.json`
- `project_state/local_reverse_evaluation_queue.json`
- `training_materials/local_reverse/status_overlay.json`
- sample binaries
- solver/runtime/debugger files

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_affine_blocked_archive_consistency_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

## 8. Stop Conditions

Stop and report `BLOCKED` if:

- archived report still differs from live report.
- `files_changed` cannot be reconciled with Git diff.
- `generated_artifacts` cannot be reconciled with archive contents.
- post-archive doctor/lint cannot parse report or pytest_result.
- fixing the issue would require changing sample analysis logic or rerunning static triage.
