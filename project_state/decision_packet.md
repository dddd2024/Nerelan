```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260704_user_solve_tool_profile_capability_v1",
  "round_id": "round_20260704_user_solve_tool_profile_capability_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260704_user_solve_local_frontend_mvp_big_step_v1",
  "follows_last_accepted_round_id": "round_20260704_user_solve_local_frontend_mvp_big_step_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_38_user_solve_tool_profile_capability_v1",
  "primary_goal": "Add a deterministic tool profile and runner capability contract layer for future user-solve real-analysis routing, without invoking IDA/Ghidra/debuggers, processing binaries, creating services, or dispatching runners.",
  "command_plan_authority_required": true,
  "accepted_requires_tool_profile_contract": true,
  "accepted_requires_runner_capability_contract": true,
  "accepted_requires_example_config": true,
  "accepted_requires_gate_artifact": true,
  "accepted_requires_no_external_tool_invocation": true,
  "allowed_source_files": [
    "reverse_agent/tool_profiles.py",
    "reverse_agent/tool_capabilities.py",
    "reverse_agent/project_gate.py",
    "tests/test_tool_profiles.py",
    "tests/test_tool_capabilities.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_config_files": [
    ".reverse-agent/config/tool_profiles.example.json"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_tool_profiles.md",
    "docs/user_solve_layer.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260704_user_solve_tool_profile_capability_v1/*"
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
    "frontend/user_solve_demo/*"
  ],
  "forbidden_capabilities_this_round": [
    "ida_execution",
    "ghidra_execution",
    "ollydbg_execution",
    "debugger_execution",
    "emulator_execution",
    "external_process_invocation",
    "real_binary_processing",
    "real_user_upload_ingestion",
    "candidate_search",
    "solver_execution",
    "runtime_probe",
    "dynamic_debug",
    "ida_mcp_adapter",
    "production_http_service",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "ci_dispatch_or_polling",
    "persistent_user_task_or_session_creation"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Tool Profile and Runner Capability Contract v1**.

The previous accepted round delivered a local, fixture-only frontend MVP over the offline user-solve control plane. The next safe step is not real upload handling, real IDA/Ghidra execution, IDA MCP, Web service infrastructure, or reverse sample solving. The next step is to add the configuration and capability contract layer that future user-solve routing will need before any real analysis backend is enabled.

Deliver in this round:

1. A deterministic `ToolProfile` contract for configured reverse-engineering tools such as IDA, Ghidra, OllyDbg, x64dbg, radare2, solver, harness, and local script capabilities.
2. A deterministic `RunnerCapability` contract describing what a runner can support without dispatching the runner or invoking tools.
3. A bounded loader for example config, environment-provided paths, explicit overrides, and synthetic test fixtures. It must not execute external processes.
4. A `.reverse-agent/config/tool_profiles.example.json` file showing portable configuration structure without storing local secrets or mandatory machine-specific paths.
5. A `project_gate` check that emits `project_state/gates/tool_profile_capability_result.json` and proves the contract layer is schema-valid, deterministic, non-dispatching, and non-invasive.
6. Tests for profile normalization, path-source priority, runner capability serialization, forbidden execution behavior, example config validity, gate output, and report/final-check integration.
7. Documentation explaining how tool profiles and runner capabilities will later support real user-solve routing, while preserving command-plan, execution-log, artifact, and permission boundaries.

Accepted target:

- This is an engineering foundation round.
- No real binary is processed.
- No IDA, Ghidra, debugger, emulator, solver, harness, or external process is invoked.
- No production API, scheduler, queue, database, remote runner, persistent session, or upload pipeline is added.
- No concrete sample is claimed solved, static verified, runtime validated, or audit verified.
- The result should make later real-analysis routing safer by eliminating hidden hardcoded assumptions about the local Windows machine or IDA path.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`.

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

- User-solve contracts, trace, fallback ladder, evidence quality mapper, session bundle, request/response/handoff/controller/CLI, frontend bridge, local API, schema, UI state, errors, fixtures, static demo, command-plan, execution-log, project gates, jobs, AgentRunner, pipeline, harness, solver/tool interfaces.
- Mature external reverse-engineering tools remain responsible for disassembly, decompilation, debugging, and evidence extraction. This project only records configuration/capability metadata in this round.

Artifact freshness policy:

