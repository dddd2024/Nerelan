```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260704_user_solve_workbench_foundation_big_step_v1",
  "round_id": "round_20260704_user_solve_workbench_foundation_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "supersedes_decision_id": "decision_20260704_user_solve_tool_profile_capability_v1",
  "supersedes_round_id": "round_20260704_user_solve_tool_profile_capability_v1",
  "follows_last_accepted_decision_id": "decision_20260704_user_solve_local_frontend_mvp_big_step_v1",
  "follows_last_accepted_round_id": "round_20260704_user_solve_local_frontend_mvp_big_step_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_38_user_solve_workbench_foundation_big_step",
  "primary_goal": "Build a larger User Solve Workbench Foundation over the accepted local frontend MVP: tool profiles, runner capability metadata, route planning, local in-process workbench API facade, synthetic task trace contract, workbench fixtures, schema snapshots, CLI preview, gates, reports, docs, and focused tests. This round remains metadata-only and fixture-only; it must not perform real sample analysis or call external analysis tools.",
  "command_plan_authority_required": true,
  "accepted_requires_tool_profile_contract": true,
  "accepted_requires_runner_capability_contract": true,
  "accepted_requires_route_planner_contract": true,
  "accepted_requires_workbench_api_facade": true,
  "accepted_requires_synthetic_task_trace_contract": true,
  "accepted_requires_workbench_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/tool_profiles.py",
    "reverse_agent/tool_capabilities.py",
    "reverse_agent/user_solve_route_plan.py",
    "reverse_agent/user_solve_workbench.py",
    "reverse_agent/user_solve_workbench_api.py",
    "reverse_agent/user_solve_task_trace.py",
    "reverse_agent/user_solve_fixtures.py",
    "reverse_agent/user_solve_api_schema.py",
    "reverse_agent/user_solve_cli.py",
    "reverse_agent/user_solve_controller.py",
    "reverse_agent/user_solve_frontend_bridge.py",
    "reverse_agent/user_solve_ui_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/project_gate.py",
    "tests/test_tool_profiles.py",
    "tests/test_tool_capabilities.py",
    "tests/test_user_solve_route_plan.py",
    "tests/test_user_solve_workbench.py",
    "tests/test_user_solve_workbench_api.py",
    "tests/test_user_solve_task_trace.py",
    "tests/test_user_solve_api_schema.py",
    "tests/test_user_solve_fixtures.py",
    "tests/test_user_solve_cli.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_frontend_files": [
    "frontend/user_solve_demo/app.js",
    "frontend/user_solve_demo/index.html",
    "frontend/user_solve_demo/style.css",
    "frontend/user_solve_demo/README.md",
    "frontend/user_solve_demo/fixtures/*.json"
  ],
  "allowed_config_files": [
    ".reverse-agent/config/tool_profiles.example.json",
    ".reverse-agent/config/user_solve_workbench.example.json"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_layer.md",
    "docs/user_solve_control_plane.md",
    "docs/user_solve_local_frontend_mvp.md",
    "docs/user_solve_workbench.md",
    "docs/user_solve_tool_profiles.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260704_user_solve_workbench_foundation_big_step_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/*",
    "solve_reports/*",
    ".github/workflows/*",
    "training_materials/local_reverse/*",
    "project_state/solve_tasks/*",
    "project_state/user_sessions/*",
    "project_state/jobs/*"
  ],
  "forbidden_capabilities_this_round": [
    "external_analysis_tool_invocation",
    "real_sample_analysis_execution",
    "real_user_upload_ingestion",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "interactive_tool_adapter",
    "production_http_service",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "persistent_user_task_or_session_creation",
    "auto_iteration"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Workbench Foundation Big Step v1**.

This supersedes the smaller tool-profile-only plan. The accepted baseline already has a local fixture frontend MVP. The next step should be larger: connect the existing user-solve contracts, frontend bridge, local API shape, capability metadata, route planning, synthetic task trace, CLI preview, gates, docs, and tests into one coherent local workbench foundation.

Deliver in one round:

1. Tool profile and runner capability contracts for future routing.
2. A route planner that maps request state, missing evidence, risk level, permissions, and capability metadata into safe planned next actions.
3. A local workbench facade that composes existing controller/session/result/UI/error/fixture behavior instead of duplicating it.
4. A local in-process workbench API adapter with route-shaped pure functions for fixture catalog, solve preview, route plan preview, capability snapshot, task trace preview, and schema snapshot.
5. A synthetic task trace contract for workbench demo tasks. It may serialize in memory and in gate artifacts, but must not create persistent task/session files.
6. Expanded deterministic fixtures and schema snapshots shared by CLI, local API, frontend bridge, and tests.
7. Optional static demo refresh under `frontend/user_solve_demo/` to display the larger workbench fixture payloads, without adding a framework or backend service.
8. Project gate integration that emits `project_state/gates/user_solve_workbench_result.json` and `project_state/gates/user_solve_workbench_snapshot.json` or equivalent artifacts.
9. CLI previews for candidate, missing-evidence, blocked, verified, route-plan, capability, and workbench states.
10. Documentation for the new workbench foundation and future execution boundary.
11. Focused tests plus required report-summary/final-check/run-closeout integration.

Accepted target:

- The implementation is a large engineering foundation step, not a reverse-solving step.
- It is local, deterministic, synthetic, fixture-backed, and non-persistent.
- It does not perform real sample analysis or call external analysis tools.
- It does not create a production service, database, queue, scheduler, remote dispatch, CI polling, persistent task/session store, or auto-iteration loop.
- It does not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`.

