# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_foundation_v3",
  "round_id": "round_20260809_governance_v2_foundation_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_governance_v2_foundation_v2",
  "follows_last_round_id": "round_20260809_governance_v2_foundation_v2",
  "previous_audit_outcome": "V2_EXACT_HEAD_REWORK_REQUIRED_WORKTREE_CLASSIFIER_NOT_WIRED_AND_SENSITIVE_POLICY_INCOMPLETE",
  "workstream_id": "governance-v2-foundation-v3",
  "source_issue": 153,
  "parent_issue": 148,
  "related_issue": 105,
  "required_branch": "owner/governance-v2-foundation-v1",
  "starting_head": "2aeafcbc5b9b314ae4f63394b23f9e7d3b0b8d52",
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
  "repair_attempt_limit": 1,
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
    "git show origin/owner/governance-v2-foundation-v1:project_state/decision_packet.md",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-foundation-v1",
    "git merge --ff-only origin/owner/governance-v2-foundation-v1",
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
      "command_id": "test.governance_foundation_rework",
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
      "command": "git add AGENTS.md reverse_agent/control_plane/worktree_state.py reverse_agent/project_gate.py tests/test_path_a_gate.py tests/test_project_gate.py tests/test_minimal_integration_baseline_docs.py",
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
      "command_id": "mutation.commit_rework",
      "command": "git commit -m \"governance: wire worktree classification into gates\"",
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
      "command": "git diff --check 2aeafcbc5b9b314ae4f63394b23f9e7d3b0b8d52..HEAD",
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
      "command": "git diff --name-only 2aeafcbc5b9b314ae4f63394b23f9e7d3b0b8d52..HEAD",
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
    "AGENTS.md",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py",
    "tests/test_minimal_integration_baseline_docs.py"
  ],
  "reference_paths": [
    ".github/workflows/state-gate.yml",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".gitignore",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "pyproject.toml"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".gitignore",
    "frontend/**",
    "docs/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/**",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/orchestrator_context.py",
    "reverse_agent/orchestrator_console_schema.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
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
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "git fetch origin owner/repository-modernization-v2-planning",
      "git fetch origin owner/governance-v2-foundation-v1",
      "git push origin owner/governance-v2-foundation-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "AGENTS.md",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/project_gate.py", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R1"}
  ]
}
```

## Goal

v3 is a bounded exact-head rework of the accepted v2 direction. It does not redesign Path A.

Owner exact-head static audit accepted the v2 branch topology, branch-neutral immutable snapshot, live Issue/PR authority observation, authority-revision binding, R2/R3 Path-A risk floor, State Gate ordinary-PR routing, narrow runtime ignores, and v2 implementation scope. Two blocking defects remain:

1. `reverse_agent/control_plane/worktree_state.py` exists and is unit-tested, but v2 does not wire it into any real startup/pre-publication gate path. The Foundation requirement is machine-enforced classification, not a library plus prompt/documentation convention.
2. the classifier's sensitive-path patterns are narrower than the already-accepted Path-A R3 policy. Sensitive-looking untracked paths such as `*secret*`, `*.key`, `*.so`, and `*.dylib` can be classified as `UNKNOWN_UNTRACKED` instead of immediate `UNAUTHORIZED_TRACKED_OR_SENSITIVE`.

Required rework:

- wire the deterministic classifier into the existing `startup-snapshot` / startup dirty-state path so `KNOWN_RUNTIME_SCRATCH` and generated Gate artifacts do not hard-stop bootstrap, while `UNAUTHORIZED_TRACKED_OR_SENSITIVE` still does;
- wire the same classifier or one shared helper into the existing pre-publication/worktree validation surface, or expose one repository-owned deterministic `project_gate` pre-publication command that consumes trusted authorized paths and blocks `UNKNOWN_UNTRACKED` plus `UNAUTHORIZED_TRACKED_OR_SENSITIVE` before staging/push;
- do not encode either behavior only in AGENTS/prompt text;
- align worktree sensitive patterns with the accepted Path-A R3 categories at minimum for secret/credential names, `.env*`, private-key formats (`.pem`, `.key`, `.p12`, `.pfx`) and native binaries (`.exe`, `.dll`, `.so`, `.dylib`), case-insensitively;
- add integration-level regressions proving the real gate path, not only direct calls to `classify_worktree_path`;
- preserve the v2 branch-neutral Path-A behavior unchanged.

No `.github`, template, Path-A verifier, legacy router, runtime product, dependency, provider/model, #151, or #146 changes are authorized in v3.

Terminal success:

`GOVERNANCE_V2_FOUNDATION_V3_READY_FOR_OWNER_EXACT_HEAD_AUDIT`

Terminal failure:

`GOVERNANCE_V2_FOUNDATION_V3_STOPPED_WITH_EVIDENCE`
