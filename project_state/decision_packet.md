# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260801_issue92_multi_surface_reference_consistency_v6",
  "round_id": "round_20260801_issue92_multi_surface_reference_consistency_v6",
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
  "follows_last_decision_id": "decision_20260801_issue92_operation_surface_consistency_v5",
  "follows_last_round_id": "round_20260801_issue92_operation_surface_consistency_v5",
  "previous_audit_outcome": "REWORK_REQUIRED_MULTI_SURFACE_AND_REFERENCE_OVERMATCH",
  "workstream_id": "issue92-multi-surface-reference-consistency-v6",
  "source_issue": 92,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "62accc87a2546cab2254ad43fc378ab5413e850f",
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
  "repair_attempt_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "v07_observation_only": true,
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
      "command_id": "test.supervisor_multi_surface_reference_consistency",
      "command": "python -m pytest tests/test_supervisor_validate.py -q -k operation_prompt_consistency",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "regression_test"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "test.supervisor_focused",
      "command": "python -m pytest tests/test_supervisor_validate.py tests/test_repository_hygiene.py -q",
      "phase": "test",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "regression_test"
      ],
      "network_access": false,
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "observation.v07_presence",
      "command": "python -c \"import hashlib,pathlib; p=pathlib.Path('../reverse-agent-supervisor-audit-v07.json'); print('ABSENT' if not p.exists() else hashlib.sha256(p.read_bytes()).hexdigest())\"",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "push",
        "network_access"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "issue_comment",
        "network_access"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "pull_request_comment",
        "network_access"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "network_access"
      ],
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
    "scripts/supervisor_validate.py",
    "tests/test_supervisor_validate.py",
    "docs/supervisor/audit-instructions.md"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
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
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "tests/test_repository_hygiene.py"
  ],
  "forbidden_operations": [
    "implementation before PRE_EXECUTION_AUTHORIZED",
    "generate, modify, validate, or publish v07 or any later audit result",
    "modify or replace v05 or v06",
    "more than one multi-surface/reference consistency repair attempt",
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
    "scripts/supervisor_validate.py",
    "tests/test_supervisor_validate.py",
    "docs/supervisor/audit-instructions.md"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "scripts/supervisor_validate.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "tests/test_supervisor_validate.py",
      "minimum_risk": "R1"
    },
    {
      "pattern": "docs/supervisor/audit-instructions.md",
      "minimum_risk": "R1"
    }
  ]
}
```

## Goal

Close the remaining fail-closed gaps in the operation-surface classifier before any shadow audit. The v5 implementation can return only one effective surface per clause because it stops after the first target match, so a Draft-PR target can hide a repository edit or unsupported GitHub write in the same clause. It also treats a bare reference such as Issue #92 as a mutation target, suppresses repository edits whenever a reporting noun is present even when the same clause names a function/module/file, and checks every occurrence of push without positive-intent or branch-target binding. After PRE_EXECUTION_AUTHORIZED, change only scripts/supervisor_validate.py, tests/test_supervisor_validate.py, and docs/supervisor/audit-instructions.md. Make classification additive: one clause may emit multiple surfaces. Bind GitHub mutation only to a positive action directed at that GitHub target, not to a reference mention. Reporting language is read-only only when the clause contains no repository-artifact target or explicit repository path. Replace the global push keyword check with a finite positive named-branch-push detector that respects direct negation and does not treat phrases such as 'push evidence into the report' as branch publication. Tighten explicit path recognition so URLs, pass/fail wording, and version numbers such as 1.0 do not imply a repository path. Expand unsupported GitHub action detection only through a finite documented set such as comment, review, approve, label, close/reopen, assign/unassign, mark ready, and branch create/delete/rename. requested_operations remains authoritative; schema 0.2, cycle-marker inputs, policy scans, repository/main binding, publication behavior, and unrelated guards remain unchanged. This Decision authorizes no model/audit generation, validator run on v07, or publication planning.

## Acceptance boundary

The v6 repair is complete only when compiler-owned v6 Gate artifacts are generated and committed separately, PRE_EXECUTION_AUTHORIZED has no blockers, implementation changes are confined to the three named files, targeted and full focused tests pass, and exact-head CI, Decision Preflight, and State Gate succeed. Tests must prove: 'Update scripts/supervisor_validate.py and edit the PR body' requires both permissions regardless of target order; 'Update the draft PR description and create an Issue comment' rejects the unsupported surface; 'Write an audit report for Issue #92' and 'Update the status summary for PR #93' remain read-only references; 'Edit Issue #92 body' remains unsupported; 'Modify the audit report generator function' and 'Modify the status report module' require edit_bounded_files; 'Do not push the branch' does not require push authority; 'Push the named branch' does; 'Push evidence into the report' is read-only; 'Comment on Issue #92', 'Review PR #93', 'Approve PR #93', and 'mark PR #93 ready' fail as unsupported mutation surfaces; pass/fail and version 1.0 text do not become paths; actual relative paths still do. Existing repository-edit, Draft-PR, dangerous-policy, schema, marker, and publication checks must remain fail-closed. Any v07 file may only be observed for presence and SHA-256 and must not be read for content, modified, regenerated, validated, or published. Success is MULTI_SURFACE_REFERENCE_CONSISTENCY_COMPLETE_AWAITING_SHADOW_AUDIT_AUTHORITY. Any Gate failure, out-of-scope mutation, test failure, unsupported weakening, second repair attempt, audit generation/validation, or forbidden GitHub operation must stop as BLOCKED_WITH_EXACT_EVIDENCE.