This decision supersedes:

- `decision_20260704_user_solve_tool_profile_capability_v1`
- `round_20260704_user_solve_tool_profile_capability_v1`

Last accepted baseline:

- `decision_20260704_user_solve_local_frontend_mvp_big_step_v1`
- `round_20260704_user_solve_local_frontend_mvp_big_step_v1`
- audit outcome: `ACCEPTED`

Evidence from the accepted baseline:

1. The local frontend MVP round reported `SUCCESS` and `acceptance_recommendation=ACCEPTED`.
2. The frontend bridge, local fixture API adapter, UI state mapper, error taxonomy, deterministic fixtures, static demo files, schema snapshot, and frontend MVP gate were implemented.
3. The local frontend MVP gate proved fixture-only, local-only, evidence-only, non-persistent, non-dispatching, and non-executing behavior.
4. Focused tests and broad gate/report/CI/runner contract tests passed.
5. final-check and run-closeout passed.
6. The round made no solved/static/runtime/audit verification claim for any concrete sample.

Existing capabilities to preserve and not duplicate:

- User-solve result/state/trace/fallback/evidence-quality/session/request/response/handoff/controller/CLI/frontend/local API/schema/UI/error/fixture contracts.
- command-plan, execution-log, project gates, jobs, AgentRunner, pipeline, harness, solver/tool interfaces.
- External specialist tools remain outside this round; this round only prepares metadata, route plans, API contracts, and synthetic trace representation.

Artifact freshness policy:

- Current-round artifacts must carry `decision_20260704_user_solve_workbench_foundation_big_step_v1` and `round_20260704_user_solve_workbench_foundation_big_step_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only and must not be used as current evidence.
- Missing historical sample artifacts are non-blocking for this engineering round.
- Any generated workbench gate artifact must be synthetic/configuration/fixture evidence only.

Negative results:

- `negative_results.json` blocks old solver blind search, budget-only expansion, invalid frontier reuse, full solve_reports commits, and repeated stale diagnostics.
- This round is engineering-only and must not enter those reverse-solving directions.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.
- If `Tests` conflicts with command-plan, command-plan wins.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not process real samples, real user uploads, or training samples.

Do not invoke external analysis tools or add external process execution.

Do not implement interactive tool adapters, production HTTP infrastructure, database, queue, scheduler, remote runner dispatch, CI dispatch/polling, persistent user task/session storage, or real upload ingestion.

Do not create files under `project_state/solve_tasks/`, `project_state/user_sessions/`, or `project_state/jobs/` in this round. Use in-memory synthetic fixtures and gate artifacts only.

Do not add dynamic machine-specific facts to `.codex-skills/`.

Do not mutate forbidden paths listed in `decision_contract`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, statically verified, runtime validated, or audit verified.

Do not hardcode local machine paths as required defaults. Example config may show placeholders only.

Do not duplicate existing command-plan, execution-log, jobs, AgentRunner, pipeline, harness, solver/tool, result/trace/fallback/session/control-plane/frontend responsibilities.

## 4. Files To Inspect

Read first:

1. `project_state/task_packet.json`
2. `project_state/current_state.json`
3. `project_state/artifact_index.json`
4. `project_state/negative_results.json`
5. `project_state/decision_packet.md`
6. `project_state/codex_execution_report.md`
7. `project_state/execution_report.md`
8. `project_state/pytest_result.txt`
9. `.codex-skills/registry.json`

Inspect accepted user-solve/frontend control plane:

1. `reverse_agent/user_solve_request.py`
2. `reverse_agent/user_solve_response.py`
3. `reverse_agent/user_solve_handoff.py`
4. `reverse_agent/user_solve_controller.py`
5. `reverse_agent/user_solve_cli.py`
6. `reverse_agent/user_solve_session.py`
7. `reverse_agent/user_solve.py`
8. `reverse_agent/user_solve_contract.py`
9. `reverse_agent/user_solve_trace.py`
10. `reverse_agent/fallback_ladder.py`
11. `reverse_agent/evidence_quality.py`
12. `reverse_agent/user_solve_frontend_bridge.py`
13. `reverse_agent/user_solve_local_api.py`
14. `reverse_agent/user_solve_api_schema.py`
15. `reverse_agent/user_solve_ui_state.py`
16. `reverse_agent/user_solve_errors.py`
17. `reverse_agent/user_solve_fixtures.py`
18. `frontend/user_solve_demo/README.md`
19. `frontend/user_solve_demo/app.js`
20. `frontend/user_solve_demo/fixtures/catalog.json`
21. existing user-solve tests and docs

Inspect orchestration/tool-adjacent code only to avoid duplication:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `reverse_agent/project_jobs.py`
5. `reverse_agent/project_agent_runner.py`
6. `reverse_agent/project_runner_contract.py`
7. `reverse_agent/pipeline.py`
8. `reverse_agent/harness.py`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless command-plan authorizes a bounded diagnostic.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current decision treated as execution authority and task_packet as background only?
2. Did decision metadata remain valid and aligned with active `reverse-agent-iteration@v2`?
3. Did this decision supersede the smaller tool-profile-only plan without mixing scopes?
4. Was the last accepted local frontend MVP treated as baseline?
5. Were startup and prework provenance commands recorded before implementation validation?
6. Was existing related functionality inspected before adding new modules?
7. Was `reverse_agent/tool_profiles.py` implemented or compatibly extended?
8. Does `ToolProfile` support stable identity, category, path source, availability metadata, capability flags, risk level, disabled/unavailable states, and safe serialization?
9. Does tool profile loading use deterministic precedence without external process execution?
10. Was `reverse_agent/tool_capabilities.py` implemented or compatibly extended?
11. Does `RunnerCapability` represent runner id, platform metadata, available/missing/disabled tools, permission flags, and supported analysis features without dispatching work?
12. Was `reverse_agent/user_solve_route_plan.py` implemented or compatibly extended?
13. Does route planning map request state, missing evidence, capability availability, risk level, and permissions into safe planned next actions without executing them?
14. Was `reverse_agent/user_solve_task_trace.py` implemented or compatibly extended?
15. Does synthetic task trace capture request metadata, fixture/demo source, candidate state, missing evidence, route plan, validation state, and artifact placeholders without persistent task files?
16. Was `reverse_agent/user_solve_workbench.py` implemented or compatibly extended?
17. Does the workbench facade compose existing controller/session/result/UI/error/fixture behavior instead of duplicating it?
18. Was `reverse_agent/user_solve_workbench_api.py` implemented or compatibly extended?
19. Does the workbench API provide route-shaped pure-function handling without production service behavior?
20. Were fixture catalog and frontend/demo fixtures expanded consistently if touched?
21. Were schema snapshots expanded for tool profiles, runner capabilities, route plans, workbench API routes, task traces, fixtures, UI states, and public/developer payloads?
22. Were example configs added with portable placeholders and no secrets?
23. Were CLI previews added for candidate, missing-evidence, blocked, verified, route-plan, capability, and workbench states?
24. Was documentation added or updated for the workbench foundation and future execution boundary?
25. Was a current `user_solve_workbench_result.json` or equivalent gate artifact generated?
26. Was a current `user_solve_workbench_snapshot.json` or equivalent snapshot generated?
27. Do gate artifacts carry current decision/report/round IDs?
28. Do gate artifacts prove no external tool invocation, no real sample analysis, no dispatch, no persistence, and no production service behavior?
29. Do tests cover profile normalization, invalid profile rejection, capability serialization, route planner behavior, task trace serialization/redaction, workbench facade/API behavior, example config validity, schema stability, gates, reports, and CLI previews?
30. Do existing user-solve/frontend/control-plane tests continue passing under command-plan coverage?
31. Did pytest_result record real commands and exit codes?
32. Did command-plan authorize all executed commands and omit no executed commands?
33. Did final-check pass with current IDs?
34. Did run-closeout pass and archive current reports if authorized?
35. Were forbidden files untouched?
36. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?

## 6. Implementation Scope

Allowed implementation:

1. Add or extend `reverse_agent/tool_profiles.py` for deterministic tool metadata.
2. Add or extend `reverse_agent/tool_capabilities.py` for deterministic runner capability metadata.
3. Add or extend `reverse_agent/user_solve_route_plan.py` for planned next-action metadata.
4. Add or extend `reverse_agent/user_solve_task_trace.py` for synthetic workbench task traces.
5. Add or extend `reverse_agent/user_solve_workbench.py` to compose existing user-solve controller, fixtures, UI state mapping, route plans, capabilities, and task trace.
6. Add or extend `reverse_agent/user_solve_workbench_api.py` for route-shaped pure-function local workbench previews.
7. Update existing user-solve modules only as needed for compatibility: fixtures, schema, CLI, controller, frontend bridge, UI state, and errors.
8. Add `.reverse-agent/config/tool_profiles.example.json` and `.reverse-agent/config/user_solve_workbench.example.json` with safe placeholders.
9. Update static demo files only if needed, keeping the demo static and fixture-only.
10. Update `reverse_agent/project_gate.py` with a `user-solve-workbench` gate or equivalent.
11. Add focused tests for the new contracts, facade, API, CLI, schema, gate, and report integration.
12. Add/update documentation for the workbench foundation and future execution boundary.

Compatibility rules:

- Existing accepted tests must continue passing under command-plan coverage.
- New modules must import without optional external reverse-engineering tools installed.
- New logic must be deterministic in unit tests.
- New logic must be configuration/capability/routing/fixture metadata only.
- Future execution must remain controlled by command-plan, execution-log, runner permission profiles, artifact indexing, and gates.

## 7. Tests

Startup sequence must be recorded first:

```powershell
Set-Location F:\reverse-agent
Get-Location
Test-Path F:\reverse-agent
git rev-parse --show-toplevel
git status --short
python -m reverse_agent.project_gate startup-snapshot --state-dir project_state
python -m reverse_agent.project_gate prework-provenance --state-dir project_state
```

Execution policy:

- Generate/read `project_state/gates/command_plan.json` through the existing command-plan flow.
- Execute only commands authorized by `command_plan.commands`.
- Do not execute commands listed in `command_plan.omitted_commands`.
- If this section conflicts with command-plan, command-plan wins.

Expected validation coverage, subject to command-plan authorization:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_tool_profiles.py tests/test_tool_capabilities.py tests/test_user_solve_route_plan.py tests/test_user_solve_task_trace.py tests/test_user_solve_workbench.py tests/test_user_solve_workbench_api.py tests/test_user_solve_api_schema.py tests/test_user_solve_fixtures.py tests/test_user_solve_cli.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.user_solve_cli --demo candidate
python -m reverse_agent.user_solve_cli --demo missing-evidence
python -m reverse_agent.user_solve_cli --demo blocked
python -m reverse_agent.user_solve_cli --demo verified
python -m reverse_agent.user_solve_cli --workbench-demo route-plan
python -m reverse_agent.user_solve_cli --workbench-demo capability
python -m reverse_agent.project_gate user-solve-workbench --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If command-plan profile requires broader validation:

```powershell
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_request.py tests/test_user_solve_response.py tests/test_user_solve_handoff.py tests/test_user_solve_controller.py tests/test_user_solve_cli.py tests/test_user_solve_frontend_bridge.py tests/test_user_solve_local_api.py tests/test_user_solve_api_schema.py tests/test_user_solve_ui_state.py tests/test_user_solve_errors.py tests/test_user_solve_fixtures.py tests/test_tool_profiles.py tests/test_tool_capabilities.py tests/test_user_solve_route_plan.py tests/test_user_solve_task_trace.py tests/test_user_solve_workbench.py tests/test_user_solve_workbench_api.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py tests/test_project_agent_runner.py tests/test_project_runner_contract.py -q
```

If command-plan authorizes closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260704_user_solve_workbench_foundation_big_step_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record actual commands and exit codes. Reports must list real tests in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any condition occurs:

1. Current decision/report/round IDs do not match.
2. `skill_profiles` do not match active registry entries.
3. `task_packet.json` is treated as execution authority.
4. Startup provenance is missing or ambiguous.
5. Any forbidden path is modified.
6. Any real sample analysis or external analysis tool invocation is added.
7. Any real sample, training sample, or user upload is processed.
8. Any production service, database, queue, scheduler, remote dispatch, CI polling, persistent task/session, or real upload flow is added.
9. Any interactive external tool adapter is implemented in this round.
10. A machine-specific local path is hardcoded as a required default.
11. New code duplicates AgentRunner, pipeline, harness, solver, or existing tool interface responsibilities instead of describing or composing them.
12. Missing tool capability is treated as working execution evidence.
13. Planned actions are executed instead of represented as route-plan metadata.
14. Default user serialization leaks internal project paths, developer trace refs, artifact paths, local filesystem details, or machine-specific config.
15. `verified` can be represented without passed validation evidence.
16. Missing evidence is treated as solved evidence.
17. Current-round gate artifacts are missing or carry stale decision/report/round IDs.
18. `user_solve_workbench_result.json` or equivalent is missing.
19. `user_solve_workbench_snapshot.json` or equivalent is missing.
20. Required focused tests are missing.
21. Existing accepted user-solve/frontend/control-plane behavior regresses.
22. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
23. command-plan is missing, stale, or not respected.
24. final-check fails.
25. closeout is executed without command-plan authorization.
26. closeout is required but missing or failed.
27. The final report claims any concrete sample is solved, statically verified, runtime validated, or audit verified.

If only part of the workbench foundation is completed, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
