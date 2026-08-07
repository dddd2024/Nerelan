# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_issue126_codex_heterogeneous_compat_v2",
  "round_id": "round_20260807_issue126_codex_heterogeneous_compat_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260807_pr121_final_owner_authority_v4",
  "follows_last_round_id": "round_20260807_pr121_final_owner_authority_v4",
  "previous_audit_outcome": "PR121_V4_FINAL_OWNER_AUTHORITY_READY_FOR_REMOTE_AUDIT",
  "workstream_id": "issue126-codex-heterogeneous-compat-v2",
  "source_issue": 126,
  "required_branch": "owner/issue126-codex-compat-v1",
  "activation_base_sha": "9f9b4336c58777b30eb45a85c9c2d4253ba993c1",
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
  "bounded_codex_upgrade_allowed": true,
  "codex_install_method_must_be_confirmed": true,
  "repair_attempt_limit": 2,
  "infrastructure_retry_limit": 2,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_COMPLETE",
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "project_state/decisions/decision_20260807_issue126_codex_heterogeneous_compat_v2.md"
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
      "command_id": "observation.git_merge_base",
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
      "allowed_mutated_paths": [
        "project_state/gates/startup_snapshot.json"
      ]
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
      "command_id": "observation.codex_source",
      "command": "(Get-Command codex).Source",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_where",
      "command": "where.exe codex",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_version_old",
      "command": "codex --version",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_login",
      "command": "codex login status",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.codex_help",
      "command": "codex --help",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.npm_list",
      "command": "npm list -g @openai/codex --depth=0",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.npm_prefix",
      "command": "npm config get prefix",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.codex_upgrade",
      "command": "npm install -g @openai/codex@latest",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_install", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [],
      "allowed_only_after_validation": true,
      "validation_note": "May only execute after PRE_EXECUTION_AUTHORIZED from v2 gate preflight."
    },
    {
      "command_id": "observation.codex_version_new",
      "command": "codex --version",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "observation.codex_login_post",
      "command": "codex login status",
      "phase": "observation",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "experiment.codex_baseline_openai",
      "command": "codex exec",
      "phase": "experiment",
      "required": false,
      "expected_exit_codes": [0, 1, 2],
      "execution_surface": "local",
      "operations": ["model_execution", "network_access", "file_mutation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": []
    },
    {
      "command_id": "validation.git_diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["diff_validation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.git_diff_name_only",
      "command": "git diff --name-only origin/main...HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.secret_scan",
      "command": "git diff --cached",
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
        "project_state/decision_packet.md",
        "project_state/decisions/**",
        "project_state/gates/**",
        "docs/research/**"
      ]
    },
    {
      "command_id": "publication.git_push",
      "command": "git push origin owner/issue126-codex-compat-v1",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/decisions/**",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.md",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.json",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07-v2.md",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07-v2.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
    "project_state/schemas/**",
    "project_state/decisions/decision_20260807_issue126_codex_heterogeneous_compat_v1.md",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.md",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.json"
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
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
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
    "credential_access",
    "credential_publication",
    "external_reverse_tool_invocation",
    "runner_dispatch",
    "destructive",
    "unbounded_network_access",
    "reset_hard",
    "git_clean",
    "merge",
    "mark_ready"
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
    "bounded_codex_upgrade_allowed": true,
    "codex_upgrade_method": "npm_install_global_or_standalone_updater_only",
    "local_network_exceptions": [
      "git push origin owner/issue126-codex-compat-v1",
      "codex exec",
      "npm install -g @openai/codex@latest"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/decisions/**",
    "project_state/gates/**",
    "docs/research/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/decisions/**", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #126 Round C v2 rework.

v1 findings accepted (C126-F1 through C126-F7). v1 Decision `decision_20260807_issue126_codex_heterogeneous_compat_v1` is immutable and NOT modified.

This v2 round is NOT a product implementation task. Sole objective:

```
Correct Round C v1 environment blockage and premature conclusions
-> establish at least one real working Codex CLI single-agent path
-> with third-party provider, complete heterogeneous matrix
-> output final architecture conclusion only when evidence sufficient
```

## Codex install method and bounded upgrade

v1 did NOT authorize Codex upgrade. This v2 authorizes it ONLY after v2 Decision is committed and v2 gate preflight reports PRE_EXECUTION_AUTHORIZED.

Install method identification (mandatory, before any upgrade):

```
(Get-Command codex).Source
where.exe codex
codex --version
codex --help
codex login status
npm list -g @openai/codex --depth=0
npm config get prefix
```

These must produce NO credential output.

If npm-managed (confirmed):
```
npm install -g @openai/codex@latest
```

If standalone-managed and CLI provides a documented updater:
```
codex update
```

Never use both. If install method cannot be reliably determined:
```
ISSUE126_BLOCKED_CODEX_INSTALL_METHOD_AMBIGUOUS
```
Stop. Do not blindly reinstall.

After upgrade, record:
```
old Codex version
new Codex version
resolved executable path
install method
```

Do NOT record auth token, cookie, API key, or auth.json content.

## Credential boundary

`model_api_invocation_allowed=true` and `real_provider_credential_allowed=false` means:

```
Codex CLI may use its own pre-existing authenticated sessions
```

NOT:

```
The Agent may read, print, or copy any API key, token, or auth blob
```

Never read/print:
```
Get-Content ~/.codex/auth.json
cat auth.json
echo $env:*KEY*
Get-ChildItem Env:
```

Only non-sensitive metadata recorded: profile name, provider name/type, model name, env variable NAME (not value), auth presence (YES/NO).

## Experiments

Disposable fixture:
```
F:\reverse-agent-labs\issue126-codex-compat-v2\openai\
```

Content:
```
input.txt = alpha
```

Task:
```
Read input.txt.
Run one harmless shell command.
Create output.txt containing exactly:
alpha-ok
Verify the file.
Reply with PASS only after verification.
```

Use current CLI's actual legal `codex exec` flags (ephemeral, JSON output if supported, isolated fixture, workspace-write, no repo source mutation).

OpenAI PASS requires ALL:
```
model session actually starts
tool call occurs
input.txt actually read
output.txt actually created
content == alpha-ok
verification actually runs
Codex exits successfully
```

If OpenAI baseline fails, classify into:
```
CLI_VERSION / MODEL_CATALOG / AUTH_ROUTE / NETWORK / CLOUDFLARE / PROXY_VPN / SERVICE / UNKNOWN
```

Use bounded retries only. Do not randomly try models.

If blocked:
```
ISSUE126_BLOCKED_OPENAI_EXEC_<CLASS>
```

## Milestone

If OpenAI baseline succeeds, record:
```
SINGLE_AGENT_CODEX_PATH_ESTABLISHED = TRUE
```

This enables Issue #127 technical preconditions. Do NOT start #127 in this round.

## Third-party provider

Check Codex config non-sensitive metadata only:
```
profile name, provider name, model name, base URL, wire API, env_key NAME
```

Do NOT read env_key VALUE, API key, auth file, token, cookie.

If no third-party Codex profile exists after upgrade:
```
ISSUE126_SINGLE_AGENT_PATH_ESTABLISHED_NEEDS_THIRD_PARTY_PROFILE
```
Architecture: INCONCLUSIVE, OpenAI: PASS, third-party: NOT_TESTED, cross-provider: NOT_TESTED.

## Auth coexistence

Must have OpenAI process + Provider A process with time overlap. Both must complete independent fixtures. Re-run OpenAI baseline after to confirm ChatGPT auth intact.

## Native MultiAgent

Only after ordinary baseline succeeds. Test stable `multi_agent` path first. Use marker-based handoff:
```
ASSIGNMENT_MARKER_126_C2_A7
RESULT_MARKER_126_C2_B9
```

Parallelism must use runtime events/timestamps, not agent self-report.

## v1 report correction

Correct v1 report (must retain historical evidence):

Mark v1 as `historical blocked environment result`.

Replace:
```
auth coexistence PASS (trivially)
-> NOT_TESTED
```

Replace baseless:
```
UNSUPPORTED
-> NOT_TESTED / BLOCKED_ENVIRONMENT
```

Delete unsupported claim:
```
ChatGPT auth appears designed for interactive TUI only
```

## Architecture field

If Issue #126 acceptance not satisfied:
```
architecture_decision_status: INCONCLUSIVE_REWORK_REQUIRED
architecture_recommendation: null
```

Only output CODEX_NATIVE / EXTERNAL_ORCHESTRATION / HYBRID as accepted when:
```
OpenAI + at least one third-party ordinary path
+ real auth coexistence
+ native MultiAgent control
+ cross-provider capability known
```

## Local hygiene

`.frontend_stage/**` and `.platform_v1_runtime/runs.sqlite3` must not be staged. Git diff must not include them. No product code modified.

## Publication

Only commit and normal push to `owner/issue126-codex-compat-v1`. No PR. No merge. No mark-ready.
