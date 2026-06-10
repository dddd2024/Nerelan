```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_repair_report_archive_and_status_evidence_v1","round_id":"round_20260610_repair_report_archive_and_status_evidence_v1","based_on_state_build_id":"state_20260610_043358_c568aa84f77a","based_on_state_digest":"c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining report/archive/status evidence inconsistency after `decision_20260610_reconcile_harness_diagnostics_report_evidence_v1`.

This is an `engineering_branch` state-evidence repair round. Do not continue reverse solving. Do not rerun samples, solvers, probes, debuggers, IDA/Ghidra, or any external reverse tool. The purpose is to make the live `project_state` files internally consistent so a later GPT audit can decide whether the previous implementation is acceptable.

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` remains advisory.

## 2. Current Evidence

- Current state build is `state_20260610_043358_c568aa84f77a` with digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
- The previous active decision was `decision_20260610_reconcile_harness_diagnostics_report_evidence_v1`.
- `project_state/codex_execution_report.md` currently reports:
  - `report_id`: `report_20260610_reconcile_harness_diagnostics_report_evidence_v1`
  - `round_id`: `round_20260610_reconcile_harness_diagnostics_report_evidence_v1`
  - `based_on_decision_id`: `decision_20260610_reconcile_harness_diagnostics_report_evidence_v1`
  - `status`: `SUCCESS`
  - `acceptance_recommendation`: `ACCEPTED`
- `project_state/pytest_result.txt` top-level `pytest_result_summary` also uses the reconcile decision/report/round IDs and says `status: PASSED`.
- However, the detailed `python -m reverse_agent.project_state status` block inside `pytest_result.txt` still shows stale previous report/test identifiers:
  - `report_id: report_20260610_audit_latest_failed_harness_case_state_gap_v1`
  - `report_based_on_decision_id: decision_20260610_audit_latest_failed_harness_case_state_gap_v1`
  - `pytest_result_decision_id: decision_20260610_audit_latest_failed_harness_case_state_gap_v1`
  - `decision_report_id_match: False`
  - `decision_consumed_by_report: False`
  - `decision_execution_state: READY_FOR_EXECUTION`
- The later `python -m reverse_agent.project_state lint-report` block says the reconcile report now matches the reconcile decision and `pytest_result_matches_report: True`.
- The same later `lint-report` block still says:
  - `warning: report round not archived yet`
  - `round_manifest_present: False`
  - `archive_status: not_archived`
  - `round_manifest_path: project_state\\rounds\\round_20260610_reconcile_harness_diagnostics_report_evidence_v1\\round_manifest.json`
- `codex_execution_report.md` claims archived files exist for `round_20260610_reconcile_harness_diagnostics_report_evidence_v1`, but the recorded `lint-report` output says the round manifest is not present. This must be reconciled before acceptance.
- The existing `harness_diagnostics` behavior appears directionally correct and has a focused regression test named `tests/test_project_state.py::test_model_gate_diagnoses_summary_error_with_missing_case_results`.
- `artifact_index.json` still contains stale/missing artifacts; stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, pure beam/budget expansion, repeated blocked probes, stale hook reuse, and full `solve_reports` commits.
- Mature reverse tools and existing tool interfaces may exist in the project, but this round must not run or alter IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, hook, sidecar, solver, runtime probe, or sample execution code.

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
- `project_state/rounds/round_20260610_reconcile_harness_diagnostics_report_evidence_v1/round_manifest.json`, if present
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional bounded files only if a failing state/report/archive test requires them:

- `tests/test_harness_artifact_manifest.py`
- `tests/test_tool_runners.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260610_043358_c568aa84f77a` and digest `c568aa84f77a6d3a24679815a3d08efd360c70419e73194325effb77df392e50`.
2. Confirm `decision_meta.mainline == engineering_branch`.
3. Confirm both skill profiles are active in `.codex-skills/registry.json`.
4. Confirm `task_packet.json` is advisory only and this decision controls the round.
5. Explain why the current `pytest_result.txt` first `status` block still contains stale previous report/test IDs while the later `lint-report` block says the reconcile report matches.
6. Re-run `python -m reverse_agent.project_state status` after the live report and pytest result are updated, and ensure the recorded status block no longer shows stale `audit_latest_failed_harness_case_state_gap` report/test IDs for the active report.
7. Reconcile the archive claim: either create/archive `round_20260610_reconcile_harness_diagnostics_report_evidence_v1` with the expected manifest through existing project-state archive tooling, or correct the report so it does not claim archived files that `lint-report` cannot see.
8. Ensure `round_manifest_path` in recorded outputs points to the active report round and is consistent with whether the round is archived.
9. Update `project_state/codex_execution_report.md` with a valid `codex_report_summary` for this decision.
10. Update `project_state/pytest_result.txt` with exact command outputs for this round.
11. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
12. Ensure no sample/tool/debugger/solver/probe execution occurred.
13. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `reverse_agent/project_state.py` only if the stale status/archive mismatch is caused by a real project-state bug.
2. `tests/test_project_state.py` only if a focused regression test is needed for report/archive/status consistency.

Allowed dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/decision_packet.md` only if archiving this active decision requires copying it into the round archive
4. `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, and `project_state/model_gate.json` only if regenerated by `python -m reverse_agent.project_state build`
5. `project_state/rounds/round_20260610_repair_report_archive_and_status_evidence_v1/round_manifest.json` and minimal archived report/test/decision files, only via existing archive tooling

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
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py -q
```

If `reverse_agent/project_state.py` changes, also run and record:

```bash
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py tests/test_tool_runners.py -q
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
- `pytest_result.txt` detailed `status` block corresponds to this active report/round or is explicitly labeled as pre-repair diagnostic output and followed by a post-repair status block
- No stale previous report/test IDs are presented as the active post-repair state
- `round_manifest_path` and archive status are internally consistent
- No stale/missing artifact is promoted to current
- No candidate/search/runtime/debugger/sample execution occurred
- No `.codex-skills/` modification occurred
- Any source change is minimal, tested, and limited to project-state diagnostics/report/archive/status consistency

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Fixing the evidence mismatch requires executing samples or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation, candidate validation, solver/search expansion, runtime probe, debugger work, or tool execution.
- pytest fails outside the project-state/report evidence area.
- Fixing requires broad refactor beyond project-state diagnostics/report/archive/status consistency.
- Fixing requires `.codex-skills/` modification.
- `lint-decision` fails.
- `lint-report` fails after report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
