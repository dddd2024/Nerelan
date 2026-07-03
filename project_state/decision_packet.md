```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_user_solve_session_bundle_v1",
  "round_id": "round_20260703_user_solve_session_bundle_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_decision_id": "decision_20260703_user_solve_trace_fallback_ladder_v1",
  "follows_round_id": "round_20260703_user_solve_trace_fallback_ladder_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_35_user_solve_session_bundle",
  "primary_goal": "Consolidate UserSolveResult, UserSolveTaskTrace, and FallbackLadder metadata into an in-memory user-solve session bundle contract, while cleaning up Required Audit answer precision and duplicate changed-file reporting from the previous round.",
  "command_plan_authority_required": true,
  "accepted_requires_required_audit_answer_precision_fix": true,
  "accepted_requires_changed_file_deduplication": true,
  "accepted_requires_user_solve_session_bundle_contract": true,
  "accepted_requires_public_private_serialization_boundary": true,
  "accepted_requires_session_bundle_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_session.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_trace.py",
    "reverse_agent/fallback_ladder.py",
    "reverse_agent/evidence_quality.py",
    "reverse_agent/project_gate.py",
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
    "docs/user_solve_layer.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260703_user_solve_session_bundle_v1/*"
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
    "project_state/solve_tasks/*"
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
    "persistent_user_task_creation",
    "real_user_upload_ingestion"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Session Bundle v1**.

This is an `engineering_branch` continuation after the accepted trace/fallback round. The previous round delivered `UserSolveTaskTrace`, `FallbackLadder`, a trace/fallback gate artifact, and focused tests. The previous audit accepted it with limitations: several Required Audit answers were too generic, one answer about fallback step coverage described only three static steps even though the gate proved all six steps, and the `Allowed Changed Source/Test Files` list duplicated `tests/test_user_solve_trace.py`.

This round must clean up those report-quality limitations and then consolidate the user-solve layer into a first session-level contract. The session bundle is the future UI/API boundary, but this round must remain in-memory and non-executing. It must not implement a Web endpoint, database row, queue job, scheduler, persistent task directory, file upload ingestion, or runner dispatch.

Primary objectives:

1. Fix report generation/report-summary so Required Audit answers are precise and evidence-specific, especially fallback step coverage and report wording items.
2. Deduplicate changed source/test file reporting in execution reports and generated summaries.
3. Add an in-memory `UserSolveSessionBundle` contract that packages:
   - user-facing result;
   - user-facing trace summary;
   - fallback decision / next safe step;
   - validation status;
   - evidence status;
   - missing evidence summary;
   - public message;
   - developer-only trace/artifact references.
4. Add safe public/private serialization boundaries for the session bundle.
5. Add a non-executing session builder/factory that adapts already-supplied in-memory analysis payloads through existing `FastSolveWrapper`, `UserSolveTaskTrace`, `FallbackLadder`, and `EvidenceQualityMapper` components.
6. Add a project gate artifact, for example `project_state/gates/user_solve_session_bundle_result.json`, proving session bundle schema, redaction, fallback linkage, no-execution safety, and report-quality fixes.
7. Add focused tests covering session serialization, trace/fallback/result consistency, no internal path leakage, developer serialization, changed-file deduplication, and precise Required Audit answer generation.
8. Preserve all previously accepted behavior: `candidate_found` may be returned before validation, `verified` requires passed validation, fallback selection remains non-executing, and high-risk/local/dynamic steps remain blocked without explicit synthetic policy.

Accepted target:

- The report does not duplicate source/test paths in `Allowed Changed Source/Test Files`, `files_changed`, or summary-derived changed-file sections.
- Required Audit answers cite the specific gate/source/test evidence for each item and do not use broad generic filler answers when the item asks for a concrete implementation fact.
- `UserSolveSessionBundle` has stable `to_user_dict()` and `to_developer_dict()` or equivalent.
- Default user serialization contains only safe user-facing fields and no raw `project_state/`, `decision_packet.md`, `command_plan.json`, `artifact_index.json`, `negative_results.json`, `codex_execution_report.md`, `pytest_result.txt`, internal artifact paths, or developer trace references.
- Developer serialization may retain explicit internal references for audit use.
- Session bundle creation is in-memory only and does not create persistent `project_state/solve_tasks/` artifacts.
- The session builder/factory returns data decisions only; it must not execute samples, tools, solvers, subprocesses, network calls, runners, or debuggers.
- No concrete reverse sample is solved or claimed solved.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`; it must not control this round.

