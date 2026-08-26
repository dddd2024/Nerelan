# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260826_issue367_pr378_owner_landing_r2_v1",
  "round_id": "round_20260826_issue367_pr378_owner_landing_r2_v1",
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
  "follows_last_decision_id": "decision_20260826_issue370_strict_required_checks_r2_v1",
  "follows_last_round_id": "round_20260826_issue370_strict_required_checks_r2_v1",
  "previous_audit_outcome": "PR378_EXACT_HEAD_ACCEPTED_AND_RULESET21023698_STRICT_TRUE_READY_FOR_OWNER_LANDING",
  "workstream_id": "issue367-pr378-owner-landing-r2-v1",
  "source_issue": 367,
  "parent_issue": 365,
  "integration_base_ref": "main",
  "base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "activation_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "starting_head": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "required_branch": "owner/issue367-pr378-owner-landing-r2-v1",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "pr_creation_allowed": false,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "test_semantics_changes_allowed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main/base 9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf and fresh landing-authority branch",
    "commit this immutable Owner landing Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
    "python -m reverse_agent.project_gate worktree-publication-readiness --state-dir project_state"
  ],
  "allowed_commands": [
    {
      "command_id": "issue367_pr378_landing.bootstrap",
      "command": "verify locked main and clean landing-authority branch; commit this Decision first; run startup snapshot, deterministic command plan, transition lint, preflight and publication readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY; commit exactly five generated gate files; push this exact authority branch once without creating a PR",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "code_read",
        "local_static_check",
        "commit",
        "push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue367_pr378_landing.observe",
      "command": "immediately re-observe main, PR378 OPEN Draft head/base/mergeability/auto-merge, zero unresolved threads, exact three workflow runs, active schema-v3 intent and digests, Ruleset21023698 active strict merge-only baseline/state-gate policy, independent audit acceptance, and attestation expiry margin; stop on any drift",
      "phase": "pre_landing_observation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue367_pr378_landing.audit_comment",
      "command": "create exactly one PR378 independent exact-head audit comment binding accepted head/base, Luna ACCEPTED_EXACT_HEAD, Decision/Plan/intent digests and exact workflow runs; state that it grants no merge authority; read back exact comment id/author/body and do not retry an unknown result",
      "phase": "audit_publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr378_landing.attestation",
      "command": "create exactly one inert PR378 placeholder comment containing nonce pr378-owner-attestation-placeholder-v1-8f9a7c75 and no attestation marker; read back its numeric comment id; compute canonical approval and attestation digests; edit that same comment exactly once into the unique active schema-v3 MAINLINE_MERGE_APPROVAL_ATTESTATION bound to PR378/head/base/intent/workflow runs/owner and expiry 2026-08-26T12:30:00Z; read back and require canonical premerge validation PASS; reserve one additional edit only to revoke/remove marker if landing stops before merge",
      "phase": "attestation_publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr378_landing.ready",
      "command": "re-observe every bound fact and expiry margin, then mark PR378 Ready exactly once; require a new ready_for_review State Gate pull_request run on exact head attempt1 SUCCESS; on failure do not merge and use at most one convert-to-draft plus reserved attestation revocation edit",
      "phase": "ready_gate",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr378_landing.merge",
      "command": "immediately before merge require main still locked base, PR378 OPEN non-Draft exact head/base MERGEABLE/CLEAN, auto-merge disabled, baseline and Decision Preflight exact-head SUCCESS, fresh Ready State Gate SUCCESS, zero unresolved threads, strict Ruleset unchanged, unique active attestation unchanged and unexpired; perform exactly one owner expected-head merge with method merge and sha 8f9a7c75ac428253669393b420c4b8c36ec29997; unknown result is resolved read-only and never retried",
      "phase": "owner_merge",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr378_landing.postmerge",
      "command": "verify merged_by owner, new main equals merge commit, ordered parents locked base and accepted head, merge tree equals d23cad01b907432166fe5902ffd77e4be40b1598, fresh State Gate push attempt1 SUCCESS and canonical mainline validation 46 checks zero failed with receipt EMITTED; only then create exactly one non-marker PR receipt comment and read it back",
      "phase": "postmerge_validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access",
        "local_static_check"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue367_pr378_landing.close_issue",
      "command": "only after postmerge validation and receipt readback, close Issue367 exactly once and verify CLOSED/completed; do not close Issue370, which retains its stale-PR scenario acceptance",
      "phase": "issue_close",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    ".codex-skills/**",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml",
    "reverse_agent/project_state.py",
    "reverse_agent/decision_preflight.py",
    "reverse_agent/post_final_evidence_sync.py",
    "reverse_agent/project_ci.py",
    "reverse_agent/project_jobs.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/github_adapter.py",
    "reverse_agent/architecture/**",
    "reverse_agent/base_platform/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/worktree_state.py",
    "frontend/**",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "project_state/schemas/**",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_authority_adapter.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/platform_v1/test_task_service.py",
    "tests/base_platform/**",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_execution_evidence.py",
    "tests/test_decision_preflight.py",
    "tests/test_trusted_command_runner.py"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "reset",
    "clean",
    "stash",
    "restore",
    "amend",
    "history_rewrite",
    "unknown_binary_execution",
    "secrets",
    "destructive_delete",
    "privileged_remote_execution",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "auth_store_read",
    "runner_dispatch",
    "workflow_rerun",
    "tag_or_release",
    "deployment",
    "issue_comment",
    "dependency_install",
    "browser_execution",
    "snapshot_update",
    "arbitrary_remote_browsing",
    "external_url_navigation",
    "offensive_security_or_network_attack_work",
    "second_decision_commit",
    "make_state_gate_push_pre_merge",
    "broad_dependency_change",
    "new_gate_family",
    "new_decision_artifact_family",
    "new_receipt_artifact_family",
    "modify_issue345_decision",
    "modify_issue360_branch_or_pr",
    "modify_issue363_branch_or_pr",
    "modify_issue364_decision",
    "revisit_issue283_protection",
    "mark_ready_pr360",
    "merge_pr360",
    "close_pr360",
    "rebase_pr360",
    "start_issue358",
    "start_issue363",
    "delete_or_rotate_inherited_active_intent",
    "second_post_publication_binding_commit",
    "reuse_v1_or_v2_decision_or_binding",
    "create_owner_merge_attestation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "known_binary_execution_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "mark_ready_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": true,
    "github_pr_comment_allowed": true,
    "github_pr_creation_allowed": false,
    "github_pr_close_allowed": false,
    "remote_observation_read_only_allowed": true,
    "github_ruleset_mutation_allowed": false
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/command_plan.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/startup_snapshot.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/bootstrap_state.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/transition_command_plan_preview.json",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/transition_preflight_result.json",
      "minimum_risk": "R2"
    }
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "ci_network_exceptions": [
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --event-path \"$GITHUB_EVENT_PATH\""
  ],
  "github_ruleset_mutation_allowed": false,
  "issue_close_allowed": true,
  "pr_comment_create_limit": 3,
  "pr_comment_edit_limit": 2,
  "audit_comment_create_limit": 1,
  "attestation_placeholder_create_limit": 1,
  "attestation_finalize_edit_limit": 1,
  "attestation_revoke_edit_limit": 1,
  "receipt_comment_create_limit": 1,
  "convert_to_draft_attempt_limit": 1,
  "issue_close_attempt_limit": 1,
  "external_authority_branch_push_limit": 1,
  "bound_repository": "dddd2024/reverse-agent",
  "bound_issue": 367,
  "bound_pr": 378,
  "bound_owner": "dddd2024",
  "bound_base_sha": "9f5fa5a7c9846352346daf44c2d063bf8f6fb3bf",
  "bound_head_sha": "8f9a7c75ac428253669393b420c4b8c36ec29997",
  "bound_merge_method": "merge",
  "bound_merge_tree_sha": "d23cad01b907432166fe5902ffd77e4be40b1598",
  "bound_ruleset_id": 21023698,
  "bound_ruleset_strict_required_checks": true,
  "bound_workflow_runs": [
    {
      "name": "CI",
      "run_id": 32954647789,
      "workflow_file": ".github/workflows/ci.yml",
      "event": "pull_request",
      "run_attempt": 1,
      "head_sha": "8f9a7c75ac428253669393b420c4b8c36ec29997",
      "conclusion": "success"
    },
    {
      "name": "Decision Preflight",
      "run_id": 32954647707,
      "workflow_file": ".github/workflows/decision-preflight.yml",
      "event": "pull_request",
      "run_attempt": 1,
      "head_sha": "8f9a7c75ac428253669393b420c4b8c36ec29997",
      "conclusion": "success"
    },
    {
      "name": "State Gate (pull_request)",
      "run_id": 32954647719,
      "workflow_file": ".github/workflows/state-gate.yml",
      "event": "pull_request",
      "run_attempt": 1,
      "head_sha": "8f9a7c75ac428253669393b420c4b8c36ec29997",
      "conclusion": "success"
    }
  ],
  "bound_intent_id": "pr378_issue367_engineering_landing_boundary_r2_v4",
  "bound_intent_digest": "sha256:34efd172d8695c4fc7829eb23d57ae90cbdf8b8e10f7f319cdc969f093ba4399",
  "bound_decision_digest": "e411ef0ba32b1f8d6f63d2bdbc94cf3ded13a2a6343bbc6bd23a641a649ded99",
  "bound_command_plan_digest": "0cb4ed0b90b8df86f3e1c116409e9c1d30cb2a19172575d4d430b0f443a28102",
  "bound_approval_payload_digest": "sha256:a08844afb4309d22f2e251dce16302c26f61453f9dbe2c84650eb0703eb4e581",
  "attestation_id": "attestation_pr378_issue367_owner_landing_v1",
  "attestation_expires_at": "2026-08-26T12:30:00Z",
  "attestation_placeholder_nonce": "pr378-owner-attestation-placeholder-v1-8f9a7c75",
  "independent_audit_outcome": "ACCEPTED_EXACT_HEAD",
  "required_fresh_ready_state_gate": true,
  "expected_postmerge_validation_checks": 46,
  "expected_postmerge_validation_failures": 0
}
```
