```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_affine_current_static_bridge_report_fix_v1",
  "round_id": "round_20260619_affine_current_static_bridge_report_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

修复上一轮 `affine_current_static_bridge_validation` 的报告与 provenance artifact 一致性问题。不得重新求解，不得生成 candidate/flag，不得运行 runtime。

本轮不是重新做 static triage，也不是 reverse_solving。本轮只修复当前轮 project_state 报告一致性，使 live report、provenance report、bridge result、solver dispatch plan、pytest_result 和 final gate 互相一致。

必须修复：

1. `project_state/codex_execution_report.md` 中错误的 `executed_sample=true`，必须改为与 `project_state/local_reverse_affine_8cfebe03_current_static_triage.json` 一致的 `executed_sample=false`。
2. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json` 和 `.md` 中错误的 `evidence_counts`，必须从 `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json` 重新计算。
3. `codex_report_summary.generated_artifacts` 必须补全上一轮核心产物：current static triage、bridge result、solver dispatch plan、provenance report json/md、artifact_index。
4. `project_state/pytest_result.txt` summary 不得同时声明整体 `status=PASSED` 又保留未解释的 failed command。若 doctor 允许 exit 1，必须明确标注为 expected/non-blocking；否则重新运行到一致状态。
5. 重新运行 gate，确保 final-check 不再显示 `report_status=PARTIAL` 或 `report_acceptance_recommendation=NEEDS_REVIEW`。

成功标准：

- current static triage artifact 仍保持 `tool_status=success`、`executed_sample=false`、`static_only=true`、`runtime_validated=false`、`source_run=round_20260619_affine_current_static_bridge_validation_v1`。
- bridge result 仍显示 evidence families：StaticInputEvidence、StaticCompareEvidence、StaticTransformHintEvidence、StaticAntiDebugEvidence。
- provenance report 的 evidence_counts 与 bridge result 一致。
- solver dispatch plan 仍不 claim solve-ready。
- final gate 对本修复轮给出可审计接受状态；若仍有 warning，必须是 historical/backlog artifact 或明确 non-blocking 的 gate policy warning。

## 2. Current Evidence

上一轮 `decision_20260619_affine_current_static_bridge_validation_v1` 已执行并生成了 current static artifact，但审计结论是 `REWORK_REQUIRED`。

已经确认的有效事实：

- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json` 显示：
  - `sample_id=affine_8cfebe03`
  - `tool_status=success`
  - `executed_sample=false`
  - `static_only=true`
  - `runtime_validated=false`
  - `source_tool=IDA`
  - `source_run=round_20260619_affine_current_static_bridge_validation_v1`
- `project_state/artifact_index.json` 已登记 `local_reverse_affine_8cfebe03_static_triage`，freshness 为 `current`，path 指向 `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`，source_run 为上一轮 round。
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json` 显示 4 条 evidence：
  - `StaticInputEvidence`
  - `StaticCompareEvidence`
  - `StaticTransformHintEvidence`
  - `StaticAntiDebugEvidence`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json` 显示：
  - `readiness=needs_current_static_provenance`
  - `recommended_solver_profiles=["string_compare", "anti_debug_precondition"]`
  - `required_missing_evidence=["transform_constant_evidence"]`

必须修复的错误事实：

- `project_state/codex_execution_report.md` prose 错误声称 `executed_sample=true`，与 actual artifact 矛盾。
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json` 的 `evidence_counts` 全部为 0，和 bridge result 矛盾。
- `project_state/codex_execution_report.md` 的 `generated_artifacts` 没有覆盖核心 current static/bridge/provenance artifacts。
- `project_state/gates/final_gate_result.json` 显示 `report_status=PARTIAL`、`report_acceptance_recommendation=NEEDS_REVIEW`，不能接受。

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议，不是本轮执行权威。

当前 `negative_results.json` 继续有效：不要回到旧 `sample_solver` blind search，不要只扩 beam/budget/topN，不要把 `compare_semantics_agree=false` candidates 当 primary frontier，不要提交完整 `solve_reports/`。

## 3. Do Not Do

不要重新运行 reverse-solving。

