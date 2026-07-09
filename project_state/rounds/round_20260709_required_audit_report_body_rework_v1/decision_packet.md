```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260709_required_audit_report_body_rework_v1",
  "round_id": "round_20260709_required_audit_report_body_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_user_solve_contract_test_coverage_rework_v1",
  "follows_last_round_id": "round_20260708_user_solve_contract_test_coverage_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "report_body_required_audit_required": true,
  "report_body_required_audit_must_cover_all_items": true,
  "structured_summary_remains_required": true,
  "final_check_must_validate_required_audit_body": true,
  "allowed_source_files": [
    "reverse_agent/project_reports.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_control_plane.py"
  ],
  "allowed_test_files": [
    "tests/test_project_reports.py",
    "tests/test_project_gate.py",
    "tests/test_project_control_plane.py"
  ],
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260709_required_audit_report_body_rework_v1/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/user_solve_views.py",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/state_manifest.json",
    "project_state/context/*",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite",
    "docs/roadmap/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Repair the audit limitation from the previous User Solve Contract test coverage rework round by making execution reports human-readable as well as machine-checkable.

Previous round:

```text
decision_id: decision_20260708_user_solve_contract_test_coverage_rework_v1
round_id: round_20260708_user_solve_contract_test_coverage_rework_v1
audit_outcome: ACCEPTED_WITH_LIMITATIONS
```

The previous round satisfied the core evidence path: command-plan, pytest_result, reports, final-check, execution_log, run-closeout, and round_manifest all covered the User Solve tests. The remaining limitation is that the report body `## Required Audit` section was not useful enough for human review.

This round must make `codex_execution_report.md` and `execution_report.md` include a substantive `## Required Audit` body that answers every Required Audit item from the current decision. It must preserve the existing structured JSON summary blocks and final-check behavior.

This is an engineering report/gate readability hardening round only.

## 2. Current Evidence

Current task authority is:

```text
project_state/decision_packet.md
```

`task_packet.json` is background only and must not control this round.

Current mainline:

```text
engineering_branch
```

Reason:

```text
This round repairs report generation, Required Audit prose coverage, and final-check validation for engineering auditability.
```

Skill profile:

```text
reverse-agent-iteration@v2
```

Previous accepted-with-limitations baseline:

```text
decision_20260708_user_solve_contract_test_coverage_rework_v1
round_20260708_user_solve_contract_test_coverage_rework_v1
ACCEPTED_WITH_LIMITATIONS
```

Evidence from the previous round:

```text
1. decision_meta was valid and APPROVED.
2. mainline was engineering_branch.
3. command_plan.json was PASSED and omitted_commands was empty.
4. command_plan.json included the explicit User Solve pytest command.
5. pytest_result.txt recorded the same pytest command.
6. pytest_result.txt showed 1219 passed and exit code 0.
7. codex_execution_report.md and execution_report.md tests_ran included the same User Solve pytest command.
8. final_gate_result.json PASSED and changed_tests_covered_by_pytest covered the User Solve tests.
9. execution_log.json recorded current decision_id, round_id, report_id, and command coverage.
10. run_closeout_result.json PASSED.
11. round_manifest.json was created for the previous round.
```

Remaining limitation from audit:

```text
The report body Required Audit section was not human-readable enough. The acceptance evidence relied mainly on structured JSON summaries, report-summary synthesis, and final-check.
```

Current state summary:

```text
project_state/current_state.json remains older reverse_solving / samplereverse context and is not current task authority.
project_state/task_packet.json remains older reverse_solving advisory context and is not current task authority.
project_state/artifact_index.json still contains many missing historical sample artifacts; these are non-blocking for this engineering_branch round unless claimed as current evidence.
```

Artifact freshness:

```text
Current acceptance must use this round's project_state/gates artifacts and this round's reports. Historical User Solve / Web / sample artifacts may be referenced only as historical non-blocking evidence.
```

Negative results:

```text
negative_results.json is mostly reverse_solving oriented. The global hard block against committing full solve_reports remains relevant.
```

Existing capabilities to reuse:

