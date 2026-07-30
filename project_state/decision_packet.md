# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260730_unattended_gate2_workspace_provisioning_recovery_v9","round_id":"round_20260730_unattended_gate2_workspace_provisioning_recovery_v9","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260730_unattended_gate2_attempt_readiness_recovery_v8",
  "follows_last_round_id": "round_20260730_unattended_gate2_attempt_readiness_recovery_v8",
  "previous_audit_outcome": "BLOCKED_PROVIDER_FREE_RUNTIME_PROOF",
  "workstream_id": "unattended-gate2-workspace-provisioning-recovery-v9",
  "source_issue": 85,
  "predecessor_issue": 84,
  "parent_plan": 74,
  "active_pr": 78,
  "required_branch": "codex/unattended-base-platform-v0",
  "starting_head": "67e49f7044a82c0ea464f9b54946ce73cbb8c14e",
  "activation_base_sha": "2aacf42dbab7f283454908da861b6ef44990f1d5",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_must_be_draft": true,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "checkpoint_push_allowed": true,
  "real_provider_credential_allowed": false,
  "stop_after_exact_head_ci": false,
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
    {"command_id":"test.unattended_unit","command":"python -m pytest tests/unattended/unit -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.unattended_integration","command":"python -m pytest tests/unattended/integration -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.compose_config","command":"docker compose -f deploy/unattended/compose.yaml config --quiet","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_configuration_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.doctor","command":"python -m reverse_agent.unattended.cli doctor","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_health_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.full_regression","command":"python -m pytest -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check 2aacf42dbab7f283454908da861b6ef44990f1d5..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.workspace_fresh","command":"python -m reverse_agent.unattended.cli workspace-preflight --compose-project reverse-agent-issue85-workspace --stack-mode fresh","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","container_runtime","secret_boundary_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.workspace_restart","command":"python -m reverse_agent.unattended.cli workspace-preflight --compose-project reverse-agent-issue85-workspace --stack-mode restart","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","container_runtime","secret_boundary_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push -u origin codex/unattended-base-platform-v0","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.update_draft_pr","command":"gh pr edit 78 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_update","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue85","command":"gh issue comment 85 --repo dddd2024/reverse-agent --body-file ISSUE85_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_draft_pr","command":"gh pr comment 78 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observation.exact_head_checks","command":"gh pr checks 78 --repo dddd2024/reverse-agent --watch","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_fresh","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue85-runtime-proof -f deploy/unattended/compose.yaml --profile runtime-proof up -d --wait","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.runtime_proof","command":"python -m reverse_agent.unattended.cli gate2-runtime-proof --workflow-id unattended:dddd2024/reverse-agent:issue:85:runtime-proof-a","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","container_runtime","network_access","secret_boundary_validation"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_cleanup","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue85-runtime-proof -f deploy/unattended/compose.yaml --profile runtime-proof down -v","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "deploy/unattended/**",
    "reverse_agent/unattended/**",
    "tests/unattended/**",
    "docs/unattended/**",
    ".github/workflows/ci.yml",
    ".github/scripts/**",
    ".gitignore"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_project_audits.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
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
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_project_audits.py",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "AGENTS.md",
    "pytest.ini",
    "setup.cfg"
  ],
  "forbidden_operations": [
    "implementation before PRE_EXECUTION_AUTHORIZED",
    "new branch or second pull request",
    "GitHub branch or pull request adapter product implementation",
    "CI wait product implementation",
    "complete R1 fixture or unified Web Console",
    "real provider credential use",
    "automatic rework loop",
    "custom workflow engine",
    "general-purpose custom sandbox",
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
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "python -m reverse_agent.unattended.cli workspace-preflight --compose-project reverse-agent-issue85-workspace --stack-mode fresh",
      "python -m reverse_agent.unattended.cli workspace-preflight --compose-project reverse-agent-issue85-workspace --stack-mode restart",
      "git push -u origin codex/unattended-base-platform-v0",
      "gh pr edit 78 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH",
      "gh issue comment 85 --repo dddd2024/reverse-agent --body-file ISSUE85_COMMENT_TEMP_PATH",
      "gh pr comment 78 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH",
      "gh pr checks 78 --repo dddd2024/reverse-agent --watch",
      "wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue85-runtime-proof -f deploy/unattended/compose.yaml --profile runtime-proof up -d --wait",
      "python -m reverse_agent.unattended.cli gate2-runtime-proof --workflow-id unattended:dddd2024/reverse-agent:issue:85:runtime-proof-a",
      "wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue85-runtime-proof -f deploy/unattended/compose.yaml --profile runtime-proof down -v"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "deploy/unattended/**",
    "reverse_agent/unattended/**",
    "tests/unattended/**",
    "docs/unattended/**",
    ".github/workflows/ci.yml",
    ".github/scripts/**"
    ,".gitignore"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":"deploy/unattended/**","minimum_risk":"R2"},
    {"pattern":"reverse_agent/unattended/**","minimum_risk":"R2"},
    {"pattern":"tests/unattended/**","minimum_risk":"R2"},
    {"pattern":"docs/unattended/**","minimum_risk":"R2"},
    {"pattern":".github/workflows/ci.yml","minimum_risk":"R2"},
    {"pattern":".github/scripts/**","minimum_risk":"R2"},
    {"pattern":".gitignore","minimum_risk":"R2"}
  ],
  "scope_policy": {
    "scope": "unattended-gate2-workspace-provisioning-recovery-v9",
    "implementation_risk_tier": "R2",
    "governance_artifact_risk_tier": "R2",
    "allow_product_source": true,
    "allow_test_changes": true,
    "allow_dependency_changes": false,
    "allow_workflow_changes": true,
    "allow_gate_runtime_changes": false,
    "allow_path_a_changes": false,
    "allow_new_branch_or_pr": false,
    "allow_pr47_or_pr49_mutation": false
  },
  "component_lock_projection_sha256": "e7c334033f8999d7b53fdd7b4b34e4469c3f87a871d4524e4270c707b7f2f83d",
  "stop_conditions": [
    "startup_state_mismatch",
    "governance_preflight_failure",
    "component_digest_drift",
    "temporal_payload_contract_failure",
    "sandbox_controller_integration_failure",
    "workspace_identity_contract_failure",
    "workspace_root_preflight_failure",
    "attempt_directory_provision_failure",
    "attempt_transport_failure",
    "upstream_tool_path_probe_failure",
    "agent_server_session_isolation_failure",
    "executor_key_log_boundary_failure",
    "litellm_least_privilege_failure",
    "ci_credential_hygiene_failure",
    "component_compatibility_failure",
    "execution_environment_failure",
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

Authorize only Issue #85 local-chain recovery and fixed workspace provisioning
correction on existing Draft PR #78: preserve the exact unpublished #82-#84
chain, fail fast on finite workspace-root contract violations before Docker
launch, publish the mandatory auditable Draft checkpoint, and then prove one
provider-free OpenHands conversation/tool lifecycle after exact-head checks.

### Authority and sequencing

This successor Decision is the sole R2 recovery and rework authority. It is
committed alone on exact recovered starting head
`67e49f7044a82c0ea464f9b54946ce73cbb8c14e`. The compiler-generated Command
Plan and successful `PRE_EXECUTION_AUTHORIZED` must be committed separately
before any implementation mutation.

### Product boundary

The existing seventeen unpublished commits remain immutable historical inputs. Rework is
limited to `deploy/unattended/**`, `docs/unattended/**`,
`reverse_agent/unattended/**`, `tests/unattended/**`, `.github/scripts/**`,
`.gitignore`, and the single workflow `.github/workflows/ci.yml`, plus the Decision and
compiler-owned Gate files.
No dependency, audit record, state/decision workflow, mainline landing,
remote verifier, or control-plane file may change. A fixed Docker-exec JSON
transport, a dedicated controller worker, and a test-only provider-free
fixture remain allowed. A fixed one-shot workspace bootstrap with no Docker
socket, credential, or public network, plus typed preflight and exact Attempt
directory provisioning, is allowed; a generic sandbox, coding loop, scheduler,
model service, or unified Web Console is not. Real provider credentials and
real-provider completion are explicitly outside this Work Item.

### Publication and stop boundary

After Path B, all local checks, fresh/restart workspace preflight,
converter/replay checks, and secret scans pass, this Decision requires one
non-force Draft checkpoint update of the existing branch and PR #78 with
`RUNTIME_PROOF_PENDING`, followed by successful exact-head Actions. Only then
may the single disposable provider-free runtime proof run. Evidence comments
may be posted on Draft PR #78 and Issue #85. No second branch or PR may be
created. PR #78 must remain Draft and `rework-required`. Mark-ready, merge, auto-merge,
history rewrite, direct main push, real provider credential use, tag, release,
production deployment, and mutation of PR #47 or PR #49 are never authorized.
