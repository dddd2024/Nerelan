```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260707_fast_profile_report_truth_rework_v1",
  "round_id": "round_20260707_fast_profile_report_truth_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1",
  "follows_last_round_id": "round_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1",
  "previous_audit_doc": "docs/audits/20260707_fast_close_round_key_fix_audit.md",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "primary_goal": "Repair the status-truthfulness mismatch so report-summary, final-check, execution reports, pytest_result, and execution_log agree on one truthful state.",
  "command_plan_authority_required": true,
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_state.py",
    "reverse_agent/project_state_manifest.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_state.py",
    "tests/test_project_state_manifest.py"
  ],
  "allowed_generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260707_fast_profile_report_truth_rework_v1/*"
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

Repair the project-governance status mismatch left by the previous fast roadmap-registration round.

Previous round:

```text
decision_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
round_20260707_next_step_roadmap_registration_fast_close_round_key_fix_v1
```

Current problem:

```text
execution reports claim ACCEPTED_WITH_LIMITATIONS;
report-summary synthesizes FAILED / REWORK_REQUIRED;
final-check is FAILED with blocking reasons;
pytest_result only proves command exit-code coverage, not final acceptance.
```

This decision authorizes a bounded rework so the current reports, report-summary, final-check, pytest_result, execution_log, and round archive agree on a truthful state.

Accepted target:

```text
report-summary passes;
final-check passes;
execution_report.md and codex_execution_report.md match;
pytest_result and execution_log match command-plan;
closeout / close-round run only if command-plan authorizes them;
no report claims acceptance while final-check has blocking reasons.
```

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. The previously uploaded audit and roadmap files are reference material only, not execution authority:

```text
docs/audits/20260707_fast_close_round_key_fix_audit.md
docs/roadmap/next_step_after_fast_close_round_key_fix_audit.md
```

`task_packet.json` remains advisory/background only. It still reflects reverse-solving sample state and must not control this project-governance round.

`current_state.json` still contains reverse-solving sample state. It must not be converted into a global summary in this round.

Known current failure:

```text
project_state/gates/report_summary_synthesis.json: FAILED / REWORK_REQUIRED
project_state/gates/final_gate_result.json: FAILED
project_state/codex_execution_report.md: ACCEPTED_WITH_LIMITATIONS
project_state/execution_report.md: ACCEPTED_WITH_LIMITATIONS
```

Existing capabilities that must be reused, not duplicated:

```text
decision-packet authority;
command-plan authority;
project_gate;
report-summary;
final-check;
run-closeout / close-round;
execution_log;
pytest_result;
codex/execution report parity;
state_manifest and artifact_index foundations;
workstream registry and context packet foundations.
```

This round must not proceed to Phase A.1, Phase B, User Solve, Web, tool integration, training dataset, database, or runner automation.

## 3. Do Not Do

Do not implement Phase A.1.

Do not create `project_state/domains/*`.

Do not modify `current_state.json`, `task_packet.json`, `negative_results.json`, `artifact_index.json`, `state_manifest.json`, `.codex-skills/*`, `.github/workflows/*`, `frontend/*`, `solve_reports/*`, or database files.

Do not perform sample solving, external tool invocation, Web runtime, workflow dispatch, runner dispatch, cleanup apply, deletion, file move, database migration, local commit, local push, branch creation, PR creation, merge, or rebase.

Do not claim `ACCEPTED` or `ACCEPTED_WITH_LIMITATIONS` if final-check still has blocking reasons.

## 4. Files To Inspect

Required files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/preflight_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
docs/audits/20260707_fast_close_round_key_fix_audit.md
docs/roadmap/next_step_after_fast_close_round_key_fix_audit.md
```

Allowed source/test inspection and modification is limited to the files listed in `decision_contract.allowed_source_files` and `decision_contract.allowed_test_files`.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer:

1. Is `decision_meta` valid, APPROVED, and on `project_governance`?
2. Is `reverse-agent-iteration@v2` active in the registry?
3. Does the report match this decision ID and round ID?
4. Does the report acknowledge the previous decision was already consumed/submitted?
5. Does command-plan carry this decision ID and round ID?
6. Were all executed commands authorized by command-plan?
7. Were any omitted commands executed?
8. Did source/test changes stay within the allowed lists?
9. Were forbidden state files left unchanged?
10. Does report-summary match the execution report?
11. Does final-check pass if the report claims acceptance?
12. If final-check fails, does the report honestly say REWORK_REQUIRED?
13. Does pytest_result match this decision, round, report, and transcript?
14. Does execution_log cover required command-plan commands?
15. If closeout/close-round ran, were they command-plan-authorized and archived consistently?
16. Did the round avoid Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, and external tool work?

Audit conclusion must be exactly one of:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
REWORK_REQUIRED
BLOCKED
```

Use `REWORK_REQUIRED` if report-summary or final-check still fails, if status fields disagree, or if forbidden files/capabilities are touched.

## 6. Implementation Scope

This is a bounded status-truthfulness repair.

Allowed work:

```text
1. Diagnose report-summary/final-check/report mismatch.
2. Fix minimal gate/report/status handling if needed, only in allowed source files.
3. Add/update focused tests only in allowed test files.
4. Regenerate pytest_result, execution reports, report-summary, final-check, execution_log, and closeout artifacts under command-plan authority.
5. Archive this new round only if command-plan authorizes closeout/close-round.
```

The key invariant:

```text
pytest_result PASSED is not enough for accepted status;
accepted reports require report-summary and final-check support.
```

If a stale closeout artifact from the previous fast round is involved, the fix must ensure stale previous-round closeout failures are not treated as current blockers unless the current decision and round require them.

## 7. Tests

Run only commands authorized by `project_state/gates/command_plan.json`.

Expected command categories:

```text
startup status commands;
command-plan;
preflight;
focused pytest for project gate/report/control-plane/state behavior;
report-summary;
final-check;
run-closeout / close-round if command-plan requires them.
```

If command-plan differs from this expectation, command-plan wins.

Commands omitted by command-plan must not be executed.

`pytest_result.txt` must contain the command transcript and current decision/round/report IDs.

`codex_execution_report.md` and `execution_report.md` must not claim acceptance unless report-summary and final-check support it.

## 8. Stop Conditions

Stop with `BLOCKED` if required authority files cannot be read, the registry does not mark the skill active, or command-plan/preflight cannot be generated.

Stop with `REWORK_REQUIRED` if:

```text
report-summary fails;
final-check fails;
report status and gate truth disagree;
pytest_result is missing or mismatched;
execution_log is missing or mismatched;
source/test changes exceed allowed files;
forbidden state files are modified;
an omitted or unauthorized command is executed;
the work requires Phase A.1, domains, sample solving, Web, database, runner, workflow, cleanup, deletion, file move, or external tool work;
local executor runs commit, push, branch creation, PR creation, merge, or rebase.
```

If this rework is accepted, the next separate decision may return to Phase A.1 scoped metadata visibility refresh. Do not start Phase A.1 here.
