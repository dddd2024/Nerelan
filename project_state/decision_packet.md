# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260726_governance_migration_owner_manual_merge_rework_v3","round_id":"round_20260726_governance_migration_owner_manual_merge_rework_v3","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260726_governance_migration_owner_manual_merge_rework_v2",
  "follows_last_round_id": "round_20260726_governance_migration_owner_manual_merge_rework_v2",
  "previous_audit_outcome": "REWORK_REQUIRED_V2_HEAD_3b11954c_REJECTED_F5_F6",
  "workstream_id": "governance-migration-owner-manual-merge-rework-v3",
  "source_issue": 43,
  "program_issue": 26,
  "required_branch": "codex/governance-migration-owner-manual-merge-v1",
  "starting_head": "3b11954c64d2edde0b6baf9697ddbaa0f231c35c",
  "activation_base_sha": "964cd647afc3d51a7fdf855080351da53c5e79ef",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "stop_after_exact_head_ci": true,
  "one_time_governance_migration_rework_v3": true,
  "bootstrap_exception_files": ["project_state/decision_packet.md", "project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot", "status.git_status", "gate.command_plan", "gate.transition_lint", "gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"test.minimal_integration_baseline_docs","command":"python -m pytest tests/test_minimal_integration_baseline_docs.py -q","phase":"test","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["regression_test"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"validation.diff_check","command":"git diff --check","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push origin codex/governance-migration-owner-manual-merge-v1","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.update_pr_body","command":"gh pr edit 44 --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_edit","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
  ],
  "allowed_mutated_paths": [
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
    "docs/run_closeout.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "tests/test_project_gate.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md"
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
    "docs/run_closeout.md",
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    "tests/test_project_gate.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifactindex.json"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "merge",
    "mark_ready_for_review",
    "tag or release",
    "cross-repository publication",
    "unbounded network access",
    "credentials or secrets access",
    "unknown-binary execution",
    "model API invocation from repository code",
    "external reverse-tool invocation",
    "runner dispatch",
    "workflow dispatch",
    "automatic merge",
    "GitHub auto-merge",
    "agent-initiated merge or mark-ready",
    "automation-initiated merge or mark-ready",
    "workflow-initiated merge or mark-ready",
    "scheduled or delegated merge or mark-ready",
    "external-service-initiated merge or mark-ready",
    "history rewrite",
    "product source changes outside allowed paths",
    "dependency changes",
    "workflow changes",
    "Gate runtime changes",
    "LangGraph runtime changes",
    "new Gate implementation",
    "new receipt schema",
    "new verifier implementation",
    "modifying docs/run_closeout.md",
    "modifying .codex-skills/**",
    "modifying AGENTS.md",
    "modifying docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "modifying docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "modifying docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
    "R2/R3 PR using the new lightweight merge path",
    "creating new PR (must update PR #44 only)",
    "applying fixes before PRE_EXECUTION_AUTHORIZED"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "git push origin codex/governance-migration-owner-manual-merge-v1",
      "gh pr edit 44 --body-file"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    "tests/test_minimal_integration_baseline_docs.py",
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "AGENTS.md", "minimum_risk": "R2"},
    {"pattern": "docs/architecture/**", "minimum_risk": "R2"},
    {"pattern": "docs/roadmap/**", "minimum_risk": "R2"},
    {"pattern": ".github/ISSUE_TEMPLATE/**", "minimum_risk": "R2"},
    {"pattern": "tests/**", "minimum_risk": "R1"},
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ],
  "scope_policy": {
    "scope": "governance_migration_owner_manual_merge_rework_v3",
    "one_time_r2_governance_migration_rework_v3": true,
    "rework_deliverable_files": [
      ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
      "tests/test_minimal_integration_baseline_docs.py"
    ],
    "transition_evidence_files": [
      "project_state/decision_packet.md",
      "project_state/gates/command_plan.json",
      "project_state/gates/startup_snapshot.json",
      "project_state/gates/bootstrap_state.json",
      "project_state/gates/transition_command_plan_preview.json",
      "project_state/gates/transition_preflight_result.json"
    ],
    "rework_deliverable_files_count": 2,
    "transition_evidence_files_count": 6,
    "counting_rule": "Two rework deliverable files and Decision/Gate transition evidence files are counted separately. PR #44 body metadata is updated via gh pr edit (no repo file).",
    "preserve_accepted_semantics": ["AGENTS.md", "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md", "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md", "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md"],
    "allow_product_source": false,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_gate_runtime_changes": false,
    "allow_test_additions": true,
    "allow_template_changes": true,
    "allow_documentation_changes": false,
    "allow_run_closeout_changes": false,
    "allow_agents_md_changes": false,
    "allow_roadmap_changes": false,
    "allow_source_matrix_changes": false,
    "allow_containment_changes": false
  },
  "rework_semantics": {
    "fixes_audit_findings": ["F5", "F6"],
    "F5_scope_risk_tier_justification_placeholder_to_agent_implementation_stage": true,
    "F6_add_risk_tier_justification_block_test_and_clause_local_only_qualifier_tests": true,
    "clause_local_rule": "Stage qualifier must appear in the same sentence or immediately associated clause as each 'only' rule, not merely somewhere in the section.",
    "pr_body_records": "Path-B Decision snapshot (NOT R1 Work Item snapshot)",
    "pr_body_must_record_after_rework": ["exact_head_sha", "two rework deliverables", "one owner-authored Decision file", "five compiler-owned Gate outputs", "8 changed files total in v3 delta (cumulative PR still 12)"],
    "audit_comments_are_evidence_not_authority": true,
    "v2_head_3b11954c_frozen_as_failed_semantic_acceptance_evidence": true,
    "migration_pr_self_merge_rule": "This migration PR's own final merge must follow current old rules until the new rule reaches main. Either this Decision is amended to explicitly authorize the final exact-head merge, or a separate bounded Path-B merge authorization is required."
  },
  "stop_conditions": [
    "transition_lint_failure",
    "preflight_not_authorized",
    "focused_tests_failure",
    "diff_check_failure",
    "ci_failure_on_exact_head",
    "scope_violation_detected",
    "independent_audit_rejects_head",
    "files_changed_outside_two_rework_files_plus_transition_evidence",
    "attempted_merge_or_mark_ready_without_separate_authorization",
    "fixes_applied_before_PRE_EXECUTION_AUTHORIZED",
    "modified_agents_md_or_roadmap_or_source_matrix_or_containment"
  ]
}
```

## DECISION_PACKET

### Goal

One-time R2 governance migration rework (v3) addressing the two blocking findings (F5, F6) from the independent re-audit of PR #44 exact head `3b11954c64d2edde0b6baf9697ddbaa0f231c35c`. The v2 head is frozen as failed semantic acceptance evidence; no corrective implementation commit may be appended under v2.

This v3 Decision authorizes minimal corrections to two deliverable files only. It does NOT authorize merging the migration PR itself; that requires either a follow-up amendment or a separate bounded Path-B merge authorization.

### Audit findings addressed

- **F5** — `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml` under `risk_tier_justification` placeholder still guides users to write "The only network/publication operations are push to the exact approved non-main branch and create/update of the exact Draft PR." — not scoped to Agent implementation before independent exact-head acceptance. Scope this placeholder explicitly to the Agent-implementation stage.
- **F6** — `tests/test_minimal_integration_baseline_docs.py` F3 regression coverage does not inspect the `risk_tier_justification` block, so F5 passes all 87 tests. Also, the AGENTS/roadmap stage-qualification test accepts a qualifier anywhere in the whole publication section, allowing an unqualified `Path A permits only:` sentence to be reintroduced while an unrelated qualifier remains elsewhere. Add deterministic checks that: (1) extract and validate the `risk_tier_justification` block; (2) reject any unqualified `only network/publication` guidance in the template; (3) require the stage qualifier in the same sentence or immediately associated clause as each `only` rule, rather than merely somewhere in the section.

### Implementation Scope

1. Modify exactly the two rework deliverable files:
   - `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml` — F5 fix: scope the `risk_tier_justification` placeholder to "During Agent implementation, before independent exact-head acceptance, the Agent's only network/publication operations are...".
   - `tests/test_minimal_integration_baseline_docs.py` — F6 fix: add a `risk_tier_justification` block extraction and validation test; add clause-local `only`-qualifier tests for AGENTS.md and roadmap (stage qualifier must be in the same sentence or immediately associated clause as each `only` rule).

2. Do NOT modify `AGENTS.md`, `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`, `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`, or `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md` — preserve v2-accepted semantics.

3. Do NOT modify: Gate runtime, LangGraph runtime, workflows, dependencies, `docs/run_closeout.md`, `.codex-skills/**`, product source, or any test file other than `tests/test_minimal_integration_baseline_docs.py`.

4. Do NOT create a new PR. Update PR #44 body only (via `gh pr edit 44`).

5. Generate and validate v3 Command Plan / preflight evidence. Require CI, Decision Preflight, and State Gate success on one new exact head.

6. Update PR #44 body with the new exact head. Keep the PR Draft until independent audit accepts the new exact head.

### Authority and evidence boundary

- This is a Path-B (R2) Decision. Authority is this approved Decision + generated command_plan.json + PRE_EXECUTION_AUTHORIZED.
- Audit comments on PR #44 are evidence, not execution authority. They inform the Decision shape but do not authorize commands, file changes, closeout, or merge.
- The v2 head `3b11954c64d2edde0b6baf9697ddbaa0f231c35c` is frozen as failed semantic acceptance evidence. No corrective commit may be appended under v2.

### Completion

Completion requires:
- `python -m pytest tests/test_minimal_integration_baseline_docs.py -q` passes;
- `git diff --check` passes;
- exactly the two rework deliverable files are modified (transition evidence files are separate);
- F5/F6 corrections verifiable in the diff;
- PR #44 body updated with new exact head (F4 carryover);
- CI passes on the new exact head;
- STOP for independent re-audit.

Merge is NOT part of this round. The migration PR's own final merge requires either a follow-up amendment to this Decision or a separate bounded Path-B merge authorization.

### Stop Conditions

Stop immediately when:
- transition-lint fails;
- transition-preflight does not return PRE_EXECUTION_AUTHORIZED;
- focused tests fail;
- `git diff --check` fails;
- CI fails on exact head;
- scope violation detected (files changed outside the two rework files plus transition evidence);
- `AGENTS.md`, `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`, `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`, or `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md` is modified;
- independent audit rejects the head;
- any attempt to merge or mark-ready without separate authorization;
- fixes applied before PRE_EXECUTION_AUTHORIZED.
