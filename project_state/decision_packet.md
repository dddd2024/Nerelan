```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_state_hygiene_retention_policy_v1",
  "round_id": "round_20260705_state_hygiene_retention_policy_v1",
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
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_41_state_hygiene_retention_policy_v1",
  "primary_goal": "Create a bounded State Hygiene + Retention Policy v1 layer over the accepted governance context registry. This round must define artifact lifecycle classes, retention policy rules, and a cleanup-plan artifact that identifies retain/archive/delete-candidate decisions without deleting, moving, archiving, compacting, or mutating evidence files. It must reduce state-noise risk from closeout temporary logs, historical nonblocking gates, and missing historical sample artifacts while preserving project_state as the audit fact source.",
  "command_plan_authority_required": true,
  "accepted_requires_retention_policy": true,
  "accepted_requires_state_hygiene_gate": true,
  "accepted_requires_cleanup_plan": true,
  "accepted_requires_no_cleanup_apply": true,
  "accepted_requires_existing_hygiene_inventory_check": true,
  "accepted_requires_context_workstream_update": true,
  "allowed_source_files": [
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/state_hygiene.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "tests/test_state_hygiene.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/state_hygiene_retention_policy.md",
    "docs/state_manifest.md",
    "docs/workstream_registry.md",
    "docs/project_governance_context.md"
  ],
  "allowed_config_files": [
    "project_state/retention_policy.json"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/retention_policy.json",
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/roadmap/workstreams.json",
    "project_state/gates/state_hygiene_retention_result.json",
    "project_state/gates/state_hygiene_retention_snapshot.json",
    "project_state/gates/cleanup_plan.json",
    "project_state/gates/cleanup_plan_summary.json",
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
    "project_state/rounds/round_20260705_state_hygiene_retention_policy_v1/*"
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
    "tombstone_write",
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

Implement **State Hygiene + Retention Policy v1**.

The previous governance round created the deterministic state entrypoints that this project needed: `project_state/state_manifest.json`, `project_state/context/current_context_packet.json`, and `project_state/roadmap/workstreams.json`. Its audit outcome was `ACCEPTED_WITH_LIMITATIONS`, not pure `ACCEPTED`, because `final-check` reported `PASSED_WITH_LIMITATIONS`: historical sample artifacts remain missing and the doctor status is still nonblocking-failed for this current non-sample governance track.

The next step is therefore not another Web/API expansion, not reverse solving, not runner dispatch, and not a database. The next step is a small state-governance round that formalizes artifact lifecycle and cleanup planning without deleting anything.

Deliver in one round:

1. `project_state/retention_policy.json`
   - A deterministic policy file that classifies artifact families and retention rules.
   - It must distinguish audit-critical current evidence, accepted-round minimum evidence, generated gate artifacts, historical nonblocking artifacts, transient closeout logs/pids, stale sample artifacts, missing sample references, docs, config, and disposable cache-like artifacts.

2. `project_state/gates/cleanup_plan.json`
   - A non-destructive cleanup plan.
   - It may list retain/archive/delete-candidate recommendations, but it must not delete, move, compact, or archive any file.
   - Every destructive recommendation must be marked `requires_future_cleanup_apply_decision=true`.

3. `project_state/gates/state_hygiene_retention_result.json`
   - A current governance gate proving the policy and cleanup plan are bounded, non-destructive, and compatible with existing audit evidence.

4. `project_state/gates/state_hygiene_retention_snapshot.json`
   - A compact snapshot summarizing counts by lifecycle class, not a full recursive dump.

5. Context/workstream updates
   - Update `state_manifest`, `current_context_packet`, and `workstreams` so the active workstream becomes `state_hygiene_retention_policy` and the previous context-registry workstream is treated as accepted baseline.

Accepted target:

- Mainline: `project_governance`.
- The round only produces lifecycle policy, inventory summaries, cleanup-plan recommendations, gate artifacts, docs, and tests.
- `project_state` remains the audit fact source.
- `retention_policy.json` and `cleanup_plan.json` are planning artifacts, not authority to delete.
- No cleanup apply, deletion, archive compaction, tombstone write, real sample execution, external tool invocation, model API call, runner dispatch, database, service, queue, scheduler, or GitHub workflow mutation is allowed.

## 2. Current Evidence

Mainline: `project_governance`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only; it still carries old sample-reverse context and says `execution_scope=decision_packet_controls_current_round`.

Previous accepted-with-limitations baseline:

- `decision_20260705_project_governance_context_registry_v1`
- `round_20260705_project_governance_context_registry_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the prior round:

1. `project_state/codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for the governance context registry round.
2. `project_state/pytest_result.txt` reported `PASSED` and recorded project governance tests.
3. `project_state/gates/execution_log.json` was current and listed all recorded commands as passed.
4. `project_state/gates/project_governance_context_result.json` passed and proved the state manifest, current context packet, and workstream registry are current and index-only.
5. `project_state/gates/final_gate_result.json` was `PASSED_WITH_LIMITATIONS`, with limitations caused by historical sample artifact gaps and doctor status fail. These limitations were treated as nonblocking for current non-sample governance evidence.
6. `project_state/rounds/round_20260705_project_governance_context_registry_v1/round_manifest.json` archived current report, neutral execution report, decision packet, and pytest result.

Current state entrypoints now exist:

- `project_state/state_manifest.json` exists and classifies current, generated_or_updated, historical_nonblocking, archived, and missing artifacts.
- It reports 10 current artifacts and 50 missing artifacts, with `missing_sample_artifacts_blocking_for_current_round=false`.
- It treats `current_state.json`, `task_packet.json`, `artifact_index.json`, and `negative_results.json` as historical/nonblocking for the governance context.
- `project_state/roadmap/workstreams.json` exists and marks `state_hygiene_retention_policy` as `READY_FOR_DECISION`.
- The same registry states that roadmap entries are not execution authority and only the current decision may mark an active round.

Existing hygiene capability to preserve and not duplicate:

- `project_state/gates/state_hygiene_inventory.json` already exists as a historical inventory artifact from `decision_20260627_limited_acceptance_status_policy_rework_v1`.
- That artifact was explicitly `no_delete=true` and categorized files without deleting anything.
- This round must not claim state hygiene starts from zero. It should build on that prior inventory pattern and the new state manifest/context registry.

Current problem to address:

- `final-check` still reports historical missing sample artifacts as a nonblocking limitation.
- Closeout temporary log/pid artifacts such as `run_closeout_*.out.log`, `run_closeout_*.err.log`, and `run_closeout_*.pid` appeared in the previous round delta.
- Historical nonblocking gate artifacts are accumulating and should be classified by lifecycle.
- The project needs a retention policy and cleanup-plan gate before any future deletion/archive/compaction decision.

Negative results:

- `project_state/negative_results.json` blocks old solver blind search, budget-only expansion, invalid frontier reuse, full `solve_reports` commits, and repeated stale diagnostics.
- This round is governance-only and must not enter reverse-solving directions.

Artifact freshness policy:

- Current-round state hygiene artifacts must carry `decision_20260705_state_hygiene_retention_policy_v1` and `round_20260705_state_hygiene_retention_policy_v1`.
- Historical user-solve, runner, CI, sample, and prior state-hygiene artifacts may be referenced only as historical/backlog evidence unless their IDs are current.
- Missing historical sample artifacts are nonblocking for this governance round, but they must be explicitly classified.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- If this Tests section conflicts with command-plan, command-plan wins.

This round will not repeat already accepted context-registry work. It will consume the manifest/context/workstream outputs as inputs and add lifecycle/retention/cleanup-plan governance on top.

## 3. Do Not Do

Do not delete, move, rename, archive, compact, tombstone, or otherwise destructively mutate any state artifact.

Do not implement `cleanup-apply` in this round.

Do not implement archive compaction, cold storage migration, blob store migration, database indexing, or SQLite/PostgreSQL.

Do not solve a concrete reverse sample.

Do not process real samples, real uploads, training samples, or local binary corpora.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external analysis tools.

Do not invoke model APIs, planner APIs, auditor APIs, Codex CLI, remote agents, CI workflows, or automatic runners.

Do not implement production HTTP infrastructure, database, queue, scheduler, background service, remote dispatch, CI polling, or auto-iteration.

Do not modify `.github/workflows/*`.

Do not modify `.codex-skills/*` or store dynamic project facts in long-term prompt/skill files.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not modify `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.

Do not treat `retention_policy.json` or `cleanup_plan.json` as authority to delete. They are planning artifacts only.

Do not mark any cleanup candidate as safe for immediate deletion. Any destructive action must require a future explicit cleanup-apply decision.

Do not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

Do not mix this round with user-solve, Web/API, runner dispatch, CI workflow, tool integration, or reverse-solving implementation.

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

Inspect current gates and prior accepted-with-limitations baseline:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/execution_log.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/project_governance_context_result.json`
7. `project_state/gates/project_governance_context_snapshot.json`
8. `project_state/rounds/round_20260705_project_governance_context_registry_v1/round_manifest.json`

Inspect prior hygiene work before adding new code:

1. `project_state/gates/state_hygiene_inventory.json`
2. `project_state/rounds/round_20260619_project_state_hygiene_rebuild_v1/decision_packet.md`
3. `project_state/rounds/round_20260623_naming_hygiene_inventory_v1/decision_packet.md`
4. `project_state/rounds/round_20260624_state_hygiene_archive_scope_rework_v1/decision_packet.md`

Inspect existing governance/gate surfaces:

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

1. `reverse_agent/state_hygiene.py`
2. `tests/test_state_hygiene.py`
3. `project_state/retention_policy.json`
4. `project_state/gates/cleanup_plan.json`
5. `project_state/gates/cleanup_plan_summary.json`
6. `project_state/gates/state_hygiene_retention_result.json`
7. `project_state/gates/state_hygiene_retention_snapshot.json`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`. Use bounded files, current manifests, and known historical hygiene artifacts only.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was the previous governance context registry round treated as accepted-with-limitations baseline?
5. Did the round inspect existing state manifest, context packet, workstream registry, and prior state hygiene inventory before adding new code?
6. Did the implementation avoid duplicating existing command-plan, execution-log, report-summary, closeout, context-builder, and workstream-registry mechanisms?
7. Was `project_state/retention_policy.json` generated?
8. Does `retention_policy.json` classify artifact lifecycle classes including current audit evidence, accepted-round minimum evidence, generated gate artifacts, historical nonblocking artifacts, transient closeout logs/pids, missing sample references, docs/config, and disposable cache-like artifacts?
9. Does `retention_policy.json` explicitly forbid deletion without a future cleanup-apply decision?
10. Was `project_state/gates/cleanup_plan.json` generated?
11. Does `cleanup_plan.json` only produce retain/archive/delete-candidate recommendations and no destructive actions?
12. Does every destructive recommendation in `cleanup_plan.json` include `requires_future_cleanup_apply_decision=true`?
13. Does the cleanup plan classify `run_closeout_*.out.log`, `run_closeout_*.err.log`, and `run_closeout_*.pid` as transient candidates without deleting them?
14. Does the cleanup plan classify missing historical sample artifacts as nonblocking references rather than current evidence gaps?
15. Does the cleanup plan preserve current decision, report, pytest, command-plan, execution-log, final-check, closeout, state_manifest, context packet, workstreams, and accepted-round minimum evidence?
16. Was `project_state/gates/state_hygiene_retention_result.json` generated?
17. Was `project_state/gates/state_hygiene_retention_snapshot.json` generated?
18. Do new gate artifacts carry current decision/report/round IDs?
19. Does the state-hygiene gate prove no deletion, move, archive compaction, tombstone write, database, runner dispatch, model API, external tool, or real sample processing occurred?
20. Were `project_state/state_manifest.json`, `project_state/context/current_context_packet.json`, and `project_state/roadmap/workstreams.json` updated for this round?
21. Does `workstreams.json` mark only `state_hygiene_retention_policy` as `ACTIVE_ROUND`?
22. Does `workstreams.json` mark `project_governance_context_registry` as accepted baseline rather than active?
23. Did command-plan authorize every executed command?
24. Were command-plan omitted commands left unexecuted?
25. Did pytest_result record real commands and exit codes?
26. Did focused tests cover retention policy, cleanup plan, state-hygiene gate, and no-delete behavior?
27. Did existing project governance/gate/report tests continue to pass?
28. Did final-check pass or pass-with-limitations only for explicitly nonblocking historical sample artifact gaps?
29. Did report-summary synthesis pass and match the report summary?
30. Did run-closeout pass if authorized?
31. Were forbidden files untouched?
32. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, `project_state/archives/*`, and `project_state/deletions/*` untouched?
33. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?
34. Did the final report explicitly state that this round is cleanup-plan only and not cleanup-apply?
35. Did the final report identify remaining limitations and recommend a future cleanup-apply round only after tombstone/deletion manifest design is accepted?

## 6. Implementation Scope

Allowed implementation is limited to non-destructive state lifecycle planning.

### A. Retention Policy v1

Add `reverse_agent/state_hygiene.py` or compatibly extend an existing equivalent module if one already exists.

Generate `project_state/retention_policy.json` with stable ordering.

Required policy classes:

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

Required rule fields:

- `class_name`
- `description`
- `examples`
- `retain_minimum`
- `can_archive_in_future`
- `can_delete_in_future`
- `requires_cleanup_apply_decision`
- `requires_tombstone_if_deleted`
- `current_round_delete_allowed=false`

### B. Cleanup Plan v1

Generate `project_state/gates/cleanup_plan.json` and optionally `project_state/gates/cleanup_plan_summary.json`.

Required behavior:

- Read only bounded state locations: current manifest/context/workstreams, current gates, immediate `project_state/gates/*` names, current report summary, and known historical nonblocking lists.
- Do not recursively scan full `project_state/rounds/`.
- Do not scan `solve_reports/`.
- Classify each candidate into lifecycle classes.
- Preserve all current evidence and accepted-round minimum evidence.
- Identify transient closeout logs/pids as cleanup candidates, but set `action="defer"` or `delete_allowed_now=false`.
- Identify historical nonblocking gates as archive candidates, but set `archive_allowed_now=false` unless a future archive decision exists.
- Identify missing historical sample artifacts as nonblocking references, not files to delete.
- Emit counts by class and by recommended future action.

Every candidate that could ever be deleted must include:

```json
{
  "delete_allowed_now": false,
  "requires_future_cleanup_apply_decision": true,
  "requires_tombstone_if_deleted": true
}
```

### C. State Hygiene Gate v1

Extend `reverse_agent/project_gate.py` with a bounded gate command, for example:

```powershell
python -m reverse_agent.project_gate state-hygiene-retention --state-dir project_state
```

The exact CLI name may differ if an existing convention is better, but it must be recorded in command-plan and pytest_result.

Required generated artifacts:

- `project_state/gates/state_hygiene_retention_result.json`
- `project_state/gates/state_hygiene_retention_snapshot.json`

Required checks:

- retention policy exists and is current;
- cleanup plan exists and is current;
- no candidate has `delete_allowed_now=true`;
- no file was deleted, moved, archived, compacted, or tombstoned;
- current evidence is protected;
- accepted-round minimum evidence is protected;
- missing historical sample artifacts are nonblocking;
- transient closeout logs/pids are classified but not removed;
- workstream active status is unique and current;
- generated artifacts carry current IDs.

### D. Context and Workstream Updates

Update existing governance outputs using the existing modules:

- `project_state/state_manifest.json`
- `project_state/context/current_context_packet.json`
- `project_state/roadmap/workstreams.json`

Required updates:

- Active decision/round becomes this state hygiene round.
- `state_hygiene_retention_policy` becomes `ACTIVE_ROUND`.
- `project_governance_context_registry` becomes `ACCEPTED` or accepted baseline reference.
- Deferred workstreams remain deferred: runner dispatch, database indexing, IDA/Ghidra/debugger integration, dynamic reverse solving, cleanup-apply.
- Context packet must state cleanup planning is allowed but cleanup application is forbidden.

### E. Final-check and Report Compatibility

Update `project_gate` and report-summary only as needed to recognize the new artifacts and no-delete rule.

Do not weaken existing checks for:

- decision/report/round matching;
- pytest/report matching;
- command-plan authority;
- execution-log consistency;
- report-summary synthesis;
- forbidden paths;
- artifact role taxonomy;
- closeout.

If final-check remains `PASSED_WITH_LIMITATIONS` only because of historical missing sample artifacts, the execution report must state that limitation explicitly and explain why it is nonblocking for this governance round.

### F. Documentation

Add or update concise docs:

- `docs/state_hygiene_retention_policy.md`
- `docs/state_manifest.md` only if needed for lifecycle cross-reference
- `docs/workstream_registry.md` only if needed for active workstream policy
- `docs/project_governance_context.md` only if needed for context packet changes

Docs must explain:

- retention policy does not delete files;
- cleanup-plan is not cleanup-apply;
- future cleanup-apply requires a separate decision;
- deletion requires deletion manifest/tombstone design;
- current audit fact sources are protected;
- project_state remains the audit fact source.

## 7. Tests

Command-plan is command authority. If this Tests section conflicts with `project_state/gates/command_plan.json`, command-plan wins.

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
python -m pytest tests/test_state_hygiene.py tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate state-hygiene-retention --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_state_hygiene_retention_policy_v1
```

If the project-gate CLI name differs, implement the smallest compatible CLI surface and record the exact command in command-plan, pytest_result, execution_log, and report.

Test expectations:

- New state hygiene tests pass.
- Existing context/workstream tests pass.
- Existing gate/report tests pass.
- State-hygiene-retention gate passes.
- final-check passes, or passes with limitations only for historical missing sample artifacts explicitly classified as nonblocking.
- report-summary passes or exits with the command-plan-allowed diagnostic exit while final-check records alignment.
- run-closeout passes if authorized.
- No command-plan omissions are executed.
- No forbidden files are mutated.
- No deletion/move/archive/compaction/tombstone occurs.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. The repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects untracked or dirty source/test files before implementation and they are not recorded by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active in `.codex-skills/registry.json`.
5. `command_plan.json` cannot be generated or does not authorize required commands.
6. Existing state manifest/context/workstream artifacts cannot be read and the failure cannot be represented as a bounded BLOCKED report.
7. The implementation would require deleting, moving, renaming, archiving, compacting, or tombstoning files.
8. The implementation would require `cleanup-apply`.
9. The implementation would require reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
10. The implementation would require Web runtime, database, queue, scheduler, runner dispatch, model API, CI dispatch, or external reverse tool execution.
11. The implementation would need to modify `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, `project_state/negative_results.json`, `project_state/archives/*`, or `project_state/deletions/*`.
12. More than one workstream would need to be marked `ACTIVE_ROUND`.
13. Any cleanup candidate must be marked `delete_allowed_now=true` to make tests pass.
14. Current audit fact sources or accepted-round minimum evidence cannot be protected.
15. Tests fail and the failure is not explainable with a bounded fix in the allowed scope.
16. final-check fails for a reason other than explicitly nonblocking historical sample artifact gaps.
17. report-summary cannot reconcile report status with generated evidence.
18. Any concrete sample solve/static/runtime/audit verification claim is introduced.

If a stop condition is hit, write the execution report with `status=BLOCKED` or `status=FAILED` as appropriate, preserve all available evidence, and do not run closeout unless command-plan explicitly authorizes diagnostic closeout for failed rounds.
