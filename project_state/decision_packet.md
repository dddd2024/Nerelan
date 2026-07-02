```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_live_ci_observation_handoff_v1",
  "round_id": "round_20260702_live_ci_observation_handoff_v1",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "previous_accepted_decision_id": "decision_20260702_ci_run_evidence_and_local_ci_parity_v1",
  "previous_accepted_round_id": "round_20260702_ci_run_evidence_and_local_ci_parity_v1",
  "previous_audit_outcome": "ACCEPTED",
  "phase_label": "phase_2_31_live_ci_observation_handoff",
  "primary_goal": "Define a bounded live-CI observation handoff layer that can validate supplied GitHub Actions run metadata, reconcile it with local evidence, and preserve a clear not-observed state without dispatching or polling remote CI.",
  "command_plan_authority_required": true,
  "accepted_requires_ci_observation_schema_artifact": true,
  "accepted_requires_ci_observation_handoff_artifact": true,
  "accepted_requires_ci_observation_reconcile_artifact": true,
  "accepted_requires_prior_ci_parity_not_regressed": true,
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
    "project_state/rounds/round_20260702_live_ci_observation_handoff_v1/*"
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

Implement **Live CI Observation Handoff v1**.

This is an `engineering_branch` round. The previous accepted round created local CI run evidence and local-CI parity gates, but it correctly recorded live CI as `NOT_OBSERVED`. This round should create the next layer: a bounded handoff contract for bringing real CI run metadata into `project_state` later, validating any supplied CI snapshot, and reconciling supplied run metadata with existing local evidence.

Primary objectives:

1. Add or repair `ci-observation-schema`, writing `project_state/gates/ci_observation_schema_result.json`.
2. Add or repair `ci-observation-handoff`, writing `project_state/gates/ci_observation_handoff_packet.json`.
3. Add or repair `ci-observation-reconcile`, writing `project_state/gates/ci_observation_reconcile_result.json`.
4. Keep `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, and `ci_workflow_readiness_result.json` current and non-regressed.
5. Update existing workflow validation only if needed so the new observation gates are covered by CI validation surfaces.
6. Preserve local execution bundle, Codex prompt packet, audit precheck, audit readiness, report-summary, execution-log, final-check, run-closeout, and close-round behavior.
7. Keep this round limited to CI observation schema, handoff, reconciliation, tests, reports, and closeout. Do not enter product UI, agent runner automation, tool integration, reverse solving, or sample execution.

Accepted target:

- `codex_execution_report.md` status is `SUCCESS` and recommendation is `ACCEPTED`.
- `pytest_result.txt` status is `PASSED`.
- `ci_observation_schema_result.json` is current and defines required fields for a bounded GitHub Actions run snapshot.
- `ci_observation_handoff_packet.json` is current, evidence-only, and either requests external CI observation or records a validated supplied snapshot.
- `ci_observation_reconcile_result.json` is current and reconciles observation state with local CI run evidence and local-CI parity.
- Existing CI workflow coverage/readiness/parity artifacts remain current and non-regressed.
- `final_gate_result.json` passes.
- `run_closeout_result.json` passes and close-round is `CLOSED`.

## 2. Current Evidence

Mainline: `engineering_branch`.

`project_state/decision_packet.md` controls this round. `project_state/task_packet.json` is background only.

Previous accepted round:

- `decision_20260702_ci_run_evidence_and_local_ci_parity_v1`
- `round_20260702_ci_run_evidence_and_local_ci_parity_v1`
- audit outcome: `ACCEPTED`

Current accepted evidence from that round:

1. `ci_run_evidence_result.json` was current and evidence-only, with `ci_observation_status: NOT_OBSERVED`.
2. `local_ci_parity_result.json` was current, evidence-only, and had no required parity gaps.
3. `ci_workflow_coverage_result.json` was current and complete.
4. `ci_workflow_readiness_result.json` was current and `READY`.
5. `pytest_result.txt` recorded focused pytest success.
6. `final_gate_result.json` passed with no blocking reasons or warnings.
7. `run_closeout_result.json` passed and close-round was `CLOSED`.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_live_ci_observation_handoff_v1` and `round_20260702_live_ci_observation_handoff_v1` when regenerated.
- Historical artifacts may be referenced only as historical or nonblocking unless rebuilt with current IDs.
- Reverse-solving sample artifacts remain out of scope for this engineering round.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only local command authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- CI observation gates in this round are evidence/validation surfaces, not remote execution surfaces.

## 3. Do Not Do

Do not cross out of `engineering_branch`.

Do not implement product UI, API planner/auditor, queue/database/scheduler, agent-runner execution, debugger integration, reverse-solving behavior, or sample execution in this round.

Do not trigger, poll, mutate, or upload remote CI state from local execution. If no CI snapshot is supplied, record that as a current explicit handoff state.

Do not modify files outside the allowed source/config/artifact lists in `decision_contract`.

Do not weaken command-plan authority, workflow safety checks, report-summary semantics, audit readiness, final-check, or report status rules.

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

1. `project_state/gates/ci_run_evidence_result.json`
2. `project_state/gates/local_ci_parity_result.json`
3. `project_state/gates/ci_workflow_coverage_result.json`
4. `project_state/gates/ci_workflow_readiness_result.json`
5. `project_state/gates/command_plan.json`
6. `project_state/gates/final_gate_result.json`
7. `project_state/gates/report_summary_synthesis.json`
8. `project_state/gates/execution_log.json`
9. `project_state/gates/run_closeout_result.json`
10. `project_state/gates/audit_readiness_packet.json`
11. `project_state/gates/local_execution_bundle.json`
12. `project_state/gates/codex_prompt_packet.json`
13. `project_state/gates/audit_precheck_result.json`

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
6. Was `ci_observation_schema_result.json` generated with current decision ID, round ID, and report ID?
7. Does `ci_observation_schema_result.json` define the required fields for a bounded CI run snapshot?
8. Was `ci_observation_handoff_packet.json` generated with current IDs and evidence-only semantics?
9. Does `ci_observation_handoff_packet.json` clearly state whether a snapshot is supplied or an external observation is still required?
10. Was `ci_observation_reconcile_result.json` generated with current IDs and evidence-only semantics?
11. Does `ci_observation_reconcile_result.json` reconcile CI observation state with `ci_run_evidence_result.json` and `local_ci_parity_result.json`?
12. Are no remote dispatch/poll/mutation behaviors introduced by the new gates?
13. Did `ci_run_evidence_result.json` remain current and honest about live observation state?
14. Did `local_ci_parity_result.json` remain current with no required parity gaps?
15. Did `ci_workflow_coverage_result.json` remain current and complete?
16. Did `ci_workflow_readiness_result.json` remain current and READY?
17. Did workflow validation cover the new observation commands if workflows were changed?
18. Did regression tests cover missing snapshot fields, supplied snapshot validation, and reconciliation states?
19. Did local execution bundle remain valid?
20. Did codex prompt packet remain valid?
21. Did audit precheck remain valid?
22. Did audit readiness remain ready and accepted?
23. Did report-summary include observation schema, handoff, and reconcile statuses?
24. Did execution-log align with command-plan and pytest_result?
25. Did final-check pass?
26. Did run-closeout pass and close-round close?
27. Did the report clearly state that this round stayed within CI observation handoff infrastructure?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Add or repair `ci-observation-schema` as a project gate.
2. Add or repair `ci-observation-handoff` as a project gate.
3. Add or repair `ci-observation-reconcile` as a project gate.
4. Ensure all three new artifacts are current-round aligned and evidence-only.
5. Define a bounded snapshot schema for CI observation metadata, including at minimum commit SHA, workflow name, run ID or equivalent run identifier when supplied, job names or step summaries, conclusion/status, observed command summaries, and observation provenance.
6. If no supplied snapshot exists, generate a current handoff artifact with a clear `AWAITING_EXTERNAL_CI_OBSERVATION` or equivalent status rather than failing or inventing evidence.
7. If a bounded snapshot fixture is supplied in tests, validate required fields and reject malformed snapshots.
8. Reconcile observation state against `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, and `ci_workflow_readiness_result.json`.
9. Integrate the new artifacts into report-summary and final-check so they are not orphaned.
10. Keep all changes backward-compatible with old reports and old gate artifacts.

Expected new commands:

- `python -m reverse_agent.project_gate ci-observation-schema --state-dir project_state`
- `python -m reverse_agent.project_gate ci-observation-handoff --state-dir project_state`
- `python -m reverse_agent.project_gate ci-observation-reconcile --state-dir project_state`

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
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_live_ci_observation_handoff_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- `ci-observation-schema` emits the required schema fields.
- `ci-observation-handoff` emits a current awaiting-observation packet when no snapshot is supplied.
- `ci-observation-handoff` validates a bounded supplied snapshot fixture in tests.
- `ci-observation-reconcile` detects malformed or incomplete observation snapshots.
- `ci-observation-reconcile` records a nonblocking awaiting-observation state when no live snapshot is supplied.
- `report-summary` and `final-check` include the new observation artifacts.
- Existing CI run evidence, local-CI parity, workflow coverage, and workflow readiness tests still pass.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if startup, repository root, decision metadata, skill profile, command-plan, workflow readiness, CI observation schema, handoff, or reconciliation validation cannot be established.

Stop with `REWORK_REQUIRED` if required observation artifacts are missing or stale, no clear awaiting-observation/supplied-snapshot state is recorded, malformed snapshots are accepted, remote dispatch/poll/mutation behavior is introduced, prior CI run evidence/parity regresses, workflow readiness regresses, tests are incomplete, changed files exceed allowed scope, final-check fails, closeout fails, close-round is not closed, or report status is `SUCCESS` without real pytest and gate evidence.
```