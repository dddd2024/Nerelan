```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_decision_command_plan_conflict_lint_v1",
  "round_id": "round_20260621_decision_command_plan_conflict_lint_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_decision_id": "decision_20260621_closeout_report_refresh_contract_rework_v1",
  "previous_round_id": "round_20260621_closeout_report_refresh_contract_rework_v1",
  "previous_acceptance": "ACCEPTED",
  "primary_goal": "Detect conflicts between decision Tests/closeout expectations and command-plan before implementation proceeds.",
  "command_plan_authority_required": true,
  "accepted_requires_preflight_conflict_detection_tests": true,
  "accepted_requires_final_check_passed": true,
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
    "project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/*"
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

Implement a bounded engineering check that detects conflicts between `decision_packet.md` Tests / closeout expectations and the current `command-plan` before Codex enters implementation or closeout.

The previous accepted round fixed closeout/report refresh contract behavior: `run-closeout` passed, `final-check` passed, command-plan authority passed, and report status became `SUCCESS/ACCEPTED`. The next gap is earlier conflict detection. If a future decision hard-codes commands that the current gate profile or command-plan omits, or requires closeout when profile/command-plan forbids it, the system should stop at `decision-lint` or `preflight` instead of relying on final-check after execution.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is stale sample-derived background. It still references `samplereverse` and `collect_missing_evidence`; it must not control this round.

The previous round `decision_20260621_closeout_report_refresh_contract_rework_v1` is accepted. Its final evidence shows:

- `codex_execution_report.md` status is `SUCCESS` and `acceptance_recommendation` is `ACCEPTED`.
- `run_closeout_result.json` has `closeout_status=PASSED`.
- `final_gate_result.json` has `gate_status=PASSED`, no blocking reasons, and `recommended_next_action=no_action_required`.
- `command_plan_execution_authority` passed, proving all recorded commands were authorized by command-plan.
- `report_summary_fields_match_synthesis` passed.

Existing related capabilities to reuse:

- `reverse_agent.project_gate.decision_lint`
- `reverse_agent.project_gate.preflight`
- `reverse_agent.project_gate.gate_profile`
- `reverse_agent.project_gate.command_plan`
- `reverse_agent.project_gate.final_check`
- command kind classification via `_command_kind()`
- existing fast/standard/full profile logic
- existing command-plan `commands`, `omitted_commands`, `required_command_kinds`, `closeout_allowed`, and expected exit code metadata
- tests in `tests/test_project_gate.py`

This is not a reverse-solving round. Do not inspect or run sample binaries. Do not use IDA, Ghidra, debuggers, emulators, runtime probes, harnesses, or full `solve_reports/`.

## 3. Do Not Do

Do not redo the previous closeout/report-refresh fixes.

Do not weaken `command_plan_execution_authority`, `report_summary_fields_match_synthesis`, or final-check.

Do not change the existing profile names. The project profile names are `fast`, `standard`, and `full`; do not introduce `medium`.

Do not make Tests authoritative over command-plan. The aim is the opposite: detect and block conflicts where Tests demand commands that command-plan does not authorize.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, or `.codex-skills/registry.json`.

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

Then inspect only files relevant to this engineering check:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/gate_profile_plan.json`
5. `project_state/gates/preflight_result.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/report_summary_synthesis.json`

Historical files may be read only by exact path when needed to build focused regression fixtures. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. What concrete conflict classes between decision Tests and command-plan are now detected?
2. Which component performs the check: `decision-lint`, `preflight`, `command-plan`, or final-check, and why?
3. How does the check detect a decision that requires `run-closeout` or `close-round` while `closeout_allowed=false`?
4. How does the check detect a decision Tests block that hard-codes a command listed in `command_plan.omitted_commands`?
5. How does the check avoid false positives for commands that command-plan explicitly authorizes under `standard` or `full`?
6. How does the check avoid treating explanatory prose or examples as mandatory commands?
7. How does the fix preserve command-plan execution authority and the previous closeout/report-refresh behavior?
8. What regression tests prove fast omitted-command conflicts, closeout conflicts, and standard/full authorized commands behave correctly?

## 6. Implementation Scope

Implement one bounded feature: decision/command-plan conflict detection before implementation proceeds.

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
- `project_state/rounds/round_20260621_decision_command_plan_conflict_lint_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Add or extend a helper that compares decision Tests / closeout policy text or contract fields against current command-plan and gate-profile semantics.
2. If decision Tests explicitly require a command kind that command-plan omits, report a conflict before implementation proceeds.
3. If decision text or contract requires `run-closeout`, `close-round`, or round archive artifacts while `closeout_allowed=false`, report a conflict before implementation proceeds.
4. If command-plan explicitly authorizes a command under `standard` or `full`, the check must not flag it.
5. If a command appears only as an example, optional diagnostic, or conditional instruction guarded by command-plan authorization, the check should not block it.
6. The check may start as `decision-lint` warning plus `preflight` BLOCKED for hard conflicts, but the policy must be explicit and tested.
7. Preserve current command-plan authority checks and final-check semantics.
8. Add focused regression tests for fast omitted commands, closeout forbidden conflicts, and full profile authorized commands.

Do not introduce a new profile system. Do not add `execution_log.json` in this round; that is a later roadmap item.

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

Targeted tests:

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

Run closeout only if command-plan explicitly includes or authorizes the closeout command for this round:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_decision_command_plan_conflict_lint_v1
```

If closeout runs, rerun report-summary and final-check afterward.

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation for unrelated reasons;
2. fixing this requires broad redesign of command-plan, decision parser, final-check, closeout, or execution-log storage;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. the fix requires running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, runtime probes, or full `solve_reports/` scans;
5. the conflict detector flags the current valid decision as conflicting without a clear reason;
6. the detector cannot distinguish required commands from examples or conditional command-plan-authorized instructions;
7. final-check, report-summary, or command-plan authority regresses;
8. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
9. tests fail or any required command exit code is nonzero;
10. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
