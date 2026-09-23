# Approved bounded worktree source policy

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260923_issue990_worktree_source_policy_r2_v1",
  "round_id": "round_20260923_issue990_worktree_source_policy_r2_v1",
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
  "risk_tier": "R2",
  "authorized_risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "integration_base_ref": "main",
  "base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "activation_base_sha": "58d4068f43ca4914b122445685cae410a8fa156e",
  "starting_head": "58d4068f43ca4914b122445685cae410a8fa156e",
  "fresh_base": "58d4068f43ca4914b122445685cae410a8fa156e",
  "current_main_expected": "58d4068f43ca4914b122445685cae410a8fa156e",
  "follows_last_decision_id": "decision_20260923_issue982_gpt_oauth_network_r3_v1",
  "follows_last_round_id": "round_20260923_issue982_gpt_oauth_network_r3_v1",
  "decision_activation_commit_limit": 1,
  "product_change_commit_limit": 1,
  "generated_governance_commit_limit": 0,
  "normal_push_attempt_limit": 0,
  "draft_pr_creation_limit": 1,
  "mark_ready_attempt_limit": 0,
  "merge_attempt_limit": 0,
  "workflow_rerun_limit": 0,
  "runner_dispatch_limit": 0,
  "workflow_dispatch_limit": 0,
  "credential_access_limit": 0,
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
  "credential_access_allowed": false,
  "unknown_binary_execution_allowed": false,
  "external_reverse_tool_invocation_allowed": false,
  "destructive_operations_allowed": false,
  "bootstrap_exception_files": [
    "project_state/decision_packet.md"
  ],
  "bootstrap_exception_commands": [],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    ".github/**",
    ".codex-skills/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/e2e/snapshots/**",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "pyproject.toml",
    "requirements*.txt",
    "**/secrets/**",
    "**/.env"
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
    "fix_forward_after_mandatory_failure",
    "model_api_invocation",
    "provider_network_call",
    "oauth_operation",
    "runtime_restart",
    "browser_launch",
    "old_worktree_cleanup"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/e2e/snapshots/**",
      "minimum_risk": "R3"
    },
    {
      "pattern": "reverse_agent/control_plane/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "reverse_agent/project_gate.py",
      "minimum_risk": "R2"
    }
  ],
  "decision_scope": "BOUNDED_TRACKED_SOURCE_CLASSIFICATION_REPAIR",
  "source_issue": 990,
  "parent_issue": 260,
  "approved_by": "dddd2024 via explicit delegated Owner execution",
  "approval_basis": "User explicitly authorizes supervisor fallback when system cannot complete. Actual Issue988 attempt failed with no product patch. Independently reviewed exact candidate ee711b70ab74bb87c026a5f5c2bd55c29178e3e139d84fbef5c159aaca576d0a. This bounded round permits the independently reviewed existing worktree classifier and Path B readiness correction with provider-free checks and Draft-only publication. No models, credentials, runtime restart or landing.",
  "required_branch": "codex/worktree-source-policy-r2-v1-20260923",
  "workstream_id": "issue990-worktree-source-policy-r2-v1",
  "workflow_profile": "baseline",
  "live_provider_access_allowed": false,
  "model_api_invocation_allowed": false,
  "live_model_call_limit": 0,
  "provider_network_call_limit": 0,
  "oauth_operation_limit": 0,
  "local_browser_launch_limit": 0,
  "system_task_attempt_limit": 0,
  "runtime_restart_limit": 0,
  "development_check_round_limit": 8,
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
  "semantic_implementation_contract": {
    "specification": "Introduce only the reviewed exact source identity reverse_agent/model_access/credential_relay.py as a narrow exception to soft credential/secret basename classification in applicable, passed, validated Path-B publication readiness with an immutable APPROVED R3 Decision and its matching current valid preflight. Require literal exact allowed path (not wildcard), ordinary regular source blobs at both frozen integration base and current HEAD, same-path M-only modification in index/worktree, no symlink or type change. Obtain independent Git tree/index/filesystem metadata; fail closed on missing or inconsistent identity. Never infer existence from tracked=git_tracked or authority_matched, from status!=??, or from .py extension. Deny additions including staged A and additions committed after base, deletions, rename/copy both ends, type changes, untracked, sensitive case variants and unauthorized neighbors. Preserve hard deny for secret directories, actual credential stores/config, .env, private keys, cert/key and binary paths before any soft-name exception. No global authorization-first reorder, generic Python exception, new Decision schema, override flag or receipt. Keep Path A sensitive R3 risk floor and behavior unchanged; no exception in startup or clean-start policy. Preserve ordinary authorized nonsensitive additions and generated-governance nonstageable semantics. Only validated Path-B readiness caller may supply separately named verified source evidence to pure classifier, default empty.",
    "tests": "New test file must cover positive exact existing base/HEAD regular source M in both unstaged and staged states; missing/stale/invalid authority or preflight; broad glob; neighbors; untracked, staged A, committed-after-base addition, deletion, rename/copy both ends, symlink/type change, failed metadata lookup, hard secret/config/key/binary and case variants; unchanged Path A and ordinary additions/gates behavior. Include real production worktree-publication-readiness in isolated synthetic Git repositories with test-only approved fixture Decision/preflight and regular source metadata. Never modify user repository/Issue989 to fabricate readiness; no real secret content reads.",
    "completion_boundary": "Provider-free exact-head source acceptance and one Draft only. Preserve Issue989 Decision and five-file patch byte-for-byte. No staging/commit/transfer of that patch, no runtime repair or restart, model/system task/OAuth/browser execution, merge/Ready or Issue closure. Later Issue989 successor requires fresh base and authority after separately controlled landing."
  },
  "concurrent_work_preservation": {
    "981": "849af4ae2039bb7d30ebb442404a567e5c7152f2",
    "979": "73128ceac2d3efcab53e8e2964033da53143af2b",
    "978": "d4a227e63347972f3f3bfd3cea27fa7abb0f3222",
    "987": "2d5c2b1a5dd54320a1bfb3866eb2c513ad53a7c9",
    "policy": "Preserve all named heads, Issue988 failed task/worktree and Issue989 activation, Decision and five-file patch byte-for-byte. No import, cherry-pick, cleanup, staging, closure or mutation. PR979 task_service.py and tests remain untouched. No runtime or product behavior changes beyond approved governance classifier/readiness.",
    "988_local": "6e9f156a543293f37abc19a2dba6bc7b7364a852",
    "989_local": "ad18e253183fdf0d4e10f3f6e2c2054af0e22332",
    "989_decision_sha256": "2284442de5130cd3f2e570d61c0931b9247433df4d90648f41f83bb1782b9ac3"
  },
  "reference_paths": [
    "AGENTS.md",
    "docs/agents/governance-reference.md",
    "reverse_agent/control_plane/path_a.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_decision_preflight.py"
  ],
  "runtime_scratch_policy": {
    "paths": [
      "**/__pycache__/**",
      ".pytest_cache/**"
    ],
    "stage_allowed": false,
    "note": "Only disposable synthetic test repositories/fixtures and external evidence under F:/Nerelan-final-audit-evidence-20260911. Existing runtime, settings, Issue988/989 worktrees and old artifacts are untouched; no cleanup."
  },
  "required_provider_free_checks": [
    "python -m pytest tests/test_worktree_source_policy.py -q",
    "python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py -q",
    "python -m pytest tests/test_control_plane_transition.py tests/test_decision_preflight.py -q",
    "git diff --check"
  ],
  "allowed_commands": [
    {
      "command_id": "issue990v1.bootstrap",
      "command": "After fresh exact main/base and concurrent ownership observation, create F:/Nerelan-issue990-worktree-source-policy on codex/worktree-source-policy-r2-v1-20260923 from exact 58d4068f43ca4914b122445685cae410a8fa156e. Commit only approved Decision once, then sequential startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre and worktree-publication-readiness. Require PRE_EXECUTION_AUTHORIZED and PUBLICATION_READY before product edits. Preserve activated Decision and never commit generated gates.",
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
      "command_id": "issue990v1.implement",
      "command": "Supervisor edits only worktree_state.py, project_gate.py and new tests/test_worktree_source_policy.py under exact semantic contract. Integrate the narrow reviewed source exception only in fully validated Path-B readiness; unchanged startup uses prior valid cached clean startup snapshot, with no exception. Test actual readiness using isolated synthetic Git fixtures, never Issue989. Existing regression suites are read-only. No runtime/model/OAuth/browser/credential/install operations or remote network.",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "user_local",
      "operations": [
        "code_read",
        "source_edit",
        "machine_specific_execution"
      ],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/worktree_state.py",
        "reverse_agent/project_gate.py",
        "tests/test_worktree_source_policy.py"
      ],
      "produced_artifacts": []
    },
    {
      "command_id": "issue990v1.validate",
      "command": "At most eight provider-free development check rounds before one frozen product commit using: python -m pytest tests/test_worktree_source_policy.py -q; python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_decision_preflight.py -q; git diff --check. Test-owned loopback only if required by existing tests; no live endpoints or provider calls. After development success and canonical pre-stage readiness using valid cached clean-start snapshot, stage only the three approved product paths and commit once. Run all listed mandatory commands once on that exact head, plus git diff --check 58d4068f43ca4914b122445685cae410a8fa156e HEAD and sequential startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, worktree-publication-readiness on the clean committed head. Mandatory failure stops publication; no fix-forward, rerun or extra commit.",
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
        "commit",
        "command_plan_generation",
        "machine_specific_execution",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "reverse_agent/control_plane/worktree_state.py",
        "reverse_agent/project_gate.py",
        "tests/test_worktree_source_policy.py"
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
      "command_id": "issue990v1.publish",
      "command": "Only after exact mandatory checks, PUBLICATION_READY and independent exact-head implementation acceptance, re-observe locked main and concurrent ownership. Publish identical local Decision plus product blob/tree/commit graph via canonical GitHub Git API to codex/worktree-source-policy-r2-v1-20260923, verify all SHAs and create one exact-head Draft against main. Complete base-to-head delta limited to Decision and three approved product paths; no generated gates. No local git push, semantic remote edits, refs except the one exact approved branch, Ready/merge, issue closure, history rewrite, dispatch/rerun or other publication.",
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
      "command_id": "issue990v1.natural_checks",
      "command": "Require unchanged applicable exact-head natural CI, Decision Preflight, State Gate and Model Access workflows; actual full CI exit0/native JUnit zero failures/errors. Verify precise triggers and run head/event/attempt. No workflow changes, reruns or dispatch, no custom CI bypass. Existing CI-only dependency setup stays unchanged; no local install.",
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
      "command_id": "issue990v1.audit",
      "command": "Read canonical main/base/head, Issue990, immutable Decision and natural exact-head artifacts. Independently audit source exception, actual synthetic-repository readiness evidence and negative guard regressions; require frozen Issue989 patch hashes and named concurrent heads unchanged. Keep Draft; do not claim runtime repair, system implementation, live authentication, UI or overall completion.",
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
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
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
      "Require unchanged applicable exact-head natural CI, Decision Preflight, State Gate and Model Access workflows; actual full CI exit0/native JUnit zero failures/errors. Verify precise triggers and run head/event/attempt. No workflow changes, reruns or dispatch, no custom CI bypass. Existing CI-only dependency setup stays unchanged; no local install."
    ],
    "trusted_worker_network_exceptions": [],
    "user_local_network_exceptions": [
      "At most eight provider-free development check rounds before one frozen product commit using: python -m pytest tests/test_worktree_source_policy.py -q; python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py -q; python -m pytest tests/test_control_plane_transition.py tests/test_decision_preflight.py -q; git diff --check. Test-owned loopback only if required by existing tests; no live endpoints or provider calls. After development success and canonical pre-stage readiness using valid cached clean-start snapshot, stage only the three approved product paths and commit once. Run all listed mandatory commands once on that exact head, plus git diff --check 58d4068f43ca4914b122445685cae410a8fa156e HEAD and sequential startup-snapshot, transition-command-plan, transition-lint, transition-preflight --mode pre, worktree-publication-readiness on the clean committed head. Mandatory failure stops publication; no fix-forward, rerun or extra commit."
    ],
    "github_control_plane_network_exceptions": [
      "Only after exact mandatory checks, PUBLICATION_READY and independent exact-head implementation acceptance, re-observe locked main and concurrent ownership. Publish identical local Decision plus product blob/tree/commit graph via canonical GitHub Git API to codex/worktree-source-policy-r2-v1-20260923, verify all SHAs and create one exact-head Draft against main. Complete base-to-head delta limited to Decision and three approved product paths; no generated gates. No local git push, semantic remote edits, refs except the one exact approved branch, Ready/merge, issue closure, history rewrite, dispatch/rerun or other publication."
    ]
  },
  "provider_free_network_boundaries": "user_local validate network exception permits test-owned loopback only; all non-loopback provider/model access forbidden. Canonical GitHub read-only observations use remote_observation. Publication limited to exact approved Draft graph. No runtime endpoints or user configuration mutations."
}
```
