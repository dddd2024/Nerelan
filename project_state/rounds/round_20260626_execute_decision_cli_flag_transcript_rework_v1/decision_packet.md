```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_execute_decision_cli_flag_transcript_rework_v1",
  "round_id": "round_20260626_execute_decision_cli_flag_transcript_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_execute_decision_managed_execute_mode_v1",
  "previous_round_id": "round_20260626_execute_decision_managed_execute_mode_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair execute-decision managed execute mode by unifying CLI flag semantics, command-plan generation, pytest transcript blocks, execution-log coverage, final-check, and run-closeout convergence.",
  "command_plan_authority_required": true,
  "accepted_requires_execute_mode_cli_consistency": true,
  "accepted_requires_execute_decision_not_plan_validation_only": true,
  "accepted_requires_required_commands_recorded": true,
  "accepted_requires_command_plan_stdout_artifact_parity": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_no_phase2_scope": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
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

Repair Execute Decision CLI Flag and Transcript Rework v1.

The previous round `decision_20260626_execute_decision_managed_execute_mode_v1` failed. It attempted to move `execute-decision` from plan-validation into managed execute mode, but command-plan generated `execute-decision --mode execute` while the implementation/report indicated the actual CLI supports `--execute`. The recorded evidence remained plan-validation only, required command blocks were missing, final-check failed, and run-closeout failed.

Final accepted state must satisfy:

1. `execute-decision` CLI, decision text, command-plan, pytest_result, and Required Audit use one execute-mode convention consistently.
2. The preferred convention for this rework is `--mode execute`. If implementation chooses `--execute` instead, all generated command-plan commands, docs, pytest_result command blocks, tests, and audit answers must consistently use `--execute` with no mixed form.
3. `pytest_result.txt` must record the actual execute-mode command from the current round, not a stale plan-validation command and not a previous-round command.
4. `project_state/gates/execute_decision_result.json` must carry current decision_id and round_id and must not claim only `plan_validation_only` when this round claims execute-mode success.
5. execution-log must record all command-plan required commands, including the current execute-mode command and current run-closeout command.
6. command-plan `--json` stdout recorded in pytest_result must match live `project_state/gates/command_plan.json` command list, expected exits, and notes.
7. final-check must pass.
8. run-closeout must pass.
9. report status must remain `FAILED / REWORK_REQUIRED` unless all above evidence is current and consistent.
10. No Phase 2, Web, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous round failed and self-reported `status: FAILED` and `acceptance_recommendation: REWORK_REQUIRED`.

Blocking evidence from the failed round:

- `project_state/codex_execution_report.md` reported `FAILED / REWORK_REQUIRED` for `decision_20260626_execute_decision_managed_execute_mode_v1`.
- Required Audit item 1 stated that `decision_packet.md` expected `--mode execute`, while the implementation supported `--dry-run` default and `--execute`; command-plan generated `--mode execute`, creating a CLI incompatibility.
- `project_state/pytest_result.txt` had top-level `pytest_result_summary.status: FAILED`.
- `pytest_result.txt` recorded `execute-decision` without execute mode and its output was `mode: plan-validation` with `executed_count: 0`.
- `project_state/gates/execute_decision_result.json` still showed `mode: plan-validation`, `contract_mode: plan_validation_only`, and `executed_commands: []`.
- execution-log failed because command-plan required commands were missing from the transcript, including the current `execute-decision ... --mode execute` command and current `run-closeout` command.
- final-check failed with command-plan stdout/artifact drift, pytest_result exit-code mismatch against command-plan, command-plan execution authority failures, stale or mismatched prior-round commands, and startup baseline consistency failure.
- run-closeout failed because close-round failed and report_status was `FAILED`.

`task_packet.json` remains non-authoritative background state. It describes a stale `samplereverse` evidence collection suggestion but explicitly says `decision_packet_controls_current_round`.

`current_state.json` still reflects old sample state and is only the digest baseline for this engineering round.

`negative_results.json` contains reverse-solving prohibitions such as old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false frontiers, and committing full solve_reports. This round does not enter reverse-solving and must not repeat those directions.

Existing implementation evidence to preserve:

- `reverse_agent/project_gate.py` already defines execute-decision artifact names and integrates `execute_decision_result.json` into gate/report artifacts.
- plan-validation mode was previously accepted as a bounded contract; it must not be broken, but it must not be mislabeled as execute-mode success.
- prior pytest/report/gate/closeout convergence checks were accepted and must not regress.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not repeat a plan-validation-only execution and claim execute mode is complete.

Do not let command-plan generate a CLI command that `argparse` does not support.

Do not mix `--mode execute` and `--execute` in accepted evidence.

Do not leave previous-round command blocks in pytest_result as current-round evidence.

Do not omit required command-plan commands from pytest_result, execution-log, or report tests_ran.

Do not let live command_plan.json drift from the command-plan `--json` stdout recorded in pytest_result.

Do not let final-check or run-closeout fail in an accepted report.

Do not use `SUCCESS / ACCEPTED` if `pytest_result_summary.status` is not `PASSED`, if final-check fails, if run-closeout fails, or if execute_decision_result remains plan-validation only.

Do not delete failed transcript blocks to manufacture success. Regenerate transcript evidence through the authorized workflow.

Do not implement Web UI, CI integration, AgentRunner adapters, database, queue, scheduler, background daemon, or multi-agent orchestration in this round.

Do not rename Codex-specific files, `.codex-skills`, historical round archives, or report block names in this round. Naming neutralization remains a separate future round.

Do not inspect, run, solve, debug, or emulate sample binaries.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify forbidden paths:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/project_workspace_prompt.md`
- `docs/prompts/codex_execution_prompt.md`
- `docs/prompts/README.md`

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

