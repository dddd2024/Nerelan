```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_startup_command_coverage_logic_fix_v1",
  "round_id": "round_20260618_startup_command_coverage_logic_fix_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `startup_command_coverage` 与 `command_plan_covers_report_tests` 之间的循环冲突。

当前剩余阻塞是：`startup_command_coverage` FAIL。问题表现为：

- 将 `Set-Location`、`Get-Location`、`Test-Path`、`git rev-parse`、`git status` 等启动命令加入 `tests_ran` 时，`command_plan_covers_report_tests` 会因为 command-plan 不包含这些启动命令而 FAIL。
- 从 `tests_ran` 移除启动命令时，`startup_command_coverage` 会 FAIL。

目标行为：startup coverage 应从 `pytest_result.txt` 的实际 command blocks 判断；startup 命令不应被强制放入 `codex_report_summary.tests_ran` 才算覆盖；startup 命令也不应导致 `command_plan_covers_report_tests` 失败。保持启动路径、启动顺序和 exit code 校验严格，不降低 full profile closeout/archive/manifest 要求。最终 `report-summary` 和 `final-check` 不得有 FAIL。

## 2. Current Evidence

主线是 `engineering_branch`。

当前 gate/report 状态显示：preflight PASSED，gate-profile PASSED，profile 为 fast，`closeout_allowed=false`，command-plan PASSED，report-summary PASSED，report/pytest_result 字段一致，但 final-check 剩余 `startup_command_coverage` FAIL。

这说明继续 artifact-only 修改 report 或 pytest_result 会在两个检查间来回冲突；需要授权修改 `reverse_agent/project_gate.py` 的 coverage 判断逻辑，并补回归测试。

`task_packet.json` 仍是旧 `samplereverse` reverse-solving 建议，本轮不以它为执行权威。

`negative_results.json` 中 reverse-solving 禁止方向继续有效，本轮不触碰样本求解、旧 solver、budget expansion、compare_semantics_agree=false candidate 或完整 solve_reports。

本轮不进入 reverse_solving/tool_integration/training_dataset，不运行 IDA/Ghidra/debugger/emulator/solver/harness。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行样本、IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe。

不要调用旧 `sample_solver`，不要提交完整 `solve_reports/`，不要修改 `.codex-skills/`。

不要新增 `medium` profile；当前 profile 名称仍是 `standard`。

不要降低 full profile closeout/archive/manifest 严格性。

不要通过只编辑 report 或 pytest_result 掩盖 `startup_command_coverage`。

不要删除 startup 校验；不要让缺失启动 command blocks 的 pytest_result 通过 final-check。

不要修改本 decision 文件；如果启动时本 decision 文件 dirty，立即停止。

## 4. Files To Inspect

默认先读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

重点检查：

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/command_plan.json`
7. `project_state/pytest_result.txt`
8. `project_state/codex_execution_report.md`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

修改前必须确认：工作目录是 `F:\reverse-agent`；`Test-Path F:\reverse-agent` 为 `True`；`git rev-parse --show-toplevel` 指向本仓库；启动 `git status --short` 已记录；decision_meta 为 APPROVED；mainline 为 engineering_branch；`reverse-agent-iteration@v2` 是 active skill。

必须定位：

1. `startup_command_coverage` check 的实现。
2. `command_plan_covers_report_tests` 如何读取 `tests_ran`。
3. `pytest_result.txt` command block parser 如何识别 startup command blocks。
4. 为什么 startup 命令加入 `tests_ran` 会导致 command-plan coverage 失败。
5. 为什么 startup 命令从 `tests_ran` 移除会导致 startup coverage 失败。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`

建议实现方向：

1. 修改 `startup_command_coverage`，以 `pytest_result.txt` 中实际 command blocks 为主要证据，不要求 startup commands 出现在 `codex_report_summary.tests_ran`。
2. 修改或补充 `command_plan_covers_report_tests`，将 startup commands 视为特殊类别，不因 startup commands 不在 command-plan 中而 FAIL；普通 test/gate command 仍必须被 command-plan 覆盖。
3. 添加回归测试：`tests_ran` 不含 startup commands 但 pytest_result 有完整 startup command blocks 时 PASS；`tests_ran` 含 startup commands 但 command-plan 不含 startup commands 时不触发 command_plan coverage FAIL；pytest_result 缺少任一启动命令时 FAIL；启动命令顺序错误时仍 FAIL 或由现有 order check 捕获；普通测试命令缺失 command-plan 覆盖时仍 FAIL。
4. 不修改 profile 三档语义，不削弱 full closeout/archive/manifest 逻辑。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

1. `Set-Location F:\reverse-agent`
2. `Get-Location`
3. `Test-Path F:\reverse-agent`
4. `git rev-parse --show-toplevel`
5. `git status --short`
6. `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`
7. `python -m reverse_agent.project_gate preflight --state-dir project_state`
8. `python -m reverse_agent.project_gate gate-profile --state-dir project_state`
9. `python -m reverse_agent.project_gate gate-profile --state-dir project_state --json`
10. `python -m reverse_agent.project_gate command-plan --state-dir project_state`
11. `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
12. `python -m reverse_agent.project_gate report-summary --state-dir project_state`
13. `python -m reverse_agent.project_gate final-check --state-dir project_state`

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行 close-round 使用 round id `round_20260618_startup_command_coverage_logic_fix_v1`，随后再次运行 final-check。如果 profile 是 fast 且 `closeout_allowed=false`，不得强行 close-round；报告应说明 fast non-closeout。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：目录或仓库不正确；decision_meta 不合法；skill inactive；需要修改允许范围外文件；需要运行样本或逆向工具；需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG；修改会让缺失 startup command blocks 的 pytest_result 通过；修改会削弱 full profile closeout/archive/manifest 要求；`report-summary` 或 `final-check` 最终仍有 FAIL；报告声称 coverage 修复完成但没有覆盖循环冲突的回归测试。
