# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260810_issue176_task3c_narrow_relay_r2_v1",
  "round_id": "round_20260810_issue176_task3c_narrow_relay_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
  "follows_last_round_id": "round_20260808_pr134_frontend_opencode_devup_landing_v1",
  "previous_audit_outcome": "TASK3C_LITELLM_CAPABILITY_ACCEPTED_DOCKER_BOUNDARY_REJECTED_NON_DOCKER_IMPLEMENTATION_NEXT",
  "workstream_id": "issue176-task3c-narrow-relay-r2-v1",
  "source_issue": 176,
  "parent_issue": 172,
  "required_branch": "owner/issue176-task3c-narrow-relay-r2-v1",
  "starting_head": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
  "activation_base_sha": "a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
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
  "exact_head_workflow_observation_allowed": true,
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
  "opencode_invocation_allowed": true,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin owner/repository-modernization-v2-planning",
    "git fetch origin owner/issue176-task3c-narrow-relay-r2-v1",
    "git branch --list owner/issue176-task3c-narrow-relay-r2-v1",
    "git switch -c owner/issue176-task3c-narrow-relay-r2-v1 --track origin/owner/issue176-task3c-narrow-relay-r2-v1",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git merge-base HEAD a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
    "git show HEAD:project_state/decision_packet.md",
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
      "required_evidence_source": "local_command_evidence"
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
      "command_id": "observation.merge_base",
      "command": "git merge-base HEAD a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.task3c_focused",
      "command": "python -m pytest tests/test_model_access.py tests/platform_v1 tests/test_dev_up_contract.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.full_regression",
      "command": "python -m pytest -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.fake_provider_opencode_smoke",
      "command": "python -m pytest tests/platform_v1/test_task3c_opencode_fake_provider_smoke.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "known_local_opencode_invocation", "loopback_fixture_network"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
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
      "command_id": "validation.path_list",
      "command": "git diff --name-only a5b9b1dbc246bc95b9140a0eed0a08c1a598b7d2..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.stage_allowed",
      "command": "git add -- reverse_agent/model_access reverse_agent/platform_v1 dev-up.ps1 tests/test_model_access.py tests/test_dev_up_contract.py tests/platform_v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["stage_allowed_paths"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "publication.commit_product",
      "command": "git commit -m \"feat: add execution-scoped provider credential relay\"",
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
      "command_id": "publication.push_branch",
      "command": "git push origin owner/issue176-task3c-narrow-relay-r2-v1",
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
  "allowed_source_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "dev-up.ps1",
    "tests/test_model_access.py",
    "tests/test_dev_up_contract.py",
    "tests/platform_v1/**"
  ],
  "allowed_mutated_paths": [
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "dev-up.ps1",
    "tests/test_model_access.py",
    "tests/test_dev_up_contract.py",
    "tests/platform_v1/**",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/binding_resolver.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_model_access.py",
    "tests/test_dev_up_contract.py",
    "tests/platform_v1/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/**",
    "frontend/**",
    "docs/**",
    "dev-down.ps1",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "real_credential_access",
    "credential_publication",
    "real_provider_call",
    "real_model_call",
    "package_installation",
    "dependency_change",
    "docker_or_container_gateway",
    "new_gateway_product_research",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "unbounded_network_access"
  ]
}
```

## Owner implementation boundary

This Decision authorizes exactly GitHub Issue #176 after local transition preflight reaches `PRE_EXECUTION_AUTHORIZED`.

The implementation is a product feature, not a generic gateway project. It must keep the long-lived provider key out of OpenCode process environment, argv, config/auth storage, prompt, TaskStore, evidence and logs. The OpenCode-visible value is only a per-execution high-entropy lease scoped to the frozen Binding model and exact inference route.

The trusted host may use fake provider secrets and a fake loopback provider for tests. It may invoke the already-installed OpenCode binary only for the exact fake-provider smoke test named in `allowed_commands`; no real provider/model request is authorized.

The current Docker-hosted LiteLLM path is not authorized because #175 proved the same Windows user can recover the container's fake provider master through Docker control. No other gateway candidate research is authorized.

For an existing secret-bearing Connection, a change to `provider`, `base_url`, or `auth_method` must fail unless the same trusted update provides a replacement secret or explicitly clears the secret. `name`/`enabled`-only changes may preserve it.

The implementation does not claim resistance to arbitrary same-user OS process-memory debugging/scraping. That stronger host-compromise threat remains outside Task 3C.

If the installed OpenCode fake-provider smoke uses an inference route other than `/chat/completions`, stop and return exact evidence. Do not broaden the relay route without a new Owner Decision.
