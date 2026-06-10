```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_reconcile_harness_diagnostics_report_evidence_v1","round_id":"round_20260610_reconcile_harness_diagnostics_report_evidence_v1","based_on_state_build_id":"state_20260610_043358_c568aa84f77a","based_on_state_digest":"c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Reconcile the evidence records for `decision_20260610_audit_latest_failed_harness_case_state_gap_v1`.

Do not redo reverse solving. Do not rerun samples or tools. The existing `harness_diagnostics` implementation appears directionally correct; this round is to fix report/test/state evidence inconsistencies and add a focused regression test if missing.

This is an `engineering_branch` evidence-reconciliation round. Current task authority is this `project_state/decision_packet.md`; `task_packet.json` remains advisory.

## 2. Current Evidence

- Current state build is `state_20260610_043358_c568aa84f77a` with digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
- Previous round decision was `decision_20260610_audit_latest_failed_harness_case_state_gap_v1`.
- Previous round report was `report_20260610_audit_latest_failed_harness_case_state_gap_v1` with status `SUCCESS` and acceptance recommendation `ACCEPTED`.
- Previous round added `harness_diagnostics` to explain `latest harness case has errors`.
- The reported root cause is `case_results_directory_absent` for `samplereverse_exact1_projected_vs_neighbor_20260424`.
- `pytest_result.txt` currently contains inconsistent status fields:
  - `decision_report_id_match: True`
  - `decision_consumed_by_report: False`
  - `decision_execution_state: READY_FOR_EXECUTION`
- `pytest_result.txt` also points `round_manifest_path` to the previous `round_20260609_reconcile_material_schema_report_ids_v1`, while the current round archive exists under `round_20260610_audit_latest_failed_harness_case_state_gap_v1`.
- The previous decision body had stale state evidence from `state_20260609_145049_7ee702d3b2b6` even though its `decision_meta` had been updated to `state_20260610_043358_c568aa84f77a`.
- `codex_execution_report.md.files_changed` does not fully account for dynamic state files and round archive outputs from the previous round.
- `artifact_index.json` still contains stale/missing artifacts; stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, pure beam/budget expansion, repeated blocked probes, stale hook reuse, and full `solve_reports` commits.
- Existing relevant implementation is `reverse_agent/project_state.py`; do not duplicate state, tool, IDA, Ghidra, debugger, solver, or harness interfaces.
- Mature reverse tools may exist in the project, but this round must not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, sidecar, solver, runtime probe, or sample binaries.

## 3. Do Not Do

- Do not run any sample binary.
- Do not launch IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, winpty, sidecar, runtime probe, solver, or console validator.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, solver validation, or candidate ranking.
- Do not generate, mutate, rank, validate, or promote candidates or flags.
- Do not treat stale or missing artifacts as current evidence.
- Do not promote any artifact merely because it appears in `latest_artifacts`; use `latest_artifacts_v2.freshness` and provenance.
- Do not repeat any `negative_results.json` blocked direction.
- Do not modify `.codex-skills/`.
- Do not change solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/OllyDbg/x64dbg interfaces.
- Do not modify material evidence schema or tool runners.
- Do not modify `harness_diagnostics` logic unless a focused test proves it is wrong.
- Do not read or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not hand-edit reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`; if these files need refresh, use existing project-state build commands.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `project_state/rounds/round_20260610_audit_latest_failed_harness_case_state_gap_v1/round_manifest.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Optional bounded files only if directly required by a failing test:

- `tests/test_tool_runners.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260610_043358_c568aa84f77a` and digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `task_packet.json` is advisory only and this decision controls the round.
5. Explain why the previous `status` output showed `decision_report_id_match=True` but `decision_execution_state=READY_FOR_EXECUTION`.
6. Regenerate or correct `project_state/pytest_result.txt` so detailed outputs correspond to the current report/round and no longer show the stale previous-round `round_manifest_path` for the active report.
7. Ensure `round_manifest_path` points to the active report round when the current report is being linted.
8. Update `project_state/codex_execution_report.md.files_changed` or equivalent report sections to include dynamic state files and archive files, or explicitly separate:
   - `source_files_changed`
   - `state_files_regenerated`
   - `archived_files`
9. Add or identify a focused automated test asserting `harness_diagnostics.diagnosis == "case_results_directory_absent"` when the latest summary reports errors and `case_results/` is absent.
10. Preserve backward compatibility for existing consumers that ignore `harness_diagnostics`.
11. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
12. Ensure no sample/tool/debugger/solver/probe execution occurred.
13. Ensure no `.codex-skills/` changes occurred.
14. Update `project_state/codex_execution_report.md` with a valid `codex_report_summary` for this decision.
15. Update `project_state/pytest_result.txt` with exact command outputs for this round.
16. Archive this rework round using existing project-state archive tooling only after report/test consistency is achieved.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `tests/test_project_state.py` if a focused regression test is missing
2. `reverse_agent/project_state.py` only if the focused regression test reveals a real bug

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/decision_packet.md` only to reconcile stale body metadata with current `decision_meta`
4. `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, and `project_state/model_gate.json` only if regenerated by `python -m reverse_agent.project_state build`
5. `project_state/rounds/round_20260610_reconcile_harness_diagnostics_report_evidence_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/OllyDbg/x64dbg interface code
- material evidence schema or tool runner continuation
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_tool_runners.py -q
python -m reverse_agent.project_state lint-report
```

If state files are regenerated, also run and record:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
```

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK` after report update
- pytest passes for all tests run
- `pytest_result.txt` detailed status output corresponds to this active report/round
- `round_manifest_path` no longer points to an unrelated previous round for the active report
- A focused regression test exists for `harness_diagnostics.diagnosis == "case_results_directory_absent"`
- No stale/missing artifact is promoted to current
- No candidate/search/runtime/debugger/sample execution occurred
- No `.codex-skills/` modification occurred
- Any source change is minimal, tested, and limited to project-state diagnostics/report evidence consistency

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Fixing the evidence mismatch requires executing samples or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation, candidate validation, solver/search expansion, runtime probe, debugger work, or tool execution.
- pytest fails outside the project-state/report evidence area.
- Fixing requires broad refactor beyond project-state diagnostics/report evidence consistency.
- Fixing requires `.codex-skills/` modification.
- `lint-decision` fails.
- `lint-report` fails after report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```