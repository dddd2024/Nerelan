```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_evidence_bridge_closeout_consistency_rework_v1",
  "round_id": "round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "reworks_decision_id": "decision_20260702_ci_evidence_bridge_and_audit_handoff_v1",
  "reworks_round_id": "round_20260702_ci_evidence_bridge_and_audit_handoff_v1",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "phase_label": "phase_2_31_ci_evidence_bridge_closeout_consistency_rework",
  "primary_goal": "Fix post-closeout consistency for CI evidence bridge artifacts so reconcile and audit handoff bundle reflect final final-check/run-closeout/close-round state instead of stale pre-closeout diagnostic snapshots.",
  "command_plan_authority_required": true,
  "accepted_requires_reconcile_post_closeout_consistency": true,
  "accepted_requires_audit_bundle_post_closeout_consistency": true,
  "accepted_requires_final_check_hardening": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_ci.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_ci.py"
  ],
  "allowed_config_files": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1/*"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/task_packet.json",
    "project_state/artifact_index.json",
    "project_state/negative_results.json",
    ".codex-skills/registry.json",
    "docs/prompts/*",
    "solve_reports/*"
  ]
}
```

# DECISION_PACKET

## 1. Goal

Implement **CI Evidence Bridge Closeout Consistency Rework v1**.

This is an `engineering_branch` rework round. The previous round implemented the CI evidence bridge, but audit found that `ci_audit_handoff_bundle.json` and `ci_observation_reconcile_result.json` preserved stale pre-closeout diagnostic state even though final-check and run-closeout ultimately passed. This round must fix that consistency failure without expanding the CI bridge feature set.

Primary objectives:

1. Fix `ci_observation_reconcile_result.json` so it does not report plain `RECONCILED` while referenced execution evidence is still failed, incomplete, or pre-closeout diagnostic unless that state is explicitly classified as non-final.
2. Fix `ci_audit_handoff_bundle.json` so it reflects final post-closeout evidence, or explicitly separates pre-closeout diagnostic snapshots from post-closeout final status.
3. Harden `final-check` so a bundle containing stale `final_check: FAILED`, `run_closeout: IN_PROGRESS`, or unresolved `pending_diagnostic_sources` cannot pass as a final accepted audit bundle.
4. Refresh report-summary and closeout behavior so the final audit handoff bundle is not stale after final-check/run-closeout/close-round.
5. Keep existing CI evidence bridge capabilities intact: observation schema, observation handoff, observation reconcile, artifact manifest, audit handoff bundle, workflow coverage/readiness, CI run evidence, and local-CI parity.
6. Do not introduce remote CI dispatch, polling, repository mutation, product UI/API, database/queue/scheduler, AgentRunner execution, reverse-solving, or sample execution.

Accepted target:

- `codex_execution_report.md` status is `SUCCESS` and recommendation is `ACCEPTED`.
- `pytest_result.txt` status is `PASSED`.
- `ci_observation_reconcile_result.json` is current and has an accurate final consistency state.
- `ci_audit_handoff_bundle.json` is current and has accurate final post-closeout status for final-check, run-closeout, close-round, execution-log, pytest, report status, workflow coverage/readiness, local-CI parity, and CI observation state.
- `ci_audit_handoff_bundle.json` must not retain stale `final_check: FAILED`, `run_closeout: IN_PROGRESS`, or unresolved `pending_diagnostic_sources` while claiming `READY_FOR_AUDIT` and report `SUCCESS`.
- `final_gate_result.json` hard-checks bundle/reconcile consistency and passes only after the stale bundle/reconcile condition is fixed.
- `run_closeout_result.json` passes and close-round is `CLOSED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only.

Reworked round:

- `decision_20260702_ci_evidence_bridge_and_audit_handoff_v1`
- `round_20260702_ci_evidence_bridge_and_audit_handoff_v1`
- audit outcome: `REWORK_REQUIRED`

Blocking evidence from the audit:

1. `ci_audit_handoff_bundle.json` was current but internally recorded `final_check.gate_status: FAILED`, `run_closeout.status: IN_PROGRESS`, and pending diagnostic sources even though final `final_gate_result.json` passed and `run_closeout_result.json` closed the round.
2. `ci_observation_reconcile_result.json` reported `reconcile_status: RECONCILED` while its referenced `execution_log` source was still failed/incomplete.
3. The prior final-check did not hard-fail on stale internal bundle status.
4. Several Required Audit answers used `ci_audit_handoff_bundle.json` as broad evidence instead of directly citing the specific artifact being asserted.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_ci_evidence_bridge_closeout_consistency_rework_v1` and `round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1` when regenerated.
- Historical artifacts from the failed bridge round may be referenced only as rework evidence; they must not be treated as current accepted evidence.
- Reverse-solving sample artifacts remain out of scope for this engineering round.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only local command authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- The Tests section does not override command-plan.

