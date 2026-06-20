```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_closeout_authorization_report_summary_rework_v1",
  "round_id": "round_20260621_closeout_authorization_report_summary_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "rework_target_decision_id": "decision_20260621_command_plan_execution_authority_v1",
  "rework_target_round_id": "round_20260621_command_plan_execution_authority_v1",
  "primary_failed_checks": [
    "report_summary_fields_match_synthesis"
  ],
  "command_plan_authority_required": true,
  "closeout_policy": "only_if_command_plan_authorizes_or_report_summary_no_longer_requires_archive",
  "accepted_requires_final_check_passed": true,
  "forbid_unplanned_commands_on_success": true,
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
    "project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/*"
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

Repair the closeout authorization and report-summary/archive drift left by `decision_20260621_command_plan_execution_authority_v1` without redoing the completed execution-authority implementation.

The previous round successfully implemented and tested `command_plan_execution_authority`, but final-check still failed because `report_summary_fields_match_synthesis` expected round archive files while the command-plan did not list an executable closeout command. This round must make the closeout/report-summary contract internally consistent.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is only background. It is still a stale/sample-derived `samplereverse` suggestion and must not control this round.

Current live decision before this packet was `decision_20260621_command_plan_execution_authority_v1`. That round implemented `command_plan_execution_authority` and added 8 tests. `pytest_result.txt` records both targeted and combined test runs passing: `tests/test_project_gate.py -q` and `tests/test_project_gate.py tests/test_project_state.py -q`.

The remaining blocker is not the execution-authority feature itself. `project_state/gates/final_gate_result.json` has `gate_status=FAILED` because `report_summary_fields_match_synthesis` failed. The synthesized report summary expects round archive files under `project_state/rounds/round_20260621_command_plan_execution_authority_v1/`, while the live `codex_report_summary` did not list those archive files.

`project_state/gates/command_plan.json` for the previous round had profile `full`, `closeout_allowed=true`, and `required_command_kinds` containing `close-round`, but `commands` did not include `run-closeout` or `close-round`; it only provided `recommended_next_action` for `run-closeout`. This creates a contract mismatch: report-summary/final-check expects archive files, but command-plan did not authorize the archive-producing command as an executable command.

Relevant existing capabilities to reuse:

- `reverse_agent.project_gate.command_plan`
- `reverse_agent.project_gate.gate_profile`
- `reverse_agent.project_gate.report_summary`
- `reverse_agent.project_gate.final_check`
- `reverse_agent.project_gate.run_closeout`
- command-plan metadata: `commands`, `omitted_commands`, `profile_meta`, `closeout_allowed`, `recommended_next_action`
- report-summary synthesis and final gate checks
- tests in `tests/test_project_gate.py`

Do not read full `solve_reports/` or `PROJECT_PROGRESS_LOG.txt`. No reverse-solving, no sample execution, no runtime probe, no debugger/emulator, no IDA/Ghidra/OllyDbg/x64dbg work.

## 3. Do Not Do

Do not redo or weaken the already-passing `command_plan_execution_authority` check.

Do not mark the prior round accepted while final-check is failed.

Do not manually run `run-closeout` unless the current command-plan explicitly authorizes it, or unless this round's implementation first changes command-plan/final-check semantics so that closeout is authorized by command-plan.

Do not bypass `report_summary_fields_match_synthesis` by deleting expected archive paths from summaries without fixing the underlying policy.

Do not mutate `project_state/current_state.json`, `task_packet.json`, `artifact_index.json`, `negative_results.json`, or `.codex-skills/registry.json`.

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

Then inspect only the files needed for this engineering rework:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/gate_profile_plan.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/round_delta_summary.json`
8. `project_state/gates/run_closeout_result.json` if present
9. `project_state/rounds/round_20260621_command_plan_execution_authority_v1/round_manifest.json` if present

Historical files may be read only by exact path when needed to understand this failure. Do not scan entire `project_state/rounds/` or `solve_reports/`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Why did `report_summary_fields_match_synthesis` fail in the previous round? Cite the expected archive files and the actual missing summary fields.
2. Why did command-plan say `full` and `closeout_allowed=true` while not listing `run-closeout` or `close-round` in `commands`?
3. Should archive-producing closeout be represented as a command-plan command, a recommended fallback action, or a post-final-check manual action? Define the policy.
4. Which component must change: `command_plan`, `report_summary`, `final_check`, `run_closeout`, or report generation? Explain why.
5. How does the fix preserve command-plan execution authority and avoid authorizing omitted/unplanned commands?
6. How does the fix avoid breaking fast profile rounds where closeout is intentionally forbidden?
7. How does the fix avoid breaking full profile rounds where closeout is required or allowed?
8. What tests prove that report-summary and final-check no longer disagree about round archive files?

## 6. Implementation Scope

Implement one bounded fix: make closeout authorization and report-summary archive expectations consistent.

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
- `project_state/rounds/round_20260621_closeout_authorization_report_summary_rework_v1/*`

Acceptable implementation approaches, choose the smallest correct one:

1. If full-profile closeout should be executable, make command-plan include an explicit authorized closeout command when `closeout_allowed=true` and closeout/archive files are required.
2. If closeout is only a recommended manual fallback before archive creation, make report-summary/final-check treat missing archive files as pre-closeout pending, not as a required summary mismatch.
3. If the intended model is two-phase finalization, make the phases explicit so pre-closeout final-check and post-closeout final-check have different archive expectations.

Requirements:

- Do not weaken final-check generally.
- Do not remove `report_summary_fields_match_synthesis`; fix the policy mismatch that caused it.
- Preserve the already-passing `command_plan_execution_authority` behavior.
- Preserve current fast/standard/full naming and behavior except for the narrow closeout/report-summary contract fix.
- Add focused regression tests covering both pre-closeout and closeout-allowed behavior.
- Ensure a SUCCESS report cannot omit required archive files if archive creation was actually performed or required by policy.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then run preflight before implementation:

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

Final validation commands, only when authorized by command-plan:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Run closeout only if command-plan explicitly includes or authorizes the closeout command after this fix:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_closeout_authorization_report_summary_rework_v1
```

If closeout runs, rerun report-summary and final-check afterward:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` if:

1. preflight fails before implementation;
2. fixing this requires broad redesign of command-plan, closeout, report-summary, or final-check;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. the fix requires running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, or runtime probes;
5. command-plan still omits closeout while report-summary/final-check still require archive files for success;
6. final-check still fails `report_summary_fields_match_synthesis` after the intended closeout/report-summary policy is applied;
7. `command_plan_execution_authority` regresses from PASS to FAIL/WARN without an explicit expected test case;
8. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
9. tests fail or required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
