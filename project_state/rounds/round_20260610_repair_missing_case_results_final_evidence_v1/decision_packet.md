```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_missing_case_results_final_evidence_v1","round_id":"round_20260610_repair_missing_case_results_final_evidence_v1","based_on_state_build_id":"state_20260610_081228_6c1551059244","based_on_state_digest":"6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Complete the final evidence chain for `decision_20260610_repair_missing_case_results_harness_artifact_v1`.

Do not redo the missing `case_results/` implementation unless final status exposes a real defect. The previous round already updated `model_gate.json` and `task_packet.json` to represent the incomplete harness artifact. This round exists only to bind the live report/test files to a final evidence repair decision and record post-archive `lint-report` and `status` output.

This is an `engineering_branch` evidence-closure round, not reverse solving.

## 2. Current Evidence

- Current live `decision_packet.md` before this packet was `decision_20260610_repair_missing_case_results_harness_artifact_v1`.
- Live `codex_execution_report.md` is bound to `decision_20260610_repair_missing_case_results_harness_artifact_v1` and reports `status: SUCCESS`.
- Live `model_gate.json` reports `harness_diagnostics.case_results_missing: true`, `harness_diagnostics.latest_harness_run_status: invalid_or_incomplete`, and `next_local_action: repair_harness_artifact`.
- Live `task_packet.json` reports `task: repair_harness_artifact` and `next_local_action: repair_harness_artifact`.
- Live `pytest_result.txt` reports `163 passed`, but only records build/status/lint-decision/pytest in `tests_ran`.
- The previous report did not record final `lint-report`, final `status`, or post-archive final `lint-report/status` output.
- A round manifest exists for `round_20260610_repair_missing_case_results_harness_artifact_v1`, but the live pytest/report evidence does not show the final consumed/archived status required by the project workflow.
- Current state anchor for this evidence-closure decision is `state_20260610_081228_6c1551059244` with digest `6c1551059244adb018154536da5d72c4cfa2b59e8502b8f026b587a6f4d6e936`.
- `artifact_index.json` may still contain stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, repeated stale probes, and stale hook reuse.
- `.codex-skills/registry.json` has active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.

## 3. Do Not Do

- Do not redo the missing `case_results/` feature implementation unless final status exposes a true defect.
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
- Do not create another broad project-state feature.

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

Required source/test files only if final status exposes a true defect:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Allowed archive files:

- `project_state/rounds/round_20260610_repair_missing_case_results_harness_artifact_v1/round_manifest.json`
- `project_state/rounds/round_20260610_repair_missing_case_results_harness_artifact_v1/codex_execution_report.md`
- `project_state/rounds/round_20260610_repair_missing_case_results_harness_artifact_v1/pytest_result.txt`
- New minimal archive for this evidence-closure round.

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm the active decision is this packet and that `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm live `model_gate.json` still reports:
   - `case_results_missing: true`
   - `latest_harness_run_status: invalid_or_incomplete`
   - `next_local_action: repair_harness_artifact`
4. Confirm live `task_packet.json` reports:
   - `task: repair_harness_artifact`
   - `next_local_action: repair_harness_artifact`
5. Run and record final evidence commands, without rerunning sample/solver/tool work.
6. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
7. Update live `project_state/pytest_result.txt` so it includes exact command outputs, not only a one-line pytest summary.
8. Archive this evidence-closure round only after live report/test files are updated.
9. After archive, rerun or record final `lint-report` and `status` so the final recorded output reflects the archived round.
10. Ensure final status shows:
    - `decision_report_id_match: True`
    - `decision_consumed_by_report: True`
    - `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`
    - `round_manifest_present: True`
    - `archive_status: archived`
11. Ensure no stale/missing artifact is promoted to current.
12. Ensure no sample/tool/debugger/solver/probe execution occurred.
13. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Preferred changes are report/state evidence only:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_repair_missing_case_results_final_evidence_v1/*`, minimal archive only

Allowed generated files only if existing tooling regenerates them while recording final status:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`

Allowed source/test changes only if final status exposes a true project-state bug:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

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

Run and record exact outputs in live `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_repair_missing_case_results_final_evidence_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

If Codex needs to re-run focused tests because a source/test bug is exposed, record:

```bash
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
```

Acceptance requirements:

- Live `model_gate.json` still reports `case_results_missing: true` for the current latest harness run.
- Live `model_gate.json` still reports `latest_harness_run_status: invalid_or_incomplete`.
- Live `model_gate.json` still reports `next_local_action: repair_harness_artifact`.
- Live `task_packet.json` still reports `task: repair_harness_artifact`.
- Live `pytest_result.txt` records full final command outputs.
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

- Final `lint-report` cannot pass.
- Final `status` cannot reach consumed/archived state.
- Fixing requires running a sample binary.
- Fixing requires solver/search/candidate generation/candidate validation.
- Fixing requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires broad refactor outside project-state evidence closure.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```