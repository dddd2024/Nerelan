# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260727_pr60_final_merge_authorization_v1","round_id":"round_20260727_pr60_final_merge_authorization_v1","based_on_state_build_id":"state_20260618_134029_d6bd033d2532","based_on_state_digest":"d6bd033d25324345cfd8ada0ac65db42bc86eb5017f3ffc92906fcd8b71cacb5","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260726_governance_migration_owner_manual_merge_rework_v3",
  "follows_last_round_id": "round_20260726_governance_migration_owner_manual_merge_rework_v3",
  "previous_audit_outcome": "PR60_EXACT_HEAD_REPRODUCTION_AND_FINAL_AUDIT_ACCEPTED",
  "workstream_id": "pr60-final-merge-authorization-v1",
  "source_issue": 63,
  "source_work_item": 59,
  "implementation_rework_issue": 61,
  "independent_reproduction_issue": 62,
  "target_pr": 60,
  "target_head": "0ab750cf0ea49463d29577948becc768a6c176b8",
  "target_base": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "required_branch": "codex/pr60-final-merge-authorization-v1",
  "activation_base_sha": "61570724495aa7053eba78bd2e34d8bda22f6407",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_update_allowed": false,
  "mark_ready_allowed": true,
  "merge_allowed": true,
  "auto_merge_allowed": false,
  "merge_method": "merge",
  "expected_head_protection_required": true,
  "owner_manual_execution_only": true,
  "owner_manual_action_required": true,
  "agent_execution_mark_ready_allowed": false,
  "agent_execution_merge_allowed": false,
  "authorization_branch_is_authority_carrier_only": true,
  "authorization_branch_enters_main": false,
  "stop_after_authorization_report": true,
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
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"],
      "produced_artifacts": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "status.git_status",
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
      "command_id": "gate.command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["command_plan_generation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ],
      "produced_artifacts": [
        "project_state/gates/command_plan.json",
        "project_state/gates/transition_command_plan_preview.json"
      ]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authority_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "gate.pre_execution",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pre_execution_authorization"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ],
      "produced_artifacts": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
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
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.push_authorization_branch",
      "command": "git push -u origin codex/pr60-final-merge-authorization-v1",
      "phase": "publication",
      "required": true,
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
      "command_id": "observation.pr60_live_state",
      "command": "gh pr view 60 --repo dddd2024/reverse-agent --json state,isDraft,mergedAt,headRefOid,baseRefOid,mergeable,mergeStateStatus,autoMergeRequest,statusCheckRollup",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "repository_observation"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.pr60_review_threads",
      "command": "gh api graphql --input PR60_REVIEW_THREADS_QUERY_PATH",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "repository_observation"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.issue62",
      "command": "gh issue view 62 --repo dddd2024/reverse-agent --json state,stateReason,comments",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "repository_observation"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.issue63_report",
      "command": "gh issue comment 63 --repo dddd2024/reverse-agent --body-file PR60_FINAL_AUTHORIZATION_REPORT_PATH",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["network_access", "issue_comment"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/control_plane/models.py",
    "project_state/schemas/transition_authority.schema.json",
    "project_state/schemas/transition_command_plan.schema.json",
    "project_state/schemas/transition_preflight_result.schema.json",
    "tests/test_project_gate.py",
    "tests/test_control_plane_transition.py"
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
    ".codex-skills/**",
    "AGENTS.md",
    "docs/**",
    "reverse_agent/**",
    "tests/**",
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/codex_execution_report.md",
    "project_state/execution_report.md",
    "project_state/pytest_result.txt"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "force_push",
    "rebase",
    "squash",
    "tag_or_release",
    "destructive",
    "secret_change",
    "runner_dispatch",
    "model_api_invocation",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "workflow_dispatch",
    "automatic_merge",
    "auto_merge",
    "agent_initiated_mark_ready",
    "agent_initiated_merge",
    "automation_initiated_mark_ready",
    "automation_initiated_merge",
    "workflow_initiated_mark_ready",
    "workflow_initiated_merge",
    "scheduled_mark_ready",
    "scheduled_merge",
    "delegated_mark_ready",
    "delegated_merge",
    "external_service_mark_ready",
    "external_service_merge",
    "pr_update",
    "pr_creation",
    "direct_push_to_main",
    "history_rewrite",
    "workflow_change",
    "dependency_change",
    "product_source_change",
    "test_change"
  ],
  "capability_policy": {
    "direct_push_to_main_allowed": false,
    "merge_allowed": true,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "destructive_operations_allowed": false,
    "unknown_binary_execution_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "runner_dispatch_allowed": false,
    "network_access_default_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push -u origin codex/pr60-final-merge-authorization-v1",
      "gh pr view 60 --repo dddd2024/reverse-agent --json state,isDraft,mergedAt,headRefOid,baseRefOid,mergeable,mergeStateStatus,autoMergeRequest,statusCheckRollup",
      "gh api graphql --input PR60_REVIEW_THREADS_QUERY_PATH",
      "gh issue view 62 --repo dddd2024/reverse-agent --json state,stateReason,comments",
      "gh issue comment 63 --repo dddd2024/reverse-agent --body-file PR60_FINAL_AUTHORIZATION_REPORT_PATH"
    ]
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ],
  "final_merge_binding": {
    "repository": "dddd2024/reverse-agent",
    "target_pr": 60,
    "target_head": "0ab750cf0ea49463d29577948becc768a6c176b8",
    "target_base": "61570724495aa7053eba78bd2e34d8bda22f6407",
    "mark_ready_allowed": true,
    "merge_allowed": true,
    "auto_merge_allowed": false,
    "merge_method": "merge",
    "expected_head_protection_required": true,
    "owner_manual_execution_only": true,
    "agent_execution_mark_ready": "forbidden",
    "agent_execution_merge": "forbidden"
  },
  "required_live_acceptance": {
    "origin_main": "61570724495aa7053eba78bd2e34d8bda22f6407",
    "pr_state": "OPEN",
    "pr_draft": true,
    "pr_merged": false,
    "pr_head": "0ab750cf0ea49463d29577948becc768a6c176b8",
    "pr_base": "61570724495aa7053eba78bd2e34d8bda22f6407",
    "pr_mergeable": true,
    "auto_merge_disabled": true,
    "unresolved_review_threads": 0,
    "required_exact_head_workflows": ["CI", "State Gate", "Decision Preflight"],
    "independent_reproduction_issue": 62,
    "independent_reproduction_result": "EXACT_HEAD_REPRODUCTION_ACCEPTED",
    "final_audit_result": "accepted exact head"
  },
  "owner_action_commands": [
    "gh pr ready 60 --repo dddd2024/reverse-agent",
    "gh pr merge 60 --repo dddd2024/reverse-agent --merge --match-head-commit 0ab750cf0ea49463d29577948becc768a6c176b8"
  ],
  "stop_conditions": [
    "startup_state_mismatch",
    "decision_schema_cannot_bind_final_merge",
    "transition_lint_failure",
    "preflight_not_authorized",
    "authorization_branch_push_failure",
    "origin_main_drift",
    "pr60_state_drift",
    "pr60_head_or_base_drift",
    "pr60_not_mergeable",
    "pr60_auto_merge_enabled",
    "pr60_unresolved_review_threads_nonzero",
    "exact_head_workflow_failure",
    "independent_reproduction_not_accepted",
    "final_audit_not_accepted",
    "attempted_agent_or_automation_mark_ready",
    "attempted_agent_or_automation_merge"
  ]
}
```

## DECISION_PACKET

### Goal

Prepare the bounded Path-B final merge authorization for PR #60 exact head
`0ab750cf0ea49463d29577948becc768a6c176b8` against base
`61570724495aa7053eba78bd2e34d8bda22f6407`.

This Decision is an authority carrier only. It does not enter `main`, does not
modify PR #60, and does not authorize an Agent, automation, workflow, scheduled
task, delegate, or external service to mark the PR ready or merge it.

### Final merge binding

- Target repository: `dddd2024/reverse-agent`
- Target PR: `#60`
- Accepted target head: `0ab750cf0ea49463d29577948becc768a6c176b8`
- Required main/base: `61570724495aa7053eba78bd2e34d8bda22f6407`
- Mark-ready allowed: `true`, owner manual execution only
- Merge allowed: `true`, owner manual execution only
- Auto-merge allowed: `false`
- Merge method: `merge`
- Expected-head protection: required

The owner must personally re-observe every required live acceptance invariant
and then personally execute the owner action commands. Agent execution of
mark-ready or merge remains forbidden.

### Implementation scope

Only these repository paths may change:

- `project_state/decision_packet.md`
- `project_state/gates/bootstrap_state.json`
- `project_state/gates/command_plan.json`
- `project_state/gates/startup_snapshot.json`
- `project_state/gates/transition_command_plan_preview.json`
- `project_state/gates/transition_preflight_result.json`

No product source, test, workflow, dependency, Gate/runtime, schema, PR #60,
PR #47, PR #49, or `main` mutation is authorized.

### Publication scope

The only authorized branch publication is:

`git push -u origin codex/pr60-final-merge-authorization-v1`

No PR may be created for the authorization branch. One final result comment may
be published to Issue #63 after fresh live verification.

### Stop boundary

After publishing the Issue #63 authorization report, stop immediately. Do not
mark PR #60 ready, merge PR #60, enable auto-merge, close Issue #59 or #63,
delete the authorization branch, or begin another milestone.
