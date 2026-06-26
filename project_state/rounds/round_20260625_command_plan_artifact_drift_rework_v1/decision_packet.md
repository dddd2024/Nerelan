```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260625_command_plan_artifact_drift_rework_v1",
  "round_id": "round_20260625_command_plan_artifact_drift_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260625_gate_closeout_audit_truth_rework_v1",
  "previous_round_id": "round_20260625_gate_closeout_audit_truth_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair command-plan artifact drift so live command_plan.json, pytest_result command-plan stdout, execution_log, final-check, and run-closeout all agree on accepted-state command semantics.",
  "command_plan_authority_required": true,
  "accepted_requires_live_command_plan_matches_pytest_stdout": true,
  "accepted_requires_no_accepted_diagnostic_run_closeout_note": true,
  "accepted_requires_final_check_detects_command_plan_artifact_drift": true,
  "accepted_requires_run_closeout_final_success_semantics": true,
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

Implement Command Plan Artifact Drift Rework v1.

The previous round improved Required Audit alignment, nested closeout failure detection, and execution-log consistency, but it cannot be accepted because the live `project_state/gates/command_plan.json` artifact drifted from the command-plan stdout recorded in `project_state/pytest_result.txt`.

Final accepted state must satisfy:

1. `project_state/gates/command_plan.json` and the command-plan stdout recorded in `project_state/pytest_result.txt` must describe the same command list, expected exit codes, and notes for accepted-state validation.
2. `final-check` must fail if live `command_plan.json` differs from the command-plan block recorded in `pytest_result.txt`.
3. Accepted-state `run-closeout` must not retain the diagnostic note `run-closeout diagnostic after final-check failed; exit 1 is expected`.
4. Accepted-state `run-closeout` must either have `expected_exit_codes: [0]`, or a clearly separated field must distinguish diagnostic allowance from final success requirements.
5. `execution_log.json` must remain consistent with both `pytest_result.txt` and live `command_plan.json`.
6. `codex_execution_report.md` must not claim `SUCCESS / ACCEPTED` unless these command-plan consistency checks pass.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains non-authoritative background state. This round is controlled only by `project_state/decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260625_gate_closeout_audit_truth_rework_v1`.

Blocking evidence from that audit:

- `pytest_result.txt` command-plan stdout showed `run-closeout` expected exit as `[0]` and described it as expected to exit 0 after final-check passed.
- Live `project_state/gates/command_plan.json` showed the same `run-closeout` command with expected exit `[0, 1]` and the note `run-closeout diagnostic after final-check failed; exit 1 is expected`.
- `final_gate_result.json` still reported top-level `PASSED`, so final-check did not detect the live command-plan artifact drift.
- The previous decision explicitly required command-plan to distinguish diagnostic expected-exit `[0, 1]` from final accepted success requirements.

Accepted facts to preserve:

- command-plan remains the command execution authority;
- Tests remain subordinate to command-plan;
- legacy `codex_execution_report.md` remains supported;
- neutral `execution_report.md` alias remains supported;
- valid profiles remain `fast`, `standard`, and `full`;
- no sample-solving or Phase 2 work is allowed in this round.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not accept a report if live `command_plan.json` differs from the command-plan block recorded in `pytest_result.txt`.

Do not keep an accepted-state `run-closeout` command with the note `run-closeout diagnostic after final-check failed; exit 1 is expected`.

Do not treat diagnostic expected-exit `[0, 1]` as final accepted success for `run-closeout`.

Do not allow `final-check` to pass if command-plan artifact drift exists.

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

1. Why did live `project_state/gates/command_plan.json` differ from the command-plan stdout recorded in `project_state/pytest_result.txt`?
2. How does final-check now compare live `command_plan.json` against the command-plan block recorded in `pytest_result.txt`?
3. What is the accepted-state expected exit behavior for `run-closeout`, and how is it represented?
4. How is the diagnostic note `run-closeout diagnostic after final-check failed; exit 1 is expected` prevented from appearing in accepted-state command-plan artifacts?
5. Which regression tests prove command-plan artifact drift is detected?
6. How does execution-log consistency with both `pytest_result.txt` and live `command_plan.json` remain enforced?
7. How does this rework preserve no forbidden path mutation and no legacy artifact deletion?
8. How does this rework preserve no Phase 2, Web, CI, AgentRunner, database, queue, scheduler, reverse-solving, or heavy artifact scan expansion?

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
- `project_state/rounds/round_20260625_command_plan_artifact_drift_rework_v1/*`

Required behavior:

1. Parse the command-plan JSON block recorded in `pytest_result.txt` and compare it with live `project_state/gates/command_plan.json`.
2. Make `final-check` fail when the recorded command-plan stdout and live command-plan artifact disagree on command list, expected exit codes, or notes.
3. Ensure accepted-state `run-closeout` command semantics are not represented as a failed-final-check diagnostic path.
4. Keep execution-log validation aligned with both `pytest_result.txt` command blocks and live command-plan artifact.
5. Add focused regression tests for command-plan artifact drift, especially `run-closeout` expected-exit and note drift.
6. Regenerate current-round artifacts according to command-plan authority.

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260625_command_plan_artifact_drift_rework_v1
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

- live `command_plan.json` differs from the command-plan stdout recorded in `pytest_result.txt`;
- accepted-state `run-closeout` still carries the diagnostic failed-final-check note;
- accepted-state `run-closeout` still treats exit 1 as final accepted success without a separate diagnostic/final-success distinction;
- final-check top-level `PASSED` masks command-plan artifact drift;
- execution_log, pytest_result, and live command_plan disagree on top-level command exit codes;
- report-summary claims `ACCEPTED` while command-plan/pytest_result evidence contains unresolved semantic contradictions;
- tests fail;
- policy-lint or policy-impact fails.
