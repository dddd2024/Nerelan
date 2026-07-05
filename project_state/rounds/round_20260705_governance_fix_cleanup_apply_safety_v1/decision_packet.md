```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_governance_fix_cleanup_apply_safety_v1",
  "round_id": "round_20260705_governance_fix_cleanup_apply_safety_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260705_state_governance_bundle_big_step_v1",
  "follows_last_accepted_round_id": "round_20260705_state_governance_bundle_big_step_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_42_governance_fix_cleanup_apply_safety_v1",
  "primary_goal": "Run one project_governance round with two lanes under the same mainline: fix the nonblocking limitations from the previous state governance bundle, and advance cleanup-apply safety engineering through dry-run-only gates and manifests. The fix lane must reconcile historical sample artifact gaps and doctor/status-policy semantics so non-sample governance rounds are not incorrectly downgraded by stale sample backlog. The engineering lane must add cleanup-apply safety prechecks, dry-run plans, manifest validation, tombstone validation, and rollback/audit handoff design without deleting, moving, archiving, compacting, or mutating any protected evidence.",
  "command_plan_authority_required": true,
  "accepted_requires_fix_lane": true,
  "accepted_requires_engineering_lane": true,
  "accepted_requires_status_policy_reconcile": true,
  "accepted_requires_doctor_backlog_split": true,
  "accepted_requires_cleanup_apply_safety_gate": true,
  "accepted_requires_cleanup_apply_dry_run": true,
  "accepted_requires_manifest_and_tombstone_validation": true,
  "accepted_requires_no_real_cleanup_apply": true,
  "accepted_requires_no_destructive_mutation": true,
  "allowed_source_files": [
    "reverse_agent/state_governance.py",
    "reverse_agent/state_hygiene.py",
    "reverse_agent/cleanup_apply_safety.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "tests/test_cleanup_apply_safety.py",
    "tests/test_state_governance.py",
    "tests/test_state_hygiene.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/governance_fix_cleanup_apply_safety.md",
    "docs/state_governance_bundle.md",
    "docs/state_hygiene_retention_policy.md",
    "docs/deletion_manifest_and_tombstone.md",
    "docs/archive_index.md",
    "docs/state_manifest.md",
    "docs/workstream_registry.md",
    "docs/project_governance_context.md"
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
    "project_state/gates/status_policy_reconcile_result.json",
    "project_state/gates/doctor_backlog_split_result.json",
    "project_state/gates/governance_fix_result.json",
    "project_state/gates/cleanup_apply_safety_plan.json",
    "project_state/gates/cleanup_apply_dry_run.json",
    "project_state/gates/cleanup_apply_safety_result.json",
    "project_state/gates/cleanup_apply_safety_snapshot.json",
    "project_state/gates/deletion_manifest_validation_result.json",
    "project_state/gates/tombstone_validation_result.json",
    "project_state/gates/rollback_handoff_plan.json",
    "project_state/gates/audit_handoff_for_cleanup_apply.json",
    "project_state/gates/cleanup_plan.json",
    "project_state/gates/cleanup_plan_summary.json",
    "project_state/gates/archive_index.json",
    "project_state/gates/archive_index_summary.json",
    "project_state/gates/deletion_manifest_schema.json",
    "project_state/gates/tombstone_schema.json",
    "project_state/gates/retention_policy_validation.json",
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
    "project_state/rounds/round_20260705_governance_fix_cleanup_apply_safety_v1/*"
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
    "project_state/deletions/*"
  ],
  "forbidden_capabilities_this_round": [
    "real_cleanup_apply",
    "file_delete",
    "file_move",
    "archive_compaction",
    "archive_apply",
    "real_tombstone_write",
    "real_deletion_manifest_write",
    "real_sample_analysis_execution",
    "real_user_upload_ingestion",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "model_api_invocation",
    "production_http_service",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "github_workflow_modification",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Governance Fix + Cleanup Apply Safety v1**.

The user explicitly requested that repair and engineering progress happen in the same next plan. To preserve the project rule that each round advances one mainline only, this round stays inside `project_governance` and is split into two lanes under that one mainline:

1. **Fix lane**
   - Repair the previous `ACCEPTED_WITH_LIMITATIONS` cause where historical sample artifact gaps and doctor status still downgrade a non-sample governance round.
   - Add explicit status-policy reconciliation so historical sample backlog is separated from current governance evidence.
   - Add a doctor/backlog split artifact so final-check can distinguish current evidence failure from historical backlog notices.
   - Keep missing historical sample artifacts visible, but stop treating them as a current governance blocker or as a reason to downgrade if the active decision makes no sample-evidence claim.

2. **Engineering lane**
   - Advance the cleanup-apply system from schema-only planning to dry-run-only safety engineering.
   - Add cleanup-apply precondition checks, dry-run plan generation, deletion manifest validation, tombstone validation, rollback handoff planning, and cleanup-apply audit handoff planning.
   - Do not perform cleanup apply.
   - Do not delete, move, archive, compact, or tombstone any real file.

Accepted target:

- Mainline remains `project_governance`.
- The fix lane should make final-check able to pass cleanly for non-sample governance rounds when the only remaining issue is historical sample artifact backlog.
- The engineering lane should create dry-run-only cleanup-apply safety gates.
- `project_state/decision_packet.md` remains task authority.
- `project_state/gates/command_plan.json` remains command authority.
- `project_state` remains the audit fact source.
- No cleanup apply, deletion, move, archive compaction, real deletion manifest, real tombstone, Web runtime, runner dispatch, CI dispatch, model API, database, external reverse tool, or sample solving is allowed.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` remains old sample-reverse background and still states that `decision_packet` controls the current round.

