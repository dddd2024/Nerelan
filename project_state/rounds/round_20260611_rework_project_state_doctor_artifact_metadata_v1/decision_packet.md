```json decision_meta
{"schema_version":1,"decision_id":"decision_20260611_rework_project_state_doctor_artifact_metadata_v1","round_id":"round_20260611_rework_project_state_doctor_artifact_metadata_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the final doctor-artifact metadata defects left by `decision_20260610_rework_project_state_command_output_authority_v1`.

The previous round correctly established final command-output authority: old `all_command_outputs.json` was labeled historical/non-authoritative and `final_command_outputs.json` was created as the final authoritative command-output artifact. However, the live `pytest_result.txt` still contains `TBD` metadata for `doctor_pre_archive.json` and `doctor_post_archive.json`, and `doctor_pre_archive.json` is not present in the repository. The report also omits the existing final `doctor_post_archive.json` from `codex_report_summary.files_changed` even though it is referenced as evidence.

This round must only repair those final evidence metadata defects. It must not change doctor behavior, source code, tests, skills, samples, solvers, debuggers, IDA, Ghidra, emulator, hook, sidecar, or runtime-probe workflows.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_command_output_authority_v1`.
- Previous report: `report_20260610_rework_project_state_command_output_authority_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest result: `167 passed in 70.98s`, bound to the previous decision/report/round.
- Previous report says Strategy A+B was used: `all_command_outputs.json` is historical/non-authoritative and `final_command_outputs.json` is final authoritative evidence.
- Previous `final_command_outputs.json` records final lint OK, final status `CONSUMED_BY_SUCCESS_REPORT`, archive `archived`, doctor `WARN`, and final doctor JSON artifact path + sha256.
- Previous `all_command_outputs.json` has machine-readable historical labels: `_label: historical_pre_final_evidence` and `_authoritative_for_final_evidence_convergence: false`.
- Blocking defect: `project_state/pytest_result.txt` records `doctor_pre_archive.json` with `sha256: TBD`, `byte_size: TBD`, and `line_count: TBD`.
- Blocking defect: `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_pre_archive.json` is not present in the repository.
- Blocking defect: `project_state/pytest_result.txt` records `doctor_post_archive.json` with `sha256: TBD`, `byte_size: TBD`, and `line_count: TBD`.
- Blocking defect: `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_post_archive.json` exists and is valid final evidence with `status: WARN`, current report id, and `CONSUMED_BY_SUCCESS_REPORT`, but it is omitted from `codex_report_summary.files_changed`.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not modify `reverse_agent/project_state.py` or `tests/test_project_state.py`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not change doctor behavior.
- Do not mutate previous archived rounds.
- Do not introduce placeholder values such as `TBD`.
- Do not record any artifact path that does not exist in the repository.
- Do not use a pre-archive doctor artifact as final authoritative evidence.

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
- `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_post_archive.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`

Optional only if verifying absence/removal:

- `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_pre_archive.json`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Verify whether `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_pre_archive.json` exists.
4. If `doctor_pre_archive.json` does not exist, remove its artifact claim from `pytest_result.txt` and do not list it in final evidence. If Codex keeps it, it must create or preserve the real file and record exact sha256, byte size, and line count.
5. Verify `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_post_archive.json` exists, is complete valid JSON, has `status: WARN` or `PASS`, references `report_20260610_rework_project_state_command_output_authority_v1`, and has `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
6. Replace every `TBD` in `pytest_result.txt` with exact values, or remove the corresponding artifact claim if the artifact is intentionally not used.
7. Record exact metadata for `doctor_post_archive.json` in `pytest_result.txt`: path, sha256, byte size, line count, status, report id, and decision execution state.
8. Add `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_post_archive.json` to `codex_report_summary.files_changed` if it was created or intentionally updated in the previous/current evidence chain, or explicitly list it as a verified evidence artifact with exact metadata in `generated_artifacts` or the report body. Do not leave it untracked while referencing it as evidence.
9. Ensure `codex_report_summary.files_changed`, `pytest_result.txt`, `final_command_outputs.json`, and `doctor_post_archive.json` are mutually consistent.
10. Ensure `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
11. Archive this repair round into `project_state/rounds/round_20260611_rework_project_state_doctor_artifact_metadata_v1/`.
12. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json` and record exact outputs or artifact metadata.
13. Record final `git status --short`.
14. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260611_rework_project_state_doctor_artifact_metadata_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_command_output_authority_v1/doctor_post_archive.json` only if already present or regenerated as exact final doctor evidence
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_command_outputs.json` only if metadata must be corrected to match the verified final doctor artifact

Allowed only for verification, not intentional modification:

- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`
- `project_state/model_gate.json`
- `project_state/task_packet.json`

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

Run and record exact outputs in `project_state/pytest_result.txt`. If an output is saved as an artifact, record path, sha256, byte size, line count, and exact command.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260611_rework_project_state_doctor_artifact_metadata_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `pytest_result_summary.tests_ran` includes every required command run in this round.
- `codex_report_summary.tests_ran` matches `pytest_result_summary.tests_ran`.
- `python -m pytest tests/test_project_state.py -q` passes.
- Final `lint-report` is OK.
- Final status shows `decision_report_id_match: True`, `decision_consumed_by_report: True`, `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`, `round_manifest_present: True`, and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` output is complete valid JSON or saved as artifact with path and sha256.
- No `TBD` appears in `project_state/pytest_result.txt`, `project_state/codex_execution_report.md`, or final evidence metadata.
- No nonexistent artifact path is claimed in `pytest_result.txt` or report.
- `doctor_post_archive.json` has exact metadata recorded in pytest/report and is included in `files_changed` or explicitly listed as verified evidence artifact.
- If `doctor_pre_archive.json` is absent, it is not claimed as an artifact in final evidence.
- `codex_report_summary.files_changed`, `pytest_result.txt`, `final_command_outputs.json`, and `doctor_post_archive.json` are mutually consistent.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Any `TBD` remains in final report/pytest/evidence metadata.
- A nonexistent artifact path remains in final report or pytest.
- `doctor_post_archive.json` cannot be verified as valid JSON with `PASS` or `WARN` status and current report id.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
