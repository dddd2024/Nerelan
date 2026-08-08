# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_pr132_opencode_backend_landing_v5",
  "round_id": "round_20260808_pr132_opencode_backend_landing_v5",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue127_opencode_vertical_slice_v4",
  "follows_last_round_id": "round_20260808_issue127_opencode_vertical_slice_v4",
  "previous_audit_outcome": "ISSUE127_V4_EXACT_HEAD_BACKEND_SLICE_ACCEPTED",
  "workstream_id": "pr132-opencode-backend-landing-v5",
  "source_issue": 127,
  "parent_issue": 90,
  "active_pr": 132,
  "required_branch": "owner/issue127-opencode-vertical-slice-v1",
  "starting_head": "e103fc53bd985375f0513c0369eb9dcc18510004",
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
      "command_id": "sync.fetch_pr132_branch",
      "command": "git fetch origin owner/issue127-opencode-vertical-slice-v1",
      "phase": "bootstrap",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
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

PR #132 v5 is the governance-only landing round for the accepted Issue #127 OpenCode backend slice. Product implementation head `e103fc53bd985375f0513c0369eb9dcc18510004` has passed Owner exact-head static audit and a clean detached exact-head local runtime acceptance using OpenCode CLI 1.18.15 with `sensetime/sensenova-6.7-flash-lite`.

The product tree is now frozen for landing. This round authorizes no product, frontend, test, workflow, documentation, package, executor, or model/provider mutation.

The only known remaining failures before landing are the mainline-landing governance checks caused by `project_state/mainline_merge_intents/active.json` still binding completed PR #129 / `decision_20260807_pr129_provider_free_task_plane_landing_v5` instead of this PR #132 landing authority.

This v5 Decision authorizes ONLY:
1. this v5 Decision committed first;
2. standard transition gate generation against this Decision;
3. current PR129 v5 active intent archived byte-for-byte to `project_state/mainline_merge_intents/archive/pr129_v5.json` before active intent modification;
4. new active intent bound to this committed Decision and the generated v5 command plan, with `source_pr=132`, `locked_base_sha=e4e23028c6c78c4ab9a8e032677e71370ace7627`, and merge method `merge`;
5. validation of the resulting exact governance head and normal push of the implementation branch.

Owner retains PR comment, Ready and merge actions. The local executor must not perform them.

## Acceptance

1. This Decision commit must precede gate generation and merge-intent mutation.
2. Accepted product head `e103fc53bd985375f0513c0369eb9dcc18510004` remains an immutable ancestor and no product/test/runtime file changes after it.
3. Current PR129 active intent is archived byte-for-byte to `project_state/mainline_merge_intents/archive/pr129_v5.json` before modification.
4. Standard transition sequence reports `transition-lint: PASS` and `transition-preflight: PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
5. New active intent binds exactly: `source_pr=132`, `decision_id=decision_20260808_pr132_opencode_backend_landing_v5`, `locked_base_sha=e4e23028c6c78c4ab9a8e032677e71370ace7627`, `allowed_merge_method=merge`, and the exact SHA-256 of this Decision content and generated command plan.
6. Required workflows in active intent are `[CI, Decision Preflight, State Gate (pull_request), State Gate (push)]`.
7. `python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q` passes.
8. `python -m pytest tests/platform_v1 -q` passes with zero failures; the prior 12 landing-governance failures must disappear without test modification.
9. `python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q` passes.
10. `git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD` passes.
11. `git diff --name-only e103fc53bd985375f0513c0369eb9dcc18510004..HEAD` contains only the 8 allowed governance paths.
12. No product code, frontend, tests, workflows, docs, package files, provider configuration or runtime model calls occur.
13. Codex runtime calls = 0, OpenHands runtime calls = 0, OpenCode/model/provider runtime calls = 0 in the landing round.
14. Branch is pushed normally; no force push, rebase, squash, main push, release or deploy.

```text
PR132_V5_LANDING_GOVERNANCE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- This v5 landing Decision follows the accepted Issue #127 v4 engineering Decision only for PR #132 final landing authority.
- v4 product Decision and exact-head evidence remain historical immutable acceptance evidence.
- Run the standard Path-B transition gate sequence before modifying the active merge intent.
- Archive the old intent byte-for-byte; do not rewrite the archived content.
- The new active intent must be derived from the actual committed Decision and generated command plan hashes, never guessed or copied from prior rounds.
- `mainline` remains `engineering_branch` to satisfy the existing landing contract.
- Owner-only permissions (`pr_comment_allowed`, `mark_ready_allowed`, `merge_allowed`) authorize the remote Owner after exact-head checks; the local Agent must not exercise them.
- No real provider credentials, OpenCode, Codex, OpenHands, model execution, live provider probe or external tool execution is authorized in the landing round.
