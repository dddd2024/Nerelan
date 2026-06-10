```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_materialize_selected_fallback_harness_evidence_v1","round_id":"round_20260610_materialize_selected_fallback_harness_evidence_v1","based_on_state_build_id":"state_20260610_092202_cf5553b58360","based_on_state_digest":"cf5553b58360ccffd52bd86599f0ae6f0743a9ae4df5258a04fb45690c87f2a8","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Materialize the selected fallback harness run as an explicit project-state evidence source.

The previous round resolved the generic `repair_harness_artifact` state into `select_fallback_harness_run`. Current live `model_gate.json` already identifies a fallback run, but the project still needs a schema-compatible way to record that fallback selection in live state so later reverse-solving rounds can use the fallback evidence without silently promoting it to the latest/current run.

This is an `engineering_branch` state-materialization round. It must not start reverse solving, run samples, run harness execution, or validate candidates.

## 2. Current Evidence

- Current state anchor: `state_20260610_092202_cf5553b58360` with digest `cf5553b58360ccffd52bd86599f0ae6f0743a9ae4df5258a04fb45690c87f2a8`.
- Current `model_gate.json` reports `harness_diagnostics.case_results_missing: true` for latest run `solve_reports\harness_runs\samplereverse_exact1_projected_vs_neighbor_20260424`.
- Current `model_gate.json` reports `harness_diagnostics.latest_harness_run_status: invalid_or_incomplete`.
- Current `model_gate.json` reports `harness_diagnostics.fallback_available: true`.
- Current `model_gate.json` reports `harness_diagnostics.fallback_harness_run.run_name: sr_arg0_hook_readiness_ordering_20260526_r1`.
- Current `model_gate.json` reports `harness_diagnostics.fallback_harness_run.provenance: fallback_from_invalid_latest_run`.
- Current `model_gate.json` reports `next_local_action: select_fallback_harness_run`.
- Current `task_packet.json` reports `task: select_fallback_harness_run`, `derived_task: select_fallback_harness_run`, and `next_local_action: select_fallback_harness_run`.
- The latest invalid run must remain visible as invalid/incomplete; the fallback run must not be silently promoted to latest/current.
- `artifact_index.json` may still include stale/missing artifacts; stale or missing artifacts must not be promoted to current.
- Existing project-state build/status/lint/archive logic lives in `reverse_agent/project_state.py`; extend that mechanism rather than duplicating it.
- Existing harness case-result manifest coverage exists in `tests/test_harness_artifact_manifest.py`; do not rewrite harness execution.
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
- Do not treat the latest run without `case_results/` as inspectable failed-case evidence.
- Do not create synthetic `case_results/`.
- Do not silently rewrite `latest_harness_run` to the fallback run.
- Do not open full fallback case-result payloads unless a minimal metadata field cannot be derived otherwise; prefer summary/run_manifest/case_results existence/count metadata.

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

Allowed bounded fallback metadata inspection:

- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- Directory existence/count metadata for `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/case_results/`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/summary.json`
- `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/run_manifest.json`
- Directory existence/count metadata for `solve_reports/harness_runs/sr_arg0_hook_readiness_ordering_20260526_r1/case_results/`

Do not inspect unrelated harness runs except if the existing tests require a temporary fixture. Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm live `model_gate.json` and `task_packet.json` currently request `select_fallback_harness_run`.
4. Identify the current project-state fields that describe latest harness run, fallback availability, artifact freshness, and task derivation.
5. Design the smallest schema-compatible live-state representation for selected fallback evidence. Acceptable naming includes an explicit block such as `selected_harness_evidence_source`, `fallback_evidence_source`, or equivalent.
6. The selected fallback evidence source must include at least:
   - `selection_role: fallback`
   - fallback run name/path
   - summary path
   - run manifest path if present
   - case_results path or case_results count metadata
   - provenance `fallback_from_invalid_latest_run`
   - latest invalid run name/path retained separately
   - reason that latest run remains invalid/incomplete
7. Ensure `latest_harness_run` remains the invalid latest run and is not silently overwritten.
8. Ensure artifact freshness semantics do not call the fallback run `current` unless explicitly scoped as fallback-selected evidence. Prefer a distinct freshness/provenance label instead of overloading `current`.
9. Update `model_gate.json`, `task_packet.json`, and/or `current_state.json` so downstream rounds can see that fallback selection has been materialized.
10. After materialization, set `next_local_action` / `task` to a bounded next action such as `inspect_selected_fallback_evidence` or an equivalent existing action, not back to `select_fallback_harness_run`.
11. Preserve backward compatibility for existing fields consumed by tests or UI.
12. Add or update focused tests that exercise the actual build path and assert that fallback selection is materialized into live state.
13. Run the required tests and record exact outputs in live `project_state/pytest_result.txt`.
14. Update live `project_state/codex_execution_report.md` with a valid `codex_report_summary` bound to this decision.
15. Archive this round after live report/test/state files are updated.
16. After archive, record final `lint-report` and `status` output showing the round is consumed and archived.
17. Ensure no sample/tool/debugger/solver/probe execution occurred.
18. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_state.py`, limited to materializing selected fallback harness evidence into project-state outputs and status/lint display.
- `tests/test_project_state.py`, limited to focused regression tests for build-path fallback evidence materialization.
- `tests/test_harness_artifact_manifest.py`, only if directly affected by fallback evidence metadata compatibility.

Allowed generated/report changes:

- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_materialize_selected_fallback_harness_evidence_v1/*`, minimal archive only

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_materialize_selected_fallback_harness_evidence_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Live state contains an explicit selected fallback evidence source block with provenance.
- The fallback evidence source references `sr_arg0_hook_readiness_ordering_20260526_r1` and its summary/run manifest/case_results metadata.
- The latest invalid harness run `samplereverse_exact1_projected_vs_neighbor_20260424` remains separately recorded as invalid/incomplete.
- Fallback is not silently promoted to latest/current run.
- Artifact freshness/provenance clearly distinguishes fallback-selected evidence from current latest run evidence.
- `model_gate.json` / `task_packet.json` advance beyond `select_fallback_harness_run` to a bounded next action such as `inspect_selected_fallback_evidence` or equivalent.
- `task_packet.json` must not revert to `collect_missing_evidence` for this condition.
- Focused regression tests cover the actual build path.
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

- Materializing fallback evidence requires running a sample binary.
- Materializing fallback evidence requires running the harness on a sample.
- Materializing fallback evidence requires solver/search/candidate generation/candidate validation.
- Materializing fallback evidence requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Materializing fallback evidence requires full `solve_reports/` traversal.
- No schema-compatible way exists to represent selected fallback evidence without breaking existing state consumers.
- `lint-report` fails after final report update.
- Final `status` cannot reach consumed/archived state.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```