```json
{"schema_version":"1.0","decision_id":"decision_20260609_repair_cpp2_state_mismatch_v1","round_id":"round_20260609_repair_cpp2_state_mismatch_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration"]}
```

# DECISION_PACKET

## 1. Goal

Repair the current `project_state` consistency failure before any further sample analysis. The immediate target is to replace the truncated `project_state/decision_packet.md` with a complete, auditable decision packet and force the next Codex round to reconcile `codex_execution_report.md`, `pytest_result.txt`, and the cpp2 static-triage artifact provenance.

This is an `engineering_branch` repair round. It is not a `tool_integration` execution round, not a `reverse_solving` round, and not a `training_dataset` advancement round.

## 2. Current Evidence

- `task_packet.json` is advisory only. The active execution authority is `project_state/decision_packet.md`.
- The current `decision_packet.md` was truncated to a partial packet: it contains `decision_meta`, `Goal`, and the beginning of `Current Evidence`, but it does not contain all required sections.
- The current `codex_execution_report.md` claims `status=SUCCESS` and `acceptance_recommendation=ACCEPTED` for `decision_20260609_cpp2_f2738577_static_extraction_v3`, but the active decision packet is incomplete and therefore cannot support that success claim.
- The current report also claims that `decision_packet.md` was restored completely; that is contradicted by the current file contents.
- `project_state/local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json` exists, but its internal `decision_id` and `round_id` are `decision_20260609_cpp2_f2738577_bounded_static_triage_readiness_v1` and `round_20260609_cpp2_f2738577_bounded_static_triage_readiness_v1`, which do not match the current report's `decision_20260609_cpp2_f2738577_static_extraction_v3` / `round_20260609_cpp2_f2738577_static_extraction_v3`.
- `pytest_result.txt` records a passing project-state test run, but passing tests do not override the live decision/report/artifact provenance mismatch.
- `artifact_index.json` contains both legacy `latest_artifacts` and v2 `latest_artifacts_v2`; stale or mismatched artifacts must not be promoted as current evidence.
- `negative_results.json` contains multiple hard/soft blocks for repeated solver/search/probe directions. This repair round must not enter any of those directions.
- `.codex-skills/registry.json` lists `reverse-agent-iteration` as active. No new skill profile is needed.
- Existing tool interfaces must be acknowledged but not run in this repair round: IDA/IDAPython script wrappers, tool runners, console validator, and local reverse triage adapters may be inspected only as metadata if needed.
- Running IDA/Ghidra/debugger/emulator/runtime probes is not allowed in this repair round.
- Reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt` is not allowed in this repair round.

## 3. Do Not Do

- Do not execute `Cpp2.exe`.
- Do not run runtime validation, debugger, emulator, hook, winpty, or sidecar probes.
- Do not generate, mutate, rank, or validate any candidate input or flag.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, or topN expansion.
- Do not re-run Base64/RC4/DES/XOR static or runtime extraction.
- Do not treat stale or mismatched artifacts as current evidence.
- Do not read or commit full `solve_reports/`.
- Do not modify `.codex-skills/`.
- Do not modify sample metadata, training status, or status overlay unless required only to mark the provenance mismatch; prefer not modifying them in this round.
- Do not convert this repair round into cpp2 solving, cpp2 static extraction, or training-set advancement.
- Do not report `SUCCESS` unless the active decision packet, report metadata, test record, and generated artifact provenance are mutually consistent.

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
- `project_state/local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json`

Optional bounded files, only if needed for consistency verification:

- latest relevant `project_state/rounds/<round_id>/round_manifest.json`, if present
- latest relevant `project_state/rounds/<round_id>/git_diff.patch`, if present
- commit diff for the latest decision/report repair commits

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm `project_state/decision_packet.md` has a fenced JSON `decision_meta` block.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch` for this repair round.
4. Confirm `decision_meta.skill_profiles` contains only active skills from `.codex-skills/registry.json`.
5. Confirm the active decision packet contains all required sections:
   - Goal
   - Current Evidence
   - Do Not Do
   - Files To Inspect
   - Required Audit
   - Implementation Scope
   - Tests
   - Stop Conditions
6. Confirm `codex_execution_report.md` either matches this repair decision after Codex completes, or is explicitly marked as stale/mismatch before the repair is complete.
7. Confirm any report with `status=SUCCESS` includes non-empty `tests_ran`, valid `generated_artifacts`, and a matching `based_on_decision_id` / `round_id`.
8. Confirm `pytest_result.txt` corresponds to this repair round after tests are run.
9. Confirm the cpp2 static-triage artifact is not promoted as current evidence unless its internal decision/round provenance is reconciled in a later, separately approved `tool_integration` round.
10. Confirm no negative-result direction was repeated.
11. Confirm no runtime/debugger/solver/sample execution was performed.
12. Confirm no `.codex-skills/` changes were made.

## 6. Implementation Scope

Codex is allowed to make only a small state-repair change set:

1. Keep this complete `project_state/decision_packet.md` as the active execution authority.
2. Update `project_state/codex_execution_report.md` after performing the repair audit so that it reports the real result of this repair round.
3. Update `project_state/pytest_result.txt` with the actual command output from this repair round.
4. If necessary, add a short note in the report that `project_state/local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json` is provenance-mismatched relative to the prior report and must not be treated as current evidence.
5. Do not edit source modules unless a project-state lint command exposes a minimal, directly related parser/status bug. If such a bug appears, stop and report it rather than expanding scope.
6. Do not update `artifact_index.json` unless the existing project-state tooling requires it for consistency; if updated, preserve legacy fields and v2 fields and clearly mark stale/mismatched artifacts.

## 7. Tests

Run and record the exact output in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

If any command is unavailable or fails, record the failure exactly in `pytest_result.txt` and set the report status to `FAILED` or `BLOCKED`, not `SUCCESS`.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if any of the following occurs:

- `decision_packet.md` is still truncated or missing any required section.
- `codex_execution_report.md` cannot be made to match this repair decision.
- `pytest_result.txt` cannot be updated with real command output.
- The cpp2 static-triage artifact provenance remains ambiguous and Codex attempts to promote it as current evidence.
- Any runtime/debugger/emulator/probe/sample execution is required to proceed.
- Any `.codex-skills/` modification appears necessary.
- Any full `solve_reports/` read appears necessary.
- Any task would move this round from `engineering_branch` into `tool_integration`, `reverse_solving`, or `training_dataset`.
