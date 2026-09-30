# A2a — trusted collector execution and checkout binding

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260930_issue1039_collector_binding_r2_v1",
  "round_id": "round_20260930_issue1039_collector_binding_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "A2A_TRUSTED_COLLECTOR_EXECUTION_AND_CHECKOUT_BINDING",
  "source_issue": 1039,
  "parent_issue": 379,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner next-round request in this conversation",
  "approval_basis": "The user requests the next execution round under #1010. A2 is the next unoccupied remote slice; A0/#1036 and A1/#1038 are code-complete CI-success review-wait candidates. Reuse existing evidence_adapter and AuthorityBundle. Exact base source blob83f7d58b460b6ad78997ffe0573d8b167471883e was hash-verified; a disclosed partial-module probe reproduced empty selection success, Boolean/float exit success and unobserved HEAD drift before live evidence assembly. The production collector also does not pass its observed checkout as test cwd. Repair only those bounded collector bindings, add dedicated regressions/docs, preserve every other owner's work. ChatGPT is the delegated source author; self-review is not independent acceptance. No claim that a probe with adapter/schema doubles is a real GitHub bypass, and no claim that this slice completes evaluator isolation or verifier provenance.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260930-trusted-collector-binding-r2-v1",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 5,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 7,
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
    "specification": "In existing evidence_adapter.py, empty required-test selection never yields test_results.passed=True. Preserve missing-runner nonpass and optional/non-test exclusion. Validate all selected command IDs as nonempty, unique and admitted by bundle.allowed_command_ids; parse all selected command strings with existing shell policy before running any command, producing nonpassing diagnostics without partial execution when invalid. Require a genuine integer zero return code; invalid runner result shape/type cannot count as pass. Bind production LiveGitAdapter test execution to its actual Git worktree root rather than an unrelated runner default cwd, and recheck that root remains consistent. Reobserve exact HEAD before/after each executed command and after workflow collection; mismatch or failed observation prevents a trusted evidence result. Keep current GitHub workflow checks, live/fixture constructor behavior, accepted command provenance ownership, subprocess shell=False and no install/network fallback. Existing injected Python test seams remain supported and disclosed; they are not a security boundary against hostile in-process code. Add dedicated provider-free tests and real disposable Git/fixed Python or pytest subprocess cases covering wrong runner cwd, HEAD drift and nonvacuous selection. Document remaining dirty-tree/ABA, independent verifier process/identity, same-name workflow provenance, permission and complete-obligation limits. No source changes to other files except the new test/doc paths.",
    "reuse": "Existing AuthorityBundle, Git/GitHub adapters, command parser, ExecutionEvidence and blocking Platform V1 CI. No new gate, authority source, signed receipt schema, evidence store, TaskStore migration, generic judge or runtime.",
    "execution_surface_note": "Source begins only after actual PRE_EXECUTION_AUTHORIZED on the Decision-only Draft. Natural CI supplies full checkout/gates/integration. Hash-verified partial source may be tested in the isolated trusted worker with disclosed schema/GitHub doubles; it is not full-package evidence. Fixed disposable local Git commits and bounded Python/pytest test subprocesses are permitted in tests only; no real model, provider, credential, user PC or remote target mutation.",
    "completion_boundary": "One Draft with three exact product paths. Keep existing tests unchanged and selected. No Ready, merge, Issue closure, release, deployment or completed-A2 claim. Record exact-head CI and self-review separately from independent acceptance. Update #1039/#1010 and parent progress on completion or blockage."
  },
  "bootstrap_exception_files": ["project_state/decision_packet.md"],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": ["project_state/decision_packet.md", "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json", "reverse_agent/platform_v1/evidence_adapter.py", "tests/platform_v1/test_collector_execution_binding.py", "docs/evidence-collector-binding.md"],
  "authorized_risk_paths": ["project_state/decision_packet.md", "project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json", "reverse_agent/platform_v1/evidence_adapter.py", "tests/platform_v1/test_collector_execution_binding.py", "docs/evidence-collector-binding.md"],
  "generated_artifact_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md", "docs/agents/governance-reference.md", "tests/platform_v1/test_evidence_adapter.py", ".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md", "docs/agents/**", ".github/**", ".codex-skills/**", "reverse_agent/control_plane/**", "reverse_agent/model_access/**", "reverse_agent/project_gate.py", "reverse_agent/mainline_landing.py", "reverse_agent/github_remote_verifier.py", "reverse_agent/platform_v1/functional_validation.py", "reverse_agent/platform_v1/contracts.py", "reverse_agent/platform_v1/authority_adapter.py", "reverse_agent/platform_v1/run_store.py", "reverse_agent/platform_v1/durable_execution.py", "reverse_agent/platform_v1/task_execution.py", "reverse_agent/platform_v1/task_service.py", "reverse_agent/platform_v1/run_read_model.py", "reverse_agent/platform_v1/goal_service.py", "frontend/**", "project_state/rounds/**", "project_state/mainline_merge_intents/**", "launch_nerelan.bat", "launch_reverse_agent.bat", "dev-up.ps1", "dev-down.ps1", "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"],
  "forbidden_operations": ["direct_push_main", "auto_merge", "force_push", "rebase", "squash", "amend", "history_rewrite", "mark_ready", "merge", "workflow_rerun", "workflow_dispatch", "runner_dispatch", "model_api_invocation", "provider_network_call", "credential_access", "unknown_binary_execution", "external_reverse_tool_invocation", "destructive", "tag_or_release", "dependency_install", "local_browser_execution", "generated_governance_commit"],
  "capability_policy": {
    "runner_dispatch_allowed": false, "workflow_dispatch_allowed": false, "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false, "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false, "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false, "force_push_allowed": false, "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false, "merge_allowed": false, "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": ["Unchanged natural repository CI dependency setup and provider-free tests only; no rerun or dispatch."],
    "trusted_worker_network_exceptions": [], "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Only this exact branch and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Decision-only bootstrap first, product publication after actual preflight. Read checks and update #1039/#1010/#379/#653 and prior #1037 CI status. No Ready, merge, settings, release, deployment or other-owner source mutation."]
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}, {"pattern": "reverse_agent/platform_v1/evidence_adapter.py", "minimum_risk": "R2"}],
  "allowed_commands": [
    {"command_id": "collector.bootstrap", "command": "Verify exact base and Decision-only activation. Existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness run on an authorized trusted checkout when available; unchanged natural CI supplies full-checkout generated gate evidence. Require actual PRE_EXECUTION_AUTHORIZED before product work. Never fabricate or commit generated gates.", "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]},
    {"command_id": "collector.implement", "command": "After actual preflight implement only the collector execution/checkout binding, dedicated new regressions and document. Keep all unrelated source and tests unchanged. No additional authority or evidence framework.", "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker", "operations": ["source_edit", "unit_test", "local_static_check"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": ["reverse_agent/platform_v1/evidence_adapter.py", "tests/platform_v1/test_collector_execution_binding.py", "docs/evidence-collector-binding.md"], "produced_artifacts": []},
    {"command_id": "collector.validate", "command": "Run python -m pytest tests/platform_v1/test_collector_execution_binding.py tests/platform_v1/test_evidence_adapter.py -q; existing natural CI blocking tests/platform_v1; git diff --check. Use real disposable Git/fixed test subprocesses plus disclosed GitHub doubles. No provider, new skip/deselect or weakened old tests. Partial-module local checks are supplemental, not full-package acceptance.", "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only", "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []},
    {"command_id": "collector.publish", "command": "Publish only this exact branch and one Draft; rebind exact head. Update #1039/#1010/#379/#653 progress and previous #1037 final CI observation. Preserve all other owners and old evidence. No Ready, merge, closure or deployment.", "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane", "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []},
    {"command_id": "collector.observe", "command": "Read exact head/base, full scoped diff, immutable Decision and natural CI. Preserve negatives and distinguish author tests from independent acceptance. Update index immediately after completed or blocked phases; keep Draft.", "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation", "operations": ["read_only_audit", "code_read"], "network_access": false, "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []}
  ],
  "issue_completion_close_allowed": []
}
```

## Remaining trust boundary

No new independent verifier process, credential isolation, signed provenance, atomic snapshot, complete requirement coverage or automatic merge is delivered by this slice. Passing command exit codes are not a universal functional oracle. Public JSON remains fixture-only under the existing constructors. Test adapter injection is a trusted-host test seam, not isolation against hostile Python in the host process.
