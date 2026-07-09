```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260709_post_closeout_context_sync_v1",
  "round_id": "round_20260709_post_closeout_context_sync_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260709_context_manifest_sync_closeout_artifact_rework_v1",
  "follows_last_round_id": "round_20260709_context_manifest_sync_closeout_artifact_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "context_domain_awareness_must_have_zero_stale_facts": true,
  "required_audit_body_quality_required": true,
  "required_audit_body_forbidden_patterns": [
    "The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.",
    "will pass",
    "will exist",
    "will no longer"
  ],
  "allowed_source_files": [
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_context.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_context.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_project_state_files": [
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260709_post_closeout_context_sync_v1/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/round_manifest.json",
    "project_state/gates/run_closeout_result.json"
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

Advance one bounded `project_governance` round to remove the remaining context freshness limitation after the accepted closeout-artifact rework round.

Previous round:

```text
decision_id: decision_20260709_context_manifest_sync_closeout_artifact_rework_v1
round_id: round_20260709_context_manifest_sync_closeout_artifact_rework_v1
audit_outcome: ACCEPTED_WITH_LIMITATIONS
```

The previous rework repaired the blocking closeout inconsistency:

```text
run_closeout_result.json closeout_status=PASSED
run_closeout_result.json close_round_result.close_status=CLOSED
run_closeout_execution_log.json contains a complete closeout transcript
final_check_after_archive_passed=true
round_manifest exists for round_20260709_context_manifest_sync_closeout_artifact_rework_v1
```

Remaining limitations to address now:

```text
1. final_gate_result.json reports context_domain_awareness stale_facts=2 because current_context_packet.json still points to decision_20260709_context_manifest_sync_v1 and round_20260709_context_manifest_sync_v1.
2. The previous report body covered all Required Audit items but used some generic/template answers and future-tense claims. This round must use concrete live-artifact evidence in the report body.
```

This round must refresh `project_state/context/current_context_packet.json` to the current decision/round, regenerate post-final sync evidence, rerun final-check so `context_domain_awareness.stale_fact_count=0`, and close the round with a clear non-template Required Audit body.

This is a context freshness and report-quality governance round only.

## 2. Current Evidence

Current task authority is:

```text
project_state/decision_packet.md
```

`task_packet.json` remains background only. It is still an old `samplereverse` advisory packet and must not control this round.

Current mainline:

```text
project_governance
```

Current accepted baseline:

```text
round_20260709_context_manifest_sync_closeout_artifact_rework_v1
```

Closeout evidence from the previous round:

```text
1. codex_execution_report.md status=SUCCESS and acceptance_recommendation=ACCEPTED.
2. pytest_result.txt records 1186 passed and exit code 0.
3. run_closeout_result.json is PASSED and includes executed_steps.
4. close_round_result.close_status=CLOSED.
5. final_gate_result.json gate_status=PASSED.
6. round_manifest exists and agrees with report_status=SUCCESS and acceptance_recommendation=ACCEPTED.
```

Known non-blocking limitations from the previous audit:

```text
1. context_domain_awareness stale_facts=2: context packet decision_id and round_id lag behind the closeout rework round.
2. status_policy_valid WARN due to historical/backlog sample artifacts; this is not a current blocker.
3. Required Audit prose was acceptable for closure but should be made more concrete and should not use placeholder or future-tense claims.
```

Existing abilities that must be reused rather than reimplemented:

```text
project_context_builder.build_current_context_packet
project_context.build_context_domain_awareness
post_final_evidence_sync.build_post_final_evidence_sync_result
project_gate command-plan
project_gate execution-log
project_gate report-summary
project_gate final-check
project_gate run-closeout
project_gate close-round
```

Workstream evidence:

```text
project_state/roadmap/workstreams.json exists, but it explicitly says decision_packet.md is execution authority and roadmap entries are not execution authority. Do not modify workstreams in this round.
```

Artifact freshness policy:

```text
Current acceptance must use live project_state artifacts for this round. Historical reverse_solving sample artifacts and old User Solve/Web artifacts remain non-blocking unless claimed as current evidence.
```

Repeat check:

```text
This round must not repeat command-plan, execution-log, report-summary, run-closeout, close-round, context builder, or post-final sync as new systems. It only refreshes current context evidence and proves it with existing gates.
```

## 3. Do Not Do

Do not perform reverse_solving work.

Do not process samples.

Do not expand User Solve behavior.

Do not modify User Solve source files.

Do not implement Web, frontend, workbench, trace replay, tool-provider integration, database, queue, runner dispatcher, scheduler, CI workflow, cleanup-apply, deletion, archive compaction, or roadmap planning.

Do not modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
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

Do not claim ACCEPTED if `context_domain_awareness.stale_fact_count` remains greater than 0 for this round.

Do not claim ACCEPTED if `current_context_packet.json` still reports the previous closeout rework decision or round after post-final sync.

Do not use generic Required Audit answers such as:

```text
The Required Audit item is satisfied per current-round evidence and required_audit_coverage validation.
```

Do not use future-tense claims such as `will pass`, `will exist`, or `will no longer` for artifacts that must already exist at report time.

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
project_state/gates/run_closeout_execution_log.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/post_final_evidence_sync_result.json
project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/round_manifest.json
```

Allowed source files to inspect or modify if needed:

```text
reverse_agent/project_context_builder.py
reverse_agent/project_context.py
reverse_agent/post_final_evidence_sync.py
reverse_agent/project_gate.py
```

Allowed tests to inspect or modify if needed:

```text
tests/test_project_context.py
tests/test_project_gate.py
tests/test_project_reports.py
```

Allowed generated state/report files:

```text
project_state/context/current_context_packet.json
project_state/state_manifest.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260709_post_closeout_context_sync_v1/*
```

