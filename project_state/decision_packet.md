```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_user_solve_trace_fallback_ladder_v1",
  "round_id": "round_20260703_user_solve_trace_fallback_ladder_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_decision_id": "decision_20260703_user_solve_layer_foundation_big_step_v1",
  "follows_round_id": "round_20260703_user_solve_layer_foundation_big_step_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_34_user_solve_trace_fallback_ladder",
  "primary_goal": "Extend the accepted User Solve Layer foundation with internal solve-task trace contracts and a non-executing fallback ladder, while fixing the misleading inherited-baseline report wording observed in the previous audit.",
  "command_plan_authority_required": true,
  "accepted_requires_report_baseline_wording_fix": true,
  "accepted_requires_user_solve_trace_contract": true,
  "accepted_requires_fallback_ladder_contract": true,
  "accepted_requires_trace_fallback_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_trace.py",
    "reverse_agent/fallback_ladder.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/evidence_quality.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_trace.py",
    "tests/test_fallback_ladder.py",
    "tests/test_user_solve.py",
    "tests/test_evidence_quality.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_layer.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260703_user_solve_trace_fallback_ladder_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "solve_reports/*",
    ".github/workflows/*",
    "training_materials/local_reverse/*"
  ],
  "forbidden_capabilities_this_round": [
    "web_api_endpoint",
    "database_or_queue",
    "scheduler_or_service",
    "remote_runner_dispatch",
    "github_actions_dispatch_or_polling",
    "codex_or_trae_adapter_execution",
    "ida_mcp_adapter",
    "ida_ghidra_ollydbg_execution",
    "sample_execution",
    "runtime_probe",
    "dynamic_debugging",
    "reverse_solving_candidate_search",
    "persistent_user_task_creation_outside_tests"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Trace + Fallback Ladder v1**.

This is an `engineering_branch` continuation after the accepted User Solve Layer foundation round. The previous round landed the user-facing result contract, state machine, safe fast wrapper, evidence-quality mapper, gate artifact, tests, and documentation. Audit accepted the implementation with one limitation: the report body included an "Allowed Inherited Dirty Baseline Files" section that listed current-round source/test changes even though startup evidence showed only `project_state/gates/command_plan.json` was inherited dirty. This round must fix that report wording problem and then add the next user-solve foundation layer.

Primary objectives:

1. Fix report generation or report-summary synthesis so inherited baseline dirty files are not mislabeled as current-round source/test changes, and current-round changed files are not mislabeled as inherited dirty files.
2. Add an internal `UserSolveTaskTrace` contract for recording user-solve progress, candidate sources, missing evidence, fallback steps, validation status, and artifact references without exposing internal project paths by default.
3. Add a non-executing `FallbackLadder` contract for ordered user-solve fallback steps, risk levels, timeout metadata, permission requirements, and stop reasons.
4. Integrate the existing `FastSolveWrapper` / `EvidenceQualityMapper` with trace and fallback metadata at the data-contract level only.
5. Add a project gate artifact, for example `project_state/gates/user_solve_trace_fallback_result.json`, proving trace schema, fallback ladder policy, redaction, and no-execution constraints.
6. Add focused tests for trace serialization, fallback policy, risk gating, no-execution safety, report wording, and wrapper/evidence mapper integration.
7. Preserve the previous User Solve Layer behavior: `candidate_found` may return before validation, `verified` requires passed validation, and default user output must hide internal engineering references.

Accepted target:

- The final report no longer has a misleading "Allowed Inherited Dirty Baseline Files" section that contains current-round source/test changes.
- A solve trace can represent: task id, user status, engineering status, candidate sources, fallback steps, missing evidence, validation result, artifact references, and user/developer serialization modes.
- A fallback ladder can represent at least these steps: `fast_strings`, `ida_summary`, `targeted_decompile`, `constant_material_extract`, `solver_attempt`, and `runtime_validation`.
- Fallback steps carry risk level, timeout, required capability, `can_run_in_fast_mode`, `writes_artifact`, and permission requirements.
- The ladder can select safe next steps from synthetic state without executing any tool or sample.
- Static-only steps may be considered automatically eligible; local execution, dynamic debug, network, and manual-review steps must require explicit permission and remain non-executed in this round.
- No Web/API, database, queue, scheduler, remote runner, GitHub Actions dispatch/polling, IDA MCP, IDA/Ghidra/OllyDbg execution, sample execution, runtime probe, dynamic debugging, or concrete reverse solving is implemented or executed.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and still states `execution_scope=decision_packet_controls_current_round`.

Previous round:

- `decision_20260703_user_solve_layer_foundation_big_step_v1`
- `round_20260703_user_solve_layer_foundation_big_step_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the previous round:

