```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_user_solve_layer_foundation_big_step_v1",
  "round_id": "round_20260703_user_solve_layer_foundation_big_step_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_accepted_decision_id": "decision_20260703_required_audit_direct_evidence_rework_v1",
  "follows_accepted_round_id": "round_20260703_required_audit_direct_evidence_rework_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_33_user_solve_layer_foundation_big_step",
  "primary_goal": "Implement the first usable User Solve Layer foundation in one larger engineering round: result contract, state machine, safe fast wrapper adapter, evidence-quality mapper, and project gate/test coverage.",
  "command_plan_authority_required": true,
  "accepted_requires_user_solve_contract": true,
  "accepted_requires_state_machine": true,
  "accepted_requires_safe_fast_wrapper": true,
  "accepted_requires_evidence_quality_mapper": true,
  "accepted_requires_gate_artifact": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_state.py",
    "reverse_agent/user_solve.py",
    "reverse_agent/evidence_quality.py",
    "reverse_agent/project_gate.py",
    "tests/test_user_solve_contract.py",
    "tests/test_user_solve_state.py",
    "tests/test_user_solve.py",
    "tests/test_evidence_quality.py",
    "tests/test_project_gate.py"
  ],
  "allowed_documentation_files": [
    "docs/user_solve_layer.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260703_user_solve_layer_foundation_big_step_v1/*"
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
    "reverse_solving_candidate_search"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **User Solve Layer Foundation Big Step v1**.

This round is intentionally larger than a narrow evidence-sync round. It creates the first project-level user-facing solve abstraction, while still remaining an `engineering_branch` task. The target is not to solve a concrete sample. The target is to make future user-facing solving calls return a structured, safe, auditable result without exposing internal engineering files.

The round must deliver all of the following in one accepted execution:

1. `UserSolveResult` contract and validation rules.
2. `UserSolveStateMachine` with explicit state transitions.
3. Safe `FastSolveWrapper` that adapts existing in-memory or pipeline-like result dictionaries into user-facing results without executing tools or samples.
4. `EvidenceQualityMapper` that maps engineering evidence gaps to user-facing statuses/messages.
5. A project gate artifact, for example `project_state/gates/user_solve_layer_result.json`, proving the contract/state/wrapper/evidence-quality checks are present and current.
6. Focused tests covering valid and invalid states, visibility redaction, no internal path leakage by default, candidate-before-validation behavior, verified-result validation requirements, and evidence-gap mapping.
7. Updated execution reports and pytest record with current decision/round IDs.

Accepted target:

- Users can receive `candidate_found` with `validation_status=pending` and `evidence_status=building`.
- Users can receive `verified` only when validation has passed.
- User-visible serialization does not expose `decision_packet.md`, `command_plan.json`, `artifact_index.json`, `negative_results.json`, `codex_execution_report.md`, `pytest_result.txt`, or raw `project_state/` paths by default.
- Engineering trace references may exist internally but must be hidden from normal user-visible output unless an explicit developer/debug serialization is requested.
- No sample, IDA, Ghidra, OllyDbg, debugger, harness, runtime probe, Web/API endpoint, database, queue, scheduler, remote runner, Codex adapter, Trae adapter, or GitHub Actions dispatch is implemented or executed in this round.

## 2. Current Evidence

Mainline: `engineering_branch`.

The previous accepted round was:

- `decision_20260703_required_audit_direct_evidence_rework_v1`
- `round_20260703_required_audit_direct_evidence_rework_v1`
- audit outcome: `ACCEPTED`

Evidence from the previous accepted round:

1. `codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for `decision_20260703_required_audit_direct_evidence_rework_v1`.
2. `pytest_result.txt` reported `PASSED` for the same decision/report/round and included the required startup sequence plus focused pytest.
3. `final_gate_result.json` passed, including decision/report matching, pytest matching, Required Audit coverage, command-plan authority, and closeout checks.
4. `run_closeout_result.json` passed and close-round reached `CLOSED`.
5. Required Audit direct-evidence validation was repaired; reports now cite direct artifacts and no longer use `ci_audit_handoff_bundle.json` as a generic substitute.

Background project architecture evidence:

