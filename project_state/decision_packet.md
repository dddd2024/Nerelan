```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260710_state_manifest_freshness_rework_v1",
  "round_id": "round_20260710_state_manifest_freshness_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260709_post_closeout_context_sync_v1",
  "follows_last_round_id": "round_20260709_post_closeout_context_sync_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "state_manifest_refresh_required": true,
  "state_manifest_current_artifact_digest_validation_required": true,
  "context_packet_sync_required": true,
  "post_final_evidence_sync_required": true,
  "required_audit_body_quality_required": true,
  "allowed_source_files": [
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_gate.py"
  ],
  "allowed_test_files": [
    "tests/test_project_state_manifest.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_project_state_files": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/*"
  ],
  "read_only_evidence_files": [
    "project_state/rounds/round_20260709_post_closeout_context_sync_v1/round_manifest.json",
    "docs/roadmap/trustworthy_hostile_binary_analysis_long_term_plan.md"
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

Advance one bounded `project_governance` rework round to repair the stale current-state index in:

```text
project_state/state_manifest.json
```

The previous round successfully synchronized `current_context_packet.json`, passed pytest and final-check, and closed its round. The subsequent audit found that `state_manifest.json` still represented an older decision and round and still contained old SHA-256 and size values for files classified as current.

This round must:

```text
1. Regenerate state_manifest.json for the current decision and round.
2. Make final-check validate state_manifest decision_id, round_id, report_id, and current artifact file metadata.
3. Detect stale SHA-256 or size values for manifest entries classified as current.
4. Refresh current_context_packet.json and post-final evidence after the new final gate.
5. Produce a concrete Required Audit body based on observed manifest values.
6. Run the full authorized governance closeout and archive this round.
```

The target is not merely to regenerate one JSON file. The target is to prevent a stale `state_manifest.json` from passing final-check while claiming that it indexes current state only.

## 2. Current Evidence

Current task authority:

```text
project_state/decision_packet.md
```

Current command authority:

```text
project_state/gates/command_plan.json
```

Current mainline:

```text
project_governance
```

`task_packet.json` remains background only. It is an older `samplereverse` advisory packet and must not control this round.

Previous round evidence:

```text
decision_id: decision_20260709_post_closeout_context_sync_v1
round_id: round_20260709_post_closeout_context_sync_v1
codex report status: SUCCESS
acceptance recommendation: ACCEPTED
pytest: 1186 passed, exit code 0
final_gate_result.json: PASSED
context_domain_awareness.stale_fact_count: 0
run_closeout_result.json: PASSED
close_round_result.close_status: CLOSED
```

Audit finding that controls this rework:

```text
state_manifest.json still reports:
  decision_id=decision_20260709_context_manifest_sync_v1
  round_id=round_20260709_context_manifest_sync_v1
  report_id=codex_report_20260709_context_manifest_sync_v1
  generated_at=2026-07-09T13:17:55Z
```

The same manifest declares:

```text
artifact_kind=governance_index
classification_policy.state_manifest_indexes_current_state_only=true
classification_policy.project_state_files_remain_audit_fact_sources=true
```

The manifest also contains stale SHA-256 and size values for entries classified as current, including the decision packet, reports, pytest result, command plan, final gate, execution log, and run-closeout result.

This is not the historical sample-artifact warning. It is stale metadata inside a current governance index.

Existing abilities that must be reused rather than reimplemented:

```text
reverse_agent.project_state_manifest.build_state_manifest
reverse_agent.project_state_manifest.validate_state_manifest
project_gate command-plan
project_gate execution-log
project_gate report-summary
project_gate final-check
project_gate run-closeout
project_gate close-round
post-final evidence sync
current context packet builder
round archive and round manifest
```

Existing limitation:

```text
validate_state_manifest currently checks schema, decision_id, round_id, artifact kind, authority policy, role buckets, and historical sample policy.
It does not prove that current artifact SHA-256 and size values match the live files.
The previous final-check therefore passed while state_manifest.json was stale.
```

Artifact freshness policy for this round:

```text
1. Live project_state files are the fact sources.
2. state_manifest.json is a derived governance index, not a replacement fact source.
3. Every manifest entry classified as current must match the corresponding live file.
4. Historical sample artifact gaps remain non-blocking and must not be confused with manifest freshness.
5. The uploaded hostile-binary trust roadmap is read-only long-term planning and is not execution authority.
```

Negative-results check:

```text
negative_results.json contains reverse_solving constraints such as avoiding old blind search, budget-only expansion, and repeated sample probes.
This round performs no reverse_solving work and must not modify or repeat those directions.
```

Capability permissions:

```text
local deterministic Python: allowed
unit tests: allowed
project gate commands: allowed
state/report JSON generation: allowed
external reverse tools: not allowed
model API invocation: not allowed
runner dispatch: not allowed
Web runtime: not allowed
remote workflow dispatch: not allowed
cleanup/deletion: not allowed
```

Repeat check:

```text
Do not implement another state manifest system, command-plan, execution-log, report-summary, final-check framework, or closeout framework.
Extend the existing manifest validator and existing final-check only as needed to enforce current-file freshness.
```

## 3. Do Not Do

Do not perform reverse-solving work or process samples.

Do not implement the hostile-binary Trust Layer, Binary Evidence Firewall, Claim Graph, Counterevidence Graph, Action Provenance Guard, Analysis Capsule, or Trust Workbench in this round.

Do not modify the uploaded long-term roadmap.

Do not modify roadmap workstreams or activate a new workstream.

Do not expand User Solve behavior or modify User Solve source files.

Do not implement or modify:

```text
Web or frontend
CI workflows
AgentRunner or runner dispatch
IDA/Ghidra/debugger integration
database or SQLite index
queue or scheduler
cleanup-apply
deletion or tombstones
archive compaction
sample solvers or harnesses
```

Do not modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/roadmap/workstreams.json
project_state/domains/*
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

Do not accept a manifest merely because its top-level decision and round IDs match. Current artifact SHA-256 and size metadata must also match live files.

Do not accept a report that answers the state-manifest audit item only by citing a policy sentence. The report must cite actual fields and observed values from the regenerated manifest and live files.

Do not claim `ACCEPTED` when any current manifest reference is stale, missing unexpectedly, or inconsistent with the current decision, report, tests, gates, or closeout artifacts.

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

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
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/post_final_evidence_sync_result.json
project_state/rounds/round_20260709_post_closeout_context_sync_v1/round_manifest.json
```

