# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260725_p0_minimal_integration_r1_authority_closure_rework_v5",
  "round_id": "round_20260725_p0_minimal_integration_r1_authority_closure_rework_v5",
  "based_on_state_build_id": "state_20260618_134029_d6bd033d2532",
  "based_on_state_digest": "d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5",
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
  "follows_last_decision_id": "decision_20260725_p0_minimal_integration_semantic_consistency_rework_v4",
  "follows_last_round_id": "round_20260725_p0_minimal_integration_semantic_consistency_rework_v4",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "failed_authority_acceptance_head": "e641c9b7eec70e31352dd309834f671350fea14f",
  "workstream_id": "p0-minimal-integration-r1-authority-closure-rework-v5",
  "source_issue": 32,
  "program_issue": 26,
  "source_work_item": 28,
  "source_pull_request": 27,
  "required_branch": "codex/p0-minimal-integration-baseline-v1",
  "starting_head": "e641c9b7eec70e31352dd309834f671350fea14f",
  "activation_base_sha": "38de9106d191d6b66d5f878354144817095e7bca",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "merge_allowed": false,
  "stop_after_exact_head_ci": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json"
  ],
  "bootstrap_exception_commands": [
    "gate.startup_snapshot",
    "status.git_status",
    "gate.command_plan",
    "gate.transition_lint",
    "gate.pre_execution"
  ],
  "allowed_commands": [
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"],
      "produced_artifacts": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "status.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "test.minimal_integration_contracts",
      "command": "python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin codex/p0-minimal-integration-baseline-v1",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "tests/test_minimal_integration_baseline_docs.py",
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "README.md",
    "pyproject.toml",
    "reverse_agent/architecture/contracts.py",
    "reverse_agent/workflows/development_graph.py",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    "docs/architecture/architecture-spine-v1.md",
    "docs/architecture/legacy-control-plane-boundary.md",
    "docs/architecture/control-plane-transition-kernel.md",
    "project_state/current_state.json",
    "project_state/state_manifest.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "reverse_agent/**",
    ".github/workflows/**",
    ".codex-skills/**",
    "docs/audits/**",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    "docs/architecture/architecture-spine-v1.md",
    "docs/architecture/legacy-control-plane-boundary.md",
    "docs/architecture/control-plane-transition-kernel.md",
    "docs/roadmap/architecture_spine_attestation_policy_seal_v1.md",
    "docs/roadmap/architecture_spine_authority_closure_rework_v1.md",
    "docs/roadmap/architecture_spine_evidence_runtime_closeout_v1.md",
    "docs/roadmap/architecture_spine_provenance_integration_final_rework_v1.md",
    "docs/roadmap/architecture_spine_trusted_execution_cutover_rework_v1.md",
    "docs/roadmap/architecture_transition_next_24h.md",
    "docs/roadmap/closeout_order_provenance_rework_plan.md",
    "docs/roadmap/evidence_centered_user_solve_execution_plan.md",
    "docs/roadmap/next_step_after_fast_close_round_key_fix_audit.md",
    "docs/roadmap/next_step_after_scoped_metadata_foundation.md",
    "docs/roadmap/project_state_domain_taxonomy_supplement.md",
    "docs/roadmap/reverse_agent_larger_step_plan.md",
    "docs/roadmap/reverse_agent_normal_pace_plan.md",
    "docs/roadmap/reverse_agent_unified_architecture_and_trust_roadmap.md",
    "docs/roadmap/trustworthy_hostile_binary_analysis_long_term_plan.md",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "tag",
    "release",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "workflow_dispatch",
    "automatic_merge",
    "mark_pr_ready_for_review",
    "branch_creation",
    "git_config_modification",
    "history_rewrite",
    "secret_access",
    "destructive_operations",
    "product_source_changes",
    "dependency_changes",
    "workflow_changes",
    "new_gate_implementation",
    "new_receipt_schema",
    "new_verifier_implementation",
    "langgraph_runtime_expansion",
    "agent_registry",
    "web_console",
    "spec_kit_installation",
    "open_swe_installation",
    "openhands_installation",
    "trust_layer_implementation",
    "binary_evidence_firewall_implementation",
    "hostile_binary_analysis_implementation"
  ],
  "capability_policy": {
    "git_push_from_local_executor": true,
    "branch_creation_from_local_executor": false,
    "pull_request_creation_from_local_executor": false,
    "merge_from_local_executor": false,
    "mark_pr_ready_for_review": false,
    "local_network_exceptions": [
      "git push origin codex/p0-minimal-integration-baseline-v1",
      "gh pr edit 27"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": ".github/workflows/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/**",
      "minimum_risk": "R1"
    }
  ],
  "scope_policy": {
    "scope": "planning_only",
    "allow_product_source": false,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_test_additions": true,
    "allow_documentation_changes": true,
    "allow_template_changes": true
  },
  "stop_conditions": [
    "transition_lint_failure",
    "preflight_not_authorized",
    "focused_tests_failure",
    "diff_check_failure",
    "ci_failure_on_exact_head",
    "scope_violation_detected",
    "independent_audit_rejects_head"
  ]
}
```

## DECISION_PACKET

### Goal

Close the remaining authority-model defects identified by the independent audit of v4 head `e641c9b7eec70e31352dd309834f671350fea14f`. This v5 round makes the ordinary R1 Work Item internally consistent, explicitly approved, and bound to an immutable authority snapshot without adding a new platform, Gate, receipt, or tracked artifact family.

### Current Evidence

- v4 exact head `e641c9b7eec70e31352dd309834f671350fea14f` passed CI, Decision Preflight, and State Gate.
- Independent audit Issue #32 returned `REWORK_REQUIRED` because:
  1. the mandatory R2/R3 checkbox revokes the narrow R1 publication exception;
  2. `AGENTS.md` recommends rebase although Path A forbids history rewriting;
  3. an approved mutable Issue body has no approval mechanism or immutable revision identity;
  4. tests do not detect those authority defects;
  5. the reuse-inventory parser skips tables and accepts illegal disposition tokens.
- v4 is immutable and stopped after exact-head CI; no repair may append under v4 authority.

### Do Not Do

- Do not modify `reverse_agent/**`, workflows, dependencies, legacy roadmaps, containment, or the reuse inventory.
- Do not create a new Gate, receipt, verifier, schema family, database, or tracked per-run artifact family.
- Do not merge, mark ready, force push, rebase, squash, tag, release, or push directly to `main`.
- Do not start LangGraph runtime, Agent Registry, Web console, Spec Kit, Open SWE, OpenHands, Trust Layer, or binary-domain work.

### Implementation Scope

1. Replace this Decision as the v5 activation authority before implementation.
2. Fix the R1 boundary checkbox so only network/publication outside the narrow named-branch/Draft-PR exception requires Path B.
3. Remove every Path-A instruction to rebase or rewrite history. On base mismatch, stop and create a fresh branch only after a revised and reapproved Work Item.
4. Define the minimal Work Item lifecycle:
   - template-created Issue = `CANDIDATE`;
   - repository owner/maintainer applies the explicit `r1-approved` label after review;
   - executor records repository, Issue number, approver identity, approval event/time, normalized Issue-body SHA-256 digest, and `immutable_observation_ref` in the Draft PR body;
   - the authority identity is `{repository}#{issue_number}@{immutable_observation_ref}`;
   - a material Issue-body edit changes the digest, invalidates the snapshot, and requires reapproval;
   - comments remain non-authoritative.
5. Strengthen `tests/test_minimal_integration_baseline_docs.py` to fail on each authority regression and to parse every Markdown table containing a `Disposition` column. Every data row must contain exactly one legal disposition and zero illegal tokens.
6. Update PR #27 description to the final v5 exact head and validation truth.

### Required Audit

- Generate the v5 Command Plan from this Decision.
- Require transition lint success and `PRE_EXECUTION_AUTHORIZED` before content changes.
- Run the focused test suite and `git diff --check`.
- Require CI, Decision Preflight, and State Gate success on one immutable exact head.
- Keep PR #27 Draft and unmerged.

### Completion

This round is complete when all Issue #32 findings are fixed, the strengthened focused suite passes, `git diff --check` passes, all three remote checks are green on one immutable exact head, the PR description is current, and independent audit accepts the head. Merge is not part of this round.
