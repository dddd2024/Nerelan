# Approved bounded delegated UX14 timeout evidence repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_ux14_delegated_repair_r3_v1",
  "round_id": "round_20260923_ux14_delegated_repair_r3_v1",
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
  "decision_scope": "DELEGATED_AI_UX14_TIMEOUT_EVIDENCE_ONLY",
  "source_issue": 448,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit Owner delegation and implementer replacement",
  "approval_basis": "User explicitly stated: 现在一切由你决定，可以更换. This resolves alternate-implementer approval in ux14-alternate-implementation-handoff.json. Delegated AI authors the three bounded product files; root remains supervisor and independent reviewers remain read-only. This new Decision authorizes local provider-free implementation only; no Nerelan task, external model/provider call, CLI probe, service synchronization or publication.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "codex/ux14-timeout-evidence-r3-v1-20260923",
  "base_sha": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "activation_base_sha": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "starting_head": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "fresh_base": "a438c404d5d858846d9faf3c8ccaca8a53a7cf45",
  "required_branch": "codex/ux14-delegated-repair-r3-v1-20260923",
  "workstream_id": "ux14-delegated-repair-r3-v1",
  "follows_last_decision_id": "decision_20260923_ux14_timeout_evidence_r3_v1",
  "follows_last_round_id": "round_20260923_ux14_timeout_evidence_r3_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
  "pr_creation_allowed": false,
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
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_timeout_evidence.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/durable_execution.py",
    "tests/platform_v1/test_timeout_evidence.py",
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
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure",
    "model_api_invocation",
    "live_provider_access",
    "runtime_restart",
    "runtime_sync",
    "task_dispatch",
    "cli_probe"
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
    "specification": "Implement ux14-alternate-implementation-handoff.json requirements in only three named product paths: bounded redacted partial TimeoutExpired bytes/str/None stdout/stderr; complete structurally valid events and factual nonduplicated usage; distinguish incomplete/truncated/absent output; cap parsing/persistence; retain FAILED timeout, original300-second budget and lease release. In _dispatch_opencode_durable_single failed returned ExecutorResult branch only persist changed_files using existing owner/epoch fencing before terminalization. Preserve baseline failure checkpoint sequence (role_attempt=1 is not success), zero validator calls and empty validation command/digest with exit_code=-1. No team/resume/state-machine or API display mapping changes. No edits to existing tests; new named test only.",
    "completion_boundary": "Provider-free development checks and independent patch review before single frozen product commit, exact-head full mandatory checks and independent final acceptance. No runtime sync, deployment, publication, historical evidence reconstruction or root-cause claim."
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing dependencies only; disposable provider-free test fixtures and logs outside tracked source. External audit artifacts in existing nerelan-audit directory. No user config/credential reads."
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
    "remote_observation_read_only_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Delegated AI implements only three named files according to semantic contract and external handoff. Up to six provider-free development edit/test cycles, including focused pytest for new test and existing executor/server/runtime-budget/durable/durable-v5/task-service tests, git diff --check and local temporary fixture inspection. Development failures may be fixed within scope and budget before product freeze; no weak tests or edits to existing tests. Independent reviewer checks exact patch and tests; address findings within budget before freezing. No model/provider, installed OpenCode probe, settings/credential reads, production task creation, production service or GitHub mutation. Test-only loopback exception: provider-free synthetic Tasks/fake executors in temporary directories or in-memory stores and temporary HTTP fixtures bound to 127.0.0.1 random ports only. Do not contact or mutate existing ports8765/8766, real runtime data/services, providers, installed CLI, credentials or user configuration. Temporary test HTTP fixtures may be started and stopped within their owned test lifecycle; no external network.",
      "After independent patch acceptance and passing development checks, run actual worktree-publication-readiness and stage only three approved product files. Commit product exactly once; immutable thereafter. Run python -m pytest tests/platform_v1/test_timeout_evidence.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_execution_runtime_budget.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_service.py -q; git diff --check; git diff a438c404d5d858846d9faf3c8ccaca8a53a7cf45 HEAD --check. Regenerate startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre/worktree-publication-readiness with --state-dir project_state. Any mandatory frozen exact-head failure stops; no fix-forward. Obtain independent exact-head acceptance and give root artifacts. No deployment or publication. Test-only loopback exception: provider-free synthetic Tasks/fake executors in temporary directories or in-memory stores and temporary HTTP fixtures bound to 127.0.0.1 random ports only. Do not contact or mutate existing ports8765/8766, real runtime data/services, providers, installed CLI, credentials or user configuration. Temporary test HTTP fixtures may be started and stopped within their owned test lifecycle; no external network."
    ],
    "github_control_plane_network_exceptions": []
  },
  "allowed_commands": [
    {
      "command_id": "ux14d.bootstrap",
      "command": "Verify exact local base a438c404d5d858846d9faf3c8ccaca8a53a7cf45 and integration branch; preserve original/old trees. After independent Decision review create only F:/Nerelan-ux14-delegated-repair-20260923 fresh branch codex/ux14-delegated-repair-r3-v1-20260923. Commit approved Decision only once. Run python -m reverse_agent.project_gate startup-snapshot --state-dir project_state; transition-command-plan; transition-lint; transition-preflight --mode pre; worktree-publication-readiness (each --state-dir project_state). Require all zero, PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY, then independent exact activation review before product edits. Never stage five generated Gate files.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
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
      "command_id": "ux14d.implement",
      "command": "Delegated AI implements only three named files according to semantic contract and external handoff. Up to six provider-free development edit/test cycles, including focused pytest for new test and existing executor/server/runtime-budget/durable/durable-v5/task-service tests, git diff --check and local temporary fixture inspection. Development failures may be fixed within scope and budget before product freeze; no weak tests or edits to existing tests. Independent reviewer checks exact patch and tests; address findings within budget before freezing. No model/provider, installed OpenCode probe, settings/credential reads, production task creation, production service or GitHub mutation. Test-only loopback exception: provider-free synthetic Tasks/fake executors in temporary directories or in-memory stores and temporary HTTP fixtures bound to 127.0.0.1 random ports only. Do not contact or mutate existing ports8765/8766, real runtime data/services, providers, installed CLI, credentials or user configuration. Temporary test HTTP fixtures may be started and stopped within their owned test lifecycle; no external network.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "unit_test",
        "integration_test",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux14d.validate",
      "command": "After independent patch acceptance and passing development checks, run actual worktree-publication-readiness and stage only three approved product files. Commit product exactly once; immutable thereafter. Run python -m pytest tests/platform_v1/test_timeout_evidence.py tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py tests/platform_v1/test_execution_runtime_budget.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_task_service.py -q; git diff --check; git diff a438c404d5d858846d9faf3c8ccaca8a53a7cf45 HEAD --check. Regenerate startup-snapshot/transition-command-plan/transition-lint/transition-preflight --mode pre/worktree-publication-readiness with --state-dir project_state. Any mandatory frozen exact-head failure stops; no fix-forward. Obtain independent exact-head acceptance and give root artifacts. No deployment or publication. Test-only loopback exception: provider-free synthetic Tasks/fake executors in temporary directories or in-memory stores and temporary HTTP fixtures bound to 127.0.0.1 random ports only. Do not contact or mutate existing ports8765/8766, real runtime data/services, providers, installed CLI, credentials or user configuration. Temporary test HTTP fixtures may be started and stopped within their owned test lifecycle; no external network.",
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
        "commit",
        "command_plan_generation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/durable_execution.py",
        "tests/platform_v1/test_timeout_evidence.py"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_durable_execution_v5.py"
  ],
  "source_inbox_id": "inbox-1790158620782-05e360330915",
  "development_iteration_limit": 6,
  "preservation_boundary": "Original F:/reverse-agent, all prior worktrees and Decisions, current runtime and task data are read-only. Only the named fresh worktree is mutable. Existing generated Gate files there are nonstageable.",
  "external_handoff_sha256": "c27888577ff3e7131001a4621b007bc3154788f01009cc707b01f6b8139f868d"
}
```
