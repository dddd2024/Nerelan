# Exact PR1048 delegated landing authority

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261003_pr1048_delegated_landing_r3_v1",
  "round_id": "round_20261003_pr1048_delegated_landing_r3_v1",
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
  "fresh_worktree_creation_required": false,
  "history_reuse_allowed": false,
  "provider_free_acceptance_required": true,
  "decision_scope": "EXACT_PR1048_DELEGATED_LANDING_ONLY",
  "source_issue": 1047,
  "parent_issue": 1010,
  "approved_by": "dddd2024",
  "approval_basis": "Owner explicit persistent full project control and permission to change any part; NEW bounded delegated stage, not personal human R1 carve-out. Owner persistent explicit full project delegation prospectively authorizes this NEW exact PR1048 delegated landing stage, not a reset or edit of its immutable source Decision. Source head 9d07f111faf6f2c5cea3fac3dd52be39f417aafb; locked main/base 9092911f41a089e249f27c883526904299be1d17; source Decision blob13a6e3a5ecc0126469b171cfde5d0517d4b89e91 sha2569a9dd72d5751e016185b7ca9a67db794677bbd5d0cd29f69a32255e96e432aad. Only three product paths dev-up.ps1,dev-down.ps1,tests/platform_v1/test_dev_up_contract.py plus source Decision. Independent comment5928275769 provides exact-head Windows functional proof:61 actual PowerShell5.1 and61 PowerShell7.6.5; strict identities, keeper loss, late LISTEN descendants, partial failure/retry and preservation of unknown processes. It expressly grants no merge; this separate Decision does. Fresh remote source CI36835408571attempt2,Windows36835408656,Decision andordinaryStateGate SUCCESS required. Verify original source diagnostic/artifact and scope, independent proof and all source acceptance criteria; do not broaden independent acceptance to whole repo. No product changes, live fixture/model/provider/runtime/browser or dependency installation. Reuse known checkout preserving five unstaged generated gates, fresh exact-base branch and Decision-only activation, actual existing bootstrap/plan/lint/preflight/readiness. At most one provider-free tests/test_mainline_landing.py pytest process<=300s; mandatory failure stops without retry. At most one normal authority branch push, one unmerged authority Draft, two description updates, one transparent delegated Owner-account COMMENTED exact-head review, one existing-format attestation, one target Ready and one expected-head merge; no authority Ready/merge. Reuse existing false/none protocol exactly as merged1022: ready_state_gate_run_id is explicitly pre-Ready ordinary successful State Gate, never a claim formal landing already passed; require newly natural formal landing-state-gate after Ready. All owner-account actions delegated automation, never personal human acceptance. Before Ready/merge require both Decisions/heads/base/digests current, no unresolved blocking threads/concurrent publication, current ruleset21023698, exact source and authority natural checks, existing canonical validation. Before merge require newly natural formal baseline/state-gate/landing-state-gate success,MERGEABLE,CLEAN,current main andPRbase equal lockedbase; merge methodmerge withmatchhead; no owner bypass or admin. Postmerge verify merged mergeOID,parents,tree,remote main equalsmergeOID and existing native landing receipt/naturalmainCI before mainline acceptance. Close no Issues in this stage, deploy nothing. Stop on scope/head/base/authority drift, failed mandatory checks,budget or deadline. Window ends 2026-10-03T13:49:45.046755+00:00. Preserve all other branches/PRs/Issues/services/source/evidence; no new Gate/schema/receipt family.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "required_branch": "codex/pr1048-delegated-landing-r3-v1-20261003",
  "workstream_id": "pr1048-delegated-landing-r3-v1",
  "follows_last_decision_id": "decision_20261001_windows_owned_shutdown_r3_v1",
  "follows_last_round_id": "round_20261001_windows_owned_shutdown_r3_v1",
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
  "base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "activation_base_sha": "9092911f41a089e249f27c883526904299be1d17",
  "starting_head": "9092911f41a089e249f27c883526904299be1d17",
  "fresh_base": "9092911f41a089e249f27c883526904299be1d17",
  "current_main_expected": "9092911f41a089e249f27c883526904299be1d17",
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
    "specification": "Owner persistent explicit full project delegation prospectively authorizes this NEW exact PR1048 delegated landing stage, not a reset or edit of its immutable source Decision. Source head 9d07f111faf6f2c5cea3fac3dd52be39f417aafb; locked main/base 9092911f41a089e249f27c883526904299be1d17; source Decision blob13a6e3a5ecc0126469b171cfde5d0517d4b89e91 sha2569a9dd72d5751e016185b7ca9a67db794677bbd5d0cd29f69a32255e96e432aad. Only three product paths dev-up.ps1,dev-down.ps1,tests/platform_v1/test_dev_up_contract.py plus source Decision. Independent comment5928275769 provides exact-head Windows functional proof:61 actual PowerShell5.1 and61 PowerShell7.6.5; strict identities, keeper loss, late LISTEN descendants, partial failure/retry and preservation of unknown processes. It expressly grants no merge; this separate Decision does. Fresh remote source CI36835408571attempt2,Windows36835408656,Decision andordinaryStateGate SUCCESS required. Verify original source diagnostic/artifact and scope, independent proof and all source acceptance criteria; do not broaden independent acceptance to whole repo. No product changes, live fixture/model/provider/runtime/browser or dependency installation. Reuse known checkout preserving five unstaged generated gates, fresh exact-base branch and Decision-only activation, actual existing bootstrap/plan/lint/preflight/readiness. At most one provider-free tests/test_mainline_landing.py pytest process<=300s; mandatory failure stops without retry. At most one normal authority branch push, one unmerged authority Draft, two description updates, one transparent delegated Owner-account COMMENTED exact-head review, one existing-format attestation, one target Ready and one expected-head merge; no authority Ready/merge. Reuse existing false/none protocol exactly as merged1022: ready_state_gate_run_id is explicitly pre-Ready ordinary successful State Gate, never a claim formal landing already passed; require newly natural formal landing-state-gate after Ready. All owner-account actions delegated automation, never personal human acceptance. Before Ready/merge require both Decisions/heads/base/digests current, no unresolved blocking threads/concurrent publication, current ruleset21023698, exact source and authority natural checks, existing canonical validation. Before merge require newly natural formal baseline/state-gate/landing-state-gate success,MERGEABLE,CLEAN,current main andPRbase equal lockedbase; merge methodmerge withmatchhead; no owner bypass or admin. Postmerge verify merged mergeOID,parents,tree,remote main equalsmergeOID and existing native landing receipt/naturalmainCI before mainline acceptance. Close no Issues in this stage, deploy nothing. Stop on scope/head/base/authority drift, failed mandatory checks,budget or deadline. Window ends 2026-10-03T13:49:45.046755+00:00. Preserve all other branches/PRs/Issues/services/source/evidence; no new Gate/schema/receipt family.",
    "completion_boundary": "Exact1048 source mainline acceptance only after existing protocol and actual native evidence; no Issue closure, frontend fix or whole goal completion."
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
      "Owner persistent explicit full project delegation prospectively authorizes this NEW exact PR1048 delegated landing stage, not a reset or edit of its immutable source Decision. Source head 9d07f111faf6f2c5cea3fac3dd52be39f417aafb; locked main/base 9092911f41a089e249f27c883526904299be1d17; source Decision blob13a6e3a5ecc0126469b171cfde5d0517d4b89e91 sha2569a9dd72d5751e016185b7ca9a67db794677bbd5d0cd29f69a32255e96e432aad. Only three product paths dev-up.ps1,dev-down.ps1,tests/platform_v1/test_dev_up_contract.py plus source Decision. Independent comment5928275769 provides exact-head Windows functional proof:61 actual PowerShell5.1 and61 PowerShell7.6.5; strict identities, keeper loss, late LISTEN descendants, partial failure/retry and preservation of unknown processes. It expressly grants no merge; this separate Decision does. Fresh remote source CI36835408571attempt2,Windows36835408656,Decision andordinaryStateGate SUCCESS required. Verify original source diagnostic/artifact and scope, independent proof and all source acceptance criteria; do not broaden independent acceptance to whole repo. No product changes, live fixture/model/provider/runtime/browser or dependency installation. Reuse known checkout preserving five unstaged generated gates, fresh exact-base branch and Decision-only activation, actual existing bootstrap/plan/lint/preflight/readiness. At most one provider-free tests/test_mainline_landing.py pytest process<=300s; mandatory failure stops without retry. At most one normal authority branch push, one unmerged authority Draft, two description updates, one transparent delegated Owner-account COMMENTED exact-head review, one existing-format attestation, one target Ready and one expected-head merge; no authority Ready/merge. Reuse existing false/none protocol exactly as merged1022: ready_state_gate_run_id is explicitly pre-Ready ordinary successful State Gate, never a claim formal landing already passed; require newly natural formal landing-state-gate after Ready. All owner-account actions delegated automation, never personal human acceptance. Before Ready/merge require both Decisions/heads/base/digests current, no unresolved blocking threads/concurrent publication, current ruleset21023698, exact source and authority natural checks, existing canonical validation. Before merge require newly natural formal baseline/state-gate/landing-state-gate success,MERGEABLE,CLEAN,current main andPRbase equal lockedbase; merge methodmerge withmatchhead; no owner bypass or admin. Postmerge verify merged mergeOID,parents,tree,remote main equalsmergeOID and existing native landing receipt/naturalmainCI before mainline acceptance. Close no Issues in this stage, deploy nothing. Stop on scope/head/base/authority drift, failed mandatory checks,budget or deadline. Window ends 2026-10-03T13:49:45.046755+00:00. Preserve all other branches/PRs/Issues/services/source/evidence; no new Gate/schema/receipt family."
    ]
  },
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Preserve pre-existing five generated gates unstaged and known ignored Python scratch; write new external evidence only; never stage generated artifacts."
  },
  "allowed_commands": [
    {
      "command_id": "pr1048.bootstrap",
      "command": "Fresh exact-base codex/pr1048-delegated-landing-r3-v1-20261003 Decision-only activation; existing canonical startup/plan/lint/preflight/readiness; preserve prior gates.",
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
      "command_id": "pr1048.validate",
      "command": "One python -B -m pytest tests/test_mainline_landing.py -q -p no:cacheprovider <=300s; git diff --check; source exact native diagnostic/artifact/scope and independent proof checks; no repeat on failure.",
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
      "command_id": "pr1048.publish_authority",
      "command": "One exact authority push and one unmerged Draft against main@9092911f41a089e249f27c883526904299be1d17; require natural CI/Decision/State SUCCESS.",
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
      "command_id": "pr1048.attest",
      "command": "One transparent delegated COMMENTED review and one existing-format attestation on1048 after source+authority native acceptance and fresh observation; explicitly bind successful pre-Ready ordinaryStateGate as existing1022 precedent; canonical validator only.",
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
      "command_id": "pr1048.ready",
      "command": "One gh pr ready1048 only after valid attestation; require newly natural formal landing-state-gate and ordinaryStateGate SUCCESS.",
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
      "command_id": "pr1048.merge",
      "command": "One gh pr merge1048 --merge --match-head-commit 9d07f111faf6f2c5cea3fac3dd52be39f417aafb only after immediate lockedbase 9092911f41a089e249f27c883526904299be1d17 and head,MERGEABLE,CLEAN,current canonical required checks,threads/scope/concurrency verification; no admin/bypass; verify native mainline receipt/parents/tree/main; close no Issues.",
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
      "command_id": "pr1048.natural_ci",
      "command": "Read-only natural exact authority,target andmain CI/Decision/State/Windows observations; no rerun/dispatch.",
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
  "target_pr": 1048,
  "accepted_exact_head_sha": "9d07f111faf6f2c5cea3fac3dd52be39f417aafb",
  "expected_head_protection_required": true,
  "allowed_merge_method": "merge",
  "workflow_profile": "baseline",
  "source_issues": [
    1047
  ]
}
```
