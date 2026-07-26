# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260725_governance_migration_owner_manual_merge_v1","round_id":"round_20260725_governance_migration_owner_manual_merge_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260725_p0_minimal_integration_ci_contract_compatible_enforcement_v9",
  "follows_last_round_id": "round_20260725_p0_minimal_integration_ci_contract_compatible_enforcement_v9",
  "previous_audit_outcome": "V9_DECISION_APPROVED_PREDECESSOR",
  "workstream_id": "governance-migration-owner-manual-merge-v1",
  "source_issue": 43,
  "program_issue": 26,
  "required_branch": "codex/governance-migration-owner-manual-merge-v1",
  "starting_head": "964cd647afc3d51a7fdf855080351da53c5e79ef",
  "activation_base_sha": "964cd647afc3d51a7fdf855080351da53c5e79ef",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "stop_after_exact_head_ci": true,
  "one_time_governance_migration": true,
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
    {"command_id":"publication.create_draft_pr","command":"gh pr create --base main --head codex/governance-migration-owner-manual-merge-v1 --draft --title governance-r1-owner-manual-merge-carve-out-one-time-r2-migration --body-file PR_BODY_TEMP_PATH","phase":"publication","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_creation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
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
    "docs/run_closeout.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "tests/test_project_gate.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py"
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
    "R2/R3 PR using the new lightweight merge path",
    "applying six-file patch before PRE_EXECUTION_AUTHORIZED"
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
      "gh pr create --base main --head codex/governance-migration-owner-manual-merge-v1 --draft"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
    "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
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
    "scope": "governance_migration_owner_manual_merge",
    "one_time_r2_governance_migration": true,
    "six_governance_files": [
      "AGENTS.md",
      "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
      "docs/architecture/SOURCE_OF_TRUTH_MATRIX.md",
      "docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md",
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
    "six_governance_files_count": 6,
    "transition_evidence_files_count": 6,
    "counting_rule": "Six governance migration files and Decision/Gate transition evidence files are counted separately. The migration deliverable is exactly six files; transition evidence is generated by the gate sequence and is not part of the deliverable.",
    "allow_product_source": false,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_gate_runtime_changes": false,
    "allow_test_additions": true,
    "allow_documentation_changes": true,
    "allow_template_changes": true,
    "allow_run_closeout_changes": false
  },
  "migration_semantics": {
    "introduces_owner_manual_merge_carve_out": true,
    "carve_out_covers_both_mark_ready_and_merge": true,
    "actor_distinction": "human-initiated vs agent-initiated vs automation-initiated",
    "agent_and_automation_merge_remains_path_b": true,
    "auto_merge_remains_forbidden": true,
    "r2_r3_prs_excluded_from_carve_out": true,
    "does_not_modify": ["Gate runtime", "LangGraph runtime", "workflows", "dependencies", "docs/run_closeout.md", ".codex-skills/**"],
    "pr_body_records": "Path-B Decision snapshot (NOT R1 Work Item snapshot)",
    "pr_body_snapshot_fields": ["decision_id", "round_id", "status", "authorized_risk_tier", "activation_base_sha", "required_branch", "six_governance_files", "forbidden_operations", "one_time_governance_migration", "merge_allowed=false", "migration_pr_self_merge_rule"],
    "saved_six_file_patch_status": "UNAUTHORIZED_PROPOSAL_ONLY. The previously saved patch at f:\\reverse-agent-governance-migration-v1.patch is not execution authority. It may only be re-applied after transition-preflight returns PRE_EXECUTION_AUTHORIZED, and must be re-reviewed after application.",
    "audit_comments_are_evidence_not_authority": true,
    "migration_pr_self_merge_rule": "This migration PR's own final merge must follow current old rules until the new rule reaches main. Either this Decision is amended to explicitly authorize the final exact-head merge, or a separate bounded Path-B merge authorization is required. The new lightweight rule cannot be used to merge itself."
  },
  "main_anomaly_note": "origin/main moved from 4abf7fc90e05253452e4199f2a65401be782422d to 964cd647afc3d51a7fdf855080351da53c5e79ef due to two accidental empty-file creations (__invalid__, __invalid2__) and their reverts. Net tree diff is empty. No force-push to revert main is permitted. activation_base_sha is set to the new 964cd647.",
  "stop_conditions": [
    "transition_lint_failure",
    "preflight_not_authorized",
    "focused_tests_failure",
    "diff_check_failure",
    "ci_failure_on_exact_head",
    "scope_violation_detected",
    "independent_audit_rejects_head",
    "files_changed_outside_six_allowed_paths_plus_transition_evidence",
    "attempted_merge_or_mark_ready_without_separate_authorization",
    "six_file_patch_applied_before_PRE_EXECUTION_AUTHORIZED"
  ]
}
```

## DECISION_PACKET

### Goal

One-time R2 governance migration authorizing the introduction of a narrow owner-manual-merge carve-out for ordinary R1 PRs. After this migration reaches `main`, an accepted ordinary R1 PR may be merged by a repository owner/maintainer acting personally (human-initiated) without a separate Path-B Decision, subject to all R1 final-acceptance conditions holding immediately before the merge.

This carve-out covers BOTH owner-performed `mark-ready` AND `merge` as a single human-initiated sequence. Agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, and external-service-initiated merge/mark-ready, GitHub auto-merge, and merge/mark-ready of R2/R3 work items remain Path-B.

This Decision authorizes ONLY the six-file rule migration. It does NOT authorize merging the migration PR itself; that requires either a follow-up amendment to this Decision or a separate bounded Path-B merge authorization (Phase 4). The new lightweight rule cannot be used to merge itself.

### Authority and evidence boundary

- This is a Path-B (R2) Decision. Authority is this approved Decision + generated command_plan.json + PRE_EXECUTION_AUTHORIZED.
- Audit comments on Issue #43 are evidence, not execution authority. They inform the Decision shape but do not authorize commands, file changes, closeout, or merge.
- The previously saved six-file patch at `f:\reverse-agent-governance-migration-v1.patch` is an unauthorized proposal only. It is NOT execution authority. It may only be re-applied after transition-preflight returns PRE_EXECUTION_AUTHORIZED, and must be re-reviewed after application.
- The PR body for this migration PR records a Path-B Decision snapshot (NOT an R1 Work Item snapshot), using the fields listed in `migration_semantics.pr_body_snapshot_fields`.

### Implementation Scope

1. Modify exactly the six governance migration files to introduce the R1 final-acceptance owner-manual-merge carve-out:
   - `AGENTS.md` — add "R1 final acceptance — owner manual merge carve-out" subsection; narrow R2 publication scope to Agent/automation merge; clarify prohibited actions.
   - `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md` — update narrow R1 publication and after-acceptance sections to include the carve-out.
   - `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md` — update publication boundary to clarify owner-manual-merge conditions.
   - `docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md` — align rule 8 with the carve-out conditions.
   - `.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml` — distinguish actor control in forbidden_operations; add carve-out acknowledgment checkboxes.
   - `tests/test_minimal_integration_baseline_docs.py` — add semantic tests validating the carve-out and ensuring Agent/automation merge remains Path-B.

2. The carve-out conditions that must ALL hold immediately before owner manual mark-ready + merge:
   - approved immutable R1 Work Item snapshot in PR body with `body_digest_sha256` matching current normalized Issue body;
   - `r1-approved` label applied by owner/maintainer, no material Issue-body edit since;
   - PR from fresh branch with merge-base == snapshot `base_sha`;
   - allowed-path compliance (PR diff touches only approved paths);
   - deterministic local checks passed on exact head (`pytest`, `git diff --check`);
   - required exact-head GitHub Actions checks == SUCCESS;
   - independent exact-head audit accepted and recorded as PR comment identifying accepted head SHA;
   - no unresolved blocking review threads;
   - owner/maintainer immediate re-observation immediately before merge:
     - `origin/main` == snapshot `base_sha` (no main drift);
     - PR `headRefOid` == accepted audit head (no head movement);
     - PR `baseRefOid` == snapshot `base_sha`;
     - PR `mergeable` == MERGEABLE;
     - PR `mergeStateStatus` == CLEAN;
     - PR CI on exact head == SUCCESS;
     - no concurrent Agent publication or branch mutation active.

3. The carve-out permits ONLY a human-initiated owner/maintainer action performed personally through the GitHub UI or an owner-controlled CLI session. `gh pr merge` run personally by an owner/maintainer is permitted. The decisive property is who reviews, decides, and personally triggers the action — not whether a UI or CLI is used.

4. The following remain Path-B (forbidden under the carve-out):
   - Agent-initiated, automation-initiated, workflow-initiated, scheduled, delegated, or external-service-initiated merge or mark-ready;
   - GitHub auto-merge;
   - merge or mark-ready of R2/R3 work items;
   - direct push to `main`, force push, rebase, squash (without separate authorization), tag, release.

5. Do NOT modify: Gate runtime, LangGraph runtime, workflows (`.github/workflows/**`), dependencies, `docs/run_closeout.md`, `.codex-skills/**`, product source (`reverse_agent/**`), or any test file other than `tests/test_minimal_integration_baseline_docs.py`.

6. Do NOT clean up old `project_state/gates/*` artifacts in this round (tracked-file cleanup requires separate authority). Do NOT create `project_state/pr_body_governance_migration_v1.md` as a repo file; the PR body is written to a temp path outside the repo and passed via `gh pr create --body-file`.

7. Generate and validate v1 Command Plan / preflight evidence. Require CI, Decision Preflight, and State Gate success on one exact head.

8. Create a Draft PR recording the Path-B Decision snapshot in its body. Keep the PR Draft until independent audit accepts the exact head.

### Counting rule

The six governance migration files (the deliverable) and the Decision/Gate transition evidence files (generated by the gate sequence) are counted separately. See `scope_policy.six_governance_files` and `scope_policy.transition_evidence_files`. The migration deliverable is exactly six files; transition evidence is not part of the deliverable.

### Completion

Completion requires:
- `python -m pytest tests/test_minimal_integration_baseline_docs.py -q` passes;
- `git diff --check` passes;
- exactly the six allowed governance files are modified as the deliverable (transition evidence files are separate);
- new tests explicitly permit owner manual mark-ready + merge under carve-out conditions;
- new tests continue to prohibit Agent/automation merge;
- CI passes on the final exact head;
- Draft PR created with Path-B Decision snapshot in body;
- STOP for independent audit.

Merge is NOT part of this round. The migration PR's own final merge requires either a follow-up amendment to this Decision explicitly authorizing exact-head merge, or a separate bounded Path-B merge authorization. The new lightweight rule cannot be used to merge itself.

### Stop Conditions

Stop immediately when:
- transition-lint fails;
- transition-preflight does not return PRE_EXECUTION_AUTHORIZED;
- focused tests fail;
- `git diff --check` fails;
- CI fails on exact head;
- scope violation detected (files changed outside the six allowed paths plus transition evidence);
- independent audit rejects the head;
- any attempt to merge or mark-ready without separate authorization;
- the six-file patch is applied before PRE_EXECUTION_AUTHORIZED.
