```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260617_generated_artifact_existence_rework_v1",
  "round_id": "round_20260617_generated_artifact_existence_rework_v1",
  "based_on_state_build_id": "state_20260615_150220_24f61a9ac337",
  "based_on_state_digest": "24f61a9ac337b596ff7d56b3e29f01e5ab68342825fb2a32ba50b65a84512bae",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

# DECISION_PACKET

## 1. Goal

Repair generated-artifact existence and summary consistency checks so `codex_report_summary.generated_artifacts`, `report_summary_synthesis`, `final_gate_result`, and the actual repository state cannot disagree about whether a project-state artifact exists or was generated.

This is a narrow engineering rework after `decision_20260617_clean_start_report_delta_rework_v1`. The previous round fixed source/test prose-to-files_changed coverage and removed the `tmp8osv9s8n` dirty path, but still allowed `project_state/gates/run_round_result.json` to be listed in generated artifacts even though the live repository path was absent.

Required end state:

- `generated_artifacts` entries for live `project_state/` artifacts must either exist at final-check time or be explicitly recognized as deleted/not-generated with a blocking or clearly explained policy;
- `report_summary_synthesis` and `final_gate_result` must detect generated artifacts that are listed but missing;
- `report_summary_fields_match_synthesis` must compare `files_changed` and `generated_artifacts` with enough strictness to catch report/synthesis mismatches;
- `run_round_result.json` must not remain in `generated_artifacts` if it is not present or not generated in the current round;
- do not modify solver, harness, IDA/Ghidra/debugger/tool-runner, sample runner, GUI/frontend, raw samples, or `.codex-skills/` behavior.

## 2. Current Evidence

Current execution authority is this `project_state/decision_packet.md`. `task_packet.json` and `current_state.json` are state inputs only and must not override this decision.

Previous round requiring rework:

- `decision_20260617_clean_start_report_delta_rework_v1`
- `round_20260617_clean_start_report_delta_rework_v1`
- mainline: `engineering_branch`
- GPT audit conclusion: `REWORK_REQUIRED`

Observed facts from the previous audit:

- `codex_report_summary.files_changed` correctly included `reverse_agent/project_gate.py` and `tests/test_project_gate.py`.
- Startup `git status --short` showed no source/test dirty and no `tmp8osv9s8n/` path.
- `report_prose_claims_covered_by_files_changed` passed.
- `tmp_paths_absent_from_dirty_state` passed.
- However, `codex_report_summary.generated_artifacts` contained `project_state/gates/run_round_result.json`.
- `report_summary_synthesis.generated_artifacts` also contained `project_state/gates/run_round_result.json`.
- The live repository path `project_state/gates/run_round_result.json` was absent when fetched from GitHub.
- `final_dirty_files`, `git_changed_files`, and `required_round_delta_files` did not prove the file existed.
- Yet final gate still reported `report_summary_fields_match_synthesis: PASS`.

Meaning:

- The source/test claim problem was fixed.
- The remaining defect is generated-artifact existence and structural summary consistency.
- A successful closeout must not claim a generated artifact that is absent from the live project-state path unless the gate has an explicit deletion/non-generation policy and records it.

Existing useful implementation to preserve:

- clean-start baseline guard behavior;
- report-prose claimed source/test coverage;
- `tmp*/` dirty-state blocking behavior;
- gate-profile classifier behavior;
- current command-plan/final-check/close-round flow.

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

Do not rewrite the clean-start guard.

Do not rewrite report-summary or final-check from scratch.

Do not weaken existing gate, report-summary, final-check, or close-round checks.

Do not keep missing live project-state paths in `generated_artifacts` without an explicit blocking or documented non-generation policy.

Do not let `generated_artifacts` and live file existence drift silently.

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

- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_round_result.json` if present; if absent, record absence explicitly
- `project_state/gates/command_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/rounds/round_20260617_clean_start_report_delta_rework_v1/round_manifest.json`
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
4. If startup `git status --short` shows `tmp*/` or other temporary files/directories, remove them if safe; otherwise stop and report `BLOCKED`.
5. `decision_meta` is valid, `status=APPROVED`, `mainline=engineering_branch`, and `reverse-agent-iteration@v2` is active.
6. Current decision controls execution; `task_packet.json` is not authoritative.
7. Confirm whether `project_state/gates/run_round_result.json` exists at startup and after running `run-round --dry-run --json`.
8. Confirm the previous generated-artifact existence inconsistency before changing code.
9. No mature reverse-engineering tool integration needs to be modified.

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
- `project_state/gates/run_round_result.json` only if the command actually writes it and it exists at final-check time
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/rounds/round_20260617_generated_artifact_existence_rework_v1/*`

## Allowed Inherited Dirty Baseline Files

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Required implementation behavior:

- Add a generated-artifact existence check for live `project_state/` artifact paths listed in `generated_artifacts`.
- Exclude archive paths under `project_state/rounds/<round_id>/` from live-path existence requirements if they are validated by round manifest/archive checks.
- If a generated artifact path is under `project_state/gates/` or another live `project_state/` path, it must exist at final-check/report-summary time unless explicitly classified as intentionally absent and removed from generated_artifacts.
- If `run_round_result.json` is not created by the current `run-round --dry-run --json` behavior, remove it from synthesized and reported `generated_artifacts`; otherwise ensure it exists and is covered by tests.
- Strengthen `report_summary_fields_match_synthesis` so mismatches in `files_changed` and `generated_artifacts` cannot be hidden by partial comparison or unordered/list handling issues.
- Preserve the existing clean-start baseline guard behavior.
- Preserve the report-prose claimed source/test coverage behavior.
- Preserve the `tmp*/` dirty-state check.
- Preserve the gate-profile classifier behavior.
- Preserve backward compatibility for existing command-plan/final-check/close-round tests.
- Preserve path normalization across Windows and POSIX separators.

Required tests:

1. A live `project_state/gates/missing_artifact.json` listed in `generated_artifacts` but absent on disk must fail report-summary or final-check.
2. An existing live `project_state/gates/command_plan.json` listed in `generated_artifacts` must pass.
3. Archive artifacts under `project_state/rounds/<round_id>/...` remain validated by existing round archive checks, not by the live gate artifact existence check.
4. `run_round_result.json` is included in `generated_artifacts` only if it exists or is intentionally generated by `run-round`.
5. A mismatch between report summary `files_changed` and synthesized `files_changed` must fail.
6. A mismatch between report summary `generated_artifacts` and synthesized `generated_artifacts` must fail.
7. Existing clean-start baseline guard tests continue to pass.
8. Existing report prose claim coverage tests continue to pass.
9. Existing tmp-path dirty-state tests continue to pass.
10. Existing gate-profile tests continue to pass.

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
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260617_generated_artifact_existence_rework_v1
```

The pytest result header must include:

- `decision_id=decision_20260617_generated_artifact_existence_rework_v1`
- `round_id=round_20260617_generated_artifact_existence_rework_v1`
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
- generated-artifact existence cannot be checked without broad refactoring;
- tests fail for reasons outside the narrow generated-artifact existence/report-summary scope.
