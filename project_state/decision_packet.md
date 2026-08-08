# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue136_agent_canvas_direct_reuse_spike_v2",
  "round_id": "round_20260808_issue136_agent_canvas_direct_reuse_spike_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_pr134_frontend_opencode_devup_landing_v1",
  "follows_last_round_id": "round_20260808_pr134_frontend_opencode_devup_landing_v1",
  "previous_audit_outcome": "ISSUE136_STAGE_A_V1_LOCAL_BLOCKED_WRONG_CLONE_URL_UNPUBLISHED",
  "workstream_id": "issue136-agent-canvas-direct-reuse-spike-v2",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
  "activation_base_sha": "dd4cb074ab5b9baacf300706878b29bd745f12c3",
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
  "worktree_creation_allowed": true,
  "local_commit_allowed": true,
  "normal_push_allowed": true,
  "exact_head_workflow_observation_allowed": true,
  "merge_allowed": false,
  "mark_ready_allowed": false,
  "auto_merge_allowed": false,
  "force_push_allowed": false,
  "rebase_allowed": false,
  "direct_push_to_main_allowed": false,
  "release_allowed": false,
  "deployment_allowed": false,
  "real_provider_credential_allowed": false,
  "live_provider_probe_allowed": false,
  "model_execution_required": false,
  "model_api_invocation_allowed": false,
  "opencode_invocation_allowed": false,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": true,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
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
    "git status --short",
    "git fetch origin main",
    "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
    "git show origin/owner/issue136-agent-canvas-reuse-spike-v2:project_state/decision_packet.md",
    "git switch owner/issue136-agent-canvas-reuse-spike-v2",
    "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
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
      "command_id": "sync.fetch_main",
      "command": "git fetch origin main",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "sync.fetch_v2_branch",
      "command": "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "sync.inspect_remote_decision",
      "command": "git show origin/owner/issue136-agent-canvas-reuse-spike-v2:project_state/decision_packet.md",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.switch_branch",
      "command": "git switch owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.fast_forward_v2_branch",
      "command": "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_sync"],
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
      "required_evidence_source": "repository_state_attestation"
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
      "command_id": "observation.node_version",
      "command": "node --version",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["environment_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.npm_version",
      "command": "npm --version",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["environment_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "observation.frontend_peers",
      "command": "npm --prefix frontend ls react react-dom react-router --depth=0",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["dependency_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.npm_metadata",
      "command": "npm view @openhands/agent-canvas@1.6.1 version license engines repository peerDependencies exports --json",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_external_source_access", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.clone_official_v161",
      "command": "git clone --branch v1.6.1 --single-branch https://github.com/OpenHands/agent-canvas.git F:/reverse-agent-upstreams/agent-canvas-v1.6.1",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["bounded_external_source_access", "network_access", "external_scratch_mutation"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.remote_identity",
      "command": "git -C F:/reverse-agent-upstreams/agent-canvas-v1.6.1 remote -v",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.clean_status",
      "command": "git -C F:/reverse-agent-upstreams/agent-canvas-v1.6.1 status --short",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.exact_tag",
      "command": "git -C F:/reverse-agent-upstreams/agent-canvas-v1.6.1 describe --tags --exact-match",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.exact_head",
      "command": "git -C F:/reverse-agent-upstreams/agent-canvas-v1.6.1 rev-parse HEAD",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.prepare_primary",
      "command": "powershell -NoProfile -Command \"if (Test-Path 'F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe') { exit 42 }; New-Item -ItemType Directory -Path 'F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe' | Out-Null\"",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.primary_init",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe init -y",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.primary_current_peers",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe install react@19.2.8 react-dom@19.2.8 react-router@8.3.0 --save-exact",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_installation", "external_scratch_mutation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.primary_agent_canvas",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe install @openhands/agent-canvas@1.6.1 --save-exact",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0, 1],
      "execution_surface": "local",
      "operations": ["package_installation", "external_scratch_mutation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.prepare_diagnostic",
      "command": "powershell -NoProfile -Command \"if (Test-Path 'F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe') { exit 42 }; New-Item -ItemType Directory -Path 'F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe' | Out-Null\"",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.diagnostic_init",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe init -y",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.diagnostic_install",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe install react@19.2.5 react-dom@19.2.5 react-router@7.17.0 @openhands/agent-canvas@1.6.1 --save-exact",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_installation", "external_scratch_mutation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.cli_help_primary",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe exec -- agent-canvas --help",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_ui_reference_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.cli_help_diagnostic",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe exec -- agent-canvas --help",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_ui_reference_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.artifact_dir",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Force -Path 'frontend/artifacts/agent-canvas-v1.6.1' | Out-Null\"",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["authorized_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["frontend/artifacts/agent-canvas-v1.6.1/**"]
    },
    {
      "command_id": "reference.start_primary",
      "command": "powershell -NoProfile -Command \"$p=Start-Process -FilePath 'npm.cmd' -ArgumentList '--prefix','F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe','exec','--','agent-canvas','--frontend-only','--port','18080' -PassThru -RedirectStandardOutput 'F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reference.out.log' -RedirectStandardError 'F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reference.err.log'; $p.Id | Set-Content 'F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reference.pid'; Write-Output $p.Id\"",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_ui_reference_run", "external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.start_diagnostic",
      "command": "powershell -NoProfile -Command \"$p=Start-Process -FilePath 'npm.cmd' -ArgumentList '--prefix','F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe','exec','--','agent-canvas','--frontend-only','--port','18080' -PassThru -RedirectStandardOutput 'F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe/reference.out.log' -RedirectStandardError 'F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe/reference.err.log'; $p.Id | Set-Content 'F:/reverse-agent-workspaces/issue136-agent-canvas-diagnostic-probe/reference.pid'; Write-Output $p.Id\"",
      "phase": "research",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_ui_reference_run", "external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.capture_upstream",
      "command": "powershell -NoProfile -Command \"$edge=@('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1; if (-not $edge) { exit 2 }; & $edge --headless --disable-gpu --window-size=1440,900 --screenshot='F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png' 'http://127.0.0.1:18080'\"",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["browser_screenshot", "authorized_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png"]
    },
    {
      "command_id": "baseline.start_reverse_agent_mock",
      "command": "powershell -NoProfile -Command \"$p=Start-Process -FilePath 'npm.cmd' -ArgumentList '--prefix','frontend','run','dev:mock','--','--host','127.0.0.1','--port','18081' -PassThru -RedirectStandardOutput 'F:/reverse-agent-workspaces/issue136-reverse-agent-baseline.out.log' -RedirectStandardError 'F:/reverse-agent-workspaces/issue136-reverse-agent-baseline.err.log'; $p.Id | Set-Content 'F:/reverse-agent-workspaces/issue136-reverse-agent-baseline.pid'; Write-Output $p.Id\"",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_ui_reference_run", "external_scratch_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.capture_reverse_agent",
      "command": "powershell -NoProfile -Command \"$edge=@('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Microsoft/Edge/Application/msedge.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1; if (-not $edge) { exit 2 }; & $edge --headless --disable-gpu --window-size=1440,900 --screenshot='F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png' 'http://127.0.0.1:18081'\"",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["browser_screenshot", "authorized_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": ["frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png"]
    },
    {
      "command_id": "test.frontend",
      "command": "npm --prefix frontend test",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.frontend_typecheck",
      "command": "npm --prefix frontend run typecheck",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.frontend_lint",
      "command": "npm --prefix frontend run lint",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.frontend_build",
      "command": "npm --prefix frontend run build",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
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
      "command": "git diff --name-only dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push_branch",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
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
    "frontend/AGENT_CANVAS_DIRECT_REUSE_SPIKE.md",
    "frontend/artifacts/agent-canvas-v1.6.1/**"
  ],
  "reference_paths": [
    "AGENTS.md",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/OPENHANDS_REUSE_MAP.md",
    "frontend/OPENHANDS_VISUAL_ACCEPTANCE.md",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/hooks/use-tasks.ts",
    "project_state/schemas/**",
    "reverse_agent/project_gate.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/**",
    "frontend/tests/**",
    "reverse_agent/**",
    "tests/**",
    ".github/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "docs/**",
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
    "create_pull_request",
    "mark_ready",
    "merge",
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
    "provider_configuration_mutation",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_agent_invocation",
    "production_frontend_mutation",
    "publication_controller_implementation",
    "package_installation_inside_repository"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "path_risk_floor": [
    {"pattern": ".github/workflows/**", "minimum_risk": "R2"},
    {"pattern": "**/secrets/**", "minimum_risk": "R3"}
  ]
}
```

## Owner ruling

This Decision supersedes the unpublished local v1 attempt as execution authority. The v1 attempt stopped correctly after the authorized clone target was found to be wrong. Its local commits are evidence only and MUST NOT be rebased, cherry-picked, pushed, or used as the base for v2.

The only canonical Stage A execution branch is `owner/issue136-agent-canvas-reuse-spike-v2`, created by Owner from `main@dd4cb074ab5b9baacf300706878b29bd745f12c3`.

The official upstream clone authority is exact and immutable for this round:

`https://github.com/OpenHands/agent-canvas.git` at tag `v1.6.1`.

The pinned npm CLI has been Owner-verified to support `--frontend-only` and `--port <port>`. Stage A may therefore run the static Agent Canvas frontend only on `127.0.0.1:18080` without starting an LLM conversation. Starting an Agent Server/LLM conversation remains forbidden.

The primary compatibility probe must first model the current reverse-agent peers (`react@19.2.8`, `react-dom@19.2.8`, `react-router@8.3.0`) and attempt a normal install of `@openhands/agent-canvas@1.6.1`. If that install fails, the failure is evidence. A second diagnostic harness using the Agent Canvas peers (`19.2.5`, `19.2.5`, `7.17.0`) is optional and exists only to inspect/render the package; it cannot by itself justify package-embed acceptance.

Package installs are permitted only under `F:/reverse-agent-workspaces/**`; they are forbidden in `F:/reverse-agent/frontend` and may not mutate tracked package manifests.

Launching the Agent Canvas UI/reference without starting an LLM conversation is permitted. Starting an OpenHands Agent, submitting a model task, provider login/configuration, or reading credential values remains forbidden.

Stage A must end in exactly one evidence-backed disposition:

- `AGENT_CANVAS_PACKAGE_EMBED_ACCEPTED`, or
- `AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED`.

No production UI replacement is authorized by this Decision.
