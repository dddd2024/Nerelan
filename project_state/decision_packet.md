# Decision Packet

```json decision_meta
{
  "schema_version": 1,
  "decision_id": "decision_20260808_issue133_frontend_opencode_devup_v2",
  "round_id": "round_20260808_issue133_frontend_opencode_devup_v2",
  "status": "APPROVED",
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260808_issue133_frontend_opencode_devup_v1",
  "follows_last_round_id": "round_20260808_issue133_frontend_opencode_devup_v1",
  "previous_audit_outcome": "ISSUE133_V1_SUPERSEDED_PREEXECUTION_BOOTSTRAP_SYNC_OMISSION",
  "workstream_id": "issue133-frontend-opencode-devup-v2",
  "source_issue": 133,
  "parent_issue": 127,
  "required_branch": "owner/issue133-frontend-opencode-devup-v1",
  "starting_head": "4b44390d4d80960bb1232c6aefdb1994ba16b729",
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
  "branch_creation_allowed": true,
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
    "git switch --track origin/owner/issue133-frontend-opencode-devup-v1",
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
    {"command_id":"sync.switch_existing_branch","command":"git switch owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Use only if the local tracking branch already exists."},
    {"command_id":"sync.create_local_tracking_branch","command":"git switch --track origin/owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":false,"expected_exit_codes":[0],"execution_surface":"local","operations":["branch_creation","repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Authorized only to create the local tracking branch for the already-existing Owner remote branch. Do not create any other local or remote branch."},
    {"command_id":"sync.fast_forward_issue133","command":"git merge --ff-only origin/owner/issue133-frontend-opencode-devup-v1","phase":"bootstrap","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_sync"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"observation.git_head","command":"git rev-parse HEAD","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"observation.git_main","command":"git rev-parse origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"repository_state_attestation"},
    {"command_id":"observation.merge_base","command":"git merge-base HEAD origin/main","phase":"status","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"gate.startup_snapshot","command":"python -m reverse_agent.project_gate startup-snapshot --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/startup_snapshot.json"]},
    {"command_id":"gate.transition_command_plan","command":"python -m reverse_agent.project_gate transition-command-plan --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/command_plan.json","project_state/gates/transition_command_plan_preview.json"]},
    {"command_id":"gate.transition_lint","command":"python -m reverse_agent.project_gate transition-lint --state-dir project_state","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"gate.transition_preflight","command":"python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre","phase":"gate","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["gate_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","allowed_mutated_paths":["project_state/gates/transition_preflight_result.json","project_state/gates/bootstrap_state.json"]},
    {"command_id":"test.frontend","command":"npm --prefix frontend test","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_typecheck","command":"npm --prefix frontend run typecheck","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_lint","command":"npm --prefix frontend run lint","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.frontend_build","command":"npm --prefix frontend run build","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.issue133_backend_focused","command":"python -m pytest tests/test_model_access.py tests/platform_v1/test_task_service.py tests/platform_v1/test_opencode_executor.py tests/test_dev_up_contract.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.platform_v1","command":"python -m pytest tests/platform_v1 -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"test.gate_regression","command":"python -m pytest tests/test_project_gate.py tests/test_control_plane_transition.py -q","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["run_checks"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"validation.create_clean_source","command":"git worktree add --detach F:/reverse-agent-workspaces/issue133-gui-source HEAD","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["worktree_creation","external_workspace_mutation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Run only after implementation and generated gates are committed. Destination must not pre-exist; do not delete or overwrite an existing path."},
    {"command_id":"validation.clean_source_before","command":"git -C F:/reverse-agent-workspaces/issue133-gui-source status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","exact_head_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Output must be empty."},
    {"command_id":"acceptance.dev_up","command":"powershell -ExecutionPolicy Bypass -File .\\dev-up.ps1 -RepoDir F:/reverse-agent-workspaces/issue133-gui-source -OpenCodeModel sensetime/sensenova-6.7-flash-lite -NoBrowser","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_start","loopback_service_start","tool_execution"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Must return only after model-control, Task API and frontend loopback health checks pass. It must not invoke a model by itself."},
    {"command_id":"acceptance.frontend_http","command":"powershell -NoProfile -Command \"$r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4173/; if ($r.StatusCode -ne 200) { exit 1 }\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["loopback_http_probe"],"network_access":false,"required_evidence_source":"local_command_evidence"},
    {"command_id":"acceptance.real_opencode_task","command":"powershell -NoProfile -Command \"$body=@{title='Create issue133_gui_acceptance.txt containing exactly gui-opencode-ok and do not modify any other file';repository='dddd2024/reverse-agent';executor_kind='opencode';model_profile_ref='';permission_profile='ASK_FOR_APPROVAL';policy_ref='';workspace='';branch=''}|ConvertTo-Json -Compress; $created=Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8766/api/tasks -ContentType 'application/json' -Body $body; $done=Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:8766/api/tasks/'+$created.id+'/execute') -ContentType 'application/json' -Body '{}'; $read=Invoke-RestMethod -Method Get -Uri ('http://127.0.0.1:8766/api/tasks/'+$created.id); if ($read.status -ne 'READY_FOR_REVIEW') { throw ('unexpected status '+$read.status) }; if ($read.executor_kind -ne 'opencode') { throw 'executor mismatch' }; if (-not ($read.changed_files | Where-Object { $_.path -eq 'issue133_gui_acceptance.txt' })) { throw 'acceptance file missing' }; if (-not ($read.evidence | Where-Object { $_.category -eq 'ExecutorAction' -or $_.label -eq 'git_diff_check' })) { throw 'executor or validation evidence missing' }; Write-Output $created.id\"","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["model_execution","network_access","tool_execution","external_workspace_mutation","deterministic_validation"],"network_access":true,"required_evidence_source":"local_command_evidence","validation_note":"Use only the pre-existing OpenCode provider session; no credential-value access. Source validation worktree must remain unchanged."},
    {"command_id":"validation.clean_source_after","command":"git -C F:/reverse-agent-workspaces/issue133-gui-source status --short","phase":"validation","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["repository_observation","exact_head_validation"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Output must remain empty after real execution."},
    {"command_id":"acceptance.dev_down","command":"powershell -ExecutionPolicy Bypass -File .\\dev-down.ps1","phase":"acceptance","required":true,"expected_exit_codes":[0],"execution_surface":"local","operations":["process_stop","loopback_service_stop"],"network_access":false,"required_evidence_source":"local_command_evidence","validation_note":"Stop only processes recorded by dev-up; never kill unrelated Python, Node or OpenCode processes."},
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
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "frontend/tests/real-executor-task-plane.test.tsx",
    "tests/test_dev_up_contract.py"
  ],
  "reference_paths": [
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "reverse_agent/project_gate.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/task_runtime.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "reverse_agent/model_access/service.py",
    "reverse_agent/model_access/contracts.py",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/schemas/model-profile.ts",
    "frontend/src/components/model-profile-editor.tsx",
    "frontend/vite.config.ts",
    "frontend/package.json",
    "tests/test_model_access.py",
    "tests/platform_v1/**",
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
    "reverse_agent/**",
    "frontend/src/lib/model-control-client.ts",
    "frontend/src/schemas/model-profile.ts",
    "frontend/src/components/model-profile-editor.tsx",
    "frontend/vite.config.ts",
    "frontend/package.json",
    "docs/**",
    "project_state/mainline_merge_intents/**",
    "project_state/current_state.json",
    "project_state/state_manifest.json",
    "project_state/artifact_index.json",
    "project_state/schemas/**",
    "project_state/rounds/**",
    "project_state/audits/**",
    "tests/platform_v1/**",
    "tests/test_model_access.py"
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
    "merge_intent_mutation"
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
      "opencode run",
      "git fetch origin main",
      "git fetch origin owner/issue133-frontend-opencode-devup-v1",
      "git push origin owner/issue133-frontend-opencode-devup-v1",
      "loopback http://127.0.0.1:4173",
      "loopback http://127.0.0.1:8765",
      "loopback http://127.0.0.1:8766"
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
    "frontend/src/hooks/use-tasks.ts",
    "frontend/src/lib/task-client.ts",
    "frontend/tests/provider-free-task-plane.test.tsx",
    "frontend/tests/real-executor-task-plane.test.tsx",
    "tests/test_dev_up_contract.py"
  ],
  "path_risk_floor": [
    {"pattern":"project_state/decision_packet.md","minimum_risk":"R2"},
    {"pattern":"project_state/gates/**","minimum_risk":"R2"},
    {"pattern":"dev-up.ps1","minimum_risk":"R2"},
    {"pattern":"dev-down.ps1","minimum_risk":"R2"},
    {"pattern":"frontend/**","minimum_risk":"R1"},
    {"pattern":"tests/test_dev_up_contract.py","minimum_risk":"R1"}
  ]
}
```

