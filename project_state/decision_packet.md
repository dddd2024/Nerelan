# Decision Packet

```json decision_meta
{"schema_version":1,"decision_id":"decision_20260816_issue204_durable_process_smoke1_r2_v3","round_id":"round_20260816_issue204_durable_process_smoke1_r2_v3","status":"APPROVED","mainline":"engineering_branch","skill_profiles":["reverse-agent-iteration@v2"]}
```

```json decision_contract
{
  "transition_kernel_required": true,
  "follows_last_decision_id": "decision_20260816_issue206_post_coder_product_only_validation_r2_v4",
  "follows_last_round_id": "round_20260816_issue206_post_coder_product_only_validation_r2_v4",
  "previous_audit_outcome": "ISSUE206_POST_CODER_PRODUCT_ONLY_ISOLATED_PUBLICATION_PROVEN_AND_PRODUCT_LANDED",
  "workstream_id": "issue204-durable-process-smoke1-r2-v3",
  "source_issue": 204,
  "parent_issue": 148,
  "related_recovery_issue": 205,
  "related_validation_issue": 206,
  "related_flaky_test_issue": 207,
  "required_branch": "owner/issue204-durable-process-smoke1-r2-v3",
  "starting_head": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "activation_base_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "canonical_planning_sha": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "accepted_product_head": "deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
  "risk_tier": "R2",
  "governance_artifact_risk_tier": "R2",
  "decision_commit_must_precede_implementation": true,
  "decision_content_immutable_after_activation": true,
  "pr_creation_allowed": false,
  "draft_pr_creation_allowed": false,
  "pr_body_update_allowed": false,
  "pr_comment_allowed": false,
  "issue_comment_allowed": false,
  "branch_creation_allowed": false,
  "worktree_creation_allowed": true,
  "local_commit_allowed": false,
  "normal_push_allowed": false,
  "push_allowed": false,
  "merge_allowed": false,
  "force_push_allowed": false,
  "rebase_during_execution_allowed": false,
  "destructive_operations_allowed": false,
  "capability_policy": {
    "runner_dispatch_allowed": false,
    "model_api_invocation_allowed": false,
    "opencode_invocation_allowed": false,
    "codex_invocation_allowed": false,
    "openhands_invocation_allowed": false,
    "external_reverse_tool_invocation_allowed": false,
    "unknown_binary_execution_allowed": false,
    "destructive_operations_allowed": false,
    "network_access_default_allowed": false,
    "package_installation_allowed": true,
    "local_network_exceptions": [
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
      "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue204-durable-process-smoke1-r2-v3",
      "python -m pip install langgraph==1.0.10 langgraph-checkpoint-sqlite==3.1.0"
    ],
    "remote_observation_read_only_allowed": true,
    "direct_push_to_main_allowed": false,
    "merge_allowed": false,
    "force_push_allowed": false,
    "rebase_during_execution_allowed": false,
    "tag_or_release_allowed": false
  },
  "bootstrap_exception_files": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "bootstrap_exception_commands": [
    "git -C F:/reverse-agent-planning-smoke status --short",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke fetch origin owner/issue204-durable-process-smoke1-r2-v3",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/repository-modernization-v2-planning",
    "git -C F:/reverse-agent-planning-smoke rev-parse origin/owner/issue204-durable-process-smoke1-r2-v3",
    "powershell -NoProfile -Command \"$b=(git -C F:/reverse-agent-planning-smoke branch --list owner/issue204-durable-process-smoke1-r2-v3);if($b){'ISSUE204_V3_LOCAL_BRANCH_ALREADY_EXISTS';exit 25};if(Test-Path -LiteralPath 'F:/reverse-agent-issue204-durable-process-smoke1-r2-v3'){'ISSUE204_V3_AUTH_WORKTREE_ALREADY_EXISTS';exit 24};if(Test-Path -LiteralPath 'F:/reverse-agent-issue204-smoke-source-v3'){'ISSUE204_V3_SOURCE_WORKTREE_ALREADY_EXISTS';exit 23};if(Test-Path -LiteralPath 'F:/reverse-agent-durable-process-smoke1-v3'){'ISSUE204_V3_SMOKE_ROOT_ALREADY_EXISTS';exit 22};'ISSUE204_V3_BOOTSTRAP_TARGETS_ABSENT'\"",
    "git -C F:/reverse-agent-planning-smoke worktree add --track -b owner/issue204-durable-process-smoke1-r2-v3 F:/reverse-agent-issue204-durable-process-smoke1-r2-v3 origin/owner/issue204-durable-process-smoke1-r2-v3",
    "Set-Location F:/reverse-agent-issue204-durable-process-smoke1-r2-v3",
    "git status --short",
    "git rev-parse HEAD",
    "git merge-base HEAD deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
    "git show HEAD:project_state/decision_packet.md",
    "python -m reverse_agent.project_gate startup-snapshot --state-dir project_state",
    "python -m reverse_agent.project_gate transition-command-plan --state-dir project_state",
    "python -m reverse_agent.project_gate transition-lint --state-dir project_state",
    "python -m reverse_agent.project_gate transition-preflight --state-dir project_state --mode pre"
  ],
  "allowed_commands": [
    {
      "command_id": "issue204v3.dependencies_install",
      "command": "python -m pip install langgraph==1.0.10 langgraph-checkpoint-sqlite==3.1.0",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["package_installation", "network_access"],
      "network_access": true,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.dependencies_identity",
      "command": "python -c \"import importlib.metadata as m; assert m.version('langgraph')=='1.0.10'; assert m.version('langgraph-checkpoint-sqlite')=='3.1.0'; print('ISSUE204_V3_DEPENDENCIES_OK')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.source_create",
      "command": "git worktree add --detach F:/reverse-agent-issue204-smoke-source-v3 deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["worktree_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.source_identity",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue204-smoke-source-v3';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='deed415c7dff3101b18aac6a3ea0cc01fc5eba3c',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;print('ISSUE204_V3_SOURCE_IDENTITY_OK',h)\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.smoke_root_create",
      "command": "powershell -NoProfile -Command \"New-Item -ItemType Directory -Path 'F:/reverse-agent-durable-process-smoke1-v3' -ErrorAction Stop | Out-Null; Write-Output 'ISSUE204_V3_SMOKE_ROOT_CREATED'\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["external_evidence_directory_creation"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.smoke_driver",
      "command": "python F:/reverse-agent-durable-process-smoke1-v3/smoke_driver.py --source F:/reverse-agent-issue204-smoke-source-v3 --root F:/reverse-agent-durable-process-smoke1-v3/runtime --planning deed415c7dff3101b18aac6a3ea0cc01fc5eba3c",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["run_checks", "subprocess_crash_recovery_smoke", "os_process_kill", "linked_worktree_smoke"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.source_unchanged",
      "command": "python -c \"import subprocess;root=r'F:/reverse-agent-issue204-smoke-source-v3';h=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip();assert h=='deed415c7dff3101b18aac6a3ea0cc01fc5eba3c',h;s=subprocess.check_output(['git','-C',root,'status','--porcelain'],text=True);assert not s,s;print('ISSUE204_V3_SOURCE_UNCHANGED')\"",
      "phase": "validation",
      "required": true,
      "expected_exit_codes": [0],
      "execution_surface": "local",
      "operations": ["repository_observation", "run_checks"],
      "network_access": false,
      "required_evidence_source": "local_command_evidence"
    },
    {
      "command_id": "issue204v3.authority_diff_check",
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
      "command_id": "issue204v3.final_status",
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
  "reference_paths": [
    "reverse_agent/platform_v1/durable_execution.py",
    "reverse_agent/platform_v1/run_store.py",
    "reverse_agent/platform_v1/task_service.py",
    "reverse_agent/platform_v1/trusted_host.py",
    "reverse_agent/platform_v1/opencode_executor.py",
    "tests/platform_v1/test_durable_execution.py"
  ],
  "generated_artifact_paths": [
    "project_state/gates/command_plan.json",
    "project_state/gates/startup_snapshot.json",
    "project_state/gates/bootstrap_state.json",
    "project_state/gates/transition_command_plan_preview.json",
    "project_state/gates/transition_preflight_result.json"
  ],
  "forbidden_mutated_paths": [
    "pyproject.toml",
    "reverse_agent/**",
    "tests/**",
    "project_state/decision_packet.md",
    "project_state/mainline_merge_intents/**",
    ".github/**",
    "docs/**",
    "frontend/**",
    "AGENTS.md",
    "README.md"
  ],
  "forbidden_operations": [
    "product_change",
    "test_change",
    "commit",
    "push",
    "pr_create",
    "merge",
    "force_push",
    "rebase",
    "reset",
    "clean",
    "stash",
    "model_api_invocation",
    "opencode_invocation",
    "codex_invocation",
    "openhands_invocation",
    "real_provider_call"
  ],
  "authorized_risk_tier": "R2",
  "authorized_risk_paths": ["project_state/gates/**"],
  "runner_managed_artifact_paths": []
}
```

