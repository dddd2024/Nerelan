# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260804_issue111_pr112_bootstrap_v13_retry_v1",
  "round_id": "round_20260804_issue111_pr112_bootstrap_v13_retry_v1",
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
  "follows_last_decision_id": "decision_20260804_issue109_pr110_bootstrap_test_rebind_v1",
  "follows_last_round_id": "round_20260804_issue109_pr110_bootstrap_test_rebind_v1",
  "previous_audit_outcome": "PR106_V13_REJECTED_ACTIVE_BASE_ALIAS_LEAKED_INTO_HISTORICAL_ARCHIVES",
  "workstream_id": "issue111-pr106-bootstrap-v13-retry-v1",
  "source_issue": 111,
  "parent_issue": 90,
  "dependent_issue": 105,
  "dependent_pr": 106,
  "prior_bootstrap_issue": 109,
  "prior_bootstrap_pr": 110,
  "active_pr": 112,
  "required_branch": "owner/state-gate-bootstrap-v13-retry-v3",
  "starting_head": "34e4e7bf3bad770a4f58edf7cc3a12f108818dee",
  "activation_base_sha": "93984db182b7ee11b3ccb8795bb5fc3741205b92",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_work_item_publication_allowed": false,
  "trusted_host_live_probe_allowed": false,
  "repair_attempt_limit": 0,
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
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_control_plane_and_gate",
      "command": "python -m pytest tests/test_control_plane_transition.py tests/test_planning_and_github_adapters.py tests/test_project_gate.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_platform_v1_contracts_and_intent",
      "command": "python -m pytest tests/platform_v1/test_contracts.py tests/platform_v1/test_merge_intent.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_platform_v1_all",
      "command": "python -m pytest tests/platform_v1 -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_repository_hygiene_and_supervisor",
      "command": "python -m pytest tests/test_repository_hygiene.py tests/test_supervisor_validate.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.pytest_minimal_integration_baseline_docs",
      "command": "python -m pytest tests/test_minimal_integration_baseline_docs.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check 93984db182b7ee11b3ccb8795bb5fc3741205b92..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/state-gate-bootstrap-v13-retry-v3",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.pr_metadata",
      "command": "gh pr view 112 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.pr_checks",
      "command": "gh pr checks 112 --repo dddd2024/reverse-agent --watch",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.pr_edit",
      "command": "gh pr edit 112 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_body_update", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.pr_comment",
      "command": "gh pr comment 112 --repo dddd2024/reverse-agent --body-file -",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pr_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    ".github/workflows/state-gate.yml",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr110_v1.json",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/project_gate.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/platform_v1/contracts.py",
    "tests/test_control_plane_transition.py",
    "tests/test_planning_and_github_adapters.py",
    "tests/test_project_gate.py",
    "tests/test_repository_hygiene.py",
    "tests/test_supervisor_validate.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "project_state/mainline_merge_intents/archive/pr97_v1.json",
    "project_state/mainline_merge_intents/archive/pr97_v2.json",
    "project_state/mainline_merge_intents/archive/pr97_v3.json",
    "project_state/mainline_merge_intents/archive/pr97_v4.json",
    "project_state/mainline_merge_intents/archive/pr108_v1.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/ci.yml",
    ".github/workflows/decision-preflight.yml",
    "reverse_agent/**",
    "docs/**",
    "deploy/**",
    "examples/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/archive/pr97_v1.json",
    "project_state/mainline_merge_intents/archive/pr97_v2.json",
    "project_state/mainline_merge_intents/archive/pr97_v3.json",
    "project_state/mainline_merge_intents/archive/pr108_v1.json"
  ],
  "forbidden_operations": [
    "create a branch or pull request",
    "direct push to main",
    "mark ready",
    "merge",
    "auto merge",
    "force push",
    "rebase",
    "squash",
    "tag or release",
    "deployment",
    "credential access or publication",
    "Issue 102 execution",
    "Docker OpenHands Agent Canvas or Codex ACP execution",
    "shadow-audit generation or execution",
    "invoke a second model or nested agent",
    "runner dispatch",
    "unknown binary execution",
    "external reverse-tool invocation",
    "modify PR 106",
    "modify paths outside the exact eleven-path Bootstrap scope",
    "delete historical or negative assertions",
    "weaken digest or workflow validation",
    "fall back to an older successful workflow run"
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
    "local_network_exceptions": [
      "git push origin owner/state-gate-bootstrap-v13-retry-v3",
      "gh pr view 112 --repo dddd2024/reverse-agent --json number,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,autoMergeRequest,mergeable,mergeStateStatus,url",
      "gh pr checks 112 --repo dddd2024/reverse-agent --watch",
      "gh pr edit 112 --repo dddd2024/reverse-agent --body-file -",
      "gh pr comment 112 --repo dddd2024/reverse-agent --body-file -"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    ".github/workflows/state-gate.yml",
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr110_v1.json",
    "tests/platform_v1/test_contracts.py",
    "tests/platform_v1/test_merge_intent.py"
  ],
  "path_risk_floor": [
    {
      "pattern": ".github/workflows/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/mainline_merge_intents/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "tests/platform_v1/**",
      "minimum_risk": "R2"
    }
  ]
}
```

## Goal

Create the repository-backed Path-B authority for Issue #111 and Draft PR #112, then advance the trusted `pull_request_target` Bootstrap bridge so dependent Draft PR #106 can be reconstructed as v14 after the bounded v13 semantic-test failure. The round starts from reservation head `34e4e7bf3bad770a4f58edf7cc3a12f108818dee` on branch `owner/state-gate-bootstrap-v13-retry-v3` and base B2 `93984db182b7ee11b3ccb8795bb5fc3741205b92`.

The implementation is limited to the exact eleven paths in `allowed_mutated_paths`. It must preserve every historical and negative assertion, the existing push and ordinary pull-request routes, read-only permissions, credential-free candidate execution, H0-compatible receipt schema and single-artifact publication. It must not modify PR #106 or execute Docker, OpenHands, Agent Canvas, Codex ACP, Issue #102, deployment, credentials, tag or release operations.

## Acceptance boundary

The Decision is committed before generated authority or implementation. The standard transition Gate sequence must produce `transition-lint == PASSED`, `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons == []`, and 18/18 checks `PASS` for the exact branch and B2 base. The B2 active PR110 v1 Intent is archived byte-for-byte as `archive/pr110_v1.json`; the new active Intent binds PR #112, B2, the committed Decision and generated Command Plan, merge method `merge`, the current four-workflow policy, and a bounded expiry.

The trusted bridge derives B3 and the candidate head from the bound PR #106 event, proves that B3 is the PR #112 ordered merge descendant of B2, proves the exact four-commit H0-to-v14 topology and exact eleven-path net change, and validates the active-versus-historical base constants by reading candidate test files only as data. It requires the permanent workflow and production Python trees at the candidate to equal H0, preserves all H0 test names and rejects new skip/skipif/xfail markers or changed historical archives, selects only latest exact-head CI and Decision Preflight successes, runs candidate code only in a tokenless `permissions: {}` job, and emits one verifier-compatible receipt bound to B3, the candidate head and canonical B3..candidate changed-path digest.

All specified tests, YAML and structural workflow checks, and `git diff --check 93984db182b7ee11b3ccb8795bb5fc3741205b92..HEAD` must pass without repair or retry. The cumulative diff remains within the exact eleven-path scope. Publication is limited to pushing the existing branch and updating or commenting on Draft PR #112 plus read-only check observation. Merge, mark-ready and auto-merge remain false. The terminal status is `BOOTSTRAP_V3_PR106_V14_BRIDGE_READY_FOR_OWNER_AUDIT`.
