```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260704_user_solve_frontend_bridge_contract_v1",
  "round_id": "round_20260704_user_solve_frontend_bridge_contract_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_decision_id": "decision_20260703_user_solve_offline_control_plane_big_step_v1",
  "follows_round_id": "round_20260703_user_solve_offline_control_plane_big_step_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_37_user_solve_frontend_bridge_contract",
  "primary_goal": "Turn the accepted offline user-solve control plane into a frontend-ready contract layer: transport-neutral route schema, request/response validation facade, error taxonomy, fixture response catalog, UI state mapping, schema snapshots, gates, tests, and docs.",
  "command_plan_authority_required": true,
  "accepted_requires_frontend_route_contract": true,
  "accepted_requires_schema_snapshot_artifact": true,
  "accepted_requires_ui_state_mapping": true,
  "accepted_requires_fixture_catalog": true,
  "accepted_requires_error_taxonomy": true,
  "accepted_requires_frontend_bridge_gate": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_frontend_bridge.py",
    "reverse_agent/user_solve_api_schema.py",
    "reverse_agent/user_solve_ui_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/user_solve_fixtures.py",
    "reverse_agent/user_solve_request.py",
    "reverse_agent/user_solve_response.py",
    "reverse_agent/user_solve_handoff.py",
    "reverse_agent/user_solve_controller.py",
    "reverse_agent/user_solve_cli.py",
    "reverse_agent/user_solve_session.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_frontend_bridge.py",
    "tests/test_user_solve_api_schema.py",
    "tests/test_user_solve_ui_state.py",
    "tests/test_user_solve_errors.py",
    "tests/test_user_solve_fixtures.py",
    "tests/test_user_solve_request.py",
    "tests/test_user_solve_response.py",
    "tests/test_user_solve_handoff.py",
    "tests/test_user_solve_controller.py",
    "tests/test_user_solve_cli.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_layer.md",
    "docs/user_solve_control_plane.md",
    "docs/user_solve_frontend_bridge.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260704_user_solve_frontend_bridge_contract_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "solve_reports/*",
    ".github/workflows/*",
    "training_materials/local_reverse/*",
    "project_state/solve_tasks/*",
    "project_state/user_sessions/*"
  ],
  "forbidden_capabilities_this_round": [
    "live_http_service",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "external_process_invocation",
    "real_binary_processing",
    "candidate_search",
    "persistent_user_task_or_session_creation",
    "real_user_upload_ingestion"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Frontend Bridge Contract v1**.

The previous accepted round delivered an offline user-solve control plane: request, response envelope, handoff, controller, fixture-only CLI preview, prework provenance, and control-plane gate. This round should move one layer closer to a usable front end by defining the transport-neutral bridge contract that a future UI or local service can consume.

This is a larger engineering step than a narrow cleanup. It should deliver:

1. A frontend route contract describing the intended user-solve operations without starting a live service.
2. A JSON-like schema snapshot for request, response, error, UI state, and fixture payloads.
3. A frontend bridge facade that validates a user-solve request, calls the existing offline controller on fixture data, and returns a frontend-ready response envelope.
4. A UI state mapper that converts internal solve statuses into stable display states such as `ready`, `candidate_pending_validation`, `needs_more_evidence`, `verified`, `blocked`, and `failed`.
5. A user-facing error taxonomy with stable codes, safe messages, retryability, and developer-only diagnostics.
6. A fixture catalog covering candidate, missing-evidence, blocked, failed, and verified demo outputs, all synthetic.
7. A frontend-bridge gate artifact, for example `project_state/gates/user_solve_frontend_bridge_result.json`.
8. A schema snapshot artifact, for example `project_state/gates/user_solve_frontend_schema_snapshot.json`.
9. Tests that prove schema stability, redaction, fixture catalog coverage, UI state mapping, error taxonomy, frontend bridge behavior, and existing control-plane compatibility.
10. Documentation that explains how a future UI should consume the bridge contract and what remains intentionally out of scope.

Accepted target:

- The bridge is transport-neutral and does not start an HTTP server.
- The bridge delegates to the accepted offline controller and does not duplicate result/session/handoff/control-plane logic.
- Default user output contains no internal project paths, artifact paths, developer trace references, or local filesystem details.
- Developer serialization may retain explicit audit diagnostics.
- Fixture catalog outputs are deterministic and snapshot-tested.
- The schema snapshot is current, versioned, and safe for a future front end to consume.
- Existing offline control-plane CLI and gates continue passing.
- No concrete sample is claimed solved, static verified, runtime validated, or audit verified.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`.

Last accepted baseline:

