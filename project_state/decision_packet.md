# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue136_agent_canvas_direct_reuse_stagea_v6",
  "round_id": "round_20260808_issue136_agent_canvas_direct_reuse_stagea_v6",
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
  "follows_last_decision_id": "decision_20260808_issue136_agent_canvas_pathb_cleanup_v5",
  "follows_last_round_id": "round_20260808_issue136_agent_canvas_pathb_cleanup_v5",
  "previous_audit_outcome": "ISSUE136_PATHB_V5_CLEANUP_EVIDENCE_PUSHED_OWNER_VERIFIED",
  "workstream_id": "issue136-agent-canvas-direct-reuse-stagea-v6",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "253569ff30bcda1f4f20eeaeafa2e622adcf9ebb",
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
  "bounded_external_source_access_allowed": true,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 0,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "known_preexisting_external_evidence": {
    "upstream_clone": "F:/reverse-agent-upstreams/agent-canvas-v1.6.1",
    "upstream_tag": "v1.6.1",
    "upstream_head": "43f091baf135142ed6c146f888f44a957141193f",
    "official_upstream_url": "https://github.com/OpenHands/agent-canvas.git",
    "primary_harness": "F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe",
    "package": "@openhands/agent-canvas@1.6.1",
    "primary_install_result": "PASS_WITH_CURRENT_REVERSE_AGENT_PEERS",
    "root_package_cleanup": "COMPLETE_V5"
  },
  "selection_rule": {
    "allowed_terminal_dispositions": [
      "AGENT_CANVAS_PACKAGE_EMBED_ACCEPTED",
      "AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED"
    ],
    "package_embed_requires": "mature workbench reuse with only thin reverse-agent presentation/data adapters",
    "package_embed_reject_if": [
      "requires fake Agent Server APIs",
      "requires OpenHands conversation API emulation",
      "requires large settings/config/backend compatibility graph",
      "requires backend registry emulation",
      "requires second execution-state model"
    ]
  },
  "shell_safety_policy": {
    "powershell_rule": "Every PowerShell command containing variables is invoked with an outer single-quoted -Command argument; script literals use double quotes so the parent shell cannot expand child variables."
  },
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
      "operations": [
        "repository_observation"
      ],
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
      "operations": [
        "repository_observation",
        "network_access"
      ],
      "network_access": true,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "sync.fetch_branch",
      "command": "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "network_access"
      ],
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
      "operations": [
        "repository_observation"
      ],
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
      "operations": [
        "repository_sync"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "sync.fast_forward_branch",
      "command": "git merge --ff-only origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "bootstrap",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_sync"
      ],
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
      "operations": [
        "repository_observation"
      ],
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
      "operations": [
        "repository_observation"
      ],
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
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "guard.root_package_absent",
      "command": "powershell -NoProfile -Command 'if (Test-Path -LiteralPath \"package.json\") { throw \"unexpected repository-root package.json reappeared\" }'",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "upstream.remote_identity",
      "command": "git -C F:/reverse-agent-upstreams/agent-canvas-v1.6.1 remote -v",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
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
      "operations": [
        "external_source_observation"
      ],
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
      "operations": [
        "external_source_observation"
      ],
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
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.verify_primary_package",
      "command": "powershell -NoProfile -Command '$p=\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/node_modules/@openhands/agent-canvas/package.json\"; if (!(Test-Path -LiteralPath $p)) { throw \"Agent Canvas package missing from primary harness\" }; $j=Get-Content -Raw -LiteralPath $p | ConvertFrom-Json; if ($j.version -ne \"1.6.1\") { throw (\"unexpected Agent Canvas version: \" + $j.version) }; Write-Output $j.version'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "probe.verify_primary_peers",
      "command": "npm --prefix F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe ls react react-dom react-router @openhands/agent-canvas --depth=0",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "dependency_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.cli_help",
      "command": "node F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/node_modules/@openhands/agent-canvas/bin/agent-canvas.mjs --help",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.port_precheck",
      "command": "powershell -NoProfile -Command 'if (Test-NetConnection 127.0.0.1 -Port 18080 -InformationLevel Quiet -WarningAction SilentlyContinue) { throw \"port 18080 already occupied\" }'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.start_frontend_only",
      "command": "powershell -NoProfile -Command '$meta=\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reference-process.json\"; if (Test-Path -LiteralPath $meta) { throw \"reference process metadata already exists\" }; $node=(Get-Command node.exe -ErrorAction Stop).Source; $p=Start-Process -FilePath $node -ArgumentList @(\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/node_modules/@openhands/agent-canvas/bin/agent-canvas.mjs\",\"--frontend-only\",\"--port\",\"18080\") -WorkingDirectory \"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe\" -PassThru; [ordered]@{pid=$p.Id;path=$node;start_time=$p.StartTime.ToUniversalTime().ToString(\"o\")} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $meta; Write-Output $p.Id'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_scratch_mutation",
        "local_process_start"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.health",
      "command": "powershell -NoProfile -Command '$ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing \"http://127.0.0.1:18080/\" -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true; break} } catch {}; Start-Sleep -Seconds 1 }; if(-not $ok){ throw \"Agent Canvas reference did not become healthy\" }'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "artifact.prepare_directory",
      "command": "powershell -NoProfile -Command 'New-Item -ItemType Directory -Force -Path \"frontend/artifacts/agent-canvas-v1.6.1\" | Out-Null'",
      "phase": "evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "evidence_artifact_mutation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/artifacts/agent-canvas-v1.6.1/**"
      ]
    },
    {
      "command_id": "reference.screenshot",
      "command": "powershell -NoProfile -Command '$c=@(); if(${env:ProgramFiles(x86)}){$c+=(Join-Path ${env:ProgramFiles(x86)} \"Microsoft/Edge/Application/msedge.exe\")}; if($env:ProgramFiles){$c+=(Join-Path $env:ProgramFiles \"Microsoft/Edge/Application/msedge.exe\")}; $edge=$c | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1; if(-not $edge){$ec=Get-Command msedge.exe -ErrorAction SilentlyContinue; if($ec){$edge=$ec.Source}}; if(-not $edge){throw \"Microsoft Edge not found\"}; & $edge --headless=new --disable-gpu --window-size=1440,900 --screenshot=\"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png\" \"http://127.0.0.1:18080/\"; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}'",
      "phase": "evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "evidence_artifact_mutation",
        "local_browser_capture"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png"
      ]
    },
    {
      "command_id": "reference.stop",
      "command": "powershell -NoProfile -Command '$meta=\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reference-process.json\"; if (!(Test-Path -LiteralPath $meta)) { throw \"reference process metadata missing\" }; $m=Get-Content -Raw -LiteralPath $meta | ConvertFrom-Json; $p=Get-Process -Id ([int]$m.pid) -ErrorAction SilentlyContinue; if($p){ if($p.Path -ne $m.path){throw \"reference process path identity mismatch\"}; $recorded=[datetime]::Parse($m.start_time).ToUniversalTime(); $delta=[math]::Abs(($p.StartTime.ToUniversalTime()-$recorded).TotalMilliseconds); if($delta -gt 100){throw \"reference process start_time identity mismatch\"}; taskkill /PID $p.Id /T /F; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE} }; Remove-Item -LiteralPath $meta -Force'",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_scratch_mutation",
        "bounded_process_stop"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "reference.port_closed",
      "command": "powershell -NoProfile -Command 'if (Test-NetConnection 127.0.0.1 -Port 18080 -InformationLevel Quiet -WarningAction SilentlyContinue) { throw \"port 18080 still open\" }'",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.port_precheck",
      "command": "powershell -NoProfile -Command 'if (Test-NetConnection 127.0.0.1 -Port 18081 -InformationLevel Quiet -WarningAction SilentlyContinue) { throw \"port 18081 already occupied\" }'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.start_mock",
      "command": "powershell -NoProfile -Command '$meta=\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reverse-agent-process.json\"; if (Test-Path -LiteralPath $meta) { throw \"reverse-agent process metadata already exists\" }; $ce=(Get-Command cmd.exe -ErrorAction Stop).Source; $p=Start-Process -FilePath $ce -ArgumentList @(\"/d\",\"/s\",\"/c\",\"npm --prefix frontend run dev:mock -- --host 127.0.0.1 --port 18081 --strictPort\") -WorkingDirectory \"F:/reverse-agent\" -PassThru; [ordered]@{pid=$p.Id;path=$ce;start_time=$p.StartTime.ToUniversalTime().ToString(\"o\")} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $meta; Write-Output $p.Id'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_scratch_mutation",
        "local_process_start"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.health",
      "command": "powershell -NoProfile -Command '$ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing \"http://127.0.0.1:18081/\" -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true; break} } catch {}; Start-Sleep -Seconds 1 }; if(-not $ok){ throw \"reverse-agent mock frontend did not become healthy\" }'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.screenshot",
      "command": "powershell -NoProfile -Command '$c=@(); if(${env:ProgramFiles(x86)}){$c+=(Join-Path ${env:ProgramFiles(x86)} \"Microsoft/Edge/Application/msedge.exe\")}; if($env:ProgramFiles){$c+=(Join-Path $env:ProgramFiles \"Microsoft/Edge/Application/msedge.exe\")}; $edge=$c | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1; if(-not $edge){$ec=Get-Command msedge.exe -ErrorAction SilentlyContinue; if($ec){$edge=$ec.Source}}; if(-not $edge){throw \"Microsoft Edge not found\"}; & $edge --headless=new --disable-gpu --window-size=1440,900 --screenshot=\"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png\" \"http://127.0.0.1:18081/\"; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}'",
      "phase": "evidence",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "evidence_artifact_mutation",
        "local_browser_capture"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png"
      ]
    },
    {
      "command_id": "baseline.stop",
      "command": "powershell -NoProfile -Command '$meta=\"F:/reverse-agent-workspaces/issue136-agent-canvas-package-probe/reverse-agent-process.json\"; if (!(Test-Path -LiteralPath $meta)) { throw \"reverse-agent process metadata missing\" }; $m=Get-Content -Raw -LiteralPath $meta | ConvertFrom-Json; $p=Get-Process -Id ([int]$m.pid) -ErrorAction SilentlyContinue; if($p){ if($p.Path -ne $m.path){throw \"reverse-agent process path identity mismatch\"}; $recorded=[datetime]::Parse($m.start_time).ToUniversalTime(); $delta=[math]::Abs(($p.StartTime.ToUniversalTime()-$recorded).TotalMilliseconds); if($delta -gt 100){throw \"reverse-agent process start_time identity mismatch\"}; taskkill /PID $p.Id /T /F; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE} }; Remove-Item -LiteralPath $meta -Force'",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_scratch_mutation",
        "bounded_process_stop"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "baseline.port_closed",
      "command": "powershell -NoProfile -Command 'if (Test-NetConnection 127.0.0.1 -Port 18081 -InformationLevel Quiet -WarningAction SilentlyContinue) { throw \"port 18081 still open\" }'",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_network_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "analysis.sidebar_dependencies",
      "command": "powershell -NoProfile -Command 'Select-String -Path \"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/features/sidebar/sidebar.tsx\" -Pattern \"useSettings|useConfig|useNavigation|useActiveBackendContext|useBackendsHealth|useSidebarStore|SettingsModal|AddBackendModal|ManageBackendsModal\"'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "analysis.conversation_dependencies",
      "command": "powershell -NoProfile -Command 'Select-String -Path \"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/features/conversation/conversation-main/conversation-main.tsx\" -Pattern \"ChatInterfaceWrapper|ConversationTabContent|ConversationNameWithStatus|ConversationTabs|useResizablePanels|useConversationStore|SidebarMobileMenuToggle\"'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "analysis.public_exports",
      "command": "powershell -NoProfile -Command 'Get-Content \"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/sidebar/index.ts\",\"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/conversation/index.ts\",\"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/files/index.ts\",\"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/settings/index.ts\",\"F:/reverse-agent-upstreams/agent-canvas-v1.6.1/src/components/terminal/index.ts\"'",
      "phase": "research",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "external_source_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.frontend",
      "command": "npm --prefix frontend test",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "run_checks"
      ],
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
      "operations": [
        "run_checks"
      ],
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
      "operations": [
        "run_checks"
      ],
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
      "operations": [
        "run_checks"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.git_status",
      "command": "git status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.working_diff_check",
      "command": "git diff --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "stage.evidence_and_gates",
      "command": "git add project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_stage"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.cached_diff_check",
      "command": "git diff --cached --check",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.cached_paths",
      "command": "git diff --cached --name-only",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.commit",
      "command": "git commit -m \"evidence(frontend): record issue136 stage-a compatibility\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "local_commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.path_list",
      "command": "git diff --name-only 253569ff30bcda1f4f20eeaeafa2e622adcf9ebb..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.final_diff_check",
      "command": "git diff --check dd4cb074ab5b9baacf300706878b29bd745f12c3..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.push",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "push",
        "network_access"
      ],
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
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.remote_head",
      "command": "git rev-parse origin/owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
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
    "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png"
  ],
  "reference_paths": [
    "AGENTS.md",
    "frontend/src/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/vite.config.*",
    "frontend/tsconfig*.json",
    "reverse_agent/project_gate.py",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "frontend/src/**",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/vite.config.*",
    "frontend/tsconfig*.json",
    "reverse_agent/**",
    "tests/**",
    ".github/**",
    "docs/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "package.json",
    "project_state/mainline_merge_intents/**",
    "project_state/current_state.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "direct_push_main",
    "auto_merge",
    "merge",
    "force_push",
    "rebase",
    "amend",
    "tag_or_release",
    "release",
    "deployment",
    "credential_access",
    "credential_publication",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "package_installation",
    "provider_configuration_mutation",
    "production_frontend_mutation"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "bmad_installation_allowed": false,
    "network_access_default_allowed": false,
    "local_network_exceptions": [
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "git push origin owner/issue136-agent-canvas-reuse-spike-v2"
    ],
    "ci_network_exceptions": [],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**"
  ],
  "path_risk_floor": [
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    }
  ],
  "acceptance": {
    "root_package": "ABSENT",
    "upstream_tag": "v1.6.1",
    "upstream_head": "43f091baf135142ed6c146f888f44a957141193f",
    "reference_http": 200,
    "baseline_http": 200,
    "viewport": "1440x900",
    "required_screenshots": [
      "frontend/artifacts/agent-canvas-v1.6.1/reference-home-1440x900.png",
      "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-current-1440x900.png"
    ],
    "frontend_checks": [
      "test",
      "typecheck",
      "lint",
      "build"
    ],
    "package_installs": 0,
    "model_calls": 0,
    "production_frontend_source_changes": 0,
    "terminal": "ISSUE136_STAGE_A_V6_EVIDENCE_READY_FOR_OWNER_DISPOSITION"
  }
}
```