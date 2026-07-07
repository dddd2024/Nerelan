```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_scoped_state_metadata_foundation_big_step_v1",
  "round_id": "round_20260706_scoped_state_metadata_foundation_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_required_audit_status_truth_rework_v1",
  "follows_last_round_id": "round_20260706_required_audit_status_truth_rework_v1",
  "supersedes_unexecuted_decision_id": "decision_20260706_normal_pace_state_taxonomy_roadmap_registration_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_50_scoped_state_metadata_foundation_big_step_v1",
  "primary_goal": "Register the normal-pace roadmap and implement Project State Domain Taxonomy Phase A: add scoped metadata foundations for state_manifest, artifact_index, and negative_results without moving, deleting, or migrating state files.",
  "command_plan_authority_required": true,
  "accepted_requires_workstream_registry_current": true,
  "accepted_requires_docs_for_normal_pace_and_state_taxonomy": true,
  "accepted_requires_state_manifest_scope_metadata": true,
  "accepted_requires_artifact_index_scope_metadata": true,
  "accepted_requires_negative_results_scope_metadata": true,
  "accepted_requires_backward_compatibility": true,
  "accepted_requires_scope_validation_tests": true,
  "accepted_requires_no_file_moves_or_deletes": true,
  "accepted_requires_no_domain_directory_creation": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [
    "reverse_agent/project_state.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "tests/test_project_state.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/roadmap/reverse_agent_normal_pace_plan.md",
    "docs/roadmap/project_state_domain_taxonomy_supplement.md"
  ],
  "allowed_governance_files": [
    "project_state/roadmap/workstreams.json"
  ],
  "allowed_state_files": [
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/prework_provenance_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/execution_log.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/run_closeout_execution_log.json",
    "project_state/gates/run_closeout_result.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/gates/codex_report_auto_summary.json",
    "project_state/gates/execution_report_auto_summary.json",
    "project_state/rounds/round_20260706_scoped_state_metadata_foundation_big_step_v1/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/jobs/*",
    "project_state/user_sessions/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/index.sqlite",
    "project_state/*.db",
    "project_state/domains/*"
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
    "frontend_runtime",
    "production_http_service",
    "scheduler_or_service",
    "database_or_queue",
    "real_user_upload_ingestion",
    "real_sample_analysis_execution",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
    "manual_runner_dispatch",
    "remote_runner_dispatch",
    "workflow_dispatch_trigger",
    "github_actions_dispatch_or_polling",
    "model_api_invocation",
    "git_push_from_local_executor",
    "branch_creation_from_local_executor",
    "pull_request_creation_from_local_executor",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Scoped State Metadata Foundation Big Step v1**.

This is a larger `project_governance` round. It supersedes the unexecuted small roadmap-only decision `decision_20260706_normal_pace_state_taxonomy_roadmap_registration_v1`.

The last accepted engineering baseline fixed Required Audit, status truthfulness, pytest_result, final-check, execution-log, and run-closeout consistency. The next useful larger step is to stop merely registering the state-taxonomy idea and implement the safe first foundation phase.

This round combines three related but bounded tasks:

1. **Roadmap documentation**: add or refresh the normal-pace roadmap and state-domain taxonomy supplement.
2. **Workstream registry**: register `project_state_domain_taxonomy` in `project_state/roadmap/workstreams.json` as a real project-governance workstream, without treating roadmap as execution authority.
3. **Phase A metadata foundation**: add backward-compatible `scope`, `domain`, `mainline`, `role`, and `freshness` metadata support to `state_manifest`, `artifact_index`, and `negative_results` records, plus validation tests and final-check/report support.

This round must not perform Phase B/C/D migrations. It must not create `project_state/domains/*`, move files, delete files, split `negative_results` into domain files, or turn top-level `current_state.json` into a global summary. Those are future rounds.

Accepted target:

- normal-pace roadmap doc exists and replaces rushed MVP framing;
- state taxonomy supplement doc exists and identifies future phases;
- `workstreams.json` contains `project_state_domain_taxonomy` with status no stronger than `ROADMAP_ACCEPTED` unless the registry explicitly marks this round only as the active registration/foundation round;
- `state_manifest.json` records or can emit role/scope/domain/mainline/freshness metadata for current state files while preserving existing consumers;
- `artifact_index.json` records or can be upgraded to include artifact scope/domain/mainline/freshness metadata while preserving existing consumers;
- `negative_results.json` records or can be upgraded to include global/domain scope metadata while preserving existing list-style compatibility;
- validation warns on missing scope metadata for old entries but does not hard-fail legacy records in this first phase;
- final-check/report-summary can surface scoped metadata coverage without requiring full domain migration;
- no `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/domains/*`, Web, database, runner, sample-solving, or tool-integration work is performed;
- pytest, report-summary, execution-log, final-check, and run-closeout pass.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`.

Previous accepted baseline:

- Previous accepted decision: `decision_20260706_required_audit_status_truth_rework_v1`.
- Previous accepted round: `round_20260706_required_audit_status_truth_rework_v1`.
- Previous audit outcome: `ACCEPTED`.
- Previous final gate and run-closeout passed.
- The current small roadmap registration decision was uploaded but not executed; this decision supersedes it to provide a larger, still bounded engineering step.

Why this larger step is justified now:

- `project_state/current_state.json` still contains reverse-solving sample state for `samplereverse`, which is not suitable as a permanent global project summary.
- `project_state/negative_results.json` still mixes reverse-solving failure directions and global policy restrictions.
- `artifact_index.json` and state manifest need scope/freshness metadata before User Solve, Evidence Replay, Web, tool integration, or automation can safely consume state.
- The uploaded long-term plan states the normal sequence should be governance stabilization before User Solve, evidence replay, Web, tools, and automation.
- The state taxonomy supplement identifies Phase A as adding scope/domain/mainline metadata before moving files or creating domain directories.

Existing capabilities that must be reused, not duplicated:

- decision packet authority;
- command-plan authority;
- project_gate;
- state_manifest generation;
- artifact_index;
- negative_results;
- context packet builder;
- workstream registry;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and round archive;
- policy-lint and prompt-consistency foundations;
- User Solve Layer foundation;
- CI/state-gate foundations;
- job lifecycle foundation.

This round must extend those mechanisms. It must not introduce a new state database, second manifest format, second artifact registry, parallel negative-results system, or new workflow engine.

Tool and execution policy:

- Local deterministic Python and pytest are allowed only through command-plan.
- No model API invocation is allowed.
- No GitHub Actions dispatch or polling is allowed.
- No runner dispatch is allowed.
- No Web/frontend runtime is allowed.
- No sample solving or external reverse tool invocation is allowed.
- No cleanup apply, deletion, archive compaction apply, tombstone write, database creation, or database migration is allowed.

## 3. Do Not Do

Do not migrate `project_state/current_state.json`.

Do not modify `project_state/task_packet.json`.

Do not create `project_state/domains/*`.

Do not move files.

Do not delete files.

Do not split `negative_results.json` into domain-specific files yet.

Do not make missing scope metadata a hard failure for legacy entries in this first phase; it should be warning/coverage information unless the current decision explicitly requires new records.

Do not modify `.codex-skills/*`.

Do not modify `.github/workflows/*`.

Do not modify `frontend/*`.

Do not modify `project_state/jobs/*`.

Do not read or commit full `solve_reports/*`.

Do not run sample solving, candidate search, runtime validation, IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools.

Do not implement Web/API runtime, frontend runtime, scheduler, service, queue, database, GitHub App, ChatGPT Action, or remote runner.

Do not run workflow dispatch, agent dispatch, runner dispatch, or auto-iteration.

Do not perform cleanup apply, file deletion, file moving, archive compaction apply, real deletion manifest write, or real tombstone write.

Do not mark the state taxonomy implementation as complete. This round only completes Phase A metadata foundation.

## 4. Files To Inspect

Must inspect:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/roadmap/workstreams.json`
- `project_state/state_manifest.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/current_state.json`
- `.codex-skills/registry.json`
- `reverse_agent/project_state.py`
- `reverse_agent/project_state_manifest.py`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_reports.py`
- `tests/test_project_state.py`
- `tests/test_project_state_manifest.py`
- `tests/test_project_gate.py`
- `tests/test_project_reports.py`

May inspect:

- `project_state/context/current_context_packet.json`
- `README.md`
- `docs/roadmap/*`
- `docs/prompts/README.md`

Do not inspect by default:

- full `solve_reports/*`
- full `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/*`
- archived/cold historical artifacts unless a failing gate explicitly requires them.

## 5. Required Audit

Audit must answer all of the following:

1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `project_governance`?
2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?
3. Does `codex_execution_report.md` match this decision ID and round ID?
4. Does `execution_report.md` semantically match `codex_execution_report.md`?
5. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
6. Does `command_plan.json` carry current decision and round IDs?
7. Does command-plan authorize every executed command?
8. Were any omitted or unauthorized commands executed?
9. Does execution-log record every command-plan required command?
10. Does report-summary match the execution report?
11. Does `final_gate_result.json` pass?
12. Does `run_closeout_result.json` pass if closeout is permitted?
13. Does `workstreams.json` preserve the policy that roadmap entries are not execution authority?
14. Does `workstreams.json` register `project_state_domain_taxonomy` without claiming full implementation completion?
15. Does the normal-pace roadmap document exist and avoid rushed MVP commitments?
16. Does the state taxonomy supplement document exist and distinguish Phase A from future migration phases?
17. Does `state_manifest.json` include or support role/scope/domain/mainline/freshness metadata for state files?
18. Does `artifact_index.json` include or support scope/domain/mainline/freshness metadata for artifact entries?
19. Does `negative_results.json` include or support global/domain scope metadata while preserving legacy compatibility?
20. Do tests cover legacy records without metadata and new scoped records with metadata?
21. Does final-check/report-summary surface scoped metadata coverage without hard-failing old records in this phase?
22. Did the implementation avoid modifying `current_state.json`, `task_packet.json`, `project_state/domains/*`, `.codex-skills/*`, `.github/workflows/*`, `frontend/*`, `solve_reports/*`, and database files?
23. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, file deletion/move, sample solving, and external reverse tools?
24. Did this round reuse existing state_manifest/artifact_index/negative_results/project_gate/report mechanisms rather than creating parallel systems?
25. Does the final conclusion avoid claiming completion of future domain migration phases?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is a larger but bounded governance foundation bundle.

1. Roadmap documentation.
   - Add or update `docs/roadmap/reverse_agent_normal_pace_plan.md`.
   - Add or update `docs/roadmap/project_state_domain_taxonomy_supplement.md`.
   - The docs must define normal phase order and state taxonomy migration phases.
   - The docs must state they are roadmap material, not execution authority.

2. Workstream registry update.
   - Update `project_state/roadmap/workstreams.json`.
   - Preserve `authority_policy.decision_packet_is_execution_authority=true`.
   - Preserve `authority_policy.roadmap_entries_are_not_execution_authority=true`.
   - Register `project_state_domain_taxonomy` with `family=project_governance`.
   - Status may be `ROADMAP_ACCEPTED` for the direction; do not mark full migration as `ACCEPTED`.
   - Include phase list: Phase A metadata, Phase B domain skeleton, Phase C reverse_solving current_state copy, Phase D negative_results split, Phase E top-level current_state summary, Phase F final-check hardening.

3. State manifest Phase A metadata.
   - Extend manifest entry generation or validation to support `role`, `scope`, `domain`, `mainline`, and `freshness`.
   - Preserve old schema consumers.
   - Current top-level files should be classifiable, for example: global state summary, legacy sample state, gate artifact, roadmap registry, context packet, report artifact.
   - Missing metadata on legacy entries should produce warnings/coverage information, not hard failure.

4. Artifact index Phase A metadata.
   - Extend artifact records or upgrade logic to support `scope`, `domain`, `mainline`, `freshness`, `producer`, and `consumed_by` where safe.
   - Do not store bulky artifact contents in the index.
   - Do not require every historical artifact to be fully annotated immediately.
   - Add tests for current artifact metadata and legacy artifact compatibility.

5. Negative results Phase A metadata.
   - Extend negative result record parsing/upgrading to support `scope`, `domain`, `mainline`, `sample_id`, `severity`, `override_allowed`, and `replacement_direction`.
   - Preserve current list-style JSON compatibility.
   - Classify existing entries as best-effort: reverse-solving domain entries vs global policy entries such as `commit full solve_reports directory`.
   - Do not split the file into domain files yet.

6. Gate/report integration.
   - Add final-check or report-summary visibility for scope metadata coverage.
   - The new check should report coverage status and warnings in Phase A.
   - It should not block legacy records unless new current-round records violate this decision's requirements.

7. Tests.
   - Add/update tests for state_manifest scoped entries.
   - Add/update tests for artifact_index scoped entries or upgrade helpers.
   - Add/update tests for negative_results scoped entries and legacy list compatibility.
   - Add/update final-check/report-summary tests for scoped metadata coverage warnings.

Allowed source, state, governance, and documentation changes are limited to the files listed in `decision_contract`.

## 7. Tests

Run only command-plan authorized commands. If this Tests section conflicts with `project_state/gates/command_plan.json`, command-plan wins.

Expected minimum validation set:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_project_state.py tests/test_project_state_manifest.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_scoped_state_metadata_foundation_big_step_v1
```

If command-plan requires broader validation, run the authorized broader set.

Required result artifacts:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260706_scoped_state_metadata_foundation_big_step_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- roadmap docs exist;
- workstream registration exists and is not overstated;
- state_manifest scoped metadata support exists;
- artifact_index scoped metadata support exists;
- negative_results scoped metadata support exists;
- legacy compatibility tests pass;
- no state files are moved or deleted;
- no `project_state/domains/*` is created;
- no forbidden capabilities are used;
- report-summary, execution-log, final-check, and run-closeout pass;
- execution report recommends `ACCEPTED` only with supporting artifacts.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- repository root is not `F:\reverse-agent` or equivalent;
- `project_state/decision_packet.md` cannot be read;
- `.codex-skills/registry.json` does not mark `reverse-agent-iteration` active;
- command-plan cannot be generated or is inconsistent with this decision;
- command-plan omits required validation and no approved fallback exists;
- implementation requires moving, deleting, or archiving files;
- implementation requires creating `project_state/domains/*`;
- implementation requires editing forbidden paths;
- implementation requires workflow files, frontend files, database files, jobs, sample artifacts, cleanup artifacts, or `.codex-skills`;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, file move, or archive apply becomes necessary.

Stop with `REWORK_REQUIRED` if:

- `project_state_domain_taxonomy` is not registered in `workstreams.json`;
- roadmap docs imply they are current execution authority;
- scope/domain/mainline metadata support is absent from state_manifest/artifact_index/negative_results;
- legacy compatibility breaks;
- the implementation modifies `current_state.json`, `task_packet.json`, or creates `project_state/domains/*`;
- the workstream is marked fully implemented without evidence;
- report-summary, execution-log, final-check, or run-closeout fails;
- the report claims `ACCEPTED` without passing final-check and closeout.