不要执行任何本地样本二进制。

不要重新运行 runtime probe、debugger、emulator、harness、GUI/frontend。

不要生成 candidate、flag、密码、key 或最终答案。

不要修改 solver 搜索逻辑、beam/topN/budget、runtime validation、harness、debugger、GUI/frontend。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制或提交本地样本二进制。

不要修改 `.codex-skills/`。

不要把历史 affine artifact 当 current evidence。

不要再次运行 IDA/static triage，除非当前 artifact 文件缺失或损坏；若必须重跑，必须说明理由并保持 sample execution 禁止。

不要把这轮扩展成 affine 求解；本轮只修报告和 provenance 统计一致性。

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

必须读取并交叉核对：

1. `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
2. `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
3. `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
4. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
5. `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/command_plan.json`

Do not read complete heavy-history directories.

## 5. Required Audit

Before modifying files, audit and record:

1. Worktree is `F:\reverse-agent` and repository root is correct.
2. Startup `git status --short` is recorded. If dirty files exist, record baseline and do not overwrite unrelated work.
3. `decision_meta.status=APPROVED`.
4. `mainline=tool_integration`.
5. `reverse-agent-iteration@v2` is active in `.codex-skills/registry.json`.
6. `task_packet.json` is advisory, not execution authority.
7. Current static triage artifact exists and has `executed_sample=false`.
8. Bridge result exists and is parseable.
9. Solver dispatch plan exists and does not claim solve-ready.
10. No source/test files need to change unless a reusable report-generation bug is found.

Must verify after fixing:

1. `codex_execution_report.md` does not claim `executed_sample=true`.
2. `codex_execution_report.md` does not claim candidate/flag/solver/runtime execution.
3. provenance report evidence_counts match bridge result exactly by evidence kind family.
4. generated_artifacts includes all core artifacts created by the previous validation round and this fix round.
5. `pytest_result.txt` summary accurately reflects allowed/expected nonzero command exits.
6. final-check does not leave `report_status=PARTIAL` or `report_acceptance_recommendation=NEEDS_REVIEW`.
7. artifact_index entry for `local_reverse_affine_8cfebe03_static_triage` remains current and points to the current static triage artifact.

## 6. Implementation Scope

Preferred implementation is metadata/report-only. Do not modify Python source unless absolutely necessary.

Allowed files:

- `project_state/codex_execution_report.md`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260619_affine_current_static_bridge_report_fix_v1/*`

Allowed only if gate/report synthesis requires them to stay consistent:

- `project_state/artifact_index.json`

Allowed source files only if a reusable bug in report/provenance generation is found and tested:

- `reverse_agent/static_evidence_bridge.py`
- `reverse_agent/solver_dispatch_plan.py`
- `reverse_agent/evidence.py`

If source files are changed, add or update tests. If no source files are changed, do not add tests just to satisfy scope.

Expected provenance evidence_counts:

- `input`: 1
- `compare`: 1
- `constants`: 0
- `transform_hints`: 1
- `crypto_signatures`: 0
- `gui`: 0
- `anti_debug`: 1

These counts must be computed from `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`, not hardcoded blindly. If the bridge result differs, use the bridge result and explain the difference.

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m pytest tests/test_static_evidence_bridge.py tests/test_solver_dispatch_plan.py tests/test_evidence.py tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes or only has explicitly non-blocking warnings, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_current_static_bridge_report_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `tool_integration`.
4. `reverse-agent-iteration@v2` is not active.
5. Current static triage artifact is missing.
6. Current bridge result is missing or unparsable.
7. Provenance report cannot be made consistent with bridge result.
8. Fix requires running sample binary, solver, runtime probe, debugger, emulator, harness, GUI/frontend, or candidate generation.
9. Fix requires reading complete `solve_reports/` or complete `PROJECT_PROGRESS_LOG.txt`.
10. report/decision/pytest_result IDs mismatch after regeneration.
11. final-check has any FAIL.
12. final-check still leaves `report_status=PARTIAL` or `report_acceptance_recommendation=NEEDS_REVIEW` without a precise non-blocking explanation.
