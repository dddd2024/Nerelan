```json decision_meta
{"schema_version":1,"decision_id":"decision_20260610_rework_project_state_workspace_diff_audit_v1","round_id":"round_20260610_rework_project_state_workspace_diff_audit_v1","based_on_state_build_id":"state_20260610_131714_88c14099a13a","based_on_state_digest":"88c14099a13a2bf2999e4a61b2c53d8edd9568217bb5ee36f0cfd4462e8cbbd2","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2","samplereverse-frontier@v2"]}
```

# DECISION_PACKET

## 1. Goal

Repair the remaining audit defect from the final `project_state doctor` evidence round by producing a trustworthy workspace-change audit and, if necessary, cleaning or explaining out-of-scope modified files.

The previous round successfully proved final live-state `doctor` as `WARN` and recorded complete `doctor --json` output. Do not rework doctor behavior. The remaining blocker is that the recorded `git status --short` listed modified source, test, decision, model_gate, and task_packet files, while the report claimed only `project_state/codex_execution_report.md` and `project_state/pytest_result.txt` changed. The recorded scoped `git diff` also claimed no diff despite modified scoped paths.

This is an `engineering_branch` workspace-evidence repair round. It must reconcile `git status`, `git diff`, `git diff --cached`, `files_changed`, and report scope. It must not expand into reverse solving, sample execution, or doctor feature work.

## 2. Current Evidence

- Previous audit conclusion: `REWORK_REQUIRED`.
- Previous decision: `decision_20260610_rework_project_state_doctor_final_doctor_evidence_v1`.
- Previous report: `report_20260610_rework_project_state_doctor_final_doctor_evidence_v1`, `status: SUCCESS`, bound to that decision.
- Previous pytest result recorded `167 passed in 37.08s`.
- Previous final `doctor` output was `doctor: WARN`; all decision/report/pytest/archive checks passed, with only artifact freshness warning: `3 missing, 48 stale artifacts`.
- Previous `doctor --json` output was complete and had `status: WARN`, full `checks`, and `decision_execution_state: CONSUMED_BY_SUCCESS_REPORT`.
- Previous round archive exists at `project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1/round_manifest.json`.
- Blocking problem: previous `git status --short` recorded modified files outside the stated scope: `project_state/decision_packet.md`, `project_state/model_gate.json`, `project_state/task_packet.json`, `reverse_agent/project_state.py`, and `tests/test_project_state.py`, plus the new round archive directory.
- Blocking problem: previous report declared no source changes, but `git status --short` showed `reverse_agent/project_state.py` and `tests/test_project_state.py` as modified.
- Blocking problem: previous scoped `git diff -- ...` claimed no diff while scoped modified paths existed, making the self-check record inconsistent.
- `task_packet.json` remains advisory. This `decision_packet.md` controls the current round.
- `model_gate.json` and sample-state evidence remain context only and must not drive this round into reverse solving.
- Negative results still block blind search, candidate expansion, repeated stale runtime probes, and full `solve_reports/` scans.

## 3. Do Not Do

- Do not modify `.codex-skills/`.
- Do not start or run any sample-solving workflow.
- Do not run sample binaries.
- Do not generate, mutate, rank, validate, or emit candidates or flags.
- Do not run solver/search expansion.
- Do not run runtime probes, debuggers, emulators, hooks, sidecars, IDA, Ghidra, OllyDbg, x64dbg, Frida, or pywinauto.
- Do not inspect full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
- Do not change doctor behavior unless a command needed for this audit genuinely fails because of a code defect.
- Do not rewrite `reverse_agent/project_state.py` or `tests/test_project_state.py` merely to make status clean.
- Do not mutate previous archived rounds.
- Do not hide out-of-scope modifications by omitting them from `git status`, `git diff`, or report scope.
- Do not claim `git diff` has no output when `git status --short` shows unstaged modifications for the same scoped paths.
- Do not claim staged files are absent unless `git diff --cached -- ...` proves it.

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

Optional only to compare previous evidence:

- `project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1/round_manifest.json`
- `project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1/pytest_result.txt`