1. `codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for the User Solve Layer foundation round.
2. `pytest_result.txt` reported `PASSED` for the same decision/report/round and recorded focused user-solve tests plus broad project gate/job/runner tests.
3. `final_gate_result.json` passed, including decision/report matching, pytest matching, command-plan authority, Required Audit coverage, and the `user_solve_layer_gate_artifact` check.
4. `project_state/gates/user_solve_layer_result.json` passed and showed the user-solve layer is evidence-only, not executable, cannot dispatch, does not mutate state, and has no sample/subprocess/network/runner/GitHub Actions invocation.
5. The previous audit limitation was not a code/gate failure, but a report-body semantics problem: the report's "Allowed Inherited Dirty Baseline Files" section listed current-round source/test files, while startup evidence showed only `project_state/gates/command_plan.json` was dirty at startup.

Existing capabilities to preserve:

- `reverse_agent/user_solve_contract.py` implements `UserSolveResult`, candidate/result serialization, validation rules, redaction, and developer serialization.
- `reverse_agent/user_solve_state.py` implements the state machine.
- `reverse_agent/user_solve.py` implements safe in-memory `FastSolveWrapper` adaptation.
- `reverse_agent/evidence_quality.py` maps missing evidence to user-facing fallback/deep-analysis status.
- `reverse_agent/project_gate.py` already has `user-solve-layer` gate support.
- Existing command-plan, execution-log, job, AgentRunner, pipeline, solver, harness, and project gate capabilities must not be duplicated or replaced.

Artifact freshness policy:

- Current-round generated gate/report artifacts must carry `decision_20260703_user_solve_trace_fallback_ladder_v1` and `round_20260703_user_solve_trace_fallback_ladder_v1`.
- Historical sample artifacts in `current_state.json` / `artifact_index.json` are backlog context only and remain non-blocking for this engineering round.
- New tests must use synthetic trace/fallback payloads only. Do not use real local samples.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, budget-only search expansion, compare_semantics_agree=false frontier use, full solve_reports commits, and repeated sample diagnostics without new runtime evidence.
- This round must not enter any of those reverse-solving directions.

Command-plan policy:

- `project_state/gates/command_plan.json` is the only command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- The Tests section lists intended validation targets, but command-plan is binding.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not execute samples, solvers, IDA, Ghidra, OllyDbg, debuggers, emulators, harnesses, runtime probes, network calls, Web/API endpoints, databases, queues, schedulers, services, remote runners, GitHub Actions dispatch/polling, Codex adapter execution, Trae adapter execution, Claude Code adapter execution, Aider adapter execution, or IDA MCP adapter.

Do not create persistent live user solve tasks under `project_state/solve_tasks/` in this round. Implement the trace contract and tests using temporary test directories or in-memory synthetic data. Gate evidence should be written under `project_state/gates/` only.

Do not mutate forbidden files listed in `decision_contract`.

Do not add dynamic facts to `.codex-skills/`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static_verified, runtime_validated, or audit_verified.

Do not treat filename, category, queue item, metadata, or user-solve trace fields as solve evidence.

Do not replace existing User Solve Layer behavior from the previous accepted round.

Do not introduce Web/API, database, or runner abstractions beyond the static trace/fallback contracts.

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

Inspect current user-solve implementation:

1. `reverse_agent/user_solve_contract.py`
2. `reverse_agent/user_solve_state.py`
3. `reverse_agent/user_solve.py`
4. `reverse_agent/evidence_quality.py`
5. `tests/test_user_solve_contract.py`
6. `tests/test_user_solve_state.py`
7. `tests/test_user_solve.py`
8. `tests/test_evidence_quality.py`
9. `docs/user_solve_layer.md`

Inspect report/gate code before changing report wording:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `project_state/gates/round_delta_summary.json`
5. `project_state/gates/final_gate_result.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/user_solve_layer_result.json`

Inspect orchestration code only to avoid duplication:

1. `reverse_agent/project_jobs.py`
2. `reverse_agent/project_agent_runner.py`
3. `reverse_agent/project_runner_contract.py`
4. `reverse_agent/pipeline.py`
5. `reverse_agent/harness.py`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless a command-plan-authorized diagnostic requires it.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current `decision_packet.md` treated as execution authority and `task_packet.json` as background only?
2. Did decision metadata remain valid, approved, on `engineering_branch`, and aligned with active `reverse-agent-iteration@v2`?
3. Were startup commands recorded before project gates/tests?
4. Were current IDs used in reports, pytest_result, gate artifacts, and closeout artifacts?
5. Was the previous audit limitation addressed by fixing misleading inherited-baseline report wording?
6. Does the final report distinguish inherited startup dirty files from current-round changed source/test files?
7. Does the final report avoid listing current-round source/test files under an inherited-dirty heading unless they were truly inherited dirty at startup?
8. Was `UserSolveTaskTrace` implemented as a structured internal contract?
9. Does trace serialization include task id, user status, engineering status, candidate sources, fallback steps, missing evidence, validation result, artifact references, and timestamps or equivalent ordering metadata?
10. Does trace default user serialization hide internal engineering paths and developer references?
11. Does trace developer/debug serialization preserve internal trace/artifact references explicitly?
12. Does trace validation reject inconsistent states, such as verified user status without passed validation evidence?
13. Was `FallbackLadder` implemented as a non-executing data/policy contract?
14. Does the ladder include `fast_strings`, `ida_summary`, `targeted_decompile`, `constant_material_extract`, `solver_attempt`, and `runtime_validation` steps?
15. Does each fallback step include risk level, timeout, required capability, fast-mode eligibility, artifact-write flag, and permission requirement metadata?
16. Does fallback selection choose a safe next step from synthetic state without executing tools or samples?
17. Are local execution, dynamic debugging, network, and manual-review steps blocked unless explicit permission is represented in synthetic policy input?
18. Does fallback ladder logic record stop reasons when no safe step is eligible?
19. Did `EvidenceQualityMapper` integrate missing evidence with fallback recommendations without exposing internal paths to user output?
20. Did `FastSolveWrapper` preserve previous behavior for candidate_found, verified, failed, blocked, and missing-evidence branches?
21. Did the implementation avoid duplicating pipeline, solver, harness, job, AgentRunner, command-plan, or execution-log responsibilities?
22. Did the implementation avoid Web/API, DB/queue/scheduler, remote runner, GitHub Actions dispatch/polling, IDA/Ghidra/OllyDbg, IDA MCP, runtime probe, dynamic debugging, and concrete reverse solving?
23. Were changes limited to allowed source/test/documentation/generated artifact paths?
24. Were forbidden files untouched?
25. Was a current gate artifact generated, for example `project_state/gates/user_solve_trace_fallback_result.json`?
26. Does the gate artifact prove no external invocation or dispatch capability was added?
27. Did tests cover trace user/developer serialization and redaction?
28. Did tests cover trace validation errors?
29. Did tests cover fallback ladder step ordering and permission/risk gating?
30. Did tests cover fallback no-eligible-step stop reasons?
31. Did tests cover report baseline wording fix?
32. Did tests cover wrapper/evidence mapper integration with fallback metadata?
33. Did pytest_result record the real commands and exit codes?
34. Did command-plan authorize all executed commands and omit no executed commands?
35. Did final-check pass with current decision/report/round IDs?
36. Did run-closeout pass and archive corrected reports if command-plan authorized closeout?
37. Did the final report avoid claiming solved/static_verified/runtime_validated/audit_verified for any sample?
38. Did the final report use direct artifact evidence rather than generic summaries for Required Audit answers?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_trace.py`.
   - Define `UserSolveTaskTrace`, `CandidateSource`, `FallbackStepRecord`, and validation/serialization helpers or equivalent names.
   - Keep default user serialization redacted and developer serialization explicit.
   - Support synthetic trace creation in tests without writing live `project_state/solve_tasks/` files.

