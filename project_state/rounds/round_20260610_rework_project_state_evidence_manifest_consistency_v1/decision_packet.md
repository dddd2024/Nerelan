```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_evidence_manifest_consistency_v1","round_id":"round_20260610_rework_project_state_evidence_manifest_consistency_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining evidence-manifest consistency defects from `decision_20260610_rework_project_state_full_evidence_outputs_v1`.

The previous round executed and created evidence artifacts, including `doctor_result_final.json`, but `codex_report_summary.files_changed`, `pytest_result.txt`, and `evidence_metadata.json` are not fully aligned. This round must make the evidence chain internally consistent and auditable without changing doctor behavior or running any sample-solving workflow.

This is an `engineering_branch` evidence bookkeeping repair. It is not a reverse-solving, tool-integration, or training-dataset round.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_full_evidence_outputs_v1`.
- Previous report: `report_20260610_rework_project_state_full_evidence_outputs_v1`, status `SUCCESS`, bound to the previous decision.
- Previous pytest result: `167 passed in 73.91s`, bound to the previous decision/report/round.
- Previous archive exists at `project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1/round_manifest.json`.
- Previous final status showed consumed and archived.
- Previous `doctor_result_final.json` exists at `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json`; it is complete valid JSON with status `WARN` and `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Blocking defect: `codex_report_summary.files_changed` omits `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json` even though `evidence_metadata.json` lists it.
- Blocking defect: `pytest_result.txt` final `doctor --json` section only says `(complete valid JSON output...)`; it does not record the final artifact path, sha256, byte size, line count, and status.
- Blocking defect: `git_diff_scoped.patch` appears incomplete or captured mid-write: it only contains a partial diff for `project_state/codex_execution_report.md` and ends at a truncated line `+| \`lint-repor`.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- `model_gate.json` and sample-state evidence are context only and must not drive reverse solving.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not change doctor behavior.
- Do not rewrite `reverse_agent/project_state.py` or `tests/test_project_state.py` merely to make status clean.
- Do not mutate previous archived rounds.
- Do not delete `doctor_result_final.json`; reconcile metadata and report/pytest around it.
- Do not use English summaries as substitutes for evidence metadata when an artifact path and sha256 are required.
- Do not claim `git_diff_scoped.patch` is complete unless the regenerated artifact is a full patch output or the report explicitly explains why only a subset is expected.

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
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch`
- `reverse_agent/project_state.py`
- `tests/test_project_state.py`

Optional only to compare previous evidence:

- `project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1/round_manifest.json`
- `project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1/pytest_result.txt`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Verify `doctor_result_final.json` exists, is valid JSON, and has status `WARN` or `PASS`.
4. Update `codex_report_summary.files_changed` so it includes every evidence artifact intentionally created or updated by this repair, including `doctor_result_final.json`.
5. Update `pytest_result.txt` final `doctor --json` section to record `doctor_result_final.json` path, sha256, byte size, line count, status, and exact generation command.
6. Update `evidence_metadata.json` if needed so it matches the report and pytest result exactly.
7. Regenerate `git_diff_scoped.patch` from the real scoped `git diff -- ...` command, or clearly replace it with a complete scoped patch artifact. It must not be a truncated mid-write diff.
8. Record `git_diff_scoped.patch` path, sha256, byte size, line count, and exact generation command in both report and pytest result.
9. Keep `git_diff_cached.patch` as empty only if `git diff --cached -- ...` is truly empty; record path, sha256, byte size, line count, and exact generation command.
10. Ensure `pytest_result_summary.tests_ran` covers every command claimed in `codex_report_summary.tests_ran`.
11. Archive this repair round into `project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1/`.
12. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
13. Record final `git status --short`.
14. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1/*`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/evidence_metadata.json`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_scoped.patch`
- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/git_diff_cached.patch`

Allowed only if already present and provenance is documented; do not modify intentionally in this round:

- `project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1/doctor_result_final.json`
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

Run and record exact outputs in `project_state/pytest_result.txt`. For artifacts, record path, sha256, byte size, line count, and exact command used to generate or verify them.

```bash
pwd
git rev-parse --show-toplevel
git status --short
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/evidence/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/rounds/round_20260610_rework_project_state_full_evidence_outputs_v1 project_state/rounds/round_20260610_rework_project_state_evidence_manifest_consistency_v1
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_evidence_manifest_consistency_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
```

Acceptance requirements:

- `pwd` and `git rev-parse --show-toplevel` prove the local repository root is `F:\reverse-agent`.
- `python -m pytest tests/test_project_state.py -q` passes.
- Final `lint-report` is OK.
- Final status shows `decision_report_id_match: True`.
- Final status shows `decision_consumed_by_report: True`.
- Final status shows `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Final status shows `round_manifest_present: True` and `archive_status: archived`.
- Final `doctor` output is `PASS` or `WARN`, not `FAIL`.
- Final `doctor --json` output is complete valid JSON or saved as an artifact with path and sha256.
- `doctor_result_final.json` is listed in `codex_report_summary.files_changed` or explicitly marked as existing prior artifact with provenance; if used for final evidence, it must be referenced in pytest and report.
- `pytest_result.txt` records `doctor_result_final.json` path, sha256, byte size, line count, status, and exact command.
- `git_diff_scoped.patch` is complete real patch output or report explains the limited scope with evidence.
- `git_diff_cached.patch` is complete real output; empty output is acceptable if explicitly recorded.
- `codex_report_summary.files_changed`, `pytest_result.txt`, and `evidence_metadata.json` are mutually consistent.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- `doctor_result_final.json` cannot be verified as complete valid JSON.
- `doctor_result_final.json` metadata cannot be reconciled across report, pytest, and evidence metadata.
- Real scoped `git diff` output cannot be recorded inline or as an artifact with sha256.
- `codex_report_summary.files_changed`, `pytest_result.txt`, and `evidence_metadata.json` cannot be made consistent.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
