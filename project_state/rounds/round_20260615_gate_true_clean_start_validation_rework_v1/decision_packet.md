```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_gate_true_clean_start_validation_rework_v1",
  "round_id": "round_20260615_gate_true_clean_start_validation_rework_v1",
  "based_on_state_build_id": "state_20260613_054156_2729a02c7407",
  "based_on_state_digest": "2729a02c7407808c057a8a3f3e1d414797d660957dbe80b6c0780ffe6ec6bac9",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

做一轮真正的 clean-start gate validation。

本轮目标不是继续改 gate 逻辑，而是验证：在 `git status --short` 完全干净的工作区中，baseline lifecycle、startup command coverage、files_changed coverage、round archive 一整套流程能稳定通过。

## 2. Current Evidence

当前执行权威是本 `project_state/decision_packet.md`，不是 `task_packet.json`。

上一轮 final gate 最终为 `PASSED_WITH_LIMITATIONS`，关键 gate 检查通过，但启动阶段 `git status --short` 已经显示 gate 文件 dirty。这违反了上一轮 decision 的 stop condition，所以不能接受为 clean validation。

上一轮可作为工程实现线索，但本轮必须重新从真正干净的工作区开始验证。

## 3. Do Not Do

不得修改样本分析 artifact。不得运行样本。不得调用 IDA/Ghidra/debugger/emulator/harness。不得在 dirty worktree 下继续执行 clean validation。不得把 dirty-start round 写成 clean pass。不得修改 `.codex-skills/`、`training_materials/` 或 `solve_reports/`。

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
- `tests/test_project_gate.py`
- `tests/test_project_gate_baseline_lifecycle.py`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`

## 5. Required Audit

启动后第一组命令必须是：

- `Set-Location F:\reverse-agent`
- `Get-Location`
- `Test-Path F:\reverse-agent`
- `git rev-parse --show-toplevel`
- `git status --short`

如果 `git status --short` 有任何输出，立即停止，写入 `codex_execution_report.md`：

- `status=BLOCKED`
- `acceptance_recommendation=REWORK_REQUIRED`
- `reason=BLOCKED_DIRTY_WORKTREE_BEFORE_CLEAN_VALIDATION`

如果工作区干净，再执行：

- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
- `python -m pytest tests/test_project_gate.py tests/test_project_state.py tests/test_project_gate_baseline_lifecycle.py -q`
- `python -m reverse_agent.project_state doctor --state-dir project_state`
- `python -m reverse_agent.project_state lint-report --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`
- `python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_gate_true_clean_start_validation_rework_v1`

## 6. Implementation Scope

默认不修改源码。

允许更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/rounds/round_20260615_gate_true_clean_start_validation_rework_v1/*`

只有发现 command-plan stdout 与 live command_plan 不一致的根因在代码层，才允许小范围修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_gate_baseline_lifecycle.py`

若修改源码，必须在 `files_changed` 中列出，并重新运行完整相关测试。

## 7. Tests

必须验证：

- 启动 `git status --short` 无输出；
- `baseline_lifecycle_violation=PASS`；
- `startup_command_coverage=PASS`；
- `files_changed_covers_substantive_changes=PASS`；
- `report_summary_fields_match_synthesis=PASS`；
- `command-plan --json` stdout 与 live `project_state/gates/command_plan.json` 关键命令一致；
- close-round 后 archived report / pytest 与 live 文件一致。

## 8. Stop Conditions

如果启动 worktree 不干净，停止并报告 `BLOCKED_DIRTY_WORKTREE_BEFORE_CLEAN_VALIDATION`。

如果 final gate FAILED，停止并报告 `REWORK_REQUIRED`。

如果 pytest_result 与 gate artifact 不一致，停止并报告 `REWORK_REQUIRED`。

如果 archive 缺失或不一致，停止并报告 `REWORK_REQUIRED`。
