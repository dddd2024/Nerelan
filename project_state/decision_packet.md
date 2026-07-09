```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260709_context_manifest_sync_closeout_artifact_rework_v1",
  "round_id": "round_20260709_context_manifest_sync_closeout_artifact_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260709_context_manifest_sync_v1",
  "follows_last_round_id": "round_20260709_context_manifest_sync_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "run_closeout_result_must_be_final": true,
  "run_closeout_execution_log_must_be_complete": true,
  "final_check_after_archive_required": true,
  "round_manifest_required": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py"
  ],
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/*"
  ],
  "read_only_current_artifacts": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/rounds/round_20260709_context_manifest_sync_v1/round_manifest.json"
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

Repair the current closeout artifact inconsistency from the previous context/manifest synchronization round.

Previous round:

```text
decision_id: decision_20260709_context_manifest_sync_v1
round_id: round_20260709_context_manifest_sync_v1
audit_outcome: REWORK_REQUIRED
```

The previous round completed the core context/manifest goals: `state_manifest.json` now has `scoped_metadata`, `current_context_packet.json` is current for the previous round, `post_final_evidence_sync_result.json` passed, and final-check reported zero stale context facts.

The blocking issue is not the context/manifest functionality. The blocking issue is closeout evidence inconsistency:

```text
project_state/gates/run_closeout_result.json still says closeout_status=IN_PROGRESS.
project_state/gates/run_closeout_execution_log.json only contains a partial closeout transcript.
pytest_result.txt, execution_log.json, and reports claim run-closeout PASSED and close-round CLOSED.
final_gate_result.json still contains close_round_in_progress traces.
```

This round must make the live closeout artifacts, execution log, final-check, reports, pytest_result, and round manifest agree on the same current round.

This is a project_governance closeout-artifact consistency rework only.

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

Reason:

```text
This round repairs governance closeout artifacts and final acceptance evidence. It does not perform reverse solving, user solve expansion, Web work, tool integration, cleanup, archive compaction, deletion, database, or CI workflow work.
```

Skill profile:

```text
reverse-agent-iteration@v2
```

Accepted sub-evidence from the previous round that should be preserved:

```text
1. current_context_packet.json was synchronized to decision_20260709_context_manifest_sync_v1.
2. state_manifest.json contains scoped_metadata.
3. final-check reported scoped_metadata_coverage=PASS.
4. final-check reported context_domain_awareness=PASS and stale_fact_count=0.
5. post_final_evidence_sync_result.json reported PASSED.
```

Blocking audit evidence:

```text
1. live project_state/gates/run_closeout_result.json has closeout_status=IN_PROGRESS.
2. live run_closeout_result.json has executed_steps=[] and close_round_result=null.
3. live project_state/gates/run_closeout_execution_log.json contains only started, decision-lint, and preflight command blocks.
4. pytest_result.txt claims run-closeout PASSED and close-round CLOSED.
5. execution_log.json claims run-closeout and close-round commands passed.
6. final_gate_result.json still contains close_round_in_progress / final_check_after_archive_passed=false / empty close_round_close_status traces.
7. round_manifest exists, but the live closeout artifact does not agree with the accepted/closed state claimed by reports.
```

Existing abilities to reuse:

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
closeout consistency checks
```

Do not implement these systems again. Reuse and repair the existing closeout path.

Artifact freshness:

```text
Current acceptance must use this rework round's live project_state/gates artifacts and reports. Historical sample artifacts and old User Solve/Web/gate artifacts may be referenced only as historical non-blocking context.
```

Context packet and state manifest policy:

```text
The previous context/manifest outputs are evidence to preserve. This round should not re-open domain taxonomy or state migration. If deterministic regeneration occurs as part of final-check, it must remain bounded to current project_governance metadata and must not modify forbidden source facts.
```

Workstream policy:

```text
project_state/roadmap/workstreams.json is not execution authority and must not be modified.
```

Closeout policy:

```text
closeout_allowed=true
closeout_required=true
close_round_required=true
```

Command policy:

```text
Use generated command-plan as command authority.
No omitted command may be executed.
```

Repeat check:

```text
This round does not repeat prompt versioning, prompt consistency, policy-lint, report-summary, execution-log, command-plan, run-closeout, or close-round as new features. It repairs the existing closeout artifact lifecycle so the live artifacts match the recorded transcript and reports.
```

## 3. Do Not Do

Do not expand User Solve functionality.

Do not modify User Solve source files.

Do not perform reverse_solving work.

Do not process samples.

Do not implement Web, frontend, workbench, trace replay, tool provider integration, database, queue, runner dispatcher, scheduler, CI workflow, cleanup-apply, deletion, archive compaction, or roadmap planning.

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

Do not claim ACCEPTED if live `run_closeout_result.json` is still `IN_PROGRESS`.

Do not claim ACCEPTED if `run_closeout_execution_log.json` remains partial.

Do not claim ACCEPTED if final-check still has active `close_round_in_progress` traces for the current rework round.

