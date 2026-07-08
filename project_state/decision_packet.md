```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260708_state_domain_taxonomy_closeout_evidence_rework_v1",
  "round_id": "round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "project_governance",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "follows_last_decision_id": "decision_20260708_state_domain_taxonomy_foundation_v1",
  "follows_last_round_id": "round_20260708_state_domain_taxonomy_foundation_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "required_profile": "standard_or_full",
  "closeout_required": true,
  "close_round_required": true,
  "closeout_allowed": true,
  "pytest_required": true,
  "explicit_pytest_command_required": true,
  "command_plan_must_not_omit_pytest": true,
  "command_plan_must_include_explicit_pytest_command": true,
  "command_plan_must_not_omit_report_summary": true,
  "command_plan_must_not_omit_execution_log": true,
  "command_plan_must_not_omit_final_check": true,
  "command_plan_must_not_omit_run_closeout": true,
  "command_plan_must_not_omit_close_round": true,
  "final_check_must_pass_before_acceptance": true,
  "final_gate_status_summary_must_support_acceptance": true,
  "run_closeout_must_pass_before_acceptance": true,
  "round_archive_required_before_acceptance": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_reports.py",
    "reverse_agent/project_control_plane.py",
    "reverse_agent/project_state_manifest.py",
    "reverse_agent/project_context.py"
  ],
  "allowed_test_files": [
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_control_plane.py",
    "tests/test_project_state_manifest.py",
    "tests/test_project_context.py"
  ],
  "allowed_project_state_files": [
    "project_state/gates/*.json",
    "project_state/pytest_result.txt",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/round_manifest.json",
    "project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/decision_packet.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/codex_execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/execution_report.md",
    "project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/pytest_result.txt"
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

Repair the acceptance-evidence mismatch from the previous `state_domain_taxonomy_foundation` round.

Previous round:

```text
Decision: decision_20260708_state_domain_taxonomy_foundation_v1
Round: round_20260708_state_domain_taxonomy_foundation_v1
Audit outcome: REWORK_REQUIRED
```

The previous round made useful project-governance progress, but it cannot be accepted because its evidence chain is internally inconsistent:

```text
1. execution_report.md and codex_execution_report.md claim SUCCESS / ACCEPTED;
2. final_gate_result.json reports gate_status WARN;
3. final_gate_result.json status_summary reports PARTIAL / NEEDS_REVIEW;
4. pytest_result.txt summary does not explicitly record the real pytest command;
5. command_plan required pytest but did not list an explicit pytest command in commands[];
6. run-closeout wrapped diagnostic final-check behavior into an apparent pass even while close-round reported PARTIAL;
7. report prose and structured evidence disagree about whether the round is actually acceptable.
```

This rework round must make acceptance status mechanically consistent across:

```text
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/<this_round>/round_manifest.json
```

The target is not to expand the domain taxonomy feature. The target is to fix the governance closeout/evidence path so that a future acceptance claim is supported by current evidence.

## 2. Current Evidence

Current task authority is this file:

```text
project_state/decision_packet.md
```

`task_packet.json` is background only and must not control this round.

Current mainline:

```text
project_governance
```

Skill profile required:

```text
reverse-agent-iteration@v2
```

Current accepted baseline before the failed round:

```text
Previous accepted/limited baseline: round_20260708_profile_contract_closeout_consistency_rework_v1
Audit result: ACCEPTED_WITH_LIMITATIONS
```

Immediate failed round to repair:

```text
Failed decision: decision_20260708_state_domain_taxonomy_foundation_v1
Failed round: round_20260708_state_domain_taxonomy_foundation_v1
Audit result: REWORK_REQUIRED
```

Evidence from the failed round:

```text
1. decision_meta was valid and APPROVED.
2. mainline was project_governance.
3. useful files were changed: reverse_agent/project_context.py, reverse_agent/project_gate.py, tests/test_project_context.py, and domain README skeletons.
4. forbidden current_state/task_packet/domain runtime payload changes were not observed.
5. run-closeout and close-round generated artifacts.
6. report_summary_synthesis eventually reported PASSED.
```

Blocking mismatch from the failed round:

```text
1. codex_execution_report.md summary claimed SUCCESS / ACCEPTED.
2. execution_report.md summary claimed SUCCESS / ACCEPTED.
3. final_gate_result.json had gate_status WARN.
4. final_gate_result.json status_summary had report_status PARTIAL and report_acceptance_recommendation NEEDS_REVIEW.
5. pytest_result.txt summary omitted the explicit pytest command.
6. command_plan required pytest but commands[] did not include an explicit pytest command.
7. run_closeout_result.json included an internal pytest command, but not as direct pytest_result summary coverage.
8. pytest coverage did not clearly include all files changed in the round, especially project_context-related tests.
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
execution_report / codex_execution_report parity
pytest_result status parsing
round delta summary
artifact freshness policy
status policy checks
```

Do not create parallel systems. Repair the existing gate/report/closeout path.

Artifact freshness policy:

```text
1. All current-round gate artifacts must match this decision_id and round_id after regeneration.
2. Stale artifacts from decision_20260708_state_domain_taxonomy_foundation_v1 are failure evidence only, not acceptance evidence for this round.
3. Historical sample artifacts remain non-blocking for this project_governance rework unless the report claims them as current evidence.
4. final_gate_result.json status_summary must not contradict execution reports.
```

Negative results:

```text
Do not repeat prohibited solve_reports behavior. Do not solve samples. Do not expand budgets or run tools. This is a closeout/evidence rework only.
```

Context packet / workstream registry:

```text
Do not modify context packet or workstreams in this round. Stale context packet facts may be reported as non-blocking only if they are not used as current acceptance evidence.
```

This round must not repeat the implementation work of Project State Domain Taxonomy Foundation unless a small adjustment is directly necessary to make the evidence chain truthful and auditable.

## 3. Do Not Do

Do not implement new domain taxonomy features.

Do not add new domains.

Do not modify domain README skeletons unless a gate absolutely requires a mechanical path correction, and if so stop and report the need rather than silently modifying them.

Do not implement User Solve Layer.

Do not implement Evidence Replay.

Do not implement Fast Static Solve.

Do not implement Web Workbench.

Do not implement Tool Provider contracts.

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

Do not perform:

```text
sample solving
candidate or flag generation
runtime probing
sample execution
dynamic debugging
IDA invocation
Ghidra invocation
OllyDbg invocation
x64dbg invocation
radare2 invocation
MCP invocation
Web runtime work
database migration
runner dispatch
workflow dispatch
cleanup apply
deletion
moving historical artifacts
archive compaction
local commit
local push
branch creation
PR creation
merge
rebase
```

Do not claim `SUCCESS`, `ACCEPTED`, or `ACCEPTED_WITH_LIMITATIONS` unless all of the following are true for this rework round:

```text
1. command_plan commands[] includes an explicit pytest command.
2. pytest_result.txt summary includes the explicit pytest command.
3. pytest_result.txt records direct pytest output, exit code 0, and test count.
4. pytest covers the source/test files changed by the failed round or this rework round.
5. report-summary passes or any diagnostic exit 1 is reflected truthfully in final status.
6. final_gate_result.json supports the report status and acceptance recommendation.
7. final_gate_result.json status_summary does not say PARTIAL / NEEDS_REVIEW while reports say SUCCESS / ACCEPTED.
8. run_closeout_result.json has no active nested contradiction.
9. close-round generates a round_manifest for this rework round.
10. codex_execution_report.md and execution_report.md agree.
```

## 4. Files To Inspect

Required authority and registry files:

```text
project_state/decision_packet.md
.codex-skills/registry.json
project_state/task_packet.json
project_state/current_state.json
project_state/artifact_index.json
project_state/negative_results.json
project_state/state_manifest.json
```

Required failed-round evidence:

```text
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/pytest_result.txt
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_state_domain_taxonomy_foundation_v1/round_manifest.json
```

Required source/test inspection candidates:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
reverse_agent/project_context.py
reverse_agent/project_state_manifest.py
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
tests/test_project_context.py
tests/test_project_state_manifest.py
```

