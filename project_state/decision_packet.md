```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_final_evidence_convergence_v1","round_id":"round_20260610_rework_project_state_final_evidence_convergence_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the final evidence-convergence defects from `decision_20260610_rework_project_state_command_log_exactness_v1`.

The previous round improved command coverage, but the live report, pytest result, doctor JSON artifacts, evidence metadata, and command output artifacts still disagree about final doctor status and `doctor_result_final.json` sha256. This round must converge all final evidence onto one coherent set of facts.

This is an `engineering_branch` evidence convergence repair. It must not change doctor behavior, must not modify source code, and must not run any reverse-solving, sample, solver, debugger, IDA, Ghidra, emulator, hook, sidecar, or runtime-probe workflow.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_command_log_exactness_v1`.
- Previous report: `report_20260610_rework_project_state_command_log_exactness_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest result: `167 passed in 69.74s`, bound to the previous decision/report/round.
- Previous `pytest_result_summary.tests_ran` now included required commands such as `pwd`, `git rev-parse --show-toplevel`, `git status --short`, scoped `git diff -- ...`, scoped `git diff --cached -- ...`, pytest, lint/status/doctor, archive, final doctor, and `git fsck --full`.
- Blocking defect: `pytest_result.txt` says post-archive doctor is `WARN`, but `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/doctor_post_archive.json` has `status: FAIL` and still points to `report_20260610_rework_project_state_evidence_manifest_consistency_v1`.
- Blocking defect: `doctor_result_final.json` sha256 is inconsistent across evidence files. `evidence_metadata.json` still lists `4bcbf6183d7900d4e931004ee64ede858e4edf24d5ef3886d28a98ea282dba05`, while command-log artifacts/report claim `c5c8f711ce7c7b11f4acf3ebe2189631d8308c5d8baa64e96fbcf3442beb7592`.
- Blocking defect: `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json` records `doctor_result_final_match: false`.
- Blocking defect: `all_command_outputs.json` contains post-archive outputs showing report/decision mismatch and `READY_FOR_EXECUTION`, which conflicts with live `pytest_result.txt` and report claims of consumed/archived final state.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- `model_gate.json` and sample-state evidence are context only and must not drive reverse solving.
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
- Do not introduce new hashes, placeholder hashes, abbreviated JSON, or unsupported explanations.
- Do not keep any final evidence artifact that says final doctor is `FAIL` unless the report status is also `FAILED` or `BLOCKED`. For a successful repair, final doctor artifacts must show `PASS` or `WARN`.
- Do not allow `doctor_result_final_match: false` or equivalent mismatch markers to remain in final command evidence.

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
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/doctor_post_archive.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/doctor_pre_archive.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/git_diff_cached.patch`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/git_fsck_full.txt`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Run final post-report/post-pytest/post-archive `python -m reverse_agent.project_state doctor --state-dir project_state` and `python -m reverse_agent.project_state doctor --state-dir project_state --json` only after `codex_execution_report.md` and `pytest_result.txt` are updated for this round.
4. Save the final post-archive doctor JSON for this round to `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/doctor_post_archive.json`.
5. The final `doctor_post_archive.json` must have `status` equal to `PASS` or `WARN`, not `FAIL`, and must reference `report_20260610_rework_project_state_final_evidence_convergence_v1`.
6. Choose one canonical sha256 for `doctor_result_final.json` by computing the actual current file content hash. Record that exact value in:
   - `project_state/codex_execution_report.md`
   - `project_state/pytest_result.txt`
   - `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
   - `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json`, if still referenced
   - `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/final_evidence_metadata.json`
7. Remove or replace any final evidence marker equivalent to `doctor_result_final_match: false`. Final evidence must either show `true` or not make a comparison claim.
8. If preserving `all_command_outputs.json`, clearly mark mismatch/READY_FOR_EXECUTION entries as pre-report/pre-archive evidence, or create a new final command output artifact that records only the final post-archive state.
9. Update `codex_report_summary.files_changed` so it lists every file intentionally modified or created by this repair round.
10. Ensure `codex_report_summary.tests_ran` and `pytest_result_summary.tests_ran` match command-for-command.
11. Ensure `codex_report_summary.files_changed`, `pytest_result.txt`, `evidence_metadata.json`, `command_outputs.json`, and final doctor artifacts are mutually consistent.
12. Archive this repair round into `project_state/rounds/round_20260610_rework_project_state_final_evidence_convergence_v1/`.
13. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json` and record exact outputs or artifact metadata.
14. Record final `git status --short`.
15. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_final_evidence_convergence_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/all_command_outputs.json`
- `project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1/doctor_post_archive.json`
- `project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1/*`

Allowed only if already present and provenance is documented; do not intentionally modify source/test content:

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
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_final_evidence_convergence_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Only if continuing to rely on git-corruption evidence, preserve or re-record exact metadata for:

```bash
git fsck --full
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1 project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1 project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1 project_state/rounds/round_20260610_rework_project_state_final_evidence_convergence_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/evidence/round_20260610_rework_project_state_command_log_exactness_v1 project_state/evidence/round_20260610_rework_project_state_final_evidence_convergence_v1 project_state/rounds/round_20260610_rework_project_state_command_log_exactness_v1 project_state/rounds/round_20260610_rework_project_state_final_evidence_convergence_v1
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
- `doctor_post_archive.json` for this round has `status` `PASS` or `WARN` and references current report id.
- `doctor_result_final.json` sha256 is identical across report, pytest, evidence metadata, command output metadata, and final evidence metadata.
- No `doctor_result_final_match: false` or equivalent mismatch marker remains in final evidence.
- No final command output artifact claims `READY_FOR_EXECUTION` or report/decision mismatch unless it is clearly labeled as pre-report/pre-archive evidence.
- `codex_report_summary.files_changed`, `pytest_result.txt`, evidence metadata, command output metadata, and final doctor artifacts are mutually consistent.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Final doctor remains `FAIL`.
- `doctor_post_archive.json` cannot be generated with current report id and `PASS`/`WARN` status.
- `doctor_result_final.json` sha256 cannot be reconciled across report, pytest, metadata, and command output evidence.
- Any final evidence still contains `doctor_result_final_match: false`.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
