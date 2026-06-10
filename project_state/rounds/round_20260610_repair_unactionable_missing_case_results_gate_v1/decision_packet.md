```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_unactionable_missing_case_results_gate_v1","round_id":"round_20260610_repair_unactionable_missing_case_results_gate_v1","based_on_state_build_id":"state_20260610_043358_c568aa84f77a","based_on_state_digest":"c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the unactionable project-state gate for `latest harness case has errors` when the selected harness run has `case_results/` missing.

This round must make the model-gate/status output actionable. The current gate says `next_local_action: inspect_failed_case_result`, but `harness_diagnostics.case_results_missing == true`, `case_results_count == 0`, `summary_executed_cases == 0`, `summary_resumed_cases == 1`, and `summary_error_cases == 1`. There is no failed case-result file to inspect. Codex must either repair the gate/next-action classification or prove that an existing code path already supports the correct behavior and only stale generated state needs rebuilding.

This is an `engineering_branch` state/diagnostic repair round. Do not continue reverse solving. Do not run samples, solvers, probes, debuggers, IDA/Ghidra, or external reverse tools. Current execution authority is this `project_state/decision_packet.md`; `task_packet.json` remains advisory only.

## 2. Current Evidence

- Current state build is `state_20260610_043358_c568aa84f77a` with digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
- Previous repair round `decision_20260610_repair_report_archive_and_status_evidence_v1` was accepted with limitations. Its final status showed:
  - `decision_report_id_match: True`
  - `decision_consumed_by_report: True`
  - `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`
  - `decision_ready_for_execution: False`
  - `archive_status: archived`
- `project_state/model_gate.json` currently reports:
  - `reason: latest harness case has errors`
  - `next_local_action: inspect_failed_case_result`
  - `missing_evidence: []`
  - `should_call_model: false`
  - `harness_diagnostics.diagnosis: case_results_directory_absent`
  - `harness_diagnostics.latest_harness_run: solve_reports\\harness_runs\\samplereverse_exact1_projected_vs_neighbor_20260424`
  - `harness_diagnostics.case_results_missing: true`
  - `harness_diagnostics.case_results_count: 0`
  - `harness_diagnostics.summary_total_cases: 1`
  - `harness_diagnostics.summary_executed_cases: 0`
  - `harness_diagnostics.summary_resumed_cases: 1`
  - `harness_diagnostics.summary_error_cases: 1`
- This makes the current `next_local_action` non-actionable: it asks Codex to inspect a failed case-result even though no `case_results/` directory exists.
- `artifact_index.json` was generated at `2026-06-10T04:33:53Z` and still contains stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `latest_artifacts_v2` entries such as Base64/RC4, compare probes, bridge, SMT, and related artifacts are stale or missing unless explicitly marked current. They can be used only as historical context, not as current proof.
- `negative_results.json` still blocks old `sample_solver` blind search, pure beam/budget expansion, compare_semantics_agree=false frontiers, full `solve_reports` commits, repeated Base64/RC4 breakpoint probes before required gates, and several stale hook/probe directions.
- Existing relevant capability is `reverse_agent/project_state.py` plus `tests/test_project_state.py` and harness artifact manifest tests. Do not duplicate state builder, harness, IDA/Ghidra/debugger, or solver interfaces.
- Mature reverse tools may exist in the project, but this round must not run or alter IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, sidecar, solver, runtime probe, or sample execution code.

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
- Do not read or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not hand-edit reverse-solving conclusions in `current_state.json`, `task_packet.json`, or `artifact_index.json`; if these files need refresh, use existing project-state build commands.
- Do not solve the `samplereverse` sample in this round.

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
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Bounded harness metadata only, if needed to verify the missing-case-results diagnosis:

- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/run_manifest.json`, if present
- `solve_reports/harness_runs/samplereverse_exact1_projected_vs_neighbor_20260424/summary.json`, if present

Optional bounded files only if a focused failing test requires them:

- `reverse_agent/harness.py`
- `tests/test_tool_runners.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260610_043358_c568aa84f77a` and digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `task_packet.json` is advisory only and this decision controls the round.
5. Re-run `python -m reverse_agent.project_state status --state-dir project_state` before changes and capture the pre-repair output.
6. Verify whether `next_local_action: inspect_failed_case_result` is emitted while `harness_diagnostics.case_results_missing == true` and no concrete failed case-result path exists.
7. Inspect existing `reverse_agent/project_state.py` logic that builds `model_gate.json`, `task_packet.json`, and status output. Do not create a duplicate state-builder path.
8. Implement the smallest backward-compatible fix so a missing `case_results/` harness error is not surfaced as an instruction to inspect a non-existent failed case result.
9. The repaired output must either:
   - set a more accurate actionable next action, such as selecting/rebuilding a valid harness run or repairing the incomplete harness artifact; or
   - include a concrete existing case-result path if it still asks to inspect a failed case result.
10. Preserve the existing `harness_diagnostics` fields; downstream consumers that ignore them must keep working.
11. Add or update a focused regression test proving the missing `case_results/` condition does not produce an unactionable `inspect_failed_case_result` instruction.
12. If generated state files are refreshed, use existing project-state commands only. Do not hand-edit reverse-solving conclusions.
13. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
14. Ensure no sample/tool/debugger/solver/probe execution occurred.
15. Ensure no `.codex-skills/` changes occurred.
16. Update `project_state/codex_execution_report.md` with a valid `codex_report_summary` for this decision.
17. Update `project_state/pytest_result.txt` with exact command outputs for this round.
18. Archive this round using existing project-state archive tooling only after report/test consistency is achieved.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `reverse_agent/project_state.py`
2. `tests/test_project_state.py`
3. `tests/test_harness_artifact_manifest.py`, only if project-state/harness manifest behavior is directly affected

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, and `project_state/model_gate.json` only if regenerated by existing project-state build/status tooling
4. `project_state/rounds/round_20260610_repair_unactionable_missing_case_results_gate_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

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
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
```

If `reverse_agent/project_state.py` changes, also run and record:

```bash
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
```

If tool-runner compatibility is touched unexpectedly, also run and record:

```bash
python -m pytest tests/test_tool_runners.py -q
```

If state files are regenerated, also run and record:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
```

Acceptance requirements:

- `lint-decision: OK`
- `lint-report: OK` after report update
- pytest passes for all tests run
- A focused test covers the missing-`case_results/` gate behavior
- The final status/model-gate output no longer directs Codex to inspect a failed case result unless a concrete existing failed case-result path is available
- `harness_diagnostics.diagnosis == case_results_directory_absent` remains visible for this failure mode
- No stale/missing artifact is promoted to current
- No candidate/search/runtime/debugger/sample execution occurred
- No `.codex-skills/` modification occurred
- Any source change is minimal, tested, and limited to project-state diagnostics/actionability

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Fixing the gate requires executing samples or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation, candidate validation, solver/search expansion, runtime probe, debugger work, or tool execution.
- pytest fails outside the project-state/report evidence area.
- Fixing requires broad refactor beyond project-state diagnostics/actionability.
- Fixing requires `.codex-skills/` modification.
- `lint-decision` fails.
- `lint-report` fails after report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
