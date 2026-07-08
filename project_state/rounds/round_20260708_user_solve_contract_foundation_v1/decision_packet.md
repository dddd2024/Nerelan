```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_user_solve_contract_foundation_v1",
  "round_id": "round_20260708_user_solve_contract_foundation_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_state_domain_taxonomy_final_status_rework_v1",
  "follows_last_round_id": "round_20260708_state_domain_taxonomy_final_status_rework_v1",
  "previous_audit_outcome": "ACCEPTED_WITH_LIMITATIONS",
  "roadmap_basis": "docs/roadmap/evidence_centered_user_solve_execution_plan.md#Round-B-User-Solve-Contract-and-State-Machine",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "command_plan_must_include_explicit_pytest_command": true,
  "command_plan_must_not_omit_report_summary": true,
  "command_plan_must_not_omit_execution_log": true,
  "command_plan_must_not_omit_final_check": true,
  "command_plan_must_not_omit_run_closeout": true,
  "command_plan_must_not_omit_close_round": true,
  "allowed_source_files": [
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/user_solve_views.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_control_plane.py"
  ],
  "allowed_test_files": [
    "tests/test_user_solve_contract.py",
    "tests/test_user_solve_state.py",
    "tests/test_user_solve_errors.py",
    "tests/test_user_solve_views.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py"
  ],
  "allowed_docs": [
    "docs/user_solve_contract.md"
  ],
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_foundation_v1/round_manifest.json",
    "project_state/rounds/round_20260708_user_solve_contract_foundation_v1/decision_packet.md",
    "project_state/rounds/round_20260708_user_solve_contract_foundation_v1/codex_execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_foundation_v1/execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_foundation_v1/pytest_result.txt"
  ],
  "forbidden_mutated_paths": [
    ".codex-skills/*",
    ".github/workflows/*",
    "frontend/*",
    "solve_reports/*",
    "training_materials/local_reverse/*",
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    "project_state/state_manifest.json",
    "project_state/context/*",
    "project_state/roadmap/workstreams.json",
    "project_state/domains/*",
    "project_state/archives/*",
    "project_state/deletions/*",
    "project_state/blob_store/*",
    "project_state/*.db",
    "project_state/index.sqlite",
    "docs/roadmap/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement the next roadmap step: **User Solve Contract and State Machine foundation**.

This round must define the user-facing solve result contract without implementing solving, Web runtime, tool invocation, or sample execution.

The purpose is to give later reverse_solving, Evidence Trace, Fast Static Solve, and Web Workbench rounds a stable payload to consume.

The minimum contract must cover:

```text
1. UserSolveTask;
2. UserSolveResult;
3. CandidateResult;
4. ValidationStatus;
5. user-facing solve status enum;
6. state transition validator;
7. failed / blocked reason model;
8. internal evidence reference fields that do not expose raw governance files;
9. JSON serialization / deserialization with stable schema_version;
10. documentation explaining user-layer vs engineering-evidence-layer boundaries.
```

This is an engineering foundation round. It is not a reverse_solving round and must not generate flags, candidates from binaries, or run samples.

## 2. Current Evidence

Current task authority is:

```text
project_state/decision_packet.md
```

`task_packet.json` is background only and must not control this round.

Current mainline:

```text
engineering_branch
```

Reason for `engineering_branch`:

```text
The project mainline registry does not currently require a separate user_solve_layer mainline. This round implements contract/schema/state-machine infrastructure only, so it belongs under engineering_branch. Future rounds may use this contract from reverse_solving or Web workbench, but those are not part of this round.
```

Previous accepted baseline:

```text
Decision: decision_20260708_state_domain_taxonomy_final_status_rework_v1
Round: round_20260708_state_domain_taxonomy_final_status_rework_v1
Audit outcome: ACCEPTED_WITH_LIMITATIONS
```

The previous round repaired final status consistency:

```text
1. final_gate_result.json gate_status became PASSED;
2. final_gate_result.status_summary became SUCCESS / ACCEPTED;
3. run_closeout.close_round_result.report_status became SUCCESS;
4. round_manifest matched SUCCESS / ACCEPTED;
5. pytest_result recorded explicit pytest and 1171 passed.
```

Remaining non-blocking background warnings from the previous round:

```text
1. scoped_metadata_coverage warnings are legacy/non-blocking;
2. context_domain_awareness warnings show stale context packet facts but are advisory/non-blocking;
3. historical sample artifacts are non-blocking for current non-sample evidence policy.
```

Existing capabilities to reuse:

```text
decision-packet authority
command-plan authority
project_gate
preflight
gate-profile
command-plan
execution-log
report-summary
final-check
run-closeout
close-round
round manifest archive
pytest_result parser
report status consistency checks
project_state domain taxonomy skeletons
roadmap document for evidence-centered user solve foundation
```

Existing User Solve related evidence:

```text
Repository search currently finds the User Solve Contract names in the roadmap document, not as stable code modules. Historical user_solve_* gate artifacts exist but are not current authority for this round. If analogous code already exists locally, extend it rather than duplicating it.
```

This round must avoid repeating existing gate, report, command-plan, final-check, run-closeout, or project_state mechanisms.

Artifact freshness policy:

```text
1. All current-round gate artifacts must match this decision_id and round_id.
2. Historical user_solve_* artifacts are not current acceptance evidence.
3. Historical sample artifacts are non-blocking unless explicitly claimed as current evidence.
4. New User Solve contract artifacts must not claim runtime validation or actual solving.
```

## 3. Do Not Do

Do not solve samples.

Do not upload or execute binaries.

Do not generate real candidate flags from samples.

Do not implement Fast Static Solve.

Do not implement Evidence Trace / Replay schema beyond simple internal evidence reference placeholders needed by the contract.

Do not implement Web Workbench or frontend.

Do not implement tool provider integration.

Do not invoke:

```text
IDA
Ghidra
OllyDbg
x64dbg
radare2
MCP
emulator
debugger
runtime probe
```

Do not create or modify:

```text
project_state/current_state.json
project_state/task_packet.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/context/*
project_state/roadmap/workstreams.json
project_state/domains/*
```

Do not modify:

```text
.codex-skills/*
.github/workflows/*
frontend/*
solve_reports/*
training_materials/local_reverse/*
project_state/archives/*
project_state/deletions/*
project_state/blob_store/*
project_state/*.db
project_state/index.sqlite
docs/roadmap/*
```

Do not add a database, queue, runner dispatcher, PR automation, cleanup-apply flow, archive compaction, or deletion flow.

Do not claim:

```text
candidate_found == verified
static_verified == runtime_validated
user-layer result == engineering-layer ACCEPTED
roadmap entry == execution authority
```

## 4. Files To Inspect

Required authority and state files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_state_domain_taxonomy_final_status_rework_v1/round_manifest.json
```

Required roadmap/context inspection:

```text
docs/roadmap/evidence_centered_user_solve_execution_plan.md
```

Search before implementation:

```text
reverse_agent/*user_solve*.py
reverse_agent/*solve*contract*.py
reverse_agent/*solve*state*.py
tests/test_user_solve*.py
docs/*user_solve*.md
```

Allowed source inspection candidates:

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
reverse_agent/user_solve_views.py
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
```

Allowed test inspection candidates:

```text
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
tests/test_user_solve_errors.py
tests/test_user_solve_views.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this round must answer all of the following:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline engineering_branch?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous accepted baseline identified as decision_20260708_state_domain_taxonomy_final_status_rework_v1?
7. Was the User Solve Contract roadmap basis inspected?
8. Were existing user_solve / solve_contract / solve_state modules searched before adding new code?
9. Did the round avoid duplicating existing User Solve functionality if found?
10. Is UserSolveTask defined with schema_version and stable identity fields?
11. Is UserSolveResult defined with status, validation_status, candidates, message, confidence, and evidence refs?
12. Is CandidateResult defined without implying runtime validation?
13. Is ValidationStatus defined so candidate_found, static_verified, and runtime_validated are distinct?
14. Are failed and blocked reason codes explicit and serializable?
15. Does the state transition validator reject illegal transitions?
16. Does the state transition validator require evidence refs for verified/runtime_validated states?
17. Does candidate_found allow validation_status=pending?
18. Does runtime_validated require runtime validation evidence and not just static evidence?
19. Does blocked carry a reason such as policy/tool/environment/sample_format/unsupported?
20. Does the user-facing payload avoid exposing raw decision_packet, command-plan, negative_results, or internal gate file bodies?
21. Are JSON serialization/deserialization tests deterministic?
22. Are backward/forward compatibility rules documented for unknown optional fields?
23. Did pytest run and pass with explicit command recorded in pytest_result.txt?
24. Did command-plan include explicit pytest, report-summary, execution-log, final-check, run-closeout, and close-round?
25. Were any omitted or unauthorized commands executed?
26. Were project_state/current_state.json and task_packet.json left untouched?
27. Were artifact_index, negative_results, state_manifest, context, roadmap, domains, frontend, workflows, solve_reports, and training materials left untouched?
28. Did final-check pass or accurately reflect any limitations?
29. Did run-closeout and close-round pass and generate a round_manifest for this round?
30. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, and generated_artifacts?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Add or extend User Solve contract data structures.
2. Add or extend User Solve state enum and validation status enum.
3. Add transition validation for user solve states.
4. Add explicit error/reason codes for failed and blocked cases.
5. Add JSON serialization/deserialization helpers.
6. Add tests for valid payloads, invalid payloads, legal transitions, illegal transitions, evidence requirements, and blocked/failed reasons.
7. Add a short docs/user_solve_contract.md explaining user-layer contract boundaries.
8. Update gate/report code only if necessary to recognize generated artifacts or keep existing closeout/report consistency intact.
```

Required user-facing statuses:

```text
uploaded
fast_analyzing
candidate_found
static_verified
runtime_validation_pending
runtime_validated
failed
blocked
```

Required validation statuses:

```text
pending
candidate_only
static_verified
runtime_validated
failed
blocked
unsupported
```

Required safety semantics:

```text
candidate_found != verified
static_verified != runtime_validated
runtime_validated requires runtime validation evidence
failed requires a reason
blocked requires a reason
user-layer result does not equal engineering-layer ACCEPTED
```

Allowed source files:

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
reverse_agent/user_solve_views.py
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
```

Allowed test files:

```text
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
tests/test_user_solve_errors.py
tests/test_user_solve_views.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Allowed docs:

```text
docs/user_solve_contract.md
```

If implementation requires solver code, sample harnesses, Web runtime, tool providers, database, runner dispatch, or roadmap mutation, stop and report BLOCKED.

## 7. Tests

The exact command list must come from generated command-plan. It must include explicit pytest.

Minimum pytest command:

```text
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
```

If `user_solve_views.py` is implemented, include:

```text
tests/test_user_solve_views.py
```

If command-plan chooses a broader command, that is allowed if it includes the new User Solve tests.

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260708_user_solve_contract_foundation_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260708_user_solve_contract_foundation_v1
```

Required output files:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_user_solve_contract_foundation_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. implementing the contract requires sample execution, solver implementation, Web runtime, external tool invocation, database, runner dispatch, cleanup, or roadmap mutation.
6. an existing User Solve contract implementation is found but cannot be safely extended within allowed scope.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest or required closeout gates.
3. UserSolveResult conflates candidate_found with verified.
4. static_verified is treated as runtime_validated.
5. runtime_validated can be produced without runtime evidence.
6. failed or blocked can be produced without explicit reason.
7. illegal state transitions are accepted.
8. user-facing payload exposes raw governance files or internal gate bodies.
9. final-check fails or reports unsupported acceptance status.
10. run-closeout or close-round fails.
11. round_manifest is missing.
12. execution_report.md and codex_execution_report.md disagree.
13. any forbidden path is modified.
14. current_state.json or task_packet.json is modified.
15. roadmap, context, state_manifest, artifact_index, negative_results, domains, docs/roadmap, frontend, workflows, solve_reports, databases, archives, or training materials are modified.
16. sample solving, runtime probing, debugger/tool/MCP invocation, Web work, runner dispatch, cleanup apply, deletion, commit/push/PR/merge/rebase is performed.
```

Acceptance target:

```text
ACCEPTED if the User Solve contract and state machine are implemented, tested, documented, and all required gates agree for this decision_id and round_id.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly non-blocking and do not affect contract semantics.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
