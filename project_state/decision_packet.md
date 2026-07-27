# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260726_path_a_r1_state_gate_cutover_rework_v3","round_id":"round_20260726_path_a_r1_state_gate_cutover_rework_v3","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260726_path_a_r1_state_gate_cutover_rework_v2",
  "follows_last_round_id": "round_20260726_path_a_r1_state_gate_cutover_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED_V2_SEMANTIC_ACCEPTANCE_WITHHELD",
  "acceptance_target": "PATH_A_R1_GATE_RISK_FLOOR_REWORK_V3_ACCEPTED",
  "workstream_id": "path-a-r1-state-gate-cutover-rework-v3",
  "source_issue": 51,
  "predecessor_issue": 50,
  "active_pr": 49,
  "program_issue": 45,
  "blocked_source_issue": 46,
  "blocked_pull_request": 47,
  "blocked_pull_request_frozen_head": "6e096b11df43bc33c8b21dfba08cfd07549352d9",
  "frozen_v1_head": "f0bf2e585f2b578d5acdb8cd521bf1f960d9988c",
  "frozen_v2_head": "7a238bbdd0bdc77d90715819bb01e355b2af9ca1",
  "accepted_v2_workflow_runs": {
    "CI": 30205750461,
    "State Gate": 30205750471,
    "Decision Preflight": 30205750474
  },
  "starting_main": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "starting_head": "7a238bbdd0bdc77d90715819bb01e355b2af9ca1",
  "activation_base_sha": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "required_branch": "codex/path-a-r1-state-gate-cutover-v1",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "rebase_allowed": false,
  "squash_allowed": false,
  "force_push_allowed": false,
  "direct_push_to_main_allowed": false,
  "tag_or_release_allowed": false,
  "stop_after_exact_head_ci": true,
  "stop_before_independent_audit": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json"
  ],
  "bootstrap_exception_commands": [
    "gate.startup_snapshot",
    "status.git_status",
    "gate.command_plan",
    "gate.transition_lint",
    "gate.pre_execution"
  ],
  "allowed_commands": [
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"],
      "produced_artifacts": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "status.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "status.changed_paths",
      "command": "git diff --name-only origin/main...HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "test.path_a_gate",
      "command": "python -m pytest tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_planning_and_github_adapters.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.ci_workflow",
      "command": "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py tests/test_control_plane_transition.py tests/test_architecture_contracts.py tests/test_risk_classifier.py tests/test_development_graph.py tests/test_trust_authorization_adapter.py tests/test_planning_and_github_adapters.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.state_gate_workflow",
      "command": "python -m pytest tests/test_project_gate.py tests/test_project_reports.py tests/test_project_jobs.py tests/test_post_final_evidence_sync.py tests/test_decision_preflight.py tests/test_project_state.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
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
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push -u origin codex/path-a-r1-state-gate-cutover-v1",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.update_pr_body",
      "command": "gh pr edit 49 --body-file PR_BODY_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_edit", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/CODEOWNERS",
    ".github/actions/**",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/github_adapter.py",
    "reverse_agent/base_platform/**",
    "tests/base_platform/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_decision_preflight.py",
    ".github/workflows/decision-preflight.yml"
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
    "docs/**",
    ".github/ISSUE_TEMPLATE/**",
    ".github/workflows/decision-preflight.yml",
    ".codex-skills/**",
    "reverse_agent/base_platform/**",
    "tests/base_platform/**",
    "tests/test_decision_preflight.py",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifactindex.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "direct push to main",
    "merge",
    "mark_ready",
    "mark-ready",
    "auto_merge",
    "automatic_merge",
    "force_push",
    "force push",
    "rebase",
    "squash",
    "history_rewrite",
    "tag",
    "release",
    "cross_repository_publication",
    "unbounded_network_access",
    "credentials_or_secrets_access",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "workflow_dispatch",
    "destructive",
    "dependency_changes",
    "packaging_changes",
    "web_changes",
    "model_routing_changes",
    "reverse_tool_changes",
    "edit_pr_47",
    "modify_pr_47_branch",
    "copy_m1_implementation",
    "create_replacement_m1_work_item",
    "execute_issue_shell_commands",
    "trust_issue_or_pr_comments_as_authority",
    "new_gate_artifact_family"
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
    "mark_ready_allowed": false,
    "auto_merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "squash_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push -u origin codex/path-a-r1-state-gate-cutover-v1",
      "gh pr view --repo dddd2024/reverse-agent",
      "gh pr checks --repo dddd2024/reverse-agent",
      "gh pr edit 49 --body-file PR_BODY_TEMP_PATH"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_paths": [
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py",
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": ".github/actions/**", "minimum_risk": "R2"},
    {"pattern": ".github/ISSUE_TEMPLATE/**", "minimum_risk": "R2"},
    {"pattern": ".github/CODEOWNERS", "minimum_risk": "R2"},
    {"pattern": ".codex-skills/**", "minimum_risk": "R2"},
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/project_gate.py", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/decision_preflight.py", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/github_adapter.py", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"},
    {"pattern": "**/*credential*", "minimum_risk": "R3"},
    {"pattern": "**/*secret*", "minimum_risk": "R3"},
    {"pattern": "**/*.exe", "minimum_risk": "R3"},
    {"pattern": "tests/**", "minimum_risk": "R1"}
  ],
  "scope_policy": {
    "scope": "path_a_r1_repository_risk_floor_and_bounded_scope_rework_v3",
    "three_mutually_exclusive_modes": ["path_a_r1", "transition", "legacy"],
    "allow_workflow_changes": false,
    "allow_router_and_verifier_changes": true,
    "allow_test_additions": true,
    "allow_compiler_owned_gate_outputs": true,
    "allow_dependency_changes": false,
    "allow_documentation_changes": false,
    "allow_base_platform_changes": false,
    "allow_pr47_changes": false,
    "allow_new_branch": false,
    "allow_new_pr": false,
    "allow_existing_pr49_body_update": true,
    "allow_replacement_m1_work_item": false
  },
  "publication_policy": {
    "repository": "dddd2024/reverse-agent",
    "base_branch": "main",
    "head_branch": "codex/path-a-r1-state-gate-cutover-v1",
    "draft_required": true,
    "exact_head_required": true,
    "required_checks": ["CI", "State Gate", "Decision Preflight"],
    "post_exact_head_branch_mutation_allowed": false,
    "independent_audit_required": true
  },
  "stop_conditions": [
    "origin_main_drifted_from_starting_main",
    "transition_lint_failure",
    "preflight_not_authorized",
    "scope_violation_detected",
    "focused_tests_failure",
    "exact_workflow_tests_failure",
    "diff_check_failure",
    "ci_failure_on_exact_head",
    "state_gate_failure_on_exact_head",
    "decision_preflight_failure_on_exact_head",
    "pr47_head_or_body_changed",
    "attempted_mark_ready_or_merge",
    "attempted_force_push_rebase_squash_or_history_rewrite",
    "attempted_direct_push_to_main",
    "attempted_tag_or_release",
    "attempted_replacement_m1_work_item_creation"
  ]
}
```

## DECISION_PACKET

### Goal

Implement the bounded R2 semantic rework described by planning Issue #51 on the
existing PR #49 branch after the frozen v2 head passed exact-head workflows but
failed independent semantic acceptance. Close the ordinary-R1 repository-owned
path-risk-floor, unbounded allowed-path, and equal-timestamp approval ambiguity
gaps without weakening transition or legacy behavior and without copying or
modifying the blocked M1 implementation.

### Authority and binding

- Authority is this APPROVED Path-B Decision, its compiler-generated Command Plan,
  and `PRE_EXECUTION_AUTHORIZED`.
- Planning Issue #51, predecessor Issue #50, and all Issue/PR comments are context
  or evidence only.
- Base is `61570724495aa7053eba78bd2e34d8bda22f6407`.
- Frozen v2 head is `7a238bbdd0bdc77d90715819bb01e355b2af9ca1`.
- Required branch is `codex/path-a-r1-state-gate-cutover-v1`.
- Existing Draft PR #49 is the only publication target; no new branch or PR.
- PR #47 and branch `codex/base-platform-m1-spec-policy-core-v1` are frozen and
  read-only at exact head `6e096b11df43bc33c8b21dfba08cfd07549352d9`.

### Required implementation

1. Define a deterministic repository-owned ordinary-R1 minimum-risk policy and
   reject every observed current or previous path whose floor exceeds R1.
2. Classify governance, workflow, permission, Path-A trust-boundary, Decision,
   Gate, GitHub-authority, dependency, and packaging paths as at least R2.
3. Classify secrets, credentials, private keys, and unknown binary paths as R3.
4. Reject repository-root catch-all allowed-path forms, including normalized
   equivalents of `*`, `**`, `**/*`, `.`, and `./`, while preserving bounded
   directory-prefix patterns and exact files.
5. Reject an observed Issue body edit when its timestamp is equal to or later
   than the effective approval timestamp.
6. Add deterministic negative coverage for current paths, rename/copy previous
   paths, unbounded globs, and equal timestamps; preserve the valid bounded M1,
   transition, and legacy routing behavior.

### Publication boundary

After all exact workflow-equivalent local validation succeeds, push one minimal
corrective commit to the existing branch and update Draft PR #49 metadata. Observe
CI, State Gate, and Decision Preflight on that exact head, then stop for independent
re-audit. Do not create a branch or PR, mark ready, merge, rebase, squash,
force-push, tag, release, modify PR #47, or create a replacement M1 Work Item.
