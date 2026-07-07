```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260707_profile_contract_alignment_rework_v1",
  "round_id": "round_20260707_profile_contract_alignment_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260707_fast_profile_report_truth_rework_v1",
  "follows_last_round_id": "round_20260707_fast_profile_report_truth_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "command_plan_must_not_omit_pytest": true,
  "command_plan_must_not_omit_close_round": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_control_plane.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/state_manifest.json",
    "project_state/context/*",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/*.db",
    "project_state/index.sqlite"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Fix the profile/contract mismatch that caused the previous rework round to fail.

Previous failed round:

```text
decision_20260707_fast_profile_report_truth_rework_v1
round_20260707_fast_profile_report_truth_rework_v1
```

Observed failure:

```text
The decision authorized source-level gate repair and expected pytest/closeout behavior,
but command-plan still generated a fast profile,
omitted pytest,
omitted close-round,
and final-check failed because source code changed under fast profile.
```

This round must align the decision contract, implementation scope parser, command-plan profile selection, pytest requirement, report-summary, final-check, and closeout behavior.

Accepted target:

```text
command-plan uses a standard/full profile for source-level governance repair;
pytest is not omitted;
close-round is not omitted if closeout is required;
preflight passes before implementation;
pytest passes;
report-summary passes;
final-check passes;
run-closeout and close-round complete if command-plan requires them;
reports do not claim acceptance unless gates support it.
```

## 2. Current Evidence

Current authority is this `project_state/decision_packet.md`.

The previous round honestly ended as `FAILED / REWORK_REQUIRED`, not false accepted. That part is acceptable.

Remaining current blockers from the previous round:

```text
preflight_result.json: FAILED
pytest_result.txt: FAILED
final_gate_result.json: FAILED
blocking reasons: pytest_result_exit_codes_match_command_plan, fast_profile_scope_valid, fast_profile_pytest_not_omitted_with_source_changes, status_policy_valid
```

Root cause:

```text
The decision and implementation intent were source-level repair,
but command-plan selected fast profile and omitted pytest/close-round.
```

`task_packet.json` and `current_state.json` are reverse-solving background state only. They do not control this round.

Existing capabilities to reuse:

```text
decision-packet authority
command-plan authority
project_gate
preflight
report-summary
final-check
pytest_result
execution_log
run-closeout / close-round
codex/execution report parity
```

Do not duplicate those systems. Only repair the mismatch that made them disagree.

## 3. Do Not Do

Do not implement Phase A.1 scoped metadata visibility refresh.

Do not create `project_state/domains/*`.

Do not modify `current_state.json`, `task_packet.json`, `negative_results.json`, `artifact_index.json`, `state_manifest.json`, `.codex-skills/*`, `.github/workflows/*`, `frontend/*`, `solve_reports/*`, `training_materials/local_reverse/*`, or database files.

Do not perform sample solving, external reverse-tool invocation, Web runtime, workflow dispatch, runner dispatch, cleanup apply, deletion, file move, database migration, local commit, local push, branch creation, PR creation, merge, or rebase.

Do not claim `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` unless preflight, pytest, report-summary, final-check, and required closeout/close-round evidence support it.

## 4. Files To Inspect

Required files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/preflight_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/execution_log.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/gate_profile_plan.json
project_state/gates/round_delta_summary.json
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
```

Allowed source files:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
```

Allowed test files:

```text
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer:

1. Is `decision_meta` valid, APPROVED, and on `project_governance`?
2. Is `reverse-agent-iteration@v2` active?
3. Does command-plan carry this decision ID and round ID?
4. Does command-plan select a standard/full profile rather than fast profile when source-level repair is authorized?
5. Does command-plan include pytest instead of listing pytest in omitted_commands?
6. Does command-plan include run-closeout/close-round if closeout is required?
7. Does preflight pass before implementation?
8. Were all executed commands authorized by command-plan?
9. Were any omitted commands executed?
10. Did source/test changes stay within allowed files?
11. Were forbidden state files left unchanged?
12. Did pytest run and pass?
13. Does report-summary match the execution report?
14. Does final-check pass if the report claims acceptance?
15. If final-check fails, does the report honestly say REWORK_REQUIRED?
16. Were run-closeout and close-round executed only if command-plan authorized them?
17. If close-round ran, was the round archived consistently?
18. Did the round avoid Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, and external tool work?

Final conclusion must be exactly one of:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
REWORK_REQUIRED
BLOCKED
```

## 6. Implementation Scope

This is a bounded project-governance rework.

Allowed paths are exactly:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/*.json
project_state/rounds/round_20260707_profile_contract_alignment_rework_v1/*
```

Required work:

```text
1. Make Implementation Scope parseable by existing preflight rules.
2. Ensure command-plan does not choose fast profile when this decision allows source-level repair.
3. Ensure pytest is required when source files are in round delta.
4. Ensure closeout/close-round requirements are consistent with command-plan.
5. Preserve the rule that pytest_result alone cannot imply acceptance.
6. Regenerate reports and gate artifacts after the fix.
```

This round may adjust command-plan/profile-selection logic only as needed to align source-level repair with standard/full validation.

## 7. Tests

Run only commands authorized by `project_state/gates/command_plan.json`.

Expected command categories:

```text
startup status commands
startup-snapshot
command-plan
preflight
pytest for project_gate/project_reports/project_control_plane
report-summary
final-check
run-closeout
close-round
```

If command-plan still omits pytest while source files are changed, stop and report `REWORK_REQUIRED`.

If command-plan still selects fast profile for this source-level repair decision, stop and report `REWORK_REQUIRED`.

`pytest_result.txt` must contain current decision ID, round ID, report ID, and command transcript.

Reports must not claim acceptance unless preflight, pytest, report-summary, final-check, and required closeout/close-round all support it.

## 8. Stop Conditions

Stop with `BLOCKED` if required authority files cannot be read, the active skill is missing, or command-plan cannot be generated.

Stop with `REWORK_REQUIRED` if:

```text
command-plan selects fast profile;
command-plan omits pytest while source repair is authorized;
command-plan omits close-round while closeout is required;
preflight fails;
pytest fails or is omitted;
report-summary fails;
final-check fails;
execution_log or pytest_result is missing or mismatched;
source/test changes exceed allowed files;
forbidden state files are modified;
an omitted or unauthorized command is executed;
the work requires Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, deletion, file move, or external tool work;
local executor runs commit, push, branch creation, PR creation, merge, or rebase.
```

After this round is accepted, a separate later decision may return to Phase A.1 scoped metadata visibility refresh. Do not start Phase A.1 here.
