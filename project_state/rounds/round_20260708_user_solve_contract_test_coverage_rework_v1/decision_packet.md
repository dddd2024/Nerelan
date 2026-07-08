```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_user_solve_contract_test_coverage_rework_v1",
  "round_id": "round_20260708_user_solve_contract_test_coverage_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_user_solve_contract_foundation_v1",
  "follows_last_round_id": "round_20260708_user_solve_contract_foundation_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "pytest_must_include_user_solve_tests": true,
  "command_plan_must_include_explicit_pytest_command": true,
  "command_plan_pytest_must_include_user_solve_tests": true,
  "pytest_result_must_include_user_solve_tests": true,
  "report_tests_must_include_user_solve_tests": true,
  "final_check_must_verify_changed_tests_are_covered": true,
  "command_plan_must_not_omit_report_summary": true,
  "command_plan_must_not_omit_execution_log": true,
  "command_plan_must_not_omit_final_check": true,
  "command_plan_must_not_omit_run_closeout": true,
  "command_plan_must_not_omit_close_round": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/user_solve_contract.py",
    "reverse_agent/user_solve_state.py",
    "reverse_agent/user_solve_errors.py",
    "reverse_agent/user_solve_views.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py",
    "tests/test_user_solve_contract.py",
    "tests/test_user_solve_state.py",
    "tests/test_user_solve_errors.py",
    "tests/test_user_solve_views.py"
  ],
  "allowed_docs": [
    "docs/user_solve_contract.md"
  ],
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/execution_report.md",
    "project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/pytest_result.txt"
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

Repair the test coverage gap from the previous User Solve Contract foundation round.

Previous round:

```text
decision_id: decision_20260708_user_solve_contract_foundation_v1
round_id: round_20260708_user_solve_contract_foundation_v1
audit_outcome: REWORK_REQUIRED
```

The previous round added useful User Solve contract files and tests, but it cannot be accepted because the executed pytest command did not include any `tests/test_user_solve_*` files.

This rework must make the evidence chain prove that the new User Solve contract tests actually ran.

The minimum repaired evidence must show:

```text
1. command_plan.json contains an explicit pytest command that includes tests/test_user_solve_contract.py;
2. command_plan.json contains tests/test_user_solve_state.py;
3. command_plan.json contains tests/test_user_solve_errors.py;
4. command_plan.json contains tests/test_user_solve_views.py when user_solve_views.py exists or is claimed changed;
5. pytest_result.txt summary includes the same explicit pytest command;
6. pytest_result.txt command transcript shows the same pytest command and exit code 0;
7. codex_execution_report.md and execution_report.md tests_ran include the User Solve pytest command;
8. final-check detects changed tests not covered by pytest and blocks future ACCEPTED reports;
9. run-closeout and close-round archive a round_manifest for this rework round.
```

This is a test coverage and gate coverage rework only. Do not expand the User Solve contract feature unless the User Solve tests reveal a direct contract bug that can be fixed inside the already allowed contract files.

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

Reason:

```text
This round repairs command-plan / pytest / final-check coverage for an engineering contract module. It is not a reverse_solving round, and it must not perform sample solving or tool invocation.
```

Skill profile:

```text
reverse-agent-iteration@v2
```

Previous accepted baseline before the failed User Solve round:

```text
decision_20260708_state_domain_taxonomy_final_status_rework_v1
round_20260708_state_domain_taxonomy_final_status_rework_v1
ACCEPTED_WITH_LIMITATIONS
```

Failed round to repair:

```text
decision_20260708_user_solve_contract_foundation_v1
round_20260708_user_solve_contract_foundation_v1
REWORK_REQUIRED
```

Evidence from the failed round:

```text
1. codex_execution_report.md claimed SUCCESS / ACCEPTED;
2. final_gate_result.json claimed PASSED;
3. run_closeout_result.json claimed PASSED;
4. round_manifest.json claimed SUCCESS / ACCEPTED;
5. files_changed included reverse_agent/user_solve_contract.py, user_solve_state.py, user_solve_errors.py, user_solve_views.py;
6. files_changed included tests/test_user_solve_contract.py, tests/test_user_solve_state.py, tests/test_user_solve_errors.py, tests/test_user_solve_views.py;
7. pytest_result.txt only ran project_gate/project_reports/project_control_plane/project_context/project_state_manifest tests;
8. no tests/test_user_solve_* appeared in the executed pytest command;
9. final-check validated report/pytest consistency but did not catch that newly changed tests were excluded from pytest coverage.
```

Already acceptable from the failed round:

```text
1. decision_meta was valid;
2. mainline was engineering_branch;
3. User Solve source/test files were within allowed paths;
4. no sample solving, Web, tool provider, database, or runner dispatch was observed;
5. report/final-check/run-closeout/round_manifest status consistency path itself worked.
```

Current insufficient evidence:

```text
The User Solve implementation cannot be accepted until User Solve tests are executed and the gate layer prevents this class of coverage omission.
```

Existing capabilities to reuse:

```text
command-plan authority
pytest_result parser
execution-log
report-summary
final-check
run-closeout
close-round
round_delta_summary
files_changed coverage checks
report/pytest semantic parity checks
```

Do not create parallel gates. Extend the existing command-plan/final-check/report validation path.

Artifact freshness policy:

```text
1. All current-round gate artifacts must match this decision_id and round_id.
2. Failed-round artifacts are failure evidence only.
3. Historical user_solve_* gate artifacts are not current acceptance evidence.
4. Historical sample artifacts remain non-blocking unless claimed as current evidence.
```

## 3. Do Not Do

Do not expand the User Solve contract beyond fixing test coverage and direct test failures.

Do not implement solving.

Do not generate candidate flags.

Do not run samples.

Do not upload or execute binaries.

Do not implement Fast Static Solve.

Do not implement Evidence Trace or Evidence Replay.

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

Do not claim ACCEPTED unless User Solve tests are visibly present in:

```text
command_plan.json
pytest_result.txt summary
pytest_result.txt command transcript
codex_execution_report.md tests_ran
execution_report.md tests_ran
final_gate_result.json checks
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
project_state/rounds/round_20260708_user_solve_contract_foundation_v1/round_manifest.json
```

Required failed-round files to inspect:

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
reverse_agent/user_solve_views.py
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
tests/test_user_solve_errors.py
tests/test_user_solve_views.py
docs/user_solve_contract.md
```

