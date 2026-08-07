# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260807_issue126_codex_heterogeneous_compat_v1",
  "round_id": "round_20260807_issue126_codex_heterogeneous_compat_v1",
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
  "workstream_id": "issue126-codex-heterogeneous-compat-v1",
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
  "repair_attempt_limit": 1,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_COMPLETE",
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
      "command_id": "observation.codex_version",
      "command": "codex --version",
      "phase": "observation",
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
      "phase": "observation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["tool_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "experiment.codex_baseline",
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
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.md",
    "docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.json"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/control_plane/**",
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
    "project_state/schemas/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/mainline_merge_intents/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "docs/**"
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
    "local_network_exceptions": [
      "git push origin owner/issue126-codex-compat-v1",
      "codex exec"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "docs/research/**"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "project_state/mainline_merge_intents/**", "minimum_risk": "R2"}
  ]
}
```

## Goal

Issue #126 Round C: Codex CLI heterogeneous-provider / native-multi-agent compatibility research spike.

This is NOT a product implementation task. The sole objective is to determine, through real CLI experiments:

```
CODEX_NATIVE
vs
EXTERNAL_ORCHESTRATION
vs
HYBRID
```

The Decision authorizes:
- Codex CLI execution against already-configured providers (OpenAI/ChatGPT + at least one third-party)
- Bounded external network to already-configured provider endpoints only
- Local disposable fixture creation outside the repository (F:\reverse-agent-labs\issue126-codex-compat\)
- Sanitized evidence/report creation under docs/research/
- Normal git commit and push to the exact branch

The Decision explicitly does NOT authorize:
- Reading, printing, or exfiltrating any credential values, auth files, tokens, or API keys
- Direct push to main
- Merge, mark-ready, force push, rebase, tag, release, or deployment
- Runner dispatch, external reverse-tool invocation, or unknown binary execution
- Model API invocation from repository code (only via Codex CLI itself)
- Modification of product code (reverse_agent/**, frontend/**, tests/**, .github/**, AGENTS.md)

## Credential boundary

The meaning of `model_api_invocation_allowed=true` and `real_provider_credential_allowed=false` is:

```
Codex CLI may use its own pre-existing authenticated sessions
```

NOT:

```
The Agent may read, print, or copy any API key, token, or auth blob
```

The credential boundary is absolute:
- API key values, Bearer tokens, auth.json contents, session cookies, refresh/access tokens, encrypted login blobs, and credential-store raw content are NEVER read, printed, or committed.
- Only non-sensitive metadata is recorded: profile name, provider name/type, model name, env variable NAME (not value), authentication presence (YES/NO).

## Acceptance

1. Decision commit is authored before any gate generation or experiment execution.
2. `python -m reverse_agent.project_gate transition-lint --state-dir project_state` reports `PASSED`.
3. `python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre` reports `PRE_EXECUTION_AUTHORIZED`.
4. Codex CLI version is recorded.
5. At least one third-party provider is tested alongside OpenAI/ChatGPT.
6. C1 (ordinary Codex baseline) is executed for each provider.
7. C2 (auth coexistence) is verified.
8. C3 (native MultiAgent) is tested with OpenAI as parent.
9. C3 is repeated with Provider A as parent if Provider A passes C1.
10. C4 (cross-provider child) is attempted only if the CLI natively supports child provider selection.
11. Assignment markers and result markers are used to verify parent-child handoff.
12. All experiments run only inside the disposable fixture directory.
13. Research report written to `docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.md`.
14. JSON matrix written to `docs/research/codex-cli-heterogeneous-multiagent-2026-08-07.json`.
15. `git diff --check` passes.
16. Secret scan confirms no credentials in git diff.
17. Only Decision, generated gate artifacts, and research reports are committed.
18. Push to `owner/issue126-codex-compat-v1` only.

```text
ISSUE126_CODEX_COMPAT_EVIDENCE_READY_FOR_OWNER_AUDIT
```

## Execution policy

- This R3 Decision follows and supersedes `decision_20260807_pr121_final_owner_authority_v4` for the Issue126 compatibility research spike only.
- Run the standard Path-B gate sequence: startup-snapshot, transition-command-plan, transition-lint, transition-preflight (pre), before any experiment execution.
- `mainline` must be `engineering_branch`.
- Experiments execute only inside `F:\reverse-agent-labs\issue126-codex-compat\` (outside the repository).
- No product code, workflow, test, or governance file outside the Decision/gate/research scope is modified.
- No credential values are ever read, printed, or committed.
- Publication is limited to the exact branch and normal push.
- No PR creation, PR comments, issue comments, mark-ready, merge, main push, history rewrite, tag, or release.
- The architecture recommendation must be evidence-driven, not expectation-driven.
