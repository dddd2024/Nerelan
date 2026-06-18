```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_gate_report_hygiene_and_build_scope_v1",
  "round_id": "round_20260618_gate_report_hygiene_and_build_scope_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

清理上一轮 `startup_command_coverage_logic_fix_v1` 的两个非阻断限制项，并生成一致、可审计的最终报告。

上一轮核心 gate 逻辑已经通过：`final-check=PASSED`，`archive_status=archived`，`report_status=SUCCESS`，`acceptance_recommendation=ACCEPTED`。剩余限制是：

1. `codex_execution_report.md` 正文仍写着 close-round “To be run”，但实际 close-round 已运行并归档成功。
2. `final_gate_result.json` 仍有 `build_output_scope_unverified` WARN，因为 round delta 中有 build-generated state files，但 pytest_result/report 未清楚记录 state build 命令。

本轮目标：

- 修正 report 正文中 close-round 状态描述，使其与 final gate 和 archive evidence 一致。
- 对 build-generated project_state 文件作出明确处理：若它们确实由 `project_state build` 生成，则重新运行并记录 build 命令；若不是本轮必要产物，则不要把它们列为本轮 substantive change。
- 保持上一轮 startup coverage 源码修复和回归测试，不重写三档 profile 逻辑。
- 最终 `report-summary` 与 `final-check` 不得有 FAIL；若仍有 WARN，必须在报告中明确说明是否为 non-blocking。

## 2. Current Evidence

主线是 `engineering_branch`。

上一轮有效成果：

- `reverse_agent/project_gate.py` 已修复 startup command coverage 与 command-plan coverage 的循环冲突。
- `tests/test_project_gate.py` 已补回归测试。
- pytest 记录显示 `789 passed`。
- `final_gate_result.json` 显示 `gate_status=PASSED`、archived report/pytest 与 live 一致、blocking_reasons 为空。

当前限制：

- report 正文中 close-round 状态描述滞后。
- `build_output_scope` 为 WARN。

`task_packet.json` 仍是旧 `samplereverse` reverse-solving 建议，本轮仍以 `project_state/decision_packet.md` 为执行权威。

`negative_results.json` 中 reverse-solving 禁止方向继续有效；本轮不触碰样本求解、旧 solver、budget expansion、compare_semantics_agree=false candidate 或完整 solve_reports。

本轮不进入 reverse_solving/tool_integration/training_dataset，不运行 IDA/Ghidra/debugger/emulator/solver/harness。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行样本、IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe。

不要调用旧 `sample_solver`，不要提交完整 `solve_reports/`，不要修改 `.codex-skills/`。

不要新增 `medium` profile；当前 profile 名称仍是 `standard`。

不要改动三档 profile 语义，不要降低 full profile closeout/archive/manifest 严格性。

不要重写上一轮 startup coverage 修复，除非发现明确 bounded bug。

不要只改正文而不重新运行 report-summary/final-check。

不要在 close-round 后修改 live report/pytest_result；如果必须修改，必须重新运行 gate，并在允许时重新 close-round。

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

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/round_delta_summary.json`
6. `project_state/gates/round_close_snapshot.json`
7. `project_state/rounds/round_20260618_startup_command_coverage_logic_fix_v1/round_manifest.json`
8. `reverse_agent/project_gate.py`
9. `tests/test_project_gate.py`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

修改前必须确认：工作目录是 `F:\reverse-agent`；`Test-Path F:\reverse-agent` 为 `True`；`git rev-parse --show-toplevel` 指向本仓库；启动 `git status --short` 已记录；decision_meta 为 APPROVED；mainline 为 engineering_branch；`reverse-agent-iteration@v2` 是 active skill。

必须说明：

1. 上一轮 final gate 是否已经 PASSED。
2. close-round 是否已经成功创建 archive。
3. report 正文中哪些 close-round 描述需要修正。
4. `build_output_scope_unverified` 的具体原因。
5. 本轮是否运行了 `python -m reverse_agent.project_state build`，以及是否写入 pytest_result。
6. 本轮最终 report-summary/final-check 状态。

## 6. Implementation Scope

优先只修改 project_state/report artifacts：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260618_gate_report_hygiene_and_build_scope_v1/*`
- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`

仅当发现 gate 对 build-output WARN 的判断存在明确 bounded bug 时，才允许小范围修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

要求：

1. report 正文不得再写 close-round “To be run” 一类过期状态。
2. 若 build-generated state files 出现在 round delta，pytest_result 必须记录对应 build command 或报告必须解释其 non-blocking 依据。
3. report summary 的 `status` / `acceptance_recommendation` 必须与 final gate 一致。
4. 不得把 stale archive 当成本轮 current evidence。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

1. `Set-Location F:\reverse-agent`
2. `Get-Location`
3. `Test-Path F:\reverse-agent`
4. `git rev-parse --show-toplevel`
5. `git status --short`
6. `python -m reverse_agent.project_state build`
7. `python -m pytest tests/test_project_gate.py tests/test_project_state.py -q`
8. `python -m reverse_agent.project_gate preflight --state-dir project_state`
9. `python -m reverse_agent.project_gate gate-profile --state-dir project_state`
10. `python -m reverse_agent.project_gate gate-profile --state-dir project_state --json`
11. `python -m reverse_agent.project_gate command-plan --state-dir project_state`
12. `python -m reverse_agent.project_gate command-plan --state-dir project_state --json`
13. `python -m reverse_agent.project_gate report-summary --state-dir project_state`
14. `python -m reverse_agent.project_gate final-check --state-dir project_state`

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行 close-round 使用 round id `round_20260618_gate_report_hygiene_and_build_scope_v1`，随后再次运行 final-check。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：目录或仓库不正确；decision_meta 不合法；skill inactive；需要修改允许范围外文件；需要运行样本或逆向工具；需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG；修改会削弱 full profile closeout/archive/manifest 要求；report 仍包含与 close-round 事实冲突的描述；report-summary 或 final-check 最终出现 FAIL；报告声称 closeout 成功但 archived report/pytest 与 live 不一致。
