# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue133_frontend_opencode_devup_v4",
  "round_id": "round_20260808_issue133_frontend_opencode_devup_v4",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue133_frontend_opencode_devup_v3",
  "follows_last_round_id": "round_20260808_issue133_frontend_opencode_devup_v3",
  "previous_audit_outcome": "ISSUE133_V3_REWORK_REQUIRED_PROCESS_INSTANCE_AND_PROFILE_SELECTION",
  "workstream_id": "issue133-frontend-opencode-devup-v4",
  "source_issue": 133,
  "parent_issue": 127,
  "active_pr": 134,
  "required_branch": "owner/issue133-frontend-opencode-devup-v1",
  "starting_head": "2002f353bbe00f9379bbef7e8ea3fddf977ec434",
  "activation_base_sha": "a1d09d4ae8887405721efe9871881db788c5820a",
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
    "git fetch origin owner/issue133-frontend-opencode-devup-v1",
    "git show origin/owner/issue133-frontend-opencode-devup-v1:project_state/decision_packet.md",
    "git switch owner/issue133-frontend-opencode-devup-v1",
    "git merge --ff-only origin/owner/issue133-frontend-opencode-devup-v1",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {"command_id":"observation.git_status","command":"git status --short","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"sync.fetch_main","command":"git fetch origin main","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"sync.fetch_issue133","command":"git fetch origin owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"sync.inspect_remote_decision","command":"git show origin/owner/issue133-frontend-opencode-devup-v1:project_state/decision_packet.md","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"sync.switch_branch","command":"git switch owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"sync.fast_forward_issue133","command":"git merge --ff-only origin/owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"observation.git_head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"observation.git_main","command":"git rev-parse origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"observation.merge_base","command":"git merge-base HEAD origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"gate.transition_command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"gate.transition_preflight","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"test.lifecycle_contract","command":"python -m pytest tests/test_dev_up_contract.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend","command":"npm --prefix frontend test","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_typecheck","command":"npm --prefix frontend run typecheck","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_lint","command":"npm --prefix frontend run lint","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_build","command":"npm --prefix frontend run build","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.backend_focused","command":"python -m pytest tests/test_model_access.py tests/platform_v1/test_task_service.py tests/platform_v1/test_opencode_executor.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.platform_v1","command":"python -m pytest tests/platform_v1 -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.gate_regression","command":"python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.create_clean_source","command":"git worktree add --detach F:/reverse-agent-workspaces/issue133-gui-v4-source HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["worktree_creation","external_workspace_mutation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Run only after v4 repair and generated gates are committed. Destination must not pre-exist; do not delete or overwrite an existing path."},
    {"command_id":"validation.clean_source_before","command":"git -C F:/reverse-agent-workspaces/issue133-gui-v4-source status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","exact_head_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Output must be empty."},
    {"command_id":"acceptance.dev_up","command":"powershell -ExecutionPolicy Bypass -File .\\dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/reverse-agent-workspaces/issue133-gui-v4-source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_start","loopback_service_start","tool_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"RepoDir is the trusted service host; SourceDir is the clean exact-head repository exposed to OpenCode. dev-up must not invoke a model."},
    {"command_id":"acceptance.frontend_http","command":"powershell -NoProfile -Command \"$r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4173/; if ($r.StatusCode -ne 200) { exit 1 }\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["loopback_http_probe"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"acceptance.real_opencode_task","command":"powershell -NoProfile -Command \"$body=@{title='Create issue133_gui_v4_acceptance.txt containing exactly gui-opencode-v4-ok and do not modify any other file';repository='dddd2024/reverse-agent';executor_kind='opencode';model_profile_ref='';permission_profile='ASK_FOR_APPROVAL';policy_ref='';workspace='';branch=''}|ConvertTo-Json -Compress; $created=Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8766/api/tasks -ContentType 'application/json' -Body $body; $done=Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:8766/api/tasks/'+$created.id+'/execute') -ContentType 'application/json' -Body '{}'; $read=Invoke-RestMethod -Method Get -Uri ('http://127.0.0.1:8766/api/tasks/'+$created.id); if ($read.status -ne 'READY_FOR_REVIEW') { throw ('unexpected status '+$read.status) }; if ($read.executor_kind -ne 'opencode') { throw 'executor mismatch' }; if (-not ($read.changed_files | Where-Object { $_.path -eq 'issue133_gui_v4_acceptance.txt' })) { throw 'acceptance file missing' }; if (-not ($read.evidence | Where-Object { $_.category -eq 'ExecutorAction' -or $_.label -eq 'git_diff_check' })) { throw 'executor or validation evidence missing' }; Write-Output $created.id\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["model_execution","network_access","tool_execution","external_workspace_mutation","deterministic_validation"],"network_access":true,"required_evidence_source":"local_command_evidence","validation_note":"Exactly one real task. Use only the pre-existing OpenCode provider session; no credential-value access. Source validation worktree must remain unchanged."},
    {"command_id":"validation.clean_source_after","command":"git -C F:/reverse-agent-workspaces/issue133-gui-v4-source status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","exact_head_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Output must remain empty after real execution."},
    {"command_id":"acceptance.dev_down","command":"powershell -ExecutionPolicy Bypass -File .\\dev-down.ps1 -RepoDir F:/reverse-agent","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_stop","loopback_service_stop"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Stop only exact owned process instances after PID, executable, and recorded start-time validation."},
    {"command_id":"acceptance.ports_closed","command":"powershell -NoProfile -Command \"$open=@(4173,8765,8766)|Where-Object { Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue }; if ($open) { throw ('ports still open: '+($open -join ',')) }\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["loopback_http_probe"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"acceptance.dev_up_repeat","command":"powershell -ExecutionPolicy Bypass -File .\\dev-up.ps1 -RepoDir F:/reverse-agent -SourceDir F:/reverse-agent-workspaces/issue133-gui-v4-source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_start","loopback_service_start"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Second startup proves repeatability; no second model task."},
    {"command_id":"acceptance.dev_down_repeat","command":"powershell -ExecutionPolicy Bypass -File .\\dev-down.ps1 -RepoDir F:/reverse-agent","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_stop","loopback_service_stop"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"acceptance.ports_closed_repeat","command":"powershell -NoProfile -Command \"$open=@(4173,8765,8766)|Where-Object { Test-NetConnection 127.0.0.1 -Port $_ -InformationLevel Quiet -WarningAction SilentlyContinue }; if ($open) { throw ('ports still open after repeat: '+($open -join ',')) }\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["loopback_http_probe"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.diff_check","command":"git diff --check a1d09d4ae8887405721efe9871881db788c5820a..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["diff_validation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.path_list","command":"git diff --name-only a1d09d4ae8887405721efe9871881db788c5820a..HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"publication.push_branch","command":"git push origin owner/issue133-frontend-opencode-devup-v1","phase":"publication","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["push","network_access"],"network_access":true,"required_evidence_source":"repository_state_attestation","allowed_only_after_validation":true}
  ],
  "allowed_mutated_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/real-executor-task-plane.test.tsx",
    "tests/test_dev_up_contract.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "reverse_agent/model_access/service.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/test_model_access.py",
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
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/schemas/model-profile.ts",
    "frontend/src/components/model-profile-editor.tsx",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "reverse_agent/**",
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
    "name_wide_process_kill"
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
      "git fetch origin owner/issue133-frontend-opencode-devup-v1",
      "git push origin owner/issue133-frontend-opencode-devup-v1",
      "opencode run"
    ],
    "ci_network_exceptions": []
  },
  "authorized_risk_tier": "R3",
  "authorized_risk_paths": [
    "project_state/decision_packet.md",
    "project_state/gates/**",
    "dev-up.ps1",
    "dev-down.ps1",
    "frontend/src/components/new-task-composer.tsx",
    "frontend/tests/real-executor-task-plane.test.tsx",
    "tests/test_dev_up_contract.py"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":"dev-up.ps1","minimum_risk":"R2"},
    {"pattern":"dev-down.ps1","minimum_risk":"R2"}
  ]
}
```

## Goal

v4 is a minimal fail-forward repair after Owner exact-head audit of Draft PR #134 at `2002f353bbe00f9379bbef7e8ea3fddf977ec434`.

The v2 frontend-to-OpenCode cutover and the v3 RepoDir/SourceDir, partial-start cleanup, truthful shutdown outcome, and duplicate-note repairs are retained. Do **not** rebuild the task plane, model-access subsystem, OpenCode executor, or startup architecture. v4 fixes only two remaining correctness/safety defects, then repeats the exact local runtime acceptance.

## Owner findings

### V4-F1 — fixture model selection is overwritten after the user clears it

Exact-head GitHub `Model Access` workflow failed twice, including an Owner-triggered rerun, on the existing test `fixture submission is disabled when no model profile is selected`.

`NewTaskComposer` derives `enabledProfiles` with a fresh `.filter(...)` array on render and has an effect keyed by that array. After the user deliberately changes the fixture model select to an empty value, another render reruns the effect and restores the default `coding-default` profile. The submit boundary therefore receives a profile even though the user explicitly cleared it.

Repair the initialization/synchronization semantics so an explicit empty fixture selection remains empty and Submit remains disabled. Default-profile initialization may still occur when appropriate, but it must not continuously overwrite a deliberate user choice. Do not modify the existing provider-free regression test to hide the failure.

### V4-F2 — dev-down records start_time but does not validate the process instance

v3 records `start_time`, PID and executable for each owned child, but current `dev-down.ps1` validates only PID + executable before terminating. If Windows recycles a PID to another process with the same executable, the current code can terminate an unrelated process.

Before any termination, `dev-down` must compare the recorded `start_time` with the currently observed process start time using a deterministic normalized representation/tolerance appropriate to PowerShell/JSON DateTime serialization. Missing, unreadable, or mismatched start-time identity must produce `refused_identity_mismatch` (or an equivalent explicit refusal) and **must not kill the process**. The regression must prove dev-down consumes and checks the recorded start instance, not merely that dev-up writes the field.

## Acceptance

1. Transition command plan PASS, transition lint PASS, preflight `PRE_EXECUTION_AUTHORIZED`, blockers empty.
2. Only v4-authorized paths mutate after the v4 Decision commit.
3. Existing `frontend/tests/provider-free-task-plane.test.tsx` passes unchanged, including deliberate empty fixture profile behavior.
4. OpenCode remains the default real executor; fixture remains explicit test mode; no task-client/hook/model-access mutation.
5. `dev-down` validates exact process instance using PID + executable + recorded start time before any termination and refuses mismatches.
6. Lifecycle regression covers matching and mismatching start-time identity plus bounded exact-PID tree termination.
7. Frontend tests/typecheck/lint/build, focused backend tests, full `tests/platform_v1`, and gate/control-plane regressions pass with zero failures.
8. One real OpenCode task using the pre-existing SenseNova session reaches `READY_FOR_REVIEW`, records the expected changed file and evidence, and leaves the exact-head source worktree unchanged.
9. First and repeat dev-up/dev-down cycles close ports 4173/8765/8766; repeat cycle runs no second model task.
10. No credential read/copy/log, no Codex/OpenHands call, no package install, no provider config mutation.
11. Do not modify mainline merge intent. The two known engineering-vs-landing-governance CI failures remain Owner landing work.
12. Normal push only; local Agent does not update PR #134, mark Ready, merge, release, or deploy.

Terminal target:

```text
ISSUE133_V4_RUNTIME_AND_PROFILE_STATE_READY_FOR_OWNER_EXACT_HEAD_REVIEW
```

## Execution policy

- v4 is the only executable repair authority after this Owner Decision commit; v3 is superseded for further execution.
- Preserve all unknown staged/unstaged/untracked local files. Never clean/reset/rebase/force-push.
- Do not edit `frontend/tests/provider-free-task-plane.test.tsx`; it is the existing regression that exposed V4-F1.
- Keep repair scope minimal. No backend/model-access/task-client/hook/package/workflow/docs/merge-intent changes.
- Exactly one real OpenCode model execution is required after deterministic tests pass; do not substitute fixture acceptance and do not run a second model task during repeatability validation.
- Stop after tested normal push and report exact remote head to Owner.
