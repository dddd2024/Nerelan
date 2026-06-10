```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_selected_fallback_evidence_materialization_v1","round_id":"round_20260610_repair_selected_fallback_evidence_materialization_v1","based_on_state_build_id":"state_20260610_103205_f0ad87317cc3","based_on_state_digest":"f0ad87317cc3be9adedda92452a22391b8cb8f6b21a246949b6fec5f4435df9a","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the selected fallback evidence chain after strict readiness classification.

The current live state correctly refuses to treat the selected fallback run as ready because the selected case result is `not_found`, `validation_count` is `0`, and the embedded artifact manifest includes `instrumentation_incomplete`. This round must not bypass that strictness. The goal is to make the repair path concrete, schema-compatible, and test-covered so the next local action is no longer a vague `repair_selected_fallback_evidence` placeholder.

This is an `engineering_branch` round. It is not a reverse-solving round and must not generate, rank, validate, or emit any candidate or flag.

## 2. Current Evidence

- Previous decision consumed: `decision_20260610_repair_selected_fallback_readiness_strictness_v1`.
- Previous audit result: `ACCEPTED_WITH_LIMITATIONS`.
- `project_state/codex_execution_report.md` is bound to the previous decision and reports `SUCCESS`.
- `project_state/pytest_result.txt` records `166 passed in 41.83s`, final `lint-report: OK`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, and `archive_status: archived`.
- Live `project_state/model_gate.json` now sets `next_local_action: repair_selected_fallback_evidence`.
- Live `selected_harness_evidence_source.readiness_audit.classification` is `fallback_evidence_incomplete`.
- Live readiness reason is `case_result_status_is_not_found`.
- Live readiness metadata still records `case_result_statuses: ["not_found"]`, `validation_count: 0`, `candidate_count: 3`, `structured_evidence_count: 1`, and `tool_artifact_count: 1`.
- The selected fallback run remains `sr_arg0_hook_readiness_ordering_20260526_r1` with `selection_role: fallback` and `provenance: fallback_from_invalid_latest_run`.
- The latest invalid run remains separately recorded as `solve_reports\\harness_runs\\samplereverse_exact1_projected_vs_neighbor_20260424` with reason `case_results_directory_absent`.
- `project_state/task_packet.json` currently has `task: repair_selected_fallback_evidence`; it is advisory only. This `decision_packet.md` controls the current round.
- `project_state/artifact_index.json` still contains stale artifacts. Stale/missing artifacts must not be promoted to current.
- Negative results still block blind search, beam/budget expansion, stale hook reuse, full `solve_reports/` scans, and repeated failed runtime probe directions.
- Existing relevant capabilities include `reverse_agent/project_state.py`, `reverse_agent/harness.py`, `tests/test_project_state.py`, `tests/test_harness_artifact_manifest.py`, and `tests/test_harness_compare.py`. Inspect and reuse them; do not create duplicate harness/project-state writers.
- IDA/Ghidra/debugger/solver interfaces are not in scope for this engineering repair round. Their existence must not be denied, but they must not be run.

## 3. Do Not Do

- Do not run any sample binary.
- Do not run the harness on a real sample or replay the selected fallback run.
- Do not generate, mutate, rank, or validate candidates.
- Do not run solver/search expansion.
- Do not run runtime probes, debugger, emulator, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not change solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not change sample binaries, candidate files, training data, or status overlays.
- Do not promote stale/missing artifacts to current.
- Do not silently promote the fallback run to latest/current.
- Do not mark fallback evidence ready unless all strict readiness requirements are actually satisfied by bounded metadata.
- Do not paper over `not_found`, `instrumentation_incomplete`, or `validation_count: 0` by changing labels only.

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
- `reverse_agent/harness.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`
- `tests/test_harness_compare.py`, only if the harness status/manifest contract is directly affected.

Allowed bounded fallback evidence inspection:

- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
- Directory existence and filenames under `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/`
- The single selected fallback case-result JSON file, if exactly one exists, limited to metadata fields: `case_id`, `input_value`, `resolved_path`, `status`, `matched_expected`, `candidate_count`, `structured_evidence_count`, `tool_artifact_count`, `validation_count`, `artifact_manifest`, `error`, and provenance/status fields.
- Embedded artifact manifest entries already present in that case result. Do not open all referenced tool artifact payloads unless bounded metadata is insufficient to classify the repair blocker.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm the previous round is consumed/archived and report/decision matched.
4. Inspect the current strict readiness classifier in `reverse_agent/project_state.py` and preserve its blocking semantics.
5. Inspect the existing harness case-result and artifact-manifest writer path in `reverse_agent/harness.py`; reuse existing code and do not create a duplicate writer.
6. Determine, from bounded metadata and existing code, which component owns each blocker:
   - `status: not_found`;
   - `summary.not_found_cases > 0` if present;
   - `artifact_manifest[].classification: instrumentation_incomplete`;
   - `validation_count: 0`.
7. Add a schema-compatible repair diagnostic to live project state, preferably under `selected_harness_evidence_source.readiness_audit.repair_diagnostics` or an adjacent stable field, with:
   - `blockers`: a list of concrete blocker codes;
   - `repairable_from_existing_metadata`: boolean;
   - `required_rebuild`: boolean;
   - `owner_component`: `project_state`, `harness`, `case_result_writer`, `artifact_manifest_writer`, or `unknown`;
   - `next_local_action`: a precise bounded action, not generic guessing.
8. If the current selected fallback cannot be made ready from existing bounded metadata, keep `classification: fallback_evidence_incomplete` and set a precise action such as `rebuild_selected_fallback_case_result_metadata` or `repair_harness_case_result_materialization`.
9. If a schema/projection bug is found and can be repaired without executing samples or harness runs, fix only that bug and add tests.
10. Do not change historical `solve_reports/` files merely to make the current fallback appear ready.
11. Preserve fallback provenance, run name/path, summary path, manifest path, latest invalid run, and fallback selection role.
12. Preserve the latest invalid run record separately; do not overwrite it with the fallback.
13. Ensure no stale/missing artifact is promoted to current.
14. Ensure no sample/tool/debugger/solver/probe/IDA/Ghidra execution occurred.
15. Update live `project_state/pytest_result.txt` with exact command outputs.
16. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
17. Archive this round after live report/test/state files are updated.
18. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to selected fallback evidence repair diagnostics, precise next-local-action projection, status/lint display if necessary, and schema-compatible state output.
- `reverse_agent/harness.py`, only if a bounded bug is found in case-result status, not-found accounting, validation count projection, or embedded artifact-manifest metadata generation. Do not alter runtime execution behavior.
- `tests/test_project_state.py`, limited to focused project-state repair diagnostic tests.
- `tests/test_harness_artifact_manifest.py`, limited to focused case-result/artifact-manifest contract tests.
- `tests/test_harness_compare.py`, only if directly affected by a harness case-result contract change.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_repair_selected_fallback_evidence_materialization_v1/*`, minimal archive only

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
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_harness_compare.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_repair_selected_fallback_evidence_materialization_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Current fallback remains not ready unless strict readiness blockers are genuinely absent.
- `status: not_found` remains a blocker.
- Embedded `instrumentation_incomplete` remains a blocker.
- `validation_count == 0` remains a blocker.
- Repair diagnostics identify all current blockers and their owner component as specifically as possible.
- `task_packet.json` advances to a precise bounded repair action, not `prepare_reverse_solving_from_selected_fallback_evidence`.
- Fallback remains selected fallback evidence, not latest/current evidence.
- Latest invalid harness run remains separately recorded as invalid/incomplete.
- Regression tests cover the current not-found / instrumentation-incomplete / zero-validation path.
- Positive tests cover a repair-ready or genuinely-ready metadata path without weakening strictness.
- `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_harness_compare.py -q` passes.
- `lint-report: OK` after live report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution occurred.
- No `.codex-skills/` modification occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repairing selected fallback evidence requires running a sample binary.
- Repairing selected fallback evidence requires running the harness on a sample.
- Repairing selected fallback evidence requires solver/search/candidate generation/candidate validation.
- Repairing selected fallback evidence requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Repairing selected fallback evidence requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent repair diagnostics without breaking existing state consumers.
- The only way to make the fallback look ready is to relabel incomplete evidence.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into direct reverse solving, candidate generation, runtime validation, or debugger work.
