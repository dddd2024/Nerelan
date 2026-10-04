# Owner-approved compatibility correction with preserved failures

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261004_issue118_launcher_compatibility_r3_v2",
  "round_id": "round_20261004_issue118_launcher_compatibility_r3_v2",
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
  "decision_scope": "ISSUE118_OWNER_APPROVED_COMPATIBILITY_CORRECTION",
  "source_issue": 118,
  "parent_issue": 90,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 / explicit current Owner full architecture delegation",
  "approval_basis": "Explicit Owner \u6279\u51c6\uff0c\u7ee7\u7eed to the pending exact one-correction/one-dev/mandatory-replay/two-push/Draft compatibility plan.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "codex/issue118-launcher-repair-r3-v1-20261004",
  "base_sha": "ae7475d3cef2a738a9ad68b2bd373234f67e99a5",
  "activation_base_sha": "ae7475d3cef2a738a9ad68b2bd373234f67e99a5",
  "starting_head": "ae7475d3cef2a738a9ad68b2bd373234f67e99a5",
  "required_branch": "codex/issue118-launcher-compatibility-r3-v2-20261004",
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
    "specification": "# Reviewable compatibility correction \u2014 EXPLICITLY OWNER APPROVED\n\nCurrent source activation: ae7475d3cef2a738a9ad68b2bd373234f67e99a5, Draft1083. The approved five-file change is uncommitted. Preserve it and the five generated gates; no reset/stash/restore/cleanup.\n\nActual native regressions first failed before repair. After repair, actual frontend AST invocation passed selected port18879/strict loopback/configLoader runner; all18 native broker transport/bootstrap tests passed, including actual child exit1 while the parent kept stdin open. Original69 Python functions and all old native tests are unchanged.\n\nDevelopment2 produced99 passes and72 tmp_path setup errors from an absent approved basetemp parent. Its original evidence remains. Creating only that empty parent preceded the first mandatory full Platform check, without another development invocation.\n\nThe first mandatory Platform invocation now reports failures. Source observation identifies a compatibility defect: deleting VITE_PORT broke the existing npm.cmd fixture that forwards %VITE_PORT% to its owned stub-host.ps1. No fixture weakening, source correction, further mandatory check, product commit or push follows this failure under the current packet.\n\n## Exact proposed delta\n\nIn dev-up.ps1, retain both original VITE_PORT=[string]$FrontendPort and VITE_INLINE_CONFIG compatibility variables alongside the new real npm/Vite CLI arguments. Actual CLI port/strictPort remains authoritative for real Vite; variables preserve existing callers and Windows safety fixtures. Do not change old test assertions. Remaining approved four files retain their current source patch.\n\n## Proposed bounded continuation\n\nOne additional source compatibility correction, one disposable provider-free focused development invocation, one new full Platform mandatory invocation, then the unused Path-A and exact-head checks. Use actual existing tests/test_path_a_gate.py; the earlier generated prose's tests/control_plane/test_path_a_policy.py does not exist and has never been claimed executed. Keep the old immutable Decision unchanged; a new exact source scope/Decision/plan/preflight/Draft must bind the approved correction and mandatory replay explicitly.\n\nNo original failure/counter/deadline reset. Original source deadline2026-10-04T14:55:31.639949Z remains. New prospective activation/product commit and exact Draft publication need two new bounded branch pushes; do not claim those granted by the exhausted original phase. No actual browser/runtime/model calls, credentials, dependency installs, workflow dispatch/rerun, Ready/Merge, main push, tag/release/deploy or existing frontend mutation.\n\nMandatory source/local/natural exact-head CI evidence remains necessary; source completion is not authenticated real browser acceptance, independent audit, #118 completion or mainline landing.\n\nOwner explicitly replied \u6279\u51c6\uff0c\u7ee7\u7eed to the pending exact compatibility proposal in this chat on2026-10-04. Approval grants1 additional compatibility correction,1 focused development invocation,1 new mandatory full Platform invocation after preserving original failure, the unused Path-A and committed exact-head focused checks,2 branch pushes and1 new Draft. No actual browser/runtime/model/credential/install/Ready/Merge or workflow dispatch/rerun permission. Exact planning base is prior activation codex/issue118-launcher-repair-r3-v1-20261004@ae7475d3cef2a738a9ad68b2bd373234f67e99a5; underlying product source1b99c23d remains unchanged until carried candidate edits.\nExisting five-file candidate changes were already authorized and made under prior Draft1083. Freeze and preserve their exact hashes/patch before this activation; they are carried existing work, not newly edited before this Draft. Only Decision is staged/committed for activation. No new source correction until canonical gates/PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and bound Draft exist. Restore exactly the two original compatibility environment entries in dev-up.ps1; preserve actual Vite CLI arguments and all other four candidate files byte-identical. Preserve all original69 Python functions/all original native tests.\nSource hashes freeze for mandatory checks. Known Node E:\\Program Files\\nodejs\\node.exe@58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f may execute committed native standard-library source tests; no actual browser or SDK execution. One focused dev<=900s; full tests/platform_v1 once<=2400s with ONLY four original installed-OpenCode opt-in exclusions; tests/test_path_a_gate.py once<=120s; committed focused launcher/bootstrap/client-auth/host/session once<=900s. Each invocation uses a new disposable child under F:\\nrl-launch118-v2; create its empty parent first. No failed check is waived. Git diff --check and canonical publication readiness required. Natural exact-head CI must be observed with original native logs/JUnit/artifacts before claiming this source phase complete. Independent acceptance/actual Windows browser acceptance/full118/full384/fullgoal remain pending. Original absolute expiry 2026-10-04T14:55:31.639949+00:00; never renew runtime expiry or discard any failure/spending.\n",
    "completion_boundary": "Five-file carried source candidate plus one compatibility correction, required local checks and natural exact-head CI. Not actual browser acceptance, independent review, landing or whole architecture completion."
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
      "Two exact pushes codex/issue118-launcher-compatibility-r3-v2-20261004, one Draft against codex/issue118-launcher-repair-r3-v1-20261004@ae7475d3cef2a738a9ad68b2bd373234f67e99a5, two descriptions and bounded read-only exact-head natural CI evidence. No other writes."
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
      "command_id": "compatibility.bootstrap",
      "command": "Fresh exact planning-base branch, Decision-only activation, canonical gates and bound Draft before new source edits; preserve already-authorized carried source.",
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
      "command_id": "compatibility.implementation",
      "command": "# Reviewable compatibility correction \u2014 EXPLICITLY OWNER APPROVED\n\nCurrent source activation: ae7475d3cef2a738a9ad68b2bd373234f67e99a5, Draft1083. The approved five-file change is uncommitted. Preserve it and the five generated gates; no reset/stash/restore/cleanup.\n\nActual native regressions first failed before repair. After repair, actual frontend AST invocation passed selected port18879/strict loopback/configLoader runner; all18 native broker transport/bootstrap tests passed, including actual child exit1 while the parent kept stdin open. Original69 Python functions and all old native tests are unchanged.\n\nDevelopment2 produced99 passes and72 tmp_path setup errors from an absent approved basetemp parent. Its original evidence remains. Creating only that empty parent preceded the first mandatory full Platform check, without another development invocation.\n\nThe first mandatory Platform invocation now reports failures. Source observation identifies a compatibility defect: deleting VITE_PORT broke the existing npm.cmd fixture that forwards %VITE_PORT% to its owned stub-host.ps1. No fixture weakening, source correction, further mandatory check, product commit or push follows this failure under the current packet.\n\n## Exact proposed delta\n\nIn dev-up.ps1, retain both original VITE_PORT=[string]$FrontendPort and VITE_INLINE_CONFIG compatibility variables alongside the new real npm/Vite CLI arguments. Actual CLI port/strictPort remains authoritative for real Vite; variables preserve existing callers and Windows safety fixtures. Do not change old test assertions. Remaining approved four files retain their current source patch.\n\n## Proposed bounded continuation\n\nOne additional source compatibility correction, one disposable provider-free focused development invocation, one new full Platform mandatory invocation, then the unused Path-A and exact-head checks. Use actual existing tests/test_path_a_gate.py; the earlier generated prose's tests/control_plane/test_path_a_policy.py does not exist and has never been claimed executed. Keep the old immutable Decision unchanged; a new exact source scope/Decision/plan/preflight/Draft must bind the approved correction and mandatory replay explicitly.\n\nNo original failure/counter/deadline reset. Original source deadline2026-10-04T14:55:31.639949Z remains. New prospective activation/product commit and exact Draft publication need two new bounded branch pushes; do not claim those granted by the exhausted original phase. No actual browser/runtime/model calls, credentials, dependency installs, workflow dispatch/rerun, Ready/Merge, main push, tag/release/deploy or existing frontend mutation.\n\nMandatory source/local/natural exact-head CI evidence remains necessary; source completion is not authenticated real browser acceptance, independent audit, #118 completion or mainline landing.\n\nOwner explicitly replied \u6279\u51c6\uff0c\u7ee7\u7eed to the pending exact compatibility proposal in this chat on2026-10-04. Approval grants1 additional compatibility correction,1 focused development invocation,1 new mandatory full Platform invocation after preserving original failure, the unused Path-A and committed exact-head focused checks,2 branch pushes and1 new Draft. No actual browser/runtime/model/credential/install/Ready/Merge or workflow dispatch/rerun permission. Exact planning base is prior activation codex/issue118-launcher-repair-r3-v1-20261004@ae7475d3cef2a738a9ad68b2bd373234f67e99a5; underlying product source1b99c23d remains unchanged until carried candidate edits.\nExisting five-file candidate changes were already authorized and made under prior Draft1083. Freeze and preserve their exact hashes/patch before this activation; they are carried existing work, not newly edited before this Draft. Only Decision is staged/committed for activation. No new source correction until canonical gates/PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and bound Draft exist. Restore exactly the two original compatibility environment entries in dev-up.ps1; preserve actual Vite CLI arguments and all other four candidate files byte-identical. Preserve all original69 Python functions/all original native tests.\nSource hashes freeze for mandatory checks. Known Node E:\\Program Files\\nodejs\\node.exe@58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f may execute committed native standard-library source tests; no actual browser or SDK execution. One focused dev<=900s; full tests/platform_v1 once<=2400s with ONLY four original installed-OpenCode opt-in exclusions; tests/test_path_a_gate.py once<=120s; committed focused launcher/bootstrap/client-auth/host/session once<=900s. Each invocation uses a new disposable child under F:\\nrl-launch118-v2; create its empty parent first. No failed check is waived. Git diff --check and canonical publication readiness required. Natural exact-head CI must be observed with original native logs/JUnit/artifacts before claiming this source phase complete. Independent acceptance/actual Windows browser acceptance/full118/full384/fullgoal remain pending. Original absolute expiry 2026-10-04T14:55:31.639949+00:00; never renew runtime expiry or discard any failure/spending.\n",
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
      "command_id": "compatibility.validation",
      "command": "# Reviewable compatibility correction \u2014 EXPLICITLY OWNER APPROVED\n\nCurrent source activation: ae7475d3cef2a738a9ad68b2bd373234f67e99a5, Draft1083. The approved five-file change is uncommitted. Preserve it and the five generated gates; no reset/stash/restore/cleanup.\n\nActual native regressions first failed before repair. After repair, actual frontend AST invocation passed selected port18879/strict loopback/configLoader runner; all18 native broker transport/bootstrap tests passed, including actual child exit1 while the parent kept stdin open. Original69 Python functions and all old native tests are unchanged.\n\nDevelopment2 produced99 passes and72 tmp_path setup errors from an absent approved basetemp parent. Its original evidence remains. Creating only that empty parent preceded the first mandatory full Platform check, without another development invocation.\n\nThe first mandatory Platform invocation now reports failures. Source observation identifies a compatibility defect: deleting VITE_PORT broke the existing npm.cmd fixture that forwards %VITE_PORT% to its owned stub-host.ps1. No fixture weakening, source correction, further mandatory check, product commit or push follows this failure under the current packet.\n\n## Exact proposed delta\n\nIn dev-up.ps1, retain both original VITE_PORT=[string]$FrontendPort and VITE_INLINE_CONFIG compatibility variables alongside the new real npm/Vite CLI arguments. Actual CLI port/strictPort remains authoritative for real Vite; variables preserve existing callers and Windows safety fixtures. Do not change old test assertions. Remaining approved four files retain their current source patch.\n\n## Proposed bounded continuation\n\nOne additional source compatibility correction, one disposable provider-free focused development invocation, one new full Platform mandatory invocation, then the unused Path-A and exact-head checks. Use actual existing tests/test_path_a_gate.py; the earlier generated prose's tests/control_plane/test_path_a_policy.py does not exist and has never been claimed executed. Keep the old immutable Decision unchanged; a new exact source scope/Decision/plan/preflight/Draft must bind the approved correction and mandatory replay explicitly.\n\nNo original failure/counter/deadline reset. Original source deadline2026-10-04T14:55:31.639949Z remains. New prospective activation/product commit and exact Draft publication need two new bounded branch pushes; do not claim those granted by the exhausted original phase. No actual browser/runtime/model calls, credentials, dependency installs, workflow dispatch/rerun, Ready/Merge, main push, tag/release/deploy or existing frontend mutation.\n\nMandatory source/local/natural exact-head CI evidence remains necessary; source completion is not authenticated real browser acceptance, independent audit, #118 completion or mainline landing.\n\nOwner explicitly replied \u6279\u51c6\uff0c\u7ee7\u7eed to the pending exact compatibility proposal in this chat on2026-10-04. Approval grants1 additional compatibility correction,1 focused development invocation,1 new mandatory full Platform invocation after preserving original failure, the unused Path-A and committed exact-head focused checks,2 branch pushes and1 new Draft. No actual browser/runtime/model/credential/install/Ready/Merge or workflow dispatch/rerun permission. Exact planning base is prior activation codex/issue118-launcher-repair-r3-v1-20261004@ae7475d3cef2a738a9ad68b2bd373234f67e99a5; underlying product source1b99c23d remains unchanged until carried candidate edits.\nExisting five-file candidate changes were already authorized and made under prior Draft1083. Freeze and preserve their exact hashes/patch before this activation; they are carried existing work, not newly edited before this Draft. Only Decision is staged/committed for activation. No new source correction until canonical gates/PRE_EXECUTION_AUTHORIZED/PUBLICATION_READY and bound Draft exist. Restore exactly the two original compatibility environment entries in dev-up.ps1; preserve actual Vite CLI arguments and all other four candidate files byte-identical. Preserve all original69 Python functions/all original native tests.\nSource hashes freeze for mandatory checks. Known Node E:\\Program Files\\nodejs\\node.exe@58e74bf02fc5bbacc41dcb8bef089961cd5bddd37830b87784e4fc624d145d1f may execute committed native standard-library source tests; no actual browser or SDK execution. One focused dev<=900s; full tests/platform_v1 once<=2400s with ONLY four original installed-OpenCode opt-in exclusions; tests/test_path_a_gate.py once<=120s; committed focused launcher/bootstrap/client-auth/host/session once<=900s. Each invocation uses a new disposable child under F:\\nrl-launch118-v2; create its empty parent first. No failed check is waived. Git diff --check and canonical publication readiness required. Natural exact-head CI must be observed with original native logs/JUnit/artifacts before claiming this source phase complete. Independent acceptance/actual Windows browser acceptance/full118/full384/fullgoal remain pending. Original absolute expiry 2026-10-04T14:55:31.639949+00:00; never renew runtime expiry or discard any failure/spending.\n",
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
      "command_id": "compatibility.publication",
      "command": "Two exact pushes/one Draft/two descriptions, read-only natural CI evidence. codex/issue118-launcher-compatibility-r3-v2-20261004",
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
    "note": "Provider-free disposable source tests only under F:\\nrl-launch118-v2; preserve all existing runtimes/shared dependencies/candidate source/unknown work."
  },
  "workstream_id": "issue118-launcher-compatibility-r3-v2",
  "source_issues": [
    118,
    384
  ],
  "local_browser_launch_limit": 0,
  "development_check_run_limit": 1,
  "development_correction_round_limit": 1,
  "execution_window_hours": 6,
  "integration_observation_surface": "user_local_exact_planning_base_fresh_branch",
  "runtime_host_launch_limit": 0,
  "frontend_launch_limit": 0,
  "approval_event_or_time": "2026-10-04T13:21:23.701585+00:00",
  "credential_status_probe_limit": 0,
  "provider_network_call_limit": 0,
  "pull_request_description_update_limit": 2,
  "owned_test_scratch_root": "F:\\nrl-launch118-v2",
  "mandatory_pytest_process_limit": 3,
  "cumulative_development_check_limit": 6,
  "cumulative_correction_round_limit": 7,
  "cumulative_prior_correction_rounds": 6,
  "cumulative_prior_development_checks": 5,
  "approved_repair_limits": {
    "new_corrections": 1,
    "new_development_checks": 1,
    "prior_source1081_dev": 3,
    "prior_source1081_corrections": 4,
    "prior_repair1083_dev": 2,
    "prior_repair1083_corrections": 2,
    "prior_repair_mandatory_failed": 1,
    "new_mandatory_full": 1,
    "unused_path_a": 1,
    "unused_exact_head": 1,
    "prior_failed_runtime_launches": 1,
    "runtime_launches_allowed": 0,
    "expires_at": "2026-10-04T14:55:31.639949+00:00"
  }
}
```
