# Decision Packet — PR886 owner landing sidecar

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260914_issue887_pr886_owner_landing_r2_v1",
  "round_id": "round_20260914_issue887_pr886_owner_landing_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "OWNER_LANDING_AUTHORITY_SIDECAR",
  "sidecar_authority": true,
  "sidecar_rooted_at_locked_main": true,
  "sidecar_does_not_enter_target_history": true,
  "repository": "dddd2024/Nerelan",
  "source_issue": 887,
  "parent_issue": 884,
  "target_pr": 886,
  "source_pr": 886,
  "target_branch": "owner/issue642-compact-instructions-r2-v2",
  "accepted_exact_head_sha": "9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5",
  "owner_exact_head_review_id": 5194840527,
  "owner_exact_head_review_commit": "9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5",
  "base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "activation_base_sha": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "starting_head": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "fresh_base": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "current_main_expected": "a019b0f7ec3c807869eb076883be737c4dc3116d",
  "integration_base_ref": "main",
  "required_branch": "owner/issue887-pr886-owner-landing-r2-v1",
  "follows_last_decision_id": "decision_20260914_issue884_compact_instructions_r2_v2",
  "follows_last_round_id": "round_20260914_issue884_compact_instructions_r2_v2",
  "workstream_id": "issue887-pr886-owner-landing-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "landing_actor": "ChatGPT/Codex under explicit current user Owner delegation",
  "approval_basis": "The user explicitly instructed the Agent to continue and permitted completing the merge into main. This is disclosed delegated Agent activity, not independent human review.",
  "landing_authority_scope_note": "Governance-only sidecar for target PR886 exact head 9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5 at locked main a019b0f7ec3c807869eb076883be737c4dc3116d. The sidecar itself stays Draft and unmerged. After target natural exact-head CI, Decision Preflight and State Gate are terminal SUCCESS, sidecar natural CI/Decision/State are SUCCESS, no target/base/head/review-thread drift exists, this Decision grants exactly one target Ready and exactly one expected-head protected ordinary merge using method merge. No target branch push, no direct main push, no auto-merge, no force/rebase/squash, no workflow rerun/dispatch and no unrelated mutation.",
  "owner_landing_bounds": {
    "ready_attempts": 1,
    "merge_attempts": 1,
    "allowed_merge_method": "merge",
    "expected_head_protection_required": true,
    "expected_head": "9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5"
  },
  "required_landing_sequence": [
    "require terminal successful natural target exact-head CI Decision Preflight and State Gate",
    "require terminal successful natural sidecar CI Decision Preflight and State Gate",
    "fresh-read main target PR target head review threads and checks and require no drift from the bound snapshot",
    "mark target PR886 Ready exactly once",
    "observe any natural Ready-triggered State Gate and require success before merge if produced by repository policy",
    "fresh no-drift check",
    "merge target PR886 exactly once with method merge and expected head 9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5",
    "verify merged true merge commit parents and new main head"
  ],
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/transition_command_plan_preview.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/state-gate.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/control_plane/transition.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md", ".github/**", ".codex-skills/**", "docs/**", "reverse_agent/**", "frontend/**", "tests/**", "project_state/mainline_merge_intents/**", "pyproject.toml", "requirements*.txt"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "squash", "history_rewrite", "target_branch_push", "workflow_rerun", "workflow_dispatch", "runner_dispatch", "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution", "destructive", "tag_or_release", "dependency_install", "sidecar_pr_ready_or_merge"
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/issue887-pr886-owner-landing-r2-v1 and exactly one Draft sidecar against locked main; keep sidecar Draft and unmerged.",
      "After every required target and sidecar check is terminal success and fresh no-drift validation passes, mark target PR886 Ready exactly once and merge target PR886 exactly once using method merge with expected head 9b20d92aceb8f1122a8c3dfbf96b3c5e04e369a5. Then verify the resulting main head and post bounded completion evidence to Issues887 and884."
    ],
    "user_local_network_exceptions": []
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "issue887.bootstrap",
      "command": "On the exact sidecar activation run the existing transition command plan, transition lint and transition preflight against locked main. Require PRE_EXECUTION_AUTHORIZED and immutable Decision evidence before materializing generated plan files.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
    },
    {
      "command_id": "issue887.materialize",
      "command": "Materialize exactly one generated-governance commit containing only command_plan.json and transition_command_plan_preview.json from the immutable Decision projection. No product/test/source edit.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["source_edit", "local_static_check"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"], "produced_artifacts": []
    },
    {
      "command_id": "issue887.validate",
      "command": "Require natural sidecar CI Decision Preflight and State Gate success, exact target CI Decision Preflight State Gate success, unchanged main/head/base, target open/unmerged, and no blocking review threads. Do not rerun workflows.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation", "operations": ["code_read", "read_only_audit", "repository_observation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue887.publish",
      "command": "Publish only the exact landing sidecar branch and one Draft PR against locked main. Keep the sidecar Draft forever and never merge or mark it Ready.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["push", "draft_pr", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "issue887.land_target",
      "command": "Only after validation: fresh-read all bound target/base/check/thread state; mark target PR886 Ready once; observe any naturally triggered landing State Gate and require terminal success if present; fresh-read again; merge PR886 once with method merge and expected head protection; verify merged state and new main head; post bounded evidence to Issues887 and884.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [884, 887]
}
```

## Goal

Authorize only the no-drift landing of accepted PR886 after all bound natural checks succeed.

## Stop Conditions

Any target/base/head drift, failed/pending mandatory check, blocking review thread, Decision mutation, sidecar check failure or unexpected landing gate failure stops landing. No bypass, rerun, force, rebase or alternate merge method.
