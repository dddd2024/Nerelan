```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260621_closeout_report_refresh_contract_rework_v1",
  "round_id": "round_20260621_closeout_report_refresh_contract_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "rework_target_decision_id": "decision_20260621_gate_profile_authority_cleanup_v1",
  "rework_target_round_id": "round_20260621_gate_profile_authority_cleanup_v1",
  "primary_cleanup_goal": "Fix remaining closeout/report refresh contract defects discovered after gate-profile authority cleanup.",
  "primary_issues": [
    "_refresh_codex_report_for_closeout does not set decision_contract.required_closeout_artifacts",
    "close_round post-archive flow lacks report status refresh and creates a chicken-and-egg cycle",
    "_refresh_codex_report_for_closeout incorrectly overwrites pytest_result header status"
  ],
  "command_plan_authority_required": true,
  "accepted_requires_run_closeout_passed": true,
  "accepted_requires_final_check_passed": true,
  "accepted_requires_report_summary_passed": true,
  "forbid_hiding_evidence_by_deleting_command_blocks": true,
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
    "project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/*"
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

Repair the remaining closeout/report refresh contract defects discovered after `decision_20260621_gate_profile_authority_cleanup_v1`.

The previous cleanup completed its direct goal: `command_plan_execution_authority` no longer has the original `gate-profile` warning, `run-closeout` passed, `final-check` passed all checks, and the round archive was created. During that process, three adjacent closeout defects were exposed and must now be fixed in a narrow engineering round:

1. `_refresh_codex_report_for_closeout()` does not populate `decision_contract.required_closeout_artifacts`.
2. `close_round()` lacks a post-archive report status refresh, creating a chicken-and-egg cycle between archive creation, report-summary synthesis, and final-check status.
3. `_refresh_codex_report_for_closeout()` incorrectly overwrites the `pytest_result.txt` header status.

This round must fix these defects without redoing the prior gate-profile authority cleanup.

## 2. Current Evidence

Mainline: `engineering_branch`.

`task_packet.json` is only background. It remains a stale/sample-derived `samplereverse` task and must not control this round.

The prior decision was `decision_20260621_gate_profile_authority_cleanup_v1`. Its reported end state was that the round target completed: the original warning from `command_plan_execution_authority` about `gate-profile` was cleared, `run-closeout` passed all 10 steps, `final-check` passed 50+ checks, and round archive creation succeeded.

The remaining issues are not reverse-solving issues and not sample evidence issues. They are closeout/report-refresh contract defects inside `project_gate`:

- closeout refresh should write `decision_contract.required_closeout_artifacts` when archive files become required evidence;
- closeout should refresh report status after archive creation so report-summary and final-check no longer depend on stale pre-archive status fields;
- closeout report refresh must not corrupt or overwrite the `pytest_result.txt` header status, because pytest_result is an execution log and should retain the real command/test status semantics.

Relevant existing capabilities to reuse:

- `reverse_agent.project_gate.close_round`
- `reverse_agent.project_gate.run_closeout`
- `reverse_agent.project_gate.report_summary`
- `reverse_agent.project_gate.final_check`
- `_refresh_codex_report_for_closeout()`
- pytest/result parsing and report-summary synthesis helpers
- existing closeout and report-summary tests in `tests/test_project_gate.py`

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`. Do not run samples, solvers, harnesses, debuggers, emulators, IDA, Ghidra, OllyDbg, x64dbg, runtime probes, or GUI workflows.

## 3. Do Not Do

Do not redo the prior `gate-profile` authority cleanup.

Do not weaken `command_plan_execution_authority`, `report_summary_fields_match_synthesis`, or final-check to force a PASS.

Do not delete command evidence from `pytest_result.txt` to hide prior behavior.

Do not rewrite unrelated project_state architecture, add a database, add a new workflow engine, or introduce a broad execution-log migration in this round.

