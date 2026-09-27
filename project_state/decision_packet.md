# Bounded Windows Binding child tool environment repair

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260927_issue997_windows_binding_env_r2_v1",
  "round_id": "round_20260927_issue997_windows_binding_env_r2_v1",
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
  "decision_scope": "WINDOWS_BINDING_TOOL_ENVIRONMENT_ONLY",
  "source_issue": 997,
  "parent_issue": 643,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "The Owner explicitly authorizes all pending and newly discovered system tasks, configured API use, no monetary/token limit, independent AI/supervisor acceptance, and publication. This bounded source/worker-configuration stage repairs reproduced Windows tool invocation failure without broad environment or credential exposure. It permits system-authored implementation and exact Draft publication, not landing or application-code deployment.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "cf0c06aaee9d21e5da6c8d558387017ad4259edb",
  "activation_base_sha": "cf0c06aaee9d21e5da6c8d558387017ad4259edb",
  "starting_head": "cf0c06aaee9d21e5da6c8d558387017ad4259edb",
  "fresh_base": "cf0c06aaee9d21e5da6c8d558387017ad4259edb",
  "current_main_expected": "cf0c06aaee9d21e5da6c8d558387017ad4259edb",
  "required_branch": "codex/windows-binding-tool-env-r2-v1-20260927",
  "workstream_id": "issue997-windows-binding-env-r2-v1",
  "follows_last_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "follows_last_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "workflow_profile": "baseline",
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
  "live_model_call_limit": 3,
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
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_binding_windows_env.py",
    "tests/platform_v1/test_opencode_executor.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_binding_windows_env.py",
    "tests/platform_v1/test_opencode_executor.py",
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
    "frontend/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/repository_workspace.py",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
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
    "specification": "Only repair Windows executable discovery/invocation in _BINDING_CHILD_ENV_ALLOWLIST, build_binding_child_env, build_role_child_env and immediately adjacent pure helper if needed. Preserve known non-secret allowlisting, relay configuration and all existing permission, credential, budget and network fences. Do not modify model/provider configuration or copy the full parent environment. Preserve existing _bounded_value from merged PR996 and unrelated account-auth/runtime-launch behavior. Handle absent/nonstring environment values conservatively; portable behavior must stay compatible. Use existing test framework, no new dependency or runner. All product code and tests are authored by Nerelan system workers; supervisor may prepare authority, transfer exact reviewed system artifacts to this branch, run checks and publish. Workers use a clean detached materialization of this activated Decision commit through existing SourceDir configuration; the named branch belongs to the trusted publisher, and worker base/provenance must be verified before artifact acceptance.",
    "completion_boundary": "Provider-free exact-head tests, independent AI or supervisor review, and natural exact-head CI. Draft only. No Ready/merge/deployment under this source stage. Live configured model calls are solely system implementation/review dispatch through existing coding-glm binding; no model call in tests. No live model/provider operation introduced into product tests."
  },
  "runtime_scratch_policy": {
    "paths": [
      ".platform_v1_runtime/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing host F:/reverse-agent runtime metadata/database effects are permitted only through its existing dev-up and Task APIs in the bounded runtime command. Preserve all tracked/unknown user files and existing stores; never stage runtime scratch."
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
    "ci_network_exceptions": [
      "Unchanged natural CI package setup and provider-free checks only; no added workflow or manual dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing loopback Task API/Model Control API and the already configured coding-glm binding via its existing trusted relay, for at most three system implementation/review calls. Provider-free local fixture servers only during tests. No credential reads or arbitrary endpoint access."
    ],
    "github_control_plane_network_exceptions": [
      "Only canonical dddd2024/Nerelan exact approved branch pushes and one Draft against locked main. No Ready/merge/tag/release."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue997.bootstrap",
      "command": "Fresh full checkout F:/Nerelan-issue997-windows-tool-env-20260927 from locked main. Commit only this Decision once; run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness, all through python -m reverse_agent.project_gate --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before implementation. Never edit activated Decision.",
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
      "command_id": "issue997.runtime_source",
      "command": "Only after all current tasks finish and the active window is stopped, use existing unchanged F:/reverse-agent/dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/Nerelan-issue997-windows-tool-env-20260927 -NoBrowser, preserving the recorded model selector and ports4173/8766/8765. Permit its verified-owned process restart and existing .platform_v1_runtime metadata/store writes; no source edits, package installs, global environment changes, browser launch or model call from startup. This reconfigures task source authority, not the existing host/frontend code. Verify SourceDir and execution_authority_sha equal the activated Decision checkout, all three health endpoints, prior Task counts/history and fresh task worker HEAD before acceptance. On startup failure restore the prior SourceDir F:/reverse-agent with the same existing launcher and model selector; no unverified process kill or data removal.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue997.system_implement",
      "command": "Dispatch at most three bounded system implementation/review tasks via existing local Task API using coding-glm, one concurrent task, zero automatic retries, optional token/cost caps unset as Owner requested. The canonical source directory is the activated Decision checkout; verify worker initial HEAD matches activation commit. System worker may edit only approved source/test region inside its own worktree with native file tools, never commit/push/PR or access outside files. For read-only installed Git or Python tool invocation, use only the demonstrated process-local PATHEXT standard-extension workaround; no global change. Supervisor may transfer only the exact reviewed system patch and byte-identical tests to the named source branch and commit once, preserving provenance and pre-transfer clean state.",
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
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/platform_v1/opencode_executor.py",
        "tests/platform_v1/test_binding_windows_env.py",
        "tests/platform_v1/test_opencode_executor.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue997.validate",
      "command": "Provider-free development checks followed by final exact-head python -B -m pytest tests/platform_v1/test_binding_windows_env.py tests/platform_v1/test_opencode_executor.py -q -p no:cacheprovider; python -m compileall -q reverse_agent/platform_v1/opencode_executor.py tests/platform_v1/test_binding_windows_env.py; git diff --check. Verify Windows installed-Git --version via disposable PowerShell child current/repaired environment; no provider, credential, global env or source change in probe. A failing mandatory final check stops publication; development iteration within this bounded scope precedes final checks.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue997.publish",
      "command": "Push only codex/windows-binding-tool-env-r2-v1-20260927 to canonical origin and create/update its one exact Draft against main at cf0c06aaee9d21e5da6c8d558387017ad4259edb, binding this immutable Decision and each exact source head. Require local publication readiness, live main equality, unchanged approved scope, and no concurrent source-branch mutation. No Ready, merge, other branch, tag or release.",
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
      "command_id": "issue997.natural_ci",
      "command": "Observe unchanged natural CI, State Gate and Decision Preflight on exact Draft head. CI executes provider-free tests only; no manual rerun or dispatch and no model calls.",
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
      "command_id": "issue997.audit",
      "command": "Independent exact-head audit: verify narrow Windows environment repair, secret exclusion and unchanged role/relay semantics, actual worker/publisher provenance, local checks and native CI diagnostic. Preserve all unrelated PRs and user dirty files. Report source acceptance separately from runtime deployment or landing.",
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
    "pr": 995,
    "frozen_head": "22ece480512a5ad14205db1a7bc436fdc4a123ce",
    "shared_path": "reverse_agent/platform_v1/opencode_executor.py",
    "policy": "Preserve existing dirty host/frontend workspace and PR995/991/992 source branches. Host code stays unchanged. Only this bounded environment helper repair is permitted; no transfer of unrelated root user changes."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "dev-up.ps1",
    "reverse_agent/platform_v1/repository_workspace.py",
    "reverse_agent/platform_v1/trusted_host.py"
  ]
}
```