# Goal

Run post-landing Durable Execution process-boundary smoke only, now against canonical planning `deed415c7dff3101b18aac6a3ea0cc01fc5eba3c` containing the validated #205 POST_CODER resume fix. No repository product/test mutation is authorized. All harness/runtime/evidence must remain outside the repository under `F:/reverse-agent-durable-process-smoke1-v3`.

# Mandatory execution semantics

These semantics are part of this Decision. The local Agent must not depend on GitHub comments to obtain them.

1. **True OS kill, not `_CrashSimulated`.** The crash child must run the landed `DurableExecutionService` with an in-memory replacement for `reverse_agent.platform_v1.durable_execution._check_crash_seam`. The replacement must atomically write an external marker only after the target checkpoint (`POST_PLANNER` or `POST_CODER`) is accepted, then block indefinitely. The parent must prove the child remains alive, prove the persisted accepted checkpoint equals the target, sample `heartbeat_at_ms` at least twice with a bounded delay and require it advances while the child is blocked, then terminate the child with `subprocess.Popen.kill()` and require nonzero exit. `_CrashSimulated`, `set_crash_after_checkpoint`, catching `BaseException`, or graceful child exit are not acceptable crash proofs.
2. **No graceful lease cleanup.** Immediately after kill, reopen the DB and require the same old nonempty `lease_owner`, same `lease_epoch`, and persisted expiry remain. Do not edit lease/heartbeat timestamps. Wait using wall clock until strictly later than the persisted `lease_expiry_ms` plus a bounded safety margin before recovery.
3. **Real linked worktree.** Fake `prepare_worktree_once()` must create a linked worktree from exact detached source `F:/reverse-agent-issue204-smoke-source-v3` at planning SHA `deed415c7dff3101b18aac6a3ea0cc01fc5eba3c` using `git -C <source> worktree add --detach <case-worktree> <planning-sha>`. It must not run `git init` and must not create any commit. Source and execution worktree must resolve to the same Git common directory. Execution worktree HEAD and persisted `repository_base_sha` must both equal the planning SHA.
4. **Role behavior.** Planner creates only `.reverse-agent-handoff/plan.md`; Coder requires the plan and creates one deterministic uncommitted product diff inside the linked worktree only; Reviewer creates only `.reverse-agent-handoff/review.md`. External role-log entries are appended only after a fake role completes successfully. No OpenCode/model/provider/network call. This POST_CODER case must exercise the landed snapshot-restore path rather than bypassing it.
5. **CASE A.** Target `POST_PLANNER`. Before kill, roles exactly Planner=1, Coder=0, Reviewer=0. After actual lease expiry, a fresh recovery process calls `reconcile_expired_runs()`, requires Task `INTERRUPTED` and classification `orphan_stale_lease`, proves one old-owner heartbeat with old owner+epoch raises `TaskStoreError`, then resumes with a new owner. Recovery roles exactly Planner=0, Coder=1, Reviewer=1.
6. **CASE B.** Independent DB/task/worktree, target `POST_CODER`. Before kill, roles exactly Planner=1, Coder=1, Reviewer=0. Recovery roles exactly Planner=0, Coder=0, Reviewer=1. The persisted `coder_product_diff_digest` must be nonempty before kill; after recovery, final success proves the reconstructed worktree product snapshot matched that persisted digest and Reviewer was not falsely classified as `reviewer_product_mutation`.
7. **Both cases final invariants.** Same task_id/execution_id/run_id before and after; exactly one durable run; recovery epoch strictly greater than crash epoch; same linked-worktree path; same nonempty repository base equal to planning SHA and actual worktree HEAD; same checkpoint DB path and file exists; checkpoint history exactly `PRE_PLANNER,POST_PLANNER,POST_CODER,POST_REVIEWER,POST_VALIDATION`, each once; final Task `READY_FOR_REVIEW`; final accepted checkpoint `POST_VALIDATION`; validation exit 0; detached source remains exact planning and clean.
8. **Evidence.** External `summary.json` must contain, per case: crash/recovery PIDs and exit codes; marker timestamp; task/execution/run IDs; live-at-marker checkpoint; at least two pre-kill heartbeat samples; pre-kill owner/epoch/expiry; kill timestamp; immediate post-kill owner/epoch/heartbeat/expiry; recovery owner/epoch; linked-worktree path/HEAD; repository base; source/worktree Git common-dir identities; checkpoint DB path; crash/recovery role counts; durable-run count; checkpoint history; final status/checkpoint/validation exit; POST_CODER persisted coder digest presence; zero OpenCode/model/provider counts.
9. **#207 isolation.** Credential-relay Windows socket lifecycle flakiness remains tracked independently in #207. This smoke must not invoke credential relay, provider networking, or change `tests/platform_v1/test_credential_relay.py` / `reverse_agent/model_access/**`; a #207 symptom is not grounds to expand this smoke's scope.
10. **Fail closed.** Any invariant failure prints `DURABLE_PROCESS_CRASH_RESTART_SMOKE1_BOUNDED_FAILURE`, preserves external evidence, and performs no repository/remote mutation. Success prints exactly `DURABLE_PROCESS_CRASH_RESTART_SMOKE1_ACCEPTED` and exits 0.
