```json decision_meta
{"schema_version":1,"decision_id":"decision_20260611_add_verified_artifacts_report_schema_v1","round_id":"round_20260611_add_verified_artifacts_report_schema_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Add a small, backward-compatible `verified_artifacts` report-summary field to reduce future evidence-audit ambiguity.

The previous accepted round used `generated_artifacts` to list a pre-existing verified evidence artifact. That was accepted with limitations, but the field name is semantically wrong: generated artifacts are created by the current round, while verified artifacts already existed and were only checked or referenced. This round should make that distinction explicit in the project-state report schema and lint/status/doctor handling.

This is an `engineering_branch` schema/validation cleanup. It is not a reverse-solving, tool-integration, or training-dataset round.

## 2. Current Evidence

- The current active `decision_packet.md` controls execution; `task_packet.json` remains advisory only.
- The last accepted round was `decision_20260611_rework_project_state_doctor_artifact_metadata_v1`, with report/pytest/archive/doctor all aligned enough for `ACCEPTED_WITH_LIMITATIONS`.
- The remaining limitation was field semantics: `codex_report_summary.generated_artifacts` included an older verified artifact path, even though the report body explained it was verified existing evidence rather than current-round output.
- `task_packet.json` still contains older sample-solving context and a derived task related to harness case materialization, but that is not authoritative for this round.
- `current_state.json` and `artifact_index.json` contain many sample/harness artifact references, most not current for a new engineering schema cleanup.
- `artifact_index.latest_artifacts_v2` contains stale sample artifacts; stale artifacts must not be treated as current evidence.
- `negative_results.json` still blocks old blind sample solver search, beam/budget expansion, stale runtime probes, full `solve_reports/` commits, and several repeated reverse-solving directions.
- `.codex-skills/registry.json` shows both selected skills are active: `reverse-agent-iteration@v2` and `samplereverse-frontier@v2`.
- Existing relevant capability: `reverse_agent.project_state` already parses report summaries, validates report/pytest matching, runs `lint-report`, `status`, `doctor`, and archives rounds.
- This round should improve existing project-state validation rather than adding another ad-hoc evidence file.
- No IDA/Ghidra/debugger/solver/harness/sample execution is required or allowed.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not change sample metadata, candidate files, or training dataset state.
- Do not rewrite the whole project-state subsystem.
- Do not make `verified_artifacts` mandatory for old reports.
- Do not break existing reports that only contain `generated_artifacts`.
- Do not rename `generated_artifacts`; keep backward compatibility.
- Do not count `verified_artifacts` as current-round generated output.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional if directly relevant:

- README or other local docs that mention `codex_report_summary.generated_artifacts`
- `project_state/rounds/round_20260611_rework_project_state_doctor_artifact_metadata_v1/round_manifest.json`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Inspect the existing report-summary parser/validator implementation before changing it.
4. Add support for an optional `verified_artifacts` list in `codex_report_summary`.
5. Preserve backward compatibility for reports that omit `verified_artifacts`.
6. Preserve existing behavior for `generated_artifacts`.
7. Ensure `lint-report`, `status`, and `doctor` can parse reports with both fields.
8. Ensure report/pytest test coverage logic still compares `tests_ran` correctly and is not affected by artifact field changes.
9. Add tests that cover:
   - report summary with only `generated_artifacts`;
   - report summary with only `verified_artifacts`;
   - report summary with both lists;
   - old reports with no `verified_artifacts`;
   - invalid non-list `verified_artifacts`, if current validation has list-type checks for analogous fields.
10. Update current `codex_execution_report.md` format for this round to use `verified_artifacts` for any pre-existing checked artifact and `generated_artifacts` only for current-round generated output.
11. Archive this round into `project_state/rounds/round_20260611_add_verified_artifacts_report_schema_v1/`.
12. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
13. Record final `git status --short`.
14. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_add_verified_artifacts_report_schema_v1/*`

Allowed only if directly documenting the schema change:

- README or a local project-state documentation file, if one already documents `codex_report_summary`

Disallowed:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay unrelated to report validation
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_add_verified_artifacts_report_schema_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `python -m pytest tests/test_project_state.py -q` passes.
- Tests cover optional `verified_artifacts` behavior and old report compatibility.
- `lint-report` is OK after the report and pytest files are written for this round.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` is complete valid JSON or saved as artifact with path and sha256.
- `codex_report_summary.generated_artifacts` remains supported and semantically means current-round generated artifacts.
- `codex_report_summary.verified_artifacts` is optional and semantically means pre-existing artifacts verified/referenced by the current round.
- Old reports without `verified_artifacts` still parse and lint.
- `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Adding `verified_artifacts` requires changing `.codex-skills/`.
- Adding `verified_artifacts` would break old reports that omit the field.
- `lint-report`, `status`, or `doctor` cannot parse the updated report summary.
- Tests fail.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
