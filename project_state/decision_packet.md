# Decision Packet - Issue687 provider-free test isolation and truthful diagnostics

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260919_issue687_ci_diagnostic_isolation_r2_v2",
  "round_id": "round_20260919_issue687_ci_diagnostic_isolation_r2_v2",
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
  "follows_last_decision_id": "decision_20260919_issue721_safe_base_refresh_r2_v11_current",
  "follows_last_round_id": "round_20260919_issue721_safe_base_refresh_r2_v11_current",
  "integration_base_ref": "main",
  "base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "activation_base_sha": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "starting_head": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "workflow_profile": "baseline",
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
  "post_publication_binding_commit_limit": 0,
  "commit_order_contract": [
    "D_decision_only_on_clean_tree",
    "startup_snapshot",
    "transition_command_plan",
    "transition_lint",
    "transition_preflight_pre",
    "worktree_publication_readiness",
    "S_semantic_implementation_only"
  ],
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "dependency_install_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/project_gate.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/github_remote_verifier.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/test_mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/test_project_gate.py",
      "minimum_risk": "R2"
    }
  ],
  "workflow_dispatch_limit": 0,
  "workflow_dispatch_allowed": false,
  "provider_free_acceptance_required": true,
  "repository": "dddd2024/Nerelan",
  "source_issue": 687,
  "parent_issue": 659,
  "mother_roadmap": 137,
  "decision_scope": "BOUNDED_PROVIDER_FREE_TEST_SELECTION_AND_DIAGNOSTIC_DISPLAY",
  "required_branch": "codex/ci-diagnostic-tool-isolation-r2-v2-20260919",
  "workstream_id": "issue687-ci-diagnostic-isolation-r2-v2",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "Renewed full Owner delegation authorizes bounded successor of rejected PR958. Preserve original failed head and tests. Correct workflow boundary assertions for exact diagnostic steps/exit handling, retaining all existing blocking controls. Existing freshness failure remains independently blocking; this round does not refresh dates or claim component compatibility.",
  "superseded_evidence": "PR958 head84020997dc1a094fa14d61da91a156a8ccfa4a97 rejected by independent audit; CI35441998404, DecisionPreflight35441998367, StateGate35441998382 failed existing boundary assertion; freshness35441998425 failed separately. No reuse of old Decision authority.",
  "fresh_base": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "current_main_expected": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "source_test_mutation_authorized": true,
  "source_test_mutation_scope": [
    ".github/workflows/ci.yml",
    "pyproject.toml",
    "tests/conftest.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/test_ci_responsibility.py",
    "scripts/ci_test_summary.py",
    "tests/test_project_gate.py"
  ],
  "issue_completion_close_allowed": [],
  "landing_authority_scope_note": "Draft implementation only; no Ready/Merge under this Decision. Preserve occupied #721 and all other accepted candidate heads.",
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
    "pyproject.toml",
    "tests/conftest.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/test_ci_responsibility.py",
    "scripts/ci_test_summary.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/test_project_gate.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
    "pyproject.toml",
    "tests/conftest.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/test_ci_responsibility.py",
    "scripts/ci_test_summary.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "tests/test_project_gate.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/control_plane/path_a.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".codex-skills/**",
    "docs/**",
    "reverse_agent/**",
    "frontend/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
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
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit"
  ],
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Publish only locally authored exact Decision/semantic trees and commits to codex/ci-diagnostic-tool-isolation-r2-v2-20260919 in dddd2024/Nerelan, one Draft against locked main, description/comments for Issue687 and that Draft. No local git push, Ready/Merge or dispatch."
    ]
  },
  "semantic_implementation_contract": {
    "specification": "Mark exactly the four already excluded installed OpenCode methods, leaving each function body/assertion unchanged. Register installed_opencode marker. Add a thin pytest collection hook with explicit --run-installed-opencode opt-in, default deselection of exactly marked tests even if another -m selection is supplied. Opt-in changes collection only and is not execution authority. Keep existing four exact blocking-gate --deselect controls and all existing CI responsibility assertions. Full nonblocking diagnostic records real pytest exit code, writes native JUnit XML, and displays raw tests/failures/errors/skipped plus explicit excluded scope in GitHub step summary. Never derive passed by subtraction; missing/malformed XML or unavailable exit is unknown, not success. Use one small stdlib summary script and native artifact upload; no new authority/gate/schema or dependency. Update only test_transition_packaging_and_workflow_boundary in tests/test_project_gate.py: allow the two exact new summary/artifact step names, and replace the obsolete single-line diagnostic assertion with exact multiline command, exit recording/propagation and summary/artifact assertions. Preserve every other test and blocking workflow assertion.",
    "completion_boundary": "Keep provider-free blocking gate blocking and full diagnostic nonblocking. No actual OpenCode/IDA/model/provider invocation. Verify exact four marker identities and unchanged method ASTs; isolated synthetic default/explicit opt-in/-m collection; summary with success/failure/errors/no-tests, missing/corrupt XML and double failures. Natural CI/Preflight/StateGate on exact head and independent review; historical team/legacy failures on base remain tracked separately. Full focused workflow suite must pass locally before publication. Freshness is a separately known failure: no all-checks-success or acceptance claim until real component revalidation under separate bounded authority; no skipping or modifying freshness workflow."
  },
  "run_environment_binding": {
    "run_strategy": "user_local",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "codex/ci-diagnostic-tool-isolation-r2-v2-20260919",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  },
  "allowed_commands": [
    {
      "command_id": "issue687r2.bootstrap",
      "phase": "bootstrap",
      "command": "Use this exact Windows local checkout F:/Nerelan-issue687-ci-diagnostics-v2. Commit Decision only, then startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED before test edits.",
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
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue687r2.implement",
      "phase": "implementation",
      "command": "Implement only the nine exact paths in semantic_implementation_contract. Preserve all four integration test method bodies and old blocking-deselection assertions. Commit once after scoped development checks; no real-tool test execution or product/runtime changes.",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "tests/conftest.py",
        "tests/platform_v1/test_task3c_v4_repairs.py",
        "tests/platform_v1/test_task3c_v5_opencode_probe.py",
        "tests/platform_v1/test_task3c_v6_production_relay.py",
        "tests/test_ci_responsibility.py",
        "scripts/ci_test_summary.py",
        "tests/test_project_gate.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue687r2.validate",
      "phase": "validation",
      "command": "Run the complete provider-free Focused tests command from CI plus tests/test_path_a_gate.py before publication, git diff --check, exact original function AST comparison except the explicitly revised workflow-boundary function, and final preflight/readiness. Preserve tests/controls; no real installed tools/providers. Natural CI should reach full diagnostics and native artifact; report actual results and separately failing unchanged freshness honestly.",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue687r2.publish",
      "phase": "publication",
      "command": "Publish exact local trees/commits with GitHub Git API; create one named branch and one Draft PR, update its body/comments; never local git push, Ready/Merge or workflow rerun.",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue687r2.observe",
      "phase": "final_evidence",
      "command": "Observe natural exact-head CI/Decision Preflight/State Gate and independent audit. Keep Draft.",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "code_read",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ]
}
```

## Scope
Implement existing Issue687 installed-tool selection and nonblocking diagnostic presentation with mature pytest/JUnit/GitHub mechanisms. No changes to production, fixture-repair branches, governance selector, blocking policy, dependencies or other workflows. Known freshness failure remains a separate acceptance blocker; no registry-date refresh is authorized.

## Stop conditions
Stop on base drift, activated Decision mutation, scope expansion, failed mandatory final checks, changed integration assertions, unexpected files or actual external-tool/provider execution. Generated gates stay uncommitted. This is not acceptance of the excluded installed-tool integrations.
