```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_state_domain_taxonomy_foundation_v1",
  "round_id": "round_20260708_state_domain_taxonomy_foundation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_profile_contract_closeout_consistency_rework_v1",
  "follows_last_round_id": "round_20260708_profile_contract_closeout_consistency_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "command_plan_must_not_omit_pytest": true,
  "command_plan_must_not_omit_final_check": true,
  "command_plan_must_not_omit_run_closeout": true,
  "command_plan_must_not_omit_close_round": true,
  "final_check_must_pass_before_acceptance": true,
  "run_closeout_must_pass_before_acceptance": true,
  "round_archive_required_before_acceptance": true,
  "allowed_source_files": [
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_control_plane.py"
  ],
  "allowed_test_files": [
    "tests/test_project_state_manifest.py",
    "tests/test_project_context.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/context/current_context_packet.json",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*/README.md",
    "project_state/gates/*.json",
    "project_state/rounds/*/round_manifest.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md"
  ],
  "allowed_docs": [
    "docs/roadmap/project_state_domain_taxonomy_supplement.md",
    "docs/roadmap/evidence_centered_user_solve_execution_plan.md"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/domains/*/current_state.json",
    "project_state/domains/*/negative_results.json",
    "project_state/domains/*/solve_tasks/*",
    "project_state/domains/*/reports/*",
    "project_state/domains/*/traces/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement the first larger platform step from the roadmap: **Project State Domain Taxonomy Foundation**.

This round must make `project_state/` safer for the next stages of User Solve, Evidence Replay, Web Workbench, Tool Integration, and Automation Runner by adding compatibility-first state ownership metadata and domain skeletons.

The target is not another tiny closeout-only repair. The target is a bounded project-governance foundation round that prepares the state layer for the evidence-centered user solve platform.

This round must establish:

```text
1. state files can declare role / scope / domain / mainline / freshness;
2. artifacts can declare scope / domain / mainline / freshness;
3. negative results can distinguish global policy blocks from domain-specific failures;
4. context packet generation can identify stale domain facts instead of treating them as current global evidence;
5. domain skeleton README files exist for future state placement;
6. final-check reports missing legacy scope metadata as warnings first, not immediate hard failures;
7. the current governance closeout path still passes preflight, pytest, report-summary, execution-log, final-check, run-closeout, and close-round.
```

This round is a foundation round only. It must not migrate live reverse-solving state, must not run samples, and must not implement User Solve, Web, tools, database, or runner automation.

## 2. Current Evidence

Current task authority is this file:

```text
project_state/decision_packet.md
```

`task_packet.json` remains advisory/background only. It must not control this round.

Current mainline:

```text
project_governance
```

Reason for selecting this mainline:

```text
The next product direction requires clean state ownership before User Solve, Evidence Replay, Web, and Tool Integration can safely consume project_state. This is a governance/state taxonomy round, not a solver or Web round.
```

Previous accepted baseline:

```text
Previous decision: decision_20260708_profile_contract_closeout_consistency_rework_v1
Previous round: round_20260708_profile_contract_closeout_consistency_rework_v1
Audit outcome: ACCEPTED_WITH_LIMITATIONS
```

Previous audit limitations that this round should address or reduce:

```text
1. state_manifest freshness was not strong enough to use as current acceptance evidence;
2. report/gate prose had minor expected-exit wording drift;
3. pytest coverage wording and decision examples were not perfectly aligned.
```

This round should not reopen the previous closeout implementation unless needed to support the new state taxonomy checks.

Existing capabilities to reuse:

```text
decision-packet authority
command-plan authority
project_gate
preflight
gate-profile
command-plan
execution-log
report-summary
final-check
run-closeout
close-round
round manifest archive
state_manifest
artifact_index
negative_results
context packet
workstream registry
policy-lint and prompt-consistency foundations
job lifecycle and runner contract foundations
```

Do not create parallel systems for any of the above.

Artifact freshness policy:

```text
1. Current-round gate artifacts must match this decision_id and round_id after regeneration.
2. Historical sample artifacts must not support current project_governance acceptance.
3. Stale or missing reverse_solving artifacts are non-blocking for this governance round unless a generated gate explicitly makes them current evidence.
4. New metadata added in this round must preserve backward compatibility for legacy records.
```

Negative results:

```text
project_state/negative_results.json contains reverse-solving failures and global hard blocks. This round may add classification metadata but must not delete old entries or weaken hard blocks. It must not repeat prohibited solve_reports behavior.
```

Context packet and workstream registry:

```text
They exist as planner/auditor inputs but are not execution authority. This round may update them only to record or consume domain taxonomy metadata. They must not mark unrelated directions as ACTIVE_ROUND.
```

Existing roadmap basis:

```text
docs/roadmap/evidence_centered_user_solve_execution_plan.md describes the larger sequence:
Project State Domain Taxonomy -> User Solve Contract -> Evidence Trace Schema -> Fast Static Solve Wrapper -> Web Read Model -> Tool Provider Contract.
```

This round implements only the first item in that sequence.

This round must avoid repeating existing functionality. It should extend the existing state/gate/report path with scoped metadata and checks, not create a new planner, new gate engine, new artifact index, new database, or new runner.

## 3. Do Not Do

Do not implement User Solve Layer in this round.

Do not implement Evidence Replay schemas in this round, except for references in documentation or future-facing domain README text.

Do not implement Fast Static Solve in this round.

Do not implement Web Workbench in this round.

Do not implement Tool Provider contracts in this round.

Do not create or modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/domains/*/current_state.json
project_state/domains/*/negative_results.json
project_state/domains/*/solve_tasks/*
project_state/domains/*/reports/*
project_state/domains/*/traces/*
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

Do not convert roadmap entries into execution authority. Only `project_state/decision_packet.md` controls this round.

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
pytest_result matches report and command-plan
command-plan did not omit pytest/final-check/run-closeout/close-round
no forbidden path was modified
```

