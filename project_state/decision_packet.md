```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_user_solve_offline_control_plane_big_step_v1",
  "round_id": "round_20260703_user_solve_offline_control_plane_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "supersedes_decision_id": "decision_20260703_user_solve_handoff_provenance_v1",
  "supersedes_round_id": "round_20260703_user_solve_handoff_provenance_v1",
  "follows_last_accepted_decision_id": "decision_20260703_user_solve_session_bundle_v1",
  "follows_last_accepted_round_id": "round_20260703_user_solve_session_bundle_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_36_user_solve_offline_control_plane_big_step",
  "primary_goal": "Build a larger offline user-solve control-plane slice: prework provenance hardening, request contract, offline controller, response envelope, handoff packet, fixture-only CLI preview, gates, reports, tests, and docs.",
  "command_plan_authority_required": true,
  "accepted_requires_prework_provenance_hardening": true,
  "accepted_requires_request_contract": true,
  "accepted_requires_offline_controller": true,
  "accepted_requires_response_envelope": true,
  "accepted_requires_handoff_packet": true,
  "accepted_requires_fixture_only_cli_preview": true,
  "accepted_requires_control_plane_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_request.py",
    "reverse_agent/user_solve_response.py",
    "reverse_agent/user_solve_handoff.py",
    "reverse_agent/user_solve_controller.py",
    "reverse_agent/user_solve_cli.py",
    "reverse_agent/user_solve_session.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_trace.py",
    "reverse_agent/fallback_ladder.py",
    "reverse_agent/evidence_quality.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_request.py",
    "tests/test_user_solve_response.py",
    "tests/test_user_solve_handoff.py",
    "tests/test_user_solve_controller.py",
    "tests/test_user_solve_cli.py",
    "tests/test_user_solve_session.py",
    "tests/test_user_solve.py",
    "tests/test_user_solve_contract.py",
    "tests/test_user_solve_trace.py",
    "tests/test_fallback_ladder.py",
    "tests/test_evidence_quality.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_layer.md",
    "docs/user_solve_control_plane.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260703_user_solve_offline_control_plane_big_step_v1/*"
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
    "web_or_http_api",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "external_tool_execution",
    "real_binary_processing",
    "candidate_search",
    "persistent_user_task_or_session_creation",
    "real_user_upload_ingestion"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Offline User Solve Control Plane Big Step v1**.

This supersedes the smaller `user_solve_handoff_provenance` plan. The new round is intentionally larger: it should produce the first local/offline control-plane slice that can later sit behind a front end. It must still remain fully evidence-only, fixture-only, and non-invasive.

Deliver in one round:

1. Prework provenance hardening so startup dirty source/test/doc ambiguity is mechanically blocking for `SUCCESS` unless explicitly declared as inherited baseline.
2. A safe `UserSolveRequest` contract for future front-end or CLI entry.
3. A stable `UserSolveResponseEnvelope` contract for user-visible answers, candidates, next action, fallback summary, warnings, and errors.
4. A `UserSolveHandoffPacket` derived from `UserSolveSessionBundle`.
5. A non-invasive `UserSolveController` that composes existing result, trace, fallback, evidence, session, handoff, and response components.
6. A fixture-only CLI preview such as `python -m reverse_agent.user_solve_cli --demo candidate` and `--demo missing-evidence`.
7. A control-plane gate artifact such as `project_state/gates/user_solve_control_plane_result.json`.
8. A prework provenance gate artifact such as `project_state/gates/prework_provenance_result.json`.
9. Focused and broad tests proving request/response/controller/handoff/CLI/provenance behavior.
10. Documentation explaining the local control-plane boundary and how it will later connect to a UI without changing solver/tool responsibilities.

Accepted target:

- The round cannot report `SUCCESS` if the first startup status has undeclared dirty source/test/doc files.
- Request, response, handoff, controller, and CLI preview contracts exist and are tested.
- Default user serialization contains no internal project paths, artifact paths, developer trace references, or local filesystem details.
- Developer serialization may retain explicit audit references.
- The controller and CLI preview use synthetic in-memory fixtures only.
- The round does not implement Web/API, persistence, queueing, remote dispatch, CI dispatch, external tool execution, real binary processing, candidate search, or persistent user sessions.
- No concrete sample is claimed solved, static verified, runtime validated, or audit verified.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only and states `execution_scope=decision_packet_controls_current_round`.

This decision supersedes the smaller plan:

- `decision_20260703_user_solve_handoff_provenance_v1`
- `round_20260703_user_solve_handoff_provenance_v1`

Last accepted baseline:

- `decision_20260703_user_solve_session_bundle_v1`
- `round_20260703_user_solve_session_bundle_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the last accepted round:

