```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_state_governance_bundle_big_step_v1",
  "round_id": "round_20260705_state_governance_bundle_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260705_project_governance_context_registry_v1",
  "follows_last_accepted_round_id": "round_20260705_project_governance_context_registry_v1",
  "supersedes_unexecuted_decision_id": "decision_20260705_state_hygiene_retention_policy_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_41_state_governance_bundle_big_step_v1",
  "primary_goal": "Deliver a larger project-governance bundle in one round: retention policy, cleanup-plan, archive index, deletion/tombstone schema design, state lifecycle registry, governance context/workstream refresh, and integrated gate/final-check/report validation. This remains non-destructive: no deletion, move, archive compaction, cleanup-apply, database, runner dispatch, CI dispatch, Web runtime, model API, external reverse tool, or concrete sample processing is allowed.",
  "command_plan_authority_required": true,
  "accepted_requires_retention_policy": true,
  "accepted_requires_cleanup_plan": true,
  "accepted_requires_archive_index": true,
  "accepted_requires_deletion_manifest_schema": true,
  "accepted_requires_tombstone_schema": true,
  "accepted_requires_lifecycle_registry": true,
  "accepted_requires_state_manifest_refresh": true,
  "accepted_requires_context_packet_refresh": true,
  "accepted_requires_workstream_registry_refresh": true,
  "accepted_requires_governance_gate": true,
  "accepted_requires_no_cleanup_apply": true,
  "accepted_requires_existing_hygiene_inventory_check": true,
  "allowed_source_files": [
    "reverse_agent/state_governance.py",
    "reverse_agent/state_hygiene.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "tests/test_state_governance.py",
    "tests/test_state_hygiene.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/state_governance_bundle.md",
    "docs/state_hygiene_retention_policy.md",
    "docs/archive_index.md",
    "docs/deletion_manifest_and_tombstone.md",
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
    "project_state/gates/state_governance_bundle_result.json",
    "project_state/gates/state_governance_bundle_snapshot.json",
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
    "project_state/rounds/round_20260705_state_governance_bundle_big_step_v1/*"
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
    "cleanup_apply",
    "file_delete",
    "file_move",
    "archive_compaction",
    "archive_apply",
    "tombstone_write_for_real_deletion",
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

Implement **State Governance Bundle Big Step v1**.

This decision intentionally replaces the smaller unexecuted `decision_20260705_state_hygiene_retention_policy_v1`. The user requested a larger step. The larger step is still constrained to a single mainline: `project_governance`. It must not drift into Web runtime work, runner dispatch, CI mutation, database implementation, tool integration, or concrete reverse solving.

The round should deliver a larger non-destructive governance bundle:

1. **Retention Policy v1**
   - Generate `project_state/retention_policy.json`.
   - Define lifecycle and retention classes for current evidence, accepted-round evidence, generated gate artifacts, historical nonblocking artifacts, missing sample references, transient closeout logs, PID files, docs/config, unknown files, and future disposable candidates.

2. **Cleanup Plan v1**
   - Generate `project_state/gates/cleanup_plan.json` and `project_state/gates/cleanup_plan_summary.json`.
   - It must be a planning artifact only.
   - It may classify files as retain/archive-candidate/delete-candidate, but no candidate may be deleted, moved, archived, compacted, or tombstoned in this round.

3. **Archive Index v1**
   - Generate `project_state/gates/archive_index.json` and `project_state/gates/archive_index_summary.json`.
   - It must index current known round archives and historical nonblocking gate artifacts from bounded sources.
   - It must not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or the entire `project_state/rounds/` tree recursively.

4. **Deletion Manifest and Tombstone Schema v1**
   - Generate `project_state/gates/deletion_manifest_schema.json` and `project_state/gates/tombstone_schema.json`.
   - These are schema/design artifacts only.
   - No real deletion manifest for actual files may be produced, and no tombstone may be written for actual deletion.

5. **State Lifecycle Registry v1**
   - Generate `project_state/state_lifecycle_registry.json`.
   - It should connect retention classes, cleanup-plan actions, archive-index roles, deletion/tombstone schema requirements, and future cleanup-apply preconditions.

6. **Governance Context Refresh**
   - Refresh `project_state/state_manifest.json`.
   - Refresh `project_state/context/current_context_packet.json`.
   - Refresh `project_state/roadmap/workstreams.json` so this bundle is the only `ACTIVE_ROUND`, the previous context-registry round is accepted baseline, and cleanup-apply remains deferred.

7. **Integrated Gate**
   - Generate `project_state/gates/state_governance_bundle_result.json` and `project_state/gates/state_governance_bundle_snapshot.json`.
   - The gate must prove no destructive operation occurred and that every artifact is index/design/planning evidence only.

Accepted target:

- Mainline remains `project_governance`.
- This is a larger governance round, not an execution/runtime round.
- `project_state/decision_packet.md` remains task authority.
- `project_state/gates/command_plan.json` remains command authority.
- `project_state` files remain audit fact sources.
- `retention_policy`, `cleanup_plan`, `archive_index`, `state_lifecycle_registry`, deletion schema, and tombstone schema are planning/index/schema artifacts, not execution authority.
- No cleanup apply is allowed.

## 2. Current Evidence

Current fact priority:

1. GitHub current code and current `project_state` files.
2. `project_state/decision_packet.md`.
3. `project_state/state_manifest.json`.
4. `project_state/context/current_context_packet.json`.
5. `project_state/roadmap/workstreams.json`.
6. current gates and reports.
7. `.codex-skills/registry.json`.

Current task authority:

- This new `decision_packet.md` controls the round.
- `task_packet.json` remains old sample-reverse context and background only.
- `command_plan.json` must authorize commands before execution.

Previous accepted-with-limitations baseline:

- `decision_20260705_project_governance_context_registry_v1`
- `round_20260705_project_governance_context_registry_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Relevant prior evidence:

