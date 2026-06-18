```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_build_output_scope_recording_fix_v1",
  "round_id": "round_20260618_build_output_scope_recording_fix_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

清理上一轮 `training_coverage_matrix_gap_report_v1` 的唯一 gate 限制项：`build_output_scope_unverified`。

上一轮训练集覆盖矩阵和能力缺口报告可以接受，但 `final_gate_result.json` 仍显示 `PASSED_WITH_LIMITATIONS`，原因是 `project_state/artifact_index.json` 被识别为 build-generated state file，而当前 round delta 没有记录对应 build command。

本轮目标：

1. 让 build-generated project_state 文件的来源可审计，尤其是 `project_state/artifact_index.json`。
2. 如果该文件确实由 `python -m reverse_agent.project_state build` 生成，必须在 `project_state/pytest_result.txt` 中记录该命令、stdout/stderr 和 exit code。
3. 如果 command-plan/final-check 当前不能正确覆盖或识别 project_state build 命令，则小范围修复 gate 逻辑并补回归测试。
4. 不修改训练覆盖矩阵语义，不继续扩展训练集报告内容。
5. 最终 `report-summary` 和 `final-check` 不得有 FAIL；理想目标是消除 `build_output_scope_unverified` WARN，使 final-check 达到 PASSED。

本轮不是逆向解题，不进入样本求解，不运行 IDA/Ghidra/debugger/emulator/runtime probe。

## 2. Current Evidence

主线是 `engineering_branch`。

上一轮 `training_coverage_matrix_gap_report_v1` 已经完成并被审计为 `ACCEPTED_WITH_LIMITATIONS`：

- `pytest` 通过，记录为 `846 passed`。
- `local_reverse_training_status --json` 为只读模式，返回 `sample_count=65`、`writes_files=false`。
- 已生成训练集 inventory refresh、coverage matrix、solver/tool capability map、gap report。
- `final_gate_result.json` 中 archived report 与 live report 一致，archived pytest_result 与 live pytest_result 一致，blocking_reasons 为空。
- 当前唯一限制是 `build_output_scope_unverified` WARN，具体文件为 `project_state/artifact_index.json`，原因是 build-generated state file 出现在 round delta，但未记录 build command。

`task_packet.json` 仍保留旧 `samplereverse` sample_state/reverse-solving 内容；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`current_state.json` 仍偏旧 sample_state，不应作为训练覆盖或 build-output 当前证据。

`artifact_index.json` 多数历史 reverse-solving artifact 仍为 missing；这些只能作外部状态通知，不能作为当前证据。

`negative_results.json` 禁止旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 必须为 active。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要把一次性样本 candidate、flag、本地绝对路径或 runtime metric 写进 skill。

不要改动训练覆盖矩阵的题型结论，除非发现上一轮产物有结构性错误。

不要通过删除 `project_state/artifact_index.json` 来规避 build_output_scope；应解释或记录其生成来源。

不要降低 full/standard profile 的 closeout/archive/manifest 严格性。

不要在 close-round 后再修改 live report 或 pytest_result；如果必须修改，必须重新运行 report-summary/final-check，并在允许时重新 close-round。

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
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/round_close_snapshot.json`
9. `project_state/artifact_index.json`
10. `project_state/codex_execution_report.md`
11. `project_state/pytest_result.txt`
12. `project_state/rounds/round_20260618_training_coverage_matrix_gap_report_v1/round_manifest.json`

不要读取完整 `PROJECT_PROGRESS_LOG.txt` 或完整 `solve_reports/`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录。
5. `decision_meta.status=APPROVED`。
6. `mainline=engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. 本轮是 build-output scope / gate-report hygiene 工作，不是训练样本求解。

必须审计并记录：

1. 上一轮 `build_output_scope_unverified` 的具体触发逻辑。
2. `project_state/artifact_index.json` 是否由 `python -m reverse_agent.project_state build` 或其它命令生成。
3. command-plan 是否应该包含 project_state build 命令。
4. final-check 当前如何判断 build-generated state files 是否有 recorded build command。
5. 是否需要修改 `reverse_agent/project_gate.py`；如需修改，必须说明 bounded bug 和测试覆盖。
6. close-round 前后的 report/pytest/archive 是否一致。

## 6. Implementation Scope

优先只修改 project_state/gate/report artifacts：

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
- `project_state/rounds/round_20260618_build_output_scope_recording_fix_v1/*`
- `project_state/artifact_index.json` only if regenerated by an explicitly recorded build command

仅当 gate 逻辑无法正确识别已记录 build command，才允许小范围修改：

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
- `tests/test_project_state.py`

建议实现方式：

1. 先复现上一轮 WARN：确认 `build_output_scope` 指向 `project_state/artifact_index.json`。
2. 运行并记录 `python -m reverse_agent.project_state build`，确保 `pytest_result.txt` 中有完整 command block 和 exit code。
3. 重新运行 gate profile、command-plan、report-summary、final-check。
4. 如果 final-check 仍认为 build command 未记录，则修复 build command detection 逻辑，增加回归测试：
   - round delta 包含 `project_state/artifact_index.json` 且 pytest_result 有 `python -m reverse_agent.project_state build` command block => build_output_scope PASS。
   - round delta 包含 build-generated state file 但 pytest_result 缺少 build command => build_output_scope WARN 或 FAIL，按现有策略保持严格。
5. 如果最终 closeout_allowed=true 且 final-check 无 FAIL，运行 close-round，且 close-round 后不再修改 live report/pytest_result。

不得修改 solver、harness、tool runner、训练覆盖矩阵主体逻辑或样本 metadata 语义。

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

如果本轮修改了 `reverse_agent/project_gate.py` 或 tests，还必须运行：

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_build_output_scope_recording_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- `build_output_scope` 最终状态；
- build command 是否记录；
- 是否仍有 WARN；
- 如果仍有 WARN，为什么 non-blocking；
- 是否运行 close-round；
- archived report/pytest 是否与 live 一致。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `engineering_branch`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 通过删除 build-generated artifact 或弱化 gate 来消除 WARN。
9. 修改会削弱 full/standard closeout/archive/manifest 要求。
10. `report-summary` 或 `final-check` 最终出现 FAIL。
11. 报告声称 build-output 已修复，但 pytest_result 没有对应 build command 或 final_gate_result 仍无证据。
12. close-round 后 live report/pytest 与 archive 不一致。
