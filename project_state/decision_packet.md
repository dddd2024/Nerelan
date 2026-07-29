# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260729_unattended_gate2_owner_audit_rework_v3","round_id":"round_20260729_unattended_gate2_owner_audit_rework_v3","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260729_unattended_gate2_regression_reconciliation_v2",
  "follows_last_round_id": "round_20260729_unattended_gate2_regression_reconciliation_v2",
  "previous_audit_outcome": "OWNER_AUDIT_REWORK_REQUIRED",
  "workstream_id": "unattended-gate2-owner-audit-rework-v3",
  "source_issue": 79,
  "predecessor_issue": 77,
  "parent_plan": 74,
  "active_pr": 78,
  "required_branch": "codex/unattended-base-platform-v0",
  "starting_head": "22c37c5050891cd10c868de8047dd948d0c89220",
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
    {"command_id":"test.unattended_unit","command":"python -m pytest tests/unattended/unit -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.unattended_integration","command":"python -m pytest tests/unattended/integration -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.compose_config","command":"docker compose -f deploy/unattended/compose.yaml config --quiet","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_configuration_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.doctor","command":"python -m reverse_agent.unattended.cli doctor","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_health_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"test.full_regression","command":"python -m pytest -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check 2aacf42dbab7f283454908da861b6ef44990f1d5..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_fresh","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue79-gate2 -f deploy/unattended/compose.yaml up -d --wait","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.gate2_first","command":"wsl.exe -d Ubuntu -- python -m reverse_agent.unattended.cli gate2-probe","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_down_retain","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue79-gate2 -f deploy/unattended/compose.yaml down","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_restart","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue79-gate2 -f deploy/unattended/compose.yaml up -d --wait","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.gate2_second","command":"wsl.exe -d Ubuntu -- python -m reverse_agent.unattended.cli gate2-probe","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["component_compatibility_validation","network_access"],"network_access":true,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"probe.compose_cleanup","command":"wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue79-gate2 -f deploy/unattended/compose.yaml down -v","phase":"probe","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["container_runtime"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push -u origin codex/unattended-base-platform-v0","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.update_draft_pr","command":"gh pr edit 78 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_update","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue79","command":"gh issue comment 79 --repo dddd2024/reverse-agent --body-file ISSUE79_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_issue77","command":"gh issue comment 77 --repo dddd2024/reverse-agent --body-file ISSUE77_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["issue_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.comment_draft_pr","command":"gh pr comment 78 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_comment","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observation.exact_head_checks","command":"gh pr checks 78 --repo dddd2024/reverse-agent --watch","phase":"observation","required":false,"expected_exit_codes":[0],"execution_surface":"remote_observation","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
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
    ".github/workflows/ci.yml"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "pyproject.toml",
    ".gitignore",
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
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "wsl.exe -d Ubuntu -- docker compose -p reverse-agent-issue79-gate2 -f deploy/unattended/compose.yaml up -d --wait",
      "wsl.exe -d Ubuntu -- python -m reverse_agent.unattended.cli gate2-probe",
      "git push -u origin codex/unattended-base-platform-v0",
      "gh pr edit 78 --repo dddd2024/reverse-agent --body-file PR_BODY_TEMP_PATH",
      "gh issue comment 79 --repo dddd2024/reverse-agent --body-file ISSUE79_COMMENT_TEMP_PATH",
      "gh issue comment 77 --repo dddd2024/reverse-agent --body-file ISSUE77_COMMENT_TEMP_PATH",
      "gh pr comment 78 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH"
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
    ".github/workflows/ci.yml"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":"deploy/unattended/**","minimum_risk":"R2"},
    {"pattern":"reverse_agent/unattended/**","minimum_risk":"R2"},
    {"pattern":"tests/unattended/**","minimum_risk":"R2"},
    {"pattern":"docs/unattended/**","minimum_risk":"R2"},
    {"pattern":".github/workflows/ci.yml","minimum_risk":"R2"}
  ],
  "scope_policy": {
    "scope": "unattended-gate2-owner-audit-rework-v3",
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
    "workspace_boundary_failure",
    "openhands_lifecycle_contract_failure",
    "contract_alignment_failure",
    "temporal_bootstrap_failure",
    "compose_restart_idempotence_failure",
    "component_lock_validation_failure",
    "full_suite_ci_failure",
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

Authorize only Issue #79 Owner-audit rework F1-F8 on the existing exact-head
Draft PR #78: enforce the workspace submission boundary, reconcile OpenHands
conversation lifecycle, align the six v0 contracts and policy semantics, make
Temporal startup/restart idempotent, bind development ports to loopback,
make the fixed component lock machine-verifiable, and make CI run truthful
full-suite checks.

### Authority and sequencing

This successor Decision is the sole R2 rework authority. It is committed
alone on exact starting head
`22c37c5050891cd10c868de8047dd948d0c89220`. The compiler-generated Command
Plan and successful `PRE_EXECUTION_AUTHORIZED` must be committed separately
before any F1-F8 mutation.

### Product boundary

The existing nine PR commits remain immutable historical inputs. Rework is
limited to `deploy/unattended/**`, `docs/unattended/**`,
`reverse_agent/unattended/**`, `tests/unattended/**`, and the single workflow
`.github/workflows/ci.yml`, plus the Decision and compiler-owned Gate files.
No dependency, audit record, state/decision workflow, mainline landing,
remote verifier, or control-plane file may change. Real provider credentials
and provider/model completion are explicitly outside this Work Item.

### Publication and stop boundary

After Path B, all local checks, and the disposable fresh/restart proof pass,
this Decision permits one non-force update of the existing branch, updates
and evidence comments on Draft PR #78, evidence comments on Issues #79 and
#77, and read-only observation of exact-head Actions. No second branch or PR
may be created. PR #78 must remain Draft. Mark-ready, merge, auto-merge,
history rewrite, direct main push, real provider credential use, tag, release,
production deployment, and mutation of PR #47 or PR #49 are never authorized.
