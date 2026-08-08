# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_pr132_opencode_backend_landing_v6",
  "round_id": "round_20260808_pr132_opencode_backend_landing_v6",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_pr132_opencode_backend_landing_v5",
  "follows_last_round_id": "round_20260808_pr132_opencode_backend_landing_v5",
  "previous_audit_outcome": "PR132_V5_SUPERSEDED_PREEXECUTION_BOOTSTRAP_SYNC_COMMAND_OMISSION",
  "workstream_id": "pr132-opencode-backend-landing-v6",
  "source_issue": 127,
  "parent_issue": 90,
  "active_pr": 132,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "aa3da225f6da45232fa550ed6fc660442788f88a",
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

PR #132 v6 supersedes v5 before any local gate generation or merge-intent mutation. v5 correctly established the PR-bound landing authority but omitted the explicit fast-forward bootstrap command needed to move a clean local implementation branch from the accepted product head to the Owner-committed landing Decision.

No v5 local execution occurred. No v5 gate generation, active-intent mutation, product mutation, PR publication action, merge, model call, release or deploy occurred.

Accepted product head remains:

```text
e103fc53bd985375f0513c0369eb9dcc18510004
```

The product tree is frozen. This v6 round is governance-only and differs from v5 only by explicitly authorizing the bounded branch fast-forward bootstrap needed after fetching the Owner Decision.

After the local branch is fast-forwarded to the current remote Decision, the round authorizes only:
1. standard transition gate generation against this v6 Decision;
2. current PR129 v5 active intent archived byte-for-byte to `project_state/mainline_merge_intents/archive/pr129_v5.json`;
3. new active intent bound to this committed v6 Decision and generated v6 command plan, with `source_pr=132`, `locked_base_sha=e4e23028c6c78c4ab9a8e032677e71370ace7627`, and merge method `merge`;
4. governance-only validation and normal push.

Owner retains PR comments, Ready and merge actions.

## Acceptance

1. Fetch the implementation branch, inspect the remote v6 Decision, and use only `git merge --ff-only origin/owner/issue127-opencode-vertical-slice-v1` to synchronize the clean local branch. No rebase/reset/force behavior.
2. v6 Decision commit precedes all gate generation and merge-intent mutation.
3. Accepted product head `e103fc53bd985375f0513c0369eb9dcc18510004` remains an immutable ancestor; no product/test/runtime file changes after it.
4. Gate sequence reports `transition-lint: PASS` and `transition-preflight: PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
5. Current PR129 active intent is archived byte-for-byte to `project_state/mainline_merge_intents/archive/pr129_v5.json` before active modification.
6. New active intent binds exactly: `source_pr=132`, `decision_id=decision_20260808_pr132_opencode_backend_landing_v6`, `locked_base_sha=e4e23028c6c78c4ab9a8e032677e71370ace7627`, `allowed_merge_method=merge`, and the exact SHA-256 of this Decision content and generated command plan.
7. Required workflows are `[CI, Decision Preflight, State Gate (pull_request), State Gate (push)]`.
8. `python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q` passes.
9. `python -m pytest tests/platform_v1 -q` passes with zero failures; the prior landing-governance failures disappear without test modification.
10. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
11. `git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD` passes.
12. `git diff --name-only e103fc53bd985375f0513c0369eb9dcc18510004..HEAD` contains only the 8 authorized governance paths.
13. No product code, frontend, tests, workflows, docs, package, provider configuration or runtime model changes/calls.
14. Codex calls = 0, OpenHands calls = 0, OpenCode/model/provider calls = 0 in this landing round.
15. Normal branch push only; no force push, rebase, squash, main push, release or deploy.

```text
PR132_V6_LANDING_GOVERNANCE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- v5 is superseded pre-execution solely because its bootstrap command list omitted the explicit local fast-forward sync needed to obtain the already-committed Owner authority.
- The remote v6 Decision may be read from `origin/owner/issue127-opencode-vertical-slice-v1` immediately after the authorized fetch, before the fast-forward command is executed.
- The only history synchronization operation authorized is `git merge --ff-only origin/owner/issue127-opencode-vertical-slice-v1`; no rebase, force update, reset, squash or history rewrite.
- v4 product Decision/evidence and product head `e103fc53...` remain immutable historical acceptance evidence.
- Archive the old merge intent byte-for-byte and derive new hashes from actual committed files after gate generation; never guess them.
- Owner-only permissions (`pr_comment_allowed`, `mark_ready_allowed`, `merge_allowed`) are not delegated to the local Agent.
- No OpenCode, Codex, OpenHands, provider/model, credential, external binary, release or deployment action is authorized.
