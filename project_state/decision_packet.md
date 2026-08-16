# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260816_issue211_issue210_product_validation_r2_v1",
  "round_id": "round_20260816_issue211_issue210_product_validation_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue210_durable_product_setup_r2_v1",
  "follows_last_round_id": "round_20260816_issue210_durable_product_setup_r2_v1",
  "previous_audit_outcome": "ISSUE210_V1_PRODUCT_PLAUSIBLE_BUT_REQUIRED_FULL_SUITE_INVALIDATED_BY_AUTHORITY_WORKTREE_GOVERNANCE_STATE",
  "workstream_id": "issue211-issue210-product-validation-r2-v1",
  "source_issue": 211,
  "parent_issue": 210,
  "required_branch": "owner/issue211-issue210-product-validation-r2-v1",
  "starting_head": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "activation_base_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "canonical_planning_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "immutable_product_candidate_sha": "e5e656c86bfcb2c8f63fe4857394b742b0a183b3",
  "immutable_product_candidate_branch": "owner/issue210-durable-product-setup-product-only-v1",
  "original_implementation_sha": "5fd87fb589252e38712bb26e922f76ef4daaa499",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": false,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue210-durable-product-setup-product-only-v1",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue211-issue210-product-validation-r2-v1"
    ],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
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
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue210-durable-product-setup-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue211-issue210-product-validation-r2-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue210-durable-product-setup-product-only-v1",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue211-issue210-product-validation-r2-v1",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue211-issue210-product-validation-r2-v1);if($b){'ISSUE211_V1_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue211-issue210-product-validation-r2-v1'){'ISSUE211_V1_AUTHORITY_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue211-product-validation-v1'){'ISSUE211_V1_PRODUCT_WORKTREE_ALREADY_EXISTS';exit 23};'ISSUE211_V1_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue211-issue210-product-validation-r2-v1 F:/reverse-agent-issue211-issue210-product-validation-r2-v1 origin/owner/issue211-issue210-product-validation-r2-v1",
    "Set-Location F:/reverse-agent-issue211-issue210-product-validation-r2-v1",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue211v1.product_worktree_create",
      "command": "git -C F:/reverse-agent-planning-smoke worktree add --detach F:/reverse-agent-issue211-product-validation-v1 e5e656c86bfcb2c8f63fe4857394b742b0a183b3",
      "phase": "validation_setup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_head",
      "command": "git -C F:/reverse-agent-issue211-product-validation-v1 rev-parse HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_status_before",
      "command": "git -C F:/reverse-agent-issue211-product-validation-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_diff_paths",
      "command": "git -C F:/reverse-agent-issue211-product-validation-v1 diff --name-only deed415c7dff3101b18aac6a3ea0cc01fc5eba3c..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_diff_exact",
      "command": "powershell -NoProfile -Command \"$p=@(git -C F:/reverse-agent-issue211-product-validation-v1 diff --name-only deed415c7dff3101b18aac6a3ea0cc01fc5eba3c..HEAD);$e=@('reverse_agent/model_access/store.py','reverse_agent/platform_v1/trusted_host.py','tests/platform_v1/test_trusted_host.py','tests/test_connection_binding.py');if((Compare-Object ($p|Sort-Object) ($e|Sort-Object)).Count -ne 0){$p;exit 31};'ISSUE211_PRODUCT_DIFF_EXACT'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_diff_check",
      "command": "git -C F:/reverse-agent-issue211-product-validation-v1 diff --check deed415c7dff3101b18aac6a3ea0cc01fc5eba3c..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.focused",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue211-product-validation-v1'; python -m pytest tests/test_connection_binding.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_binding_resolver.py -q\"",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.integration",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue211-product-validation-v1'; python -m pytest tests/platform_v1/test_task_service.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task3c_v6_production_relay.py -q\"",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.nonrelay_full",
      "command": "powershell -NoProfile -Command \"Set-Location 'F:/reverse-agent-issue211-product-validation-v1'; python -m pytest tests/platform_v1 -q --ignore=tests/platform_v1/test_credential_relay.py\"",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.product_status_after",
      "command": "git -C F:/reverse-agent-issue211-product-validation-v1 status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue211v1.authority_status_final",
      "command": "git -C F:/reverse-agent-issue211-issue210-product-validation-r2-v1 status --short",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/test_connection_binding.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_binding_resolver.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_merge_intent.py",
    "tests/platform_v1/test_credential_relay.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    ".github/**",
    "docs/**",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "product_mutation",
    "test_mutation",
    "governance_mutation_outside_generated_gates",
    "local_commit",
    "push",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "tag_or_release",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "real_provider_call",
    "real_credential_read",
    "dependency_install"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/gates/**"
  ],
  "runner_managed_artifact_paths": []
}
```

# Goal

Validate immutable product-only candidate `e5e656c86bfcb2c8f63fe4857394b742b0a183b3` without allowing the R2 authority Decision/gate state to alter the governance files seen by the candidate's Platform V1 test suite.

# Separation rule

The authority worktree exists only for transition-gate authorization and generated gate evidence. The detached product validation worktree must remain exactly at `e5e656c...`; its `project_state/**` comes from canonical planning and must not be modified. All pytest commands run only in the detached product validation worktree.

# Acceptance

Success requires all required commands to exit 0, the product validation worktree to be clean before and after testing, and the exact four-path product diff to remain unchanged.

Success terminal:

`ISSUE210_PRODUCT_ONLY_VALIDATION_ACCEPTED`

Failure terminal:

`ISSUE210_PRODUCT_ONLY_VALIDATION_BOUNDED_FAILURE`

On failure, preserve evidence and report the first failing invariant/test set. Do not repair or mutate the product candidate in this round.
