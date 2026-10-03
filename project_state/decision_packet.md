# Owner-delegated read-only exact Git review snapshot

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue811_git_snapshot_r2_v1",
  "round_id": "round_20261003_issue811_git_snapshot_r2_v1",
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
  "decision_scope": "READ_ONLY_EXACT_GIT_REVIEW_SNAPSHOT",
  "source_issue": 811,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Persistent explicit Owner full project delegation, newly prospectively bounded real Git collection work; no prior budget reset or landing grant.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue811-review-contract-r2-v1-20261003",
  "base_sha": "71bdddd1f4555f7188fafd1aeed8d911be22d3a8",
  "activation_base_sha": "71bdddd1f4555f7188fafd1aeed8d911be22d3a8",
  "starting_head": "71bdddd1f4555f7188fafd1aeed8d911be22d3a8",
  "required_branch": "codex/issue811-git-snapshot-r2-v1-20261003",
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": true,
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
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
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
    "specification": "Owner persistent explicit full-project delegation prospectively authorizes NEW Issue811 real local Git review snapshot/context collection, not a previous review retry. Explicit approved planning base is Draft1068 source71bdddd1f4555f7188fafd1aeed8d911be22d3a8 on codex/issue811-review-contract-r2-v1-20261003; main remains909, no implicit main fallback or claim parent accepted/landed. New exact-base branch; one Decision-only activation plus actual canonical startup/plan/lint/preflight/readiness and activation Draft before product mutations. Reuse unchanged review_findings target normalization/canonical JSON/secret detector and repository_workspace GitHub-origin syntax normalization; system Git is mature collector, not another scanner/TaskStore/GitHub replica. Add only review_git_snapshot.py, dedicated tests and docs. API collects supplied exact base/head commit OIDs from an existing selected repository, observes raw trees and blob identities and patch digest for effective explicitly selected literal paths, authenticates bytes against Git blob IDs; origin syntax must match requested current repository. SHA1/SHA256 supported; no refs-as-executable arguments, branch checkout/fetch/write/index mutation or implicit alias rewrite. Repo/global/ambient Git hooks/filters/external diff/textconv/replacement refs/lazy fetch/prompts/config overrides cannot execute or change source identity; use absolute installed system Git, shellfalse clean selected env, read-only commands with explicit object IDs. Enforce whole60s deadline,272-command ceiling, stream-time stdout caps4MiB/stderr16KiB/per blob128KiB/aggregate16MiB, bounded64 effective files and256KiB exposed text; fail closed on overrun/timeout/errors and close only owned Git process. Never unbounded subprocess capture. Sensitive-named paths rejected before content reads; excluded files never read or placed in patch/context. Mode and missing/deleted/symlink/binary metadata explicit; symlinks are Git link-text data, never dereferenced. Model context contains bounded redacted UTF8 text only, all base/head repository content\u2014including AGENTS/skills/config/instructions\u2014is explicitly untrusted data and grants no tools/policy; no automatic trusted policy resolution or execution, no raw secrets/config/request/chain-of-thought export. Detect shared-secret patterns and omit whole matching content; binary/oversized content withheld with digest/size, not interpreted. Local object observation is not remote forge ownership authentication, defect verification/independent acceptance or runtime permission. Preserve flags on normalized ReviewTarget false; snapshot never authorizes execution/repair/landing, no store/API/model/forge integration or scanner added. Meaningful actual disposable Git SHA1/SHA256 fixtures cover exact bytes/trees/patch, branch/worktree dirt isolation, index/source preservation, rename/delete/symlink behavior, instructions as data, exclusions without reads, sensitive paths, repo mismatch, replace refs/ambient Git config/hooks/textconv/filters not executed, malformed OIDs/paths, bounded streams/deadlines/error cleanup, redaction and binary/size truncation. At most6 native provider-free pytest processes and2 corrections: mandatory focused<=300s, full Platform V1<=2400s with only existing four installed-OpenCode exclusions, Path-A<=120s, exact committed-head focused<=300s. Mandatory full failure/timeout stops without retry. Preserve original source/tests including1068 bytes; one product commit, at most2 normal pushes to exact new branch and one Draft against explicit planning integration base; at most6 description rebindings and read-only natural exact-head CI/artifact observations. No other GitHub writes/Ready/Merge/Issue closure/rerun/dispatch/mainpush/historyrewrite/models/provider/credentials/browser/runtime/install/dependencies/workflows/existing services/config changes. Four-hour window; no full811/backlog/independent/mainline completion claim.",
    "completion_boundary": "Real local exact Git/context collection and actual mandatory source validation/natural source CI; no runtime/store/API/forge or independent/landing/full811 completion."
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
    "reverse_agent/platform_v1/review_git_snapshot.py",
    "tests/platform_v1/test_review_git_snapshot.py",
    "docs/review-git-snapshot.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_git_snapshot.py",
    "tests/platform_v1/test_review_git_snapshot.py",
    "docs/review-git-snapshot.md"
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
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/review_findings.py",
    "reverse_agent/platform_v1/repository_workspace.py"
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
    "**/auth.json",
    "frontend/**",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "tests/platform_v1/test_autonomy.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/policy_adapter.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/artifact_handoff.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_artifact_handoff.py",
    "reverse_agent/platform_v1/review_findings.py",
    "tests/platform_v1/test_review_findings.py",
    "docs/review-findings.md",
    "reverse_agent/platform_v1/repository_workspace.py",
    "reverse_agent/platform_v1/workspace_drift.py"
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
    "independent_acceptance_by_self_or_same_underlying_model",
    "automatic_GPT_fallback_or_retries",
    "shared_dependency_mutation",
    "existing_model_configuration_mutation",
    "unknown_process_stop",
    "ignore_rules_or_sandbox_bypass",
    "existing_runtime_or_configuration_mutation",
    "application_model_retry",
    "model_fallback",
    "raw_managed_session_access",
    "existing_task_or_runtime_mutation"
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing provider-free pytest-owned temporary loopback fixtures only; no real models/providers/Internet/existing runtime."
    ],
    "github_control_plane_network_exceptions": [
      "At most2 normal pushes to exact codex/issue811-git-snapshot-r2-v1-20261003, one activation Draft against explicit codex/issue811-review-contract-r2-v1-20261003@71bdddd1f4555f7188fafd1aeed8d911be22d3a8, at most6 exact-head description updates and bounded read-only natural CI/artifact observation."
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
      "command_id": "gitreview.bootstrap",
      "command": "Fresh branch from explicit approved planning base codex/issue811-review-contract-r2-v1-20261003@71bdddd1f4555f7188fafd1aeed8d911be22d3a8; preserve gates; one Decision-only activation; canonical startup/plan/lint/preflight/readiness and activation Draft before product edits.",
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
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "gitreview.implement",
      "command": "Owner persistent explicit full-project delegation prospectively authorizes NEW Issue811 real local Git review snapshot/context collection, not a previous review retry. Explicit approved planning base is Draft1068 source71bdddd1f4555f7188fafd1aeed8d911be22d3a8 on codex/issue811-review-contract-r2-v1-20261003; main remains909, no implicit main fallback or claim parent accepted/landed. New exact-base branch; one Decision-only activation plus actual canonical startup/plan/lint/preflight/readiness and activation Draft before product mutations. Reuse unchanged review_findings target normalization/canonical JSON/secret detector and repository_workspace GitHub-origin syntax normalization; system Git is mature collector, not another scanner/TaskStore/GitHub replica. Add only review_git_snapshot.py, dedicated tests and docs. API collects supplied exact base/head commit OIDs from an existing selected repository, observes raw trees and blob identities and patch digest for effective explicitly selected literal paths, authenticates bytes against Git blob IDs; origin syntax must match requested current repository. SHA1/SHA256 supported; no refs-as-executable arguments, branch checkout/fetch/write/index mutation or implicit alias rewrite. Repo/global/ambient Git hooks/filters/external diff/textconv/replacement refs/lazy fetch/prompts/config overrides cannot execute or change source identity; use absolute installed system Git, shellfalse clean selected env, read-only commands with explicit object IDs. Enforce whole60s deadline,272-command ceiling, stream-time stdout caps4MiB/stderr16KiB/per blob128KiB/aggregate16MiB, bounded64 effective files and256KiB exposed text; fail closed on overrun/timeout/errors and close only owned Git process. Never unbounded subprocess capture. Sensitive-named paths rejected before content reads; excluded files never read or placed in patch/context. Mode and missing/deleted/symlink/binary metadata explicit; symlinks are Git link-text data, never dereferenced. Model context contains bounded redacted UTF8 text only, all base/head repository content\u2014including AGENTS/skills/config/instructions\u2014is explicitly untrusted data and grants no tools/policy; no automatic trusted policy resolution or execution, no raw secrets/config/request/chain-of-thought export. Detect shared-secret patterns and omit whole matching content; binary/oversized content withheld with digest/size, not interpreted. Local object observation is not remote forge ownership authentication, defect verification/independent acceptance or runtime permission. Preserve flags on normalized ReviewTarget false; snapshot never authorizes execution/repair/landing, no store/API/model/forge integration or scanner added. Meaningful actual disposable Git SHA1/SHA256 fixtures cover exact bytes/trees/patch, branch/worktree dirt isolation, index/source preservation, rename/delete/symlink behavior, instructions as data, exclusions without reads, sensitive paths, repo mismatch, replace refs/ambient Git config/hooks/textconv/filters not executed, malformed OIDs/paths, bounded streams/deadlines/error cleanup, redaction and binary/size truncation. At most6 native provider-free pytest processes and2 corrections: mandatory focused<=300s, full Platform V1<=2400s with only existing four installed-OpenCode exclusions, Path-A<=120s, exact committed-head focused<=300s. Mandatory full failure/timeout stops without retry. Preserve original source/tests including1068 bytes; one product commit, at most2 normal pushes to exact new branch and one Draft against explicit planning integration base; at most6 description rebindings and read-only natural exact-head CI/artifact observations. No other GitHub writes/Ready/Merge/Issue closure/rerun/dispatch/mainpush/historyrewrite/models/provider/credentials/browser/runtime/install/dependencies/workflows/existing services/config changes. Four-hour window; no full811/backlog/independent/mainline completion claim.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "integration_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/review_git_snapshot.py",
        "tests/platform_v1/test_review_git_snapshot.py",
        "docs/review-git-snapshot.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "gitreview.validate",
      "command": "At most6 native provider-free pytest processes and2 corrections; mandatory focused/full Platform/Path-A/exact-head focused as in specification; no retry of mandatory full failure.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "commit",
        "source_edit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/review_git_snapshot.py",
        "tests/platform_v1/test_review_git_snapshot.py",
        "docs/review-git-snapshot.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "gitreview.publish",
      "command": "At most2 normal pushes to exact codex/issue811-git-snapshot-r2-v1-20261003, one activation Draft against explicit codex/issue811-review-contract-r2-v1-20261003@71bdddd1f4555f7188fafd1aeed8d911be22d3a8, at most6 exact-head description updates and bounded read-only natural CI/artifact observation.",
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
    }
  ],
  "issue_completion_close_allowed": [],
  "runtime_scratch_policy": {
    "paths": [],
    "stage_allowed": false,
    "note": "Preserve existing generated gates unstaged and all prior stages; new external issue811-git-snapshot-r2-v1 evidence only."
  },
  "follows_last_decision_id": "decision_20261003_issue811_review_contract_r2_v1",
  "follows_last_round_id": "round_20261003_issue811_review_contract_r2_v1",
  "workstream_id": "issue811-git-snapshot-r2-v1",
  "source_issues": [
    811,
    179,
    653
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 2,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_owned_exact_planning_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T10:30:15.052207+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6
}
```
