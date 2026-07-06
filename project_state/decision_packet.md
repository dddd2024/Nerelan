```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_normal_pace_state_taxonomy_roadmap_registration_v1",
  "round_id": "round_20260706_normal_pace_state_taxonomy_roadmap_registration_v1",
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
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_50_normal_pace_state_taxonomy_roadmap_registration_v1",
  "primary_goal": "Register the normal-pace roadmap and project_state domain taxonomy workstream before any implementation of state restructuring. This is a roadmap/workstream registration round, not a project_state migration round.",
  "command_plan_authority_required": true,
  "accepted_requires_workstream_registry_current": true,
  "accepted_requires_new_direction_registered_before_execution": true,
  "accepted_requires_docs_for_normal_pace_and_state_taxonomy": true,
  "accepted_requires_no_state_file_migration": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [],
  "allowed_documentation_files": [
    "docs/roadmap/reverse_agent_normal_pace_plan.md",
    "docs/roadmap/project_state_domain_taxonomy_supplement.md"
  ],
  "allowed_governance_files": [
    "project_state/roadmap/workstreams.json"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
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
    "project_state/rounds/round_20260706_normal_pace_state_taxonomy_roadmap_registration_v1/*"
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

Implement **Normal Pace + State Taxonomy Roadmap Registration v1**.

The last accepted engineering round fixed the Required Audit, report status, pytest_result, final-check, execution-log, and run-closeout consistency chain. The project can now leave repeated closeout rework and return to normal governance planning.

This round must not implement a state migration. It must only register the next long-term direction in roadmap/workstreams and documentation:

1. Replace the old short-deadline MVP framing with a normal engineering cadence: governance stabilization first, then User Solve Layer, evidence/replay, sample inventory/capability matrix, Web workbench, tool providers, and automation.
2. Register `project_state_domain_taxonomy` as a project-governance workstream before any `project_state/` restructuring begins.
3. Add or refresh two roadmap documents:
   - `docs/roadmap/reverse_agent_normal_pace_plan.md`
   - `docs/roadmap/project_state_domain_taxonomy_supplement.md`
4. Update `project_state/roadmap/workstreams.json` so the new workstream exists as `CANDIDATE` or `ROADMAP_ACCEPTED`, not `ACTIVE_ROUND` unless this exact decision explicitly marks it as the current roadmap-registration round.
5. Preserve execution authority: roadmap entries remain planning facts; only `project_state/decision_packet.md` controls the current execution round.

Accepted target:

- normal-pace roadmap doc exists and clearly states the phase order;
- state taxonomy supplement doc exists and clearly states that it is not the current execution authority;
- `workstreams.json` contains a `project_state_domain_taxonomy` workstream with lifecycle status no stronger than `ROADMAP_ACCEPTED` unless justified by this registration decision;
- `workstreams.json` continues to state that `decision_packet.md` is execution authority and roadmap entries are not execution authority;
- no `project_state/current_state.json`, `artifact_index.json`, `negative_results.json`, `project_state/domains/*`, Web, database, runner, sample-solving, or tool-integration implementation is performed;
- final-check and run-closeout pass.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`.

Previous accepted baseline:

- Previous decision: `decision_20260706_required_audit_status_truth_rework_v1`.
- Previous round: `round_20260706_required_audit_status_truth_rework_v1`.
- Previous audit outcome: `ACCEPTED`.
- The previous round had `codex_execution_report.md` status `SUCCESS` and acceptance recommendation `ACCEPTED`.
- `pytest_result.txt` passed and recorded final-check/run-closeout success.
- `final_gate_result.json` passed with no active warnings or blocking reasons.
- `run_closeout_result.json` passed and archived the round.

Why this round is roadmap-only:

- `project_state/current_state.json` still carries reverse-solving sample state for `samplereverse`, not a global project summary.
- `project_state/negative_results.json` still mixes reverse-solving failure directions with global policy restrictions.
- `project_state/roadmap/workstreams.json` already states that roadmap entries are not execution authority, but it does not yet register the state-domain taxonomy direction as a proper workstream.
- A new direction must enter roadmap/workstream before becoming an implementation round.

Existing capabilities that must not be duplicated:

- decision packet authority;
- command-plan authority;
- project_gate;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and round archive;
- state manifest;
- context packet builder;
- workstream registry;
- negative_results;
- artifact_index;
- policy-lint and prompt-consistency foundations;
- User Solve Layer foundation;
- CI/state-gate foundations;
- job lifecycle foundation;
- manual-mode Web orchestrator foundation.

This round must only connect the next direction to the existing roadmap mechanism. It must not introduce a new planner, new state store, new database, new runner, new Web runtime, or new execution workflow.

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

Do not modify `project_state/artifact_index.json`.

Do not modify `project_state/negative_results.json`.

Do not create `project_state/domains/*` yet.

Do not split negative_results yet.

Do not add scope/domain/mainline metadata to real state entries yet.

Do not modify `.codex-skills/*`.

Do not modify `.github/workflows/*`.

Do not modify `frontend/*`.

Do not modify `project_state/jobs/*`.

Do not read or commit full `solve_reports/*`.

Do not run sample solving, candidate search, runtime validation, IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools.

Do not implement Web/API runtime, frontend runtime, scheduler, service, queue, database, GitHub App, ChatGPT Action, or remote runner.

Do not run workflow dispatch, agent dispatch, runner dispatch, or auto-iteration.

Do not perform cleanup apply, file deletion, file moving, archive compaction apply, real deletion manifest write, or real tombstone write.

Do not mark a future workstream as implementation-complete. This round only registers planning direction and readiness gates.

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
- `project_state/current_state.json`
- `project_state/negative_results.json`
- `project_state/artifact_index.json`
- `.codex-skills/registry.json`

May inspect:

- `project_state/context/current_context_packet.json`
- `project_state/state_manifest.json`
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
14. Does `workstreams.json` register `project_state_domain_taxonomy` without pretending implementation is complete?
15. Does the normal-pace roadmap document exist and avoid short-deadline MVP commitments?
16. Does the state taxonomy supplement document exist and clearly state it is not a current execution authority?
17. Did the implementation avoid modifying `current_state.json`, `artifact_index.json`, `negative_results.json`, `project_state/domains/*`, `.codex-skills/*`, `.github/workflows/*`, `frontend/*`, `solve_reports/*`, and database files?
18. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?
19. Did this round reuse existing roadmap/workstream/final-check/report mechanisms rather than creating a parallel planning system?
20. Does the final conclusion avoid claiming implementation of the future state-taxonomy migration?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is limited to roadmap registration and documentation.

1. Add or update `docs/roadmap/reverse_agent_normal_pace_plan.md`.
   - Remove the assumption of a rushed 10-day MVP.
   - Define the sequence: governance stabilization, User Solve contract, safe static solving, evidence/replay, sample inventory/capability matrix, Web workbench, tool providers, and automation.
   - State explicitly that Web should not lead the architecture.
   - State explicitly that candidate results are not verified answers.

2. Add or update `docs/roadmap/project_state_domain_taxonomy_supplement.md`.
   - Explain why top-level `current_state.json` and `negative_results.json` need domain ownership metadata in future rounds.
   - State that no state migration is performed in this round.
   - Define future phases only as roadmap material: metadata first, domain skeleton second, reverse_solving state copy later, negative_results split later, final-check hardening later.

3. Update `project_state/roadmap/workstreams.json`.
   - Preserve `authority_policy.decision_packet_is_execution_authority=true`.
   - Preserve `authority_policy.roadmap_entries_are_not_execution_authority=true`.
   - Add `project_state_domain_taxonomy` as a `project_governance` workstream.
   - Status should be `CANDIDATE` or `ROADMAP_ACCEPTED`; do not mark the implementation as `ACCEPTED`.
   - Include clear non-goals: no database replacement, no file moving, no deletion, no sample solving, no Web/tool/runner work.

4. Keep all real state-migration files unchanged.
   - No edits to `project_state/current_state.json`.
   - No edits to `project_state/artifact_index.json`.
   - No edits to `project_state/negative_results.json`.
   - No creation of `project_state/domains/*`.

5. Run only command-plan authorized validation.
   - Since this is documentation/roadmap governance, tests may be lightweight if command-plan selects a lightweight profile.
   - Still produce pytest_result, execution report, execution-log, final-check, and closeout artifacts.

Allowed documentation/governance changes are limited to the files listed in `decision_contract`.

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
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_normal_pace_state_taxonomy_roadmap_registration_v1
```

If command-plan requires pytest, run only the authorized subset. Suggested candidates:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state_manifest.py -q
```

Required result artifacts:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/run_closeout_result.json`
- `project_state/rounds/round_20260706_normal_pace_state_taxonomy_roadmap_registration_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- workstream registration is present and not overstated;
- docs exist and clearly distinguish roadmap from execution authority;
- no state migration files are modified;
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
- roadmap registration requires modifying forbidden paths;
- any state migration becomes necessary;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, or archive apply becomes necessary.

Stop with `REWORK_REQUIRED` if:

- `project_state_domain_taxonomy` is not registered in `workstreams.json`;
- the roadmap docs imply they are current execution authority;
- the implementation modifies `current_state.json`, `artifact_index.json`, `negative_results.json`, or creates `project_state/domains/*`;
- the workstream is marked implementation-complete without evidence;
- report-summary, execution-log, final-check, or run-closeout fails;
- the report claims `ACCEPTED` without passing final-check and closeout.
