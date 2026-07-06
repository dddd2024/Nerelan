```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_post_final_sync_job_preflight_big_step_v1",
  "round_id": "round_20260706_post_final_sync_job_preflight_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260705_governance_operations_bundle_big_step_v1",
  "follows_last_round_id": "round_20260705_governance_operations_bundle_big_step_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_45_post_final_sync_job_preflight_big_step_v1",
  "primary_goal": "Fix the post-final context packet status drift and advance the engineering control plane in one bounded round: post-final evidence sync gate, READY job materialization/validation, decision-preflight GitHub workflow, and state-gate integration. This is a larger engineering step, but it remains non-dispatching and non-destructive.",
  "command_plan_authority_required": true,
  "accepted_requires_context_packet_post_final_status_sync": true,
  "accepted_requires_post_final_evidence_sync_gate": true,
  "accepted_requires_ready_job_contract_materialized": true,
  "accepted_requires_job_lifecycle_validation_gate": true,
  "accepted_requires_decision_preflight_workflow": true,
  "accepted_requires_state_gate_or_ci_coverage_for_new_preflight": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/decision_preflight.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_gate.py",
    "tests/test_project_jobs.py",
    "tests/test_project_reports.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_workstreams.py",
    "tests/test_post_final_evidence_sync.py",
    "tests/test_decision_preflight.py"
  ],
  "allowed_workflow_files": [
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml"
  ],
  "allowed_documentation_files": [
    "docs/post_final_evidence_sync.md",
    "docs/job_lifecycle_and_decision_preflight.md",
    "docs/github_decision_preflight.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/roadmap/workstreams.json",
    "project_state/jobs/job_20260706_post_final_sync_job_preflight_big_step_v1.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
    "project_state/gates/job_lifecycle_validation_result.json",
    "project_state/gates/job_lifecycle_snapshot.json",
    "project_state/gates/decision_preflight_result.json",
    "project_state/gates/decision_preflight_workflow_readiness.json",
    "project_state/gates/ci_workflow_coverage_result.json",
    "project_state/gates/ci_workflow_readiness_result.json",
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
    "project_state/rounds/round_20260706_post_final_sync_job_preflight_big_step_v1/*"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
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

Implement **Post-Final Evidence Sync + Job Preflight Big Step v1**.

This round intentionally combines one repair and one larger engineering-control-plane advance under a single `engineering_branch` mainline:

1. **Repair: post-final context packet status sync**
   - Fix the observed drift where `project_state/context/current_context_packet.json` can report `auditor_context.final_gate_status=FAILED` after `project_state/gates/final_gate_result.json` has already become `PASSED`.
   - Add explicit post-final evidence semantics so context packets and downstream auditor/planner packets can distinguish pre-final, post-final, stale, and current final-check status.

2. **Engineering advance: non-dispatching job + decision-preflight bridge**
   - Materialize a bounded READY job contract for this round under `project_state/jobs/`.
   - Strengthen job lifecycle validation so local/manual/CI preflight can reason about READY/RUNNING/DONE/AUDITED transitions without dispatching a runner.
   - Add a static `decision-preflight.yml` GitHub workflow and a corresponding local gate that validates decision metadata, skill profile, command-plan presence, post-final context freshness, job contract validity, and forbidden capability boundaries.
   - Integrate the new preflight checks into `state-gate.yml` or existing CI coverage/readiness checks without triggering GitHub Actions from local execution.

Accepted target:

- `current_context_packet.json.auditor_context.final_gate_status` matches the current `final_gate_result.json.gate_status` after final-check/closeout, or explicitly records that it is pre-final/stale with a nonblocking warning.
- A new post-final evidence sync gate exists and is covered by tests.
- A deterministic READY job artifact for this round exists and validates under the job lifecycle validator.
- `decision-preflight.yml` exists and only performs validation; it does not execute agents, dispatch runners, call model APIs, or mutate project state remotely.
- `state-gate.yml` or CI coverage/readiness checks cover the new decision-preflight workflow.
- `final_gate_result.json.gate_status` is `PASSED`.
- `codex_execution_report.md` reports `SUCCESS` and `acceptance_recommendation=ACCEPTED` only if pytest, command-plan, execution-log, post-final sync, job lifecycle validation, CI workflow readiness, and final-check support it.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only.

Current accepted/limited baseline:

- Previous decision: `decision_20260705_governance_operations_bundle_big_step_v1`.
- Previous round: `round_20260705_governance_operations_bundle_big_step_v1`.
- Previous execution report status: `SUCCESS`.
- Previous execution report acceptance recommendation: `ACCEPTED`.
- Manual audit outcome used for this next decision: `ACCEPTED_WITH_LIMITATIONS`, due to context packet status drift after final-check.

Observed repair target:

- `project_state/gates/final_gate_result.json` reports `gate_status=PASSED` for the previous round.
- `project_state/context/current_context_packet.json` was generated before/around final-check and still reports `auditor_context.final_gate_status=FAILED`.
- This is not a reason to redo the previous implementation, but it is a reason to harden post-final state synchronization before more automation depends on the context packet.

Existing capabilities that must not be duplicated:

- `project_gate` hard gates;
- command-plan authority;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and round archive;
- state manifest;
- context packet builder;
- workstream registry;
- CI workflow coverage/readiness foundations;
- local CI parity and CI observation artifacts;
- job lifecycle and non-dispatching runner contract foundations;
- manual-mode orchestrator foundations;
- policy-lint and prompt-consistency foundations;
- retention policy, cleanup-plan, archive index, round compaction dry-run, SQLite read-index readiness, state-hygiene dashboard feed, and lifecycle transition guard.

Existing CI/workflow baseline:

- `.github/workflows/ci.yml` already runs baseline import checks and focused tests.
- `.github/workflows/state-gate.yml` already runs project preflight, command-plan, audit/readiness handoff, CI workflow coverage/readiness, local CI parity, focused tests, and final-check.
- This round should extend those foundations; it must not replace them.

Existing job baseline:

- `reverse_agent/project_jobs.py` already defines job statuses, transitions, runner kinds, non-dispatching validation, deterministic planned job IDs, lock/lease validation, and `validate_jobs_dir`.
- `tests/test_project_jobs.py` already covers non-dispatching contracts, valid/invalid transitions, lock/lease metadata, and backward compatibility.
- This round should move from contract-only foundations to a current READY job artifact and stronger preflight integration; it must not introduce actual runner dispatch.

Roadmap/workstream baseline:

- `project_state/roadmap/workstreams.json` treats roadmap entries as non-authoritative unless selected by `decision_packet.md`.
- The previous active workstream was `governance_operations_bundle`.
- `github_ci_and_state_gate` exists as a roadmap-accepted engineering track.
- `agent_runner_dispatch` remains deferred.
- `tool_integration_ida_ghidra_debugger` remains deferred.
- `reverse_solving_capability_matrix` remains candidate/non-active.

Negative results still apply:

- no old sample-solver blind search;
- no beam/topN/budget expansion;
- no compare_semantics_agree=false frontier;
- no full `solve_reports` scan or commit;
- no repeat of stale transform-trace diagnostics without new runtime evidence.

Artifact freshness policy:

- New or refreshed artifacts must carry `decision_20260706_post_final_sync_job_preflight_big_step_v1` and `round_20260706_post_final_sync_job_preflight_big_step_v1`.
- Historical artifacts may be referenced only as historical/backlog unless explicitly refreshed under this decision.
- Historical sample backlog remains visible and nonblocking.

Command policy:

- Codex or any local executor may run only commands authorized by `project_state/gates/command_plan.json`.
- Omitted commands must not be executed.
- If this Tests section conflicts with command-plan, command-plan wins.

## 3. Do Not Do

Do not treat this as a reverse-solving round. Do not run sample solving, static/dynamic analysis of real binaries, candidate generation, runtime validation, IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools.

Do not implement Web runtime, frontend runtime, production HTTP service, scheduler, service, queue, database migration, or persistent SQLite/DB file.

Do not execute, dispatch, or poll GitHub Actions. Adding or updating workflow YAML is allowed only as static configuration and must be validated locally.

Do not implement `agent-execute.yml`, `audit.yml`, self-hosted runner dispatch, Codex/Trae/Claude/Aider adapter execution, automatic runner dispatch, or auto-iteration.

Do not run cleanup-apply. Do not delete, move, rename, archive, compact, tombstone, or destructively mutate files.

Do not create real deletion manifests or real tombstones under `project_state/deletions/`.

Do not mutate `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `frontend/*`, `solve_reports/*`, `training_materials/local_reverse/*`, `project_state/archives/*`, `project_state/deletions/*`, `project_state/blob_store/*`, `project_state/index.sqlite`, or `project_state/*.db`.