Do not hide closeout inconsistency by relying only on pytest transcript or report prose.

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
project_state/rounds/round_20260709_context_manifest_sync_v1/round_manifest.json
```

Allowed source files to inspect or modify:

```text
reverse_agent/project_gate.py
```

Allowed test files to inspect or modify:

```text
tests/test_project_gate.py
```

Allowed generated state/report files:

```text
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/*
```

Read-only current evidence:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/rounds/round_20260709_context_manifest_sync_v1/round_manifest.json
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this round must answer all of the following in the human-readable `## Required Audit` body, and the structured report summary must remain consistent with those answers:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous REWORK_REQUIRED round correctly identified as decision_20260709_context_manifest_sync_v1?
7. Is the current blocking issue specifically closeout artifact inconsistency, not context/manifest functionality?
8. Does live run_closeout_result.json initially show IN_PROGRESS or otherwise stale/partial closeout state?
9. Does live run_closeout_execution_log.json initially lack the full closeout step transcript?
10. Does the implementation avoid modifying User Solve files?
11. Does the implementation avoid reverse_solving, Web, tool provider, database, cleanup, deletion, archive compaction, workflow, and roadmap work?
12. Were current_state.json and task_packet.json left untouched?
13. Were artifact_index.json, negative_results.json, roadmap/workstreams.json, domains, frontend, workflows, solve_reports, training materials, archives, deletions, blob_store, and databases left untouched?
14. Does command_plan.json exist and pass for this rework round?
15. Does command_plan.json include run-closeout and close-round?
16. Were any omitted or unauthorized commands executed?
17. Does pytest_result.txt record an explicit pytest command and exit code 0?
18. Does pytest include tests/test_project_gate.py?
19. Does execution_log.json carry the current decision_id, round_id, and report_id?
20. Does execution_log.json record all command-plan required commands?
21. Does run_closeout_result.json end with closeout_status=PASSED for this rework round?
22. Does run_closeout_result.json contain executed_steps for the closeout pipeline?
23. Does run_closeout_result.json contain a close_round_result with close_status=CLOSED or equivalent current closed state?
24. Does run_closeout_execution_log.json contain the complete closeout transcript rather than only the initial start/preflight blocks?
25. Does final_gate_result.json pass for this rework round?
26. Does final_gate_result.json no longer contain active close_round_in_progress / final_check_after_archive_passed=false / empty close_round_close_status evidence for this rework round?
27. Does final-check after archive pass or otherwise accurately record closed archive status?
28. Does round_manifest exist for round_20260709_context_manifest_sync_closeout_artifact_rework_v1?
29. Does round_manifest agree with live reports and final_gate status_summary?
30. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, generated_artifacts, and closeout evidence?
31. Does the report body explicitly explain how the previous closeout inconsistency was resolved?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Repair or reuse run-closeout so project_state/gates/run_closeout_result.json is finalized to PASSED, not IN_PROGRESS.
2. Ensure run_closeout_result.json records executed_steps and close_round_result for the current rework round.
3. Ensure run_closeout_execution_log.json records the complete closeout transcript, not only the start/preflight portion.
4. Rerun or repair close-round so the current rework round has a round_manifest.
5. Regenerate final_gate_result.json so current closeout status is closed and no active close_round_in_progress traces remain.
6. Regenerate codex_execution_report.md, execution_report.md, pytest_result.txt, command_plan.json, execution_log.json, report_summary_synthesis.json, and gate artifacts for this rework round.
7. Add or adjust tests only for closeout artifact finalization and closeout transcript completeness.
```

Allowed source files:

```text
reverse_agent/project_gate.py
```

Allowed test files:

```text
tests/test_project_gate.py
```

If the existing code already supports the required behavior, prefer rerunning the correct commands and regenerating artifacts over source changes.

## 7. Tests

The exact command list must come from generated command-plan.

Minimum pytest command:

```text
python -m pytest tests/test_project_gate.py -q
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
python -m pytest tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260709_context_manifest_sync_closeout_artifact_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260709_context_manifest_sync_closeout_artifact_rework_v1
```

Required output files:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/rounds/round_20260709_context_manifest_sync_closeout_artifact_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. closeout artifact repair requires forbidden path changes.
6. closeout artifact repair requires off-scope capabilities such as database, queue, runner dispatch, Web, CI workflow mutation, cleanup, deletion, or archive compaction.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits run-closeout or close-round.
4. run_closeout_result.json is missing.
5. run_closeout_result.json is still IN_PROGRESS after the round.
6. run_closeout_result.json lacks executed_steps or close_round_result.
7. run_closeout_execution_log.json is still partial.
8. execution_log.json and pytest_result.txt disagree about run-closeout or close-round.
9. final_gate_result.json still has active close_round_in_progress traces.
10. final_check_after_archive_passed remains false for the current rework round.
11. close_round_close_status remains empty for the current rework round.
12. round_manifest is missing for round_20260709_context_manifest_sync_closeout_artifact_rework_v1.
13. report body Required Audit is missing or incomplete.
14. codex_execution_report.md and execution_report.md disagree.
15. any forbidden path is modified.
```

Acceptance target:

```text
ACCEPTED if live closeout artifacts, execution_log, pytest_result, reports, final_gate_result, and round_manifest all agree that this rework round is closed, archived, and passed.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly historical/non-blocking and not related to closeout artifact consistency.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
