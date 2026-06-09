```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_archive_command_evidence_repair_v1","round_id":"round_20260609_archive_command_evidence_repair_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 1. Goal

Close the audit limitation from the previous archive/refresh round by producing a non-destructive, command-backed evidence record for the prior repair-round archive status.

The previous round `round_20260609_archive_repair_round_and_refresh_state_v1` reached consistent `decision_packet` / `codex_execution_report` / `pytest_result` state, and the prior repair round archive manifest exists. The remaining limitation is evidentiary: the previous report and `pytest_result.txt` did not record the `archive-round` command requested by its decision packet. This round must repair that record without corrupting the already archived prior round.

This is an `engineering_branch` state-evidence repair round only. It must not advance `samplereverse`, `cpp2`, training samples, candidate generation, solver work, static extraction, runtime validation, or tool integration.

## 2. Current Evidence

- Active execution authority is `project_state/decision_packet.md`; `task_packet.json` remains advisory and still carries old sample-derived text such as `derived_task: Review bounded window discovery diagnostics`.
- The consumed prior active decision was `decision_20260609_archive_repair_round_and_refresh_state_v1`, with report `report_20260609_archive_repair_round_and_refresh_state_v1` and round `round_20260609_archive_repair_round_and_refresh_state_v1`.
- The previous report claimed `SUCCESS` and `ACCEPTED`, and recorded no reverse-solving action: no sample execution, no candidate generation, no runtime validation, no debugger/emulator, no IDA/Ghidra extraction, and no full `solve_reports/` read.
- `project_state/pytest_result.txt` for the previous round records `lint-decision: OK`, `lint-report: OK`, `pytest_result_matches_report: True`, and `pytest tests/test_project_state.py` passed with 158 tests.
- The same `pytest_result.txt` records `round_manifest_present: True`, `archive_status: archived`, and `round_manifest_path: project_state\\rounds\\round_20260609_fix_repair_round_lint_and_report_v1\\round_manifest.json`.
- The prior repair archive manifest exists at `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/round_manifest.json`; it uses `archive_mode: minimal`, includes only `codex_execution_report.md`, `decision_packet.md`, `pytest_result.txt`, and the manifest, and omits broad state/runtime files.
- Audit limitation: the previous round's `tests_ran` listed only `status`, `lint-decision`, `lint-report`, and `pytest`; it did not list `archive-round`, even though the previous decision requested an archive command.
- The prior archive is now historical evidence. Re-running `archive-round` blindly may overwrite the prior archive with the current live decision/report/test files if the CLI is not idempotent or no-overwrite safe. Codex must not corrupt historical archive provenance merely to satisfy a command checklist.
- `artifact_index.json` still contains many stale reverse-solving artifacts, plus some current artifacts from `sr_arg0_hook_readiness_ordering_20260526_r1`; none of these are current evidence for this engineering round.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits.
- Existing project-state CLI/status/lint/archive tooling is the only relevant capability for this round. IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, sidecars, solvers, and sample binaries are not relevant and must not be run.
- `.codex-skills/registry.json` shows `reverse-agent-iteration` is active with version 2, so `reverse-agent-iteration@v2` is the valid skill profile.

## 3. Do Not Do

- Do not execute any sample binary, including `Cpp2.exe` or any `samplereverse` executable.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, runtime probe, hook, sidecar, winpty, console validator, or binary instrumentation.
- Do not generate, mutate, rank, validate, or report candidate inputs or flags.
- Do not run compare-aware search, old `sample_solver` blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not inspect or commit full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.
- Do not modify `.codex-skills/`.
- Do not modify source modules unless a project-state CLI defect directly prevents a non-destructive evidence repair; if that happens, stop and report `BLOCKED` instead of widening scope.
- Do not overwrite the already archived `round_20260609_fix_repair_round_lint_and_report_v1` files unless the existing archive command is explicitly confirmed to be idempotent/no-overwrite safe for existing archive contents.
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

Required bounded CLI/code inspection only if needed to determine whether the archive command is safe to rerun:

- `python -m reverse_agent.project_state --help`
- `python -m reverse_agent.project_state archive-round --help`
- the minimal project-state CLI function implementing `archive-round`, only if help output does not prove idempotency/no-overwrite behavior

Optional bounded files, only if directly needed for archive provenance:

- `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/codex_execution_report.md`
- `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/decision_packet.md`
- `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/pytest_result.txt`

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm `decision_meta.skill_profiles == ["reverse-agent-iteration@v2"]` and the skill is active in `.codex-skills/registry.json`.
5. Confirm `project_state/decision_packet.md` is the execution authority and `task_packet.json` is advisory only.
6. Confirm the previous report/test state is consistent before this round begins.
7. Confirm the prior repair archive manifest exists and is minimal.
8. Confirm the prior repair archive files are historical and must not be overwritten unless the archive command is proven idempotent/no-overwrite safe.
9. Run and record archive command help or bounded implementation inspection sufficient to classify `archive-round` behavior as one of:
   - `safe_to_rerun_idempotent_or_no_overwrite`
   - `unsafe_may_overwrite_existing_archive`
   - `unknown_blocked`
10. If and only if the command is classified `safe_to_rerun_idempotent_or_no_overwrite`, run:
    `python -m reverse_agent.project_state archive-round --round-id round_20260609_fix_repair_round_lint_and_report_v1`
    and record the exact output in `project_state/pytest_result.txt`.
11. If the command is classified `unsafe_may_overwrite_existing_archive`, do not run it. Instead record the reason, the manifest path, manifest file list, and the existing `archive_status: archived` evidence from `status`/`lint-report` in `project_state/pytest_result.txt`.
12. If the command behavior is `unknown_blocked`, stop and report `BLOCKED` without modifying unrelated files.
13. Confirm no reverse-solving, runtime, debugger, solver, sample execution, or static extraction occurred.
14. Confirm stale artifacts in `artifact_index.json` remain stale and are not promoted as current evidence.
15. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
16. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes are limited to engineering state files:

1. `project_state/codex_execution_report.md`, updated to report the real outcome of this archive-command evidence repair round.
2. `project_state/pytest_result.txt`, updated with this round's command outputs and archive-command safety classification.
3. Existing archive files under `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/` only if the existing archive command is proven idempotent/no-overwrite safe and the command itself updates or preserves them. Do not hand-edit archive files.
4. `project_state/task_packet.json`, `project_state/current_state.json`, `project_state/artifact_index.json`, and `project_state/negative_results.json` only if an existing project-state status/build command updates them as part of bounded state refresh. Preserve legacy/v2 compatibility fields and do not hand-edit solver conclusions.
5. `project_state/decision_packet.md` should normally remain unchanged during Codex execution except for preserving active packet formatting if required by project-state tooling.

Do not modify source modules, `.codex-skills/`, training status, sample metadata, status overlay, runtime artifacts, or solver code.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m reverse_agent.project_state archive-round --help
```