## Goal

Issue #133 v2 is the executable authority for the first user-facing real-Agent round after PR #132 landed on `main`. v1 is superseded before any local gate activation or implementation because it omitted the explicit bootstrap synchronization commands needed to enter the already-created Owner branch safely.

Target chain:

```text
Frontend -> explicit executor choice -> Task API -> ExecutorRouter -> OpenCodeExecutor
         -> linked Git worktree -> deterministic validation -> SQLite readback
         -> frontend READY_FOR_HUMAN
```

This round also adds a Windows-first one-command development stack startup.

### Architecture boundary

Do not expand model-access to invent an OpenCode profile type. For `executor_kind=opencode`, the frontend must not send a model-control profile id as though it were an OpenCode model id. It sends empty `model_profile_ref`; the trusted Task API process receives `REVERSE_AGENT_OPENCODE_MODEL` from `dev-up.ps1`; OpenCode uses the already-proven local provider session. The UI must label OpenCode as host-configured. Fixture remains explicit/mock-only and is never a silent fallback.

The model-control service still starts under `dev-up.ps1` so existing Settings/model-profile functionality stays available, but it is not the authority for the OpenCode CLI session.

### One-click startup

`dev-up.ps1` must start and health-check model-control (`127.0.0.1:8765`), Task API (`127.0.0.1:8766`) and Vite frontend (`127.0.0.1:4173`), set coherent origins/API bases, set `REVERSE_AGENT_REPO_DIR` and `REVERSE_AGENT_OPENCODE_MODEL` for the Task API child, fail closed on missing Python/Node/npm/OpenCode or occupied ports, install nothing, print no secret, and record only owned child PIDs under ignored runtime state.

