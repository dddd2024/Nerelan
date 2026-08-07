# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_issue130_real_executor_spike_v1",
  "round_id": "round_20260807_issue130_real_executor_spike_v1",
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
  "previous_audit_outcome": "PR129_MERGED_PROVIDER_FREE_TASK_PLANE_READY_FOR_REAL_EXECUTOR_SPIKE",
  "workstream_id": "issue130-real-executor-spike-v1",
  "source_issue": 130,
  "parent_issue": 90,
  "enables_issue": 127,
  "related_research_issue": 126,
  "required_branch": "owner/issue130-real-executor-spike-v1",
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
  "real_provider_credential_allowed": false,
  "model_execution_required": true,
  "bounded_external_source_access_allowed": true,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "codex_upgrade_allowed": false,
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "candidate_order": [
    "CODEX_CUSTOM_PROVIDER",
    "OPENHANDS_CLI"
  ],
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
      "allowed_mutated_paths": [
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
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "observation.codex_where",
      "command": "where.exe codex",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_version",
      "command": "codex --version",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_exec_help",
      "command": "codex exec --help",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_profile_metadata",
      "command": "python -",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["credential_safe_metadata_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Inline Python may parse Codex config only to emit an explicit safe whitelist: provider/profile IDs, model IDs, base URL host, wire_api, env_key NAME, requires_openai_auth, and env-var presence boolean. It must never emit environment values, auth blobs, headers, cookies, tokens, or raw config text."
    },
    {
      "command_id": "experiment.codex_custom_provider_fixture",
      "command": "codex exec",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "external_fixture_file_mutation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "validation_note": "May use only an already-configured non-OpenAI custom provider/profile and only inside F:/reverse-agent-labs/issue130-real-executor/codex-custom. Do not use OpenAI official quota and do not mutate provider config."
    },
    {
      "command_id": "observation.openhands_where",
      "command": "where.exe openhands",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.openhands_version",
      "command": "openhands --version",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.openhands_help",
      "command": "openhands --help",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.openhands_fixture",
      "command": "openhands",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "external_fixture_file_mutation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "validation_note": "Use only if OpenHands is already installed and already configured with a non-OpenAI provider/model. Derive actual headless flags from local --help; run only in F:/reverse-agent-labs/issue130-real-executor/openhands. No installation or provider configuration is allowed."
    },
    {
      "command_id": "fixture.prepare_and_verify",
      "command": "python -",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_fixture_file_mutation", "deterministic_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "May create/reset/verify only F:/reverse-agent-labs/issue130-real-executor/**. Must never mutate F:/reverse-agent tracked source."
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
        "docs/research/real-executor-spike-2026-08-07.md",
        "docs/research/real-executor-spike-2026-08-07.json"
      ]
    },
    {
      "command_id": "publication.git_push",
      "command": "git push origin owner/issue130-real-executor-spike-v1",
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
    "docs/research/real-executor-spike-2026-08-07.md",
    "docs/research/real-executor-spike-2026-08-07.json"
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
    "docs/model-access.md",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "create_pr",
    "draft_pr_creation",
    "pr_body_update",
    "pr_comment",
    "issue_comment",
    "merge",
    "mark_ready",
    "auto_merge",
    "force_push",
    "rebase",
    "amend",
    "squash",
    "tag_or_release",
    "release",
    "deployment",
    "credential_value_read",
    "credential_publication",
    "auth_blob_read",
    "environment_dump",
    "provider_profile_write",
    "provider_configuration_mutation",
    "package_install",
    "codex_upgrade",
    "openhands_install",
    "multi_agent",
    "scheduler_implementation",
    "product_code_mutation",
    "unknown_binary_execution",
    "destructive",
    "unbounded_network_access",
    "reset_hard",
    "git_clean"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": true,
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
      "codex exec",
      "openhands",
      "git push origin owner/issue130-real-executor-spike-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "docs/research/real-executor-spike-2026-08-07.md",
    "docs/research/real-executor-spike-2026-08-07.json"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "docs/research/real-executor-spike-2026-08-07.md", "minimum_risk": "R1"},
    {"pattern": "docs/research/real-executor-spike-2026-08-07.json", "minimum_risk": "R1"}
  ]
}
```

## Goal

Issue #130 is a quota-independent real-executor feasibility spike for Issue #127.

PR #129 has already landed the provider-free Task API, durable TaskStore, ExecutorRouter, fixture executor, frontend HTTP flow, validation/evidence normalization and backend readback on `main@e4e23028c6c78c4ab9a8e032677e71370ace7627`.

This round must NOT modify any product code. It answers only:

```text
Does this Windows host already have one preconfigured real single-Agent execution path that can perform read -> shell/tool -> edit -> deterministic verify without OpenAI official Codex quota?
```

Candidate priority:

```text
1. CODEX_CUSTOM_PROVIDER
2. OPENHANDS_CLI
```

## Credential boundary

Credential values are never Owner/Agent-readable evidence.

Allowed sanitized facts only:

```text
provider/profile identifier
model identifier
base URL host or sanitized base URL
wire/API mode
env_key NAME only
env-key presence boolean
requires_openai_auth boolean
CLI version and capability flags
```

Forbidden output/access:

```text
API-key value
token value
cookie
auth.json
Authorization header value
provider HTTP header value
full environment dump
raw config dump
```

A metadata parser may read the Codex TOML only to emit the explicit whitelist above. If literal secret-bearing fields are detected, it must report only `SECRET_BEARING_CONFIG_FIELD_PRESENT=true` and skip that candidate rather than outputting the field value.

## Disposable fixture

Use only:

```text
F:\reverse-agent-labs\issue130-real-executor\codex-custom\
F:\reverse-agent-labs\issue130-real-executor\openhands\
```

For each attempted candidate prepare:

```text
input.txt = alpha
```

Agent task:

```text
Read input.txt.
Run one harmless shell/tool command.
Create output.txt containing exactly:
alpha-ok
Verify output.txt.
Reply PASS only after the verification succeeds.
```

PASS requires runtime evidence that the session started, real file/tool operations occurred, `output.txt` exists with exact content, deterministic verification ran, and the process/session completed successfully. Agent prose is insufficient.

## Candidate A — Codex custom provider

Do not call the official OpenAI provider in this spike.

Use only an already-existing custom Codex provider/profile. Do not add, edit, or migrate a provider. Derive legal invocation flags from local `codex exec --help`; do not guess flags. If no safe usable custom profile exists, classify `NOT_CONFIGURED` and proceed to OpenHands.

A custom-provider PASS establishes a practical Codex harness for #127 but does NOT satisfy #126's OpenAI-control or heterogeneous/native-MultiAgent architecture gate.

## Candidate B — OpenHands

Use only if `openhands` is already installed and already configured for a non-OpenAI model/provider. Derive headless invocation from local `openhands --help`; do not install the CLI or create provider configuration in this round.

## Result contract

Report exactly:

```text
REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = TRUE|FALSE
SELECTED_EXECUTOR_PATH = CODEX_CUSTOM_PROVIDER|OPENHANDS_CLI|null
```

If TRUE, also report a sanitized invocation shape and runtime evidence sufficient for Owner to authorize a fresh #127 implementation branch from current main. Do not start #127 product mutation in this round.

If both candidates are unavailable or blocked:

```text
ISSUE130_NEEDS_ONE_PRECONFIGURED_REAL_EXECUTOR
```

## Repository publication

Only generated gates and sanitized research evidence may be committed after preflight. No product code, tests, frontend, workflows, provider configuration or package files. Normal-push only to `owner/issue130-real-executor-spike-v1`, then STOP for Owner audit.

Terminal success with a real path:

```text
ISSUE130_REAL_EXECUTOR_PATH_READY_FOR_OWNER_AUDIT
```

Terminal without a preconfigured path:

```text
ISSUE130_NEEDS_ONE_PRECONFIGURED_REAL_EXECUTOR
```
