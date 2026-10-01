# EBA-0 — truthful authorization and preapproval diagnostics, v3

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260929_issue1033_evidence_bound_autonomy_r2_v3",
  "round_id": "round_20260929_issue1033_evidence_bound_autonomy_r2_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "EBA_0_TRUTHFUL_AUTHORIZATION_PREAPPROVAL_AND_EXPLICIT_TEST_CONTRACT_MIGRATION",
  "source_issue": 1033,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner implementation request in the current conversation",
  "approval_basis": "User requests GitHub fixation and all feasible concrete implementation of evidence-bound autonomy. Preserve #1034 and #1035 and their immutable Decisions. v2 source ca95aa4281575a3608eb713f94609bdef2c2037f passed 107 isolated regressions and 1917 existing focused CI tests, but natural CI 36585763792 showed four failures in tests/test_path_a_gate.py: three parameterizations of test_I1_valid_implementation_draft_remains_authorized and test_D2_converted_to_draft_with_delta_is_implementation explicitly assert product_accepted True solely from authorization; test_I1 also asserts implementation_complete True. These are the wrong contract being repaired, not legitimate functional evidence. v2 forbids this test path, so it is preserved rather than edited in place. This fresh v3 authorizes the precise three True-to-False assertion replacements in those two functions, plus an explanatory comment, while preserving every authorization/denial assertion and all test cases. This is an explicit approved semantic test migration, not skipping tests or accepting a failed candidate. Reuse the four already-authored EBA-0 blobs as unaccepted content only after actual PRE_EXECUTION_AUTHORIZED. ChatGPT authors this scope under delegated authority; the offline Nerelan runtime does not. Self-review is not independent acceptance.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "owner/20260929-evidence-bound-autonomy-r2-v3",
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
    "specification": "Keep product_accepted and implementation_complete false for every authorization-only path_a lifecycle result while preserving all actual authorization and denial semantics. Fix write_task_check_outputs to emit DeltaObservation.head_sha. Reuse the v2 read-only work_item_preflight API/module CLI and architecture/regressions: bounded UTF-8 input, unambiguous required sections, existing normalization/digest, shell-token rules, allowed-path parser, R1 risk floor, fixed test selection, safe literal paths, branch/ref/base SHA, optional supplied base/head/occupancy and Draft snapshot ties. APPROVAL_READY never grants authority, accepts a product, executes Issue commands or verifies live facts. Add only the explicit three obsolete completion assertions in tests/test_path_a_gate.py to the corrected false contract, retaining all remaining bytes apart from explanatory comments. Additional necessary fixes may occur only within the existing four EBA-0 source/test/doc paths, without changing Path-A approval, risk, permissions, scope validation or check selection. No second authority engine, store, schema family, semantic-digest migration or automatic base refresh.",
    "exact_test_migration": "tests/test_path_a_gate.py base blob 225e3e314e75a094a4612becd1361769b060d73b: in test_I1_valid_implementation_draft_remains_authorized, product_accepted True -> False and implementation_complete True -> False; in test_D2_converted_to_draft_with_delta_is_implementation, product_accepted True -> False. Preserve implementation_authority True and every existing exact-head, digest, approval, risk and denial assertion. No test deletion, skip, deselection, broad monkeypatch or weakened functional check.",
    "content_reuse": "v2 content blobs path_a 4068cb18125778529eeaac2d6c44847f1f829f81, preflight 777c765a88b910a8e1aa43b9f123c713bd42849b, new regressions afaf10d553e2ee0f3f08199796323e4e450e2222 and doc 87fc025bd2834fa02bf9e4c79512d1c93bcd7758 are unaccepted source inputs, not reusable CI/approval authority. Copy their exact bytes onto the fresh v3 after actual preflight; do not merge/rebase old history.",
    "execution_surface_note": "GitHub-first and unchanged natural CI full-checkout validation. Isolated exact-file tests supplement but do not replace CI. Connected user machine is offline. command_plan_generation is bound to trusted_worker per current registry. No provider/model calls, credentials, user-local runtime, dependency or workflow mutation.",
    "completion_boundary": "One new source Draft, exact-head mandatory CI and honest evidence. Actual PRE_EXECUTION_AUTHORIZED precedes product changes. EBA-0 foundation is not EBA-1..4. No Ready, merge, Issue closure or deployment; self-review cannot be called independent acceptance."
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
    "tests/test_path_a_gate.py",
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
    "tests/test_path_a_gate.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "generated_artifact_paths": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"],
  "reference_paths": ["AGENTS.md", "docs/agents/governance-reference.md", "reverse_agent/platform_v1/functional_validation.py", "reverse_agent/platform_v1/task_store.py", ".github/workflows/ci.yml"],
  "forbidden_mutated_paths": ["AGENTS.md", "docs/agents/**", ".github/**", ".codex-skills/**", "reverse_agent/platform_v1/**", "reverse_agent/model_access/**", "reverse_agent/project_gate.py", "reverse_agent/mainline_landing.py", "reverse_agent/github_remote_verifier.py", "frontend/**", "project_state/rounds/**", "project_state/mainline_merge_intents/**", "launch_nerelan.bat", "launch_reverse_agent.bat", "dev-up.ps1", "dev-down.ps1", "pyproject.toml", "requirements*.txt", "**/secrets/**", "**/.env"],
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
    "ci_network_exceptions": ["Unchanged natural repository CI dependency setup and provider-free validation only; no rerun or dispatch."],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": ["Publish only owner/20260929-evidence-bound-autonomy-r2-v3 and one Draft against main@9092911f41a089e249f27c883526904299be1d17. Decision-only bootstrap first; five exact product paths only after actual preflight. Task and parent progress/supersession comments allowed. No Ready, merge, settings, tag, release, deployment or closing other tasks."]
  },
  "path_risk_floor": [{"pattern": "project_state/**", "minimum_risk": "R2"}, {"pattern": "reverse_agent/control_plane/**", "minimum_risk": "R2"}],
  "allowed_commands": [
    {
      "command_id": "eba0v3.bootstrap",
      "command": "Verify exact base and Decision-only activation. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and publication readiness on a trusted checkout when available. Unchanged natural CI supplies full-checkout generated validation evidence. Require actual PRE_EXECUTION_AUTHORIZED before product work; no hand-written or committed gates.",
      "phase": "bootstrap", "required": false, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["code_read", "local_static_check", "command_plan_generation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/startup_snapshot.json", "project_state/gates/bootstrap_state.json", "project_state/gates/transition_command_plan_preview.json", "project_state/gates/transition_preflight_result.json"]
    },
    {
      "command_id": "eba0v3.implement",
      "command": "After actual preflight reuse the four v2 EBA-0 content blobs on this fresh branch and perform only the three explicit obsolete-assertion corrections in tests/test_path_a_gate.py. Additional fixes stay inside the other four EBA-0 paths and retain all approval/denial behavior. No test skipping or semantic authority expansion.",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "trusted_worker",
      "operations": ["source_edit", "unit_test", "local_static_check"], "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": ["reverse_agent/control_plane/path_a.py", "reverse_agent/control_plane/work_item_preflight.py", "tests/platform_v1/test_evidence_bound_autonomy.py", "tests/test_path_a_gate.py", "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"], "produced_artifacts": []
    },
    {
      "command_id": "eba0v3.validate",
      "command": "Run exact-head python -m pytest tests/platform_v1/test_evidence_bound_autonomy.py tests/test_path_a_gate.py -q and python -m pytest tests/test_control_plane_transition.py tests/test_project_gate.py tests/test_decision_preflight.py -q and git diff --check. Natural CI runs the existing blocking Platform V1 suite including all new regressions. All 191 existing Path-A cases remain selected; only the explicitly obsolete completion expectations change. No provider/model/credential calls, new skip/deselect, forged log or submitted Issue command execution. Report partial checks separately.",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "ci_only",
      "operations": ["unit_test", "local_static_check", "diff_validation"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0v3.publish",
      "command": "Publish exact branch and one Draft; rebind exact head after product changes. Record #1033/#653/#252/#1010 progress and #1035 supersession. Preserve failed v1/v2 Decisions, heads and CI. Do not touch active #1024/#1031/#1032 or close sidecars. No Ready, merge, closure or deployment.",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "github_control_plane",
      "operations": ["push", "draft_pr", "pull_request_comment", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    },
    {
      "command_id": "eba0v3.observe",
      "command": "Read exact base/head, full diff and natural checks. Confirm test-file delta contains only the explicit migration and optional explanation; retain denied authorization cases. Preserve all failures. Author self-review is not independent acceptance; report foundation implementation separately from full autonomy and landing.",
      "phase": "final_evidence", "required": true, "expected_exit_codes": [0], "execution_surface": "remote_observation",
      "operations": ["read_only_audit", "code_read"], "network_access": false,
      "required_evidence_source": "repository_state_attestation", "allowed_mutated_paths": [], "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": []
}
```

## Explicit migration, not test weakening

Only three obsolete positive completion expectations change to false, in the two named tests. All original test cases, authorization assertions, deny boundaries and required CI remain. New blocking tests independently exercise the corrected distinction: valid authority without a functional oracle must never certify completion. Prior false results and failed CI stay preserved. v3 does not alter old Decisions or bypass their scope.
