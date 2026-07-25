# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260725_p0_minimal_integration_test_observability_and_closure_v8","round_id":"round_20260725_p0_minimal_integration_test_observability_and_closure_v8","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260725_p0_minimal_integration_authority_field_correction_v7",
  "follows_last_round_id": "round_20260725_p0_minimal_integration_authority_field_correction_v7",
  "previous_audit_outcome": "TEST_FAILURE_NOT_OBSERVABLE",
  "failed_validation_head": "3827a33797b5821cbf314d0af2dc80a2f3d55035",
  "workstream_id": "p0-minimal-integration-test-observability-and-closure-v8",
  "source_issue": 35,
  "program_issue": 26,
  "source_pull_request": 27,
  "required_branch": "codex/p0-minimal-integration-baseline-v1",
  "starting_head": "3827a33797b5821cbf314d0af2dc80a2f3d55035",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "merge_allowed": false,
  "stop_after_exact_head_ci": true,
  "bootstrap_exception_files": ["project_state/decision_packet.md","project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot","status.git_status","gate.command_plan","gate.transition_lint","gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"test.minimal_integration_contracts","command":"python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push origin codex/p0-minimal-integration-baseline-v1","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [".github/workflows/ci.yml","AGENTS.md","docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md","docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml","tests/test_minimal_integration_baseline_docs.py","project_state/decision_packet.md","project_state/gates/command_plan.json","project_state/gates/startup_snapshot.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md","docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md"],
  "generated_artifact_paths": ["project_state/gates/startup_snapshot.json","project_state/gates/command_plan.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": ["reverse_agent/**",".github/workflows/state-gate.yml",".github/workflows/decision-preflight.yml",".codex-skills/**","docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md","docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md","pyproject.toml","pytest.ini","setup.cfg"],
  "forbidden_operations": ["direct push to main","force push","rebase","squash","merge","tag","release","unknown_binary_execution","model_api_invocation","external_reverse_tool_invocation","runner_dispatch","workflow_dispatch","automatic_merge","mark_pr_ready_for_review","branch_creation","git_config_modification","history_rewrite","secret_access","destructive_operations","product_source_changes","dependency_changes","new_gate_implementation","new_receipt_schema","new_verifier_implementation","langgraph_runtime_expansion","agent_registry","web_console","spec_kit_installation","open_swe_installation","openhands_installation","trust_layer_implementation","binary_evidence_firewall_implementation","hostile_binary_analysis_implementation"],
  "capability_policy": {"git_push_from_local_executor":true,"branch_creation_from_local_executor":false,"pull_request_creation_from_local_executor":false,"merge_from_local_executor":false,"mark_pr_ready_for_review":false,"local_network_exceptions":["git push origin codex/p0-minimal-integration-baseline-v1","gh pr edit 27"]},
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [".github/workflows/ci.yml","AGENTS.md","docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md","docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml","tests/test_minimal_integration_baseline_docs.py","project_state/decision_packet.md","project_state/gates/**"],
  "path_risk_floor": [{"pattern":".github/workflows/**","minimum_risk":"R2"},{"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},{"pattern":"project_state/gates/**","minimum_risk":"R2"},{"pattern":"tests/**","minimum_risk":"R1"}],
  "scope_policy": {"scope":"observable_contract_closure","allow_product_source":false,"allow_dependency_changes":false,"allow_workflow_changes":true,"allow_test_additions":true,"allow_documentation_changes":true,"allow_template_changes":true},
  "stop_conditions": ["transition_lint_failure","preflight_not_authorized","focused_tests_failure","diff_check_failure","ci_failure_on_exact_head","scope_violation_detected","independent_audit_rejects_head"]
}
```

## DECISION_PACKET

### Goal

Make semantic contract failures reviewable as an Actions Artifact, then apply only evidence-backed corrections and finish exact-head validation.

### Implementation Scope

1. Activate v8 and generate/validate its Command Plan and preflight.
2. Keep the existing focused CI suite unchanged except moving `tests/test_minimal_integration_baseline_docs.py` to a dedicated step.
3. Run that step with `--junitxml=pytest-minimal-integration.xml` and upload the XML with `actions/upload-artifact@v4` even on failure.
4. Inspect the XML and correct only defects evidenced by it within the allowed authority files/test.
5. Require both test steps, Decision Preflight, and State Gate to pass on one exact head.
6. Keep PR #27 Draft and unmerged.

### Completion

Completion requires a green exact head with a published semantic-test XML artifact and independent audit acceptance. Merge is not part of this round.
