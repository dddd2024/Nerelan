```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_audit_latest_failed_harness_case_state_gap_v1","round_id":"round_20260610_audit_latest_failed_harness_case_state_gap_v1","based_on_state_build_id":"state_20260610_043358_c568aa84f77a","based_on_state_digest":"c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Audit and repair the state gap behind `latest harness case has errors` / missing `case_results` before any further reverse-solving work.

The previous reconcile round repaired report/pytest ID consistency and is accepted with the known limitation that `pytest_result.txt` keeps an explicitly labeled pre-repair diagnostic block containing old IDs. Treat the final post-repair `lint-report: OK` and the top-level pytest summary as current.

This round is an `engineering_branch` diagnostic/repair round. Its purpose is to make the project state actionable again by identifying why the latest harness run is selected but `case_results` is missing or unusable, and by adding a minimal, schema-compatible state diagnostic if the current state builder hides the actual root cause.

Do not continue reverse solving, candidate search, debugger work, runtime probing, material-probe execution, or sample execution in this round.

## 2. Current Evidence

- Current state build is `state_20260609_145049_7ee702d3b2b6` with digest `7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
- `task_packet.json` is advisory only. This `decision_packet.md` controls the current round.
- `task_packet.json` reports:
  - `derived_task`: `collect_missing_evidence`
  - `next_local_action`: `inspect_failed_case_result`
  - `reason`: `latest harness case has errors`
  - `missing_evidence`: `[]`
  - `execution_scope`: `decision_packet_controls_current_round`
- `pytest_result.txt` from the previous repair round shows final `lint-decision: OK`, final `lint-report: OK`, and `175 passed` for `tests/test_tool_runners.py tests/test_project_state.py`.
- `artifact_index.json` was generated at `2026-06-09T14:50:43Z`; `latest_artifacts_v2` contains stale and missing artifacts. Stale/missing artifacts must not be promoted to current evidence.
- `artifact_index.json` includes missing legacy keys such as `compare_handoff_probe`, `compare_stack_pivot_probe`, and `smt_validation`; these are not current proof.
- Current best candidates exist in state, but they are not enough to justify direct candidate expansion because artifact freshness is stale/missing and negative results block repeated search expansion.
- `negative_results.json` blocks old sample_solver blind search, pure beam/budget expansion, compare_semantics_agree=false frontiers, full solve_reports commits, repeated Base64/RC4 breakpoint probes before required gates, and several stale hook/probe directions.
- `.codex-skills/registry.json` confirms both required skill profiles are active:
  - `reverse-agent-iteration@v2`
  - `samplereverse-frontier@v2`
- Existing project capabilities include `reverse_agent/project_state.py`, harness artifact manifest tests, IDA/OllyDbg/tool-runner integration, and the recently added Base64/RC4/UTF-16LE material evidence ingestion. Do not duplicate these interfaces.
- Mature reverse tools may exist in the project, but this round must not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, sidecar, solver, or sample binaries.
- Bounded reading of the single latest failed harness run metadata is allowed only to diagnose state selection and `case_results` absence. Full `solve_reports/` traversal remains disallowed.

## 3. Do Not Do

