```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rebind_unactionable_gate_repair_live_state_v1","round_id":"round_20260610_rebind_unactionable_gate_repair_live_state_v1","based_on_state_build_id":"state_20260610_043358_c568aa84f77a","based_on_state_digest":"c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Rebind and finalize the previous `repair_unactionable_missing_case_results_gate` work into live `project_state`.

The code appears to contain the intended `repair_harness_artifact` behavior, and the round archive contains a report/test record for `decision_20260610_repair_unactionable_missing_case_results_gate_v1`. However, live `project_state/codex_execution_report.md`, live `project_state/pytest_result.txt`, and live `project_state/model_gate.json` still reflect the previous round or stale generated state.

This is an `engineering_branch` project-state consistency repair round. Do not solve `samplereverse`. Do not run samples, solvers, probes, debuggers, IDA/Ghidra, or external reverse tools. Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` remains advisory only.

## 2. Current Evidence

- Current state build is `state_20260610_043358_c568aa84f77a` with digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
- Active pre-rebind decision was `decision_20260610_repair_unactionable_missing_case_results_gate_v1`.
- Live `project_state/codex_execution_report.md` still reports `report_20260610_repair_report_archive_and_status_evidence_v1` and `based_on_decision_id: decision_20260610_repair_report_archive_and_status_evidence_v1`.
- Live `project_state/pytest_result.txt` still reports `decision_20260610_repair_report_archive_and_status_evidence_v1`, `report_20260610_repair_report_archive_and_status_evidence_v1`, and `round_20260610_repair_report_archive_and_status_evidence_v1`.
- Live `project_state/model_gate.json` still reports:
  - `reason: latest harness case has errors`
  - `harness_diagnostics.case_results_missing: true`
  - `harness_diagnostics.diagnosis: case_results_directory_absent`
  - `next_local_action: inspect_failed_case_result`
- `reverse_agent/project_state.py` appears to contain the intended conditional mapping: when `summary_error_detail.get("case_results_missing") is True`, `next_local_action` becomes `repair_harness_artifact`; otherwise it remains `inspect_failed_case_result`.
- Archive files exist for `round_20260610_repair_unactionable_missing_case_results_gate_v1`, but the live report/test/model gate were not rebound to that work.
- The archive report for `round_20260610_repair_unactionable_missing_case_results_gate_v1` claims `current_repair_archive_created: false` and `archived_files: []`, while a round manifest exists. This archive metadata is internally inconsistent and should be corrected in the new live report/archive.
- `artifact_index.json` still contains stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, and repeated stale probe directions.
- Existing relevant capability is `reverse_agent/project_state.py` plus `tests/test_project_state.py` and harness artifact manifest tests. Do not duplicate state builder, harness, IDA/Ghidra/debugger, or solver interfaces.

## 3. Do Not Do

- Do not run any sample binary.
- Do not run solver/search/candidate generation/candidate validation.
- Do not run runtime probe, debugger, emulator, hook, sidecar, IDA, Ghidra, OllyDbg, or x64dbg.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not change solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not hand-edit reverse-solving conclusions.
- Do not promote stale/missing artifacts to current.
- Do not solve the `samplereverse` sample in this round.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`
- `project_state/rounds/round_20260610_repair_unactionable_missing_case_results_gate_v1/codex_execution_report.md`
- `project_state/rounds/round_20260610_repair_unactionable_missing_case_results_gate_v1/pytest_result.txt`
- `project_state/rounds/round_20260610_repair_unactionable_missing_case_results_gate_v1/round_manifest.json`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260610_043358_c568aa84f77a` and digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `task_packet.json` is advisory only and this decision controls the round.
5. Confirm the previous implementation in `reverse_agent/project_state.py` maps missing `case_results/` to `repair_harness_artifact`.
6. Rebuild or regenerate live `model_gate.json` using existing project-state tooling so the live file no longer says `inspect_failed_case_result` when `harness_diagnostics.case_results_missing == true`.
7. Update live `project_state/codex_execution_report.md` so `codex_report_summary.based_on_decision_id` matches this rebind decision.
8. Update live `project_state/pytest_result.txt` so `pytest_result_summary.decision_id`, `pytest_result_summary.report_id`, and `pytest_result_summary.round_id` match this rebind decision/report/round and include exact command outputs.
9. Run final `python -m reverse_agent.project_state status --state-dir project_state` and ensure it shows this rebind decision consumed by a matching report.
10. Ensure archive metadata is internally consistent: if the round is archived, report fields must not claim `archived_files: []` or `current_repair_archive_created: false`.
11. Preserve the existing source fix; do not rewrite it unless a focused test proves it is wrong.
12. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
13. Ensure no sample/tool/debugger/solver/probe execution occurred.
14. Ensure no `.codex-skills/` changes occurred.
15. Archive this round using existing project-state archive tooling only after live report/test/model-gate consistency is achieved.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `reverse_agent/project_state.py`, only if the existing fix is incomplete
2. `tests/test_project_state.py`, only if a missing assertion must be restored
3. `tests/test_harness_artifact_manifest.py`, only if directly affected

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/model_gate.json`, only via existing project-state tooling
4. `project_state/task_packet.json`, `project_state/current_state.json`, and `project_state/artifact_index.json`, only if regenerated by existing project-state build tooling
5. `project_state/rounds/round_20260610_rebind_unactionable_gate_repair_live_state_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

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
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- `lint-decision: OK`.
- `lint-report: OK` after report update.
- pytest passes for all tests run.
- Live `model_gate.json` has `next_local_action: repair_harness_artifact` when `case_results_missing: true`.
- Live `codex_execution_report.md` matches this rebind decision.
- Live `pytest_result.txt` matches this rebind report.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.
- Any source change is minimal, tested, and limited to project-state gate/report/build consistency.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Fixing live state requires running samples or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation or validation.
- Fixing requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Fixing requires broad refactor outside project-state report/build/gate consistency.
- `.codex-skills/` changes are required.
- `lint-decision` or `lint-report` fails after update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
