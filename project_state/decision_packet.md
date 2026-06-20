```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_command_plan_execution_authority_v1",
  "round_id": "round_20260621_command_plan_execution_authority_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5".replace("d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5", "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5"),
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "command_plan_authority_required": true,
  "forbid_unplanned_commands_on_success": true,
  "closeout_policy": "if_profile_allows",
  "required_files_changed": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "required_generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/command_plan.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/final_gate_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json"
  ],
  "accepted_requires_final_check_passed": true
}
```

# DECISION_PACKET

## 1. Goal

Make `command-plan` the execution authority for gate/profile-driven rounds. The immediate defect to fix is that a decision may list commands such as pytest or run-closeout while `gate-profile` and `command-plan` omit them for a fast profile; Codex can still execute those omitted commands manually, producing stale IDs, contradictory closeout state, and expensive gate work.

Implement a small, testable guard in `project_gate` so final validation can detect when the recorded execution log contains commands that were not authorized by the current round's `command-plan`. Do not redesign the whole gate system in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is only a stale/sample-derived suggestion. It still says `execution_scope` is `decision_packet_controls_current_round`, but its derived task is `collect_missing_evidence` for `samplereverse`; that is not this round's task.

`current_state.json` is still a `samplereverse` sample state with missing runtime/artifact evidence. This round must not resume sample solving.

`negative_results.json` blocks old sample_solver blind search, beam/budget-only expansion, compare_semantics_agree=false primary candidates, full `solve_reports/` commit, and repeated failed candidate/runtime branches.

The previous training capability round failed because report, pytest summary, gate artifacts, closeout expectations, and stale IDs did not align. In particular, command-plan/gate-profile had already selected fast behavior, but the decision/test contract still encouraged or required heavier commands.

Existing relevant capabilities already present and must be reused:

- `reverse_agent.project_gate.classify_gate_profile`
- `reverse_agent.project_gate.gate_profile`
- `reverse_agent.project_gate.command_plan`
- `reverse_agent.project_gate.final_check`
- recorded command parsing from `pytest_result.txt`
- command kind classification via `_command_kind`
- existing tests in `tests/test_project_gate.py`

The repository already has fast/standard/full gate profile logic. Do not implement a second profile system.

## 3. Do Not Do

Do not continue `samplereverse` solving.

Do not run samples, binaries, runtime probes, harnesses, debuggers, emulators, GUI workflows, IDA, Ghidra, x64dbg, or OllyDbg.

Do not scan full `solve_reports/`.

Do not rewrite `.codex-skills/`.

Do not rename the existing `standard` profile to `medium` in this round. If aliasing `medium -> standard` is useful, record it as a future task, not part of this implementation.

Do not add a new gate profile system. Reuse the existing fast/standard/full profile and command-plan metadata.

Do not make `decision_packet.md` mutable during execution except for the initial user-authorized replacement already present at round start.

Do not weaken final-check to make the previous failure pass. The aim is stricter execution-authority detection, not bypassing failures.

## 4. Files To Inspect

Default state files:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/codex_execution_report.md`
6. `project_state/decision_packet.md`
7. `project_state/pytest_result.txt`
8. `.codex-skills/registry.json`

Gate implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_state.py` only if existing tests require shared fixtures or report-summary behavior

Current gate artifacts for failure analysis:

1. `project_state/gates/gate_profile_plan.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/report_summary_synthesis.json`
4. `project_state/gates/final_gate_result.json`

Historical artifacts may be read only by exact path when needed to understand an existing regression test. Do not scan full `project_state/rounds/` or `solve_reports/`.

## 5. Required Audit

Before editing, answer these in `project_state/codex_execution_report.md`:

1. Where is the existing fast/standard/full profile logic implemented, and what command kinds does each profile require?
2. How does current `command-plan` represent omitted commands, active commands, profile metadata, and `closeout_allowed`?
3. How are executed commands currently recorded and parsed from `pytest_result.txt`?
4. Which prior failure would have been caught earlier if unplanned/omitted commands were treated as a final-check violation?
5. Which command kinds should be exempt from unplanned-command failure, if any, and why?
6. Should an unplanned command be FAIL or WARN when report status is already FAILED? Define the policy clearly.
7. How will the new check avoid breaking standard/full rounds where pytest or close-round is actually planned?
8. How will tests prove that fast profile omits pytest/run-closeout/close-round and final-check detects those commands if they were nevertheless recorded as executed?

## 6. Implementation Scope

Implement one bounded feature: command-plan execution authority validation.

Allowed source changes:

- `reverse_agent/project_gate.py`
- `tests/test_project_gate.py`

Allowed generated/project-state files:

- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/command_plan.json`
- `project_state/gates/gate_profile_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/round_baseline.json`
- `project_state/gates/round_delta_summary.json`
- `project_state/gates/round_close_snapshot.json` only if command-plan/profile permits closeout
- `project_state/rounds/round_20260621_command_plan_execution_authority_v1/*` only if command-plan/profile permits closeout

Required implementation behavior:

1. Add or extend a final-check helper that compares executed commands recorded in `pytest_result.txt` against the current round's `command_plan.commands`.
2. Treat commands listed only in `command_plan.omitted_commands` as unauthorized if they appear as executed commands for the same round.
3. Treat command kinds absent from the active command-plan as unauthorized, except for explicitly safe startup/status commands already represented by the command-plan startup phase.
4. A SUCCESS/ACCEPTED report with unauthorized commands must fail final-check.
5. A FAILED/REWORK_REQUIRED report may downgrade unauthorized command detection to WARN only if the report explicitly states it stopped because of the unauthorized command. Otherwise keep it FAIL.
6. Preserve standard/full behavior: pytest, doctor, lint-report, run-round, run-closeout, or close-round must be accepted when command-plan actually includes them for the current profile.
7. Ensure stale command-plan artifacts from a previous round cannot authorize current-round commands.
8. Add focused regression tests for fast, standard, and full behavior.

Do not require a new `execution_log.json` in this round. That can be a later migration. This round may continue using `pytest_result.txt` as the recorded command source.

## 7. Tests

Run startup checks first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Then run targeted tests while developing:

```powershell
python -m pytest tests/test_project_gate.py -q
```

Before final report, run:

```powershell
python -m reverse_agent.project_gate decision-lint --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_state.py -q
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

After `command-plan --json`, follow the current command-plan output. Run closeout only if the current command-plan and gate profile both permit it. If the current profile says closeout is not allowed, do not run close-round or run-closeout.

Record all commands and results in `project_state/pytest_result.txt` with a structured summary whose decision/report/round IDs match this decision.

## 8. Stop Conditions

Stop and report `BLOCKED` if:

1. implementing the check requires a broad rewrite of command-plan, final-check, or report-summary;
2. tests require running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, or runtime probes;
3. command-plan for this engineering source-change round says closeout is forbidden while decision/final-check requires closeout;
4. current command-plan artifacts reference a stale decision/report/round and cannot be regenerated safely;
5. pytest_result command parsing is insufficient to distinguish active planned commands from omitted commands without a larger execution-log migration;
6. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
7. final-check still passes a SUCCESS report that executed a command omitted by fast profile;
8. final-check fails only because of unrelated stale training artifacts and not because of this implementation; in that case report the unrelated blocker explicitly instead of broadening scope.
