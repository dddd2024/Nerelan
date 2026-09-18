# Decision Packet — #891 false/none pre-merge attestation closure v4 API publication

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v4",
  "round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v4",
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
  "decision_scope": "FALSE_NONE_PREMERGE_ATTESTATION_V4_CONTROL_PLANE_PUBLICATION",
  "source_issue": 891,
  "parent_issue": 156,
  "repository": "dddd2024/Nerelan",
  "approved_by": "dddd2024 via explicitly delegated repository Owner execution",
  "approval_basis": "User delegated Owner execution and Remote Desktop Commander trusted local work. PR938 v3 is terminal wrong-publication-surface evidence only: semantic bytes, tests, Owner audit and Actions were green, but its branch was created by trusted_worker git push instead of the Decision-required github_control_plane. V4 changes publication provenance only.",
  "supersedes_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v3",
  "superseded_evidence": "PR938@146d6dd328911a4d6e7dfef852b31508532440e0 CLOSED_UNMERGED_TERMINAL_WRONG_PUBLICATION_SURFACE_EVIDENCE; semantic content retained, authority not reused.",
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "activation_base_sha": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "starting_head": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "required_branch": "owner/issue891-false-none-attestation-r2-v4-api",
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
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "workflow_rerun_allowed": false,
  "runner_dispatch_allowed": false,
  "direct_push_to_main_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "dependency_install_allowed": false,
  "live_provider_access_allowed": false,
  "credential_access_allowed": false,
  "local_browser_execution_allowed": false,
  "provider_free_acceptance_required": true,
  "mainline_merge_intent_required": false,
  "active_pr_binding_mode": "none",
  "workflow_profile": "baseline",
  "semantic_implementation_contract": {
    "specification": "Close the real false/none pre-merge landing path using reviewed PR893 S2 semantics. Ready/non-Draft landing-state-gate must route through project_gate transition-preflight and require exactly one valid existing-format OWNER_LANDING_MERGE_ATTESTATION bound to exact target PR/head/base, exact unmerged landing-authority Decision/head/base, Owner review and exact-head workflow evidence. Premerge requires completed baseline+state-gate plus trusted current landing-state-gate execution context, without self-requiring that currently executing landing-state-gate already be complete. Postmerge remains unchanged and requires all three completed contexts. Draft/non-landing and legacy merge-intent behavior remain unchanged. No second receipt family or PR-number exception.",
    "execution_surface_note": "Decision/source/test/commit work runs only on the clean isolated trusted_worker checkout. Generated gate evidence has zero commit budget. Remote Decision/semantic commits, branch ref and Draft PR are created only through GitHub control plane; local git push/gh publication is forbidden.",
    "completion_boundary": "One immutable Decision commit plus one semantic commit and one Draft PR. No generated-governance commit, local git push, Ready, Merge, rerun or dispatch."
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
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/project_gate.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/transition.py",
    ".github/workflows/state-gate.yml",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "AGENTS.md",
    "docs/agents/governance-reference.md"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/control_plane/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/rounds/**",
    "project_state/mainline_merge_intents/**",
    "**/secrets/**",
    "**/.env"
  ],
  "forbidden_operations": [
    "active_json_rewrite",
    "amend",
    "auto_merge",
    "browser_execution",
    "destructive",
    "direct_push_main",
    "external_reverse_tool_invocation",
    "force_push",
    "generated_governance_commit",
    "history_rewrite",
    "mark_ready",
    "merge",
    "model_api_invocation",
    "rebase",
    "runner_dispatch",
    "squash",
    "tag_or_release",
    "unknown_binary_execution",
    "workflow_dispatch",
    "workflow_rerun"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "merge_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [],
    "github_control_plane_network_exceptions": [
      "Create only the v4 Decision/semantic commit graph and branch owner/issue891-false-none-attestation-r2-v4-api in dddd2024/Nerelan, then one Draft PR against main@3ec2235d583c92c71077aae3751e3216d5bcd94c; comment only on Issue891/156 and that Draft; never Ready/Merge."
    ]
  },
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/mainline_landing.py",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/project_gate.py",
      "minimum_risk": "R2"
    }
  ],
  "allowed_commands": [
    {
      "command_id": "issue891v4.bootstrap",
      "command": "On this exact clean isolated current-main checkout verify Decision/branch/base. Run startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Generated gate files are ephemeral evidence only and must not be committed. Require PRE_EXECUTION_AUTHORIZED before semantic mutation.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "code_read",
        "local_static_check",
        "command_plan_generation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json"
      ]
    },
    {
      "command_id": "issue891v4.implement",
      "command": "After PRE_EXECUTION_AUTHORIZED rematerialize the exact reviewed v3 semantic bytes in the four authorized files; do not reuse commit history. Run focused #891 regressions and commit once.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "source_edit",
        "unit_test",
        "local_static_check",
        "commit"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/mainline_landing.py",
        "reverse_agent/project_gate.py",
        "tests/test_mainline_landing.py",
        "tests/test_project_gate.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v4.validate",
      "command": "Run python -m pytest tests/test_mainline_landing.py -k false_none -q; python -m pytest tests/test_project_gate.py -k 'false_none or landing_authority' -q; git diff --check. V3 full-suite 1522/4 is content evidence only; v4 natural exact-head CI/Decision Preflight/State Gate are mandatory final validation.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "trusted_worker",
      "operations": [
        "unit_test",
        "local_static_check",
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v4.publish",
      "command": "Through github_control_plane only, create the exact Decision then semantic commit graph, create branch owner/issue891-false-none-attestation-r2-v4-api, and one Draft PR against main@3ec2235d583c92c71077aae3751e3216d5bcd94c. No local git push, Ready or Merge.",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "github_control_plane",
      "operations": [
        "push",
        "draft_pr",
        "pull_request_comment",
        "issue_comment",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue891v4.observe",
      "command": "Fresh-read remote commit trees/ref/PR and natural exact-head Actions. Confirm remote tree identities match trusted-worker trees and Owner-audit the production path. No Ready/Merge.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "read_only_audit",
        "code_read"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "issue_completion_close_allowed": [],
  "workstream_id": "issue891-false-none-attestation-r2-v4-api",
  "follows_last_decision_id": "decision_20260918_issue891_false_none_premerge_attestation_r2_v3",
  "follows_last_round_id": "round_20260918_issue891_false_none_premerge_attestation_r2_v3",
  "fresh_base": "3ec2235d583c92c71077aae3751e3216d5bcd94c",
  "current_main_expected": "3ec2235d583c92c71077aae3751e3216d5bcd94c"
}
```

## Goal

Make the real false/none Owner landing entrypoint fail closed before merge when the existing-format Owner landing attestation is absent or invalid, while preserving the reviewed acyclic PR893 S2 lifecycle.

## Build vs reuse

Reuse PR893 S2 semantic content, current State Gate transition-preflight, OWNER_LANDING_MERGE_ATTESTATION parser/digest/binding, GitHubRemoteAcceptanceVerifier and unchanged post-merge validation. Do not add another receipt family, Gate, GitHub client, scheduler, workflow, dependency, database or policy engine.

## Implementation scope

After PRE_EXECUTION_AUTHORIZED, exactly four semantic paths:
- reverse_agent/mainline_landing.py
- reverse_agent/project_gate.py
- tests/test_mainline_landing.py
- tests/test_project_gate.py

## Stop conditions

Stop on main/base drift, Decision mutation, unavailable trusted-worker surface, failed preflight, scope expansion, test/check failure or exhausted publication budget. Generated gate evidence may be regenerated but not committed. Never Ready or Merge under this Decision.
