# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260725_p0_minimal_integration_acceptance_rework_v3",
  "round_id": "round_20260725_p0_minimal_integration_acceptance_rework_v3",
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
  "follows_last_decision_id": "decision_20260724_p0_minimal_integration_and_legacy_containment_rework_v2",
  "follows_last_round_id": "round_20260724_p0_minimal_integration_and_legacy_containment_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "failed_acceptance_head": "657b119cc52e30f0e76ee8ecee4878569425c114",
  "workstream_id": "p0-minimal-integration-acceptance-rework-v3",
  "source_issue": 30,
  "program_issue": 26,
  "source_pull_request": 27,
  "required_branch": "codex/p0-minimal-integration-baseline-v1",
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
      "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"],
      "produced_artifacts": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
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
      "allowed_mutated_paths": ["project_state/gates/transition_preflight_result.json", "project_state/gates/bootstrap_state.json"],
      "produced_artifacts": ["project_state/gates/transition_preflight_result.json", "project_state/gates/bootstrap_state.json"]
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
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
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

Rework the minimal AI development integration baseline to fix the six content acceptance failures identified by the independent audit of head `657b119cc52e30f0e76ee8ecee4878569425c114`. The v2 round produced six documentation deliverables and passed exact-head CI, but content acceptance failed because the deliverables were inconsistent, incomplete, or untested. This v3 rework freezes `657b119` as historical evidence ("remote checks passed, content acceptance failed") and produces a corrected, tested final head on the same PR #27 branch.

### Current Evidence

- The v2 Decision (`decision_20260724_p0_minimal_integration_and_legacy_containment_rework_v2`) authorized six documentation deliverables on branch `codex/p0-minimal-integration-baseline-v1`.
- The v2 implementation head `657b119cc52e30f0e76ee8ecee4878569425c114` passed all four remote checks (baseline, decision-preflight, state-gate x2).
- Independent audit returned `REWORK_REQUIRED` with six findings:
  1. root `AGENTS.md` is the zero-byte Git object (`e69de29...`), so the mandatory operating guide does not exist in usable form;
  2. the roadmap says normal R0/R1 no longer needs full Decision/Command Plan, but the source-of-truth matrix, containment guide, and R1 Issue template still declare those files as ordinary execution authority;
  3. routine feature-branch/Draft-PR publication is not consistently classified, so the proposed lightweight R1 path is not executable without ambiguity;
  4. the reuse inventory permits only `KEEP / ADAPT / DEFER / ARCHIVE_CANDIDATE` but contains `NO_NEW_FEATURES` as a disposition;
  5. the selected focused tests did not detect the empty mandatory deliverable;
  6. the PR description remains stale at the original activation head and v1 Decision.
- The v2 Decision is immutable and sets `stop_after_exact_head_ci=true`; no corrective commit may append under v2 authority.
- `main` remains at `38de9106d191d6b66d5f878354144817095e7bca`.

### Do Not Do

- Do not modify product source under `reverse_agent/**`.
- Do not modify workflows under `.github/workflows/**`.
- Do not modify `.codex-skills/**`.
- Do not modify any legacy roadmap or architecture spec under `docs/roadmap/**` (except the single active roadmap) or `docs/architecture/architecture-spine-v1.md`, `docs/architecture/legacy-control-plane-boundary.md`, `docs/architecture/control-plane-transition-kernel.md`.
- Do not modify dependencies (`pyproject.toml`, `pytest.ini`, `setup.cfg`).
- Do not modify any existing test file other than creating `tests/test_minimal_integration_baseline_docs.py`.
- Do not merge, mark PR ready, force push, rebase, squash, tag, or release.
- Do not create a new branch, new PR, new Gate, new receipt schema, or new verifier.
- Do not expand into LangGraph runtime, Agent Registry, Web console, Spec Kit, Open SWE, OpenHands, Trust Layer, or binary directions.
- Do not invoke model APIs, external reverse tools, unknown binaries, or runner dispatch.

### Files To Inspect

