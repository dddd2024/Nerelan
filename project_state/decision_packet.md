# Decision Packet — #908 BRAND-2B v4 current landing identity prerequisite

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260916_issue908_brand2b_v4_landing_identity_r3_v1",
  "round_id": "round_20260916_issue908_brand2b_v4_landing_identity_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "BRAND2B_V4_CURRENT_LANDING_IDENTITY_PREREQUISITE",
  "source_issue": 908,
  "parent_issue": 530,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated Agent Owner authoring",
  "approval_basis": "The user delegated repository Owner execution for the continuous Nerelan audit and explicitly requires new authority to be created rather than treating authority as a default stop. Fresh canonical audit at main@d3ffafc8924614f309a8f85b6224137f94b2d8c1 proves #901 cannot legally emit a new current Owner landing attestation because mainline_landing.py only supports frozen v1/v2/v3 old-slug semantics, while #530 requires all new/current intent and attestation evidence to bind dddd2024/Nerelan. Issue #908 is Owner-approved r3-approved and freezes the minimum v4 compatibility slice needed to break that cycle. This delegated approval is not independent final acceptance and grants no Ready/Merge.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "workflow_profile": "baseline",
  "integration_base_ref": "main",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "required_branch": "owner/brand2b-v4-current-landing-identity-r3-v1",
  "fresh_worktree_creation_required": false,
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
    "specification": "Implement only the minimum BRAND-2B v4 landing-identity compatibility slice authorized by Issue #908. Freeze v1/v2/v3 validation semantics exactly as historical evidence records them. Add a v4 merge-intent and v4 approval-attestation schema path whose top-level repository and nested approval payload repository require exactly dddd2024/Nerelan. No generation may accept both identities. Reuse existing exact PR/base/head, Decision, digest, expiry, workflow-profile, remote-observation, approval-binding and post-merge semantics. Add deterministic regressions proving historical old-slug fixtures remain valid, historical generations rewritten to Nerelan fail, v4 Nerelan fixtures pass, v4 old-slug and mixed nested approval payloads fail, wrong PR/base/head/digest/workflow/event/run bindings fail, and a #901-shaped unmerged target can validate one canonical Nerelan v4 pre-merge attestation without weakening exact-head checks. Do not emit or mutate any #900/#902 receipt or current active merge intent under this implementation Decision. If reverse_agent/github_remote_verifier.py proves necessary, stop for scope review.",
    "execution_surface_note": "GitHub-first Decision-only activation and Draft publication are allowed on the exact non-main branch. Natural Decision Preflight and State Gate on the immutable activation must establish PRE_EXECUTION_AUTHORIZED before semantic publication. The bounded semantic tree may then be authored only in the four exact semantic paths using the GitHub control plane; natural exact-head CI/Decision Preflight/State Gate are final machine evidence. No user-local, provider/model, browser, credential, binary or dependency activity is required.",
    "completion_boundary": "Draft implementation only. This Decision grants no Ready or Merge. Historical v1/v2/v3 evidence and failed main State Gate run 34820409545 remain immutable. After this slice is independently accepted and separately landed, #901 must fresh-read/re-authorize PR #900 before creating any canonical v4 attestation. Broader BRAND-2B product/default documentation cleanup remains outside this Decision."
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
    "squash",
    "amend",
    "merge",
    "mark_ready",
    "auto_merge",
    "tag_or_release",
    "runner_dispatch",
    "workflow_dispatch",
    "workflow_rerun",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "browser_execution",
    "credential_access",
    "active_json_rewrite"
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
      "Publish and update only owner/brand2b-v4-current-landing-identity-r3-v1 and one Draft PR in dddd2024/Nerelan against exact main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Initial publication is Decision-only. After PRE_EXECUTION_AUTHORIZED, mutate only the exact semantic allowlist and generated gate artifacts explicitly authorized here. Record bounded evidence on #908/#530/#901/#612 and the exact Draft. Never Ready or Merge, never emit #900/#902 attestation evidence, and never rewrite historical v1/v2/v3 evidence."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R3"},
    {"pattern": "reverse_agent/mainline_landing.py", "minimum_risk": "R3"},
    {"pattern": "tests/test_mainline_landing.py", "minimum_risk": "R3"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue908.bootstrap",
      "command": "On the exact Decision-only activation of owner/brand2b-v4-current-landing-identity-r3-v1 at main@d3ffafc8924614f309a8f85b6224137f94b2d8c1, run the existing startup-snapshot, transition-command-plan, transition-lint and transition-preflight --mode pre through the natural full-checkout governance workflow. Require PRE_EXECUTION_AUTHORIZED before any semantic path changes. Do not hand-author successful gate outputs and do not reuse stale generated evidence.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "ci_only",
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
      "command_id": "issue908.implement",
      "command": "Only after PRE_EXECUTION_AUTHORIZED, implement the minimum v4 compatibility slice in exactly reverse_agent/mainline_landing.py, project_state/schemas/mainline_merge_intent_v4.schema.json, project_state/schemas/merge_approval_attestation_v4.schema.json and tests/test_mainline_landing.py. Preserve v1/v2/v3 semantics byte-for-byte where applicable; add version-dispatched v4 Nerelan-only identity and the #908 regression matrix. No #900/#902 receipt or active intent mutation. Stop if github_remote_verifier.py is required.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "github_control_plane",
      "operations": ["source_edit", "code_read", "push", "network_access"],
      "network_access": true,
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
      "command_id": "issue908.validate",
      "command": "On the exact semantic head run python -m pytest tests/test_mainline_landing.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q; git diff --check. Natural exact-head CI, Decision Preflight and State Gate must succeed without rerun/dispatch. Prove the full #908 v1/v2/v3/v4 identity matrix and one unmerged #901-shaped v4 pre-merge attestation fixture.",
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
      "command_id": "issue908.publish",
      "command": "Publish only owner/brand2b-v4-current-landing-identity-r3-v1 and one Draft against exact main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. The first publication is Decision-only. Rebind the Draft to each exact head after authorized publication. Record bounded evidence on #908/#530/#901/#612. Never mark Ready or Merge and never publish a new old-slug attestation.",
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
      "command_id": "issue908.observe",
      "command": "Fresh-read current main, exact Draft base/head, changed paths, immutable Decision, natural CI/Decision Preflight/State Gate and full semantic diff. Independently audit historical v1/v2/v3 preservation and v4 canonical identity. Do not call self-review independent acceptance. Keep Draft until a fresh independent exact-head audit. This Decision never authorizes Ready/Merge.",
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

Break the current canonical-repository attestation dependency cycle without weakening historical evidence semantics or widening BRAND-2B.

## Current evidence

Current server truth is `main@d3ffafc8924614f309a8f85b6224137f94b2d8c1`, ordinary CI green and main State Gate red. #901/#900/#902 are machine-validated but legally held because current landing validation can only accept historical old-slug evidence while #530 requires new/current evidence to use `dddd2024/Nerelan`. This Decision activates the minimum v4 compatibility prerequisite and does not itself repair or land #900.

## Do not do

No Ready/Merge, no direct main push, no history rewrite, no workflow/dependency/product/frontend/broad-branding change, no provider/browser/credential/binary execution, no active-intent mutation, no new old-slug receipt, and no historical evidence rewrite.

## Implementation scope

Only the four exact semantic paths in the Decision after natural PRE_EXECUTION_AUTHORIZED, plus explicitly authorized generated gate evidence.

## Acceptance

Historical generations remain frozen; v4 is Nerelan-only; mixed identities fail closed; exact PR/base/head/workflow/digest bindings stay intact; focused tests and natural exact-head CI/Decision/State Gate pass; independent exact-head audit accepts the semantic head. Draft only.
