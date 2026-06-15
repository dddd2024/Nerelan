```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260615_decision_immutability_scope_guard_rework_v1",
  "round_id": "round_20260615_decision_immutability_scope_guard_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# REWORK DECISION_PACKET

## 1. Goal

修复 `round_20260615_decision_immutability_and_build_output_scope_guard_v1` 的失败点，不新增大功能。

目标只包括：

1. 确保 baseline 在任何源码/测试修改前捕获；
2. 将 `active-execution-view` 命令注册为 command-plan 已知命令类型；
3. 修复 `report-summary / final-check / close-round` 失败；
4. 保持上一轮已实现的 decision immutability、build output scope、verified CLI coverage 检查；
5. 重新跑完整 gate 并成功 close-round。

## 2. Current Evidence

上一轮 `codex_execution_report.md` 为 `FAILED / REWORK_REQUIRED`。

上一轮 final gate 的 blocking reasons 是：

- `baseline_lifecycle_guard`
- `baseline_capture_order`
- `command_plan_ids_match`
- `pytest_result_exit_codes_match_command_plan`
- `report_summary_fields_match_synthesis`

`pytest` 已经通过 543 个测试，但 `report-summary`、`final-check`、`close-round` 均 exit 1。

上一轮已完成但未通过 closeout 的部分：

- `BUILD_OUTPUT_WHITELIST`
- `_decision_immutability_check()`
- `_build_output_scope_check()`
- `_verified_cli_coverage_check()`
- `preflight()` 中的 `decision_not_dirty_in_baseline`
- 相关单元测试

这些实现方向可以保留，但必须修复 gate 失败和执行顺序问题。

## 3. Do Not Do

不要推进逆向样本求解。

不要运行 sample、runtime probe、debugger、hook、emulator、sidecar、solver search。

不要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。

不要修改 solver、strategy、transform、IDA/Ghidra/debugger/harness。

不要修改 `.codex-skills/`。

不要修改 live `project_state/decision_packet.md` 来补 allowlist。

不要运行 live `project_state build`。

不要把 `task_packet.task` 当执行权威。

不要把 gate 失败的 round 写成 `SUCCESS`。

## 4. Files To Inspect

必须读取：

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/command_plan.json`
10. `.codex-skills/registry.json`

重点检查：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- 必要时 `reverse_agent/project_state.py`
- 必要时 `tests/test_project_state.py`

## 5. Required Audit

执行前必须先完成启动检查，且在任何修改前记录：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
```

如果此时 `git status --short` 已显示 `reverse_agent/project_gate.py` 或 `tests/test_project_gate.py` dirty，必须先判断它们是否是上一轮未提交改动；不得直接继续修改并伪装成新 baseline。

如果 live `project_state/decision_packet.md` dirty，立即停止并报告 `BLOCKED`。

## 6. Implementation Scope

允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

必要时允许修改：

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

允许生成或更新：

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/*.json`
- `project_state/rounds/round_20260615_decision_immutability_scope_guard_rework_v1/*`

只读，不得修改：

- live `project_state/decision_packet.md`，除本文件由 GPT 预先上传外，Codex 执行期间不得修改；
- `.codex-skills/`
- `solve_reports/`
- `PROJECT_PROGRESS_LOG.txt`
- solver / strategy / transform / probe / IDA / Ghidra / debugger 相关模块。

具体要求：

1. 在 command-plan 识别逻辑中把 `python -m reverse_agent.project_state active-execution-view --state-dir project_state --json` 归类为已知 command，不能再是 `phase: unknown / kind: unknown`。
2. `command-plan --json` 的 `plan_status` 必须为 `PASSED`。
3. 不允许通过修改 live decision 添加 `Allowed Inherited Dirty Baseline Files` 来压掉 baseline 错误。
4. 修复或规避 late baseline capture：baseline 必须在实现修改前捕获。
5. `report-summary`、`final-check`、`close-round` 必须 exit 0。
6. `codex_report_summary.status` 只有在上述 gate 全部通过后才能写 `SUCCESS`。
7. 若 gate 仍失败，report 必须保持 `FAILED` 或 `BLOCKED`，不得写 `SUCCESS`。
8. 保留上一轮新增的 decision immutability、build output scope、verified CLI coverage 检查，不要回退这些规则。

## 7. Tests

必须记录命令、stdout/stderr、exit code 到 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state active-execution-view --state-dir project_state --json
python -m pytest tests/test_project_state.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260615_decision_immutability_scope_guard_rework_v1
```

必须新增或确认测试覆盖：

1. `active-execution-view` command 在 command-plan 中不是 unknown；
2. `command-plan --json` 对该命令返回 `PASSED`；
3. late baseline capture 仍会失败；
4. clean startup + valid modifications 不触发 baseline_lifecycle_guard；
5. live decision 修改仍会失败；
6. archive decision copy 仍允许；
7. build output scope 检查不回退；
8. verified CLI coverage 检查不回退。

## 8. Stop Conditions

如果需要修改 live `project_state/decision_packet.md` 才能通过，停止并报告 `REWORK_REQUIRED`。

如果启动时 live `project_state/decision_packet.md` dirty，停止并报告 `BLOCKED`。

如果仍然出现 `baseline_lifecycle_guard` 或 `baseline_capture_order` FAIL，停止并报告 `REWORK_REQUIRED`。

如果 `command-plan` 仍是 WARN，停止并报告 `REWORK_REQUIRED`。

如果 `report-summary / final-check / close-round` 任何一个 exit 1，不得写 `SUCCESS`。

如果 `pytest_result.txt` 缺失、测试未真实运行、report/decision id 不匹配，不得提交 `SUCCESS` 报告。
