```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_tool_integration_freshness_policy_rework_v1",
  "round_id": "round_20260619_tool_integration_freshness_policy_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复 `project_gate` 的 status/freshness policy：对于 `tool_integration` 主线下的 schema/helper/synthetic-test-only 轮次，如果没有 claim sample artifacts 为 current evidence、没有运行 sample/IDA/Ghidra/runtime/harness，历史 sample artifacts 的 `50 missing, 0 stale artifacts` 不应导致 `status_policy_valid=FAIL`。应降级为 limitation 或 warning。

本轮只修 gate/status policy 和对应测试，不继续扩展 static triage type-evidence helper，不运行任何逆向样本或工具。

## 2. Current Evidence

主线是 `engineering_branch`，因为本轮修改目标是 project gate/status policy，不是继续推进 `tool_integration` 实现，也不是 reverse-solving 或 training dataset 批量回填。

上一轮 `decision_20260619_static_triage_type_evidence_schema_v1` 的实现和测试已经完成，但最终 gate 没有通过。当前 `project_state/codex_execution_report.md` 记录：

- `report_id=codex_report_20260619_static_triage_type_evidence_schema_v1`
- `round_id=round_20260619_static_triage_type_evidence_schema_v1`
- `based_on_decision_id=decision_20260619_static_triage_type_evidence_schema_v1`
- `status=FAILED`
- `acceptance_recommendation=REWORK_REQUIRED`

上一轮完成内容包括：

- 复用 `reverse_agent/local_reverse_single_sample_static_triage.py`，新增纯 adapter-side type evidence normalization。
- 给 success artifact 和 blocked artifact 都加入 `triage.type_evidence`。
- 新增 stable profiles：`string_comparison`、`xor`、`shift_affine`、`bit_operations`、`lookup_table`、`rc4`、`des`、`hash_md5_sha`、`simple_antidebug`、`mixed_unknown`。
- 新增 schema/report artifacts 和 synthetic tests。
- 没有运行 IDA/Ghidra/sample/runtime/solver/harness/debugger/emulator/sidecar/GUI。

当前 `project_state/pytest_result.txt` 显示上一轮启动路径正确，`git status --short` 起始为空，pytest 通过：`869 passed`。`local_reverse_training_status --json` 显示 `writes_files=false`。

当前 `project_state/gates/final_gate_result.json` 显示：

- `gate_status=FAILED`
- `decision_id=decision_20260619_static_triage_type_evidence_schema_v1`
- `report_id=codex_report_20260619_static_triage_type_evidence_schema_v1`
- `round_id=round_20260619_static_triage_type_evidence_schema_v1`
- `status_policy_valid=FAIL`
- `lint_errors=["50 missing, 0 stale artifacts"]`
- `report_status=FAILED`
- `blocking_reasons=["status_policy_valid: status policy found blocking issues"]`
- `recommended_next_action=fix_gate_failures_before_archive_or_handoff`

当前 `project_state/gates/report_summary_synthesis.json` 已经 `synthesis_status=PASSED`，且 synthesized summary 与 live report 一致为 `status=FAILED` / `acceptance_recommendation=REWORK_REQUIRED`。因此当前核心阻塞不是 summary mismatch，而是 status/freshness policy。

`task_packet.json` 仍是旧 sample-state / `collect_missing_evidence` 建议；它不是本轮执行权威。本轮执行以 `project_state/decision_packet.md` 为准。

`current_state.json` 仍指向 `samplereverse`，best candidates 为空，多个 artifact 字段为空；这不能作为当前样本求解证据。

`artifact_index.json` 中大量 sample/runtime artifact 是 `freshness=missing`。本轮不得把这些 missing/stale/unknown artifact 当作 current evidence，也不得用它们作为 reverse-solving 依据。

`negative_results.json` 禁止方向继续有效：

- 不回到旧 `sample_solver` blind search。
- 不做 only beam/budget/topN expansion。
- 不把 `compare_semantics_agree=false` candidate 作为 primary frontier。
- 不提交完整 `solve_reports/`。
- 不重复 exact2 basin/H1-H3 fixed contrast/current 5-candidate transform trace consistency audit。

已有相关能力检查：

- project gate 已存在：`reverse_agent/project_gate.py`。
- project state tests 已存在：`tests/test_project_gate.py`、`tests/test_project_state.py`。
- IDA/Ghidra/debugger/tool runner/solver/harness 能力已存在但本轮不运行、不修改。

## 3. Do Not Do

不要运行 reverse-solving。

不要运行任何本地样本可执行文件。

不要运行 IDA、Ghidra、OllyDbg、x64dbg、debugger hook、emulator、runtime probe、sidecar、sample runner、solver、harness 或 GUI/frontend workflow。

不要改 `reverse_agent/local_reverse_single_sample_static_triage.py`，不要继续扩展 type-evidence helper。

不要修改 IDA script、Ghidra runner、debugger runner、tool runner、solver、harness、GUI/frontend、inventory builder、training status builder 或 sample metadata builder。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要修改 `.codex-skills/`。

不要把 missing/stale artifact 当 current evidence。

不要为了让 gate 通过而整体关闭 freshness/status policy。

不要放宽 `reverse_solving` 主线对 current runtime/static artifacts 的严格要求。

不要忽略 report/decision/pytest_result mismatch。

不要把上一轮 FAILED report 直接改成 SUCCESS；必须先修 gate policy、跑测试和 gate，再由本轮 report 记录真实结果。

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

重点读取：

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/gate_profile_plan.json`
7. `project_state/gates/command_plan.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/rounds/round_20260619_static_triage_type_evidence_schema_v1/round_manifest.json`
10. `project_state/local_reverse_static_triage_type_evidence_schema_report.md`
11. `project_state/local_reverse_static_triage_type_evidence_schema.json`

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

