# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260801_issue92_replacement_shadow_audit_v2",
  "round_id": "round_20260801_issue92_replacement_shadow_audit_v2",
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
  "follows_last_decision_id": "decision_20260801_issue92_shadow_audit_recovery_v1",
  "follows_last_round_id": "round_20260801_issue92_shadow_audit_recovery_v1",
  "previous_audit_outcome": "BLOCKED_VALIDATOR_OPERATION_PROMPT_INCONSISTENCY",
  "workstream_id": "issue92-replacement-shadow-audit-v2",
  "source_issue": 92,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "3dd972d04b6973d93aaa72043585b0eb525ddc14",
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
  "replacement_attempt_limit": 1,
  "original_audit_immutable": true,
  "frozen_context_path": "../reverse-agent-supervisor-context-v05.json",
  "frozen_context_sha256": "08ec84b2b38cc12cd45e154d08437ee8a536f2775d3ce87af5e046967f5ce50c",
  "rejected_audit_path": "../reverse-agent-supervisor-audit-v05.json",
  "rejected_audit_sha256": "87a6ccbdf2dc89a3e23a1f25f61ac84a7ae5eeee4289ed4a0d05c792ca7f27ef",
  "replacement_audit_path": "../reverse-agent-supervisor-audit-v06.json",
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
      "command_id": "validation.frozen_context_digest",
      "command": "python -c \"import hashlib,pathlib; p=pathlib.Path('../reverse-agent-supervisor-context-v05.json'); assert p.is_file(); assert hashlib.sha256(p.read_bytes()).hexdigest() == '08ec84b2b38cc12cd45e154d08437ee8a536f2775d3ce87af5e046967f5ce50c'\"",
      "phase": "validation",
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
      "command_id": "validation.rejected_audit_digest",
      "command": "python -c \"import hashlib,pathlib; p=pathlib.Path('../reverse-agent-supervisor-audit-v05.json'); assert p.is_file(); assert hashlib.sha256(p.read_bytes()).hexdigest() == '87a6ccbdf2dc89a3e23a1f25f61ac84a7ae5eeee4289ed4a0d05c792ca7f27ef'\"",
      "phase": "validation",
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
      "command_id": "validation.replacement_audit_result",
      "command": "python scripts/supervisor_validate.py --result ../reverse-agent-supervisor-audit-v06.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
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
      "command": "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v06.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
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
    "project_state/gates/transition_preflight_result.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/supervisor/audit-instructions.md",
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_validate.py",
    "scripts/supervisor_publish.py",
    "tests/test_supervisor_validate.py",
    "tests/test_repository_hygiene.py",
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
    "scripts/**",
    "tests/**"
  ],
  "forbidden_operations": [
    "implementation before PRE_EXECUTION_AUTHORIZED",
    "modify or replace the rejected v05 audit result",
    "reuse the rejected v05 audit result as the replacement",
    "more than one replacement audit attempt",
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
      "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v06.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
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
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Authorize exactly one fresh replacement schema-0.2 Codex App shadow-audit result after the immutable v05 result failed validation with OPERATION_PROMPT_INCONSISTENCY:edit_bounded_files_required_for_file_scope. Reuse the frozen v05 Context only after verifying its SHA-256. Preserve the rejected v05 audit result byte-for-byte. Generate v06 from scratch in the current, human-dispatched Codex App task, validate it once, and only if validation succeeds run publication planning without --live. The direct current-task audit is permitted; nested codex exec, repository model API invocation, a second agent, and a second replacement attempt remain forbidden. The replacement prompt must make operation grants internally consistent: any repository file path in allowed_scope, or any instruction to create/edit files, requires requested_operations to include edit_bounded_files; a named branch push requires push_named_branch; Draft PR creation or description update requires create_or_update_draft_pr. No repository implementation change is authorized.

## Acceptance boundary

Success is limited to:

```text
CODEX_APP_REPLACEMENT_SHADOW_AUDIT_COMPLETE_ZERO_WRITES
```

The v05 result remains immutable evidence. This Decision authorizes one new v06 result, not repair of v05. A validator failure, missing artifact, digest mismatch, second attempt, or any GitHub write during the shadow phase must stop as BLOCKED_WITH_EXACT_EVIDENCE. This Decision does not authorize live publication, source/test/docs changes, mark-ready, merge, main mutation, release, deployment, nested model calls, or a new branch/Issue/PR.
