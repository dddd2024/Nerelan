# Native candidate lifecycle correction successor

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261002_issue1049_candidate_lifecycle_fix_r3_v1",
  "round_id": "round_20261002_issue1049_candidate_lifecycle_fix_r3_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": []
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "decision_scope": "NATIVE_FIXED_PROFILES_AND_EXACT_CANDIDATE_VALIDATION",
  "source_issue": 1049,
  "parent_issue": 653,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicit delegated Owner request in the current conversation",
  "approval_basis": "Owner explicitly delegated complete project takeover, decisions and GitHub backlog execution; prioritize native project execution with Codex fallback. Existing PR1050 exact01f86e98914af7b5e07c67e36a82b5fcece01b04 native model attempt actually failed lease_requires_resolved_secret before provider dispatch. Independent local audit under immutable v2 reproduced four lifecycle failures with baseline PASS. This distinct bounded successor reuses unchanged PR1050 implementation then fixes those failures using Codex; no old Decision alteration or old branch mutation. Fresh remote main observed9092911f41a089e249f27c883526904299be1d17. Separate independent auditor still required after implementation. No provider/vault/configuration access, installs, Ready/Merge or closure.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "required_branch": "codex/issue1049-candidate-lifecycle-fix-r3-v1-20261002",
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
    "specification": "After immutable Decision-only activation, actual PRE_EXECUTION_AUTHORIZED, PUBLICATION_READY and exact activation Draft, import only eleven product/test/doc changed files from PR1050 exact01f86e98914af7b5e07c67e36a82b5fcece01b04. Fix PRE_PLANNER recovery absent and existing nonrepository container: recheck live native admission, keep exact candidate/repository/authority/lease guards, prepare only disposable checkout, persist frozen approved base before validation. A contradictory existing Git repository must remain denied. Split existing candidate Goal snapshot checks from live Goal status/window admission so accepted terminal checkpoint readback validates immutable snapshot and existing run/result/head/tree/digest bindings without requiring an unexpired window or RUNNING Goal. Fresh/reexecuted validation must retain live admission. Add regressions for both recovery cases, completed Goal, expired/stopped window, changed Goal/contract/plan/candidate/repository/run/base/head/tree/report and rejected fresh execution. Reuse existing runtime/store/proof; no schema/artifact/gate/workflow/dependency/framework changes. Preserve old audit scripts, failed results and original native checkout.",
    "completion_boundary": "Publish one successor Draft, final exact-head four-suite pytest and diff-check, actual gates/readiness and natural CI observed. Self implementation checks are not independent acceptance; separate auditor required. No Ready/Merge/closure/deployment."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/candidate_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/goal_models.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_native_candidate_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/functional_validation.py",
    "reverse_agent/platform_v1/candidate_validation.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/goal_models.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_native_candidate_validation.py",
    "tests/platform_v1/test_functional_report_consistency.py",
    "docs/functional-validation.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "tests/platform_v1/test_functional_execution.py",
    "tests/platform_v1/test_artifact_handoff.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/control_plane/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/run_read_model.py",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "launch_nerelan.bat",
    "launch_reverse_agent.bat",
    "dev-up.ps1",
    "dev-down.ps1",
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
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit",
    "raw_secret_read_or_export",
    "model_provider_config_mutation",
    "payment",
    "process_stop_without_identity",
    "model_api_invocation",
    "credential_access",
    "issue_comment",
    "pull_request_comment"
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
      "Normal exact approved non-main branch push and one Draft against main909; exact-head description updates and read-only natural CI. No other remote mutation, rerun, dispatch, Ready/Merge or closure."
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
      "command": "Reuse isolated audit clone preserving old branches and five known unstaged generated gates; fresh required branch from main909. LF Decision-only activation commit, diff-check, actual startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre and publication-readiness. Exact normal non-main activation push and one Draft before source changes. No CLI history rewrite, old branch mutation or generated gate staging.",
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
      "command": "After actual preflight and activation Draft import exact eleven scoped PR1050 files; implement only approved lifecycle recovery/readback corrections and regressions/docs, using existing installed provider-free native Goal/Window/Git/SQLite checks. No model, secret, configuration, install or shared runtime write.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/functional_validation.py",
        "reverse_agent/platform_v1/candidate_validation.py",
        "reverse_agent/platform_v1/goal_service.py",
        "reverse_agent/platform_v1/goal_models.py",
        "reverse_agent/platform_v1/control_store.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "reverse_agent/platform_v1/task_execution.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "reverse_agent/platform_v1/run_store.py",
        "tests/platform_v1/test_native_candidate_validation.py",
        "tests/platform_v1/test_functional_report_consistency.py",
        "docs/functional-validation.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "native.validate",
      "command": "Development focused checks/fixes within five commits. Final exact-head python -B -m pytest tests/platform_v1/test_native_candidate_validation.py tests/platform_v1/test_functional_report_consistency.py tests/platform_v1/test_functional_execution.py tests/platform_v1/test_artifact_handoff.py -q -p no:cacheprovider; git diff --check base HEAD; actual transition gates and PUBLICATION_READY. Fixed-argv/stale-contract/candidate-SHA-other-descendant/repo/head/tree/report negative tests mandatory. Existing natural CI blocking Platform/all suite distinct from local, no installs/reruns.",
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
      "command": "At most7 normal exact approved successor branch pushes, one Draft against main909, activation first; rebind exact head in description; observe natural CI. No comments/Ready/Merge/closure/deployment/history rewrite.",
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
      ".platform_v1_runtime/**"
    ],
    "stage_allowed": false,
    "note": "All new disposable synthetic/native fixtures and logs stay in F:/reverse-agent-artifacts/worktree-audit-20261002-56c5/issue1049-lifecycle-fix. Existing root/runtime/config/credentials untouched."
  },
  "follows_last_decision_id": "decision_20261001_issue1049_native_fixed_candidate_r3_v3",
  "follows_last_round_id": "round_20261001_issue1049_native_fixed_candidate_r3_v3",
  "workstream_id": "issue1049-candidate-lifecycle-fix-v1"
}
```
