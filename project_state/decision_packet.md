```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260706_post_final_timestamp_precision_hardening_v1",
  "round_id": "round_20260706_post_final_timestamp_precision_hardening_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260706_post_final_sync_job_preflight_big_step_v1",
  "follows_last_round_id": "round_20260706_post_final_sync_job_preflight_big_step_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_46_post_final_timestamp_precision_hardening_v1",
  "primary_goal": "Harden post-final sync freshness semantics so context/final-check synchronization is based on precise timestamps plus source artifact identity, not rounded timestamp ordering alone.",
  "command_plan_authority_required": true,
  "accepted_requires_final_gate_passed": true,
  "accepted_requires_post_final_sync_warning_removed_or_reclassified": true,
  "accepted_requires_source_artifact_identity_checks": true,
  "accepted_requires_context_packet_precise_sync_fields": true,
  "accepted_requires_final_check_coverage_for_timestamp_precision": true,
  "accepted_requires_no_runner_or_workflow_dispatch": true,
  "accepted_requires_no_sample_solving": true,
  "allowed_source_files": [
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_reports.py",
    "tests/test_post_final_evidence_sync.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_gate.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/post_final_evidence_sync.md",
    "docs/post_final_timestamp_precision.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/context/current_context_packet.json",
    "project_state/state_manifest.json",
    "project_state/gates/post_final_evidence_sync_result.json",
    "project_state/gates/post_final_evidence_sync_snapshot.json",
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
    "project_state/rounds/round_20260706_post_final_timestamp_precision_hardening_v1/*"
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
    "project_state/roadmap/workstreams.json",
    "project_state/user_sessions/*",
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

Implement **Post-Final Timestamp Precision Hardening v1**.

This round is a narrow `engineering_branch` repair following the previous audit outcome `ACCEPTED_WITH_LIMITATIONS`.

The previous round successfully fixed the substantive context/final-check drift: `final_gate_result.json.gate_status` and `current_context_packet.json.auditor_context.final_gate_status` both reached `PASSED`. The remaining limitation is a timestamp-ordering warning where the post-final sync gate can still report that the context packet is current while also warning that the context packet timestamp appears before the final gate timestamp. The next step is to make that freshness judgement precise, deterministic, and audit-friendly.

Accepted target:

- Post-final sync compares precise parsed timestamps, not string-truncated timestamps.
- Post-final sync records source artifact identity for the final gate and context packet, including SHA-256 or equivalent digest fields.
- `current_context_packet.json.auditor_context` records enough fields to explain why the context is current even when `generated_at` values share the same second or differ only by microseconds.
- A context packet that reads the current final gate artifact by digest/ID should not produce an active warning merely because `context_generated_at` is rounded to seconds while `final_gate_generated_at` includes fractional seconds.
- A genuinely stale context packet still produces a warning or failure.
- `final_gate_result.json.gate_status` is `PASSED`.
- `codex_execution_report.md` may recommend `ACCEPTED` only if pytest, command-plan, execution-log, post-final sync, report-summary, and final-check support it.

## 2. Current Evidence

Current task authority is this `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still contains older sample-solving context; it must not control this engineering round.

Current audited baseline:

- Previous decision: `decision_20260706_post_final_sync_job_preflight_big_step_v1`.
- Previous round: `round_20260706_post_final_sync_job_preflight_big_step_v1`.
- Previous execution report status: `SUCCESS`.
- Previous execution report acceptance recommendation: `ACCEPTED`.
- Manual audit outcome: `ACCEPTED_WITH_LIMITATIONS`.

Evidence from previous accepted-limited round:

- `project_state/gates/final_gate_result.json` reports `gate_status=PASSED`, no blocking reasons, and no active warnings.
- `project_state/context/current_context_packet.json` reports `auditor_context.final_gate_status=PASSED`, `final_gate_current=true`, and `post_final_sync_status=CURRENT_POST_FINAL_SYNCED`.
- `project_state/gates/post_final_evidence_sync_result.json` reports `gate_status=PASSED` and `sync_status=PASSED`.
- The remaining limitation is a nonblocking warning: context packet is current but was generated before the final gate timestamp.
- The likely cause is timestamp precision/rounding, because context `generated_at` can be second-granularity while final gate `generated_at` can carry fractional seconds.

Existing capabilities that must not be duplicated:

- `project_gate` hard gates;
- command-plan authority;
- execution-log synthesis;
- report-summary synthesis;
- final-check;
- run-closeout and round archive;
- state manifest;
- context packet builder;
- post-final evidence sync gate;
- decision-preflight gate and workflow;
- job lifecycle and non-dispatching job contract foundations;
- CI workflow coverage/readiness foundations;
- policy-lint and prompt-consistency foundations;
- retention policy, cleanup-plan, archive index, round compaction dry-run, SQLite read-index readiness, state-hygiene dashboard feed, and lifecycle transition guard.

