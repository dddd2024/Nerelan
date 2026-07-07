```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260707_next_step_roadmap_registration_v1",
  "round_id": "round_20260707_next_step_roadmap_registration_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_scoped_state_metadata_foundation_big_step_v1",
  "follows_last_round_id": "round_20260706_scoped_state_metadata_foundation_big_step_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_51_next_step_roadmap_registration_v1",
  "primary_goal": "Register and audit the already uploaded next-step roadmap document as project-governance roadmap material without implementing Phase A.1, Phase B, or any runtime capability.",
  "command_plan_authority_required": true,
  "accepted_requires_next_step_doc_present": true,
  "accepted_requires_doc_marked_roadmap_not_execution_authority": true,
  "accepted_requires_no_phase_a1_implementation": true,
  "accepted_requires_no_phase_b_domain_skeleton": true,
  "accepted_requires_no_file_moves_or_deletes": true,
  "accepted_requires_no_domain_directory_creation": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "accepted_requires_no_local_git_commit_or_push": true,
  "allowed_source_files": [],
  "allowed_test_files": [],
  "allowed_documentation_files": [
    "docs/roadmap/next_step_after_scoped_metadata_foundation.md"
  ],
  "allowed_governance_files": [],
  "allowed_state_files": [],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
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
    "project_state/rounds/round_20260707_next_step_roadmap_registration_v1/*"
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
    "project_state/domains/*",
    "reverse_agent/*",
    "tests/*"
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
    "git_commit_from_local_executor",
    "git_push_from_local_executor",
    "branch_creation_from_local_executor",
    "pull_request_creation_from_local_executor",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Register and audit **Next Step After Scoped Metadata Foundation** as roadmap material.

The target document is:

```text
docs/roadmap/next_step_after_scoped_metadata_foundation.md
```

This round exists because the roadmap document was uploaded to GitHub through an explicit user request, but it has not yet been consumed by a normal `decision_packet.md` / `command_plan.json` / `execution_log.json` / `final-check` / `run-closeout` project-governance round.

This round must only verify and register the roadmap document as project-governance evidence. It must not implement Phase A.1, must not create Phase B domain skeletons, and must not open any reverse-solving, Web, database, runner, workflow, or external-tool capability.

Accepted target:

- `docs/roadmap/next_step_after_scoped_metadata_foundation.md` exists in the working tree after the executor syncs to the GitHub state that contains it;
- the document clearly says it is roadmap material and not execution authority;
- the document recommends Phase A.1 before Phase B without claiming either phase is implemented;
- the document preserves the rule that only `project_state/decision_packet.md` is execution authority and only `project_state/gates/command_plan.json` is command authority;
- no source files, test files, `current_state.json`, `task_packet.json`, `project_state/domains/*`, database files, Web/frontend files, workflow files, solve reports, or training materials are modified;
- no local executor commit, push, branch, PR, workflow dispatch, runner dispatch, sample solving, external reverse tool, database, cleanup apply, file move, or file deletion is performed;
- pytest, report-summary, execution-log, final-check, and run-closeout pass under command-plan authority.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`.

The previous active decision was:

```text
decision_20260706_scoped_state_metadata_foundation_big_step_v1
```

The previous active round was:

```text
round_20260706_scoped_state_metadata_foundation_big_step_v1
```

That round has current evidence of completion:

- `project_state/codex_execution_report.md` reports `status=SUCCESS` and `acceptance_recommendation=ACCEPTED` for the previous scoped metadata foundation round;
- `project_state/pytest_result.txt` reports `status=PASSED`;
- `project_state/gates/final_gate_result.json` reports `gate_status=PASSED`;
- `project_state/gates/run_closeout_result.json` reports `closeout_status=PASSED`.

The external audit conclusion for the previous round was `ACCEPTED_WITH_LIMITATIONS`, because Phase A source-level scoped metadata support and tests were accepted, but full on-disk scoped metadata visibility in all current artifacts and the later Phase B/C/D/E/F migrations were not accepted as complete.

The uploaded roadmap document records a safe next-step sequence after that limitation:

```text
Phase A.1 — materialize scoped metadata visibility in on-disk governance artifacts.
Phase B — create empty domain skeletons with README/manifests only.
Phase C — copy reverse-solving current_state into reverse_solving domain scope.
Phase D — split negative_results with compatibility shim.
Phase E — convert top-level current_state into global summary.
Phase F — harden final-check for new scope metadata regressions.
```

This round only registers and audits that roadmap note. It does not execute Phase A.1 or Phase B.

`task_packet.json` remains background only and must not control this round. It is associated with reverse-solving sample state and is not current execution authority.

`current_state.json` still contains reverse-solving sample state and must not be turned into a global project summary in this round.

`artifact_index.json` and `state_manifest.json` may still contain legacy or missing scoped metadata warnings. This round does not fix those warnings; Phase A.1 is a future decision.

`negative_results.json` contains historical reverse-solving failed directions and global policy restrictions. This round does not split or migrate it.

The workstream registry exists and records that roadmap entries are not execution authority. It must not be treated as permission to skip the current decision packet or command plan.

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

Tool and execution policy:

- Local deterministic Python and pytest are allowed only through command-plan.
- No model API invocation is allowed.
- No GitHub Actions dispatch or polling is allowed.
- No runner dispatch is allowed.
- No Web/frontend runtime is allowed.
- No sample solving or external reverse tool invocation is allowed.
- No cleanup apply, deletion, archive compaction apply, tombstone write, database creation, or database migration is allowed.
- No local executor commit, push, branch, PR, merge, or rebase is allowed.

This round must not repeat Phase A implementation. It only verifies the next-step roadmap artifact and produces audit evidence.

## 3. Do Not Do

Do not implement Phase A.1.

Do not create `project_state/domains/*`.

Do not implement Phase B domain skeletons.

Do not copy or migrate `project_state/current_state.json`.

Do not modify `project_state/task_packet.json`.

Do not split `project_state/negative_results.json`.

Do not convert top-level `current_state.json` into a global project summary.

Do not modify source files under `reverse_agent/*`.

Do not modify tests under `tests/*`.

Do not modify `.codex-skills/*`.

Do not modify `.github/workflows/*`.

Do not modify `frontend/*`.

Do not modify `solve_reports/*`.

Do not modify `training_materials/local_reverse/*`.

Do not create, update, or migrate any SQLite/database file.

Do not run Web/frontend runtime.

Do not run sample solving, candidate search, runtime validation, binary parsing, unpacking, debugger, emulator, IDA, Ghidra, OllyDbg, radare2, MCP, or any external reverse-analysis tool.

Do not perform cleanup apply, deletion, file move, archive compaction apply, tombstone write, or deletion manifest write.

Do not run GitHub Actions dispatch or polling.

Do not dispatch local, remote, or automatic runners.

Do not invoke any model API.

Do not run `git commit`, `git push`, `git branch`, `git checkout -b`, `git merge`, `git rebase`, create a PR, or push from the local executor.

Do not claim `ACCEPTED` if `pytest_result`, `report-summary`, `execution-log`, `final-check`, or `run-closeout` fails.

Do not claim that Phase A.1, Phase B, Phase C, Phase D, Phase E, or Phase F is complete.

## 4. Files To Inspect

Required files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
docs/roadmap/next_step_after_scoped_metadata_foundation.md
docs/roadmap/project_state_domain_taxonomy_supplement.md
docs/roadmap/reverse_agent_normal_pace_plan.md
project_state/roadmap/workstreams.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
```

Optional files:

```text
project_state/context/current_context_packet.json
project_state/state_manifest.json
project_state/gates/startup_snapshot.json
project_state/gates/gate_profile_plan.json
project_state/gates/preflight_result.json
project_state/gates/round_baseline.json
project_state/gates/round_close_snapshot.json
project_state/gates/round_delta_summary.json
project_state/rounds/round_20260706_scoped_state_metadata_foundation_big_step_v1/round_manifest.json
```

Do not read full `solve_reports/`.

Do not read full `PROJECT_PROGRESS_LOG.txt` unless a required gate explicitly references it.

Do not inspect binaries or training samples in this round.

## 5. Required Audit

The execution report must answer all of the following:

1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `project_governance`?
2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?
3. Does the report match this decision ID and round ID?
4. Does `execution_report.md` semantically match `codex_execution_report.md`?
5. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
6. Does `command_plan.json` carry the current decision and round IDs?
7. Does command-plan authorize every executed command?
8. Were any omitted or unauthorized commands executed?
9. Does `execution_log.json` record every command-plan required command?
10. Does report-summary match the execution report?
11. Does `final_gate_result.json` pass?
12. Does `run_closeout_result.json` pass?
13. Does `docs/roadmap/next_step_after_scoped_metadata_foundation.md` exist?
14. Does that document explicitly state it is roadmap material and not execution authority?
15. Does that document preserve `decision_packet.md` as execution authority and `command_plan.json` as command authority?
16. Does that document recommend Phase A.1 before Phase B without claiming either is implemented?
17. Does this round avoid implementing Phase A.1?
18. Does this round avoid creating `project_state/domains/*`?
19. Does this round avoid modifying `current_state.json` and `task_packet.json`?
20. Does this round avoid splitting or migrating `negative_results.json`?
21. Does this round avoid modifying source files and test files?
22. Does this round avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, deletion, file move, sample solving, and external reverse tools?
23. Does this round avoid local `git commit`, `git push`, branch creation, PR creation, merge, and rebase?
24. Does the report avoid claiming completion of Phase A.1, Phase B, Phase C, Phase D, Phase E, or Phase F?
25. Does the final conclusion fit one of `ACCEPTED`, `ACCEPTED_WITH_LIMITATIONS`, `REWORK_REQUIRED`, or `BLOCKED`?

The audit conclusion must be exactly one of:

```text
ACCEPTED
ACCEPTED_WITH_LIMITATIONS
REWORK_REQUIRED
BLOCKED
```

Use `ACCEPTED` only if all required gates pass and the document is properly registered as roadmap material.

Use `ACCEPTED_WITH_LIMITATIONS` only if the document exists and all hard gates pass, but there is a clearly documented non-blocking limitation, such as local working tree sync lag that does not affect the GitHub artifact.

Use `REWORK_REQUIRED` if any required gate fails, if report status is inconsistent, if an unauthorized command was executed, if the round implements Phase A.1 or Phase B, or if forbidden paths are modified.

Use `BLOCKED` if the local executor cannot see the uploaded document because the local workspace has not been synced to GitHub, or if command-plan/preflight cannot be generated.

## 6. Implementation Scope

This is a documentation-registration and audit round only.

Allowed substantive artifact:

```text
docs/roadmap/next_step_after_scoped_metadata_foundation.md
```

The executor may read and validate this file. It may not substantially rewrite it unless command-plan and final-check explicitly allow the documentation path and the change is limited to clarifying roadmap-not-authority language.

Allowed generated artifacts:

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/startup_snapshot.json
project_state/gates/gate_profile_plan.json
project_state/gates/command_plan.json
project_state/gates/preflight_result.json
project_state/gates/prework_provenance_result.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_execution_log.json
project_state/gates/run_closeout_result.json
project_state/gates/round_baseline.json
project_state/gates/round_close_snapshot.json
project_state/gates/round_delta_summary.json
project_state/gates/codex_report_auto_summary.json
project_state/gates/execution_report_auto_summary.json
project_state/rounds/round_20260707_next_step_roadmap_registration_v1/*
```

No source files or test files may be modified.

No state migration may be performed.

No domain directory may be created.

No local Git commit or push may be performed by the executor.

This round should be small, auditable, and reversible. It should only close the governance gap created by the out-of-band user-requested roadmap upload.

## 7. Tests

Run only commands authorized by `project_state/gates/command_plan.json`.

Expected minimum validation:

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
python -m pytest tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260707_next_step_roadmap_registration_v1
```

If command-plan requires broader tests, command-plan wins.

The executor must write:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260707_next_step_roadmap_registration_v1/round_manifest.json
```

`pytest_result.txt` must include the executed command transcript and a summary block with the current decision ID, round ID, report ID, and status.

`codex_execution_report.md` and `execution_report.md` must not claim acceptance unless the tests and gates support it.

## 8. Stop Conditions

Stop with `BLOCKED` if:

- repository root is not `F:\reverse-agent` or equivalent;
- `project_state/decision_packet.md` cannot be read;
- `.codex-skills/registry.json` does not mark `reverse-agent-iteration@v2` active;
- `docs/roadmap/next_step_after_scoped_metadata_foundation.md` is missing from the local working tree after sync;
- command-plan cannot be generated;
- preflight cannot be generated;
- the work requires GitHub Actions dispatch, runner dispatch, Web runtime, database work, sample solving, external reverse tools, cleanup apply, file move, file deletion, or local Git commit/push.

Stop with `REWORK_REQUIRED` if:

- report status and audit conclusion disagree;
- `pytest_result.txt` is missing or failed;
- `report-summary` fails;
- `execution-log` fails or omits required commands;
- `final-check` fails;
- `run-closeout` fails;
- an omitted or unauthorized command was executed;
- source files or test files were modified;
- `current_state.json` or `task_packet.json` was modified;
- `negative_results.json` was split or migrated;
- `project_state/domains/*` was created;
- the round implements Phase A.1 or Phase B instead of registering the roadmap;
- local executor runs `git commit`, `git push`, branch creation, PR creation, merge, or rebase;
- the report claims `ACCEPTED` without passing final-check and run-closeout.

The correct next decision after this registration round, if accepted, is still expected to be a separate Phase A.1 decision to materialize scoped metadata visibility in on-disk governance artifacts.