- `project_state/task_packet.json` remains background and states `execution_scope=decision_packet_controls_current_round`; it does not control this round.
- `current_state.json` and `artifact_index.json` still describe the older `samplereverse` sample-state backlog. Those sample artifacts are not current execution evidence for this engineering round.
- `negative_results.json` blocks repeated reverse-solving failures such as old sample_solver blind search, budget-only beam expansion, compare_semantics_agree=false primary frontier, and full solve_reports commits. This round does not enter those directions.
- Existing runner/job/CI/orchestration capabilities exist in project history and current gates, including command-plan, execution-log, local execution bundle, codex prompt packet, agent runner dry-run artifacts, and execute-decision evidence. Do not duplicate those capabilities. Build the new User Solve Layer as a user-facing result abstraction above existing pipeline/runner concepts.

Uploaded long-term planning context establishes two relevant constraints:

1. The broader system should evolve toward Web console, Planner/Auditor API, command-plan authorization, AgentRunner execution, GitHub CI verification, Project Gate final-check, and project_state evidence. This round contributes only the user-facing result layer, not the full web/control-plane system.
2. User Solve Layer should separate user-facing quick results from engineering evidence: user side returns answer/candidate/status/confidence/message, while engineering side continues recording evidence, artifact, execution_log, missing_evidence, and audit data.

Artifact freshness policy:

- Current-round gate/report artifacts must carry `decision_20260703_user_solve_layer_foundation_big_step_v1` and `round_20260703_user_solve_layer_foundation_big_step_v1`.
- Historical sample artifacts remain background only.
- New user-solve test fixtures must be synthetic and local to tests; do not use real sample binaries.

Command-plan policy:

- `project_state/gates/command_plan.json` is the execution authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Tests in this decision are targets; command-plan is the binding execution authority.
- Valid profiles are `fast`, `standard`, and `full`; do not use `medium`.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not run IDA, Ghidra, OllyDbg, debuggers, emulators, harnesses, runtime probes, or sample execution.

Do not implement Web/API endpoints, database, queue, scheduler, service, remote runner dispatch, GitHub Actions dispatch/polling, Codex adapter execution, Trae adapter execution, Claude Code adapter execution, Aider adapter execution, IDA MCP adapter, or dynamic debugging.

Do not rewrite existing pipeline, solver, harness, command-plan, execution-log, job, or AgentRunner capabilities. The user-solve layer must wrap or adapt existing result concepts, not replace the mature internal tools.

Do not expose internal engineering files in default user-visible output. In particular, do not expose raw references to:

