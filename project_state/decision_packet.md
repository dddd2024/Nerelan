# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
  "round_id": "round_20260808_pr134_frontend_opencode_devup_landing_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue133_frontend_opencode_devup_v4",
  "follows_last_round_id": "round_20260808_issue133_frontend_opencode_devup_v4",
  "previous_audit_outcome": "ISSUE133_V4_LOCAL_ACCEPTANCE_READY_FOR_OWNER_LANDING",
  "workstream_id": "pr134-frontend-opencode-devup-landing-v1",
  "source_issue": 133,
  "parent_issue": 127,
  "active_pr": 134,
  "required_branch": "owner/issue133-frontend-opencode-devup-v1",
  "starting_head": "f6c9bad0cfad9f380a917f1a8f8c14eb58a52466",
  "activation_base_sha": "a1d09d4ae8887405721efe9871881db788c5820a",
  "accepted_product_head": "f6c9bad0cfad9f380a917f1a8f8c14eb58a52466",
  "allowed_merge_method": "merge",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
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
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git status --short",
    "git fetch origin main",
    "git fetch origin owner/issue133-frontend-opencode-devup-v1",
    "git show origin/owner/issue133-frontend-opencode-devup-v1:project_state/decision_packet.md",
    "git switch owner/issue133-frontend-opencode-devup-v1",
    "git merge --ff-only origin/owner/issue133-frontend-opencode-devup-v1",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
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
      "command_id": "sync.fetch_main",
      "command": "git fetch origin main",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "sync.fetch_pr134_branch",
      "command": "git fetch origin owner/issue133-frontend-opencode-devup-v1",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "sync.inspect_remote_decision",
      "command": "git show origin/owner/issue133-frontend-opencode-devup-v1:project_state/decision_packet.md",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.switch_branch",
      "command": "git switch owner/issue133-frontend-opencode-devup-v1",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.fast_forward_pr134_branch",
      "command": "git merge --ff-only origin/owner/issue133-frontend-opencode-devup-v1",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
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
      "command_id": "observation.git_main",
      "command": "git rev-parse origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.merge_base",
      "command": "git merge-base HEAD origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.active_intent_hash_before",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'project_state/mainline_merge_intents/active.json').Hash.ToLower()\"",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "mutation.archive_pr132_intent",
      "command": "powershell -NoProfile -Command \"Copy-Item 'project_state/mainline_merge_intents/active.json' 'project_state/mainline_merge_intents/archive/pr132_v7.json'\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/mainline_merge_intents/archive/pr132_v7.json"]
    },
    {
      "command_id": "observation.archive_hash_after",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'project_state/mainline_merge_intents/archive/pr132_v7.json').Hash.ToLower()\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.decision_sha256",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'project_state/decision_packet.md').Hash.ToLower()\"",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.command_plan_sha256",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'project_state/gates/command_plan.json').Hash.ToLower()\"",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.mainline_landing",
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
      "command_id": "test.platform_v1",
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
      "command_id": "test.gate_regression",
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
      "command_id": "validation.diff_check",
      "command": "git diff --check a1d09d4ae8887405721efe9871881db788c5820a..HEAD",
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
      "command": "git diff --name-only f6c9bad0cfad9f380a917f1a8f8c14eb58a52466..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/issue133-frontend-opencode-devup-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
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
    "project_state/mainline_merge_intents/archive/pr132_v7.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/mainline_landing.py",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py",
    "tests/test_mainline_landing.py",
    "tests/test_integration_baseline.py",
    "tests/test_project_audits.py",
    "tests/platform_v1/**",
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
    ".github/**",
    "frontend/**",
    "docs/**",
    "reverse_agent/**",
    "tests/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
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
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "create_pr",
    "pr_creation",
    "draft_pr_creation",
    "pr_body_update",
    "reset_hard",
    "git_clean"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "mark_ready_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue133-frontend-opencode-devup-v1",
      "git push origin owner/issue133-frontend-opencode-devup-v1",
      "gh pr view 134 --repo dddd2024/reverse-agent",
      "gh pr checks 134 --repo dddd2024/reverse-agent"
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

PR #134 v1 is the governance-only landing authority for the already accepted frontend OpenCode cutover and one-click development stack. The product/runtime head is frozen at:

```text
f6c9bad0cfad9f380a917f1a8f8c14eb58a52466
```

