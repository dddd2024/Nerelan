# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_issue136_agent_canvas_stageb2_existing_screenshot_publication_v16",
  "round_id": "round_20260809_issue136_agent_canvas_stageb2_existing_screenshot_publication_v16",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_issue136_agent_canvas_stageb2_screenshot_recovery_v15",
  "follows_last_round_id": "round_20260809_issue136_agent_canvas_stageb2_screenshot_recovery_v15",
  "previous_audit_outcome": "ISSUE136_STAGE_B2_V15_BLOCKED_AT_VALIDATE_OR_RECAPTURE_TOOL_POLICY_REJECTION_AFTER_EXISTING_SCREENSHOT_CONFIRMED",
  "workstream_id": "issue136-agent-canvas-stageb2-existing-screenshot-publication-v16",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "03228ae287cbcd2719f10a10e3f14b35442ff8e7",
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
  "worktree_creation_allowed": false,
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
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": false,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "publication_contract": {
    "purpose": "Validate and publish the already-existing v14 real-task screenshot. No recapture, service start, task GET/POST, model, provider, or runtime execution is authorized.",
    "required_screenshot": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "expected_bytes": 138341,
    "expected_width": 1440,
    "expected_height": 900,
    "task_id": "task-1786237330883-8460dbd1c478",
    "prior_readback_backend_status": "READY_FOR_REVIEW",
    "prior_readback_frontend_state": "READY_FOR_HUMAN",
    "prior_readback_executor_kind": "opencode",
    "prior_readback_validation_exit_code": 0,
    "model_calls_allowed": 0,
    "task_create_allowed": false,
    "task_execute_allowed": false,
    "service_start_allowed": false,
    "screenshot_recapture_allowed": false
  },
  "bootstrap_exception_files": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
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
    "git rev-parse HEAD",
    "git rev-parse origin/main",
    "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "validation.existing_screenshot",
      "command": "powershell -NoProfile -Command '$p=\"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\"; if(-not (Test-Path -LiteralPath $p)){throw \"required screenshot missing\"}; $b=[IO.File]::ReadAllBytes($p); if($b.Length -ne 138341){throw (\"unexpected screenshot bytes: \"+$b.Length)}; $sig=@(137,80,78,71,13,10,26,10); for($i=0;$i -lt 8;$i++){if($b[$i] -ne $sig[$i]){throw \"invalid PNG signature\"}}; $w=($b[16]-shl 24)-bor($b[17]-shl 16)-bor($b[18]-shl 8)-bor$b[19]; $h=($b[20]-shl 24)-bor($b[21]-shl 16)-bor($b[22]-shl 8)-bor$b[23]; if($w -ne 1440 -or $h -ne 900){throw (\"unexpected screenshot dimensions: \"+$w+\"x\"+$h)}; $hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower(); Write-Output (\"EXISTING_SCREENSHOT_VALID BYTES=\"+$b.Length+\" DIMENSIONS=\"+$w+\"x\"+$h+\" SHA256=\"+$hash)'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.stage",
      "command": "git add -- project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_stage"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_mutated_paths": [
        "project_state/gates/bootstrap_state.json",
        "project_state/gates/command_plan.json",
        "project_state/gates/startup_snapshot.json",
        "project_state/gates/transition_command_plan_preview.json",
        "project_state/gates/transition_preflight_result.json",
        "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
      ]
    },
    {
      "command_id": "publication.cached_check",
      "command": "git diff --cached --check",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.staged_paths",
      "command": "git diff --cached --name-only",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit",
      "command": "git commit -m \"evidence(frontend): publish issue136 real task screenshot\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_commit"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.commit_paths",
      "command": "git diff-tree --no-commit-id --name-only -r HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.push",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_push", "network_access"],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.local_head",
      "command": "git rev-parse HEAD",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.remote_head",
      "command": "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "publication.final_status",
      "command": "git status --short",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
  ],
  "reference_paths": [
    "dev-up.ps1",
    "dev-down.ps1",
    "reverse_agent/**",
    "tests/**",
    "frontend/src/**",
    "frontend/tests/**",
    ".frontend_stage/**",
    ".platform_v1_runtime/**",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    ".github/**",
    ".frontend_stage/**",
    ".platform_v1_runtime/**",
    "frontend/src/**",
    "frontend/tests/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "reverse_agent/**",
    "tests/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "project_state/mainline_merge_intents/**"
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
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "runner_dispatch",
    "external_reverse_tool_invocation",
    "unknown_binary_execution",
    "destructive",
    "package_install",
    "dependency_install",
    "provider_configuration_mutation",
    "local_service_start",
    "local_service_stop",
    "loopback_http_probe",
    "persistent_state_readback",
    "create_pr",
    "pr_creation",
    "draft_pr_creation",
    "pr_body_update",
    "reset_hard",
    "git_clean"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
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
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "git push origin owner/issue136-agent-canvas-reuse-spike-v2"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
  ],
  "path_risk_floor": [
    {"pattern": "project_state/decision_packet.md", "minimum_risk": "R2"},
    {"pattern": "project_state/gates/**", "minimum_risk": "R2"},
    {"pattern": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png", "minimum_risk": "R2"}
  ]
}
```

## Owner instruction

v16 supersedes v15. The v15 salvage command already established that the required screenshot exists at the final target path with exactly 138341 bytes. The v15 combined validate-or-recapture command was rejected by the outer local-Agent execution policy before process creation because the entire command contained fallback process-launch/service-start behavior even though its runtime first branch would have exited immediately.

v16 deliberately removes every fallback and runtime branch. It authorizes only a read-only validation of the already-existing PNG (existence, exact byte length, PNG signature, 1440x900 IHDR dimensions, SHA-256), then publication of that screenshot plus the five generated gate artifacts.

No service start/stop, GET/POST, Edge/browser process, model/OpenCode/provider call, credential access, package operation, product/source/test mutation, PR, merge, or main push is authorized.

Require command-plan PASS, lint PASS, preflight `PRE_EXECUTION_AUTHORIZED` with `blocking_reasons=[]`, screenshot validation PASS, exact staged-path verification, normal commit/push, and local/remote head equality.
