```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260622_report_auto_summary_closeout_consistency_v1",
  "round_id": "round_20260622_report_auto_summary_closeout_consistency_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_run_round_scaffold_v1",
  "previous_round_id": "round_20260621_run_round_scaffold_v1",
  "previous_acceptance": "ACCEPTED_WITH_LIMITATIONS",
  "primary_goal": "Fix report-auto-summary and live codex_report_summary consistency around closeout/archive artifacts without expanding run-round into an executor.",
  "command_plan_authority_required": true,
  "accepted_requires_no_unauthorized_command_execution": true,
  "accepted_requires_pytest_result_and_execution_log_compatibility": true,
  "accepted_requires_report_auto_summary_consistency": true,
  "accepted_requires_final_check_passed_or_only_documented_nonblocking_historical_warnings": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/policy_impact_audit.json",
    "project_state/gates/policy_lint_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/run_round_result.json",
    "project_state/rounds/round_20260622_report_auto_summary_closeout_consistency_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/project_workspace_prompt.md",
    "docs/prompts/codex_execution_prompt.md",
    "docs/prompts/README.md"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement Report Auto-Summary Closeout Consistency v1.

The previous round added Run-Round Scaffold v1 and was accepted with limitations. The implementation goal was substantially met: `run-round` exists as a dry-run scaffold, `run_round_result.json` is produced, command-plan authority is preserved, and targeted/combined tests passed. The remaining limitation is not a missing run-round feature. It is a consistency warning between `codex_report_auto_summary.json`, live `codex_report_summary`, `report_summary_synthesis.json`, and closeout/archive artifacts after the closeout step updates round archive files.

This round must make report-auto-summary and final-check handle closeout/archive-generated artifacts deterministically so a valid current round does not remain in a `PARTIAL` / `NEEDS_REVIEW` state solely because post-closeout archive files or `final_gate_result.json` inclusion differ from the pre-closeout synthesized summary.

The intended outcome is:

- `report-auto-summary`, `report-summary`, and `final-check` agree on whether round archive files and `final_gate_result.json` are generated artifacts, live gate artifacts, closeout artifacts, or non-report-level artifacts;
- non-SUCCESS/PARTIAL status is not used as a fallback when the only remaining differences are explainable closeout/archive timing differences;
- `report_auto_summary_consistency` no longer warns for a valid current round whose summary and synthesis are otherwise consistent;
- no command-plan authority checks are weakened;
- no run-round execution functionality is added in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is background only. It still describes stale `samplereverse` reverse-solving work and must not control this round.

Current decision control: this `decision_packet.md` controls the current round. `task_packet.task` is only a stale suggestion and must not be used as execution authority.

Current state summary:

- `current_state.json` still reflects `state_20260618_134029_d6bd033d2532` / digest `d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5`.
- The state is sample-oriented and has many missing sample artifacts, but this round is engineering-only, so those missing sample artifacts are non-blocking unless the implementation claims sample evidence.
- `artifact_index.json` contains many missing sample artifacts; do not treat them as current evidence.
- `negative_results.json` applies to reverse-solving directions and is not directly relevant to this engineering round. Do not touch reverse-solving.

Previous round evidence:

- `decision_20260621_run_round_scaffold_v1` was accepted with limitations.
- `run_round_result.json` existed and reported dry-run `PASSED`.
- `execution_log.json` had no unauthorized command or omitted-command violation.
- `command_plan.json` used `full` profile with no omitted commands.
- `pytest_result.txt` recorded `755 passed` for `tests/test_project_gate.py -q` and `1053 passed` for `tests/test_project_gate.py tests/test_project_state.py -q`.
- `final_gate_result.json` had no blocking reasons but had warnings: `report_status is PARTIAL` and `report_auto_summary_consistency` mismatch for non-SUCCESS report.
- The mismatch involved generated/file lists differing around `final_gate_result.json`, `round_close_snapshot.json`, `run_closeout_result.json`, and archived `project_state/rounds/<round_id>/...` files.

Existing capabilities to reuse:

- `command-plan` and command kind classification.
- `execution_log.json` derived from `pytest_result.txt` and command-plan.
- `codex_report_auto_summary.json` synthesis from structured evidence.
- `build_report_summary_synthesis()`.
- `final-check` checks for report-summary consistency, command-plan authority, artifact coverage, closeout/archive coverage, and Required Audit coverage.
- `run-closeout` and round archive behavior.
- policy-lint and policy-impact checks.
- tests in `tests/test_project_gate.py`.

Gate/command-plan strategy:

- Use existing profiles only: `fast`, `standard`, `full`.
- Because this changes project gate/report-summary/final-check behavior, command-plan should normally select or require `full` validation.
- Tests section must remain subordinate to command-plan. Run only commands authorized by command-plan.
- Closeout may run only if command-plan authorizes it and gate profile allows it.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect or run sample binaries.
- Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, solvers, or full `solve_reports/`.
- Heavy historical artifacts may be read only by exact path if needed for a focused regression fixture. Do not scan full historical directories.

## 3. Do Not Do

Do not build a full autonomous `execute-decision` runner in this round.

Do not make `run-round` execute arbitrary implementation commands.

Do not add AgentRunner, job manager, database, queue, scheduler, web UI, daemon, message bus, GitHub Actions workflow, or API planner/auditor in this round.

Do not weaken command-plan authority to make warnings disappear.

Do not hide real mismatches by downgrading failures to warnings. Fix the classification/provenance rules so expected closeout/archive artifacts are handled explicitly.

Do not make `codex_report_summary.status` use unsupported values. Use supported project statuses such as `SUCCESS`, `PARTIAL`, `FAILED`, or `BLOCKED`; do not use `COMPLETED_WITH_LIMITATIONS`.

Do not modify prompt docs or `.codex-skills/` in this round.

Do not change profile names. The only valid profiles are `fast`, `standard`, and `full`; do not introduce `medium`.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `.codex-skills/registry.json`, or `docs/prompts/*`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

Do not push, commit, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Then inspect only files relevant to report-auto-summary / closeout consistency:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execution_log.json`
5. `project_state/gates/codex_report_auto_summary.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/round_delta_summary.json`
9. `project_state/gates/round_close_snapshot.json`
10. `project_state/gates/run_closeout_result.json`
11. `project_state/gates/run_round_result.json`
12. `project_state/rounds/round_20260621_run_round_scaffold_v1/round_manifest.json` only if needed to understand archive artifact classification.

Historical files may be read only by exact path when needed for a focused regression fixture. Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What exact inconsistency caused the previous `report_auto_summary_consistency` warning?
2. Which artifact classes now exist, and how are they classified: live gate artifacts, report-level generated artifacts, closeout artifacts, archive artifacts, and non-report-level artifacts?
3. How does `codex_report_auto_summary.json` decide whether to include `final_gate_result.json`, `round_close_snapshot.json`, `run_closeout_result.json`, and `project_state/rounds/<round_id>/*`?
4. How does `report_summary_synthesis.json` stay consistent with live `codex_report_summary` before and after closeout?
5. How does final-check distinguish real report-summary mismatches from expected closeout/archive timing differences?
6. How is `status` / `acceptance_recommendation` derived after this change, and under what conditions can the report be `SUCCESS` / `ACCEPTED`?
7. What regression tests prove the fix for post-closeout consistency, pre-closeout consistency, partial/non-success behavior, and real mismatch detection?
8. How does this round preserve command-plan authority, execution-log compatibility, run-round dry-run behavior, policy-impact, policy-lint, final-check, closeout, and prompt-doc behavior?

## 6. Implementation Scope

Implement one bounded feature: Report Auto-Summary Closeout Consistency v1.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/codex_report_auto_summary.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/rounds/round_20260622_report_auto_summary_closeout_consistency_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Identify the exact source of the previous generated_artifacts/files_changed mismatch between `codex_report_auto_summary.json`, live `codex_report_summary`, and `report_summary_synthesis.json`.
2. Introduce or harden a single deterministic classification rule for artifact inclusion.
3. Ensure live report summary and synthesized report summary use the same classification rule.
4. Ensure `report-auto-summary` does not omit archive artifacts when they are intentionally included in the live report, or alternatively ensure live report does not claim archive artifacts as report-level generated artifacts unless the synthesis also does.
5. Ensure `final_gate_result.json`, `round_close_snapshot.json`, and `run_closeout_result.json` have explicit classification instead of ad-hoc inclusion/exclusion.
6. Ensure final-check can still fail on real mismatches; do not suppress real inconsistency.
7. Ensure command-plan execution authority checks remain unchanged or stricter.
8. Ensure execution-log consistency checks remain unchanged or stricter.
9. Ensure run-round remains dry-run scaffold behavior unless explicitly invoked with future execute mode outside this round.
10. Add focused regression tests in `tests/test_project_gate.py` covering:
    - post-closeout archive artifact consistency;
    - pre-closeout summary consistency;
    - final_gate_result inclusion only when intended;
    - round_close_snapshot and run_closeout_result classification;
    - real generated_artifacts mismatch still warns or fails;
    - report status can reach `SUCCESS` only when all required checks are satisfied;
    - backward compatibility when closeout artifacts are absent.

Do not implement unrelated refactors. Do not move report-summary logic into a new subsystem. Do not add a database or workflow engine.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight before implementation:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
```

Then run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted tests, only if command-plan authorizes pytest:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Full project-state gate tests, only if command-plan authorizes them:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
```

Gate validation commands, only if command-plan authorizes them:

```powershell
python -m reverse_agent.project_gate policy-lint --state-dir project_state
python -m reverse_agent.project_gate policy-impact --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-auto-summary --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Closeout, only if command-plan explicitly includes/authorizes it and the gate profile allows closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260622_report_auto_summary_closeout_consistency_v1
```

Record every executed command in `project_state/pytest_result.txt`. Ensure `project_state/gates/execution_log.json` agrees with `pytest_result.txt` and `project_state/gates/command_plan.json`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` without source changes if:

- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is not one of `engineering_branch`, `reverse_solving`, `tool_integration`, `training_dataset`;
- `skill_profiles` do not match active registry entries;
- command-plan is missing, failed, or conflicts with Tests;
- command-plan does not authorize the command needed to proceed;
- startup path checks do not confirm `F:\reverse-agent` and the repository root;
- source/test files are already dirty in a way that cannot be recorded as baseline;
- implementation would require editing forbidden paths;
- implementation would require reading full `solve_reports/` or running reverse-solving tools;
- implementation would require changing `.codex-skills/` or prompt docs;
- final-check fails with blocking reasons;
- execution-log shows unauthorized commands or exit-code mismatches;
- report-auto-summary and live report remain inconsistent for reasons other than explicitly documented non-blocking historical/backlog artifacts.

Stop with `REWORK_REQUIRED` if tests fail, if Required Audit is incomplete, if report-summary mismatch remains unexplained, or if the fix merely suppresses warnings instead of defining artifact classification/provenance clearly.
