```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260709_context_manifest_sync_v1",
  "round_id": "round_20260709_context_manifest_sync_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260709_required_audit_report_body_rework_v1",
  "follows_last_round_id": "round_20260709_required_audit_report_body_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "state_manifest_sync_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "allowed_source_files": [
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_context.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_context.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_gate.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260709_context_manifest_sync_v1/*"
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

Advance one project_governance round to synchronize the current governance context after the accepted report-body rework round.

Previous accepted baseline:

```text
decision_id: decision_20260709_required_audit_report_body_rework_v1
round_id: round_20260709_required_audit_report_body_rework_v1
audit_outcome: ACCEPTED
```

The previous round repaired the human-readable Required Audit body and was accepted. The next smallest useful governance step is to repair stale current-context evidence and surface scoped state metadata in the current manifest.

This round must:

```text
1. Refresh project_state/context/current_context_packet.json so it matches the current decision/round and does not report stale project_governance facts after post-final sync.
2. Regenerate project_state/state_manifest.json so the existing scoped_metadata section is present and reflects current state roles.
3. Ensure final-check and run-closeout prove that context synchronization and manifest scoped metadata are current for this round.
4. Keep roadmap/workstreams as non-authoritative context only; do not modify it.
```

This is a project_governance state synchronization round only. It must not expand solving, User Solve, Web, tool providers, CI workflows, databases, runners, cleanup, deletion, archive compaction, or roadmap planning.

## 2. Current Evidence

Current task authority is:

```text
project_state/decision_packet.md
```

`task_packet.json` remains background only. It is still an older reverse_solving / samplereverse advisory packet with `execution_scope=decision_packet_controls_current_round`; it must not control this round.

Current accepted evidence from the previous round:

```text
1. codex_execution_report.md status=SUCCESS and acceptance_recommendation=ACCEPTED.
2. execution_report.md semantically matches codex_execution_report.md.
3. pytest_result.txt records 1182 passed with exit code 0.
4. final_gate_result.json gate_status=PASSED.
5. run_closeout_result.json closeout_status=PASSED.
6. round_manifest exists for round_20260709_required_audit_report_body_rework_v1.
```

Remaining non-blocking warnings from final-check:

```text
1. scoped_metadata_coverage: Phase A scoped metadata foundation not yet surfaced in state_manifest or artifact_index.
2. context_domain_awareness: context packet contains stale facts for decision_id, round_id, and auditor_context.stale_context_detected.
```

Existing abilities that must be reused rather than reimplemented:

```text
project_context_builder.build_current_context_packet
project_context.build_context_domain_awareness
project_state_manifest.build_state_manifest
post_final_evidence_sync.build_post_final_evidence_sync_result
project_gate final-check
project_gate command-plan
project_gate report-summary
project_gate execution-log
project_gate run-closeout
project_gate close-round
```

The repository already contains a state manifest builder with scoped_metadata generation support. The current live state_manifest is missing or not surfacing that section for final-check. This round should repair generation, ordering, or validation around the existing mechanism; do not create a parallel manifest system.

Context packet evidence:

```text
project_state/context/current_context_packet.json exists but points to an older decision/round and marks stale_context_detected=true.
```

Workstream evidence:

```text
project_state/roadmap/workstreams.json exists and says decision_packet.md is execution authority while roadmap entries are not execution authority.
The project_state_domain_taxonomy workstream already exists, but it does not itself authorize execution.
```

Artifact freshness:

```text
project_state/artifact_index.json is still older reverse_solving/sample evidence with many missing sample artifacts. Those gaps are historical and non-blocking for this project_governance round unless claimed as current evidence.
```

Negative results:

```text
negative_results.json mainly constrains reverse_solving branches and includes a hard block against committing full solve_reports. This round does not repeat any of those branches.
```

Closeout policy:

```text
closeout_allowed=true
closeout_required=true
close_round_required=true
```

Gate profile / command-plan policy:

```text
Use generated command-plan as command authority.
No omitted command may be executed.
```

Repeat check:

```text
This round must not repeat prompt versioning, prompt consistency, policy-lint, report-summary, execution-log, command-plan, run-closeout, or close-round as new systems. It only synchronizes existing context/manifest artifacts and validates them through existing gates.
```

## 3. Do Not Do

Do not modify User Solve source files.

Do not expand User Solve behavior.

Do not perform reverse_solving work.

Do not process samples.

Do not implement Web or frontend work.

Do not add tool-provider integration.

Do not add a database, queue, dispatcher, scheduled runner, new workflow engine, cleanup-apply path, deletion path, or archive compaction path.

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

Do not treat generated context packet or state_manifest as replacements for the underlying project_state facts. They are indexes/summaries only.

Do not claim ACCEPTED if current_context_packet still reports stale facts for this decision/round.

Do not claim ACCEPTED if state_manifest still lacks scoped_metadata or final-check still reports scoped_metadata_coverage as an active warning caused by missing state_manifest scoped metadata.

## 4. Files To Inspect

Required state and authority files:

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
project_state/rounds/round_20260709_required_audit_report_body_rework_v1/round_manifest.json
```

Allowed source files to inspect or modify:

```text
reverse_agent/project_context_builder.py
reverse_agent/project_context.py
reverse_agent/project_state_manifest.py
reverse_agent/post_final_evidence_sync.py
reverse_agent/project_gate.py
```

