```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_profile_contract_closeout_consistency_rework_v1",
  "round_id": "round_20260708_profile_contract_closeout_consistency_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260707_profile_contract_alignment_rework_v1",
  "follows_last_round_id": "round_20260707_profile_contract_alignment_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "command_plan_must_not_omit_pytest": true,
  "command_plan_must_not_omit_close_round": true,
  "final_check_must_pass_before_acceptance": true,
  "run_closeout_must_pass_before_acceptance": true,
  "round_archive_required_before_acceptance": true,
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

Repair the remaining closeout consistency failures from the previous project-governance rework round.

Previous failed round:

```text
Round: round_20260707_profile_contract_alignment_rework_v1
Decision: decision_20260707_profile_contract_alignment_rework_v1
Audit outcome: REWORK_REQUIRED
```

The previous round fixed the fast-profile / pytest omission issue, but it still did not reach an accepted closeout state.

This round must make the governance gate chain internally consistent so that:

```text
report-summary passes;
final-check passes;
run-closeout passes;
close-round succeeds;
round_manifest.json is generated for this round;
execution reports only claim acceptance after all required gates support acceptance.
```

The target is not a new feature. The target is a clean, auditable closeout for the existing project-governance gate/report/archive workflow.

## 2. Current Evidence

Current task authority is this file:

```text
project_state/decision_packet.md
```

`task_packet.json` and `current_state.json` remain reverse-solving background state only. They do not control this round.

Current mainline:

```text
project_governance
```

Previous round status summary:

```text
codex_execution_report.md: FAILED / REWORK_REQUIRED
execution_report.md: FAILED / REWORK_REQUIRED
pytest_result.txt: FAILED summary, with pytest itself passing
report_summary_synthesis.json: FAILED
final_gate_result.json: FAILED
run_closeout_result.json: FAILED
close-round: FAILED
archive_status: not_archived
```

Important evidence from the previous round:

```text
1. decision_meta was valid and APPROVED.
2. reverse-agent-iteration@v2 was active.
3. command-plan selected full profile, not fast profile.
4. command-plan included pytest, run-closeout, and close-round.
5. pytest ran and passed.
6. preflight passed.
7. The report honestly said FAILED / REWORK_REQUIRED.
8. The remaining blockers were closeout/report-summary/final-check/archive consistency failures.
```

Known previous blocking reasons:

```text
close_round_is_last_command_block
pytest_result_exit_codes_match_command_plan
status_policy_valid
closeout_nested_failures_absent
report_summary_fields_match_synthesis
generated_artifacts_cover_round_archive
```

Existing capabilities to reuse:

```text
decision-packet authority
command-plan authority
project_gate
preflight
report-summary
execution-log
final-check
pytest_result
execution_report / codex_execution_report parity
run-closeout
close-round
round manifest archive handling
round delta summary
status policy checks
```

Do not duplicate these systems. Repair only the remaining inconsistencies that prevent a successful closeout.

Artifact freshness:

```text
Use current project_state/gates artifacts only if their decision_id and round_id match this round after regeneration.
Old artifacts from round_20260707_profile_contract_alignment_rework_v1 are evidence for the failure cause, not current acceptance evidence.
```

Negative results:

```text
project_state/negative_results.json is reverse-solving oriented and includes global hard blocks such as not committing full solve_reports. Do not repeat prohibited solve_reports behavior. No reverse-solving exploration is authorized in this round.
```

Context packet / workstream registry:

```text
Do not modify context packet or workstreams in this round.
If they are stale or missing, report that as non-authoritative background unless a generated gate explicitly requires them.
```

This round must not repeat existing functionality. It must strengthen the existing gate/report/closeout path instead of creating a parallel closeout or report system.

## 3. Do Not Do

Do not implement Phase A.1 scoped metadata visibility refresh.

Do not create or modify:

```text
project_state/domains/*
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/context/*
project_state/roadmap/workstreams.json
```

Do not modify:

```text
.codex-skills/*
.github/workflows/*
frontend/*
solve_reports/*
training_materials/local_reverse/*
project_state/*.db
project_state/index.sqlite
```

Do not perform:

```text
sample solving
candidate or flag generation
runtime probing
dynamic debugging
IDA / Ghidra / OllyDbg / MCP invocation
Web runtime work
database migration
runner dispatch
workflow dispatch
cleanup apply
deletion
file move
archive compaction
local commit
local push
branch creation
PR creation
merge
rebase
```

Do not claim `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` unless all required current-round evidence supports it:

```text
preflight PASSED
pytest PASSED
report-summary PASSED
execution-log acceptable
final-check PASSED
run-closeout PASSED
close-round PASSED
round_manifest.json generated for this round
execution_report and codex_execution_report agree
pytest_result matches the report and command-plan
```

## 4. Files To Inspect

Required files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/gate_profile_plan.json
project_state/gates/preflight_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/execution_log.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/round_delta_summary.json
project_state/gates/round_baseline.json
project_state/gates/startup_snapshot.json
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
```

Required source/test files to inspect if changing logic:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer all of the following:

1. Is `decision_meta` valid, APPROVED, and on `project_governance`?
2. Is `reverse-agent-iteration@v2` active in `.codex-skills/registry.json`?
3. Does command-plan carry this decision ID and round ID?
4. Does command-plan select standard/full profile rather than fast profile?
5. Does command-plan include pytest instead of listing pytest in omitted_commands?
6. Does command-plan include run-closeout and close-round because this decision requires closeout?
7. Did startup status commands run in the required order before substantive work?
8. Did preflight pass before implementation?
9. Were all executed non-startup commands authorized by command-plan?
10. Were any omitted commands executed?
11. Did source/test changes stay within allowed files?
12. Were forbidden state files left unchanged?
13. Did pytest run and pass?
14. Does `pytest_result.txt` carry the current decision ID, report ID, round ID, and command transcript?
15. Do recorded command exit codes match command-plan expected exit codes, including run-closeout and close-round?
16. Does report-summary pass and match the execution report?
17. Does final-check pass?
18. Does run-closeout pass?
19. Does close-round pass and generate `project_state/rounds/round_20260708_profile_contract_closeout_consistency_rework_v1/round_manifest.json`?
20. Do generated_artifacts / files_changed cover current round delta and round archive artifacts without stale omissions?
21. Are nested FAILED states absent from `run_closeout_result.json` when the report claims acceptance?
22. Does `execution_report.md` semantically match `codex_execution_report.md`?
23. Did the round avoid Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, deletion, file moves, and external tool work?
24. Did the final report refrain from claiming acceptance until all required gates passed?

Final audit conclusion must be exactly one of:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
REWORK_REQUIRED
BLOCKED
```

## 6. Implementation Scope

This is a bounded project-governance rework.

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

Allowed generated state/report artifacts:

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/*.json
project_state/gates/*.txt
project_state/rounds/round_20260708_profile_contract_closeout_consistency_rework_v1/*
```

Required work:

```text
1. Fix report-summary synthesis/status behavior so current-round report-summary can pass when the report and generated artifacts are internally consistent.
2. Fix final-check checks that incorrectly treat current expected closeout behavior as a blocker, without weakening real hard gates.
3. Fix run-closeout / close-round sequencing or evidence recording so close-round succeeds only after final-check is actually clean.
4. Fix command exit-code accounting so pytest_result, execution_log, command-plan, final-check, and run-closeout agree.
5. Ensure generated_artifacts and files_changed cover round archive artifacts when close-round succeeds.
6. Ensure nested FAILED states are absent when and only when the round is truly accepted.
7. Regenerate reports and gate artifacts after the fix.
8. Preserve the rule that pytest_result alone cannot imply acceptance.
```

Compatibility requirements:

```text
1. Do not remove legacy codex_execution_report.md support.
2. Preserve neutral execution_report.md alias behavior.
3. Preserve command-plan as command authority.
4. Preserve expected_exit_codes semantics.
5. Preserve hard failure on real unauthorized commands, forbidden paths, stale current evidence, or false accepted reports.
6. Do not make report-summary/final-check pass by suppressing real failures.
```

This round may adjust only the minimum necessary project-governance gate/report/closeout logic.

## 7. Tests

Run only commands authorized by the regenerated `project_state/gates/command_plan.json`.

Expected command categories:

```text
startup path/status commands
startup-snapshot if required by local workflow
preflight
gate-profile
command-plan
command-plan --json
pytest
report-summary
execution-log
final-check
run-closeout
close-round if command-plan lists it separately
```

At minimum, the command-plan should require coverage equivalent to:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260708_profile_contract_closeout_consistency_rework_v1
```

If command-plan still omits pytest while source files are changed, stop and report `REWORK_REQUIRED`.

If command-plan still selects fast profile for this source-level governance repair decision, stop and report `REWORK_REQUIRED`.

If report-summary, final-check, run-closeout, or close-round fails, the execution report must say `FAILED / REWORK_REQUIRED`.

`project_state/pytest_result.txt` must contain:

```text
current decision_id
current round_id
current report_id
startup transcript
pytest transcript
command-plan transcript or command-plan --json transcript
report-summary transcript
execution-log transcript
final-check transcript
run-closeout transcript
close-round transcript if executed separately
exit codes
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
required authority files cannot be read;
reverse-agent-iteration@v2 is missing or inactive;
command-plan cannot be generated;
required source/test files are unavailable;
repository state prevents safe local execution before any implementation work.
```

Stop with `REWORK_REQUIRED` if:

```text
command-plan selects fast profile;
command-plan omits pytest while source repair is authorized;
command-plan omits run-closeout while closeout is required;
command-plan omits close-round without a documented valid non-recursive closeout alternative;
preflight fails;
pytest fails or is omitted;
report-summary fails;
execution-log is missing or mismatched;
final-check fails;
run-closeout fails;
close-round fails when required;
round_manifest.json is not generated for this round after claimed closeout;
pytest_result is missing, stale, or mismatched;
execution_report.md and codex_execution_report.md disagree semantically;
report-summary synthesis disagrees with report status or generated artifacts;
files_changed or generated_artifacts omit current round archive artifacts after successful close-round;
run_closeout_result.json contains active nested FAILED states while the report claims acceptance;
source/test changes exceed allowed files;
forbidden state files are modified;
an omitted or unauthorized command is executed;
the work requires Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, deletion, file move, archive compaction, or external tool work;
local executor runs commit, push, branch creation, PR creation, merge, or rebase.
```

A later separate decision may return to scoped metadata visibility, project_state domain taxonomy, User Solve, Web, tool integration, or automation. Do not start any of those directions in this round.
