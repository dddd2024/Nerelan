# Existing EBA-0 current-main recovery

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20261008_issue1033_current_base_recovery_r2_v1",
  "round_id": "round_20261008_issue1033_current_base_recovery_r2_v1",
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
  "decision_scope": "ISSUE1033_CURRENT_MAIN_EBA0_RECOVERY",
  "source_issue": 1033,
  "parent_issue": 118,
  "repository": "dddd2024/Nerelan",
  "approved_by": "Codex/root acting under explicit dddd2024 Owner delegation",
  "approval_basis": "\u8fd9\u4e9b\u6388\u6743\u4e5f\u662f\u4f60\u6765\u505a\uff0c\u73b0\u5728\u76ee\u6807\u662f\u957f\u671f\u65e0\u4eba\u5e72\u9884\u7684\u5e73\u53f0\uff0c\u8fd9\u6837\u4e00\u76f4\u505c\u4e5f\u662f\u95ee\u9898\u9700\u8981\u4fee\u6b63; delegated controller selects existing EBA-0 current-base recovery under the continuing goal.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "activation_base_sha": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "starting_head": "97d766d7253378c093c31ed29c990cb6921f2ae4",
  "required_branch": "codex/issue1033-current-base-recovery-r2-20261008",
  "fresh_worktree_creation_required": true,
  "history_reuse_allowed": false,
  "decision_commit_must_precede_implementation": true,
  "decision_commit_must_precede_execution": true,
  "decision_content_immutable_after_activation": true,
  "decision_immutability_required": true,
  "decision_immutability_check_required_in": [
    "transition_preflight",
    "transition_reconcile",
    "worktree_publication_readiness"
  ],
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 4,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 5,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": false,
  "pull_request_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
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
  "local_browser_execution_allowed": false,
  "model_api_invocation_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "unknown_binary_execution_allowed": false,
  "destructive_operations_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "semantic_implementation_contract": {
    "specification": "Recover the five existing EBA-0 files from independently reviewed Draft #1036@44d9d9a2111b4acc306f0a97a1483654d13a0ebb on exact current main. Existing paths are byte-identical to the original approved base; retain source blob identities where no correction is needed. Authorization-only results must not claim product acceptance or implementation completion; fix real task-check output head binding; reuse existing static Work Item preflight and all original negative tests. Do not duplicate the framework or relax authority/rejection semantics. Record original source and actual new tested head separately; keep old candidate untouched.",
    "reuse": "Exact source #1036 five approved blobs, current Path A parser/normalization/fixed check selection, existing transition compiler and original regressions; source/Decision of other active tasks untouched.",
    "execution_surface_note": "Full fresh current-main worktree; immutable Decision-only activation and actual canonical preflight precede source edits. Provider-free original tests and approved CLI probes in owned external scratch. Distinct new allocation preserves all prior spending/failures and original delegation expiry.",
    "completion_boundary": "Local exact-head checks, natural required CI and independent exact-head review; Draft only, no Ready/merge/Issue closure or full autonomy claims."
  },
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
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "tests/test_path_a_gate.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/control_plane/work_item_preflight.py",
    "tests/platform_v1/test_evidence_bound_autonomy.py",
    "tests/test_path_a_gate.py",
    "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    ".codex-skills/reverse-agent-iteration/SKILL.md",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "reverse_agent/project_gate.py",
    ".github/workflows/ci.yml"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".codex-skills/**",
    "AGENTS.md",
    "docs/agents/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/model_access/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "frontend/**",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env",
    "dev-up.ps1",
    "dev-down.ps1"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "squash",
    "amend",
    "history_rewrite",
    "mark_ready",
    "merge",
    "workflow_rerun",
    "workflow_dispatch",
    "runner_dispatch",
    "model_api_invocation",
    "provider_network_call",
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "tag_or_release",
    "dependency_install",
    "local_browser_execution",
    "generated_governance_commit"
  ],
  "capability_policy": {
    "github_control_plane_network_exceptions": [
      "Publish only exact codex/issue1033-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "reverse_agent/control_plane/**",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "eba0.implementation",
      "command": "Recover the five existing EBA-0 files from independently reviewed Draft #1036@44d9d9a2111b4acc306f0a97a1483654d13a0ebb on exact current main. Existing paths are byte-identical to the original approved base; retain source blob identities where no correction is needed. Authorization-only results must not claim product acceptance or implementation completion; fix real task-check output head binding; reuse existing static Work Item preflight and all original negative tests. Do not duplicate the framework or relax authority/rejection semantics. Record original source and actual new tested head separately; keep old candidate untouched.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "source_edit",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/path_a.py",
        "reverse_agent/control_plane/work_item_preflight.py",
        "tests/platform_v1/test_evidence_bound_autonomy.py",
        "tests/test_path_a_gate.py",
        "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "eba0.validation",
      "command": "python -m pytest tests/platform_v1/test_evidence_bound_autonomy.py tests/test_path_a_gate.py tests/test_control_plane_transition.py tests/test_decision_preflight.py -q -p no:cacheprovider",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "unit_test",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "eba0.cli-probes",
      "command": "Run the existing Work Item preflight module CLI against frozen valid and invalid static candidates in owned external scratch; inspect JSON and output-file real path without GitHub/model/runtime calls. This is structural readiness, not approval.",
      "phase": "validation",
      "required": false,
      "expected_exit_codes": [
        0,
        1,
        2
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "local_static_check"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "eba0.publication",
      "command": "Publish only exact codex/issue1033-current-base-recovery-r2-20261008 to dddd2024/Nerelan and create/update its single Draft PR against approved main after publication readiness.",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "approval_event_or_time": "2026-10-08T05:38:38.073620+00:00",
  "owner_delegation_sha256": "75705d8dfce811a39649a707062b991143153a4a000fc9e2b62287112299b29e",
  "confirmation_mode": "DELEGATED_CONTROLLER",
  "personally_human": false,
  "development_check_run_limit": 4,
  "development_correction_round_limit": 3,
  "mandatory_check_run_limit": 6,
  "execution_expires_at": "2026-10-08T09:22:21.386602+00:00",
  "reference_implementation": {
    "repository": "dddd2024/Nerelan",
    "pr": 1036,
    "head": "44d9d9a2111b4acc306f0a97a1483654d13a0ebb",
    "files": [
      {
        "path": "reverse_agent/control_plane/path_a.py",
        "candidate_blob": "4068cb18125778529eeaac2d6c44847f1f829f81",
        "candidate_sha256": "caf30ed28f9c950ca83cc0a8008e1143618a636d8e961a02f652c2f0ddb922c8",
        "original_base_blob": "83fd21b9f6d14665c216b8dd6a8815fcd26d6df5",
        "current_main_blob": "83fd21b9f6d14665c216b8dd6a8815fcd26d6df5",
        "main_unchanged_from_original_base": true,
        "candidate_is_current_main": false
      },
      {
        "path": "reverse_agent/control_plane/work_item_preflight.py",
        "candidate_blob": "777c765a88b910a8e1aa43b9f123c713bd42849b",
        "candidate_sha256": "6c60a49695a54f785c490bcdbe1643ac47e5a1b68680a999987d68f9d273a231",
        "original_base_blob": null,
        "current_main_blob": null,
        "main_unchanged_from_original_base": true,
        "candidate_is_current_main": false
      },
      {
        "path": "tests/platform_v1/test_evidence_bound_autonomy.py",
        "candidate_blob": "6aced66a98220375dc9b6dde33f959e41b791885",
        "candidate_sha256": "77c5e06e0392bfce39a292de4e122fb17ca05dd279d05997fd906393d3034104",
        "original_base_blob": null,
        "current_main_blob": null,
        "main_unchanged_from_original_base": true,
        "candidate_is_current_main": false
      },
      {
        "path": "tests/test_path_a_gate.py",
        "candidate_blob": "c9eacd9e7389ee5fca6e15f331e95ae646e51a1d",
        "candidate_sha256": "05a2a82b60c561d77e804f2ca29584d8aed493966e16e058a3e0eccaa63448c6",
        "original_base_blob": "225e3e314e75a094a4612becd1361769b060d73b",
        "current_main_blob": "225e3e314e75a094a4612becd1361769b060d73b",
        "main_unchanged_from_original_base": true,
        "candidate_is_current_main": false
      },
      {
        "path": "docs/architecture/EVIDENCE_BOUND_AUTONOMY.md",
        "candidate_blob": "87fc025bd2834fa02bf9e4c79512d1c93bcd7758",
        "candidate_sha256": "e9016e224c4affaf85c18d84910752393ba5e6c0c43ee15087614eba84436195",
        "original_base_blob": null,
        "current_main_blob": null,
        "main_unchanged_from_original_base": true,
        "candidate_is_current_main": false
      }
    ]
  }
}
```