- `README.md` (reference)
- `pyproject.toml` (reference)
- `reverse_agent/architecture/contracts.py` (reference)
- `reverse_agent/workflows/development_graph.py` (reference)
- `project_state/current_state.json` (reference)
- `project_state/state_manifest.json` (reference)

### Required Audit

- Preserve the full local `transition-lint` stdout/stderr.
- Preserve the full local `transition-preflight --mode pre` stdout/stderr.
- Confirm `PRE_EXECUTION_AUTHORIZED` before any implementation.
- Confirm focused tests pass and `git diff --check` passes before push.
- Confirm all three remote GitHub Actions are green on the exact head before declaring the round stopped.
- PR #27 remains Draft; do not merge or mark ready.

### Implementation Scope

1. **Replace `project_state/decision_packet.md`** with this v3 Decision (bootstrap exception).
2. **Rewrite `AGENTS.md`** with full, non-empty content (fix audit finding 1). The guide must state: repository purpose, non-goals, startup checks, source-of-truth order, R0/R1 allowed operations, R2/R3 approval boundary, feature-branch push and Draft-PR creation as R1 operations, test commands, branch/PR rules, prohibited actions, stop conditions.
3. **Unify the R0/R1 authority model** across `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`, `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`, `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md`, and `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml` (fix audit finding 2). All four documents must agree that, after the transition round, ordinary R0/R1 work does not require a full Decision/Command Plan, while R2/R3 operations remain fail-closed and require a bounded Decision. `decision_packet.md` and `command_plan.json` are authority for transition rounds and R2/R3, not ordinary R0/R1.
4. **Classify feature-branch push and Draft-PR creation as R1 operations** in `AGENTS.md`, the roadmap, the source-of-truth matrix, and the R1 Issue template (fix audit finding 3). Direct `main` push, merge, force push, rebase, squash, tag, and release remain R2+ or forbidden.
5. **Fix the `NO_NEW_FEATURES` disposition** in `docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md` (fix audit finding 4). The reuse inventory must use only `KEEP`, `ADAPT`, `DEFER`, or `ARCHIVE_CANDIDATE`. `NO_NEW_FEATURES` is a containment-tier label, not a reuse disposition; the affected row must be changed to one of the four legal reuse values.
6. **Create `tests/test_minimal_integration_baseline_docs.py`** (fix audit finding 5). The test must verify: (a) all six deliverable files are non-empty; (b) necessary sections exist in each; (c) R1 authority semantics are consistent across the documents; (d) reuse dispositions are limited to `KEEP / ADAPT / DEFER / ARCHIVE_CANDIDATE`.
7. **Update the PR #27 description** via `gh pr edit 27` to reference the v3 Decision, the v2 failed acceptance head, and the rework scope (fix audit finding 6).

### Tests

Focused tests (authorized in `allowed_commands`):

```bash
python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q
git diff --check
```

The new `tests/test_minimal_integration_baseline_docs.py` must fail before the content fixes are applied (TDD red), then pass after the fixes (TDD green).

### Stop Conditions

- `transition-lint` returns FAILURE.
- `transition-preflight --mode pre` does not return `PRE_EXECUTION_AUTHORIZED`.
- Any focused test fails for a reason inside the current round scope.
- `git diff --check` reports whitespace or conflict markers.
- Any remote GitHub Actions check is not green on the exact head.
- Any scope violation is detected (product source, workflow, dependency, legacy roadmap, or forbidden operation).
- Independent audit rejects the final head.

When `stop_after_exact_head_ci` is satisfied (all remote checks green on the immutable exact head), the round is stopped. Merge remains separately authorized and human-controlled.

### Completion

This round is complete when:

- the v3 Decision is committed and the gate sequence returns `PRE_EXECUTION_AUTHORIZED`;
- all six content findings are fixed;
- `tests/test_minimal_integration_baseline_docs.py` passes;
- the focused test suite passes;
- `git diff --check` passes;
- a new immutable exact head is pushed to `origin/codex/p0-minimal-integration-baseline-v1`;
- all three remote GitHub Actions are green on the exact head;
- the PR #27 description is updated;
- PR #27 remains Draft.

Merge is not part of this round.