1. The session-bundle round reported `SUCCESS` and `acceptance_recommendation=ACCEPTED`.
2. Focused and broad tests passed.
3. `user_solve_session_bundle_result.json` passed and proved the session bundle was evidence-only, non-dispatching, non-persistent, and safe by default.
4. final-check passed and required the session-bundle gate.
5. run-closeout passed and close-round reached `CLOSED`.
6. The remaining limitation was startup provenance ambiguity: the first recorded status already showed in-scope source/test/doc changes, so the next round must harden this into a mechanical policy.

Existing capabilities to preserve:

- `UserSolveResult`, `UserSolveTaskTrace`, `FallbackLadder`, `EvidenceQualityMapper`, and `UserSolveSessionBundle`.
- command-plan, execution-log, project gates, jobs, AgentRunner, pipeline, harness, solver/tool interfaces.

Artifact freshness policy:

- Current-round artifacts must carry `decision_20260703_user_solve_offline_control_plane_big_step_v1` and `round_20260703_user_solve_offline_control_plane_big_step_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only.
- Tests must use synthetic in-memory payloads and fixture-only CLI preview data.

Negative results:

- `negative_results.json` blocks old solver blind search, budget-only expansion, invalid frontier reuse, full solve_reports commits, and repeated stale diagnostics.
- This round must remain engineering-only and must not enter those directions.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not process real binaries or local user uploads.

Do not implement Web/API routing, HTTP service, database, queue, scheduler, remote runner, CI dispatch, persistent task/session storage, or real upload ingestion.

Do not execute external reverse-engineering tools or existing solver/harness pipelines in this round.

Do not mutate forbidden paths listed in `decision_contract`.

Do not add dynamic facts to `.codex-skills/`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static verified, runtime validated, or audit verified.

Do not duplicate existing project responsibilities: command-plan, execution-log, jobs, AgentRunner, pipeline, harness, solver/tool interfaces, result/trace/fallback/session contracts.

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

Inspect user-solve contracts:

1. `reverse_agent/user_solve_contract.py`
2. `reverse_agent/user_solve_state.py`
3. `reverse_agent/user_solve.py`
4. `reverse_agent/user_solve_trace.py`
5. `reverse_agent/fallback_ladder.py`
6. `reverse_agent/evidence_quality.py`
7. `reverse_agent/user_solve_session.py`
8. existing user-solve tests and docs

Inspect gate/provenance/report code:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `project_state/gates/startup_snapshot.json`
5. `project_state/gates/round_baseline.json`
6. `project_state/gates/round_delta_summary.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/final_gate_result.json`
9. `project_state/gates/user_solve_session_bundle_result.json`

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
3. Did this decision supersede the smaller handoff/provenance plan without mixing scopes?
4. Were startup commands recorded before gates/tests?
5. Was prework provenance captured and enforced?
6. Did undeclared startup dirty source/test/doc files block `SUCCESS`?
7. Was `prework_provenance_result.json` or equivalent generated with current IDs?
8. Was `UserSolveRequest` implemented and tested?
9. Does request validation reject real-file execution semantics and unsafe internal references?
10. Was `UserSolveResponseEnvelope` implemented and tested?
11. Does response serialization include status, answer/candidate, confidence, validation status, evidence status, public message, next action, fallback summary, warnings/errors, and developer audit fields?
12. Was `UserSolveHandoffPacket` implemented and derived from `UserSolveSessionBundle`?
13. Does handoff serialization preserve user/developer boundaries?
14. Was `UserSolveController` implemented and tested?
15. Does the controller compose existing result/trace/fallback/evidence/session/handoff components?
16. Does the controller avoid external tool execution, persistence, dispatch, and real binary processing?
17. Was fixture-only CLI preview implemented and tested?
18. Does CLI preview emit safe response envelopes for candidate and missing-evidence demos?
19. Does CLI preview avoid persistence, external calls, real-file processing, and dispatch?
20. Does the control plane preserve candidate_found pending-validation behavior?
21. Does the control plane preserve verified requires passed validation behavior?
22. Does the control plane preserve missing-evidence to fallback/deep-analysis behavior?
23. Does user serialization hide internal paths and developer trace refs by default?
24. Does developer serialization retain audit references explicitly?
25. Was `user_solve_control_plane_result.json` or equivalent generated with current IDs?
26. Does the gate artifact prove non-invasive behavior and fixture-only operation?
27. Did tests cover prework provenance clean start, dirty-start block, and explicit inherited baseline?
28. Did tests cover request, response, handoff, controller, CLI, and report generation?
29. Did existing user-solve/session/trace/fallback/evidence tests continue passing?
30. Did pytest_result record real commands and exit codes?
31. Did command-plan authorize all executed commands and omit no executed commands?
32. Did final-check pass with current IDs?
33. Did run-closeout pass and archive corrected reports if authorized?
34. Were forbidden files untouched?
35. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_request.py` for request/input contract and validation.
2. Add `reverse_agent/user_solve_response.py` for response envelope, warning/error payloads, and serialization.
3. Add `reverse_agent/user_solve_handoff.py` for handoff packet derived from session bundle.
4. Add `reverse_agent/user_solve_controller.py` for non-invasive offline controller composition.
5. Add `reverse_agent/user_solve_cli.py` for fixture-only CLI preview.
6. Update existing user-solve/session/trace/fallback/evidence modules only for compatibility and without regressing accepted behavior.
7. Update `reverse_agent/project_gate.py` with `prework-provenance` and `user-solve-control-plane` checks.
8. Update report-summary/final-check logic so ambiguous startup dirty state blocks `SUCCESS`.
9. Add focused tests for all new contracts, controller, CLI preview, provenance, gates, and reports.
10. Update `docs/user_solve_layer.md` and add `docs/user_solve_control_plane.md`.