Required generated current-round files after execution:

```text
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/round_manifest.json
```

Do not read full `solve_reports/` or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report for this rework round must answer all of the following:

```text
1. Is decision_meta valid JSON and schema_version=1?
2. Is status APPROVED?
3. Is mainline project_governance?
4. Is reverse-agent-iteration@v2 active?
5. Is task_packet treated as advisory/background only?
6. Was the previous failed round correctly identified as decision_20260708_state_domain_taxonomy_foundation_v1?
7. Does command-plan select standard/full profile?
8. Does command-plan required_command_kinds include pytest, report-summary, execution-log, final-check, run-closeout, and close-round?
9. Does command-plan commands[] include an explicit pytest command?
10. Does pytest_result.txt summary include the explicit pytest command?
11. Does pytest_result.txt record direct pytest output, exit code, and test count?
12. Does pytest cover tests relevant to files changed in the failed round and this rework round?
13. Were any omitted commands executed?
14. Were any commands executed outside command-plan authority?
15. Does report-summary synthesis match execution_report and codex_execution_report?
16. Does execution-log cover all executed commands?
17. Does final_gate_result.json have a gate status that supports the report status?
18. Does final_gate_result.json status_summary support SUCCESS / ACCEPTED if the report claims it?
19. If final_gate_result.json is WARN or status_summary is PARTIAL / NEEDS_REVIEW, do reports honestly avoid SUCCESS / ACCEPTED?
20. Does run_closeout_result.json avoid wrapping active WARN/PARTIAL/NEEDS_REVIEW evidence into ACCEPTED?
21. Does close-round generate the rework round manifest?
22. Do codex_execution_report.md and execution_report.md agree on report_id, decision_id, round_id, status, acceptance_recommendation, files_changed, tests_ran, and generated_artifacts?
23. Were project_state/current_state.json and project_state/task_packet.json left untouched?
24. Were project_state/artifact_index.json, negative_results.json, state_manifest.json, context/*, roadmap/workstreams.json, and domains/* left untouched?
25. Were User Solve, Evidence Replay, Web, tools, runner, database, cleanup, and sample solving avoided?
26. Were all generated artifacts current for this decision_id and round_id?
27. Are stale failed-round artifacts treated only as failure evidence, not current acceptance evidence?
28. Are warnings either resolved or explicitly reflected in the final acceptance recommendation?
29. Does round_manifest report status agree with live execution reports?
30. Is the final recommendation one of ACCEPTED, ACCEPTED_WITH_LIMITATIONS, REWORK_REQUIRED, or BLOCKED, and is it supported by evidence?
```

