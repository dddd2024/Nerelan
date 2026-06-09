```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_fix_repair_round_lint_and_report_v1","round_id":"round_20260609_fix_repair_round_lint_and_report_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the current repair-round lint/report/test consistency failure. The immediate target is to make `project_state/decision_packet.md`, `project_state/codex_execution_report.md`, and `project_state/pytest_result.txt` agree on the same engineering repair decision and round.

This is an `engineering_branch` state repair round only. It must not advance cpp2 static extraction, cpp2 solving, candidate generation, runtime validation, or training-set advancement.

## 2. Current Evidence

- The prior repair packet restored the required eight-section shape, but its `skill_profiles` value was `reverse-agent-iteration` while current lint expects `skill-name@vN` format.
- `.codex-skills/registry.json` shows `reverse-agent-iteration` is active with `version: 2`, so the valid profile string is `reverse-agent-iteration@v2`.
- `project_state/pytest_result.txt` from the prior round records `lint-decision: FAILED` because of the missing `@v2` suffix.
- The same `pytest_result.txt` records `lint-report: FAILED` because the report and current decision/round were mismatched at the time of that run.
- `project_state/codex_execution_report.md` nevertheless reports `status=SUCCESS` and `acceptance_recommendation=ACCEPTED`; that is inconsistent with the recorded lint failures.
- `project_state/codex_execution_report.md` also describes the cpp2 static-triage artifact provenance inaccurately. The actual artifact file begins with `decision_id=decision_20260609_cpp2_f2738577_bounded_static_triage_readiness_v1` and `round_id=round_20260609_cpp2_f2738577_bounded_static_triage_readiness_v1`, not the static_extraction_v3 IDs claimed in the report.
- The cpp2 static-triage artifact remains a non-current, provenance-mismatched artifact for this repair round and must not be promoted as current evidence.
- `task_packet.json` remains advisory only and must not override this decision packet.
- Existing negative results prohibit returning to blind solver/search/probe expansion directions. This repair round must not enter those directions.

## 3. Do Not Do

- Do not execute `Cpp2.exe`.
- Do not run runtime validation, debugger, emulator, hook, winpty, sidecar, or any sample process.
- Do not generate, mutate, rank, or validate candidate inputs or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, or topN expansion.
- Do not run Base64/RC4/DES/XOR extraction or solver work.
- Do not inspect or commit full `solve_reports/`.
- Do not modify `.codex-skills/`.
- Do not modify training status, status overlay, sample metadata, or source modules unless a lint command proves a minimal directly related state-tooling bug; if that happens, stop and report instead of expanding scope.
- Do not mark the report `SUCCESS` if `lint-decision`, `lint-report`, or pytest fails.
- Do not promote `local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json` as current evidence.

## 4. Files To Inspect

Required files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `.codex-skills/registry.json`
- `project_state/local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json`
- `project_state/task_packet.json`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`

Optional bounded files, only if needed for provenance verification:

- latest relevant `project_state/rounds/<round_id>/round_manifest.json`, if present
- latest relevant `project_state/rounds/<round_id>/git_diff.patch`, if present
- latest related commit diff for the prior repair-report commits

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm `decision_packet.md` has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm `decision_meta.skill_profiles == ["reverse-agent-iteration@v2"]` and that this resolves to an active registry skill.
5. Confirm the active decision packet contains all required sections:
   - Goal
   - Current Evidence
   - Do Not Do
   - Files To Inspect
   - Required Audit
   - Implementation Scope
   - Tests
   - Stop Conditions
6. Confirm `codex_execution_report.md` is updated to this decision and this round only after the audit has actually run.
7. Confirm the report's `based_on_decision_id` and `round_id` match this packet.
8. Confirm the report status is not `SUCCESS` unless `lint-decision`, `lint-report`, and pytest all pass.
9. Confirm `pytest_result.txt` records this round's real command outputs, not stale outputs from a prior round.
10. Confirm the report describes `project_state/local_reverse_cpp2_f2738577_bounded_static_triage_readiness.json` using the artifact's actual internal `decision_id` and `round_id`.
11. Confirm the cpp2 artifact is not promoted as current evidence for this repair round.
12. Confirm no runtime/debugger/solver/sample execution was performed.
13. Confirm no `.codex-skills/` changes were made.
14. Confirm no negative-result direction was repeated.

## 6. Implementation Scope

Allowed changes are limited to:

1. `project_state/decision_packet.md` only if Codex needs to preserve this exact active repair decision or fix formatting without changing scope.
2. `project_state/codex_execution_report.md`, to report the real outcome of this repair round.
3. `project_state/pytest_result.txt`, to record the exact outputs from this repair round's commands.

Do not modify source modules, `.codex-skills/`, sample metadata, training status, status overlay, or runtime artifacts. If lint fails because of a project-state tooling bug rather than state content, stop and report `BLOCKED` with the exact failure; do not widen the implementation scope.

## 7. Tests

Run and record the exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Acceptance requirements:

- `lint-decision` exits successfully.
- `lint-report` exits successfully.
- `pytest tests/test_project_state.py` passes.
- `codex_execution_report.md` matches this decision id and round id.
- Report `status` and `acceptance_recommendation` reflect the real command results.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- `lint-decision` still fails after the `reverse-agent-iteration@v2` fix.
- `lint-report` still fails after report metadata is updated to this decision/round.
- `pytest_result.txt` cannot be updated with real outputs from this round.
- `codex_execution_report.md` cannot be made consistent with this decision and round.
- Any test output is stale or copied from a prior round.
- Any task requires executing cpp2, using a debugger/emulator/hook/sidecar, or running solver/search.
- Any task requires full `solve_reports/` or `.codex-skills/` modification.
- Any task would shift this round from `engineering_branch` into `tool_integration`, `reverse_solving`, or `training_dataset`.
