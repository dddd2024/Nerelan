# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_r1_unblocker_sanitized_integration_forensics_v4",
  "round_id": "round_20260809_governance_v2_r1_unblocker_sanitized_integration_forensics_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_governance_v2_r1_unblocker_sanitized_integration_v3",
  "follows_last_round_id": "round_20260809_governance_v2_r1_unblocker_sanitized_integration_v3",
  "previous_audit_outcome": "INTEGRATION_V3_STOPPED_WITH_EVIDENCE_TRANSITION_PREFLIGHT_BLOCKED_WITH_EMPTY_AUTHORITY_IDENTITY",
  "workstream_id": "governance-v2-r1-unblocker-sanitized-integration-forensics-v4",
  "source_issue": 157,
  "parent_issue": 148,
  "related_issue": 156,
  "blocked_issue": 151,
  "required_branch": "owner/governance-v2-r1-unblocker-integration-authority-v1",
  "starting_head": "b3102eca7d20571d7f81ea4c0ba1dff370464575",
  "activation_base_sha": "f8010e1c05d64f556d64f81c35e6916bf825409e",
  "integration_target_branch": "owner/repository-modernization-v2-planning",
  "accepted_product_head": "f3690515f38bcb9072a9a5bc289a6335758dfd1a",
  "sanitized_target_branch": "owner/governance-v2-r1-unblocker-sanitized-v1",
  "risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": false,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 1,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git rev-parse HEAD",
    "git fetch origin owner/repository-modernization-v2-planning",
    "git fetch origin owner/governance-v2-r1-unblocker-v1",
    "git fetch origin owner/governance-v2-r1-unblocker-integration-authority-v1",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-r1-unblocker-v1",
    "git rev-parse origin/owner/governance-v2-r1-unblocker-integration-authority-v1",
    "git merge --ff-only origin/owner/governance-v2-r1-unblocker-integration-authority-v1",
    "git diff --name-only",
    "git diff --cached --name-only",
    "git ls-files --others --exclude-standard",
    "powershell -NoProfile -Command \"Get-Content 'project_state/gates/transition_preflight_result.json' -Raw\"",
    "powershell -NoProfile -Command \"Get-Content 'project_state/gates/command_plan.json' -Raw\"",
    "powershell -NoProfile -Command \"Get-Content 'project_state/gates/startup_snapshot.json' -Raw\"",
    "powershell -NoProfile -Command \"Get-Content 'project_state/gates/transition_command_plan_preview.json' -Raw\"",
    "powershell -NoProfile -Command \"if(Test-Path 'project_state/gates/bootstrap_state.json'){Get-Content 'project_state/gates/bootstrap_state.json' -Raw}\"",
    "powershell -NoProfile -Command \"Get-FileHash -Algorithm SHA256 'project_state/gates/transition_preflight_result.json','project_state/gates/command_plan.json','project_state/gates/startup_snapshot.json','project_state/gates/transition_command_plan_preview.json' | Format-Table Path,Hash -AutoSize\""
  ],
  "allowed_commands": [
    {"command_id":"observation.head","command":"git rev-parse HEAD","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"sync.fetch_planning","command":"git fetch origin owner/repository-modernization-v2-planning","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true},
    {"command_id":"sync.fetch_source","command":"git fetch origin owner/governance-v2-r1-unblocker-v1","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true},
    {"command_id":"sync.fetch_authority","command":"git fetch origin owner/governance-v2-r1-unblocker-integration-authority-v1","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true},
    {"command_id":"observation.working_paths","command":"git diff --name-only","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"observation.cached_paths","command":"git diff --cached --name-only","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"observation.untracked_paths","command":"git ls-files --others --exclude-standard","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.preflight","command":"powershell -NoProfile -Command \"Get-Content 'project_state/gates/transition_preflight_result.json' -Raw\"","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.command_plan","command":"powershell -NoProfile -Command \"Get-Content 'project_state/gates/command_plan.json' -Raw\"","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.startup_snapshot","command":"powershell -NoProfile -Command \"Get-Content 'project_state/gates/startup_snapshot.json' -Raw\"","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.plan_preview","command":"powershell -NoProfile -Command \"Get-Content 'project_state/gates/transition_command_plan_preview.json' -Raw\"","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.bootstrap_state","command":"powershell -NoProfile -Command \"if(Test-Path 'project_state/gates/bootstrap_state.json'){Get-Content 'project_state/gates/bootstrap_state.json' -Raw}\"","phase":"forensics","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false},
    {"command_id":"forensics.hashes","command":"powershell -NoProfile -Command \"Get-FileHash -Algorithm SHA256 'project_state/gates/transition_preflight_result.json','project_state/gates/command_plan.json','project_state/gates/startup_snapshot.json','project_state/gates/transition_command_plan_preview.json' | Format-Table Path,Hash -AutoSize\"","phase":"forensics","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false}
  ],
  "allowed_mutated_paths": ["project_state/decision_packet.md"],
  "reference_paths": [
    "project_state/gates/transition_preflight_result.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/bootstrap_state.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    "AGENTS.md",
    "reverse_agent/**",
    "tests/**",
    "docs/**",
    "frontend/**",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    "project_state/mainline_merge_intents/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json"
  ],
  "forbidden_operations": [
    "source_mutation",
    "test_mutation",
    "branch_create",
    "worktree_create",
    "commit",
    "push",
    "pr_create",
    "merge",
    "mark_ready",
    "reset",
    "clean",
    "restore",
    "stash",
    "rebase",
    "force_push",
    "amend",
    "squash",
    "cherry_pick",
    "tag_or_release",
    "deployment",
    "credential_access",
    "model_api_invocation"
  ]
}
```

## Owner notes

- This is a read-only forensic successor. It does not authorize sanitized reconstruction, tests, commits, or publication.
- Preserve the v3 failed gate artifacts exactly as they exist before any regeneration. Do NOT run startup-snapshot, transition-command-plan, transition-lint, or transition-preflight in this round.
- The first forensic payload to capture is `project_state/gates/transition_preflight_result.json`; report its complete JSON including any `error`, `blocking_reasons`, `checks`, `decision_id`, `round_id`, and artifact binding fields.
- v3 semantic failure must be diagnosed from preserved evidence before any corrective integration authority is issued.
