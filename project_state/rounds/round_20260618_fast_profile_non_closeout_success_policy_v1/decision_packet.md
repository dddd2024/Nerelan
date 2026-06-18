```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260618_fast_profile_non_closeout_success_policy_v1",
  "round_id": "round_20260618_fast_profile_non_closeout_success_policy_v1",
  "based_on_state_build_id": "state_20260618_114539_14d4ec94f06b",
  "based_on_state_digest": "14d4ec94f06bab113eb55fdf774e82b449b2851672e927f2b0df7a6052a95cc2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 fast profile 下 `closeout_allowed=false` 与 final-check/report status 之间的策略不一致。

上一轮 `build_output_scope_recording_fix_v1` 已经完成核心目标：`build_output_scope` 由 WARN 变为 PASS，`python -m reverse_agent.project_state build` 已记录并 exit 0。但是本轮 final-check 仍为 WARN，report 仍为 `PARTIAL / REWORK_REQUIRED`，原因不是当前任务失败，而是 fast profile 本来不允许 close-round，却仍把缺少 round manifest、archive/live 不一致、report round not archived 作为 WARN，导致 artifact-only cleanup 无法产生干净成功态。

本轮目标：

1. 明确 fast profile 的成功语义：当 `closeout_allowed=false` 且 profile 为 fast 时，不应要求 close-round，也不应因为没有 round archive 而把当前轮标为 PARTIAL/REWORK_REQUIRED。
2. 保持严格性：如果 fast profile 报告声称生成了 archive、或者 generated_artifacts 包含 round archive 文件、或者 close-round 被错误执行/记录，仍必须 FAIL/WARN。
3. 修复 final-check/report-summary/status-policy 逻辑，使 artifact/report-only fast profile 在所有必需命令通过、无 blocking reasons、无 archive claims 时可以达到干净成功态。
4. 补回归测试，覆盖 fast non-closeout clean success 与错误 archive claim 两类情况。
5. 不改变 standard/full profile 的 closeout/archive/manifest 严格性。

本轮不是逆向解题，不进入样本求解，不运行 IDA/Ghidra/debugger/emulator/runtime probe。

## 2. Current Evidence

主线是 `engineering_branch`。

上一轮事实：

- `decision_20260618_build_output_scope_recording_fix_v1` 合法，目标是清理 `build_output_scope_unverified`。
- `python -m reverse_agent.project_state build` 已在 pytest_result 中记录并 exit 0。
- `pytest` 通过，记录为 `789 passed`。
- final-check 中 `build_output_scope` 已为 PASS，build-generated files 包括 `project_state/artifact_index.json`、`current_state.json`、`model_gate.json`、`task_packet.json`，且 `build_command_recorded=true`、`build_exit_zero=true`。
- gate-profile 自动选择 fast，`closeout_allowed=false`，原因是 artifact-only cleanup。
- 当前剩余 WARN 为 round manifest missing、archived report differs from live、archived pytest differs from live、status_policy_valid 中 report_status PARTIAL / report round not archived。
- fast_profile_closeout_consistency 已 PASS，并确认 fast profile correctly omits close-round，validation success does not imply closeout。

因此下一步不是继续改 report 文本，也不是运行 close-round，而是修正 gate 对 fast non-closeout 的成功态表达。

`task_packet.json` 仍保留旧 `samplereverse` sample_state/reverse-solving 内容；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`negative_results.json` 禁止旧 sample_solver blind search、budget-only expansion、compare_semantics_agree=false candidate frontier、提交完整 solve_reports。本轮不触碰这些方向。

`.codex-skills/registry.json` 中 `reverse-agent-iteration@v2` 必须为 active。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner 或 GUI/frontend workflow。

不要调用旧 `sample_solver`，不要扩大 beam/topN/budget/timeout。

不要读取或提交完整 `solve_reports/`。

不要修改 `.codex-skills/`。

不要通过强行 close-round 规避 fast profile 的策略问题。

不要降低 standard/full profile 的 closeout/archive/manifest 严格性。

不要让 fast profile 在存在 archive claims、round archive generated_artifacts、或 close-round 命令记录时静默通过。

不要修改训练覆盖矩阵、solver、harness、tool runner 或样本 metadata 语义。

不要在 close-round 后再修改 live report 或 pytest_result；本轮预期 fast profile 不应 close-round。

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
6. `project_state/gates/gate_profile_plan.json`
7. `project_state/gates/command_plan.json`
8. `project_state/pytest_result.txt`
9. `project_state/codex_execution_report.md`
10. `project_state/gates/round_delta_summary.json`
11. `project_state/gates/round_close_snapshot.json` if present

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
8. 本轮是 fast profile gate status policy 修复，不是训练样本求解。

必须审计并记录：

1. final-check 中 round manifest / archived report / archived pytest checks 的 fast profile 分支逻辑。
2. status-policy 如何把 `PARTIAL / REWORK_REQUIRED` 派生出来。
3. report-summary synthesis 如何根据 final_gate_result 派生 report status 与 acceptance recommendation。
4. fast profile closeout_allowed=false 时，哪些 archive 相关检查应被标记为 PASS/SKIP/non-blocking，而不是 WARN。
5. 哪些情况下 fast profile 仍必须失败：存在 archive claims、generated_artifacts 声称 round archive、close-round 命令被记录、或 closeout_allowed 与 profile 不一致。

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
- `project_state/gates/round_close_snapshot.json` only if generated by current gate logic

建议实现方向：

1. 在 final-check 中识别 `profile=fast` 且 `closeout_allowed=false` 且无 archive claims 的状态。
2. 对该状态下的 `round_manifest_present`、`archived_report_matches_live_report`、`archived_pytest_result_matches_live_pytest_result` 采用 non-required / SKIP / PASS-with-detail 的语义，不作为 WARN 推高 gate_status。
3. 调整 status-policy 和 report-summary 派生规则，使 clean fast non-closeout round 可以输出 `SUCCESS / ACCEPTED` 或等价的干净成功态。
4. 添加回归测试：
   - fast profile artifact-only scope、无 archive claims、所有 required commands 通过 => final-check clean success，无 archive WARN。
   - fast profile 若 generated_artifacts 声称 round archive 但未 close-round => FAIL/WARN。
   - fast profile 若 tests_ran 记录 close-round 但 closeout_allowed=false => FAIL/WARN。
   - standard/full profile archive/manifest 仍保持严格。
5. 不修改训练 coverage matrix、solver/harness/tool runner 主逻辑。

## 7. Tests

必须运行并写入 `project_state/pytest_result.txt`：

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_project_gate.py tests/test_project_state.py -q

python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

如果 gate-profile 仍选择 fast 且 `closeout_allowed=false`，不得运行 close-round。报告必须说明 fast non-closeout clean success 的最终状态，以及 archive/manifest checks 为什么不是 WARN。

如果 gate-profile 因源码/test 修改选择 standard 或 full 且 `closeout_allowed=true`，则运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260618_fast_profile_non_closeout_success_policy_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- profile 与 closeout_allowed；
- archive/manifest checks 最终状态；
- status_policy_valid 最终状态；
- report-summary 派生出的 `status` / `acceptance_recommendation`；
- fast profile 下是否有 archive claims；
- 是否有 final-check FAIL/WARN。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 APPROVED。
3. `mainline` 不是 `engineering_branch`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、debugger、IDA/Ghidra、emulator、runtime probe 或 sidecar。
6. 需要读取完整 `solve_reports/` 或 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改允许范围之外的文件。
8. 修改会削弱 standard/full closeout/archive/manifest 要求。
9. fast profile 存在 archive claims 或 close-round 命令时仍被判为 clean success。
10. `report-summary` 或 `final-check` 最终出现 FAIL。
11. 报告声称 fast non-closeout policy 已修复，但没有覆盖错误 archive claim/close-round 误用的回归测试。
