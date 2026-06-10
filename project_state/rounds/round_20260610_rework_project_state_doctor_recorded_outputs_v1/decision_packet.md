```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_doctor_recorded_outputs_v1","round_id":"round_20260610_rework_project_state_doctor_recorded_outputs_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Rework the previous `project_state doctor` round by completing the missing recorded command outputs and final self-check evidence.

The previous implementation appears mostly correct and should not be rewritten. The audit result was `REWORK_REQUIRED` because the live `pytest_result.txt` did not record the implemented `doctor --json` command, did not record the required final self-check commands, and only recorded a pre-report `doctor: FAIL` run rather than a final live-state `doctor` run after report/pytest files were updated.

This is an `engineering_branch` documentation/test-record repair round. The goal is to make the evidence trail complete and auditable, not to add new doctor features or change solving behavior.

## 2. Current Evidence

- Active previous decision: `decision_20260610_add_project_state_doctor_v1`.
- Previous Codex report: `report_20260610_add_project_state_doctor_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest record: `167 passed in 55.54s` for `python -m pytest tests/test_project_state.py -q`.
- Previous implementation added `doctor()` and the CLI subcommand with `--state-dir` and `--json`.
- Previous report claims the working tree root was `F:\reverse-agent`, but the required command outputs were not recorded in `pytest_result.txt`.
- Previous `pytest_result.txt` recorded `python -m reverse_agent.project_state doctor --state-dir project_state`, but the recorded output was `doctor: FAIL` because the report still pointed to a prior decision at that moment.
- Previous `pytest_result.txt` did not record `python -m reverse_agent.project_state doctor --state-dir project_state --json`, even though `--json` exists.
- Previous final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- `model_gate.json` currently reports `next_local_action: repair_harness_case_result_materialization`; that is sample-state context and is not the implementation target for this rework round.
- `task_packet.json` is advisory. This `decision_packet.md` controls the current round.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not implement new doctor features unless a command fails because the existing implementation is broken.
- Do not create a second project-state system or a parallel doctor module.
- Do not modify sample binaries, candidate files, training metadata, status overlays, or historical runtime reports.
- Do not overwrite the previous archived round directory if the manifest would differ. Use this new rework round archive.

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

Optional only if needed to confirm previous archive state:

- `project_state/rounds/round_20260610_add_project_state_doctor_v1/round_manifest.json`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Confirm the previous doctor implementation exists and reuse it. Do not rewrite `doctor()` unless a recorded command fails.
4. Run a final live-state `doctor` command after the report/pytest files have been brought into consistency, so the recorded output is `PASS` or `WARN`, not the previous pre-report `FAIL`.
5. Run and record `doctor --json` because the implementation exposes `--json`.
6. Record the required local repository self-check outputs: `pwd`, `git rev-parse --show-toplevel`, `git status --short`, and the scoped `git diff -- ...` command.
7. Update `project_state/pytest_result.txt` so its `pytest_result_summary.tests_ran` includes every command that the report claims was run.
8. Update `project_state/codex_execution_report.md` with a new `codex_report_summary` bound to this rework decision and round.
9. If no source change is required, make that explicit in the report.
10. If source change is required only because the existing doctor command fails, limit it to `reverse_agent/project_state.py` and focused tests in `tests/test_project_state.py`.
11. Archive this rework round into `project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1/` after live report/test files are updated.
12. After archive, record final `lint-report` and `status` output proving the rework round is consumed and archived.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1/*`

Allowed only if a command genuinely fails and a code fix is necessary:

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
- previous archived round mutation if manifest differs

## 7. Tests

Run and record exact outputs in `project_state/pytest_result.txt`:

```bash
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
pwd
git rev-parse --show-toplevel
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/codex_execution_report.md project_state/pytest_result.txt project_state/rounds/round_20260610_rework_project_state_doctor_recorded_outputs_v1
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_doctor_recorded_outputs_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
```

Acceptance requirements:

- Final `doctor --state-dir project_state` output is `PASS` or `WARN`, not `FAIL`.
- `doctor --json` runs successfully and emits parseable JSON with top-level `status`, `checks`, `decision_id`, `report_id`, and `decision_execution_state`.
- `pwd` and `git rev-parse --show-toplevel` prove the local repo root is `F:\reverse-agent`.
- `git status --short` is recorded.
- Scoped `git diff -- ...` is recorded.
- `pytest_result_summary.tests_ran` includes all commands listed in this decision and all commands listed in `codex_report_summary.tests_ran`.
- `python -m pytest tests/test_project_state.py -q` passes.
- `lint-report: OK` after live report update.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived` after archive.
- No source files are changed unless needed to fix a failing doctor command.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- `doctor --json` fails and cannot be fixed within `reverse_agent/project_state.py` and `tests/test_project_state.py`.
- Final live-state doctor remains `FAIL` after report/pytest files are updated.
- `pytest_result_summary` cannot be made to cover `codex_report_summary.tests_ran`.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- The repair would require sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