## 3. Do Not Do

Do not expand beyond closeout consistency rework.

Do not implement live GitHub Actions polling, workflow dispatch, GitHub API ingestion, product UI/API, database, queue, scheduler, autonomous AgentRunner execution, debugger integration, reverse-solving behavior, or sample execution.

Do not add new CI bridge artifact types beyond what is necessary to fix reconcile/bundle/final-check consistency.

Do not modify files outside the allowed source/config/artifact lists in `decision_contract`.

Do not weaken command-plan authority, workflow safety checks, report-summary semantics, audit readiness, final-check, closeout, or report status rules.

Do not use `COMPLETED_WITH_LIMITATIONS` as report status.

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

1. `project_state/gates/ci_observation_schema_result.json`
2. `project_state/gates/ci_observation_handoff_packet.json`
3. `project_state/gates/ci_observation_reconcile_result.json`
4. `project_state/gates/ci_artifact_manifest_result.json`
5. `project_state/gates/ci_audit_handoff_bundle.json`
6. `project_state/gates/ci_run_evidence_result.json`
7. `project_state/gates/local_ci_parity_result.json`
8. `project_state/gates/ci_workflow_coverage_result.json`
9. `project_state/gates/ci_workflow_readiness_result.json`
10. `project_state/gates/command_plan.json`
11. `project_state/gates/execution_log.json`
12. `project_state/gates/report_summary_synthesis.json`
13. `project_state/gates/final_gate_result.json`
14. `project_state/gates/run_closeout_result.json`
15. `project_state/gates/audit_readiness_packet.json`
16. `project_state/gates/audit_precheck_result.json`

Inspect workflow files only if needed:

1. `.github/workflows/state-gate.yml`
2. `.github/workflows/decision-preflight.yml`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_ci.py`
3. `tests/test_project_gate.py`
4. `tests/test_project_reports.py`
5. `tests/test_project_ci.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Were startup commands recorded before project gates?
2. Was startup-snapshot the first project gate?
3. Did decision metadata remain valid and approved?
4. Was this rework decision treated as current authority and `task_packet.json` as background only?
5. Were changes limited to allowed source/test/workflow/artifact files?
6. Did the report clearly identify the previous bridge round as `REWORK_REQUIRED` rather than accepted?
7. Was `ci_observation_reconcile_result.json` regenerated with current decision ID, round ID, and report ID?
8. Does `ci_observation_reconcile_result.json` accurately classify reconcile state when execution-log or other diagnostic sources are not final?
9. Does `ci_observation_reconcile_result.json` avoid plain `RECONCILED` when any required source is failed or stale?
10. Was `ci_audit_handoff_bundle.json` regenerated with current decision ID, round ID, and report ID?
11. Does `ci_audit_handoff_bundle.json` reflect final post-closeout `final_gate_result.json` status?
12. Does `ci_audit_handoff_bundle.json` reflect final post-closeout `run_closeout_result.json` and close-round status?
13. Does `ci_audit_handoff_bundle.json` avoid stale `final_check: FAILED` while claiming `READY_FOR_AUDIT`?
14. Does `ci_audit_handoff_bundle.json` avoid stale `run_closeout: IN_PROGRESS` while claiming `READY_FOR_AUDIT`?
15. Does `ci_audit_handoff_bundle.json` avoid unresolved `pending_diagnostic_sources` when report status is `SUCCESS` and recommendation is `ACCEPTED`?
16. Did final-check add or enforce a hard check for stale bundle/reconcile internal status?
17. Did final-check fail in tests or fixtures when bundle final_check/run_closeout states are stale?
18. Did report-summary include the corrected reconcile and audit handoff bundle statuses?
19. Did execution-log align with command-plan and pytest_result, or was any diagnostic gap explicitly non-final before closeout?
20. Did `ci_run_evidence_result.json` remain current and honest about live observation state?
21. Did `local_ci_parity_result.json` remain current with no required parity gaps?
22. Did `ci_workflow_coverage_result.json` remain current and complete?
23. Did `ci_workflow_readiness_result.json` remain current and READY?
24. Did local execution bundle remain valid?
25. Did codex prompt packet remain valid?
26. Did audit precheck remain valid?
27. Did audit readiness become ready and accepted after closeout?
28. Did final-check pass only after the corrected bundle/reconcile state was produced?
29. Did run-closeout pass and close-round close?
30. Did Required Audit answers cite direct artifact evidence rather than using `ci_audit_handoff_bundle.json` as a generic substitute for all claims?
31. Did this round avoid remote CI dispatch/poll/repository mutation and stay within closeout consistency rework?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Fix the logic that builds `ci_observation_reconcile_result.json` so its status model distinguishes final success from diagnostic/pre-closeout gaps.
2. Fix the logic that builds `ci_audit_handoff_bundle.json` so it either runs after final closeout evidence is available or records both pre-closeout and post-closeout states without contradiction.
3. Add final-check validation that rejects an accepted report when `ci_audit_handoff_bundle.json` internally contains stale `final_check: FAILED`, `run_closeout: IN_PROGRESS`, or unresolved pending diagnostic sources.
4. Add tests for stale bundle failure modes and corrected post-closeout bundle success modes.
5. Add tests for reconcile status classification when execution-log is failed/incomplete versus post-closeout converged.
6. Ensure report-summary and audit readiness consume the corrected final bundle state.
7. Preserve all existing CI evidence bridge artifacts and workflow safety checks.
8. Keep compatibility with old reports and old gate artifacts.

