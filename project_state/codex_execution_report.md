```json codex_report_summary
{
  "schema_version": 1,
  "report_id": "report_20260608_solver_profile_dispatch_integration_v1",
  "round_id": "round_20260608_solver_profile_dispatch_integration_v1",
  "based_on_decision_id": "decision_20260608_solver_profile_dispatch_integration_v1",
  "status": "SUCCESS",
  "acceptance_recommendation": "ACCEPTED",
  "mainline": "engineering_branch",
  "sample_id": "multi_solved_profile_dispatch_integration",
  "identity_verified": true,
  "candidate_generated": false,
  "candidate_validation_attempted": false,
  "candidate_validated": false,
  "runtime_validation_attempted": false,
  "debugger_attached": false,
  "emulator_used": false,
  "training_status_modified": false,
  "status_overlay_modified": false,
  "files_changed": [
    "reverse_agent/local_reverse_solver_profiles.py",
    "reverse_agent/local_reverse_constraint_recovery.py",
    "tests/test_local_reverse_solver_profile_dispatch.py",
    "project_state/local_reverse_solver_profile_dispatch_integration_audit.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "tests_ran": [
    ".venv\\Scripts\\python -m py_compile reverse_agent/local_reverse_solver_profiles.py reverse_agent/local_reverse_constraint_recovery.py reverse_agent/project_state.py",
    ".venv\\Scripts\\python -m pytest -q tests/test_local_reverse_solver_profile_dispatch.py tests/test_local_reverse_solver_profiles.py tests/test_project_state.py",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-decision --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state lint-report --state-dir project_state",
    ".venv\\Scripts\\python -m reverse_agent.project_state status --state-dir project_state",
    "git diff --check",
    "git status --short",
    "git diff --name-status"
  ],
  "generated_artifacts": [
    "project_state/local_reverse_solver_profile_dispatch_integration_audit.json"
  ]
}
```

# Solver profile dispatch integration v1

## Outcome

Executed `decision_20260608_solver_profile_dispatch_integration_v1` as an `engineering_branch` dispatch integration round. The active decision packet was the execution authority; `task_packet.json` remained advisory.

Status: `SUCCESS / ACCEPTED`.

## Implementation

- Added a lightweight profile-normalized evidence contract in `reverse_agent/local_reverse_solver_profiles.py`.
- Integrated `xor_array_table_compare`, `bytewise_reversible_transform_table_compare`, and `digit_mod_affine_transform_compare` into `recover_constraints`.
- Kept unsupported or incomplete normalized evidence conservative: missing `profile_evidence`, unknown bytewise `transform_kind`, and helper `PARTIAL/BLOCKED` results produce no candidate.
- Converted `SOLVED` helper results to existing candidate records with `validation_status=unverified`.
- Preserved the existing api-assisted/hash/sha recovery dispatch order and behavior.

## Guardrails

No real sample candidate was generated. Synthetic candidates were generated only inside unit tests. No local sample was executed, and no runtime validation, debugger, hook, emulator, probe, winpty, IDA, Ghidra, brute force, dictionary search, fuzzing, full `solve_reports` read, training status edit, or status overlay edit was performed.

Production code does not hardcode `KEEP_DREAM`, `WeKnowItOk`, `10013`, or `hookapi`; this is covered by the dispatch test.

## Artifacts

Generated `project_state/local_reverse_solver_profile_dispatch_integration_audit.json` and registered it as current in `artifact_index.latest_artifacts`, `artifact_index.latest_artifacts_v2`, and `artifact_index.artifact_refs` without overwriting the previous solver engineering recovery audit.

## Validation

Required validation commands were run and recorded in `project_state/pytest_result.txt`. The final validation bundle passed, and `project_state status` reports this decision as consumed by a success report.
