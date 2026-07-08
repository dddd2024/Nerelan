```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_state_domain_taxonomy_final_status_rework_v1",
  "round_id": "round_20260708_state_domain_taxonomy_final_status_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_state_domain_taxonomy_closeout_evidence_rework_v1",
  "follows_last_round_id": "round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "command_plan_must_include_explicit_pytest_command": true,
  "command_plan_must_not_omit_report_summary": true,
  "command_plan_must_not_omit_execution_log": true,
  "command_plan_must_not_omit_final_check": true,
  "command_plan_must_not_omit_run_closeout": true,
  "command_plan_must_not_omit_close_round": true,
  "final_check_must_pass_before_unqualified_acceptance": true,
  "final_gate_status_summary_must_match_reports": true,
  "run_closeout_close_round_status_must_match_reports": true,
  "round_manifest_status_must_match_reports": true,
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
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/pytest_result.txt"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "reverse_agent/project_context.py",
    "reverse_agent/project_state_manifest.py",
    "tests/test_project_context.py",
    "tests/test_project_state_manifest.py",
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

Repair the remaining final-status mismatch from the previous closeout evidence rework round.

Previous round:

```text
decision_id: decision_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
round_id: round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
audit_outcome: REWORK_REQUIRED
```

The previous rework fixed the explicit pytest coverage issue:

```text
1. command-plan now includes an explicit pytest command;
2. pytest_result.txt now includes the explicit pytest command;
3. pytest_result.txt records direct pytest output and 1167 passed;
4. report-summary synthesis is current and PASSED.
```

The only remaining blocker is final status consistency:

```text
1. codex_execution_report.md claims SUCCESS / ACCEPTED;
2. execution_report.md claims SUCCESS / ACCEPTED;
3. round_manifest.json claims SUCCESS / ACCEPTED;
4. final_gate_result.json still has gate_status = WARN;
5. final_gate_result.json status_summary still says report_status = PARTIAL and report_acceptance_recommendation = NEEDS_REVIEW;
6. run_closeout_result.json close_round_result still says report_status = PARTIAL.
```

This round must make the final status model truthful and consistent.

Acceptance is valid only if all final status sources agree. If WARN / PARTIAL / NEEDS_REVIEW remains active, the reports must not claim unqualified SUCCESS / ACCEPTED.

## 2. Current Evidence

Current task authority is:

```text
project_state/decision_packet.md
```

`task_packet.json` is background only and must not control this round.

Current mainline:

```text
project_governance
```

Skill profile:

```text
reverse-agent-iteration@v2
```

Previous failed round to repair:

```text
decision_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
```

Evidence already fixed in previous rework and should not be reopened unless needed for final status consistency:

```text
1. explicit pytest command exists in command-plan commands[];
2. pytest_result.txt includes explicit pytest command;
3. pytest_result.txt records direct pytest output and exit code 0;
4. command-plan, pytest_result, and report tests cover the explicit pytest command;
5. report-summary synthesis is current and PASSED.
```

Remaining failure evidence:

```text
1. final_gate_result.json gate_status remains WARN;
2. final_gate_result.json status_summary remains PARTIAL / NEEDS_REVIEW;
3. run_closeout_result.json close_round_result.report_status remains PARTIAL;
4. codex_execution_report.md and execution_report.md still claim SUCCESS / ACCEPTED;
5. round_manifest.json still records SUCCESS / ACCEPTED;
6. this violates the previous decision requirement that final_gate, run_closeout, reports, and round_manifest agree.
```

Existing capabilities to reuse:

```text
project_gate final-check
run-closeout
close-round
report-summary
execution-log
execution_report / codex_execution_report parity
round manifest archive
status policy checks
report status schema
command-plan authority
pytest_result parser
```

Do not create a new status system. Repair the existing final-check / run-closeout / close-round / report status path.

Artifact freshness policy:

```text
1. All current-round gate artifacts must match this decision_id and round_id.
2. Prior failed-round artifacts may be referenced only as failure evidence.
3. Stale historical artifacts must not be used to justify current ACCEPTED.
4. final_gate_result.status_summary is the canonical evidence for whether an unqualified ACCEPTED claim is supported.
```

This round must not expand project_state domain taxonomy, User Solve, Web, tools, runner, database, cleanup, or sample solving.

## 3. Do Not Do

Do not change domain taxonomy behavior.

Do not add or edit domain README skeletons.

Do not modify project_context or project_state_manifest unless the existing tests fail solely because of final status consistency. If that occurs, stop and report BLOCKED rather than silently broadening scope.

Do not implement User Solve Layer.

Do not implement Evidence Replay.

Do not implement Fast Static Solve.

Do not implement Web Workbench.

Do not implement Tool Provider contracts.

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

Do not perform:

```text
sample solving
candidate or flag generation
runtime probing
sample execution
dynamic debugging
IDA invocation
Ghidra invocation
OllyDbg invocation
x64dbg invocation
radare2 invocation
MCP invocation
Web runtime work
database migration
runner dispatch
workflow dispatch
cleanup apply
deletion
moving historical artifacts
archive compaction
local commit
local push
branch creation
PR creation
merge
rebase
```

Do not claim unqualified `SUCCESS / ACCEPTED` if any current-round final status source still says:

```text
WARN
PARTIAL
NEEDS_REVIEW
FAILED
REWORK_REQUIRED
```

If final status warnings are deliberately accepted as non-blocking, the reports must use `ACCEPTED_WITH_LIMITATIONS` and list the warnings explicitly.

## 4. Files To Inspect

Required authority files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/task_packet.json
project_state/current_state.json
```

