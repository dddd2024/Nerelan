```json decision_meta
{"schema_version":1,"decision_id":"decision_20260609_reconcile_post_build_state_and_report_v1","round_id":"round_20260609_reconcile_post_build_state_and_report_v1","based_on_state_build_id":"state_20260609_145049_7ee702d3b2b6","based_on_state_digest":"7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the post-build project-state/report mismatch introduced by `decision_20260609_refresh_project_state_handoff_v1`.

The previous round successfully ran `python -m reverse_agent.project_state build` and refreshed `current_state.json`, `task_packet.json`, `artifact_index.json`, `model_gate.json`, and `negative_results.json`, but it did not finish the consistency loop. After the build, `lint-decision` and `lint-report` failed because the active decision still referenced the old state digest and the report/pytest evidence still mismatched the current decision/round.

This is an `engineering_branch` repair round only. The goal is to reconcile `decision_packet.md`, `codex_execution_report.md`, and `pytest_result.txt` against the current post-build state without rerunning build unless a status/lint command explicitly requires it.

## 2. Current Evidence

- Current `current_state.json` has `state_build_id=state_20260609_145049_7ee702d3b2b6`.
- Current `current_state.json` has `state_digest=7ee702d3b2b6e31ff52b17c9d74ecc21ccb6ee0a81c88a8d526458985b4b0153`.
- Current `current_state.json` still has `profile=samplereverse`, `sample=samplereverse`, `round_id=round_20260609_145049`, and `workflow_status=REPORT_AVAILABLE`.
- Current `task_packet.json` is refreshed to the same new digest but remains advisory only.
- Current `task_packet.json` still carries old samplereverse reverse-solving context such as `active_strategy=CompareAwareSearchStrategy` and `derived_task=collect_missing_evidence`; this must not override the decision packet.
- Current `artifact_index.json` was refreshed and still marks old reverse-solving artifacts as stale; do not promote them.
- Previous `pytest_result.txt` records `lint-decision: FAILED` after build because the old decision digest no longer matched current state.
- Previous `pytest_result.txt` records `lint-report: FAILED` after build because report ID/round ID still pointed to the wrong decision/round.
- Previous `codex_execution_report.md` incorrectly marked the round `SUCCESS / ACCEPTED` despite the post-build lint failures.
- `.codex-skills/registry.json` confirms `reverse-agent-iteration@v2` and `samplereverse-frontier@v2` are active.
- No reverse-solving, debugger, runtime probe, external reverse tool, or sample execution is required.

## 3. Do Not Do

- Do not run samples.
- Do not execute `Cpp2.exe` or any other sample binary.
- Do not run OllyDbg, x64dbg, IDA, Ghidra, Frida, emulator, debugger, hook, sidecar, winpty, runtime probe, or console validator.
- Do not run solver/search/candidate generation/candidate validation/beam expansion/budget expansion/topN expansion.
- Do not run compare-aware search or old sample_solver blind search.
- Do not read or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver code, runtime probe code, reverse tool integration behavior, sample binaries, sample metadata, training status, or status overlay.
- Do not promote stale artifacts as current evidence.
- Do not hand-edit reverse-solving conclusions.
- Do not mark report `SUCCESS` unless final `lint-decision`, `lint-report`, and pytest all pass.
- Do not rerun `python -m reverse_agent.project_state build` unless a status/lint command explicitly shows it is necessary; the known current state is already the post-build state.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`

Optional, bounded:

- `project_state/model_gate.json`
- `project_state/rounds/round_20260609_refresh_project_state_handoff_v1/round_manifest.json`, if present
- project-state CLI help only if required to identify the correct lint/status/report validation command

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is based on `state_20260609_145049_7ee702d3b2b6`.
2. Confirm `decision_meta.based_on_state_digest` equals the current `current_state.state_digest`.
3. Confirm `decision_meta.status == APPROVED`.
4. Confirm `decision_meta.mainline == engineering_branch`.
5. Confirm both skill profiles are active:
   - `reverse-agent-iteration@v2`
   - `samplereverse-frontier@v2`
6. Confirm `task_packet.json` is advisory only and does not control this round.
7. Confirm stale artifacts in `artifact_index.json` remain stale and are not promoted as current evidence.
8. Confirm no negative-result direction was repeated.
9. Update `codex_execution_report.md` to this decision/round only.
10. Update `pytest_result.txt` with this round's real command outputs.
11. Ensure report status is not `SUCCESS` unless all final checks pass.
12. Confirm no sample/tool/debugger/solver/probe execution occurred.
13. Confirm no `.codex-skills/` changes occurred.
14. Confirm no source-code changes occurred unless a project-state lint/report bug blocks reconciliation; if source changes are required, stop and report `BLOCKED`.

## 6. Implementation Scope

Allowed changes:

1. `project_state/decision_packet.md`, only to preserve this active repair packet if formatting normalization is required.
2. `project_state/codex_execution_report.md`, updated to report this round's real outcome.
3. `project_state/pytest_result.txt`, updated with this round's exact command outputs.
4. `project_state/rounds/round_20260609_reconcile_post_build_state_and_report_v1/round_manifest.json`, only if existing archive tooling is used after report/test consistency is achieved.

Disallowed changes:

- source modules unrelated to project-state report/lint consistency
- `.codex-skills/`
- solver/search/runtime/debugger/tool execution code
- sample binaries
- sample metadata
- training status
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- hand edits to reverse-solving conclusions in `current_state`, `task_packet`, or `artifact_index`

## 7. Tests

Run and record exact outputs:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py -q
```

Acceptance requirements:

- `lint-decision: OK`.
- `lint-report: OK`.
- pytest passes.
- `pytest_result.txt` matches this round's report.
- `codex_execution_report.md` matches this decision and round.
- report status reflects the real command results.
- no sample execution, reverse tool launch, solver run, runtime probe, or full `solve_reports/` read occurred.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if:

- `lint-decision` fails.
- `lint-report` fails.
- pytest fails.
- report/decision/pytest_result IDs do not match.
- fixing the mismatch requires source-code changes.
- fixing the mismatch requires running samples, reverse tools, runtime probes, or solver/search.
- fixing the mismatch requires hand-editing reverse-solving conclusions.
- `.codex-skills/` modification is required.
- the task shifts from `engineering_branch` into `reverse_solving`, `tool_integration`, or `training_dataset`.
