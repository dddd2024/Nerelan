# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260801_issue92_shadow_audit_recovery_v1",
  "round_id": "round_20260801_issue92_shadow_audit_recovery_v1",
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
  "follows_last_decision_id": "decision_20260729_pr67_final_intent_rebind_v5",
  "follows_last_round_id": "round_20260729_pr67_final_intent_rebind_v5",
  "previous_audit_outcome": "BLOCKED_GATE_0_PATH_B_AUTHORITY_MISMATCH",
  "workstream_id": "issue92-shadow-audit-recovery-v1",
  "source_issue": 92,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "e5baee5464c25a2a94883b7f0756e0041d4b3e1f",
  "activation_base_sha": "16526801bda2a816fc707342f903c1ad037de9bd",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "real_provider_credential_allowed": false,
  "live_work_item_publication_allowed": false,
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
      "command_id": "test.supervisor_focused",
      "command": "python -m pytest tests/test_supervisor_validate.py tests/test_repository_hygiene.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["regression_test"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.context_retry",
      "command": "python scripts/supervisor_context.py --repository dddd2024/reverse-agent --goal-issue 90 --active-pr 93 --output ../reverse-agent-supervisor-context-v05.json",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.audit_result",
      "command": "python scripts/supervisor_validate.py --result ../reverse-agent-supervisor-audit-v05.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["policy_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.publication_dry_run",
      "command": "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v05.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check 16526801bda2a816fc707342f903c1ad037de9bd..HEAD",
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
      "command": "git push origin agent/codex-supervisor-foundation-v0",
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
      "command_id": "publication.comment_issue92",
      "command": "gh issue comment 92 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["issue_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.comment_pr93",
      "command": "gh pr comment 93 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH",
      "phase": "publication",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["pull_request_comment", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.pr93_checks",
      "command": "gh pr checks 93 --repo dddd2024/reverse-agent --watch",
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
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "scripts/supervisor_context.py",
    "tests/test_supervisor_validate.py",
    "tests/test_repository_hygiene.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/supervisor/audit-instructions.md",
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_validate.py",
    "scripts/supervisor_publish.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    ".codex-skills/registry.json"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/**",
    "reverse_agent/**",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "AGENTS.md",
    "pyproject.toml",
    "docs/**",
    "scripts/supervisor_validate.py",
    "scripts/supervisor_publish.py"
  ],
  "forbidden_operations": [
    "implementation before PRE_EXECUTION_AUTHORIZED",
    "new branch",
    "new issue",
    "new pull request",
    "direct push to main",
    "live generated Work Item publication",
    "mark ready",
    "merge",
    "auto merge",
    "force push",
    "rebase",
    "squash",
    "tag or release",
    "deployment",
    "credential access",
    "nested model invocation",
    "runner dispatch",
    "unknown binary execution",
    "external reverse-tool invocation"
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
      "python scripts/supervisor_context.py --repository dddd2024/reverse-agent --goal-issue 90 --active-pr 93 --output ../reverse-agent-supervisor-context-v05.json",
      "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v05.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "git push origin agent/codex-supervisor-foundation-v0",
      "gh issue comment 92 --repo dddd2024/reverse-agent --body-file ISSUE_COMMENT_TEMP_PATH",
      "gh pr comment 93 --repo dddd2024/reverse-agent --body-file PR_COMMENT_TEMP_PATH",
      "gh pr checks 93 --repo dddd2024/reverse-agent --watch"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "scripts/supervisor_context.py",
    "tests/test_supervisor_validate.py",
    "tests/test_repository_hygiene.py"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "scripts/supervisor_context.py", "minimum_risk": "R1"},
    {"pattern": "tests/test_supervisor_validate.py", "minimum_risk": "R1"},
    {"pattern": "tests/test_repository_hygiene.py", "minimum_risk": "R1"}
  ]
}
```

## Goal

Recover Issue #92 from the stale PR #67 Path-B authority, bind execution to PR #93 and the exact Supervisor branch, add only the missing Windows UTF-8 regression coverage or a narrowly proven adjacent collector correction, then run one successful bounded Context collection and one schema-0.2 Codex App shadow audit. The shadow result must be validated and passed to publication planning without `--live`; no generated Work Item may be published.

## Acceptance boundary

Success is limited to:

```text
CODEX_APP_SHADOW_AUDIT_COMPLETE_ZERO_WRITES
```

This Decision does not authorize live publication, mark-ready, merge, main mutation, release, deployment, nested model calls, or any new framework/dependency/workflow/Gate family.