```text
command-plan authority
pytest_result parser
execution-log synthesis
report-summary synthesis
final-check
run-closeout
close-round
round_manifest archive
report/pytest semantic parity checks
required audit coverage checks
changed tests coverage checks
```

Tool and runtime policy:

```text
No off-scope analysis tools, sample execution, Web runtime, model API runner, queue, database, or runner dispatch is allowed.
```

Heavy artifact policy:

```text
Do not read full solve_reports/.
Do not read full PROJECT_PROGRESS_LOG.txt.
Only inspect targeted project_state, gate, report, source, and test files listed in this decision.
```

Closeout policy:

```text
closeout_allowed=true
closeout_required=true
close_round_required=true
```

Gate profile / command-plan strategy:

```text
Use generated command-plan as command authority.
The command-plan must include pytest, report-summary, execution-log, final-check, run-closeout, and close-round.
No omitted command may be executed.
```

Context packet / workstream registry:

```text
project_state/context/current_context_packet.json exists but is stale and must not be treated as current fact authority.
project_state/roadmap/workstreams.json exists and says roadmap entries are not execution authority.
This round must not update roadmap/workstreams.json.
```

Repeat check:

```text
This round does not reimplement prompt versioning, prompt consistency, policy-lint, report-summary, execution-log, command-plan, final-check, or run-closeout. It only tightens the existing report body and final-check validation for Required Audit prose coverage.
```

## 3. Do Not Do

Do not expand User Solve functionality.

Do not modify User Solve source files.

Do not implement solving or sample processing.

Do not implement Fast Static Solve.

Do not implement Evidence Trace or Evidence Replay.

Do not implement Web Workbench or frontend.

Do not implement tool provider integration.

