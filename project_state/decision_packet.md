```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_archive_evidence_lint_report_record_v1","round_id":"round_20260609_fix_archive_evidence_lint_report_record_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the current evidence record mismatch: `project_state/pytest_result.txt` says `PASSED` while the recorded `lint-report` command failed. This round must produce a clean final `lint-report` after updating the report, or mark the round failed. Do not change archive contents.

This is an `engineering_branch` report/test-record repair round only. It must not advance `samplereverse`, `cpp2`, training samples, candidate generation, solver work, static extraction, runtime validation, or tool integration.

## 2. Current Evidence

- Active execution authority is `project_state/decision_packet.md`; `task_packet.json` remains advisory and still carries old sample-derived text such as `derived_task: Review bounded window discovery diagnostics`.
- Current report `report_20260609_archive_command_evidence_repair_v1` claims `SUCCESS` and `ACCEPTED`, but `project_state/pytest_result.txt` contains a failed `lint-report` output.
- The failed `lint-report` output reports `based_on_decision_id does not match current decision_id` and `report round_id does not match current decision round_id`; it was noted as expected before report update, but no final post-update `lint-report` success output was recorded.
- `pytest_result.txt` top summary says `status: PASSED`, which conflicts with the recorded failed `lint-report`. This is not acceptable evidence for a SUCCESS report.
- The previous archive-command safety classification is acceptable: `archive-round` was classified as `unsafe_may_overwrite_existing_archive`, and the mutating archive command was deliberately not rerun.
- `archive_round()` in `reverse_agent/project_state.py` returns no-op only when the existing manifest matches the new manifest; otherwise it raises `FileExistsError` and refuses overwrite. This supports not rerunning the mutating archive command against the already archived prior round.
- The prior repair archive manifest still exists at `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/round_manifest.json`; it is minimal and must remain unchanged.
- `artifact_index.json` still contains many stale reverse-solving artifacts, plus some current artifacts from `sr_arg0_hook_readiness_ordering_20260526_r1`; none of these are current evidence for this engineering round.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits.
- Existing project-state status/lint tooling is the only relevant capability for this round. IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, sidecars, solvers, and sample binaries are not relevant and must not be run.
- `.codex-skills/registry.json` shows `reverse-agent-iteration` is active with version 2, so `reverse-agent-iteration@v2` is the valid skill profile.

## 3. Do Not Do

- Do not rerun the mutating `archive-round` command.
- Do not overwrite, regenerate, or hand-edit anything under `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/`.
- Do not execute any sample binary, including `Cpp2.exe` or any `samplereverse` executable.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, runtime probe, hook, sidecar, winpty, console validator, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run compare-aware search, old `sample_solver` blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify source modules.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not treat stale or mismatched artifacts as current evidence.
- Do not overwrite training status, status overlay, sample metadata, or runtime artifacts as part of this bookkeeping round.

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
- `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/round_manifest.json`

Optional bounded file, only to verify the already-accepted archive-command safety classification if needed:

- the small `archive_round()` implementation region in `reverse_agent/project_state.py`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm `decision_meta.skill_profiles == ["reverse-agent-iteration@v2"]` and the skill is active in `.codex-skills/registry.json`.
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm the prior archive manifest remains present and unchanged.
7. Confirm `archive-round` is not rerun and no archive files are modified.
8. Update `project_state/codex_execution_report.md` for this round only after generating the new test outputs.
9. Update `project_state/pytest_result.txt` so it does not claim `PASSED` if any required final command failed.
10. Run final `lint-report` after report/test update and record the exact final output.
11. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
12. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.
13. Confirm no reverse-solving, runtime, debugger, solver, sample execution, or static extraction occurred.
14. Confirm stale artifacts in `artifact_index.json` remain stale and are not promoted as current evidence.

## 6. Implementation Scope

Allowed changes are limited to engineering state files:

1. `project_state/codex_execution_report.md`, updated to report the real outcome of this lint-report record repair round.
2. `project_state/pytest_result.txt`, updated with this round's command outputs.

Do not modify source modules, `.codex-skills/`, training status, sample metadata, status overlay, runtime artifacts, solver code, or archive files.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Required final state for `SUCCESS`:

- `lint-decision: OK`
- `lint-report: OK`
- `pytest tests/test_project_state.py` passes
- `pytest_result.txt` has this round's `decision_id`, `report_id`, and `round_id`
- `pytest_result.txt` matches the current report
- no failed command is hidden under `status: PASSED`
- prior archive manifest remains present and unchanged
- no reverse-solving or runtime action occurred

If final `lint-report` fails, report `FAILED` or `BLOCKED`; do not mark `SUCCESS`.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- final `lint-report` fails
- final `lint-decision` fails
- pytest fails
- `pytest_result.txt` cannot be updated with real outputs from this round
- report/test IDs mismatch
- any archive file would need to be overwritten
- any command requires rerunning mutating `archive-round`
- any test output is copied from a prior round rather than generated in this round
- any task requires executing samples, using reverse tools, running solvers, promoting stale artifacts, or shifting this round from `engineering_branch` into `tool_integration`, `reverse_solving`, or `training_dataset`
