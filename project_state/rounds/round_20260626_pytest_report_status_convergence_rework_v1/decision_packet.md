```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260626_pytest_report_status_convergence_rework_v1",
  "round_id": "round_20260626_pytest_report_status_convergence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260625_command_plan_artifact_drift_rework_v1",
  "previous_round_id": "round_20260625_command_plan_artifact_drift_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair pytest/report/gate/closeout status convergence so pytest_result, reports, final-check, execution-log, and run-closeout cannot disagree in accepted state.",
  "command_plan_authority_required": true,
  "accepted_requires_pytest_result_status_passed": true,
  "accepted_requires_report_status_matches_pytest_result": true,
  "accepted_requires_no_failed_command_blocks_in_accepted_pytest_result": true,
  "accepted_requires_execution_log_records_required_commands": true,
  "accepted_requires_live_archive_pytest_parity": true,
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

Implement Pytest / Report Status Convergence Rework v1.

The previous round cannot be accepted because `codex_execution_report.md` claimed `SUCCESS / ACCEPTED` while `project_state/pytest_result.txt` recorded `pytest_result_summary.status: FAILED` and contained failed command blocks for execution-log, final-check, and run-closeout.

Final accepted state must satisfy:

1. `project_state/pytest_result.txt` top-level `pytest_result_summary.status` is `PASSED`.
2. `codex_execution_report.md` and `execution_report.md` must not claim `SUCCESS / ACCEPTED` unless `pytest_result_summary.status` is `PASSED`.
3. `final_gate_result.json.gate_status: PASSED` must not coexist with failed command blocks in `pytest_result.txt`.
4. `run_closeout_result.json.closeout_status: PASSED` must not coexist with a failed run-closeout block in `pytest_result.txt`.
5. Archived `pytest_result.txt` and live `project_state/pytest_result.txt` must match.
6. `execution_log.json` must record every command-plan required command.
7. final-check must catch pytest/report/gate/closeout status divergence before any accepted report is emitted.
8. No Phase 2, Web, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan work is allowed.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains non-authoritative background state. This round is controlled only by `project_state/decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260625_command_plan_artifact_drift_rework_v1`.

Blocking evidence from that audit:

- `codex_execution_report.md` claimed `SUCCESS / ACCEPTED`.
- `project_state/pytest_result.txt` top-level `pytest_result_summary.status` was `FAILED`.
- `pytest_result.txt` recorded `execution-log: FAILED` because four required command-plan commands were not recorded in execution_log.
- `pytest_result.txt` recorded `final-check: FAILED`, including failures for `pytest_result_match`, archived pytest mismatch, command exit mismatch, status policy, required command recording, and nested closeout failures.
- `pytest_result.txt` recorded `run-closeout: FAILED`, with `close-round` failed and `report_status: FAILED`.
- Later live artifacts showed `final_gate_result.json.gate_status: PASSED` and `run_closeout_result.json.closeout_status: PASSED`, so final live state did not converge with the failed pytest transcript.

Accepted facts to preserve:

- command-plan remains the command execution authority;
- Tests remain subordinate to command-plan;
- legacy `codex_execution_report.md` remains supported;
- neutral `execution_report.md` alias remains supported;
- valid profiles remain `fast`, `standard`, and `full`;
- the command-plan artifact drift repair from the previous round should be preserved: accepted-state `run-closeout` must use final-success semantics, not failed-final-check diagnostic semantics.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not accept a report if `pytest_result_summary.status` is not `PASSED`.

Do not allow report `SUCCESS / ACCEPTED` to coexist with failed command blocks in `pytest_result.txt`.

Do not allow live `final_gate_result.json.gate_status: PASSED` to mask failed final-check blocks in `pytest_result.txt`.

Do not allow live `run_closeout_result.json.closeout_status: PASSED` to mask failed run-closeout blocks in `pytest_result.txt`.

Do not delete failed command blocks to manufacture a passing transcript. Re-run the authorized final sequence and regenerate a consistent final transcript.

Do not widen the task into Phase 2, Web UI, CI, AgentRunner, database, queue, scheduler, or multi-executor work.

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
13. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Why did `pytest_result_summary.status` remain `FAILED` while the report claimed `SUCCESS / ACCEPTED`?
2. How does report-summary or final-check now prevent report `SUCCESS / ACCEPTED` when `pytest_result_summary.status` is `FAILED`?
3. How does final-check now detect failed command blocks inside `pytest_result.txt`, not only the latest live gate artifacts?
4. How does run-closeout now avoid leaving a live `PASSED` closeout artifact when the pytest transcript contains a failed run-closeout block?
5. How is archived `pytest_result.txt` kept identical to live `project_state/pytest_result.txt`?
6. How does execution-log guarantee all command-plan required commands are recorded before acceptance?
7. Which regression tests prove pytest/report/gate/closeout status convergence failures cannot recur?
8. How does this rework preserve no forbidden path mutation, no legacy artifact deletion, no Phase 2/Web/CI/AgentRunner/database/queue/scheduler work, no reverse-solving, and no heavy artifact scans?

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
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/run_closeout_execution_log.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_close_snapshot.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260626_pytest_report_status_convergence_rework_v1/*`

Required behavior:

1. final-check must fail when `pytest_result_summary.status != PASSED` for a report that claims `SUCCESS / ACCEPTED`.
2. final-check must detect failed command blocks in `pytest_result.txt` and prevent accepted-state `PASSED` artifacts from masking them.
3. report-summary must not synthesize `SUCCESS / ACCEPTED` from a failed pytest transcript.
4. run-closeout must not produce accepted `PASSED` closeout state when the current pytest transcript contains unresolved failed command blocks.
5. execution-log validation must require all command-plan required commands before acceptance.
6. archived `pytest_result.txt` must match live `pytest_result.txt` after closeout.
7. Add focused regression tests for pytest/report/gate/closeout status divergence.
8. Regenerate current-round artifacts according to command-plan authority.

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

After implementation, run only command-plan-authorized commands. If authorized, expected validation includes:

```powershell
python -m pytest tests/test_project_gate.py -q
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260626_pytest_report_status_convergence_rework_v1
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

- `pytest_result_summary.status` is not `PASSED`;
- `codex_execution_report.md` claims `SUCCESS` while pytest_result is failed;
- failed command blocks remain in `pytest_result.txt`;
- final-check fails;
- run-closeout fails;
- execution-log required commands are incomplete;
- archived pytest_result differs from live pytest_result;
- live gate `PASSED` and pytest_result `FAILED` coexist;
- report-summary claims `ACCEPTED` while pytest/report/gate/closeout evidence contains unresolved contradictions;
- tests fail;
- policy-lint or policy-impact fails.
