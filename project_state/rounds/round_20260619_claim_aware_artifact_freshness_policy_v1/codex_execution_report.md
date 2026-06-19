```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "codex_report_20260619_claim_aware_artifact_freshness_policy_v1",
  "round_id": "round_20260619_claim_aware_artifact_freshness_policy_v1",
  "based_on_decision_id": "decision_20260619_claim_aware_artifact_freshness_policy_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "files_changed": [
    "project_state/artifact_policy.json",
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/round_manifest.json",
    "reverse_agent/project_gate.py",
    "tests/test_project_gate.py"
  ],
  "tests_ran": [
    "python -m pytest tests/test_project_gate.py tests/test_project_state.py -q",
    "python -m reverse_agent.project_state doctor --state-dir project_state",
    "python -m reverse_agent.project_gate preflight --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state",
    "python -m reverse_agent.project_gate gate-profile --state-dir project_state --json",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate command-plan --state-dir project_state --json",
    "python -m reverse_agent.project_gate report-summary --state-dir project_state",
    "python -m reverse_agent.project_gate final-check --state-dir project_state",
    "python -m reverse_agent.project_gate close-round --state-dir project_state --round-id round_20260619_claim_aware_artifact_freshness_policy_v1"
  ],
  "generated_artifacts": [
    "project_state/codex_execution_report.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/final_gate_result.json",
    "project_state/gates/gate_profile_plan.json",
    "project_state/gates/preflight_result.json",
    "project_state/gates/report_summary_synthesis.json",
    "project_state/gates/round_baseline.json",
    "project_state/gates/round_close_snapshot.json",
    "project_state/gates/round_delta_summary.json",
    "project_state/pytest_result.txt",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/codex_execution_report.md",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/decision_packet.md",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/pytest_result.txt",
    "project_state/rounds/round_20260619_claim_aware_artifact_freshness_policy_v1/round_manifest.json"
  ],
  "external_state_notices": [
    "50 missing historical sample artifacts"
  ]
}
```

# Codex Execution Report - Claim-Aware Artifact Freshness Policy V1

## Decision

Decision `decision_20260619_claim_aware_artifact_freshness_policy_v1` (round `round_20260619_claim_aware_artifact_freshness_policy_v1`) on mainline `engineering_branch`.

## Status: SUCCESS

### Completed Work

1. Updated `reverse_agent/project_gate.py` so final-check classifies artifact freshness as claim-aware: required current artifacts and claimed evidence remain blocking, while unclaimed historical/backlog sample artifacts become limitations for non-sample mainlines.
2. Preserved strict behavior for `reverse_solving` and for any report that claims sample/current evidence artifacts.
3. Added status-policy output fields for `required_current_artifacts`, `claimed_evidence_artifacts`, `historical_or_backlog_artifacts`, and `historical_backlog`.
4. Added `project_state/artifact_policy.json` to document the new blocking and limitation rules.
5. Updated `tests/test_project_gate.py` coverage for `engineering_branch`, `tool_integration`, `training_dataset`, `reverse_solving`, and claimed-evidence blocking behavior.

### Safety Scope

This round changed only project gate policy, its tests, and project_state closeout artifacts. It did not run samples, solvers, harnesses, IDA, Ghidra, debuggers, runtime probes, GUI workflows, or full `solve_reports`/progress-log reads.

### Tests And Gates

The required pytest target passed with `804 passed`. Gate/profile/report/final closeout commands are recorded in `project_state/pytest_result.txt`.

### External State Notices

50 missing historical sample artifacts.