Compatibility rules:

- Existing accepted tests must continue passing.
- New modules must import without optional reverse-engineering tools installed.
- No real samples, local paths, subprocesses, or network calls are required.
- Existing project gate/report/closeout semantics must remain compatible except for intentional provenance hardening.

## 7. Tests

Startup sequence must be recorded first and must be true pre-work capture:

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
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_request.py tests/test_user_solve_response.py tests/test_user_solve_handoff.py tests/test_user_solve_controller.py tests/test_user_solve_cli.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.user_solve_cli --demo candidate
python -m reverse_agent.user_solve_cli --demo missing-evidence
python -m reverse_agent.project_gate user-solve-control-plane --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_user_solve_offline_control_plane_big_step_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record actual commands and exit codes. Reports must list real tests in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any condition occurs:

1. Current decision/report/round IDs do not match.
2. `skill_profiles` do not match active registry entries.
3. `task_packet.json` is treated as execution authority.
4. The superseded smaller plan is used as execution scope.
5. Startup provenance is missing or ambiguous.
6. The first startup status shows undeclared dirty source/test/doc files and the report still claims `SUCCESS`.
7. Any forbidden path is modified.
8. Real binary processing, external tool execution, persistence, remote dispatch, Web/API, DB/queue, scheduler, or CI dispatch is added.
9. Persistent solve task or user session files are created.
10. The controller or CLI preview uses anything except synthetic in-memory fixture data.
11. User-visible request/response/handoff output leaks internal paths by default.
12. Developer-only references appear in default user output.
13. `verified` can be represented without passed validation evidence.
14. Missing evidence is treated as solved evidence.
15. Handoff or response duplicates session/result/trace/fallback responsibilities instead of deriving from existing contracts.
16. Existing user-solve result/trace/fallback/session behavior regresses.
17. Existing pipeline/harness/job/runner/command-plan/execution-log responsibilities are duplicated or replaced.
18. Required focused tests are missing.
19. `prework_provenance_result.json` or equivalent is missing.
20. `user_solve_control_plane_result.json` or equivalent is missing.
21. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
22. command-plan is missing, stale, or not respected.
23. final-check fails.
24. closeout is executed without command-plan authorization.
25. closeout is required but missing or failed.
26. The final report claims any concrete sample is solved, static verified, runtime validated, or audit verified.

If only part of the larger control-plane slice is completed, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