Previous accepted-with-limitations baseline:

- `decision_20260705_state_governance_bundle_big_step_v1`
- `round_20260705_state_governance_bundle_big_step_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from that baseline:

- The state governance bundle report was `SUCCESS` and generated retention policy, cleanup plan, archive index, deletion/tombstone schemas, state lifecycle registry, state manifest, context packet, workstream registry, and state governance bundle gate artifacts.
- `pytest_result.txt` was `PASSED` with broad gate/report tests and state governance tests.
- `execution_log.json` was current and listed all recorded commands as passed.
- `state_governance_bundle_result.json` showed no destructive operation, `cleanup_apply_allowed=false`, and all forbidden capabilities disabled.
- `final_gate_result.json` was still `PASSED_WITH_LIMITATIONS` because `doctor_status=FAIL` was carried forward for historical sample artifact gaps, even though the same result stated those gaps are nonblocking for current non-sample governance evidence.

Current limitation to fix:

- Historical sample artifact gaps remain visible as `50 missing, 0 stale artifacts`.
- The active governance rounds make no concrete sample-evidence claim.
- Therefore this should be classified as backlog context, not a current governance limitation.
- A new status-policy reconcile gate should record this distinction and allow a clean current-governance result if all active evidence passes.

Current engineering opportunity:

- The last round produced schemas and planning artifacts for cleanup, archive, deletion manifest, and tombstone design.
- The next engineering step should not be real cleanup apply.
- The correct next engineering step is cleanup-apply **dry-run safety foundation**: validate preconditions, simulate candidates, validate manifest/tombstone schemas, and produce rollback/audit handoff artifacts.

Existing capabilities that must not be duplicated:

- command-plan authority;
- execution-log validation;
- report-summary synthesis;
- final-check;
- run-closeout;
- state manifest;
- context packet;
- workstream registry;
- retention policy;
- cleanup plan;
- archive index;
- deletion/tombstone schema artifacts;
- state governance bundle gate.

This round must extend those capabilities, not reimplement them from scratch.

Negative results still apply:

- no old sample-solver blind search;
- no beam/budget expansion;
- no invalid frontier reuse;
- no full `solve_reports` commits;
- no repeated stale runtime diagnostics.

Artifact freshness policy:

- New artifacts must carry `decision_20260705_governance_fix_cleanup_apply_safety_v1` and `round_20260705_governance_fix_cleanup_apply_safety_v1`.
- Historical sample, user-solve, runner, CI, Web, and prior governance artifacts may be referenced only as historical/backlog evidence unless current IDs match.

Command policy:

- Codex may execute only commands authorized by `project_state/gates/command_plan.json`.
- Omitted commands must not be executed.
- If this Tests section conflicts with command-plan, command-plan wins.

## 3. Do Not Do

Do not run cleanup apply.

Do not delete, move, rename, archive, compact, tombstone, or destructively mutate any file.

Do not write a real deletion manifest for actual deletion.

Do not write a real tombstone for actual deletion.

Do not modify `.github/workflows/*`.

Do not modify `.codex-skills/*`.

Do not store dynamic project facts in long-term prompt/skill files.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not modify `project_state/archives/*` or `project_state/deletions/*`.

Do not scan full `solve_reports/`.

Do not scan full `PROJECT_PROGRESS_LOG.txt`.

Do not recursively scan the whole `project_state/rounds/` tree.

Do not process real samples, training binaries, local reverse corpora, or user uploads.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external analysis tools.

Do not invoke model APIs, planner APIs, auditor APIs, automatic runners, manual runner dispatch, remote agents, CI workflow dispatch, or CI polling.

Do not implement a database, queue, production HTTP service, scheduler, background service, or Web runtime.

Do not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

Do not split this into multiple mainlines. The only active mainline is `project_governance`.

## 4. Files To Inspect

Read first:

1. `project_state/decision_packet.md`
2. `project_state/state_manifest.json`
3. `project_state/context/current_context_packet.json`
4. `project_state/roadmap/workstreams.json`
5. `project_state/retention_policy.json`
6. `project_state/state_lifecycle_registry.json`
7. `project_state/task_packet.json`
8. `project_state/current_state.json`
9. `project_state/artifact_index.json`
10. `project_state/negative_results.json`
11. `project_state/codex_execution_report.md`
12. `project_state/execution_report.md`
13. `project_state/pytest_result.txt`
14. `.codex-skills/registry.json`

Inspect current and previous gates:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/execution_log.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/state_governance_bundle_result.json`
7. `project_state/gates/state_governance_bundle_snapshot.json`
8. `project_state/gates/cleanup_plan.json`
9. `project_state/gates/cleanup_plan_summary.json`
10. `project_state/gates/archive_index.json`
11. `project_state/gates/archive_index_summary.json`
12. `project_state/gates/deletion_manifest_schema.json`
13. `project_state/gates/tombstone_schema.json`
14. `project_state/rounds/round_20260705_state_governance_bundle_big_step_v1/round_manifest.json`

Inspect existing source surfaces before adding new code:

1. `reverse_agent/state_governance.py`
2. `reverse_agent/state_hygiene.py`
3. `reverse_agent/project_state_manifest.py`
4. `reverse_agent/project_context_builder.py`
5. `reverse_agent/project_workstreams.py`
6. `reverse_agent/project_gate.py`
7. `reverse_agent/project_reports.py`
8. `tests/test_state_governance.py`
9. `tests/test_state_hygiene.py`
10. `tests/test_project_gate.py`
11. `tests/test_project_reports.py`

Check whether these paths already exist before creating them:

1. `reverse_agent/cleanup_apply_safety.py`
2. `tests/test_cleanup_apply_safety.py`
3. `project_state/gates/status_policy_reconcile_result.json`
4. `project_state/gates/doctor_backlog_split_result.json`
5. `project_state/gates/governance_fix_result.json`
6. `project_state/gates/cleanup_apply_safety_plan.json`
7. `project_state/gates/cleanup_apply_dry_run.json`
8. `project_state/gates/cleanup_apply_safety_result.json`
9. `project_state/gates/cleanup_apply_safety_snapshot.json`
10. `project_state/gates/deletion_manifest_validation_result.json`
11. `project_state/gates/tombstone_validation_result.json`
12. `project_state/gates/rollback_handoff_plan.json`
13. `project_state/gates/audit_handoff_for_cleanup_apply.json`

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was the previous state governance bundle treated as accepted-with-limitations baseline?
5. Did this round remain one mainline, `project_governance`, while containing a fix lane and engineering lane?
6. Were existing state governance, retention, cleanup-plan, archive-index, manifest, context, and workstream capabilities inspected before adding code?
7. Did the implementation avoid duplicating command-plan, execution-log, report-summary, final-check, closeout, state manifest, context packet, and workstream registry?
8. Was `project_state/gates/status_policy_reconcile_result.json` generated?
9. Does status-policy reconcile distinguish current governance evidence from historical sample backlog?
10. Does status-policy reconcile prevent historical sample backlog from downgrading a non-sample governance round when active evidence passes?
11. Was `project_state/gates/doctor_backlog_split_result.json` generated?
12. Does doctor/backlog split record historical sample gaps as backlog notices rather than current blockers?
13. Was `project_state/gates/governance_fix_result.json` generated?
14. Does governance fix result show whether the previous limitation is resolved for current non-sample governance evidence?
15. Was `project_state/gates/cleanup_apply_safety_plan.json` generated?
16. Was `project_state/gates/cleanup_apply_dry_run.json` generated?
17. Does cleanup-apply dry run explicitly set `real_cleanup_apply=false`?
18. Does cleanup-apply dry run leave `deleted_files`, `moved_files`, `archived_files`, `compacted_archives`, `written_tombstones`, and `real_deletion_manifests` empty?
19. Was `project_state/gates/cleanup_apply_safety_result.json` generated?
20. Was `project_state/gates/cleanup_apply_safety_snapshot.json` generated?
21. Does cleanup-apply safety gate prove no real cleanup apply, deletion, move, archive, compaction, tombstone write, database, runner dispatch, model API, external tool, CI dispatch, Web runtime, or real sample processing occurred?
22. Was `project_state/gates/deletion_manifest_validation_result.json` generated?
23. Was `project_state/gates/tombstone_validation_result.json` generated?
24. Do manifest/tombstone validation artifacts validate schema-only or dry-run-only payloads, not real deletion payloads?
25. Was `project_state/gates/rollback_handoff_plan.json` generated?
26. Was `project_state/gates/audit_handoff_for_cleanup_apply.json` generated?
27. Do rollback/audit handoff artifacts state that future cleanup-apply needs a separate decision and audit?
28. Were `state_manifest`, `current_context_packet`, and `workstreams` refreshed for this round?
29. Does `workstreams.json` mark only `governance_fix_cleanup_apply_safety` as `ACTIVE_ROUND`?
30. Does `workstreams.json` keep real cleanup-apply deferred until a future decision?
31. Did command-plan authorize every executed command?
32. Were command-plan omitted commands left unexecuted?
33. Did pytest_result record real commands and exit codes?
34. Did focused tests cover status-policy reconciliation, doctor/backlog split, cleanup-apply safety, dry-run no-op behavior, manifest validation, and tombstone validation?
35. Did existing governance/gate/report tests continue to pass?
36. Did final-check pass cleanly, or if not, did it identify only nonblocking historical sample backlog with a clear reason?
37. Did report-summary synthesis pass and match the execution report?
38. Did run-closeout pass if authorized?
39. Were forbidden paths untouched?
40. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, `project_state/archives/*`, and `project_state/deletions/*` untouched?
41. Did the final report avoid any concrete sample solve/static/runtime/audit validation claim?
42. Did the final report explicitly state that cleanup-apply safety is dry-run-only and no real deletion occurred?

## 6. Implementation Scope

Allowed implementation is a combined repair-and-advance governance round.

### A. Fix lane: status-policy and doctor/backlog reconciliation

Add or extend bounded helpers in `reverse_agent/state_governance.py`, `reverse_agent/state_hygiene.py`, or a small new helper if necessary.

Generate:

- `project_state/gates/status_policy_reconcile_result.json`
- `project_state/gates/doctor_backlog_split_result.json`
- `project_state/gates/governance_fix_result.json`

Required behavior:

- Classify each doctor/status issue as `current_blocker`, `current_warning`, `historical_backlog_notice`, or `external_notice`.
- Historical sample artifact gaps must be represented as `historical_backlog_notice` when the active decision is non-sample governance and makes no concrete sample-evidence claim.
- The fix must not hide the backlog. It must make the backlog explicit and nonblocking.
- The fix must not mutate `current_state.json`, `artifact_index.json`, `negative_results.json`, or `task_packet.json`.
- The fix must integrate with final-check/report-summary without weakening checks for current artifacts.

### B. Engineering lane: cleanup-apply dry-run safety foundation

Add `reverse_agent/cleanup_apply_safety.py` or extend existing state governance code if that is cleaner.

Generate:

- `project_state/gates/cleanup_apply_safety_plan.json`
- `project_state/gates/cleanup_apply_dry_run.json`
- `project_state/gates/cleanup_apply_safety_result.json`
- `project_state/gates/cleanup_apply_safety_snapshot.json`
- `project_state/gates/deletion_manifest_validation_result.json`
- `project_state/gates/tombstone_validation_result.json`
- `project_state/gates/rollback_handoff_plan.json`
- `project_state/gates/audit_handoff_for_cleanup_apply.json`

Required behavior:

- Simulate cleanup-apply preconditions only.
- Validate deletion manifest schema and tombstone schema with dry-run/example payloads only.
- Produce a dry-run candidate summary from existing cleanup plan, but do not execute candidates.
- Every dry-run candidate must have `real_action_allowed=false`.
- All destructive-result arrays must be empty.
- Future cleanup-apply must require a separate decision, command-plan authorization, deletion manifest, tombstone plan, audit handoff, rollback handoff, and final-check.

### C. Gate integration

Add a bounded project-gate command, for example:

```powershell
python -m reverse_agent.project_gate cleanup-apply-safety --state-dir project_state
```

Also add or extend a governance fix gate, for example:

```powershell
python -m reverse_agent.project_gate governance-fix --state-dir project_state
```

The exact command names may differ if existing CLI conventions require it, but command-plan, pytest_result, execution_log, and reports must record the exact commands.

### D. Context and workstream refresh

Update:

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`

Required updates:

- current active decision/round becomes this round;
- `governance_fix_cleanup_apply_safety` is the only `ACTIVE_ROUND`;
- `state_governance_bundle_big_step` becomes accepted-with-limitations baseline;
- real cleanup-apply remains deferred;
- Web, runner, CI mutation, database, tool integration, and reverse solving remain non-active.

### E. Tests and reports

Add tests for:

- status-policy reconcile;
- doctor/backlog split;
- governance fix artifact generation;
- cleanup-apply dry-run no-op behavior;
- manifest validation;
- tombstone validation;
- rollback/audit handoff requirements;
- final-check/report-summary consistency.

Do not weaken existing gate/report tests.

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
python -m pytest tests/test_cleanup_apply_safety.py tests/test_state_governance.py tests/test_state_hygiene.py tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate governance-fix --state-dir project_state
python -m reverse_agent.project_gate cleanup-apply-safety --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_governance_fix_cleanup_apply_safety_v1
```

Expected results:

- New cleanup-apply safety tests pass.
- Existing state governance/hygiene tests pass.
- Existing manifest/context/workstream tests pass.
- Existing gate/report tests pass.
- governance-fix gate passes.
- cleanup-apply-safety gate passes.
- report-summary passes and matches report.
- final-check passes cleanly, or only carries explicitly nonblocking historical sample backlog notices.
- run-closeout passes if authorized.
- no omitted command is executed.
- no forbidden path is mutated.
- no real cleanup apply or destructive operation occurs.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. Repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects dirty source/test files and they are not captured by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active.
5. command-plan cannot be generated or does not authorize required commands.
6. The implementation requires real cleanup apply.
7. The implementation requires deleting, moving, renaming, archiving, compacting, or tombstoning any file.
8. The implementation requires a real deletion manifest for actual deletion.
9. The implementation requires modifying `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `project_state/archives/*`, or `project_state/deletions/*`.
10. The implementation requires reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
11. The implementation requires recursive full `project_state/rounds/` inventory.
12. The implementation requires Web runtime, database, queue, scheduler, runner dispatch, model API, CI dispatch, external reverse tool execution, or real sample processing.
13. More than one workstream would need to be marked `ACTIVE_ROUND`.
14. Historical sample backlog must be hidden or removed to make tests pass.
15. Any cleanup dry-run candidate must be marked as real-action-allowed to make tests pass.
16. Current audit fact sources cannot be protected.
17. final-check fails for a current evidence reason.
18. report-summary cannot reconcile report status with generated evidence.
19. Any concrete sample solve/static/runtime/audit verification claim is introduced.

If a stop condition is hit, write `codex_execution_report.md`, `execution_report.md`, and `pytest_result.txt` with the blocked/failed evidence available. Do not run closeout unless command-plan explicitly authorizes diagnostic closeout for failed rounds.
