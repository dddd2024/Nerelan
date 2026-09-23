# Approved bounded supervised Nerelan modal repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_ux05_system_modal_r3_v1",
  "round_id": "round_20260923_ux05_system_modal_r3_v1",
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
  "decision_scope": "SUPERVISED_SYSTEM_AUTHORED_UX05_MODAL",
  "source_issue": 448,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner completion",
  "approval_basis": "User explicitly stated that Owner authority is delegated to the supervisor to complete this task; original scope remains Nerelan authors product repairs and supervisor inspects and assigns tasks. Independent candidate review accepts SHA256 1562e1f89e8e6043327c48b3f51168c2a3e8ed8c4cdef4be27191611ef473cf2. This new bounded round authorizes isolated consumption/validation of frozen #989 runtime prerequisite, one300second-process-budget Nerelan UX05 task, independent exact-artifact review and local runtime preview only. No authority is borrowed from old work items; no GitHub publication/landing, retries, credential reads, or supervisor-authored product fixes.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
  "integration_base_ref": "codex/worktree-source-policy-r2-v1-20260923",
  "base_sha": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
  "activation_base_sha": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
  "starting_head": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
  "fresh_base": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "required_branch": "codex/ux05-system-modal-r3-v1-20260923",
  "workstream_id": "ux05-system-modal-r3-v1",
  "follows_last_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "follows_last_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "workflow_profile": "browser_r3",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 2,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 4,
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
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/new-task-modal-accessibility.test.tsx",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_worktree_source_policy.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/new-task-modal-accessibility.test.tsx",
    "reverse_agent/model_access/credential_relay.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "tests/platform_v1/test_opencode_executor.py",
    "tests/platform_v1/test_execution_runtime_budget.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_worktree_source_policy.py"
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
    "specification": "Nerelan implements full UX05: new-task modal has complete viewport backdrop, correct centered/clamped geometry and internal scrolling, labelled modal dialog, appropriate initial focus, Tab/Shift-Tab confinement, Escape dismissal and trigger focus return. Cover 1920x1080,1366x768, reduced viewport, different background scroll positions and actual 200 percent browser zoom; handle nested custom-policy editor safely without breaking existing form state, model/repository selection or backend authority. Prefer existing repository modal/focus patterns and React portal; no dependencies. Scope solely the two listed frontend files. Other UX01-04,06-10 remain tracked subsequent work, not declared resolved.",
    "completion_boundary": "Actual system-authored patch, preserved provenance, deterministic exact-head checks, independent review, and fresh real-page visual/keyboard retest. Local accepted runtime preview only; no GitHub publication/merge or claim all UX issues solved."
  },
  "runtime_scratch_policy": {
    "paths": [
      "frontend/node_modules/**",
      "frontend/dist/**",
      "**/__pycache__/**",
      ".pytest_cache/**",
      ".platform_v1_runtime/**"
    ],
    "stage_allowed": false,
    "note": "Only existing runtime scratch and new named child workspaces under F:/Nerelan-first-use-task-workspaces-20260923; audit artifacts in the existing nerelan-audit directory. Reuse installed frontend dependencies by a narrow node_modules junction after exact package+lock equality; no install. Never stage scratch or inspect auth/config/credential files."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
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
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Bounded read-only GitHub observation of dddd2024/Nerelan main and PR991 only; no mutation, unrelated repositories or unbounded network. Fresh observe remote main=58d4068f43ca4914b122445685cae410a8fa156e, PR991 Draft head/base, independent acceptance and frozen #989 files; create only fresh F:/Nerelan-ux05-system-modal-20260923 on codex/ux05-system-modal-r3-v1-20260923 from exact independently accepted f015eed511e3b1226e7ef1f2db22dd5b26fe47f5. Commit only independently reviewed approved Decision once. Generate startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. No implementation before that.",
      "After fresh independent review accepts the exact frozen five-file #989 candidate, verify file hashes and base blobs, transfer those exact bytes only to this fresh worktree. Preserve original worktree and do not change candidate bytes. Run listed provider-free prerequisite validation; one immutable prerequisite commit, repeat those exact checks on that head plus diff --check. Regenerate plan/preflight/readiness sequentially. Any failed mandatory check stops runtime/model actions; no supervisor fix-forward.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. Only after prerequisite exact-head independent acceptance and fresh no-running-task/no-login observations, verify current clean runtime branch codex/first-use-20260923 at58d4068f43ca4914b122445685cae410a8fa156e, all owned PID/executable/start-time/repo identity, and exact package-lock equality. Use existing dev-down/dev-up hidden NoBrowser to stop/restart only owned services. Permit two local git merge --ff-only operations total: first advance runtime checkout to this accepted prerequisite commit, later to independently accepted system-modal commit. Verify ancestry, clean tree and resulting tree/head. Preserve the same runtime DB/settings/credential owner. SourceDir becomes F:/Nerelan-ux05-system-modal-20260923 and explicit trusted execution/planning identity is the exact current accepted host commit; external task root unchanged. No raw credential reads, settings changes, installs, OAuth or model calls in this step.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After exact host plan/preflight/hash verification and saved coding-default binding identity verification, create and execute exactly one direct Task via existing loopback Task API8766. OpenCode/single/deepseek-flash only, branch exact accepted host prerequisite commit, bounded modal specification and full host authorization evidence in instruction. Verify persisted request/digest <=256KiB. Existing executor owns one detached child and300-second timeout; reviewed relay grants only finite matching budget+margin. No launch of the pending UX01 Goal, autonomous window, duplicate execute, retry, fallback, other providers or publication. System alone may edit frontend/src/components/new-task-composer.tsx and frontend/tests/new-task-modal-accessibility.test.tsx. System may run scoped provider-free checks if dependencies available, otherwise report unavailable, never install.",
      "Observe that same live task through supported API and real browser through terminal. Capture exact task/run/child identity, state/time/usage/errors/changedfiles; do not relaunch on observation timeout. Independently review all child changes, require allowed-path-only system provenance, then transfer exactly reviewed patch to host. Supervisor may apply exact patch but authors no product implementation. Preserve failed artifacts. Record task failure honestly and stop further attempts if no acceptable patch.",
      "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After independent acceptance and second identity-verified runtime fast-forward/restart, fresh real app screenshots at1920x1080,1366x768, different background scroll positions and actual200percent browser zoom; reduced viewport or deviceScaleFactor alone is not proof of browser zoom; keyboard initial focus,Tab/Shift-Tab,Escape,focus-return, nested custom editor and form value persistence checks. Use installed Edge/headless Playwright only against loopback real services; no model or fixture dispatch for these tests. No generated snapshots/threshold changes. Preserve task history and original user window; report exact limitations and remaining UX tasks. Do not publish, Ready, merge, close Issues or claim all-system acceptance."
    ],
    "github_control_plane_network_exceptions": []
  },
  "allowed_commands": [
    {
      "command_id": "ux05v1.bootstrap",
      "command": "Bounded read-only GitHub observation of dddd2024/Nerelan main and PR991 only; no mutation, unrelated repositories or unbounded network. Fresh observe remote main=58d4068f43ca4914b122445685cae410a8fa156e, PR991 Draft head/base, independent acceptance and frozen #989 files; create only fresh F:/Nerelan-ux05-system-modal-20260923 on codex/ux05-system-modal-r3-v1-20260923 from exact independently accepted f015eed511e3b1226e7ef1f2db22dd5b26fe47f5. Commit only independently reviewed approved Decision once. Generate startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. No implementation before that.",
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
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
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
      "command_id": "ux05v1.prerequisite",
      "command": "After fresh independent review accepts the exact frozen five-file #989 candidate, verify file hashes and base blobs, transfer those exact bytes only to this fresh worktree. Preserve original worktree and do not change candidate bytes. Run listed provider-free prerequisite validation; one immutable prerequisite commit, repeat those exact checks on that head plus diff --check. Regenerate plan/preflight/readiness sequentially. Any failed mandatory check stops runtime/model actions; no supervisor fix-forward.",
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
        "commit",
        "command_plan_generation",
        "machine_specific_execution"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/model_access/credential_relay.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_execution_runtime_budget.py"
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
      "command_id": "ux05v1.runtime",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. Only after prerequisite exact-head independent acceptance and fresh no-running-task/no-login observations, verify current clean runtime branch codex/first-use-20260923 at58d4068f43ca4914b122445685cae410a8fa156e, all owned PID/executable/start-time/repo identity, and exact package-lock equality. Use existing dev-down/dev-up hidden NoBrowser to stop/restart only owned services. Permit two local git merge --ff-only operations total: first advance runtime checkout to this accepted prerequisite commit, later to independently accepted system-modal commit. Verify ancestry, clean tree and resulting tree/head. Preserve the same runtime DB/settings/credential owner. SourceDir becomes F:/Nerelan-ux05-system-modal-20260923 and explicit trusted execution/planning identity is the exact current accepted host commit; external task root unchanged. No raw credential reads, settings changes, installs, OAuth or model calls in this step.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "machine_specific_execution",
        "network_access",
        "source_edit"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md",
        "reverse_agent/control_plane/worktree_state.py",
        "reverse_agent/project_gate.py",
        "tests/test_worktree_source_policy.py",
        "reverse_agent/model_access/credential_relay.py",
        "reverse_agent/platform_v1/opencode_executor.py",
        "reverse_agent/platform_v1/trusted_host.py",
        "tests/platform_v1/test_opencode_executor.py",
        "tests/platform_v1/test_execution_runtime_budget.py",
        "frontend/src/components/new-task-composer.tsx",
        "frontend/tests/new-task-modal-accessibility.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux05v1.dispatch",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After exact host plan/preflight/hash verification and saved coding-default binding identity verification, create and execute exactly one direct Task via existing loopback Task API8766. OpenCode/single/deepseek-flash only, branch exact accepted host prerequisite commit, bounded modal specification and full host authorization evidence in instruction. Verify persisted request/digest <=256KiB. Existing executor owns one detached child and300-second timeout; reviewed relay grants only finite matching budget+margin. No launch of the pending UX01 Goal, autonomous window, duplicate execute, retry, fallback, other providers or publication. System alone may edit frontend/src/components/new-task-composer.tsx and frontend/tests/new-task-modal-accessibility.test.tsx. System may run scoped provider-free checks if dependencies available, otherwise report unavailable, never install.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "model_api_invocation",
        "integration_test",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/new-task-composer.tsx",
        "frontend/tests/new-task-modal-accessibility.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux05v1.observe",
      "command": "Observe that same live task through supported API and real browser through terminal. Capture exact task/run/child identity, state/time/usage/errors/changedfiles; do not relaunch on observation timeout. Independently review all child changes, require allowed-path-only system provenance, then transfer exactly reviewed patch to host. Supervisor may apply exact patch but authors no product implementation. Preserve failed artifacts. Record task failure honestly and stop further attempts if no acceptable patch.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "read_only_audit",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/new-task-composer.tsx",
        "frontend/tests/new-task-modal-accessibility.test.tsx"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "ux05v1.validate",
      "command": "On exact transferred system artifact reuse installed runtime frontend/node_modules only after package+lock equality; no installation. Run npm --prefix frontend test -- --run tests/new-task-modal-accessibility.test.tsx tests/model-task-composer.test.tsx tests/workspace.test.tsx; npm --prefix frontend run build; git diff --check. Freeze one system-product commit and repeat those checks plus base-to-head diff check, regenerate startup/plan/lint/preflight/readiness. At most two development verification rounds with no supervisor product edits. Failure stops runtime synchronization; no invented receipt, weakened test, golden update or fix-forward. Independent exact-head acceptance required before local runtime preview.",
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
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "frontend/src/components/new-task-composer.tsx",
        "frontend/tests/new-task-modal-accessibility.test.tsx"
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
      "command_id": "ux05v1.retest",
      "command": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. After independent acceptance and second identity-verified runtime fast-forward/restart, fresh real app screenshots at1920x1080,1366x768, different background scroll positions and actual200percent browser zoom; reduced viewport or deviceScaleFactor alone is not proof of browser zoom; keyboard initial focus,Tab/Shift-Tab,Escape,focus-return, nested custom editor and form value persistence checks. Use installed Edge/headless Playwright only against loopback real services; no model or fixture dispatch for these tests. No generated snapshots/threshold changes. Preserve task history and original user window; report exact limitations and remaining UX tasks. Do not publish, Ready, merge, close Issues or claim all-system acceptance.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "integration_test",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "frontend/src/components/app-shell.tsx",
    "frontend/tests/model-task-composer.test.tsx",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "system_task_attempt_limit": 1,
  "system_execution_timeout_seconds": 300,
  "gpt_model_invocation_limit": 0,
  "model_budget_semantics": "One manual OpenCode task attempt, existing 300-second process timeout with independently reviewed #989 lease binding; no automatic retry or fallback. coding-default/deepseek-flash only, no other model or OAuth operation. Agent can make multiple provider requests within that task; token/cost total is observed, not claimed hard-capped. No autonomous window activation; no queued work dispatch.",
  "source_inbox_id": "inbox-1790156090745-2d62eda7b9aa",
  "runtime_only_path_boundary": {
    "paths": [
      "project_state/decision_packet.md",
      "reverse_agent/control_plane/worktree_state.py",
      "reverse_agent/project_gate.py",
      "tests/test_worktree_source_policy.py",
      "reverse_agent/model_access/credential_relay.py",
      "reverse_agent/platform_v1/opencode_executor.py",
      "reverse_agent/platform_v1/trusted_host.py",
      "tests/platform_v1/test_opencode_executor.py",
      "tests/platform_v1/test_execution_runtime_budget.py",
      "frontend/src/components/new-task-composer.tsx",
      "frontend/tests/new-task-modal-accessibility.test.tsx"
    ],
    "checkout": "F:/Nerelan-first-use-20260923",
    "restriction": "Only exact reviewed, verified local fast-forward to this round accepted commit; never author source in runtime checkout. Keep original #989/#990/#988 worktrees byte-for-byte. Runtime prerequisite transfer is frozen external-author patch only; supervisor authors no product fixes."
  },
  "frozen_prerequisite": {
    "source_worktree": "F:/Nerelan-issue989-execution-runtime-budget",
    "source_head": "ad18e253183fdf0d4e10f3f6e2c2054af0e22332",
    "source_hashes": {
      "reverse_agent/model_access/credential_relay.py": "4f6f3078a54141e8e12809dc59fbecbc52b779784684a127a83c50527859a4ea",
      "reverse_agent/platform_v1/opencode_executor.py": "3dd6f69baa9c047f26d7d095a4ccc42a8812c9fec926327af7f2a70845ba5d2f",
      "reverse_agent/platform_v1/trusted_host.py": "aba04e7a40b724e352909d6a0b367d42c41f4d3229000fcf105e5a27e20255e8",
      "tests/platform_v1/test_opencode_executor.py": "068ad0800b57b53ecbf1c3695632527370aad05474bc484d293def0beedabef6",
      "tests/platform_v1/test_execution_runtime_budget.py": "accb3c7f0bf0c080b2660bbc1daa2949426fd27e5cb986541dfc5468f9816dee"
    },
    "source_authority": "Existing #989 candidate is not authority for this round. Transfer permitted only after fresh independent source and evidence acceptance; verify base blobs match chosen f015 base, every hash remains equal, original worktree is unchanged, and no concurrent owner is displaced. No cherry-pick or import of its Decision/gates.",
    "validation": [
      "python -m pytest tests/platform_v1/test_execution_runtime_budget.py -q",
      "python -m pytest tests/platform_v1/test_opencode_executor.py tests/platform_v1/test_opencode_server_transport.py -q",
      "python -m pytest tests/platform_v1/test_credential_relay.py tests/platform_v1/test_trusted_host.py tests/platform_v1/test_trusted_host_lifecycle.py -q",
      "git diff --check"
    ]
  },
  "host_child_authority_handoff": "Host named branch contains immutable Decision and the independently accepted frozen runtime prerequisite commit. Generate and verify actual plan/preflight on that exact head. Child detached worktree must derive from that same commit; embed complete host plan/preflight bytes, path, SHA256, branch/head and Decision digest in the bounded task instruction. Old child gate files are not authority. System verifies child HEAD and Decision, may read its own repo but cannot regenerate gates or access host paths. Host proof bytes unchanged until patch collection.",
  "concurrent_work_preservation": {
    "main": "58d4068f43ca4914b122445685cae410a8fa156e",
    "991": "f015eed511e3b1226e7ef1f2db22dd5b26fe47f5",
    "989_source_head": "ad18e253183fdf0d4e10f3f6e2c2054af0e22332",
    "988_source_head": "6e9f156a543293f37abc19a2dba6bc7b7364a852",
    "policy": "Observe only and preserve all old worktrees/branches/PRs. This is an isolated local verification consumer, not ownership transfer, editing, publication or landing of #989/#990. Stop if frozen source/base/remote identity changes; do not resolve by reset, stash, rebase or changing the activated Decision."
  },
  "source_objective_sha256": "66ae1d62920f3c3991598872cba50a2ca2fe6679bd797ec007fdf35efc8c2047",
  "runtime_activation_guard": "Before and after EACH service restart and immediately before dispatch require live supported-API observations active_window=null, coordinator.inflight_batch=false, no running/executing task and no login flow in progress; dev-up enables the coordinator and existing windows must not cause any queued dispatch. If any predicate fails stop the affected action without cancelling other work or altering window state. ",
  "local_fast_forward_boundary": "merge_allowed=false and forbidden merge mean no GitHub landing or non-fast-forward/history mutation. Exactly two local --ff-only runtime synchronizations are expressly permitted as described, with clean exact source/destination, ancestry and post-tree/head verification; no merge commit or other ref update."
}
```
