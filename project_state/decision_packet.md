# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260809_issue136_agent_canvas_source_fork_stageb2_real_opencode_v11",
  "round_id": "round_20260809_issue136_agent_canvas_source_fork_stageb2_real_opencode_v11",
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
  "follows_last_decision_id": "decision_20260809_issue136_agent_canvas_source_fork_stageb1_evidence_v10",
  "follows_last_round_id": "round_20260809_issue136_agent_canvas_source_fork_stageb1_evidence_v10",
  "previous_audit_outcome": "ISSUE136_STAGE_B1_VISUAL_SOURCE_PROVENANCE_ACCEPTED",
  "workstream_id": "issue136-agent-canvas-source-fork-stageb2-real-opencode-v11",
  "source_issue": 136,
  "parent_issue": 127,
  "required_branch": "owner/issue136-agent-canvas-reuse-spike-v2",
  "starting_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
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
  "exact_head_workflow_observation_allowed": false,
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
  "model_execution_required": true,
  "model_api_invocation_allowed": true,
  "opencode_invocation_allowed": true,
  "codex_invocation_allowed": false,
  "openhands_invocation_allowed": false,
  "package_installation_allowed": false,
  "provider_configuration_mutation_allowed": false,
  "credential_value_access_allowed": false,
  "preexisting_provider_session_use_allowed": true,
  "bounded_external_source_access_allowed": false,
  "repair_attempt_limit": 0,
  "infrastructure_retry_limit": 1,
  "audit_generation_allowed": false,
  "prior_audits_immutable": true,
  "bootstrap_state_initial": "BOOTSTRAP_OPEN",
  "accepted_disposition": "AGENT_CANVAS_PINNED_SOURCE_FORK_SELECTED",
  "carry_forward_stage_b1": {
    "implementation_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
    "visual_owner_audit": "PASS",
    "source_provenance_owner_audit": "PASS",
    "frontend": "18 files / 110 tests PASS; typecheck PASS; lint PASS; build PASS",
    "platform_product": "410 passed excluding landing-governance files",
    "landing_governance": "201 passed / 12 expected authority-binding mismatches only",
    "source_repair_allowed_in_b2": false
  },
  "stage_b2_contract": {
    "purpose": "Minimum real OpenCode execution plus frontend GUI readback proof on the visually accepted Agent Canvas source-fork workbench.",
    "exact_model_execution_count": 1,
    "model": "sensetime/sensenova-6.7-flash-lite",
    "source_checkout": "F:/reverse-agent-workspaces/issue136-stageb2-v11-source",
    "source_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
    "task_id_evidence": "F:/reverse-agent-workspaces/issue136-stageb2-v11-task-id.txt",
    "real_task_screenshot": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "expected_backend_status": "READY_FOR_REVIEW",
    "expected_frontend_state": "READY_FOR_HUMAN",
    "required_readback": [
      "changed_files",
      "evidence",
      "events",
      "executor_kind",
      "validation_exit_code"
    ],
    "product_source_mutation_allowed": false,
    "provider_configuration_mutation_allowed": false,
    "credential_value_access_allowed": false,
    "pr_or_merge_allowed": false,
    "failure_cleanup": "If any command after dev-up fails, do not rerun the real OpenCode task. Run only acceptance.dev_down and acceptance.ports_closed when safe, report evidence, and stop.",
    "retry_rule": "Infrastructure retry allowance applies only before acceptance.real_opencode_task. acceptance.real_opencode_task has zero retry authority."
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "guard.b1_head_ancestor",
      "command": "git merge-base --is-ancestor 5629306ecb1ac1377ad414decbe31993e3b34c27 HEAD",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "B2 Decision must descend from the visually accepted B1 implementation head."
    },
    {
      "command_id": "guard.root_package_absent",
      "command": "powershell -NoProfile -Command 'if (Test-Path -LiteralPath \"package.json\") { throw \"unexpected repository-root package.json\" }'",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.startup_snapshot",
      "command": "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "gate_execution"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "gate_execution"
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "gate_execution"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "gate.transition_preflight",
      "command": "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre",
      "phase": "gate",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "gate_execution"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "project_state/gates/transition_preflight_result.json",
        "project_state/gates/bootstrap_state.json"
      ]
    },
    {
      "command_id": "guard.product_unchanged_before_acceptance",
      "command": "powershell -NoProfile -Command '$p=@(git diff --name-only 5629306ecb1ac1377ad414decbe31993e3b34c27..HEAD); $bad=$p | Where-Object { $_ -ne \"project_state/decision_packet.md\" -and $_ -notlike \"project_state/gates/*\" }; if($bad){ throw (\"unexpected pre-acceptance product diff: \"+($bad -join \",\")) }'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "exact_head_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "test.runtime_focused",
      "command": "python -m pytest tests/test_dev_up_contract.py tests/platform_v1/test_task_service.py tests/platform_v1/test_opencode_executor.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "run_checks"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.ports_precheck",
      "command": "powershell -NoProfile -Command '$open=@(4173,8765,8766)|Where-Object { Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue }; if($open){ throw (\"ports already open: \"+($open -join \",\")) }'",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "loopback_http_probe"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.source_path_precheck",
      "command": "powershell -NoProfile -Command 'if (Test-Path -LiteralPath \"F:/reverse-agent-workspaces/issue136-stageb2-v11-source\") { throw \"B2 source worktree path already exists\" }; if (Test-Path -LiteralPath \"F:/reverse-agent-workspaces/issue136-stageb2-v11-task-id.txt\") { throw \"B2 task-id evidence path already exists\" }'",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "external_workspace_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.create_clean_source",
      "command": "git worktree add --detach F:/reverse-agent-workspaces/issue136-stageb2-v11-source 5629306ecb1ac1377ad414decbe31993e3b34c27",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "worktree_creation",
        "external_workspace_mutation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Create a clean detached source checkout at the visually accepted B1 exact head. Do not overwrite an existing path."
    },
    {
      "command_id": "acceptance.clean_source_before",
      "command": "git -C F:/reverse-agent-workspaces/issue136-stageb2-v11-source status --short",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "exact_head_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Output must be empty."
    },
    {
      "command_id": "acceptance.dev_up",
      "command": "powershell -ExecutionPolicy Bypass -File .\\dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/reverse-agent-workspaces/issue136-stageb2-v11-source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "process_start",
        "loopback_service_start",
        "tool_execution"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Startup must not itself invoke a model. Use the existing authenticated OpenCode session only."
    },
    {
      "command_id": "acceptance.stack_health",
      "command": "powershell -NoProfile -Command '$ports=@(4173,8765,8766); foreach($p in $ports){ if(-not (Test-NetConnection 127.0.0.1 -Port $p -InformationLevel Quiet -WarningAction SilentlyContinue)){ throw (\"port not healthy: \"+$p) } }; $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4173/ -TimeoutSec 10; if($r.StatusCode -ne 200){ throw \"frontend health failed\" }'",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "loopback_http_probe"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "acceptance.real_opencode_task",
      "command": "powershell -NoProfile -Command '$body=@{title=\"Create issue136_stageb2_acceptance.txt containing exactly issue136-b2-ok and do not modify any other repository file. Read it back, run git diff --check, do not commit, and do not push\";repository=\"dddd2024/reverse-agent\";executor_kind=\"opencode\";model_profile_ref=\"\";permission_profile=\"ASK_FOR_APPROVAL\";policy_ref=\"\";workspace=\"\";branch=\"\"}|ConvertTo-Json -Compress; $created=Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8766/api/tasks -ContentType \"application/json\" -Body $body; $null=Invoke-RestMethod -Method Post -Uri (\"http://127.0.0.1:8766/api/tasks/\"+$created.id+\"/execute\") -ContentType \"application/json\" -Body \"{}\"; $read=Invoke-RestMethod -Method Get -Uri (\"http://127.0.0.1:8766/api/tasks/\"+$created.id); if($read.status -ne \"READY_FOR_REVIEW\"){throw (\"unexpected backend status \"+$read.status)}; if($read.state -ne \"READY_FOR_HUMAN\"){throw (\"unexpected frontend state \"+$read.state)}; if($read.executor_kind -ne \"opencode\"){throw \"executor mismatch\"}; if($read.validation_exit_code -ne 0){throw \"validation did not pass\"}; if(-not ($read.changed_files | Where-Object { $_.path -eq \"issue136_stageb2_acceptance.txt\" })){throw \"acceptance changed file missing\"}; $cats=@($read.evidence | ForEach-Object { $_.category }); foreach($c in @(\"Executor\",\"Validation\",\"ExecutorAction\")){if($cats -notcontains $c){throw (\"missing evidence category \"+$c)}}; $types=@($read.events | ForEach-Object { $_.type }); foreach($t in @(\"DISCOVERED\",\"EXECUTOR_RUNNING\",\"EXECUTOR_FINISHED\",\"WORKSPACE_READY\")){if($types -notcontains $t){throw (\"missing event \"+$t)}}; if(($types -notcontains \"VALIDATED\") -and ($types -notcontains \"LOCAL_VALIDATED\")){throw \"validation event missing\"}; Set-Content -Encoding ascii -NoNewline -LiteralPath \"F:/reverse-agent-workspaces/issue136-stageb2-v11-task-id.txt\" -Value $created.id; Write-Output $created.id'",
      "phase": "acceptance",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "model_execution",
        "network_access",
        "tool_execution",
        "external_workspace_mutation",
        "deterministic_validation"
      ],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Exactly one real OpenCode task/model execution. No retries except one infrastructure retry before any second model call; never access credential values or mutate provider config."
    },
    {
      "command_id": "acceptance.screenshot_real_task",
      "command": "powershell -NoProfile -Command '$id=(Get-Content -Raw -LiteralPath \"F:/reverse-agent-workspaces/issue136-stageb2-v11-task-id.txt\").Trim(); if(-not $id){throw \"missing task id\"}; $c=@(); if(${env:ProgramFiles(x86)}){$c+=(Join-Path ${env:ProgramFiles(x86)} \"Microsoft/Edge/Application/msedge.exe\")}; if($env:ProgramFiles){$c+=(Join-Path $env:ProgramFiles \"Microsoft/Edge/Application/msedge.exe\")}; $edge=$c | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1; if(-not $edge){$cmd=Get-Command msedge.exe -ErrorAction SilentlyContinue; if($cmd){$edge=$cmd.Source}}; if(-not $edge){throw \"Microsoft Edge not found\"}; & $edge --headless=new --disable-gpu --window-size=1440,900 --screenshot=\"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\" (\"http://127.0.0.1:4173/tasks/\"+$id); if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}; if(-not (Test-Path -LiteralPath \"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\")){throw \"real-task screenshot missing\"}; $len=(Get-Item -LiteralPath \"F:/reverse-agent/frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\").Length; if($len -lt 50000){throw (\"real-task screenshot unexpectedly small: \"+$len)}'",
      "phase": "evidence",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "evidence_artifact_mutation",
        "local_browser_capture"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "allowed_mutated_paths": [
        "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
      ]
    },
    {
      "command_id": "acceptance.clean_source_after",
      "command": "git -C F:/reverse-agent-workspaces/issue136-stageb2-v11-source status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "exact_head_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Output must remain empty after the real task."
    },
    {
      "command_id": "acceptance.dev_down",
      "command": "powershell -ExecutionPolicy Bypass -File .\\dev-down.ps1 -RepoDir F:/reverse-agent",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "process_stop",
        "loopback_service_stop"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Stop only exact owned process instances after PID, executable, and recorded start-time validation."
    },
    {
      "command_id": "acceptance.ports_closed",
      "command": "powershell -NoProfile -Command '$open=@(4173,8765,8766)|Where-Object { Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue }; if($open){ throw (\"ports still open: \"+($open -join \",\")) }'",
      "phase": "cleanup",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "loopback_http_probe"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.git_status",
      "command": "git status --short",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "stage.stageb2_evidence",
      "command": "git add frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png project_state/gates/bootstrap_state.json project_state/gates/command_plan.json project_state/gates/startup_snapshot.json project_state/gates/transition_command_plan_preview.json project_state/gates/transition_preflight_result.json",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "publication.commit",
      "command": "git commit -m \"test(frontend): prove real OpenCode readback in Agent Canvas workbench\"",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "local_commit"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.path_list",
      "command": "git diff --name-only 5629306ecb1ac1377ad414decbe31993e3b34c27..HEAD",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "diff_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.no_product_diff_final",
      "command": "powershell -NoProfile -Command '$p=@(git diff --name-only 5629306ecb1ac1377ad414decbe31993e3b34c27..HEAD); $bad=$p | Where-Object { $_ -ne \"project_state/decision_packet.md\" -and $_ -notlike \"project_state/gates/*\" -and $_ -ne \"frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png\" }; if($bad){ throw (\"unexpected B2 product diff: \"+($bad -join \",\")) }'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation",
        "exact_head_validation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "validation.final_status_boundary",
      "command": "powershell -NoProfile -Command '$s=@(git status --short); $bad=$s | Where-Object { $_ -notmatch \"^\\?\\? \\.(frontend_stage|platform_v1_runtime)/\" }; if($bad){ throw (\"unexpected final status: \"+($bad -join \"; \")) }; $s'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [
        0
      ],
      "execution_surface": "local",
      "operations": [
        "repository_observation"
      ],
      "network_access": false,
      "required_evidence_source": "local_command_evidence",
      "validation_note": "Only the two known local untracked runtime directories may remain; no tracked/staged product change may remain."
    },
    {
      "command_id": "publication.push",
      "command": "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "phase": "publication",
      "required": true,
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
      "expected_exit_codes": [
        0
      ],
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
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/src/lib/task-client.ts",
    "frontend/src/hooks/use-task.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/components/app-shell.tsx",
    "frontend/src/components/sidebar.tsx",
    "frontend/src/components/task-detail.tsx",
    "frontend/src/vendor/agent-canvas-v1.6.1/**",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/platform_v1/run_store.py",
    "tests/test_dev_up_contract.py",
    "tests/platform_v1/test_task_service.py",
    "tests/platform_v1/test_opencode_executor.py",
    "project_state/mainline_merge_intents/active.json",
    "project_state/schemas/**"
  ],
  "generated_artifact_paths": [
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png"
  ],
  "forbidden_mutated_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "poetry.lock",
    "uv.lock",
    ".github/**",
    "docs/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/vite.config.*",
    "frontend/tsconfig*.json",
    "frontend/src/**",
    "frontend/tests/**",
    "reverse_agent/**",
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
    "create_pr",
    "mark_ready",
    "merge",
    "merge_intent_mutation",
    "name_wide_process_kill",
    "product_source_repair"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": true,
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
      "git fetch origin main",
      "git fetch origin owner/issue136-agent-canvas-reuse-spike-v2",
      "git push origin owner/issue136-agent-canvas-reuse-spike-v2",
      "opencode run"
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
    {
      "pattern": "project_state/decision_packet.md",
      "minimum_risk": "R2"
    },
    {
      "pattern": "project_state/gates/**",
      "minimum_risk": "R2"
    },
    {
      "pattern": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
      "minimum_risk": "R2"
    }
  ],
  "acceptance": {
    "stage_b1_visual_audit": "PASS",
    "stage_b1_implementation_head": "5629306ecb1ac1377ad414decbe31993e3b34c27",
    "product_source_diff_after_b1": "NONE",
    "focused_runtime_tests": "PASS",
    "real_opencode_tasks": 1,
    "real_model_calls": 1,
    "provider_session": "PREEXISTING_ONLY",
    "backend_status": "READY_FOR_REVIEW",
    "frontend_state": "READY_FOR_HUMAN",
    "source_checkout_before_after": "CLEAN_AND_UNCHANGED",
    "changed_files_readback": "NONEMPTY_AND_CONTAINS_issue136_stageb2_acceptance.txt",
    "evidence_categories": [
      "Executor",
      "Validation",
      "ExecutorAction"
    ],
    "event_readback": "DISCOVERED_EXECUTOR_RUNNING_EXECUTOR_FINISHED_WORKSPACE_READY_VALIDATED",
    "real_task_screenshot": "frontend/artifacts/agent-canvas-v1.6.1/reverse-agent-source-fork-real-opencode-task-1440x900.png",
    "ports_after_cleanup": "4173_8765_8766_CLOSED",
    "pr_created": false,
    "merge_performed": false,
    "terminal": "ISSUE136_STAGE_B2_REAL_OPENCODE_GUI_EVIDENCE_READY_FOR_OWNER_AUDIT"
  }
}
```
