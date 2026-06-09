```json decision_meta
{"schema_version":"1.0","decision_id":"decision_20260609_archive_repair_round_and_refresh_state_v1","round_id":"round_20260609_archive_repair_round_and_refresh_state_v1","based_on_state_build_id":"state_20260608_152003_e6fc7ab3ce85","based_on_state_digest":"e6fc7ab3ce8537d3a989adf7eeba7366ef987bf6887ee459b727c9417f958067","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

# DECISION_PACKET

## 1. Goal

Archive the accepted repair round and refresh `project_state` handoff consistency without advancing any reverse-solving work.

The previous repair round `round_20260609_fix_repair_round_lint_and_report_v1` reached a consistent `decision_packet` / `codex_execution_report` / `pytest_result` state. Its remaining limitation is that the round is not archived and the live state still carries old sample-state context from `samplereverse`. This round should close that engineering bookkeeping gap.

## 2. Current Evidence

- The active prior decision `decision_20260609_fix_repair_round_lint_and_report_v1` was consumed by a matching SUCCESS report.
- `project_state/pytest_result.txt` for that prior round records `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, and `report_decision_round_id_match: True`.
- `lint-decision` passed with `skill_profiles: ['reverse-agent-iteration@v2']`.
- `lint-report` passed and confirms report/decision/round consistency, but warns `report round not archived yet` and `round_manifest_present: False`.
- `pytest tests/test_project_state.py` passed with 158 tests.
- `task_packet.json` remains advisory and still carries `derived_task: Review bounded window discovery diagnostics` from old sample-state context. It must not override this decision packet.
- `current_state.json` remains a `sample_state` for `samplereverse` with `state_build_id=state_20260608_152003_e6fc7ab3ce85` and `workflow_status=REPORT_AVAILABLE`.
- `artifact_index.json` still contains many stale reverse-solving artifacts; they must not be promoted as current evidence in this engineering round.
- `negative_results.json` continues to prohibit repeated blind solver/search/probe directions and full `solve_reports` commits.
- The cpp2 static-triage readiness artifact remains non-current for this round and must not be promoted, regenerated, or edited here.
- Existing project-state tooling is the relevant capability for this round. IDA/Ghidra/debugger/emulator/tool sidecars are not relevant and must not be run.

## 3. Do Not Do

- Do not execute any sample binary, including `Cpp2.exe`.
- Do not run IDA, Ghidra, OllyDbg, x64dbg, debugger, emulator, runtime probe, hook, sidecar, winpty, or console validator.
- Do not generate, mutate, rank, or validate candidates or flags.
- Do not run compare-aware search, sample_solver blind search, brute force, beam expansion, budget expansion, topN expansion, Base64/RC4/DES/XOR solver work, or any reverse-solving action.
- Do not inspect or commit full `solve_reports/`.
- Do not modify `.codex-skills/`.
- Do not modify source modules unless a project-state CLI bug directly blocks this engineering task; if that happens, stop and report `BLOCKED` instead of widening scope.
- Do not treat `task_packet.task` or `derived_task` as execution authority.
- Do not treat stale or mismatched artifacts as current evidence.
- Do not overwrite training status, status overlay, or sample metadata as part of this bookkeeping round.

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

Required after archiving:

- `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/round_manifest.json`
- any minimal files produced by the project-state archive command for that round

Optional bounded files, only if the project-state CLI requires them:

- latest relevant `project_state/rounds/<round_id>/git_diff.patch`
- latest relevant state snapshot produced by the archive command

Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Codex must perform and record these checks:

1. Confirm this decision packet has a fenced JSON block tagged `decision_meta`.
2. Confirm `decision_meta.status == APPROVED`.
3. Confirm `decision_meta.mainline == engineering_branch`.
4. Confirm `decision_meta.skill_profiles == ["reverse-agent-iteration@v2"]` and the skill is active in `.codex-skills/registry.json`.
5. Confirm the prior repair report remains internally consistent before archiving.
6. Archive `round_20260609_fix_repair_round_lint_and_report_v1` using existing project-state tooling; do not manually invent archive format if the CLI exists.
7. Confirm `round_manifest.json` exists after archiving and references only allowed/minimal project-state files for that round.
8. Confirm the archive did not include full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, bulky runtime artifacts, `.codex-skills/`, or unrelated source files.
9. Refresh or rebuild project-state summaries only through existing project-state commands if needed to make status/lint reflect the archived round.
10. Confirm `task_packet.json` remains advisory and does not become the execution authority.
11. Confirm no reverse-solving, runtime, debugger, solver, or sample execution occurred.
12. Confirm stale artifacts in `artifact_index.json` remain stale and are not promoted as current evidence.
13. Confirm `codex_execution_report.md` for this round matches this decision id and round id.
14. Confirm `pytest_result.txt` records this round's real command outputs and matches this round's report.

## 6. Implementation Scope

Allowed changes are limited to engineering state files:

1. Archive outputs under `project_state/rounds/round_20260609_fix_repair_round_lint_and_report_v1/` generated by existing project-state archive tooling.
2. `project_state/codex_execution_report.md`, updated to report the real outcome of this archive/refresh round.
3. `project_state/pytest_result.txt`, updated with this round's command outputs.
4. `project_state/task_packet.json`, `project_state/current_state.json`, `project_state/artifact_index.json`, and `project_state/negative_results.json` only if an existing project-state build/status command updates them as part of a bounded refresh. Preserve legacy/v2 compatibility fields and do not hand-edit solver conclusions.
5. `project_state/decision_packet.md` only if Codex must preserve this active decision packet formatting; otherwise leave it unchanged during execution.

Do not modify source modules, `.codex-skills/`, training status, sample metadata, status overlay, or runtime artifacts.

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-decision
python -m reverse_agent.project_state lint-report
python -m reverse_agent.project_state archive-round --round-id round_20260609_fix_repair_round_lint_and_report_v1
python -m reverse_agent.project_state status
python -m reverse_agent.project_state lint-report
python -m pytest tests/test_project_state.py
```

If the exact archive command name differs, inspect the existing project-state CLI help and use the existing archive command. Record the actual command used. Do not implement a new archive command in this round.

Acceptance requirements:

- The prior accepted repair round is archived.
- `round_manifest.json` exists for `round_20260609_fix_repair_round_lint_and_report_v1`.
- `lint-decision` passes for this decision.
- `lint-report` passes for this round's report.
- `pytest tests/test_project_state.py` passes.
- `pytest_result.txt` matches this round's report.
- No reverse-solving or runtime action occurred.

## 8. Stop Conditions

Stop and report `FAILED` or `BLOCKED` if any of the following occurs:

- Existing project-state tooling cannot archive the prior repair round.
- The archive command would require reading or committing full `solve_reports/`.
- The archive command would include `.codex-skills/`, bulky runtime artifacts, source modules, or unrelated files.
- `lint-decision` fails for this decision.
- `lint-report` fails after this round's report is written.
- `pytest_result.txt` cannot be updated with real outputs from this round.
- Any test output is copied from a prior round rather than generated in this round.
- Any task requires executing samples, using reverse tools, running solvers, or promoting stale artifacts.
- Any task shifts this round from `engineering_branch` into `tool_integration`, `reverse_solving`, or `training_dataset`.
