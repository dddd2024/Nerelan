```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_preflight_and_workflow_readiness_v1",
  "round_id": "round_20260702_ci_preflight_and_workflow_readiness_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_accepted_decision_id": "decision_20260702_ci_workflow_coverage_audit_gate_v1",
  "previous_accepted_round_id": "round_20260702_ci_workflow_coverage_audit_gate_v1",
  "previous_audit_outcome": "ACCEPTED",
  "supersedes_uploaded_decision_id": "decision_20260702_ci_workflow_update_from_coverage_audit_v1",
  "phase_label": "phase_2_29_ci_preflight_and_workflow_readiness",
  "primary_goal": "Close workflow coverage gaps, currentize decision-preflight validation, and add a combined workflow readiness gate.",
  "command_plan_authority_required": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_jobs.py"
  ],
  "allowed_config_files": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "allowed_generated_or_updated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt",
    "project_state/gates/*.json",
    "project_state/rounds/round_20260702_ci_preflight_and_workflow_readiness_v1/*"
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

Implement **CI Preflight and Workflow Readiness v1**.

This round supersedes the narrower uploaded workflow-update decision. It is still an `engineering_branch` round, but the scope is larger than only fixing `ci.yml` and `state-gate.yml` coverage.

Objectives:

1. Update `.github/workflows/ci.yml`, `.github/workflows/state-gate.yml`, and `.github/workflows/decision-preflight.yml` as one bounded CI validation set.
2. Close the previous `ci_workflow_coverage_result.json` missing coverage items: `tests_project_reports_py`, `audit_inventory`, `audit_readiness_packet`, `current_handoff_packet`, `local_execution_bundle`, `codex_prompt_packet`, `audit_precheck`, `report_summary`, and `execution_log`.
3. Add or repair `ci-workflow-readiness`, writing `project_state/gates/ci_workflow_readiness_result.json`.
4. Regenerate `ci_workflow_coverage_result.json` and require required coverage to be complete.
5. Preserve local execution bundle, Codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, run-closeout, and close-round behavior.

Accepted target:

- report status `SUCCESS` and recommendation `ACCEPTED`.
- `pytest_result.txt` status `PASSED`.
- `ci_workflow_coverage_result.json` current with no required missing coverage.
- `ci_workflow_readiness_result.json` current and covering all three workflow files.
- `final_gate_result.json` passed.
- `run_closeout_result.json` passed and close-round closed.

## 2. Current Evidence

The previous accepted decision was `decision_20260702_ci_workflow_coverage_audit_gate_v1` for `round_20260702_ci_workflow_coverage_audit_gate_v1`.

That round produced current evidence that existing workflow validation was safe but incomplete. The missing items were the report tests and local execution loop gates listed in the Goal section.

Existing workflow files:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`
3. `.github/workflows/decision-preflight.yml`

`decision_packet.md` controls this round. `task_packet.json` is background only. `command_plan.json` remains the only local command authority.

This round does not use reverse-solving evidence. `negative_results.json` remains relevant only to avoid re-entering blocked reverse-solving directions.

## 3. Do Not Do

Do not cross out of `engineering_branch`.

Do not implement later architecture layers in this round. Keep the work limited to bounded CI validation, project-gate evidence, tests, reports, and closeout.

Do not modify files outside the allowed source/config/artifact lists in `decision_contract`.

Do not weaken existing project gate checks or report status rules.

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

1. `project_state/gates/ci_workflow_coverage_result.json`
2. `project_state/gates/command_plan.json`
3. `project_state/gates/final_gate_result.json`
4. `project_state/gates/report_summary_synthesis.json`
5. `project_state/gates/execution_log.json`
6. `project_state/gates/run_closeout_result.json`
7. `project_state/gates/audit_readiness_packet.json`
8. `project_state/gates/local_execution_bundle.json`
9. `project_state/gates/codex_prompt_packet.json`
10. `project_state/gates/audit_precheck_result.json`

Inspect implementation and tests:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`
3. `.github/workflows/decision-preflight.yml`
4. `reverse_agent/project_gate.py`
5. `tests/test_project_gate.py`
6. `tests/test_project_reports.py`
7. `tests/test_project_jobs.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Were startup commands recorded before project gates?
2. Was startup-snapshot the first project gate?
3. Did decision metadata remain valid and approved?
4. Was this decision treated as current authority?
5. Was the narrower uploaded decision treated as superseded?
6. Were changes limited to allowed workflow/source/test/artifact files?
7. Do the workflow files cover the previous missing coverage items?
8. Is `decision-preflight.yml` included in the readiness review?
9. Is `ci_workflow_coverage_result.json` current and complete?
10. Is `ci_workflow_readiness_result.json` current and complete?
11. Did workflow validation tests cover omitted required snippets?
12. Did workflow validation tests cover policy-disallowed workflow patterns?
13. Did local execution bundle remain valid?
14. Did codex prompt packet remain valid?
15. Did audit precheck remain valid?
16. Did audit readiness remain ready and accepted?
17. Did report-summary include workflow coverage and readiness status?
18. Did execution-log align with command-plan and pytest_result?
19. Did final-check pass?
20. Did run-closeout pass and close-round close?
21. Did the report clearly state that the round stayed within CI validation infrastructure?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Update existing workflows instead of adding duplicate workflow concepts.
2. Keep workflows as validation-only CI surfaces.
3. Include focused pytest with `tests/test_project_reports.py`.
4. Include local execution loop gate coverage in state-gate workflow.
5. Include decision-preflight workflow in readiness analysis.
6. Add or repair `ci-workflow-readiness` and tests.
7. Keep `ci-workflow-coverage` aligned with the updated workflow set.
8. Preserve existing local execution loop evidence and final-check behavior.

Expected minimum workflow command coverage:

- `python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_state.py -q`
- `python -m reverse_agent.project_gate preflight --state-dir project_state`
- `python -m reverse_agent.project_gate command-plan --state-dir project_state`
- `python -m reverse_agent.project_gate audit-inventory --state-dir project_state`
- `python -m reverse_agent.project_gate audit-readiness-packet --state-dir project_state`
- `python -m reverse_agent.project_gate current-handoff-packet --state-dir project_state`
- `python -m reverse_agent.project_gate local-execution-bundle --state-dir project_state`
- `python -m reverse_agent.project_gate codex-prompt-packet --state-dir project_state`
- `python -m reverse_agent.project_gate audit-precheck --state-dir project_state`
- `python -m reverse_agent.project_gate report-summary --state-dir project_state`
- `python -m reverse_agent.project_gate execution-log --state-dir project_state`
- `python -m reverse_agent.project_gate final-check --state-dir project_state`

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
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py -q
```

Required closeout path:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_preflight_and_workflow_readiness_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

## 8. Stop Conditions

Stop with `BLOCKED` if startup, repository root, decision metadata, skill profile, command-plan, or required workflow readiness validation cannot be established.

Stop with `REWORK_REQUIRED` if required coverage remains missing, workflow readiness artifact is missing or stale, tests are incomplete, changed files exceed allowed scope, final-check fails, closeout fails, close-round is not closed, or report status is `SUCCESS` without real pytest and gate evidence.
```