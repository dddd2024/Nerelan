# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260729_unattended_gate2_regression_reconciliation_v2","round_id":"round_20260729_unattended_gate2_regression_reconciliation_v2","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260729_unattended_gate2_baseline_v1",
  "follows_last_round_id": "round_20260729_unattended_gate2_baseline_v1",
  "previous_audit_outcome": "BLOCKED_SCOPE_EXPANSION_REQUIRED",
  "workstream_id": "unattended-gate2-regression-reconciliation-v2",
  "source_issue": 77,
  "predecessor_issue": 76,
  "parent_plan": 74,
  "required_branch": "codex/unattended-base-platform-v0",
  "starting_head": "d625474b8bc878ecd7973068892404f60653afb7",
  "activation_base_sha": "2aacf42dbab7f283454908da861b6ef44990f1d5",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "pr_must_be_draft": true,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "stop_after_exact_head_ci": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"diagnostic.audit_isolated","command":"python -m pytest tests/test_project_audits.py::test_validate_audits_dir_accepts_current_audit_record -q -vv","phase":"diagnostic","required":false,"expected_exit_codes":[0,1],"execution_surface":"local","operations":["regression_diagnostic"],"network_access":false,"diagnostic_only":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"diagnostic.audit_file","command":"python -m pytest tests/test_project_audits.py -q -vv","phase":"diagnostic","required":false,"expected_exit_codes":[0,1],"execution_surface":"local","operations":["regression_diagnostic"],"network_access":false,"diagnostic_only":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.focused_reconciliation","command":"python -m pytest tests/test_mainline_landing.py::test_committed_pr67_intent_binds_exact_v5_authority tests/test_mainline_landing.py::test_production_pre_merge_simulation tests/test_project_audits.py::test_validate_audits_dir_accepts_current_audit_record tests/test_project_gate.py::test_transition_packaging_and_workflow_boundary -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.unattended_unit","command":"python -m pytest tests/unattended/unit -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.unattended_integration","command":"python -m pytest tests/unattended/integration -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.compose_config","command":"docker compose -f deploy/unattended/compose.yaml config --quiet","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_configuration_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.doctor","command":"python -m reverse_agent.unattended.cli doctor","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_health_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.full_regression","command":"python -m pytest -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check 2aacf42dbab7f283454908da861b6ef44990f1d5..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.python313_temporal","command":"python3.13 -c \"import temporalio; print(temporalio.__version__)\"","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_up","command":"docker compose -f deploy/unattended/compose.yaml up -d --wait","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.gate2","command":"python -m reverse_agent.unattended.cli gate2-probe","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","model_api_invocation","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push -u origin codex/unattended-base-platform-v0","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.create_draft_pr","command":"gh pr create --repo dddd2024/reverse-agent --base main --head codex/unattended-base-platform-v0 --draft --title \"Gate 2: unattended base platform v0\" --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_create","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue77","command":"gh issue comment 77 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_draft_pr","command":"gh pr comment PR_NUMBER --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observation.exact_head_checks","command":"gh pr checks PR_NUMBER --repo dddd2024/reverse-agent --watch","phase":"observation","required":false,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_project_audits.py",
    "deploy/unattended/**",
    "reverse_agent/unattended/**",
    "examples/unattended_target/**",
    "tests/unattended/**",
    "docs/unattended/**",
    "pyproject.toml",
    ".gitignore"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/**",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/mainline_integration_receipts/**",
    "project_state/mainline_recoveries/**",
    "project_state/integration_baselines/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "AGENTS.md",
    "pytest.ini",
    "setup.cfg"
  ],
  "forbidden_operations": [
    "implementation before PRE_EXECUTION_AUTHORIZED",
    "GitHub branch or pull request adapter product implementation",
    "CI wait product implementation",
    "complete R1 fixture",
    "worker restart proof",
    "automatic rework loop",
    "custom workflow engine",
    "custom sandbox",
    "custom agent coding loop",
    "custom model gateway",
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "mark_ready_for_review",
    "auto_merge",
    "tag or release",
    "production deployment",
    "workflow dispatch",
    "runner dispatch",
    "unknown binary execution",
    "PR #47 mutation",
    "PR #49 mutation"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "auto_merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": true,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "docker compose -f deploy/unattended/compose.yaml up -d --wait",
      "python -m reverse_agent.unattended.cli gate2-probe",
      "git push -u origin codex/unattended-base-platform-v0",
      "gh pr create --repo dddd2024/reverse-agent --base main --head codex/unattended-base-platform-v0 --draft --title \"Gate 2: unattended base platform v0\" --body-file PR_BODY_TEMP_PATH",
      "gh issue comment 77 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH",
      "gh pr comment PR_NUMBER --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_project_audits.py",
    "deploy/unattended/**",
    "reverse_agent/unattended/**",
    "examples/unattended_target/**",
    "tests/unattended/**",
    "docs/unattended/**",
    "pyproject.toml",
    ".gitignore"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":"tests/test_mainline_landing.py","minimum_risk":"R2"},
    {"pattern":"tests/test_project_gate.py","minimum_risk":"R2"},
    {"pattern":"tests/test_project_audits.py","minimum_risk":"R2"},
    {"pattern":"deploy/unattended/**","minimum_risk":"R2"},
    {"pattern":"reverse_agent/unattended/**","minimum_risk":"R2"},
    {"pattern":"examples/unattended_target/**","minimum_risk":"R2"},
    {"pattern":"tests/unattended/**","minimum_risk":"R2"},
    {"pattern":"docs/unattended/**","minimum_risk":"R2"},
    {"pattern":"pyproject.toml","minimum_risk":"R2"},
    {"pattern":".gitignore","minimum_risk":"R2"}
  ],
  "scope_policy": {
    "scope": "unattended-gate2-regression-reconciliation-v2",
    "implementation_risk_tier": "R2",
    "governance_artifact_risk_tier": "R2",
    "allow_product_source": true,
    "allow_test_changes": true,
    "allow_dependency_changes": true,
    "allow_workflow_changes": false,
    "allow_gate_runtime_changes": false,
    "allow_path_a_changes": false,
    "allow_new_branch_or_pr": true,
    "allow_pr47_or_pr49_mutation": false
  },
  "component_lock_projection_sha256": "e7c334033f8999d7b53fdd7b4b34e4469c3f87a871d4524e4270c707b7f2f83d",
  "stop_conditions": [
    "startup_state_mismatch",
    "governance_preflight_failure",
    "component_digest_drift",
    "component_compatibility_failure",
    "execution_environment_failure",
    "llm_provider_credential_missing",
    "secret_boundary_failure",
    "scope_expansion_required",
    "focused_tests_failure",
    "regression_test_failure",
    "diff_check_failure",
    "exact_head_CI_failure",
    "attempted_merge_mark_ready_auto_merge_tag_release_or_main_push",
    "PR47_or_PR49_mutation"
  ]
}
```

## DECISION_PACKET

### Goal

Authorize only the Issue #77 recovery of the exact unpublished Issue #76
commit chain, reconciliation of the four named regressions, real Gate 2
compatibility probes, and auditable Draft publication on
`codex/unattended-base-platform-v0`.

### Authority and sequencing

This successor Decision is the sole R2 recovery authority. It is committed
alone on exact recovered head
`d625474b8bc878ecd7973068892404f60653afb7`. The compiler-generated Command
Plan and successful `PRE_EXECUTION_AUTHORIZED` must be committed separately
before regression or product/security mutation.

### Product boundary

The recovered product commits remain immutable historical inputs. Rework is
limited to the three named regression-test files and, only if independent
audit proves a defect, the existing unattended allowed paths. No file under
`project_state/audits/**` may change. GitHub/CI product adapters, full R1
fixtures, worker-restart proof, automatic rework, and main mutation remain out
of scope.

### Publication and stop boundary

After Path B and the zero-failure full regression pass, this Decision permits
one non-force push of the exact non-main branch, creation of one Draft PR
against `main`, evidence comments on Issue #77 and that Draft PR, and read-only
observation of exact-head Actions. Publication remains permitted when all
non-provider probes pass and the sole remaining blocker is a missing real
provider credential. The PR must remain Draft. Mark-ready, merge, auto-merge,
history rewrite, direct main push, tag, release, production deployment, and
mutation of PR #47 or PR #49 are never authorized.