This round must strengthen the existing post-final sync mechanism. It must not create a parallel freshness system, a new job runner, a new workflow dispatcher, or a database-backed state model.

Artifact freshness policy:

- Current evidence must use current decision/round/report IDs.
- Historical sample artifacts and missing sample artifacts are nonblocking for this engineering round.
- Stale historical governance artifacts may be referenced only as historical/nonblocking, not as current proof.

Tool and execution policy:

- Local deterministic Python and pytest are allowed only through command-plan.
- No model API invocation is allowed.
- No GitHub Actions dispatch or polling is allowed.
- No runner dispatch is allowed.
- No Web/frontend runtime is allowed.
- No sample solving or external reverse tool invocation is allowed.
- No cleanup apply, deletion, archive compaction apply, tombstone write, database creation, or database migration is allowed.

## 3. Do Not Do

Do not modify `.codex-skills/*`.

Do not modify `.github/workflows/*` in this round. The previous round already added decision-preflight workflow support; this round is about timestamp/freshness semantics in local gates and context artifacts.

Do not modify `frontend/*`.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not modify `project_state/jobs/*`; the previous READY job work is already accepted as a foundation and must not be reopened here.

Do not modify `project_state/roadmap/workstreams.json`; roadmap refresh is not part of this narrow repair.

Do not read or commit full `solve_reports/*`.

Do not run sample solving, binary parsing, unpacking, candidate search, runtime validation, IDA, Ghidra, OllyDbg, debugger, emulator, MCP, or external reverse tools.

Do not implement Web/API runtime, frontend runtime, scheduler, service, queue, database, GitHub App, ChatGPT Action, or remote runner.

Do not run workflow dispatch, agent dispatch, runner dispatch, or auto-iteration.

Do not perform cleanup apply, file deletion, file moving, archive compaction apply, real deletion manifest write, or real tombstone write.

Do not mark the round `ACCEPTED` if the timestamp warning remains active without an explicit downgrade/reclassification rationale and final-check support.

## 4. Files To Inspect

Must inspect:

- `project_state/decision_packet.md`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/pytest_result.txt`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/post_final_evidence_sync_snapshot.json`
- `project_state/context/current_context_packet.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/execution_log.json`
- `.codex-skills/registry.json`
- `reverse_agent/post_final_evidence_sync.py`
- `reverse_agent/project_context_builder.py`
- `reverse_agent/project_gate.py`
- `tests/test_post_final_evidence_sync.py`
- `tests/test_project_context_builder.py`
- `tests/test_project_gate.py`

May inspect if needed:

- `reverse_agent/project_state_manifest.py`
- `reverse_agent/project_reports.py`
- `tests/test_project_state_manifest.py`
- `tests/test_project_reports.py`
- `docs/post_final_evidence_sync.md`

Do not inspect by default:

- full `solve_reports/*`
- full `PROJECT_PROGRESS_LOG.txt`
- `training_materials/local_reverse/*`
- archived/cold historical artifacts unless explicitly required by a failing gate.

## 5. Required Audit

Audit must answer all of the following:

1. Is `decision_meta` present, valid, `APPROVED`, and on legal mainline `engineering_branch`?
2. Does `skill_profiles` use only active skills from `.codex-skills/registry.json`?
3. Does `codex_execution_report.md` match this decision ID and round ID?
4. Does `pytest_result.txt` match this decision ID, round ID, and report ID?
5. Does `execution_log.json` record every required command from command-plan?
6. Were any omitted or unauthorized commands executed?
7. Did the implementation avoid modifying forbidden paths?
8. Did the implementation avoid Web/frontend runtime, runner dispatch, workflow dispatch, model API invocation, database writes, cleanup apply, sample solving, and external reverse tools?
9. Does post-final sync preserve and compare precise timestamps rather than only truncated timestamp strings?
10. Does post-final sync record final gate artifact identity, such as path plus SHA-256 or equivalent digest?
11. Does post-final sync record context packet artifact identity, such as path plus SHA-256 or equivalent digest?
12. Does `current_context_packet.json.auditor_context` explain the source of `final_gate_status` with current final gate IDs and source artifact identity?
13. Does the previous warning condition become either absent or explicitly reclassified as non-active when the context packet is source-synced to the current final gate artifact?
14. Does a genuinely stale context packet still warn or fail in tests?
15. Does `post_final_evidence_sync_result.json` carry current decision, round, and report IDs?
16. Does `final_gate_result.json` pass?
17. Does report-summary match the execution report?
18. Does run-closeout archive this round if command-plan permits closeout?
19. Did this round reuse existing post-final sync/context/final-check/report foundations instead of reimplementing them?
20. Did the final conclusion avoid claiming `ACCEPTED` unless all hard gates and tests support it?

Audit conclusion must be one of:

- `ACCEPTED`
- `ACCEPTED_WITH_LIMITATIONS`
- `REWORK_REQUIRED`
- `BLOCKED`

If `REWORK_REQUIRED`, the audit must give a concrete rework decision, not a generic “continue improving” instruction.

## 6. Implementation Scope

Allowed implementation is intentionally small.

1. Harden timestamp parsing and comparison.
   - Parse ISO timestamps with fractional seconds when present.
   - Normalize timezone handling deterministically.
   - Avoid comparing only rounded string timestamps.
   - Treat absent/invalid timestamps as explicit warning or failure, not silent success.

2. Add source artifact identity to post-final sync.
   - Record final gate source path, generated_at, decision_id, round_id, report_id, and digest.
   - Record context packet source path, generated_at, decision_id, round_id, report_id, and digest when available.
   - Record the comparison basis, for example `timestamp_and_digest`, `digest_current_timestamp_rounded`, `pre_final`, or `stale`.

3. Refine freshness classification.
   - If context final gate status was derived from the current final gate artifact and digest/IDs match, do not emit an active stale warning solely because context `generated_at` is not strictly greater than final gate `generated_at`.
   - If final gate IDs or digest do not match, continue to warn or fail.
   - If context was generated before a different final gate artifact, mark stale.
   - If context is pre-final, mark pre-final rather than current.

4. Update `current_context_packet.json` fields emitted by the context builder.
   - Preserve current fields for backward compatibility.
   - Add new fields without breaking old consumers.
   - Suggested fields include `final_gate_source_path`, `final_gate_source_sha256`, `context_sync_basis`, `context_final_gate_status_source`, `context_final_gate_status_source_sha256`, `post_final_sync_evaluated_at`, and `timestamp_precision_policy`.

5. Update final-check integration.
   - Final-check should require the post-final sync artifact for this decision.
   - Final-check should accept digest-backed current sync even if generated_at precision makes strict timestamp ordering ambiguous.
   - Final-check should still block or warn on true stale context/final-gate mismatch.

6. Add or update tests.
   - Test microsecond precision mismatch where strict timestamp ordering would falsely warn.
   - Test source digest/ID match with rounded context timestamp.
   - Test source digest/ID mismatch.
   - Test stale context after a newer final gate artifact.
   - Test malformed timestamp behavior.
   - Test backward compatibility for consumers of old context fields.

7. Update documentation only if needed.
   - Keep docs focused on timestamp precision and source artifact identity.
   - Do not expand into broader architecture planning.

Allowed source/test/documentation changes are limited to the files listed in `decision_contract`.

## 7. Tests

Run only command-plan authorized commands. If the Tests section conflicts with `project_state/gates/command_plan.json`, command-plan wins.

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
python -m pytest tests/test_post_final_evidence_sync.py tests/test_project_context_builder.py tests/test_project_gate.py -q
python -m pytest tests/test_project_reports.py tests/test_project_state_manifest.py -q
python -m reverse_agent.project_gate post-final-evidence-sync --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260706_post_final_timestamp_precision_hardening_v1
```

Required result artifacts:

- `project_state/pytest_result.txt`
- `project_state/codex_execution_report.md`
- `project_state/execution_report.md`
- `project_state/gates/execution_log.json`
- `project_state/gates/post_final_evidence_sync_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`
- `project_state/rounds/round_20260706_post_final_timestamp_precision_hardening_v1/round_manifest.json` if closeout is permitted.

Acceptance requires:

- all required pytest commands pass;
- post-final sync passes;
- active timestamp warning is removed or explicitly reclassified with final-check support;
- final-check passes;
- execution report recommends `ACCEPTED` only with supporting artifacts.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

- repository root is not `F:\reverse-agent` or equivalent;
- `project_state/decision_packet.md` cannot be read;
- `.codex-skills/registry.json` does not mark `reverse-agent-iteration` active;
- command-plan cannot be generated or is inconsistent with this decision;
- command-plan omits required testing and no approved fallback exists;
- final gate, context packet, or post-final sync artifact has mismatched current decision/round/report IDs;
- implementing the fix requires modifying forbidden paths;
- implementing the fix requires changing workflows, frontend, jobs, roadmap, database files, cleanup artifacts, sample artifacts, or `.codex-skills`;
- any runner dispatch, workflow dispatch, model API, Web runtime, database write, sample solving, external reverse tool invocation, cleanup apply, deletion, or archive apply becomes necessary;
- pytest or final-check fails and cannot be fixed within allowed files;
- stale context/final-gate mismatch remains active while the report claims `SUCCESS/ACCEPTED`.

Stop with `REWORK_REQUIRED` if:

- the implementation only suppresses the warning without adding source artifact identity checks;
- tests do not cover true stale context detection;
- timestamp precision behavior is undocumented in code or tests;
- final-check passes only because the warning was ignored rather than correctly classified;
- report-summary or execution-log does not match pytest and final-check evidence.