Do not commit, push, create PRs, switch branches, rebase, merge, or modify remote state unless the user explicitly requests it in the current message given to the executor.

## 4. Files To Inspect

Read default state files first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/execution_report.md` if present
7. `project_state/decision_packet.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Then inspect only bounded implementation and gate evidence:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/execute_decision_result.json`
5. `project_state/gates/run_round_result.json` if present
6. `project_state/gates/execution_log.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/run_closeout_execution_log.json`
10. `project_state/gates/report_summary_synthesis.json`
11. `project_state/gates/round_baseline.json`
12. `project_state/gates/round_delta_summary.json`
13. `project_state/gates/round_close_snapshot.json` if present
14. `project_state/gates/policy_impact_audit.json` if present
15. `project_state/gates/policy_lint_result.json` if present
16. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which execute-mode CLI convention is now canonical: `--mode execute` or `--execute`?
2. How do argparse, command-plan generation, decision text, pytest_result command blocks, and Required Audit prove the same convention is used everywhere?
3. Does `pytest_result.txt` record the current round's execute-mode command, and does it avoid stale previous-round command blocks as current evidence?
4. Does `execute_decision_result.json` prove execute mode was invoked, or if execute mode cannot complete, does it correctly block success instead of falling back to plan-validation success?
5. How are recursive execute-decision invocations prevented or recorded without bypassing command-plan authority?
6. Does execution-log record every required command-plan command, including execute-decision and run-closeout for the current round?
7. Do command-plan stdout/artifact parity, final-check, and run-closeout all pass after the fix?
8. How does this rework preserve no forbidden path mutation, no naming migration, no Web/CI/AgentRunner/database/queue/scheduler work, no reverse-solving, and no heavy artifact scans?

Do not write TODO, TBD, PENDING, `should pass`, `expected to pass`, `(to be filled)`, or speculative answers.

## 6. Implementation Scope

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated or updated state artifacts:

- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/run_round_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_execute_decision_cli_flag_transcript_rework_v1/*`

Required behavior:

1. Choose one execute-mode CLI convention and apply it consistently. Prefer `--mode execute` because it is already specified by the failed decision and command-plan evidence.
2. If choosing `--mode execute`, add argparse support and tests for `--mode plan-validation` / default and `--mode execute` as appropriate.
3. If choosing `--execute`, update command-plan generation and all generated evidence to use `--execute`, with no remaining `--mode execute` in accepted current-round commands.
4. Regenerate command-plan after the fix so `project_state/gates/command_plan.json` and pytest_result command-plan stdout match.
5. Ensure pytest_result records the current round execute-mode command exactly as command-plan generated it.
6. Ensure execute_decision_result for accepted state is not merely `plan_validation_only` when decision_contract requires execute mode.
7. Ensure execution-log derives all current required commands from pytest_result and command-plan with no missing required command failures.
8. Ensure report-summary, final-check, and run-closeout pass after transcript and artifacts are current.
9. Add regression tests for CLI flag consistency, command-plan/CLI parity, execute-mode artifact status, missing required command blocking, stale previous-round command blocking, and final-check/run-closeout convergence.
10. Preserve prior accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact drift, run-closeout final-success semantics, and nested closeout failure absence.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Run preflight and command-plan:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
```

After implementation, regenerate command-plan and run only command-plan-authorized commands. If command-plan uses the preferred convention, it must include:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_execute_decision_cli_flag_transcript_rework_v1 --mode execute
```

If and only if the implementation deliberately chooses `--execute`, command-plan and all evidence must consistently use:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_execute_decision_cli_flag_transcript_rework_v1 --execute
```

At minimum, validation should include command-plan-authorized equivalents of:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_execute_decision_cli_flag_transcript_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands and exit codes in `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- startup checks do not confirm `F:\reverse-agent` and repository root;
- `decision_meta` is missing or invalid;
- `status` is not `APPROVED`;
- `mainline` is invalid;
- skill profiles do not match active registry entries;
- command-plan is missing, failed, or conflicts with safe execution;
- a needed command is not authorized by command-plan;
- implementation requires forbidden path mutation;
- implementation requires Phase 2 / Web / CI / AgentRunner scope;
- implementation requires sample-solving or heavy artifact scan.

Stop with `REWORK_REQUIRED` if:

- execute mode CLI and command-plan convention disagree;
- both `--mode execute` and `--execute` appear as current accepted evidence without an explicit compatibility reason;
- pytest_result does not record the current round execute-mode command;
- pytest_result retains stale previous-round execute-decision or run-closeout commands as current evidence;
- execute_decision_result remains `plan_validation_only` while claiming execute-mode success;
- execute_decision_result is missing, stale, or lacks current decision_id/round_id;
- execution-log has missing required command-plan commands;
- command-plan stdout differs from live command_plan.json;
- final-check fails;
- run-closeout fails;
- pytest_result_summary.status is not `PASSED` in accepted state;
- report status disagrees with pytest_result, execution-log, final-check, or run-closeout;
- command failures do not propagate to non-success status;
- forbidden paths are modified;
- work enters Web/CI/AgentRunner/database/queue/scheduler/reverse-solving/heavy scan;
- tests fail;
- policy-lint or policy-impact fails.