Required failed-round evidence:

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/round_manifest.json
```

Required source/test inspection candidates:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Required current-round generated files after execution:

```text
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/round_manifest.json
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this round must answer all of the following:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous failed round correctly identified as decision_20260708_state_domain_taxonomy_closeout_evidence_rework_v1?
7. Does command-plan still include an explicit pytest command?
8. Does pytest_result.txt still include direct pytest output, exit code 0, and test count?
9. Does report-summary synthesis match execution_report and codex_execution_report?
10. Does execution-log cover all executed commands?
11. Does final_gate_result.json gate_status support the report status?
12. Does final_gate_result.json status_summary support the report status and acceptance recommendation?
13. Does run_closeout_result.json close_round_result.report_status match execution_report and codex_execution_report?
14. Does round_manifest.json report_status match execution_report and codex_execution_report?
15. If final_gate_result.json is WARN, do reports avoid unqualified SUCCESS / ACCEPTED?
16. If status_summary is PARTIAL / NEEDS_REVIEW, do reports avoid unqualified SUCCESS / ACCEPTED?
17. If close_round_result.report_status is PARTIAL, do reports avoid unqualified SUCCESS / ACCEPTED?
18. If all reports claim SUCCESS / ACCEPTED, is final_gate_result.json free of active WARN/PARTIAL/NEEDS_REVIEW status?
19. Are non-blocking historical warnings explicitly classified as historical/non-blocking?
20. Are current active warnings either resolved or reflected as ACCEPTED_WITH_LIMITATIONS / REWORK_REQUIRED?
21. Were current_state.json and task_packet.json left untouched?
22. Were artifact_index.json, negative_results.json, state_manifest.json, context/*, roadmap/workstreams.json, and domains/* left untouched?
23. Were User Solve, Evidence Replay, Web, tools, runner, database, cleanup, and sample solving avoided?
24. Were all generated artifacts current for this decision_id and round_id?
25. Are stale failed-round artifacts treated only as failure evidence, not current acceptance evidence?
26. Do codex_execution_report.md and execution_report.md agree on report_id, decision_id, round_id, status, acceptance_recommendation, files_changed, tests_ran, and generated_artifacts?
27. Does close-round generate the final-status rework round manifest?
28. Does round_manifest status agree with live reports and final_gate status_summary?
29. Does run-closeout avoid wrapping active WARN/PARTIAL/NEEDS_REVIEW into ACCEPTED?
30. Is the final recommendation one of ACCEPTED, ACCEPTED_WITH_LIMITATIONS, REWORK_REQUIRED, or BLOCKED, and is it supported by evidence?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Fix final_gate_result.status_summary generation so it cannot remain PARTIAL / NEEDS_REVIEW while reports claim SUCCESS / ACCEPTED.
2. Fix report status derivation so execution_report and codex_execution_report follow final_gate_result.status_summary.
3. Fix run-closeout so close_round_result.report_status cannot remain PARTIAL while the live reports and round manifest claim SUCCESS.
4. Fix close-round / round_manifest status derivation so round_manifest agrees with live reports and final_gate status_summary.
5. If warnings are truly non-blocking, express that as ACCEPTED_WITH_LIMITATIONS or a clearly supported ACCEPTED only when final_gate status_summary explicitly supports it.
6. Add tests for final_gate/report/run_closeout/round_manifest status consistency.
7. Regenerate current-round gate artifacts, reports, pytest_result, and round_manifest for this decision_id and round_id.
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

Do not modify project_context.py or project_state_manifest.py in this round.

Do not modify domain README files or roadmap files in this round.

## 7. Tests

The exact command list must come from generated command-plan. It must still include explicit pytest.

Minimum pytest command:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
```

If command-plan chooses the broader prior pytest command, that is allowed:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q
```

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260708_state_domain_taxonomy_final_status_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260708_state_domain_taxonomy_final_status_rework_v1
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
project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. final status consistency requires modifying forbidden paths.
6. final status consistency requires User Solve, Web, tools, runner, database, cleanup, or sample execution.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. report-summary and reports disagree.
4. final_gate_result.status_summary and reports disagree.
5. run_closeout_result.close_round_result and reports disagree.
6. round_manifest and reports disagree.
7. final_gate_result remains WARN while reports claim unqualified SUCCESS / ACCEPTED.
8. final_gate_result.status_summary remains PARTIAL / NEEDS_REVIEW while reports claim unqualified SUCCESS / ACCEPTED.
9. run_closeout_result.close_round_result.report_status remains PARTIAL while reports claim unqualified SUCCESS / ACCEPTED.
10. warnings are not resolved or explicitly reflected in ACCEPTED_WITH_LIMITATIONS / REWORK_REQUIRED.
11. codex_execution_report.md and execution_report.md disagree.
12. any forbidden path is modified.
13. current_state.json or task_packet.json is modified.
14. roadmap, context, state_manifest, artifact_index, negative_results, domains, docs, frontend, workflows, solve_reports, databases, or archives are modified.
15. sample solving, runtime probing, debugger/tool/MCP invocation, Web work, runner dispatch, cleanup apply, deletion, commit/push/PR/merge/rebase is performed.
```

Acceptance target:

```text
ACCEPTED only if final_gate_result, run_closeout_result, execution_report, codex_execution_report, report_summary_synthesis, pytest_result, command_plan, close-round, and round_manifest all agree for this decision_id and round_id.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly non-blocking and all status sources agree on the limitations-aware recommendation.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