Do not scan full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or unbounded `project_state/rounds/` history.

Do not push, create branches, open PRs, merge, rebase, or perform remote Git mutation from the local executor. This decision packet has already been uploaded separately; execution should remain local and evidence-based.

## 4. Files To Inspect

Default current-state files:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`

Implementation files likely needed:

- `reverse_agent/project_context_builder.py`
- `reverse_agent/project_gate.py`
- `reverse_agent/project_jobs.py`
- `reverse_agent/project_reports.py`
- `reverse_agent/project_state_manifest.py`
- `reverse_agent/project_workstreams.py`
- `tests/test_project_context_builder.py`
- `tests/test_project_gate.py`
- `tests/test_project_jobs.py`
- `tests/test_project_reports.py`
- `tests/test_project_state_manifest.py`
- `tests/test_project_workstreams.py`
- `.github/workflows/ci.yml`
- `.github/workflows/state-gate.yml`

Allowed new files:

- `reverse_agent/post_final_evidence_sync.py`
- `reverse_agent/decision_preflight.py`
- `tests/test_post_final_evidence_sync.py`
- `tests/test_decision_preflight.py`
- `.github/workflows/decision-preflight.yml`
- `docs/post_final_evidence_sync.md`
- `docs/job_lifecycle_and_decision_preflight.md`
- `docs/github_decision_preflight.md`
- `project_state/jobs/job_20260706_post_final_sync_job_preflight_big_step_v1.json`

Avoid unless required by command-plan:

- Full historical `project_state/rounds/*` traversal.
- Full `solve_reports/` traversal.
- Full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report and final audit must explicitly answer all of the following:

1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `engineering_branch`?
2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?
3. Does `codex_execution_report.md` match this decision ID and round ID?
4. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
5. Does `execution_log.json` record every required command from command-plan?
6. Were any omitted or unauthorized commands executed?
7. Was `current_context_packet.json` regenerated or validated after final-check?
8. Does `auditor_context.final_gate_status` match current `final_gate_result.json.gate_status`, or does the context packet explicitly mark itself pre-final/stale?
9. Is there a post-final evidence sync result artifact?
10. Does the post-final sync gate fail or warn on stale context/final-check mismatch?
11. Is the new READY job artifact present under `project_state/jobs/`?
12. Does the job artifact validate with `validate_jobs_dir` or equivalent gate?
13. Does the job artifact keep runner dispatch disabled?
14. Does the job artifact keep remote mutation, model calls, reverse solving, database writes, scheduler, Web mutation, and GitHub Actions dispatch disabled?
15. Are job transitions still backward compatible with existing tests?
16. Does `decision-preflight.yml` exist?
17. Does `decision-preflight.yml` validate decision metadata and command-plan without running agents?
18. Does `decision-preflight.yml` avoid model API calls, runner dispatch, workflow dispatch, external tools, and database writes?
19. Is `state-gate.yml` or CI workflow coverage updated to cover decision-preflight?
20. Did this round avoid implementing `agent-execute.yml`, `audit.yml`, self-hosted runner dispatch, or auto-iteration?
21. Did this round avoid Web/frontend runtime?
22. Did this round avoid sample solving and external reverse tools?
23. Did this round avoid cleanup-apply, real deletion manifests, real tombstones, archives, and destructive mutations?
24. Were `project_state/current_state.json`, `task_packet.json`, `artifact_index.json`, and `negative_results.json` left untouched?
25. Were `.codex-skills/*` left untouched?
26. Were `solve_reports/*` and `training_materials/local_reverse/*` left untouched?
27. Were `project_state/archives/*`, `deletions/*`, `blob_store/*`, and database files left untouched?
28. Did the implementation reuse existing job, CI, command-plan, execution-log, report-summary, final-check, and run-closeout foundations instead of reimplementing them from scratch?
29. Did new artifacts carry the current decision ID and round ID?
30. Did historical sample artifact gaps remain visible but nonblocking?
31. Did final-check pass?
32. Did report-summary match the execution report?
33. Did pytest cover post-final sync, decision-preflight, job lifecycle, project gate, project reports, context builder, and state manifest changes?
34. Did run-closeout archive this round's report, pytest, decision, and manifest if command-plan permits closeout?
35. Did the execution report list all changed files and generated artifacts?
36. Did the final conclusion avoid claiming `ACCEPTED` unless all hard gates and tests support it?

## 6. Implementation Scope

Implement the round as one bounded engineering bundle.

### A. Post-final evidence sync repair

Allowed work:

- Add or extend deterministic code that reads `project_state/gates/final_gate_result.json` and `project_state/context/current_context_packet.json`.
- Add fields such as `final_gate_generated_at`, `context_generated_at`, `context_generated_after_final_gate`, `final_gate_status_source`, `post_final_sync_status`, and `stale_context_detected` if useful.
- Make `project_context_builder` or a new `post_final_evidence_sync` module able to regenerate or validate context packets after final-check.
- Add a `project_gate` command such as `post-final-evidence-sync` that writes `project_state/gates/post_final_evidence_sync_result.json` and optionally `post_final_evidence_sync_snapshot.json`.
- Add tests for matching status, stale pre-final context, missing final-check, and nonblocking historical backlog cases.

Requirements:

- If final-check is current and PASSED, context packet must not keep an unqualified `FAILED` status.
- If context is intentionally pre-final, it must say so explicitly and must not look like current final evidence.
- The fix must preserve the rule that context packet is an index, not a replacement fact source.

### B. READY job contract materialization and lifecycle validation

Allowed work:

- Reuse `reverse_agent/project_jobs.py` rather than replacing it.
- Materialize `project_state/jobs/job_20260706_post_final_sync_job_preflight_big_step_v1.json` with status `READY`.
- Keep runner dispatch disabled.
- Add or extend a `project_gate` command such as `job-lifecycle` or `job-lifecycle-validation` that validates all jobs and writes `project_state/gates/job_lifecycle_validation_result.json` and `job_lifecycle_snapshot.json`.
- Enforce at most one active/running job unless explicitly authorized by a future decision.
- Keep lock/lease validation deterministic and non-mutating unless writing the planned job artifact itself.

Requirements:

- Job contracts must remain backward compatible with existing tests.
- The READY job must reference this decision and round.
- Job validation must not start execution.

### C. Decision-preflight local gate and GitHub workflow

Allowed work:

- Add `reverse_agent/decision_preflight.py` or extend `project_gate` with a `decision-preflight` command.
- Add `.github/workflows/decision-preflight.yml` as a validation-only workflow.
- The workflow may support `workflow_dispatch` inputs such as `decision_id`, `round_id`, and `branch`, but it must only validate; it must not execute agents or mutate remote state.
- Add `project_state/gates/decision_preflight_result.json` and `decision_preflight_workflow_readiness.json` artifacts.
- Update `state-gate.yml` and/or CI workflow readiness checks to include the new preflight workflow.

Requirements:

- Preflight must validate `decision_meta`, active skill profiles, command-plan presence/consistency, context post-final sync status, job contract validity, and forbidden capability boundaries.
- It must not call model APIs.
- It must not trigger other workflows.
- It must not dispatch any runner.

### D. Reports, command-plan, execution-log, final-check, closeout

Allowed work:

- Update command-plan generation so all required commands for this round are represented.
- Update execution-log/report-summary/final-check only as needed to recognize new artifacts and commands.
- Update run-closeout to archive this round if command-plan permits.

Requirements:

- Preserve existing report-summary and final-check semantics.
- Preserve the previous governance rule that historical sample backlog is visible but nonblocking.
- Preserve command-plan as command authority.

## 7. Tests

The final `project_state/pytest_result.txt` must include startup checks and all command-plan-authorized commands actually run.

Required startup checks:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
```

Required command/gate sequence, subject to command-plan authority:

```powershell
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_state doctor --state-dir project_state
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate job-lifecycle --state-dir project_state
python -m reverse_agent.project_gate decision-preflight --state-dir project_state
python -m reverse_agent.project_gate ci-workflow-coverage --state-dir project_state
python -m reverse_agent.project_gate ci-workflow-readiness --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate prework-provenance --state-dir project_state
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_jobs.py tests/test_project_context_builder.py tests/test_project_state_manifest.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_workstreams.py -q
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_post_final_sync_job_preflight_big_step_v1
```

If command names differ after implementation, command-plan must contain the actual authorized command names and explain the mapping.

Acceptance requires:

- All pytest commands pass.
- `post_final_evidence_sync_result.json` reports `PASSED` or equivalent success.
- `job_lifecycle_validation_result.json` reports `PASSED`.
- `decision_preflight_result.json` reports `PASSED`.
- CI workflow readiness/coverage recognizes `decision-preflight.yml`.
- `final_gate_result.json.gate_status` is `PASSED`.
- `codex_execution_report.md` and `pytest_result.txt` are consistent.

## 8. Stop Conditions

Stop and mark `BLOCKED` or `REWORK_REQUIRED` if any of the following occurs:

- `decision_meta` is missing, invalid, not `APPROVED`, or mismatched with report/pytest/final-check.
- `.codex-skills/registry.json` does not contain `reverse-agent-iteration@v2` as active.
- Command-plan cannot be generated or does not authorize required commands.
- Any command outside command-plan is executed.
- `current_context_packet.json` remains unqualified `FAILED` while current `final_gate_result.json` is `PASSED`.
- Post-final sync cannot determine whether context packet is pre-final, stale, or current.
- READY job artifact cannot validate.
- Any job or workflow starts a runner, dispatches an agent, triggers GitHub Actions, calls a model API, or performs remote mutation.
- `.github/workflows/decision-preflight.yml` executes anything beyond validation.
- Web/frontend runtime, database file, scheduler, service, queue, sample solving, external reverse tools, cleanup-apply, deletion, archive mutation, tombstone, or database migration is introduced.
- Forbidden paths are modified.
- `pytest_result.txt`, `execution_log.json`, report-summary, or final-check is missing or inconsistent.
- `final_gate_result.json.gate_status` is not `PASSED`.
- The implementation repeats existing job/CI/gate capabilities from scratch instead of extending them.
- The round drifts into reverse_solving, tool_integration, frontend runtime, database indexing apply, or runner dispatch.
