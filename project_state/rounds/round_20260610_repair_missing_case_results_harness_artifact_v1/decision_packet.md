```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_missing_case_results_harness_artifact_v1","round_id":"round_20260610_repair_missing_case_results_harness_artifact_v1","based_on_state_build_id":"state_20260610_072727_3823c4ff37ca","based_on_state_digest":"3823c4ff37cacde2c7fefb71a97f8dc003bed57d1c6d77ed868ce3c401c3ecc9","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the `project_state` handling of a latest harness run whose `summary.json` exists but whose `case_results/` directory is missing.

Current live `model_gate.json` correctly reports `harness_diagnostics.case_results_missing == true` and `next_local_action == repair_harness_artifact`. This round must turn that signal into a precise, auditable harness artifact state so the system no longer treats the latest incomplete run as inspectable failed-case evidence or produces a generic reverse-solving task from it.

This is an `engineering_branch` task. Do not solve the sample, do not generate candidates, and do not run external reverse/debug tools.

## 2. Current Evidence

- Current state anchor: `state_20260610_072727_3823c4ff37ca` with digest `3823c4ff37cacde2c7fefb71a97f8dc003bed57d1c6d77ed868ce3c401c3ecc9`.
- Current `model_gate.json` has `harness_diagnostics.case_results_missing: true`, `diagnosis: case_results_directory_absent`, and `next_local_action: repair_harness_artifact`.
- The latest harness run referenced by state is `solve_reports\harness_runs\samplereverse_exact1_projected_vs_neighbor_20260424`.
- Current `harness_diagnostics` says `summary_present: true`, `summary_resumed_cases: 1`, `summary_error_cases: 1`, `summary_executed_cases: 0`, `summary_total_cases: 1`, and `case_results_count: 0`.
- Current `task_packet.json` still reports `task: collect_missing_evidence` and reverse-solving relevant files, even though the actionable local repair is the missing `case_results/` artifact.
- Current `artifact_index.json` still contains stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, repeated stale probes, and stale hook reuse.
- `.codex-skills/registry.json` has active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
- Existing relevant capabilities are the current `reverse_agent/project_state.py` state builder, model gate construction, harness diagnostics, task packet generation, artifact index generation, and existing project-state tests. Do not duplicate these mechanisms.

## 3. Do Not Do

- Do not run any sample binary.
- Do not generate, mutate, rank, or validate candidates.
- Do not run solver/search expansion.
- Do not run runtime probe, debugger, emulator, hook, sidecar, IDA, Ghidra, OllyDbg, or x64dbg.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not change sample binaries, candidate files, training data, or status overlays.
- Do not promote stale/missing artifacts to current.
- Do not treat a missing `case_results/` directory as an inspectable failed case.
- Do not replace mature external reverse tooling with custom static/dynamic analysis logic.

## 4. Files To Inspect

Required project-state files:

- `project_state/decision_packet.md`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`

Required source/test files:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Allowed bounded runtime artifact inspection:

- Directory existence/listing for `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/`
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- Do not inspect unrelated harness runs except by metadata summary needed to test fallback selection logic.

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm the active decision is this packet and that `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm the latest harness run has `summary_present == true` but `case_results_missing == true`.
4. Identify the current code path in `reverse_agent/project_state.py` that builds `harness_diagnostics`, `model_gate.json`, and `task_packet.json` from harness artifacts.
5. Check whether existing tests already cover the case where summary exists but `case_results/` is absent.
6. Implement the smallest project-state change needed so this condition is represented as an explicit incomplete/invalid harness artifact state, for example `latest_harness_run_status: invalid_or_incomplete` or an equivalent existing schema-compatible field.
7. Ensure `task_packet.json` no longer frames this condition as ordinary reverse-solving `collect_missing_evidence` when the actionable next local work is repairing/rebuilding the harness artifact.
8. Preserve compatibility with existing fields; do not remove old fields consumed by current tests or UI.
9. Ensure `model_gate.json` keeps `next_local_action: repair_harness_artifact` or a documented equivalent existing action for this missing-artifact state.
10. Ensure stale/missing artifacts remain stale/missing unless a current artifact with provenance is generated by build tooling.
11. Add or update focused tests for the summary-present/case_results-absent case.
12. Run the required tests and record exact outputs in `project_state/pytest_result.txt`.
13. Update `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
14. Archive this round only after live report/test/state files are updated.
15. After archive, rerun or record final `lint-report` and `status` so the final recorded output reflects the archived round.
16. Ensure no sample/tool/debugger/solver/probe execution occurred.
17. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to project-state harness diagnostics, model gate, task packet, artifact-index/status handling for missing `case_results/`.
- `tests/test_project_state.py`, limited to focused regression coverage for summary-present/case_results-absent behavior.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by artifact manifest validation.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_repair_missing_case_results_harness_artifact_v1/*`, minimal archive only

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`

## 7. Tests

Run and record exact outputs:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

After archiving this round, record final outputs for:

```bash
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- `model_gate.json` still reports `case_results_missing: true` for the current latest harness run.
- `model_gate.json` reports `next_local_action: repair_harness_artifact` or a documented equivalent existing action.
- The missing `case_results/` condition is explicitly classified as an incomplete/invalid harness artifact state.
- `task_packet.json` no longer presents this condition as generic reverse-solving `collect_missing_evidence` if the actionable local step is harness artifact repair.
- Focused regression tests cover summary-present/case_results-absent behavior.
- pytest passes for the tests run.
- `lint-report: OK` after report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Fixing requires running a sample binary.
- Fixing requires solver/search/candidate generation/candidate validation.
- Fixing requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires broad refactor outside project-state harness diagnostics/task/model-gate logic.
- `.codex-skills/` changes are required.
- No schema-compatible way exists to represent incomplete harness run status without breaking existing state consumers.
- `lint-report` fails after final report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```