## 6. Implementation Scope

This is a narrow rework round. It may modify only the gate/report/closeout code necessary to make acceptance status truthful and mechanically consistent.

Allowed implementation tasks:

```text
1. Ensure command-plan emits an explicit pytest command when pytest is required.
2. Ensure pytest_result.txt summary records the explicit pytest command, direct pytest output, exit code 0, and test count.
3. Ensure selected pytest covers changed source/test files relevant to project_gate, project_reports, project_control_plane, project_context, and project_state_manifest when those files are changed or were part of the failed round evidence.
4. Ensure report-summary synthesis and execution reports cannot disagree silently.
5. Ensure final_gate_result.json status_summary cannot report PARTIAL / NEEDS_REVIEW while execution reports claim SUCCESS / ACCEPTED.
6. Ensure run-closeout does not treat active final-check WARN/PARTIAL/NEEDS_REVIEW as accepted evidence unless reports also honestly use a limited or review-needed recommendation.
7. Ensure close-round archives the rework round with report status matching the live reports.
8. Update tests for command-plan pytest coverage, pytest_result coverage, final_gate status_summary/report parity, and run-closeout acceptance semantics.
9. Update codex_execution_report.md, execution_report.md, pytest_result.txt, gate artifacts, and round manifest for this rework round.
```

