```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_governance_operations_bundle_big_step_v1",
  "round_id": "round_20260705_governance_operations_bundle_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260705_status_policy_final_acceptance_rework_v1",
  "follows_last_accepted_round_id": "round_20260705_status_policy_final_acceptance_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "supersedes_unexecuted_decision_id": "decision_20260705_cleanup_apply_review_bundle_v1",
  "phase_label": "phase_2_44_governance_operations_bundle_big_step_v1",
  "primary_goal": "Deliver a larger project_governance operations bundle in one round: cleanup-apply human review/readiness package, round compaction dry-run, archive/index refresh, SQLite read-index readiness schema, state-hygiene dashboard feed, lifecycle transition guard, and consolidated governance operations gate. This is still non-destructive: no cleanup-apply execution, deletion, move, archive compaction, real tombstone, real deletion manifest, database migration, Web runtime, runner dispatch, CI dispatch, model API, external reverse tool, or concrete sample processing is allowed.",
  "command_plan_authority_required": true,
  "accepted_requires_cleanup_apply_review_bundle": true,
  "accepted_requires_round_compaction_dry_run": true,
  "accepted_requires_archive_index_refresh": true,
  "accepted_requires_sqlite_read_index_schema": true,
  "accepted_requires_state_hygiene_dashboard_feed": true,
  "accepted_requires_lifecycle_transition_guard": true,
  "accepted_requires_governance_operations_gate": true,
  "accepted_requires_status_policy_clean_acceptance_preserved": true,
  "accepted_requires_no_real_cleanup_apply": true,
  "accepted_requires_no_destructive_mutation": true,
  "allowed_source_files": [
    "reverse_agent/cleanup_apply_safety.py",
    "reverse_agent/state_governance.py",
    "reverse_agent/state_hygiene.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/state_index_readiness.py",
    "reverse_agent/round_compaction.py",
    "tests/test_cleanup_apply_safety.py",
    "tests/test_state_governance.py",
    "tests/test_state_hygiene.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py",
    "tests/test_state_index_readiness.py",
    "tests/test_round_compaction.py"
  ],
  "allowed_documentation_files": [
    "docs/governance_operations_bundle.md",
    "docs/cleanup_apply_review_bundle.md",
    "docs/round_compaction.md",
    "docs/state_index_readiness.md",
    "docs/state_hygiene_dashboard_feed.md",
    "docs/state_hygiene_retention_policy.md",
    "docs/archive_index.md",
    "docs/deletion_manifest_and_tombstone.md",
    "docs/state_manifest.md",
    "docs/workstream_registry.md"
  ],
  "allowed_config_files": [
    "project_state/retention_policy.json",
    "project_state/state_lifecycle_registry.json"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/retention_policy.json",
    "project_state/state_lifecycle_registry.json",
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/roadmap/workstreams.json",
    "project_state/gates/governance_operations_bundle_result.json",
    "project_state/gates/governance_operations_bundle_snapshot.json",
    "project_state/gates/cleanup_apply_review_bundle.json",
    "project_state/gates/cleanup_apply_review_result.json",
    "project_state/gates/cleanup_apply_review_snapshot.json",
    "project_state/gates/cleanup_candidate_risk_matrix.json",
    "project_state/gates/cleanup_apply_approval_checklist.json",
    "project_state/gates/evidence_lock_manifest.json",
    "project_state/gates/deletion_manifest_dry_run.json",
    "project_state/gates/tombstone_plan_dry_run.json",
    "project_state/gates/round_compaction_plan.json",
    "project_state/gates/round_compaction_dry_run.json",
    "project_state/gates/round_compaction_manifest_dry_run.json",
    "project_state/gates/archive_index.json",
    "project_state/gates/archive_index_summary.json",
    "project_state/gates/state_index_readiness_schema.json",
    "project_state/gates/state_index_readiness_plan.json",
    "project_state/gates/state_index_readiness_result.json",
    "project_state/gates/state_hygiene_dashboard_feed.json",
    "project_state/gates/state_hygiene_dashboard_summary.json",
    "project_state/gates/lifecycle_transition_guard_result.json",
    "project_state/gates/status_policy_reconcile_result.json",
    "project_state/gates/doctor_backlog_split_result.json",
    "project_state/gates/cleanup_plan.json",
    "project_state/gates/cleanup_plan_summary.json",
    "project_state/gates/deletion_manifest_schema.json",
    "project_state/gates/tombstone_schema.json",
    "project_state/gates/rollback_rehearsal_plan.json",
    "project_state/gates/audit_handoff_for_cleanup_apply.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260705_governance_operations_bundle_big_step_v1/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/user_sessions/*",
    "frontend/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/index.sqlite",
    "project_state/*.db"
  ],
  "forbidden_capabilities_this_round": [
    "real_cleanup_apply",
    "cleanup_apply_execute",
    "file_delete",
    "file_move",
    "archive_compaction_apply",
    "archive_apply",
    "real_tombstone_write",
    "real_deletion_manifest_write",
    "sqlite_database_creation",
    "database_migration",
    "web_runtime",
    "production_http_service",
    "scheduler_or_service",
    "database_or_queue",
    "real_sample_analysis_execution",
    "real_user_upload_ingestion",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "model_api_invocation",
    "github_workflow_modification",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Governance Operations Bundle Big Step v1**.

The previous accepted round fixed status-policy/final-acceptance semantics. This next round should be larger than a single cleanup review artifact. It should consolidate the state-governance work into a practical operations bundle that prepares the project for later Web/orchestrator/query workflows without crossing into destructive cleanup, live database migration, runner dispatch, CI dispatch, Web runtime, or sample solving.

This round has six bundled deliverables under one `project_governance` mainline:

1. **Cleanup-apply review/readiness bundle**
   - Build a human review package from existing retention policy, cleanup plan, archive index, deletion/tombstone schema, dry-run safety, and audit handoff artifacts.
   - Produce risk matrix, approval checklist, evidence lock manifest, dry-run deletion manifest, dry-run tombstone plan, and audit/rollback handoff.

2. **Round compaction dry-run**
   - Design and generate a dry-run compaction plan for historical governance rounds.
   - No archive writing, no file movement, no deletion, no compaction apply.
   - Output what would be retained, summarized, referenced, or left untouched in a future compaction decision.

3. **Archive/index refresh**
   - Refresh bounded archive index and summary so current/historical/backlog artifacts can be surfaced without recursive full history scans.
   - Do not mutate `project_state/archives/*`.

4. **SQLite read-index readiness schema**
   - Define schema/plan for a future SQLite read index over decisions, rounds, artifacts, executions, audits, and workstreams.
   - Do not create a database file, run migrations, or replace project_state as the fact source.

5. **State-hygiene dashboard feed**
   - Generate a bounded JSON feed usable by a future Web dashboard: current round, active decision, latest report, final-check, backlog notices, cleanup readiness, compaction readiness, and index readiness.
   - This is a static artifact, not a Web server.

6. **Lifecycle transition guard**
   - Add/extend a gate that verifies only one active workstream, real cleanup-apply remains deferred, future destructive work requires a separate decision, and current status-policy clean acceptance remains preserved.

Accepted target:

- `final_gate_result.json.gate_status` remains `PASSED`.
- `status_summary.report_acceptance_recommendation` remains `ACCEPTED`.
- Historical sample backlog remains visible but nonblocking.
- Cleanup review, compaction dry-run, SQLite readiness, dashboard feed, and lifecycle guard are all current and internally consistent.
- No destructive action occurs.
- No database file is created.
- No Web runtime, runner dispatch, CI dispatch, model API, external reverse tool, or real sample processing occurs.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` is background only.

Accepted baseline:

- `decision_20260705_status_policy_final_acceptance_rework_v1`
- `round_20260705_status_policy_final_acceptance_rework_v1`
- audit outcome: `ACCEPTED`

Baseline facts:

- final-check was clean: `PASSED`.
- report acceptance was clean: `ACCEPTED`.
- `doctor_status=FAIL` from historical sample backlog was preserved as external/backlog notice, not a current governance limitation.
- `status_policy_valid.limitations` was null while `50 missing, 0 stale artifacts` remained visible as historical backlog.
- cleanup-apply safety artifacts already exist and were historical/nonblocking in the accepted rework; they should be reused or refreshed only as review/dry-run evidence, not reimplemented from scratch.

Existing capabilities that must not be duplicated:

- command-plan;
- execution-log;
- report-summary synthesis;
- final-check;
- run-closeout;
- state manifest;
- context packet;
- workstream registry;
- retention policy;
- cleanup plan;
- archive index;
- deletion manifest schema;
- tombstone schema;
- cleanup-apply dry-run safety;
- status-policy reconciliation;
- doctor/backlog split.

Why this is the right larger step:

- A narrow cleanup review bundle is useful but too small.
- The broader governance operations bundle prepares the next architecture layer: Web display, bounded state queries, future compaction, and future cleanup-apply audit readiness.
- It still respects the project rule that new directions enter roadmap/workstreams and that project_state remains the audit fact source.

Negative results still apply:

- no old sample-solver blind search;
- no beam/topN/budget expansion;
- no stale runtime diagnostics;
- no full `solve_reports` scan;
- no full `PROJECT_PROGRESS_LOG.txt` scan;
- no concrete sample solve/static/runtime/audit verification claim.

Artifact freshness policy:

- New artifacts must carry `decision_20260705_governance_operations_bundle_big_step_v1` and `round_20260705_governance_operations_bundle_big_step_v1`.
- Historical artifacts may be referenced as historical/backlog only unless explicitly refreshed under this round.
- Historical sample backlog must remain visible and nonblocking.

Command policy:

- Codex may execute only commands authorized by `project_state/gates/command_plan.json`.
- Omitted commands must not be executed.
- If this Tests section conflicts with command-plan, command-plan wins.

## 3. Do Not Do

Do not run cleanup-apply.

Do not delete, move, rename, archive, compact, tombstone, or destructively mutate any file.

Do not create or write a real deletion manifest.

Do not create or write a real tombstone.

Do not create SQLite files, `.db` files, migrations, or persistent database state.

Do not mutate `project_state/archives/*`, `project_state/deletions/*`, or `project_state/blob_store/*`.

Do not modify `.github/workflows/*` or `.codex-skills/*`.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or recursively scan all `project_state/rounds/`.

Do not process real samples, binaries, training corpora, or user uploads.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external reverse tools.

Do not invoke model APIs, automatic runners, manual runner dispatch, remote agents, CI workflow dispatch, or CI polling.

Do not implement Web runtime, database, queue, scheduler, production HTTP service, or background service.

Do not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

Do not weaken final-check, status-policy, command-plan, execution-log, report-summary, closeout, retention policy, or archive/cleanup safety checks to make the bundle pass.

## 4. Files To Inspect

Read first:

1. `project_state/decision_packet.md`
2. `project_state/codex_execution_report.md`
3. `project_state/execution_report.md`
4. `project_state/pytest_result.txt`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/report_summary_synthesis.json`
7. `project_state/gates/status_policy_reconcile_result.json`
8. `project_state/gates/doctor_backlog_split_result.json`
9. `project_state/retention_policy.json`
10. `project_state/state_lifecycle_registry.json`
11. `project_state/gates/cleanup_plan.json`
12. `project_state/gates/cleanup_plan_summary.json`
13. `project_state/gates/archive_index.json`
14. `project_state/gates/archive_index_summary.json`
15. `project_state/gates/cleanup_apply_safety_result.json`
16. `project_state/gates/cleanup_apply_safety_snapshot.json`
17. `project_state/gates/cleanup_apply_dry_run.json`
18. `project_state/gates/deletion_manifest_schema.json`
19. `project_state/gates/tombstone_schema.json`
20. `project_state/gates/deletion_manifest_validation_result.json`
21. `project_state/gates/tombstone_validation_result.json`
22. `project_state/gates/rollback_handoff_plan.json`
23. `project_state/gates/audit_handoff_for_cleanup_apply.json`
24. `project_state/state_manifest.json`
25. `project_state/context/current_context_packet.json`
26. `project_state/roadmap/workstreams.json`
27. `project_state/task_packet.json`
28. `project_state/current_state.json`
29. `project_state/artifact_index.json`
30. `project_state/negative_results.json`
31. `.codex-skills/registry.json`

Inspect source/test surfaces:

1. `reverse_agent/cleanup_apply_safety.py`
2. `reverse_agent/state_governance.py`
3. `reverse_agent/state_hygiene.py`
4. `reverse_agent/project_gate.py`
5. `reverse_agent/project_reports.py`
6. `reverse_agent/project_state_manifest.py`
7. `reverse_agent/project_context_builder.py`
8. `reverse_agent/project_workstreams.py`
9. `reverse_agent/state_index_readiness.py` if present
10. `reverse_agent/round_compaction.py` if present
11. `tests/test_cleanup_apply_safety.py`
12. `tests/test_state_governance.py`
13. `tests/test_state_hygiene.py`
14. `tests/test_project_gate.py`
15. `tests/test_project_reports.py`
16. `tests/test_project_state_manifest.py`
17. `tests/test_project_context_builder.py`
18. `tests/test_project_workstreams.py`
19. `tests/test_state_index_readiness.py` if present
20. `tests/test_round_compaction.py` if present

Do not inspect full heavy artifacts unless command-plan explicitly authorizes a bounded read.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was `decision_20260705_status_policy_final_acceptance_rework_v1` treated as the last accepted baseline?
5. Did this round remain one mainline, `project_governance`?
6. Did the round supersede the smaller unexecuted `cleanup_apply_review_bundle_v1` plan rather than running both?
7. Were existing retention, cleanup, archive, status-policy, doctor/backlog, cleanup-apply safety, command-plan, execution-log, report-summary, final-check, closeout, manifest, context, and workstream capabilities inspected before modification?
8. Did the implementation avoid duplicating existing capabilities from scratch?
9. Was `cleanup_apply_review_bundle.json` generated?
10. Was `cleanup_apply_review_result.json` generated?
11. Was `cleanup_candidate_risk_matrix.json` generated and did it classify candidates by evidence role, retention class, future action, risk, confidence, required approval, and future decision requirement?
12. Was `cleanup_apply_approval_checklist.json` generated and did it require a separate future decision before any real cleanup-apply?
13. Was `evidence_lock_manifest.json` generated and did it protect current audit fact sources and accepted-round minimum evidence?
14. Was `deletion_manifest_dry_run.json` generated with `real_deletion_manifest=false` and `delete_allowed_now=false`?
15. Was `tombstone_plan_dry_run.json` generated with `real_tombstone_write=false`?
16. Was `round_compaction_plan.json` generated?
17. Was `round_compaction_dry_run.json` generated?
18. Did round compaction dry-run avoid writing archives, moving files, deleting files, or mutating `project_state/archives/*`?
19. Was `round_compaction_manifest_dry_run.json` generated and clearly marked dry-run-only?
20. Was `archive_index.json` refreshed in bounded mode without recursive full history scan?
21. Was `state_index_readiness_schema.json` generated without creating a real database?
22. Was `state_index_readiness_plan.json` generated and did it state SQLite is a read/query index, not the audit fact source?
23. Was `state_index_readiness_result.json` generated and did it prove no SQLite/db file was created?
24. Was `state_hygiene_dashboard_feed.json` generated?
25. Did dashboard feed contain current decision, round, report, final-check, backlog notices, cleanup readiness, compaction readiness, and index readiness?
26. Was `lifecycle_transition_guard_result.json` generated?
27. Did lifecycle guard verify exactly one active workstream and keep real cleanup-apply deferred?
28. Were `state_manifest`, `current_context_packet`, and `workstreams` refreshed for this round if needed?
29. Does `workstreams.json` mark only `governance_operations_bundle` as `ACTIVE_ROUND`?
30. Did status-policy/final-check acceptance remain `PASSED`/`ACCEPTED`?
31. Did historical sample backlog remain visible as nonblocking backlog?
32. Did the round prove no cleanup-apply, deletion, move, archive apply, archive compaction, real tombstone, real deletion manifest, database migration, Web runtime, runner dispatch, CI dispatch, model API, external reverse tool, or real sample processing occurred?
33. Did command-plan authorize every executed command?
34. Were command-plan omitted commands left unexecuted?
35. Did pytest_result record real commands and exit codes?
36. Did focused tests cover review bundle, compaction dry-run, read-index schema, dashboard feed, lifecycle guard, and no-op safety behavior?
37. Did existing governance/gate/report tests continue to pass?
38. Did report-summary synthesis pass and match the execution report?
39. Did final-check pass?
40. Did run-closeout pass if authorized?
41. Were forbidden paths untouched?
42. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, `project_state/archives/*`, `project_state/deletions/*`, `project_state/blob_store/*`, and SQLite/db files untouched or absent as required?
43. Did the final report avoid any concrete sample solve/static/runtime/audit validation claim?
44. Did the final report explicitly state this is an operations readiness bundle only, not cleanup apply, not compaction apply, not database creation, and not Web/runtime work?

## 6. Implementation Scope

Allowed implementation is a larger but bounded governance operations bundle.

### A. Cleanup-apply review package

Extend existing cleanup-apply safety/governance helpers. Do not reimplement the earlier dry-run safety layer from scratch.

Generate:

- `project_state/gates/cleanup_apply_review_bundle.json`
- `project_state/gates/cleanup_apply_review_result.json`
- `project_state/gates/cleanup_apply_review_snapshot.json`
- `project_state/gates/cleanup_candidate_risk_matrix.json`
- `project_state/gates/cleanup_apply_approval_checklist.json`
- `project_state/gates/evidence_lock_manifest.json`
- `project_state/gates/deletion_manifest_dry_run.json`
- `project_state/gates/tombstone_plan_dry_run.json`
- `project_state/gates/rollback_rehearsal_plan.json`
- `project_state/gates/audit_handoff_for_cleanup_apply.json`

Required behavior:

- All review artifacts are advisory/readiness only.
- No candidate may have `delete_allowed_now=true` or `archive_allowed_now=true`.
- Current audit fact sources and accepted-round minimum evidence must be protected.
- Unknown entries require manual review.
- Future cleanup-apply requires separate decision, command-plan, final-check, deletion manifest, tombstone plan, rollback handoff, and audit.

### B. Round compaction dry-run

Add or extend bounded compaction planning helpers, preferably in `reverse_agent/round_compaction.py` or existing state governance modules.

Generate:

- `project_state/gates/round_compaction_plan.json`
- `project_state/gates/round_compaction_dry_run.json`
- `project_state/gates/round_compaction_manifest_dry_run.json`

Required behavior:

- Source rounds are selected only from bounded known baselines and current manifests.
- No recursive full `project_state/rounds/` scan.
- No archive writing, no file deletion, no movement, no compression, no mutation of `project_state/archives/*`.
- Output should say what a future compaction would retain, summarize, reference, or reject.
- Dry-run manifest must include `compaction_apply_allowed=false`.

### C. Archive/index refresh

Refresh archive index artifacts in bounded mode.

Generate or update:

- `project_state/gates/archive_index.json`
- `project_state/gates/archive_index_summary.json`

Required behavior:

- No archive apply.
- No mutation of archive directories.
- Classify current, accepted baseline, historical nonblocking, dry-run review, and backlog artifacts.

### D. SQLite read-index readiness

Add or extend a schema-only readiness module, preferably `reverse_agent/state_index_readiness.py` if it does not already exist.

Generate:

- `project_state/gates/state_index_readiness_schema.json`
- `project_state/gates/state_index_readiness_plan.json`
- `project_state/gates/state_index_readiness_result.json`

Required behavior:

- Define future read-index tables for decisions, rounds, artifacts, executions, audits, workstreams, and backlog notices.
- State clearly that SQLite is a query/read index only and does not replace `project_state` as audit fact source.
- Do not create `project_state/index.sqlite`, `.db`, migration files, or any persistent database.

### E. State-hygiene dashboard feed

Generate:

- `project_state/gates/state_hygiene_dashboard_feed.json`
- `project_state/gates/state_hygiene_dashboard_summary.json`

Required behavior:

- Provide a bounded feed for future Web/dashboard use.
- Include current decision/round/report/final-check, last accepted baseline, workstream state, cleanup review readiness, compaction readiness, index readiness, historical backlog notices, and forbidden capability status.
- No HTTP server, API, frontend code, or Web runtime.

### F. Lifecycle transition guard

Generate:

- `project_state/gates/lifecycle_transition_guard_result.json`
- `project_state/gates/governance_operations_bundle_result.json`
- `project_state/gates/governance_operations_bundle_snapshot.json`

Required behavior:

- Verify one active workstream.
- Verify destructive work remains deferred.
- Verify status-policy clean acceptance remains preserved.
- Verify cleanup review, compaction dry-run, SQLite readiness, dashboard feed, and archive/index refresh are current.
- Verify forbidden capabilities are disabled.

### G. Context/workstream refresh

Update as needed:

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`

Required state:

- `governance_operations_bundle` is the only `ACTIVE_ROUND`.
- `status_policy_final_acceptance_rework` is accepted baseline.
- The smaller cleanup review plan is superseded/unexecuted.
- Real cleanup-apply, compaction apply, database migration, Web runtime, runner dispatch, CI mutation, tool integration, and reverse solving remain deferred/non-active.

### H. Documentation

Add or update concise docs for the new bundle:

- `docs/governance_operations_bundle.md`
- `docs/cleanup_apply_review_bundle.md`
- `docs/round_compaction.md`
- `docs/state_index_readiness.md`
- `docs/state_hygiene_dashboard_feed.md`

Docs must emphasize project_state remains audit fact source and this round is readiness/dry-run only.

## 7. Tests

Command-plan is command authority. If this section conflicts with generated command-plan, command-plan wins.

Minimum expected validation commands:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate prework-provenance --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_state doctor --state-dir project_state
python -m pytest tests/test_cleanup_apply_safety.py tests/test_state_governance.py tests/test_state_hygiene.py tests/test_round_compaction.py tests/test_state_index_readiness.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m reverse_agent.project_gate governance-operations-bundle --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_governance_operations_bundle_big_step_v1
```

Expected results:

- governance operations bundle tests pass;
- cleanup review tests pass;
- compaction dry-run tests pass;
- state index readiness tests pass;
- existing governance/gate/report tests pass;
- governance-operations-bundle gate passes;
- report-summary passes and matches execution report;
- final-check passes;
- run-closeout passes if authorized;
- no omitted command is executed;
- no forbidden path is mutated;
- no destructive operation occurs;
- no database file is created.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. Repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects dirty source/test files not captured by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active.
5. command-plan cannot be generated or does not authorize required commands.
6. Implementation requires real cleanup-apply or cleanup-apply execution.
7. Implementation requires deleting, moving, renaming, archiving, compacting, tombstoning, or destructively mutating any file.
8. Implementation requires writing a real deletion manifest or real tombstone.
9. Implementation requires creating SQLite/db files, migrations, or replacing `project_state` as fact source.
10. Implementation requires modifying `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `project_state/archives/*`, `project_state/deletions/*`, or `project_state/blob_store/*`.
11. Implementation requires reading full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or recursively scanning all `project_state/rounds/`.
12. Implementation requires Web runtime, database, queue, scheduler, runner dispatch, model API, CI dispatch, external reverse tool execution, or real sample processing.
13. Any candidate must be marked `delete_allowed_now=true` or `archive_allowed_now=true` to make the bundle pass.
14. Round compaction dry-run needs real archive write, real delete, or real move.
15. State index readiness needs a real database file.
16. Historical sample backlog must be hidden or removed to make final-check pass.
17. Status-policy/final-check acceptance regresses from `PASSED`/`ACCEPTED` for current governance evidence.
18. More than one workstream would need to be marked `ACTIVE_ROUND`.
19. A concrete sample solve/static/runtime/audit verification claim is introduced.

If blocked, write `codex_execution_report.md`, `execution_report.md`, and `pytest_result.txt` with available evidence. Do not run closeout unless command-plan explicitly authorizes diagnostic closeout for failed rounds.
