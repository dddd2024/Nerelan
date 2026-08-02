# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260802_issue101_platform_v1_scope_freeze_v1",
  "round_id": "round_20260802_issue101_platform_v1_scope_freeze_v1",
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
  "follows_last_decision_id": "decision_20260802_issue100_platform_v1_authority_collector_v4",
  "follows_last_round_id": "round_20260802_issue100_platform_v1_authority_collector_v4",
  "previous_audit_outcome": "PLATFORM_V1_V4_ACCEPTED_AS_PROVIDER_FREE_EXPERIMENTAL_BASELINE",
  "workstream_id": "issue101-platform-v1-scope-freeze",
  "source_issue": 101,
  "parent_issue": 90,
  "predecessor_issue": 100,
  "active_pr": 97,
  "required_branch": "agent/platform-v1-openhands-codex-acp",
  "starting_head": "2e6dd422188c3c77928c4496049f763f81048ba7",
  "activation_base_sha": "705a0bfd6638d51c688752f154433020225c4e99",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": true,
  "pr_body_update_allowed": true,
  "pr_comment_allowed": true,
  "issue_comment_allowed": true,
  "merge_allowed": true,
  "mark_ready_allowed": true,
  "allowed_merge_method": "merge",
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_work_item_publication_allowed": false,
  "repair_attempt_limit": 0,
  "product_code_changes_allowed": false,
  "test_semantics_changes_allowed": false,
  "new_security_hardening_allowed": false,
  "trusted_host_live_probe_allowed": false,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
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
      "command": "git diff --check 705a0bfd6638d51c688752f154433020225c4e99..HEAD",
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
      "command_id": "test.pytest_platform_v1",
      "command": "python -m pytest tests/platform_v1 -q",
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
      "command_id": "test.pytest_supervisor_mainline_integration",
      "command": "python -m pytest tests/test_supervisor_validate.py tests/test_mainline_landing.py tests/test_integration_baseline.py -q",
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
      "command": "git push origin agent/platform-v1-openhands-codex-acp",
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
      "command_id": "observation.workflow_runs",
      "command": "gh run list --repo dddd2024/reverse-agent --commit <EXACT_HEAD> --json attempt,conclusion,databaseId,event,headBranch,headSha,name,status,workflowDatabaseId,workflowName",
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
      "command_id": "publication.issue101_comment",
      "command": "gh issue comment 101 --repo dddd2024/reverse-agent --body-file -",
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
      "command_id": "publication.pr_comment",
      "command": "gh pr comment 97 --repo dddd2024/reverse-agent --body-file -",
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
    "project_state/mainline_merge_intents/archive/pr97_v4.json",
    "docs/platform_v1/adr-001-component-compatibility.md",
    "docs/platform_v1/component-lock.json"
  ],
  "reference_paths": [
    "docs/supervisor/audit-result.schema.json",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py",
    "tests/test_repository_hygiene.py",
    "tests/test_supervisor_validate.py",
    "tests/test_integration_baseline.py",
    "tests/test_mainline_landing.py",
    "tests/test_project_gate.py",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/legacy_adapter.py",
    "reverse_agent/control_plane/transition.py",
    "reverse_agent/mainline_landing.py",
    "reverse_agent/github_remote_verifier.py",
    "reverse_agent/project_audits.py",
    ".codex-skills/registry.json",
    ".github/workflows/state-gate.yml",
    ".github/workflows/decision-preflight.yml",
    ".github/workflows/ci.yml",
    "reverse_agent/platform_v1/**",
    "tests/platform_v1/**"
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
    ".github/workflows/ci.yml",
    "reverse_agent/**",
    "tests/**",
    "README.md",
    "AGENTS.md",
    "docs/roadmap/MINIMAL_AI_DEVELOPMENT_INTEGRATION_PLAN.md",
    "deploy/**",
    "examples/**",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifactindex.json",
    "project_state/mainline_merge_intents/archive/pr97_v1.json",
    "project_state/mainline_merge_intents/archive/pr97_v2.json",
    "project_state/mainline_merge_intents/archive/pr97_v3.json",
    "pyproject.toml",
    "docs/supervisor/audit-result.schema.json",
    "docs/supervisor/audit-instructions.md",
    "scripts/supervisor_context.py",
    "scripts/supervisor_publish.py",
    "scripts/supervisor_validate.py"
  ],
  "forbidden_operations": [
    "shadow-audit generation or execution",
    "invoke a second model or nested agent",
    "live publication or apply_result",
    "live generated Work Item publication",
    "new issue",
    "direct push to main",
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
    "modify product code under reverse_agent/**",
    "modify test semantics under tests/**",
    "modify workflow files under .github/workflows/**",
    "delete or modify unknown ignored or untracked files",
    "skip xfail delete or weaken tests to manufacture green status",
    "add Temporal LiteLLM Langfuse Spec Kit or specialized reverse tooling",
    "add custom frontend second executor new database custom sandbox or custom agent loop",
    "fork or copy OpenHands source",
    "expose long-lived credentials to task code",
    "close sandbox isolation",
    "claim live compatibility from fixtures or documentation",
    "manufacture live success without trusted-host probe results",
    "accept caller-supplied collection_mode=live or trusted provenance as live evidence",
    "accept caller-supplied pass/fail booleans or CI success lists as trusted truth in the live path",
    "fall back to untrusted changed_paths test_results or ci_checks when trusted evidence is empty",
    "accept caller-supplied Work Item or authority digest as live authority via stdin",
    "execute caller-supplied shell text or test_command from stdin",
    "use shell=True in production command execution",
    "request unsupported gh pr checks JSON fields",
    "confuse baseline job name with CI workflow name",
    "accept empty conclusion as success for completed workflow runs",
    "retry BLOCKED_APPROVAL automatically without a new approved Work Item",
    "run or claim the trusted-host OpenHands/Codex live probe",
    "create the next repair Issue or propose a new F-numbered finding"
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
    "merge_allowed": true,
    "mark_ready_allowed": true,
    "auto_merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "git push origin agent/platform-v1-openhands-codex-acp",
      "gh run list --repo dddd2024/reverse-agent --commit <EXACT_HEAD> --json attempt,conclusion,databaseId,event,headBranch,headSha,name,status,workflowDatabaseId,workflowName",
      "gh issue comment 101 --repo dddd2024/reverse-agent --body-file -",
      "gh pr comment 97 --repo dddd2024/reverse-agent --body-file -"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "project_state/mainline_merge_intents/**",
    "docs/platform_v1/**"
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
    },
    {
      "pattern": "docs/platform_v1/**",
      "minimum_risk": "R2"
    }
  ]
}
```

## Goal

Freeze Platform V1 as a provider-free experimental reference implementation and ratify the exact product tree at head `2e6dd422188c3c77928c4496049f763f81048ba7` for Owner merge. This is a finalization task, not a rework round. No product code, test semantics, workflow files, or new security hardening may change. The Decision ratifies the existing v4 product tree, archives the v4 merge intent verbatim as `archive/pr97_v4.json`, and creates a new active merge intent binding the scope-freeze Decision, the accepted product head, the canonical workflow/event requirements, and a bounded expiry. The product definition is: Platform V1 is a provider-free experimental reference implementation. It is not a production trusted executor, not an unattended R2/R3 platform, not a cryptographically rooted trust system, and not a verified live OpenHands/Codex integration. Trusted-host OpenHands/Codex compatibility remains unverified. R2/R3 live execution remains blocked pending a separate approved live-probe task. The executor must not mark Ready, merge, auto-merge, push main, release, deploy, access credentials, or run the trusted-host probe. The terminal status is `PR97_EXPERIMENTAL_BASELINE_READY_FOR_OWNER_MERGE` after exact-head CI, Decision Preflight, State Gate push, and State Gate pull_request all succeed.

## Acceptance boundary

The Platform V1 scope freeze is complete only when: the Decision commit and generated Gate commit are separate; `PRE_EXECUTION_AUTHORIZED` is 18/18 PASS with `blocking_reasons=[]` before the finalization commit; the finalization commit only modifies `project_state/mainline_merge_intents/active.json`, `project_state/mainline_merge_intents/archive/pr97_v4.json`, `docs/platform_v1/adr-001-component-compatibility.md`, and `docs/platform_v1/component-lock.json`; the v4 active intent is archived verbatim to `project_state/mainline_merge_intents/archive/pr97_v4.json`; the new active intent binds `source_pr: 97`, `locked_base_sha: 705a0bfd...`, `accepted_product_head: 2e6dd422...`, `allowed_merge_method: merge`, exact scope-freeze Decision content SHA-256, exact scope-freeze Command Plan SHA-256, `classification: provider_free_experimental_baseline`, `live_compatibility_verified: false`, canonical workflow/event requirements, and a bounded expiry; `git diff --name-only 2e6dd422..HEAD` contains only the 10 authorized governance/status paths; `python -m pytest tests/platform_v1 -q` passes with zero failures; `python -m pytest tests/test_supervisor_validate.py tests/test_mainline_landing.py tests/test_integration_baseline.py -q` passes; `python -m pytest tests/test_project_gate.py -q` passes; `git diff --check 705a0bfd..HEAD` passes; exact-head CI, Decision Preflight, State Gate push, and State Gate pull_request succeed; the PR remains Draft and unmerged. The terminal status is `PR97_EXPERIMENTAL_BASELINE_READY_FOR_OWNER_MERGE`. Any scope conflict, need to change product code or test semantics, credential exposure, idempotency failure, Gate block, or required-suite failure must stop as `BLOCKED_WITH_EXACT_EVIDENCE` without retry or repair.
