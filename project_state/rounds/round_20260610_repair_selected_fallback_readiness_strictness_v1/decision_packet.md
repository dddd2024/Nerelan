```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_selected_fallback_readiness_strictness_v1","round_id":"round_20260610_repair_selected_fallback_readiness_strictness_v1","based_on_state_build_id":"state_20260610_100735_78fcbbcf9a7c","based_on_state_digest":"78fcbbcf9a7c195e1409a59f9f6c6de51336bbf5e23b0731bad496b78214bd07","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair selected fallback evidence readiness classification.

The current implementation classifies fallback evidence as `fallback_evidence_ready_for_reverse_decision` even when the bounded case result has `status: not_found`, `validation_count: 0`, and an embedded tool artifact classification of `instrumentation_incomplete`.

This round must make the readiness classifier stricter and schema-compatible. The goal is not to solve the sample. The goal is to prevent incomplete fallback instrumentation evidence from being treated as ready for reverse-solving handoff.

This is an `engineering_branch` repair round. Do not run samples, solvers, candidate generation, candidate validation, runtime probes, debuggers, IDA, Ghidra, emulator, hooks, or sidecars.

## 2. Current Evidence

- Active previous decision: `decision_20260610_audit_selected_fallback_evidence_readiness_v1`.
- Previous Codex report/test wiring is mostly valid: report/decision matched, pytest passed, final status consumed and archived.
- Live `model_gate.json` currently sets `selected_harness_evidence_source.readiness_audit.classification` to `fallback_evidence_ready_for_reverse_decision`.
- The same readiness audit records `case_result_statuses: ["not_found"]`, `validation_count: 0`, `candidate_count: 3`, `structured_evidence_count: 1`, and `tool_artifact_count: 1`.
- Codex report records the bounded case result metadata as `status: not_found`, `validation_count: 0`, and `artifact_manifest[0].classification: instrumentation_incomplete`.
- The selected fallback run is still `sr_arg0_hook_readiness_ordering_20260526_r1`.
- The latest invalid run remains separately recorded as `solve_reports\\harness_runs\\samplereverse_exact1_projected_vs_neighbor_20260424` with status `invalid_or_incomplete` and reason `case_results_directory_absent`.
- `task_packet.json` currently advances to `prepare_reverse_solving_from_selected_fallback_evidence`; this should be changed to a bounded engineering repair action unless the stricter classifier finds sufficient evidence.
- `task_packet.json` remains advisory; this `decision_packet.md` is the current execution authority.
- `artifact_index.json` contains many stale/missing artifacts; stale/missing artifacts must not be promoted to current.
- Negative results still block blind search, beam/budget expansion, stale hook reuse, full `solve_reports/` scanning, and repeated failed probe directions.
- Existing IDA/Ghidra/debugger/solver/harness interfaces are not in scope for modification in this engineering repair round.

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
- `tests/test_harness_artifact_manifest.py`, only if directly affected by compatibility.

Allowed bounded fallback evidence inspection:

- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
- Directory existence and filenames under `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/`
- The single selected fallback case-result JSON file, if exactly one exists, limited to metadata fields such as `case_id`, `input_value`, `resolved_path`, `status`, `matched_expected`, `candidate_count`, `structured_evidence_count`, `tool_artifact_count`, `validation_count`, `artifact_manifest`, and related provenance/status fields.
- Artifact manifest entries referenced by that case result, but only metadata already embedded in the case result. Do not open every tool artifact payload unless the case-result metadata is insufficient to classify readiness.

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm the previous round is consumed/archived and report/decision matched.
4. Inspect the readiness classifier logic in `reverse_agent/project_state.py`.
5. Tighten the fallback readiness classifier so any of the following prevents `fallback_evidence_ready_for_reverse_decision` unless a future explicit allowlist/override says otherwise:
   - case result `status` is `not_found`;
   - summary has `not_found_cases > 0`;
   - embedded artifact manifest classification is `instrumentation_incomplete`;
   - `validation_count == 0` when the classifier rationale claims the fallback is sufficient as evidence for a reverse-solving decision.
6. Reclassify the current selected fallback as `fallback_evidence_incomplete` or `fallback_evidence_stale_or_untrusted`; prefer `fallback_evidence_incomplete` if the metadata is present but instrumentation is incomplete.
7. Set `model_gate.json` `next_local_action` and `task_packet.json` `task` / `derived_task` to `repair_selected_fallback_evidence` or an equivalent bounded engineering repair action.
8. Preserve `selected_harness_evidence_source` provenance, run name/path, summary path, manifest path, latest invalid run, and fallback selection role.
9. Preserve the latest invalid run record separately; do not overwrite it with the fallback.
10. Add focused regression tests proving `status: not_found` plus `instrumentation_incomplete` is not classified as ready.
11. Keep or add a positive ready-path test, but make ready require non-`not_found` case status and non-incomplete artifact classification.
12. Ensure no stale/missing artifact is promoted to current.
13. Ensure no sample/tool/debugger/solver/probe/IDA/Ghidra execution occurred.
14. Update live `project_state/pytest_result.txt` with exact command outputs.
15. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
16. Archive this round after live report/test/state files are updated.
17. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to stricter selected fallback evidence readiness classification, project-state output fields, and status/lint display if needed.
- `tests/test_project_state.py`, limited to focused regression tests for strict selected fallback evidence readiness classification.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by metadata compatibility.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_repair_selected_fallback_readiness_strictness_v1/*`, minimal archive only

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_repair_selected_fallback_readiness_strictness_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Current fallback with `status: not_found` is not classified ready.
- Embedded `instrumentation_incomplete` prevents ready classification.
- `summary.not_found_cases > 0` prevents ready classification.
- `validation_count == 0` prevents a ready classification when readiness rationale claims enough evidence for reverse decision.
- Current selected fallback is classified as `fallback_evidence_incomplete` or `fallback_evidence_stale_or_untrusted`, preferably incomplete.
- `model_gate.json` / `task_packet.json` advance to `repair_selected_fallback_evidence` or equivalent bounded engineering repair action.
- Fallback remains selected fallback evidence, not latest/current evidence.
- Latest invalid harness run remains separately recorded as invalid/incomplete.
- Focused regression tests cover both negative strictness and positive ready path.
- `python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q` passes.
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

- Strict readiness classification requires running a sample binary.
- Strict readiness classification requires running the harness on a sample.
- Strict readiness classification requires solver/search/candidate generation/candidate validation.
- Strict readiness classification requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Strict readiness classification requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent incomplete readiness without breaking existing state consumers.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into direct reverse solving, candidate generation, runtime validation, or debugger work.
