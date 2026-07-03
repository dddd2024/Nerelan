```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_user_solve_handoff_provenance_v1",
  "round_id": "round_20260703_user_solve_handoff_provenance_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_decision_id": "decision_20260703_user_solve_session_bundle_v1",
  "follows_round_id": "round_20260703_user_solve_session_bundle_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "phase_label": "phase_2_36_user_solve_handoff_provenance",
  "primary_goal": "Harden pre-work startup provenance so source/test dirty state cannot be normalized after edits, and add a safe user-solve handoff packet contract derived from the accepted session bundle without introducing Web/API, persistence, runner dispatch, or sample execution.",
  "command_plan_authority_required": true,
  "accepted_requires_prework_provenance_gate": true,
  "accepted_requires_startup_dirty_hard_block_or_explicit_inherited_baseline": true,
  "accepted_requires_user_solve_handoff_packet_contract": true,
  "accepted_requires_public_private_handoff_serialization": true,
  "accepted_requires_handoff_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_handoff.py",
    "reverse_agent/user_solve_session.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_trace.py",
    "reverse_agent/fallback_ladder.py",
    "reverse_agent/evidence_quality.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_handoff.py",
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
    "project_state/rounds/round_20260703_user_solve_handoff_provenance_v1/*"
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
    "persistent_user_session_creation",
    "real_user_upload_ingestion"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Handoff + Prework Provenance v1**.

This is an `engineering_branch` continuation after the accepted session-bundle round. The previous round delivered `UserSolveSessionBundle`, session serialization, session validation, a session gate artifact, and report-quality cleanup. Audit accepted it with one limitation: the recorded first `git status --short` already showed source/test/doc files dirty, so the audit could accept those changes as in-scope but could not strictly prove the startup check was captured before file edits.

This round has two coupled goals:

1. Harden startup/prework provenance so future rounds cannot silently normalize source/test dirty state after edits.
2. Add a safe user-solve handoff packet contract that turns an accepted in-memory `UserSolveSessionBundle` into a user-facing handoff shape for future UI/API integration, without implementing UI/API, persistence, queueing, runner dispatch, sample execution, or tool execution.

Primary objectives:

1. Add a prework provenance gate/check, for example `prework-provenance`, that records or validates the first startup snapshot before implementation work.
2. Add hard policy: if startup source/test/doc files are dirty before work and are not explicitly declared as inherited baseline, the round must not report `SUCCESS`; it must report `BLOCKED` or `REWORK_REQUIRED` with exact dirty paths.
3. Ensure final-check/report-summary can detect and report startup dirty provenance ambiguity rather than accepting it as a clean start.
4. Add `UserSolveHandoffPacket` or equivalent in-memory contract derived from `UserSolveSessionBundle`.
5. The handoff packet must expose only user-safe fields: answer/candidate status, confidence, validation status, evidence status, public message, next action, fallback summary, missing-evidence summary, and optional UI hints.
6. The handoff packet must keep developer audit references out of default user serialization while preserving them in developer serialization.
7. Add a project gate artifact, for example `project_state/gates/user_solve_handoff_result.json`, proving handoff schema, redaction, session linkage, no-execution safety, and prework provenance enforcement.
8. Add focused tests for startup/prework dirty hard-block behavior, explicit inherited baseline behavior, handoff serialization, developer serialization, fallback summary, no internal path leakage, and no-execution constraints.
9. Preserve all accepted behavior from the result, trace, fallback, and session rounds.

Accepted target:

- A future Codex run cannot claim `SUCCESS` when the first startup `git status --short` shows source/test/doc dirty files unless those files are explicitly recorded as inherited baseline and excluded from `files_changed` semantics.
- `project_state/gates/prework_provenance_result.json` or equivalent exists for this round and carries current decision/round IDs.
- `project_state/gates/user_solve_handoff_result.json` or equivalent exists for this round and carries current decision/report/round IDs.
- `UserSolveHandoffPacket` has stable `to_user_dict()` and `to_developer_dict()` or equivalent.
- Default user handoff output contains no raw `project_state/`, `decision_packet.md`, `command_plan.json`, `artifact_index.json`, `negative_results.json`, `codex_execution_report.md`, `pytest_result.txt`, internal artifact path, local sample path, or developer trace reference.
- Developer serialization may retain explicit internal references for audit use.
- The handoff packet is in-memory only and does not create persistent `project_state/user_sessions/` or `project_state/solve_tasks/` files.
- The handoff builder returns data only and does not execute samples, tools, solvers, subprocesses, network calls, runners, debuggers, IDA, Ghidra, or OllyDbg.
- No concrete reverse sample is solved or claimed solved.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` remains background only and states `execution_scope=decision_packet_controls_current_round`; it must not control this round.

