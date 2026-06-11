```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260611_rework_command_plan_exact_json_output_v1",
  "round_id": "round_20260611_rework_command_plan_exact_json_output_v1",
  "based_on_state_build_id": "state_20260610_131714_88c14099a13a",
  "based_on_state_digest": "88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2",
    "samplereverse-frontier@v2"
  ]
}
```

# DECISION_PACKET

## 1. Goal

修复 `command-plan --json` 与 `pytest_result.txt` 的精确输出一致性问题。

本轮只修 report / pytest_result / 必要测试，不新增 `close-round`，不执行 command plan，不推进样本求解。

必须完成：

1. 确认 `python -m reverse_agent.project_gate command-plan --state-dir project_state --json` 实际 stdout 是否输出完整 JSON。
2. 若实现已经输出完整 JSON，只修 `pytest_result.txt`，重新记录真实 stdout。
3. 若实现会输出摘要 JSON，则修实现，使 `--json` 输出完整 `commands` 数组。
4. `pytest_result.txt` 必须保存完整 stdout，不能用 `"17 entries; full artifact saved ..."` 代替。
5. 重新 archive 当前 round。
6. `final-check` 必须通过。

## 2. Current Evidence

- `command_plan.json` 本身完整，包含 17 条 command entries。
- `pytest_result.txt` 中 `command-plan --json` 输出被摘要化，不是完整 JSON。
- `report` 当前声明 SUCCESS，但该测试记录不满足 decision 的 exact stdout/stderr 要求。
- 本轮不涉及样本求解、IDA、solver、runtime、training status。

## 3. Do Not Do

- 不实现自动 `close-round`。
- 不执行 command plan 中的命令。
- 不运行样本二进制。
- 不运行 solver、candidate search、runtime probe、debugger、hook、emulator、sidecar。
- 不修改 `.codex-skills/`。
- 不读取完整 `solve_reports/`。
- 不修改训练集状态、IDA runner、solver/runtime/debugger 模块。
- 不用摘要替代真实 stdout。

## 4. Files To Inspect

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `project_state/gates/command_plan.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/decision_packet.md`

## 5. Required Audit

Codex must:

1. Confirm active decision is this packet.
2. Confirm mainline is `engineering_branch`.
3. Run `project_gate preflight` before modification.
4. Inspect `project_gate command-plan --json` implementation.
5. Confirm whether CLI emits full `commands` list.
6. Ensure `pytest_result.txt` records exact stdout/stderr for:
   ```bash
   python -m reverse_agent.project_gate command-plan --state-dir project_state --json
   ```
7. Do not abbreviate large JSON outputs.
8. Ensure report `tests_ran` matches `pytest_result_summary.tests_ran`.
9. Ensure archived `pytest_result.txt` matches live `pytest_result.txt`.

## 6. Implementation Scope

Allowed:

- `reverse_agent/project_gate.py` only if actual CLI output is summarized
- `tests/test_project_gate.py` only if test needs to assert full JSON output
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/rounds/round_20260611_rework_command_plan_exact_json_output_v1/*`

Disallowed:

- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- sample binaries
- `reverse_agent/local_reverse_training_status.py`
- `reverse_agent/local_reverse_single_sample_static_triage.py`
- solver modules
- IDA/Ghidra/debugger/runtime/probe modules
- training inventory/status/queue files

## 7. Tests

Run and record exact outputs:

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_command_plan_exact_json_output_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state --json
git status --short
```

`pytest_result.txt` 必须使用正式 `pytest_result_summary`，并记录所有命令 stdout/stderr。`command-plan --json` 的 stdout 必须包含完整 `commands` 数组。

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- `command-plan --json` cannot emit complete command plan JSON.
- `pytest_result.txt` cannot record complete stdout.
- `final-check` fails after archive.
- Any scope-out file appears in final git status.
- Fixing this requires implementing `close-round` or touching sample-solving/tooling modules.
