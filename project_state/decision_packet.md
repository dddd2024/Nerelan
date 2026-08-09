# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_issue136_agent_canvas_draft_pr_landing_v18",
  "round_id": "round_20260809_issue136_agent_canvas_draft_pr_landing_v18",
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
  "follows_last_decision_id": "decision_20260809_issue136_agent_canvas_stageb2_atomic_screenshot_recapture_v17",
  "follows_last_round_id": "round_20260809_issue136_agent_canvas_stageb2_atomic_screenshot_recapture_v17",
  "previous_audit_outcome": "ISSUE136_STAGE_B_PIXEL_VISUAL_ACCEPTED_READY_FOR_DRAFT_PR_LANDING_AUTHORITY",
  "workstream_id": "issue136-agent-canvas-draft-pr-landing-v18",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "draft_pr_creation_allowed": true,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "accepted_stage_b": {
    "stage_a_disposition": "AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED",
    "implementation_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
    "real_opencode_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
    "real_task_id": "task-1786237330883-8460dbd1c478",
    "real_task_state": "READY_FOR_HUMAN",
    "real_task_backend_status": "READY_FOR_REVIEW",
    "real_task_executor": "opencode",
    "validation_exit_code": 0,
    "screenshot_path": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "screenshot_sha256": "5d4610dc2383fd3c09081c77d346b408b37e4f3a58ffea7bd1eda7ec8dab0083",
    "screenshot_dimensions": "1440x900",
    "owner_pixel_review": "ACCEPTED",
    "nonblocking_followup_issue": 145
  },
  "draft_pr_contract": {
    "base_branch": "main",
    "expected_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
    "head_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
    "draft_required": true,
    "owner_connector_creation_only": true,
    "creation_only_after_v18_preflight_and_generated_gate_commit_are_pushed": true,
    "title": "Frontend: reuse Agent Canvas v1.6.1 workbench source",
    "body_must_reference_issues": [
      136,
      127,
      145
    ],
    "must_record_stage_a_disposition": "AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED",
    "must_record_real_task_evidence_head": "ab00b03952d96c2421be8297f29699a59ec69fda",
    "must_record_nonblocking_ui_debt": 145,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "auto_merge_allowed": false,
    "subsequent_pr_bound_landing_authority_required": true
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin main",
    "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
    "git show origin/owner/issue136-agent-canvas-reuse-spike-v2:project_state/decision_packet.md",
    "git switch owner/issue136-agent-canvas-reuse-spike-v2",
    "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "validation.accepted_evidence_ancestor",
      "command": "git merge-base --is-ancestor ab00b03952d96c2421be8297f29699a59ec69fda HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "exact_head_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "run_checks"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.stage_gates",
      "command": "git add -- project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_stage"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "publication.cached_check",
      "command": "git diff --cached --check",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "run_checks"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit_gates",
      "command": "git commit -m \"governance: generate issue136 draft-pr landing authority\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit_paths",
      "command": "git diff-tree --no-commit-id --name-only -r HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.push",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_push",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.local_head",
      "command": "git rev-parse HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.remote_head",
      "command": "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.final_status",
      "command": "git status --short",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-task-detail-1440x900.png",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/index.css",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/resize-handle.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-layout.ts",
    "frontend/tests/workspace.test.tsx",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "carry_forward_cumulative_paths": [
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/THIRD_PARTY_NOTICES.md",
    "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-task-detail-1440x900.png",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/index.css",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-sidebar-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/resize-handle.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-collapsed-icon-slot.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/sidebar-layout.ts",
    "frontend/tests/workspace.test.tsx",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "no_new_product_mutation": true,
  "reference_paths": [
    "reverse_agent/**",
    "tests/**",
    ".github/**",
    ".frontend_stage/**",
    ".platform_v1_runtime/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/package-lock.json",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    ".frontend_stage/**",
    ".platform_v1_runtime/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/package-lock.json",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "mark_ready",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "package_install",
    "dependency_install",
    "provider_configuration_mutation",
    "local_service_start",
    "local_service_stop",
    "loopback_http_probe",
    "persistent_state_readback",
    "task_create",
    "task_execute"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
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
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "git push origin owner/issue136-agent-canvas-reuse-spike-v2"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "frontend/artifacts/agent-canvas-v1.6.1/**",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/THIRD_PARTY_NOTICES.md"
  ]
}
```

## Owner instructions

This v18 Decision is a landing-publication authority only. Stage A and Stage B implementation/runtime evidence are already accepted. The cumulative implementation/evidence paths are carry-forward scope only: no new product/source/test/artifact mutation is authorized by any command in this round.

Do not rerun OpenCode/model/task execution, do not recapture screenshots, and do not modify frontend/product/backend/tests/runtime scratch. Local execution is limited to syncing the exact v18 Decision, regenerating the five standard transition Gate artifacts, requiring `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, validating that accepted evidence head `ab00b03952d96c2421be8297f29699a59ec69fda` remains an ancestor, staging only the five generated Gate JSON files, committing them with the exact authorized message, and normal-pushing `owner/issue136-agent-canvas-reuse-spike-v2`.

After the generated-gate commit is pushed and local/remote heads match, stop. The repository Owner will create exactly one Draft PR from `owner/issue136-agent-canvas-reuse-spike-v2` to `main` through the GitHub connector under this Decision. Do not create the PR locally. The Draft PR must not be marked Ready or merged. A separate PR-bound landing authority is required before any merge-readiness or merge action.
