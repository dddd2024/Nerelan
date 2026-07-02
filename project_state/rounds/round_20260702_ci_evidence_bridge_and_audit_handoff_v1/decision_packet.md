```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260702_ci_evidence_bridge_and_audit_handoff_v1",
  "round_id": "round_20260702_ci_evidence_bridge_and_audit_handoff_v1",
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
  "supersedes_uploaded_decision_id": "decision_20260702_live_ci_observation_handoff_v1",
  "phase_label": "phase_2_31_ci_evidence_bridge_and_audit_handoff",
  "primary_goal": "Build a larger CI evidence bridge: validate CI observation snapshots, export workflow evidence artifacts, reconcile CI/local evidence, and synthesize a GPT-auditable CI handoff bundle without introducing autonomous remote mutation.",
  "command_plan_authority_required": true,
  "accepted_requires_ci_observation_schema_artifact": true,
  "accepted_requires_ci_observation_handoff_artifact": true,
  "accepted_requires_ci_observation_reconcile_artifact": true,
  "accepted_requires_ci_artifact_manifest_artifact": true,
  "accepted_requires_ci_audit_handoff_bundle_artifact": true,
  "accepted_requires_prior_ci_evidence_not_regressed": true,
  "allowed_source_files": [
    "reverse_agent/project_gate.py",
    "reverse_agent/project_ci.py",
    "tests/test_project_gate.py",
    "tests/test_project_reports.py",
    "tests/test_project_jobs.py",
    "tests/test_project_ci.py"
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
    "project_state/rounds/round_20260702_ci_evidence_bridge_and_audit_handoff_v1/*"
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

Implement **CI Evidence Bridge and Audit Handoff Bundle v1**.

This is an `engineering_branch` round. It supersedes the narrower uploaded `live_ci_observation_handoff` plan. The previous accepted round already created local CI evidence and local/CI command parity. This round should build a larger bridge that makes CI evidence useful for future Web/API and GPT audit flows without adding a database, scheduler, autonomous runner, or sample-solving behavior.

Primary objectives:

1. Add or repair `ci-observation-schema`, writing `project_state/gates/ci_observation_schema_result.json`.
2. Add or repair `ci-observation-handoff`, writing `project_state/gates/ci_observation_handoff_packet.json`.
3. Add or repair `ci-observation-reconcile`, writing `project_state/gates/ci_observation_reconcile_result.json`.
4. Add or repair `ci-artifact-manifest`, writing `project_state/gates/ci_artifact_manifest_result.json`.
5. Add or repair `ci-audit-handoff-bundle`, writing `project_state/gates/ci_audit_handoff_bundle.json`.
6. Update existing workflows, if needed, so CI can export bounded evidence artifacts such as gate summaries, pytest result, and CI observation handoff metadata using read-only repository permissions.
7. Keep `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, and `ci_workflow_readiness_result.json` current and non-regressed.
8. Integrate the new CI evidence bridge artifacts into report-summary, final-check, run-closeout, close-round, and the current audit handoff path.
9. Stay within CI evidence infrastructure. Do not enter product UI/API implementation, queue/database/scheduler, autonomous agent execution, tool integration, reverse-solving, or sample execution.

Accepted target:

- `codex_execution_report.md` status is `SUCCESS` and recommendation is `ACCEPTED`.
- `pytest_result.txt` status is `PASSED`.
- `ci_observation_schema_result.json` is current and defines the bounded CI observation snapshot schema.
- `ci_observation_handoff_packet.json` is current and either records a validated supplied snapshot or a clear awaiting-external-observation state.
- `ci_observation_reconcile_result.json` is current and reconciles CI observation state with local CI evidence, workflow readiness, local-CI parity, command-plan, pytest_result, and execution-log.
- `ci_artifact_manifest_result.json` is current and validates workflow artifact export expectations without requiring repository write permissions.
- `ci_audit_handoff_bundle.json` is current, evidence-only, and suitable as a compact GPT audit input for the CI evidence bridge.
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

The narrower uploaded decision `decision_20260702_live_ci_observation_handoff_v1` was only a proposed next plan and is superseded by this larger CI evidence bridge plan.

Artifact freshness policy:

