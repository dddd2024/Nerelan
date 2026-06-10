```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_audit_selected_fallback_evidence_readiness_v1","round_id":"round_20260610_audit_selected_fallback_evidence_readiness_v1","based_on_state_build_id":"state_20260610_094837_a4313227b2c2","based_on_state_digest":"a4313227b2c22e056f7c941825be22228943efb53d28f251cc0292e8f475f15e","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Audit the selected fallback harness evidence for readiness.

The previous round materialized `selected_harness_evidence_source` in live `model_gate.json` and advanced the current task to `inspect_selected_fallback_evidence`. This round must perform a bounded metadata/provenance audit of that selected fallback evidence and write an explicit readiness classification into project state.

The goal is not to solve the reverse sample. The goal is to answer whether the selected fallback run is safe and sufficient as the evidence basis for a later reverse-solving decision, or whether the fallback evidence is incomplete/stale and a rebuild/audit repair is still required.

This is an `engineering_branch` evidence-readiness round. Do not run samples, solvers, candidates, runtime probes, debuggers, IDA, or Ghidra.

## 2. Current Evidence

- Current state anchor: `state_20260610_094837_a4313227b2c2` with digest `a4313227b2c22e056f7c941825be22228943efb53d28f251cc0292e8f475f15e`.
- Current `model_gate.json` contains `selected_harness_evidence_source`.
- The selected fallback source has `selection_role: fallback` and `provenance: fallback_from_invalid_latest_run`.
- The selected fallback run is `sr_arg0_hook_readiness_ordering_20260526_r1`.
- The selected fallback run path is `solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1`.
- The selected fallback summary path is `solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\summary.json`.
- The selected fallback manifest path is `solve_reports\harness_runs\sr_arg0_hook_readiness_ordering_20260526_r1\run_manifest.json`.
- The selected fallback source has `case_results_count: 1` and `total_cases: 1`.
- The latest invalid run is still separately recorded as `solve_reports\harness_runs\samplereverse_exact1_projected_vs_neighbor_20260424` with status `invalid_or_incomplete` and reason `case_results_directory_absent`.
- Current `model_gate.json` has `next_local_action: inspect_selected_fallback_evidence`.
- Current `task_packet.json` has `task: inspect_selected_fallback_evidence` and `next_local_action: inspect_selected_fallback_evidence`.
- `artifact_index.json` may still contain stale/missing artifacts. Stale or missing artifacts must not be promoted to current.
- Negative results still block blind search, beam/budget expansion, stale hook reuse, full solve_reports scanning, and repeated failed probe directions.
- `.codex-skills/registry.json` has active `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.

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
- Do not silently promote the fallback run to latest/current.
- Do not decide or emit a flag/candidate.
- Do not treat this as permission for reverse-solving execution.

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

Allowed bounded fallback evidence inspection:

- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
- Directory existence and filenames under `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/`
- The single selected fallback case-result JSON file, if exactly one exists, limited to metadata fields such as `case_id`, `input_value`, `resolved_path`, `status`, `matched_expected`, `candidate_count`, `structured_evidence_count`, `tool_artifact_count`, `artifact_manifest`, and related provenance/status fields.
- Artifact manifest entries referenced by that case result, but only metadata already embedded in the case result. Do not open every tool artifact payload unless the case-result metadata is insufficient to classify readiness.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm live `model_gate.json` and `task_packet.json` currently request `inspect_selected_fallback_evidence`.
4. Confirm `selected_harness_evidence_source.selection_role == fallback` and provenance is `fallback_from_invalid_latest_run`.
5. Confirm the latest invalid run remains recorded separately and was not overwritten by the fallback.
6. Perform bounded metadata-only inspection of the selected fallback summary, run manifest, and case_results directory.
7. If exactly one fallback case result exists, inspect only bounded metadata from that case result and its embedded artifact manifest.
8. Classify fallback evidence readiness into one explicit state, for example:
   - `fallback_evidence_ready_for_reverse_decision`
   - `fallback_evidence_incomplete`
   - `fallback_evidence_stale_or_untrusted`
   - `fallback_evidence_schema_gap`
9. Record why the classification was chosen, including the specific missing or sufficient fields.
10. Write the classification into live project state in a schema-compatible way, for example under `model_gate.json`, `task_packet.json`, or `current_state.json` as `selected_fallback_evidence_readiness` or equivalent.
11. Advance `next_local_action` / `task` to a bounded next action:
    - if ready: `prepare_reverse_solving_from_selected_fallback_evidence` or equivalent handoff action;
    - if not ready: `repair_selected_fallback_evidence` or equivalent engineering action.
12. Do not generate candidates, run solvers, validate candidates, or attempt reverse-solving in this round.
13. Preserve backward compatibility for existing project-state fields consumed by tests or UI.
14. Add or update focused tests that exercise the actual build/readiness path with selected fallback evidence.
15. Run required tests and record exact outputs in live `project_state/pytest_result.txt`.
16. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
17. Archive this round after live report/test/state files are updated.
18. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.
19. Ensure no sample/tool/debugger/solver/probe execution occurred.
20. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to selected fallback evidence readiness classification, project-state output fields, and status/lint display.
- `tests/test_project_state.py`, limited to focused regression tests for selected fallback evidence readiness classification.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by selected fallback evidence metadata compatibility.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_audit_selected_fallback_evidence_readiness_v1/*`, minimal archive only

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_audit_selected_fallback_evidence_readiness_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Live state contains an explicit selected fallback evidence readiness classification.
- The classification references `sr_arg0_hook_readiness_ordering_20260526_r1` and its bounded summary/manifest/case_result metadata.
- The latest invalid harness run remains separately recorded as invalid/incomplete.
- Fallback is not silently promoted to latest/current.
- `model_gate.json` / `task_packet.json` advance beyond `inspect_selected_fallback_evidence` to the appropriate next bounded action.
- If evidence is ready, the next action must be a handoff-preparation action, not direct solving.
- If evidence is not ready, the next action must be an engineering repair action.
- `task_packet.json` must not revert to `collect_missing_evidence` for this condition.
- Focused regression tests cover the actual readiness classification path.
- `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q` passes.
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

- Readiness classification requires running a sample binary.
- Readiness classification requires running the harness on a sample.
- Readiness classification requires solver/search/candidate generation/candidate validation.
- Readiness classification requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Readiness classification requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent readiness without breaking existing state consumers.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into direct reverse solving, candidate generation, runtime validation, or debugger work.
```