```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_refresh_project_state_handoff_v1","round_id":"round_20260609_refresh_project_state_handoff_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Perform a bounded project-state handoff refresh after the archive-governance chain has been accepted and archived.

The immediate goal is to make `project_state/task_packet.json`, `project_state/current_state.json`, `project_state/artifact_index.json`, `project_state/codex_execution_report.md`, and `project_state/pytest_result.txt` accurately reflect the current handoff state. The task is state governance only. It must not advance reverse solving, OllyDbg runtime readiness, cpp2 analysis, samplereverse search, or any solver/debugger/runtime-probe path.

## 2. Current Evidence

- The latest accepted archive-governance round is `round_20260609_archive_current_archive_round_and_rebuild_state_v1`.
- That round produced a matching `codex_execution_report.md`, `pytest_result.txt`, and `project_state/rounds/round_20260609_archive_current_archive_round_and_rebuild_state_v1/round_manifest.json`.
- The previous audit accepted that archive round with limitations because `current_state.json` and `task_packet.json` still point at old `samplereverse` sample-state context.
- `current_state.json` still reports `profile=samplereverse`, `sample=samplereverse`, `round_id=round_20260608_152003`, and `workflow_status=REPORT_AVAILABLE`.
- `task_packet.json` still reports `active_strategy=CompareAwareSearchStrategy` and `derived_task=Review bounded window discovery diagnostics` from old samplereverse reverse-solving context.
- `artifact_index.json` still contains many stale reverse-solving artifacts. Stale artifacts must remain stale unless existing project-state tooling recomputes their freshness with clear provenance.
- `negative_results.json` contains hard/soft blocks against repeating blind search, beam/budget-only expansion, compare_semantics_agree=false candidates, and full `solve_reports` commits.
- `.codex-skills/registry.json` lists `reverse-agent-iteration` and `samplereverse-frontier` as active version 2 profiles. This packet therefore uses `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
- `project_state/decision_packet.md` remains the execution authority. `task_packet.json`, `task_packet.task`, and derived task fields are advisory only.
- Existing project-state CLI/tooling should be used for refresh/build/status work. Do not hand-edit dynamic state if a project-state command already provides the operation.

## 3. Do Not Do

- Do not execute any sample binary.
- Do not run OllyDbg, x64dbg, IDA, Ghidra, Frida, emulator, debugger, hook, winpty, sidecar, runtime probe, or console validator.
- Do not generate, mutate, rank, or validate candidate inputs or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not inspect or commit full `solve_reports/`.
- Do not inspect full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not change solver code, runtime probe code, reverse tool integration behavior, sample binaries, sample metadata, training status, or status overlay.
- Do not mark OllyDbg/backend/runtime readiness as true.
- Do not promote stale artifacts as current evidence.
- Do not treat `task_packet.json` as execution authority.
- Do not compress the final report into un-auditable prose; it must include `codex_report_summary` and exact tests.

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
- `project_state/rounds/round_20260609_archive_current_archive_round_and_rebuild_state_v1/round_manifest.json`

Project-state CLI/code may be inspected only as needed to determine the correct existing refresh/build/status command:

- `reverse_agent/project_state*`
- project-state command entrypoints referenced by `python -m reverse_agent.project_state --help`
- project-state tests directly relevant to state refresh/report/lint behavior

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm both skill profiles resolve to active registry skills:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm the latest accepted archive round remains archived and its `round_manifest.json` exists.
7. Run the existing project-state status/build/refresh command that is appropriate for updating stale handoff metadata. Prefer an existing command such as `python -m reverse_agent.project_state build` or a documented refresh command. Do not invent a new CLI command in this round.
8. If a project-state build/refresh command updates `task_packet.json`, `current_state.json`, or `artifact_index.json`, verify that generated fields preserve provenance and legacy/v2 compatibility.
9. If no existing command can update the stale sample-state handoff safely, leave state files unchanged and mark the round `BLOCKED` or `SUCCESS_WITH_LIMITATIONS` in the report; do not hand-edit conclusions.
10. Confirm stale reverse-solving artifacts remain stale unless refreshed by an existing provenance-aware command.
11. Confirm no negative-result direction was repeated.
12. Confirm no external reverse tool, sample execution, solver, or runtime probe occurred.
13. Confirm no `.codex-skills/` changes occurred.
14. Confirm `codex_execution_report.md` for this round has `codex_report_summary`, matching `based_on_decision_id`, matching `round_id`, and truthful status.
15. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes are limited to engineering state files:

1. `project_state/task_packet.json`, only if updated by existing project-state build/refresh tooling.
2. `project_state/current_state.json`, only if updated by existing project-state build/refresh tooling.
3. `project_state/artifact_index.json`, only if updated by existing project-state build/refresh tooling and provenance/freshness fields remain explicit.
4. `project_state/codex_execution_report.md`, updated to report this round's real outcome.
5. `project_state/pytest_result.txt`, updated with this round's exact command outputs.
6. `project_state/rounds/round_20260609_refresh_project_state_handoff_v1/round_manifest.json`, if existing archive tooling is used after the report/test record is complete.
7. Other minimal project-state generated metadata files only if produced by existing project-state commands and directly related to handoff refresh.

Disallowed changes:

- source modules unrelated to project-state CLI/report/lint behavior
- `.codex-skills/`
- solver/search/runtime/debugger/tool execution code
- sample binaries
- sample metadata/training status/status overlay, unless an existing project-state build command updates a purely generated field with clear provenance
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`

If the refresh requires source-code changes or broad state migrations, stop and report `BLOCKED`; do not widen scope.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py -q
```

If `python -m reverse_agent.project_state build` is not the correct existing refresh command, inspect CLI help and use the documented existing command. Record the actual command used and the reason for substituting it.

Acceptance requirements:

- `lint-decision: OK`.
- `lint-report: OK` after the report is written.
- `pytest tests/test_project_state.py -q` passes.
- `pytest_result.txt` matches this round's report.
- The report clearly states whether `task_packet/current_state/artifact_index` were refreshed, unchanged, or blocked.
- No sample execution, reverse tool launch, solver run, runtime probe, or full `solve_reports/` read occurred.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- Existing project-state tooling cannot safely refresh the stale handoff metadata.
- Refresh requires launching external reverse tools or sample binaries.
- Refresh requires running solver/search/runtime probes.
- Refresh requires hand-editing solver conclusions or promoting stale artifacts without provenance.
- Refresh requires modifying `.codex-skills/`.
- `lint-decision` fails for this packet.
- `lint-report` fails after this round's report is written.
- pytest fails.
- `pytest_result.txt` cannot be updated with real output from this round.
- The task shifts from `engineering_branch` into `reverse_solving`, `tool_integration`, or `training_dataset`.