Allowed source files to inspect and modify:

```text
reverse_agent/project_state_manifest.py
reverse_agent/project_gate.py
```

Allowed test files to inspect and modify:

```text
tests/test_project_state_manifest.py
tests/test_project_gate.py
tests/test_project_reports.py
```

Allowed generated state and report files:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/*
```

Read-only planning evidence:

```text
docs/roadmap/trustworthy_hostile_binary_analysis_long_term_plan.md
```

## 5. Required Audit

The execution report must contain a human-readable `## Required Audit` body answering every item below. Each answer must cite a concrete artifact path and observed value. Placeholder wording and future-tense claims are forbidden.

```text
1. Is decision_meta valid JSON with schema_version=1?
2. Is decision status APPROVED and mainline project_governance?
3. Is reverse-agent-iteration@v2 active?
4. Is task_packet treated as background only?
5. Is the previous audited outcome correctly recorded as REWORK_REQUIRED?
6. Is this round limited to state-manifest freshness and its gate/report coverage?
7. What stale decision_id, round_id, report_id, generated_at, SHA-256, or size values were observed in the pre-rework state_manifest.json?
8. Does regenerated state_manifest.json match decision_20260710_state_manifest_freshness_rework_v1?
9. Does regenerated state_manifest.json match round_20260710_state_manifest_freshness_rework_v1?
10. Does regenerated state_manifest.json use the current report_id?
11. Does state_manifest.json remain artifact_kind=governance_index?
12. Does state_manifest.json continue to state that project_state files remain audit fact sources?
13. Does state_manifest.json avoid claiming that it replaces underlying fact sources?
14. Do current manifest references for decision_packet.md match the live SHA-256 and size?
15. Do current manifest references for codex_execution_report.md and execution_report.md match live SHA-256 and size values?
16. Does the current manifest reference for pytest_result.txt match the live SHA-256 and size?
17. Does the current manifest reference for command_plan.json match the live SHA-256 and size?
18. Does the current manifest reference for execution_log.json match the live SHA-256 and size?
19. Does the current manifest reference for final_gate_result.json match the live SHA-256 and size?
20. Does the current manifest reference for report_summary_synthesis.json match the live SHA-256 and size?
21. Does the current manifest reference for run_closeout_result.json match the live SHA-256 and size after closeout?
22. Does manifest validation reject a stale decision_id?
23. Does manifest validation reject a stale round_id?
24. Does manifest validation or final-check reject a stale current artifact SHA-256?
25. Does manifest validation or final-check reject a stale current artifact size?
26. Does final_gate_result.json include and pass the state-manifest freshness check?
27. Does final_gate_result.json pass for the current decision and round?
28. Does current_context_packet.json match the current decision and round after post-final sync?
29. Does post_final_evidence_sync_result.json report PASSED with context_generated_after_final_gate=true?
30. Does command_plan.json exist and pass with explicit pytest, report-summary, execution-log, final-check, run-closeout, and close-round coverage?
31. Were any omitted or unauthorized commands executed?
32. Does pytest_result.txt record the exact pytest command, exit code 0, and tests/test_project_state_manifest.py?
33. Do execution_log.json and pytest_result.txt agree on commands, exits, decision_id, and round_id?
34. Were current_state.json, task_packet.json, artifact_index.json, negative_results.json, roadmap/workstreams.json, domains, frontend, workflows, solve_reports, training materials, archives, deletions, blob_store, databases, and docs/roadmap left untouched?
35. Does run_closeout_result.json report PASSED and close_round_result CLOSED?
36. Does the new round_manifest exist and agree with live reports, pytest, decision, and closeout state?
37. Do execution_report.md and codex_execution_report.md agree on IDs, status, acceptance recommendation, tests, and generated artifacts?
38. Does the Required Audit body use actual observed manifest values rather than policy-only or template answers?
```

## 6. Implementation Scope

Allowed implementation work:

```text
1. Extend validate_state_manifest or an equivalent existing validation path to validate current artifact references against live files.
2. Validate at least path existence, SHA-256, and size for entries under artifact_roles.current.
3. Ensure decision_id, round_id, report_id, artifact_kind, and authority semantics remain validated.
4. Integrate the manifest freshness result into existing final-check output.
5. Give digest/size mismatches explicit check names and actionable details.
6. Preserve backward compatibility for historical and missing_optional entries.
7. Preserve the rule that state_manifest is an index and project_state files remain fact sources.
8. Add bounded tests for stale decision ID, stale round ID, stale SHA-256, stale size, missing current file, and valid current manifest.
9. Regenerate state_manifest.json only through the existing deterministic builder.
10. Regenerate context packet and post-final sync evidence after final-check.
11. Regenerate command-plan, execution-log, report-summary, pytest result, reports, final gate, closeout artifacts, and round archive for this round.
12. Write a concrete Required Audit body containing actual manifest values.
```

Permitted modified files:

```text
reverse_agent/project_state_manifest.py
reverse_agent/project_gate.py
tests/test_project_state_manifest.py
tests/test_project_gate.py
tests/test_project_reports.py
```

Permitted generated artifacts:

```text
project_state/state_manifest.json
project_state/context/current_context_packet.json
project_state/gates/*.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/*
```

Compatibility requirements:

```text
1. Do not rename existing state-manifest fields.
2. Do not remove legacy-compatible role buckets.
3. Do not make historical sample gaps blocking for project_governance.
4. Do not make missing_optional artifacts blocking.
5. Do not create a database or move state files.
6. Do not change command authority or task authority.
```

## 7. Tests

The exact executable command list must come from the generated command plan. `command_plan.omitted_commands` must not be executed.

Minimum pytest command:

```text
python -m pytest tests/test_project_state_manifest.py tests/test_project_gate.py tests/test_project_reports.py -q
```

A broader command is allowed only when generated by command-plan and kept within the current governance scope.

Required command coverage:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_state_manifest.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260710_state_manifest_freshness_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260710_state_manifest_freshness_rework_v1
```

Required behavioral tests:

```text
1. A valid current manifest passes.
2. A manifest with an old decision_id fails.
3. A manifest with an old round_id fails.
4. A manifest with an incorrect current artifact SHA-256 fails.
5. A manifest with an incorrect current artifact size fails.
6. A missing required current artifact fails.
7. A missing optional or historical artifact remains non-blocking.
8. final-check reports state-manifest freshness failure with an actionable detail.
9. final-check passes after deterministic manifest regeneration.
10. report tests reject policy-only Required Audit answers for manifest freshness.
```

Required outputs:

```text
project_state/state_manifest.json
project_state/gates/command_plan.json
project_state/gates/execution_log.json
project_state/gates/report_summary_synthesis.json
project_state/gates/final_gate_result.json
project_state/gates/post_final_evidence_sync_result.json
project_state/gates/post_final_evidence_sync_snapshot.json
project_state/gates/run_closeout_result.json
project_state/gates/run_closeout_execution_log.json
project_state/context/current_context_packet.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260710_state_manifest_freshness_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. the manifest builder cannot access current project_state files.
6. the repair requires modifying a forbidden path.
7. the repair requires Web, CI mutation, runner dispatch, database, cleanup, deletion, roadmap mutation, external reverse tools, or model API access.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan omits report-summary, execution-log, final-check, run-closeout, or close-round.
4. state_manifest.json does not match the current decision_id.
5. state_manifest.json does not match the current round_id.
6. state_manifest.json does not match the current report_id.
7. any artifact_roles.current SHA-256 differs from the live file.
8. any artifact_roles.current size differs from the live file.
9. a required current artifact is missing.
10. final-check does not validate state-manifest freshness.
11. final_gate_result.json does not pass.
12. current_context_packet.json is stale after post-final sync.
13. post_final_evidence_sync_result.json is missing or not PASSED.
14. the Required Audit body gives policy-only, generic, placeholder, or future-tense answers.
15. execution_report.md and codex_execution_report.md disagree.
16. run_closeout_result.json does not pass.
17. close_round_result is not CLOSED.
18. the new round_manifest is missing or inconsistent.
19. any forbidden path is modified.
20. any omitted or unauthorized command is executed.
```

Acceptance target:

```text
ACCEPTED only if state_manifest.json is regenerated for the current decision and round, every current artifact reference matches its live file, final-check enforces this invariant, pytest and execution evidence agree, context is post-final synchronized, reports are concrete and consistent, run-closeout passes, and the round closes with a matching manifest.

ACCEPTED_WITH_LIMITATIONS is allowed only for explicitly historical and non-blocking warnings unrelated to current state-manifest freshness, current report quality, command authorization, tests, or closeout.

Otherwise return REWORK_REQUIRED or BLOCKED.
```
