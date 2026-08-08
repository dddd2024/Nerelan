# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue131_opencode_real_executor_v1",
  "round_id": "round_20260808_issue131_opencode_real_executor_v1",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr129_provider_free_task_plane_landing_v5",
  "follows_last_round_id": "round_20260807_pr129_provider_free_task_plane_landing_v5",
  "previous_audit_outcome": "ISSUE130_V1_ACCEPTED_NO_PRECONFIGURED_CODEX_OR_OPENHANDS_EXECUTOR",
  "workstream_id": "issue131-opencode-real-executor-v1",
  "source_issue": 131,
  "parent_issue": 90,
  "enables_issue": 127,
  "related_research_issue": 126,
  "required_branch": "owner/issue131-opencode-real-executor-v1",
  "starting_head": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
  "activation_base_sha": "e4e23028c6c78c4ab9a8e032677e71370ace7627",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R3",
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
  "release_allowed": false,
  "deployment_allowed": false,
  "model_execution_required": true,
  "opencode_invocation_allowed": true,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": true,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 1,
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
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.git_main",
      "command": "git rev-parse origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.merge_base",
      "command": "git merge-base HEAD origin/main",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/startup_snapshot.json"]
    },
    {
      "command_id": "gate.transition_command_plan",
      "command": "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/command_plan.json", "project_state/gates/transition_command_plan_preview.json"]
    },
    {
      "command_id": "gate.transition_lint",
      "command": "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["gate_execution"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["project_state/gates/transition_preflight_result.json", "project_state/gates/bootstrap_state.json"]
    },
    {
      "command_id": "observation.opencode_where",
      "command": "where.exe opencode",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.opencode_version",
      "command": "opencode --version",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.opencode_run_help",
      "command": "opencode run --help",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.opencode_models",
      "command": "opencode models",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["credential_safe_metadata_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Record only provider/model identifiers needed to select the already-configured non-OpenAI model. Do not read or print auth files, API keys, tokens, cookies, headers, or environment values."
    },
    {
      "command_id": "fixture.prepare",
      "command": "python -",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_fixture_file_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "May create/reset only F:/reverse-agent-labs/issue131-opencode-executor/** and input.txt=alpha."
    },
    {
      "command_id": "experiment.opencode_run_fixture",
      "command": "opencode run",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "external_fixture_file_mutation", "tool_execution"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "validation_note": "Use the already-configured non-OpenAI SenseNova/OpenCode provider-model path only. Derive exact flags from local help. Run only in F:/reverse-agent-labs/issue131-opencode-executor. Capture --format json if supported. No provider/auth/config mutation."
    },
    {
      "command_id": "fixture.verify",
      "command": "python -",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["deterministic_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Independently verify output.txt exists and content equals alpha-ok. Do not accept Agent prose as evidence."
    },
    {
      "command_id": "validation.git_diff_check",
      "command": "git diff --check e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD",
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
      "command": "git diff --name-only e4e23028c6c78c4ab9a8e032677e71370ace7627..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.git_commit",
      "command": "git commit",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_commit"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/**",
        "docs/research/opencode-real-executor-2026-08-08.md",
        "docs/research/opencode-real-executor-2026-08-08.json"
      ]
    },
    {
      "command_id": "publication.git_push",
      "command": "git push origin owner/issue131-opencode-real-executor-v1",
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
    "docs/research/opencode-real-executor-2026-08-08.md",
    "docs/research/opencode-real-executor-2026-08-08.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
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
    "reverse_agent/**",
    "frontend/**",
    "tests/**",
    "project_state/mainline_merge_intents/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_value_access",
    "credential_publication",
    "provider_configuration_mutation",
    "package_installation",
    "codex_invocation",
    "openhands_invocation",
    "multi_agent",
    "destructive",
    "unbounded_network_access",
    "reset_hard",
    "git_clean",
    "merge",
    "mark_ready",
    "create_pr"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
    "opencode_invocation_allowed": true,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false,
    "remote_observation_read_only_allowed": true,
    "local_network_exceptions": [
      "opencode run",
      "git push origin owner/issue131-opencode-real-executor-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "docs/research/opencode-real-executor-2026-08-08.md",
    "docs/research/opencode-real-executor-2026-08-08.json"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #131 is a proof-only R3 round. It must establish whether the already-installed and already-configured OpenCode + non-OpenAI SenseNova path can be used as the first real single-Agent executor for Platform V1.

The only authorized live task is an external disposable fixture under:

```text
F:\reverse-agent-labs\issue131-opencode-executor\
```

with `input.txt = alpha` and the task:

```text
Read input.txt.
Run one harmless shell command that prints the current working directory.
Create output.txt containing exactly:
alpha-ok
Verify output.txt.
Only report PASS after verification succeeds.
```

PASS requires actual runtime evidence: real OpenCode process/session, selected non-OpenAI model/provider, file read, tool/bash action, real file mutation, independent exact-content verification, successful terminal result, sanitized JSON/event evidence, no credential exposure, and zero reverse-agent product mutation.

If PASS:

```text
REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = TRUE
SELECTED_EXECUTOR_PATH = OPENCODE_RUN
ISSUE131_OPENCODE_REAL_EXECUTOR_READY_FOR_OWNER_AUDIT
```

If blocked, classify exactly and stop without installing/configuring anything.

## Acceptance

1. Decision commit precedes all generated gate/report changes.
2. `transition-lint` passes.
3. preflight is `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
4. OpenCode CLI and `run` help are observed locally.
5. Only safe provider/model identifiers are recorded; no credential value/auth file/env dump is read or printed.
6. The selected model/provider is non-OpenAI and already configured before this round.
7. One `opencode run` fixture is attempted only after gate authorization.
8. `--format json` is used if supported by the installed CLI; tool/action events are summarized without secret content.
9. `output.txt` is independently verified to equal `alpha-ok` exactly.
10. `git diff --check` passes and final main..HEAD paths contain only Decision-authorized governance/research files.
11. No `reverse_agent/**`, `frontend/**`, `tests/**`, workflows, dependencies, provider config, credentials, or merge intent changes.
12. Normal push to the exact branch only. No PR, Ready, merge, release, deploy, rebase, force-push, clean, or hard reset.

## Publication boundary

The local Agent may commit generated gate artifacts and sanitized research evidence, then normal-push `owner/issue131-opencode-real-executor-v1`. It must stop for Owner exact-head audit. #127 product implementation is not authorized in this Decision.
