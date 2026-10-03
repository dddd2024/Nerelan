# Owner-delegated exact review target and finding contract

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_issue811_review_contract_r2_v1",
  "round_id": "round_20261003_issue811_review_contract_r2_v1",
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
  "decision_scope": "EXACT_REVIEW_TARGET_FINDING_AND_FEEDBACK_CONTRACT",
  "source_issue": 811,
  "parent_issue": 137,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / current explicit full project delegation",
  "approval_basis": "Persistent explicit Owner full-project delegation authorizes necessary new811 provider-free contract work, prospectively bounded; no prior reset/landing grant.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "codex/issue811-review-contract-r2-v1-20261003",
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
    "specification": "Owner persistent explicit full-project delegation prospectively authorizes NEW Issue811 REVIEWAGENT-1 provider-free exact target/finding contract work. Fresh main9092911f41a089e249f27c883526904299be1d17 and current44 open PR file lists observed: three new product paths have no other active owner; do not edit reserved executor/store/runtime/authority code. Current project policy_adapter.validate_work_item rejects R2 before any backend, so authorized Codex fallback performs this R2 bootstrap/source work without changing/bypassing that adapter or retrying a model. Preserve all old Decisions/budgets/branches/review records; this is not another PR1067 review or model retry. Fresh exact-main-base branch and one Decision-only activation; actual canonical startup/plan/lint/preflight/readiness and one exact activation Draft must precede product changes. Implement bounded pure data API in review_findings.py: immutable canonical ReviewTarget binds repository/forge/change-request, base/head refs and same-family 40/64-char commit/tree OIDs, patch digest, exact reviewed/excluded file paths and review profile/observation digest; reject unknown/malformed/control/unbounded fields, require nonempty effective reviewed scope. Caller-provided identities are claims, not verified Git identity. ReviewFinding binds derived exact target generation/digest, rule/category/severity/confidence, scoped literal path and bounded line range/symbol/summary, source class and digest-only evidence refs; no raw logs/chain-of-thought/config/request text. Reuse existing canonical JSON/digest and secret redaction functions without edits or a new scanner/verifier/DB. Deterministic dedupe uses explicit shared rule+location+exact target identity, stable ordering and deterministic-source preference while preserving contributing sources/evidence; no fabricated semantic duplicate detection or model finding promoted to proven defect. A new target generation conservatively marks prior findings stale; mere disappearance must not mark fixed. Explicit bounded ACKNOWLEDGED/NOT_REPRODUCIBLE/DISMISSED_WITH_REASON feedback retains reason+evidence and cannot grant acceptance, authority, global learned policy or automatic code repair; original finding immutable. Never accept stale/mismatched target feedback, unsafe paths, secret-bearing serialized summaries, malformed identities, mutating references or conflicting finding IDs. All verified-evidence/independent-acceptance/execution-authorized/repair-authorized/landing-authorized flags remain false and cannot be supplied to grant authority. Expose no IO/store/Git/process/network/browser/provider or mutation methods. Add meaningful seeded finding, exact SHA1/SHA256 identity, input mutation, scope containment, stable dedupe, false-positive feedback, stale-generation and authority-injection regressions, including actual Python-surrogate rejection premise with sanitized deterministic fixture data, not fake live reviews or tests. Docs explicitly distinguish normalization from trusted evidence validation and list still-unimplemented runtime/API/model/forge/incremental impact/human acceptance phases of811. No full811/backlog completion claim. At most6 native provider-free pytest processes and2 bounded correction rounds; mandatory focused new review suite<=180s, full Platform V1<=2400s excluding only four already-excluded installed-OpenCode tests, Path-A<=120s, exact committed-head focused<=180s; at most2 additional development checks if justified. Mandatory full failure/timeout stops publication without retry. Preserve every original source/test byte at main base except three new paths. One product commit, at most2 normal pushes total to exact new branch, one activation Draft against explicit main@909; at most6 exact-head Draft description updates, read-only natural exact-head CI/artifact inspection. No comments/Issue writes/closure/Ready/Merge/main push/rewrite/dispatch/rerun/model/provider/credentials/runtime/browser/install/dependencies/workflows/security or original services/config changes. Four-hour window. Completion only this source candidate and actual mandatory checks/natural source CI; formal independent acceptance and all later811/runtime/user-journey/landing remain separate.",
    "completion_boundary": "REVIEWAGENT-1 pure provider-free source and actual mandatory validation/natural source CI, not trusted identity/independent approval/runtime/full811/landing."
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
    "reverse_agent/platform_v1/review_findings.py",
    "tests/platform_v1/test_review_findings.py",
    "docs/review-findings.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/review_findings.py",
    "tests/platform_v1/test_review_findings.py",
    "docs/review-findings.md"
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
    "tests/platform_v1/test_artifact_handoff.py"
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
      "At most2 normal pushes to exact codex/issue811-review-contract-r2-v1-20261003, one activation Draft against explicit main@9092911f41a089e249f27c883526904299be1d17, at most6 exact-head Draft description updates and bounded read-only natural CI/artifact observation. No other writes."
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
      "command_id": "review.bootstrap",
      "command": "Fresh main909 exact-base branch, preserve existing gates, one Decision-only activation; actual startup/plan/lint/preflight/readiness, one activation push and exact Draft before product changes.",
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
      "command_id": "review.implement",
      "command": "Owner persistent explicit full-project delegation prospectively authorizes NEW Issue811 REVIEWAGENT-1 provider-free exact target/finding contract work. Fresh main9092911f41a089e249f27c883526904299be1d17 and current44 open PR file lists observed: three new product paths have no other active owner; do not edit reserved executor/store/runtime/authority code. Current project policy_adapter.validate_work_item rejects R2 before any backend, so authorized Codex fallback performs this R2 bootstrap/source work without changing/bypassing that adapter or retrying a model. Preserve all old Decisions/budgets/branches/review records; this is not another PR1067 review or model retry. Fresh exact-main-base branch and one Decision-only activation; actual canonical startup/plan/lint/preflight/readiness and one exact activation Draft must precede product changes. Implement bounded pure data API in review_findings.py: immutable canonical ReviewTarget binds repository/forge/change-request, base/head refs and same-family 40/64-char commit/tree OIDs, patch digest, exact reviewed/excluded file paths and review profile/observation digest; reject unknown/malformed/control/unbounded fields, require nonempty effective reviewed scope. Caller-provided identities are claims, not verified Git identity. ReviewFinding binds derived exact target generation/digest, rule/category/severity/confidence, scoped literal path and bounded line range/symbol/summary, source class and digest-only evidence refs; no raw logs/chain-of-thought/config/request text. Reuse existing canonical JSON/digest and secret redaction functions without edits or a new scanner/verifier/DB. Deterministic dedupe uses explicit shared rule+location+exact target identity, stable ordering and deterministic-source preference while preserving contributing sources/evidence; no fabricated semantic duplicate detection or model finding promoted to proven defect. A new target generation conservatively marks prior findings stale; mere disappearance must not mark fixed. Explicit bounded ACKNOWLEDGED/NOT_REPRODUCIBLE/DISMISSED_WITH_REASON feedback retains reason+evidence and cannot grant acceptance, authority, global learned policy or automatic code repair; original finding immutable. Never accept stale/mismatched target feedback, unsafe paths, secret-bearing serialized summaries, malformed identities, mutating references or conflicting finding IDs. All verified-evidence/independent-acceptance/execution-authorized/repair-authorized/landing-authorized flags remain false and cannot be supplied to grant authority. Expose no IO/store/Git/process/network/browser/provider or mutation methods. Add meaningful seeded finding, exact SHA1/SHA256 identity, input mutation, scope containment, stable dedupe, false-positive feedback, stale-generation and authority-injection regressions, including actual Python-surrogate rejection premise with sanitized deterministic fixture data, not fake live reviews or tests. Docs explicitly distinguish normalization from trusted evidence validation and list still-unimplemented runtime/API/model/forge/incremental impact/human acceptance phases of811. No full811/backlog completion claim. At most6 native provider-free pytest processes and2 bounded correction rounds; mandatory focused new review suite<=180s, full Platform V1<=2400s excluding only four already-excluded installed-OpenCode tests, Path-A<=120s, exact committed-head focused<=180s; at most2 additional development checks if justified. Mandatory full failure/timeout stops publication without retry. Preserve every original source/test byte at main base except three new paths. One product commit, at most2 normal pushes total to exact new branch, one activation Draft against explicit main@909; at most6 exact-head Draft description updates, read-only natural exact-head CI/artifact inspection. No comments/Issue writes/closure/Ready/Merge/main push/rewrite/dispatch/rerun/model/provider/credentials/runtime/browser/install/dependencies/workflows/security or original services/config changes. Four-hour window. Completion only this source candidate and actual mandatory checks/natural source CI; formal independent acceptance and all later811/runtime/user-journey/landing remain separate.",
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
        "reverse_agent/platform_v1/review_findings.py",
        "tests/platform_v1/test_review_findings.py",
        "docs/review-findings.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.validate",
      "command": "At most6 native provider-free pytest processes and2 corrections; mandatory focused/full Platform/Path-A/exact-head focused as specified; preserve original source/tests and reject mandatory full failure without retry.",
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
        "reverse_agent/platform_v1/review_findings.py",
        "tests/platform_v1/test_review_findings.py",
        "docs/review-findings.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "review.publish",
      "command": "At most2 normal exact-branch pushes, one activation Draft against explicit main@9092911f41a089e249f27c883526904299be1d17, at most6 exact-head description rebindings and read-only natural exact-head CI/artifact inspection; no other writes.",
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
    "note": "Existing five generated gates preserved unstaged; external issue811-readiness-v1 and issue811-review-contract-r2-v1 only. No cleanup/runtime changes."
  },
  "follows_last_decision_id": "decision_20261002_takeover_owned_cleanup_r3_v1",
  "follows_last_round_id": "round_20261002_takeover_owned_cleanup_r3_v1",
  "workstream_id": "issue811-review-contract-r2-v1",
  "source_issues": [
    811,
    179,
    653
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 6,
  "development_correction_round_limit": 2,
  "execution_window_hours": 4,
  "integration_observation_surface": "user_local_owned_exact_main_successor",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-03T08:53:03.711795+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 6
}
```
