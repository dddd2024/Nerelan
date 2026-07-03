```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260703_required_audit_direct_evidence_rework_v1",
  "round_id": "round_20260703_required_audit_direct_evidence_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "reworks_decision_id": "decision_20260702_ci_evidence_bridge_closeout_consistency_rework_v1",
  "reworks_round_id": "round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_32_required_audit_direct_evidence_rework",
  "primary_goal": "Fix Required Audit report prose so each audit item cites direct artifact evidence and does not use ci_audit_handoff_bundle.json as a generic substitute for unrelated claims.",
  "command_plan_authority_required": true,
  "accepted_requires_required_audit_direct_evidence": true,
  "accepted_requires_generic_answer_guard": true,
  "accepted_requires_final_check_or_audit_readiness_hardening": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_ci.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_ci.py"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260703_required_audit_direct_evidence_rework_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/*",
    "solve_reports/*",
    ".github/workflows/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **Required Audit Direct Evidence Rework v1**.

This is an `engineering_branch` rework round. The previous round fixed the CI evidence bridge closeout consistency problem at the artifact/gate level: `ci_observation_reconcile_result.json` reached final consistency, `ci_audit_handoff_bundle.json` reached audit readiness, and `final-check` passed after closeout. However, audit found that the human-readable Required Audit answers in `execution_report.md` / `codex_execution_report.md` still use generic prose and over-broad evidence references.

Primary objectives:

1. Fix Required Audit answer generation so each Required Audit item cites direct artifact evidence that corresponds to the specific assertion being made.
2. Prevent `ci_audit_handoff_bundle.json` from being used as a generic substitute for unrelated Required Audit answers.
3. Add or harden final-check / audit-readiness checks so generic, template-like, or mismatched Required Audit answers cannot pass for an accepted report.
4. Preserve the closeout consistency behavior from the previous round; do not rework CI bridge semantics unless a minimal report-evidence mapping fix requires it.
5. Keep this round limited to report/audit evidence quality. Do not introduce remote CI dispatch, polling, repository mutation, product UI/API, database/queue/scheduler, AgentRunner execution, reverse-solving, sample execution, or User Solve Layer work.

Accepted target:

- `codex_execution_report.md` and `execution_report.md` status is `SUCCESS` and recommendation is `ACCEPTED` only if Required Audit answers are direct, specific, and artifact-aligned.
- `pytest_result.txt` status is `PASSED`.
- Required Audit item 30 is no longer self-contradictory: it must not cite only `ci_audit_handoff_bundle.json` while claiming that generic bundle substitution was avoided.
- Required Audit items for `ci_run_evidence`, `local_ci_parity`, workflow coverage/readiness, local execution bundle, codex prompt packet, audit precheck, audit readiness, final-check, run-closeout, and close-round cite their own direct artifacts or the specific direct artifacts needed for the claim.
- `final_gate_result.json` or `audit_readiness_packet.json` detects generic/placeholder Required Audit answers and blocks accepted status when necessary.
- `run_closeout_result.json`, if run by command-plan, passes and archives the corrected report artifacts.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only and still describes older sample/reverse-solving context; it must not control this engineering round.

Reworked round:

- `decision_20260702_ci_evidence_bridge_closeout_consistency_rework_v1`
- `round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1`
- audit outcome: `REWORK_REQUIRED`

Evidence from the previous round:

1. `decision_packet.md` was valid and approved, with `mainline=engineering_branch` and `skill_profiles=["reverse-agent-iteration@v2"]`.
2. `.codex-skills/registry.json` defines `reverse-agent-iteration` as active version 2.
3. `pytest_result.txt` reported `PASSED` with the gate and pytest commands recorded.
4. `ci_observation_reconcile_result.json` was current, `reconcile_status=RECONCILED`, `final_consistency_status=FINAL_CONSISTENT`, and `pending_diagnostic_sources=[]`.
5. `ci_audit_handoff_bundle.json` was current, `handoff_status=READY_FOR_AUDIT`, and post-closeout status showed `final_check_gate_status=PASSED`, `run_closeout_status=PASSED`, and `close_round_status=CLOSED`.
6. `final_gate_result.json` was `PASSED` and included `ci_bridge_closeout_consistency` with final consistent status.
7. The blocking issue was in Required Audit prose: several answers used generic artifact summaries, and item 30 still cited `ci_audit_handoff_bundle.json` as broad evidence while claiming direct evidence use.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260703_required_audit_direct_evidence_rework_v1` and `round_20260703_required_audit_direct_evidence_rework_v1` when regenerated.
- Historical artifacts from the previous closeout consistency round may be referenced only as rework evidence; they must not be treated as current accepted evidence after this round generates new artifacts.
- `project_state/artifact_index.json` currently contains sample/reverse-solving artifact freshness data and many missing sample artifacts. That is non-blocking for this engineering round unless the implementation incorrectly relies on those sample artifacts.
- Reverse-solving sample artifacts remain out of scope.

Negative results:

- `negative_results.json` blocks old sample_solver blind search, budget-only search expansion, compare_semantics_agree=false frontier use, full solve_reports commits, and repeated sample diagnostics without new runtime evidence.
- This round must not touch those reverse-solving directions.

Existing capabilities to preserve:

- decision metadata validation
- command-plan authority checks
- pytest/report/final-check consistency checks
- CI evidence bridge artifacts
- closeout consistency checks
- audit readiness packet generation
- report summary synthesis
- execution report alias parity

Command-plan policy:

- `project_state/gates/command_plan.json` is the only local command authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- The Tests section does not override command-plan.
- Current profiles are `fast`, `standard`, and `full`; do not use `medium`.

Heavy artifact policy:

- Do not scan full `solve_reports/`.
- Do not scan full `PROJECT_PROGRESS_LOG.txt`.
- Do not run reverse-solving tools, dynamic debugging, IDA, Ghidra, OllyDbg, emulator, or runtime probes.

Closeout policy:

- Closeout may run only if command-plan authorizes it.
- If closeout is run, generated archive artifacts must be current for this round and final-check must pass after closeout.

## 3. Do Not Do

Do not expand beyond Required Audit direct-evidence rework.

Do not rework the CI evidence bridge unless a minimal report-evidence mapping fix requires touching bridge summary code.

Do not implement live GitHub Actions polling, workflow dispatch, GitHub API ingestion, product UI/API, database, queue, scheduler, autonomous AgentRunner execution, debugger integration, reverse-solving behavior, User Solve Layer behavior, or sample execution.

Do not modify files outside the allowed source/test/artifact lists in `decision_contract`.

Do not weaken command-plan authority, workflow safety checks, report-summary semantics, audit readiness, final-check, closeout, or report status rules.

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

Do not use `ci_audit_handoff_bundle.json` as a generic substitute for Required Audit answers that need direct evidence from other artifacts.

Do not allow placeholder/template answers such as repeated "bundle summarizes..." or "bridge artifacts are current-round aligned..." to satisfy Required Audit coverage when the question asks about a specific artifact or check.

Do not mutate:

- `project_state/current_state.json`
- `project_state/task_packet.json`
- `project_state/artifact_index.json`
- `project_state/negative_results.json`
- `.codex-skills/registry.json`
- `docs/prompts/*`
- `solve_reports/*`
- `.github/workflows/*`

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

Inspect current gate artifacts:

1. `project_state/gates/final_gate_result.json`
2. `project_state/gates/audit_readiness_packet.json`
3. `project_state/gates/audit_precheck_result.json`
4. `project_state/gates/ci_observation_reconcile_result.json`
5. `project_state/gates/ci_audit_handoff_bundle.json`
6. `project_state/gates/ci_run_evidence_result.json`
7. `project_state/gates/local_ci_parity_result.json`
8. `project_state/gates/ci_workflow_coverage_result.json`
9. `project_state/gates/ci_workflow_readiness_result.json`
10. `project_state/gates/local_execution_bundle.json`
11. `project_state/gates/codex_prompt_packet.json`
12. `project_state/gates/execution_log.json`
13. `project_state/gates/report_summary_synthesis.json`
14. `project_state/gates/run_closeout_result.json`
15. `project_state/gates/command_plan.json`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_ci.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_reports.py`
5. `tests/test_project_ci.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Was the current `decision_packet.md` treated as the only execution authority and `task_packet.json` as background only?
2. Did decision metadata remain valid, approved, and aligned with an active skill profile?
3. Were startup commands recorded before project gates?
4. Was startup-snapshot recorded before substantive gate/test execution?
5. Were changes limited to allowed source/test/generated artifact paths?
6. Did the implementation avoid reverse-solving, sample execution, User Solve Layer work, remote CI dispatch/polling, UI/API, database, queue, and scheduler work?
7. Did the report generator produce Required Audit answers for every item in this decision?
8. Did each Required Audit answer cite direct artifacts specific to its claim?
9. Did the implementation prevent `ci_audit_handoff_bundle.json` from being used as a generic substitute for unrelated Required Audit claims?
10. Did item-specific CI evidence questions cite `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, or `ci_workflow_readiness_result.json` directly where appropriate?
11. Did local execution bundle claims cite `local_execution_bundle.json` directly?
12. Did codex prompt packet claims cite `codex_prompt_packet.json` directly?
13. Did audit precheck claims cite `audit_precheck_result.json` directly?
14. Did audit readiness claims cite `audit_readiness_packet.json` directly?
15. Did final-check claims cite `final_gate_result.json` directly?
16. Did run-closeout and close-round claims cite `run_closeout_result.json` and current round archive evidence directly?
17. Did reconcile claims cite `ci_observation_reconcile_result.json` directly and mention `reconcile_status`, `final_consistency_status`, and `pending_diagnostic_sources` when relevant?
18. Did audit handoff bundle claims cite `ci_audit_handoff_bundle.json` directly only when the claim is actually about the bundle?
19. Did Required Audit item 30 from the previous decision stop using `ci_audit_handoff_bundle.json` as the sole/generic evidence for direct-evidence compliance?
20. Did final-check or audit-readiness harden against placeholder, generic, or repeated Required Audit answers?
21. Did tests include a failing fixture for generic bundle-substitute Required Audit answers?
22. Did tests include a passing fixture for direct artifact-specific Required Audit answers?
23. Did report-summary synthesis remain consistent with `execution_report.md` and `codex_execution_report.md`?
24. Did `pytest_result.txt` match `tests_ran` in the execution report?
25. Did execution-log align with command-plan and pytest_result?
26. Did command-plan authorize all executed commands and omit no executed commands?
27. Did `ci_observation_reconcile_result.json` remain current and final-consistent after this report-quality rework?
28. Did `ci_audit_handoff_bundle.json` remain current and ready for audit after this report-quality rework?
29. Did `final_gate_result.json` pass only after corrected Required Audit prose was produced?
30. If run-closeout was authorized and executed, did it pass and archive the corrected report artifacts?
31. Did the final report avoid generic/template prose and provide direct, claim-specific evidence for every Required Audit answer?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Identify the report generation path that creates `## Required Audit` answers in `execution_report.md` and `codex_execution_report.md`.
2. Replace generic answer templates with item-specific evidence mapping.
3. Ensure each Required Audit answer contains evidence that directly supports the question being answered.
4. Add checks that reject generic bundle-substitute answers, especially answers that cite only `ci_audit_handoff_bundle.json` for claims about other artifacts.
5. Add tests for the previous failure mode: generic prose marked PASS despite mismatched evidence.
6. Add tests for the accepted mode: each Required Audit item has direct, artifact-specific evidence.
7. Preserve semantic parity between `execution_report.md` and `codex_execution_report.md`.
8. Preserve current closeout consistency behavior for CI reconcile and audit handoff bundle artifacts.
9. Regenerate only authorized current-round project_state artifacts.

