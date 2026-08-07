# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_pr121_final_owner_authority_v4",
  "round_id": "round_20260807_pr121_final_owner_authority_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr121_model_access_final_land_v3",
  "follows_last_round_id": "round_20260807_pr121_model_access_final_land_v3",
  "previous_audit_outcome": "PR121_AUTH_001_V3_AUTHORITY_CONTRADICTION",
  "workstream_id": "pr121-final-owner-authority-v4",
  "source_issue": 122,
  "parent_issue": 90,
  "selected_foundation_issue": 120,
  "backend_reference_pr": 120,
  "active_pr": 121,
  "required_branch": "owner/model-access-frontend-closeout-v1",
  "starting_head": "887c58614a5dee7ba3e2b5f9c170ea87f7915943",
  "activation_base_sha": "5de53389a3cf0a6557f2a0bb837eee4a5d5687fe",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "model_execution_required": false,
  "bounded_external_source_access_allowed": false,
  "frontend_dependency_installation_allowed": true,
  "loopback_frontend_runtime_allowed": true,
  "repair_attempt_limit": 2,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_COMPLETE",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "git status --short",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "observation.git_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.merge_base",
      "command": "git merge-base origin/main owner/model-access-frontend-closeout-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.model_access_pytest",
      "command": "python -m pytest tests/test_model_access.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.path_list",
      "command": "git diff --name-only origin/main...HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.integration_suite",
      "command": "python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.platform_v1",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.gate_test",
      "command": "python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/model-access-frontend-closeout-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "owner.attestation",
      "command": "gh pr comment 121 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "owner_only"
    },
    {
      "command_id": "owner.mark_ready",
      "command": "gh pr ready 121 --repo dddd2024/reverse-agent",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["mark_ready", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "owner_only"
    },
    {
      "command_id": "owner.expected_head_merge",
      "command": "gh pr merge 121 --repo dddd2024/reverse-agent --merge --match-head-commit <EXPECTED_HEAD>",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["merge", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "owner_only"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/**",
    "tests/platform_v1/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_mainline_landing.py",
    "tests/platform_v1/test_merge_intent.py",
    "project_state/schemas/**"
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
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/workflows/**",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/model_access/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_architecture_contracts.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_risk_classifier.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_mainline_landing.py",
    "tests/test_model_access.py",
    "frontend/**",
    "docs/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "pr_114_changes",
    "platform_v1_fresh_port",
    "openhands_integration",
    "provider_expansion",
    "real_provider_probe",
    "live_provider_test",
    "reset_hard",
    "git_clean",
    "issue_126_experiment_before_pr121_landing"
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
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push origin owner/model-access-frontend-closeout-v1",
      "gh pr view 121 --repo dddd2024/reverse-agent",
      "gh pr checks 121 --repo dddd2024/reverse-agent"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

PR #121 v4 final Owner authority fix-forward. The v3 Decision (`decision_20260807_pr121_model_access_final_land_v3`) correctly set `mainline=engineering_branch` and `merge_allowed=true`, `mark_ready_allowed=true`. However, it contained an authority contradiction identified as **PR121-AUTH-001**:

1. `pr_comment_allowed=false` — blocks the Owner attestation PR comment on PR #121
2. `mark_ready` appears in `forbidden_operations` despite `mark_ready_allowed=true`

With these two issues, the Owner landing sequence has no unambiguous authority:

```
Owner attestation → Ready → merge
```

This v4 Decision fixes the authority to be internally consistent:

1. Set `pr_comment_allowed=true` to authorize a single Owner attestation PR comment
2. Remove `mark_ready` from `forbidden_operations` to match `mark_ready_allowed=true`
3. Explicitly document Owner attestation, mark Ready, and expected-head merge as optional Owner-only commands
4. Bind v4 to the current branch HEAD (`887c58614a5dee7ba3e2b5f9c170ea87f7915943`)

No new product functionality is introduced in this round.

## Acceptance

1. v4 Decision commit is authored before any gate generation or intent modification.
2. Current v3 active intent archived byte-for-byte as `archive/pr121_v3.json` before modification.
3. Historical archives `archive/pr112_v6.json` and `archive/pr121_v2.json` remain unchanged.
4. Active intent updated to bind v4 Decision, v4 command plan, `source_pr=121`, `locked_base_sha=5de53389a3cf0a6557f2a0bb837eee4a5d5687fe`, `allowed_merge_method=merge`.
5. `pr_comment_allowed=true`, `mark_ready_allowed=true`, `merge_allowed=true`, `auto_merge_allowed=false`.
6. `forbidden_operations` does not contain `mark_ready` or `merge`.
7. Gate sequence reports `transition-lint: PASS`, `transition-preflight: PRE_EXECUTION_AUTHORIZED`.
8. `python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q` passes.
9. `python -m pytest tests/platform_v1 -q` passes.
10. `python -m pytest tests/test_model_access.py -q` passes.
11. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
12. `git diff --check` passes.
13. `reverse_agent/mainline_landing.py` is NOT modified.
14. No product code, workflow, or test fixture modifications.
15. Owner commands documented in Decision but NOT executed by the local Agent.
16. No main push, merge PR, history rewrite, tag, release, real provider probe, deployment, credential access, or unrelated PR work occurs.

```text
PR121_V4_FINAL_OWNER_AUTHORITY_READY_FOR_REMOTE_AUDIT
```

## Execution policy

- This v4 Decision follows and supersedes the v3 Decision for PR #121 final Owner landing authority only.
- The v3 Decision (`decision_20260807_pr121_model_access_final_land_v3`) is immutable and preserved as the historical baseline for the v3 governance closeout window.
- Run the standard Path-B gate sequence: transition-lint, transition-command-plan, transition-preflight (pre), before any intent modification.
- `mainline` must be `engineering_branch` to satisfy the canonical mainline landing contract.
- `pr_comment_allowed=true` authorizes a single Owner attestation PR comment on PR #121, bound to the exact accepted head, locked base, Decision ID/digest, command-plan digest, and required workflow run IDs/results.
- `mark_ready_allowed=true` with `mark_ready` removed from `forbidden_operations` authorizes the Owner to mark PR #121 ready, optional and only after all required exact-head workflows PASS, Owner attestation exists, head unchanged, mergeable, and no unresolved review threads.
- `merge_allowed=true` authorizes the Owner to merge PR #121 using method=merge with `--match-head-commit <EXPECTED_HEAD>`. Squash, rebase, and auto-merge are prohibited.
- `auto_merge_allowed=false` — no auto-merge.
- Owner commands are authorized for the repository Owner only. The local Agent must NOT execute `gh pr comment`, `gh pr ready`, or `gh pr merge`.
- Publication is limited to the exact branch and normal push.
- No real provider credentials, live provider probes, or model execution.