## 5. Required Audit

执行前必须确认：

1. 当前工作目录是 `F:\reverse-agent`。
2. `Test-Path F:\reverse-agent` 为 `True`。
3. `git rev-parse --show-toplevel` 指向当前仓库。
4. 启动 `git status --short` 已记录；若已有 dirty files，必须记录 baseline 并排除继承脏改动。
5. `decision_meta.status=APPROVED`。
6. `mainline=engineering_branch`。
7. `reverse-agent-iteration@v2` 是 active skill。
8. `task_packet.json` 不是执行权威。
9. 上一轮失败来自 `status_policy_valid`，核心错误是 `50 missing, 0 stale artifacts` 被当作 blocking issue。
10. 上一轮 `tool_integration` report 没有声明 current sample artifact evidence。
11. 上一轮没有运行 sample/IDA/Ghidra/runtime/harness/solver/debugger/emulator。
12. 本轮修改不会让 `reverse_solving` 缺失 current runtime/static artifacts 时通过。
13. 本轮修改不会忽略 report/decision/pytest mismatch。

必须审计并记录：

1. project gate 当前 status policy 如何读取 doctor/lint/freshness 结果。
2. `status_policy_valid` 如何把 `50 missing, 0 stale artifacts` 转成 blocking issue。
3. 是否能区分 historical sample artifact missing 与当前 report claimed current evidence。
4. 是否能按 mainline 区分：`reverse_solving` strict、`tool_integration` schema/helper-only limitation、`training_dataset` metadata/schema-only limitation。
5. tests 是否覆盖不会误放宽 reverse_solving。
6. report 是否明确这是 gate/status-policy repair，不是样本求解或工具执行。

## 6. Implementation Scope

Allowed paths:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`
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
- `project_state/rounds/round_20260619_tool_integration_freshness_policy_rework_v1/*`

Implementation requirements:

1. 在 `reverse_agent/project_gate.py` 中定位 `status_policy_valid` 对 doctor/lint/artifact freshness 的判断。
2. 增加 mainline-aware status policy，不要整体绕过 freshness 检查。
3. 对 `reverse_solving`：保持 strict。缺失 required current artifacts、claim missing/stale as current evidence、runtime/static artifact mismatch 等仍必须 FAIL。
4. 对 `tool_integration`：当本轮是 schema/helper/unit-test-only，且 report 没有声明 current sample evidence、没有运行 sample/IDA/Ghidra/runtime/harness 时，historical sample artifacts 的 `missing` 可降级为 limitation/warning。
5. 对 `training_dataset`：metadata/schema-only 轮次可将 historical sample artifact missing 降级为 limitation/warning，但如果 claim current sample evidence 仍必须 FAIL。
6. 不得让 report/decision/pytest_result mismatch 通过。
7. 不得让 stale artifact 被 claim 为 current evidence 的情况通过。
8. 添加或调整 `tests/test_project_gate.py`，至少覆盖：
   - `tool_integration` schema/helper-only + historical sample missing artifacts => `PASSED_WITH_LIMITATIONS` 或非 blocking limitation。
   - `reverse_solving` + missing required current artifacts => FAIL。
   - `tool_integration` 但 report claim missing/stale artifact as current evidence => FAIL。
   - report/decision/pytest mismatch 仍 FAIL。
9. 不修改上一轮 type-evidence helper、schema、tests，除非测试 fixture 需要读取它们；优先不碰。
10. 重新生成本轮 gate artifacts、pytest_result 和 codex_execution_report。
11. 若 final-check 无 FAIL 且 closeout_allowed=true，close-round 并确认 archive。

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

如果 `final-check` 无 FAIL 且 `gate_profile_plan.closeout_allowed=true`，运行：

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_tool_integration_freshness_policy_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

报告必须列出：

- 修复的 gate/status policy 位置；
- mainline-aware policy 的行为差异；
- reverse_solving strict 行为保持的测试证据；
- tool_integration schema/helper-only missing historical artifacts 降级为 limitation 的测试证据；
- report/decision/pytest mismatch 仍 FAIL 的测试证据；
- 没有运行 sample/IDA/Ghidra/runtime/solver/harness；
- gate profile、report-summary、final-check、close-round 状态。

## 8. Stop Conditions

立即停止并报告 `REWORK_REQUIRED` 或 `BLOCKED`，如果：

1. 目录或仓库不正确。
2. `decision_meta` 缺失或不是 `APPROVED`。
3. `mainline` 不是 `engineering_branch`。
4. `reverse-agent-iteration@v2` 不是 active。
5. 需要运行样本、solver、harness、IDA、Ghidra、debugger、emulator、runtime probe、sidecar 或 GUI workflow。
6. 需要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。
7. 需要修改上一轮 type-evidence helper 或其他非 gate 文件来绕过 gate。
8. 修改会放宽 `reverse_solving` 的 current artifact freshness 约束。
9. 修改会允许 report/decision/pytest_result mismatch 通过。
10. 修改会允许 stale/missing artifact 被 claim 为 current evidence。
11. 无法区分 historical sample missing artifacts 与当前 claimed evidence。
12. 测试需要真实 IDA/Ghidra/sample/runtime 才能通过。
13. `pytest_result.txt` 没有真实测试记录。
14. report/decision/pytest_result 的 decision_id 或 round_id 不匹配。
15. `report-summary` 或 `final-check` 仍出现 FAIL。