`dev-down.ps1` may stop only those recorded children.

### Scope boundary

Allowed implementation is only frontend executor selection/binding, focused frontend regressions, `dev-up.ps1`, `dev-down.ps1`, startup contract tests, and generated gate artifacts. No TaskService/OpenCodeExecutor/model-access rewrite, no merge-intent mutation, no Draft PR publication.

## Acceptance

1. Bootstrap may fetch/read the remote v2 Decision and either switch the existing local tracking branch or create only the local tracking branch for the already-existing Owner remote branch; then ff-only to the exact Owner head.
2. Decision commit precedes implementation and remains immutable after activation.
3. transition-command-plan PASS; transition-lint PASS; transition-preflight `PRE_EXECUTION_AUTHORIZED`, `blocking_reasons=[]`.
4. Normal HTTP create-task path no longer hard-codes fixture; explicit OpenCode selection sends `executor_kind=opencode`.
5. OpenCode selection does not require a model-control profile and sends empty `model_profile_ref`.
6. Fixture/mock path remains deterministic and explicit.
7. `dev-up.ps1` starts the three loopback services, installs nothing, exposes no secret, and detects prerequisites/port conflicts; `dev-down.ps1` stops only owned PIDs.
8. Frontend test/typecheck/lint/build all pass.
9. Focused backend/startup-contract tests, full `tests/platform_v1`, and project-gate/control-plane regressions pass.
10. After implementation commit, clean detached source worktree is empty before and after real acceptance.
11. Real task through the running stack reaches `READY_FOR_REVIEW`, records `issue133_gui_acceptance.txt`, persists executor/validation evidence, and uses `sensetime/sensenova-6.7-flash-lite` via the pre-existing OpenCode session.
12. Codex=0, OpenHands=0, credential-value access=0, provider-config mutation=0, package installation=0.
13. `git diff --check a1d09d4a...HEAD` passes; changed paths remain inside authority.
14. Normal push only; no PR creation, Ready, merge, release or deploy by the local Agent.

```text
ISSUE133_V2_FRONTEND_OPENCODE_DEVUP_READY_FOR_OWNER_AUDIT
```

## Execution policy

- v2 is the only executable local authority; v1 is superseded pre-execution.
- Preserve all unknown staged/unstaged/untracked files. Never clean/reset-hard/rebase/force-push/amend/blanket-stage.
- Existing `.frontend_stage/` and `.platform_v1_runtime/` must be preserved.
- If tracked local modifications block branch switch, do not discard them; use a safe worktree or stop with exact evidence.
- No package installation. Existing dependencies must already be available.
- `dev-up.ps1` itself must not invoke a model; real OpenCode invocation occurs only in the explicit acceptance after preflight and implementation validation.
- `REVERSE_AGENT_OPENCODE_MODEL` is non-secret metadata. Do not read or print provider credentials/tokens.
- Do not mutate `reverse_agent/**`, frontend model-profile schema/editor/client, or `project_state/mainline_merge_intents/**`.
- Do not create a PR; Owner handles exact-head audit and Draft PR later.
