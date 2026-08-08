# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_pr132_opencode_backend_landing_v7",
  "round_id": "round_20260808_pr132_opencode_backend_landing_v7",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_pr132_opencode_backend_landing_v6",
  "follows_last_round_id": "round_20260808_pr132_opencode_backend_landing_v6",
  "previous_audit_outcome": "PR132_V6_SUPERSEDED_PREEXECUTION_LANDING_UTILITY_COMMANDS_OMISSION",
  "workstream_id": "pr132-opencode-backend-landing-v7",
  "source_issue": 127,
  "parent_issue": 90,
  "active_pr": 132,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "e9e801d8150303c8c8d973b0425a30fbd40a541c",
  "activation_base_sha": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
  "accepted_product_head": "e103fc53bd985375f0513c0369eb9dcc18510004",
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
    "git fetch origin owner/issue127-opencode-vertical-slice-v1",
    "git show origin/owner/issue127-opencode-vertical-slice-v1:project_state/decision_packet.md",
    "git merge --ff-only origin/owner/issue127-opencode-vertical-slice-v1",
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
      "command_id": "sync.fetch_pr132_branch",
      "command": "git fetch origin owner/issue127-opencode-vertical-slice-v1",
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
      "command": "git show origin/owner/issue127-opencode-vertical-slice-v1:project_state/decision_packet.md",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.fast_forward_pr132_branch",
      "command": "git merge --ff-only origin/owner/issue127-opencode-vertical-slice-v1",
      "phase": "bootstrap",
      "required": false,
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
      "command_id": "observation.merge_base",
      "command": "git merge-base origin/main owner/issue127-opencode-vertical-slice-v1",
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
      "command_id": "mutation.archive_pr129_intent",
      "command": "powershell -NoProfile -Command \"Copy-Item 'project_state/mainline_merge_intents/active.json' 'project_state/mainline_merge_intents/archive/pr129_v5.json'\"",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["governance_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/mainline_merge_intents/archive/pr129_v5.json"]
    },
    {
      "command_id": "observation.archive_hash_after",
      "command": "powershell -NoProfile -Command \"(Get-FileHash -Algorithm SHA256 'project_state/mainline_merge_intents/archive/pr129_v5.json').Hash.ToLower()\"",
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
      "command": "git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD",
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
      "command": "git diff --name-only e103fc53bd985375f0513c0369eb9dcc18510004..HEAD",
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
      "command": "git push origin owner/issue127-opencode-vertical-slice-v1",
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
    "project_state/mainline_merge_intents/archive/pr129_v5.json"
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
      "git fetch origin owner/issue127-opencode-vertical-slice-v1",
      "git push origin owner/issue127-opencode-vertical-slice-v1",
      "gh pr view 132 --repo dddd2024/reverse-agent",
      "gh pr checks 132 --repo dddd2024/reverse-agent"
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

PR #132 v7 is the final governance-only landing authority. It supersedes v5 and v6 before any local landing execution. v5 introduced the PR-bound R2 authority; v6 added explicit fast-forward bootstrap; v7 additionally makes remote Decision inspection, old-intent hashing/archive, and exact Decision/command-plan hash calculation first-class deterministic commands so the active intent can be derived without guessed values.

No v5/v6 local gate generation or merge-intent mutation occurred. Accepted product head remains frozen at:

```text
e103fc53bd985375f0513c0369eb9dcc18510004
```

The prior PR-triggered product-head CI failed only the two expected stale mainline-intent tests:

```text
tests/test_mainline_landing.py::test_committed_active_intent_binds_exact_current_authority
tests/test_mainline_landing.py::test_production_pre_merge_simulation
```

All earlier CI steps passed; Decision Preflight and State Gate succeeded on the accepted product head.

After synchronizing to this Owner Decision and obtaining `PRE_EXECUTION_AUTHORIZED`, the landing round may only:
1. record the SHA-256 of the current PR129 active intent;
2. archive that exact file byte-for-byte to `project_state/mainline_merge_intents/archive/pr129_v5.json` and prove the archive SHA-256 equals the pre-copy hash;
3. calculate SHA-256 of the committed v7 Decision and generated v7 command plan;
4. replace `active.json` with the exact PR132 v7 intent using those observed hashes;
5. run landing/platform/gate validation, diff/path checks, commit only the eight governance paths, and normal-push.

The new active intent must use:

```json
{
  "schema_version": 1,
  "intent_id": "pr132_opencode_backend_landing_v7",
  "repository": "dddd2024/reverse-agent",
  "source_pr": 132,
  "locked_base_sha": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
  "allowed_merge_method": "merge",
  "decision_identity": {
    "decision_id": "decision_20260808_pr132_opencode_backend_landing_v7",
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

1. `git fetch` + remote Decision inspection + only `git merge --ff-only` for local synchronization; preserve unknown untracked files.
2. v7 Decision commit precedes all v7 gate generation and merge-intent mutation.
3. Standard transition sequence: transition-command-plan PASS, transition-lint PASS, transition-preflight `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`.
4. PR129 active-intent SHA before copy exactly equals `archive/pr129_v5.json` SHA after copy.
5. PR132 active intent contains observed, not guessed, SHA-256 values for the exact committed Decision and generated command plan.
6. Accepted product head remains ancestor and no product/test/runtime/frontend/workflow/doc/package file changes after it.
7. Landing/integration/audit tests pass with zero failures.
8. `tests/platform_v1` passes with zero failures; the known landing-governance failures disappear without modifying tests.
9. project-gate/control-plane regression tests pass.
10. `git diff --check e4e23028...HEAD` passes.
11. `git diff --name-only e103fc53...HEAD` contains only the 8 authorized governance paths.
12. No model/provider/runtime execution. OpenCode=0, Codex=0, OpenHands=0.
13. Normal push only. No rebase, reset, clean, force push, squash, main push, Ready, merge, release or deploy by local Agent.

```text
PR132_V7_LANDING_GOVERNANCE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- v7 is the only active local landing authority; v5/v6 are superseded pre-execution.
- The remote v7 Decision may be read immediately after the authorized fetch before fast-forwarding the local branch.
- Do not modify `active.json` until preflight authorizes execution and the old active intent has been hashed and archived.
- Archive must be byte-for-byte identical; hash mismatch is a hard stop.
- Do not guess or hand-copy Decision/command-plan digests; use the authorized `Get-FileHash` commands on committed/generated files.
- Product head `e103fc53...` is immutable for landing; any post-product change outside the eight governance paths is a hard stop.
- Owner-only PR comment/Ready/merge permissions are not delegated to the local Agent.
- No OpenCode, Codex, OpenHands, provider/model, credential, release or deployment action is authorized.
