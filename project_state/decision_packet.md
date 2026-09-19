# Decision Packet - Issue659 reviewed fix integration

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260919_issue659_reviewed_fixes_integration_r2_v1",
  "round_id": "round_20260919_issue659_reviewed_fixes_integration_r2_v1",
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
  "follows_last_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v5",
  "follows_last_round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v5",
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
  "source_issue": 659,
  "parent_issue": 137,
  "mother_roadmap": 137,
  "decision_scope": "BOUNDED_REVIEWED_PRODUCT_AND_TEST_FIX_INTEGRATION",
  "required_branch": "codex/audit-fixes-integration-r2-20260919",
  "workstream_id": "issue659-reviewed-fixes-integration-r2-v1",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User explicitly renewed full Owner authorization to complete the final project. This bounded integration incorporates independently scoped-reviewed fixes from PR949/952/954/957/959/960 at their exact immutable source blobs, removes duplicated team fixture content and jointly validates the actual combined provider-free product/test result. Prior Decisions are historical evidence only, not reused authority.",
  "superseded_evidence": "PR958 rejected and not a source. PR959 scoped ACCEPT but separate freshness check failed; this candidate incorporates accepted960 freshness evidence. Prior individual PRs are not claimed merged. Occupied721 worktree is untouched; integration does not grant main mutation or landing.",
  "fresh_base": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "current_main_expected": "ef8bb6959ac37301c880e0971a97a9d56e9c99a9",
  "source_test_mutation_authorized": true,
  "source_test_mutation_scope": [
    ".github/workflows/ci.yml",
    "docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md",
    "governance/freshness-registry.json",
    "pyproject.toml",
    "reverse_agent/platform_v1/environment_discovery.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "scripts/ci_test_summary.py",
    "tests/conftest.py",
    "tests/platform_v1/test_environment_discovery.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/test_ci_responsibility.py",
    "tests/test_freshness.py",
    "tests/test_local_reverse_forced_ida_extract.py",
    "tests/test_project_gate.py",
    "tests/test_team_graph.py"
  ],
  "issue_completion_close_allowed": [],
  "landing_authority_scope_note": "Draft implementation only; no Ready/Merge under this Decision. Preserve occupied #721 and all other accepted candidate heads.",
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
    "docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md",
    "governance/freshness-registry.json",
    "pyproject.toml",
    "reverse_agent/platform_v1/environment_discovery.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "scripts/ci_test_summary.py",
    "tests/conftest.py",
    "tests/platform_v1/test_environment_discovery.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/test_ci_responsibility.py",
    "tests/test_freshness.py",
    "tests/test_local_reverse_forced_ida_extract.py",
    "tests/test_project_gate.py",
    "tests/test_team_graph.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    ".github/workflows/ci.yml",
    "docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md",
    "governance/freshness-registry.json",
    "pyproject.toml",
    "reverse_agent/platform_v1/environment_discovery.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "scripts/ci_test_summary.py",
    "tests/conftest.py",
    "tests/platform_v1/test_environment_discovery.py",
    "tests/platform_v1/test_task3c_v4_repairs.py",
    "tests/platform_v1/test_task3c_v5_opencode_probe.py",
    "tests/platform_v1/test_task3c_v6_production_relay.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/test_ci_responsibility.py",
    "tests/test_freshness.py",
    "tests/test_local_reverse_forced_ida_extract.py",
    "tests/test_project_gate.py",
    "tests/test_team_graph.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/control_plane/path_a.py"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/agents/**",
    ".codex-skills/**",
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
      "Read canonical candidate/main refs, checks/reviews and source objects; publish exact local Git trees/commits only to codex/audit-fixes-integration-r2-20260919 in dddd2024/Nerelan, one Draft against locked main, its description/comments and Issue659 coordination. No Ready/Merge, main mutation or workflow dispatch."
    ]
  },
  "semantic_implementation_contract": {
    "specification": "Materialize only these exact reviewed source file blobs on the locked current base, with no new semantic edits: {\".github/workflows/ci.yml\": {\"base_blob\": \"28c25e8b4a43bcd89e3caab5797f10cd918ed3fa\", \"blob\": \"700f614646f9b39b6d50a42c06920983e6f30738\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md\": {\"base_blob\": \"e7b23330b95ac3dcf6ff60f58cfcd78f1dd8e402\", \"blob\": \"8a49193d4d07830ea158ce24e56530cad1eef5c0\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"governance/freshness-registry.json\": {\"base_blob\": \"3ed39c67b86fa8b71beeb5b910a534db988d3b7b\", \"blob\": \"4311921ecea8d2d84151bd14a6c4541640bd884b\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"pyproject.toml\": {\"base_blob\": \"35f5b600704a882193a21329129a5ef01258b5e7\", \"blob\": \"85f0d98d384cbb616bdb0795e4203f3fe201de70\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"reverse_agent/platform_v1/environment_discovery.py\": {\"base_blob\": null, \"blob\": \"3aada0845df464a80ab06db0d2d085a908693db0\", \"head\": \"c6af6dfe06e5371f526d44b4e484896a36275192\", \"pr\": 949}, \"reverse_agent/platform_v1/task_runtime.py\": {\"base_blob\": \"38f52c9f1c3b9d4f82b0d3c547c5ad80bf1c7a35\", \"blob\": \"7e40c13536ce36cacb3eb1d0689a83d370b94eff\", \"head\": \"4070b1592dad3479a82788e7c53140a4f8044877\", \"pr\": 952}, \"scripts/ci_test_summary.py\": {\"base_blob\": null, \"blob\": \"1f33ce1dca8f0cccdca9ca8d4ebe09502a3bf1fd\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/conftest.py\": {\"base_blob\": null, \"blob\": \"586f3fb1a3408c336b81f6fff9f4e9a00376dccb\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_environment_discovery.py\": {\"base_blob\": null, \"blob\": \"335945266bd389c1cd547d318b672696a22d8843\", \"head\": \"c6af6dfe06e5371f526d44b4e484896a36275192\", \"pr\": 949}, \"tests/platform_v1/test_task3c_v4_repairs.py\": {\"base_blob\": \"05d066148c6544e473608cec273dc52f62b62ecc\", \"blob\": \"2723b001320c0efb09df9d6af31b4de30a9052f8\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task3c_v5_opencode_probe.py\": {\"base_blob\": \"e11b1ba17a14f4fd5fb4e47e3cd0855c7456c7f8\", \"blob\": \"45575b80f450e84fb9b5751191f8079849391b42\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task3c_v6_production_relay.py\": {\"base_blob\": \"b544c01e6145cfcc2cc71f8c6a0b3d924c3d41ae\", \"blob\": \"a0af2926aee327b15355cda94026af0ee2ed80ed\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task_runtime.py\": {\"base_blob\": \"7214825433053a380a5fd44200ca0b4061c33a56\", \"blob\": \"354cbea0bd0b0a26299a266b1ee50ce9357e91c5\", \"head\": \"4070b1592dad3479a82788e7c53140a4f8044877\", \"pr\": 952}, \"tests/test_ci_responsibility.py\": {\"base_blob\": \"a8bf1f481dd654038c4d4360edbe50171587f07c\", \"blob\": \"8f75d5f1800d6846d698bc96d21a1079f0148d99\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/test_freshness.py\": {\"base_blob\": \"43a82cf4fd866e45ecd4f4b7b258db778bd9ec82\", \"blob\": \"d497b985c8cc2012aac5aa86fff2482d520d66dd\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"tests/test_local_reverse_forced_ida_extract.py\": {\"base_blob\": \"a96fc664ae14a29e6515a89c4fbdd0ace33cc7e3\", \"blob\": \"15dfe5744f4ef310c58c1caddd77415a177d4ed7\", \"head\": \"19bf478e685007f526c48ab3728c6ec22401b0fd\", \"pr\": 957}, \"tests/test_project_gate.py\": {\"base_blob\": \"ad51d6f178faee71c04b97515d149195bb8b7bd9\", \"blob\": \"5ff02925153f80bda5a75df26fc04541c836ce50\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/test_team_graph.py\": {\"base_blob\": \"c0e8a1ce146b7b0f0d53f0f0532f74553d5ca7b1\", \"blob\": \"fd82474b4a81ed186de125ffb29b0ddeec5e32d9\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}}. Base blob must equal manifest base_blob (or file must be absent); stop on mismatch rather than overwriting new main work. Duplicated team fixture is identical and included once. Preserve every source assertion, four exact installed markers/default opt-in, blocking controls, 30-day freshness policy, runtime authority and generated-gate exclusion. No dependency change/install, new framework/gate/schema, real external-tool or provider/model invocation.",
    "completion_boundary": "Joint provider-free correctness is required, not just individual branch evidence. Local targeted checks listed below and current UTC freshness must pass, source-content equality and git diff --check must pass, natural exact-head CI/DecisionPreflight/StateGate/freshness all SUCCESS and native full diagnostic must actually exit0 with no failures/errors and exactly4 installed cases deselected. Historical18 provider-free failures must be repaired, not skipped. Independent exact-head audit required. Keep Draft; main landing requires separately bounded existing PathB mechanism. If721 changes main before publication, stop; never overwrite its test_project_gate changes."
  },
  "run_environment_binding": {
    "run_strategy": "user_local",
    "canonical_repository": "dddd2024/Nerelan",
    "target_owner_branch": "codex/audit-fixes-integration-r2-20260919",
    "authority_path": "Path B R2 transition",
    "local_agent_ready_or_merge_authority": false
  },
  "allowed_commands": [
    {
      "command_id": "issue659r2.bootstrap",
      "phase": "bootstrap",
      "command": "Use fresh F:/Nerelan-audit-fixes-integration on exact locked base. Decision-only activation, startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness; require PRE_EXECUTION_AUTHORIZED before source materialization.",
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
      "command_id": "issue659r2.implement",
      "phase": "implementation",
      "command": "Materialize only these exact reviewed source file blobs on the locked current base, with no new semantic edits: {\".github/workflows/ci.yml\": {\"base_blob\": \"28c25e8b4a43bcd89e3caab5797f10cd918ed3fa\", \"blob\": \"700f614646f9b39b6d50a42c06920983e6f30738\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md\": {\"base_blob\": \"e7b23330b95ac3dcf6ff60f58cfcd78f1dd8e402\", \"blob\": \"8a49193d4d07830ea158ce24e56530cad1eef5c0\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"governance/freshness-registry.json\": {\"base_blob\": \"3ed39c67b86fa8b71beeb5b910a534db988d3b7b\", \"blob\": \"4311921ecea8d2d84151bd14a6c4541640bd884b\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"pyproject.toml\": {\"base_blob\": \"35f5b600704a882193a21329129a5ef01258b5e7\", \"blob\": \"85f0d98d384cbb616bdb0795e4203f3fe201de70\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"reverse_agent/platform_v1/environment_discovery.py\": {\"base_blob\": null, \"blob\": \"3aada0845df464a80ab06db0d2d085a908693db0\", \"head\": \"c6af6dfe06e5371f526d44b4e484896a36275192\", \"pr\": 949}, \"reverse_agent/platform_v1/task_runtime.py\": {\"base_blob\": \"38f52c9f1c3b9d4f82b0d3c547c5ad80bf1c7a35\", \"blob\": \"7e40c13536ce36cacb3eb1d0689a83d370b94eff\", \"head\": \"4070b1592dad3479a82788e7c53140a4f8044877\", \"pr\": 952}, \"scripts/ci_test_summary.py\": {\"base_blob\": null, \"blob\": \"1f33ce1dca8f0cccdca9ca8d4ebe09502a3bf1fd\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/conftest.py\": {\"base_blob\": null, \"blob\": \"586f3fb1a3408c336b81f6fff9f4e9a00376dccb\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_environment_discovery.py\": {\"base_blob\": null, \"blob\": \"335945266bd389c1cd547d318b672696a22d8843\", \"head\": \"c6af6dfe06e5371f526d44b4e484896a36275192\", \"pr\": 949}, \"tests/platform_v1/test_task3c_v4_repairs.py\": {\"base_blob\": \"05d066148c6544e473608cec273dc52f62b62ecc\", \"blob\": \"2723b001320c0efb09df9d6af31b4de30a9052f8\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task3c_v5_opencode_probe.py\": {\"base_blob\": \"e11b1ba17a14f4fd5fb4e47e3cd0855c7456c7f8\", \"blob\": \"45575b80f450e84fb9b5751191f8079849391b42\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task3c_v6_production_relay.py\": {\"base_blob\": \"b544c01e6145cfcc2cc71f8c6a0b3d924c3d41ae\", \"blob\": \"a0af2926aee327b15355cda94026af0ee2ed80ed\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/platform_v1/test_task_runtime.py\": {\"base_blob\": \"7214825433053a380a5fd44200ca0b4061c33a56\", \"blob\": \"354cbea0bd0b0a26299a266b1ee50ce9357e91c5\", \"head\": \"4070b1592dad3479a82788e7c53140a4f8044877\", \"pr\": 952}, \"tests/test_ci_responsibility.py\": {\"base_blob\": \"a8bf1f481dd654038c4d4360edbe50171587f07c\", \"blob\": \"8f75d5f1800d6846d698bc96d21a1079f0148d99\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/test_freshness.py\": {\"base_blob\": \"43a82cf4fd866e45ecd4f4b7b258db778bd9ec82\", \"blob\": \"d497b985c8cc2012aac5aa86fff2482d520d66dd\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}, \"tests/test_local_reverse_forced_ida_extract.py\": {\"base_blob\": \"a96fc664ae14a29e6515a89c4fbdd0ace33cc7e3\", \"blob\": \"15dfe5744f4ef310c58c1caddd77415a177d4ed7\", \"head\": \"19bf478e685007f526c48ab3728c6ec22401b0fd\", \"pr\": 957}, \"tests/test_project_gate.py\": {\"base_blob\": \"ad51d6f178faee71c04b97515d149195bb8b7bd9\", \"blob\": \"5ff02925153f80bda5a75df26fc04541c836ce50\", \"head\": \"0e3335657dde4720ebc4a1d3673e3a4bfff4859a\", \"pr\": 959}, \"tests/test_team_graph.py\": {\"base_blob\": \"c0e8a1ce146b7b0f0d53f0f0532f74553d5ca7b1\", \"blob\": \"fd82474b4a81ed186de125ffb29b0ddeec5e32d9\", \"head\": \"8a3a18b9686e64f8f1690feede1dd71199347a4b\", \"pr\": 960}}. Base blob must equal manifest base_blob (or file must be absent); stop on mismatch rather than overwriting new main work. Duplicated team fixture is identical and included once. Preserve every source assertion, four exact installed markers/default opt-in, blocking controls, 30-day freshness policy, runtime authority and generated-gate exclusion. No dependency change/install, new framework/gate/schema, real external-tool or provider/model invocation.",
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
        "docs/architecture/FRESHNESS_AND_DRIFT_GOVERNANCE.md",
        "governance/freshness-registry.json",
        "pyproject.toml",
        "reverse_agent/platform_v1/environment_discovery.py",
        "reverse_agent/platform_v1/task_runtime.py",
        "scripts/ci_test_summary.py",
        "tests/conftest.py",
        "tests/platform_v1/test_environment_discovery.py",
        "tests/platform_v1/test_task3c_v4_repairs.py",
        "tests/platform_v1/test_task3c_v5_opencode_probe.py",
        "tests/platform_v1/test_task3c_v6_production_relay.py",
        "tests/platform_v1/test_task_runtime.py",
        "tests/test_ci_responsibility.py",
        "tests/test_freshness.py",
        "tests/test_local_reverse_forced_ida_extract.py",
        "tests/test_project_gate.py",
        "tests/test_team_graph.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue659r2.validate",
      "phase": "validation",
      "command": "Run python -B -m pytest tests/platform_v1/test_environment_discovery.py tests/platform_v1/test_task_runtime.py tests/test_team_graph.py tests/test_local_reverse_forced_ida_extract.py tests/test_ci_responsibility.py tests/test_project_gate.py::test_transition_packaging_and_workflow_boundary tests/test_freshness.py tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_decision_preflight.py tests/test_development_graph.py tests/platform_v1/test_unattended_coordinator.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_durable_execution_v5.py tests/platform_v1/test_goal_service.py tests/platform_v1/test_goal_plan_revision.py -q -p no:cacheprovider; existing current UTC freshness CLI; safe --collect-only comparison default versus --run-installed-opencode on three integration files; verify all18 exact source blobs, no other semantic path, git diff --check and final preflight/readiness. Natural full diagnostic exacthead must be exit0; no added skips/exclusions hiding historical failures. No execution of opt-in installed cases.",
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
      "command_id": "issue659r2.publish",
      "phase": "publication",
      "command": "Publish exact local trees/commits via GitHub Git API to the named fresh branch and one Draft PR for Issue659; re-read exact SHA and main, update its body/comments; no git push/Ready/Merge/dispatch.",
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
      "command_id": "issue659r2.observe",
      "phase": "final_evidence",
      "command": "Verify four natural exact-head checks, actual full diagnostic exit0/nativeJUnit and independent exact-head audit. Keep Draft.",
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
Joint integration of18 exact reviewed semantic files. No new product scope or landing authority.

## Stop conditions
Stop affected action on main/base/source-blob drift, activated Decision mutation, mandatory failure or unexpected file. Preserve occupied721 and all prior evidence. Four excluded installed integrations remain unaccepted; no claim of real-provider or entire project completion.