Do not create or modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/context/*
project_state/roadmap/workstreams.json
project_state/domains/*
```

Do not modify:

```text
.codex-skills/*
.github/workflows/*
frontend/*
solve_reports/*
training_materials/local_reverse/*
project_state/archives/*
project_state/deletions/*
project_state/blob_store/*
project_state/*.db
project_state/index.sqlite
docs/roadmap/*
```

Do not add a database, queue, runner dispatcher, PR automation, cleanup-apply flow, archive compaction, deletion flow, or new workflow engine.

Do not claim ACCEPTED unless the report body `## Required Audit` section is substantive and covers every Required Audit item in this decision.

Do not rely only on JSON summary blocks for human audit coverage.

## 4. Files To Inspect

Required authority and state files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/roadmap/workstreams.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/round_manifest.json
```

Allowed source files to inspect or modify:

```text
reverse_agent/project_reports.py
reverse_agent/project_gate.py
reverse_agent/project_control_plane.py
```

Allowed test files to inspect or modify:

```text
tests/test_project_reports.py
tests/test_project_gate.py
tests/test_project_control_plane.py
```

Allowed generated state/report files:

```text
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260709_required_audit_report_body_rework_v1/*
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this round must answer all of the following in the human-readable `## Required Audit` body and the structured report summary must remain consistent with those answers:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline engineering_branch?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous accepted-with-limitations round correctly identified as decision_20260708_user_solve_contract_test_coverage_rework_v1?
7. Is the current limitation specifically the human-readable Required Audit report body?
8. Did the rework avoid modifying User Solve source files?
9. Did the rework avoid expanding User Solve functionality?
10. Did the rework avoid off-scope features and forbidden state mutations?
11. Does codex_execution_report.md contain a non-empty Required Audit body?
12. Does execution_report.md contain a non-empty Required Audit body?
13. Does the Required Audit body answer every item from this decision?
14. Does report-summary parse or validate the Required Audit body coverage?
15. Does final-check explicitly validate Required Audit body presence?
16. Does final-check explicitly validate Required Audit item coverage?
17. Does final-check fail or warn if the Required Audit body is empty while the report claims ACCEPTED?
18. Does the structured JSON summary remain present?
19. Does the structured JSON summary remain semantically aligned with the body?
20. Does pytest_result.txt record an explicit pytest command and exit code 0?
21. Does pytest include tests/test_project_reports.py?
22. Does pytest include tests/test_project_gate.py?
23. Does pytest include tests/test_project_control_plane.py when project_control_plane.py is changed?
24. Were any omitted or unauthorized commands executed?
25. Were project_state/current_state.json and task_packet.json left untouched?
26. Were artifact_index, negative_results, state_manifest, context, roadmap, domains, frontend, workflows, solve_reports, and training materials left untouched?
27. Did final-check pass or accurately reflect any limitations?
28. Did run-closeout pass?
29. Did close-round generate round_manifest for round_20260709_required_audit_report_body_rework_v1?
30. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, and generated_artifacts?
31. Does round_manifest status agree with live reports and final_gate status_summary?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Add or repair report generation so `codex_execution_report.md` and `execution_report.md` include a substantive `## Required Audit` section.
2. Ensure the Required Audit section is generated from the current decision's Required Audit items, not hard-coded stale text.
3. Ensure the Required Audit section records clear PASS / WARN / FAIL style answers or equivalent explicit prose.
4. Extend report-summary validation so it can detect empty or placeholder Required Audit bodies when a report claims SUCCESS / ACCEPTED.
5. Extend final-check so ACCEPTED reports cannot pass with an empty or placeholder Required Audit body.
6. Add tests proving empty Required Audit body is rejected for accepted reports.
7. Add tests proving a complete Required Audit body is accepted.
8. Preserve structured report summary blocks and semantic parity between codex_execution_report.md and execution_report.md.
9. Regenerate pytest_result, command_plan, report-summary, execution-log, final-check, run-closeout, close-round, execution reports, and round manifest for this rework round.
```

Allowed source files:

```text
reverse_agent/project_reports.py
reverse_agent/project_gate.py
reverse_agent/project_control_plane.py
```

Allowed test files:

```text
tests/test_project_reports.py
tests/test_project_gate.py
tests/test_project_control_plane.py
```

If implementation requires forbidden paths or off-scope capabilities, stop and report BLOCKED.

## 7. Tests

The exact command list must come from generated command-plan. It must include explicit pytest and the report/gate tests affected by this round.

Minimum pytest command:

```text
python -m pytest tests/test_project_reports.py tests/test_project_gate.py tests/test_project_control_plane.py -q
```

Allowed broader pytest command:

```text
python -m pytest tests/test_project_reports.py tests/test_project_gate.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py tests/test_user_solve_contract.py tests/test_user_solve_errors.py tests/test_user_solve_state.py tests/test_user_solve_views.py -q
```

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_reports.py tests/test_project_gate.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260709_required_audit_report_body_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260709_required_audit_report_body_rework_v1
```

Required output files:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260709_required_audit_report_body_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. fixing Required Audit body coverage requires forbidden path changes.
6. fixing Required Audit body coverage requires off-scope capabilities.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits report-summary, execution-log, final-check, run-closeout, or close-round.
4. codex_execution_report.md omits a substantive Required Audit body.
5. execution_report.md omits a substantive Required Audit body.
6. Required Audit body does not answer every current Required Audit item.
7. final-check does not catch empty or placeholder Required Audit body for accepted reports.
8. report-summary does not preserve semantic alignment between structured summary and prose body.
9. codex_execution_report.md and execution_report.md disagree.
10. final-check fails or reports unsupported acceptance status.
11. run-closeout or close-round fails.
12. round_manifest is missing.
13. any forbidden path is modified.
14. current_state.json or task_packet.json is modified.
15. roadmap, context, state_manifest, artifact_index, negative_results, domains, docs/roadmap, frontend, workflows, solve_reports, databases, archives, deletions, or training materials are modified.
```

Acceptance target:

```text
ACCEPTED if both reports include a substantive Required Audit body covering every item, structured summaries remain aligned, command-plan/pytest/final-check/run-closeout/round_manifest all pass for this decision_id and round_id, and no forbidden path or forbidden capability is used.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly non-blocking and do not affect Required Audit body coverage or report acceptance semantics.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