Read-only accepted baseline evidence:

```text
project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/round_manifest.json
project_state/gates/run_closeout_result.json
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer all items below in the human-readable `## Required Audit` body. Each answer must cite a concrete current artifact path and observed value. Do not use placeholder/template wording and do not describe required artifacts in future tense.

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous baseline correctly identified as decision_20260709_context_manifest_sync_closeout_artifact_rework_v1 with audit outcome ACCEPTED_WITH_LIMITATIONS?
7. Did the previous closeout artifact rework remain accepted, with run_closeout_result.json PASSED and close_round_result CLOSED?
8. Is the current round limited to context freshness and report body quality?
9. Does current_context_packet.json initially point to the previous context sync round rather than the closeout rework round?
10. Does regenerated current_context_packet.json match decision_20260709_post_closeout_context_sync_v1 and round_20260709_post_closeout_context_sync_v1?
11. Does current_context_packet.json report final_gate_current=true after post-final sync?
12. Does current_context_packet.json report stale_context_detected=false after post-final sync?
13. Does post_final_evidence_sync_result.json exist for this round?
14. Does post_final_evidence_sync_result.json report sync_status=PASSED?
15. Does post_final_evidence_sync_result.json prove context_generated_after_final_gate=true or an equivalent digest/timestamp-current basis?
16. Does final_gate_result.json pass for this round?
17. Does final_gate_result.json report context_domain_awareness.stale_fact_count=0?
18. Does final_gate_result.json stop warning about stale decision_id and round_id in current_context_packet.json?
19. Does state_manifest.json remain a governance index and not replace underlying project_state fact sources?
20. Were current_state.json and task_packet.json left untouched?
21. Were artifact_index.json, negative_results.json, roadmap/workstreams.json, domains, frontend, workflows, solve_reports, training materials, archives, deletions, blob_store, and databases left untouched?
22. Does command_plan.json exist and pass for this round?
23. Does command_plan.json include required pytest, report-summary, execution-log, final-check, run-closeout, and close-round coverage?
24. Were any omitted or unauthorized commands executed?
25. Does pytest_result.txt record an explicit pytest command and exit code 0?
26. Does pytest include tests/test_project_context.py?
27. Does pytest include tests/test_project_gate.py?
28. Do execution_log.json and pytest_result.txt agree on command execution and current IDs?
29. Does run_closeout_result.json pass and close the current round?
30. Does round_manifest exist for round_20260709_post_closeout_context_sync_v1 and agree with live reports?
31. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, and generated_artifacts?
32. Does the Required Audit body avoid placeholder answers and future-tense claims?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Refresh project_state/context/current_context_packet.json so it matches decision_20260709_post_closeout_context_sync_v1 and round_20260709_post_closeout_context_sync_v1.
2. Regenerate project_state/gates/post_final_evidence_sync_result.json and post_final_evidence_sync_snapshot.json for this round.
3. Regenerate final_gate_result.json so context_domain_awareness has stale_fact_count=0.
4. Regenerate state_manifest.json only if needed to keep the governance index current with the refreshed context packet.
5. Regenerate command_plan.json, execution_log.json, report_summary_synthesis.json, pytest_result.txt, codex_execution_report.md, execution_report.md, run_closeout_result.json, run_closeout_execution_log.json, and round archive files for this round.
6. Adjust source/tests only if the existing context sync or final-check logic cannot prove the refreshed context state.
7. Write a concrete Required Audit body that gives observed artifact values, not placeholders or future-tense statements.
```

If existing code already supports the behavior, prefer artifact regeneration and tests over source changes.

## 7. Tests

The exact command list must come from generated command-plan.

Minimum pytest command:

```text
python -m pytest tests/test_project_context.py tests/test_project_gate.py tests/test_project_reports.py -q
```

Allowed broader pytest command:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q
```

Required command coverage:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_context.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260709_post_closeout_context_sync_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260709_post_closeout_context_sync_v1
```

Required output files:

```text
project_state/context/current_context_packet.json
project_state/gates/post_final_evidence_sync_result.json
project_state/gates/post_final_evidence_sync_snapshot.json
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260709_post_closeout_context_sync_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. context sync requires modifying forbidden paths.
6. context sync requires off-scope capabilities such as database, queue, runner dispatch, Web, CI workflow mutation, cleanup, deletion, archive compaction, or roadmap mutation.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits report-summary, execution-log, final-check, run-closeout, or close-round.
4. current_context_packet.json still points to decision_20260709_context_manifest_sync_v1 after sync.
5. current_context_packet.json still points to round_20260709_context_manifest_sync_v1 after sync.
6. current_context_packet.json does not match decision_20260709_post_closeout_context_sync_v1 and round_20260709_post_closeout_context_sync_v1.
7. post_final_evidence_sync_result.json is missing or not PASSED.
8. final_gate_result.json does not pass.
9. context_domain_awareness.stale_fact_count is greater than 0.
10. final_gate_result.json still warns about stale decision_id or stale round_id for the current context packet.
11. Required Audit body is missing, generic, placeholder-like, or uses future-tense claims for completed artifacts.
12. codex_execution_report.md and execution_report.md disagree.
13. run_closeout_result.json does not pass.
14. round_manifest is missing for round_20260709_post_closeout_context_sync_v1.
15. any forbidden path is modified.
```

Acceptance target:

```text
ACCEPTED if context packet, post-final sync, final-check, pytest, reports, execution-log, run-closeout, and round_manifest all agree on round_20260709_post_closeout_context_sync_v1, and context_domain_awareness stale_fact_count=0.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly historical/non-blocking and unrelated to current context freshness or Required Audit body quality.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