Allowed gate/report files to inspect or modify:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
```

Allowed User Solve files to modify only if the newly run tests reveal direct contract bugs:

```text
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
reverse_agent/user_solve_views.py
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
tests/test_user_solve_errors.py
tests/test_user_solve_views.py
docs/user_solve_contract.md
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
6. Was the previous failed round correctly identified as decision_20260708_user_solve_contract_foundation_v1?
7. Did the rework avoid expanding User Solve functionality beyond coverage repair and direct test failures?
8. Does command_plan.json include an explicit pytest command?
9. Does command_plan.json pytest command include tests/test_user_solve_contract.py?
10. Does command_plan.json pytest command include tests/test_user_solve_state.py?
11. Does command_plan.json pytest command include tests/test_user_solve_errors.py?
12. Does command_plan.json pytest command include tests/test_user_solve_views.py when user_solve_views.py exists or is changed?
13. Does pytest_result.txt summary include the same User Solve pytest command?
14. Does pytest_result.txt transcript show the same User Solve pytest command with exit code 0?
15. Does codex_execution_report.md tests_ran include the User Solve pytest command?
16. Does execution_report.md tests_ran include the User Solve pytest command?
17. Does final-check explicitly validate that changed tests are covered by pytest_result?
18. Does final-check block if tests/test_user_solve_* are changed but omitted from pytest?
19. Do UserSolveResult tests still verify candidate_found != verified?
20. Do User Solve tests still verify static_verified != runtime_validated?
21. Do User Solve tests still verify runtime_validated requires runtime evidence?
22. Do User Solve tests still verify failed/blocked require explicit reason?
23. Were any omitted or unauthorized commands executed?
24. Were project_state/current_state.json and task_packet.json left untouched?
25. Were artifact_index, negative_results, state_manifest, context, roadmap, domains, frontend, workflows, solve_reports, and training materials left untouched?
26. Did final-check pass or accurately reflect any limitations?
27. Did run-closeout pass?
28. Did close-round generate round_manifest for round_20260708_user_solve_contract_test_coverage_rework_v1?
29. Do execution_report.md and codex_execution_report.md agree on decision_id, round_id, status, acceptance_recommendation, tests_ran, and generated_artifacts?
30. Does round_manifest status agree with live reports and final_gate status_summary?
```

## 6. Implementation Scope

Allowed implementation tasks:

```text
1. Fix command-plan pytest selection so changed User Solve source/test files cause tests/test_user_solve_* to be included.
2. Fix final-check so changed test files must be covered by pytest_result, not only by report tests_ran.
3. Fix report-summary or report validation if it allows reports to omit changed test files from tests_ran.
4. Add tests for command-plan selecting User Solve tests when User Solve files change.
5. Add tests for final-check rejecting changed tests omitted from pytest_result.
6. Run the User Solve test suite and fix direct contract bugs if those tests fail.
7. Regenerate pytest_result, command_plan, report-summary, execution-log, final-check, run-closeout, close-round, execution reports, and round manifest for this rework round.
```

Expected minimum pytest command:

```text
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_user_solve_views.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
```

Allowed broader pytest command:

```text
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_user_solve_views.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q
```

Allowed source files:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
reverse_agent/user_solve_contract.py
reverse_agent/user_solve_state.py
reverse_agent/user_solve_errors.py
reverse_agent/user_solve_views.py
```

