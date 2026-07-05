```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1",
  "round_id": "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260704_user_solve_workbench_foundation_big_step_v1",
  "follows_last_accepted_round_id": "round_20260704_user_solve_workbench_foundation_big_step_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_39_manual_mode_web_orchestrator_mvp_big_step",
  "primary_goal": "Build a larger Manual Mode Web Orchestrator MVP over the accepted user-solve workbench foundation: local file-backed task lifecycle, project job lifecycle, manual execution handoff, manual result import, planner/auditor context snapshots, static web console demo, route-shaped in-process API facade, configuration profile examples, gates, reports, docs, and tests. This round may create bounded demo files under project_state/solve_tasks and project_state/jobs, but must not process real samples, call external analysis tools, dispatch runners, invoke model APIs, create a production service, or modify GitHub workflows.",
  "command_plan_authority_required": true,
  "accepted_requires_task_lifecycle": true,
  "accepted_requires_job_lifecycle": true,
  "accepted_requires_manual_handoff_bridge": true,
  "accepted_requires_manual_result_import": true,
  "accepted_requires_planner_auditor_context_snapshots": true,
  "accepted_requires_static_web_console_demo": true,
  "accepted_requires_orchestrator_gate_artifacts": true,
  "accepted_requires_no_real_execution": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_task_lifecycle.py",
    "reverse_agent/user_solve_task_store.py",
    "reverse_agent/user_solve_manual_import.py",
    "reverse_agent/user_solve_task_api.py",
    "reverse_agent/manual_execution_handoff.py",
    "reverse_agent/manual_result_bridge.py",
    "reverse_agent/orchestrator_context.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/orchestrator_console_schema.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/project_runner_contract.py",
    "reverse_agent/user_solve_workbench.py",
    "reverse_agent/user_solve_workbench_api.py",
    "reverse_agent/user_solve_api_schema.py",
    "reverse_agent/user_solve_cli.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_task_lifecycle.py",
    "tests/test_user_solve_task_store.py",
    "tests/test_user_solve_manual_import.py",
    "tests/test_user_solve_task_api.py",
    "tests/test_manual_execution_handoff.py",
    "tests/test_manual_result_bridge.py",
    "tests/test_orchestrator_context.py",
    "tests/test_orchestrator_api.py",
    "tests/test_orchestrator_console_schema.py",
    "tests/test_project_jobs.py",
    "tests/test_project_runner_contract.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_frontend_files": [
    "frontend/manual_mode_console/index.html",
    "frontend/manual_mode_console/app.js",
    "frontend/manual_mode_console/style.css",
    "frontend/manual_mode_console/README.md",
    "frontend/manual_mode_console/fixtures/*.json"
  ],
  "allowed_config_files": [
    ".reverse-agent/config/manual_mode_orchestrator.example.json",
    ".reverse-agent/config/planner_profiles.example.json",
    ".reverse-agent/config/auditor_profiles.example.json",
    ".reverse-agent/config/runner_profiles.example.json",
    ".reverse-agent/config/permission_profiles.example.json"
  ],
  "allowed_documentation_files": [
    "docs/manual_mode_web_orchestrator.md",
    "docs/user_solve_task_lifecycle.md",
    "docs/manual_execution_handoff.md",
    "docs/orchestrator_context.md",
    "docs/user_solve_workbench.md",
    "docs/user_solve_layer.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/solve_tasks/demo_*.json",
    "project_state/jobs/job_demo_*.json",
    "project_state/rounds/round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1/*"
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
    "project_state/user_sessions/*"
  ],
  "forbidden_capabilities_this_round": [
    "real_sample_analysis_execution",
    "real_user_upload_ingestion",
    "binary_parsing_or_unpacking",
    "external_analysis_tool_invocation",
    "candidate_search_on_real_samples",
    "runtime_validation_on_real_samples",
    "automatic_runner_dispatch",
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

Implement **Manual Mode Web Orchestrator MVP Big Step v1**.

The accepted baseline has a fixture-only user-solve workbench foundation. The next step should not merely add task files. It should build the first complete manual-mode orchestration loop that a Web console can display and drive without granting automatic execution authority.

Deliver in one round:

1. A local file-backed user-solve task lifecycle for bounded demo tasks under `project_state/solve_tasks/demo_*.json`.
2. A project job lifecycle for bounded demo jobs under `project_state/jobs/job_demo_*.json`.
3. A manual execution handoff bridge that generates reviewable Codex/manual-runner prompt packets from the active decision and command-plan, without invoking a runner.
4. A manual result import bridge that validates structured JSON results and merges them into task/job status, execution summaries, and audit-ready evidence snapshots.
5. Planner/auditor context snapshot builders that assemble bounded context from default project_state files, gates, reports, and registry into deterministic JSON artifacts, without invoking model APIs.
6. A local in-process orchestrator API facade with route-shaped pure functions for dashboard summary, current decision, command-plan summary, job list/detail, task list/detail, handoff export, result import preview, gate summary, audit summary, and available actions.
7. A static Web console demo under `frontend/manual_mode_console/` that reads fixture JSON only and shows Dashboard, Decision, Command-plan, Jobs, Tasks, Handoff, Import, Gate, Audit, and Settings/Profile panels.
8. Config profile examples for planner, auditor, runner, permission, and manual-mode orchestrator settings. These must contain placeholders only and no secrets.
9. Project gate integration that emits `project_state/gates/manual_mode_orchestrator_result.json` and `project_state/gates/manual_mode_orchestrator_snapshot.json`.
10. CLI previews for dashboard summary, create demo job/task, export handoff, import manual result, show available actions, and render static-console fixture bundle.
11. Focused tests plus report-summary, final-check, and run-closeout integration.
12. Documentation showing how this manual-mode orchestrator preserves decision authority, command-plan authority, execution-log evidence, final-check, and LLM audit boundaries.

Accepted target:

- This is an engineering-branch orchestration round.
- It is local, deterministic, file-backed only for bounded demo task/job artifacts, and safe for manual workflows.
- It creates the UI/API shape for Web-driven manual execution but does not execute agents, external tools, real analysis, model API calls, GitHub workflows, or remote dispatch.
- It does not process real samples or uploads.
- It does not claim any concrete sample is solved, statically verified, runtime validated, or audit verified.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`.

