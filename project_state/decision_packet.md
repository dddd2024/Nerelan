```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_command_output_and_artifact_summary_completeness_v1",
  "round_id": "round_20260611_rework_command_output_and_artifact_summary_completeness_v1",
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

只补齐上一轮验收材料，不再扩大实现范围：

1. 把 required commands 的实际输出完整写入 `project_state/pytest_result.txt`。
2. 修正 `codex_execution_report.md` 的 `files_changed`、`generated_artifacts`、`verified_artifacts`，覆盖本轮实际改动、round archive 和删除的多余 archive。
3. 确认 `lint-report/status/doctor/doctor --json` 的 post-archive 输出真实记录。

## 2. Current Evidence

- header/body contradiction 检测已经实现。
- pytest 已通过：`181 passed` 和 `240 passed`。
- 当前阻塞点不是代码功能，而是验收证据不完整。
- `pytest_result.txt` 只记录 pytest 输出，没有记录 required command exact outputs。
- `codex_execution_report.md.files_changed/generated_artifacts` 没有覆盖 round archive 和删除的 extra archive。
- 本轮仍是 `training_dataset`，不得进入 reverse solving 或 tool integration。

## 3. Do Not Do

- 不改 solver、harness、IDA/Ghidra/debugger/runtime 相关代码。
- 不运行样本二进制。
- 不读取完整 `solve_reports/`。
- 不修改 `.codex-skills/`。
- 不新增额外 round_id。
- 不用手写 PASS 掩盖失败。
- 不改训练集 inventory/status，除非命令实际失败且必须修复。

## 4. Files To Inspect

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_rework_training_integrity_command_and_pytest_body_guard_v1/round_manifest.json`
- `project_state/rounds/round_20260611_rework_command_output_and_artifact_summary_completeness_v1/*`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `.codex-skills/registry.json`

## 5. Required Audit

Codex must:

1. Confirm repository root is `F:\reverse-agent`.
2. Confirm this decision is active.
3. Run every required command and paste exact stdout/stderr or concise but complete command result into `pytest_result.txt`.
4. Ensure `pytest_result_summary.tests_ran` exactly covers report `tests_ran`.
5. Ensure report `files_changed` includes:
   - live report/pytest files;
   - current round archive files;
   - any removed stale extra archive files, or explicitly explain if already removed before this round.
6. Ensure `generated_artifacts` includes current round archive files.
7. If using `verified_artifacts`, list post-archive doctor/status evidence there.
8. Run final `git status --short` and record it.
9. Report `SUCCESS/ACCEPTED` only if all required commands pass and final git status has no unexplained files.

## 6. Implementation Scope

Allowed:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_command_output_and_artifact_summary_completeness_v1/*`

Allowed only if a command genuinely fails:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Disallowed:

- `.codex-skills/`
- solver/runtime/debugger/IDA/Ghidra/harness changes
- sample binaries
- full `solve_reports/`
- training inventory regeneration

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m pytest tests/test_local_reverse_inventory.py tests/test_local_reverse_training_status.py tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_command_output_and_artifact_summary_completeness_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- Any command fails.
- Exact command output cannot be recorded.
- Final git status has unexplained files.
- Report summary cannot truthfully include all changed/generated/verified artifacts.
- Fix requires running samples, solvers, debuggers, runtime probes, IDA, or Ghidra.