Allowed test files:

```text
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
tests/test_user_solve_contract.py
tests/test_user_solve_state.py
tests/test_user_solve_errors.py
tests/test_user_solve_views.py
```

Allowed docs:

```text
docs/user_solve_contract.md
```

If implementation requires solver code, sample harnesses, Web runtime, tool providers, database, runner dispatch, cleanup, or roadmap mutation, stop and report BLOCKED.

## 7. Tests

The exact command list must come from generated command-plan. It must include explicit pytest and User Solve tests.

Minimum pytest command:

```text
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_user_solve_views.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
```

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_user_solve_contract.py tests/test_user_solve_state.py tests/test_user_solve_errors.py tests/test_user_solve_views.py tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260708_user_solve_contract_test_coverage_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260708_user_solve_contract_test_coverage_rework_v1
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
project_state/rounds/round_20260708_user_solve_contract_test_coverage_rework_v1/round_manifest.json
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. fixing coverage requires forbidden path changes.
6. fixing coverage requires sample execution, solver implementation, Web runtime, external tool invocation, database, runner dispatch, cleanup, or roadmap mutation.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. command-plan omits explicit pytest.
3. command-plan pytest omits tests/test_user_solve_contract.py.
4. command-plan pytest omits tests/test_user_solve_state.py.
5. command-plan pytest omits tests/test_user_solve_errors.py.
6. command-plan pytest omits tests/test_user_solve_views.py while user_solve_views.py exists or is changed.
7. pytest_result.txt summary omits the User Solve pytest command.
8. pytest_result.txt transcript omits the User Solve pytest command.
9. codex_execution_report.md or execution_report.md tests_ran omits the User Solve pytest command.
10. final-check does not catch changed tests omitted from pytest_result.
11. User Solve tests reveal candidate_found == verified, static_verified == runtime_validated, missing runtime evidence, or missing failed/blocked reasons.
12. final-check fails or reports unsupported acceptance status.
13. run-closeout or close-round fails.
14. round_manifest is missing.
15. execution_report.md and codex_execution_report.md disagree.
16. any forbidden path is modified.
17. current_state.json or task_packet.json is modified.
18. roadmap, context, state_manifest, artifact_index, negative_results, domains, docs/roadmap, frontend, workflows, solve_reports, databases, archives, or training materials are modified.
19. sample solving, runtime probing, debugger/tool/MCP invocation, Web work, runner dispatch, cleanup apply, deletion, commit/push/PR/merge/rebase is performed.
```

Acceptance target:

```text
ACCEPTED if User Solve tests are explicitly covered by command-plan, pytest_result, reports, final-check, run-closeout, and round_manifest for this decision_id and round_id.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly non-blocking and do not affect User Solve contract or coverage semantics.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
