# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_issue151_owner_audit_rework_v2",
  "round_id": "round_20260809_issue151_owner_audit_rework_v2",
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
  "previous_audit_outcome": "V1_OWNER_PREDELEGATION_SUPERSEDED_BEFORE_EXECUTION_BOOTSTRAP_SWITCH_OMISSION",
  "workstream_id": "issue151-owner-audit-rework-v1",
  "source_issue": 151,
  "parent_issue": 148,
  "required_branch": "owner/issue151-langgraph-worker-team-rework-v1",
  "starting_head": "acf022c8865973cef59a4da742db10ec023d01d8",
  "activation_base_sha": "acf022c8865973cef59a4da742db10ec023d01d8",
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
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
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
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
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
    "git fetch origin main",
    "git fetch origin owner/issue151-langgraph-worker-team-v1",
    "git fetch origin owner/issue151-langgraph-worker-team-rework-v1",
    "git show origin/owner/issue151-langgraph-worker-team-rework-v1:project_state/decision_packet.md",
    "git switch -c owner/issue151-langgraph-worker-team-rework-v1 --track origin/owner/issue151-langgraph-worker-team-rework-v1",
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue151-langgraph-worker-team-v1",
    "git rev-parse origin/owner/issue151-langgraph-worker-team-rework-v1",
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
      "command_id": "observation.git_head",
      "command": "git rev-parse HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "observation.original_head",
      "command": "git rev-parse origin/owner/issue151-langgraph-worker-team-v1",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "test.team_and_graph",
      "command": "python -m pytest tests/test_development_graph.py tests/test_team_graph.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.platform_focused",
      "command": "python -m pytest tests/platform_v1/test_task_contracts.py tests/platform_v1/test_task_execution.py tests/platform_v1/test_task_service.py tests/platform_v1/test_task_runtime.py tests/platform_v1/test_opencode_executor.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.platform_all",
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
      "command_id": "test.taskstore_concurrency_20x",
      "command": "powershell -NoProfile -Command \"1..20 | ForEach-Object { python -m pytest tests/platform_v1/test_task_contracts.py -q -k 'taskstore_concurrent_writes_two_threads'; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.langgraph_barrier_20x",
      "command": "powershell -NoProfile -Command \"1..20 | ForEach-Object { python -m pytest tests/test_team_graph.py -q -k 'fan_out_is_parallel_via_barrier'; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }\"",
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
      "command": "git diff --check acf022c8865973cef59a4da742db10ec023d01d8..HEAD",
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
      "command": "git diff --name-only acf022c8865973cef59a4da742db10ec023d01d8..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_rework_branch",
      "command": "git push origin owner/issue151-langgraph-worker-team-rework-v1",
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
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_execution.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/workflows/nodes/acceptance_gate.py",
    "reverse_agent/architecture/contracts.py",
    "tests/platform_v1/test_task_contracts.py",
    "tests/platform_v1/test_task_execution.py",
    "tests/platform_v1/test_task_service.py",
    "tests/test_team_graph.py",
    "docs/architecture/LANGGRAPH_TEAM_RUNTIME.md",
    "docs/architecture/LANGGRAPH_ORCHESTRATION_BOUNDARY.md"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/workflows/development_graph.py",
    "tests/platform_v1/test_task_runtime.py",
    "tests/platform_v1/test_opencode_executor.py",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
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
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/orchestrator_api.py",
    "reverse_agent/orchestrator_context.py",
    "reverse_agent/orchestrator_console_schema.py",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "cherry_pick",
    "stash",
    "reset_hard",
    "git_clean",
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
    "dependency_change",
    "workflow_change",
    "provider_configuration_mutation"
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
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue151-langgraph-worker-team-v1",
      "git fetch origin owner/issue151-langgraph-worker-team-rework-v1",
      "git push origin owner/issue151-langgraph-worker-team-rework-v1"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ],
  "runner_managed_artifact_paths": [
    "project_state/gates/evidence/**",
    "project_state/gates/execution_log.json"
  ],
  "follows_last_decision_id": "decision_20260809_issue151_owner_audit_rework_v1",
  "follows_last_round_id": "round_20260809_issue151_owner_audit_rework_v1"
}
```

## Goal

v2 supersedes v1 before any local delegation. v1 was never executed. The only v1 defect was
that its bootstrap exception set omitted the exact local branch-switch needed to move an existing
fresh #151 clone onto the Owner-created descendant rework branch.

This is a one-time Path-B rework authority for Issue #151 after independent Owner audit of
`owner/issue151-langgraph-worker-team-v1@acf022c8865973cef59a4da742db10ec023d01d8`.

The original #151 branch remains untouched while this authority is activated on the descendant
branch `owner/issue151-langgraph-worker-team-rework-v1`.

Authorized work is limited to closing the Owner-audit gaps already recorded on #151:

1. retire duplicate Task API execution helpers so `TaskExecutionService` is the sole programmatic lifecycle and OpenCode kwargs implementation;
2. propagate persisted failure classification/detail into `TaskExecutionOutcome` and `WorkerExecutionResult`;
3. make present-but-malformed `team_execution_result` fail closed while preserving the no-result legacy behavior;
4. retain one `TaskStore` `RLock` but prevent `create_task_and_execute()` from holding it across the external executor callback;
5. add focused regressions and run repeated TaskStore/LangGraph concurrency checks;
6. correct documentation so historical `sqlite3.InterfaceError` / `20/20` claims are not presented as independently reproduced facts unless this rework produces auditable evidence.

This Decision does not authorize new Multi-Agent features, provider/model work, Product Setup,
Freshness #152, PR #146 work, dependency/workflow changes, or any model/Agent runtime invocation.

## Acceptance

- bootstrap first reads back this exact remote v2 Decision, then creates the local tracking rework branch from the exact remote rework ref;
- rework branch ancestry remains rooted at `acf022c8865973cef59a4da742db10ec023d01d8`;
- transition command plan is non-empty and bound to this Decision/round;
- transition lint passes;
- transition preflight returns `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`;
- only authorized #151 source/test/doc paths are staged in the implementation commit;
- generated gate artifacts may remain local and uncommitted;
- `TaskExecutionService` is the single execution lifecycle used by HTTP and LangGraph worker paths;
- persisted failure truth reaches worker results;
- malformed present team result fails closed;
- TaskStore outer lock is not held across the external executor callback;
- TaskStore focused concurrency check passes 20 consecutive runs;
- LangGraph barrier fan-out check passes 20 consecutive runs;
- required focused and full Platform V1 tests pass;
- `git diff --check acf022c8865973cef59a4da742db10ec023d01d8..HEAD` passes;
- no frontend, `.github`, dependency, provider/credential, legacy orchestrator, or #146 product mutation;
- generated local gate files are not staged in the product implementation commit;
- exactly one normal push to the rework branch after validation;
- no PR creation, Ready, merge, main push, rebase, force push, reset, clean, stash, amend, model/OpenCode/Codex/OpenHands call, release, or deploy.

Terminal success token:

`ISSUE151_REWORK_PUSHED_FOR_OWNER_REAUDIT`
