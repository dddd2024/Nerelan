```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_resolve_harness_artifact_repair_action_v1","round_id":"round_20260610_resolve_harness_artifact_repair_action_v1","based_on_state_build_id":"state_20260610_081228_6c1551059244","based_on_state_digest":"6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Resolve the current `repair_harness_artifact` state into a precise next local action.

The previous rounds correctly classified the latest harness run as `invalid_or_incomplete` because `summary.json` exists but `case_results/` is missing. This round must not redo that classification. Instead, it must decide whether project_state can safely select an existing complete harness run, or whether the correct next action is a bounded harness artifact rebuild in a later round.

This is an `engineering_branch` state-selection and repair-planning round. It must not run samples, solvers, runtime probes, or reverse-debugging tools.

## 2. Current Evidence

- Current state anchor: `state_20260610_081228_6c1551059244` with digest `6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936`.
- Current `model_gate.json` reports `harness_diagnostics.case_results_missing: true`.
- Current `model_gate.json` reports `harness_diagnostics.latest_harness_run_status: invalid_or_incomplete`.
- Current `model_gate.json` reports `next_local_action: repair_harness_artifact`.
- Current `task_packet.json` reports `task: repair_harness_artifact` and `next_local_action: repair_harness_artifact`.
- The latest harness run remains `solve_reports\harness_runs\samplereverse_exact1_projected_vs_neighbor_20260424`, whose summary says `summary_present: true`, `summary_resumed_cases: 1`, `summary_error_cases: 1`, `summary_executed_cases: 0`, `summary_total_cases: 1`, and `case_results_count: 0`.
- `artifact_index.json` still includes stale/missing artifacts; stale/missing artifacts must not be promoted to current.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, repeated stale probes, stale hook reuse, and full solve_reports scans.
- Existing code already has project-state build/status/lint/archive logic, harness diagnostics, model gate generation, task packet generation, and artifact-index handling in `reverse_agent/project_state.py`. Do not duplicate those mechanisms.
- Existing harness tests cover case-result artifact manifests in `tests/test_harness_artifact_manifest.py`; do not rewrite harness execution.

## 3. Do Not Do

- Do not run any sample binary.
- Do not run the harness on a sample.
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
- Do not treat a run without `case_results/` as inspectable failed-case evidence.
- Do not create synthetic `case_results/` that pretend a sample was executed.
- Do not mark a fallback harness run as current unless provenance is explicit and schema-compatible.

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

Allowed bounded harness metadata inspection:

- Directory existence/listing for `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/`
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- A bounded metadata-only listing of sibling `solve_reports/harness_runs/*` directory names and their `summary.json` / `run_manifest.json` / `case_results/` presence, only to determine whether a complete fallback run exists.

Do not open full case result payloads except existence/count metadata. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm live `model_gate.json` and `task_packet.json` still represent the current condition as `repair_harness_artifact`.
4. Identify the existing project-state code path that selects the latest harness run and produces `latest_harness_run`, `harness_diagnostics`, `model_gate.json`, `task_packet.json`, and artifact freshness.
5. Perform bounded metadata-only inspection of harness runs to answer one question: is there an existing complete harness run with `case_results/` and compatible summary/run manifest that can be selected as a current evidence source without violating freshness/provenance rules?
6. If a complete compatible fallback run exists, implement the smallest schema-compatible change so project_state records that the latest run is invalid/incomplete and uses the complete run only as an explicitly identified fallback, with provenance and freshness semantics clear.
7. If no complete compatible fallback run exists, implement the smallest schema-compatible change so `model_gate.json` / `task_packet.json` move from generic `repair_harness_artifact` to a more precise next action such as `rebuild_harness_artifact` or an equivalent existing action name.
8. Preserve backward compatibility for existing fields consumed by tests or UI.
9. Add or update focused tests for the selected path:
   - invalid latest run with no complete fallback; and/or
   - invalid latest run with a complete fallback selected explicitly.
10. Ensure stale/missing artifacts remain stale/missing unless current provenance is created by existing build tooling.
11. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
12. Update live `project_state/pytest_result.txt` with exact command outputs.
13. Archive this round after live report/test/state files are updated.
14. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.
15. Ensure no sample/tool/debugger/solver/probe execution occurred.
16. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to harness run selection, invalid latest run handling, fallback provenance, model gate next action, task packet action, and status/lint display for this condition.
- `tests/test_project_state.py`, limited to focused regression tests for invalid latest harness run resolution.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by harness artifact metadata compatibility.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_resolve_harness_artifact_repair_action_v1/*`, minimal archive only

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_resolve_harness_artifact_repair_action_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- The latest incomplete harness run remains explicitly classified as invalid/incomplete.
- If a fallback run is selected, it is explicitly marked as fallback with provenance; it is not silently promoted as the latest/current run.
- If no fallback is selected, `model_gate.json` and `task_packet.json` provide a more precise next local action than generic `repair_harness_artifact`, such as `rebuild_harness_artifact` or an equivalent existing action.
- `task_packet.json` must not revert to generic reverse-solving `collect_missing_evidence` for this condition.
- Focused regression tests cover the chosen path.
- pytest passes for the tests run.
- `lint-report: OK` after live report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Resolving the repair action requires running a sample binary.
- Resolving the repair action requires running the harness on a sample.
- Resolving the repair action requires solver/search/candidate generation/candidate validation.
- Resolving the repair action requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Resolving the repair action requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent fallback or rebuild action without breaking existing state consumers.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```