- The previous governance context registry round generated `state_manifest.json`, `current_context_packet.json`, and `workstreams.json`.
- Its governance gate passed and marked the new governance artifacts as current and index-only.
- Its final-check was `PASSED_WITH_LIMITATIONS`, with the limitation tied to historical missing sample artifacts and doctor status fail.
- The limitation was nonblocking for a non-sample governance round.

State manifest evidence:

- `project_state/state_manifest.json` exists.
- It classifies current evidence, generated governance artifacts, historical nonblocking files, archived evidence, and missing artifacts.
- It reports missing sample artifacts as nonblocking for the current governance context.
- It treats `current_state.json`, `task_packet.json`, `artifact_index.json`, and `negative_results.json` as historical/nonblocking for governance planning.

Workstream evidence:

- `project_state/roadmap/workstreams.json` exists.
- It states roadmap entries are not execution authority.
- It previously marked `state_hygiene_retention_policy` as `READY_FOR_DECISION`.
- This larger bundle should supersede that smaller ready plan by marking `state_governance_bundle_big_step` as the only `ACTIVE_ROUND` and recording the smaller state-hygiene plan as superseded/unexecuted.

Existing hygiene capability:

- `project_state/gates/state_hygiene_inventory.json` exists as a historical inventory artifact.
- It was explicitly non-destructive: `no_delete=true`.
- This round must not claim state hygiene starts from zero. It should build on the existing inventory pattern, the context registry, and current state manifest.

Current problem to address in a larger step:

- Closeout temporary logs and PID files are appearing in round deltas.
- Historical nonblocking gate artifacts are accumulating.
- Missing historical sample references still show up as a nonblocking doctor limitation.
- There is no unified retention policy, cleanup-plan, archive index, deletion/tombstone schema, and lifecycle registry tying these together.
- Future cleanup-apply would be unsafe without these design artifacts and gates.

