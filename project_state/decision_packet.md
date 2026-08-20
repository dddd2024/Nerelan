# Decision: PRODUCT-UX-3/4 Spec Kit planning, project knowledge, and Pack catalog

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v1",
  "round_id": "round_20260821_issue260_product_ux34_speckit_knowledge_pack_r2_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "follows_last_round_id": "round_20260821_issue276_durable_parallel_task_batches_r2_v3",
  "previous_audit_outcome": "ISSUE276_DURABLE_LANGGRAPH_PARALLEL_TASK_BATCH_MERGED_MAIN_GREEN_ISSUE_CLOSED",
  "workstream_id": "issue260-product-ux34-speckit-knowledge-pack-r2-v1",
  "source_issue": 260,
  "related_issues": [177, 253],
  "required_branch": "owner/issue260-product-ux34-speckit-knowledge-pack-r2-v1",
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
  "governance_artifact_risk_tier": "R2",
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
    "create owner/issue260-product-ux34-speckit-knowledge-pack-r2-v1 from exact main 33095219607936ccf7157580776dbfc498da6ddc in an isolated canonical-LF checkout",
    "commit this immutable Decision as the first new commit after 33095219607936ccf7157580776dbfc498da6ddc before product or merge-intent mutation",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue260ux34.verify_baseline_and_upstreams",
      "command": "verify exact main 33095219607936ccf7157580776dbfc498da6ddc and reobserve GitHub Spec Kit v0.16.5 spec plan tasks and bundle contracts plus installed LangGraph SQLite Store availability without installing or invoking them",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue260ux34.run_transition_gates",
      "command": "run startup-snapshot transition-command-plan transition-lint and transition-preflight --mode pre; require PRE_EXECUTION_AUTHORIZED before product mutation",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "generate_governance_artifact"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.implement_product",
      "command": "implement provider-free Spec Kit v0.16.5-compatible inspectable spec plan tasks artifacts and review-before-launch; reuse the existing TaskStore connection through LangGraph SqliteStore for append-only advisory project knowledge with provenance; evolve the existing capability registry into a metadata-only Pack contract and compatibility catalog with one deterministic fixture Pack; add bounded APIs frontend pages tests docs and freshness binding",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_source_edit", "bounded_test_edit", "bounded_documentation_edit", "bounded_packaging_edit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.validate_backend",
      "command": "run focused goal knowledge capability Task API control store autonomy and coordinator tests including idempotency revision invalidation advisory authority provenance secret rejection Pack incompatibility no-activation and same-connection restart proofs",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.validate_frontend",
      "command": "run frontend typecheck tests and production build proving planning review knowledge and Pack catalog surfaces use only loopback sanitized API truth",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.prepublication_validation",
      "command": "run the CI Platform blocking gate with its ordinary seven deselections plus only the four exact pre_pr_intent_assertions_deferred entries and require 1105 or more passing tests with no other failure; run CI responsibility transition lint preflight readiness and diff checks; zero live model provider Specify CLI embedding credential dependency install or workflow change",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "diff_validation", "repository_observation"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.publish_initial_draft",
      "command": "after all prepublication validation passes push owner/issue260-product-ux34-speckit-knowledge-pack-r2-v1 once and create exactly one Draft PR to main; read its actual number without guessing",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["push", "pull_request_create", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34.bind_actual_pr",
      "command": "archive committed PR 277 schema-v2 active intent byte-for-byte as archive/pr277_v2.json and replace active.json with schema v2 bound to the observed PR locked base this Decision committed Plan merge method merge exact three workflows and expiry 2026-08-29T23:59:59Z; commit once without Decision edit",
      "phase": "implementation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["bounded_governance_mutation", "stage_authorized_paths", "commit"], "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue260ux34.final_bound_validation_and_push",
      "command": "after actual PR binding run the full CI Platform blocking gate with only the ordinary seven CI deselections and require all four formerly deferred assertions pass; rerun focused frontend CI responsibility transition readiness and diff checks; push the single binding commit once and observe fresh exact-head CI Decision Preflight and State Gate",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["run_checks", "push", "repository_observation", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34.audit_attest_land",
      "command": "after exact-head workflows succeed perform clean detached audit and ACCEPTED comment; reobserve base head checks MERGEABLE CLEAN zero blocking reviews and threads; publish schema-v2 approval attestation bound to actual comment and run IDs; owner mark-ready and merge once with merge and expected-head protection",
      "phase": "publication", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "mark_ready", "merge", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation", "allowed_only_after_validation": true
    },
    {
      "command_id": "issue260ux34.post_merge_verify",
      "command": "verify merge commit tree and origin main; wait for State Gate push and main CI; require mainline-merge-validation and integration receipt PASSED; comment exact evidence on Issues 177 253 and 260 without closing their longer-lived tracks",
      "phase": "validation", "required": true, "expected_exit_codes": [0], "execution_surface": "local",
      "operations": ["repository_observation", "issue_comment", "network_access"], "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
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
  "forbidden_mutated_paths": [
    ".github/**", "AGENTS.md", "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/unattended_coordinator.py", "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/opencode_server_transport.py", "reverse_agent/workflows/**",
    "project_state/rounds/**"
  ],
  "reference_paths": [
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/LANGGRAPH_TEAM_RUNTIME.md"
  ],
  "generated_artifact_paths": ["project_state/gates/**"],
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
      "verify exact main 33095219607936ccf7157580776dbfc498da6ddc and reobserve GitHub Spec Kit v0.16.5 spec plan tasks and bundle contracts plus installed LangGraph SQLite Store availability without installing or invoking them",
      "after all prepublication validation passes push owner/issue260-product-ux34-speckit-knowledge-pack-r2-v1 once and create exactly one Draft PR to main; read its actual number without guessing",
      "after actual PR binding run the full CI Platform blocking gate with only the ordinary seven CI deselections and require all four formerly deferred assertions pass; rerun focused frontend CI responsibility transition readiness and diff checks; push the single binding commit once and observe fresh exact-head CI Decision Preflight and State Gate",
      "after exact-head workflows succeed perform clean detached audit and ACCEPTED comment; reobserve base head checks MERGEABLE CLEAN zero blocking reviews and threads; publish schema-v2 approval attestation bound to actual comment and run IDs; owner mark-ready and merge once with merge and expected-head protection",
      "verify merge commit tree and origin main; wait for State Gate push and main CI; require mainline-merge-validation and integration receipt PASSED; comment exact evidence on Issues 177 253 and 260 without closing their longer-lived tracks"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "pyproject.toml", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": ["pyproject.toml"],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE260_PRODUCT_UX34_SPECKIT_KNOWLEDGE_PACK_MERGED_MAIN_GREEN",
  "blocked_terminal": "ISSUE260_PRODUCT_UX34_SPECKIT_KNOWLEDGE_PACK_R2_V1_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Land the next productization slice without widening execution authority: Spec Kit v0.16.5-compatible planning artifacts become reviewable before launch; project memory uses the already-pinned LangGraph SQLite Store on the one TaskStore connection and remains advisory; Pack discovery becomes a strict metadata and compatibility catalog derived from the existing registry and Spec Kit Bundle concepts.

## Acceptance

1. Goal planning persists inspectable `spec.md`, `plan.md`, and `tasks.md`-compatible artifacts, per-artifact digests, contract/version identity, clarification readiness, knowledge references, and deterministic revision invalidation without a model call or Spec Kit CLI invocation.
2. Browser creation stops at a reviewable PLANNED goal; execution begins only after a separate explicit owner launch action. Existing server-side approval, window, TaskStore, LangGraph, executor, policy, and evidence paths remain the execution authority.
3. Project knowledge is stored through pinned `langgraph-checkpoint-sqlite==3.1.0` `SqliteStore` on the existing TaskStore SQLite connection under the TaskStore RLock. Entries are append-only, versioned, provenance-bound, secret-rejecting, advisory, and never execution authority.
4. The existing CapabilityRegistry loads a strict bounded Pack manifest with Pack-vs-Skill distinction, multiple declared capabilities, Spec Kit Bundle reference, requirements, verifier/eval metadata, deterministic compatibility preview, and one packaged fixture Pack. Loading never installs or executes code, contacts a provider, or activates/grants Pack operations.
5. Loopback APIs and frontend provide planning review, project knowledge, and Pack catalog surfaces using sanitized durable readback; no raw credential, shell, filesystem, merge, Pack activation, or model authority reaches the browser.
6. Focused backend/frontend/full Platform gates, typecheck, build, readiness, exact-head CI/Decision/State Gate, detached audit, schema-v2 attestation, expected-head merge, push State Gate, mainline validation, and integration receipt all pass.

## Execution policy

- No package installation or dependency version change is authorized. The only packaging mutation is inclusion of the fixture JSON already owned by this repository.
- No Spec Kit source is copied, no `specify` process is invoked, and no generated planning content is represented as repository execution authority.
- No embeddings or semantic model calls are used. Knowledge retrieval is deterministic metadata/text filtering over the mature LangGraph SQLite Store.
- Pack manifests request metadata and requirements only. They cannot grant capabilities, install dependencies, import code, execute commands, access credentials, or mutate policy.
- Generated gate evidence remains local and non-stageable. Preserve every unrelated worktree and runtime directory.
