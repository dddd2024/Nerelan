```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_command_output_authority_v1","round_id":"round_20260610_rework_project_state_command_output_authority_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the final command-output authority defect left by `decision_20260610_rework_project_state_final_evidence_convergence_v1`.

The previous round converged the live report, pytest result, final doctor artifact, `evidence_metadata.json`, and `command_outputs.json`. One residual artifact still conflicts semantically: `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json` retains old `lint_post`, `status_post`, and `doctor_post` fields showing report/decision mismatch and `READY_FOR_EXECUTION`, while their names imply post/final evidence.

This round must define final command-output authority clearly. It must either mark the old `all_command_outputs.json` entries as historical/non-authoritative or create a new final authoritative command-output artifact and explicitly state that the old artifact is historical only.

This is an `engineering_branch` evidence-authority repair. Do not change doctor behavior, source code, tests, skills, samples, solvers, debuggers, IDA, Ghidra, emulator, hook, sidecar, or runtime-probe workflows.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_final_evidence_convergence_v1`.
- Previous report: `report_20260610_rework_project_state_final_evidence_convergence_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest result: `167 passed in 69.74s`, bound to the previous decision/report/round.
- Previous post-archive status showed `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT` and `archive_status: archived`.
- Previous final doctor artifact `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/doctor_post_archive.json` has `status: WARN`, references `report_20260610_rework_project_state_final_evidence_convergence_v1`, and shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Previous canonical `doctor_result_final.json` sha256 was converged across report, pytest, `final_evidence_metadata.json`, old `evidence_metadata.json`, and `command_outputs.json`: `c5c8f711ce7c7b11f4acf3ebe2189631d8308c5d8baa64e96fbcf3442beb7592`.
- Previous `command_outputs.json` now has `doctor_result_final_match: true`.
- Blocking defect: `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json` still contains old `lint_post`, `status_post`, and `doctor_post` fields that show failed report/decision match and `READY_FOR_EXECUTION` from an earlier round.
- Blocking defect: those old fields are not clearly labeled as historical/pre-final/non-authoritative, so they conflict with current final evidence.
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
- Do not introduce new claims about git corruption unless backed by existing recorded artifact evidence.
- Do not let any artifact presented as final authoritative evidence show `READY_FOR_EXECUTION`, report/decision mismatch, or doctor `FAIL`.

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
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/doctor_post_archive.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_evidence_metadata.json`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Choose exactly one authority strategy:
   - Strategy A: update `all_command_outputs.json` so old `lint_post`, `status_post`, and `doctor_post` entries are explicitly labeled `historical_pre_final_evidence` and `non_authoritative_for_final_evidence_convergence`; or
   - Strategy B: create `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_command_outputs.json` containing only final authoritative evidence, and clearly state that old `all_command_outputs.json` is historical/non-authoritative.
4. If using Strategy A, preserve the old text but add machine-readable metadata fields that prevent future audits from treating it as final evidence.
5. If using Strategy B, `final_command_outputs.json` must record:
   - current decision id: `decision_20260610_rework_project_state_final_evidence_convergence_v1` or this current repair decision id, whichever the final command output was generated under;
   - current report id;
   - current round id;
   - final lint-report status `OK`;
   - final status `CONSUMED_BY_SUCCESS_REPORT`;
   - final archive status `archived`;
   - final doctor status `WARN` or `PASS`;
   - final doctor JSON artifact path and sha256.
6. Update `codex_execution_report.md` so it explicitly identifies the final authoritative command-output artifact.
7. Update `pytest_result.txt` so it records the chosen authority strategy and the exact path/sha256/byte size/line count of the final authoritative artifact.
8. Update `codex_report_summary.files_changed` to include every file intentionally changed or created by this round.
9. Ensure `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
10. Archive this repair round into `project_state/rounds/round_20260610_rework_project_state_command_output_authority_v1/`.
11. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json` and record exact outputs or artifact metadata.
12. Record final `git status --short`.
13. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_command_output_authority_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_evidence_metadata.json`

Allowed only for verification, not intentional modification:

- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/doctor_post_archive.json`
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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_command_output_authority_v1
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
- A final authoritative command-output artifact is clearly identified in report and pytest.
- No artifact identified as final authoritative evidence contains `READY_FOR_EXECUTION`, report/decision mismatch, or doctor `FAIL`.
- If `all_command_outputs.json` remains with old failure text, it is explicitly labeled historical/non-authoritative with machine-readable fields.
- `codex_report_summary.files_changed`, `pytest_result.txt`, and final command-output metadata are mutually consistent.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Final doctor remains `FAIL`.
- A final authoritative artifact cannot be produced or identified.
- Any final authoritative artifact still shows `READY_FOR_EXECUTION`, report/decision mismatch, or doctor `FAIL`.
- Old `all_command_outputs.json` cannot be labeled historical/non-authoritative and no replacement final artifact is created.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
