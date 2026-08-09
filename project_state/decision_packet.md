# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_issue136_agent_canvas_stageb2_atomic_screenshot_recapture_v17",
  "round_id": "round_20260809_issue136_agent_canvas_stageb2_atomic_screenshot_recapture_v17",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260809_issue136_agent_canvas_stageb2_existing_screenshot_publication_v16",
  "follows_last_round_id": "round_20260809_issue136_agent_canvas_stageb2_existing_screenshot_publication_v16",
  "previous_audit_outcome": "ISSUE136_STAGE_B2_V16_BLOCKED_AT_EXISTING_SCREENSHOT_DIMENSIONS",
  "workstream_id": "issue136-agent-canvas-stageb2-atomic-screenshot-recapture-v17",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "d85db610a2edab1e21412ef23f84a6046f6c498d",
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
  "stage_b2_atomic_capture_contract": {
    "purpose": "Produce one valid 1440x900 screenshot of the already-persisted successful real OpenCode task using atomic commands. First prove the Edge capture mechanism against about:blank without starting reverse-agent services; only then start the existing stack and capture the task page. No model or task execution.",
    "task_id": "task-1786237330883-8460dbd1c478",
    "task_url": "http://127.0.0.1:4173/tasks/task-1786237330883-8460dbd1c478",
    "required_screenshot": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "quarantined_previous_screenshot": ".platform_v1_runtime/issue136-v14-suspect-screenshot.png",
    "probe_screenshot": ".platform_v1_runtime/issue136-edge-v17-probe-1440x900.png",
    "probe_profile": ".platform_v1_runtime/edge-v17-probe-profile",
    "task_profile": ".platform_v1_runtime/edge-v17-task-profile",
    "required_width": 1440,
    "required_height": 900,
    "minimum_bytes": 50000,
    "expected_source_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
    "source_checkout": "F:/reverse-agent-workspaces/issue136-stageb2-v11-source",
    "prior_readback_backend_status": "READY_FOR_REVIEW",
    "prior_readback_frontend_state": "READY_FOR_HUMAN",
    "prior_readback_executor_kind": "opencode",
    "prior_readback_validation_exit_code": 0,
    "model_calls_allowed": 0,
    "task_create_allowed": false,
    "task_execute_allowed": false,
    "capture_attempt_limit": 1,
    "cleanup_after_dev_up_mandatory_even_on_later_failure": true
  },
  "execution_branch_contract": {
    "inspect_existing_first": true,
    "if_existing_is_1440x900": "Do not recapture. Skip optional quarantine/probe/runtime/capture commands and run validation.final_screenshot followed by publication.",
    "if_existing_is_missing_or_not_1440x900": "Run optional commands in exact order: recovery.quarantine_suspect_if_present, probe.edge_capture, probe.validate, runtime.source_head, runtime.source_clean, runtime.ports_initially_closed, runtime.dev_up, evidence.capture_task, validation.final_screenshot, runtime.dev_down, runtime.ports_closed. After runtime.dev_up succeeds, runtime.dev_down and runtime.ports_closed are mandatory cleanup even if evidence.capture_task or validation.final_screenshot fails or is rejected before process creation. No other command may run after such a failure.",
    "no_runtime_fallback_inside_any_single_command": true
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
      "command_id": "validation.inspect_existing_screenshot",
      "command": "python -c \"from pathlib import Path; import hashlib,struct; p=Path(r'F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png'); b=p.read_bytes() if p.exists() else b''; ok=len(b)>=24 and b[:8]==bytes([137,80,78,71,13,10,26,10]); w,h=struct.unpack('>II',b[16:24]) if ok else (0,0); sha=hashlib.sha256(b).hexdigest() if b else 'NONE'; print(f'EXISTING_SCREENSHOT EXISTS={p.exists()} BYTES={len(b)} PNG={ok} DIMENSIONS={w}x{h} SHA256={sha}')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "recovery.quarantine_suspect_if_present",
      "command": "powershell -NoProfile -Command '$src=\"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\"; $dst=\"F:/reverse-agent/.platform_v1_runtime/issue136-v14-suspect-screenshot.png\"; if(Test-Path -LiteralPath $dst){throw \"quarantine destination already exists\"}; if(Test-Path -LiteralPath $src){Move-Item -LiteralPath $src -Destination $dst; Write-Output \"SUSPECT_SCREENSHOT_QUARANTINED\"} else {Write-Output \"NO_SUSPECT_SCREENSHOT_TO_QUARANTINE\"}'",
      "phase": "recovery",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["evidence_recovery"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
        ".platform_v1_runtime/issue136-v14-suspect-screenshot.png"
      ]
    },
    {
      "command_id": "probe.edge_capture",
      "command": "powershell -NoProfile -Command '$c=@(); if(${env:ProgramFiles(x86)}){$c+=(Join-Path ${env:ProgramFiles(x86)} \"Microsoft/Edge/Application/msedge.exe\")}; if($env:ProgramFiles){$c+=(Join-Path $env:ProgramFiles \"Microsoft/Edge/Application/msedge.exe\")}; $edge=$c|Where-Object {Test-Path -LiteralPath $_}|Select-Object -First 1; if(-not $edge){$cmd=Get-Command msedge.exe -ErrorAction SilentlyContinue; if($cmd){$edge=$cmd.Source}}; if(-not $edge){throw \"Microsoft Edge not found\"}; $args=@(\"--headless=new\",\"--disable-gpu\",\"--no-first-run\",\"--no-default-browser-check\",\"--force-device-scale-factor=1\",\"--user-data-dir=F:/reverse-agent/.platform_v1_runtime/edge-v17-probe-profile\",\"--window-size=1440,900\",\"--screenshot=F:/reverse-agent/.platform_v1_runtime/issue136-edge-v17-probe-1440x900.png\",\"about:blank\"); & $edge @args; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}'",
      "phase": "probe",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_browser_capture", "evidence_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [".platform_v1_runtime/**"]
    },
    {
      "command_id": "probe.validate",
      "command": "python -c \"from pathlib import Path; import struct,time; p=Path(r'F:/reverse-agent/.platform_v1_runtime/issue136-edge-v17-probe-1440x900.png'); [time.sleep(.25) for _ in range(40) if not p.exists()]; b=p.read_bytes() if p.exists() else b''; assert len(b)>=24 and b[:8]==bytes([137,80,78,71,13,10,26,10]), 'probe PNG missing/invalid'; w,h=struct.unpack('>II',b[16:24]); assert (w,h)==(1440,900), f'probe dimensions {w}x{h}'; print(f'EDGE_PROBE_VALID BYTES={len(b)} DIMENSIONS={w}x{h}')\"",
      "phase": "probe",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.source_head",
      "command": "git -C F:/reverse-agent-workspaces/issue136-stageb2-v11-source rev-parse HEAD",
      "phase": "runtime_guard",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["exact_head_validation", "external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.source_clean",
      "command": "git -C F:/reverse-agent-workspaces/issue136-stageb2-v11-source status --short",
      "phase": "runtime_guard",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_source_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.ports_initially_closed",
      "command": "powershell -NoProfile -Command '$open=@(4173,8765,8766)|Where-Object {Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue}; if($open){throw (\"ports already open: \"+($open -join \",\"))}; Write-Output \"PORTS_INITIAL_CLOSED\"'",
      "phase": "runtime_guard",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_network_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.dev_up",
      "command": "powershell -NoProfile -File .\\dev-up.ps1 -RepoDir F:\\reverse-agent -SourceDir F:\\reverse-agent-workspaces\\issue136-stageb2-v11-source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser",
      "phase": "runtime",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_service_start", "runtime_metadata_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [".platform_v1_runtime/**"]
    },
    {
      "command_id": "evidence.capture_task",
      "command": "powershell -NoProfile -Command '$c=@(); if(${env:ProgramFiles(x86)}){$c+=(Join-Path ${env:ProgramFiles(x86)} \"Microsoft/Edge/Application/msedge.exe\")}; if($env:ProgramFiles){$c+=(Join-Path $env:ProgramFiles \"Microsoft/Edge/Application/msedge.exe\")}; $edge=$c|Where-Object {Test-Path -LiteralPath $_}|Select-Object -First 1; if(-not $edge){$cmd=Get-Command msedge.exe -ErrorAction SilentlyContinue; if($cmd){$edge=$cmd.Source}}; if(-not $edge){throw \"Microsoft Edge not found\"}; $args=@(\"--headless=new\",\"--disable-gpu\",\"--no-first-run\",\"--no-default-browser-check\",\"--force-device-scale-factor=1\",\"--user-data-dir=F:/reverse-agent/.platform_v1_runtime/edge-v17-task-profile\",\"--window-size=1440,900\",\"--virtual-time-budget=5000\",\"--screenshot=F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\",\"http://127.0.0.1:4173/tasks/task-1786237330883-8460dbd1c478\"); & $edge @args; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}'",
      "phase": "evidence",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_browser_capture", "evidence_artifact_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        ".platform_v1_runtime/**",
        "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
      ],
      "produced_artifacts": ["frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"]
    },
    {
      "command_id": "validation.final_screenshot",
      "command": "python -c \"from pathlib import Path; import hashlib,struct,time; p=Path(r'F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png'); [time.sleep(.25) for _ in range(60) if not p.exists()]; assert p.exists(), 'required screenshot missing'; b=p.read_bytes(); assert len(b)>=50000, f'screenshot too small: {len(b)}'; assert b[:8]==bytes([137,80,78,71,13,10,26,10]), 'invalid PNG signature'; w,h=struct.unpack('>II',b[16:24]); assert (w,h)==(1440,900), f'unexpected screenshot dimensions: {w}x{h}'; sha=hashlib.sha256(b).hexdigest(); print(f'FINAL_SCREENSHOT_VALID BYTES={len(b)} DIMENSIONS={w}x{h} SHA256={sha}')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "runtime.dev_down",
      "command": "powershell -NoProfile -File .\\dev-down.ps1 -RepoDir F:\\reverse-agent",
      "phase": "cleanup",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_service_stop", "runtime_metadata_mutation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [".platform_v1_runtime/**"]
    },
    {
      "command_id": "runtime.ports_closed",
      "command": "powershell -NoProfile -Command '$open=@(4173,8765,8766)|Where-Object {Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue}; if($open){throw (\"ports still open: \"+($open -join \",\"))}; Write-Output \"PORTS_CLOSED\"'",
      "phase": "cleanup",
      "required": false,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["local_network_observation"],
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
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    ".platform_v1_runtime/**"
  ],
  "reference_paths": [
    "dev-up.ps1",
    "dev-down.ps1",
    "reverse_agent/**",
    "tests/**",
    "frontend/src/**",
    "frontend/tests/**",
    ".frontend_stage/**",
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
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    ".platform_v1_runtime/**"
  ],
  "final_expected": {
    "gate": "PRE_EXECUTION_AUTHORIZED",
    "existing_screenshot_inspected_with_python": true,
    "edge_probe_required_only_if_existing_invalid": true,
    "probe_dimensions": "1440x900",
    "real_task_screenshot_dimensions": "1440x900",
    "real_task_screenshot_minimum_bytes": 50000,
    "model_calls": 0,
    "task_create": 0,
    "task_execute_post": 0,
    "services_closed_after_recapture_branch": true,
    "publication_paths": [
      "project_state/gates/bootstrap_state.json",
      "project_state/gates/command_plan.json",
      "project_state/gates/startup_snapshot.json",
      "project_state/gates/transition_command_plan_preview.json",
      "project_state/gates/transition_preflight_result.json",
      "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
    ],
    "success_terminal": "ISSUE136_STAGE_B2_V17_ATOMIC_SCREENSHOT_PUBLISHED"
  }
}
```

## Owner instruction

v17 supersedes v16. The v16 byte/signature guard passed but reported the target PNG as 160x132 rather than the required 1440x900, so publication correctly stopped. v17 does not trust byte length as screenshot identity and does not combine validation with a hidden runtime fallback.

First run the normal bootstrap/transition sequence and require PRE_EXECUTION_AUTHORIZED with no blocking reasons. Then execute `validation.inspect_existing_screenshot` exactly. If Python reports a valid 1440x900 PNG, do not run any optional recovery/runtime/browser commands; execute `validation.final_screenshot` and publication only.

If Python reports missing or non-1440x900 content, execute the recapture branch atomically and in exact order. `probe.edge_capture` and `probe.validate` must complete before any reverse-agent service is started. The probe is an `about:blank` 1440x900 capture into `.platform_v1_runtime` using a dedicated Edge user-data directory. A probe failure or outer tool-policy rejection stops the round before dev-up.

Only after a valid 1440x900 probe may the local Agent validate the source checkout and closed ports, invoke the existing `dev-up.ps1`, run `evidence.capture_task` once, validate the final PNG with Python, then run `runtime.dev_down` and `runtime.ports_closed`. After `runtime.dev_up` has succeeded, those two cleanup commands are mandatory even if the capture or final validation command fails or is rejected before process creation. Cleanup is the only permitted activity after such a failure.

Do not rerun the capture. Do not call Task create/execute, OpenCode, any model/provider API, package installation, credential access, or source/product repair. Do not modify `.frontend_stage/**`, frontend source/tests, `reverse_agent/**`, tests, dev-up, or dev-down.

Publication is permitted only after `validation.final_screenshot` reports `FINAL_SCREENSHOT_VALID` with dimensions exactly 1440x900 and bytes >=50000, and after the recapture branch (if used) has closed all ports. Stage only the five generated gate JSON artifacts plus the final screenshot. Normal push only; no PR, merge, main push, force, rebase, release, or deployment.