- Do not run any sample binary.
- Do not launch IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, winpty, sidecar, runtime probe, or console validator.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, solver validation, or candidate ranking.
- Do not generate, mutate, validate, or promote candidates or flags.
- Do not treat stale or missing artifacts as current evidence.
- Do not promote any artifact merely because it is in `latest_artifacts`; use `latest_artifacts_v2.freshness` and provenance.
- Do not repeat any `negative_results.json` blocked direction unless a new, explicit evidence reason is recorded.
- Do not modify `.codex-skills/`.
- Do not modify material evidence schema or tool runners unless a directly failing project-state test proves a minimal compatibility issue. This round should not continue the previous material-schema implementation.
- Do not add duplicate IDA/Ghidra/debugger/tool-runner interfaces.
- Do not read or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not hand-edit reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`; if these files need refresh, use the existing project-state build command.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Bounded latest-run metadata only:

- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present
- The minimal `case_results` path or error file named by that run's manifest/summary, if present

Optional bounded files only if directly required by the failing state/harness manifest test:

- `reverse_agent/harness.py`
- `reverse_agent/pipeline.py`
- `tests/test_pipeline.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260609_145049_7ee702d3b2b6` and digest `7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `task_packet.json` is advisory only and this decision controls the round.
5. Re-run `python -m reverse_agent.project_state status` before changes and capture the actual status output.
6. Inspect the bounded latest harness run metadata for `samplereverse_exact1_projected_vs_neighbor_20260424` and identify whether `case_results` is absent, malformed, failed, or simply not surfaced by `project_state` diagnostics.
7. Determine whether the root cause is:
   - a real failed/unusable harness artifact that should stay stale/missing;
   - a project-state builder diagnostic gap;
   - an artifact manifest parsing bug;
   - or insufficient local files requiring a rebuild outside this round.
8. If it is a state-builder or manifest diagnostic bug, implement the smallest schema-compatible fix in `reverse_agent/project_state.py` and tests.
9. If it is a real failed/unusable artifact, do not change source code. Record a precise `BLOCKED` or `SUCCESS_WITH_DIAGNOSTIC` report explaining the next required evidence-producing action.
10. If dynamic state files are regenerated, use only `python -m reverse_agent.project_state build`; do not hand-edit reverse-solving conclusions.
11. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
12. Ensure no sample/tool/debugger/solver/probe execution occurred.
13. Ensure no `.codex-skills/` changes occurred.
14. Update `project_state/codex_execution_report.md` with a valid `codex_report_summary` for this decision.
15. Update `project_state/pytest_result.txt` with exact command outputs for this round.
16. Archive this round using existing project-state archive tooling only after report/test consistency is achieved.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `reverse_agent/project_state.py`
2. `tests/test_project_state.py`
3. `tests/test_harness_artifact_manifest.py`

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/current_state.json`, `project_state/task_packet.json`, and `project_state/artifact_index.json` only if regenerated by `python -m reverse_agent.project_state build`
4. `project_state/rounds/round_20260610_audit_latest_failed_harness_case_state_gap_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

Allowed diagnostic output:

- A bounded diagnostic field or message that explains the selected latest harness run's case-result status, without embedding bulky solve-report content.
- Backward-compatible fields only. Existing consumers must keep working if the new field is absent.

Disallowed changes:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/OllyDbg/x64dbg interface duplication
- material evidence schema continuation
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
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
```

If `reverse_agent/project_state.py` changes affect broader status/report behavior, also run:

```bash
python -m pytest tests/test_tool_runners.py -q
```

If dynamic state files are regenerated, run:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
```

After updating `project_state/codex_execution_report.md` and `project_state/pytest_result.txt`, run and record:

```bash
python -m reverse_agent.project_state lint-report
```

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK` after report update
- pytest passes for all tests run
- The report identifies the latest harness case-results state precisely
- No stale/missing artifact is promoted to current
- No candidate/search/runtime/debugger/sample execution occurred
- No `.codex-skills/` modification occurred
- Any source change is minimal, tested, and limited to project-state diagnostics or manifest parsing

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- The latest harness run metadata needed for diagnosis is absent locally.
- Diagnosis requires reading full `solve_reports/`.
- Diagnosis requires executing a sample binary, external reverse tool, debugger, emulator, hook, sidecar, runtime probe, or solver.
- The only apparent next step is candidate expansion, brute force, or repeated blocked probe/search direction.
- Fixing requires broad refactor beyond project-state diagnostics/manifest parsing.
- Fixing requires `.codex-skills/` modification.
- `lint-decision` fails.
- pytest fails and cannot be fixed with a minimal in-scope change.
- `lint-report` fails after report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```