- `project_state/decision_packet.md`
- `project_state/gates/command_plan.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `project_state/codex_execution_report.md`
- `project_state/pytest_result.txt`

Do not mutate forbidden paths listed in `decision_contract`.

Do not add new dynamic facts to `.codex-skills/`.

Do not claim any sample is solved, static_verified, runtime_validated, or audit_verified.

Do not treat filename/category metadata as solve evidence.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

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

Inspect existing orchestration and result-adjacent code before implementing:

1. `reverse_agent/pipeline.py`
2. `reverse_agent/harness.py`
3. `reverse_agent/project_jobs.py`
4. `reverse_agent/project_agent_runner.py`
5. `reverse_agent/project_runner_contract.py`
6. `reverse_agent/project_gate.py`
7. `tests/test_pipeline.py`
8. `tests/test_harness.py`
9. `tests/test_project_jobs.py`
10. `tests/test_project_agent_runner.py`
11. `tests/test_project_runner_contract.py`
12. `tests/test_project_gate.py`

Inspect relevant gates:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/execution_log.json`
4. `project_state/gates/local_execution_bundle.json`
5. `project_state/gates/codex_prompt_packet.json`
6. `project_state/gates/agent_runner_dry_run_result.json`
7. `project_state/gates/execute_decision_result.json`
8. `project_state/gates/run_closeout_result.json`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current `decision_packet.md` treated as the only execution authority and `task_packet.json` as background only?
2. Did decision metadata remain valid, approved, on `engineering_branch`, and aligned with active `reverse-agent-iteration@v2`?
3. Were startup commands recorded before project gates?
4. Was startup-snapshot recorded before substantive gate/test execution?
5. Did Codex inspect existing pipeline, harness, job, runner, runner contract, and project gate code before implementing user-solve code?
6. Did implementation avoid duplicating existing pipeline, solver, harness, command-plan, execution-log, job, and AgentRunner capabilities?
7. Were changes limited to the allowed source/test/documentation/generated artifact paths?
8. Were forbidden files not modified?
9. Was `UserSolveResult` implemented with stable JSON/dict serialization?
10. Were user statuses restricted to an explicit enum including `uploaded`, `fast_analyzing`, `candidate_found`, `validating`, `verified`, `deep_analysis_running`, `failed`, and `blocked`?
11. Were validation statuses restricted to an explicit enum including `not_started`, `pending`, `passed`, `failed`, and `unavailable`?
12. Were evidence statuses restricted to an explicit enum including `none`, `partial`, `building`, `complete`, and `failed`?
13. Does `verified` require passed validation and a usable answer or candidate?
14. Does `candidate_found` allow validation to remain pending?
15. Does default user-visible serialization hide internal engineering paths and developer trace references?
16. Is there an explicit developer/debug serialization path that can retain trace references for engineering use without becoming the default user output?
17. Was `UserSolveStateMachine` implemented with allowed transitions and rejection of invalid transitions?
18. Does `blocked` require a clear reason/message?
19. Was `EvidenceQualityMapper` implemented to translate engineering missing_evidence into user-facing status/message without exposing raw internal files?
20. Does missing targeted decompile/static evidence map to `deep_analysis_running` or equivalent non-terminal user status rather than immediate user failure?
21. Was `FastSolveWrapper` implemented as a safe adapter over in-memory or pipeline-like result data without executing samples/tools?
22. Does the wrapper convert a high-confidence candidate into `candidate_found` with pending validation when validation evidence is absent?
23. Does the wrapper convert passed validation into `verified` only when validation evidence supports it?
24. Does the wrapper return a clear `failed` or no-candidate result when no candidate exists?
25. Does the wrapper return `blocked` with reason when the input indicates tool/environment/policy blocking?
26. Did tests cover invalid verified-without-validation cases?
27. Did tests cover candidate-before-validation behavior?
28. Did tests cover user-visible redaction of `project_state`, `decision_packet`, `command_plan`, `artifact_index`, `negative_results`, `codex_execution_report`, and `pytest_result` references?
29. Did tests cover state machine valid and invalid transitions?
30. Did tests cover evidence-quality mapping from missing engineering evidence to user-facing fallback status?
31. Did tests cover the fast wrapper candidate/verified/no-candidate/blocked branches?
32. Was a current gate artifact generated for the user-solve layer foundation?
33. Did final-check pass with current decision/report/round IDs?
34. Did `pytest_result.txt` match `tests_ran` in the report?
35. Did command-plan authorize all executed commands and omit no executed commands?
36. Did run-closeout pass and archive the corrected reports if command-plan authorized closeout?
37. Did the round avoid Web/API, DB/queue/scheduler, remote runner, GitHub Actions dispatch/polling, IDA/Ghidra/OllyDbg, IDA MCP, runtime probe, dynamic debugging, and concrete reverse solving?
38. Did the final report avoid claiming solved/static_verified/runtime_validated/audit_verified for any sample?

## 6. Implementation Scope

This is a large but bounded engineering implementation round.

Allowed implementation:

1. Add `reverse_agent/user_solve_contract.py`.
   - Define enums or equivalent validated constants for user status, validation status, evidence status, and mode.
   - Define `UserSolveCandidate` and `UserSolveResult` as dataclasses or structured objects.
   - Provide validation and serialization helpers.
   - Provide default user-visible serialization that redacts internal engineering paths.
   - Provide explicit developer/debug serialization that can include `developer_trace_ref` and internal references.

2. Add `reverse_agent/user_solve_state.py`.
   - Define allowed state transitions.
   - Reject invalid transitions.
   - Require reason/message for `blocked`.
   - Keep transition logic independent from real sample execution.

