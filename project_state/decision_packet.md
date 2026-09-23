# Bounded GPT OAuth network and failure presentation repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
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
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "GPT_OAUTH_NETWORK_AND_FAILURE_PRESENTATION",
  "source_issue": 982,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner execution",
  "approval_basis": "Explicit user delegation of full Owner completion and independent subagent audit, plus current instruction to finish GPT authentication and supervise subsequent Nerelan work. This fresh bounded source-repair round preserves user credentials and unrelated work. It authorizes no live OAuth/model execution or landing; those require subsequent exact-result stages.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "main",
  "base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "activation_base_sha": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "starting_head": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "fresh_base": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "current_main_expected": "3b9eb3806ca59e119d2f8db36537b7efe593c729",
  "required_branch": "codex/gpt-oauth-network-r3-v1-20260923",
  "workstream_id": "issue982-gpt-oauth-network-r3-v1",
  "follows_last_decision_id": "decision_20260920_issue913_reviewed_goldens_r3_v3",
  "follows_last_round_id": "round_20260920_issue913_reviewed_goldens_r3_v3",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
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
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/service.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/test_model_access.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/connection-binding-flow.test.tsx",
    "frontend/tests/model-settings.test.tsx",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/account_auth.py",
    "reverse_agent/model_access/service.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/test_model_access.py",
    "frontend/src/schemas/model-access.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/components/connection-binding-editor.tsx",
    "frontend/src/routes/settings.tsx",
    "frontend/tests/connection-binding-flow.test.tsx",
    "frontend/tests/model-settings.test.tsx",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "local_browser_execution",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Repair only provider-owned OAuth child networking and truthful account-auth failure presentation. Validate explicitly supported HTTP(S) proxy variables; reject userinfo, control characters, query/fragment, ambiguous case conflicts and invalid settings without silent direct fallback. Preserve loopback bypass and never print proxy values or copy arbitrary environment. Preserve failed terminal status and safe error classification, reset on a new login, keep cancellation and expiry semantics. Reconcile frontend failed callback state with backend and provide Chinese recovery guidance. No credential reads/writes, OAuth reimplementation, service-policy bypass, model call or endpoint substitution. Do not modify assistant-evidence logic belonging to Draft981.",
    "completion_boundary": "Provider-free exact-head source and component acceptance and independent review; Draft-only. Browser success, unit tests and identity discovery do not prove real authentication or GPT execution. Subsequent runtime and landing stages remain required."
  },
  "runtime_scratch_policy": {
    "paths": [
      "frontend/node_modules/**",
      "frontend/dist/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing ignored frontend dependencies may be copied from F:/Nerelan-first-use-20260923 only after exact package and lockfile equality. No install or tracked dependency mutation."
  },
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
    "ci_network_exceptions": [
      "Only unchanged existing natural workflows provider-free dependencies/tests; no added workflow, manual dispatch or rerun."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Provider-free tests may bind isolated loopback fixture servers only. No provider network, browser login, model or credential access. No local git push."
    ],
    "github_control_plane_network_exceptions": [
      "Observe canonical dddd2024/Nerelan and publish only the exact named branch and one Draft PR against locked main. No Ready, merge, unrelated branch, tag or release."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue982v1.bootstrap",
      "command": "Fresh full Windows checkout F:/Nerelan-issue982-gpt-oauth-network from exact locked base. Verify clean tree and canonical repository; consume immediately preceding independent remote-observation evidence of main and concurrent ownership. This bootstrap command itself performs no network calls. Commit only this APPROVED Decision once. Run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness in sequence. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before source mutation. Never modify activated Decision.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue982v1.implement",
      "command": "Implement the semantic contract only within the exact source/test allowlist. Disposable provider-free development tests may guide fixes before final acceptance, at most 8 development check rounds. No live auth/provider/model or credentials. Freeze implementation in one product commit after development checks. No commit amendment or changes to Draft981 assistant-evidence logic. Preserve other active owner work.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution",
        "unit_test",
        "integration_test",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/model_access/account_auth.py",
        "reverse_agent/model_access/service.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/test_model_access.py",
        "frontend/src/schemas/model-access.ts",
        "frontend/src/lib/model-control-client.ts",
        "frontend/src/components/connection-binding-editor.tsx",
        "frontend/src/routes/settings.tsx",
        "frontend/tests/connection-binding-flow.test.tsx",
        "frontend/tests/model-settings.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue982v1.dependencies",
      "command": "Reuse existing Git/Python/Node/npm. Verify frontend package.json and package-lock.json bytes against F:/Nerelan-first-use-20260923 and copy only matching ignored node_modules. No installation, download or dependency file changes.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue982v1.validate",
      "command": "At the frozen implementation head run python -B -m pytest tests/test_model_access.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_trusted_host.py -q -p no:cacheprovider; frontend npm test, npm run lint, npm run typecheck, npm run build; git diff --check for base-to-head and working tree; sequential startup/plan/lint/preflight/readiness. Any mandatory failure stops this round. Do not weaken tests, thresholds or goldens.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "build",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
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
      "command_id": "issue982v1.publish",
      "command": "After all mandatory local checks and PUBLICATION_READY, verify current remote main equals locked base and ownership remains unchanged. Through canonical GitHub Git API publish only the identical locally authored Decision and implementation blob/tree/commit graph to codex/gpt-oauth-network-r3-v1-20260923. Verify every SHA before ref creation. At most one successful ref publication and one Draft PR against main binding exact head and immutable Decision. No remote semantic source editing, local git push, merge or mark-ready.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue982v1.natural_checks",
      "command": "Only the unchanged existing workflows naturally execute exact-head CI, Decision Preflight, State Gate, Model Access and Frontend Playwright on ci_only. Require all SUCCESS and actual full pytest diagnostic exit zero with no native JUnit failures. Agent observation belongs to the separate remote_observation command. No dispatch, rerun, manual CI, snapshots or threshold changes. Existing unchanged CI dependency setup only. Any visual snapshot failure stops the round.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue982v1.audit",
      "command": "Read canonical Actions/run identities, results and artifacts through remote_observation; this command does not execute CI. Independent exact-head audit must verify bounded networking, no secret copying/logging, lifecycle failure persistence and expiry/cancel semantics, frontend failure reconciliation, all deterministic and natural evidence, allowed paths, base freshness and frozen PR981 head. Keep Draft unmerged. Report runtime OAuth and GPT invocation as not verified in this provider-free round.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "concurrent_work_preservation": {
    "pr": 981,
    "frozen_head": "849af4ae2039bb7d30ebb442404a567e5c7152f2",
    "shared_path": "reverse_agent/platform_v1/opencode_executor.py",
    "policy": "PR981 is paused while this round runs. Before activation and publication reobserve its exact frozen head; any mutation stops for revised coordination. This round may edit only the account-auth environment builder and adjacent pure helper in the shared file, never _bounded_value or assistant evidence. Do not import PR981 commits. Paths of other owners PR978 and PR979 remain untouched."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "frontend/package.json",
    "frontend/package-lock.json",
    "reverse_agent/platform_v1/opencode_server_transport.py"
  ]
}
```
