# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260824_issue345_scope_aware_workflow_policy_r2_v2",
  "round_id": "round_20260824_issue345_scope_aware_workflow_policy_r2_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260824_issue345_scope_aware_workflow_policy_r2",
  "follows_last_round_id": "round_20260824_issue345_scope_aware_workflow_policy_r2",
  "previous_audit_outcome": "PR346_DRAFT_CLOSED_DECISION_PACKET_REFERENCE_PATH_DEFECT_CORRECTED_IN_THIS_V2_ROUND",
  "workstream_id": "issue345-scope-aware-workflow-policy-r2-v2",
  "source_issue": 345,
  "parent_issue": 343,
  "superseded_source_pr": 346,
  "superseded_source_head_sha": "1f4af0147a8ffaf1c1d5ff219c0dcf9a3bae7db7",
  "accepted_source_pr": 344,
  "accepted_source_head_sha": "50d54db6308dcb6ba1e655c7099edb61a10c13e9",
  "accepted_source_base_sha": "af0bfdb62d96e00b5f89660390950f3b7f096026",
  "integration_base_ref": "main",
  "base_sha": "cb6e7a3e3b92935525079278e327843fd1f2d03e",
  "activation_base_sha": "cb6e7a3e3b92935525079278e327843fd1f2d03e",
  "starting_head": "cb6e7a3e3b92935525079278e327843fd1f2d03e",
  "required_branch": "owner/issue345-scope-aware-workflow-policy-r2-v2",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "workflow_profile": "baseline",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": ["transition_preflight", "transition_reconcile", "worktree_publication_readiness"],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 3,
  "generated_governance_commit_limit": 1,
  "post_publication_binding_commit_limit": 1,
  "normal_push_attempt_limit": 3,
  "draft_pr_creation_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "known_browser_execution_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "allowed_merge_method": "merge",
  "mainline_merge_intent_required": true,
  "active_pr_binding_mode": "post_draft_pr_exact_remote_number",
  "issue_number_must_not_substitute_for_pr_number": true,
  "test_semantics_changes_allowed": true,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "verify exact main base cb6e7a3e3b92935525079278e327843fd1f2d03e and fresh branch merge-base",
    "commit this immutable R2 Decision as the unique first commit",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue345_r2v2.bootstrap",
      "command": "verify locked base cb6e7a3e3b92935525079278e327843fd1f2d03e and fresh branch; commit Decision first; generate five gates and require PRE_EXECUTION_AUTHORIZED",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["code_read", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "produced_artifacts": [
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue345_r2v2.trusted_profiles_and_v3_intent",
      "command": "extend reverse_agent/mainline_landing.py with the production-owned TRUSTED_PREMERGE_WORKFLOW_PROFILES mapping (baseline plus browser_r3 supersets including Frontend Playwright and Model Access), schema-v3 intent support binding workflow_profile to the same value declared by the accepted-head Decision contract, profile resolution that always includes the generic three-workflow baseline, and schema-v3 attestation validation that requires exactly the resolved profile workflow set on the exact accepted head while State Gate push remains post-merge-only",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py"
      ]
    },
    {
      "command_id": "issue345_r2v2.v3_schema",
      "command": "add project_state/schemas/mainline_merge_intent_v3.schema.json describing the schema-v3 intent with the bounded workflow_profile enum and required_workflows constrained to the baseline-first resolved profile sets",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/schemas/mainline_merge_intent_v3.schema.json"
      ]
    },
    {
      "command_id": "issue345_r2v2.profile_regressions",
      "command": "extend tests/test_mainline_landing.py with focused regressions proving: generic baseline round resolves and accepts the three-workflow baseline; browser_r3 round resolves an exact set including Frontend Playwright and Model Access; missing failing wrong-head or wrong-file/event specialized runs block; deleting a specialized workflow from committed active intent fails; unknown workflow profile name fails; duplicate run id fails; intent profile must equal the Decision-declared profile; State Gate push remains excluded from pre-merge requirements; historical schema-v1 and v2 fixtures keep their frozen semantics; post-merge mainline validation still runs unchanged",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "unit_test", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "tests/test_mainline_landing.py"
      ]
    },
    {
      "command_id": "issue345_r2v2.validate_and_publish",
      "command": "run the focused mainline-landing suite, the platform_v1 merge-intent suite, and the project-gate focused suite; commit implementation; push exact branch and create one Draft PR",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["unit_test", "lint", "local_static_check", "commit", "push", "draft_pr", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue345_r2v2.bind_intent",
      "command": "after the real Draft PR number is known archive the current PR344 intent byte-identically as archive/pr344_v2.json and bind active.json schema v3 to the exact new PR with workflow_profile baseline equal to this Decision-declared profile",
      "phase": "binding",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["source_edit", "local_static_check", "commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/mainline_merge_intents/active.json",
        "project_state/mainline_merge_intents/archive/pr344_v2.json"
      ]
    },
    {
      "command_id": "issue345_r2v2.final_push_and_audit",
      "command": "push the final intent binding and require exact-head CI Decision Preflight and State Gate terminal success plus independent audit while the PR remains Draft",
      "phase": "audit",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_static_check", "push", "network_access", "read_only_audit"],
      "network_access": true,
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr344_v2.json",
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    "tests/test_mainline_landing.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_state.py",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/schemas/mainline_merge_intent.schema.json",
    ".github/workflows/ci.yml",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/frontend-playwright.yml",
    ".github/workflows/model-access.yml"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "docs/**",
    "requirements*.txt",
    "pyproject.toml",
    ".github/workflows/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/platform_v1/**",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "project_state/schemas/mainline_merge_intent.schema.json",
    "project_state/schemas/mainline_merge_intent_v2.schema.json",
    "project_state/mainline_recoveries/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "tests/platform_v1/**",
    "tests/test_project_gate.py"
  ],
  "forbidden_operations": [
    "direct_push_main", "auto_merge", "merge", "mark_ready", "force_push", "rebase", "squash", "reset", "clean", "stash", "restore", "amend", "history_rewrite",
    "unknown_binary_execution", "secrets", "destructive_delete", "privileged_remote_execution", "model_api_invocation", "provider_network_call", "credential_access", "auth_store_read",
    "runner_dispatch", "workflow_rerun", "tag_or_release", "deployment", "issue_comment", "issue_close", "pull_request_comment", "pull_request_close",
    "dependency_install", "browser_execution", "snapshot_update", "arbitrary_remote_browsing", "external_url_navigation", "offensive_security_or_network_attack_work",
    "second_decision_commit", "weaken_baseline_three_workflow_requirement", "allow_branch_controlled_workflow_weakening", "allow_free_form_workflow_names",
    "weaken_v1_or_v2_historical_semantics", "make_state_gate_push_pre_merge", "modify_workflows_or_ci", "broad_dependency_change"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "live_provider_access_allowed": false,
    "credential_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "dependency_install_allowed": false,
    "known_binary_execution_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "mark_ready_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "auto_merge_allowed": false,
    "tag_or_release_allowed": false,
    "deployment_allowed": false,
    "github_issue_comment_allowed": false,
    "github_issue_close_allowed": false,
    "github_pr_comment_allowed": false,
    "github_pr_creation_allowed": true,
    "github_pr_close_allowed": false,
    "publication_allowed": true,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "push exact branch and create one Draft PR after all validation suites pass",
      "push the final intent binding and require exact-head CI Decision Preflight and State Gate terminal success plus independent audit while the PR remains Draft"
    ],
    "ci_network_exceptions": []
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/schemas/**", "minimum_risk": "R2"},
    {"pattern": "reverse_agent/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ],
  "authorized_risk_paths": [
    "reverse_agent/mainline_landing.py",
    "project_state/schemas/mainline_merge_intent_v3.schema.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr344_v2.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_tier": "R2",
  "success_terminal": "ISSUE345_R2V2_SCOPE_AWARE_WORKFLOW_PROFILE_POLICY_DRAFT_ACCEPTED_FOR_OWNER_LANDING",
  "blocked_terminal": "ISSUE345_R2V2_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Implement the scope-aware mainline required-workflow policy exactly as scoped by Issue #345: introduce the smallest backward-compatible production-owned mechanism that resolves required pre-merge workflows from a bounded trusted profile enum instead of a single hard-coded three-entry policy, so an approved R3/browser acceptance contract can machine-enforce its specialized exact-head checks (Frontend Playwright, and Model Access when the approved contract requires it) while the generic three-workflow baseline remains mandatory for every profile, State Gate (push) remains post-merge-only, and historical schema-v1/v2 intent and attestation semantics stay frozen and unchanged.

This v2 round supersedes the blocked v1 round (superseded Draft PR #346, final head 1f4af014): the v1 Decision packet mistakenly listed the two implementation targets `reverse_agent/mainline_landing.py` and `tests/test_mainline_landing.py` in `reference_paths` (read-only) while the same paths are required implementation targets, so the F10 `reference_paths_read_only` check correctly blocked Decision Preflight and State Gate. The v2 Decision keeps the same implementation, base, and scope with the corrected `reference_paths` list.

## Acceptance

1. This Decision is the unique immutable first commit from `main@cb6e7a3e3b92935525079278e327843fd1f2d03e`; all later implementation descends from it.
2. `reverse_agent/mainline_landing.py` defines `TRUSTED_PREMERGE_WORKFLOW_PROFILES` as a production-owned mapping where every profile is a superset of the generic baseline (`CI`, `Decision Preflight`, `State Gate (pull_request)`); `browser_r3` additionally requires `Frontend Playwright` and `Model Access` on the exact accepted head.
3. Schema-v3 merge intents carry a bounded `workflow_profile` field that must name a profile in the trusted enum, must equal the `workflow_profile` declared by the accepted-head Decision contract, and whose `required_workflows` must equal the resolved profile set exactly; unknown profile names, missing or deleted specialized workflows, and free-form workflow names all fail closed.
4. Schema-v3 attestations validate workflow observations against the intent's resolved profile set: every required workflow must bind repository, exact workflow file, event, exact accepted head SHA, current run attempt, completed status and success conclusion; missing, failing, wrong-head, wrong-file/event or duplicate-run observations block.
5. Historical schema-v1 and schema-v2 intents and attestations keep their frozen semantics and existing fixtures pass unchanged; `State Gate (push)` remains post-merge evidence only and post-merge mainline validation still runs unchanged.
6. `tests/test_mainline_landing.py` gains focused regressions covering every case in Acceptance 2-5 including the generic baseline acceptance path, the browser_r3 exact-set resolution, every blocking case, the Decision-profile binding, and the unchanged post-merge validation.
7. No workflow file, CI definition, dependency, frontend path, platform_v1 source, project_gate source, or credential surface is modified; no browser binary is executed; no model or provider call occurs.
8. One Draft PR is created and bound to a schema-v3 intent with `workflow_profile` equal to this Decision's declared `baseline`; exact-head checks and independent audit accept; it remains Draft until the owner performs the audited landing.
9. The Decision's `reference_paths` list contains no path that this round mutates; the v1 defect (implementation targets mis-listed as read-only references) is corrected.

## Execution policy

- The trusted profile mapping lives only in production source on the integration base; a feature branch can select a profile but can never weaken, remove or invent one.
- Stage only exact allowed paths. Never reset, clean, stash, restore, amend, rebase, squash or force push.
- All validation is local and deterministic: no network access except the two bounded publication/audit exceptions.
- Keep the PR Draft. Agent comment, attestation, ready and merge remain prohibited; owner landing follows independent audit under this Decision's bounded scope.