Previous round:

- `decision_20260703_user_solve_trace_fallback_ladder_v1`
- `round_20260703_user_solve_trace_fallback_ladder_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the previous accepted-with-limitations round:

1. `codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for the trace/fallback round.
2. `pytest_result.txt` reported `PASSED` with focused user-solve/trace/fallback/report tests and broader project gate/job/runner tests.
3. `project_state/gates/user_solve_trace_fallback_result.json` passed and proved the gate was evidence-only, non-executable, non-dispatching, and free of sample/subprocess/network/runner/GitHub Actions invocation.
4. The fallback ladder gate proved coverage for six required steps: `fast_strings`, `ida_summary`, `targeted_decompile`, `constant_material_extract`, `solver_attempt`, and `runtime_validation`.
5. The trace contract proved user/developer serialization boundaries and rejects verified traces without passed validation.
6. `final_gate_result.json` passed and marked `user_solve_trace_fallback_gate_artifact` as required and current.
7. `run_closeout_result.json` passed and close-round reached `CLOSED`.

Previous audit limitations to address:

1. Required Audit answer precision was uneven. At least one answer about fallback step coverage mentioned only the three static steps even though the artifact proved all six required steps.
2. Some Required Audit answers used broad statements such as "current-round source, tests, gate artifact, and report evidence directly cover this item" instead of specific evidence and direct explanation.
3. `Allowed Changed Source/Test Files` duplicated `tests/test_user_solve_trace.py`.

Existing capabilities to preserve:

- `reverse_agent/user_solve_contract.py`: user result contract, validation rules, redaction, developer serialization.
- `reverse_agent/user_solve_state.py`: user solve state machine.
- `reverse_agent/user_solve.py`: safe in-memory `FastSolveWrapper` and trace adapter behavior.
- `reverse_agent/user_solve_trace.py`: trace contract and serialization.
- `reverse_agent/fallback_ladder.py`: fallback policy, step metadata, selection, and non-execution semantics.
- `reverse_agent/evidence_quality.py`: missing-evidence mapping and fallback recommendation metadata.
- `reverse_agent/project_gate.py`: user-solve-layer and trace/fallback gate integration.

Existing orchestration, pipeline, harness, solver, command-plan, execution-log, job, and AgentRunner capabilities must not be duplicated or replaced.

Artifact freshness policy:

- Current-round gate/report artifacts must carry `decision_20260703_user_solve_session_bundle_v1` and `round_20260703_user_solve_session_bundle_v1`.
- Historical sample artifacts in `current_state.json` and `artifact_index.json` are backlog context only and remain non-blocking for this engineering round.
- New tests must use synthetic in-memory payloads only.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, budget-only search expansion, compare_semantics_agree=false primary frontier use, full solve_reports commits, and repeated sample diagnostics without new runtime evidence.
- This round must not enter those reverse-solving directions.

Command-plan policy:

- `project_state/gates/command_plan.json` is the command execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- The Tests section lists validation targets; command-plan remains binding if there is any conflict.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not execute samples, solvers, IDA, Ghidra, OllyDbg, debuggers, emulators, harnesses, runtime probes, network calls, Web/API endpoints, databases, queues, schedulers, services, remote runners, GitHub Actions dispatch/polling, Codex adapter execution, Trae adapter execution, Claude Code adapter execution, Aider adapter execution, or IDA MCP adapter.

Do not create `project_state/solve_tasks/` or any persistent user task/session files in this round. The session bundle must be in-memory or synthetic-test-only. Gate evidence belongs under `project_state/gates/` only.

