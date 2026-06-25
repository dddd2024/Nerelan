```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260625_gate_closeout_audit_truth_rework_v1",
  "round_id": "round_20260625_gate_closeout_audit_truth_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260625_executor_neutral_gate_status_scope_rework_v1",
  "previous_round_id": "round_20260625_executor_neutral_gate_status_scope_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_1_5_pre_phase_2",
  "primary_goal": "Repair gate, closeout, execution-log, and Required Audit truthfulness so accepted state cannot mask internal contradictions.",
  "command_plan_authority_required": true,
  "accepted_requires_required_audit_semantic_alignment": true,
  "accepted_requires_no_nested_closeout_failures": true,
  "accepted_requires_execution_log_pytest_exit_code_consistency": true,
  "accepted_requires_final_check_no_false_pass": true,
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

Implement Gate Closeout Audit Truth Rework v1.

The previous round cannot be accepted because its live artifacts still permit top-level success to mask internal contradictions. This round must repair those truthfulness failures without expanding scope.

Final accepted state must satisfy:

1. `codex_execution_report.md` Required Audit answers answer the exact eight questions, not merely contain eight headings.
2. `final_gate_result.json.gate_status` is not `PASSED` if any required nested artifact contains active `FAIL`, `FAILED`, mismatched exit code, or contradictory report status.
3. `run_closeout_result.json.closeout_status` is not `PASSED` if `close_round_result.report_status` is `FAILED`, any internal check is `FAIL`, any required step failed, or any active warning/blocking reason remains.
4. `execution_log.json` and `pytest_result.txt` agree on every top-level command exit code, especially `run-closeout`.
5. `command-plan` distinguishes diagnostic expected-exit `[0, 1]` from final accepted success requirements.
6. The final report does not claim `SUCCESS / ACCEPTED` until all of the above are true.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` remains non-authoritative background state. This round is controlled only by `project_state/decision_packet.md`.

Previous audit outcome: `REWORK_REQUIRED` for `decision_20260625_executor_neutral_gate_status_scope_rework_v1`.

Blocking evidence from that round:

- `codex_execution_report.md` claimed `SUCCESS / ACCEPTED`, but Required Audit answers were semantically misaligned with their questions.
- `run_closeout_result.json` had top-level `closeout_status: PASSED` while nested `close_round_result.report_status` remained `FAILED`.
- `run_closeout_result.json` still contained an internal `FAIL` for `pytest_result_exit_codes_match_command_plan`.
- `execution_log.json` recorded top-level `run-closeout` with `exit_code: 1`, while `pytest_result.txt` recorded the same top-level command as `EXIT: 0`.
- `final_gate_result.json` reported top-level `PASSED`, so final-check did not catch all internal contradictions.

Accepted facts to preserve:

- legacy `codex_execution_report.md` remains supported;
- neutral `execution_report.md` alias remains supported;
- legacy and neutral report auto-summary aliases remain supported;
- command-plan authority remains mandatory;
- valid profiles are only `fast`, `standard`, and `full`;
- Tests are subordinate to command-plan.

Tool policy:

- This is not a reverse-solving round.
- Do not inspect, execute, debug, emulate, or solve sample binaries.
- Do not use IDA, Ghidra, OllyDbg, x64dbg, radare2, runtime probes, solver expansion, harness sample execution, or full `solve_reports/` scans.

## 3. Do Not Do

Do not accept top-level `PASSED` if nested required checks contain active `FAIL` or `FAILED`.

Do not allow `run_closeout_result.json.closeout_status: PASSED` when `close_round_result.report_status` is `FAILED`.

Do not allow `execution_log.json` and `pytest_result.txt` to disagree on top-level command exit codes.

Do not treat Required Audit as complete only because eight headings exist.

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
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/run_closeout_execution_log.json`
9. `project_state/gates/round_delta_summary.json`
10. `project_state/gates/round_close_snapshot.json`
11. `project_state/gates/state_hygiene_inventory.json`
12. `project_state/gates/policy_impact_audit.json`
13. `project_state/gates/policy_lint_result.json`
14. current/previous round manifest only if needed as bounded diagnostic evidence

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Before claiming success, `project_state/codex_execution_report.md` must answer all eight items below. Each answer must include concrete evidence and one status value: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Which exact previous contradictions caused this rework, and which artifacts proved each contradiction?
2. How does Required Audit validation now detect answer/question semantic mismatch rather than only counting headings?
3. How does final-check now fail when `run_closeout_result.json` contains any active nested `FAIL` or `FAILED` state?
4. How does run-closeout now prevent `closeout_status: PASSED` when `close_round_result.report_status` is `FAILED`?
5. How do `execution_log.json` and `pytest_result.txt` now prove identical top-level command exit codes?
6. How does command-plan distinguish diagnostic expected-exit `[0, 1]` from final accepted success requirements?
7. Which regression tests prove these failures cannot recur?
8. How does this rework preserve no sample-solving, no prompt/skill mutation, no forbidden state-file mutation, no legacy artifact deletion, and no Phase 2 expansion?

Do not write TODO, TBD, PENDING, “should pass”, “expected to pass”, `(to be filled)`, or speculative answers.

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
- `project_state/gates/state_hygiene_inventory.json`
- `project_state/gates/policy_impact_audit.json`
- `project_state/gates/policy_lint_result.json`
- `project_state/rounds/round_20260625_gate_closeout_audit_truth_rework_v1/*`

Required behavior:

1. Add final-check validation that recursively inspects required closeout artifacts for active `FAIL` / `FAILED` states.
2. Add run-closeout aggregation logic that fails top-level closeout if nested close-round report status is failed.
3. Add execution-log validation that compares actual command exit codes against `pytest_result.txt` command blocks.
4. Add Required Audit alignment hardening. At minimum, reject obviously misaligned answers that do not mention the core entities in the corresponding question.
5. Add focused regression tests for all four failures above.
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260625_gate_closeout_audit_truth_rework_v1
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

- Required Audit remains semantically misaligned;
- `run_closeout_result.json` has top-level `PASSED` with nested `FAIL` / `FAILED`;
- `close_round_result.report_status` remains `FAILED` in accepted closeout;
- `execution_log.json` and `pytest_result.txt` disagree on top-level command exit codes;
- final-check top-level `PASSED` masks nested contradictions;
- report-summary claims `ACCEPTED` while hard evidence contains unresolved internal failures;
- tests fail;
- policy-lint or policy-impact fails.