Allowed tests to inspect or modify:

```text
tests/test_project_context.py
tests/test_project_state_manifest.py
tests/test_project_gate.py
```

Allowed generated state/report files:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260709_context_manifest_sync_v1/*
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer all items below in the human-readable `## Required Audit` body:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous accepted baseline correctly identified as decision_20260709_required_audit_report_body_rework_v1?
7. Does current_context_packet.json exist before this round and is it stale for the previous accepted baseline?
8. Does state_manifest.json exist before this round?
9. Does state_manifest generation preserve project_state files as fact sources rather than replacing them?
10. Did the round reuse project_context_builder, project_context, project_state_manifest, post_final_evidence_sync, and project_gate rather than creating a parallel system?
11. Does regenerated state_manifest.json contain scoped_metadata?
12. Does scoped_metadata include state_file_scope coverage for current governance artifacts?
13. Does scoped_metadata preserve historical reverse_solving files as historical/non-blocking rather than current blockers?
14. Does regenerated current_context_packet.json match decision_20260709_context_manifest_sync_v1 and round_20260709_context_manifest_sync_v1?
15. Does post-final sync prove the context packet is current after final_gate_result for this round?
16. Does context_domain_awareness report zero stale project_governance facts for the current decision/round after sync?
17. Does final-check pass or accurately report only non-blocking legacy warnings not caused by this round?
18. Does final-check stop reporting state_manifest scoped_metadata as missing?
19. Does pytest_result.txt record an explicit pytest command and exit code 0?
20. Does pytest include tests/test_project_context.py?
21. Does pytest include tests/test_project_state_manifest.py?
22. Does pytest include tests/test_project_gate.py?
23. Does command_plan.json exist, pass, and include required commands?
24. Were any omitted or unauthorized commands executed?
25. Were current_state.json and task_packet.json left untouched?
26. Were artifact_index.json, negative_results.json, roadmap/workstreams.json, domains, frontend, workflows, solve_reports, and training materials left untouched?
27. Did report-summary and execution-log pass or produce accepted diagnostic results?
28. Did run-closeout pass?
29. Did close-round generate round_manifest for round_20260709_context_manifest_sync_v1?
30. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, and generated_artifacts?
31. Does round_manifest status agree with live reports and final_gate status_summary?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Repair or reuse state_manifest generation so project_state/state_manifest.json includes scoped_metadata for this round.
2. Repair or reuse current context generation so project_state/context/current_context_packet.json is current for this round.
3. Ensure post_final_evidence_sync refreshes context after final_gate_result is current and records a sync result/snapshot.
4. Ensure context_domain_awareness sees no stale decision_id/round_id/stale_context_detected facts after sync.
5. Ensure final-check validates the above conditions without converting unrelated historical reverse_solving sample gaps into blockers.
6. Add or adjust tests only for context sync, state manifest scoped metadata, and final-check validation.
7. Regenerate reports, pytest_result, gate artifacts, and round archive for this round.
```

Allowed source files:

```text
reverse_agent/project_context_builder.py
reverse_agent/project_context.py
reverse_agent/project_state_manifest.py
reverse_agent/post_final_evidence_sync.py
reverse_agent/project_gate.py
```

Allowed test files:

```text
tests/test_project_context.py
tests/test_project_state_manifest.py
tests/test_project_gate.py
```

If the existing code already supports the required behavior, prefer regeneration and tests over unnecessary source changes.

## 7. Tests

The exact command list must come from generated command-plan.

Minimum pytest command:

```text
python -m pytest tests/test_project_context.py tests/test_project_state_manifest.py tests/test_project_gate.py -q
```

Allowed broader pytest command:

```text
python -m pytest tests/test_project_gate.py tests/test_project_context.py tests/test_project_state_manifest.py tests/test_project_reports.py tests/test_project_control_plane.py -q
```

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_context.py tests/test_project_state_manifest.py tests/test_project_gate.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260709_context_manifest_sync_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260709_context_manifest_sync_v1
```

Required output files:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/post_final_evidence_sync_result.json
project_state/gates/post_final_evidence_sync_snapshot.json
project_state/rounds/round_20260709_context_manifest_sync_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. context or manifest synchronization requires forbidden path changes.
6. context or manifest synchronization requires off-scope capabilities.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits report-summary, execution-log, final-check, run-closeout, or close-round.
4. state_manifest.json lacks scoped_metadata after the round.
5. current_context_packet.json does not match this decision_id and round_id after the round.
6. post_final_evidence_sync_result.json is missing or not current.
7. context_domain_awareness still reports stale project_governance facts for this decision/round after sync.
8. final-check still reports missing state_manifest scoped_metadata.
9. codex_execution_report.md and execution_report.md disagree.
10. Required Audit body is missing or incomplete.
11. run-closeout or close-round fails.
12. round_manifest is missing.
13. any forbidden path is modified.
14. current_state.json, task_packet.json, artifact_index.json, negative_results.json, roadmap/workstreams.json, domains, frontend, workflows, solve_reports, databases, archives, deletions, or training materials are modified.
```

Acceptance target:

```text
ACCEPTED if the current context packet is synchronized to this round, state_manifest contains scoped_metadata, final-check/run-closeout/round_manifest all pass for this decision_id and round_id, and no forbidden path is modified.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly historical/non-blocking and not caused by stale context or missing state_manifest scoped_metadata.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
