# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260802_issue94_v08_findings_remediation_v9",
  "round_id": "round_20260802_issue94_v08_findings_remediation_v9",
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
  "follows_last_decision_id": "decision_20260802_issue92_fresh_shadow_audit_v8",
  "follows_last_round_id": "round_20260802_issue92_fresh_shadow_audit_v8",
  "previous_audit_outcome": "FRESH_SHADOW_AUDIT_VALIDATED_REVISE_FOUR_FINDINGS",
  "workstream_id": "issue94-v08-findings-remediation-v9",
  "source_issue": 94,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "d3e81d760da0730b49eef19558b184c9a1605ff0",
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
  "v08_read_only_remediation_input": true,
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
      "command_id": "test.pytest_operation_prompt_consistency",
      "command": "python -m pytest tests/test_supervisor_validate.py -q -k operation_prompt_consistency",
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
      "command_id": "test.pytest_focused",
      "command": "python -m pytest tests/test_supervisor_validate.py tests/test_repository_hygiene.py -q",
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
      "command_id": "test.pytest_full",
      "command": "python -m pytest -q",
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
    },
    {
      "command_id": "publication.issue94_comment",
      "command": "gh issue comment 94 --repo dddd2024/reverse-agent --body-file -",
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
      "command_id": "publication.issue92_comment",
      "command": "gh issue comment 92 --repo dddd2024/reverse-agent --body-file -",
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
      "command_id": "publication.pr93_comment",
      "command": "gh pr comment 93 --repo dddd2024/reverse-agent --body-file -",
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
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "docs/supervisor/audit-instructions.md",
    "scripts/supervisor_validate.py",
    "tests/test_supervisor_validate.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
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
    "shadow-audit generation or execution",
    "generate v09 or any other audit version",
    "read, parse, modify, rename, or publish v07 audit content",
    "modify, rename, parse, or publish v08 audit file",
    "invoke a second model or nested agent",
    "live publication or apply_result",
    "live generated Work Item publication",
    "new branch",
    "new issue",
    "new pull request",
    "direct push to main",
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
    "external reverse-tool invocation",
    "modify paths outside the three allowed source files and gate artifacts"
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
      "gh pr checks 93 --repo dddd2024/reverse-agent --watch",
      "gh issue comment 94 --repo dddd2024/reverse-agent --body-file -",
      "gh issue comment 92 --repo dddd2024/reverse-agent --body-file -",
      "gh pr comment 93 --repo dddd2024/reverse-agent --body-file -"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "docs/supervisor/audit-instructions.md",
    "scripts/supervisor_validate.py",
    "tests/test_supervisor_validate.py"
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

Remediate the four v08 fresh shadow-audit findings in one bounded implementation attempt. Correct numbered Draft PR metadata phrase recognition so that "PR #93 body" and "pull request #93 description" require `create_or_update_draft_pr`. Correct the unsupported GitHub mutation detector so that action-target order "Add label to PR #93" is rejected as an unsupported mutation surface. Correct path recognition so that quoted and parenthesized valid filenames like `"README.md"` and `(README.md)` require `edit_bounded_files`. Do not generate new audits, do not perform live publication, do not merge or mark ready, and do not broaden scope beyond the three allowed source files.

## v08 findings summary (bounded, preserved meaning)

1. **Positive finding** — The accepted implementation (commit `14be457be4f2a7195c6882df3bbb2cf94be3cafd`) preserves the core fail-closed schema, exact repository/main binding, fresh Context binding, additive surfaces, reporting-span consumption, occurrence-bounded push handling, and dry-run/live publication separation. No remediation required.

2. **Numbered Draft-PR metadata false negatives** — Phrases "Update PR #93 body." and "Update pull request #93 description." are false negatives in operation-prompt consistency; the `_DRAFT_PR_TARGET_RE` regex matches unnumbered metadata but not the `#<number>` form, so a prompt can describe a PR body or description write without requiring `create_or_update_draft_pr`.

3. **Action-target order "Add label to PR #93" missed** — The unsupported GitHub mutation detector accepts fields after the PR target or direct "label PR" wording, but does not accept "add label to PR" where the field precedes the target and includes "to", allowing that write intent to be treated as read-only.

4. **Quoted/parenthesized filename false negatives** — Valid standalone repository filenames wrapped in quotes or parentheses (`"README.md"`, `(README.md)`) are path-recognition false negatives; `_EXPLICIT_FILE_TARGET_RE` requires start/whitespace before and whitespace/end after the filename, so quote and parenthesis delimiters prevent matching.

## Acceptance boundary

The v9 remediation is complete only when the Decision commit and generated Gate commit are separate; `PRE_EXECUTION_AUTHORIZED` is 18/18 PASS with `blocking_reasons=[]` before source changes; all four findings are remediated with regression tests in one implementation attempt; `python -m pytest tests/test_supervisor_validate.py -q -k operation_prompt_consistency` passes; `python -m pytest tests/test_supervisor_validate.py tests/test_repository_hygiene.py -q` passes; `python -m pytest -q` passes; `git diff --check 16526801bda2a816fc707342f903c1ad037de9bd..HEAD` passes; each of the four v08 probes classifies correctly against the final code; exact-head CI, Decision Preflight, and State Gate succeed; the v08 audit file SHA-256 remains `81943cf31b1bb0e3ebfd685dfa9faf2b3ad08bf6ef021e594babab2b25af9d0e`; v07 remains hash-only and unread; PR #93 remains Open, Draft, and unmerged; no new branch, Issue, PR, or audit version is created. Success is `V08_FINDINGS_REMEDIATED_AWAITING_OWNER_MERGE_REVIEW`. Any drift, hash mismatch, scope conflict, Gate block, or test failure must stop as `BLOCKED_WITH_EXACT_EVIDENCE` without retry or repair.