Do not mutate forbidden paths listed in `decision_contract`.

Do not add dynamic facts to `.codex-skills/`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static_verified, runtime_validated, or audit_verified.

Do not treat user-solve session, trace, fallback, filename, category, queue metadata, or candidate metadata as solve evidence.

Do not replace or regress the accepted `UserSolveResult`, `UserSolveTaskTrace`, `FallbackLadder`, or `EvidenceQualityMapper` behavior.

Do not add Web/API, database, runner, or upload-ingestion abstractions beyond the in-memory session-bundle contract.

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
4. `reverse_agent/user_solve_trace.py`
5. `reverse_agent/fallback_ladder.py`
6. `reverse_agent/evidence_quality.py`
7. `tests/test_user_solve_contract.py`
8. `tests/test_user_solve_state.py`
9. `tests/test_user_solve.py`
10. `tests/test_user_solve_trace.py`
11. `tests/test_fallback_ladder.py`
12. `tests/test_evidence_quality.py`
13. `docs/user_solve_layer.md`

Inspect report/gate code before modifying report wording:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `project_state/gates/round_delta_summary.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/user_solve_trace_fallback_result.json`

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
5. Were the previous audit limitations explicitly addressed?
6. Does the final report avoid duplicate entries in `Allowed Changed Source/Test Files`, `files_changed`, and summary-derived changed-file sections?
7. Are Required Audit answers precise, item-specific, and supported by direct source/test/gate/report evidence rather than generic filler?
8. Did the fallback step coverage answer explicitly account for all six required fallback steps?
9. Was `UserSolveSessionBundle` or equivalent session-level contract implemented?
10. Does the session bundle include user-facing result, trace summary, fallback decision, validation status, evidence status, missing-evidence summary, public message, and developer-only trace/artifact references?
11. Does default session user serialization hide internal project paths and developer trace references?
12. Does session developer/debug serialization preserve internal references explicitly for audit use?
13. Does session validation reject inconsistent states such as `verified` without passed validation or a verified result with missing evidence marked as unresolved?
14. Does the session builder/factory use existing `FastSolveWrapper`, `UserSolveTaskTrace`, `FallbackLadder`, and `EvidenceQualityMapper` instead of duplicating pipeline/solver/harness/job/runner responsibilities?
15. Does the session builder/factory remain in-memory and non-executing?
16. Does fallback metadata remain non-executing, with local/dynamic/high-risk steps blocked unless explicit synthetic policy allows them?
17. Does explicit synthetic permission still avoid actual tool/sample execution in this round?
18. Does the bundle preserve previous `candidate_found` pending-validation behavior?
19. Does the bundle preserve previous `verified` requires passed validation behavior?
20. Does the bundle preserve previous missing-evidence to deep-analysis/fallback behavior?
21. Does the bundle produce a clear user-facing `next_action` or equivalent field without exposing internal gate/report paths?
22. Does the bundle produce developer-only audit references without making them default user output?
23. Was a current gate artifact generated, for example `project_state/gates/user_solve_session_bundle_result.json`?
24. Does the gate artifact prove no external invocation or dispatch capability was added?
25. Did tests cover session user/developer serialization and redaction?
26. Did tests cover session validation errors?
27. Did tests cover session creation from candidate-found payloads?
28. Did tests cover session creation from verified payloads?
29. Did tests cover session creation from missing-evidence payloads with fallback recommendation?
30. Did tests cover changed-file/report deduplication?
31. Did tests cover Required Audit answer precision, including six-step fallback coverage wording?
32. Did existing user-solve/trace/fallback/evidence tests continue passing?
33. Did pytest_result record the real commands and exit codes?
34. Did command-plan authorize all executed commands and omit no executed commands?
35. Did final-check pass with current decision/report/round IDs?
36. Did run-closeout pass and archive corrected reports if command-plan authorized closeout?
37. Were forbidden files untouched?
38. Did the final report avoid claiming solved/static_verified/runtime_validated/audit_verified for any sample?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_session.py`.
   - Define `UserSolveSessionBundle`, `SessionPublicView`, `SessionDeveloperView`, `SessionNextAction`, or equivalent names.
   - Provide stable dict/JSON-like serialization.
   - Default user serialization must be redacted and must not include internal artifact paths or developer trace references.
   - Developer serialization may include internal trace/artifact references.
   - Validation must reject inconsistent session states.

2. Update `reverse_agent/user_solve.py` minimally.
   - Add a non-executing helper that builds a session bundle from an already-supplied in-memory payload, existing result, trace, fallback decision, and evidence metadata.
   - Preserve `adapt()` and existing `adapt_with_trace()` behavior.

3. Update `reverse_agent/evidence_quality.py`, `reverse_agent/user_solve_trace.py`, and `reverse_agent/fallback_ladder.py` only if needed for session-bundle metadata compatibility.
   - Do not change accepted semantics unless tests show a bug.

4. Update `reverse_agent/project_gate.py`.
   - Add or extend a gate such as `user-solve-session-bundle`.
   - Generate `project_state/gates/user_solve_session_bundle_result.json` or equivalent.
   - Gate must verify importability, schema coverage, redaction, session consistency, fallback linkage, no-execution/no-dispatch policy, report-answer precision, and changed-file deduplication.

5. Fix report generation/report-summary wording and deduplication.
   - Deduplicate source/test file lists before rendering.
   - Ensure Required Audit answers are specific and align with their item text.
   - Specifically ensure fallback step coverage answers name all six required steps when that item is asked.

6. Add tests:
   - `tests/test_user_solve_session.py`
   - update `tests/test_user_solve.py`
   - update `tests/test_user_solve_contract.py` if needed for session validation helpers
   - update `tests/test_user_solve_trace.py`
   - update `tests/test_fallback_ladder.py`
   - update `tests/test_evidence_quality.py`
   - update `tests/test_project_gate.py`
   - update `tests/test_project_reports.py`

7. Update `docs/user_solve_layer.md`.
   - Explain result/trace/fallback/session boundaries.
   - Explain that session bundle is an in-memory contract, not Web/API/persistence.

Compatibility rules:

- Existing accepted tests from user-solve foundation and trace/fallback rounds must continue passing.
- New modules must import without optional reverse-engineering tools installed.
- No real samples, local sample paths, IDA/Ghidra/OllyDbg paths, subprocesses, or network calls are required.
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

- Generate/read `project_state/gates/command_plan.json` through the existing command-plan flow.
- Execute only commands authorized by `command_plan.commands`.
- Do not execute commands listed in `command_plan.omitted_commands`.
- If this section conflicts with command-plan, command-plan wins.

Expected validation coverage, subject to command-plan authorization:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate user-solve-session-bundle --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_user_solve_session_bundle_v1
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
6. Persistent `project_state/solve_tasks/` files are created.
7. The session builder/factory executes tools rather than returning data-only contracts.
8. Fallback ladder selection executes tools or samples.
9. User-visible session output leaks internal project paths by default.
10. Developer-only references appear in default user output.
11. `verified` can be represented without passed validation evidence.
12. Missing evidence is treated as solved/static_verified/runtime_validated evidence.
13. Required Audit answers remain generic or imprecise for concrete implementation checks.
14. Fallback step coverage answer fails to name all six required steps.
15. Changed-file/report lists contain duplicate paths after report refresh.
16. Existing user-solve result/trace/fallback behavior regresses.
17. Existing pipeline/harness/job/runner/command-plan/execution-log capabilities are duplicated or replaced.
18. Required focused tests are missing.
19. `project_state/gates/user_solve_session_bundle_result.json` or equivalent current gate artifact is missing.
20. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
21. command-plan is missing, stale, or not respected.
22. final-check fails.
23. closeout is executed without command-plan authorization.
24. closeout is required but missing or failed.
25. The final report claims any concrete sample is solved, static_verified, runtime_validated, or audit_verified.

If only report cleanup or only session bundle is completed, but not both, do not claim `SUCCESS`; report `PARTIAL` or `REWORK_REQUIRED` with exact missing pieces.