## 4. Files To Inspect

Required authority and registry files:

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
```

Required previous execution files:

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/gate_profile_plan.json
project_state/gates/preflight_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
```

Required source/test inspection candidates:

```text
reverse_agent/project_state_manifest.py
reverse_agent/project_context.py
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
tests/test_project_state_manifest.py
tests/test_project_context.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Required roadmap/docs inspection candidates:

```text
docs/roadmap/evidence_centered_user_solve_execution_plan.md
docs/roadmap/reverse_agent_larger_step_plan.md
docs/roadmap/project_state_domain_taxonomy_supplement.md
```

Optional only if directly needed:

```text
project_state/rounds/round_20260708_profile_contract_closeout_consistency_rework_v1/round_manifest.json
project_state/rounds/*/round_manifest.json
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this round must answer all of the following:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active in .codex-skills/registry.json?
5. Is task_packet.json treated as advisory/background only?
6. Does command-plan select standard/full profile rather than a fast profile that omits required gates?
7. Does command-plan include pytest?
8. Does command-plan include final-check?
9. Does command-plan include run-closeout?
10. Does command-plan include close-round?
11. Were any omitted commands executed?
12. Were any commands executed outside command-plan authority?
13. Did pytest run and pass?
14. Does pytest_result.txt match the executed pytest command and report summary?
15. Did the round add or validate role/scope/domain/freshness metadata without breaking legacy records?
16. Did the round classify negative_results without deleting old entries or weakening hard blocks?
17. Did the round update or validate artifact_index scope metadata without claiming stale artifacts as current evidence?
18. Did the round update or validate state_manifest scope metadata without treating stale manifests as current acceptance evidence?
19. Did the round create only allowed domain README skeletons under project_state/domains/*?
20. Did the round avoid modifying project_state/current_state.json and project_state/task_packet.json?
21. Did the round avoid creating domain current_state/negative_results runtime payloads?
22. Did the round avoid User Solve, Evidence Replay implementation, Web runtime, tools, runner, database, cleanup, and sample solving?
23. Did report-summary pass?
24. Did execution-log exist and cover the executed commands?
25. Did final-check pass?
26. Did run-closeout pass?
27. Did close-round generate a round_manifest for this round?
28. Do codex_execution_report.md and execution_report.md agree on decision_id, round_id, report status, tests_ran, and acceptance recommendation?
29. Are generated artifacts indexed or explicitly explained if not indexed?
30. Does the report avoid claiming roadmap entries as execution authority?
```

## 6. Implementation Scope

This round may implement a compatibility-first state domain taxonomy foundation.

Allowed implementation tasks:

```text
1. Add helper structures or functions for state roles, scopes, domains, mainlines, and freshness.
2. Add or extend state_manifest validation so records can include role/scope/domain/mainline/freshness while legacy records remain readable.
3. Add or extend artifact_index validation so artifact records can include scope/domain/mainline/freshness while legacy records remain readable.
4. Add or extend negative_results validation/classification so entries can be global_policy or domain-specific while legacy entries remain readable.
5. Add context packet awareness for domain metadata and stale-domain warnings.
6. Add final-check warnings for missing legacy scope metadata.
7. Add final-check hard checks only for new current-round records generated by this round, not for all historical legacy records.
8. Add project_state/domains/*/README.md skeletons for future state placement.
9. Add or update roadmap/workstream metadata only to keep this project_governance workstream non-authoritative and consistent.
10. Add tests for backward compatibility, metadata parsing, classification, warnings, and final-check behavior.
11. Update docs only within allowed roadmap documents if needed.
```

Allowed domain README skeletons:

```text
project_state/domains/reverse_solving/README.md
project_state/domains/project_governance/README.md
project_state/domains/user_solve_layer/README.md
project_state/domains/evidence_replay/README.md
project_state/domains/web_workbench/README.md
project_state/domains/tool_integration/README.md
project_state/domains/automation_runner/README.md
project_state/domains/training_dataset/README.md
project_state/domains/engineering_branch/README.md
```

Compatibility requirements:

```text
1. Existing readers of state_manifest/artifact_index/negative_results must not fail on legacy records.
2. Missing metadata on old records should be warning-level unless current-round generated artifacts require it.
3. No existing current_state payload may be migrated or moved.
4. No historical artifact may be deleted or compacted.
5. No new database may be introduced.
```

Implementation must remain small enough to audit. If a necessary change would require Web, solver, tool invocation, cleanup, migration, or runner dispatch, stop and report `BLOCKED` or leave it for a future decision.

## 7. Tests

The exact command list must come from generated command-plan. The command-plan must not omit pytest, final-check, run-closeout, or close-round.

Recommended minimum tests:

```text
python -m pytest tests/test_project_state_manifest.py tests/test_project_context.py tests/test_project_gate.py -q
```

If files in `project_reports.py` or `project_control_plane.py` are changed, include their tests:

```text
python -m pytest tests/test_project_reports.py tests/test_project_control_plane.py -q
```

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight
python -m reverse_agent.project_gate gate-profile
python -m reverse_agent.project_gate command-plan
python -m reverse_agent.project_gate command-plan --json
python -m reverse_agent.project_gate report-summary
python -m reverse_agent.project_gate execution-log
python -m reverse_agent.project_gate final-check
python -m reverse_agent.project_gate run-closeout
python -m reverse_agent.project_gate close-round
```

