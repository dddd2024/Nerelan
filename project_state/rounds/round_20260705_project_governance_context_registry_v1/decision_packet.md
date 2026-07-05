```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260705_project_governance_context_registry_v1",
  "round_id": "round_20260705_project_governance_context_registry_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_accepted_decision_id": "decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1",
  "follows_last_accepted_round_id": "round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_40_project_governance_context_registry_v1",
  "primary_goal": "Create a small project-governance foundation that gives future GPT planning and auditing a deterministic current-state entrypoint: state_manifest, current_context_packet, and workstream registry. This round must inventory current state and existing capabilities, classify current vs historical artifacts, seed workstreams without starting new execution branches, and add gates/tests/docs. It must not process real reverse samples, run external analysis tools, dispatch runners, invoke model APIs, create a database, modify GitHub workflows, or implement Web/API runtime infrastructure.",
  "command_plan_authority_required": true,
  "accepted_requires_state_manifest": true,
  "accepted_requires_context_packet": true,
  "accepted_requires_workstream_registry": true,
  "accepted_requires_project_gate_integration": true,
  "accepted_requires_existing_capability_check": true,
  "accepted_requires_no_execution_expansion": true,
  "allowed_source_files": [
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context_builder.py",
    "reverse_agent/project_workstreams.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context_builder.py",
    "tests/test_project_workstreams.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py"
  ],
  "allowed_documentation_files": [
    "docs/project_governance_context.md",
    "docs/state_manifest.md",
    "docs/workstream_registry.md"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/state_manifest.json",
    "project_state/context/current_context_packet.json",
    "project_state/roadmap/workstreams.json",
    "project_state/gates/project_governance_context_result.json",
    "project_state/gates/project_governance_context_snapshot.json",
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
    "project_state/rounds/round_20260705_project_governance_context_registry_v1/*"
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
    "frontend/*"
  ],
  "forbidden_capabilities_this_round": [
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
    "auto_iteration",
    "cleanup_apply_or_delete"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Project Governance Context Registry v1**.

The previous accepted round built a manual-mode Web orchestrator MVP. The next required foundation is not another Web/API expansion and not another user-solve feature. The next round should make project-state consumption deterministic for future GPT planning and auditing by adding three governance artifacts and the minimal code/gates/tests needed to keep them current:

1. `project_state/state_manifest.json`
   - A compact, deterministic entrypoint for the current project state.
   - It must identify the active decision, active round, report, pytest result, execution log, command-plan, final-check, closeout state, latest accepted baseline, current generated artifacts, historical nonblocking artifacts, and missing optional artifacts.
   - It must not replace `project_state` as the audit fact source; it only indexes current state.

2. `project_state/context/current_context_packet.json`
   - A bounded context packet for GPT planning/auditing.
   - It must summarize current authority, mainline, active decision, report/test/gate alignment, artifact freshness, existing capabilities, negative-results constraints, and stop conditions.
   - It must prevent long-term prompt drift by keeping dynamic engineering facts out of `.codex-skills/` and prompt docs.

3. `project_state/roadmap/workstreams.json`
   - A lightweight workstream registry for future directions.
   - It must use the lifecycle: `IDEA -> CANDIDATE -> ROADMAP_ACCEPTED -> READY_FOR_DECISION -> ACTIVE_ROUND -> ACCEPTED / DEFERRED / REJECTED`.
   - It must seed known workstreams without activating more than the current decision.
   - It must make clear that new ideas do not become execution authority until selected by `project_state/decision_packet.md`.

Add project-gate integration so future rounds can validate these artifacts. The implementation must be small, deterministic, file-backed, and testable. It must not add a database, service, queue, scheduler, Web runtime, runner dispatch, model API, CI dispatch, or real reverse-sample processing.

Accepted target:

- Mainline: `project_governance`.
- Current task authority remains `project_state/decision_packet.md`.
- `task_packet.json` remains background only.
- `command_plan.json` remains command authority.
- `project_state` files remain audit fact sources.
- `state_manifest.json`, `current_context_packet.json`, and `workstreams.json` are generated/index artifacts, not replacements for hard evidence.

## 2. Current Evidence

Current mainline for this next round: `project_governance`.

Current active decision before this update was `decision_20260704_manual_mode_web_orchestrator_mvp_big_step_v1`, and its audit conclusion was accepted based on current report/test/gate evidence.

Observed accepted baseline:

- `project_state/codex_execution_report.md` reported `SUCCESS` and `acceptance_recommendation=ACCEPTED` for `round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1`.
- `project_state/pytest_result.txt` reported `PASSED` with command blocks and successful pytest suites.
- `project_state/gates/execution_log.json` was current, hybrid-derived from pytest result, command-plan, and closeout execution log.
- `project_state/gates/final_gate_result.json` passed, with no blocking reasons and no active warnings.
- `project_state/rounds/round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1/round_manifest.json` archived current report, neutral execution report, decision packet, and pytest result.

Dynamic state caveat:

- `project_state/current_state.json`, `project_state/task_packet.json`, and `project_state/artifact_index.json` still contain older sample-reverse context from `state_20260618_134029_d6bd033d2532`.
- Those files are background context only for this governance round.
- Their missing sample artifacts must not be treated as current blockers.
- They must not trigger reverse solving, artifact collection, runtime validation, or full `solve_reports/` reads.

Existing capabilities that must not be duplicated:

- `project_gate` hard gates.
- command-plan authority.
- execution log synthesis and validation.
- report-summary synthesis.
- run-closeout and round archive.
- policy-lint and prompt-consistency foundations.
- job lifecycle and runner contract foundations.
- manual-mode orchestrator and user-solve workbench foundations.
- artifact role taxonomy separating generated, referenced, historical, and archived artifacts.

Capability gap for this round:

- There is no stable `project_state/state_manifest.json` entrypoint observed on the default branch.
- There is no stable `project_state/context/current_context_packet.json` observed on the default branch.
- There is no stable `project_state/roadmap/workstreams.json` observed on the default branch.
- Therefore future GPT planning/auditing still has to infer current state from many files, increasing drift risk.

Negative results:

- `project_state/negative_results.json` blocks old sample-solver blind search, budget-only expansion, invalid frontier reuse, full `solve_reports` commits, and repeated stale diagnostics.
- This round is governance-only and must not enter those reverse-solving directions.

Artifact freshness policy:

- Current-round governance artifacts must carry `decision_20260705_project_governance_context_registry_v1` and `round_20260705_project_governance_context_registry_v1`.
- Historical user-solve, runner, CI, and sample artifacts may be referenced only as historical/backlog evidence unless their IDs are current.
- Missing historical sample artifacts are nonblocking for this governance round.

Tool and execution policy:

- Local deterministic Python code and tests are allowed only if authorized by command-plan.
- External reverse tools, IDA/Ghidra/OllyDbg, model APIs, runner dispatch, GitHub workflow dispatch, databases, queues, Web services, and real sample execution are forbidden.
- Heavy artifacts such as full `solve_reports/` and full `PROJECT_PROGRESS_LOG.txt` must not be read.
- Closeout is allowed only if command-plan authorizes it.

This round must not repeat existing prompt-versioning work. Existing prompt docs, policy-lint, and prompt-consistency should be treated as foundations. The new work is prompt-state decoupling through generated context and registry artifacts.

## 3. Do Not Do

Do not solve a concrete reverse sample.

Do not process real samples, real uploads, training samples, or local binary corpora.

Do not invoke IDA, Ghidra, OllyDbg, debuggers, emulators, unpackers, runtime probes, or external analysis tools.

Do not invoke model APIs, planner APIs, auditor APIs, Codex CLI, remote agents, CI workflows, or automatic runners.

Do not implement a production HTTP service, database, queue, scheduler, background service, remote dispatch, CI polling, or auto-iteration.

Do not modify `.github/workflows/*`.

Do not modify `.codex-skills/*` or store dynamic project facts in long-term prompt/skill files.

Do not rewrite existing manual-mode Web, user-solve workbench, runner, solver, harness, or CI foundations.

Do not scan full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

Do not perform cleanup deletion. `cleanup-apply`, destructive deletion, archive compaction, and tombstone generation are out of scope for this round.

Do not claim any sample is solved, statically verified, runtime validated, or audit verified.

Do not treat `state_manifest.json`, `current_context_packet.json`, or `workstreams.json` as replacements for `decision_packet`, `command_plan`, `execution_log`, `pytest_result`, `final_check`, or report evidence.

Do not activate more than one workstream. This decision is the only `ACTIVE_ROUND` workstream for the round.

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

Inspect current gates and accepted baseline:

1. `project_state/gates/command_plan.json`
2. `project_state/gates/execution_log.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/run_closeout_result.json`
6. `project_state/gates/round_close_snapshot.json`
7. `project_state/rounds/round_20260704_manual_mode_web_orchestrator_mvp_big_step_v1/round_manifest.json`

Inspect existing governance/gate surfaces before adding new code:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_reports.py`
3. `reverse_agent/project_jobs.py`
4. `reverse_agent/project_runner_contract.py`
5. `reverse_agent/orchestrator_context.py`
6. `tests/test_project_gate.py`
7. `tests/test_project_reports.py`
8. `tests/test_project_jobs.py`
9. `tests/test_orchestrator_context.py`
10. `docs/prompts/README.md`

Check whether these paths already exist before creating them:

1. `project_state/state_manifest.json`
2. `project_state/context/current_context_packet.json`
3. `project_state/roadmap/workstreams.json`
4. `reverse_agent/project_state_manifest.py`
5. `reverse_agent/project_context_builder.py`
6. `reverse_agent/project_workstreams.py`

Do not inspect full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt` unless command-plan authorizes a bounded diagnostic. Default behavior should be manifest-first and current-gate-first, not full-tree scanning.

## 5. Required Audit

The execution report must answer each item with direct evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was `project_state/decision_packet.md` treated as the only task authority?
2. Was `project_state/task_packet.json` treated as background only?
3. Did `decision_meta` remain valid, `APPROVED`, and aligned with active `reverse-agent-iteration@v2`?
4. Was the previous accepted manual-mode orchestrator round treated as the baseline?
5. Were existing project_gate/report/job/orchestrator capabilities inspected before adding new governance code?
6. Did the implementation avoid duplicating existing prompt docs, policy-lint, prompt-consistency, command-plan, execution-log, report-summary, and closeout mechanisms?
7. Was `project_state/state_manifest.json` generated?
8. Does `state_manifest.json` carry current decision, round, report, pytest, command-plan, execution-log, final-check, and closeout references?
9. Does `state_manifest.json` classify current, generated, historical_nonblocking, archived, missing, and optional artifacts without treating historical missing sample artifacts as blockers?
10. Does `state_manifest.json` preserve `project_state` files as audit fact sources rather than replacing them?
11. Was `project_state/context/current_context_packet.json` generated?
12. Does `current_context_packet.json` summarize current authority, mainline, accepted baseline, state digest, artifact freshness, negative-results constraints, existing capabilities, forbidden capabilities, and stop conditions?
13. Does `current_context_packet.json` avoid embedding large file contents, full solve reports, or dynamic facts in prompt/skill files?
14. Was `project_state/roadmap/workstreams.json` generated?
15. Does `workstreams.json` use the required lifecycle states?
16. Does `workstreams.json` mark only this governance round as active, if any workstream is active?
17. Does `workstreams.json` keep User Solve Layer, AgentRunner, CI, Web, database/indexing, state hygiene, reverse solving, and tool integration as separate workstreams rather than mixing them?
18. Does the workstream registry make clear that roadmap entries are not execution authority until selected by `decision_packet.md`?
19. Was project-gate integration added for governance context validation?
20. Did the gate generate `project_state/gates/project_governance_context_result.json` or equivalent current artifact?
21. Did the gate generate `project_state/gates/project_governance_context_snapshot.json` or equivalent current snapshot?
22. Do all new gate artifacts carry current decision/report/round IDs?
23. Did command-plan authorize every executed command?
24. Were command-plan omitted commands left unexecuted?
25. Did pytest_result record real commands and exit codes?
26. Did focused tests cover state manifest, context packet, workstream registry, and gate validation?
27. Did broad project gate/report tests continue to pass?
28. Did final-check pass with current IDs?
29. Did report-summary synthesis pass and match the report summary?
30. Did run-closeout pass if authorized?
31. Were forbidden files untouched?
32. Were `.github/workflows/*`, `.codex-skills/*`, `solve_reports/*`, and real sample directories untouched?
33. Did the implementation avoid model API calls, runner dispatch, external tool execution, database/queue creation, Web service creation, CI dispatch, and auto-iteration?
34. Did the final report avoid any solved/static/runtime/audit verification claim for concrete samples?
35. Did the final report explicitly state that `state_manifest`, `current_context_packet`, and `workstreams` are indexes/governance artifacts, not audit fact replacements?

## 6. Implementation Scope

Allowed implementation is limited to a small project-governance layer.

### A. State Manifest v1

Add `reverse_agent/project_state_manifest.py` or compatibly extend an existing equivalent module if one already exists.

Required behavior:

- Read bounded current files from `project_state/`.
- Extract current decision ID, round ID, report ID, state build ID, state digest, mainline, report status, acceptance recommendation, pytest status, command-plan status, execution-log status, final-check status, and closeout status.
- Record paths for the current decision, report, neutral execution report, pytest, command-plan, execution-log, final-check, closeout, round manifest, report-summary synthesis, and generated governance artifacts.
- Classify artifact roles as `current`, `generated_or_updated`, `referenced`, `historical_nonblocking`, `archived`, `missing_optional`, or `missing_blocking`.
- Treat old sample artifact gaps as historical/backlog unless the active decision explicitly requires them.
- Write `project_state/state_manifest.json` deterministically with stable ordering.

Do not scan full `solve_reports/`. Do not scan full `project_state/rounds/`; only read the active archived round manifest when known.

### B. Current Context Packet v1

Add `reverse_agent/project_context_builder.py` or compatibly extend an existing equivalent module if one already exists.

Required behavior:

- Generate `project_state/context/current_context_packet.json`.
- Include a compact `planner_context` and `auditor_context` section.
- Summarize task authority, command authority, current mainline, previous accepted baseline, existing capabilities, dynamic state caveats, negative-results constraints, allowed/forbidden capability profile, artifact freshness summary, and next-action policy.
- Include `source_files` with paths and digests where available.
- Include `do_not_assume` entries for missing context/workstream/state artifacts and stale sample artifacts.
- Keep the packet bounded and deterministic.

The context packet must be safe to feed into future GPT planning/auditing without reading large logs or stale historical artifacts.

### C. Workstream Registry v1

Add `reverse_agent/project_workstreams.py` or compatibly extend an existing equivalent module if one already exists.

Required behavior:

- Generate `project_state/roadmap/workstreams.json`.
- Use lifecycle states exactly from: `IDEA`, `CANDIDATE`, `ROADMAP_ACCEPTED`, `READY_FOR_DECISION`, `ACTIVE_ROUND`, `ACCEPTED`, `DEFERRED`, `REJECTED`.
- Seed at least these workstream families as separate entries:
  - `project_governance_context_registry`
  - `state_hygiene_retention_policy`
  - `manual_mode_web_orchestrator`
  - `user_solve_layer`
  - `agent_runner_dispatch`
  - `github_ci_and_state_gate`
  - `reverse_solving_capability_matrix`
  - `tool_integration_ida_ghidra_debugger`
  - `sqlite_query_index`
- Mark the current workstream as `ACTIVE_ROUND` only for this decision.
- Mark already accepted foundations as accepted or baseline references without reopening their scope.
- Mark deferred/heavier directions such as database, runner dispatch, IDA MCP, dynamic debugging, and auto-iteration as not active unless future decisions select them.

### D. Project Gate Integration

Extend `reverse_agent/project_gate.py` with a bounded governance gate, or add a small helper invoked by project_gate.

Required generated artifacts:

- `project_state/gates/project_governance_context_result.json`
- `project_state/gates/project_governance_context_snapshot.json`

Required checks:

- state manifest exists and is current.
- context packet exists and is current.
- workstream registry exists and is current.
- IDs match the current decision/round/report.
- only allowed workstream is active.
- no forbidden capabilities are enabled.
- missing historical sample artifacts are classified as nonblocking.
- generated artifacts are indexes/governance artifacts, not fact-source replacements.

### E. Report and Closeout Compatibility

Update report-summary/final-check only as needed to recognize the new governance artifacts.

Do not weaken existing checks. Do not remove current checks for command-plan authority, execution-log consistency, pytest/report matching, final-check, closeout, or artifact role taxonomy.

### F. Documentation

Add concise docs:

- `docs/project_governance_context.md`
- `docs/state_manifest.md`
- `docs/workstream_registry.md`

Docs must explain:

- why dynamic facts belong in project_state/context artifacts rather than long-term prompts;
- why `state_manifest` is an index, not the fact source;
- how workstream lifecycle prevents direct execution of new ideas;
- how this remains compatible with manual GPT audit + Codex execution.

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
python -m pytest tests/test_project_state_manifest.py tests/test_project_context_builder.py tests/test_project_workstreams.py -q
python -m pytest tests/test_project_gate.py tests/test_project_reports.py -q
python -m reverse_agent.project_gate project-governance-context --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260705_project_governance_context_registry_v1
```

If the project-gate CLI name differs, implement the smallest compatible CLI surface and record the exact command in command-plan and pytest_result.

Test expectations:

- New unit tests pass.
- Existing gate/report tests pass.
- Governance gate passes.
- final-check passes.
- report-summary passes.
- run-closeout passes if authorized.
- No command-plan omissions are executed.
- No forbidden files are mutated.

## 8. Stop Conditions

Stop immediately and report `BLOCKED` if:

1. The repository root is not `F:\reverse-agent` or `git rev-parse --show-toplevel` does not match.
2. Startup detects untracked or dirty source/test files before implementation and they are not recorded by startup/prework provenance.
3. `decision_meta` cannot be parsed or is not `APPROVED`.
4. `reverse-agent-iteration@v2` is not active in `.codex-skills/registry.json`.
5. `command_plan.json` cannot be generated or does not authorize required commands.
6. The implementation would require reading full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.
7. The implementation would require Web runtime, database, queue, scheduler, runner dispatch, model API, CI dispatch, or external reverse tool execution.
8. The implementation would need to modify `.github/workflows/*`, `.codex-skills/*`, `project_state/current_state.json`, `project_state/task_packet.json`, `project_state/artifact_index.json`, or `project_state/negative_results.json`.
9. More than one workstream would need to be marked `ACTIVE_ROUND`.
10. The new governance artifacts would need to be treated as fact-source replacements rather than indexes.
11. Tests fail and the failure is not explained with a bounded fix in the allowed scope.
12. final-check fails.
13. report-summary cannot reconcile report status with generated evidence.
14. Any concrete sample solve/static/runtime/audit verification claim is introduced.

If a stop condition is hit, write the execution report with `status=BLOCKED` or `status=FAILED` as appropriate, preserve all available evidence, and do not run closeout unless command-plan explicitly allows diagnostic closeout for failed rounds.
