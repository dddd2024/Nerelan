```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_gate_baseline_lifecycle_clean_validation_rework_v1",
  "round_id": "round_20260615_gate_baseline_lifecycle_clean_validation_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

做一轮 clean validation rework，验证上一轮新增的 baseline lifecycle 机制在干净工作区下能正常通过。

本轮不继续推进任何样本分析，不修改 cpp1 artifact，不做 runtime validation。目标是消除上一轮自身触发 `baseline_lifecycle_violation` 后留下的状态不一致问题，并证明 gate 在正确顺序下可以 clean pass。

## 2. Current Evidence

当前执行权威是本 `project_state/decision_packet.md`，不是 `task_packet.json`。

上一轮 `decision_20260615_gate_preimplementation_baseline_lifecycle_rework_v1` 实现了 baseline lifecycle 检测，但当前结果不能接受：

- `codex_report_summary.status=FAILED`；
- `acceptance_recommendation=REWORK_REQUIRED`；
- `final_gate_result.gate_status=FAILED`；
- blocking reasons 包含 `baseline_lifecycle_violation` 和 `report_summary_fields_match_synthesis`；
- `pytest_result.txt` 中的 summary/命令输出与 gate artifacts 状态存在不一致；
- round archive 状态不干净。

上一轮代码修复方向可作为待验证实现，但上一轮 round 不能 clean accept。本轮任务是从干净工作区重新执行正确流程，验证 gate 行为，而不是把 failed gate 改写成 passed。

## 3. Do Not Do

不得修改样本分析 artifact。不得运行样本。不得调用 IDA/Ghidra/debugger/emulator/harness。不得把上一轮 failed gate 改写成 passed。不得只改报告文字后宣称修复。不得修改 `.codex-skills/`、`training_materials/` 或 `solve_reports/`。

## 4. Files To Inspect

必须按顺序读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

必须有界读取：

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `tests/test_project_gate_baseline_lifecycle.py`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`

## 5. Required Audit

启动时必须先执行并记录：

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`

如果 `git status --short` 不是干净状态，立即停止，报告 `BLOCKED_DIRTY_WORKTREE_BEFORE_CLEAN_VALIDATION`。不要继续跑 command-plan，也不要捕获新的 baseline。

如果工作区干净，则按正确顺序执行：

1. preflight / command-plan 捕获实现前 baseline；
2. 不做源码修改；
3. 运行测试；
4. 运行 doctor / lint-report / report-summary / final-check；
5. close-round。

必须验证：

- `baseline_lifecycle_violation=PASS`
- `startup_command_coverage=PASS`
- `files_changed_covers_substantive_changes=PASS`
- `report_summary_fields_match_synthesis=PASS`
- `final_gate_result.gate_status` 不是 FAILED
- `pytest_result.txt` 中命令输出与 gate artifacts 一致
- round archive 与 live report/pytest 一致

## 6. Implementation Scope

原则上不修改源码。

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_gate_baseline_lifecycle_clean_validation_rework_v1/*`

只有发现上一轮代码逻辑明显错误时，才允许小范围修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate_baseline_lifecycle.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

若修改源码，必须在 `files_changed` 中列出，并重新运行完整相关测试。

## 7. Tests

必须真实运行并记录到 `project_state/pytest_result.txt`：

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_gate_baseline_lifecycle.py -q`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_gate_baseline_lifecycle_clean_validation_rework_v1`

## 8. Stop Conditions

如果启动时工作区不干净，停止并报告 `BLOCKED_DIRTY_WORKTREE_BEFORE_CLEAN_VALIDATION`。

如果 final gate 仍 FAILED，报告 `REWORK_REQUIRED`，不能写 SUCCESS。

如果 pytest_result 与 gate artifact 状态不一致，报告 `REWORK_REQUIRED`。

如果 round archive 缺失或与 live 文件不一致，报告 `REWORK_REQUIRED`。