The execution must write/update:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_state_domain_taxonomy_foundation_v1/round_manifest.json
```

If generated command-plan uses different but equivalent test commands, the report must explain why those commands are equivalent and must record exact commands and exit codes.

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. command-plan omits pytest, final-check, run-closeout, or close-round.
6. command-plan requires forbidden commands or paths.
7. implementation requires modifying .codex-skills, workflows, frontend, solve_reports, current_state, task_packet, databases, archives, deletions, or blob_store.
8. implementation requires sample execution, runtime probing, debugger/tool/MCP invocation, Web runtime work, cleanup apply, or runner dispatch.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. pytest_result.txt does not match the executed pytest command.
3. report-summary fails and is not explicitly accepted by command-plan policy.
4. execution-log is missing or does not cover executed commands.
5. final-check fails.
6. run-closeout fails.
7. close-round fails or no round_manifest is generated.
8. codex_execution_report.md and execution_report.md disagree.
9. any forbidden path is modified.
10. project_state/current_state.json or project_state/task_packet.json is modified.
11. domain current_state/negative_results runtime payloads are created in this round.
12. old negative_results hard blocks are deleted or weakened.
13. stale artifacts are claimed as current evidence.
14. roadmap/workstream entries are treated as execution authority.
15. the report claims User Solve, Evidence Replay, Web, Tool Integration, runner, database, cleanup, or sample solving was implemented.
16. the round repeats existing functionality by creating a parallel gate, report, artifact index, state manifest, or runner system.
```

Acceptance target:

```text
ACCEPTED or ACCEPTED_WITH_LIMITATIONS only after all required gates, reports, pytest records, command-plan records, execution-log records, final-check, run-closeout, and close-round evidence are current for this decision_id and round_id.
```