- `decision_20260703_user_solve_offline_control_plane_big_step_v1`
- `round_20260703_user_solve_offline_control_plane_big_step_v1`
- audit outcome: `ACCEPTED`

Evidence from the accepted baseline:

1. The offline control-plane round reported `SUCCESS` and `acceptance_recommendation=ACCEPTED`.
2. `UserSolveRequest`, `UserSolveResponseEnvelope`, `UserSolveHandoffPacket`, `UserSolveController`, and fixture-only CLI preview were implemented.
3. `prework_provenance_result.json` passed and fixed the previous startup provenance limitation.
4. `user_solve_control_plane_result.json` passed and proved the control plane was fixture-only, evidence-only, non-persistent, and non-dispatching.
5. focused and broad tests passed.
6. final-check and run-closeout passed.

Existing capabilities to preserve:

- `UserSolveResult`, `UserSolveTaskTrace`, `FallbackLadder`, `EvidenceQualityMapper`, `UserSolveSessionBundle`, `UserSolveRequest`, `UserSolveResponseEnvelope`, `UserSolveHandoffPacket`, `UserSolveController`, and fixture-only CLI preview.
- command-plan, execution-log, project gates, jobs, AgentRunner, pipeline, harness, solver/tool interfaces.

Artifact freshness policy:

- Current-round artifacts must carry `decision_20260704_user_solve_frontend_bridge_contract_v1` and `round_20260704_user_solve_frontend_bridge_contract_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only.
- Tests must use synthetic in-memory payloads and fixture-only bridge data.

Negative results:

- `negative_results.json` blocks old solver blind search, budget-only expansion, invalid frontier reuse, full solve_reports commits, and repeated stale diagnostics.
- This round is engineering-only and must not enter those directions.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not process real binaries or local user uploads.

Do not implement a live HTTP service, database, queue, scheduler, remote runner, CI dispatch, persistent task/session storage, or real upload ingestion.

Do not invoke external processes or existing solver/harness pipelines in this round.

Do not mutate forbidden paths listed in `decision_contract`.

Do not add dynamic facts to `.codex-skills/`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static verified, runtime validated, or audit verified.

Do not duplicate existing responsibilities: command-plan, execution-log, jobs, AgentRunner, pipeline, harness, solver/tool interfaces, result/trace/fallback/session/control-plane contracts.

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

Inspect current user-solve contracts and control plane:

1. `reverse_agent/user_solve_contract.py`
2. `reverse_agent/user_solve_state.py`
3. `reverse_agent/user_solve.py`
4. `reverse_agent/user_solve_trace.py`
5. `reverse_agent/fallback_ladder.py`
6. `reverse_agent/evidence_quality.py`
7. `reverse_agent/user_solve_session.py`
8. `reverse_agent/user_solve_request.py`
9. `reverse_agent/user_solve_response.py`
10. `reverse_agent/user_solve_handoff.py`
11. `reverse_agent/user_solve_controller.py`
12. `reverse_agent/user_solve_cli.py`
13. existing user-solve tests and docs

Inspect gate/provenance/report code:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `project_state/gates/prework_provenance_result.json`
5. `project_state/gates/user_solve_control_plane_result.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/report_summary_synthesis.json`

Inspect orchestration code only to avoid duplication:

1. `reverse_agent/project_jobs.py`
2. `reverse_agent/project_agent_runner.py`
3. `reverse_agent/project_runner_contract.py`
4. `reverse_agent/pipeline.py`
5. `reverse_agent/harness.py`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless command-plan authorizes a bounded diagnostic.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current decision treated as execution authority and task_packet as background only?
2. Did decision metadata remain valid and aligned with active `reverse-agent-iteration@v2`?
3. Did the round build on the accepted offline control-plane baseline rather than replacing it?
4. Were startup and prework provenance commands recorded and accepted before implementation validation?
5. Was `UserSolveFrontendBridge` or equivalent bridge facade implemented?
6. Does the bridge delegate to `UserSolveController` instead of duplicating control-plane logic?
7. Was `UserSolveApiSchema` or equivalent schema contract implemented?
8. Does the schema snapshot cover request, response, handoff, UI state, error payload, route contract, and fixtures?
9. Was `UserSolveUiState` or equivalent UI state mapper implemented?
10. Does UI state mapping cover candidate pending validation, missing evidence, verified, failed, blocked, and ready/review states?
11. Was `UserSolveError` or equivalent error taxonomy implemented?
12. Do error payloads have stable codes, safe public messages, retryability, and developer diagnostics?
13. Was a deterministic fixture catalog implemented?
14. Does the fixture catalog cover candidate, missing-evidence, blocked, failed, and verified examples?
15. Does default bridge serialization hide internal paths and developer trace refs?
16. Does developer serialization retain audit diagnostics explicitly?
17. Does the bridge remain transport-neutral and avoid starting a live service?
18. Does the bridge avoid persistence, external calls, real-file processing, and dispatch?
19. Does the bridge preserve candidate_found pending-validation behavior?
20. Does the bridge preserve verified requires passed validation behavior?
21. Does the bridge preserve missing-evidence to fallback/deep-analysis behavior?
22. Was a current `user_solve_frontend_bridge_result.json` or equivalent gate artifact generated?
23. Was a current `user_solve_frontend_schema_snapshot.json` or equivalent schema artifact generated?
24. Do gate artifacts carry current decision/report/round IDs?
25. Do gate artifacts prove fixture-only, transport-neutral, safe serialization behavior?
26. Did tests cover schema snapshot stability?
27. Did tests cover fixture catalog coverage and redaction?
28. Did tests cover UI state mapping?
29. Did tests cover error taxonomy?
30. Did tests cover frontend bridge facade behavior?
31. Did existing offline control-plane tests continue passing?
32. Did pytest_result record real commands and exit codes?
33. Did command-plan authorize all executed commands and omit no executed commands?
34. Did final-check pass with current IDs?
35. Did run-closeout pass and archive corrected reports if authorized?
36. Were forbidden files untouched?
37. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_frontend_bridge.py` for transport-neutral bridge facade.
2. Add `reverse_agent/user_solve_api_schema.py` for route/schema snapshots and schema metadata.
3. Add `reverse_agent/user_solve_ui_state.py` for UI-facing state mapping.
4. Add `reverse_agent/user_solve_errors.py` for user-safe error taxonomy.
5. Add `reverse_agent/user_solve_fixtures.py` for deterministic fixture catalog.
6. Update existing request/response/handoff/controller/CLI modules only as needed for bridge compatibility.
7. Update `reverse_agent/project_gate.py` with `user-solve-frontend-bridge` gate and schema snapshot generation.
8. Update report-summary/final-check logic to require the frontend bridge gate for this decision.
9. Add focused tests for bridge, schema, UI state, errors, fixtures, gates, and reports.
10. Update `docs/user_solve_layer.md`, `docs/user_solve_control_plane.md`, and add `docs/user_solve_frontend_bridge.md`.

