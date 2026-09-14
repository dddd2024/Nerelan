# Decision Packet — #891 false/none pre-merge attestation closure

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260914_issue891_false_none_premerge_attestation_r2_v1",
  "round_id": "round_20260914_issue891_false_none_premerge_attestation_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "FALSE_NONE_PREMERGE_ATTESTATION_CLOSURE",
  "source_issue": 891,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated Agent Owner authoring",
  "approval_basis": "The user explicitly delegated repository Owner execution and requested completion of the highest-priority non-overlapping work. Fresh server truth shows current main d3ffafc8924614f309a8f85b6224137f94b2d8c1 is governance-red after natural State Gate run 34820409545 because false/none landing could merge without the already-required OWNER_LANDING_MERGE_ATTESTATION. This bounded correction is delegated Agent authoring, not independent human review, and grants no Ready/Merge.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "activation_base_sha": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "starting_head": "d3ffafc8924614f309a8f85b6224137f94b2d8c1",
  "required_branch": "owner/issue891-false-none-attestation-r2-v1",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
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
  "workflow_profile": "baseline",
  "semantic_implementation_contract": {
    "specification": "Make false/none Owner landing fail closed before merge unless exactly one current existing-format OWNER_LANDING_MERGE_ATTESTATION is present and validates against the exact target PR/head/base, exact unmerged landing-authority Decision/head/base, required workflow observations and current formal landing context. Reuse the current attestation parser, canonical digest/binding rules and post-merge validation semantics; do not create a second receipt/authority family and do not weaken post-merge mainline validation. Missing, duplicate, stale, wrong-target, wrong-head/base, wrong-authority or wrong-workflow attestation must block pre-merge landing. A valid pre-merge attestation must remain the same evidence accepted by the unchanged post-merge validator. Legacy mainline-merge-intent landing remains unchanged; no PR-number-specific exception.",
    "execution_surface_note": "Decision activation/publication uses GitHub control plane. Natural exact-head Decision Preflight/State Gate on a full GitHub checkout must produce PRE_EXECUTION_AUTHORIZED before semantic mutation. Semantic authoring and deterministic focused checks require a clean trusted-worker checkout; CI provides final exact-head validation. No user-local, provider/model, credential, browser or Windows-specific execution is required.",
    "completion_boundary": "Draft corrective implementation only. Historical run 34820409545 remains negative evidence and must not be rerun or retroactively repaired. No Ready/Merge under this Decision. A later separately authorized landing must produce a new natural main-push State Gate SUCCESS."
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
    ".github/workflows/state-gate.yml",
    "tests/test_project_gate.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
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
      "Publish only owner/issue891-false-none-attestation-r2-v1 in dddd2024/Nerelan and one Draft against main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Initial publication is Decision-only for natural transition preflight. Semantic publication is permitted only after PRE_EXECUTION_AUTHORIZED. Update that Draft and Issues891/156 with bounded evidence. Never Ready or Merge."
    ]
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/mainline_landing.py", "minimum_risk": "R2"}
  ],
  "allowed_commands": [
    {
      "command_id": "issue891.bootstrap",
      "command": "On a full clean trusted checkout at exact main d3ffafc8924614f309a8f85b6224137f94b2d8c1 verify branch identity and immutable Decision; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Existing natural repository CI may independently generate transition plan/preflight evidence on its exact checkout. Do not hand-author successful gate outputs.",
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
      "command_id": "issue891.implement",
      "command": "Only after actual PRE_EXECUTION_AUTHORIZED, modify reverse_agent/mainline_landing.py and tests/test_mainline_landing.py to require the existing OWNER_LANDING_MERGE_ATTESTATION contract on the false/none pre-merge landing path. Reuse current parser/digest/binding/post-merge semantics. Add absent, duplicate, stale, wrong target/head/base, wrong landing-authority, wrong workflow/context, positive valid-attestation, unchanged post-merge and legacy regressions. No second authority artifact, no workflow/project_gate/verifier mutation and no PR-specific exception.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["reverse_agent/mainline_landing.py", "tests/test_mainline_landing.py"],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891.validate",
      "command": "On the full exact implementation head run python -m pytest tests/test_mainline_landing.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q; git diff --check. Natural exact-head CI, Decision Preflight and State Gate must also succeed. Do not rerun/dispatch historical failed run 34820409545 or hide a failure with skips/exclusions.",
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
      "command_id": "issue891.publish",
      "command": "Publish only owner/issue891-false-none-attestation-r2-v1 and one Draft against main@d3ffafc8924614f309a8f85b6224137f94b2d8c1. Decision-only Draft publication is allowed to obtain natural transition preflight. Semantic branch movement requires actual pre-execution authorization. Record bounded evidence on the Draft and Issues891/156. Never mark Ready or Merge.",
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
      "command_id": "issue891.observe",
      "command": "Fresh-read exact branch/base/head, natural CI/Decision Preflight/State Gate and complete scoped diff. Confirm historical PR886/run34820409545 remain unchanged negative evidence. Same-agent review is not independent acceptance; no Ready/Merge or mainline-green claim until a separately authorized landing produces a new natural main-push State Gate SUCCESS.",
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

Repair the current governance-red false/none Owner landing lifecycle by making the existing pre-merge landing path enforce the same exact Owner attestation already required by post-merge validation.

## Current Evidence

Current main is `d3ffafc8924614f309a8f85b6224137f94b2d8c1`. Natural post-merge State Gate run `34820409545` failed only because target PR #886 had zero matching `OWNER_LANDING_MERGE_ATTESTATION` comments. Preserve #886/#887/#888 and that run unchanged as negative evidence.

## Build vs Reuse

Reuse existing `OWNER_LANDING_MERGE_ATTESTATION`, current parser/digest/binding logic, `GitHubRemoteAcceptanceVerifier`, false/none landing route and post-merge validator. No new merge queue, receipt family, GitHub client, scheduler, database, workflow, dependency or policy engine.

## Implementation Scope

After actual pre-execution authorization: `reverse_agent/mainline_landing.py` and `tests/test_mainline_landing.py` only.

## Tests

Focused mainline landing tests, transition/project-gate regressions, `git diff --check`, then natural exact-head CI / Decision Preflight / State Gate.

## Stop Conditions

Stop on changed main/base, Decision mutation, missing PRE_EXECUTION_AUTHORIZED, required path expansion, mandatory test/check failure, unavailable trusted-worker implementation surface or exhausted commit/publication budget. Do not reinterpret a GitHub-control-plane-only edit as trusted-worker semantic execution.