Negative results:

- Do not return to old solver blind search.
- Do not increase beam/budget to guess.
- Do not use invalid compare candidates as primary frontier.
- Do not commit full `solve_reports/`.
- Do not repeat stale runtime diagnostics without new evidence.

Artifact freshness:

- New current artifacts must carry `decision_20260705_state_governance_bundle_big_step_v1` and `round_20260705_state_governance_bundle_big_step_v1`.
- Historical user-solve, runner, CI, sample, and old hygiene artifacts may be referenced only as historical/nonblocking evidence unless current IDs match.
- Missing historical sample artifacts remain nonblocking for this governance round, but must be explicitly classified in the lifecycle registry and cleanup plan.

## 3. Do Not Do

Do not delete, move, rename, archive, compact, tombstone, or destructively mutate any state artifact.

Do not implement or run `cleanup-apply`.

Do not create a real deletion manifest for actual file deletion.

Do not write tombstones for actual deletion.

Do not implement a database, queue, background service, scheduler, production HTTP service, Web runtime, remote runner, CI dispatcher, or polling loop.

Do not modify `.github/workflows/*`.

Do not modify `.codex-skills/*`.

Do not store dynamic state facts in prompt/skill files.

Do not scan full `solve_reports/`.

Do not scan full `PROJECT_PROGRESS_LOG.txt`.

Do not recursively inventory the entire `project_state/rounds/` tree. Use only current round, previous accepted round manifest, and bounded named historical hygiene artifacts.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not modify `project_state/archives/*` or `project_state/deletions/*`.

Do not process real reverse samples, local binaries, training corpora, or user-uploaded files.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external analysis tools.

Do not invoke model APIs, Codex CLI, planner APIs, auditor APIs, automatic runners, manual runner dispatch, or CI workflow dispatch.

Do not mark any cleanup candidate as safe for immediate deletion.

Do not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

Do not mix this governance round with user-solve, Web, runner, CI, tool integration, database, or reverse-solving implementation.

## 4. Files To Inspect

Read first:

1. `project_state/decision_packet.md`
2. `project_state/state_manifest.json`
3. `project_state/context/current_context_packet.json`
4. `project_state/roadmap/workstreams.json`
5. `project_state/task_packet.json`
6. `project_state/current_state.json`
7. `project_state/artifact_index.json`
8. `project_state/negative_results.json`
9. `project_state/codex_execution_report.md`
10. `project_state/execution_report.md`
11. `project_state/pytest_result.txt`
12. `.codex-skills/registry.json`

Inspect current and prior governance gates:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/execution_log.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/project_governance_context_result.json`
7. `project_state/gates/project_governance_context_snapshot.json`
8. `project_state/rounds/round_20260705_project_governance_context_registry_v1/round_manifest.json`

Inspect prior hygiene artifacts before implementation:

1. `project_state/gates/state_hygiene_inventory.json`
2. `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/decision_packet.md`
3. `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/decision_packet.md`
4. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/decision_packet.md`

Inspect existing source surfaces:

1. `reverse_agent/project_state_manifest.py`
2. `reverse_agent/project_context_builder.py`
3. `reverse_agent/project_workstreams.py`
4. `reverse_agent/project_gate.py`
5. `reverse_agent/project_reports.py`
6. `tests/test_project_state_manifest.py`
7. `tests/test_project_context_builder.py`
8. `tests/test_project_workstreams.py`
9. `tests/test_project_gate.py`
10. `tests/test_project_reports.py`

Check whether these paths already exist before creating them:

1. `reverse_agent/state_governance.py`
2. `reverse_agent/state_hygiene.py`
3. `tests/test_state_governance.py`
4. `tests/test_state_hygiene.py`
5. `project_state/retention_policy.json`
6. `project_state/state_lifecycle_registry.json`
7. `project_state/gates/cleanup_plan.json`
8. `project_state/gates/cleanup_plan_summary.json`
9. `project_state/gates/archive_index.json`
10. `project_state/gates/archive_index_summary.json`
11. `project_state/gates/deletion_manifest_schema.json`
12. `project_state/gates/tombstone_schema.json`
13. `project_state/gates/state_governance_bundle_result.json`
14. `project_state/gates/state_governance_bundle_snapshot.json`

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was the previous governance context registry round treated as accepted-with-limitations baseline?
5. Did this round supersede the smaller unexecuted state-hygiene retention plan rather than execute both?
6. Were existing state manifest, context packet, workstream registry, and prior state hygiene inventory inspected before adding new code?
7. Did the implementation avoid duplicating existing command-plan, execution-log, report-summary, closeout, context-builder, manifest, and workstream mechanisms?
8. Was `project_state/retention_policy.json` generated?
9. Does `retention_policy.json` classify current audit evidence, accepted-round evidence, generated gate artifacts, historical nonblocking artifacts, transient closeout logs/pids, missing sample references, docs/config, unknown files, and future disposable candidates?
10. Does retention policy explicitly forbid deletion without a future cleanup-apply decision?
11. Was `project_state/gates/cleanup_plan.json` generated?
12. Does cleanup plan only produce retain/archive-candidate/delete-candidate recommendations and no destructive actions?
13. Does every destructive recommendation include `delete_allowed_now=false`, `requires_future_cleanup_apply_decision=true`, and `requires_tombstone_if_deleted=true`?
14. Does cleanup plan classify `run_closeout_*.out.log`, `run_closeout_*.err.log`, and `run_closeout_*.pid` as transient candidates without deleting them?
15. Does cleanup plan classify missing historical sample artifacts as nonblocking references rather than current evidence gaps?
16. Does cleanup plan preserve current decision, report, pytest, command-plan, execution-log, final-check, closeout, state manifest, context packet, workstreams, and accepted-round minimum evidence?
17. Was `project_state/gates/archive_index.json` generated?
18. Does archive index use only bounded archive sources and avoid recursive full-rounds scanning?
19. Does archive index separate current, archived, historical_nonblocking, and candidate-for-future-archive entries?
20. Was `project_state/gates/deletion_manifest_schema.json` generated as schema-only evidence?
21. Was `project_state/gates/tombstone_schema.json` generated as schema-only evidence?
22. Did the round avoid writing any real deletion manifest or real tombstone?
23. Was `project_state/state_lifecycle_registry.json` generated?
24. Does lifecycle registry connect retention classes, cleanup-plan actions, archive-index roles, deletion schema, tombstone schema, and future cleanup-apply preconditions?
25. Was `project_state/gates/state_governance_bundle_result.json` generated?
26. Was `project_state/gates/state_governance_bundle_snapshot.json` generated?
27. Do new gate artifacts carry current decision/report/round IDs?
28. Does the governance bundle gate prove no deletion, move, archive compaction, tombstone write, database, runner dispatch, model API, external tool, CI dispatch, Web runtime, or real sample processing occurred?
29. Were `project_state/state_manifest.json`, `project_state/context/current_context_packet.json`, and `project_state/roadmap/workstreams.json` updated for this round?
30. Does `workstreams.json` mark only `state_governance_bundle_big_step` as `ACTIVE_ROUND`?
31. Does `workstreams.json` mark `project_governance_context_registry` as accepted baseline?
32. Does `workstreams.json` keep cleanup-apply, runner dispatch, database indexing, IDA/Ghidra/debugger integration, dynamic reverse solving, Web runtime, and CI mutation deferred or non-active?
33. Did command-plan authorize every executed command?
34. Were command-plan omitted commands left unexecuted?
35. Did pytest_result record real commands and exit codes?
36. Did focused tests cover retention policy, cleanup plan, archive index, deletion/tombstone schemas, lifecycle registry, governance bundle gate, and no-delete behavior?
37. Did existing project governance/gate/report tests continue to pass?
38. Did final-check pass or pass-with-limitations only for explicitly nonblocking historical sample artifact gaps?
39. Did report-summary synthesis pass and match the report summary?
40. Did run-closeout pass if authorized?
41. Were forbidden files untouched?
42. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, `project_state/archives/*`, and `project_state/deletions/*` untouched?
43. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?
44. Did the final report explicitly state this round is planning/index/schema only and not cleanup-apply?
45. Did the final report recommend a future cleanup-apply round only after a separate decision accepts deletion manifest/tombstone design and deletion safety gates?