Compatibility rules:

- Existing accepted tests must continue passing.
- New modules must import without optional reverse-engineering tools installed.
- No real samples, local paths, external processes, or network calls are required.
- Existing project gate/report/closeout semantics must remain compatible.

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
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_request.py tests/test_user_solve_response.py tests/test_user_solve_handoff.py tests/test_user_solve_controller.py tests/test_user_solve_cli.py tests/test_user_solve_frontend_bridge.py tests/test_user_solve_api_schema.py tests/test_user_solve_ui_state.py tests/test_user_solve_errors.py tests/test_user_solve_fixtures.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.user_solve_cli --demo candidate
python -m reverse_agent.user_solve_cli --demo missing-evidence
python -m reverse_agent.project_gate user-solve-frontend-bridge --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If command-plan profile requires broader validation:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py tests/test_project_agent_runner.py tests/test_project_runner_contract.py -q
```

If command-plan authorizes closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260704_user_solve_frontend_bridge_contract_v1
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
6. A live service, database, queue, scheduler, remote dispatch, persistent user session, real upload flow, external process invocation, or real binary processing is added.
7. The bridge uses anything except synthetic in-memory fixture data.
8. User-visible request/response/handoff/bridge output leaks internal paths by default.
9. Developer-only references appear in default user output.
10. `verified` can be represented without passed validation evidence.
11. Missing evidence is treated as solved evidence.
12. Frontend bridge duplicates controller/session/result/trace/fallback responsibilities instead of deriving from existing contracts.
13. Existing offline control-plane behavior regresses.
14. Existing pipeline/harness/job/runner/command-plan/execution-log responsibilities are duplicated or replaced.
15. Required focused tests are missing.
16. `user_solve_frontend_bridge_result.json` or equivalent is missing.
17. `user_solve_frontend_schema_snapshot.json` or equivalent is missing.
18. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
19. command-plan is missing, stale, or not respected.
20. final-check fails.
21. closeout is executed without command-plan authorization.
22. closeout is required but missing or failed.
23. The final report claims any concrete sample is solved, static verified, runtime validated, or audit verified.

If only part of the bridge layer is completed, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