- Current-round generated artifacts must carry `decision_20260702_ci_evidence_bridge_and_audit_handoff_v1` and `round_20260702_ci_evidence_bridge_and_audit_handoff_v1` when regenerated.
- Historical artifacts may be referenced only as historical or nonblocking unless rebuilt with current IDs.
- Reverse-solving sample artifacts remain out of scope for this engineering round.

Command-plan policy:

- `project_state/gates/command_plan.json` remains the only local command authority.
- Codex may execute only commands authorized by `command_plan.commands`.
- `command_plan.omitted_commands` must not be executed.
- CI observation and artifact export checks in this round are evidence/validation surfaces, not autonomous remote execution surfaces.

Existing capability policy:

- Reuse existing project-gate/report/final-check/report-summary infrastructure.
- Add a small CI evidence helper module only if it prevents `project_gate.py` from accumulating unrelated parsing logic.
- Do not introduce database, message queue, long-running daemon, web server, or self-hosted runner.

## 3. Do Not Do

Do not cross out of `engineering_branch`.

Do not implement product UI, Planner API, Auditor API, queue/database/scheduler, autonomous AgentRunner execution, debugger integration, reverse-solving behavior, or sample execution in this round.

Do not trigger, poll, mutate, or upload remote CI state from local execution. Workflow artifact export may be configured for future CI runs, but local gates must remain evidence-only and non-dispatching.

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
11. `project_state/gates/current_handoff_packet.json`
12. `project_state/gates/local_execution_bundle.json`
13. `project_state/gates/codex_prompt_packet.json`
14. `project_state/gates/audit_precheck_result.json`

Inspect workflow files:

1. `.github/workflows/ci.yml`
2. `.github/workflows/state-gate.yml`
3. `.github/workflows/decision-preflight.yml`

Inspect implementation and tests:

1. `reverse_agent/project_gate.py`
2. `reverse_agent/project_ci.py` if present or newly needed
3. `tests/test_project_gate.py`
4. `tests/test_project_reports.py`
5. `tests/test_project_jobs.py`
6. `tests/test_project_ci.py` if present or newly needed

Do not scan full `project_state/rounds/`, full `solve_reports/`, or full `PROJECT_PROGRESS_LOG.txt`.

## 5. Required Audit

The execution report must answer these items with evidence and `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.

1. Were startup commands recorded before project gates?
2. Was startup-snapshot the first project gate?
3. Did decision metadata remain valid and approved?
4. Was this decision treated as current authority and `task_packet.json` as background only?
5. Was the narrower uploaded `live_ci_observation_handoff` decision treated as superseded?
6. Were changes limited to allowed workflow/source/test/artifact files?
7. Was `ci_observation_schema_result.json` generated with current decision ID, round ID, and report ID?
8. Does `ci_observation_schema_result.json` define required fields for a bounded CI run snapshot?
9. Was `ci_observation_handoff_packet.json` generated with current IDs and evidence-only semantics?
10. Does `ci_observation_handoff_packet.json` clearly state supplied-snapshot vs awaiting-external-observation state?
11. Was `ci_observation_reconcile_result.json` generated with current IDs and evidence-only semantics?
12. Does `ci_observation_reconcile_result.json` reconcile CI observation state with `ci_run_evidence_result.json`, `local_ci_parity_result.json`, workflow readiness, command-plan, pytest_result, and execution-log?
13. Was `ci_artifact_manifest_result.json` generated with current IDs and evidence-only semantics?
14. Does `ci_artifact_manifest_result.json` validate workflow artifact export expectations and confirm no repository write permission is required?
15. Was `ci_audit_handoff_bundle.json` generated with current IDs and evidence-only semantics?
16. Does `ci_audit_handoff_bundle.json` provide a compact GPT-auditable summary of CI observation, CI artifact manifest, local-CI parity, workflow coverage/readiness, report status, pytest status, final-check, and closeout?
17. Are no remote dispatch/poll/repository-mutation behaviors introduced by the new gates or workflows?
18. Did `ci_run_evidence_result.json` remain current and honest about live observation state?
19. Did `local_ci_parity_result.json` remain current with no required parity gaps?
20. Did `ci_workflow_coverage_result.json` remain current and complete?
21. Did `ci_workflow_readiness_result.json` remain current and READY?
22. Did workflow validation cover the new observation, manifest, reconcile, and audit-handoff commands if workflows were changed?
23. Did regression tests cover missing snapshot fields, malformed snapshot rejection, supplied snapshot validation, artifact export manifest checks, and audit handoff bundle contents?
24. Did local execution bundle remain valid?
25. Did codex prompt packet remain valid?
26. Did audit precheck remain valid?
27. Did audit readiness remain ready and accepted?
28. Did report-summary include CI observation schema, handoff, reconcile, artifact manifest, and audit handoff bundle statuses?
29. Did execution-log align with command-plan and pytest_result?
30. Did final-check pass?
31. Did run-closeout pass and close-round close?
32. Did the report clearly state that this round stayed within CI evidence bridge and audit handoff infrastructure?

## 6. Implementation Scope

Allowed changes are restricted to the paths listed in `decision_contract`.

Required behavior:

1. Add or repair `ci-observation-schema` as a project gate.
2. Add or repair `ci-observation-handoff` as a project gate.
3. Add or repair `ci-observation-reconcile` as a project gate.
4. Add or repair `ci-artifact-manifest` as a project gate.
5. Add or repair `ci-audit-handoff-bundle` as a project gate.
6. Define a bounded snapshot schema for CI observation metadata, including at minimum commit SHA, workflow name, run ID or equivalent run identifier when supplied, job names or step summaries, conclusion/status, observed command summaries, artifact metadata, and observation provenance.
7. If no supplied snapshot exists, generate current artifacts with a clear awaiting-observation status rather than failing or inventing evidence.
8. If a bounded snapshot fixture is supplied in tests, validate required fields and reject malformed snapshots.
9. Reconcile observation state against `ci_run_evidence_result.json`, `local_ci_parity_result.json`, `ci_workflow_coverage_result.json`, `ci_workflow_readiness_result.json`, `command_plan.json`, `pytest_result.txt`, and `execution_log.json`.
10. If workflows are changed, keep them validation-only, read-only, and limited to bounded artifact export; do not add push/commit/PR/API mutation or model calls.
11. Integrate all new artifacts into report-summary and final-check so they are not orphaned.
12. Keep all changes backward-compatible with old reports and old gate artifacts.

Expected new commands:

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
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py -q
```

