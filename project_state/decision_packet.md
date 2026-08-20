# Decision: PRODUCT-UX-3/4 Spec Kit, knowledge, and Pack foundation V2

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v2",
  "round_id": "round_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v1",
  "follows_last_round_id": "round_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v1",
  "previous_audit_outcome": "V1_PREFLIGHT_ALLOWED_PATH_SCOPE_BLOCKED_ZERO_PRODUCT_MUTATION_ZERO_PUSH",
  "workstream_id": "issue260-product-ux34-speckit-knowledge-pack-r2-v2",
  "source_issue": 260,
  "related_issues": [177, 253],
  "required_branch": "owner/issue260-product-ux34-speckit-knowledge-pack-r2-v2",
  "starting_head": "33095219607936ccf7157580776dbfc498da6ddc",
  "activation_base_sha": "33095219607936ccf7157580776dbfc498da6ddc",
  "integration_base_ref": "main",
  "base_sha": "33095219607936ccf7157580776dbfc498da6ddc",
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "pre_pr_intent_assertions_deferred": [
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_id",
    "tests/platform_v1/test_contracts.py::TestActiveMergeIntentV6::test_active_binds_current_decision_locked_base_sha",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_id",
    "tests/platform_v1/test_merge_intent.py::TestActiveMergeIntent::test_active_binds_current_decision_locked_base_sha"
  ],
  "post_publication_binding_commit_limit": 1,
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "specify_cli_invocation_limit": 0,
  "semantic_embedding_call_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "issue_close_allowed": false,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "direct_push_to_main_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "tag_or_release_allowed": false,
  "deployment_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "create owner/issue260-product-ux34-speckit-knowledge-pack-r2-v2 from exact main 33095219607936ccf7157580776dbfc498da6ddc in an isolated canonical-LF checkout",
    "commit this immutable V2 Decision as the first new commit after 33095219607936ccf7157580776dbfc498da6ddc before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue260ux34v2.verify_baseline_and_upstreams",
      "command": "verify exact main and V1 blocked evidence; reobserve GitHub Spec Kit v0.16.5 spec plan tasks and bundle contracts plus installed LangGraph SQLite Store availability without installing or invoking them",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue260ux34v2.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before product mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.implement_product",
      "command": "implement provider-free Spec Kit v0.16.5-compatible inspectable artifacts and review-before-launch; use LangGraph SqliteStore on the existing TaskStore connection for advisory provenance knowledge; evolve CapabilityRegistry into a metadata-only Pack contract compatibility catalog with one fixture Pack; add bounded APIs frontend tests docs freshness and package-data binding",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_source_edit", "bounded_test_edit", "bounded_documentation_edit", "bounded_packaging_edit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.validate_backend",
      "command": "run focused goal knowledge capability Task API control store autonomy coordinator and contract tests including idempotency revision invalidation advisory authority provenance secret rejection Pack incompatibility no-activation and same-connection restart proofs",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.validate_frontend",
      "command": "run frontend typecheck tests and production build for planning review knowledge and Pack catalog loopback surfaces",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.prepublication_validation",
      "command": "run CI Platform blocking gate with ordinary seven deselections plus only four exact pre-PR intent assertions and require at least 1105 passes with no other failure; run CI responsibility transition readiness and diff checks; zero live calls installs credentials workflow or dependency change",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.publish_initial_draft",
      "command": "after prepublication validation push owner/issue260-product-ux34-speckit-knowledge-pack-r2-v2 once and create exactly one Draft PR to main; read its actual number without guessing",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34v2.bind_actual_pr",
      "command": "archive PR 277 active schema-v2 intent byte-for-byte as archive/pr277_v2.json and replace active.json with schema v2 bound to the observed PR base Decision Plan merge method workflows and expiry 2026-08-29T23:59:59Z; commit once without Decision edit",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34v2.final_bound_validation_and_push",
      "command": "after PR binding run full Platform gate with ordinary seven deselections and all deferred assertions passing; rerun focused frontend CI responsibility transition readiness and diff checks; push binding commit once and observe exact-head CI Decision Preflight State Gate",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "push", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34v2.audit_attest_land",
      "command": "after exact-head workflows succeed perform detached audit and ACCEPTED comment; reobserve CAS checks reviews threads; publish schema-v2 owner attestation; mark-ready and merge once with expected-head protection",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34v2.post_merge_verify",
      "command": "verify merge tree origin main push State Gate main CI mainline validation integration receipt then comment exact evidence on Issues 177 253 and 260 without closing them",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/platform_v1/control_store.py",
    "reverse_agent/platform_v1/goal_service.py",
    "reverse_agent/platform_v1/knowledge_service.py",
    "reverse_agent/platform_v1/capability_registry.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/packs/platform-engineering-fixture.json",
    "tests/platform_v1/test_goal_service.py",
    "tests/platform_v1/test_knowledge_service.py",
    "tests/platform_v1/test_capability_registry.py",
    "tests/platform_v1/test_task_service.py",
    "frontend/src/lib/platform-client.ts",
    "frontend/src/hooks/use-platform.ts",
    "frontend/src/components/goal-composer.tsx",
    "frontend/src/components/goal-progress.tsx",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/routes/home.tsx",
    "frontend/src/routes/knowledge.tsx",
    "frontend/src/routes/packs.tsx",
    "frontend/src/entry.client.tsx",
    "frontend/tests/platform-home.test.tsx",
    "frontend/tests/knowledge.test.tsx",
    "frontend/tests/packs.test.tsx",
    "frontend/tests/accessibility.test.tsx",
    "frontend/tests/responsive.test.tsx",
    "governance/freshness-registry.json",
    "pyproject.toml",
    "docs/architecture/SPEC_KIT_KNOWLEDGE_PACK_CONTRACT.md",
    "README.md",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr277_v2.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**", "AGENTS.md", "requirements*.txt", "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py", "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/opencode_server_transport.py", "reverse_agent/workflows/**", "project_state/rounds/**"
  ],
  "reference_paths": ["docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md", "docs/architecture/LANGGRAPH_TEAM_RUNTIME.md"],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "force_push", "rebase", "reset", "clean", "stash", "amend", "restore",
    "dependency_install", "workflow_change", "live_model_call", "provider_network_call", "specify_cli_invocation",
    "semantic_embedding_call", "credential_access", "auth_store_read", "runner_dispatch", "tag_or_release", "deployment",
    "worktree_deletion", "history_rewrite", "second_database", "second_task_store", "custom_planning_framework",
    "custom_package_manager", "dynamic_pack_code_execution", "pack_self_authorization", "raw_secret_persistence",
    "attack_or_hostile_binary_work"
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "local_network_exceptions": [
      "verify exact main and V1 blocked evidence; reobserve GitHub Spec Kit v0.16.5 spec plan tasks and bundle contracts plus installed LangGraph SQLite Store availability without installing or invoking them",
      "after prepublication validation push owner/issue260-product-ux34-speckit-knowledge-pack-r2-v2 once and create exactly one Draft PR to main; read its actual number without guessing",
      "after PR binding run full Platform gate with ordinary seven deselections and all deferred assertions passing; rerun focused frontend CI responsibility transition readiness and diff checks; push binding commit once and observe exact-head CI Decision Preflight State Gate",
      "after exact-head workflows succeed perform detached audit and ACCEPTED comment; reobserve CAS checks reviews threads; publish schema-v2 owner attestation; mark-ready and merge once with expected-head protection",
      "verify merge tree origin main push State Gate main CI mainline validation integration receipt then comment exact evidence on Issues 177 253 and 260 without closing them"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "pyproject.toml", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": ["pyproject.toml", "project_state/gates/**"],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE260_PRODUCT_UX34_SPECKIT_KNOWLEDGE_PACK_MERGED_MAIN_GREEN",
  "blocked_terminal": "ISSUE260_PRODUCT_UX34_SPECKIT_KNOWLEDGE_PACK_R2_V2_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Reuse Spec Kit v0.16.5 artifact/Bundle contracts and the pinned LangGraph SQLite Store to add reviewable planning, advisory project knowledge, and a metadata-only Pack catalog on the existing TaskStore and CapabilityRegistry.

## Acceptance

1. `spec.md`, `plan.md`, and `tasks.md`-compatible artifacts carry contract/version identity, individual digests, clarification readiness, knowledge references, and deterministic revision invalidation with zero model or `specify` invocation.
2. Browser planning stops at `PLANNED`; a separate explicit owner action approves, activates a bounded window, and launches through the existing authoritative path.
3. Knowledge uses `langgraph-checkpoint-sqlite==3.1.0` `SqliteStore` on the exact TaskStore connection under its RLock, with append-only versioning, provenance, idempotency, secret rejection, deterministic retrieval, and fixed `authority=NONE`.
4. Pack manifests remain bounded JSON metadata: multiple capabilities, Skills, Spec Kit Bundle reference, requirements, verifiers/evals, compatibility preview, and one packaged fixture. No install, import, command execution, activation, self-authorization, provider, embedding, or second store.
5. Loopback APIs and frontend expose planning review, knowledge, and Pack catalog with sanitized durable truth. Backend/frontend/full gates and exact-head landing evidence pass.

## V1 negative evidence

V1 Decision commit `db3fd3a9160206dd5bf7f00839f0d6d63dc3d0b4` reached `transition-preflight: BLOCKED` only because generated gate paths were not also in `allowed_mutated_paths`. V1 contains no product mutation, push, PR, dependency change, credential access, or external execution. V2 changes only that authority declaration and starts again from exact main.