## 6. Implementation Scope

Allowed implementation is a larger but still bounded **project_governance** bundle.

### A. State Governance Module

Add `reverse_agent/state_governance.py` or extend `reverse_agent/state_hygiene.py` if that better fits existing code.

The module should provide deterministic helpers to build:

- retention policy;
- cleanup plan;
- cleanup summary;
- archive index;
- archive summary;
- deletion manifest schema;
- tombstone schema;
- state lifecycle registry;
- state governance bundle result;
- state governance bundle snapshot.

The module must avoid side effects other than writing allowed artifacts.

### B. Retention Policy

Generate `project_state/retention_policy.json`.

Minimum classes:

- `current_audit_fact_source`
- `accepted_round_minimum_evidence`
- `current_generated_governance_index`
- `current_gate_artifact`
- `historical_nonblocking_gate_artifact`
- `historical_sample_reference`
- `missing_historical_sample_reference`
- `transient_closeout_log`
- `transient_closeout_pid`
- `documentation`
- `configuration`
- `unknown_requires_manual_review`
- `disposable_candidate_requires_future_decision`

Every class must state:

- retain policy;
- archive policy;
- delete policy;
- whether future cleanup-apply is required;
- whether tombstone is required if deleted in a future round;
- whether deletion is allowed in this round, which must be false for all classes.

### C. Cleanup Plan

Generate:

- `project_state/gates/cleanup_plan.json`
- `project_state/gates/cleanup_plan_summary.json`

The cleanup plan must classify bounded candidates only. It must include current evidence protection and candidate lists for future action.

Required global assertions:

```json
{
  "cleanup_apply_allowed": false,
  "deleted_files": [],
  "moved_files": [],
  "archived_files": [],
  "compacted_archives": [],
  "written_tombstones": []
}
```

Any candidate that could be deleted in the future must contain:

```json
{
  "delete_allowed_now": false,
  "requires_future_cleanup_apply_decision": true,
  "requires_tombstone_if_deleted": true
}
```

### D. Archive Index

Generate:

- `project_state/gates/archive_index.json`
- `project_state/gates/archive_index_summary.json`

The archive index must include only bounded known sources:

- current round output;
- previous accepted governance round manifest;
- known historical state hygiene decision packets;
- current state manifest roles;
- current report summary artifact roles.

It must not recursively traverse all archive history.

### E. Deletion Manifest and Tombstone Schema

Generate schema-only artifacts:

- `project_state/gates/deletion_manifest_schema.json`
- `project_state/gates/tombstone_schema.json`

They must include required fields for a future cleanup-apply round but must not identify real files for deletion.

Required schema ideas:

- deletion manifest must require future decision ID, round ID, original path, hash, reason, retention class, audit approval, and tombstone target;
- tombstone must require original path, deleted hash, deletion manifest ID, deletion round, deletion timestamp, reason, and restore/audit notes.

### F. State Lifecycle Registry

Generate `project_state/state_lifecycle_registry.json`.

It must connect:

- retention policy classes;
- cleanup-plan recommendations;
- archive-index roles;
- deletion manifest schema;
- tombstone schema;
- current/future allowed transitions;
- explicit future cleanup-apply preconditions.

### G. Context and Workstream Refresh