2. Add `reverse_agent/fallback_ladder.py`.
   - Define fallback step schema, risk levels, permission policy, and selection logic.
   - Required first ladder steps: `fast_strings`, `ida_summary`, `targeted_decompile`, `constant_material_extract`, `solver_attempt`, `runtime_validation`.
   - Logic must be policy-only and non-executing.

3. Update `reverse_agent/evidence_quality.py` and/or `reverse_agent/user_solve.py` minimally.
   - Attach fallback recommendations or trace hints to missing-evidence paths where appropriate.
   - Preserve existing public behavior and tests from the previous accepted round.

4. Update `reverse_agent/project_gate.py`.
   - Add or extend a gate such as `user-solve-trace-fallback`.
   - Gate must generate `project_state/gates/user_solve_trace_fallback_result.json` or equivalent.
   - Gate must verify importability, enum/step coverage, redaction, no-execution/no-dispatch policy, and report baseline wording support.

5. Fix report generation/report-summary wording.
   - Do not call current-round source/test changes "inherited dirty" unless they were dirty in startup/baseline evidence.
   - Prefer separate terms such as `Inherited Dirty Baseline Files`, `Allowed Changed Source/Test Files`, and `Generated/Updated Artifacts`.
   - Add tests so the old misleading wording cannot recur.

