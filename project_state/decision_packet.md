# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_foundation_v1",
  "round_id": "round_20260809_governance_v2_foundation_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "previous_audit_outcome": "OWNER_AUDIT_GOVERNANCE_FALSE_NEGATIVES_BLOCKING_MODERNIZATION",
  "workstream_id": "governance-v2-foundation-v1",
  "source_issue": 153,
  "parent_issue": 148,
  "related_issue": 105,
  "historical_reference_pr": 49,
  "historical_reference_head": "40400440e257e0d0a4aa6cabae8672bff937cde4",
  "required_branch": "owner/governance-v2-foundation-v1",
  "starting_head": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "activation_base_sha": "7e068aac0a4142e611a5d5b825353db31efd2cb7",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
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
  "repair_attempt_limit": 2,
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
    "git fetch origin codex/path-a-r1-state-gate-cutover-v1",
    "git show origin/owner/governance-v2-foundation-v1:project_state/decision_packet.md",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-foundation-v1",
    "git rev-parse origin/codex/path-a-r1-state-gate-cutover-v1",
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
      "command_id": "observation.historical_path_a_head",
      "command": "git rev-parse origin/codex/path-a-r1-state-gate-cutover-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.historical_scope",
      "command": "git diff --name-only 61570724495aa7053eba78bd2e34d8bda22f6407..40400440e257e0d0a4aa6cabae8672bff937cde4",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.governance_foundation",
      "command": "python -m pytest tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_planning_and_github_adapters.py tests/test_project_gate.py tests/test_minimal_integration_baseline_docs.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
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
      "command_id": "validation.working_tree_paths",
      "command": "git diff --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.stage_exact_paths",
      "command": "git add .github/workflows/state-gate.yml .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .gitignore AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/control_plane/legacy_adapter.py reverse_agent/control_plane/worktree_state.py reverse_agent/project_gate.py tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_minimal_integration_baseline_docs.py",
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
      "command_id": "mutation.commit_foundation",
      "command": "git commit -m \"governance: establish modernization v2 foundation\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.committed_diff_check",
      "command": "git diff --check 7e068aac0a4142e611a5d5b825353db31efd2cb7..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.committed_paths",
      "command": "git diff --name-only 7e068aac0a4142e611a5d5b825353db31efd2cb7..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/governance-v2-foundation-v1",
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
    ".github/workflows/state-gate.yml",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".gitignore",
    "AGENTS.md",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_path_a_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "tests/test_minimal_integration_baseline_docs.py"
  ],
  "reference_paths": [
    "README.md",
    "pyproject.toml",
    ".github/workflows/ci.yml",
    "tests/test_planning_and_github_adapters.py",
    "reverse_agent/platform_v1/task_service.py",
    "project_state/schemas/**"
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
    "issue151_product_mutation",
    "pr146_mutation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git fetch origin owner/repository-modernization-v2-planning",
      "git fetch origin owner/governance-v2-foundation-v1",
      "git fetch origin codex/path-a-r1-state-gate-cutover-v1",
      "git push origin owner/governance-v2-foundation-v1"
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
  ],
  "runner_managed_artifact_paths": [
    "project_state/gates/evidence/**",
    "project_state/gates/execution_log.json"
  ],
  "follows_last_decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
  "follows_last_round_id": "round_20260808_pr134_frontend_opencode_devup_landing_v1"
}
```

## Goal

Implement the minimum Governance V2 foundation required to unblock Modernization V2, using historical PR #49 / Issue #105 as the mandatory reuse source rather than building a second control plane.

Required outcomes:

1. restore `path_a_r1` routing for ordinary R1 PRs so an unrelated active Path-B Decision cannot hijack them;
2. adapt the R1 immutable snapshot from a hard-coded `main` base to an explicit `integration_base_ref + base_sha` contract, allowing exact owner-approved planning branches while retaining exact merge-base/head binding;
3. introduce deterministic worktree-state classification so known runtime scratch (`task_workspaces/**`, `.platform_v1_runtime/**`) is non-authoritative/non-staged but does not hard-stop bootstrap merely for existing, while unknown untracked content is read-only classifiable and remains blocking before publication unless resolved;
4. narrowly ignore the two known managed runtime scratch roots;
5. preserve R2/R3 path-risk floors, live authority re-observation, rename/previous-path checks, security-path case normalization and fail-closed semantics from PR #49;
6. do not add a permanent compatibility fallback for old snapshot schemas; old Work Items without `integration_base_ref` are historical and need a fresh approved Work Item.

## Reuse and implementation policy

- First fetch and inspect historical PR #49 exact head `40400440e257e0d0a4aa6cabae8672bff937cde4`.
- Reuse only behavior still correct against current planning base `7e068aac0a4142e611a5d5b825353db31efd2cb7`.
- Do not merge/cherry-pick PR #49 wholesale.
- Keep the worktree classifier in `reverse_agent/control_plane/worktree_state.py` so runtime-scratch classification does not become ad-hoc prompt logic.
- `AGENTS.md` and the R1 Issue template must describe the same branch-neutral snapshot contract as the machine verifier.
- State Gate must route ordinary PRs to Path A and Decision-bound R2/R3 surfaces to Path B without PR-number-specific special cases.

## Test and repair policy

This round permits at most two bounded repair cycles after deterministic test failures, provided every edit remains inside `allowed_mutated_paths`. Test failure alone is not authority drift. Stop immediately instead on branch/base drift, forbidden-path mutation, sensitive/credential/provider/dependency scope expansion, history rewrite, or remote publication mismatch.

The local Agent must not touch `F:\reverse-agent-issue151-rework-20260809`; that dirty #151 product diff remains frozen for recovery after this foundation is accepted.

## Publication boundary

After tests pass, commit exactly the bounded governance implementation and normal-push only `owner/governance-v2-foundation-v1`. Do not create a PR, mark ready, merge, modify planning/main/#151/#146, or run model/OpenCode/Codex/OpenHands actions. Owner will independently audit the exact pushed head and create a sanitized integration branch/PR that excludes temporary `project_state` authority artifacts.

Terminal success token:

`GOVERNANCE_V2_FOUNDATION_READY_FOR_OWNER_EXACT_HEAD_AUDIT`

Failure token:

`GOVERNANCE_V2_FOUNDATION_STOPPED_WITH_EVIDENCE`