Owner remote audit and local Windows/OpenCode acceptance have both completed. The accepted runtime evidence proves one real OpenCode/SenseNova task reached `READY_FOR_REVIEW`, created only `issue133_gui_v4_acceptance.txt` in the Executor-owned linked worktree, returned validation exit 0 with ExecutorAction/git_diff_check evidence, kept the clean exact-head source worktree unchanged, closed ports 4173/8765/8766 on two dev-up/dev-down cycles, and performed exactly one model task with Codex=0, OpenHands=0, no fixture fallback, no credential exposure, no package install, and no provider mutation.

The prior PR-triggered product-head CI failed only the two expected stale mainline-intent tests:

```text
tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority
tests/test_mainline_landing.py::test_production_pre_merge_simulation
```

All other exact-head engineering checks are accepted:

```text
Model Access      SUCCESS
Decision Preflight SUCCESS
State Gate         SUCCESS
```

After synchronizing to this Owner Decision and obtaining `PRE_EXECUTION_AUTHORIZED`, the landing round may only:
1. record the SHA-256 of the current PR132 active intent;
2. archive that exact file byte-for-byte to `project_state/mainline_merge_intents/archive/pr132_v7.json` and prove the archive SHA-256 equals the pre-copy hash;
3. calculate SHA-256 of the committed landing Decision and generated landing command plan;
4. replace `active.json` with the exact PR134 landing intent using those observed hashes;
5. run landing/platform/gate validation, diff/path checks, commit only the eight governance paths, and normal-push.

The new active intent must use:

```json
{
  "schema_version": 1,
  "intent_id": "pr134_frontend_opencode_devup_landing_v1",
  "repository": "dddd2024/reverse-agent",
  "source_pr": 134,
  "locked_base_sha": "a1d09d4ae8887405721efe9871881db788c5820a",
  "allowed_merge_method": "merge",
  "decision_identity": {
    "decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
    "decision_content_sha256": "<OBSERVED_DECISION_SHA256>"
  },
  "command_plan_sha256": "<OBSERVED_COMMAND_PLAN_SHA256>",
  "merge_tree_policy": "equal_to_accepted_head_tree",
  "required_workflows": [
    "CI",
    "Decision Preflight",
    "State Gate (pull_request)",
    "State Gate (push)"
  ],
  "expires_at": "2026-08-15T23:59:59Z"
}
```

## Acceptance

1. Remote branch must fast-forward to the Decision commit; preserve unknown untracked files.
2. Landing Decision commit precedes all landing gate generation and merge-intent mutation.
3. Standard transition sequence: transition-command-plan PASS, transition-lint PASS, transition-preflight `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`.
4. PR132 active-intent SHA before copy exactly equals `archive/pr132_v7.json` SHA after copy.
5. PR134 active intent contains observed, not guessed, SHA-256 values for the exact committed landing Decision and generated landing command plan.
6. `f6c9bad0...` remains ancestor and no product/test/runtime/frontend/workflow/doc/package file changes occur after that accepted product head.
7. Landing/integration/audit tests pass with zero failures.
8. `tests/platform_v1` passes with zero failures; the two known landing-governance failures disappear without modifying tests.
9. project-gate/control-plane regression tests pass.
10. `git diff --check a1d09d4...HEAD` passes.
11. `git diff --name-only f6c9bad0...HEAD` contains only the eight authorized governance paths.
12. No model/provider/runtime execution. OpenCode=0, Codex=0, OpenHands=0.
13. Normal push only. No rebase, reset, clean, force push, squash, main push, Ready, merge, release or deploy by local Agent.

```text
PR134_LANDING_GOVERNANCE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- This Decision is the only active local landing authority; issue133 v4 is complete and superseded for further execution.
- Do not modify `active.json` until preflight authorizes execution and the old active intent has been hashed and archived.
- Archive must be byte-for-byte identical; hash mismatch is a hard stop.
- Do not guess or hand-copy Decision/command-plan digests; use the authorized `Get-FileHash` commands on committed/generated files.
- Product head `f6c9bad0...` is immutable for landing; any post-product change outside the eight governance paths is a hard stop.
- Owner-only PR comment/Ready/merge permissions are not delegated to the local Agent.
- No OpenCode, Codex, OpenHands, provider/model, credential, release or deployment action is authorized.