6. Add tests:
   - `tests/test_user_solve_trace.py`
   - `tests/test_fallback_ladder.py`
   - update `tests/test_user_solve.py`
   - update `tests/test_evidence_quality.py`
   - update `tests/test_project_gate.py`
   - update `tests/test_project_reports.py`

7. Update documentation:
   - Update `docs/user_solve_layer.md` to describe trace and fallback ladder boundaries.
   - Documentation must remain secondary to tests/gates.

Compatibility rules:

- Existing user-solve contract/state/wrapper/evidence-quality tests must keep passing.
- New modules must import without optional reverse-engineering tools installed.
- No real samples, local sample paths, IDA/Ghidra/OllyDbg paths, subprocesses, or network are required for tests.
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
```

Execution policy:

- First generate/read `project_state/gates/command_plan.json` through the existing command-plan flow.
- Execute only commands authorized by `command_plan.commands`.
- Do not execute any command listed in `command_plan.omitted_commands`.
- If this section conflicts with command-plan, command-plan wins.

Expected validation coverage, subject to command-plan authorization:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate user-solve-trace-fallback --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

If command-plan profile requires broader validation, include existing stable suites, for example:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py tests/test_project_agent_runner.py tests/test_project_runner_contract.py -q
```

If command-plan authorizes closeout:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_user_solve_trace_fallback_ladder_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record actual commands and exit codes. `codex_execution_report.md` and `execution_report.md` must list real tests in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any condition occurs:

1. Current decision/report/round IDs do not match.
2. `skill_profiles` do not match active registry entries.
3. `task_packet.json` is treated as execution authority.
4. Any forbidden path is modified.
5. Any sample, IDA, Ghidra, OllyDbg, debugger, emulator, harness, runtime probe, Web/API endpoint, database, queue, scheduler, remote runner, GitHub Actions dispatch/polling, Codex/Trae/Claude/Aider adapter, or IDA MCP adapter is executed or implemented.
6. Persistent live `project_state/solve_tasks/` files are created outside tests.
7. Fallback ladder selection executes tools rather than returning policy decisions.
8. Static-only/local-execution/dynamic-debug/network/manual-review risk gates are not explicit.
9. User-visible trace or fallback output leaks internal project paths by default.
10. `verified` can be represented without passed validation evidence.
11. Missing evidence is treated as solved/static_verified/runtime_validated evidence.
12. Current-round source/test files are mislabeled as inherited dirty baseline files in the final report.
13. Existing user-solve foundation behavior regresses.
14. Existing pipeline/harness/job/runner/command-plan/execution-log capabilities are duplicated or replaced.
15. Required focused tests are missing.
16. `project_state/gates/user_solve_trace_fallback_result.json` or equivalent current gate artifact is missing.
17. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
18. command-plan is missing, stale, or not respected.
19. final-check fails.
20. closeout is executed without command-plan authorization.
21. closeout is required but missing or failed.
22. The final report claims any concrete sample is solved, static_verified, runtime_validated, or audit_verified.

If only trace or fallback is completed, but not both, do not claim `SUCCESS`; report `PARTIAL` or `REWORK_REQUIRED` with exact missing pieces.