If `tests/test_project_ci.py` is added, include it in the focused pytest command only after command-plan authorizes it:

```powershell
python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_project_state.py tests/test_project_ci.py -q
```

Required closeout path:

```powershell
python -m reverse_agent.project_gate run-closeout --state-dir project_state --round-id round_20260702_ci_evidence_bridge_and_audit_handoff_v1
python -m reverse_agent.project_gate final-check --state-dir project_state
```

Required regression coverage:

- `ci-observation-schema` emits the required schema fields.
- `ci-observation-handoff` emits a current awaiting-observation packet when no snapshot is supplied.
- `ci-observation-handoff` validates a bounded supplied snapshot fixture in tests.
- `ci-observation-reconcile` detects malformed or incomplete observation snapshots.
- `ci-observation-reconcile` records a nonblocking awaiting-observation state when no live snapshot is supplied.
- `ci-artifact-manifest` validates workflow artifact export configuration without requiring write permissions.
- `ci-audit-handoff-bundle` contains a compact audit summary covering observation, manifest, parity, workflow coverage/readiness, report status, pytest status, final-check, and closeout.
- `report-summary` and `final-check` include the new bridge artifacts.
- Existing CI run evidence, local-CI parity, workflow coverage, and workflow readiness tests still pass.

Write all top-level commands, exit codes, and pytest pass/fail counts to `project_state/pytest_result.txt`.

The Tests section does not itself authorize execution. If Tests and `command_plan.json` conflict, `command_plan.json` is authoritative.

## 8. Stop Conditions

Stop with `BLOCKED` if startup, repository root, decision metadata, skill profile, command-plan, workflow readiness, CI observation schema, handoff, reconciliation, artifact manifest, or audit handoff bundle validation cannot be established.

Stop with `REWORK_REQUIRED` if required bridge artifacts are missing or stale, no clear awaiting-observation/supplied-snapshot state is recorded, malformed snapshots are accepted, remote dispatch/poll/repository-mutation behavior is introduced, artifact export would require repository write permissions, prior CI run evidence/parity regresses, workflow readiness regresses, tests are incomplete, changed files exceed allowed scope, final-check fails, closeout fails, close-round is not closed, or report status is `SUCCESS` without real pytest and gate evidence.
```