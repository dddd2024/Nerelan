# Native CLI diagnostic sequencing repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261002_issue985_native_protocol_errors_r3_v1",
  "round_id": "round_20261002_issue985_native_protocol_errors_r3_v1",
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
  "decision_scope": "NATIVE_CODEX_FULL_BINDING_GOAL_TASK_DURABLE_FRONTEND_INTEGRATION",
  "source_issue": 985,
  "parent_issue": 986,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner request in the current conversation",
  "approval_basis": "The Owner explicitly delegated full project takeover and project decisions in this chat, preferring Nerelan and allowing Codex fallback. Actual Nerelan native trial v2 on unchanged product5d54ade9 invoked exactly one native CLI and FAILED with codex_event_after_terminal, no changes/functional evidence; preserve failed Task/window/database/worktree and no retries. Read-only exact installed0.159.2 upstream source proves error emits with Running then turn.failed, and warning/error items may precede turn.started. This separately bounded source-only repair approves exactly the four protocol/executor/test paths below on the current owned product planning branch at exact5d54ade9. It does not inherit or replenish any model/network runtime trial budget: ZERO model calls, app-server sessions, new browsers, installs, auth/config/provider edits, changes to failed store/tasks, fabricated wire captures or acceptance. Existing installed CLI wire source is reference only. Fresh Decision-only activation, real gates and Draft required before code. Preserve all old activated Decisions and five unstaged gates. Independent review/landing separate.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue985-native-codex-integration-r3-v3-20261002",
  "base_sha": "5d54ade9a074290c5f57bbf988b7629bd428a2a0",
  "activation_base_sha": "5d54ade9a074290c5f57bbf988b7629bd428a2a0",
  "starting_head": "5d54ade9a074290c5f57bbf988b7629bd428a2a0",
  "required_branch": "codex/issue985-native-protocol-errors-r3-v1-20261002",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 3,
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
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
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
    "specification": "Fix only native JSONL error/warning handling and redacted public diagnostic evidence. The error event is a critical diagnostic, not a turn terminal: allow repeated errors and subsequent genuine turn.failed; never infer successful access/functionality. Preserve failure after any critical error and never permit completion following it to be accepted; require actual turn terminal or finite error/incomplete classification at EOF. Permit allowlisted pre-turn warning/error items without accepting pre-turn agent/tool items. Expose bounded redacted diagnostics through existing Task EXECUTOR_PROGRESS and existing failure result without raw error payloads, keys, URLs with credentials, process env or stderr. Keep terminal duplication/cross-turn/event/stream/frame/usage/final-message bounds and real timeout/process-tree cleanup unchanged. Add independent semantic provider-free wire regressions for fatal error then failed turn, repeated diagnostics, warning before thread, error-only EOF, no success after critical error, secret-bearing diagnostics and original terminal/UTF8/usage/single-role/functional checks. Use default production parser/executor with existing disposable process fixtures solely as deterministic tests; do not claim these are observed live wire output. No live retry. Functional artifact and reviewer acceptance remain unchanged.",
    "completion_boundary": "Bounded four-file exact-head repair, deterministic native protocol/executor/integration regression checks, diff-check, actual readiness, Draft bound to exact head and natural required CI; zero new models, failed trial remains failed and underlying account/network cause UNKNOWN; no independent acceptance or landing."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/codex_protocol.py",
    "reverse_agent/platform_v1/codex_executor.py",
    "tests/platform_v1/test_codex_protocol.py",
    "tests/platform_v1/test_codex_executor.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/codex_protocol.py",
    "reverse_agent/platform_v1/codex_executor.py",
    "tests/platform_v1/test_codex_protocol.py",
    "tests/platform_v1/test_codex_executor.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "tests/platform_v1/test_artifact_handoff.py",
    "tests/platform_v1/test_functional_execution.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/model_access/os_vault.py",
    "reverse_agent/model_access/credential_relay.py",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "frontend/package*.json",
    "frontend/node_modules/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "**/auth.json"
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "issue_comment",
    "pull_request_comment",
    "raw_credential_read_copy_or_print",
    "API_key_auth",
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass"
  ],
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
    "ci_network_exceptions": [
      "Unchanged natural repository CI dependency setup and provider-free validation only. No new workflow, rerun or dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Exact approved branch normal pushes<=3, one Draft against explicit native integration5d54ade9 and description updates; read-only natural CI/upstream installed CLI source. No comments/Ready/Merge/close/rerun/dispatch."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/platform_v1/functional_validation.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "native.bootstrap",
      "command": "Preserve current runtime and five generated gates externally; fresh exact approved planning base5d54ade9 branch, Decision-only activation, actual startup/command-plan/lint/preflight PRE_EXECUTION_AUTHORIZED and readiness; one exact Draft before source edits.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "local_static_check",
        "command_plan_generation",
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
      "command_id": "native.implement",
      "command": "Fix only native JSONL error/warning handling and redacted public diagnostic evidence. The error event is a critical diagnostic, not a turn terminal: allow repeated errors and subsequent genuine turn.failed; never infer successful access/functionality. Preserve failure after any critical error and never permit completion following it to be accepted; require actual turn terminal or finite error/incomplete classification at EOF. Permit allowlisted pre-turn warning/error items without accepting pre-turn agent/tool items. Expose bounded redacted diagnostics through existing Task EXECUTOR_PROGRESS and existing failure result without raw error payloads, keys, URLs with credentials, process env or stderr. Keep terminal duplication/cross-turn/event/stream/frame/usage/final-message bounds and real timeout/process-tree cleanup unchanged. Add independent semantic provider-free wire regressions for fatal error then failed turn, repeated diagnostics, warning before thread, error-only EOF, no success after critical error, secret-bearing diagnostics and original terminal/UTF8/usage/single-role/functional checks. Use default production parser/executor with existing disposable process fixtures solely as deterministic tests; do not claim these are observed live wire output. No live retry. Functional artifact and reviewer acceptance remain unchanged.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "unit_test",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/codex_protocol.py",
        "reverse_agent/platform_v1/codex_executor.py",
        "tests/platform_v1/test_codex_protocol.py",
        "tests/platform_v1/test_codex_executor.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validate",
      "command": "Exact-head python -B -m pytest tests/platform_v1/test_codex_protocol.py tests/platform_v1/test_codex_executor.py tests/platform_v1/test_codex_integration.py -q -p no:cacheprovider --basetemp under external protocol-repair-v1/checks; git diff --check; immutable test preservation and actual readiness. Provider-free, no installs/models/test weakening. Existing native integration actual proof remains FAILED and independently unaccepted.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "native.publish",
      "command": "Normal pushes<=3 to exact branch, one activation Draft against approved native integration5d54ade9; rebind exact head in description; no comments/Ready/Merge/close/history mutation.",
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
      "command_id": "native.ci",
      "command": "Observe unchanged natural exact-head CI/Decision/State checks, provider-free and zero models. No rerun/dispatch/workflow/dependency change. Author evidence is not independent audit.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "code_read",
        "unit_test",
        "integration_test"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**",
      "frontend/node_modules/**",
      "frontend/vite.config.ts.timestamp-*.mjs",
      "frontend/*.tsbuildinfo"
    ],
    "stage_allowed": false,
    "note": "Preserve all previous runtime and fixture evidence, current owned host22828/frontend11224/browser contexts unchanged. Source-only repair uses external protocol-repair-v1 disposable provider-free checks; no runtime launches or model calls."
  },
  "follows_last_decision_id": "decision_20261002_issue985_native_live_trial_r3_v2",
  "follows_last_round_id": "round_20261002_issue985_native_live_trial_r3_v2",
  "workstream_id": "issue985-native-protocol-errors-v1",
  "source_issues": [
    985,
    986
  ],
  "local_browser_launch_limit": 1
}
```
