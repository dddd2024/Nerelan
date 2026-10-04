# Owner-approved bounded launcher repair for118/384

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_launcher_repair_r3_v1",
  "round_id": "round_20261004_issue118_launcher_repair_r3_v1",
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
  "decision_scope": "ISSUE118_OWNER_APPROVED_LAUNCHER_REPAIR",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / explicit current Owner full architecture delegation",
  "approval_basis": "Explicit current Owner approval: \u6279\u51c6\u8fd9\u4efd\u6709\u754c\u4fee\u590d\u65b9\u6848, exact five files, two corrections/two development checks, original source expiry.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-client-guard-bootstrap-r3-v1-20261004",
  "base_sha": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "activation_base_sha": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "starting_head": "1b99c23d1e6c51289b973b2bbfe893627353af6f",
  "required_branch": "codex/issue118-launcher-repair-r3-v1-20261004",
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
  "destructive_operations_allowed": true,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "# Proposed bounded source repair \u2014 EXPLICITLY OWNER APPROVED SOURCE REPAIR\n\nWork Item: dddd2024/Nerelan#118, prerequisite native-client lifecycle from #384.\nExact planning base: codex/issue118-client-guard-bootstrap-r3-v1-20261004 at 1b99c23d1e6c51289b973b2bbfe893627353af6f. No main fallback.\n\nOriginal runtime packet stops after its first failed launch and expressly forbids an automatic successor, retry or reset. It remains immutable. Source-phase1081 spent3 development checks and4 corrections; runtime1082 spent1/1 launches and permits0 source corrections. Preserve every failure, receipt, counter and original deadline.\n\n## Exact prospective source scope\n\n- dev-up.ps1: pass Vite --host127.0.0.1, --port with the selected FrontendPort, and --strictPort through npm's argument separator. Evaluate Vite's existing configLoader runner to avoid shared node_modules/.vite-temp writes; no dependency install/version change.\n- frontend/trusted-client.mjs: close the private stdin handle on terminal bootstrap failure/browser disconnect after bounded owned browser cleanup. Preserve private capability isolation and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: spawn the actual committed broker with malformed configuration while parent stdin remains open; require bounded exit1 and fixed diagnostics, no browser/SDK/model call. Keep all existing negative transport tests.\n- tests/platform_v1/test_dev_up_contract.py: verify actual forwarded CLI arguments, exact selected port and strict binding; preserve existing Windows ownership/cleanup contracts.\n- docs/local-client-session.md: describe the launcher/pipe lifecycle and explicitly distinguish source verification from actual browser acceptance.\n\n## Proposed new limits\n\nTwo source correction passes, two disposable provider-free development checks, one mandatory Platform V1 check, one mandatory Path-A check, one exact-head focused check and git diff --check. One Decision activation commit and one product commit; two exact branch pushes, one Draft, up to two description updates. Fresh bounded Path-B packet/plan/preflight/Draft must exist before source changes. Proposed phase expires at the existing source deadline2026-10-04T14:55:31.639949Z; never renew the failed runtime deadline.\n\nZero actual runtime launches, real browser launches, model/provider calls, credential access, installs, workflow dispatch/rerun, Ready, merge, main push, tag/release/deploy or existing frontend mutation. Later actual Windows acceptance requires separately selected bounded authority and retains this original failure.\n\n## Acceptance and remaining architecture\n\nNative child exits with stdin still open; selected port reaches Vite CLI with strictPort; shared dependencies receive no configuration-temp writes; original tests preserved, required local checks and exact-head natural CI pass. Source completion does not claim private browser acceptance, independent audit, mainline landing or #118 completion.\n\nAfter this prerequisite: connect authenticated Owner activation to the existing upper-authority validator/compiler; bind durable immutable policy revisions and per-operation receipts; implement separately scoped GitHub, release and deployment adapters with external-truth reconciliation; complete recovery and morning summaries. Reuse existing TaskStore/coordinator/authority code and mature runtimes.\n\nOwner explicitly replied \u6279\u51c6\u8fd9\u4efd\u6709\u754c\u4fee\u590d\u65b9\u6848 to the exact five-file/two-correction/two-development-check question in this chat. This new approval permits this prospective phase, not automatic renewal of the failed runtime packet. Preserve source1081 dev3/corrections4, runtime1082 launch1/1 failed, immutable Decisions and both original deadlines. Two new corrections yield total source corrections at most6; two new dev checks yield total at most5. No actual runtime/browser/model launch. Known installed Node may execute committed native standard-library tests only. Mandatory checks: full tests/platform_v1 once2400s with ONLY original four OpenCode opt-in exclusions; tests/control_plane/test_path_a_policy.py once120s; committed focused launcher/bootstrap/client-auth/host/session once900s. Existing original assertions must remain. Disposable test state under F:/nrl-launch118-v1. Product commit1, exact branch pushes2, Draft1, description updates2; natural exact-head CI read-only. Canonical gates required. No independent acceptance, full118 completion or landing claim.\n",
    "completion_boundary": "Five-file source repair, deterministic local and natural exact-head CI evidence; actual browser acceptance and full architecture remain pending."
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "dev-up.ps1",
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "tests/platform_v1/test_dev_up_contract.py",
    "docs/local-client-session.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "dev-up.ps1",
    "frontend/trusted-client.mjs",
    "frontend/trusted-client.node-test.mjs",
    "tests/platform_v1/test_dev_up_contract.py",
    "docs/local-client-session.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/unattended_coordinator.py",
    "reverse_agent/model_access/service.py",
    ".github/workflows/ci.yml",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/repository-client.ts",
    "frontend/src/lib/goal-start-operation.ts",
    "frontend/src/lib/goal-continuation-operation.ts"
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
    "reverse_agent/model_access/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "frontend/src/**",
    "frontend/node_modules/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "**/auth.json",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/autonomy.py",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/local_client_session.py",
    "reverse_agent/platform_v1/authority_adapter.py",
    "reverse_agent/platform_v1/publication_controller.py"
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
    "existing_task_or_runtime_mutation",
    "destructive_outside_new_owned_disposable_fixture_process_groups_or_scratch"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "workflow_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": true,
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
      "New owned provider-free synthetic HTTP/Node fixtures only, known installed Node58e74bf...; no model/provider/browser/existing ports."
    ],
    "github_control_plane_network_exceptions": [
      "Two pushes exact codex/issue118-launcher-repair-r3-v1-20261004, one Draft against codex/issue118-client-guard-bootstrap-r3-v1-20261004@1b99c23d1e6c51289b973b2bbfe893627353af6f, two descriptions, bounded read-only natural CI evidence. No other writes."
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
      "command_id": "repair.bootstrap",
      "command": "Fresh exact-base Decision activation, canonical gates and bound Draft before source.",
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
      "command_id": "repair.implementation",
      "command": "# Proposed bounded source repair \u2014 EXPLICITLY OWNER APPROVED SOURCE REPAIR\n\nWork Item: dddd2024/Nerelan#118, prerequisite native-client lifecycle from #384.\nExact planning base: codex/issue118-client-guard-bootstrap-r3-v1-20261004 at 1b99c23d1e6c51289b973b2bbfe893627353af6f. No main fallback.\n\nOriginal runtime packet stops after its first failed launch and expressly forbids an automatic successor, retry or reset. It remains immutable. Source-phase1081 spent3 development checks and4 corrections; runtime1082 spent1/1 launches and permits0 source corrections. Preserve every failure, receipt, counter and original deadline.\n\n## Exact prospective source scope\n\n- dev-up.ps1: pass Vite --host127.0.0.1, --port with the selected FrontendPort, and --strictPort through npm's argument separator. Evaluate Vite's existing configLoader runner to avoid shared node_modules/.vite-temp writes; no dependency install/version change.\n- frontend/trusted-client.mjs: close the private stdin handle on terminal bootstrap failure/browser disconnect after bounded owned browser cleanup. Preserve private capability isolation and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: spawn the actual committed broker with malformed configuration while parent stdin remains open; require bounded exit1 and fixed diagnostics, no browser/SDK/model call. Keep all existing negative transport tests.\n- tests/platform_v1/test_dev_up_contract.py: verify actual forwarded CLI arguments, exact selected port and strict binding; preserve existing Windows ownership/cleanup contracts.\n- docs/local-client-session.md: describe the launcher/pipe lifecycle and explicitly distinguish source verification from actual browser acceptance.\n\n## Proposed new limits\n\nTwo source correction passes, two disposable provider-free development checks, one mandatory Platform V1 check, one mandatory Path-A check, one exact-head focused check and git diff --check. One Decision activation commit and one product commit; two exact branch pushes, one Draft, up to two description updates. Fresh bounded Path-B packet/plan/preflight/Draft must exist before source changes. Proposed phase expires at the existing source deadline2026-10-04T14:55:31.639949Z; never renew the failed runtime deadline.\n\nZero actual runtime launches, real browser launches, model/provider calls, credential access, installs, workflow dispatch/rerun, Ready, merge, main push, tag/release/deploy or existing frontend mutation. Later actual Windows acceptance requires separately selected bounded authority and retains this original failure.\n\n## Acceptance and remaining architecture\n\nNative child exits with stdin still open; selected port reaches Vite CLI with strictPort; shared dependencies receive no configuration-temp writes; original tests preserved, required local checks and exact-head natural CI pass. Source completion does not claim private browser acceptance, independent audit, mainline landing or #118 completion.\n\nAfter this prerequisite: connect authenticated Owner activation to the existing upper-authority validator/compiler; bind durable immutable policy revisions and per-operation receipts; implement separately scoped GitHub, release and deployment adapters with external-truth reconciliation; complete recovery and morning summaries. Reuse existing TaskStore/coordinator/authority code and mature runtimes.\n\nOwner explicitly replied \u6279\u51c6\u8fd9\u4efd\u6709\u754c\u4fee\u590d\u65b9\u6848 to the exact five-file/two-correction/two-development-check question in this chat. This new approval permits this prospective phase, not automatic renewal of the failed runtime packet. Preserve source1081 dev3/corrections4, runtime1082 launch1/1 failed, immutable Decisions and both original deadlines. Two new corrections yield total source corrections at most6; two new dev checks yield total at most5. No actual runtime/browser/model launch. Known installed Node may execute committed native standard-library tests only. Mandatory checks: full tests/platform_v1 once2400s with ONLY original four OpenCode opt-in exclusions; tests/control_plane/test_path_a_policy.py once120s; committed focused launcher/bootstrap/client-auth/host/session once900s. Existing original assertions must remain. Disposable test state under F:/nrl-launch118-v1. Product commit1, exact branch pushes2, Draft1, description updates2; natural exact-head CI read-only. Canonical gates required. No independent acceptance, full118 completion or landing claim.\n",
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
        "dev-up.ps1",
        "frontend/trusted-client.mjs",
        "frontend/trusted-client.node-test.mjs",
        "tests/platform_v1/test_dev_up_contract.py",
        "docs/local-client-session.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "repair.validation",
      "command": "# Proposed bounded source repair \u2014 EXPLICITLY OWNER APPROVED SOURCE REPAIR\n\nWork Item: dddd2024/Nerelan#118, prerequisite native-client lifecycle from #384.\nExact planning base: codex/issue118-client-guard-bootstrap-r3-v1-20261004 at 1b99c23d1e6c51289b973b2bbfe893627353af6f. No main fallback.\n\nOriginal runtime packet stops after its first failed launch and expressly forbids an automatic successor, retry or reset. It remains immutable. Source-phase1081 spent3 development checks and4 corrections; runtime1082 spent1/1 launches and permits0 source corrections. Preserve every failure, receipt, counter and original deadline.\n\n## Exact prospective source scope\n\n- dev-up.ps1: pass Vite --host127.0.0.1, --port with the selected FrontendPort, and --strictPort through npm's argument separator. Evaluate Vite's existing configLoader runner to avoid shared node_modules/.vite-temp writes; no dependency install/version change.\n- frontend/trusted-client.mjs: close the private stdin handle on terminal bootstrap failure/browser disconnect after bounded owned browser cleanup. Preserve private capability isolation and fixed diagnostics.\n- frontend/trusted-client.node-test.mjs: spawn the actual committed broker with malformed configuration while parent stdin remains open; require bounded exit1 and fixed diagnostics, no browser/SDK/model call. Keep all existing negative transport tests.\n- tests/platform_v1/test_dev_up_contract.py: verify actual forwarded CLI arguments, exact selected port and strict binding; preserve existing Windows ownership/cleanup contracts.\n- docs/local-client-session.md: describe the launcher/pipe lifecycle and explicitly distinguish source verification from actual browser acceptance.\n\n## Proposed new limits\n\nTwo source correction passes, two disposable provider-free development checks, one mandatory Platform V1 check, one mandatory Path-A check, one exact-head focused check and git diff --check. One Decision activation commit and one product commit; two exact branch pushes, one Draft, up to two description updates. Fresh bounded Path-B packet/plan/preflight/Draft must exist before source changes. Proposed phase expires at the existing source deadline2026-10-04T14:55:31.639949Z; never renew the failed runtime deadline.\n\nZero actual runtime launches, real browser launches, model/provider calls, credential access, installs, workflow dispatch/rerun, Ready, merge, main push, tag/release/deploy or existing frontend mutation. Later actual Windows acceptance requires separately selected bounded authority and retains this original failure.\n\n## Acceptance and remaining architecture\n\nNative child exits with stdin still open; selected port reaches Vite CLI with strictPort; shared dependencies receive no configuration-temp writes; original tests preserved, required local checks and exact-head natural CI pass. Source completion does not claim private browser acceptance, independent audit, mainline landing or #118 completion.\n\nAfter this prerequisite: connect authenticated Owner activation to the existing upper-authority validator/compiler; bind durable immutable policy revisions and per-operation receipts; implement separately scoped GitHub, release and deployment adapters with external-truth reconciliation; complete recovery and morning summaries. Reuse existing TaskStore/coordinator/authority code and mature runtimes.\n\nOwner explicitly replied \u6279\u51c6\u8fd9\u4efd\u6709\u754c\u4fee\u590d\u65b9\u6848 to the exact five-file/two-correction/two-development-check question in this chat. This new approval permits this prospective phase, not automatic renewal of the failed runtime packet. Preserve source1081 dev3/corrections4, runtime1082 launch1/1 failed, immutable Decisions and both original deadlines. Two new corrections yield total source corrections at most6; two new dev checks yield total at most5. No actual runtime/browser/model launch. Known installed Node may execute committed native standard-library tests only. Mandatory checks: full tests/platform_v1 once2400s with ONLY original four OpenCode opt-in exclusions; tests/control_plane/test_path_a_policy.py once120s; committed focused launcher/bootstrap/client-auth/host/session once900s. Existing original assertions must remain. Disposable test state under F:/nrl-launch118-v1. Product commit1, exact branch pushes2, Draft1, description updates2; natural exact-head CI read-only. Canonical gates required. No independent acceptance, full118 completion or landing claim.\n",
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
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "repair.publication",
      "command": "Two exact branch pushes and one Draft, two descriptions; natural CI read-only. codex/issue118-launcher-repair-r3-v1-20261004",
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
    "note": "Disposable provider-free tests only F:/nrl-launch118-v1. Preserve all existing runtimes and shared dependencies."
  },
  "workstream_id": "issue118-launcher-repair-r3-v1",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 2,
  "development_correction_round_limit": 2,
  "execution_window_hours": 6,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-04T11:15:02.352755+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 2,
  "owned_test_scratch_root": "F:\\nrl-launch118-v1",
  "mandatory_pytest_process_limit": 3,
  "cumulative_development_check_limit": 5,
  "cumulative_correction_round_limit": 6,
  "cumulative_prior_correction_rounds": 4,
  "cumulative_prior_development_checks": 3,
  "approved_repair_limits": {
    "corrections": 2,
    "development_checks": 2,
    "prior_source_corrections": 4,
    "prior_source_development_checks": 3,
    "failed_runtime_launches": 1,
    "runtime_launches_allowed": 0,
    "expires_at": "2026-10-04T14:55:31.639949+00:00"
  }
}
```
