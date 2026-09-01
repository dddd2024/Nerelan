# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260901_issue444_oauth_deadline_repair_r3_v3",
  "round_id": "round_20260901_issue444_oauth_deadline_repair_r3_v3",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260901_issue444_oauth_deadline_repair_r3_v2",
  "follows_last_round_id": "round_20260901_issue444_oauth_deadline_repair_r3_v2",
  "previous_audit_outcome": "ISSUE444_V2_INTENT_BINDING_REJECTED_ACTIVATION_BASE_MISMATCH_BEFORE_PRODUCT_MUTATION",
  "supersedes_decision_id": "decision_20260901_issue444_oauth_deadline_repair_r3_v2",
  "workstream_id": "issue444-oauth-deadline-repair-r3-v3",
  "source_issue": 444,
  "parent_issue": 438,
  "source_pr": 445,
  "integration_base_ref": "main",
  "base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "activation_base_sha": "eb1cbfa520582988e90e83d798d53379ba537fa8",
  "starting_head": "7775e63d5352d6f259e6de69f351ec214b206864",
  "required_branch": "owner/issue438-auth-completion-r3-v1",
  "preserved_worktree_reuse_allowed": true,
  "fresh_worktree_creation_required": false,
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R3",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "pr_creation_allowed": false,
  "issue_comment_allowed": true,
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
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "landing_revalidation_required_for_actions": ["ready_for_review", "merge"],
  "landing_revalidation_required_when_draft": true,
  "owner_attestation_required_for_ready_state": true,
  "attestation_head_must_match_current_pr_head": true,
  "ready_state_synchronize_must_revalidate": true,
  "converted_to_draft_returns_to_draft_semantics": true,
  "malformed_event_path_fail_closed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify remote main remains eb1cbfa520582988e90e83d798d53379ba537fa8 and PR 445 remains Draft at fd44c6d50a5d3f083182c6c76ab485a8462fa5bb",
    "commit this immutable successor R3 Decision before any product mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue444v3.materialize_activation_packet",
      "command": "after the immutable Decision activation commit run startup snapshot command-plan compilation transition lint and preflight and commit only the declared generated gate artifacts",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue444v3.repair_absolute_deadline",
      "command": "make OAuth flow completion and start continuation atomically fail expired when the injected monotonic clock is at or beyond the absolute deadline even when the timer thread is delayed; preserve pre-deadline success invalid-code retry behavior provider-owned sessions and sanitized errors; add deterministic delayed-timer and legitimate-control tests",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "test_edit", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/account_auth.py",
        "tests/test_model_access.py"
      ]
    },
    {
      "command_id": "issue444v3.bind_existing_pr",
      "command": "archive the prior PR 445 schema-v3 intent byte-for-byte and bind active intent exactly once to PR 445 locked base current successor Decision current generated Command Plan baseline workflow profile and merge-only policy",
      "phase": "post_publication_binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": false,
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr445_v1.json"
      ]
    },
    {
      "command_id": "issue444v3.validate_product",
      "command": "run the deterministic delayed-timer reproductions legitimate controls focused Model Access trusted-host and OpenCode transport suites full Platform V1 blocking suite mainline landing suites transition lint publication readiness and git diff check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "integration_test", "local_static_check"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue444v3.publish_existing_draft",
      "command": "after all local validation normally push the exact existing PR 445 branch once update only its body and require fresh exact-head CI Model Access Frontend Playwright State Gate and Decision Preflight before independent audit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "pull_request_update", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue444v3.independent_exact_head_audit",
      "command": "an independent auditor that did not implement the repair reproduces delayed timer behavior at before equal and after deadline checks both authorize and callback paths confirms no refresh or success after expiry and rechecks the exact remote head and required workflows then records ACCEPTED or REWORK_REQUIRED on PR 445",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "remote_observation",
      "operations": ["code_read", "unit_test", "pull_request_comment"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue444v3.owner_landing",
      "command": "only after independent exact-head acceptance fresh successful exact-head workflows zero unresolved threads unchanged locked base valid successor merge intent and repository-owned landing attestation mark PR 445 ready once merge once using merge commit with expected-head protection verify main and close Issues 444 441 and 438",
      "phase": "landing",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["mark_ready", "merge", "issue_close", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    }
  ],
  "allowed_source_paths": [
    "reverse_agent/model_access/account_auth.py",
    "tests/test_model_access.py"
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr445_v1.json",
    "reverse_agent/model_access/account_auth.py",
    "tests/test_model_access.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr445_v1.json",
    "reverse_agent/model_access/account_auth.py",
    "tests/test_model_access.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/opencode_server_transport.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "reverse_agent/mainline_landing.py",
    "tests/platform_v1/test_trusted_host.py",
    "tests/platform_v1/test_opencode_server_transport.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "requirements*.txt",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/base_platform/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/contracts.py",
    "reverse_agent/model_access/store.py",
    "reverse_agent/model_access/service.py",
    "frontend/**",
    "docs/**",
    "tests/test_connection_binding.py",
    "tests/platform_v1/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/integration_baselines/**",
    "project_state/mainline_recoveries/**",
    "project_state/schemas/**",
    "project_state/context/**",
    "project_state/evidence/**",
    "project_state/proposed_state/**",
    "project_state/domains/**",
    "project_state/jobs/**",
    "project_state/roadmap/**",
    "project_state/solve_tasks/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "squash",
    "dependency_install",
    "workflow_change",
    "live_model_call",
    "model_api_invocation",
    "runner_dispatch",
    "credential_access",
    "live_provider_access",
    "known_browser_execution",
    "tag_or_release",
    "deployment",
    "history_rewrite",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "network_attack_or_offensive_security_work",
    "plaintext_secret_storage",
    "custom_oauth_implementation"
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
    "local_network_exceptions": [
      "normal push and PR 445 body update after local validation",
      "independent audit comment owner attestation mark-ready expected-head merge and issue close for Issue 444"
    ],
    "ci_network_exceptions": [
      "provider-free fake HTTP fixtures bound only to 127.0.0.1"
    ],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": "project_state/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/model_access/account_auth.py", "minimum_risk": "R3"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ]
}
```

## Acceptance criteria

1. The delayed-timer reproducer cannot return `authenticated` or `verification_pending`, cannot call refresh, and returns the canonical `account login expired` error when the absolute monotonic deadline is equal to or exceeded.
2. The same absolute deadline is enforced after blocking provider auth-method discovery and authorization, without relying on timely timer scheduling.
3. Successful callback completion strictly before the deadline remains successful; invalid callback input remains retryable; provider-owned session storage and sanitized output contracts do not change.
4. Timer expiry, absolute-clock expiry, successful finish, cancel and close remain idempotent and close the transient child at most once.
5. Only `reverse_agent/model_access/account_auth.py` and `tests/test_model_access.py` change as product/test paths.
6. Required local checks, fresh exact-head workflows and an independent exact-head audit all accept one immutable head with unchanged locked base.
7. Landing occurs only after valid schema-v3 intent and owner attestation, using one Ready action and one expected-head merge; no auto-merge, direct-main push, history rewrite, tag, release or deployment occurs.

## Execution policy

- The owner explicitly approved this exact minimal continuation after the prior Decision exhausted its product-commit budget; the approval is represented only by this immutable successor Decision and its generated Command Plan.
- No provider/model call, browser authorization, credential access, dependency install, workflow mutation, attack work or new product scope is authorized.
- The later PR comment claiming Owner acceptance of `fd44c6d5` is non-authoritative and cannot override the reproducible independent-audit blocker.
- Any Decision mutation after activation, main/base/head drift, out-of-scope path, failed gate/check, audit rejection, unresolved review thread or attestation failure stops the round.
