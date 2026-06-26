```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_execute_decision_managed_execute_mode_v1",
  "round_id": "round_20260626_execute_decision_managed_execute_mode_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_execute_decision_single_entrypoint_contract_v1",
  "previous_round_id": "round_20260626_execute_decision_single_entrypoint_contract_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Extend execute-decision from plan-validation into a bounded managed execution mode while preserving command-plan authority, transcript fidelity, failure propagation, and final gate/closeout convergence.",
  "command_plan_authority_required": true,
  "accepted_requires_execute_mode": true,
  "accepted_requires_no_recursive_execute_decision": true,
  "accepted_requires_transcript_compatible_pytest_result": true,
  "accepted_requires_failure_propagation": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_final_check_passed": true,
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

Implement Execute Decision Managed Execute Mode v1.

The previous round created a trustworthy local `execute-decision` entrypoint, but it was accepted with a limitation: the entrypoint is currently `plan-validation` / `plan_validation_only`, records `executed_commands: []`, and does not itself execute command-plan commands.

This round should add a bounded managed execution mode so a future local executor can use a shorter prompt without weakening audit guarantees.

Final accepted state must satisfy:

1. `python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id <round_id> --mode execute` or an equivalent explicit execute-mode flag exists.
2. Execute mode derives its command list exclusively from `project_state/gates/command_plan.json`.
3. Execute mode must not recursively spawn itself when `execute-decision` appears in `command_plan.commands`; it must represent its own entrypoint command as the current in-process step or otherwise handle it with an explicit non-recursive rule.
4. Startup/status commands such as `Set-Location`, `Get-Location`, `Test-Path`, `git rev-parse`, and `git status --short` must be handled deterministically as verified preconditions or safe subprocess commands, with recorded evidence and exit semantics.
5. Execute mode must write transcript-compatible evidence into `project_state/pytest_result.txt`, including command text, stdout/stderr summary where available, and exit code blocks.
6. Execute mode must update `project_state/gates/execute_decision_result.json` with mode, command source, executed/skipped commands, expected/actual exits, blocking reasons, warnings, transcript parity, generated artifacts, and unplanned command detection.
7. Any failed required command must propagate to `execute_decision_result.json`, `pytest_result.txt`, `execution_log.json`, `report-summary`, `final-check`, and report status. It must not be masked by later successful commands.
8. Accepted state still requires `pytest_result_summary.status: PASSED`, no failed command blocks, command-plan artifact parity, execution-log required command coverage, final-check PASSED, run-closeout PASSED when closeout is allowed, and no active nested closeout failures.
9. No Phase 2, Web, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous accepted-with-limitations round was `decision_20260626_execute_decision_single_entrypoint_contract_v1` / `round_20260626_execute_decision_single_entrypoint_contract_v1`.

The previous report claimed `SUCCESS / ACCEPTED`, and `pytest_result.txt` recorded `pytest_result_summary.status: PASSED` for that round.

The previous `execute_decision_result.json` showed:

- `gate_status: PASSED`;
- `mode: plan-validation`;
- `contract_mode: plan_validation_only`;
- `entrypoint: execute-decision`;
- `delegates_to: run-round`;
- `command_source: project_state/gates/command_plan.json`;
- `no_unplanned_commands: true`;
- `transcript_parity_status: NOT_APPLICABLE_PLAN_ONLY`;
- `executed_commands: []`.

Therefore the next useful step is not another plan-validation artifact. The next step is a bounded execute mode that can run or explicitly record command-plan-authorized work without recursion, while preserving the status-convergence protections already accepted.

`task_packet.json` remains non-authoritative background state. It still describes a stale `samplereverse` evidence collection suggestion, but it explicitly says `decision_packet_controls_current_round`.

`artifact_index.json` still lists many reverse-solving artifacts as `missing`; those are not current evidence and are irrelevant to this engineering round.

`negative_results.json` contains reverse-solving prohibitions such as old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false frontiers, and committing full solve_reports. This round does not enter reverse-solving and must not repeat those directions.

Existing implementation evidence:

- `reverse_agent/project_gate.py` already defines `EXECUTE_DECISION_NAME`, `EXECUTE_DECISION_RESULT_NAME`, and `EXECUTE_DECISION_OUTPUT_PATH`.
- `execute_decision_result.json` is already a reportable gate artifact.
- `command-plan`, `execution-log`, `report-summary`, `final-check`, and `run-closeout` already exist and must remain authoritative.
- Prior status convergence checks for pytest/report/gate/closeout have been accepted and must not regress.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not implement Web UI, CI integration, AgentRunner adapters, database, queue, scheduler, background daemon, or multi-agent orchestration in this round.

Do not rename Codex-specific files, `.codex-skills`, historical round archives, or report block names in this round. Naming neutralization remains a separate future round.

Do not let execute mode bypass command-plan authority.

Do not run commands that are absent from `command_plan.commands`, except for explicitly documented in-process handling of the current `execute-decision` entrypoint and safe startup precondition checks already represented in command-plan.

Do not recursively spawn `execute-decision` from within execute mode.

Do not treat diagnostic expected-exit `[0, 1]` as accepted final success for report, final-check, or closeout status.

Do not allow later successful commands to mask an earlier failed required command.

Do not weaken accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact drift, run-closeout final-success semantics, and nested closeout failure absence.

Do not delete failed transcript blocks to manufacture success. Regenerate transcript evidence only through the authorized managed execution flow.

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
4. `project_state/gates/execute_decision_result.json` if present
5. `project_state/gates/run_round_result.json` if present
6. `project_state/gates/execution_log.json`
7. `project_state/gates/final_gate_result.json`
8. `project_state/gates/run_closeout_result.json`
9. `project_state/gates/run_closeout_execution_log.json`
10. `project_state/gates/report_summary_synthesis.json`
11. `project_state/gates/round_delta_summary.json`
12. `project_state/gates/round_close_snapshot.json`
13. `project_state/gates/policy_impact_audit.json`
14. `project_state/gates/policy_lint_result.json`
15. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact execute mode was implemented, and how is it invoked from the CLI?
2. How does execute mode derive commands exclusively from `command_plan.json`?
3. How does execute mode avoid recursive `execute-decision` execution while still recording the entrypoint command faithfully?
4. How are startup/status commands handled and recorded?
5. How does execute mode write transcript-compatible `pytest_result.txt` evidence with command blocks and exit codes?
6. How are command failures propagated into `execute_decision_result.json`, pytest_result summary, execution-log, report-summary, final-check, run-closeout, and report status?
7. Which regression tests cover execute-mode success, failure propagation, no-unplanned-command enforcement, recursion prevention, startup/status handling, and preservation of previous status-convergence gates?
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
- `project_state/rounds/round_20260626_execute_decision_managed_execute_mode_v1/*`

Required behavior:

1. Add or harden an explicit execute mode for `python -m reverse_agent.project_gate execute-decision`.
2. Preserve plan-validation mode as a safe default or safe option; do not break the accepted previous contract.
3. Ensure execute mode is opt-in and clearly identified in `execute_decision_result.json`.
4. Ensure execute mode validates current `decision_meta`, preflight result, command-plan status, and command-plan coverage before running or recording any accepted status.
5. Ensure execute mode uses only command-plan-authorized commands and records any command it skips, substitutes, or handles in-process.
6. Ensure execute mode has a non-recursive rule for the current `execute-decision` command when command-plan includes it.
7. Ensure execute mode writes a transcript-compatible `project_state/pytest_result.txt` or a strictly validated append/update path that final-check can verify.
8. Ensure any failure in a required command forces non-success status and prevents `SUCCESS / ACCEPTED` reporting.
9. Keep previous accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact drift, run-closeout final-success semantics, and nested closeout failure absence.
10. Add focused regression tests for execute mode and its failure cases.

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

After implementation, regenerate command-plan and run only command-plan-authorized commands. If authorized by the updated command-plan, include execute mode:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_execute_decision_managed_execute_mode_v1 --mode execute
```

At minimum, validation should include:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_execute_decision_managed_execute_mode_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

The exact command set is whatever current command-plan authorizes. Command-plan overrides this Tests section if there is any conflict.

Record all top-level commands in `project_state/pytest_result.txt`.

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

- execute mode is missing or cannot be invoked explicitly;
- execute mode runs or approves any unplanned command;
- execute mode recursively spawns `execute-decision`;
- execute mode omits required command-plan commands without explicit skipped/in-process evidence;
- `execute_decision_result.json` is missing, stale, or lacks current decision_id/round_id;
- `execute_decision_result.json` claims success while pytest_result, execution_log, final-check, report-summary, or run-closeout contains unresolved failures;
- command failures do not propagate to non-success status;
- `pytest_result_summary.status` is not `PASSED` in accepted state;
- failed command blocks remain in `pytest_result.txt` in accepted state;
- final-check fails;
- run-closeout fails when closeout is allowed;
- execution-log required commands are incomplete;
- archived pytest_result differs from live pytest_result;
- command-plan artifact drift reappears;
- run-closeout accepted-state semantics regress to diagnostic `[0, 1]` final success;
- tests fail;
- policy-lint or policy-impact fails.