Update existing governance outputs:

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`

Required updates:

- current active decision/round becomes this bundle;
- only `state_governance_bundle_big_step` is `ACTIVE_ROUND`;
- `project_governance_context_registry` becomes accepted baseline;
- smaller `state_hygiene_retention_policy_v1` is recorded as superseded/unexecuted, not accepted;
- cleanup-apply remains deferred;
- runner dispatch, database indexing, IDA/Ghidra/debugger integration, dynamic reverse solving, Web runtime, and CI mutation remain non-active.

### H. Project Gate Integration

Extend `reverse_agent/project_gate.py` with a bounded command such as:

```powershell
python -m reverse_agent.project_gate state-governance-bundle --state-dir project_state
```

The exact command may differ if an existing naming convention is more appropriate, but it must be recorded in command-plan, pytest_result, execution_log, and report.

Required gate checks:

- retention policy current;
- cleanup plan current;
- archive index current;
- deletion/tombstone schemas current;
- lifecycle registry current;
- state manifest/context/workstreams current;
- no destructive arrays contain files;
- no cleanup candidate is immediately deletable;
- active workstream is unique;
- current evidence is protected;
- accepted-round minimum evidence is protected;
- historical sample missing artifacts are nonblocking;
- all forbidden capabilities are disabled.

### I. Documentation

Add or update:

- `docs/state_governance_bundle.md`
- `docs/state_hygiene_retention_policy.md`
- `docs/archive_index.md`
- `docs/deletion_manifest_and_tombstone.md`
- bounded cross-references in existing governance docs if needed.

Docs must clearly explain:

- cleanup-plan is not cleanup-apply;
- deletion/tombstone artifacts are schema-only;
- archive index is an index, not archive compaction;
- future cleanup-apply needs a separate decision;
- current audit fact sources are protected;
- project_state remains the evidence source.

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
python -m pytest tests/test_state_governance.py tests/test_state_hygiene.py tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate state-governance-bundle --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_state_governance_bundle_big_step_v1
```

Expected results:

- New state governance tests pass.
- Existing manifest/context/workstream tests pass.
- Existing gate/report tests pass.
- State governance bundle gate passes.
- final-check passes, or passes with limitations only for explicitly nonblocking historical sample artifact gaps.
- report-summary is consistent with final report.
- run-closeout passes if authorized.
- no command-plan omissions are executed.
- no forbidden paths are mutated.
- no deletion, move, archive compaction, cleanup-apply, real deletion manifest, or real tombstone occurs.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. The repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects untracked or dirty source/test files before implementation and they are not captured by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active.
5. command-plan cannot be generated or does not authorize required commands.
6. Existing state manifest/context/workstream artifacts cannot be read and the failure cannot be represented as a bounded blocked report.
7. The implementation requires deleting, moving, renaming, archiving, compacting, or tombstoning files.
8. The implementation requires cleanup-apply.
9. The implementation requires a real deletion manifest for actual files.
10. The implementation requires reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
11. The implementation requires recursive full `project_state/rounds/` inventory.
12. The implementation requires Web runtime, database, queue, scheduler, runner dispatch, model API, CI dispatch, or external reverse tool execution.
13. The implementation needs to modify `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `project_state/archives/*`, or `project_state/deletions/*`.
14. More than one workstream would need to be marked `ACTIVE_ROUND`.
15. Any cleanup candidate must be marked `delete_allowed_now=true` to make tests pass.
16. Current audit fact sources or accepted-round minimum evidence cannot be protected.
17. final-check fails for a reason other than explicitly nonblocking historical sample artifact gaps.
18. report-summary cannot reconcile report status with generated evidence.
19. Any concrete sample solve/static/runtime/audit verification claim is introduced.

If a stop condition is hit, write `codex_execution_report.md`, `execution_report.md`, and `pytest_result.txt` with the blocked/failed evidence available. Do not run closeout unless command-plan explicitly authorizes diagnostic closeout for failed rounds.