Do not inspect unrelated harness runs. Do not inspect full `solve_reports/`.

## 5. Required Audit

Codex must:

1. Confirm this decision packet is the active execution authority and `task_packet.json` is advisory only.
2. Confirm both skill profiles are active in `.codex-skills/registry.json`.
3. Run and record full `git status --short` before any cleanup.
4. Run and record full scoped `git diff -- ...` over all files that may appear in status for this round.
5. Run and record full scoped `git diff --cached -- ...` over the same paths.
6. If `reverse_agent/project_state.py` or `tests/test_project_state.py` is modified, determine whether the change belongs to this round, a previous uncommitted round, or a generated/formatting artifact. Record the provenance.
7. If `project_state/model_gate.json` or `project_state/task_packet.json` is modified, determine whether it was changed by project-state build/status logic or accidentally touched. Record the provenance.
8. If any out-of-scope modifications are not required for this round, revert or leave them uncommitted only if the report explicitly explains why they remain and why they must not be included in `files_changed`.
9. Ensure `codex_report_summary.files_changed` matches the actual files intentionally changed by this round.
10. Ensure `pytest_result_summary.tests_ran` covers every command claimed in `codex_report_summary.tests_ran`.
11. Archive this round into `project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1/`.
12. After archive, run final `lint-report`, `status`, `doctor`, and `doctor --json`.
13. Record final `git status --short`, final scoped `git diff -- ...`, and final scoped `git diff --cached -- ...` after all report/pytest/archive updates.
14. The final report must explicitly state whether any source files changed in this round. If source files did not intentionally change, say so and prove it with diff evidence.
15. Do not run any sample, solver, candidate validation, runtime probe, debugger, emulator, IDA, Ghidra, hook, or sidecar.

## 6. Implementation Scope

Allowed without further justification:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1/*`

Allowed only if proven as project-state bookkeeping and explicitly explained:

- `project_state/model_gate.json`
- `project_state/task_packet.json`

Allowed only if existing uncommitted source changes must be retained and provenance is documented:

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
pwd
git rev-parse --show-toplevel
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1 project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1 project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1
python -m pytest tests/test_project_state.py -q
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state archive-round --state-dir project_state --round-id round_20260610_rework_project_state_workspace_diff_audit_v1
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_state status --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state doctor --state-dir project_state --json
git status --short
git diff -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1 project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1
git diff --cached -- reverse_agent/project_state.py tests/test_project_state.py project_state/decision_packet.md project_state/codex_execution_report.md project_state/pytest_result.txt project_state/model_gate.json project_state/task_packet.json project_state/rounds/round_20260610_rework_project_state_doctor_final_doctor_evidence_v1 project_state/rounds/round_20260610_rework_project_state_workspace_diff_audit_v1
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
- Final `doctor --json` output is complete parseable JSON, with `status` equal to `PASS` or `WARN`.
- Final `git status --short` is recorded.
- Final scoped `git diff -- ...` is recorded and is consistent with final `git status --short`.
- Final scoped `git diff --cached -- ...` is recorded and is consistent with final `git status --short`.
- If source files are listed as modified, report must either include them in `files_changed` with provenance or explicitly prove they are prior uncommitted changes not created by this round.
- `codex_report_summary.files_changed` must match the files intentionally changed by this round.
- No `.codex-skills/` changes.
- No sample/tool/debugger/solver/probe/IDA/Ghidra execution.

## 8. Stop Conditions

Stop and report `BLOCKED` or `FAILED` if:

- Repository root is not `F:\reverse-agent`.
- Final `git status`, `git diff`, and report `files_changed` cannot be reconciled.
- Source files appear modified and Codex cannot determine whether they belong to this round or previous uncommitted work.
- Final `lint-report` fails.
- Final status cannot reach consumed/archived state.
- Final doctor remains `FAIL`.
- The repair requires sample execution, solver execution, candidate validation, runtime probe, debugger, emulator, IDA, or Ghidra.
- `.codex-skills/` changes are required.
- The round shifts from `engineering_branch` into reverse solving or tool execution.
