# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260802_issue95_pr93_merge_readiness_closure_v10",
  "round_id": "round_20260802_issue95_pr93_merge_readiness_closure_v10",
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
  "follows_last_decision_id": "decision_20260802_issue94_v08_findings_remediation_v9",
  "follows_last_round_id": "round_20260802_issue94_v08_findings_remediation_v9",
  "previous_audit_outcome": "V08_FINDINGS_REMEDIATED_FULL_SUITE_BLOCKED_BY_STALE_GOVERNANCE",
  "workstream_id": "issue95-pr93-merge-readiness-closure-v10",
  "source_issue": 95,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "f29145efe0b67583422f39eaf8e384fcb3dd7095",
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
      "command_id": "test.pytest_mainline_audits",
      "command": "python -m pytest tests/test_mainline_landing.py tests/test_project_audits.py -q",
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
      "command_id": "publication.issue95_comment",
      "command": "gh issue comment 95 --repo dddd2024/reverse-agent --body-file -",
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr67_v5.json",
    "tests/test_mainline_landing.py",
    "tests/test_project_audits.py",
    "tests/test_project_gate.py",
    ".github/workflows/ci.yml"
  ],
  "reference_paths": [
    "AGENTS.md",
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py",
    "tests/test_repository_hygiene.py",
    "tests/test_supervisor_validate.py",
    "project_state/decision_packet.md",
    "project_state/audits/audit_20260629_rework_required_audit_inventory_gate.md",
    "project_state/audits/audit_20260629_rework_required_clean_baseline_jobs_inventory_gate.md",
    "project_state/audits/audit_20260701_rework_required_audit_readiness_packet.md",
    "project_state/audits/audit_20260701_rework_required_current_handoff_packet_readiness_mismatch.md",
    "reverse_agent/project_gate.py",
    "reverse_agent/project_audits.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    ".codex-skills/registry.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
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
    "docs/supervisor/audit-instructions.md",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py",
    "tests/test_repository_hygiene.py",
    "tests/test_supervisor_validate.py"
  ],
  "forbidden_operations": [
    "shadow-audit generation or execution",
    "generate v11 or any other audit version",
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
    "modify paths outside the allowed implementation files and gate artifacts",
    "delete or modify unknown ignored or untracked files",
    "weaken validate_audits_dir or ignore malformed tracked audit records",
    "skip xfail delete or weaken tests to manufacture green status"
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
      "gh issue comment 95 --repo dddd2024/reverse-agent --body-file -",
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
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr67_v5.json",
    "tests/test_mainline_landing.py",
    "tests/test_project_audits.py",
    "tests/test_project_gate.py",
    ".github/workflows/ci.yml"
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
      "pattern": "project_state/mainline_merge_intents/**",
      "minimum_risk": "R2"
    }
  ]
}
```

## Goal

Restore PR #93 full-suite merge readiness by archiving the stale PR67 active merge intent, creating a new PR #93 active merge intent bound to the v10 Decision and command plan, converting hard-coded PR67 tests to generic active-intent tests, independently diagnosing the project-audits failure, and adding the full `python -m pytest -q` to GitHub CI. Do not generate another shadow audit, do not merge or mark ready, and do not broaden scope beyond the allowed implementation files.

## Three full-suite failure dispositions

1. **test_committed_pr67_intent_binds_exact_v5_authority** — The test hard-codes `decision_20260729_pr67_final_intent_rebind_v5` and reads `active.json` which still binds PR67. The Decision has since transitioned to v9/v10. Root cause: stale active intent + hard-coded PR67 identity. Fix: archive PR67 intent, replace active intent with PR #93 binding, convert test to read archived intent for PR67 assertions.

2. **test_production_pre_merge_simulation** — The test hard-codes `source_pr: 67` and `locked_base_sha: 68026521710c50fa9a70f3851472941605d9ead1`. The active intent now binds PR #93 with `locked_base_sha: 16526801...`. Root cause: hard-coded PR67 values in test. Fix: derive `source_pr` and `locked_base_sha` from the active intent.

3. **test_validate_audits_dir_accepts_current_audit_record** — The test is non-hermetic (reads real `project_state/audits/`). Two tracked audit files (`audit_20260701_rework_required_audit_readiness_packet.md` and `audit_20260701_rework_required_current_handoff_packet_readiness_mismatch.md`) use `json audit_result_summary` instead of `json audit_summary`, causing `validate_audits_dir` to report them as malformed. Root cause: non-hermetic test + pre-existing tracked audit format mismatch. Fix: make the test hermetic (use tmp_path with controlled audit files). Do not weaken `validate_audits_dir`.

## Acceptance boundary

The v10 merge-readiness closure is complete only when the Decision commit and generated Gate commit are separate; `PRE_EXECUTION_AUTHORIZED` is 18/18 PASS with `blocking_reasons=[]` before implementation; the PR67 intent is archived verbatim; the new PR #93 active intent binds the exact v10 Decision content SHA-256 and command-plan SHA-256; hard-coded PR67 tests are converted to generic active-intent tests; the project-audits test is made hermetic without weakening `validate_audits_dir`; CI runs `python -m pytest -q`; `python -m pytest tests/test_mainline_landing.py tests/test_project_audits.py -q` passes; `python -m pytest tests/test_supervisor_validate.py tests/test_repository_hygiene.py -q` passes; `python -m pytest -q` passes with exit code 0 in both the primary worktree and a clean detached worktree; `git diff --check 16526801bda2a816fc707342f903c1ad037de9bd..HEAD` passes; exact-head CI (including full-suite step), Decision Preflight, State Gate push, and State Gate pull_request all succeed; PR #93 remains Open, Draft, and unmerged; no new branch, Issue, PR, or audit version is created. Success is `PR53_FULL_SUITE_GREEN_AWAITING_OWNER_MERGE`. Any drift, scope conflict, Gate block, or test failure must stop as `BLOCKED_WITH_EXACT_EVIDENCE` without retry or repair.
