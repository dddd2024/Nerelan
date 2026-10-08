# Delegated Goal admission canonical reference correction v3

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue118_delegated_goal_admission_r2_v3",
  "round_id": "round_20261008_issue118_delegated_goal_admission_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": [
    "reverse-agent-iteration@v2"
  ]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "ISSUE118_DELEGATED_GOAL_ADMISSION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; explicit controller approval of exact source slice using existing unmerged trusted-host planning base #1093, not an implicit main fallback.; controller approves narrowly adding existing control_store.py activation integration after actual 17 development failures rejected the new capability pair; preserve immutable v1 and failure/spending, same expiry.; separately allocated one metadata activation removes only canonical allowed/reference conflict. Original v2 immutable BLOCKED preflight preserved. Same implementation scope, spending and expiry.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-current-candidate-profile-recovery-r3-20261008",
  "base_sha": "88a383b3d1f75935472b4eb27e4d30aba3ee44eb",
  "activation_base_sha": "88a383b3d1f75935472b4eb27e4d30aba3ee44eb",
  "starting_head": "0117d44a4c4602900587301ef9ff23a59234071d",
  "required_branch": "codex/issue118-delegated-goal-admission-r2-20261008",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": true,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Add exact preauthorized Goal admission to existing trusted delegated windows. Immutable host PolicyAuthority binding may list bounded Goal id/revision/artifact digest/idempotency snapshots for fixed host validation, with approve_goal and validate_task capabilities and cumulative max_tasks. Existing legacy fixed-checker single Goal mode stays valid. Coordinator must admit matching PLANNED Goals, approve and materialize tasks and append delegated-identity receipt atomically in the existing TaskStore transaction, replay without duplicates across restart/concurrent connections, continue unaffected eligible snapshots on isolated denial, and reject drift/revocation/expiry/missing authority or spent allowance. Preserve zero model/provider/GitHub writes and fixed check/path enforcement; do not remove R2/R3 execution rejection, create a new DB/authority schema/Gate, or claim arbitrary coding/merge implemented. Extend only existing store activation capability check to validate the same bounded host manifest and approve_goal/validate_task pairing; arbitrary capabilities, mismatched task budgets and duplicate/invalid snapshots still reject.",
    "reuse": "Existing #1093 trusted PolicyAuthority loader, canonical policy binding, TaskStore SQLite, GoalService, window budgets, append-only operation receipts, task claims and unattended coordinator. No parallel store or framework.",
    "execution_surface_note": "Fresh full exact approved planning-base worktree; Decision-only activation then canonical preflight before edits. Precharged provider-free development/final checks only; owned unique short external test scratch. All earlier Decisions/failures/spending/expiry retained.",
    "completion_boundary": "Exact scoped source and immutable Decision, focused existing+new tests, natural exact-head CI and independent acceptance, Draft against exact planning branch only. Real live host/browser/model/window deployment and mainline landing require separate bounded authority; full unattended/backlog remains open."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_delegated_goal_admission.py",
    "docs/unattended-window-lifecycle.md",
    "reverse_agent/platform_v1/control_store.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_delegated_goal_admission.py",
    "docs/unattended-window-lifecycle.md",
    "reverse_agent/platform_v1/control_store.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "tests/platform_v1/test_autonomy.py",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_unattended_coordinator.py",
    "tests/platform_v1/test_autonomy_window_lifecycle.py",
    "tests/test_trust_authorization_adapter.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".codex-skills/**",
    "AGENTS.md",
    "docs/agents/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit"
  ],
  "capability_policy": {
    "github_control_plane_network_exceptions": [
      "Publish only exact codex/issue118-delegated-goal-admission-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against exact codex/issue118-current-candidate-profile-recovery-r3-20261008@88a383b3d1f75935472b4eb27e4d30aba3ee44eb after publication readiness."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "reverse_agent/platform_v1/autonomy.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/capability_registry.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/goal_service.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/unattended_coordinator.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/control_store.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "goaladmission.implementation",
      "command": "Add exact preauthorized Goal admission to existing trusted delegated windows. Immutable host PolicyAuthority binding may list bounded Goal id/revision/artifact digest/idempotency snapshots for fixed host validation, with approve_goal and validate_task capabilities and cumulative max_tasks. Existing legacy fixed-checker single Goal mode stays valid. Coordinator must admit matching PLANNED Goals, approve and materialize tasks and append delegated-identity receipt atomically in the existing TaskStore transaction, replay without duplicates across restart/concurrent connections, continue unaffected eligible snapshots on isolated denial, and reject drift/revocation/expiry/missing authority or spent allowance. Preserve zero model/provider/GitHub writes and fixed check/path enforcement; do not remove R2/R3 execution rejection, create a new DB/authority schema/Gate, or claim arbitrary coding/merge implemented. Extend only existing store activation capability check to validate the same bounded host manifest and approve_goal/validate_task pairing; arbitrary capabilities, mismatched task budgets and duplicate/invalid snapshots still reject.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "source_edit",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/autonomy.py",
        "reverse_agent/platform_v1/capability_registry.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/unattended_coordinator.py",
        "tests/platform_v1/test_delegated_goal_admission.py",
        "docs/unattended-window-lifecycle.md",
        "reverse_agent/platform_v1/control_store.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "goaladmission.validation",
      "command": "python -m pytest tests/platform_v1/test_delegated_goal_admission.py tests/platform_v1/test_autonomy.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_autonomy_window_lifecycle.py tests/test_trust_authorization_adapter.py -q -p no:cacheprovider",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "unit_test",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "goaladmission.publication",
      "command": "Publish only exact codex/issue118-delegated-goal-admission-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against exact codex/issue118-current-candidate-profile-recovery-r3-20261008@88a383b3d1f75935472b4eb27e4d30aba3ee44eb after publication readiness.",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "approval_event_or_time": "2026-10-08T07:04:52.376339+00:00",
  "owner_delegation_sha256": "ad35b96cee06d69d6bdcc468ac11e807449e2bbc1bb434c5a9c483cf5b4d1316",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 3,
  "development_correction_round_limit": 3,
  "mandatory_check_run_limit": 6,
  "execution_expires_at": "2026-10-08T09:22:21.386602+00:00"
}
```