Expected commands remain the current bridge commands plus final consistency validation:

- `python -m reverse_agent.project_gate ci-observation-schema --state-dir project_state`
- `python -m reverse_agent.project_gate ci-observation-handoff --state-dir project_state`
- `python -m reverse_agent.project_gate ci-observation-reconcile --state-dir project_state`
- `python -m reverse_agent.project_gate ci-artifact-manifest --state-dir project_state`
- `python -m reverse_agent.project_gate ci-audit-handoff-bundle --state-dir project_state`

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

Required command-plan and gate flow:

```powershell
python -m reverse_agent.project_gate command-plan --state-dir project_state
python -m reverse_agent.project_gate command-plan --state-dir project_state --json
python -m reverse_agent.project_gate preflight --state-dir project_state --allow-consumed
python -m reverse_agent.project_gate ci-workflow-coverage --state-dir project_state
python -m reverse_agent.project_gate ci-workflow-readiness --state-dir project_state
python -m reverse_agent.project_gate ci-run-evidence --state-dir project_state
python -m reverse_agent.project_gate local-ci-parity --state-dir project_state
python -m reverse_agent.project_gate ci-observation-schema --state-dir project_state
python -m reverse_agent.project_gate ci-observation-handoff --state-dir project_state
python -m reverse_agent.project_gate ci-observation-reconcile --state-dir project_state
python -m reverse_agent.project_gate ci-artifact-manifest --state-dir project_state
python -m reverse_agent.project_gate ci-audit-handoff-bundle --state-dir project_state
python -m reverse_agent.project_gate audit-inventory --state-dir project_state
python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state
python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state
python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state
python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state
python -m reverse_agent.project_gate audit-precheck --state-dir project_state
python -m reverse_agent.project_gate report-summary --state-dir project_state
python -m reverse_agent.project_gate execution-log --state-dir project_state
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required focused pytest:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py tests/test_project_ci.py -q
```

If `tests/test_project_jobs.py` remains authorized by command-plan, include it as well:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py -q
```

Required closeout path:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_evidence_bridge_closeout_consistency_rework_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- Stale audit handoff bundle with internal `final_check: FAILED` must cause final-check failure.
- Stale audit handoff bundle with internal `run_closeout: IN_PROGRESS` must cause final-check failure.
- Bundle with unresolved pending diagnostic sources must not be accepted with report `SUCCESS` and recommendation `ACCEPTED`.
- Reconcile artifact must not report plain `RECONCILED` when required source evidence is failed or stale.
- Corrected post-closeout bundle must reflect final `final_gate_result.json`, `run_closeout_result.json`, and close-round status.
- Existing CI observation schema/handoff/reconcile/manifest/bundle tests still pass.
- Existing workflow coverage/readiness/local-CI parity tests still pass.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if startup, repository root, decision metadata, skill profile, command-plan, or required rework artifacts cannot be established.

Stop with `REWORK_REQUIRED` if `ci_audit_handoff_bundle.json` still contains stale internal `final_check: FAILED`, `run_closeout: IN_PROGRESS`, or unresolved pending diagnostic sources while claiming `READY_FOR_AUDIT`; if `ci_observation_reconcile_result.json` still reports plain `RECONCILED` while required sources are failed/stale; if final-check does not hard-fail those conditions; if tests are incomplete; if changed files exceed allowed scope; if final-check fails; if closeout fails; if close-round is not closed; or if report status is `SUCCESS` without real pytest and gate evidence.
```