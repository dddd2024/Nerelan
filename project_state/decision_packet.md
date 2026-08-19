# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260819_issue245_sprint_c_sequential_recovery_r3_v2",
  "round_id": "round_20260819_issue245_sprint_c_sequential_recovery_r3_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260819_issue246_clean_candidate_landing_r2_v5",
  "follows_last_round_id": "round_20260819_issue246_clean_candidate_landing_r2_v5",
  "previous_audit_outcome": "ISSUE246_DURABLE_RESUME_REPAIR_LANDED_B93DAF97_REMOTE_VERIFIED",
  "workstream_id": "issue245-sprint-c-sequential-recovery-r3-v2",
  "source_issue": 245,
  "parent_issue": 232,
  "required_branch": "owner/issue245-sprint-c-sequential-recovery-r3-v2",
  "starting_head": "b93daf9743f30028e98c38891edcca134772a541",
  "activation_base_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "authority_worktree": "F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v2",
  "risk_tier": "R3",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_live_execution": true,
  "decision_content_immutable_after_activation": true,
  "product_change_commit_limit": 0,
  "canonical_planning_sha": "b93daf9743f30028e98c38891edcca134772a541",
  "source_worktree": "F:/reverse-agent-issue245-sequential-team-source-v2",
  "helper_path": "F:/reverse-agent-issue245-owner-helper-v1/sequential_team_interruption.py",
  "helper_sha256": "84000ebe999ece7d32fe3269d708121de1f3ea1ccabd2f0e3bb867a12f226521",
  "helper_size_bytes": 23887,
  "live_root": "F:/reverse-agent-issue245-sequential-team-live-v2",
  "product_setup_path": "F:/reverse-agent/.platform_v1_runtime/model_setup_state.json",
  "forbidden_real_task_store": "F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3",
  "binding_ref": "opencode-sensenova-67-flash-lite",
  "task_limit": 1,
  "model_role_invocation_limit": 3,
  "role_order": ["planner", "coder", "reviewer"],
  "interruption_checkpoint": "POST_CODER",
  "live_command_attempt_limit": 1,
  "retry_limit": 0,
  "fallback_limit": 0,
  "raw_credential_read_forbidden": true,
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 fetch origin owner/issue245-sprint-c-sequential-recovery-r3-v2",
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 rev-parse origin/owner/issue245-sprint-c-sequential-recovery-r3-v2",
    "$b=(git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 branch --list owner/issue245-sprint-c-sequential-recovery-r3-v2);if($b){'ISSUE245_V2_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v2'){'ISSUE245_V2_WORKTREE_ALREADY_EXISTS';exit 24};'ISSUE245_V2_BOOTSTRAP_TARGETS_ABSENT'",
    "git -C F:/reverse-agent-issue246-clean-candidate-landing-r2-v5 worktree add --track -b owner/issue245-sprint-c-sequential-recovery-r3-v2 F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v2 origin/owner/issue245-sprint-c-sequential-recovery-r3-v2",
    "git -C F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v2 sparse-checkout disable",
    "Set-Location F:/reverse-agent-issue245-sprint-c-sequential-recovery-r3-v2",
    "git status --short",
    "git rev-parse HEAD",
    "git rev-parse HEAD^",
    "git merge-base HEAD b93daf9743f30028e98c38891edcca134772a541",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue245v2.verify_absence_and_helper",
      "command": "$helper='F:/reverse-agent-issue245-owner-helper-v1/sequential_team_interruption.py';$hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $helper).Hash.ToLower();$size=(Get-Item -LiteralPath $helper).Length;if($hash -ne '84000ebe999ece7d32fe3269d708121de1f3ea1ccabd2f0e3bb867a12f226521' -or $size -ne 23887){exit 51};if(Test-Path -LiteralPath 'F:/reverse-agent-issue245-sequential-team-source-v2'){exit 52};if(Test-Path -LiteralPath 'F:/reverse-agent-issue245-sequential-team-live-v2'){exit 53};if(-not (Test-Path -LiteralPath 'F:/reverse-agent/.platform_v1_runtime/model_setup_state.json')){exit 54};'ISSUE245_V2_INPUTS_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue245v2.provider_free_regression",
      "command": "python -m pytest tests/test_team_graph.py tests/platform_v1/test_durable_execution.py tests/platform_v1/test_task_service.py -q",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue245v2.sanitized_binding",
      "command": "python -c \"import json;from reverse_agent.model_access.store import ModelProfileStore;s=ModelProfileStore(state_path=r'F:\\\\reverse-agent\\\\.platform_v1_runtime\\\\model_setup_state.json');b=s.get_binding_public('opencode-sensenova-67-flash-lite');assert b.get('enabled') is True and b.get('executor_id')=='opencode';c={x['connection_id']:x for x in s.list_connections_public()}[b['connection_id']];assert c.get('auth_method')=='external_cli_session' and c.get('external_session_status')=='executor_managed';print(json.dumps({'binding':b,'connection':c},sort_keys=True))\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue245v2.opencode_readiness",
      "command": "python -c \"import json,subprocess;from pathlib import Path;from reverse_agent.platform_v1.opencode_executor import resolve_opencode_cli;p,is_cmd=resolve_opencode_cli();assert not is_cmd;r=subprocess.run([p,'--version'],capture_output=True,text=True,timeout=30);assert r.returncode==0;print(json.dumps({'binary':Path(p).name,'is_cmd':is_cmd,'version':r.stdout.strip()}))\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["known_binary_execution", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue245v2.prepare_source",
      "command": "git worktree add --detach F:/reverse-agent-issue245-sequential-team-source-v2 b93daf9743f30028e98c38891edcca134772a541",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_create", "repository_sync"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue245v2.verify_source",
      "command": "$p='F:/reverse-agent-issue245-sequential-team-source-v2';$head=(git -C $p rev-parse HEAD);$dirty=@(git -C $p status --short);if($head -ne 'b93daf9743f30028e98c38891edcca134772a541' -or $dirty.Count -ne 0){exit 55};'ISSUE245_V2_SOURCE_VERIFIED'",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "repository_state_attestation"
    },
    {
      "command_id": "issue245v2.live_once",
      "command": "$authority=(git rev-parse HEAD);python F:/reverse-agent-issue245-owner-helper-v1/sequential_team_interruption.py --source F:/reverse-agent-issue245-sequential-team-source-v2 --root F:/reverse-agent-issue245-sequential-team-live-v2 --product-setup F:/reverse-agent/.platform_v1_runtime/model_setup_state.json --forbidden-task-store F:/reverse-agent/.platform_v1_runtime/tasks.sqlite3 --authority $authority --planning b93daf9743f30028e98c38891edcca134772a541 --binding opencode-sensenova-67-flash-lite",
      "phase": "implementation",
      "required": true,
      "expected_exit_codes": [0, 20],
      "execution_surface": "local",
      "operations": ["runner_dispatch", "known_binary_execution", "model_api_invocation", "provider_network_call", "owned_process_termination"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence",
      "allowed_only_after_validation": true
    },
    {
      "command_id": "issue245v2.readback",
      "command": "python -c \"import json,pathlib;d=json.loads(pathlib.Path(r'F:\\\\reverse-agent-issue245-sequential-team-live-v2\\\\evidence.json').read_text(encoding='utf-8'));assert d.get('status') in ('SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_ACCEPTED','SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_BLOCKED_WITH_EXACT_EVIDENCE');assert int(d.get('model_invocations_after_resume',d.get('observed_model_invocations',-1)))<=3;print(d.get('status'),d.get('phase'),d.get('task_id',''),d.get('run_id_after',''))\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue245v2.final_status",
      "command": "git status --short",
      "phase": "status",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    }
  ],
  "allowed_mutated_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "runner_managed_artifact_paths": [
    "F:/reverse-agent-issue245-sequential-team-live-v2/**",
    "F:/reverse-agent-issue245-sequential-team-source-v2/**"
  ],
  "reference_paths": [
    "reverse_agent/model_access/store.py",
    "reverse_agent/platform_v1/**",
    "reverse_agent/workflows/team_graph.py",
    "tests/test_team_graph.py",
    "tests/platform_v1/test_durable_execution.py",
    "tests/platform_v1/test_task_service.py",
    "project_state/decision_packet.md"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "project_state/decision_packet.md",
    ".github/**",
    "reverse_agent/**",
    "tests/**",
    "frontend/**",
    "docs/**",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements*.txt",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**"
  ],
  "forbidden_operations": [
    "product_or_test_mutation",
    "second_task",
    "fourth_model_invocation",
    "retry",
    "replan",
    "fallback_model",
    "manual_opencode_run",
    "auth_store_read",
    "auth_list_probe",
    "models_probe",
    "login_or_logout",
    "raw_credential_read",
    "credential_publication",
    "merge",
    "mark_ready",
    "auto_merge",
    "push",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "amend",
    "restore",
    "tag_or_release",
    "deployment",
    "dependency_install",
    "unknown_binary_execution",
    "worktree_deletion"
  ],
  "capability_policy": {
    "runner_dispatch_allowed": true,
    "model_api_invocation_allowed": true,
    "opencode_invocation_allowed": true,
    "live_provider_access_allowed": true,
    "executor_managed_external_session_allowed": true,
    "credential_value_access_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "owned_process_termination_allowed": true,
    "destructive_operations_allowed": false,
    "github_merge_allowed": false,
    "publication_allowed": false
  },
  "success_terminal": "SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_ACCEPTED",
  "blocked_terminal": "SPRINT_C_SEQUENTIAL_TEAM_INTERRUPTION_RECOVERY_BLOCKED_WITH_EXACT_EVIDENCE"
}
```

## Goal

Run one fresh real durable `sequential_team` Task on the repaired planning head. Interrupt Host 1 immediately after durable `POST_CODER`, then restart and resume only Reviewer under a newer fencing epoch.

## Acceptance

1. Helper hash/size match; source and live roots are absent before execution.
2. Provider-free regressions, sanitized Binding, and known OpenCode readiness pass before live traffic.
3. Source worktree is exact clean planning head `b93daf97...`.
4. Exactly one Task and at most three role/model invocations; no retry or fallback.
5. Before interruption: roles exactly Planner/Coder, launch count 2, checkpoint `POST_CODER`, Coder digest present.
6. Startup performs zero model calls; resume runs only Reviewer and finishes with total count 3.
7. Task/run/execution/base/worktree identities are unchanged, fencing epoch increases, stale write is rejected.
8. Final checkpoint `POST_VALIDATION`, Task `READY_FOR_REVIEW`, `git_diff_check=0`, exact calculator change and semantic proof.
9. Product Setup and real TaskStore stat are unchanged; evidence contains no raw credential/provider output.
10. No repository product/test/docs/workflow/package or publication mutation.

## Execution policy

- The live helper may be executed once only. Exit 20 is an accepted bounded-failure terminal and must not be retried.
- The only allowed process termination is the helper's own disposable trusted-host process tree.
- OpenCode receives the existing executor-managed session by reference; no credential value or auth store may be inspected.
