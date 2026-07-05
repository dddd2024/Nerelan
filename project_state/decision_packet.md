```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_status_policy_final_acceptance_rework_v1",
  "round_id": "round_20260705_status_policy_final_acceptance_rework_v1",
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
  "reworks_decision_id": "decision_20260705_governance_fix_cleanup_apply_safety_v1",
  "reworks_round_id": "round_20260705_governance_fix_cleanup_apply_safety_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_43_status_policy_final_acceptance_rework_v1",
  "primary_goal": "Repair the mismatch between governance-fix evidence and final-check acceptance semantics. The failed round generated governance_fix_result.json claiming the historical sample backlog limitation was resolved for current non-sample governance evidence, but final_gate_result.json still returned PASSED_WITH_LIMITATIONS and ACCEPTED_WITH_LIMITATIONS because doctor_status=FAIL and historical sample backlog were still propagated into final acceptance. This rework must make final-check/report-summary/status-policy agree: when the active decision is non-sample project_governance, active current evidence passes, no concrete sample-evidence claim exists, and historical sample gaps are classified as backlog notices, final-check must produce PASSED and report acceptance must be ACCEPTED. Historical backlog must stay visible and must not be hidden or deleted.",
  "command_plan_authority_required": true,
  "accepted_requires_final_gate_passed": true,
  "accepted_requires_report_acceptance_accepted": true,
  "accepted_requires_status_policy_reconcile_current": true,
  "accepted_requires_doctor_backlog_split_current": true,
  "accepted_requires_governance_fix_current": true,
  "accepted_requires_historical_backlog_visible": true,
  "accepted_requires_no_cleanup_apply_work": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/state_governance.py",
    "reverse_agent/state_hygiene.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_state_governance.py",
    "tests/test_state_hygiene.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py"
  ],
  "allowed_documentation_files": [
    "docs/governance_fix_cleanup_apply_safety.md",
    "docs/state_governance_bundle.md",
    "docs/project_governance_context.md",
    "docs/state_manifest.md",
    "docs/workstream_registry.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/roadmap/workstreams.json",
    "project_state/gates/status_policy_reconcile_result.json",
    "project_state/gates/doctor_backlog_split_result.json",
    "project_state/gates/governance_fix_result.json",
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
    "project_state/rounds/round_20260705_status_policy_final_acceptance_rework_v1/*"
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
    "project_state/gates/cleanup_apply_safety_plan.json",
    "project_state/gates/cleanup_apply_dry_run.json",
    "project_state/gates/cleanup_apply_safety_result.json",
    "project_state/gates/cleanup_apply_safety_snapshot.json",
    "project_state/gates/deletion_manifest_validation_result.json",
    "project_state/gates/tombstone_validation_result.json",
    "project_state/gates/rollback_handoff_plan.json",
    "project_state/gates/audit_handoff_for_cleanup_apply.json"
  ],
  "forbidden_capabilities_this_round": [
    "cleanup_apply_safety_expansion",
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

Implement **Status Policy Final Acceptance Rework v1**.

This is a targeted rework of `decision_20260705_governance_fix_cleanup_apply_safety_v1`. The previous round successfully advanced the cleanup-apply safety dry-run lane, but audit found the fix lane incomplete: `governance_fix_result.json` said the limitation was resolved for current non-sample governance evidence, while `final_gate_result.json` still returned `PASSED_WITH_LIMITATIONS` and `status_summary.report_acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS` because `doctor_status=FAIL` and historical sample backlog were still propagated into final acceptance.

This round must fix only that acceptance-path mismatch.

Required final state:

- `project_state/gates/final_gate_result.json.gate_status` is `PASSED`, not `PASSED_WITH_LIMITATIONS`, when all current governance evidence passes and the only remaining issue is historical sample backlog.
- `project_state/gates/final_gate_result.json.status_summary.report_acceptance_recommendation` is `ACCEPTED`, not `ACCEPTED_WITH_LIMITATIONS`, under the same condition.
- `project_state/gates/status_policy_reconcile_result.json` explains why historical sample backlog is a backlog notice, not a current blocker.
- `project_state/gates/doctor_backlog_split_result.json` keeps the 50 missing historical sample artifacts visible as backlog context.
- `project_state/gates/governance_fix_result.json` and final-check agree with each other.
- No cleanup-apply safety expansion is performed in this rework.

## 2. Current Evidence

Current task authority is `project_state/decision_packet.md`. `project_state/task_packet.json` remains background only and still points to `decision_packet` as current-round authority.

Previous failed/rework target:

- `decision_20260705_governance_fix_cleanup_apply_safety_v1`
- `round_20260705_governance_fix_cleanup_apply_safety_v1`
- audit outcome: `REWORK_REQUIRED`

Evidence from that failed round:

1. `codex_execution_report.md` claimed `SUCCESS` and `ACCEPTED` for `decision_20260705_governance_fix_cleanup_apply_safety_v1`.
2. `pytest_result.txt` reported `PASSED`, with startup clean and focused tests passing.
3. `execution_log.json` recorded 18 commands, all `PASSED`, with no warnings or blocking reasons.
4. `cleanup_apply_safety_result.json` was acceptable: dry-run only, no real cleanup apply, no destructive arrays populated, and forbidden capabilities disabled.
5. `governance_fix_result.json` claimed `fix_status=RESOLVED_FOR_CURRENT_GOVERNANCE_EVIDENCE` and `previous_limitation_resolved_for_current_non_sample_governance=true`.
6. `final_gate_result.json` contradicted that claim by keeping `gate_status=PASSED_WITH_LIMITATIONS` and `report_acceptance_recommendation=ACCEPTED_WITH_LIMITATIONS`.
7. The remaining limitation text was still historical sample artifacts missing and doctor status fail.

Therefore the rework target is not cleanup-apply safety and not state-governance artifact generation. The rework target is final acceptance semantics across status-policy, doctor/backlog split, governance-fix, report-summary, and final-check.

Existing capabilities that must not be duplicated:

- command-plan;
- execution-log;
- report-summary synthesis;
- final-check;
- run-closeout;
- state manifest;
- context packet;
- workstream registry;
- governance-fix gate;
- cleanup-apply-safety dry-run artifacts.

Negative results still apply:

- no reverse-solving fallback;
- no budget/beam expansion;
- no full `solve_reports` scan;
- no stale runtime diagnostics;
- no concrete sample claim.

Artifact freshness policy:

- New or refreshed artifacts must carry `decision_20260705_status_policy_final_acceptance_rework_v1` and `round_20260705_status_policy_final_acceptance_rework_v1`.
- Historical sample backlog must remain visible as historical/backlog evidence.
- No current sample evidence claim may be introduced.

## 3. Do Not Do

Do not add new cleanup-apply safety features.

Do not modify cleanup-apply safety artifacts except as historical referenced evidence if existing gate/report machinery requires reference updates.

Do not run cleanup apply.

Do not delete, move, rename, archive, compact, tombstone, or destructively mutate any file.

Do not write a real deletion manifest or real tombstone.

Do not modify `.github/workflows/*`.

Do not modify `.codex-skills/*`.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not modify `project_state/archives/*` or `project_state/deletions/*`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not recursively scan the whole `project_state/rounds/` tree.

Do not process real samples, local binaries, training corpora, or user uploads.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external analysis tools.

Do not invoke model APIs, automatic runners, manual runner dispatch, remote agents, CI workflow dispatch, or CI polling.

Do not implement a database, queue, production HTTP service, scheduler, background service, or Web runtime.

Do not hide historical sample backlog. It must remain visible as backlog notice.

Do not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

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
9. `project_state/gates/governance_fix_result.json`
10. `project_state/gates/execution_log.json`
11. `project_state/gates/command_plan.json`
12. `project_state/gates/run_closeout_result.json`
13. `project_state/state_manifest.json`
14. `project_state/context/current_context_packet.json`
15. `project_state/roadmap/workstreams.json`
16. `project_state/task_packet.json`
17. `project_state/current_state.json`
18. `project_state/artifact_index.json`
19. `project_state/negative_results.json`
20. `.codex-skills/registry.json`

Inspect source/test surfaces:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_reports.py`
3. `reverse_agent/state_governance.py`
4. `reverse_agent/state_hygiene.py`
5. `reverse_agent/project_state_manifest.py`
6. `reverse_agent/project_context_builder.py`
7. `reverse_agent/project_workstreams.py`
8. `tests/test_project_gate.py`
9. `tests/test_project_reports.py`
10. `tests/test_state_governance.py`
11. `tests/test_state_hygiene.py`
12. `tests/test_project_state_manifest.py`
13. `tests/test_project_context_builder.py`
14. `tests/test_project_workstreams.py`

Do not inspect full `solve_reports/`, full `PROJECT_PROGRESS_LOG.txt`, or recursively scan full `project_state/rounds/`.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was the previous `governance_fix_cleanup_apply_safety` round treated as `REWORK_REQUIRED` target?
5. Did the implementation avoid adding or expanding cleanup-apply safety functionality?
6. Were status-policy, doctor/backlog split, governance-fix, report-summary, and final-check inspected before modification?
7. Was `project_state/gates/status_policy_reconcile_result.json` generated or refreshed for this round?
8. Was `project_state/gates/doctor_backlog_split_result.json` generated or refreshed for this round?
9. Was `project_state/gates/governance_fix_result.json` generated or refreshed for this round?
10. Does governance-fix result agree with final-check outcome?
11. Is historical sample backlog still visible as backlog notice?
12. Is historical sample backlog prevented from downgrading current non-sample governance acceptance when current evidence passes?
13. Does final-check produce `gate_status=PASSED` when current governance evidence passes and only historical sample backlog remains?
14. Does `status_summary.report_acceptance_recommendation=ACCEPTED` under that condition?
15. Does `status_policy_valid` avoid carrying `doctor_status=FAIL` as a limitation for current non-sample governance acceptance?
16. Does report-summary synthesis match the updated final-check/report status?
17. Did command-plan authorize every executed command?
18. Were command-plan omitted commands left unexecuted?
19. Did pytest_result record real commands and exit codes?
20. Did focused tests cover final acceptance semantics, backlog visibility, and no cleanup-apply expansion?
21. Did existing governance/gate/report tests continue to pass?
22. Did run-closeout pass if authorized?
23. Were forbidden paths untouched?
24. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, `project_state/archives/*`, and `project_state/deletions/*` untouched?
25. Did the final report avoid any concrete sample solve/static/runtime/audit validation claim?
26. Did the final report explicitly state that this was a status-policy/final-acceptance rework only?

## 6. Implementation Scope

Allowed implementation is limited to final acceptance semantics for current non-sample governance rounds.

### A. Status-policy reconcile

Update the existing status-policy reconciliation logic so that historical sample artifact gaps are treated as backlog notices when all of the following are true:

- active decision mainline is `project_governance`;
- active decision does not claim concrete sample evidence;
- current required governance artifacts are present and current;
- pytest/report/execution-log/final-check command authority evidence is otherwise passing;
- historical sample gaps are still recorded as backlog evidence.

Generate or refresh:

- `project_state/gates/status_policy_reconcile_result.json`

### B. Doctor/backlog split

Update doctor/backlog split behavior so `doctor_status=FAIL` caused only by historical sample backlog does not become a current acceptance limitation for a non-sample governance round.

The backlog must remain explicit:

- missing artifact count;
- missing artifact names or classes;
- reason they are historical/nonblocking;
- statement that they are not current evidence.

Generate or refresh:

- `project_state/gates/doctor_backlog_split_result.json`

### C. Governance-fix/final-check alignment

Ensure `governance_fix_result.json` and `final_gate_result.json` agree.

Required alignment:

- if `governance_fix_result.fix_status=RESOLVED_FOR_CURRENT_GOVERNANCE_EVIDENCE`, then final-check must not keep the same issue as `PASSED_WITH_LIMITATIONS`;
- final-check must make the backlog visible but non-limiting;
- `status_summary.report_acceptance_recommendation` must be `ACCEPTED` if no other active limitation exists.

Generate or refresh:

- `project_state/gates/governance_fix_result.json`
- `project_state/gates/final_gate_result.json`
- `project_state/gates/report_summary_synthesis.json`

### D. Context and workstream refresh

Update only as needed:

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`

Required workstream state:

- only `status_policy_final_acceptance_rework` is `ACTIVE_ROUND`;
- `governance_fix_cleanup_apply_safety` is marked as rework target / not accepted;
- `state_governance_bundle_big_step` remains the last accepted baseline;
- cleanup-apply safety remains completed historical engineering evidence, but not active expansion.

### E. Tests

Add or update focused tests for:

- historical sample backlog visible but non-limiting;
- doctor status fail from historical sample backlog does not downgrade non-sample governance acceptance;
- final-check returns `PASSED` and `ACCEPTED` under the required condition;
- governance-fix result and final-check do not contradict each other;
- cleanup-apply safety artifacts are not regenerated or expanded as new work.

Do not weaken current-artifact, command-plan, execution-log, report-summary, final-check, or closeout checks.

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
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_state_governance.py tests/test_state_hygiene.py -q
python -m pytest tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m reverse_agent.project_gate governance-fix --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_status_policy_final_acceptance_rework_v1
```

Expected results:

- focused status-policy/final-check tests pass;
- existing governance/gate/report tests pass;
- final-check returns `PASSED`;
- report-summary returns `ACCEPTED`;
- historical sample backlog remains visible as backlog notice;
- no cleanup-apply safety expansion occurs;
- no forbidden paths are mutated;
- no destructive operation occurs;
- run-closeout passes if authorized.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. Repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects dirty source/test files not captured by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active.
5. command-plan cannot be generated or does not authorize required commands.
6. The implementation requires cleanup-apply work or cleanup-apply safety expansion.
7. The implementation requires deleting, moving, renaming, archiving, compacting, or tombstoning any file.
8. The implementation requires modifying `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `project_state/archives/*`, or `project_state/deletions/*`.
9. Historical sample backlog must be hidden or removed to make final-check pass.
10. final-check cannot produce `PASSED` while preserving backlog visibility.
11. report-summary cannot reconcile `ACCEPTED` with the generated evidence.
12. Any concrete sample solve/static/runtime/audit verification claim is introduced.

If a stop condition is hit, write `codex_execution_report.md`, `execution_report.md`, and `pytest_result.txt` with blocked/failed evidence. Do not run closeout unless command-plan explicitly authorizes diagnostic closeout for failed rounds.