3. Add `reverse_agent/evidence_quality.py`.
   - Define `EvidenceQuality` / `MissingEvidenceAssessment` or equivalent.
   - Map missing engineering evidence to user-facing status/message.
   - Treat evidence gaps as fallback/deep-analysis triggers where appropriate, not immediate user failure.
   - Avoid exposing raw `project_state` internals in default user messages.

4. Add `reverse_agent/user_solve.py`.
   - Implement a safe `FastSolveWrapper` that accepts in-memory or pipeline-like result dictionaries/objects.
   - Convert candidates and validation fields into `UserSolveResult`.
   - Do not call external tools, sample binaries, IDA, Ghidra, debuggers, harnesses, subprocesses, web, network, or runner adapters.
   - Do not implement Web/API endpoints.

5. Update `reverse_agent/project_gate.py` minimally.
   - Add a current-round gate command or final-check hook for the User Solve Layer foundation, for example `user-solve-layer`.
   - The gate should verify importability, enum coverage, redaction behavior, and safe/no-execution policy through static checks or test-backed evidence.
   - The gate must write `project_state/gates/user_solve_layer_result.json` or equivalent with current decision/round/report IDs.

6. Add tests:
   - `tests/test_user_solve_contract.py`
   - `tests/test_user_solve_state.py`
   - `tests/test_evidence_quality.py`
   - `tests/test_user_solve.py`
   - Update `tests/test_project_gate.py` only for the new gate/final-check integration.

7. Optional documentation:
   - Add `docs/user_solve_layer.md` summarizing the user-facing contract and engineering boundary.
   - Documentation must not replace tests or gate evidence.

Compatibility rules:

- Do not break existing pipeline/harness/project_gate/job/runner tests.
- Do not rename existing public functions unless tests and compatibility adapters prove it is safe.
- New modules must be importable without optional reverse tooling installed.
- The implementation must work on synthetic tests without local samples or IDA.

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

Required command policy:

- First generate or read `project_state/gates/command_plan.json` through the existing command-plan flow.
- Execute only commands authorized by `command_plan.commands`.
- Do not execute any command listed in `command_plan.omitted_commands`.
- If this Tests section conflicts with command-plan, command-plan wins.

Expected validation coverage, subject to command-plan authorization:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_evidence_quality.py tests/test_user_solve.py tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate user-solve-layer --state-dir project_state
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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_user_solve_layer_foundation_big_step_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record actual commands and exit codes. `codex_execution_report.md` and `execution_report.md` must list the real tests in `tests_ran`.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any condition occurs:

1. The current decision/report/round IDs do not match.
2. `skill_profiles` do not match active registry entries.
3. `task_packet.json` is treated as execution authority.
4. Any forbidden path is modified.
5. The implementation executes or attempts to execute a sample, solver search, harness, IDA, Ghidra, OllyDbg, debugger, emulator, runtime probe, web/network call, Web/API endpoint, database, queue, scheduler, remote runner, Codex adapter, Trae adapter, GitHub Actions dispatch/polling, or IDA MCP adapter.
6. Existing pipeline/harness/job/runner capabilities are duplicated or replaced instead of wrapped/adapted.
7. `verified` can be created without passed validation.
8. Default user-visible serialization leaks internal engineering paths or raw project_state artifacts.
9. `candidate_found` requires complete validation before returning a candidate.
10. Missing static evidence immediately becomes user-visible hard failure when fallback/deep-analysis status is appropriate.
11. The fast wrapper invokes external tools, subprocesses, samples, runners, or network.
12. Tests are missing for contract validation, state transitions, redaction, evidence-quality mapping, and wrapper branches.
13. `project_state/gates/user_solve_layer_result.json` or equivalent current gate artifact is missing when the new gate is implemented.
14. `pytest_result.txt` is missing, stale, or inconsistent with report `tests_ran`.
15. command-plan is missing, stale, or not respected.
16. final-check fails.
17. closeout is executed without command-plan authorization.
18. closeout is required but missing or failed.
19. The final report claims any concrete sample is solved, static_verified, runtime_validated, or audit_verified.

If only part of the User Solve Layer foundation is implemented, do not claim `SUCCESS`; report `PARTIAL` or `REWORK_REQUIRED` with exact missing modules/tests/gates.