Previous round:

- `decision_20260703_user_solve_session_bundle_v1`
- `round_20260703_user_solve_session_bundle_v1`
- audit outcome: `ACCEPTED_WITH_LIMITATIONS`

Evidence from the previous accepted-with-limitations round:

1. `codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for the session-bundle round.
2. `pytest_result.txt` reported `PASSED` with focused user-solve/session/report tests and broader project gate/job/runner tests.
3. `project_state/gates/user_solve_session_bundle_result.json` passed and proved the session bundle was evidence-only, non-executable, non-dispatching, non-persistent, and free of sample/subprocess/network/runner/GitHub Actions/Web/API/DB/queue/scheduler invocation.
4. `final_gate_result.json` passed and marked `user_solve_session_bundle_gate_artifact` as required and current.
5. `run_closeout_result.json` passed and close-round reached `CLOSED`.
6. The report-quality limitations from the trace/fallback round were mostly fixed: changed-file duplicates were removed and six-step fallback coverage was explicitly reported.

Previous audit limitation to address:

- The first recorded `git status --short` already contained modified/new source/test/doc files, including `docs/user_solve_layer.md`, `reverse_agent/project_gate.py`, `reverse_agent/user_solve.py`, `tests/test_project_gate.py`, `tests/test_project_reports.py`, `tests/test_user_solve.py`, `reverse_agent/user_solve_session.py`, and `tests/test_user_solve_session.py`. The prior audit accepted the result because the files were in scope, but this left a provenance ambiguity: the transcript did not strictly prove startup capture happened before editing.

Existing capabilities to preserve:

- `reverse_agent/user_solve_contract.py`: user result contract, validation rules, redaction, developer serialization.
- `reverse_agent/user_solve_state.py`: user solve state machine.
- `reverse_agent/user_solve.py`: safe in-memory `FastSolveWrapper`, trace/session adapters.
- `reverse_agent/user_solve_trace.py`: trace contract and serialization.
- `reverse_agent/fallback_ladder.py`: fallback policy, step metadata, non-executing selection.
- `reverse_agent/evidence_quality.py`: missing-evidence mapping and fallback recommendation metadata.
- `reverse_agent/user_solve_session.py`: session bundle contract, session validation, user/developer serialization.
- `reverse_agent/project_gate.py`: command-plan, startup-snapshot, report-summary, final-check, closeout, and user-solve gates.

Existing orchestration, pipeline, harness, solver, command-plan, execution-log, job, and AgentRunner capabilities must not be duplicated or replaced.

Artifact freshness policy:

- Current-round gate/report artifacts must carry `decision_20260703_user_solve_handoff_provenance_v1` and `round_20260703_user_solve_handoff_provenance_v1`.
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

Do not create `project_state/solve_tasks/`, `project_state/user_sessions/`, or any persistent user task/session files in this round. Handoff packet data must be in-memory or synthetic-test-only. Gate evidence belongs under `project_state/gates/` only.

Do not mutate forbidden paths listed in `decision_contract`.

Do not add dynamic facts to `.codex-skills/`.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not claim any sample is solved, static_verified, runtime_validated, or audit_verified.

Do not treat user-solve handoff, session, trace, fallback, filename, category, queue metadata, or candidate metadata as solve evidence.

Do not replace or regress accepted `UserSolveResult`, `UserSolveTaskTrace`, `FallbackLadder`, `EvidenceQualityMapper`, or `UserSolveSessionBundle` behavior.

Do not add Web/API, database, queue, runner, scheduler, or upload-ingestion abstractions beyond the in-memory handoff-packet contract.

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
7. `reverse_agent/user_solve_session.py`
8. `tests/test_user_solve_contract.py`
9. `tests/test_user_solve_state.py`
10. `tests/test_user_solve.py`
11. `tests/test_user_solve_trace.py`
12. `tests/test_fallback_ladder.py`
13. `tests/test_evidence_quality.py`
14. `tests/test_user_solve_session.py`
15. `docs/user_solve_layer.md`

Inspect report/gate/provenance code before modifying policy:

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

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless a command-plan-authorized diagnostic requires it.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current `decision_packet.md` treated as execution authority and `task_packet.json` as background only?
2. Did decision metadata remain valid, approved, on `engineering_branch`, and aligned with active `reverse-agent-iteration@v2`?
3. Were startup commands recorded before project gates/tests?
4. Does the first startup `git status --short` prove a clean source/test/doc start, or explicitly declare inherited dirty baseline files?
5. If source/test/doc files were dirty at startup, did prework provenance hard-block `SUCCESS` unless they were explicitly inherited baseline?
6. Was a current `prework_provenance_result.json` or equivalent artifact generated?
7. Did final-check enforce prework provenance and startup dirty ambiguity policy?
8. Were current IDs used in reports, pytest_result, gate artifacts, and closeout artifacts?
9. Were the previous audit limitations explicitly addressed?
10. Was `UserSolveHandoffPacket` or equivalent in-memory handoff contract implemented?
11. Does the handoff packet derive from an existing `UserSolveSessionBundle` or equivalent without duplicating session/result/trace/fallback logic?
12. Does the handoff packet include user-safe status, answer/candidate fields, confidence, validation status, evidence status, public message, next action, fallback summary, missing-evidence summary, and optional UI hints?
13. Does default handoff user serialization hide internal project paths, artifact paths, local paths, and developer trace references?
14. Does handoff developer/debug serialization preserve internal audit references explicitly?
15. Does handoff validation reject inconsistent states such as verified without passed validation, answer present with failed validation, or executable fallback metadata?
16. Does the handoff builder/factory remain in-memory and non-executing?
17. Does the handoff builder/factory avoid creating `project_state/user_sessions/`, `project_state/solve_tasks/`, or other persistent user task/session files?
18. Does fallback summary remain non-executing, with local/dynamic/high-risk steps blocked unless explicit synthetic policy allows metadata selection?
19. Does explicit synthetic permission still avoid actual tool/sample execution in this round?
20. Does the handoff preserve previous `candidate_found` pending-validation behavior?
21. Does the handoff preserve previous `verified` requires passed validation behavior?
22. Does the handoff preserve previous missing-evidence to deep-analysis/fallback behavior?
23. Does the handoff produce a clear user-facing `next_action` without exposing internal gate/report paths?
24. Does the handoff avoid claiming solved/static_verified/runtime_validated/audit_verified for any sample?
25. Was a current gate artifact generated, for example `project_state/gates/user_solve_handoff_result.json`?
26. Does the gate artifact prove no external invocation, dispatch capability, Web/API, DB/queue, scheduler/service, persistent session creation, sample execution, or subprocess/network execution was added?
27. Did tests cover prework provenance clean-start acceptance?
28. Did tests cover prework provenance dirty-start hard-block behavior?
29. Did tests cover explicit inherited baseline behavior separately from current-round changed files?
30. Did tests cover handoff user/developer serialization and redaction?
31. Did tests cover handoff validation errors?
32. Did tests cover handoff creation from candidate-found session bundles?
33. Did tests cover handoff creation from verified session bundles?
34. Did tests cover handoff creation from missing-evidence/deep-analysis session bundles?
35. Did existing user-solve/result/trace/fallback/session/evidence tests continue passing?
36. Did pytest_result record the real commands and exit codes?
37. Did command-plan authorize all executed commands and omit no executed commands?
38. Did final-check pass with current decision/report/round IDs?
39. Did run-closeout pass and archive corrected reports if command-plan authorized closeout?
40. Were forbidden files untouched?

## 6. Implementation Scope

Allowed implementation:

1. Add `reverse_agent/user_solve_handoff.py`.
   - Define `UserSolveHandoffPacket`, `HandoffFallbackSummary`, `HandoffUiHint`, or equivalent names.
   - Provide stable dict/JSON-like user and developer serialization.
   - Default user serialization must be redacted and must not include internal artifact paths, local paths, or developer trace references.
   - Developer serialization may include internal references.
   - Validation must reject inconsistent handoff states.

2. Update `reverse_agent/user_solve.py` and/or `reverse_agent/user_solve_session.py` minimally.
   - Add a non-executing helper that builds a handoff packet from an already-supplied in-memory `UserSolveSessionBundle`.
   - Preserve `adapt()`, `adapt_with_trace()`, `adapt_session_bundle()`, and existing session behavior.

3. Update `reverse_agent/project_gate.py`.
   - Add or extend a gate such as `prework-provenance`.
   - Add or extend a gate such as `user-solve-handoff`.
   - Generate `project_state/gates/prework_provenance_result.json` and `project_state/gates/user_solve_handoff_result.json` or equivalents.
   - Final-check must treat unauthorized source/test/doc dirty startup provenance ambiguity as blocking for `SUCCESS`.
   - Gate must verify importability, handoff schema coverage, redaction, session linkage, fallback linkage, no-execution/no-dispatch policy, no persistent session creation, and prework provenance enforcement.

4. Update report generation/report-summary.
   - Required Audit must explicitly discuss startup clean/dirty provenance.
   - `SUCCESS` reports must not normalize ambiguous prework dirty source/test/doc files.
   - Keep changed-file lists deduplicated.

5. Add tests:
   - `tests/test_user_solve_handoff.py`
   - update `tests/test_user_solve_session.py`
   - update `tests/test_user_solve.py`
   - update `tests/test_user_solve_contract.py` if needed for validation helpers
   - update `tests/test_user_solve_trace.py` only if needed
   - update `tests/test_fallback_ladder.py` only if needed
   - update `tests/test_evidence_quality.py` only if needed
   - update `tests/test_project_gate.py`
   - update `tests/test_project_reports.py`

6. Update `docs/user_solve_layer.md`.
   - Explain result/trace/fallback/session/handoff boundaries.
   - Explain that handoff is an in-memory response contract, not Web/API/persistence.
   - Document prework provenance expectation for local Codex runs.

Compatibility rules:

- Existing accepted tests from user-solve foundation, trace/fallback, and session-bundle rounds must continue passing.
- New modules must import without optional reverse-engineering tools installed.
- No real samples, local sample paths, IDA/Ghidra/OllyDbg paths, subprocesses, or network calls are required.
- Existing project gate/report/closeout semantics must remain compatible except where the new prework provenance hardening intentionally makes ambiguous startup dirty state blocking.

## 7. Tests

Startup sequence must be recorded first and must be a true pre-work capture:

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
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_user_solve_trace.py tests/test_fallback_ladder.py tests/test_user_solve_session.py tests/test_user_solve_handoff.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate user-solve-handoff --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_user_solve_handoff_provenance_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record actual commands and exit codes. `codex_execution_report.md` and `execution_report.md` must list real tests in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any condition occurs:

1. Current decision/report/round IDs do not match.
2. `skill_profiles` do not match active registry entries.
3. `task_packet.json` is treated as execution authority.
4. The first startup `git status --short` shows source/test/doc dirty files and those files are not explicitly declared as inherited baseline before implementation work.
5. Prework provenance gate is missing, stale, or not enforced by final-check.
6. Any forbidden path is modified.
7. Any sample, IDA, Ghidra, OllyDbg, debugger, emulator, harness, runtime probe, Web/API endpoint, database, queue, scheduler, remote runner, GitHub Actions dispatch/polling, Codex/Trae/Claude/Aider adapter, or IDA MCP adapter is executed or implemented.
8. Persistent `project_state/solve_tasks/` or `project_state/user_sessions/` files are created.
9. The handoff builder/factory executes tools rather than returning data-only contracts.
10. Fallback ladder selection executes tools or samples.
11. User-visible handoff output leaks internal project paths by default.
12. Developer-only references appear in default user output.
13. `verified` can be represented without passed validation evidence.
14. Missing evidence is treated as solved/static_verified/runtime_validated evidence.
15. The handoff packet duplicates session/result/trace/fallback responsibilities instead of deriving from existing contracts.
16. Existing user-solve result/trace/fallback/session behavior regresses.
17. Existing pipeline/harness/job/runner/command-plan/execution-log capabilities are duplicated or replaced.
18. Required focused tests are missing.
19. `project_state/gates/user_solve_handoff_result.json` or equivalent current gate artifact is missing.
20. `project_state/gates/prework_provenance_result.json` or equivalent current gate artifact is missing.
21. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
22. command-plan is missing, stale, or not respected.
23. final-check fails.
24. closeout is executed without command-plan authorization.
25. closeout is required but missing or failed.
26. The final report claims any concrete sample is solved, static_verified, runtime_validated, or audit_verified.

If only prework provenance hardening or only handoff packet is completed, but not both, do not claim `SUCCESS`; report `PARTIAL`, `BLOCKED`, or `REWORK_REQUIRED` with exact missing pieces.
