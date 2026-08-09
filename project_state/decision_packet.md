# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_foundation_sanitized_integration_v1",
  "round_id": "round_20260809_governance_v2_foundation_sanitized_integration_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "previous_audit_outcome": "GOVERNANCE_V2_FOUNDATION_V3_EXACT_HEAD_STATICALLY_ACCEPTED_SANITIZED_INTEGRATION_REQUIRED",
  "workstream_id": "governance-v2-foundation-sanitized-integration-v1",
  "source_issue": 153,
  "parent_issue": 148,
  "required_branch": "owner/governance-v2-foundation-integration-authority-v1",
  "starting_head": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "activation_base_sha": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "accepted_product_source_branch": "owner/governance-v2-foundation-v1",
  "accepted_product_source_head": "41733d9f0cedfbdf862672a584268a72c56138cf",
  "sanitized_target_branch": "owner/governance-v2-foundation-sanitized-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": true,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin owner/repository-modernization-v2-planning",
    "git fetch origin owner/governance-v2-foundation-v1",
    "git fetch origin owner/governance-v2-foundation-integration-authority-v1",
    "git show origin/owner/governance-v2-foundation-integration-authority-v1:project_state/decision_packet.md",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-foundation-v1",
    "git rev-parse origin/owner/governance-v2-foundation-integration-authority-v1",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "observation.git_status",
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
      "command_id": "observation.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.planning_head",
      "command": "git rev-parse origin/owner/repository-modernization-v2-planning",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.source_head",
      "command": "git rev-parse origin/owner/governance-v2-foundation-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.sanitized_remote_absent",
      "command": "git ls-remote --heads origin owner/governance-v2-foundation-sanitized-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "evidence.export_product_patch",
      "command": "git diff --binary 7e068aac0a4142e611a5d5b825353db31efd2cb7 41733d9f0cedfbdf862672a584268a72c56138cf -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/state-gate.yml .gitignore AGENTS.md reverse_agent/control_plane/legacy_adapter.py reverse_agent/control_plane/path_a.py reverse_agent/control_plane/worktree_state.py reverse_agent/project_gate.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py > issue153_sanitized_product.patch",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["evidence_export"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["issue153_sanitized_product.patch"]
    },
    {
      "command_id": "evidence.product_patch_sha256",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'issue153_sanitized_product.patch').Hash.ToLower()\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.create_sanitized_worktree",
      "command": "git worktree add -b owner/governance-v2-foundation-sanitized-v1 F:\\reverse-agent-governance-v2-sanitized-20260809 7e068aac0a4142e611a5d5b825353db31efd2cb7",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create", "branch_create"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.apply_product_patch",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 apply F:\\reverse-agent-governance-v2-integration-authority-20260809\\issue153_sanitized_product.patch",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "evidence.export_validation_patch",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 diff --binary 7e068aac0a4142e611a5d5b825353db31efd2cb7 -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/state-gate.yml .gitignore AGENTS.md reverse_agent/control_plane/legacy_adapter.py reverse_agent/control_plane/path_a.py reverse_agent/control_plane/worktree_state.py reverse_agent/project_gate.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py > issue153_sanitized_validation.patch",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["evidence_export"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["issue153_sanitized_validation.patch"]
    },
    {
      "command_id": "evidence.validation_patch_sha256",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'issue153_sanitized_validation.patch').Hash.ToLower()\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.sanitized_governance_foundation",
      "command": "python -m pytest tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_planning_and_github_adapters.py tests/test_project_gate.py tests/test_minimal_integration_baseline_docs.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "working_directory": "F:\\reverse-agent-governance-v2-sanitized-20260809",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.sanitized_diff_check",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.sanitized_paths",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 diff --name-only 7e068aac0a4142e611a5d5b825353db31efd2cb7",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.stage_exact_product_paths",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 add .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/state-gate.yml .gitignore AGENTS.md reverse_agent/control_plane/legacy_adapter.py reverse_agent/control_plane/path_a.py reverse_agent/control_plane/worktree_state.py reverse_agent/project_gate.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_staging"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.cached_paths",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 diff --cached --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.commit_sanitized",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 commit -m \"governance: integrate modernization v2 foundation\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.sanitized_parent",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 rev-parse HEAD^",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.sanitized_commit_paths",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 show --name-only --format= HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_sanitized_branch",
      "command": "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 push origin owner/governance-v2-foundation-sanitized-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "issue153_sanitized_product.patch",
    "issue153_sanitized_validation.patch",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/workflows/state-gate.yml",
    ".gitignore",
    "AGENTS.md",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/**",
    "docs/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/actions/**",
    ".github/workflows/ci.yml",
    ".github/CODEOWNERS",
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/**",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/orchestrator_context.py",
    "reverse_agent/orchestrator_console_schema.py",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "cherry_pick",
    "reset_hard",
    "git_clean",
    "stash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "create_pr",
    "pr_creation",
    "draft_pr_creation",
    "pr_body_update",
    "dependency_change",
    "provider_configuration_mutation",
    "source_repair"
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
      "git fetch origin owner/repository-modernization-v2-planning",
      "git fetch origin owner/governance-v2-foundation-v1",
      "git fetch origin owner/governance-v2-foundation-integration-authority-v1",
      "git ls-remote --heads origin owner/governance-v2-foundation-sanitized-v1",
      "git -C F:\\reverse-agent-governance-v2-sanitized-20260809 push origin owner/governance-v2-foundation-sanitized-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    ".github/workflows/state-gate.yml",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".github/ISSUE_TEMPLATE/**", "minimum_risk": "R2"},
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/project_gate.py", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R1"}
  ]
}
```

## Goal

Create one sanitized product commit whose parent is exactly the Modernization planning head `7e068aac0a4142e611a5d5b825353db31efd2cb7` and whose product tree delta is byte-for-byte equivalent to the accepted Governance V2 Foundation product delta at `41733d9f0cedfbdf862672a584268a72c56138cf`, excluding all temporary `project_state` authority history.

This is an integration/transplant operation only. No source repair, refactor, compatibility patch, test modification, or authority change is permitted.

Required invariant:

```text
planning@7e068aac...
  -> exactly one sanitized product commit
  -> owner/governance-v2-foundation-sanitized-v1

source product patch SHA-256 == sanitized worktree patch SHA-256
project_state/** in sanitized commit == 0
```

The local Agent must stop after the normal push. Owner will independently compare the sanitized branch to the accepted source product delta and will create any Draft PR/merge only after that audit.

Success token:

`GOVERNANCE_V2_FOUNDATION_SANITIZED_BRANCH_PUSHED_FOR_OWNER_AUDIT`

Failure token:

`GOVERNANCE_V2_FOUNDATION_SANITIZED_INTEGRATION_STOPPED_WITH_EVIDENCE`
