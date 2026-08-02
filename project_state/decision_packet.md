# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260802_issue95_scoped_merge_gate_repair_v11",
  "round_id": "round_20260802_issue95_scoped_merge_gate_repair_v11",
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
  "follows_last_decision_id": "decision_20260802_issue95_pr93_merge_readiness_closure_v10",
  "follows_last_round_id": "round_20260802_issue95_pr93_merge_readiness_closure_v10",
  "previous_audit_outcome": "PR93_MERGE_READINESS_CI_FAILED_UNSCOPED_LEGACY_SUITE",
  "workstream_id": "issue95-scoped-merge-gate-repair-v11",
  "source_issue": 95,
  "parent_issue": 90,
  "active_pr": 93,
  "required_branch": "agent/codex-supervisor-foundation-v0",
  "starting_head": "33d1272e1c8a4d9b51d361d091ea28adf85c414b",
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
      "command_id": "test.pytest_codex_skills",
      "command": "python -m pytest tests/test_codex_skills.py -q",
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
      "command_id": "test.pytest_integration_mainline_audits",
      "command": "python -m pytest tests/test_integration_baseline.py tests/test_mainline_landing.py tests/test_project_audits.py -q",
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
      "command_id": "test.pytest_supervisor_hygiene",
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
      "command_id": "test.pytest_project_gate",
      "command": "python -m pytest tests/test_project_gate.py -q",
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
    ".github/workflows/ci.yml",
    "tools/sync_codex_skills.ps1",
    "tests/test_codex_skills.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/mainline_merge_intents/archive/pr93_v10.json",
    "docs/testing/legacy-full-suite-debt.md"
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
    "project_state/artifactindex.json",
    "AGENTS.md",
    "pyproject.toml",
    "docs/supervisor/audit-result.schema.json",
    "docs/supervisor/audit-instructions.md",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py",
    "tests/test_repository_hygiene.py",
    "tests/test_supervisor_validate.py",
    "tests/test_integration_baseline.py",
    "tests/test_local_reverse_forced_ida_extract.py"
  ],
  "forbidden_operations": [
    "shadow-audit generation or execution",
    "generate v12 or any other audit version",
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
    "skip xfail delete or weaken tests to manufacture green status",
    "modify dedicated reverse-tool production code or reverse-tool tests",
    "add frontend database workflow engine Spec Kit or specialized reverse tooling"
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
    "project_state/mainline_merge_intents/archive/pr93_v10.json",
    ".github/workflows/ci.yml",
    "tools/sync_codex_skills.ps1",
    "tests/test_codex_skills.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "docs/testing/legacy-full-suite-debt.md"
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

Establish scoped merge gates for PR #93 by adding `fetch-depth: 0` to CI checkout, fixing `tools/sync_codex_skills.ps1` for Linux dot-prefixed hidden directory access, defining required CI gate suites covering the reusable base-platform surfaces, documenting legacy reverse-tool test debt, archiving the v10 PR93 intent, and rebinding the active intent to the v11 Decision and command plan. Do not add reverse tooling, frontend, database, workflow engine, or Spec Kit.

## v10 CI failure dispositions

1. **PowerShell hidden-directory portability — 5 failures** in `tests/test_codex_skills.py`. Root cause: `Get-Item` cannot see `.codex-skills` on Linux without `-Force`. Fix: add `-Force` to `Get-Item` in `tools/sync_codex_skills.ps1`.

2. **Shallow Git checkout — 6 failures** across `tests/test_integration_baseline.py` and `tests/test_mainline_landing.py`. Root cause: `fetch-depth: 1` omits historical git objects needed by baseline, PR60 recovery, and pre-merge simulation tests. Fix: set `fetch-depth: 0` in CI checkout.

3. **Dedicated reverse-tool tests — 4 failures** in `tests/test_local_reverse_forced_ida_extract.py`. Root cause: fixtures reference local Windows binaries and reverse-specific behavior outside the reusable base-platform scope. Fix: document as legacy debt in `docs/testing/legacy-full-suite-debt.md`; do not require them as merge gates.

4. **PR93 simulation defect — 1 failure** in `test_production_pre_merge_simulation`. Root cause: shallow checkout lacks base object `16526801...`. Fix: resolved by `fetch-depth: 0`.

## Acceptance boundary

The v11 scoped merge-gate repair is complete only when the Decision commit and generated Gate commit are separate; `PRE_EXECUTION_AUTHORIZED` is 18/18 PASS with `blocking_reasons=[]` before implementation; CI uses `fetch-depth: 0`; `sync_codex_skills.ps1` handles dot-prefixed directories on Linux; required CI gate suites cover focused, supervisor/hygiene, codex-skills, integration-baseline/mainline-landing/project-audit, and project-gate tests; the repository-wide diagnostic step is nonblocking and labelled as legacy debt with its failing node set recorded in `docs/testing/legacy-full-suite-debt.md`; the v10 active PR93 intent is archived verbatim as `project_state/mainline_merge_intents/archive/pr93_v10.json`; the new active intent binds the exact v11 Decision content SHA-256 and command-plan SHA-256 with `source_pr: 93`, locked base `16526801...`, merge method `merge`, canonical four workflows, and expiry no later than `2026-08-09T23:59:59Z`; all required suites pass in both the primary worktree and a clean detached worktree; `git diff --check 16526801bda2a816fc707342f903c1ad037de9bd..HEAD` passes; exact-head CI (all required scoped gates), Decision Preflight, State Gate push, and State Gate pull_request all succeed; PR #93 remains Open, Draft, and unmerged; no new branch, Issue, PR, or audit version is created. Success is `PR93_SCOPED_GATES_GREEN_AWAITING_OWNER_MERGE`. Any drift, scope conflict, Gate block, required-suite failure, or new non-legacy failure must stop as `BLOCKED_WITH_EXACT_EVIDENCE` without retry or repair.
