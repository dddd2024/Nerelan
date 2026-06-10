```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_doctor_final_doctor_evidence_v1","round_id":"round_20260610_rework_project_state_doctor_final_doctor_evidence_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining evidence-recording defect in the `project_state doctor` rework round.

The previous rework round correctly rebound the report and pytest result to `decision_20260610_rework_project_state_doctor_recorded_outputs_v1`, and created the expected round archive. However, the recorded `doctor` and `doctor --json` outputs were still pre-archive/pre-final-state outputs with `status: FAIL`. This round must record final live-state doctor evidence after report, pytest result, and archive are consistent.

This is an `engineering_branch` evidence-record repair. It is not a reverse-solving round, not a tool-integration round, and not a training-dataset round.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Current previous decision: `decision_20260610_rework_project_state_doctor_recorded_outputs_v1`.
- Previous report: `report_20260610_rework_project_state_doctor_recorded_outputs_v1`, `status: SUCCESS`, bound to the previous decision.
- Previous pytest result is bound to `decision_20260610_rework_project_state_doctor_recorded_outputs_v1` and records `167 passed in 41.17s`.
- Previous pytest result includes required command names, but the recorded `doctor` output is still `doctor: FAIL`.
- Previous pytest result records `doctor --json` as `status: FAIL` and abbreviates the `checks` list as `[...]`, so it is not complete parseable JSON evidence.
- Previous pytest result records `git status --short` with modified report and pytest files, but then records the scoped `git diff -- ...` as no output. This is internally inconsistent unless the modified files were staged, which was not recorded.
- Previous final `lint-report` and `status` show the previous rework round was consumed and archived.
- Previous rework archive exists at `project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1/round_manifest.json` and is minimal.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- `model_gate.json` and sample-state evidence remain context only and must not drive this round into reverse solving.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.
- Existing doctor implementation and tests should be reused. Do not rewrite doctor unless the final live-state command genuinely fails.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not implement new doctor features.
- Do not rewrite the existing `doctor()` implementation unless final live-state `doctor` genuinely fails and cannot be fixed by correcting report/pytest/archive order.
- Do not create a second project-state system or a parallel doctor module.
- Do not modify sample binaries, candidate files, training metadata, status overlays, or historical runtime reports.
- Do not mutate the previous archived round. Use this new round archive.
- Do not record abbreviated JSON such as `"checks": [...]` for `doctor --json`.
- Do not claim scoped diff has no output if `git status --short` shows unstaged modified files in the scoped paths.

## 4. Files To Inspect

Required:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/current_state.json`
- `project_state/artifact_index.json`
- `project_state/model_gate.json`
- `project_state/task_packet.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional only if needed to compare previous evidence:

- `project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1/round_manifest.json`
- `project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1/pytest_result.txt`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm the existing `doctor` command exists with `--state-dir` and `--json`.
4. Preserve the existing doctor implementation unless the final live-state command genuinely fails.
5. Update live `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` for this new round before final doctor evidence is recorded, so final doctor validates the current report/pytest pair.
6. Archive this round into `project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1/`.
7. After archive, run final `lint-report` and final `status`.
8. After archive and final status are consistent, run final live-state `doctor` and final live-state `doctor --json`.
9. Record the full final `doctor --json` output as parseable JSON. Do not abbreviate lists or nested objects.
10. Record `pwd`, `git rev-parse --show-toplevel`, `git status --short`, and scoped `git diff -- ...` after the final doctor evidence.
11. Ensure `git status --short` and scoped `git diff` are mutually consistent. If files are staged, record `git diff --cached -- ...` as well.
12. Ensure `pytest_result_summary.tests_ran` includes every command claimed in `codex_report_summary.tests_ran`.
13. Ensure the new `codex_report_summary` is bound to this decision and this round.
14. State explicitly whether source files changed. If no source files changed, record that no source change was necessary.
15. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1/*`

Allowed only if final live-state doctor genuinely fails due to a code defect:

- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Disallowed:

- `.codex-skills/`
- solver/search/runtime/debugger/probe code
- IDA/Ghidra/debugger interface code
- sample binaries
- candidate files
- training dataset/sample metadata
- status overlay
- full `solve_reports/`
- full `PROJECT_PROGRESS_LOG.txt`
- previous archived round mutation

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_doctor_final_doctor_evidence_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
pwd
git rev-parse --show-toplevel
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/codex_execution_report.md project_state/pytest_result.txt project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/codex_execution_report.md project_state/pytest_result.txt project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1
```

Acceptance requirements:

- Final `doctor --state-dir project_state` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` output is complete parseable JSON, not abbreviated JSON.
- Final `doctor --json.status` is `PASS` or `WARN`.
- Final `doctor --json.checks` is a real list of check objects.
- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `git status --short` is recorded.
- Scoped `git diff -- ...` is recorded.
- If `git status --short` shows staged changes in scoped paths, `git diff --cached -- ...` is recorded and explains them.
- `pytest_result_summary.tests_ran` includes all commands listed in this decision and all commands listed in `codex_report_summary.tests_ran`.
- `python -m pytest tests/test_project_state.py -q` passes.
- `lint-report: OK` after live report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No source files are changed unless needed to fix a genuine doctor command failure.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Final live-state doctor remains `FAIL` after report/pytest/archive are consistent.
- Final `doctor --json` cannot emit complete parseable JSON.
- `pytest_result_summary` cannot cover `codex_report_summary.tests_ran`.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
