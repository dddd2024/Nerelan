# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_governance_v2_r1_unblocker_sanitized_integration_v1",
  "round_id": "round_20260809_governance_v2_r1_unblocker_sanitized_integration_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "previous_audit_outcome": "ISSUE157_V6_ACCEPTED_SOURCE_HEAD_F369051_AWAITING_SANITIZED_ONE_COMMIT_INTEGRATION",
  "workstream_id": "governance-v2-r1-unblocker-sanitized-integration-v1",
  "source_issue": 157,
  "parent_issue": 148,
  "related_issue": 156,
  "blocked_issue": 151,
  "required_branch": "owner/governance-v2-r1-unblocker-integration-authority-v1",
  "starting_head": "f8010e1c05d64f556d64f81c35e6916bf825409e",
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
  "branch_creation_allowed": true,
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
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
  "infrastructure_retry_limit": 0,
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
    "git status --short",
    "git fetch origin owner/repository-modernization-v2-planning",
    "git fetch origin owner/governance-v2-r1-unblocker-v1",
    "git fetch origin owner/governance-v2-r1-unblocker-integration-authority-v1",
    "git rev-parse HEAD",
    "git rev-parse origin/owner/repository-modernization-v2-planning",
    "git rev-parse origin/owner/governance-v2-r1-unblocker-v1",
    "git rev-parse origin/owner/governance-v2-r1-unblocker-integration-authority-v1",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {"command_id":"observation.status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"sync.fetch_planning","command":"git fetch origin owner/repository-modernization-v2-planning","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"sync.fetch_source","command":"git fetch origin owner/governance-v2-r1-unblocker-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"sync.fetch_authority","command":"git fetch origin owner/governance-v2-r1-unblocker-integration-authority-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"evidence.source_manifest","command":"git diff --raw --full-index --no-renames f8010e1c05d64f556d64f81c35e6916bf825409e f3690515f38bcb9072a9a5bc289a6335758dfd1a -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/decision-preflight.yml AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/project_gate.py tests/test_decision_preflight.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"mutation.create_sanitized_worktree","command":"git -c core.autocrlf=false -c core.eol=lf worktree add -b owner/governance-v2-r1-unblocker-sanitized-v1 F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 f8010e1c05d64f556d64f81c35e6916bf825409e","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["branch_create","worktree_create"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"mutation.apply_product_delta","command":"cmd /d /c \"git diff --binary f8010e1c05d64f556d64f81c35e6916bf825409e f3690515f38bcb9072a9a5bc289a6335758dfd1a -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/decision-preflight.yml AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/project_gate.py tests/test_decision_preflight.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py | git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 apply -\"","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["source_mutation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"mutation.stage_product","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 add .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/decision-preflight.yml AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/project_gate.py tests/test_decision_preflight.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_staging"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"evidence.staged_manifest","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 diff --cached --raw --full-index --no-renames f8010e1c05d64f556d64f81c35e6916bf825409e -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/decision-preflight.yml AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/project_gate.py tests/test_decision_preflight.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.focused_governance","command":"powershell -NoProfile -Command \"Set-Location 'F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809'; python -m pytest tests/test_path_a_gate.py tests/test_project_gate.py tests/test_control_plane_transition.py tests/test_minimal_integration_baseline_docs.py tests/test_decision_preflight.py -q\"","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.platform_v1","command":"powershell -NoProfile -Command \"Set-Location 'F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809'; python -m pytest tests/platform_v1 -q\"","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.diff_check","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 diff --cached --check","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"mutation.commit_product","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 commit -m \"governance: integrate R1 execution unblocker\"","phase":"implementation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["commit"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.product_equivalence","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 diff --exit-code f3690515f38bcb9072a9a5bc289a6335758dfd1a HEAD -- .github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml .github/workflows/decision-preflight.yml AGENTS.md reverse_agent/control_plane/path_a.py reverse_agent/project_gate.py tests/test_decision_preflight.py tests/test_minimal_integration_baseline_docs.py tests/test_path_a_gate.py tests/test_project_gate.py","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"publication.push_sanitized","command":"git -C F:\\reverse-agent-governance-v2-r1-unblocker-sanitized-20260809 push origin owner/governance-v2-r1-unblocker-sanitized-v1","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true}
  ],
  "allowed_mutated_paths": [
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/workflows/decision-preflight.yml",
    "AGENTS.md",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/project_gate.py",
    "tests/test_decision_preflight.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py",
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "required_files_changed": [
    ".github/ISSUE_TEMPLATE/minimal-ai-r1-task.yml",
    ".github/workflows/decision-preflight.yml",
    "AGENTS.md",
    "reverse_agent/control_plane/path_a.py",
    "reverse_agent/project_gate.py",
    "tests/test_decision_preflight.py",
    "tests/test_minimal_integration_baseline_docs.py",
    "tests/test_path_a_gate.py",
    "tests/test_project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    ".github/workflows/state-gate.yml",
    "frontend/**",
    "docs/**",
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/**",
    "reverse_agent/architecture/contracts.py",
    "tests/platform_v1/**",
    "tests/test_team_graph.py",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "restore",
    "stash",
    "amend",
    "squash",
    "cherry_pick",
    "tag_or_release",
    "deployment",
    "credential_access",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation"
  ]
}
```

## Owner notes

- Accepted source head is immutable: `f3690515f38bcb9072a9a5bc289a6335758dfd1a`.
- Planning base must remain exactly `f8010e1c05d64f556d64f81c35e6916bf825409e` until sanitized push completes.
- Sanitized product history must be one commit parented directly by planning and contain exactly nine product/test paths, zero `project_state/**`.
- Raw/full-index Git object manifest equality is canonical identity proof; patch text hash is not authority.
- The sanitized worktree must use canonical LF checkout because Platform V1 contains byte/hash fixtures.
- No PR, merge, planning push, main push, #151 recovery, #146 mutation, Product Setup, or #152 work is authorized in this round.