Last accepted baseline:

- `decision_20260704_user_solve_workbench_foundation_big_step_v1`
- `round_20260704_user_solve_workbench_foundation_big_step_v1`
- audit outcome: `ACCEPTED`

Accepted baseline evidence:

1. The workbench foundation report was `SUCCESS` with `acceptance_recommendation=ACCEPTED`.
2. Tool profile, runner capability, route plan, synthetic task trace, workbench facade, workbench API, schema snapshot, CLI preview, docs, tests, and workbench gate were implemented.
3. `user_solve_workbench_result.json` proved fixture-only, local-only, evidence-only, non-dispatching, non-persistent, and non-service behavior.
4. Focused and broad tests passed.
5. final-check and run-closeout passed.
6. The accepted workbench round made no solved/static/runtime/audit verification claim for any concrete sample.

Existing capabilities to preserve and not duplicate:

- User-solve contracts, state, trace, fallback, evidence quality, request/response/handoff/controller/CLI, frontend bridge, local API, schema, UI state, errors, fixtures, workbench facade, workbench API, tool profiles, runner capability, route planning, command-plan, execution-log, project gates, jobs, AgentRunner, pipeline, harness, solver/tool interfaces.
- This round composes those capabilities into a manual-mode orchestration surface. It must not replace them with a parallel framework.

Artifact freshness policy:

- Current-round artifacts must carry `decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1` and `round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only and must not be used as current evidence.
- Missing historical sample artifacts are non-blocking for this engineering round.
- Demo task/job artifacts are current only if generated by this round and named under the allowed `demo_*` patterns.

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

Do not process real samples, real uploads, or training samples.

Do not invoke external analysis tools or add external process execution for analysis.

Do not invoke model APIs, planner APIs, auditor APIs, Codex CLI, remote agents, CI workflows, or any automatic runner.

Do not implement production HTTP infrastructure, database, queue, scheduler, background service, remote dispatch, CI polling, or auto-iteration.

Do not modify `.github/workflows/*` in this round.

Do not add dynamic machine-specific facts to `.codex-skills/`.

Do not mutate forbidden paths listed in `decision_contract`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, statically verified, runtime validated, or audit verified.

Do not hardcode local machine paths as required defaults. Example configs must use placeholders.

Do not create arbitrary user task/session files. Only bounded demo task/job files matching the allowed patterns may be generated.

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

Inspect accepted workbench and user-solve surfaces:

1. `reverse_agent/user_solve_workbench.py`
2. `reverse_agent/user_solve_workbench_api.py`
3. `reverse_agent/user_solve_task_trace.py`
4. `reverse_agent/user_solve_route_plan.py`
5. `reverse_agent/user_solve_api_schema.py`
6. `reverse_agent/user_solve_cli.py`
7. `reverse_agent/user_solve_controller.py`
8. `reverse_agent/user_solve_fixtures.py`
9. `reverse_agent/tool_profiles.py`
10. `reverse_agent/tool_capabilities.py`
11. `frontend/user_solve_demo/README.md`
12. relevant user-solve tests and docs

Inspect orchestration and gate surfaces:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_jobs.py`
3. `reverse_agent/project_runner_contract.py`
4. `reverse_agent/project_agent_runner.py`
5. `tests/test_project_gate.py`
6. `tests/test_project_reports.py`
7. `tests/test_project_jobs.py`
8. `tests/test_project_runner_contract.py`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless command-plan authorizes a bounded diagnostic.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current decision treated as execution authority and task_packet as background only?
2. Did decision metadata remain valid and aligned with active `reverse-agent-iteration@v2`?
3. Was the accepted workbench foundation treated as the baseline?
4. Were startup and prework provenance commands recorded before implementation validation?
5. Was existing workbench/job/runner/gate functionality inspected before adding new modules?
6. Was `UserSolveTaskLifecycle` implemented or compatibly extended?
7. Are task status transitions deterministic, bounded, and validated?
8. Was a file-backed demo-only task store implemented under `project_state/solve_tasks/demo_*.json`?
9. Does the task store reject non-demo paths, unsafe names, unexpected schema, and arbitrary persistence?
10. Was a project job lifecycle/demo job layer implemented or compatibly extended under `project_state/jobs/job_demo_*.json`?
11. Does job lifecycle distinguish DRAFT, READY, MANUAL_DISPATCHED, MANUAL_RESULT_IMPORTED, FINAL_CHECKED, AUDITED, ACCEPTED, REWORK_REQUIRED, and BLOCKED without dispatching runners?
12. Was a manual execution handoff bridge implemented?
13. Does handoff export preserve decision authority, command-plan authority, allowed commands, omitted commands, stop conditions, and no-push/no-remote constraints?
14. Was a manual result import bridge implemented?
15. Does manual import validate structured JSON and reject unsupported file paths, arbitrary command claims, stale IDs, and real execution claims?
16. Were planner/auditor context snapshots implemented without invoking model APIs?
17. Do context snapshots read only bounded default files and current gate/report artifacts?
18. Was a local orchestrator API facade implemented as route-shaped pure functions?
19. Does the API facade expose dashboard, decision, command-plan, job, task, handoff, import preview, gate, audit, and available-action views without a production service?
20. Was a static manual-mode console demo added with fixture JSON only?
21. Does the static console avoid frameworks, build steps, network calls, and direct mutation of project_state?
22. Were config profile examples added with placeholders and no secrets?
23. Were demo task/job artifacts generated and bounded to allowed patterns?
24. Were schema snapshots generated for task, job, handoff, import, context, console, and orchestrator API payloads?
25. Were CLI previews added for dashboard, demo task/job creation, handoff export, manual import preview, available actions, and console fixture bundle?
26. Was documentation added for manual-mode Web orchestration and future automation boundaries?
27. Was a current `manual_mode_orchestrator_result.json` or equivalent gate artifact generated?
28. Was a current `manual_mode_orchestrator_snapshot.json` or equivalent snapshot generated?
29. Do gate artifacts carry current decision/report/round IDs?
30. Do gate artifacts prove no real sample processing, no external analysis execution, no runner dispatch, no model API invocation, no production service, no database, and no CI dispatch?
31. Do focused tests cover lifecycle, task store, job lifecycle, handoff export, result import, context snapshots, API facade, static console fixture bundle, config examples, CLI previews, gates, and reports?
32. Do existing user-solve/workbench/control-plane tests continue passing under command-plan coverage?
33. Did pytest_result record real commands and exit codes?
34. Did command-plan authorize all executed commands and omit no executed commands?
35. Did final-check pass with current IDs?
36. Did run-closeout pass and archive current reports if authorized?
37. Were forbidden files untouched?
38. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_task_lifecycle.py` for task status transition policy.
2. Add `reverse_agent/user_solve_task_store.py` for demo-only task JSON read/write validation.
3. Add `reverse_agent/user_solve_manual_import.py` for structured manual result import validation and merge logic.
4. Add `reverse_agent/user_solve_task_api.py` for pure-function task routes.
5. Add `reverse_agent/manual_execution_handoff.py` for Codex/manual-runner handoff packet generation without execution.
6. Add `reverse_agent/manual_result_bridge.py` for job/task result import preview and evidence summary conversion.
7. Add `reverse_agent/orchestrator_context.py` for bounded planner/auditor context snapshots without model calls.
8. Add `reverse_agent/orchestrator_api.py` for route-shaped pure functions backing the static console.
9. Add `reverse_agent/orchestrator_console_schema.py` for static console fixture/schema payloads.
10. Extend `project_jobs.py` and `project_runner_contract.py` only for demo/manual lifecycle fields and non-dispatching validation.
11. Extend existing workbench/API/schema/CLI only as needed to expose task/job/handoff/import previews.
12. Add `frontend/manual_mode_console/` as a static fixture-only demo.
13. Add example configs for planner, auditor, runner, permission, and manual orchestrator profiles.
14. Update `project_gate.py` with a `manual-mode-orchestrator` gate or equivalent.
15. Generate bounded demo task and demo job artifacts under allowed patterns.
16. Add focused tests and docs.

Compatibility rules:

- Existing accepted tests must continue passing under command-plan coverage.
- New logic must be deterministic in unit tests.
- New modules must import without optional external tools or API credentials.
- Manual-mode handoff is export-only; it must not execute.
- Manual import is structured JSON validation/merge only; it must not trust arbitrary claims as verified evidence.
- Future automation must remain controlled by decision, command-plan, execution-log, final-check, and audit.

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
python -m pytest tests/test_user_solve_task_lifecycle.py tests/test_user_solve_task_store.py tests/test_user_solve_manual_import.py tests/test_user_solve_task_api.py tests/test_manual_execution_handoff.py tests/test_manual_result_bridge.py tests/test_orchestrator_context.py tests/test_orchestrator_api.py tests/test_orchestrator_console_schema.py tests/test_project_jobs.py tests/test_project_runner_contract.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.user_solve_cli --manual-console-demo dashboard
python -m reverse_agent.user_solve_cli --manual-console-demo create-demo-task
python -m reverse_agent.user_solve_cli --manual-console-demo create-demo-job
python -m reverse_agent.user_solve_cli --manual-console-demo export-handoff
python -m reverse_agent.user_solve_cli --manual-console-demo import-result-preview
python -m reverse_agent.user_solve_cli --manual-console-demo available-actions
python -m reverse_agent.project_gate manual-mode-orchestrator --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If command-plan profile requires broader validation:

```powershell
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_request.py tests/test_user_solve_response.py tests/test_user_solve_handoff.py tests/test_user_solve_controller.py tests/test_user_solve_cli.py tests/test_user_solve_frontend_bridge.py tests/test_user_solve_local_api.py tests/test_user_solve_api_schema.py tests/test_user_solve_ui_state.py tests/test_user_solve_errors.py tests/test_user_solve_fixtures.py tests/test_tool_profiles.py tests/test_tool_capabilities.py tests/test_user_solve_route_plan.py tests/test_user_solve_task_trace.py tests/test_user_solve_workbench.py tests/test_user_solve_workbench_api.py tests/test_user_solve_task_lifecycle.py tests/test_user_solve_task_store.py tests/test_user_solve_manual_import.py tests/test_user_solve_task_api.py tests/test_manual_execution_handoff.py tests/test_manual_result_bridge.py tests/test_orchestrator_context.py tests/test_orchestrator_api.py tests/test_orchestrator_console_schema.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py tests/test_project_agent_runner.py tests/test_project_runner_contract.py -q
```

If command-plan authorizes closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1
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
6. Any real sample processing, upload parsing, external analysis execution, runner dispatch, model API invocation, production service, database, queue, scheduler, CI dispatch, or auto-iteration is added.
7. `.github/workflows/*` is modified.
8. Arbitrary task/job files outside the allowed demo patterns are created.
9. Manual import treats arbitrary user claims as verified evidence.
10. Handoff export executes commands or mutates remote state.
11. Static console performs network calls, build steps, or direct project_state mutation.
12. Context snapshots read full solve_reports or full PROJECT_PROGRESS_LOG without command-plan authorization.
13. Demo task/job artifacts carry stale IDs or unsafe paths.
14. Current-round gate artifacts are missing or carry stale decision/report/round IDs.
15. `manual_mode_orchestrator_result.json` or equivalent is missing.
16. `manual_mode_orchestrator_snapshot.json` or equivalent is missing.
17. Required focused tests are missing.
18. Existing accepted user-solve/workbench/control-plane behavior regresses.
19. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
20. command-plan is missing, stale, or not respected.
21. final-check fails.
22. closeout is executed without command-plan authorization.
23. closeout is required but missing or failed.
24. The final report claims any concrete sample is solved, statically verified, runtime validated, or audit verified.

If only part of the manual-mode orchestrator MVP is completed, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
