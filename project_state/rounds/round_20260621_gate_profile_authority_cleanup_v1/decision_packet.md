```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_gate_profile_authority_cleanup_v1",
  "round_id": "round_20260621_gate_profile_authority_cleanup_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "rework_target_decision_id": "decision_20260621_closeout_authorization_report_summary_rework_v1",
  "rework_target_round_id": "round_20260621_closeout_authorization_report_summary_rework_v1",
  "primary_warning_checks": [
    "command_plan_execution_authority",
    "status_policy_valid"
  ],
  "primary_cleanup_goal": "Resolve gate-profile command authorization/report consistency drift after closeout/report-summary rework.",
  "command_plan_authority_required": true,
  "accepted_requires_final_check_no_blocking_failures": true,
  "accepted_requires_tests_ran_match_pytest_result_commands": true,
  "forbid_hiding_unauthorized_command_evidence": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "allowed_state_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/rounds/round_20260621_gate_profile_authority_cleanup_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Clean up the remaining command-plan authority/report consistency warning after `decision_20260621_closeout_authorization_report_summary_rework_v1`.

Do not redo the closeout/report-summary fix. The previous rework fixed the original `report_summary_fields_match_synthesis` blocker and created a round archive, but `final-check` still reports a command-plan authority warning because `gate-profile` was executed without being listed in `command_plan.commands`. This round must define and enforce the correct policy for `gate-profile`: planned command, exempt diagnostic command, or forbidden unless explicitly authorized.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is only background and must not control this round. It still reflects stale/sample-derived `samplereverse` work.

Current decision before this packet was `decision_20260621_closeout_authorization_report_summary_rework_v1`. That round repaired the main closeout/report-summary drift:

- `command-plan` now lists `run-closeout` as an authorized command for the full profile.
- Round archive files exist and are listed in the report/gate artifacts.
- `report_summary_fields_match_synthesis` now passes.
- `pytest_result_exit_codes_match_command_plan` passes.
- Required Audit coverage passes.

Remaining issue:

- `project_state/gates/final_gate_result.json` has `gate_status=WARN`, not clean PASS.
- `command_plan_execution_authority` warns that `python -m reverse_agent.project_gate gate-profile --state-dir project_state` was executed even though `gate-profile` is not in `required_command_kinds` and not present in `command_plan.commands`.
- `codex_execution_report.md` has `status=PARTIAL` and `acceptance_recommendation=NEEDS_REVIEW`.
- `codex_report_summary.tests_ran` does not fully reflect all actual command blocks in `pytest_result.txt`, especially repeated `gate-profile` invocations.

Existing capabilities to reuse:

- `reverse_agent.project_gate.command_plan`
- `reverse_agent.project_gate.gate_profile`
- `reverse_agent.project_gate.final_check`
- `reverse_agent.project_gate.report_summary`
- `_command_plan_execution_authority_check()`
- `_parse_recorded_command_blocks()`
- `_command_kind()`
- tests in `tests/test_project_gate.py`

No reverse-solving, sample execution, runtime probing, debugger/emulator work, IDA/Ghidra/OllyDbg/x64dbg work, or full `solve_reports/` scan is allowed.

## 3. Do Not Do

Do not redo or weaken the closeout/report-summary fix from the prior round.

Do not weaken `command_plan_execution_authority` to hide unauthorized commands.

Do not delete or rewrite evidence merely to hide that `gate-profile` was executed. If the command was executed, either authorize it correctly, exempt it with a precise policy, or keep the warning and report `REWORK_REQUIRED`.

Do not treat `task_packet.json` as current task authority.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, or `.codex-skills/registry.json`.

Do not continue `samplereverse` solving. Do not run samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, runtime probes, GUI workflows, or full `solve_reports/` scans.

Do not rename `standard` to `medium`.

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

Then inspect only files relevant to this cleanup:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/gate_profile_plan.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/run_closeout_result.json` if needed
9. `project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/round_manifest.json` only if needed to confirm prior closeout state

Historical files may be read only by exact path. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Why was `gate-profile` executed even though it was not in `command_plan.commands`?
2. Should `gate-profile` be a planned command, an exempt diagnostic command, or forbidden unless explicitly authorized? State the policy.
3. Does `codex_report_summary.tests_ran` exactly match all non-exempt command blocks in `pytest_result.txt`?
4. Does `command_plan_execution_authority` return PASS after the fix? If not, why is the remaining WARN acceptable or not acceptable?
5. Does final-check have no blocking failures?
6. Is report status consistent with final gate status and project schema?
7. How does the fix avoid hiding unauthorized commands by merely deleting evidence?
8. What regression tests prevent this drift from recurring?

## 6. Implementation Scope

Implement one bounded cleanup: resolve `gate-profile` command authorization/report consistency drift.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed state/artifact updates:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/preflight_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260621_gate_profile_authority_cleanup_v1/*` only if command-plan authorizes closeout

Acceptable implementation approaches, choose the smallest correct one:

1. If `gate-profile` is part of the intended full profile diagnostic pipeline, add it to command-plan as an explicit authorized command and ensure expected exit codes are validated.
2. If `gate-profile` is purely a safe, non-mutating status/diagnostic command, add it to a narrow execution-authority exemption with tests proving it cannot mask mutating commands.
3. If `gate-profile` should not be run directly, keep it unauthorized and update execution guidance/reporting so future runs do not execute it and `tests_ran` accurately reports all actual non-exempt commands.

Requirements:

- Preserve command-plan execution authority.
- Preserve the closeout/report-summary fix from the prior round.
- Do not remove or bypass `command_plan_execution_authority`.
- Do not hide actual command execution by editing summaries without policy support.
- Ensure `tests_ran` and `pytest_result.txt` command blocks are consistent under the chosen policy.
- Add focused regression tests for the selected `gate-profile` policy.
- Final output must not use unsupported status values in `codex_report_summary.status`.

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

If preflight passes, run command-plan and follow only command-plan-authorized commands:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

Targeted development tests:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Final validation commands, only when authorized by command-plan or explicitly exempt by the implemented policy:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this new round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_gate_profile_authority_cleanup_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation;
2. fixing this requires broad redesign of command-plan, final-check, report-summary, or closeout;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. the fix requires running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, runtime probes, or full `solve_reports/` scans;
5. `command_plan_execution_authority` still reports WARN/FAIL for `gate-profile` without an explicit, tested policy;
6. `codex_report_summary.tests_ran` still omits non-exempt commands that appear in `pytest_result.txt`;
7. final-check has blocking failures;
8. report status or acceptance recommendation uses unsupported values or contradicts final gate status;
9. tests fail or any required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