Implementation must be small, testable, backward-compatible with old report fields, and limited to engineering/audit report quality.

Suggested evidence mapping expectations:

- startup and startup-snapshot claims: `startup_snapshot.json`, `pytest_result.txt`
- decision authority claims: `decision_packet.md`, `preflight_result.json`
- source/test scope claims: `round_delta_summary.json`, `final_gate_result.json`
- CI run evidence claims: `ci_run_evidence_result.json`
- local CI parity claims: `local_ci_parity_result.json`
- workflow coverage claims: `ci_workflow_coverage_result.json`
- workflow readiness claims: `ci_workflow_readiness_result.json`
- local execution bundle claims: `local_execution_bundle.json`
- codex prompt packet claims: `codex_prompt_packet.json`
- audit precheck claims: `audit_precheck_result.json`
- audit readiness claims: `audit_readiness_packet.json`
- final-check claims: `final_gate_result.json`
- run-closeout / close-round claims: `run_closeout_result.json`, current round archive files
- reconcile claims: `ci_observation_reconcile_result.json`
- audit handoff bundle claims: `ci_audit_handoff_bundle.json`, only when the claim is about the bundle itself

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

- First run or regenerate `project_state/gates/command_plan.json` using the existing project gate command-plan flow.
- Then execute only commands authorized by `command_plan.commands`.
- If `command_plan.omitted_commands` lists a command, do not execute it.
- If this Tests section conflicts with command-plan, command-plan wins.

Expected validation coverage, subject to command-plan authorization:

```powershell
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_ci.py -q
```

If command-plan authorizes full closeout, also run:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260703_required_audit_direct_evidence_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

`project_state/pytest_result.txt` must record the actual commands and exit codes. The execution report `tests_ran` must match the recorded commands.

## 8. Stop Conditions

Stop and report `REWORK_REQUIRED` or `BLOCKED` if any of the following occurs:

1. Any Required Audit answer is missing, empty, placeholder-like, or generic.
2. Any Required Audit answer cites an artifact that does not directly support the claim.
3. `ci_audit_handoff_bundle.json` is used as the sole evidence for claims about unrelated artifacts.
4. Required Audit item 30 still claims direct evidence compliance while citing only generic bundle evidence.
5. `pytest_result.txt` is missing, stale, or inconsistent with `tests_ran`.
6. `execution_log.json` is missing, stale, or inconsistent with command-plan and pytest_result.
7. Any command outside command-plan is executed.
8. Any `command_plan.omitted_commands` command is executed.
9. `final-check` fails.
10. `run-closeout` is executed without command-plan authorization.
11. `run-closeout` fails or close-round does not close when closeout is required.
12. Any forbidden path is modified.
13. The round expands into reverse-solving, sample execution, User Solve Layer, Web/API, database, queue, scheduler, remote CI dispatch/polling, or AgentRunner execution.

If only report prose remains incomplete, do not claim `SUCCESS`; report `PARTIAL` or `REWORK_REQUIRED` with exact missing Required Audit item numbers.
