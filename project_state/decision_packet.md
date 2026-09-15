# Decision Packet — tracked command-plan normal-path prerequisite closure

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260915_issue898_tracked_plan_prerequisite_r2_v1",
  "round_id": "round_20260915_issue898_tracked_plan_prerequisite_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "G2_0_TRACKED_PLAN_NORMAL_PATH_PREREQUISITE_CLOSURE",
  "source_issue": 898,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "The user explicitly delegated repository Owner authority and asked to resolve the repeated user-local handoff caused by fresh Path-B Decisions requiring a tracked command-plan rebind. Fresh current-main audit confirms production transition lint already treats missing or previous-round tracked plans as historical evidence while Platform V1 still unconditionally requires tracked Decision/round equality. This Decision authorizes only the minimum regression correction; it does not touch active #891/#894 product or landing work.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "fresh_base": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "current_main_expected": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "required_branch": "owner/issue898-tracked-plan-prereq-r2-v1",
  "workstream_id": "issue898-tracked-plan-prereq-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
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
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
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
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Replace only the stale Platform V1 invariant that unconditionally requires tracked command_plan Decision/round identity to equal the active Decision. Reuse build_transition_command_plan as the single deterministic projection. A tracked plan whose decision_id and round_id both match current authority must equal the deterministic current projection exactly; one-component identity collision must fail closed; a plan whose decision_id and round_id are both from an older round is historical generated evidence and must not block a fresh Decision. Preserve all existing transition-lint current-plan tamper detection. Do not change production transition code, workflows, landing code, dependencies, target PR893 or recovery PR897.",
    "execution_surface_note": "Decision activation/publication and remote observation use GitHub control plane. The single semantic test authoring step requires a real trusted checkout. Repository CI performs exact-head validation. This round deliberately has generated_governance_commit_limit=0; a tracked command-plan rebind is not an allowed implementation prerequisite.",
    "completion_boundary": "Draft implementation only. No Ready/Merge, no main mutation, no #893/#897 state mutation. Acceptance requires natural exact-head CI/Decision Preflight/State Gate and proof that the fresh Decision can reach full CI without committing a matching command_plan.json."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "generated_artifact_paths": [],
  "reference_paths": [
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/command_authority.py",
    "reverse_agent/control_plane/evidence_recorder.py",
    "reverse_agent/project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_trusted_command_runner.py",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/state-gate.yml"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/**",
    "frontend/**",
    "docs/**",
    ".codex-skills/**",
    "project_state/gates/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_trusted_command_runner.py",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "merge",
    "mark_ready",
    "tag_or_release",
    "runner_dispatch",
    "workflow_rerun",
    "workflow_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "dependency_install",
    "target_branch_push"
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/issue898-tracked-plan-prereq-r2-v1 in dddd2024/Nerelan and exactly one Draft PR against main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Comment only on Issue898 and that Draft for this implementation round. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "tests/platform_v1/test_merge_intent.py", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue898.bootstrap",
      "command": "On an exact trusted checkout of owner/issue898-tracked-plan-prereq-r2-v1 inspect the immutable Decision and current tracked historical command plan. Run transition-lint and transition-preflight dry-run semantics without persisting or committing generated governance. The stale tracked plan must not be treated as current authority.",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue898.implement",
      "command": "Author only tests/platform_v1/test_merge_intent.py. Replace the unconditional tracked command-plan current-identity assertion with a projection-aware invariant reusing the existing production Decision-to-plan compiler. Both-old identity is historical evidence and allowed; current identity requires exact deterministic equality; partial identity collision fails closed. Do not modify production code or generated governance.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "local_static_check", "unit_test"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["tests/platform_v1/test_merge_intent.py"],
      "produced_artifacts": []
    },
    {
      "command_id": "issue898.validate",
      "command": "Run the affected Platform V1 test file and the existing G2-0 control-plane transition regressions, then git diff --check. Natural exact-head CI, Decision Preflight and State Gate are final repository validation. Do not generate or commit command_plan.json as a prerequisite.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "ci_check_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue898.publish",
      "command": "Publish only owner/issue898-tracked-plan-prereq-r2-v1 and one Draft PR against exact locked main. Update only Issue898 and that Draft. No target PR893/897 mutation, Ready, Merge, workflow rerun or dispatch.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue898.observe",
      "command": "Fresh-read exact branch/base/head and natural CI/Decision Preflight/State Gate. Confirm full CI no longer requires a tracked current command-plan rebind, no generated governance commit exists, no active #891/#894 files were touched, and current-identity tamper semantics remain fail closed.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read", "repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Goal

Close the remaining G2-0 normal-path bootstrap defect under #156: a fresh Path-B Decision must not require a matching tracked `project_state/gates/command_plan.json` commit before full CI can be green.

## Build vs Reuse

Reuse the existing deterministic Decision compiler and transition-lint/preflight semantics. Do not build a second compiler, workflow, worker runtime, scheduler, evidence family or Git client.

## Implementation Scope

Exactly one semantic path after pre-execution authorization:

```text
tests/platform_v1/test_merge_intent.py
```

If production code must change, stop and use a fresh Decision; do not expand this immutable scope.

## Acceptance

Old/missing tracked plan is non-authoritative historical evidence during a fresh Decision; a tracked current-identity plan must still match the deterministic projection exactly; partial identity collision fails closed; existing G2-0 transition regressions stay green; natural full CI/Decision Preflight/State Gate succeed without any generated-governance commit.

## Stop Conditions

Any main drift, Decision mutation, unexpected second path, generated-governance commit, current-plan tamper weakening, #893/#897 overlap, workflow rerun/dispatch, Ready/Merge attempt or failed mandatory natural check stops the round.