# Decision Packet — #910 BRAND-2B v4 current landing identity prerequisite v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260916_issue910_brand2b_v4_landing_identity_r3_v2",
  "round_id": "round_20260916_issue910_brand2b_v4_landing_identity_r3_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "BRAND2B_V4_CURRENT_LANDING_IDENTITY_PREREQUISITE_V2",
  "source_issue": 910,
  "parent_issue": 530,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated Agent Owner authoring",
  "approval_basis": "The user delegated repository Owner execution for the continuous Nerelan audit and requires creation of fresh authority rather than default stopping when authority is missing. Issue #910 is the bounded r3-approved successor to #908/#909. Fresh exact-head natural Decision Preflight run 35065363773 proved the v1 immutable activation invalid at Transition lint before semantic execution because it assigned command_plan_generation to ci_only and source_edit/code_read to github_control_plane, contrary to the current canonical operation-surface registry. This v2 preserves v1 as negative evidence, keeps the exact semantic scope unchanged, and corrects only the typed execution-surface contract. This delegated approval is not independent final acceptance and grants no Ready/Merge.",
  "supersedes_decision_id": "decision_20260916_issue908_brand2b_v4_landing_identity_r3_v1",
  "superseded_evidence": "PR909 exact head d31c441b0c499b649abcdc837bb082ed52c4fb63 is CLOSED-OR-STOPPED negative implementation-authority evidence for this successor. Decision Preflight run 35065363773 / job 104694329553 failed at Transition lint before command-plan/preflight execution; no semantic v4 source/schema/test mutation was made. Preserve PR909, its checks, artifacts and Decision unchanged. No rerun, amend or history rewrite.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "workflow_profile": "baseline",
  "integration_base_ref": "main",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "required_branch": "owner/brand2b-v4-current-landing-identity-r3-v2",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "workflow_dispatch_limit": 0,
  "runner_dispatch_limit": 0,
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
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Implement only the minimum BRAND-2B v4 landing-identity compatibility slice authorized by Issue #910. Freeze v1/v2/v3 validation semantics exactly as historical evidence records them. Add a v4 merge-intent and v4 approval-attestation schema path whose top-level repository and nested approval payload repository require exactly dddd2024/Nerelan. No generation may accept both identities. Reuse existing exact PR/base/head, Decision, digest, expiry, workflow-profile, remote-observation, approval-binding and post-merge semantics. Add deterministic regressions proving historical old-slug fixtures remain valid, historical generations rewritten to Nerelan fail, v4 Nerelan fixtures pass, v4 old-slug and mixed nested approval payloads fail, wrong PR/base/head/digest/workflow/event/run bindings fail, and a #901-shaped unmerged target can validate one canonical Nerelan v4 pre-merge attestation without weakening exact-head checks. Do not emit or mutate any #900/#902 receipt or current active merge intent under this implementation Decision. If reverse_agent/github_remote_verifier.py proves necessary, stop for scope review.",
    "execution_surface_note": "Decision activation/publication uses GitHub control plane only. Checkout-local command-plan generation and semantic source/schema/test editing require an actually available trusted_worker and never the GitHub control plane. Natural Decision Preflight/State Gate on the Decision-only activation must first establish PRE_EXECUTION_AUTHORIZED. If trusted_worker is unavailable after valid activation, semantic implementation is BLOCKED_BY_CAPABILITY; do not relabel GitHub contents mutation as trusted-worker execution and do not fall back to user_local without separate authority. Natural exact-head CI/Decision Preflight/State Gate provide final machine validation after semantic publication.",
    "completion_boundary": "Draft implementation only. This Decision grants no Ready or Merge. PR909 and main State Gate run 34820409545 remain immutable negative evidence. After this slice is independently accepted and separately landed, #901 must fresh-read/re-authorize PR900 before creating any canonical v4 attestation. Broader BRAND-2B cleanup remains outside this Decision."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v4.schema.json",
    "project_state/schemas/merge_approval_attestation_v4.schema.json",
    "tests/test_mainline_landing.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v4.schema.json",
    "project_state/schemas/merge_approval_attestation_v4.schema.json",
    "tests/test_mainline_landing.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    ".github/workflows/state-gate.yml",
    "project_state/schemas/mainline_merge_intent_v1.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    "project_state/schemas/merge_approval_attestation_v1.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v3.schema.json",
    "tests/test_control_plane_transition.py",
    "tests/test_project_gate.py",
    "tests/test_decision_preflight.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "README.txt",
    "AGENTS.md",
    "docs/**",
    "scripts/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/mainline_merge_intent_v1.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    "project_state/schemas/merge_approval_attestation_v1.schema.json",
    "project_state/schemas/merge_approval_attestation_v2.schema.json",
    "project_state/schemas/merge_approval_attestation_v3.schema.json",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "merge",
    "mark_ready",
    "tag_or_release",
    "runner_dispatch",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "browser_execution",
    "workflow_dispatch"
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
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only owner/brand2b-v4-current-landing-identity-r3-v2 in dddd2024/Nerelan and one Draft against exact main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Update only that Draft and bounded Issues #910/#908/#530/#901/#612. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R3"},
    {"pattern": "reverse_agent/mainline_landing.py", "minimum_risk": "R3"},
    {"pattern": "tests/test_mainline_landing.py", "minimum_risk": "R3"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue910.bootstrap",
      "command": "On a fresh clean trusted checkout at exact main d3ffafc8924614f309a8f85b6224137f94b2d8c1 and branch owner/brand2b-v4-current-landing-identity-r3-v2, verify the immutable v2 Decision and no unrelated tracked mutation; run the existing startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre. Do not reuse PR909 evidence.",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue910.implement",
      "command": "Only after v2 PRE_EXECUTION_AUTHORIZED, use an actually available trusted_worker to implement the minimum v4 compatibility slice in exactly reverse_agent/mainline_landing.py, project_state/schemas/mainline_merge_intent_v4.schema.json, project_state/schemas/merge_approval_attestation_v4.schema.json and tests/test_mainline_landing.py. Preserve v1/v2/v3 semantics and add the #910 regression matrix. Do not mutate #900/#902 evidence. Stop if github_remote_verifier.py is required.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "code_read", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "project_state/schemas/mainline_merge_intent_v4.schema.json",
        "project_state/schemas/merge_approval_attestation_v4.schema.json",
        "tests/test_mainline_landing.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue910.validate",
      "command": "On the exact semantic head run python -m pytest tests/test_mainline_landing.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q; git diff --check. Prove the complete historical-vs-v4 identity matrix and one #901-shaped unmerged canonical v4 pre-merge fixture. Natural exact-head CI, Decision Preflight and State Gate must succeed without rerun or dispatch.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue910.publish",
      "command": "Publish only owner/brand2b-v4-current-landing-identity-r3-v2 in dddd2024/Nerelan and one Draft against exact main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Update only that Draft and bounded Issues #910/#908/#530/#901/#612. Never Ready or Merge.",
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
      "command_id": "issue910.observe",
      "command": "Fresh-read current main, exact Draft base/head, changed paths, immutable Decision, natural CI/Decision Preflight/State Gate and full semantic diff. Audit historical v1/v2/v3 preservation and v4 canonical identity. Same-agent audit is not independent final acceptance. Never Ready or Merge under this Decision.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"],
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

Provide a valid typed Path-B activation for the minimum current v4 landing-identity compatibility prerequisite, without modifying historical v1/v2/v3 evidence or widening BRAND-2B.

## Current evidence

Current server truth is `main@d3ffafc8924614f309a8f85b6224137f94b2d8c1`, ordinary CI green and main State Gate red. #901/#900/#902 remain held because no legal canonical current attestation path exists. PR909/v1 remains immutable negative evidence: its natural Decision Preflight failed before semantic execution on an invalid operation-surface assignment.

## Do not do

No Ready/Merge, direct main push, history rewrite, workflow rerun/dispatch, provider/browser/credential/binary activity, active-intent mutation, #900/#902 receipt mutation, broad branding cleanup, old-schema rewrite or user_local substitution.

## Acceptance boundary

First require natural v2 activation preflight. If it is valid but no trusted_worker is available, report `BLOCKED_BY_CAPABILITY` for semantic implementation and continue other remote audit/research work; do not manufacture execution provenance.
