# EBA-0 — truthful authorization and preapproval diagnostics, v2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260929_issue1033_evidence_bound_autonomy_r2_v2",
  "round_id": "round_20260929_issue1033_evidence_bound_autonomy_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "EBA_0_TRUTHFUL_AUTHORIZATION_AND_PREAPPROVAL_DIAGNOSTICS",
  "source_issue": 1033,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner implementation request in the current conversation",
  "approval_basis": "User requests GitHub fixation and all feasible implementation of evidence-bound autonomy. This fresh successor preserves invalid activation PR #1034 at b55bd6a32221fb70902abcd2b77b59802ff84c49 without modifying it. Its bootstrap assigned command_plan_generation to ci_only, rejected by current operation-surface registry. v2 uses trusted_worker for that operation and does not change product scope. Actual hosted CI performs unchanged repository validation; isolated trusted-worker exact-file checks are supplemental. ChatGPT authors this slice under delegated authority because the connected Nerelan machine is offline. This is not system-authored or independently accepted source. No source changes precede actual PRE_EXECUTION_AUTHORIZED.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260929-evidence-bound-autonomy-r2-v2",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 8,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 10,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Keep product_accepted and implementation_complete false for every authorization-only path_a lifecycle result while preserving all existing authorization and denial semantics. Fix write_task_check_outputs to emit DeltaObservation.head_sha. Add a read-only work_item_preflight API/module CLI reusing existing Path-A body normalization/digest, command validator, allowed-path parser, risk floor and fixed check selection. Diagnose bounded UTF-8 input, missing/duplicate/ambiguous sections, forbidden shell metacharacters, unbounded/traversing/risk-sensitive R1 paths, malformed branch/ref/base SHA, supplied stale base or occupied paths, and optional Draft snapshot mismatches. An absent Draft snapshot is normal before activation; a candidate body embedding one is rejected. Emit stable bounded diagnostics, APPROVAL_READY or NEEDS_REVISION, and authority/acceptance/completion false. No submitted commands execute, no approvals or network requests occur, and no digest/approval policy is changed. Add provider-free regressions in the existing blocking platform_v1 suite and the evidence-bound-autonomy architecture/phased acceptance document.",
    "execution_surface_note": "Reuse existing GitHub control plane and unchanged natural CI. Exact-file isolated-worker checks are not a full checkout. CI-owned validation may generate its existing gate artifacts; the command-plan-generation operation declared for an actual checked-out worker is trusted_worker, never a ci_only subprocess grant. No model, provider, credential, user runtime or dependency/workflow mutation.",
    "completion_boundary": "One source Draft with exact-head tests/evidence. Start product work only after actual preflight. Preserve existing tests and skip policy. Self-review is not independent acceptance. No Ready, merge, source Issue closure, deployment or claim of completed EBA-1..4."
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
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": ["AGENTS.md", "docs/agents/governance-reference.md", "tests/test_path_a_gate.py", "reverse_agent/platform_v1/functional_validation.py", "reverse_agent/platform_v1/task_store.py", ".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md", "docs/agents/**", ".github/**", ".codex-skills/**", "reverse_agent/platform_v1/**", "reverse_agent/model_access/**", "reverse_agent/project_gate.py", "reverse_agent/mainline_landing.py", "reverse_agent/github_remote_verifier.py", "frontend/**", "tests/test_path_a_gate.py", "project_state/rounds/**", "project_state/mainline_merge_intents/**", "launch_nerelan.bat", "launch_reverse_agent.bat", "dev-up.ps1", "dev-down.ps1", "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"],
  "forbidden_operations": ["direct_push_main", "auto_merge", "force_push", "rebase", "squash", "amend", "history_rewrite", "mark_ready", "merge", "workflow_rerun", "workflow_dispatch", "runner_dispatch", "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution", "external_reverse_tool_invocation", "destructive", "tag_or_release", "dependency_install", "local_browser_execution", "generated_governance_commit"],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": ["Unchanged natural CI dependency setup and provider-free validation only; no rerun or dispatch."],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Publish only owner/20260929-evidence-bound-autonomy-r2-v2 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Decision-only bootstrap first, product publication only after actual preflight. Task/parent progress comments allowed. No Ready, merge, settings, tag, release or deployment."]
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}, {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "eba0v2.bootstrap",
      "command": "Verify exact base and Decision-only activation. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree publication readiness on a trusted checkout when available. Unchanged natural repository CI provides full-checkout validation and existing generated evidence. Require actual PRE_EXECUTION_AUTHORIZED; do not fabricate or commit generated gates.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "eba0v2.implement",
      "command": "After actual preflight implement only the exact EBA-0 claim ceiling, DeltaObservation head output, read-only Work Item preflight, blocking regression tests and architecture document. Reuse current code and do not take other tasks or broaden authority.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"], "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["reverse_agent/control_plane/path_a.py", "reverse_agent/control_plane/work_item_preflight.py", "tests/platform_v1/test_evidence_bound_autonomy.py", "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"], "produced_artifacts": []
    },
    {
      "command_id": "eba0v2.validate",
      "command": "Run exact-head python -m pytest tests/platform_v1/test_evidence_bound_autonomy.py tests/test_path_a_gate.py -q and python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q and git diff --check. Natural CI runs existing blocking platform_v1 tests. No provider/model calls or submitted Issue commands, no new skip/deselect or weakened existing expectation. Report partial standalone checks separately.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0v2.publish",
      "command": "Publish only this exact branch and one Draft PR. Rebind exact head after product commits. Record #1033/#653/#252/#1010 progress and #1034 supersession without changing old authority/history. No Ready, merge, closure or deployment.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0v2.observe",
      "command": "Fresh-read exact base/head, full diff and natural checks. Preserve failure chronology. Author self-review is not independent acceptance. Record implemented, actually tested and unavailable capabilities separately; keep Draft.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Preserved scope

Same four product paths as #1033. Source v1 #1034 is immutable negative activation evidence, not an implementation. Reuse existing Path-A rules; no replacement governance store or permissive fallback. Preflight success means ready to request approval, not authority. Authorization success is never functional acceptance. All product changes require actual preflight and final deterministic validation; Ready, merge, independent acceptance and full autonomy remain separate.