Allowed source files:

```text
reverse_agent/project_gate.py
reverse_agent/project_reports.py
reverse_agent/project_control_plane.py
reverse_agent/project_context.py
reverse_agent/project_state_manifest.py
```

Allowed test files:

```text
tests/test_project_gate.py
tests/test_project_reports.py
tests/test_project_control_plane.py
tests/test_project_context.py
tests/test_project_state_manifest.py
```

Do not make feature changes outside the evidence/closeout path. If a fix requires broad refactoring, stop and report `BLOCKED` with the exact reason.

## 7. Tests

The exact command list must come from generated command-plan. The command-plan must include an explicit pytest command.

Minimum pytest command expected:

```text
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q
```

If command-plan selects a different pytest command, the report must explain why it provides equal or stronger coverage.

Required gate sequence:

```text
python -m reverse_agent.project_gate preflight --state-dir project_state
python -m reverse_agent.project_gate gate-profile --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_control_plane.py tests/test_project_context.py tests/test_project_state_manifest.py -q
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1
```

Required outputs:

```text
project_state/pytest_result.txt
project_state/codex_execution_report.md
project_state/execution_report.md
project_state/gates/command_plan.json
project_state/gates/report_summary_synthesis.json
project_state/gates/execution_log.json
project_state/gates/final_gate_result.json
project_state/gates/run_closeout_result.json
project_state/rounds/round_20260708_state_domain_taxonomy_closeout_evidence_rework_v1/round_manifest.json
```

`pytest_result.txt` must include both:

```text
1. the explicit pytest command in pytest_result_summary.tests_ran;
2. the command transcript showing direct pytest output and exit code.
```

## 8. Stop Conditions

Stop with `BLOCKED` if:

```text
1. project_state/decision_packet.md cannot be read.
2. .codex-skills/registry.json cannot be read.
3. reverse-agent-iteration@v2 is not active.
4. command-plan cannot be generated.
5. command-plan cannot include an explicit pytest command without broad refactor.
6. fixing the mismatch requires modifying forbidden paths.
7. fixing the mismatch requires User Solve, Web, tools, runner, database, cleanup, or sample execution.
```

Stop with `REWORK_REQUIRED` if:

```text
1. pytest fails or is not recorded.
2. pytest_result.txt summary omits the explicit pytest command.
3. pytest_result.txt lacks direct pytest output or exit code.
4. command-plan required_command_kinds and commands[] remain inconsistent.
5. report-summary and execution reports disagree.
6. final_gate_result.json remains WARN while reports claim SUCCESS / ACCEPTED.
7. final_gate_result.json status_summary remains PARTIAL / NEEDS_REVIEW while reports claim SUCCESS / ACCEPTED.
8. run_closeout_result.json has active nested WARN/FAIL/PARTIAL/NEEDS_REVIEW evidence not reflected in reports.
9. close-round fails or round_manifest is missing.
10. round_manifest status disagrees with live reports.
11. codex_execution_report.md and execution_report.md disagree.
12. any forbidden path is modified.
13. current_state.json or task_packet.json is modified.
14. roadmap, context, state_manifest, artifact_index, negative_results, domains, docs, frontend, workflows, solve_reports, databases, or archives are modified.
15. sample solving, runtime probing, debugger/tool/MCP invocation, Web work, runner dispatch, cleanup apply, deletion, commit/push/PR/merge/rebase is performed.
```

Acceptance target:

```text
ACCEPTED only if command-plan, pytest_result, report-summary, execution-log, final-check, run-closeout, close-round, live reports, and round_manifest all agree for this decision_id and round_id.
ACCEPTED_WITH_LIMITATIONS only if remaining warnings are explicitly non-blocking and the reports use a limitations-aware recommendation that matches final_gate_result.json status_summary.
Otherwise report REWORK_REQUIRED or BLOCKED.
```
