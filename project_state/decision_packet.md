# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260725_governance_migration_owner_manual_merge_v1","round_id":"round_20260725_governance_migration_owner_manual_merge_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260725_merge_run_closeout_legacy_doc_pilot_v1",
  "follows_last_round_id": "round_20260725_merge_run_closeout_legacy_doc_pilot_v1",
  "previous_audit_outcome": "R0_ASSESSMENT_ACCEPTED_WITH_REQUIRED_CORRECTIONS",
  "workstream_id": "governance-migration-owner-manual-merge-v1",
  "source_issue": 43,
  "program_issue": 26,
  "owner_design_review_comment_id": "issuecomment-5078843920",
  "implementation_branch": "codex/governance-migration-owner-manual-merge-v1",
  "required_branch": "plan/governance-migration-owner-manual-merge-v1",
  "starting_head": "4abf7fc90e05253452e4199f2a65401be782422d",
  "activation_base_sha": "4abf7fc90e05253452e4199f2a65401be782422d",
  "expected_current_main_sha": "4abf7fc90e05253452e4199f2a65401be782422d",
  "implementation_must_create_branch_from_main": true,
  "pr_creation_allowed": true,
  "mark_ready_allowed": false,
  "merge_allowed": false,
  "auto_merge_allowed": false,
  "stop_after_implementation_push_and_ci": true,
  "stop_for_independent_audit": true,
  "bootstrap_exception_files": ["project_state/decision_packet.md","project_state/gates/command_plan.json"],
  "bootstrap_exception_commands": ["gate.startup_snapshot","status.git_status","gate.command_plan","gate.transition_lint","gate.pre_execution"],
  "allowed_commands": [
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"],"produced_artifacts":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"status.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["command_plan_generation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"],"produced_artifacts":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["authority_validation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"gate.pre_execution","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pre_execution_authorization"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"],"produced_artifacts":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"observe.verify_main_unchanged","command":"git fetch origin main && test \"$(git rev-parse origin/main)\" = \"4abf7fc90e05253452e4199f2a65401be782422d\"","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"implementation.create_branch","command":"git switch -c codex/governance-migration-owner-manual-merge-v1 origin/main","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["branch_creation"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"implementation.pytest","command":"python -m pytest tests/test_minimal_integration_baseline_docs.py tests/test_planning_and_github_adapters.py -q","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["deterministic_check"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"implementation.git_diff_check","command":"git diff --check","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["deterministic_check"],"network_access":false,"required_evidence_source":"local_provenance","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.push_branch","command":"git push -u origin codex/governance-migration-owner-manual-merge-v1","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.create_draft_pr","command":"gh pr create --repo dddd2024/reverse-agent --base main --head codex/governance-migration-owner-manual-merge-v1 --title \"governance: owner-manual-merge carve-out for accepted ordinary R1 PRs (R2 migration v1)\" --draft --body-file <pr_body_file>","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_creation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"observe.wait_ci","command":"gh pr view <pr_number> --repo dddd2024/reverse-agent --json statusCheckRollup,headRefOid,baseRefOid,mergeable,mergeStateStatus","phase":"observation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_observation","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]},
    {"command_id":"publication.update_pr_description","command":"gh pr edit <pr_number> --repo dddd2024/reverse-agent --body-file <pr_body_final_file>","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["pull_request_update","network_access"],"network_access":true,"required_evidence_source":"repository_truth","authority_origin":"normal_plan","allowed_mutated_paths":[],"produced_artifacts":[]}
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
  "reference_paths": ["docs/run_closeout.md","docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md","reverse_agent/project_gate.py"],
  "generated_artifact_paths": ["project_state/gates/startup_snapshot.json","project_state/gates/command_plan.json","project_state/gates/bootstrap_state.json","project_state/gates/transition_command_plan_preview.json","project_state/gates/transition_preflight_result.json"],
  "forbidden_mutated_paths": [
    "reverse_agent/**",
    ".github/workflows/**",
    ".github/ISSUE_TEMPLATE/**",
    "docs/run_closeout.md",
    "docs/architecture/ARCHITECTURE_SPINE_REUSE_INVENTORY.md",
    "docs/roadmap/architecture_spine_*.md",
    "docs/audits/**",
    "docs/prompts/**",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/rounds/**"
  ],
  "forbidden_operations": [
    "direct push to main",
    "force push",
    "rebase",
    "squash",
    "tag",
    "release",
    "unknown_binary_execution",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "workflow_dispatch",
    "automatic_merge",
    "merge",
    "mark_pr_ready_for_review",
    "git_config_modification",
    "history_rewrite",
    "secret_access",
    "destructive_operations",
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
    "hostile_binary_analysis_implementation",
    "modify_run_closeout_md",
    "modify_workflows",
    "modify_runtime_code",
    "create_new_artifact_family",
    "weaken_existing_test_without_replacement",
    "merge_implementation_pr",
    "mark_ready_implementation_pr"
  ],
  "capability_policy": {
    "git_push_from_local_executor": true,
    "branch_creation_from_local_executor": true,
    "pull_request_creation_from_local_executor": true,
    "merge_from_local_executor": false,
    "mark_pr_ready_for_review": false,
    "local_network_exceptions": [
      "git fetch origin main",
      "git push -u origin codex/governance-migration-owner-manual-merge-v1",
      "gh pr create --repo dddd2024/reverse-agent --base main --head codex/governance-migration-owner-manual-merge-v1",
      "gh pr view <pr_number> --repo dddd2024/reverse-agent",
      "gh pr edit <pr_number> --repo dddd2024/reverse-agent"
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
    {"pattern":"AGENTS.md","minimum_risk":"R2"},
    {"pattern":"docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md","minimum_risk":"R2"},
    {"pattern":"docs/architecture/SOURCE_OF_TRUTH_MATRIX.md","minimum_risk":"R2"},
    {"pattern":"docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md","minimum_risk":"R2"},
    {"pattern":".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml","minimum_risk":"R2"},
    {"pattern":"tests/test_minimal_integration_baseline_docs.py","minimum_risk":"R2"},
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"}
  ],
  "scope_policy": {
    "scope": "governance_migration_owner_manual_merge_carve_out",
    "allow_product_source": false,
    "allow_dependency_changes": false,
    "allow_workflow_changes": false,
    "allow_test_additions": true,
    "allow_documentation_changes": true,
    "allow_template_changes": true,
    "allow_governance_simplification": true,
    "allow_authority_boundary_modification": true
  },
  "stop_conditions": [
    "transition_lint_failure",
    "preflight_not_authorized",
    "working_tree_not_clean_at_gate_time",
    "current_main_sha_mismatch",
    "implementation_branch_creation_failure",
    "pytest_failure",
    "git_diff_check_failure",
    "push_failure",
    "pr_creation_failure",
    "ci_not_successful_on_exact_head",
    "pr_head_moved_after_push",
    "pr_base_mismatch",
    "scope_violation_detected",
    "attempted_mark_ready",
    "attempted_merge",
    "attempted_workflow_change",
    "attempted_dependency_change",
    "attempted_runtime_code_change",
    "attempted_run_closeout_modification",
    "local_gate_residue_not_isolated"
  ]
}
```

## DECISION_PACKET

### Goal

Perform a one-time R2/Path-B governance migration that introduces a narrow owner-manual-merge carve-out for accepted ordinary R1 PRs. The migration edits exactly six files, runs deterministic tests, pushes an implementation branch, creates a Draft PR, waits for exact-head CI, updates the PR description with exact-head validation truth, and stops for independent audit. This Decision does not authorize mark-ready or merge of the implementation PR; a separate future R2 Decision will authorize the merge after audit acceptance.

### Authority and bindings

This Decision is activated by the repository owner/planning authority on branch `plan/governance-migration-owner-manual-merge-v1`. It binds:

- `source_issue`: #43 (R0 assessment with accepted owner design review)
- `owner_design_review_comment_id`: `issuecomment-5078843920` (ACCEPT_WITH_REQUIRED_CORRECTIONS)
- `activation_base_sha`: `4abf7fc90e05253452e4199f2a65401be782422d` (current `origin/main`)
- `expected_current_main_sha`: `4abf7fc90e05253452e4199f2a65401be782422d` (must not move before implementation branch creation)
- `implementation_branch`: `codex/governance-migration-owner-manual-merge-v1` (created from `origin/main` during execution)
- `risk_tier`: R2 (this migration modifies the privileged-publication authority boundary)

### Why R2, not R1

Per owner design review correction #1: the proposed change alters when `mark-ready` and `merge` may occur without a separate Path-B Decision. Under the current rules these operations are R2. The existing R1 authority model must not be used to rewrite its own privilege boundary. The one-time rule migration implementation is therefore R2/Path-B. The future qualifying owner-manual acceptance that the rule enables is a lightweight Path-A carve-out; the migration itself is not.

### Required design content (seven owner-review corrections)

The implementation must write the following design content into the six allowed files. The corrections are mandatory; an implementation that omits any of them is a scope violation.

#### Correction 1 — implementation tier

The migration is R2/Path-B. The future qualifying owner-manual acceptance is a Path-A carve-out. Both statements must appear in `AGENTS.md` and `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`.

#### Correction 2 — actor/control distinction, not "tool-initiated"

The rule must distinguish by who reviews, decides, and personally triggers the action, not by whether a UI or CLI is used. Use these terms:

```text
permitted carve-out:
  human-initiated owner/maintainer action performed personally through
  the GitHub UI or an owner-controlled CLI session

Path-B remains mandatory:
  agent-initiated, automation-initiated, workflow-initiated, scheduled,
  delegated, or external-service-initiated mark-ready/merge
```

The implementation must not use the phrase "tool-initiated" as the decisive property. `gh pr merge` run personally by an owner/maintainer is permitted; the same command run by an Agent, automation, workflow, scheduler, delegated service, or external service is Path-B.

#### Correction 3 — carve-out covers both mark-ready and merge

Because ordinary R1 PRs remain Draft until independent exact-head audit, the final human sequence is:

```text
owner/maintainer manual mark-ready
-> immediate owner/maintainer manual merge
-> post-merge verification
```

Agent/automation mark-ready, Agent/automation merge, and GitHub auto-merge remain Path-B. This must appear in `AGENTS.md`, `docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md`, `docs/architecture/SOURCE_OF_TRUTH_MATRIX.md`, and the R1 template.

#### Correction 4 — local working-tree cleanliness is conditional

The implementation must state:

```text
GitHub UI merge:
  no universal local-working-tree requirement;
  no concurrent Agent publication or branch mutation may be active

owner-controlled local CLI merge:
  the local session/worktree must be clean enough to prevent accidental
  commit, push, branch mutation, or mixing of unrelated changes
```

The nine re-observation invariants from the R0 assessment remain mandatory; the local-working-tree invariant is narrowed per actor/control path.

#### Correction 5 — local Gate residue isolation

Before creating the implementation branch, the executor must verify the working tree is clean of prior Path-B Gate residue. If any `project_state/gates/*` file is modified relative to `origin/main`, the executor must restore it before proceeding. The residue must not be included in the implementation branch or PR. This is encoded as a stop condition `local_gate_residue_not_isolated`.

#### Correction 6 — six-file scope

The implementation may modify only:

```text
AGENTS.md
docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md
docs/architecture/SOURCE_OF_TRUTH_MATRIX.md
docs/architecture/LEGACY_GOVERNANCE_CONTAINMENT.md
.github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml
tests/test_minimal_integration_baseline_docs.py
```

It must not modify `docs/run_closeout.md`, runtime or Gate code, GitHub Actions workflows, dependencies, `project_state` protocols or artifact families, permissions, credentials, secrets, tags, or releases.

#### Correction 7 — safety invariants remain mandatory

The implementation must preserve at least:

```text
approved immutable R1 Work Item snapshot
normalized Issue-body digest and reapproval invalidation rule
exact allowed_paths and forbidden_operations
fresh branch and approved base_sha / merge-base equality
focused deterministic checks
required exact-head GitHub Actions success
independent audit accepting the exact head
no unresolved blocking review threads
immediate pre-merge head/base/main/CI/mergeability re-observation
accepted-head immutability / expected-head protection
owner/maintainer-only personal mark-ready and merge
plain merge method unless separately Path-B authorized
post-merge verification and recorded merge SHA
source Work Item closure only after verification
```

### Authorized sequence

1. Generate and validate the Decision-bound Command Plan and require `PRE_EXECUTION_AUTHORIZED`.
2. Verify `origin/main` is exactly `4abf7fc90e05253452e4199f2a65401be782422d`.
3. Verify the working tree is clean of prior Gate residue; restore if needed.
4. Create implementation branch `codex/governance-migration-owner-manual-merge-v1` from `origin/main`.
5. Edit the six allowed files to introduce the owner-manual-merge carve-out per the seven corrections above.
6. Run `python -m pytest tests/test_minimal_integration_baseline_docs.py tests/test_planning_and_github_adapters.py -q` and `git diff --check`.
7. Commit the implementation.
8. Push the implementation branch.
9. Create a Draft PR with an immutable authority snapshot referencing this Decision and Issue #43.
10. Wait for exact-head CI to complete successfully.
11. Update the Draft PR description with exact-head validation truth (head SHA, base SHA, CI status, changed paths).
12. Stop for independent audit. Do not mark ready. Do not merge.

### Explicit prohibitions

This Decision does **not** authorize any of the following:

- Marking the implementation PR ready for review.
- Merging the implementation PR.
- Modifying any file outside the six-file scope (Correction 6).
- Modifying `docs/run_closeout.md`, runtime/Gate code, workflows, dependencies, `project_state` protocols, permissions, credentials, secrets, tags, or releases.
- Rebase, squash, force-push, auto-merge, or direct push to `main`.
- Starting any other governance simplification beyond the six-file scope.
- Weakening any existing test assertion without replacing it with an equivalent or stronger assertion.
- Creating a new artifact family.
- Running implementation work before `PRE_EXECUTION_AUTHORIZED`.

### Stop conditions

Stop immediately and do not proceed if any of the following is true:

- `transition-lint` or `transition-preflight` fails, or `PRE_EXECUTION_AUTHORIZED` is not achieved.
- The working tree is not clean at Gate time, or prior Gate residue is not isolated.
- `origin/main` has moved away from `4abf7fc90e05253452e4199f2a65401be782422d` before implementation branch creation.
- Implementation branch creation fails.
- `pytest` or `git diff --check` fails.
- Push or Draft PR creation fails.
- CI on the exact head is not successful.
- The PR head moves after push, or the PR base does not match `4abf7fc90e05253452e4199f2a65401be782422d`.
- Any scope violation is detected.
- Any attempt to mark-ready, merge, change workflows, change dependencies, modify runtime code, or modify `docs/run_closeout.md`.

### Completion

Completion requires: six-file implementation committed on `codex/governance-migration-owner-manual-merge-v1`; deterministic tests pass; branch pushed; Draft PR created with immutable authority snapshot; exact-head CI successful; PR description updated with exact-head validation truth. The implementation PR remains Draft and unmerged for independent audit. A separate future R2 Decision will authorize mark-ready + merge after audit acceptance.

### Future merge of the implementation PR

This Decision does not authorize merge. After independent audit accepts the implementation PR's exact head, a separate bounded R2 Path-B Decision must be created to authorize mark-ready + merge of the implementation PR. That future Decision will bind the accepted implementation PR head, the then-current `origin/main` SHA, and `merge_method: merge` with `--match-head-commit` protection. The future merge Decision is not preemptively authorized by this Decision.
