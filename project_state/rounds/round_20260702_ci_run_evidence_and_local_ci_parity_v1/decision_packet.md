```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_run_evidence_and_local_ci_parity_v1",
  "round_id": "round_20260702_ci_run_evidence_and_local_ci_parity_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_accepted_decision_id": "decision_20260702_ci_preflight_and_workflow_readiness_v1",
  "previous_accepted_round_id": "round_20260702_ci_preflight_and_workflow_readiness_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_30_ci_run_evidence_and_local_ci_parity",
  "primary_goal": "Add CI run evidence ingestion and local-to-CI parity gates so the project can compare local execution evidence with workflow-defined CI evidence without changing project mainline or entering later architecture layers.",
  "command_plan_authority_required": true,
  "accepted_requires_ci_run_evidence_artifact": true,
  "accepted_requires_local_ci_parity_artifact": true,
  "accepted_requires_workflow_readiness_not_regressed": true,
  "accepted_requires_local_execution_loop_not_regressed": true,
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
    "project_state/rounds/round_20260702_ci_run_evidence_and_local_ci_parity_v1/*"
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

Implement **CI Run Evidence and Local-CI Parity v1**.

This is an `engineering_branch` round. The previous accepted round made the workflow set complete from a static coverage perspective. This round should move one layer higher: define how CI run evidence is represented in `project_state`, and compare the local execution transcript against the workflow-defined CI command surface.

Primary objectives:

1. Add or repair a bounded `ci-run-evidence` gate that writes `project_state/gates/ci_run_evidence_result.json`.
2. Add or repair a bounded `local-ci-parity` gate that writes `project_state/gates/local_ci_parity_result.json`.
3. Update the existing workflows only if needed so their validation commands remain aligned with the new evidence/parity gates.
4. Keep `ci_workflow_coverage_result.json` and `ci_workflow_readiness_result.json` passing and current.
5. Preserve local execution bundle, Codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, run-closeout, and close-round behavior.
6. Keep this round limited to project-state evidence, CI command parity, tests, reports, and closeout. Do not enter later product, runner, user solve, tool integration, or sample-solving phases.

Expected accepted state:

- `codex_execution_report.md` status is `SUCCESS` and recommendation is `ACCEPTED`.
- `pytest_result.txt` status is `PASSED`.
- `ci_run_evidence_result.json` is current, evidence-only, and states whether live CI run evidence was observed, not observed, or supplied as bounded input.
- `local_ci_parity_result.json` is current and compares workflow command coverage with local command-plan / pytest_result / execution-log coverage.
- `ci_workflow_coverage_result.json` remains current with no required missing coverage.
- `ci_workflow_readiness_result.json` remains current and `READY`.
- `final_gate_result.json` passes.
- `run_closeout_result.json` passes and close-round is `CLOSED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only.

Previous accepted round:

- `decision_20260702_ci_preflight_and_workflow_readiness_v1`
- `round_20260702_ci_preflight_and_workflow_readiness_v1`
- audit outcome: `ACCEPTED`

Current accepted evidence from that round:

1. `ci_workflow_coverage_result.json` was current, passed, had `missing_coverage: []`, and had `unsafe_patterns_found: []`.
2. `ci_workflow_readiness_result.json` was current, passed, reported `READY`, and covered `.github/workflows/ci.yml`, `.github/workflows/state-gate.yml`, and `.github/workflows/decision-preflight.yml`.
3. `ci.yml` runs import checks and focused tests including report/job/state gate tests.
4. `state-gate.yml` covers the local execution loop gates and final-check.
5. `decision-preflight.yml` covers preflight, command-plan, readiness, and focused tests.
6. `pytest_result.txt` recorded `1361 passed` for the focused test set.
7. `final_gate_result.json` passed with no blocking reasons or warnings.
8. `run_closeout_result.json` passed and close-round was `CLOSED`.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_ci_run_evidence_and_local_ci_parity_v1` and `round_20260702_ci_run_evidence_and_local_ci_parity_v1` when regenerated.
- Historical artifacts may be referenced only as historical or nonblocking unless rebuilt with current IDs.
- Reverse-solving sample artifacts remain out of scope for this engineering round.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only local command authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- Workflow YAML defines CI command expectations, but it does not authorize local commands beyond command-plan.

## 3. Do Not Do

Do not cross out of `engineering_branch`.

Do not implement later architecture layers in this round. Keep the work limited to CI evidence, parity checks, project-gate artifacts, workflow validation, tests, reports, and closeout.

Do not modify files outside the allowed source/config/artifact lists in `decision_contract`.

Do not weaken existing project gate checks, workflow readiness checks, command-plan authority, report-summary semantics, or report status rules.

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
2. `project_state/gates/ci_workflow_readiness_result.json`
3. `project_state/gates/command_plan.json`
4. `project_state/gates/final_gate_result.json`
5. `project_state/gates/report_summary_synthesis.json`
6. `project_state/gates/execution_log.json`
7. `project_state/gates/run_closeout_result.json`
8. `project_state/gates/audit_readiness_packet.json`
9. `project_state/gates/local_execution_bundle.json`
10. `project_state/gates/codex_prompt_packet.json`
11. `project_state/gates/audit_precheck_result.json`

Inspect workflow files:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`
3. `.github/workflows/decision-preflight.yml`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `tests/test_project_gate.py`
3. `tests/test_project_reports.py`
4. `tests/test_project_jobs.py`

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Were startup commands recorded before project gates?
2. Was startup-snapshot the first project gate?
3. Did decision metadata remain valid and approved?
4. Was this decision treated as current authority and `task_packet.json` as background only?
5. Were changes limited to allowed workflow/source/test/artifact files?
6. Was `ci_run_evidence_result.json` generated with current decision ID, round ID, and report ID?
7. Does `ci_run_evidence_result.json` clearly state whether CI run evidence was observed, not observed, or supplied as bounded input?
8. Is `ci_run_evidence_result.json` evidence-only and non-dispatching?
9. Was `local_ci_parity_result.json` generated with current decision ID, round ID, and report ID?
10. Does `local_ci_parity_result.json` compare workflow commands against command-plan, pytest_result, and execution-log evidence?
11. Does `local_ci_parity_result.json` report no required parity gaps for this round, or clearly classify any nonblocking future live-CI observation gap?
12. Did `ci_workflow_coverage_result.json` remain current and complete?
13. Did `ci_workflow_readiness_result.json` remain current and READY?
14. Did workflow validation tests cover omitted parity inputs and omitted run evidence fields?
15. Did local execution bundle remain valid?
16. Did codex prompt packet remain valid?
17. Did audit precheck remain valid?
18. Did audit readiness remain ready and accepted?
19. Did report-summary include CI run evidence and local-CI parity status?
20. Did execution-log align with command-plan and pytest_result?
21. Did final-check pass?
22. Did run-closeout pass and close-round close?
23. Did the report clearly state that this round stayed within CI evidence/parity infrastructure?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Add or repair `ci-run-evidence` as a project gate.
2. Add or repair `local-ci-parity` as a project gate.
3. Ensure both new artifacts are current-round aligned and evidence-only.
4. Ensure parity checks compare workflow expected commands to local command-plan / pytest_result / execution-log evidence.
5. Ensure the gates classify live CI observation status explicitly instead of pretending unobserved CI evidence exists.
6. Keep workflow coverage and workflow readiness gates passing.
7. Integrate the new artifacts into report-summary and final-check if needed so they are not orphaned.
8. Preserve existing local execution loop evidence and closeout behavior.
9. Keep changes compatible with old reports and old gate artifacts.

Expected new commands:

- `python -m reverse_agent.project_gate ci-run-evidence --state-dir project_state`
- `python -m reverse_agent.project_gate local-ci-parity --state-dir project_state`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_run_evidence_and_local_ci_parity_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- `ci-run-evidence` produces a current artifact when no live CI snapshot is available and labels that status explicitly.
- `ci-run-evidence` validates a bounded supplied CI snapshot fixture if tests provide one.
- `local-ci-parity` detects omitted workflow commands.
- `local-ci-parity` detects local transcript gaps against required workflow commands.
- `report-summary` and `final-check` include the new artifact statuses.
- Existing workflow coverage and readiness tests still pass.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if startup, repository root, decision metadata, skill profile, command-plan, workflow readiness, or required CI evidence/parity validation cannot be established.

Stop with `REWORK_REQUIRED` if required artifacts are missing or stale, parity comparison is only superficial, workflow readiness regresses, tests are incomplete, changed files exceed allowed scope, final-check fails, closeout fails, close-round is not closed, or report status is `SUCCESS` without real pytest and gate evidence.
```