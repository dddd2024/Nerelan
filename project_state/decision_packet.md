```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260619_affine_report_generated_artifacts_fix_v1",
  "round_id": "round_20260619_affine_report_generated_artifacts_fix_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "tool_integration",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

只修复 `project_state/codex_execution_report.md` 顶部 `codex_report_summary.generated_artifacts` 不完整的问题。

本轮是 metadata/report-only。不得重新运行 static triage，不得运行 IDA/Ghidra，不得运行 solver/runtime/debugger/harness，不得执行样本，不得生成 candidate/flag。

必须把 `codex_report_summary.generated_artifacts` 补全为能够覆盖上一轮 current static bridge validation 的核心产物和本轮修复产物。至少必须包含：

```text
project_state/artifact_index.json
project_state/local_reverse_affine_8cfebe03_current_static_triage.json
project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json
project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json
project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json
project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md
```

成功标准：

1. `codex_report_summary.generated_artifacts` 包含上述 6 个核心 artifact。
2. `codex_report_summary.files_changed` 与本轮实际改动一致。
3. report prose 不再声称 JSON summary 没有记录的事实。
4. 不发生 source/test 修改。
5. 不重新运行 static triage、IDA、solver、runtime 或样本。
6. final-check 无 FAIL；若仍有 warning，只能是 historical/backlog artifact non-blocking 或 close-round 过程中的非阻塞提示。

## 2. Current Evidence

上一轮 `decision_20260619_affine_current_static_bridge_report_fix_v1` 已修复大部分一致性问题，但审计结论仍为 `REWORK_REQUIRED`。

已经通过的事实：

- `codex_execution_report.md` 已修正 `executed_sample=false`，不再声称样本被执行。
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json` 已修正 evidence_counts：
  - input: 1
  - compare: 1
  - constants: 0
  - transform_hints: 1
  - crypto_signatures: 0
  - gui: 0
  - anti_debug: 1
- `.md` provenance report 也同步修正。
- pytest 记录启动路径正确，startup clean，pytest `844 passed`。
- final gate 已从 `PARTIAL / NEEDS_REVIEW` 变成 `PASSED_WITH_LIMITATIONS`，status summary 为 `report_status=SUCCESS`、`report_acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`。

唯一未完成项：

- `project_state/codex_execution_report.md` 顶部 `codex_report_summary.generated_artifacts` 仍未列出核心 current/bridge/provenance artifacts。

当前有效核心 artifact：

- `project_state/artifact_index.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`

当前 `task_packet.json` 仍是旧 `samplereverse` / `collect_missing_evidence` 建议，不是本轮执行权威。

当前 `negative_results.json` 继续有效：不要回到旧 `sample_solver` blind search，不要只扩 beam/budget/topN，不要把 `compare_semantics_agree=false` candidates 当 primary frontier，不要提交完整 `solve_reports/`。

## 3. Do Not Do

不要重新运行 static triage。

不要运行 IDA/Ghidra。

不要执行任何本地样本二进制。

不要运行 reverse-solving。

不要运行 solver、runtime probe、debugger、emulator、harness、GUI/frontend。

不要生成 candidate、flag、密码、key 或最终答案。

不要修改 Python 源码。

不要修改测试文件。

不要读取完整 `solve_reports/` 或完整 `PROJECT_PROGRESS_LOG.txt`。

不要上传、复制或提交本地样本二进制。

不要修改 `.codex-skills/`。

不要把历史 affine artifact 当 current evidence。

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
7. Core artifacts listed in Goal exist and are parseable or readable.
8. No source/test files need to change.

Must verify after fixing:

1. `codex_report_summary.generated_artifacts` includes all 6 core artifact paths.
2. `codex_report_summary.files_changed` reflects the actual current round delta.
3. report prose is consistent with JSON summary.
4. `codex_execution_report.md` does not claim candidate/flag/solver/runtime/static triage execution in this fix round.
5. `pytest_result.txt` summary accurately reflects allowed/expected nonzero command exits.
6. final-check has no FAIL.
7. If final gate remains `PASSED_WITH_LIMITATIONS`, limitations are explicitly non-blocking and do not include report/provenance mismatch.

## 6. Implementation Scope

Preferred implementation is metadata/report-only. Do not modify Python source.

Allowed files:

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
- `project_state/rounds/round_20260619_affine_report_generated_artifacts_fix_v1/*`

Do not modify:

- `reverse_agent/*.py`
- `tests/*.py`
- `project_state/local_reverse_affine_8cfebe03_current_static_triage.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_bridge_result.json`
- `project_state/local_reverse_affine_8cfebe03_current_solver_dispatch_plan.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.json`
- `project_state/local_reverse_affine_8cfebe03_current_static_provenance_report.md`
- `project_state/artifact_index.json`

Those core artifacts should be read and referenced, not regenerated or modified.

## 7. Tests

Must run and write results to `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short

python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If final-check passes or only has explicitly non-blocking warnings, close the round and rerun final-check:

```powershell
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_affine_report_generated_artifacts_fix_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/codex_execution_report.md` must include a valid `codex_report_summary` with matching `based_on_decision_id`, `round_id`, `files_changed`, `tests_ran`, and `generated_artifacts`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. Cannot confirm repository root `F:\reverse-agent`.
2. `decision_meta` is missing or not `APPROVED`.
3. `mainline` is not `tool_integration`.
4. `reverse-agent-iteration@v2` is not active.
5. Any of the 6 core artifacts listed in Goal is missing.
6. Fix requires rerunning IDA/static triage.
7. Fix requires modifying Python source or tests.
8. Fix requires running sample binary, solver, runtime probe, debugger, emulator, harness, GUI/frontend, or candidate generation.
9. Fix requires reading complete `solve_reports/` or complete `PROJECT_PROGRESS_LOG.txt`.
10. report/decision/pytest_result IDs mismatch after regeneration.
11. final-check has any FAIL.
12. final-check still reports report/provenance mismatch or generated_artifacts mismatch.
