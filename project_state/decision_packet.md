```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_restore_gate_report_hygiene_v1",
  "round_id": "round_20260618_restore_gate_report_hygiene_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

恢复并执行 gate report hygiene 修复轮。

当前默认分支没有以 `decision_20260618_gate_report_hygiene_and_build_scope_v1` 为执行权威，live report 仍然基于 `decision_20260618_startup_command_coverage_logic_fix_v1`。本轮必须重新建立当前 decision，并清理上一轮残留的 report hygiene 问题。

目标行为：

1. live `project_state/decision_packet.md` 必须是本轮 `decision_20260618_restore_gate_report_hygiene_v1`。
2. `codex_execution_report.md.based_on_decision_id` 必须匹配本轮 decision。
3. 修正 report 正文中过期的 `close-round: To be run` 描述。
4. 处理或解释 `build_output_scope_unverified` WARN。
5. 重新运行 report-summary 和 final-check。
6. 最终不得有 FAIL。
7. 不改动已通过的 startup coverage 源码逻辑，除非发现新的 bounded bug。

## 2. Current Evidence

上一轮 `startup_command_coverage_logic_fix_v1` 已经通过核心 gate：

- pytest 通过。
- final-check PASSED。
- startup_command_coverage PASS。
- command_plan_covers_report_tests PASS。
- archive/live 一致。

但 hygiene 目标未完成：

- live decision 仍是 `startup_command_coverage_logic_fix_v1`。
- report 正文仍含 close-round 过期描述。
- final gate 仍有 `build_output_scope_unverified` WARN。

`task_packet.json` 仍是旧 reverse-solving 建议，不是当前执行权威。

本轮主线是 `engineering_branch`，不是 reverse-solving。

`negative_results.json` 中 reverse-solving 禁止方向继续有效；本轮不触碰旧 sample_solver、budget-only expansion、compare_semantics_agree=false candidate frontier 或完整 solve_reports 提交。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 是 active skill。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行样本、IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe。

不要调用旧 `sample_solver`。

不要提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要新增 `medium` profile；当前 profile 名仍是 `standard`。

不要降低 full profile closeout/archive/manifest 严格性。

不要重写 startup coverage 修复逻辑，除非有明确 bounded bug。

不要只改 report 正文而不重新运行 report-summary/final-check。

不要在 close-round 后再修改 live report/pytest_result；如果必须修改，必须重新 close-round。

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

必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录。
5. decision_meta 为 APPROVED。
6. mainline 为 `engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮 report 的 `based_on_decision_id` 匹配本 decision。

必须解释：

1. 为什么上一轮 startup coverage 修复可以保留。
2. 为什么当前 report 正文仍不干净。
3. `build_output_scope_unverified` 的原因。
4. 本轮是否运行 `python -m reverse_agent.project_state build`。
5. 本轮最终 final-check 是否无 FAIL。
6. 如果 close-round 运行，archive/live 是否一致。

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
- `project_state/rounds/round_20260618_restore_gate_report_hygiene_v1/*`

允许在运行 state build 后更新：

- `project_state/artifact_index.json`
- `project_state/current_state.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`

只有发现明确 bounded bug 时，才允许修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

要求：

1. 删除或修正 report 正文中的 `close-round: To be run` 过期描述。
2. 若 build-generated state files 出现在 round delta，必须在 pytest_result 中记录 build command，或在 report 中明确说明 non-blocking 依据。
3. report-summary 必须 PASSED。
4. final-check 不得有 FAIL。
5. 若 final-check 无 FAIL 且 closeout_allowed=true，再 close-round。
6. close-round 后不得再改 live report/pytest_result；如果改了，必须重新 close-round。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_state build

python -m pytest tests/test_project_gate.py tests/test_project_state.py -q

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_restore_gate_report_hygiene_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. decision_meta 不合法。
3. skill inactive。
4. report 的 based_on_decision_id 不匹配本 decision。
5. 需要修改允许范围外文件。
6. 需要运行样本或逆向工具。
7. 需要读取完整 solve_reports 或 PROJECT_PROGRESS_LOG。
8. report 仍包含 close-round 事实冲突描述。
9. `report-summary` 或 `final-check` 最终出现 FAIL。
10. close-round 后又修改 live report/pytest_result 且未重新 close-round。
11. 报告声称 closeout 成功但 archived report/pytest 与 live 不一致。