Do not mutate `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, or `.codex-skills/registry.json`.

Do not continue `samplereverse` solving. Do not run sample binaries, solvers, harnesses, runtime probes, IDA/Ghidra, debuggers, emulators, GUI workflows, or full `solve_reports/` scans.

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

Then inspect only files relevant to this closeout/report-refresh rework:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/round_close_snapshot.json`
8. `project_state/rounds/round_20260621_gate_profile_authority_cleanup_v1/round_manifest.json` only if needed to understand the previous closeout state

Historical files may be read only by exact path. Do not scan entire `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

Answer all items in `project_state/codex_execution_report.md` before claiming success:

1. Why does `_refresh_codex_report_for_closeout()` need to populate `decision_contract.required_closeout_artifacts`, and which archive files should be listed?
2. Why does `close_round()` need a post-archive report status refresh, and how did the previous behavior create a chicken-and-egg cycle?
3. Why is it incorrect for `_refresh_codex_report_for_closeout()` to overwrite the `pytest_result.txt` header status?
4. Which component owns each field after the fix: report status, acceptance recommendation, files_changed, generated_artifacts, required_closeout_artifacts, and pytest_result status?
5. How does the fix preserve command-plan authority and avoid hiding evidence?
6. How does the fix preserve the prior successful gate-profile authority cleanup?
7. What tests prove `run-closeout`, `report-summary`, and `final-check` all pass after archive creation?
8. What tests prove `pytest_result.txt` header status is preserved correctly during closeout refresh?

## 6. Implementation Scope

Implement one bounded engineering fix: make closeout report refresh produce a consistent post-archive report contract without corrupting pytest_result status.

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
- `project_state/rounds/round_20260621_closeout_report_refresh_contract_rework_v1/*` only if command-plan authorizes closeout

Required implementation behavior:

1. Update `_refresh_codex_report_for_closeout()` so `codex_report_summary` includes a correct `decision_contract.required_closeout_artifacts` entry or equivalent project-supported field when archive artifacts become required after closeout.
2. Update `close_round()` or its closeout flow so after archive creation it refreshes report status/acceptance fields before final post-archive report-summary/final-check validation.
3. Ensure `_refresh_codex_report_for_closeout()` does not overwrite or falsify the `pytest_result.txt` header status. It may append or preserve closeout evidence, but it must not convert a real execution-log status into an artificial report status.
4. Preserve `files_changed` and `generated_artifacts` coverage for round archive files.
5. Preserve the existing command-plan authorization semantics, including `run-closeout` authorization for full profile rounds.
6. Add focused regression tests covering all three defects.

Acceptable outcomes:

- `python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_closeout_report_refresh_contract_rework_v1` passes when command-plan authorizes it.
- `report-summary` passes or has only explicitly non-blocking warnings.
- `final-check` passes with no blocking failures.
- `pytest_result.txt` header status remains semantically tied to real execution results and is not overwritten by report refresh.

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260621_closeout_report_refresh_contract_rework_v1
```

If closeout runs, rerun report-summary and final-check afterward:

```powershell
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Record all executed commands, stdout/stderr, exit codes, and final conclusion in `project_state/pytest_result.txt`. The structured summary must match this decision_id and round_id.

## 8. Stop Conditions

Stop and report `BLOCKED` or `REWORK_REQUIRED` if:

1. preflight fails before implementation;
2. fixing this requires broad redesign of command-plan, final-check, report-summary, closeout, or execution-log storage;
3. source changes outside `reverse_agent/project_gate.py` and `tests/test_project_gate.py` are needed;
4. the fix requires running samples, solvers, harnesses, IDA/Ghidra, debuggers, emulators, runtime probes, or full `solve_reports/` scans;
5. `_refresh_codex_report_for_closeout()` still omits required closeout artifact contract fields after archive creation;
6. `close_round()` still requires stale pre-archive report status to pass post-archive final-check;
7. `_refresh_codex_report_for_closeout()` still overwrites the `pytest_result.txt` header status incorrectly;
8. `run-closeout`, `report-summary`, or `final-check` remains blocked after the intended fix;
9. `codex_execution_report.md`, `pytest_result.txt`, or gate artifacts use stale decision_id/round_id;
10. tests fail or any required command exit code is nonzero;
11. closeout archive files are created but not listed in `files_changed` and `generated_artifacts`.
