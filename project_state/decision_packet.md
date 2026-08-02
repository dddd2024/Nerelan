# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260802_issue92_fresh_shadow_audit_v8",
  "round_id": "round_20260802_issue92_fresh_shadow_audit_v8",
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
  "follows_last_decision_id": "decision_20260802_issue92_reporting_phrase_precedence_v7",
  "follows_last_round_id": "round_20260802_issue92_reporting_phrase_precedence_v7",
  "previous_audit_outcome": "REPORTING_PHRASE_PRECEDENCE_COMPLETE_AWAITING_SHADOW_AUDIT_AUTHORITY",
  "workstream_id": "issue92-fresh-shadow-audit-v8",
  "source_issue": 92,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "14be457be4f2a7195c6882df3bbb2cf94be3cafd",
  "activation_base_sha": "16526801bda2a816fc707342f903c1ad037de9bd",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "real_provider_credential_allowed": false,
  "live_work_item_publication_allowed": false,
  "repair_attempt_limit": 1,
  "audit_generation_allowed": true,
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
      "command_id": "observation.v07_hash",
      "command": "python -c \"import hashlib,pathlib; p=pathlib.Path('../reverse-agent-supervisor-audit-v07.json'); print('ABSENT' if not p.exists() else hashlib.sha256(p.read_bytes()).hexdigest())\"",
      "phase": "observation",
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
      "command_id": "observation.collect_context_v08",
      "command": "python scripts/supervisor_context.py --repository dddd2024/reverse-agent --goal-issue 90 --active-pr 93 --output ../reverse-agent-supervisor-context-v08.json",
      "phase": "observation",
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
      "command_id": "observation.context_v08_hash",
      "command": "python -c \"import hashlib,pathlib; p=pathlib.Path('../reverse-agent-supervisor-context-v08.json'); print(hashlib.sha256(p.read_bytes()).hexdigest())\"",
      "phase": "observation",
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
      "command_id": "validation.audit_v08",
      "command": "python scripts/supervisor_validate.py --result ../reverse-agent-supervisor-audit-v08.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["audit_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "authority_origin": "normal_plan",
      "allowed_mutated_paths": [],
      "produced_artifacts": []
    },
    {
      "command_id": "publication.plan_dry_run",
      "command": "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v08.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "phase": "observation",
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
    "project_state/decision_packet.md",
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
    "shadow-audit execution before PRE_EXECUTION_AUTHORIZED",
    "modify repository implementation, tests, or documentation",
    "modify, rename, parse, publish, or use v07 for publication planning",
    "generate more than one v08 audit result",
    "generate v09 or any other audit version",
    "invoke a second model or nested agent",
    "live publication or apply_result",
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
      "python scripts/supervisor_context.py --repository dddd2024/reverse-agent --goal-issue 90 --active-pr 93 --output ../reverse-agent-supervisor-context-v08.json",
      "python scripts/supervisor_publish.py plan --result ../reverse-agent-supervisor-audit-v08.json --repository dddd2024/reverse-agent --main-sha 16526801bda2a816fc707342f903c1ad037de9bd",
      "git push origin agent/codex-supervisor-foundation-v0",
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
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    }
  ]
}
```

## Goal

Collect a fresh bounded context after the accepted implementation Head 14be457be4f2a7195c6882df3bbb2cf94be3cafd. Perform exactly one external shadow audit of the accepted Supervisor implementation. Generate only ../reverse-agent-supervisor-audit-v08.json. Validate the result against schema 0.2, repository dddd2024/reverse-agent and main SHA 16526801bda2a816fc707342f903c1ad037de9bd. Run publication planning in dry-run mode only. Do not modify repository implementation files and do not perform a live GitHub Work Item write. In this Decision, implementation means the shadow-audit execution stage and does not authorize source-code implementation.

## Acceptance boundary

The v8 shadow audit is complete only when the Decision commit and generated Gate commit are separate; PRE_EXECUTION_AUTHORIZED is 18/18 PASS with no blockers; exact-head CI, Decision Preflight, and State Gate succeed; the repository worktree is clean before Context collection; Context current_head and PR #93 head facts equal the v8 generated-authority Head; Context main_sha equals 16526801bda2a816fc707342f903c1ad037de9bd; exactly one v08 audit file is generated; v07 remains unchanged and unread; the v08 validator returns valid=true; v08 evidence explicitly identifies implementation commit 14be457be4f2a7195c6882df3bbb2cf94be3cafd and the v8 authority Head; publication planning is dry-run only with no apply_result or live write; the repository remains clean; and PR #93 remains Open, Draft, and unmerged. Success is FRESH_SHADOW_AUDIT_VALIDATED_AWAITING_OWNER_DISPOSITION. Any authority, Context, generation, validation, dry-run, integrity, or exact-head failure must stop as BLOCKED_WITH_EXACT_EVIDENCE without retry or repair.
