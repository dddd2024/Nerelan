# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260725_p0_minimal_integration_semantic_consistency_rework_v4",
  "round_id": "round_20260725_p0_minimal_integration_semantic_consistency_rework_v4",
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
  "follows_last_decision_id": "decision_20260725_p0_minimal_integration_acceptance_rework_v3",
  "follows_last_round_id": "round_20260725_p0_minimal_integration_acceptance_rework_v3",
  "previous_audit_outcome": "REWORK_REQUIRED",
  "failed_semantic_acceptance_head": "284ec2244ba08c0bf496d09d0110441b34860d4b",
  "workstream_id": "p0-minimal-integration-semantic-consistency-rework-v4",
  "source_issue": 31,
  "program_issue": 26,
  "source_work_item": 28,
  "source_pull_request": 27,
  "required_branch": "codex/p0-minimal-integration-baseline-v1",
  "starting_head": "284ec2244ba08c0bf496d09d0110441b34860d4b",
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

Rework the minimal AI development integration baseline to fix the six semantic consistency failures (F1-F6) identified by the independent audit of v3 head `284ec2244ba08c0bf496d09d0110441b34860d4b`. The v3 round produced non-empty deliverables and passed exact-head CI, but semantic acceptance failed because the documents contradicted the lightweight R1 authority model they were supposed to define. This v4 rework freezes `284ec224` as "remote checks passed, semantic acceptance failed" historical evidence and produces a corrected, semantically tested final head on the same PR #27 branch.

### Current Evidence

