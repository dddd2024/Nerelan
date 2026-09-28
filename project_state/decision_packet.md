# Bounded system successor for Issue990 on current main

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260928_issue990_system_source_policy_r3_v2",
  "round_id": "round_20260928_issue990_system_source_policy_r3_v2",
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
  "decision_scope": "ISSUE990_SYSTEM_CURRENT_BASE_SUCCESSOR_ONLY",
  "source_issue": 990,
  "parent_issue": 989,
  "approved_by": "dddd2024 via explicit delegated Owner authorization",
  "approval_basis": "Owner explicitly delegates all GitHub tasks to the Nerelan system, supervisor independent acceptance and bounded publication/landing, no monetary/token cap. Latest request follows priority index1010: after PR1006 complete, continue990 before989. Old991 is preserved unchanged on stale base; system must adapt its existing narrow design to current main, not duplicate or widen it. This source stage authorizes three system tasks and existing launcher recovery only, with Draft publication; landing remains separate.",
  "risk_tier": "R3",
  "authorized_risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "54b161e8799d1a5ccce498e8f8dfc2519e943a22",
  "activation_base_sha": "54b161e8799d1a5ccce498e8f8dfc2519e943a22",
  "starting_head": "54b161e8799d1a5ccce498e8f8dfc2519e943a22",
  "fresh_base": "54b161e8799d1a5ccce498e8f8dfc2519e943a22",
  "current_main_expected": "54b161e8799d1a5ccce498e8f8dfc2519e943a22",
  "required_branch": "codex/issue990-source-policy-system-v2-20260928",
  "workstream_id": "issue990-system-source-policy-v2",
  "follows_last_decision_id": "decision_20260927_issue997_windows_binding_env_r2_v1",
  "follows_last_round_id": "round_20260927_issue997_windows_binding_env_r2_v1",
  "workflow_profile": "baseline",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 2,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "live_model_call_limit": 3,
  "provider_network_call_limit": 0,
  "credential_access_limit": 0,
  "local_browser_launch_limit": 0,
  "pr_creation_allowed": true,
  "issue_comment_allowed": true,
  "pull_request_comment_allowed": true,
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
  "live_provider_access_allowed": true,
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "model_api_invocation_allowed": true,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_worktree_source_policy.py",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "reverse_agent/control_plane/worktree_state.py",
    "reverse_agent/project_gate.py",
    "tests/test_worktree_source_policy.py",
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
    "frontend/**",
    "reverse_agent/model_access/**",
    "reverse_agent/platform_v1/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt"
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
    "credential_access",
    "unknown_binary_execution",
    "external_reverse_tool_invocation",
    "destructive",
    "tag_or_release",
    "dependency_install",
    "generated_governance_commit",
    "snapshot_generation_or_threshold_change",
    "fix_forward_after_mandatory_failure"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    }
  ],
  "semantic_implementation_contract": {
    "specification": "Introduce only the reviewed exact source identity reverse_agent/model_access/credential_relay.py as a narrow exception to soft credential/secret basename classification in applicable, passed, validated Path-B publication readiness with an immutable APPROVED R3 Decision and its matching current valid preflight. Require literal exact allowed path (not wildcard), ordinary regular source blobs at both frozen integration base and current HEAD, same-path M-only modification in index/worktree, no symlink or type change. Obtain independent Git tree/index/filesystem metadata; fail closed on missing or inconsistent identity. Never infer existence from tracked=git_tracked or authority_matched, from status!=??, or from .py extension. Deny additions including staged A and additions committed after base, deletions, rename/copy both ends, type changes, untracked, sensitive case variants and unauthorized neighbors. Preserve hard deny for secret directories, actual credential stores/config, .env, private keys, cert/key and binary paths before any soft-name exception. No global authorization-first reorder, generic Python exception, new Decision schema, override flag or receipt. Keep Path A sensitive R3 risk floor and behavior unchanged; no exception in startup or clean-start policy. Preserve ordinary authorized nonsensitive additions and generated-governance nonstageable semantics. Only validated Path-B readiness caller may supply separately named verified source evidence to pure classifier, default empty.",
    "tests": "New test file must cover positive exact existing base/HEAD regular source M in both unstaged and staged states; missing/stale/invalid authority or preflight; broad glob; neighbors; untracked, staged A, committed-after-base addition, deletion, rename/copy both ends, symlink/type change, failed metadata lookup, hard secret/config/key/binary and case variants; unchanged Path A and ordinary additions/gates behavior. Include real production worktree-publication-readiness in isolated synthetic Git repositories with test-only approved fixture Decision/preflight and regular source metadata. Never modify user repository/Issue989 to fabricate readiness; no real secret content reads.",
    "completion_boundary": "System authors all three allowed product/test files on detached exact activation worker. Supervisor may supply old991 three-file diff as read-only task data, not copy its obsolete Decision. Review and adapt existing implementation; no wholesale gate redesign. Supervisor transfers exact system output, independently validates, one final product commit and one final Draft push. No mark-ready/merge/deployment or Issue closure under source stage. Mandatory exact-head failure stops publication; development fixes allowed before freeze."
  },
  "runtime_scratch_policy": {
    "paths": [
      ".platform_v1_runtime/**",
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Existing launcher runtime stores/metadata only; task-specific evidence outside repository. Never edit credentials, user settings or unknown files."
  },
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [],
    "ci_network_exceptions": [
      "Unchanged natural CI package setup and provider-free checks only; no added workflow or manual dispatch."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "Existing loopback Task/Model public API and unchanged configured coding-glm binding via trusted executor, at most3 system tasks,1concurrent,0automaticretries,no monetary/token cap. Known installed Python/PowerShell/Git only. Provider-free tests may use test-owned loopback. No credential content read, connection/binding mutation or provider health probe."
    ],
    "github_control_plane_network_exceptions": [
      "Canonical exact branch activation/implementation pushes and one Draft; descriptions only. No Ready/merge/tag/release under source stage."
    ]
  },
  "allowed_commands": [
    {
      "command_id": "issue990v2.bootstrap",
      "command": "Create fresh exact-base F:/Nerelan-issue990-system-v2-20260928 on codex/issue990-source-policy-system-v2-20260928; commit only immutable Decision once; existing startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness via python -m reverse_agent.project_gate SUBCOMMAND --state-dir project_state; require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY. No product edits before activation Draft.",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "commit",
        "command_plan_generation",
        "local_static_check",
        "machine_specific_execution"
      ],
      "network_access": false,
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
      "command_id": "issue990v2.runtime",
      "command": "Current services are not listening. Inspect only existing launcher public metadata and process identity; preserve TaskStore and settings. Use unchanged Windows PowerShell5 F:/reverse-agent/dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/Nerelan-issue990-system-v2-20260928 -OpenCodeModel sensenova-6.8-flash-lite -NoBrowser with execution/planning SHA equal activation. Process-local autonomous/live ports and2700timeout/3600lease may restore previously working values without changing persisted user settings. Only launcher-verified owned processes may restart, and never with inflight tasks. If unknown ownership or start failure stop affected action, do not kill by name. No deployment of candidate into dirty root.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue990v2.system",
      "command": "After activation Draft exists, dispatch at most3 scoped tasks via existing Task API/coding-glm, one concurrent, zeroautomaticretry, no monetary/token cap. Exact activation detached worker only. System reads approved old991 three-file diff as task data and adapts within semantic contract. No external worktree access, commit/push or governance edits by worker. Process-local PATHEXT workaround allowed. Supervisor transfers only exact system output bytes, reviews/checks, then one final product commit.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "source_edit",
        "commit",
        "local_static_check",
        "machine_specific_execution",
        "model_api_invocation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/worktree_state.py",
        "reverse_agent/project_gate.py",
        "tests/test_worktree_source_policy.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue990v2.checks",
      "command": "Before freeze, development checks and fixes by system within3Task bound. Final exact-head mandatory: python -B -m pytest tests/test_worktree_source_policy.py -q -p no:cacheprovider; python -B -m pytest tests/test_path_a_gate.py tests/test_project_gate.py -q -p no:cacheprovider; python -B -m pytest tests/test_control_plane_transition.py tests/test_decision_preflight.py -q -p no:cacheprovider; git diff --check base HEAD. Existing publication readiness before stage and after commit; generated gates never staged. No dependencies/install/live providers in tests.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "unit_test",
        "integration_test",
        "diff_validation",
        "local_static_check",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue990v2.publish",
      "command": "At mosttwo exact branch codex/issue990-source-policy-system-v2-20260928 pushes (activation then final),one Draft against main at 54b161e8799d1a5ccce498e8f8dfc2519e943a22, description updates exact head. Preserve991; no Ready/merge/closure/rebase. Require fresh main/base/head and PUBLICATION_READY before each push.",
      "phase": "publication",
      "required": true,
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
    },
    {
      "command_id": "issue990v2.ci",
      "command": "Observe natural CI/Decision/State exact-head checks and native diagnostic artifact; no reruns/manualdispatch.",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "ci_only",
      "operations": [
        "unit_test",
        "integration_test",
        "local_static_check",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "issue990v2.audit",
      "command": "Supervisor independent source acceptance (no supervisor authored product/test code), exact scope/tree/checks and negative security cases. Candidate work is not deployed. Record old991 reuse and residual989 responsibility.",
      "phase": "final_evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "remote_observation",
      "operations": [
        "code_read",
        "read_only_audit",
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "concurrent_work_preservation": {
    "prs": [
      991,
      992,
      995,
      1000,
      1003,
      1007,
      1008
    ],
    "policy": "Preserve all old PR heads and worktrees, dirty root71records, user Connections/Bindings/API keys. No new UI changes, provider setting changes or old991 mutation. Same responsible supervisor serially resumes990 after1006, old991 retained as source evidence."
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py",
    "dev-up.ps1"
  ],
  "source_issues": [
    990
  ],
  "required_provider_free_checks": [
    "python -m pytest tests/test_worktree_source_policy.py -q",
    "python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py -q",
    "python -m pytest tests/test_control_plane_transition.py tests/test_decision_preflight.py -q",
    "git diff --check"
  ]
}
```