- Current-round artifacts must carry `decision_20260704_user_solve_tool_profile_capability_v1` and `round_20260704_user_solve_tool_profile_capability_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only and must not be used as current evidence.
- Missing historical sample artifacts are non-blocking for this engineering round.
- Any generated tool-profile gate artifact must be synthetic/configuration evidence only, not proof that IDA/Ghidra/debugger execution works.

Negative results:

- `negative_results.json` blocks old solver blind search, budget-only expansion, invalid frontier reuse, full solve_reports commits, and repeated stale diagnostics.
- This round is engineering-only and must not enter those reverse-solving directions.

Tool-interface caution:

- Before implementing, inspect the existing runner, pipeline, harness, solver, and project gate surfaces to avoid duplicating established responsibilities.
- If any relevant tool-profile or capability module already exists, extend it compatibly rather than creating a parallel mechanism.
- Do not assume the project lacks IDA/Ghidra/debugger interfaces.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.
- If `Tests` conflicts with command-plan, command-plan wins.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not process real binaries, real user uploads, or training samples.

Do not invoke IDA, Ghidra, OllyDbg, x64dbg, radare2, emulators, debuggers, solvers, harness runtime probes, or arbitrary external commands.

Do not implement IDA MCP, MCP adapters, remote mutation, patching, decompilation calls, xref queries, or interactive tool control.

Do not implement production HTTP infrastructure, database, queue, scheduler, remote runner dispatch, CI dispatch/polling, persistent user task/session storage, or real upload ingestion.

Do not add dynamic machine-specific facts to `.codex-skills/`.

Do not mutate forbidden paths listed in `decision_contract`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static verified, runtime validated, or audit verified.

Do not hardcode the user's local IDA/Ghidra/debugger path as a required default. Example config may show placeholder paths only.

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
18. existing user-solve tests and docs

Inspect orchestration/tool-adjacent code to avoid duplication:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `reverse_agent/project_jobs.py`
5. `reverse_agent/project_agent_runner.py`
6. `reverse_agent/project_runner_contract.py`
7. `reverse_agent/pipeline.py`
8. `reverse_agent/harness.py`
9. existing solver/tool interface modules discovered by bounded file-name search, if command-plan authorizes such inspection

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless command-plan authorizes a bounded diagnostic.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current decision treated as execution authority and task_packet as background only?
2. Did decision metadata remain valid and aligned with active `reverse-agent-iteration@v2`?
3. Was the last accepted local frontend MVP treated as the baseline, without reopening that round's scope?
4. Were startup and prework provenance commands recorded before implementation validation?
5. Was an existing tool/profile/capability implementation searched for or boundedly inspected before adding new modules?
6. Was `reverse_agent/tool_profiles.py` implemented or compatibly extended?
7. Does `ToolProfile` support stable tool identity, category, configured path, path source, availability metadata, capability flags, risk level, and safe serialization?
8. Does tool profile loading use deterministic precedence without executing external processes?
9. Does the implementation avoid hardcoding a required local IDA/Ghidra/debugger path?
10. Was `reverse_agent/tool_capabilities.py` implemented or compatibly extended?
11. Does `RunnerCapability` represent runner id, platform metadata, available/missing tools, permission flags, and supported analysis features without dispatching work?
12. Can runner capability serialization distinguish configured, discovered, unavailable, and disabled tools?
13. Was `.reverse-agent/config/tool_profiles.example.json` added with portable placeholders and no secrets?
14. Was documentation added for tool profile/capability usage and future routing semantics?
15. Was a `project_gate` check added for tool profile/capability validation?
16. Was a current `project_state/gates/tool_profile_capability_result.json` or equivalent gate artifact generated?
17. Does the gate artifact carry current decision/report/round IDs?
18. Does the gate artifact prove no external tool invocation, no binary processing, no dispatch, and no persistence?
19. Do tests cover valid profile normalization and serialization?
20. Do tests cover invalid profile rejection?
21. Do tests cover path-source precedence and explicit override behavior using synthetic fixtures only?
22. Do tests cover runner capability serialization and missing-tool reporting?
23. Do tests cover example config validity?
24. Do tests cover gate behavior and final-check/report-summary integration?
25. Do existing user-solve/frontend/control-plane tests continue passing or remain unaffected under command-plan coverage?
26. Did pytest_result record real commands and exit codes?
27. Did command-plan authorize all executed commands and omit no executed commands?
28. Did final-check pass with current IDs?
29. Did run-closeout pass and archive current reports if authorized?
30. Were forbidden files untouched?
31. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?
32. Did the implementation avoid IDA MCP, real Web/API service behavior, database/queue, scheduler, remote dispatch, and CI polling?

## 6. Implementation Scope

Allowed implementation:

1. Add or extend `reverse_agent/tool_profiles.py`.
   - Define stable data structures for tool profiles.
   - Include categories such as `static_analyzer`, `decompiler`, `debugger`, `emulator`, `solver`, `harness`, and `local_script` only as metadata.
   - Represent path source such as `explicit`, `environment`, `config`, `path_hint`, `common_path_candidate`, `disabled`, and `unavailable`.
   - Provide deterministic loaders from in-memory dictionaries, explicit overrides, environment mappings, and example config data.
   - Do not run subprocesses or invoke the configured tools.

2. Add or extend `reverse_agent/tool_capabilities.py`.
   - Define `RunnerCapability` and related serialization helpers.
   - Represent runner/platform metadata and available/missing/disabled tool capabilities.
   - Represent whether a future runner could support static extraction, decompilation, dynamic debugging, runtime validation, or solver execution, but do not execute those actions.
   - Make permission-sensitive capabilities explicit and default-safe.

3. Add `.reverse-agent/config/tool_profiles.example.json`.
   - Use placeholders and portable examples.
   - Do not include local secrets.
   - Do not require the user's machine-specific `F:\reverse-agent` or IDA path.

4. Update `reverse_agent/project_gate.py`.
   - Add a `tool-profile-capability` gate or equivalent.
   - Generate `project_state/gates/tool_profile_capability_result.json`.
   - Integrate the artifact into report-summary/final-check only for this decision when required.

5. Add tests.
   - `tests/test_tool_profiles.py`
   - `tests/test_tool_capabilities.py`
   - Focused updates to `tests/test_project_gate.py` and `tests/test_project_reports.py` only as needed.

6. Add documentation.
   - `docs/user_solve_tool_profiles.md`
   - Optionally update `docs/user_solve_layer.md` with a short pointer to the new tool profile/capability layer.

Compatibility rules:

- Existing accepted tests must continue passing under command-plan coverage.
- New modules must import without IDA, Ghidra, OllyDbg, x64dbg, radare2, or optional reverse-engineering tools installed.
- New logic must be deterministic in unit tests.
- New logic must be configuration/capability metadata only.
- Future execution must remain controlled by command-plan, execution-log, runner permission profiles, and gates.

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
python -m pytest tests/test_tool_profiles.py tests/test_tool_capabilities.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate tool-profile-capability --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If command-plan profile requires broader validation:

```powershell
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_request.py tests/test_user_solve_response.py tests/test_user_solve_handoff.py tests/test_user_solve_controller.py tests/test_user_solve_cli.py tests/test_user_solve_frontend_bridge.py tests/test_user_solve_local_api.py tests/test_user_solve_api_schema.py tests/test_user_solve_ui_state.py tests/test_user_solve_errors.py tests/test_user_solve_fixtures.py tests/test_project_gate.py tests/test_project_reports.py -q
```

If command-plan authorizes closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260704_user_solve_tool_profile_capability_v1
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
6. Any real IDA/Ghidra/debugger/emulator/solver/harness/tool execution is added or invoked.
7. Any external process invocation is added for tool discovery.
8. Any real binary, sample, or user upload is processed.
9. Any production service, database, queue, scheduler, remote dispatch, CI polling, persistent task/session, or real upload flow is added.
10. IDA MCP or another interactive tool adapter is implemented in this round.
11. A machine-specific local path is hardcoded as a required default.
12. Tool profile or runner capability code duplicates AgentRunner, pipeline, harness, solver, or existing tool interface responsibilities instead of describing capabilities.
13. Missing tool capability is treated as working execution evidence.
14. Current-round gate artifacts are missing or carry stale decision/report/round IDs.
15. `tool_profile_capability_result.json` or equivalent is missing.
16. Required focused tests are missing.
17. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
18. command-plan is missing, stale, or not respected.
19. final-check fails.
20. closeout is executed without command-plan authorization.
21. closeout is required but missing or failed.
22. The final report claims any concrete sample is solved, static verified, runtime validated, or audit verified.

If only part of the tool profile/capability contract is completed, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