Then follow the safety branch:

Safe branch only, if the command is proven idempotent/no-overwrite safe:

```bash
python -m reverse_agent.project_state archive-round --round-id round_20260609_fix_repair_round_lint_and_report_v1
```

Unsafe or unknown branch:

- Do not run the mutating archive command.
- Record the exact reason in `pytest_result.txt` and `codex_execution_report.md`.
- If unknown, stop with `BLOCKED`.

Final commands for any non-blocked outcome:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

Acceptance requirements:

- `lint-decision` passes for this decision.
- `lint-report` passes for this round's report, unless the round is explicitly `BLOCKED` because archive command safety could not be determined.
- `pytest tests/test_project_state.py` passes for any `SUCCESS` report.
- `pytest_result.txt` matches this round's report and includes the archive-command safety classification.
- Prior archive manifest remains present and minimal.
- If the archive command was rerun, the output is recorded and the archive was not corrupted.
- If the archive command was not rerun because it was unsafe, the report must mark this as a deliberate non-destructive repair decision, not a silent omission.
- No reverse-solving or runtime action occurred.

## 8. Stop Conditions

Stop and report `BLOCKED` if any of the following occurs:

- Existing project-state tooling cannot determine whether rerunning `archive-round` would overwrite existing archive contents.
- The only way to satisfy the old command checklist would be to overwrite or corrupt the already archived prior round.
- The archive command would require reading or committing full `solve_reports/`.
- The archive command would include `.codex-skills/`, bulky runtime artifacts, source modules, or unrelated files.
- `lint-decision` fails for this decision.
- `pytest_result.txt` cannot be updated with real outputs from this round.
- Any test output is copied from a prior round rather than generated in this round.
- Any task requires executing samples, using reverse tools, running solvers, promoting stale artifacts, or shifting this round from `engineering_branch` into `tool_integration`, `reverse_solving`, or `training_dataset`.
