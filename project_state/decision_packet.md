# Conditional exact-head delegated PR1028 landing

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260929_pr1028_delegated_landing_r2_v1",
  "round_id": "round_20260929_pr1028_delegated_landing_r2_v1",
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
  "repository": "dddd2024/Nerelan",
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "EXACT_PR1028_DELEGATED_LANDING_ONLY",
  "source_issue": 1027,
  "parent_issue": 1010,
  "approved_by": "dddd2024 via explicit current delegated Owner authorization",
  "approval_basis": "Owner explicitly delegated publication, independent acceptance and merge of the pending GitHub work items, with the system performing every step. This bounded Decision authorizes one Decision-only unmerged authority Draft on branch codex/pr1028-delegated-landing-v1-20260929 and the exact-head landing of PR1028, the approved R1 frontend consolidation for Issue 1027. Product content is R1: frontend presentation, design tokens, brand identity and copy, with no schema, authority, budget, publication or durable-state surface. The transition itself is the governance artifact and carries the R2 floor. PR1028 is already approved by the Owner r1-approved label event of 2026-09-29T11:29:53Z and is complete at head d13eec586d47ba7fb286486170fdf711630e160a with new-refresh visual baselines re-captured from the canonical CI container. This Decision authorizes Ready and one expected-head merge only after an independent exact-head audit confirms every acceptance criterion and all required checks are green at that exact head. No source edit is authorized on the sidecar. All Owner-account actions are disclosed delegated automation, never personal human review.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "required_branch": "codex/pr1028-delegated-landing-v1-20260929",
  "workstream_id": "pr1028-delegated-landing-r2-v1",
  "follows_last_decision_id": "decision_20260928_pr1022_delegated_landing_r3_v1",
  "follows_last_round_id": "round_20260928_pr1022_delegated_landing_r3_v1",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 0,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 1,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 1,
  "merge_attempt_limit": 1,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "base_sha": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "activation_base_sha": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "starting_head": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "fresh_base": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "current_main_expected": "393886c2e1b764e6f8a4ed638aceb24cccdc92a8",
  "workflow_rerun_allowed": false,
  "workflow_dispatch_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
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
    ".github/**",
    ".codex-skills/**",
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "docs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
  ],
  "forbidden_operations": [
    "source_edit",
    "direct_push_main",
    "force_push",
    "rebase",
    "history_rewrite",
    "auto_merge",
    "tag_or_release",
    "workflow_rerun",
    "runner_dispatch",
    "model_api_invocation",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "dependency_install",
    "generated_governance_commit",
    "active_json_rewrite",
    "authority_pr_ready_or_merge",
    "target_branch_mutation"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    }
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py"
  ],
  "semantic_implementation_contract": {
    "specification": "No source edits on this sidecar. This Decision-only branch is created from exact base 393886c2e1b764e6f8a4ed638aceb24cccdc92a8 and adds exactly one commit containing only project_state/decision_packet.md. It authorizes the landing of already-authored, already-approved PR1028 content at frozen head d13eec586d47ba7fb286486170fdf711630e160a (tree of the approved R1 frontend consolidation for Issue 1027): 78 paths, all under frontend/, 6119 insertions and 4200 deletions against the same base. Product risk is R1 (frontend presentation, design tokens, brand, copy); the transition and its evidence are the R2 governance artifact. The content is unmodified by this Decision and no frontend path is touched here. PR1028 carries the Approvals empty-state truth fix, the design-token discipline guard with a zero-literal-colour assertion, the Nerelan brand with the nerelan.appearance storage-key migration, 24px minimum interaction targets, Chinese copy, and the eight refreshed @visual baselines re-captured from the canonical CI container (mcr.microsoft.com/playwright:v1.62.1-noble, run 36562645075). The two exceptional paths stay inside the Owner constraints recorded on Issue 1027: the vendored agent-canvas files are bounded to interaction-target and visual-compatibility change with upstream defaults preserved, and frontend/src/schemas/model-access.ts is bounded to presentation-layer parsing/validation. No backend, schema, authority, budget or durable-state surface is touched.",
    "completion_boundary": "Run the existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness sequence with python -m reverse_agent.project_gate against project_state; require PRE_EXECUTION_AUTHORIZED then PUBLICATION_READY. Generated artifacts are evidence, not an independent grant, and no gate result may be hand-written. Push this authority branch once and create one Draft against locked main; observe natural Decision Preflight and State Gate success with no rerun or dispatch, and never Ready or merge the sidecar. Then independently audit PR1028 at the frozen accepted head: confirm the diff is exactly the 78 allowed paths with none outside frontend/, re-read the two exceptional paths against the Owner constraints, confirm zero unresolved review threads and all required checks green at that exact head, and post one transparent delegated Owner-account review stating that every Owner-account action is delegated automation and never personal human review. Mark PR1028 Ready exactly once and require the naturally triggered formal landing-state-gate and state-gate success at the accepted head. Immediately before merge re-verify that main still equals the base, that the head still equals the accepted head, that the PR is MERGEABLE and CLEAN, and that no concurrent publication is in flight; then merge once with expected-head protection and method merge, and verify merged, the merge commit, its parents and tree, and natural post-merge main CI and State integration success. Only then close 1027 with linked source and main evidence. If any acceptance criterion is not confirmed, retain 1027 open and record the exact residual instead of closing it. Keep every unrelated Issue and PR untouched and preserve all other authority Drafts."
  },
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
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural CI setup and provider-free checks only."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Canonical dddd2024/Nerelan only: one exact authority push and Draft on codex/pr1028-delegated-landing-v1-20260929; independent review of PR1028 at its frozen accepted head; one Ready and one expected-head merge of PR1028; then closure comment on Issue 1027 only. No other Issue or PR mutations."
    ]
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Only pre-existing/generated ignored local Python scratch; never stage."
  },
  "allowed_commands": [
    {
      "command_id": "pr1028.bootstrap",
      "command": "Commit only this Decision once in a fresh exact-base codex/pr1028-delegated-landing-v1-20260929 checkout. Run existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness using python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. Never edit the activated Decision and never stage generated gates.",
      "phase": "bootstrap",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation",
        "commit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/decision_packet.md"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "pr1028.validate",
      "command": "Run existing python -B -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider and git diff --check on the exact sidecar head. Verify the sidecar adds only project_state/decision_packet.md, and re-verify PR1028 scope, checks and review state at its frozen accepted head.",
      "phase": "validation",
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "unit_test",
        "local_static_check",
        "diff_validation",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1028.publish_authority",
      "command": "Push the exact authority branch once and create one Draft against locked main. Decision-only sidecar; never Ready or merge it. Observe natural Decision Preflight and State Gate SUCCESS. No reruns or dispatch.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1028.audit",
      "command": "Independently audit PR1028 at its frozen accepted head: allowed-path diff equals exactly the 78 Issue-1027 paths with none outside frontend/, the two exceptional paths stay inside the Owner constraints, acceptance criteria hold against the code, zero unresolved review threads, and all required checks green at that exact head. Post one transparent delegated Owner-account review disclosing that every Owner-account action is delegated automation and never personal human review.",
      "phase": "final_evidence",
      "execution_surface": "github_control_plane",
      "operations": [
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1028.ready",
      "command": "Only after the delegated audit review is posted and no drift has occurred, run gh pr ready 1028 --repo dddd2024/Nerelan exactly once. Require the naturally triggered formal landing-state-gate and ordinary state-gate SUCCESS at the exact accepted head. No rerun, dispatch, conversion cycling or fake context.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "mark_ready",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1028.merge",
      "command": "Immediately verify main still equals 393886c2e1b764e6f8a4ed638aceb24cccdc92a8 and the head still equals d13eec586d47ba7fb286486170fdf711630e160a, MERGEABLE/CLEAN, exact required checks and audit review present, and no concurrent publication. Run gh pr merge 1028 --repo dddd2024/Nerelan --merge --match-head-commit d13eec586d47ba7fb286486170fdf711630e160a once. Verify merged, the merge commit, its parents and tree, and natural post-merge main CI and State success, then close 1027 if every acceptance criterion is confirmed. Preserve every other Issue and PR.",
      "phase": "publication",
      "execution_surface": "github_control_plane",
      "operations": [
        "merge",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "pr1028.natural_ci",
      "command": "Observe unchanged natural authority and target/main CI, Decision Preflight and State Gate; no provider calls in tests.",
      "phase": "validation",
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "target_pr": 1028,
  "accepted_exact_head_sha": "d13eec586d47ba7fb286486170fdf711630e160a",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "workflow_profile": "baseline",
  "source_issues": [
    1027
  ]
}
```
