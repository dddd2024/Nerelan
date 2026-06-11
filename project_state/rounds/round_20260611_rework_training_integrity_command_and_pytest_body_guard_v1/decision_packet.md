```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_training_integrity_command_and_pytest_body_guard_v1",
  "round_id": "round_20260611_rework_training_integrity_command_and_pytest_body_guard_v1",
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

返工上一轮未完成的审计完整性问题，只处理三件事：

1. 实现并测试 `pytest_result_summary.status` 与 pytest 正文失败输出之间的一致性校验。
2. 补齐本轮 required command evidence：failing target、full pytest、lint-report、status、doctor、doctor --json、archive、post-archive checks、final git status。
3. 清理或解释多余 round archive 与 `files_changed/generated_artifacts` 不完整问题。

## 2. Current Evidence

- 上轮 pytest 已从 `1 failed` 修到 `236 passed`。
- 但 `tests_ran` 只记录了一个 pytest 命令，没有记录 decision 要求的完整命令链。
- `validate_pytest_result_for_report()` 仍未解析 pytest 正文失败行。
- 当前 round archive 存在，但 report 未列入 generated_artifacts。
- 出现额外 archive `round_20260611_fix_test_failures_and_add_mainline_coverage_v1`，不属于当前 decision scope，必须解释或移除。
- 本轮仍是 `training_dataset`，不得进入逆向解题、工具接入或样本运行。

## 3. Do Not Do

- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、IDA、Ghidra、hook、sidecar。
- 不读取完整 `solve_reports/`。
- 不修改 `.codex-skills/`。
- 不用手写 `PASSED` 掩盖失败。
- 不删除测试来制造通过。
- 不创建额外 round_id。
- 不修改 harness 行为。

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_rework_training_inventory_test_and_report_integrity_v1/round_manifest.json`
- `project_state/rounds/round_20260611_fix_test_failures_and_add_mainline_coverage_v1/round_manifest.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_local_reverse_training_status.py`
- `.codex-skills/registry.json`

## 5. Required Audit

Codex must:

1. Confirm repository root is `F:\reverse-agent`.
2. Confirm active decision is this packet.
3. Confirm skill profiles are active.
4. Add a failing test proving that a `pytest_result_summary.status: PASSED` header with body text like `1 failed, 231 passed` makes `validate_pytest_result_for_report()`, `lint-report`, or `doctor` fail.
5. Implement minimal body parsing in `validate_pytest_result_for_report()` or an equivalent project_state validation path.
6. Preserve existing valid `236 passed` behavior.
7. Run and record all required commands, not only pytest.
8. Ensure `codex_execution_report.md.files_changed` and `generated_artifacts` include all actual current-round files.
9. Explain or remove the extra `round_20260611_fix_test_failures_and_add_mainline_coverage_v1` archive if it is not part of the active decision.
10. Archive only the current round.
11. Final report must not use `SUCCESS/ACCEPTED` unless all required commands pass and all scope artifacts are accounted for.

## 6. Implementation Scope

Allowed:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_training_integrity_command_and_pytest_body_guard_v1/*`

Allowed only for cleanup if justified:

- remove or explain `project_state/rounds/round_20260611_fix_test_failures_and_add_mainline_coverage_v1/*`

Disallowed:

- `.codex-skills/`
- sample binaries
- full `solve_reports/`
- solver/runtime/debugger/IDA/Ghidra/harness behavior changes
- training inventory regeneration unless directly required by tests

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_training_integrity_command_and_pytest_body_guard_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- Any pytest command fails.
- The header/body contradiction cannot be detected.
- `lint-report` or `doctor` fails.
- Final git status has unexplained files.
- Extra round archives cannot be explained.
- Fix requires running samples, solvers, debuggers, runtime probes, IDA, or Ghidra.
