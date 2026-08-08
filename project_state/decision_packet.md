# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue131_opencode_real_executor_v2",
  "round_id": "round_20260808_issue131_opencode_real_executor_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue131_opencode_real_executor_v1",
  "follows_last_round_id": "round_20260808_issue131_opencode_real_executor_v1",
  "previous_audit_outcome": "ISSUE131_V1_BLOCKED_CLI_NOT_FOUND_WITH_PACKAGE_NAME_FALSE_NEGATIVE",
  "workstream_id": "issue131-opencode-real-executor-v2",
  "source_issue": 131,
  "parent_issue": 90,
  "enables_issue": 127,
  "related_research_issue": 126,
  "required_branch": "owner/issue131-opencode-real-executor-v1",
  "starting_head": "29d44637ed7c33db390d5cf1bf64ae2f77609c0b",
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
  "package_installation_allowed": true,
  "allowed_package_installations": ["npm:opencode-ai@latest"],
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": true,
  "bounded_external_source_access_allowed": true,
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
      "command_id": "observation.npm_package",
      "command": "npm view opencode-ai name version dist-tags.latest",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_metadata_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "experiment.install_opencode_cli",
      "command": "npm install -g opencode-ai@latest",
      "phase": "experiment",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_install", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "allowed_only_after_validation": true,
      "validation_note": "Only the official OpenCode package name documented at opencode.ai is authorized. Do not install a package named 'opencode', OpenHands, or any other executor."
    },
    {
      "command_id": "observation.opencode_where",
      "command": "where.exe opencode",
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
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
      "expected_exit_codes": [0],
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
      "validation_note": "Record only provider/model identifiers. Do not read/print auth files, API keys, tokens, cookies, headers, raw config, or environment values. If the CLI cannot see an already-configured non-OpenAI SenseNova-family provider/model, stop with MODEL_NOT_CONFIGURED; do not copy Desktop credentials/config into the CLI."
    },
    {
      "command_id": "fixture.prepare",
      "command": "python -",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_fixture_file_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Execute only after an existing non-OpenAI provider/model is visible. May create/reset only F:/reverse-agent-labs/issue131-opencode-executor/** and input.txt=alpha."
    },
    {
      "command_id": "experiment.opencode_run_fixture",
      "command": "opencode run",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "external_fixture_file_mutation", "tool_execution"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "validation_note": "Use only an already-visible non-OpenAI SenseNova-family provider/model. Derive flags from local help. Run only under F:/reverse-agent-labs/issue131-opencode-executor. Use --format json if supported. No provider/auth/config mutation."
    },
    {
      "command_id": "fixture.verify",
      "command": "python -",
      "phase": "validation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["deterministic_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "If fixture executed, independently verify output.txt exists and content equals alpha-ok. Do not accept Agent prose as evidence."
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
        "docs/research/opencode-real-executor-2026-08-08-v2.md",
        "docs/research/opencode-real-executor-2026-08-08-v2.json"
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
    "docs/research/opencode-real-executor-2026-08-08-v2.md",
    "docs/research/opencode-real-executor-2026-08-08-v2.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/task_service.py",
    "project_state/schemas/**",
    "docs/research/opencode-real-executor-2026-08-08.md",
    "docs/research/opencode-real-executor-2026-08-08.json"
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
    "project_state/audits/**",
    "docs/research/opencode-real-executor-2026-08-08.md",
    "docs/research/opencode-real-executor-2026-08-08.json"
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
      "npm view opencode-ai name version dist-tags.latest",
      "npm install -g opencode-ai@latest",
      "opencode run",
      "git push origin owner/issue131-opencode-real-executor-v1"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "docs/research/opencode-real-executor-2026-08-08-v2.md",
    "docs/research/opencode-real-executor-2026-08-08-v2.json"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #131 v2 corrects the v1 package-name false negative and proves the shortest quota-independent real executor path without changing reverse-agent product code.

Owner audit accepted the v1 host observation that the OpenCode Desktop app is installed but no `opencode` CLI is currently on PATH. It rejected only this inference from the v1 research report:

```text
npm view opencode -> 404
therefore no public OpenCode CLI package exists
```

The official OpenCode documentation uses this Windows/NPM installation command:

```text
npm install -g opencode-ai
```

Therefore v2 authorizes exactly one environment installation: `opencode-ai@latest` through the host's existing npm. No repository dependency file may change.

After installation, observe the actual CLI. If `opencode models` exposes an already-configured non-OpenAI SenseNova-family provider/model, run one disposable fixture under:

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

If the installed CLI does not inherit/see an already-configured non-OpenAI provider/model, stop with `MODEL_NOT_CONFIGURED`. Do not copy, migrate, read, print, or recreate Desktop credentials/configuration.

## Acceptance

1. v2 Decision commit precedes all v2 generated gate/report changes and all package/model execution.
2. `transition-lint` passes.
3. preflight is `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`.
4. `npm view opencode-ai ...` succeeds and identifies the exact package/version before installation.
5. Only `npm install -g opencode-ai@latest` is permitted; no OpenHands/Codex/other executor install.
6. Post-install `where.exe opencode`, `opencode --version`, and `opencode run --help` succeed.
7. `opencode models` is treated as safe provider/model metadata only; no auth/config/env values are printed.
8. If no already-visible non-OpenAI SenseNova-family model exists, stop safely with `ISSUE131_V2_BLOCKED_MODEL_NOT_CONFIGURED` and do not configure one.
9. If a qualifying model exists, one `opencode run` fixture proves real read -> tool/shell -> edit -> deterministic verify using filesystem/event evidence rather than Agent prose.
10. PASS sets `REAL_SINGLE_AGENT_EXECUTOR_PATH_ESTABLISHED = TRUE`, `SELECTED_EXECUTOR_PATH = OPENCODE_RUN`, and `INTEGRATION_SURFACE_RECOMMENDATION = OPENCODE_RUN_CHILD_PROCESS`.
11. `git diff --check` passes; product delta remains zero; v1 reports remain immutable.
12. Only generated gates and sanitized v2 reports are locally committed/pushed after the Owner-created Decision commit.
13. No PR, Ready, merge, main push, provider configuration, credential access, Codex invocation, OpenHands invocation, multi-Agent work, release, or deployment.

## Publication boundary

The local Agent may generate v2 gates, install the exact authorized external CLI package, run the bounded fixture if an existing provider/model is visible, commit only generated v2 gates/reports, and normal-push `owner/issue131-opencode-real-executor-v1`. It must then stop for Owner exact-head audit. #127 product implementation remains unauthorized in this Decision.
