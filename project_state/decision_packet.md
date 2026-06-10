```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_commit_restore_live_files_v1","round_id":"round_20260610_commit_restore_live_files_v1","based_on_state_build_id":"state_20260610_060844_d17fc0ba1c82","based_on_state_digest":"d17fc0ba1c823d328028914b3a019555162b7da63b9b03972bd4d555c8bae215","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Commit the restore repair into live `project_state`, not only into a round archive.

The previous submitted commit `41c92f611f67ef0b9cffa358849af48da5aeb3db` created `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/*`, but did not modify live `project_state/codex_execution_report.md`, live `project_state/pytest_result.txt`, live `project_state/model_gate.json`, live `project_state/current_state.json`, live `project_state/artifact_index.json`, or live `project_state/task_packet.json`.

This round is a narrow `engineering_branch` live-state correction round. Its sole goal is to make the live project-state files and final archive status match the active repair evidence. Do not create another archive-only commit.

## 2. Current Evidence

- Current uploaded decision before this one was `decision_20260610_restore_rebind_round_live_state_consistency_v1`.
- Git commit `41c92f611f67ef0b9cffa358849af48da5aeb3db` exists and its commit message claims restore was completed.
- Compare from `eb99c89020707f83f11d7e4955255aa109ed1ba3` to `41c92f611f67ef0b9cffa358849af48da5aeb3db` shows only four added files, all under `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/`.
- The previous commit did not modify live `project_state/codex_execution_report.md`, `pytest_result.txt`, `model_gate.json`, `current_state.json`, `artifact_index.json`, or `task_packet.json`.
- The archived restore report claims `files_changed` included live files, but the commit diff does not support that claim.
- Live `project_state/codex_execution_report.md` still points to `decision_20260610_repair_report_archive_and_status_evidence_v1`.
- Live `project_state/pytest_result.txt` still points to `decision_20260610_repair_report_archive_and_status_evidence_v1`.
- Live `project_state/model_gate.json` still has `harness_diagnostics.case_results_missing: true` and `next_local_action: inspect_failed_case_result`.
- Source code in `reverse_agent/project_state.py` already contains the intended mapping from missing `case_results/` to `next_local_action: repair_harness_artifact`; source code likely does not need changes.
- `artifact_index.json` still contains stale/missing artifacts. Stale or missing artifacts must not be promoted to current evidence.
- `negative_results.json` still blocks blind search, beam/budget expansion, compare_semantics_agree=false frontier promotion, full `solve_reports` commit, repeated stale probes, and stale hook reuse.
- Existing relevant capability is `reverse_agent/project_state.py` plus existing project-state build/status/lint/archive commands. Do not duplicate state builder, harness, IDA/Ghidra/debugger, or solver interfaces.

## 3. Do Not Do

- Do not create an archive-only commit.
- Do not update only `project_state/rounds/...` files.
- Do not run any sample binary.
- Do not run solver/search/candidate generation/candidate validation.
- Do not run runtime probe, debugger, emulator, hook, sidecar, IDA, Ghidra, OllyDbg, or x64dbg.
- Do not inspect full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify solver/search/runtime/debugger/probe code.
- Do not change IDA/Ghidra/debugger interfaces.
- Do not create another functional project-state feature.
- Do not hand-edit reverse-solving conclusions.
- Do not promote stale/missing artifacts to current.
- Do not solve the `samplereverse` sample in this round.

## 4. Files To Inspect

Required live files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/model_gate.json`
- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `tests/test_harness_artifact_manifest.py`

Required archive files for comparison only:

- `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/codex_execution_report.md`
- `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/pytest_result.txt`
- `project_state/rounds/round_20260610_restore_rebind_round_live_state_consistency_v1/round_manifest.json`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must:

1. Confirm the previous commit was archive-only by checking that live `project_state/codex_execution_report.md`, `pytest_result.txt`, `model_gate.json`, `current_state.json`, `artifact_index.json`, and `task_packet.json` were not modified in commit `41c92f611f67ef0b9cffa358849af48da5aeb3db`.
2. Confirm this decision packet is current execution authority and `task_packet.json` is advisory only.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm both skill profiles are active in `.codex-skills/registry.json`.
5. Run `python -m reverse_agent.project_state build` using existing project-state tooling.
6. Confirm live `project_state/model_gate.json` has `harness_diagnostics.case_results_missing == true` and `next_local_action == "repair_harness_artifact"` after build.
7. Update live `project_state/codex_execution_report.md` so `codex_report_summary.based_on_decision_id == decision_20260610_commit_restore_live_files_v1` and `round_id == round_20260610_commit_restore_live_files_v1`.
8. Update live `project_state/pytest_result.txt` so its summary decision/report/round IDs match this round and its body records exact command outputs.
9. Ensure the actual Git commit includes live project-state file changes, at minimum:
   - `project_state/codex_execution_report.md`
   - `project_state/pytest_result.txt`
   - `project_state/model_gate.json`
   - plus any regenerated `current_state.json`, `artifact_index.json`, or `task_packet.json` if build changes them.
10. Archive this round only after live report/test/state files are updated.
11. After archive, rerun or record final `lint-report` and `status` so the final recorded output reflects `round_manifest_present: True` and `archive_status: archived`.
12. Ensure final status shows:
    - `decision_report_id_match: True`
    - `decision_consumed_by_report: True`
    - `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`
    - `round_manifest_present: True`
    - `archive_status: archived`
13. Ensure the live report's `files_changed` accurately distinguishes:
    - `source_files_changed`
    - `state_files_regenerated`
    - `archived_files`
    - live report/test files changed
14. Do not claim live files changed unless they are actually part of the Git diff.
15. Do not change source code unless a focused test proves the existing `repair_harness_artifact` branch is broken.
16. Ensure stale/missing artifacts remain stale/missing unless the build tool has current provenance for a replacement artifact.
17. Ensure no sample/tool/debugger/solver/probe execution occurred.
18. Ensure no `.codex-skills/` changes occurred.

## 6. Implementation Scope

Allowed source changes only if needed:

1. `tests/test_project_state.py`, only if a targeted regression assertion is missing
2. `reverse_agent/project_state.py`, only if a focused test proves the existing `repair_harness_artifact` branch is broken
3. `tests/test_harness_artifact_manifest.py`, only if directly affected

Required live dynamic/report changes:

1. `project_state/codex_execution_report.md`
2. `project_state/pytest_result.txt`
3. `project_state/model_gate.json`, via `python -m reverse_agent.project_state build`
4. `project_state/current_state.json`, `project_state/task_packet.json`, and `project_state/artifact_index.json`, if regenerated by build tooling

Allowed archive changes:

- `project_state/rounds/round_20260610_commit_restore_live_files_v1/round_manifest.json`
- minimal archived `codex_execution_report.md`, `decision_packet.md`, `pytest_result.txt`

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

Run and record exact outputs in live `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state build
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state lint-decision --state-dir project_state
python -m pytest tests/test_project_state.py tests/test_harness_artifact_manifest.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

After archiving this round, record final outputs for:

```bash
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Also record a Git diff summary or file list proving live file changes are included, not only `project_state/rounds/...` files.

Acceptance requirements:

- `lint-report: OK` after live report update.
- pytest passes for all tests run.
- Live `model_gate.json` has `next_local_action: repair_harness_artifact` when `case_results_missing: true`.
- Live `codex_execution_report.md` matches this decision.
- Live `pytest_result.txt` matches this report.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True`.
- Final status shows `archive_status: archived`.
- The final Git diff includes live project-state file changes and is not archive-only.
- No stale/missing artifact is promoted to current.
- No sample/tool/debugger/solver/probe execution occurred.
- No `.codex-skills/` modification occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- The commit would again be archive-only.
- Live `model_gate.json` cannot be regenerated to `repair_harness_artifact`.
- Live report/pytest cannot be made to match this decision.
- Final status cannot be recorded after archive.
- Fixing requires sample execution or external reverse tools.
- Fixing requires full `solve_reports/` traversal.
- Fixing requires candidate generation or validation.
- Fixing requires runtime probe, debugger work, emulator, hook, sidecar, IDA, or Ghidra.
- Fixing requires broad refactor outside project-state report/build/gate consistency.
- `.codex-skills/` changes are required.
- `lint-report` fails after the final report update.
- The round shifts from `engineering_branch` into `reverse_solving`, tool execution, candidate generation, runtime validation, or debugger work.
```