```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_clean_start_report_delta_rework_v1",
  "round_id": "round_20260617_clean_start_report_delta_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair the audit/report metadata inconsistency from `decision_20260617_clean_start_baseline_guard_v1` so actual source/test changes cannot disappear from `codex_report_summary.files_changed`, `report_summary_synthesis`, `final_gate_result`, or the final round delta.

This is a narrow rework. Do not rewrite the clean-start baseline guard. Keep the existing source/test clean-start policy, but make the reporting and final-gate evidence consistent and enforceable.

Required end state:

- if the report body claims a source/test file changed, that file must appear in `codex_report_summary.files_changed`;
- if Git changed filenames include source/test files, they must be represented in `files_changed` unless the working tree is already clean and the commit/archive evidence proves those changes were already committed before the current round;
- `report-summary` or `final-check` must fail when source/test changes are described in report prose but omitted from structured summary fields;
- temporary files/directories such as `tmp*/` must not remain as inherited dirty files in a successful closeout;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_clean_start_baseline_guard_v1`
- `round_20260617_clean_start_baseline_guard_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed inconsistency:

- `project_state/codex_execution_report.md` body claims source changes in `reverse_agent/project_gate.py` and test changes in `tests/test_project_gate.py`.
- The report summary `files_changed` omits both `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- `pytest_result.txt` startup `git status --short` did not show those source/test files dirty; it only showed project_state files, `project_state/gates/`, and `tmp8osv9s8n/`.
- `final_gate_result.json` concluded no source/test dirty files were present at startup and passed `startup_baseline_consistency`.
- A temporary path `tmp8osv9s8n/` appeared in startup/final dirty state and must not be treated as a valid long-lived project artifact.

Meaning:

- The clean-start guard implementation direction is useful, but the report/delta audit chain did not prove that actual source/test changes were fully captured.
- A successful closeout must not rely on report prose while structured `files_changed` omits claimed source/test files.

Existing useful implementation to preserve:

- `_baseline_lifecycle_checks()` no longer lets report prose retroactively authorize inherited dirty source/test files.
- ordinary `Allowed source files` / `Allowed tests` no longer authorize inherited dirty baseline files.
- generated `project_state/` files remain non-blocking for source/test clean-start policy.
- existing tests for clean-start policy are useful and should remain.

Artifact freshness:

- Historical `samplereverse` missing/stale artifacts are not current evidence for this engineering rework.
- This round does not depend on reverse sample artifacts.

Negative results:

- Do not return to old `sample_solver` blind search.
- Do not only increase beam/budget.
- Do not use `compare_semantics_agree=false` candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat old `samplereverse` failed candidate/runtime branches.

Allowed tool execution:

- Read repository source/tests and compact `project_state/` metadata.
- Run gate/status/test commands listed in the Tests section.
- Do not run local reverse samples, IDA, Ghidra, debugger, emulator, runtime probe, harness campaigns, or solver commands.

Heavy artifact policy:

- Do not read full `solve_reports/`.
- Do not read full `PROJECT_PROGRESS_LOG.txt`.

## 3. Do Not Do

Do not rewrite the clean-start guard from scratch.

Do not weaken existing gate, report-summary, final-check, or close-round checks.

Do not let report prose substitute for `codex_report_summary.files_changed` or `generated_artifacts`.

Do not keep `tmp8osv9s8n/` or any `tmp*/` path as an accepted round artifact or inherited dirty file.

Do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, runtime probe, GUI/frontend, sample runner, raw sample, or `.codex-skills/` files.

Do not run sample binaries.

Do not run IDA/Ghidra/debugger/harness/solver/runtime probe commands.

Do not change training sample statuses.

Do not add a database, queue system, workflow engine, or new external dependency.

Do not treat `task_packet.task` as current execution authority.

## 4. Files To Inspect

Read default project-state files in order:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Also inspect:

- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260617_clean_start_baseline_guard_v1/round_manifest.json`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/status plumbing requires it
- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed
- current Git changed filenames / diff summary

Do not inspect unrelated solver/harness/tool-runner modules unless a failing test directly requires it.

## 5. Required Audit

Before implementation, confirm:

1. Startup path is `F:\reverse-agent`, `Test-Path F:\reverse-agent` is true, and `git rev-parse --show-toplevel` points to this repository.
2. Startup `git status --short` is recorded before any file modification.
3. If startup `git status --short` already shows source/test dirty files, stop immediately and write `codex_execution_report.md` with `status=BLOCKED`; do not implement changes.
4. If startup `git status --short` shows `tmp*/` or other temporary files/directories, remove them if they are safe temporary files; otherwise stop and report `BLOCKED`.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. Current decision controls execution; `task_packet.json` is not authoritative.
7. Confirm the previous report/body-vs-summary inconsistency before changing code.
8. No mature reverse-engineering tool integration needs to be modified.

## 6. Implementation Scope

Allowed source files:

- `reverse_agent/project_gate.py`
- `reverse_agent/project_state.py` only if report/status plumbing strictly requires it

Allowed tests:

- `tests/test_project_gate.py`
- `tests/test_project_state.py` only if project_state support is changed

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/preflight_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_clean_start_report_delta_rework_v1/*`

Required implementation behavior:

- Add a report-summary/final-check check that extracts claimed source/test paths from `codex_execution_report.md` sections such as `Source Changes`, `Test Changes`, and bullet lists containing backticked paths.
- If a claimed source/test path is absent from `codex_report_summary.files_changed`, fail report-summary or final-check with a clear error.
- Keep generated `project_state/` artifacts out of this source/test claimed-change check unless they are explicitly part of `generated_artifacts` validation.
- Add or harden detection for temporary paths such as `tmp*/` in dirty state; they should be removed before successful closeout or treated as blocking if still present.
- Ensure `files_changed_covers_substantive_changes` cannot pass when source/test files are omitted but report prose says they changed.
- Preserve the existing clean-start baseline guard behavior.
- Preserve the gate-profile classifier behavior.
- Preserve backward compatibility for existing command-plan/final-check/close-round tests.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. Report body claims `reverse_agent/project_gate.py` in Source Changes but summary `files_changed` omits it: report-summary or final-check must fail.
2. Report body claims `tests/test_project_gate.py` in Test Changes but summary `files_changed` omits it: report-summary or final-check must fail.
3. Claimed source/test file present in `files_changed`: check passes.
4. Project_state generated artifacts in report prose do not trigger the source/test claimed-change failure path.
5. Temporary path such as `tmp8osv9s8n/` in final dirty/inherited dirty state is blocking or explicitly removed before closeout.
6. Existing clean-start baseline guard tests continue to pass.
7. Existing gate-profile tests continue to pass.

## 7. Tests

Run and record the following commands in `project_state/pytest_result.txt`:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate gate-profile --state-dir project_state --json
python -m reverse_agent.project_gate run-round --state-dir project_state --dry-run --json
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_state lint-report --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_clean_start_report_delta_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_clean_start_report_delta_rework_v1`
- `round_id=round_20260617_clean_start_report_delta_rework_v1`
- the final `report_id`
- all commands actually run

## 8. Stop Conditions

Stop and report `BLOCKED` without expanding scope if:

- current `decision_packet.md` is no longer this decision;
- `.codex-skills/registry.json` does not contain active `reverse-agent-iteration@v2`;
- startup `git status --short` already shows source/test dirty files before implementation begins;
- temporary paths such as `tmp*/` cannot be safely removed or explained;
- implementing this requires rewriting close-round or replacing the existing gate system;
- the change would require modifying solver/harness/tool-runner/debugger/sample code;
- tests fail for reasons outside the narrow report/delta audit consistency scope;
- the check cannot distinguish source/test claim paths from project_state generated artifact paths without broad refactoring.