- The v3 Decision (`decision_20260725_p0_minimal_integration_acceptance_rework_v3`) authorized six documentation deliverables plus a baseline docs test on branch `codex/p0-minimal-integration-baseline-v1`.
- The v3 implementation head `284ec2244ba08c0bf496d09d0110441b34860d4b` passed all four remote checks (baseline, decision-preflight, state-gate x2).
- Independent audit (Issue #31) returned `REWORK_REQUIRED` with six findings:
  1. **F1**: The ordinary R1 authority model is still directly contradicted. The roadmap and matrix first state execution authority lives in Decision + Command Plan, then later say ordinary R0/R1 no longer uses those files.
  2. **F2**: The risk taxonomy classifies the same operation as both R1 and R2. Branch push / Draft PR creation are network/publication operations but are classified as R1 while R2 includes all network/publication.
  3. **F3**: `AGENTS.md` hard-codes a stale `main` SHA (`38de9106...`) into the permanent operating guide. After PR #27 merges, ordinary R1 must use the current `origin/main`, not require a new Decision because `main` advanced.
  4. **F4**: The required one-time transition-evidence exception is still missing. `SOURCE_OF_TRUTH_MATRIX.md` says runtime logs and per-run artifacts are "never tracked source state" while PR #27 tracks compiler-required transition artifacts.
  5. **F5**: Containment and precedence wording remains ambiguous. `LEGACY_GOVERNANCE_CONTAINMENT.md` lists `decision_packet.md` as "active round authority" without qualifying as transition/R2-R3 only.
  6. **F6**: The document-contract test does not verify semantic consistency. The tests are keyword-presence checks that allow the contradictions above to pass.
- The v3 Decision is immutable and sets `stop_after_exact_head_ci=true`; no corrective commit may append under v3 authority.
- `main` remains at `38de9106d191d6b66d5f878354144817095e7bca`.

### Do Not Do

- Do not modify product source under `reverse_agent/**`.
- Do not modify workflows under `.github/workflows/**`.
- Do not modify `.codex-skills/**`.
- Do not modify `docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md` (read-only this round unless the strengthened parser proves a concrete row defect).
- Do not modify any legacy roadmap or architecture spec.
- Do not modify dependencies (`pyproject.toml`, `pytest.ini`, `setup.cfg`).
- Do not modify any existing test file other than `tests/test_minimal_integration_baseline_docs.py`.
- Do not merge, mark PR ready, force push, rebase, squash, tag, or release.
- Do not create a new branch, new PR, new Gate, new receipt schema, or new verifier.
- Do not expand into LangGraph runtime, Agent Registry, Web console, Spec Kit, Open SWE, OpenHands, Trust Layer, or binary directions.
- Do not invoke model APIs, external reverse tools, unknown binaries, or runner dispatch.

### Files To Inspect

- `README.md` (reference)
- `pyproject.toml` (reference)
- `reverse_agent/architecture/contracts.py` (reference)
- `reverse_agent/workflows/development_graph.py` (reference)
- `docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md` (reference, read-only)
- `docs/architecture/architecture-spine-v1.md` (reference)
- `docs/architecture/legacy-control-plane-boundary.md` (reference)
- `docs/architecture/control-plane-transition-kernel.md` (reference)
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

1. **Replace `project_state/decision_packet.md`** with this v4 Decision (bootstrap exception).
2. **Fix F1 — R1 authority model contradiction** across `AGENTS.md`, `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`, `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`, and `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md`. Remove unconditional statements that all execution authority lives in Decision + Command Plan. Define two explicit authority paths:
   - ordinary R0/R1 path: authority = approved Work Item Issue body + exact scope + checks;
   - transition / R2-R3 path: authority = bounded Decision + generated Command Plan.
   Distinguish the Issue body used as the Work Item from comments attached to an Issue or PR (which are never authority).
3. **Fix F2 — Risk taxonomy publication contradiction** across `AGENTS.md`, the roadmap, and `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml`. Define:
   - R1 publication = bounded push to the exact named non-main branch + create/update the exact Draft PR + no merge / no mark-ready / no history rewrite;
   - R2 publication/network = direct main push, merge, mark-ready, workflow/dependency publication, release/tag, unbounded network access, cross-repository publication, credentials/secrets, or any operation outside the Work Item binding.
   Update the risk-justification prompt so a valid R1 task can truthfully declare the narrow branch/Draft-PR exception.
4. **Fix F3 — Hard-coded permanent main SHA** in `AGENTS.md` and `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml`. Replace the permanent `38de9106...` requirement with Work-Item-bound current base: fetch/observe current `origin/main` SHA; require Work Item `base_sha` to equal the approved current base; fail if branch merge-base differs. Use a generic placeholder such as `<current origin/main SHA>`. The historical `38de9106...` value remains valid only for the current transition round.
5. **Fix F4 — One-time transition-evidence exception** in `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`. Explicitly identify the current transition Decision's tracked bootstrap/command-plan/preflight files as a one-time compatibility exception. State they are not the normal R0/R1 model. Prohibit creation of any new tracked per-run artifact family.
6. **Fix F5 — Containment and precedence ambiguity** in `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md` and `AGENTS.md`. Qualify the `decision_packet.md` / `command_plan.json` authority labels as transition/R2-R3 only. Define two explicit authority paths rather than one global list.
7. **Fix F6 — Strengthen semantic contract tests** in `tests/test_minimal_integration_baseline_docs.py`. Replace keyword-presence assertions with exact invariant tests and structured parsing. The test must fail on each F1-F5 regression:
   - no unconditional statement that all execution authority lives in Decision + Command Plan;
   - Work Item Issue body is authoritative for R0/R1, while Issue/PR comments are not;
   - R1 branch/Draft-PR publication is a narrow exception and R2 publication is precisely bounded;
   - risk-justification prompt does not deny the narrow R1 network/publication exception;
   - permanent guidance does not hard-code the current transition base SHA;
   - one-time tracked transition-evidence exception is explicit;
   - containment authority labels are qualified as transition/R2-R3 only;
   - every reuse-inventory data row has exactly one disposition from `KEEP / ADAPT / DEFER / ARCHIVE_CANDIDATE`;
   - a contradictory fixture or temporary mutated text fails each invariant.
8. **Update the PR #27 description** via `gh pr edit 27` to reference the v4 Decision, the v3 failed semantic-acceptance head, and the rework scope.

### Tests

Focused tests (authorized in `allowed_commands`):

```bash
python -m pytest tests/test_architecture_contracts.py tests/test_planning_and_github_adapters.py tests/test_risk_classifier.py tests/test_minimal_integration_baseline_docs.py -q
git diff --check
```

The strengthened `tests/test_minimal_integration_baseline_docs.py` must fail before the content fixes are applied (TDD red), then pass after the fixes (TDD green).

### Stop Conditions

- `transition-lint` returns FAILURE.
- `transition-preflight --mode pre` does not return `PRE_EXECUTION_AUTHORIZED`.
- Any focused test fails for a reason inside the current round scope.
- `git diff --check` reports whitespace or conflict markers.
- Any remote GitHub Actions check is not green on the exact head.
- Any scope violation is detected (product source, workflow, dependency, legacy roadmap, reuse inventory, or forbidden operation).
- Independent audit rejects the final head.

When `stop_after_exact_head_ci` is satisfied (all remote checks green on the immutable exact head), the round is stopped. Merge remains separately authorized and human-controlled.

### Completion

This round is complete when:

- the v4 Decision is committed and the gate sequence returns `PRE_EXECUTION_AUTHORIZED`;
- all six semantic findings (F1-F6) are fixed;
- the strengthened `tests/test_minimal_integration_baseline_docs.py` passes;
- the focused test suite passes;
- `git diff --check` passes;
- a new immutable exact head is pushed to `origin/codex/p0-minimal-integration-baseline-v1`;
- all three remote GitHub Actions are green on the exact head;
- the PR #27 description is updated;
- PR #27 remains Draft.

Merge is not part of this round.
