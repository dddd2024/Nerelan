# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260818_issue240_sprint_b1_deterministic_ci_closeout_r2_v3",
  "round_id": "round_20260818_issue240_sprint_b1_deterministic_ci_closeout_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260818_issue240_sprint_b1_deterministic_ci_closeout_r2_v2",
  "follows_last_round_id": "round_20260818_issue240_sprint_b1_deterministic_ci_closeout_r2_v2",
  "previous_audit_outcome": "ISSUE240_V2_PARTIAL_CONTENT_REUSABLE_PUBLICATION_NONCOMPLIANT_REQUIRED_PROJECTION_FAILED_AND_FORBIDDEN_AMEND",
  "supersedes_decision_id": "decision_20260818_issue240_sprint_b1_deterministic_ci_closeout_r2_v2",
  "superseded_branch_must_not_execute": "owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v2",
  "workstream_id": "issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
  "source_issue": 240,
  "parent_issue": 233,
  "required_branch": "owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
  "starting_head": "6d513f0bd680dadf0019af1b56c85dc1683cb6b2",
  "activation_base_sha": "6d513f0bd680dadf0019af1b56c85dc1683cb6b2",
  "predecessor_candidate_head": "a15e01e36ddfcf67360c1932f67ad651fa65317b",
  "predecessor_candidate_publication_compliant": false,
  "predecessor_candidate_content_reusable": true,
  "predecessor_reusable_paths": [
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_task3c_v4_repairs.py"
  ],
  "predecessor_nonreusable_paths": [
    "tests/platform_v1/test_merge_intent.py"
  ],
  "canonical_planning_sha": "74bad91c3721045342e83f0ecd1c06e9ae7cf670",
  "authority_worktree": "F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
  "clean_validation_worktree": "F:/reverse-agent-issue240-sprint-b1-clean-validation-v3",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 1,
  "authority_worktree_full_materialization_required": true,
  "sparse_checkout_disable_is_bootstrap_materialization_only": true,
  "repair_scope_exact_paths": [
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_task3c_v4_repairs.py"
  ],
  "accepted_b1_projection_paths": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py"
  ],
  "clean_projection_expected_paths": [
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/test_ci_responsibility.py",
    "tests/test_project_gate.py"
  ],
  "deterministic_platform_v1_deselected_nodeids": [
    "tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_bytes_unchanged_since_commit",
    "tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_commit_precedes_implementation",
    "tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_single_decision_commit_in_range",
    "tests/platform_v1/test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end"
  ],
  "governance_history_nodes_are_nonblocking_in_product_ci": true,
  "installed_opencode_e2e_is_nonblocking_in_b1": true,
  "repository_wide_diagnostic_must_remain_nonblocking": true,
  "test_merge_intent_file_must_remain_canonical_in_clean_projection": true,
  "runtime_behavior_must_not_change": true,
  "trusted_host_runtime_fail_closed_semantics_must_not_weaken": true,
  "opencode_must_not_be_invoked": true,
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-planning-smoke status --short",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v2",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v2",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3);if($b){'ISSUE240_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3'){'ISSUE240_V3_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue240-sprint-b1-clean-validation-v3'){'ISSUE240_V3_PROJECTION_WORKTREE_ALREADY_EXISTS';exit 23};'ISSUE240_V3_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3 F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3 origin/owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
    "git -C F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD 6d513f0bd680dadf0019af1b56c85dc1683cb6b2",
    "powershell -NoProfile -Command \"$r='F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3';$req=@('pyproject.toml','.github/workflows/ci.yml','.github/workflows/state-gate.yml','tests/test_ci_responsibility.py','tests/test_project_gate.py','tests/platform_v1/test_merge_intent.py','tests/platform_v1/test_task3c_v4_repairs.py','tests/platform_v1/test_task3c_v6_production_relay.py','project_state/decision_packet.md');foreach($p in $req){if(-not (Test-Path -LiteralPath (Join-Path $r $p))){Write-Output ('MISSING:'+$p);exit 28}};$d=@(git -C $r diff HEAD --name-status);if($d.Count -ne 0){$d|Select-Object -First 20;exit 29};$s=@(git -C $r ls-files -v | Where-Object { $_ -match '^S ' });if($s.Count -ne 0){$s|Select-Object -First 20;exit 30};'ISSUE240_V3_FULL_WORKTREE_MATERIALIZED'\"",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue240v3.import_reusable_predecessor_content",
      "command": "git checkout a15e01e36ddfcf67360c1932f67ad651fa65317b -- .github/workflows/ci.yml tests/test_ci_responsibility.py tests/platform_v1/test_task3c_v4_repairs.py",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.status_after_import",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_create",
      "command": "git worktree add --detach F:/reverse-agent-issue240-sprint-b1-clean-validation-v3 74bad91c3721045342e83f0ecd1c06e9ae7cf670",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_sparse_disable",
      "command": "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v3 sparse-checkout disable",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_materialization_verify",
      "command": "powershell -NoProfile -Command \"$r='F:/reverse-agent-issue240-sprint-b1-clean-validation-v3';$req=@('pyproject.toml','.github/workflows/ci.yml','.github/workflows/state-gate.yml','tests/test_project_gate.py','tests/platform_v1/test_merge_intent.py','tests/platform_v1/test_task3c_v4_repairs.py','project_state/decision_packet.md');foreach($p in $req){if(-not (Test-Path -LiteralPath (Join-Path $r $p))){exit 31}};$d=@(git -C $r diff HEAD --name-status);if($d.Count -ne 0){exit 32};$s=@(git -C $r ls-files -v | Where-Object { $_ -match '^S ' });if($s.Count -ne 0){exit 33};'ISSUE240_V3_PROJECTION_FULLY_MATERIALIZED'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_overlay_b1",
      "command": "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v3 checkout b21ce5b2b1dad0b339172ed34567b65c3e3f36bb -- .github/workflows/state-gate.yml .github/workflows/ci.yml tests/test_project_gate.py tests/test_ci_responsibility.py",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_copy_v3_content",
      "command": "powershell -NoProfile -Command \"$src='F:/reverse-agent-issue240-sprint-b1-deterministic-ci-closeout-r2-v3';$dst='F:/reverse-agent-issue240-sprint-b1-clean-validation-v3';$paths=@('.github/workflows/ci.yml','tests/test_ci_responsibility.py','tests/platform_v1/test_task3c_v4_repairs.py');foreach($p in $paths){Copy-Item -LiteralPath (Join-Path $src $p) -Destination (Join-Path $dst $p) -Force};git -C $dst add -- $paths\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_exact_paths",
      "command": "powershell -NoProfile -Command \"$r='F:/reverse-agent-issue240-sprint-b1-clean-validation-v3';$expected=@('.github/workflows/ci.yml','.github/workflows/state-gate.yml','tests/platform_v1/test_task3c_v4_repairs.py','tests/test_ci_responsibility.py','tests/test_project_gate.py')|Sort-Object;$actual=@(git -C $r diff --cached --name-only)|Sort-Object;if(Compare-Object $expected $actual){$actual;exit 34};'ISSUE240_V3_EXACT_FIVE_FILE_PROJECTION'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_diff_check",
      "command": "git -C F:/reverse-agent-issue240-sprint-b1-clean-validation-v3 diff --cached --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_trusted_host_fixture",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue240-sprint-b1-clean-validation-v3'; python -m pytest tests/platform_v1/test_task3c_v4_repairs.py::TestTaskApiApiKeyWiring::test_trusted_host_http_handler_receives_lease_provider -q\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_platform_v1_blocking",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue240-sprint-b1-clean-validation-v3'; python -m pytest tests/platform_v1 -q --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_bytes_unchanged_since_commit --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_decision_commit_precedes_implementation --deselect=tests/platform_v1/test_merge_intent.py::TestDecisionImmutability::test_single_decision_commit_in_range --deselect=tests/platform_v1/test_task3c_v6_production_relay.py::TestCombinedTrustedHostInstalledOpenCodeE2E::test_real_task_api_opencode_relay_fake_provider_end_to_end\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.projection_b1_focused",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue240-sprint-b1-clean-validation-v3'; python -m pytest tests/test_project_gate.py tests/test_ci_responsibility.py -q\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.governance_regressions",
      "command": "python -m pytest tests/test_control_plane_transition.py tests/test_repository_hygiene.py tests/test_project_state.py tests/test_decision_preflight.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.stage_exact_scope",
      "command": "git add .github/workflows/ci.yml tests/test_ci_responsibility.py tests/platform_v1/test_task3c_v4_repairs.py",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_test_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.staged_diff_check",
      "command": "git diff --cached --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.commit_recovery",
      "command": "git commit -m \"Reclassify B1 governance history checks\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue240v3.head_after_commit",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue240v3.push_branch",
      "command": "git push origin owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue240v3.remote_tracking_head",
      "command": "git rev-parse origin/owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue240v3.status_final",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    }
  ],
  "allowed_mutated_paths": [
    ".github/workflows/ci.yml",
    "tests/test_ci_responsibility.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "pyproject.toml",
    "reverse_agent/**",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "pyproject.toml",
    "reverse_agent/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "opencode_invocation",
    "model_api_invocation",
    "provider_network_call",
    "real_user_credential_file_discovery",
    "real_user_credential_file_read",
    "live_connection_probe",
    "credential_relay_lease",
    "task_execute",
    "product_setup_mutation",
    "real_task_store_access",
    "dependency_install",
    "package_lock_mutation",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "tag_or_release",
    "direct_push_main"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git push origin owner/issue240-sprint-b1-deterministic-ci-closeout-r2-v3"
    ],
    "ci_network_exceptions": []
  }
}
```
