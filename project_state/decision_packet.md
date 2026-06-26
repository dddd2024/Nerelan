```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_execute_decision_single_entrypoint_contract_v1",
  "round_id": "round_20260626_execute_decision_single_entrypoint_contract_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260626_pytest_report_status_convergence_rework_v1",
  "previous_round_id": "round_20260626_pytest_report_status_convergence_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Create a trustworthy local execute-decision single-entrypoint contract so future executor prompts can be shortened without weakening command-plan, pytest, report, final-check, and closeout evidence.",
  "command_plan_authority_required": true,
  "accepted_requires_execute_decision_artifact": true,
  "accepted_requires_execute_decision_no_unplanned_commands": true,
  "accepted_requires_execute_decision_transcript_parity": true,
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

Implement Execute Decision Single Entrypoint Contract v1.

The previous accepted round repaired pytest/report/gate/closeout status convergence. The next engineering step is to reduce executor prompt burden by moving more execution sequencing into a local, auditable `execute-decision` entrypoint while preserving command-plan as the execution authority.

The target is not a Web UI, CI runner, database-backed scheduler, or multi-agent system. This round should only create a bounded local contract for a future short executor prompt such as "run the approved decision workflow".

Final accepted state must satisfy:

1. `python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id <round_id>` exists as a local CLI entrypoint or an equivalent already-existing entrypoint is hardened and documented in artifacts.
2. The entrypoint must derive its command set from `project_state/gates/command_plan.json` and must not run commands outside command-plan authority.
3. The entrypoint must produce `project_state/gates/execute_decision_result.json` with decision_id, round_id, command_plan reference, command list, exit codes, status, blocking reasons, and generated artifacts.
4. The entrypoint must either run a safe bounded workflow itself or provide a strict plan-only mode plus validation that proves no unplanned command would be run. If full execution is implemented, it must write transcript-compatible evidence into `project_state/pytest_result.txt`.
5. Any accepted report must still require `pytest_result_summary.status: PASSED`, final-check PASSED, run-closeout PASSED when closeout is allowed, and no failed command blocks.
6. No previous accepted status-convergence checks may be weakened.
7. No Phase 2, Web, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

The current accepted report is `codex_report_20260626_pytest_report_status_convergence_rework_v1`, based on `decision_20260626_pytest_report_status_convergence_rework_v1`, with `status: SUCCESS` and `acceptance_recommendation: ACCEPTED`.

`project_state/pytest_result.txt` currently has `pytest_result_summary.status: PASSED` and records two passing pytest runs: `tests/test_project_gate.py` and `tests/test_project_gate.py tests/test_project_state.py`.

The current final-check and run-closeout artifacts report PASSED, and final-check verifies pytest/report status support, absence of failed command blocks, archive parity, execution-log required command coverage, command-plan artifact parity, final-success run-closeout semantics, and no active nested closeout failures.

`task_packet.json` remains non-authoritative background state. It still describes a stale `samplereverse` evidence collection suggestion, but it explicitly says `decision_packet_controls_current_round`.

`artifact_index.json` still lists many reverse-solving artifacts as `missing`; those are not current evidence and are irrelevant to this engineering round.

`negative_results.json` contains reverse-solving prohibitions such as old sample_solver blind search, beam/budget expansion, compare_semantics_agree=false frontiers, and committing full solve_reports. This round does not enter reverse-solving and must not repeat those directions.

Existing implementation evidence:

- `reverse_agent/project_gate.py` already defines `EXECUTE_DECISION_NAME = "execute-decision"`, `EXECUTE_DECISION_RESULT_NAME = "execute_decision_result.json"`, and `EXECUTE_DECISION_OUTPUT_PATH`.
- `execute_decision_result.json` is already listed among reportable gate artifacts.
- `command-plan`, `execution-log`, `report-summary`, `final-check`, and `run-closeout` already exist as current gate concepts and must remain authoritative.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not implement Web UI, CI integration, AgentRunner adapters, database, queue, scheduler, background daemon, or multi-agent orchestration in this round.

Do not rename Codex-specific files, `.codex-skills`, historical round archives, or report block names in this round. Naming neutralization is a separate future round.

Do not allow `execute-decision` to bypass command-plan authority.

Do not allow `execute-decision` to run commands that are absent from `command_plan.commands`.

Do not allow `execute-decision` to treat diagnostic expected-exit `[0, 1]` as accepted final success for report, final-check, or closeout status.

Do not weaken the accepted pytest/report/gate/closeout convergence checks from the previous round.

Do not delete failed transcript blocks to manufacture success. If transcript evidence is generated, it must be regenerated through the authorized workflow.

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
4. `project_state/gates/execution_log.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/run_closeout_execution_log.json`
8. `project_state/gates/report_summary_synthesis.json`
9. `project_state/gates/round_delta_summary.json`
10. `project_state/gates/round_close_snapshot.json`
11. `project_state/gates/policy_impact_audit.json`
12. `project_state/gates/policy_lint_result.json`
13. `project_state/gates/execute_decision_result.json` if present
14. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. What exact `execute-decision` contract was implemented, and is it run-mode, plan-only mode, validation mode, or a bounded combination?
2. How does `execute-decision` derive its command list from `command_plan.json` instead of hardcoding or inventing commands?
3. How does `execute-decision` prove it did not run or authorize commands outside `command_plan.commands`?
4. What artifact does `execute-decision` write, and how are decision_id, round_id, command exits, status, blocking reasons, and generated artifacts represented?
5. How does the implementation preserve the accepted pytest/report/gate/closeout convergence checks from the previous round?
6. Which regression tests cover `execute-decision` command-plan authority, transcript/status parity, failure propagation, and generated artifact coverage?
7. How does the round keep command-plan as the execution authority while moving toward a shorter executor prompt?
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
- `project_state/gates/execution_log.json`
- `project_state/gates/execute_decision_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_execute_decision_single_entrypoint_contract_v1/*`

Required behavior:

1. Add or harden the `execute-decision` CLI under `python -m reverse_agent.project_gate execute-decision`.
2. Ensure `execute-decision` validates current `decision_meta`, preflight result, command-plan status, and command-plan coverage before any accepted status is possible.
3. Ensure `execute-decision` produces `project_state/gates/execute_decision_result.json` with explicit status and evidence.
4. Ensure `execute-decision` does not run or approve any command outside `command_plan.commands`.
5. If `execute-decision` runs commands, it must record transcript-compatible evidence and propagate failures into pytest_result, execution_log, report-summary, final-check, and run-closeout.
6. If `execute-decision` is plan-only or validation-only in this first version, it must make that limitation explicit in `execute_decision_result.json` and in Required Audit, without claiming full autonomous execution.
7. Keep previous accepted checks for pytest_result PASSED, failed command block absence, archive parity, execution-log required command coverage, command-plan artifact drift, run-closeout final-success semantics, and nested closeout failure absence.
8. Add focused regression tests for the new entrypoint contract.

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

After implementation, regenerate command-plan and run only command-plan-authorized commands. If authorized by the updated command-plan, include an `execute-decision` plan/validation invocation such as:

```powershell
python -m reverse_agent.project_gate execute-decision --state-dir project_state --round-id round_20260626_execute_decision_single_entrypoint_contract_v1
```

At minimum, validation should include:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_execute_decision_single_entrypoint_contract_v1
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

- `execute-decision` runs or approves any command not present in `command_plan.commands`;
- `execute_decision_result.json` is missing, stale, or lacks current decision_id/round_id;
- `execute_decision_result.json` claims success while pytest_result, execution_log, final-check, report-summary, or run-closeout contains unresolved failures;
- `pytest_result_summary.status` is not `PASSED`;
- failed command blocks remain in `pytest_result.txt`;
- final-check fails;
- run-closeout fails when closeout is allowed;
- execution-log required commands are incomplete;
- archived pytest_result differs from live pytest_result;
- command-plan artifact drift reappears;
- run-closeout accepted-state semantics regress to diagnostic `[0, 1]` final success;
- tests fail;
- policy-lint or policy-impact fails.
